#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


try:
    import yaml
except ImportError:  # pragma: no cover - exercised only when dependency is absent.
    yaml = None


CLOSED_STATUSES = {"verified", "not_required_with_reason", "deferred_with_user_acceptance"}
BLOCKING_STATUSES = {"planned", "missing", "blocked", "stale_needs_recheck"}
EVIDENCE_BY_OBLIGATION = {
    "ui_state": {"dom_assertion", "screenshot"},
    "migration": {"row_count", "checksum"},
    "agent_workflow": {"generated_artifact", "consumer_proof"},
    "workflow_policy": {"structured_contract_fixture", "positive_negative_trigger_tests", "schema_validation"},
    "reviewer_contract": {"structured_reviewer_contract_test", "reviewer_fixture"},
    "artifact_contract": {"schema_validation", "artifact_role_test"},
    "schema_contract": {"schema_validator_test", "negative_fixture_test"},
    "closure_contract": {"closure_validator_test", "status_counterexample_fixture"},
    "evidence_contract": {
        "evidence_compatibility_test",
        "negative_route_only_nested_state_fixture",
        "negative_prose_only_fixture",
    },
    "ship_gate": {"implementation_brake_harness", "closure_validator_result", "progress_state_assertion"},
    "lifecycle_contract": {"lifecycle_fixture_test", "stale_closure_rejection_test"},
    "verification_contract": {"targeted_validator_command", "scripts_verify_result", "external_cwd_verify_result"},
    "regression_fixture": {"negative_fixture_test_suite", "expected_error_assertions"},
    "template_parity": {"parity_test", "context_loading_file_inventory"},
}
REQUIRED_ROW_FIELDS = {
    "row_id",
    "description",
    "obligation_type",
    "source_refs",
    "data_condition",
    "required_evidence",
    "status",
    "evidence_refs",
    "recorded_in",
}
REQUIRED_DECISION_FIELDS = {
    "requirement_id",
    "decision_version",
    "ledger_required",
    "trigger_evaluation",
    "source_refs",
    "decided_by_gate",
    "decided_at",
}


@dataclass
class Error:
    code: str
    problem: str
    path: str
    row_id: str | None = None
    route: str | None = None

    def to_dict(self) -> dict[str, str]:
        data = {"code": self.code, "problem": self.problem, "path": self.path}
        if self.row_id:
            data["row_id"] = self.row_id
        if self.route:
            data["route"] = self.route
        return data


class DuplicateKeyLoader(yaml.SafeLoader if yaml else object):
    pass


def _construct_mapping(loader: Any, node: Any, deep: bool = False) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


if yaml:
    DuplicateKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value in {"true", "false"}:
        return value == "true"
    if value in {"null", "None"}:
        return None
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith("{") and value.endswith("}"):
        return json.loads(value)
    if re.fullmatch(r"-?[0-9]+", value):
        return int(value)
    return value


def preprocess_yaml_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))
    return lines


def parse_simple_yaml_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    container: Any = [] if lines[index][1].startswith("- ") else {}
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            break
        if isinstance(container, list):
            if not text.startswith("- "):
                break
            item = text[2:].strip()
            if item == "":
                child, index = parse_simple_yaml_block(lines, index + 1, indent + 2)
                container.append(child)
                continue
            if ":" in item and not item.startswith(("http://", "https://")):
                key, raw_value = item.split(":", 1)
                mapping: dict[str, Any] = {}
                if key in mapping:
                    raise ValueError(f"duplicate key: {key}")
                if raw_value.strip():
                    mapping[key.strip()] = parse_scalar(raw_value)
                    index += 1
                else:
                    child, index = parse_simple_yaml_block(lines, index + 1, indent + 2)
                    mapping[key.strip()] = child
                while index < len(lines) and lines[index][0] == indent + 2 and not lines[index][1].startswith("- "):
                    child_key, child_raw = lines[index][1].split(":", 1)
                    child_key = child_key.strip()
                    if child_key in mapping:
                        raise ValueError(f"duplicate key: {child_key}")
                    if child_raw.strip():
                        mapping[child_key] = parse_scalar(child_raw)
                        index += 1
                    else:
                        child, index = parse_simple_yaml_block(lines, index + 1, indent + 4)
                        mapping[child_key] = child
                container.append(mapping)
                continue
            container.append(parse_scalar(item))
            index += 1
            continue
        if ":" not in text:
            raise ValueError(f"expected mapping entry: {text}")
        key, raw_value = text.split(":", 1)
        key = key.strip()
        if key in container:
            raise ValueError(f"duplicate key: {key}")
        if raw_value.strip():
            container[key] = parse_scalar(raw_value)
            index += 1
        else:
            child, index = parse_simple_yaml_block(lines, index + 1, indent + 2)
            container[key] = child
    return container, index


