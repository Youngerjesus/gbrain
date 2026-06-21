#!/usr/bin/env python3
"""Codex-native SkillOpt runner.

This runner preserves the gbrain SkillOpt safety shape for both deterministic
candidate evidence and the live Codex/Gemini closed loop. It bootstraps
benchmarks, validates reviewed benchmark splits, dispatches live runs, and keeps
promotion behind validation and held-out gates.

Kept in one file despite the repo's line-count pressure because skill scripts
are one-hop standalone helpers; splitting the CLI would add import surface
without changing the public contract.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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

DEFAULT_PROVIDER = "gemini"
DEFAULT_GEMINI_TARGET_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_OPTIMIZER_MODEL = "gemini-3.5-flash"
DEFAULT_CODEX_TARGET_MODEL = "gpt-5.3-codex-spark"
DEFAULT_CODEX_OPTIMIZER_MODEL = "gpt-5.5"
LIVE_PROVIDERS = ("gemini", "codex", "auto")


def skill_dir(root: Path, skill_name: str) -> Path:
    return root / ".codex" / "skills" / skill_name


def skill_path(root: Path, skill_name: str) -> Path:
    return skill_dir(root, skill_name) / "SKILL.md"


def benchmark_path(root: Path, skill_name: str) -> Path:
    return skill_dir(root, skill_name) / "skillopt-benchmark.jsonl"


def bootstrap_from_skill(root: Path, skill_name: str, *, task_count: int = 15, force: bool = False) -> dict[str, Any]:
    path = skill_path(root, skill_name)
    if not path.is_file():
        raise FileNotFoundError(f"missing skill file: {path}")
    out = benchmark_path(root, skill_name)
    if out.exists() and not force:
        raise FileExistsError(f"benchmark already exists: {out}")
    task_count = max(1, min(task_count, 50))
    skill_text = path.read_text(encoding="utf-8")
    title = _first_heading(skill_text) or skill_name
    rows = [_bootstrap_row(skill_name, title, index) for index in range(1, task_count + 1)]
    out.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
        + "\n"
        + core.BOOTSTRAP_PENDING_REVIEW
        + "\n",
        encoding="utf-8",
    )
    return {"status": "bootstrapped", "skill": skill_name, "benchmark": str(out), "tasks": len(rows)}


def dry_run(
    root: Path,
    skill_name: str,
    *,
    split_ratio: tuple[int, int, int] = (1, 1, 1),
    bootstrap_reviewed: bool = False,
) -> dict[str, Any]:
    tasks = core.load_benchmark(benchmark_path(root, skill_name), bootstrap_reviewed=bootstrap_reviewed)
    split = core.split_benchmark(tasks, split_ratio)
    return {
        "outcome": "aborted",
        "reason": "dry_run",
        "skill": skill_name,
        "benchmark_tasks": len(tasks),
        "split": {"train": len(split.train), "sel": len(split.sel), "test": len(split.test)},
        "live_adapter_required": True,
        "candidate_input": "--candidate and --rollouts are required for a deterministic local run",
    }


def run_with_candidate(
    root: Path,
    skill_name: str,
    *,
    candidate_path: Path,
    rollouts_path: Path,
    held_out_path: Path | None = None,
    held_out_rollouts_path: Path | None = None,
    split_ratio: tuple[int, int, int] = (1, 1, 1),
    bootstrap_reviewed: bool = False,
    no_mutate: bool = True,
    baseline_score: float | None = None,
    epsilon: float = core.VALIDATION_EPSILON,
) -> dict[str, Any]:
    current_path = skill_path(root, skill_name)
    current = current_path.read_text(encoding="utf-8")
    candidate = candidate_path.read_text(encoding="utf-8")
    _assert_body_only_candidate(current, candidate)
    if not no_mutate and (held_out_path is None or held_out_rollouts_path is None):
        raise ValueError("--mutate requires --held-out and --held-out-rollouts")
    if baseline_score is None:
        raise ValueError("candidate validation requires an explicit baseline_score")

    tasks = core.load_benchmark(benchmark_path(root, skill_name), bootstrap_reviewed=bootstrap_reviewed)
    split = core.split_benchmark(tasks, split_ratio)
    rollouts = _load_json_object(rollouts_path)
    gate = core.validation_gate(split.sel, rollouts, best_score=baseline_score, epsilon=epsilon)
    held_out_gate = None
    if gate["accepted"] and held_out_path is not None:
        if held_out_rollouts_path is None:
            raise ValueError("--held-out-rollouts is required with --held-out")
        held_out_tasks = core.load_benchmark(held_out_path, bootstrap_reviewed=True)
        _assert_held_out_disjoint(tasks, held_out_tasks)
        held_out_rollouts = _load_json_object(held_out_rollouts_path)
        held_out_gate = core.validation_gate(held_out_tasks, held_out_rollouts, best_score=baseline_score, epsilon=epsilon)
        if not held_out_gate["accepted"]:
            gate = {
                **gate,
                "accepted": False,
                "reason": "held_out_regression",
                "held_out": held_out_gate,
            }
    run_id = _run_id(skill_name, candidate)
    paths = _write_version_artifacts(
        root,
        skill_name,
        run_id=run_id,
        candidate=candidate,
        outcome="accepted" if gate["accepted"] else "no_improvement",
        gate=gate,
        no_mutate=no_mutate,
    )
    mutated = False
    if gate["accepted"] and not no_mutate:
        current_path.write_text(candidate, encoding="utf-8")
        mutated = True
    elif gate["accepted"]:
        (skill_dir(root, skill_name) / "proposed.md").write_text(candidate, encoding="utf-8")
    return {
        "outcome": "accepted" if gate["accepted"] else "no_improvement",
        "reason": None if gate["accepted"] else gate["reason"],
        "run_id": run_id,
        "baseline_sel_score": baseline_score,
        "best_sel_score": gate["sel_score"] if gate["accepted"] else baseline_score,
        "candidate_sel_score": gate["sel_score"],
        "held_out": held_out_gate,
        "mutated_skill_file": mutated,
        "files_written": paths,
        "validation_gate": gate,
    }


def run_proxy_candidate(
    root: Path,
    skill_name: str,
    *,
    candidate_path: Path,
    baseline_skill_path: Path | None = None,
    split_ratio: tuple[int, int, int] = (1, 1, 1),
    bootstrap_reviewed: bool = False,
    no_mutate: bool = True,
    epsilon: float = core.VALIDATION_EPSILON,
) -> dict[str, Any]:
    current_path = skill_path(root, skill_name)
    current = current_path.read_text(encoding="utf-8")
    baseline = baseline_skill_path.read_text(encoding="utf-8") if baseline_skill_path else current
    candidate = candidate_path.read_text(encoding="utf-8")
    _assert_body_only_candidate(baseline, candidate)
    if not no_mutate:
        raise ValueError("--mutate requires live or external held-out rollout evidence")

    tasks = core.load_benchmark(benchmark_path(root, skill_name), bootstrap_reviewed=bootstrap_reviewed)
    split = core.split_benchmark(tasks, split_ratio)
    baseline_gate = _score_text_on_tasks(split.sel, baseline, best_score=-1.0, epsilon=epsilon)
    candidate_gate = _score_text_on_tasks(split.sel, candidate, best_score=baseline_gate["sel_score"], epsilon=epsilon)
    test_gate = _score_text_on_tasks(split.test, candidate, best_score=-1.0, epsilon=epsilon) if split.test else None
    run_id = _run_id(skill_name, candidate)
    paths = _write_version_artifacts(
        root,
        skill_name,
        run_id=run_id,
        candidate=candidate,
        outcome="accepted" if candidate_gate["accepted"] else "no_improvement",
        gate=candidate_gate,
        no_mutate=no_mutate,
    )
    if candidate_gate["accepted"]:
        (skill_dir(root, skill_name) / "proposed.md").write_text(candidate, encoding="utf-8")
    return {
        "outcome": "accepted" if candidate_gate["accepted"] else "no_improvement",
        "reason": None if candidate_gate["accepted"] else candidate_gate["reason"],
        "run_id": run_id,
        "mode": "proxy_from_skill_text",
        "baseline_sel_score": baseline_gate["sel_score"],
        "candidate_sel_score": candidate_gate["sel_score"],
        "best_sel_score": candidate_gate["sel_score"] if candidate_gate["accepted"] else baseline_gate["sel_score"],
        "test_score": test_gate["sel_score"] if test_gate else None,
        "mutated_skill_file": False,
        "files_written": paths,
        "validation_gate": candidate_gate,
        "proxy_warning": "Rule checks were scored against skill text, not live task rollouts.",
    }


def _score_text_on_tasks(tasks: list[dict[str, Any]], text: str, *, best_score: float, epsilon: float) -> dict[str, Any]:
    return core.validation_gate(
        tasks,
        {row["task_id"]: [text, text, text] for row in tasks},
        best_score=best_score,
        epsilon=epsilon,
    )


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _bootstrap_row(skill_name: str, title: str, index: int) -> dict[str, Any]:
    task_id = f"{skill_name}-{index:03d}"
    return {
        "task_id": task_id,
        "task": f"Use {title} on representative scenario {index}.",
        "judge": {
            "kind": "rule",
            "checks": [
                {"op": "max_chars", "arg": 1800},
                {"op": "contains", "arg": "task"},
                {"op": "contains", "arg": "answer"},
                {"op": "contains", "arg": "next step"},
            ],
        },
        "category": "bootstrap_draft",
        "review_note": "BOOTSTRAP DRAFT: replace generic checks with skill-specific quality signals before deleting the sentinel.",
    }


def _assert_body_only_candidate(current: str, candidate: str) -> None:
    current_frontmatter, _ = core.split_frontmatter(current)
    candidate_frontmatter, _ = core.split_frontmatter(candidate)
    if current_frontmatter != candidate_frontmatter:
        raise ValueError("candidate must preserve SKILL.md frontmatter exactly")


def _load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _assert_held_out_disjoint(benchmark_tasks: list[dict[str, Any]], held_out_tasks: list[dict[str, Any]]) -> None:
    benchmark_ids = {row["task_id"] for row in benchmark_tasks}
    overlap = sorted(row["task_id"] for row in held_out_tasks if row["task_id"] in benchmark_ids)
    if overlap:
        sample = ", ".join(overlap[:3])
        raise ValueError(f"Held-out set shares {len(overlap)} task_id(s) with benchmark: {sample}")


def _run_id(skill_name: str, candidate: str) -> str:
    digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:12]
    return f"{skill_name}-{digest}"


def _write_version_artifacts(
    root: Path,
    skill_name: str,
    *,
    run_id: str,
    candidate: str,
    outcome: str,
    gate: dict[str, Any],
    no_mutate: bool,
) -> list[str]:
    opt_dir = skill_dir(root, skill_name) / "skillopt"
    versions = opt_dir / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    best = opt_dir / "best.md"
    version = versions / f"v0001_{run_id}.md"
    version.write_text(candidate, encoding="utf-8")
    written = [str(version)]
    if outcome == "accepted":
        shutil.copyfile(version, best)
        written.append(str(best))
    rejected_path = opt_dir / "rejected.json"
    if outcome != "accepted":
        rejected_path.write_text(json.dumps([{"run_id": run_id, "reason": gate["reason"]}], indent=2) + "\n", encoding="utf-8")
        written.append(str(rejected_path))
    history_path = opt_dir / "history.json"
    history = []
    if history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))
        if not isinstance(history, list):
            raise ValueError(f"{history_path} must contain a JSON list")
    history.append(
        {
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "outcome": outcome,
            "sel_score": gate["sel_score"],
            "accepted": outcome == "accepted",
            "no_mutate": no_mutate,
            "validation_gate": gate,
        }
    )
    history_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written.append(str(history_path))
    return written


def _parse_split(value: str) -> tuple[int, int, int]:
    parts = tuple(int(part) for part in value.split(":"))
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("--split must be TRAIN:SEL:TEST")
    return parts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Codex SkillOpt bootstrap, dry-run, or candidate gate")
    parser.add_argument("skill")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--bootstrap-from-skill", action="store_true")
    parser.add_argument("--bootstrap-tasks", type=int, default=15)
    parser.add_argument("--bootstrap-reviewed", action="store_true")
    parser.add_argument("--split", type=_parse_split, default=(1, 1, 1))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--rollouts", type=Path)
    parser.add_argument("--proxy-from-skill-text", action="store_true")
    parser.add_argument("--baseline-skill", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--provider", choices=LIVE_PROVIDERS)
    parser.add_argument("--target-model")
    parser.add_argument("--optimizer-model")
    parser.add_argument("--judge-model")
    parser.add_argument("--gemini-model")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-runtime-sec", type=int, default=600)
    parser.add_argument("--max-llm-calls", type=int)
    parser.add_argument("--held-out", type=Path)
    parser.add_argument("--held-out-rollouts", type=Path)
    parser.add_argument("--baseline-score", type=float)
    parser.add_argument("--mutate", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.bootstrap_from_skill:
        result = bootstrap_from_skill(args.root, args.skill, task_count=args.bootstrap_tasks, force=args.force)
    elif args.dry_run:
        result = dry_run(args.root, args.skill, split_ratio=args.split, bootstrap_reviewed=args.bootstrap_reviewed)
    elif args.candidate and args.proxy_from_skill_text:
        result = run_proxy_candidate(
            args.root,
            args.skill,
            candidate_path=args.candidate,
            baseline_skill_path=args.baseline_skill,
            split_ratio=args.split,
            bootstrap_reviewed=args.bootstrap_reviewed,
            no_mutate=not args.mutate,
        )
    elif args.live:
        provider = _resolve_provider(args.provider)
        model_defaults = _resolve_live_model_defaults(args, provider)
        live = _load_live_module()
        result = live.run_live_skillopt(
            root=args.root,
            skill_name=args.skill,
            models=live.LiveModels(
                target=model_defaults["target"],
                optimizer=model_defaults["optimizer"],
                judge=model_defaults["judge"],
            ),
            chat_client=live.CliChatClient(
                provider=provider,
                gemini_model=model_defaults["client_gemini_model"],
            ),
            split_ratio=args.split,
            bootstrap_reviewed=args.bootstrap_reviewed,
            epochs=args.epochs,
            batch_size=args.batch_size,
            max_runtime_sec=args.max_runtime_sec,
            max_llm_calls=args.max_llm_calls,
            no_mutate=not args.mutate,
            held_out_path=args.held_out,
        )
    elif args.candidate and args.rollouts:
        result = run_with_candidate(
            args.root,
            args.skill,
            candidate_path=args.candidate,
            rollouts_path=args.rollouts,
            held_out_path=args.held_out,
            held_out_rollouts_path=args.held_out_rollouts,
            split_ratio=args.split,
            bootstrap_reviewed=args.bootstrap_reviewed,
            no_mutate=not args.mutate,
            baseline_score=args.baseline_score,
        )
    else:
        raise SystemExit("choose --bootstrap-from-skill, --dry-run, --candidate with --proxy-from-skill-text, or --candidate with --rollouts")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result.get("status") == "bootstrapped" or result.get("reason") == "dry_run":
        return 0
    return 0 if result.get("outcome") == "accepted" else 2


def _load_live_module():
    live_path = Path(__file__).with_name("skillopt_live.py")
    spec = importlib.util.spec_from_file_location("skillopt_live", live_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load live SkillOpt module at {live_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _resolve_provider(flag_value: str | None) -> str:
    provider = flag_value or os.environ.get("SKILLOPT_PROVIDER") or DEFAULT_PROVIDER
    if provider not in LIVE_PROVIDERS:
        raise ValueError(f"unsupported live provider {provider!r}; choose one of {', '.join(LIVE_PROVIDERS)}")
    return provider


def _resolve_live_model_defaults(args: argparse.Namespace, provider: str) -> dict[str, str | None]:
    env_target = os.environ.get("SKILLOPT_TARGET_MODEL")
    env_optimizer = os.environ.get("SKILLOPT_OPTIMIZER_MODEL")
    env_judge = os.environ.get("SKILLOPT_JUDGE_MODEL")
    single_gemini_model = args.gemini_model or os.environ.get("SKILLOPT_GEMINI_MODEL")

    if provider == "gemini":
        target_default = single_gemini_model or DEFAULT_GEMINI_TARGET_MODEL
        optimizer_default = single_gemini_model or DEFAULT_GEMINI_OPTIMIZER_MODEL
        client_gemini_model = None
    elif provider == "codex":
        target_default = DEFAULT_CODEX_TARGET_MODEL
        optimizer_default = DEFAULT_CODEX_OPTIMIZER_MODEL
        client_gemini_model = None
    else:
        target_default = DEFAULT_CODEX_TARGET_MODEL
        optimizer_default = DEFAULT_CODEX_OPTIMIZER_MODEL
        client_gemini_model = single_gemini_model or DEFAULT_GEMINI_TARGET_MODEL

    target_model = args.target_model or env_target or target_default
    optimizer_model = args.optimizer_model or env_optimizer or optimizer_default
    judge_model = args.judge_model or env_judge or target_model
    return {
        "target": target_model,
        "optimizer": optimizer_model,
        "judge": judge_model,
        "client_gemini_model": client_gemini_model,
    }


if __name__ == "__main__":
    raise SystemExit(main())
