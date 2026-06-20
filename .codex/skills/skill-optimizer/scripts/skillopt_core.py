#!/usr/bin/env python3
"""Standalone deterministic SkillOpt helper.

This stays in one file despite the repo's 220-line pressure because skill
scripts are loaded as one-hop standalone helpers; splitting the small core would
add import/reference surface before there is a live runner or provider adapter.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


BOOTSTRAP_PENDING_REVIEW = "# BOOTSTRAP_PENDING_REVIEW"
D_SEL_MIN_SIZE = 5
VALIDATION_EPSILON = 0.05


@dataclass(frozen=True)
class BenchmarkSplit:
    train: list[dict[str, Any]]
    sel: list[dict[str, Any]]
    test: list[dict[str, Any]]


def load_benchmark(path: Path, *, bootstrap_reviewed: bool = False) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    if lines and lines[-1].strip() == BOOTSTRAP_PENDING_REVIEW and not bootstrap_reviewed:
        raise ValueError("benchmark has BOOTSTRAP_PENDING_REVIEW sentinel")
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, line in enumerate(lines, start=1):
        if line.strip() == BOOTSTRAP_PENDING_REVIEW:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"row {index} is not JSON: {exc}") from exc
        validate_task(row, index)
        task_id = row["task_id"]
        if task_id in seen:
            raise ValueError(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        tasks.append(row)
    if not tasks:
        raise ValueError("benchmark is empty")
    return tasks


def validate_task(row: Any, index: int) -> None:
    if not isinstance(row, dict):
        raise ValueError(f"row {index} is not an object")
    if not isinstance(row.get("task_id"), str) or not row["task_id"].strip():
        raise ValueError(f"row {index} missing task_id")
    if not isinstance(row.get("task"), str) or not row["task"].strip():
        raise ValueError(f"row {index} missing task")
    judge = row.get("judge")
    if not isinstance(judge, dict):
        raise ValueError(f"row {index} missing judge")
    kind = judge.get("kind")
    if kind == "rule":
        checks = judge.get("checks")
        if not isinstance(checks, list) or not checks:
            raise ValueError(f"row {index} rule judge needs checks")
        for check in checks:
            if not isinstance(check, dict) or check.get("op") not in {
                "contains",
                "regex",
                "section_present",
                "max_chars",
                "min_citations",
                "tool_called",
                "tool_not_called",
                "mapping_contains",
            }:
                raise ValueError(f"row {index} has invalid rule check")
            if check.get("op") == "mapping_contains":
                _validate_mapping_contains_arg(check.get("arg"), index)
            elif not isinstance(check.get("arg"), (str, int, float)):
                raise ValueError(f"row {index} rule check has invalid arg")
    elif kind == "llm":
        if not isinstance(judge.get("rubric"), str) or not judge["rubric"].strip():
            raise ValueError(f"row {index} llm judge needs rubric")
    elif kind == "qrels":
        if not isinstance(judge.get("expected_slugs"), list):
            raise ValueError(f"row {index} qrels judge needs expected_slugs")
    else:
        raise ValueError(f"row {index} judge.kind must be rule, llm, or qrels")


def split_benchmark(tasks: list[dict[str, Any]], ratio: tuple[int, int, int]) -> BenchmarkSplit:
    train_r, sel_r, test_r = ratio
    if min(ratio) <= 0:
        raise ValueError("split ratios must be positive")
    ordered = sorted(tasks, key=lambda row: row["task_id"])
    total = len(ordered)
    denom = train_r + sel_r + test_r
    train_n = total * train_r // denom
    sel_n = total * sel_r // denom
    if sel_n < D_SEL_MIN_SIZE:
        raise ValueError(f"D_sel has {sel_n} task(s), need >= {D_SEL_MIN_SIZE}")
    if train_n == 0 or train_n + sel_n >= total:
        raise ValueError("split leaves an empty train or test set")
    return BenchmarkSplit(
        train=ordered[:train_n],
        sel=ordered[train_n : train_n + sel_n],
        test=ordered[train_n + sel_n :],
    )


def split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"^---\n[\s\S]*?\n---\n", text)
    if not match:
        return "", text
    return text[: match.end()], text[match.end() :]


def apply_edit(text: str, edit: dict[str, Any]) -> dict[str, Any]:
    frontmatter, body = split_frontmatter(text)
    outcome = _apply_body_edit(body, edit)
    if outcome["outcome"] != "applied":
        return outcome
    return {"outcome": "applied", "edit": edit, "text": frontmatter + outcome["body"]}


def _apply_body_edit(body: str, edit: dict[str, Any]) -> dict[str, Any]:
    op = edit.get("op")
    if op == "add":
        anchor = str(edit.get("anchor", "")).strip()
        matches = _heading_matches(body, anchor) or _line_matches(body, anchor)
        if not matches:
            return {"outcome": "rejected", "edit": edit, "reason": "anchor_not_found"}
        if len(matches) > 1:
            return {"outcome": "rejected", "edit": edit, "reason": "anchor_ambiguous"}
        insert_at = matches[0][1]
        if _inside_code_fence(body, insert_at):
            return {"outcome": "rejected", "edit": edit, "reason": "inside_code_fence"}
        content = str(edit.get("content", "")).rstrip()
        new_body = body[:insert_at] + "\n" + content + "\n" + body[insert_at:]
        return {"outcome": "applied", "body": new_body} if new_body != body else {
            "outcome": "rejected",
            "edit": edit,
            "reason": "no_change",
        }
    if op in {"replace", "delete"}:
        target = str(edit.get("target", ""))
        if not target:
            return {"outcome": "rejected", "edit": edit, "reason": "target_not_found"}
        starts = [match.start() for match in re.finditer(re.escape(target), body)]
        if not starts:
            return {"outcome": "rejected", "edit": edit, "reason": "target_not_found"}
        if len(starts) > 1:
            return {"outcome": "rejected", "edit": edit, "reason": "target_ambiguous"}
        start = starts[0]
        if _inside_code_fence(body, start):
            return {"outcome": "rejected", "edit": edit, "reason": "inside_code_fence"}
        replacement = "" if op == "delete" else str(edit.get("replacement", ""))
        end = start + len(target)
        if op == "delete" and end < len(body) and body[end] == "\n":
            end += 1
        new_body = body[:start] + replacement + body[end:]
        return {"outcome": "applied", "body": new_body} if new_body != body else {
            "outcome": "rejected",
            "edit": edit,
            "reason": "no_change",
        }
    return {"outcome": "rejected", "edit": edit, "reason": "unknown_op"}


def _heading_matches(body: str, anchor: str) -> list[tuple[int, int]]:
    if not anchor:
        return []
    heading = re.sub(r"^#+\s*", "", anchor).strip()
    pattern = re.compile(rf"^#{{1,6}}\s+{re.escape(heading)}\s*$", re.MULTILINE)
    return [(match.start(), match.end()) for match in pattern.finditer(body)]


def _line_matches(body: str, anchor: str) -> list[tuple[int, int]]:
    matches: list[tuple[int, int]] = []
    offset = 0
    for line in body.splitlines(keepends=True):
        stripped = line.strip()
        end = offset + len(line.rstrip("\n"))
        if stripped == anchor:
            matches.append((offset, end))
        offset += len(line)
    return matches


def _inside_code_fence(body: str, offset: int) -> bool:
    inside = False
    cursor = 0
    for line in body.splitlines(keepends=True):
        if cursor >= offset:
            return inside
        if line.lstrip().startswith("```"):
            inside = not inside
        cursor += len(line)
    return inside


def score_rule(final_text: str, tool_calls: list[dict[str, Any]], checks: list[dict[str, Any]]) -> float:
    return score_rule_detail(final_text, tool_calls, checks)["score"]


def score_rule_detail(final_text: str, tool_calls: list[dict[str, Any]], checks: list[dict[str, Any]]) -> dict[str, Any]:
    if not checks:
        return {"score": 0.0, "checks": []}
    details = []
    for check in checks:
        details.append(_rule_check_detail(final_text, tool_calls, check))
    score = sum(float(detail.get("score", 1.0 if detail["passed"] else 0.0)) for detail in details) / len(details)
    return {"score": score, "checks": details}


def _validate_mapping_contains_arg(arg: Any, index: int) -> None:
    if not isinstance(arg, dict):
        raise ValueError(f"row {index} mapping_contains arg must be an object")
    items = arg.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError(f"row {index} mapping_contains requires non-empty items")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"row {index} mapping_contains item must be an object")
        if not isinstance(item.get("key"), str) or not item["key"].strip():
            raise ValueError(f"row {index} mapping_contains item requires key")
        if not isinstance(item.get("value"), str) or not item["value"].strip():
            raise ValueError(f"row {index} mapping_contains item requires value")


def _rule_check_detail(final_text: str, tool_calls: list[dict[str, Any]], check: dict[str, Any]) -> dict[str, Any]:
    if check["op"] == "mapping_contains":
        return _mapping_contains_detail(final_text, check["arg"])
    return {
        "op": check["op"],
        "arg": check["arg"],
        "passed": _check_rule(final_text, tool_calls, check),
    }


def _check_rule(final_text: str, tool_calls: list[dict[str, Any]], check: dict[str, Any]) -> bool:
    op = check["op"]
    arg = check["arg"]
    if op == "contains":
        return isinstance(arg, str) and arg in final_text
    if op == "regex":
        return isinstance(arg, str) and re.search(arg, final_text, re.MULTILINE) is not None
    if op == "section_present":
        heading = re.sub(r"^#+\s*", "", str(arg)).strip()
        return re.search(rf"^#{{1,6}}\s+{re.escape(heading)}\s*$", final_text, re.MULTILINE | re.IGNORECASE) is not None
    if op == "max_chars":
        return isinstance(arg, (int, float)) and len(final_text) <= int(arg)
    if op == "min_citations":
        return isinstance(arg, (int, float)) and _count_citations(final_text) >= int(arg)
    if op == "tool_called":
        return isinstance(arg, str) and any(call.get("name") == arg and not call.get("failed") for call in tool_calls)
    if op == "tool_not_called":
        return isinstance(arg, str) and all(call.get("name") != arg for call in tool_calls)
    if op == "mapping_contains":
        return _mapping_contains_detail(final_text, arg)["passed"]
    return False


def _mapping_contains_detail(final_text: str, arg: dict[str, Any]) -> dict[str, Any]:
    observed = _extract_markdown_mappings(final_text)
    items = []
    for item in arg["items"]:
        key = item["key"]
        expected = item["value"]
        actual = observed.get(_normalize_mapping_text(key))
        passed = actual == _normalize_mapping_text(expected)
        items.append({
            "key": key,
            "expected": expected,
            "actual": _display_mapping_value(final_text, key, actual),
            "passed": passed,
        })
    score = sum(1 for item in items if item["passed"]) / len(items) if items else 0.0
    return {
        "op": "mapping_contains",
        "arg": arg,
        "passed": score == 1.0,
        "score": score,
        "items": items,
    }


def _extract_markdown_mappings(text: str) -> dict[str, str]:
    mappings: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 2 and not all(set(cell) <= {"-"} for cell in cells[:2]):
                mappings[_normalize_mapping_text(cells[0])] = _normalize_mapping_text(cells[1])
            continue
        line = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", line)
        for separator in ("->", ":", " - "):
            if separator in line:
                key, value = line.split(separator, 1)
                if key.strip() and value.strip():
                    mappings[_normalize_mapping_text(key)] = _normalize_mapping_text(value)
                break
    return mappings


def _normalize_mapping_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _display_mapping_value(final_text: str, key: str, normalized_value: str | None) -> str | None:
    if normalized_value is None:
        return None
    for raw_line in final_text.splitlines():
        line = raw_line.strip()
        if _normalize_mapping_text(key) not in _extract_markdown_mappings(line):
            continue
        observed = _extract_markdown_mappings(line).get(_normalize_mapping_text(key))
        if observed == normalized_value:
            if line.startswith("|") and line.endswith("|"):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if len(cells) >= 2:
                    return cells[1]
            for separator in ("->", ":", " - "):
                if separator in line:
                    return line.split(separator, 1)[1].strip()
    return normalized_value


def _count_citations(text: str) -> int:
    return (
        len(re.findall(r"\[[^\]]+\]\([^)]+\)", text))
        + len(re.findall(r"\[\d+\]", text))
        + len(re.findall(r"\b(?:wiki|docs|requirements|plans|tests)/[A-Za-z0-9_./-]+\b", text))
    )


def validation_gate(
    sel_tasks: list[dict[str, Any]],
    rollout_texts: dict[str, list[Any]],
    *,
    best_score: float,
    epsilon: float = VALIDATION_EPSILON,
) -> dict[str, Any]:
    per_task: list[dict[str, Any]] = []
    for task in sel_tasks:
        task_id = task["task_id"]
        rollouts = rollout_texts.get(task_id, [])
        if len(rollouts) != 3:
            raise ValueError(f"task {task_id} requires exactly 3 rollout records")
        runs = []
        details = []
        for rollout in rollouts:
            judge = task["judge"]
            if judge["kind"] != "rule":
                raise ValueError("deterministic validation_gate only supports rule judges")
            final_text, tool_calls = normalize_rollout_record(rollout)
            detail = score_rule_detail(final_text, tool_calls, judge["checks"])
            runs.append(detail["score"])
            detail["contract"] = rollout.get("contract") if isinstance(rollout, dict) else None
            detail.setdefault("contract_violation", any(not check["passed"] for check in detail["checks"]))
            details.append(detail)
        med = median(runs)
        per_task.append({"task_id": task_id, "median": med, "runs": runs, "run_details": details})
    sel_score = sum(row["median"] for row in per_task) / len(per_task) if per_task else 0.0
    accepted = sel_score > best_score + epsilon
    return {
        "accepted": accepted,
        "sel_score": sel_score,
        "per_task_medians": per_task,
        "reason": None if accepted else ("below_baseline" if sel_score <= best_score else "no_margin"),
    }


def normalize_rollout_record(rollout: Any) -> tuple[str, list[dict[str, Any]]]:
    if isinstance(rollout, str):
        return rollout, []
    if not isinstance(rollout, dict):
        raise ValueError("rollout record must be a string or object")
    final_text = rollout.get("final_text")
    tool_calls = rollout.get("tool_calls", [])
    if not isinstance(final_text, str):
        raise ValueError("rollout record missing final_text")
    if not isinstance(tool_calls, list) or not all(isinstance(call, dict) for call in tool_calls):
        raise ValueError("rollout record tool_calls must be a list of objects")
    return final_text, tool_calls


def median(values: Iterable[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex SkillOpt deterministic helper")
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--split", default="1:1:1")
    parser.add_argument("--bootstrap-reviewed", action="store_true")
    args = parser.parse_args()
    ratio = tuple(int(part) for part in args.split.split(":"))
    if len(ratio) != 3:
        raise SystemExit("--split must be TRAIN:SEL:TEST")
    tasks = load_benchmark(args.benchmark, bootstrap_reviewed=args.bootstrap_reviewed)
    split = split_benchmark(tasks, ratio)  # type: ignore[arg-type]
    print(json.dumps({"ok": True, "train": len(split.train), "sel": len(split.sel), "test": len(split.test)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