def parse_simple_yaml(text: str) -> dict[str, Any]:
    lines = preprocess_yaml_lines(text)
    parsed, index = parse_simple_yaml_block(lines, 0, lines[0][0] if lines else 0)
    if index != len(lines):
        raise ValueError(f"could not parse YAML line: {lines[index][1]}")
    if not isinstance(parsed, dict):
        raise ValueError("YAML root must be a mapping")
    return parsed


def result(mode: str, errors: list[Error]) -> tuple[int, str]:
    payload: dict[str, Any] = {
        "status": "fail" if errors else "pass",
        "mode": mode,
        "error_codes": sorted({error.code for error in errors}),
        "errors": [error.to_dict() for error in errors],
    }
    for error in errors:
        if error.route:
            payload["route"] = error.route
            break
    return (1 if errors else 0), json.dumps(payload, sort_keys=True)


def err(code: str, problem: str, path: Path | str, row_id: str | None = None, route: str | None = None) -> Error:
    return Error(code, problem, str(path), row_id=row_id, route=route)


def has_forbidden_yaml_construct(text: str) -> str | None:
    if re.search(r"(?m)^---\s*$", text):
        return "E_YAML_MULTI_DOCUMENT"
    if re.search(r"(?m)(^|\s)(<<:|&[A-Za-z0-9_-]+|\*[A-Za-z0-9_-]+)", text):
        return "E_YAML_UNSUPPORTED_CONSTRUCT"
    return None


def load_yaml_file(path: Path) -> tuple[Any | None, list[Error]]:
    if not path.exists():
        return None, [err("E_FILE_MISSING", "required YAML file is missing", path)]
    text = path.read_text(encoding="utf-8")
    forbidden = has_forbidden_yaml_construct(text)
    if forbidden:
        return None, [err(forbidden, "YAML construct is not supported for semantic validation", path)]
    try:
        if yaml is None:
            data = parse_simple_yaml(text)
        else:
            data = yaml.load(text, Loader=DuplicateKeyLoader)
    except ValueError as exc:
        message = str(exc)
        if "duplicate key" in message:
            code = "E_YAML_DUPLICATE_KEY"
        elif "YAML root must be a mapping" in message:
            code = "E_YAML_ROOT"
        else:
            code = "E_YAML_PARSE"
        return None, [err(code, message, path)]
    except Exception as exc:
        return None, [err("E_YAML_PARSE", str(exc), path)]
    if not isinstance(data, dict):
        return None, [err("E_YAML_ROOT", "YAML root must be a mapping", path)]
    return data, []


def require_fields(data: dict[str, Any], fields: set[str], path: Path, row_id: str | None = None) -> list[Error]:
    errors: list[Error] = []
    for field in sorted(fields):
        value = data.get(field)
        if value is None or value == "" or value == []:
            errors.append(err("E_REQUIRED_FIELD", f"{field} is required", path, row_id))
    return errors


def bool_signal(signals: dict[str, Any], key: str) -> bool:
    return signals.get(key) is True


def trigger_requires_ledger(signals: dict[str, Any]) -> bool:
    qualitative_high_risk = any(
        [
            bool_signal(signals, "multi_state_ui"),
            bool_signal(signals, "bulk_data_migration"),
            bool_signal(signals, "many_acceptance_criteria"),
            bool_signal(signals, "multiple_workflow_skills"),
            bool_signal(signals, "validator_and_fixture_foundation"),
        ]
    )
    if signals.get("low_risk_mechanical_edits") is True and not qualitative_high_risk:
        return False
    return any(
        [
            signals.get("subtask_count", 0) >= 10,
            signals.get("screen_count", 0) >= 10,
            signals.get("screenshot_count", 0) >= 10,
            bool_signal(signals, "multi_state_ui"),
            bool_signal(signals, "bulk_data_migration"),
            signals.get("module_count", 0) >= 2,
            signals.get("package_count", 0) >= 2,
            signals.get("acceptance_criteria_count", 0) >= 10,
            bool_signal(signals, "many_acceptance_criteria"),
        ]
    )


