#!/usr/bin/env python3
"""Live SkillOpt loop adapter.

This module owns the provider-dependent closed loop:
target rollout -> judge score -> optimizer reflect edit -> validation gate.
Baseline tests use a fake chat client; default real provider calls go through the
Gemini API, with an explicit provider switch for Codex CLI.
Live calls are kept out of scripts/verify.

Kept in one file for now because this is the first live adapter slice and its
test seams need to remain easy to inspect. Split provider, scoring, reflect,
and artifact-store ownership once a second provider or resume path lands.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol


def _load_core():
    core_path = Path(__file__).with_name("skillopt_core.py")
    spec = importlib.util.spec_from_file_location("skillopt_core", core_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load skillopt core at {core_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


core = _load_core()
CODEX_MIN_TIMEOUT_SEC = 600


class ChatClient(Protocol):
    def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
        ...


@dataclass(frozen=True)
class LiveModels:
    target: str
    optimizer: str
    judge: str | None = None


@dataclass
class LiveBudget:
    max_calls: int | None = None
    calls: int = 0

    def charge(self, *, model: str) -> None:
        if self.max_calls is not None and self.calls >= self.max_calls:
            raise RuntimeError(f"LLM call budget exceeded before model {model}: max {self.max_calls}")
        self.calls += 1


class BudgetedChatClient:
    def __init__(self, inner: ChatClient, budget: LiveBudget) -> None:
        self.inner = inner
        self.budget = budget

    def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
        self.budget.charge(model=model)
        return self.inner.chat(model=model, system=system, user=user, max_tokens=max_tokens)

    def chat_json_object(
        self,
        *,
        model: str,
        system: str,
        user: str,
        max_tokens: int,
        schema: dict[str, Any],
        filename: str,
    ) -> dict[str, Any]:
        json_client = getattr(self.inner, "chat_json_object", None)
        self.budget.charge(model=model)
        if not callable(json_client):
            raw = self.inner.chat(model=model, system=system, user=user, max_tokens=max_tokens)
            return _extract_json_object(raw)
        return json_client(
            model=model,
            system=system,
            user=user,
            max_tokens=max_tokens,
            schema=schema,
            filename=filename,
        )


class CliChatClient:
    def __init__(
        self,
        *,
        provider: str = "gemini",
        codex_bin: str | None = None,
        gemini_api_key: str | None = None,
        gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        gemini_model: str | None = None,
        timeout: int = 180,
        urlopen: Callable[..., Any] | None = None,
    ) -> None:
        if provider not in {"gemini", "codex", "auto"}:
            raise ValueError("provider must be 'gemini', 'codex', or 'auto'")
        self.provider = provider
        self.codex_bin = codex_bin or shutil.which("codex")
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.gemini_base_url = gemini_base_url.rstrip("/")
        self.urlopen = urlopen or urllib.request.urlopen
        if self.provider == "gemini" and not self.gemini_api_key:
            raise RuntimeError("live SkillOpt provider 'gemini' requires GEMINI_API_KEY")
        if self.provider == "codex" and not self.codex_bin:
            raise RuntimeError("live SkillOpt provider 'codex' requires codex CLI")
        if self.provider == "auto" and not self.codex_bin and not self.gemini_api_key:
            raise RuntimeError("live SkillOpt provider 'auto' requires codex CLI or GEMINI_API_KEY")
        self.gemini_model = gemini_model or os.environ.get("SKILLOPT_GEMINI_MODEL")
        self.timeout = max(timeout, CODEX_MIN_TIMEOUT_SEC) if self.provider in {"codex", "auto"} else timeout
        self.last_tool_calls: list[dict[str, Any]] = []

    def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
        self.last_tool_calls = []
        prompt = (
            "Follow the SYSTEM instructions below. Do not edit files, run tools, "
            "or perform side effects. Return only the requested final answer.\n\n"
            f"SYSTEM:\n{system}\n\nUSER:\n{user}\n"
        )
        errors: list[str] = []
        if self.provider == "gemini":
            try:
                return self._gemini_api_chat(model=model, prompt=prompt, max_tokens=max_tokens)
            except Exception as exc:
                raise RuntimeError(f"live SkillOpt Gemini API call failed: {exc}") from exc
        if self.provider in {"codex", "auto"} and self.codex_bin:
            try:
                return self._codex_chat(model=model, prompt=prompt, output_schema=_schema_for_system(system))
            except Exception as exc:  # fallback path intentionally records both failures.
                errors.append(f"codex: {exc}")
                if self.provider == "codex":
                    raise RuntimeError("live SkillOpt CLI calls failed: " + " | ".join(errors))
        if self.provider == "auto" and self.gemini_api_key:
            try:
                return self._gemini_api_chat(model=self.gemini_model or model, prompt=prompt, max_tokens=max_tokens)
            except Exception as exc:
                errors.append(f"gemini: {exc}")
        raise RuntimeError("live SkillOpt CLI calls failed: " + " | ".join(errors))

    def chat_json_object(
        self,
        *,
        model: str,
        system: str,
        user: str,
        max_tokens: int,
        schema: dict[str, Any],
        filename: str,
    ) -> dict[str, Any]:
        self.last_tool_calls = []
        if self.provider == "gemini":
            prompt = (
                "Follow the SYSTEM instructions below. Do not edit repo files, run tools, "
                "or perform side effects. Return exactly one JSON object matching the "
                "supplied schema, with no Markdown fence, prose, or second JSON object.\n\n"
                f"SYSTEM:\n{system}\n\nUSER:\n{user}\n"
            )
        else:
            prompt = (
                "Follow the SYSTEM instructions below. Do not edit repo files, run tools, "
                "or perform side effects. The final answer will be written by the CLI to "
                f"`{filename}`; make that file contain exactly one JSON object matching "
                "the supplied schema, with no Markdown fence, prose, or second JSON object.\n\n"
                f"SYSTEM:\n{system}\n\nUSER:\n{user}\n"
            )
        errors: list[str] = []
        if self.provider == "gemini":
            try:
                return self._gemini_api_json_object(
                    model=model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                raise RuntimeError(f"live SkillOpt Gemini API JSON call failed: {exc}") from exc
        if self.provider in {"codex", "auto"} and self.codex_bin:
            try:
                return self._codex_json_object(
                    model=model,
                    prompt=prompt,
                    output_schema=schema,
                    filename=filename,
                )
            except Exception as exc:
                errors.append(f"codex: {exc}")
                if self.provider == "codex":
                    raise RuntimeError("live SkillOpt JSON CLI calls failed: " + " | ".join(errors))
        if self.provider == "auto" and self.gemini_api_key:
            try:
                return self._gemini_api_json_object(
                    model=self.gemini_model or model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                errors.append(f"gemini: {exc}")
        raise RuntimeError("live SkillOpt JSON CLI calls failed: " + " | ".join(errors))

    def _gemini_api_json_object(self, *, model: str, prompt: str, max_tokens: int) -> dict[str, Any]:
        token_attempts = [max_tokens, max(max_tokens * 2, max_tokens + 1)]
        for index, token_budget in enumerate(token_attempts):
            raw = self._gemini_api_chat(
                model=model,
                prompt=prompt,
                max_tokens=token_budget,
                response_mime_type="application/json",
            )
            try:
                return _extract_json_object(raw)
            except json.JSONDecodeError:
                if index + 1 == len(token_attempts):
                    raise
        raise RuntimeError("unreachable Gemini JSON retry state")

    def _codex_chat(self, *, model: str, prompt: str, output_schema: dict[str, Any] | None = None) -> str:
        with tempfile.TemporaryDirectory(prefix="skillopt-codex-") as tmp:
            out = Path(tmp) / "last-message.txt"
            cmd = [
                self.codex_bin or "codex",
                "exec",
                "-m",
                model,
                "--sandbox",
                "read-only",
                "--ignore-rules",
                "--ignore-user-config",
                "--ephemeral",
                "--json",
                "--output-last-message",
                str(out),
            ]
            if output_schema is not None:
                schema_path = Path(tmp) / "output-schema.json"
                schema_path.write_text(json.dumps(output_schema, indent=2, sort_keys=True), encoding="utf-8")
                cmd.extend(["--output-schema", str(schema_path)])
            cmd.append("-")
            result = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}")
            self.last_tool_calls = _extract_codex_tool_calls(result.stdout)
            text = out.read_text(encoding="utf-8") if out.exists() else result.stdout
            return text.strip()

    def _codex_json_object(
        self,
        *,
        model: str,
        prompt: str,
        output_schema: dict[str, Any],
        filename: str,
    ) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="skillopt-codex-json-") as tmp:
            out = Path(tmp) / filename
            schema_path = Path(tmp) / "output-schema.json"
            schema_path.write_text(json.dumps(output_schema, indent=2, sort_keys=True), encoding="utf-8")
            cmd = [
                self.codex_bin or "codex",
                "exec",
                "-m",
                model,
                "--sandbox",
                "read-only",
                "--ignore-rules",
                "--ignore-user-config",
                "--ephemeral",
                "--json",
                "--output-last-message",
                str(out),
                "--output-schema",
                str(schema_path),
                "-",
            ]
            result = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}")
            self.last_tool_calls = _extract_codex_tool_calls(result.stdout)
            return _load_json_object(out)

    def _gemini_api_chat(
        self,
        *,
        model: str,
        prompt: str,
        max_tokens: int,
        response_mime_type: str | None = None,
    ) -> str:
        if not self.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        endpoint = (
            f"{self.gemini_base_url}/models/{urllib.parse.quote(model, safe='')}:generateContent"
            f"?key={urllib.parse.quote(self.gemini_api_key, safe='')}"
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
            },
            "toolConfig": {
                "functionCallingConfig": {
                    "mode": "NONE",
                },
            },
        }
        if response_mime_type is not None:
            payload["generationConfig"]["responseMimeType"] = response_mime_type
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(body or f"HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc
        self.last_tool_calls = []
        return _extract_gemini_api_text(data)


def run_live_skillopt(
    *,
    root: Path,
    skill_name: str,
    models: LiveModels,
    chat_client: ChatClient,
    split_ratio: tuple[int, int, int] = (1, 1, 1),
    bootstrap_reviewed: bool = False,
    epochs: int = 1,
    batch_size: int = 4,
    lr: int = 4,
    max_runtime_sec: int = 600,
    max_llm_calls: int | None = None,
    no_mutate: bool = True,
    held_out_path: Path | None = None,
    epsilon: float = core.VALIDATION_EPSILON,
) -> dict[str, Any]:
    started = time.time()
    skill_file = _skill_path(root, skill_name)
    benchmark_file = _benchmark_path(root, skill_name)
    baseline_text = skill_file.read_text(encoding="utf-8")
    tasks = core.load_benchmark(benchmark_file, bootstrap_reviewed=bootstrap_reviewed)
    split = core.split_benchmark(tasks, split_ratio)
    held_out_tasks = _load_held_out_tasks(held_out_path, tasks) if held_out_path is not None else []
    current_best = baseline_text
    if not no_mutate and not held_out_tasks:
        raise ValueError("live --mutate requires a held-out live gate")
    budget = LiveBudget(max_calls=max_llm_calls)
    metered_client = BudgetedChatClient(chat_client, budget)
    lock_path = _acquire_lock(root, skill_name)
    trace: list[dict[str, Any]] = []
    held_out_gate = None
    try:
        _write_checkpoint(root, skill_name, {"state": "started", "skill": skill_name})
        baseline_gate = _live_validation_gate(
            chat_client=metered_client,
            skill_text=current_best,
            tasks=split.sel,
            target_model=models.target,
            judge_model=models.judge,
            best_score=-1.0,
            runs_per_task=3,
            epsilon=epsilon,
        )
        best_score = baseline_gate["sel_score"]
        trace.append({"event": "baseline_validation", "sel_score": best_score, "tasks": [row["task_id"] for row in split.sel]})
        accepted = False
        candidate_text = current_best
        last_gate = baseline_gate
        rejected_reason = "no_improvement"
        rejected_edits: list[dict[str, Any]] = []

        for epoch in range(1, epochs + 1):
            _check_deadline(started, max_runtime_sec)
            _write_checkpoint(root, skill_name, {"state": "epoch", "epoch": epoch, "best_score": best_score})
            batch = split.train[: max(1, min(batch_size, len(split.train)))]
            forward = _score_rollouts_once(metered_client, current_best, batch, models.target, models.judge)
            edits = _reflect_edits(
                chat_client=metered_client,
                optimizer_model=models.optimizer,
                skill_text=current_best,
                scored_rollouts=forward,
                criteria=_describe_judges(tasks),
                rejected_edits=rejected_edits,
            )
            trace.append({
                "event": "reflect",
                "epoch": epoch,
                "failure_ids": [row["task_id"] for row in forward if row["score"] < 0.5],
                "success_ids": [row["task_id"] for row in forward if row["score"] >= 0.5],
                "rejected_buffer_size": len(rejected_edits),
                "edits_proposed": len(edits),
            })
            candidate_text, applied = _apply_edits(current_best, edits[: max(1, lr)])
            trace.append({"event": "candidate_generated", "epoch": epoch, "edits_applied": len(applied)})
            if candidate_text == current_best:
                rejected_reason = "no_edits_applied"
                rejected_edits.extend(_rejected_edit_records(edits, rejected_reason, epoch))
                trace.append({"event": "rejected_candidate", "epoch": epoch, "reason": rejected_reason})
                continue
            gate = _live_validation_gate(
                chat_client=metered_client,
                skill_text=candidate_text,
                tasks=split.sel,
                target_model=models.target,
                judge_model=models.judge,
                best_score=best_score,
                runs_per_task=3,
                epsilon=epsilon,
            )
            last_gate = gate
            trace.append({"event": "candidate_validation", "epoch": epoch, "sel_score": gate["sel_score"], "accepted": gate["accepted"]})
            if gate["accepted"]:
                accepted = True
                current_best = candidate_text
                best_score = gate["sel_score"]
                break
            rejected_reason = gate["reason"]
            task_signal = _task_signal(baseline_gate, gate)
            rejected_edits.extend(_rejected_edit_records(applied or edits, rejected_reason, epoch, task_signal=task_signal))
            trace.append({"event": "rejected_candidate", "epoch": epoch, "reason": rejected_reason, "task_signal": task_signal})

        if accepted and held_out_tasks:
            baseline_held_out = _live_validation_gate(
                chat_client=metered_client,
                skill_text=baseline_text,
                tasks=held_out_tasks,
                target_model=models.target,
                judge_model=models.judge,
                best_score=-1.0,
                runs_per_task=3,
                epsilon=epsilon,
            )
            candidate_held_out = _live_validation_gate(
                chat_client=metered_client,
                skill_text=current_best,
                tasks=held_out_tasks,
                target_model=models.target,
                judge_model=models.judge,
                best_score=baseline_held_out["sel_score"],
                runs_per_task=3,
                epsilon=epsilon,
            )
            held_out_gate = {
                "baseline_sel_score": baseline_held_out["sel_score"],
                "candidate_sel_score": candidate_held_out["sel_score"],
                "accepted": candidate_held_out["accepted"],
                "baseline_gate": baseline_held_out,
                "candidate_gate": candidate_held_out,
            }
            trace.append({
                "event": "held_out_validation",
                "baseline_sel_score": held_out_gate["baseline_sel_score"],
                "candidate_sel_score": held_out_gate["candidate_sel_score"],
                "accepted": held_out_gate["accepted"],
            })
            if not candidate_held_out["accepted"]:
                accepted = False
                rejected_reason = "held_out_regression"
                last_gate = {**last_gate, "accepted": False, "reason": rejected_reason, "held_out": held_out_gate}

        test_score = None
        test_gate = None
        if accepted and split.test:
            test_gate = _live_validation_gate(
                chat_client=metered_client,
                skill_text=current_best,
                tasks=split.test,
                target_model=models.target,
                judge_model=models.judge,
                best_score=-1.0,
                runs_per_task=3,
                epsilon=epsilon,
            )
            test_score = test_gate["sel_score"]
            trace.append({"event": "final_test", "test_score": test_score})

        run_id = _run_id(skill_name, current_best)
        mutated = False
        if accepted and not no_mutate:
            try:
                skill_file.write_text(current_best, encoding="utf-8")
            except OSError:
                _write_checkpoint(root, skill_name, {"state": "mutation_failed", "run_id": run_id})
                raise
            mutated = True
        paths = _write_artifacts(
            root,
            skill_name,
            run_id=run_id,
            candidate=current_best,
            outcome="accepted" if accepted else "no_improvement",
            gate=last_gate,
            trace=trace,
            no_mutate=no_mutate,
            rejected_edits=rejected_edits,
            held_out=held_out_gate,
            llm_calls=budget.calls,
            models=models,
            split=split,
            benchmark_file=benchmark_file,
            baseline_gate=baseline_gate,
            baseline_score=baseline_gate["sel_score"],
            test_gate=test_gate,
            test_score=test_score,
        )
        if accepted and no_mutate:
            (_skill_dir(root, skill_name) / "proposed.md").write_text(current_best, encoding="utf-8")
        _write_checkpoint(root, skill_name, {"state": "completed", "run_id": run_id, "outcome": "accepted" if accepted else "no_improvement"})

        return {
            "outcome": "accepted" if accepted else "no_improvement",
            "reason": None if accepted else rejected_reason,
            "run_id": run_id,
            "mode": "live_closed_loop",
            "baseline_sel_score": baseline_gate["sel_score"],
            "best_sel_score": best_score,
            "test_score": test_score,
            "held_out": held_out_gate,
            "llm_calls": budget.calls,
            "mutated_skill_file": mutated,
            "files_written": paths,
            "trace": trace,
        }
    finally:
        _release_lock(lock_path)


def _live_validation_gate(
    *,
    chat_client: ChatClient,
    skill_text: str,
    tasks: list[dict[str, Any]],
    target_model: str,
    judge_model: str | None,
    best_score: float,
    runs_per_task: int,
    epsilon: float,
) -> dict[str, Any]:
    rollouts: dict[str, list[Any]] = {}
    for task in tasks:
        rollouts[task["task_id"]] = [
            _run_rollout(chat_client, skill_text, task, target_model)
            for _ in range(runs_per_task)
        ]
    return _score_rollout_records(tasks, rollouts, judge_model=judge_model, chat_client=chat_client, best_score=best_score, epsilon=epsilon)


def _score_rollouts_once(
    chat_client: ChatClient,
    skill_text: str,
    tasks: list[dict[str, Any]],
    target_model: str,
    judge_model: str | None,
) -> list[dict[str, Any]]:
    out = []
    for task in tasks:
        trajectory = _run_rollout(chat_client, skill_text, task, target_model)
        score = _score_one(task, trajectory, judge_model=judge_model, chat_client=chat_client)
        out.append({"task_id": task["task_id"], "task": task["task"], "trajectory": trajectory, "score": score})
    return out


def _run_rollout(chat_client: ChatClient, skill_text: str, task: dict[str, Any], target_model: str) -> dict[str, Any]:
    contract = _rule_contract(task)
    system = skill_text if not contract else skill_text + "\n\n" + contract["system"]
    user = task["task"] if not contract else task["task"] + "\n\n" + contract["user"]
    final_text = chat_client.chat(
        model=target_model,
        system=system,
        user=user,
        max_tokens=1200,
    )
    tool_calls = _last_tool_calls(chat_client)
    contract_detail = _contract_detail(task, final_text, tool_calls)
    if contract_detail is not None and contract_detail["final_score"] < 1.0:
        repaired = chat_client.chat(
            model=target_model,
            system=_repair_system(skill_text),
            user=_repair_user(task, final_text, contract_detail),
            max_tokens=1200,
        )
        repaired_tool_calls = _last_tool_calls(chat_client)
        combined_tool_calls = tool_calls + repaired_tool_calls
        repaired_detail = _contract_detail(task, repaired, combined_tool_calls)
        if repaired_detail is not None:
            final_text = repaired
            tool_calls = combined_tool_calls
            contract_detail = {
                **repaired_detail,
                "status": "repaired" if repaired_detail["final_score"] >= 1.0 else "repair_failed",
                "attempts": 1,
                "initial_score": contract_detail["final_score"],
                "initial_missing": contract_detail["missing"],
            }
    return {"final_text": final_text, "tool_calls": tool_calls, "contract": contract_detail}


def _rule_contract(task: dict[str, Any]) -> dict[str, str] | None:
    judge = task.get("judge")
    if not isinstance(judge, dict) or judge.get("kind") != "rule":
        return None
    checks = judge.get("checks")
    if not isinstance(checks, list) or not checks:
        return None
    lines = _describe_rule_checks(checks)
    return {
        "system": (
            "Deterministic contract: answer naturally in Markdown, but satisfy "
            "the benchmark contract below exactly where it requires literal "
            "phrases, sections, tools, or limits."
        ),
        "user": "Benchmark contract:\n" + "\n".join(lines),
    }


def _describe_rule_checks(checks: list[dict[str, Any]]) -> list[str]:
    lines = []
    for check in checks:
        if check["op"] == "mapping_contains":
            lines.append("- mapping_contains: include these key -> value mappings in Markdown:")
            items = [
                {"key": item["key"], "value": item["expected"]}
                for item in check.get("items", [])
                if not item.get("passed")
            ] or check["arg"]["items"]
            for item in items:
                lines.append(f"  - {item['key']} -> {item['value']}")
        else:
            lines.append(f"- {check['op']}: {check['arg']}")
    return lines


def _contract_detail(task: dict[str, Any], final_text: str, tool_calls: list[dict[str, Any]]) -> dict[str, Any] | None:
    judge = task.get("judge")
    if not isinstance(judge, dict) or judge.get("kind") != "rule":
        return None
    detail = core.score_rule_detail(final_text, tool_calls, judge["checks"])
    missing = [check for check in detail["checks"] if not check["passed"]]
    return {
        "status": "passed" if not missing else "contract_violation",
        "attempts": 0,
        "final_score": detail["score"],
        "checks": detail["checks"],
        "missing": missing,
    }


def _repair_system(skill_text: str) -> str:
    return (
        skill_text
        + "\n\nRepair the answer so it satisfies the deterministic benchmark contract. "
        "Preserve the original answer intent. Do not invent tool use or claim work not done. "
        "Return only the repaired final Markdown answer."
    )


def _repair_user(task: dict[str, Any], final_text: str, contract_detail: dict[str, Any]) -> str:
    missing = "\n".join(_describe_rule_checks(contract_detail["missing"]))
    return (
        f"Task:\n{task['task']}\n\n"
        f"Original answer:\n{final_text}\n\n"
        "Missing deterministic contract checks:\n"
        f"{missing}\n\n"
        "Repair the answer so those checks are satisfied exactly where literal text is required."
    )


def _score_rollout_records(
    tasks: list[dict[str, Any]],
    rollouts: dict[str, list[Any]],
    *,
    judge_model: str | None,
    chat_client: ChatClient,
    best_score: float,
    epsilon: float,
) -> dict[str, Any]:
    scored: dict[str, list[str]] = {}
    if all(task["judge"]["kind"] == "rule" for task in tasks):
        return core.validation_gate(tasks, rollouts, best_score=best_score, epsilon=epsilon)
    per_task = []
    for task in tasks:
        runs = []
        run_details = []
        records = rollouts.get(task["task_id"], [])
        if len(records) != 3:
            raise ValueError(f"task {task['task_id']} requires exactly 3 rollout records")
        for record in records:
            if task["judge"]["kind"] == "rule":
                final_text, tool_calls = core.normalize_rollout_record(record)
                detail = core.score_rule_detail(final_text, tool_calls, task["judge"]["checks"])
                detail["contract"] = record.get("contract") if isinstance(record, dict) else None
                detail.setdefault("contract_violation", any(not check["passed"] for check in detail["checks"]))
                runs.append(detail["score"])
                run_details.append(detail)
            else:
                runs.append(_score_one(task, record, judge_model=judge_model, chat_client=chat_client))
        row = {"task_id": task["task_id"], "median": core.median(runs), "runs": runs}
        if run_details:
            row["run_details"] = run_details
        per_task.append(row)
        scored[task["task_id"]] = [str(run) for run in runs]
    sel_score = sum(row["median"] for row in per_task) / len(per_task) if per_task else 0.0
    accepted = sel_score > best_score + epsilon
    return {
        "accepted": accepted,
        "sel_score": sel_score,
        "per_task_medians": per_task,
        "reason": None if accepted else ("below_baseline" if sel_score <= best_score else "no_margin"),
        "scored": scored,
    }


def _score_one(task: dict[str, Any], trajectory: dict[str, Any], *, judge_model: str | None, chat_client: ChatClient) -> float:
    judge = task["judge"]
    final_text = trajectory["final_text"]
    if judge["kind"] == "rule":
        return core.score_rule(final_text, trajectory.get("tool_calls", []), judge["checks"])
    if judge["kind"] != "llm":
        raise ValueError("live runner supports rule and llm judges")
    if not judge_model:
        raise ValueError("llm judge requires judge model")
    raw = chat_client.chat(
        model=judge_model,
        system="You are a strict SkillOpt judge. Return JSON only: {\"score\": number, \"rationale\": string}.",
        user=f"Rubric:\n{judge['rubric']}\n\nTask:\n{task['task']}\n\nOutput:\n{final_text}",
        max_tokens=500,
    )
    data = _parse_judge_response(raw)
    score = data["score"]
    return max(0.0, min(1.0, score))


def _reflect_edits(
    *,
    chat_client: ChatClient,
    optimizer_model: str,
    skill_text: str,
    scored_rollouts: list[dict[str, Any]],
    criteria: str,
    rejected_edits: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    body = core.split_frontmatter(skill_text)[1]
    failures = [row for row in scored_rollouts if row["score"] < 0.5]
    successes = [row for row in scored_rollouts if row["score"] >= 0.5]
    prompt = {
        "skill_body": body,
        "success_criteria": criteria,
        "failures": failures[:8],
        "successes": successes[:8],
        "rejected_edits": (rejected_edits or [])[-12:],
        "edit_schema": {
            "add": {"op": "add", "anchor": "heading or exact line", "content": "markdown", "reason": "why"},
            "replace": {"op": "replace", "target": "exact text", "replacement": "new text", "reason": "why"},
            "delete": {"op": "delete", "target": "exact text", "reason": "why"},
        },
    }
    system = (
        "You are SkillOpt's optimizer. Propose small body-only SKILL.md edits. "
        "Return JSON only: {\"edits\": [...]}."
    )
    schema = _schema_for_system(system) or {"type": "object"}
    json_client = getattr(chat_client, "chat_json_object", None)
    if callable(json_client):
        return _parse_optimizer_data(
            json_client(
                model=optimizer_model,
                system=system,
                user=json.dumps(prompt, ensure_ascii=False),
                max_tokens=1800,
                schema=schema,
                filename="optimizer-edits.json",
            )
        )
    raw = chat_client.chat(
        model=optimizer_model,
        system=system,
        user=json.dumps(prompt, ensure_ascii=False),
        max_tokens=1800,
    )
    return _parse_optimizer_response(raw)


def _apply_edits(skill_text: str, edits: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    current = skill_text
    applied = []
    for edit in edits:
        result = core.apply_edit(current, edit)
        if result["outcome"] == "applied":
            current = result["text"]
            applied.append(edit)
    return current, applied


def _rejected_edit_records(
    edits: list[dict[str, Any]],
    reason: str,
    epoch: int,
    *,
    task_signal: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    records = []
    for edit in edits:
        record = {"epoch": epoch, "reason": reason, "edit": edit}
        if task_signal is not None:
            record["task_signal"] = task_signal
        records.append(record)
    return records


def _task_signal(baseline_gate: dict[str, Any], candidate_gate: dict[str, Any]) -> dict[str, Any]:
    baseline = _task_median_map(baseline_gate)
    candidate = _task_median_map(candidate_gate)
    signal = {"improved": [], "regressed": [], "unchanged": []}
    for task_id in sorted(set(baseline) & set(candidate)):
        before = baseline[task_id]
        after = candidate[task_id]
        row = {"task_id": task_id, "before": before, "after": after}
        if after > before:
            signal["improved"].append(row)
        elif after < before:
            signal["regressed"].append(row)
        else:
            signal["unchanged"].append(row)
    return signal


def _task_median_map(gate: dict[str, Any]) -> dict[str, float]:
    out = {}
    rows = gate.get("per_task_medians")
    if not isinstance(rows, list):
        return out
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("task_id"), str) and isinstance(row.get("median"), (int, float)):
            out[row["task_id"]] = float(row["median"])
    return out


def _describe_judges(tasks: list[dict[str, Any]]) -> str:
    blocks = []
    seen = set()
    for task in tasks:
        judge = task["judge"]
        if judge["kind"] == "rule":
            desc = "\n".join(f"- {check['op']}: {check['arg']}" for check in judge["checks"])
        elif judge["kind"] == "llm":
            desc = f"- LLM rubric: {judge['rubric']}"
        else:
            desc = f"- Unsupported judge kind for live runner: {judge['kind']}"
        if desc not in seen:
            seen.add(desc)
            blocks.append(desc)
    return "\n".join(blocks)


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) < 3 or lines[-1].strip() != "```":
            raise ValueError("fenced JSON response must close the code fence")
        stripped = "\n".join(lines[1:-1])
        if stripped.splitlines()[0].strip().lower() == "json":
            stripped = "\n".join(stripped.splitlines()[1:])
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        if start == -1:
            raise
        data, end = json.JSONDecoder().raw_decode(stripped[start:])
        if stripped[start + end :].strip():
            raise ValueError("expected exactly one JSON object")
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def _extract_gemini_api_text(data: dict[str, Any]) -> str:
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Gemini API response did not include candidates")
    first = candidates[0]
    if not isinstance(first, dict):
        raise ValueError("Gemini API candidate must be an object")
    content = first.get("content")
    if not isinstance(content, dict):
        raise ValueError("Gemini API candidate did not include content; " + _gemini_candidate_diagnostics(first))
    parts = content.get("parts")
    if not isinstance(parts, list):
        raise ValueError("Gemini API content did not include parts")
    text_parts = [part.get("text") for part in parts if isinstance(part, dict) and isinstance(part.get("text"), str)]
    if not text_parts:
        raise ValueError("Gemini API response did not include text; " + _gemini_candidate_diagnostics(first))
    return "".join(text_parts).strip()


def _gemini_candidate_diagnostics(candidate: dict[str, Any]) -> str:
    return (
        f"finishReason={candidate.get('finishReason', 'unknown')}; "
        f"SAFETY={json.dumps(candidate.get('safetyRatings'), ensure_ascii=False)}"
    )


def _parse_judge_response(text: str) -> dict[str, Any]:
    data = _extract_json_object(text)
    score = data.get("score")
    rationale = data.get("rationale")
    if not isinstance(score, (int, float)):
        raise ValueError("judge response requires numeric score")
    if rationale is not None and not isinstance(rationale, str):
        raise ValueError("judge response rationale must be a string")
    return {"score": float(score), "rationale": rationale or ""}


def _parse_optimizer_response(text: str) -> list[dict[str, Any]]:
    return _parse_optimizer_data(_extract_json_object(text))


def _parse_optimizer_data(data: dict[str, Any]) -> list[dict[str, Any]]:
    edits = data.get("edits")
    if not isinstance(edits, list):
        raise ValueError("optimizer response requires edits list")
    parsed = []
    for index, edit in enumerate(edits):
        if not isinstance(edit, dict):
            raise ValueError(f"optimizer edit {index} must be an object")
        op = edit.get("op")
        if op not in {"add", "replace", "delete"}:
            raise ValueError(f"optimizer edit {index} has invalid op")
        if op == "add":
            if not isinstance(edit.get("anchor"), str) or not isinstance(edit.get("content"), str):
                raise ValueError(f"optimizer add edit {index} requires anchor and content")
        else:
            if not isinstance(edit.get("target"), str):
                raise ValueError(f"optimizer {op} edit {index} requires target")
            if op == "replace" and not isinstance(edit.get("replacement"), str):
                raise ValueError(f"optimizer replace edit {index} requires replacement")
        if edit.get("reason") is not None and not isinstance(edit["reason"], str):
            raise ValueError(f"optimizer edit {index} reason must be a string")
        parsed.append({key: value for key, value in edit.items() if value is not None})
    return parsed


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.name} must contain exactly one JSON object: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def _schema_for_system(system: str) -> dict[str, Any] | None:
    if "SkillOpt's optimizer" in system:
        edit_schema = {
            "type": "object",
            "required": ["op", "anchor", "content", "target", "replacement", "reason"],
            "properties": {
                "op": {"type": "string", "enum": ["add", "replace", "delete"]},
                "anchor": {"type": ["string", "null"]},
                "content": {"type": ["string", "null"]},
                "target": {"type": ["string", "null"]},
                "replacement": {"type": ["string", "null"]},
                "reason": {"type": ["string", "null"]},
            },
            "additionalProperties": False,
        }
        return {
            "type": "object",
            "required": ["edits"],
            "properties": {"edits": {"type": "array", "items": edit_schema}},
            "additionalProperties": False,
        }
    if "strict SkillOpt judge" in system:
        return {
            "type": "object",
            "required": ["score", "rationale"],
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 1},
                "rationale": {"type": "string"},
            },
            "additionalProperties": False,
        }
    return None


def _last_tool_calls(chat_client: ChatClient) -> list[dict[str, Any]]:
    calls = getattr(chat_client, "last_tool_calls", [])
    if isinstance(calls, list) and all(isinstance(call, dict) for call in calls):
        return calls
    inner = getattr(chat_client, "inner", None)
    if inner is not None:
        return _last_tool_calls(inner)
    return []


def _extract_codex_tool_calls(stdout: str) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            calls.extend(_tool_calls_from_event(event))
    return calls


def _tool_calls_from_event(value: Any) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    if isinstance(value, dict):
        name = value.get("name") or value.get("tool_name")
        event_type = value.get("type") or value.get("event")
        tool_event_types = {
            "tool_call",
            "tool_call_delta",
            "tool_call_output",
            "function_call",
            "function_call_output",
        }
        if isinstance(name, str) and event_type in tool_event_types:
            calls.append({"name": name, "failed": bool(value.get("failed", False))})
        for child in value.values():
            calls.extend(_tool_calls_from_event(child))
    elif isinstance(value, list):
        for child in value:
            calls.extend(_tool_calls_from_event(child))
    return calls


def _write_artifacts(
    root: Path,
    skill_name: str,
    *,
    run_id: str,
    candidate: str,
    outcome: str,
    gate: dict[str, Any],
    trace: list[dict[str, Any]],
    no_mutate: bool,
    rejected_edits: list[dict[str, Any]] | None = None,
    held_out: dict[str, Any] | None = None,
    llm_calls: int | None = None,
    models: LiveModels | None = None,
    split: Any | None = None,
    benchmark_file: Path | None = None,
    baseline_gate: dict[str, Any] | None = None,
    baseline_score: float | None = None,
    test_gate: dict[str, Any] | None = None,
    test_score: float | None = None,
) -> list[str]:
    opt_dir = _skill_dir(root, skill_name) / "skillopt"
    versions = opt_dir / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    version = versions / f"v0001_{run_id}.md"
    version.write_text(candidate, encoding="utf-8")
    best = opt_dir / "best.md"
    written = [str(version)]
    if outcome == "accepted":
        best.write_text(candidate, encoding="utf-8")
        written.append(str(best))
    rejected_path = opt_dir / "rejected.json"
    rejected = []
    if rejected_path.exists():
        rejected = json.loads(rejected_path.read_text(encoding="utf-8"))
        if not isinstance(rejected, list):
            raise ValueError(f"{rejected_path} must contain a JSON list")
    if outcome != "accepted" or rejected_edits:
        rejected.append(
            {
                "run_id": run_id,
                "reason": gate.get("reason", "no_improvement"),
                "edits": rejected_edits or [],
            }
        )
        rejected_path.write_text(json.dumps(rejected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(str(rejected_path))
    trace_path = opt_dir / f"{run_id}.trace.json"
    trace_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written.append(str(trace_path))
    split_counts = None
    if split is not None:
        split_counts = {"train": len(split.train), "sel": len(split.sel), "test": len(split.test)}
    benchmark_sha = None
    if benchmark_file is not None:
        benchmark_sha = hashlib.sha256(benchmark_file.read_bytes()).hexdigest()
    receipt_path = opt_dir / f"{run_id}.receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "mode": "live_closed_loop",
                "outcome": outcome,
                "models": {
                    "target": models.target if models else None,
                    "optimizer": models.optimizer if models else None,
                    "judge": models.judge if models else None,
                },
                "split": split_counts,
                "benchmark_sha256": benchmark_sha,
                "candidate_sha256": hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
                "baseline_sel_score": baseline_score,
                "sel_score": gate["sel_score"],
                "test_score": test_score,
                "baseline_gate": baseline_gate,
                "validation_gate": gate,
                "test_gate": test_gate,
                "held_out": held_out,
                "rejected_edits": rejected_edits or [],
                "llm_calls": llm_calls,
                "trace": str(trace_path),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(str(receipt_path))
    history_path = opt_dir / "history.json"
    history = []
    if history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))
    history.append({
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_closed_loop",
        "outcome": outcome,
        "sel_score": gate["sel_score"],
        "no_mutate": no_mutate,
        "held_out": held_out,
        "llm_calls": llm_calls,
        "receipt": str(receipt_path),
        "trace": str(trace_path),
    })
    history_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written.append(str(history_path))
    return written


def _load_held_out_tasks(path: Path, benchmark_tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks = core.load_benchmark(path, bootstrap_reviewed=True)
    benchmark_ids = {row["task_id"] for row in benchmark_tasks}
    overlap = sorted(row["task_id"] for row in tasks if row["task_id"] in benchmark_ids)
    if overlap:
        sample = ", ".join(overlap[:3])
        raise ValueError(f"Held-out set shares {len(overlap)} task_id(s) with benchmark: {sample}")
    if len(tasks) < core.D_SEL_MIN_SIZE:
        raise ValueError(f"held-out live gate needs >= {core.D_SEL_MIN_SIZE} task(s)")
    return tasks


def _acquire_lock(root: Path, skill_name: str) -> Path:
    opt_dir = _skill_dir(root, skill_name) / "skillopt"
    opt_dir.mkdir(parents=True, exist_ok=True)
    lock_path = opt_dir / ".skillopt-live.lock"
    try:
        with lock_path.open("x", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "skill": skill_name,
                        "pid": os.getpid(),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    except FileExistsError as exc:
        raise RuntimeError(f"active live SkillOpt run already exists: {lock_path}") from exc
    return lock_path


def _release_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def _write_checkpoint(root: Path, skill_name: str, payload: dict[str, Any]) -> None:
    opt_dir = _skill_dir(root, skill_name) / "skillopt"
    opt_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = {**payload, "updated_at": datetime.now(timezone.utc).isoformat()}
    (opt_dir / "live-checkpoint.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _check_deadline(started: float, max_runtime_sec: int) -> None:
    if time.time() - started > max_runtime_sec:
        raise TimeoutError(f"live SkillOpt exceeded max runtime {max_runtime_sec}s")


def _skill_dir(root: Path, skill_name: str) -> Path:
    return root / ".codex" / "skills" / skill_name


def _skill_path(root: Path, skill_name: str) -> Path:
    return _skill_dir(root, skill_name) / "SKILL.md"


def _benchmark_path(root: Path, skill_name: str) -> Path:
    return _skill_dir(root, skill_name) / "skillopt-benchmark.jsonl"


def _run_id(skill_name: str, text: str) -> str:
    return f"{skill_name}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}"