def validate_decision(req_dir: Path, decision: dict[str, Any], decision_path: Path) -> list[Error]:
    errors = require_fields(decision, REQUIRED_DECISION_FIELDS, decision_path)
    if errors:
        return errors
    if not isinstance(decision.get("ledger_required"), bool):
        errors.append(err("E_DECISION_FIELD", "ledger_required must be boolean", decision_path))
    trigger = decision.get("trigger_evaluation")
    if not isinstance(trigger, dict) or not isinstance(trigger.get("signals"), dict):
        errors.append(err("E_DECISION_FIELD", "trigger_evaluation.signals must be a mapping", decision_path))
        return errors
    required_by_signals = trigger_requires_ledger(trigger["signals"])
    if required_by_signals and decision.get("ledger_required") is False:
        errors.append(err("E_DECISION_STALE", "not-required decision conflicts with broad-work trigger signals", decision_path))
    if decision.get("decided_at", "") < "2026-06-20" and decision.get("ledger_required") is False:
        errors.append(err("E_DECISION_STALE", "not-required decision predates current accepted scope", decision_path))
    ledger_path_value = str(decision.get("ledger_path", "coverage-ledger.yml"))
    ledger_path = req_dir / ledger_path_value
    if decision.get("ledger_required") is True:
        if "ledger_not_required" in decision:
            errors.append(err("E_DECISION_LEDGER_CONFLICT", "required and not-required branches both present", decision_path))
        if "ledger_path" not in decision:
            errors.append(err("E_LEDGER_PATH_MISSING", "required decision must name ledger_path", decision_path))
        elif Path(ledger_path_value) != Path("coverage-ledger.yml"):
            errors.append(err("E_LEDGER_PATH_MISMATCH", "ledger_path must point to coverage-ledger.yml", decision_path))
        elif not ledger_path.exists():
            errors.append(err("E_LEDGER_PATH_MISSING", "named ledger_path does not exist", ledger_path))
    if decision.get("ledger_required") is False:
        not_required = decision.get("ledger_not_required")
        if not isinstance(not_required, dict):
            errors.append(err("E_LEDGER_NOT_REQUIRED_REASON", "ledger_not_required decision is required", decision_path))
        else:
            for field in ["reason", "risk_assessment", "accepted_scope_refs"]:
                if not not_required.get(field):
                    errors.append(err("E_LEDGER_NOT_REQUIRED_REASON", f"ledger_not_required.{field} is required", decision_path))
        if (req_dir / "coverage-ledger.yml").exists():
            errors.append(err("E_DECISION_LEDGER_CONFLICT", "not-required decision conflicts with existing ledger", decision_path))
    return errors


def validate_progress_gap(req_dir: Path) -> list[Error]:
    progress_path = req_dir / "progress.md"
    if not progress_path.exists():
        return [
            err(
                "E_PROGRESS_GAP_SCHEMA",
                "missing-ledger recheck requires structured progress gap",
                progress_path,
                route="requirement-clarifier-post-review-recheck",
            )
        ]
    progress, errors = load_yaml_file(progress_path)
    if errors:
        return errors
    if not isinstance(progress, dict) or not isinstance(progress.get("coverage_gap"), dict):
        return [
            err(
                "E_PROGRESS_GAP_SCHEMA",
                "progress.md must contain coverage_gap mapping",
                progress_path,
                route="requirement-clarifier-post-review-recheck",
            )
        ]
    gap = progress["coverage_gap"]
    required = {
        "requirement_id",
        "route",
        "blocking_reason",
        "triggering_signals",
        "expected_next_gate",
        "closure_condition",
        "recorded_at",
    }
    missing = [field for field in sorted(required) if not gap.get(field)]
    if missing:
        return [
            err(
                "E_PROGRESS_GAP_SCHEMA",
                f"coverage_gap missing fields: {', '.join(missing)}",
                progress_path,
                route="requirement-clarifier-post-review-recheck",
            )
        ]
    if gap.get("route") != "requirement-clarifier-post-review-recheck":
        return [
            err(
                "E_PROGRESS_GAP_SCHEMA",
                "coverage_gap route must be requirement-clarifier-post-review-recheck",
                progress_path,
                route="requirement-clarifier-post-review-recheck",
            )
        ]
    return []


def validate_ledger_schema(req_dir: Path, ledger: dict[str, Any], ledger_path: Path) -> list[Error]:
    errors = require_fields(
        ledger,
        {"requirement_id", "ledger_version", "ledger_required", "status", "closure_policy", "coverage_rows"},
        ledger_path,
    )
    rows = ledger.get("coverage_rows")
    if not isinstance(rows, list) or not rows:
        errors.append(err("E_EMPTY_LEDGER", "coverage_rows must be a non-empty list", ledger_path))
        return errors
    seen: set[str] = set()
    for row in rows:
        row_id = row.get("row_id") if isinstance(row, dict) else None
        if not isinstance(row, dict):
            errors.append(err("E_ROW_SCHEMA", "coverage row must be a mapping", ledger_path))
            continue
        if isinstance(row_id, str):
            if row_id in seen:
                errors.append(err("E_DUPLICATE_ROW_ID", "row_id must be unique", ledger_path, row_id))
            seen.add(row_id)
        errors.extend(require_fields(row, REQUIRED_ROW_FIELDS, ledger_path, row_id))
        if not isinstance(row.get("evidence_refs"), list):
            errors.append(err("E_EVIDENCE_SCHEMA", "evidence_refs must be a list", ledger_path, row_id))
        elif any(not isinstance(item, dict) for item in row["evidence_refs"]):
            errors.append(err("E_EVIDENCE_SCHEMA", "evidence_refs entries must be objects", ledger_path, row_id))
    return errors


def validate_readiness(req_dir: Path) -> list[Error]:
    decision_path = req_dir / "coverage-decision.yml"
    ledger_path = req_dir / "coverage-ledger.yml"
    if not decision_path.exists():
        if not ledger_path.exists():
            errors = [
                err(
                    "E_DECISION_MISSING_RECHECK",
                    "broad-work signals have no coverage decision or ledger",
                    decision_path,
                    route="requirement-clarifier-post-review-recheck",
                )
            ]
            errors.extend(validate_progress_gap(req_dir))
            return errors
        return [err("E_DECISION_REQUIRED", "coverage-decision.yml is required when coverage-ledger.yml exists", decision_path)]
    decision, errors = load_yaml_file(decision_path)
    if errors:
        return errors
    assert isinstance(decision, dict)
    errors = validate_decision(req_dir, decision, decision_path)
    if decision.get("ledger_required") is True and not ledger_path.exists():
        errors.append(err("E_LEDGER_REQUIRED_MISSING", "ledger_required decision needs coverage-ledger.yml", ledger_path))
    if ledger_path.exists():
        ledger, ledger_errors = load_yaml_file(ledger_path)
        errors.extend(ledger_errors)
        if isinstance(ledger, dict):
            if ledger.get("requirement_id") != decision.get("requirement_id"):
                errors.append(err("E_DECISION_LEDGER_CONFLICT", "decision and ledger requirement_id differ", ledger_path))
            errors.extend(validate_ledger_schema(req_dir, ledger, ledger_path))
    return errors


def evidence_types(row: dict[str, Any]) -> set[str]:
    return {str(item.get("type")) for item in row.get("evidence_refs", []) if isinstance(item, dict)}


def validate_evidence_path(req_dir: Path, entry: dict[str, Any], ledger_path: Path, row_id: str) -> list[Error]:
    errors: list[Error] = []
    path_value = entry.get("path")
    if not path_value:
        return errors
    evidence_path = Path(str(path_value))
    if evidence_path.is_absolute() or any(part == ".." for part in evidence_path.parts):
        return [err("E_EVIDENCE_PATH_ESCAPE", "evidence path must stay inside requirement directory", ledger_path, row_id)]
    candidate = req_dir / evidence_path
    try:
        resolved = candidate.resolve(strict=False)
        req_resolved = req_dir.resolve(strict=True)
    except OSError:
        return [err("E_EVIDENCE_PATH_MISSING", "evidence path cannot be resolved", ledger_path, row_id)]
    if not (resolved == req_resolved or req_resolved in resolved.parents):
        return [err("E_EVIDENCE_PATH_ESCAPE", "evidence path resolves outside requirement directory", ledger_path, row_id)]
    if not candidate.exists():
        return [err("E_EVIDENCE_PATH_MISSING", "evidence artifact is missing", ledger_path, row_id)]
    if not candidate.is_file():
        return [err("E_EVIDENCE_PATH_NOT_FILE", "evidence artifact must be a file", ledger_path, row_id)]
    if not os.access(candidate, os.R_OK):
        return [err("E_EVIDENCE_PATH_UNREADABLE", "evidence artifact is not readable", ledger_path, row_id)]
    artifact_hash = entry.get("artifact_hash")
    if isinstance(artifact_hash, str) and artifact_hash.startswith("sha256:"):
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if artifact_hash != f"sha256:{digest}":
            errors.append(err("E_EVIDENCE_HASH_MISMATCH", "evidence artifact hash does not match", ledger_path, row_id))
    return errors


def validate_closure(req_dir: Path) -> list[Error]:
    decision_path = req_dir / "coverage-decision.yml"
    decision, decision_errors = load_yaml_file(decision_path)
    if decision_errors:
        return decision_errors
    assert isinstance(decision, dict)
    errors = validate_decision(req_dir, decision, decision_path)
    if decision.get("ledger_required") is not True:
        errors.append(err("E_DECISION_LEDGER_CONFLICT", "closure requires ledger_required true", decision_path))
    ledger_path = req_dir / "coverage-ledger.yml"
    ledger, ledger_errors = load_yaml_file(ledger_path)
    errors.extend(ledger_errors)
    if errors:
        return errors
    assert isinstance(ledger, dict)
    errors = validate_ledger_schema(req_dir, ledger, ledger_path)
    rows = ledger.get("coverage_rows") if isinstance(ledger.get("coverage_rows"), list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_id = str(row.get("row_id", "unknown"))
        status = row.get("status")
        if status in BLOCKING_STATUSES or status not in CLOSED_STATUSES:
            errors.append(err("E_ROW_BLOCKING_STATUS", f"row status {status!r} blocks closure", ledger_path, row_id))
        if status == "not_required_with_reason" and not row.get("not_required_reason"):
            errors.append(err("E_NOT_REQUIRED_REASON", "not_required row needs not_required_reason", ledger_path, row_id))
        if status == "deferred_with_user_acceptance" and not row.get("user_acceptance_ref"):
            errors.append(err("E_DEFERRED_ACCEPTANCE", "deferred row needs user_acceptance_ref", ledger_path, row_id))
        obligation = str(row.get("obligation_type", ""))
        allowed = EVIDENCE_BY_OBLIGATION.get(obligation)
        if allowed:
            observed = evidence_types(row)
            required = set(str(item) for item in row.get("required_evidence", []))
            compatible = required.issubset(allowed) and required.issubset(observed)
            if not compatible:
                errors.append(err("E_EVIDENCE_INCOMPATIBLE", "evidence types do not satisfy obligation", ledger_path, row_id))
            for evidence_type in observed:
                if evidence_type not in allowed:
                    errors.append(err("E_EVIDENCE_INCOMPATIBLE", "evidence type is not valid for obligation", ledger_path, row_id))
        for entry in row.get("evidence_refs", []):
            if not isinstance(entry, dict):
                continue
            for field in ["type", "ref", "recorded_in"]:
                if not entry.get(field):
                    errors.append(err("E_EVIDENCE_SCHEMA", f"evidence_refs entry needs {field}", ledger_path, row_id))
            errors.extend(validate_evidence_path(req_dir, entry, ledger_path, row_id))
    return errors


def validate_schema(req_dir: Path) -> list[Error]:
    errors: list[Error] = []
    decision_path = req_dir / "coverage-decision.yml"
    ledger_path = req_dir / "coverage-ledger.yml"
    if decision_path.exists():
        decision, decision_errors = load_yaml_file(decision_path)
        errors.extend(decision_errors)
        if isinstance(decision, dict):
            errors.extend(validate_decision(req_dir, decision, decision_path))
    if ledger_path.exists():
        ledger, ledger_errors = load_yaml_file(ledger_path)
        errors.extend(ledger_errors)
        if isinstance(ledger, dict):
            errors.extend(validate_ledger_schema(req_dir, ledger, ledger_path))
    if not decision_path.exists() and not ledger_path.exists():
        errors.append(err("E_COVERAGE_ARTIFACT_MISSING", "coverage decision or ledger is required", req_dir))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate requirement coverage-ledger artifacts.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--mode", choices=["schema", "readiness", "closure"], required=True)
    validate.add_argument("--requirement-dir", required=True)
    args = parser.parse_args(argv)
    req_dir = Path(args.requirement_dir).resolve()
    if args.mode == "schema":
        errors = validate_schema(req_dir)
    elif args.mode == "readiness":
        errors = validate_readiness(req_dir)
    else:
        errors = validate_closure(req_dir)
    code, output = result(args.mode, errors)
    print(output)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
