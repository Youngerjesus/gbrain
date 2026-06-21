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
SOURCE_METHODS = {"manual", "llm_observed", "human_manifest", "extracted", "hybrid"}
SOURCE_DISPOSITIONS = {"included", "excluded", "deferred", "ambiguous"}
SOURCE_REVIEWER_STATUSES = {"SHIP", "FINDINGS", "BLOCKED_INVALID", "BLOCKED_UNAVAILABLE"}


@dataclass
class Error:
    code: str
    problem: str
    path: str
    row_id: str | None = None
    route: str | None = None
    source_item_id: str | None = None
    ledger_row_id: str | None = None
    expected: str | None = None
    actual: str | None = None

    def to_dict(self) -> dict[str, str]:
        data = {"code": self.code, "problem": self.problem, "path": self.path}
        if self.row_id:
            data["row_id"] = self.row_id
        if self.route:
            data["route"] = self.route
        if self.source_item_id:
            data["source_item_id"] = self.source_item_id
        if self.ledger_row_id:
            data["ledger_row_id"] = self.ledger_row_id
        if self.expected:
            data["expected"] = self.expected
        if self.actual:
            data["actual"] = self.actual
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
    routes = sorted({error.route for error in errors if error.route})
    payload: dict[str, Any] = {
        "status": "fail" if errors else "pass",
        "mode": mode,
        "error_codes": sorted({error.code for error in errors}),
        "errors": [error.to_dict() for error in errors],
    }
    if routes:
        payload["routes"] = routes
    for error in errors:
        if error.route:
            payload["route"] = error.route
            break
    return (1 if errors else 0), json.dumps(payload, sort_keys=True)


def err(
    code: str,
    problem: str,
    path: Path | str,
    row_id: str | None = None,
    route: str | None = None,
    source_item_id: str | None = None,
    ledger_row_id: str | None = None,
    expected: str | None = None,
    actual: str | None = None,
) -> Error:
    return Error(
        code,
        problem,
        str(path),
        row_id=row_id,
        route=route,
        source_item_id=source_item_id,
        ledger_row_id=ledger_row_id,
        expected=expected,
        actual=actual,
    )


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
        code = "E_YAML_DUPLICATE_KEY" if "duplicate key" in str(exc) else "E_YAML_PARSE"
        return None, [err(code, str(exc), path)]
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


def canonical_source_inventory_digest(items: list[dict[str, Any]]) -> str:
    canonical = [
        {
            "source_item_id": item["source_item_id"],
            "source_method": item["source_method"],
            "source_refs": sorted(set(item["source_refs"])),
            "metadata": item.get("metadata", {}),
        }
        for item in sorted(items, key=lambda value: value["source_item_id"])
    ]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def canonical_scope_digest(items: list[dict[str, Any]]) -> str:
    canonical: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda value: value["source_item_id"]):
        obligation_ids = string_list(item.get("obligation_ids", [])) or []
        coverage_row_ids = string_list(item.get("coverage_row_ids", [])) or []
        canonical.append(
            {
                "source_item_id": item["source_item_id"],
                "disposition": item["disposition"],
                "obligation_ids": sorted(set(obligation_ids)),
                "coverage_row_ids": sorted(set(coverage_row_ids)),
                "rationale": item.get("rationale", ""),
            }
        )
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        return None
    return value


def source_validation_active(req_dir: Path, decision: dict[str, Any] | None, ledger: dict[str, Any] | None) -> bool:
    if (req_dir / "source-inventory.yml").exists() or (req_dir / "scope-reconciliation.yml").exists():
        return True
    trigger = decision.get("trigger_evaluation") if isinstance(decision, dict) else None
    signals = trigger.get("signals") if isinstance(trigger, dict) else None
    if isinstance(signals, dict) and signals.get("source_obligation_inventory_required") is True:
        return True
    if isinstance(ledger, dict):
        if ledger.get("source_inventory_digest") or ledger.get("accepted_scope_digest"):
            return True
        rows = ledger.get("coverage_rows")
        if isinstance(rows, list) and any(isinstance(row, dict) and row.get("source_item_ids") for row in rows):
            return True
    return False


def validate_source_inventory(inventory: dict[str, Any], inventory_path: Path) -> tuple[list[dict[str, Any]], str | None, list[Error]]:
    errors = require_fields(
        inventory,
        {"requirement_id", "inventory_version", "source_inventory_digest", "source_items"},
        inventory_path,
    )
    items = inventory.get("source_items")
    if not isinstance(items, list) or not items:
        errors.append(
            err("E_SOURCE_INVENTORY_SCHEMA", "source_items must be a non-empty list", inventory_path, route="source-inventory-rebuild")
        )
        return [], None, errors
    valid_items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            errors.append(err("E_SOURCE_INVENTORY_SCHEMA", "source item must be a mapping", inventory_path, route="source-inventory-rebuild"))
            continue
        source_item_id = item.get("source_item_id")
        if not isinstance(source_item_id, str) or not source_item_id:
            errors.append(err("E_SOURCE_INVENTORY_SCHEMA", "source_item_id must be a non-empty string", inventory_path, route="source-inventory-rebuild"))
            continue
        if source_item_id in seen:
            errors.append(
                err(
                    "E_SOURCE_ITEM_ID_DUPLICATE",
                    "source_item_id must be unique",
                    inventory_path,
                    route="source-inventory-rebuild",
                    source_item_id=source_item_id,
                )
            )
        seen.add(source_item_id)
        refs = string_list(item.get("source_refs"))
        method = item.get("source_method")
        metadata = item.get("metadata")
        if refs is None or not refs:
            errors.append(
                err(
                    "E_SOURCE_ITEM_REF_MISSING",
                    "source_refs must be a non-empty string list",
                    inventory_path,
                    route="source-inventory-rebuild",
                    source_item_id=source_item_id,
                )
            )
        if not isinstance(metadata, dict) or not metadata:
            errors.append(
                err(
                    "E_SOURCE_INVENTORY_SCHEMA",
                    "metadata must be a non-empty mapping",
                    inventory_path,
                    route="source-inventory-rebuild",
                    source_item_id=source_item_id,
                )
            )
        elif method in {"extracted", "hybrid"}:
            extraction_count = metadata.get("extraction_count")
            extraction_digest = metadata.get("extraction_digest")
            if not isinstance(extraction_count, int) or extraction_count < 0 or not isinstance(extraction_digest, str) or not extraction_digest:
                errors.append(
                    err(
                        "E_SOURCE_INVENTORY_SCHEMA",
                        "extracted and hybrid items need extraction_count and extraction_digest metadata",
                        inventory_path,
                        route="source-inventory-rebuild",
                        source_item_id=source_item_id,
                    )
                )
        if method not in SOURCE_METHODS:
            errors.append(
                err(
                    "E_SOURCE_INVENTORY_SCHEMA",
                    "source_method is invalid",
                    inventory_path,
                    route="source-inventory-rebuild",
                    source_item_id=source_item_id,
                )
            )
        if refs and method in SOURCE_METHODS and isinstance(metadata, dict) and metadata:
            valid_items.append(
                {
                    "source_item_id": source_item_id,
                    "source_method": method,
                    "source_refs": refs,
                    "metadata": metadata,
                }
            )
    digest = None
    if valid_items:
        digest = canonical_source_inventory_digest(valid_items)
        declared = inventory.get("source_inventory_digest")
        if declared != digest:
            errors.append(
                err(
                    "E_SOURCE_LINEAGE_STALE",
                    "source inventory digest does not match current source items",
                    inventory_path,
                    route="source-inventory-rebuild",
                    expected=digest,
                    actual=str(declared),
                )
            )
    return valid_items, digest, errors


def validate_source_reconciliation(
    reconciliation: dict[str, Any],
    reconciliation_path: Path,
    inventory_items: list[dict[str, Any]],
    inventory_version: Any,
    source_digest: str | None,
    ledger: dict[str, Any] | None,
    ledger_path: Path,
    decision: dict[str, Any] | None,
) -> list[Error]:
    errors = require_fields(
        reconciliation,
        {
            "requirement_id",
            "reconciliation_version",
            "source_inventory_digest",
            "source_inventory_version",
            "accepted_scope_digest",
            "reviewer_status",
            "reconciled_items",
        },
        reconciliation_path,
    )
    items = reconciliation.get("reconciled_items")
    if not isinstance(items, list):
        errors.append(err("E_SCOPE_RECONCILIATION_SCHEMA", "reconciled_items must be a list", reconciliation_path, route="scope-reconciliation-recheck"))
        items = []
    if reconciliation.get("source_inventory_digest") != source_digest:
        errors.append(
            err(
                "E_SOURCE_LINEAGE_STALE",
                "reconciliation source_inventory_digest does not match inventory",
                reconciliation_path,
                route="scope-reconciliation-recheck",
                expected=str(source_digest),
                actual=str(reconciliation.get("source_inventory_digest")),
            )
        )
    if reconciliation.get("source_inventory_version") != inventory_version:
        errors.append(
            err(
                "E_SOURCE_LINEAGE_STALE",
                "reconciliation source_inventory_version does not match inventory",
                reconciliation_path,
                route="scope-reconciliation-recheck",
                expected=str(inventory_version),
                actual=str(reconciliation.get("source_inventory_version")),
            )
        )
    reviewer_status = reconciliation.get("reviewer_status")
    if reviewer_status not in SOURCE_REVIEWER_STATUSES:
        errors.append(err("E_SCOPE_RECONCILIATION_REVIEWER_STATUS", "reviewer_status is invalid", reconciliation_path, route="scope-reconciliation-recheck"))
    review_required = reconciliation.get("source_obligation_review_required", True)
    if not isinstance(review_required, bool):
        errors.append(err("E_SCOPE_RECONCILIATION_REVIEWER_STATUS", "source_obligation_review_required must be boolean", reconciliation_path, route="scope-reconciliation-recheck"))
    if review_required is True and reviewer_status != "SHIP":
        errors.append(err("E_SCOPE_RECONCILIATION_REVIEWER_NOT_APPROVED", "reviewer_status must be SHIP", reconciliation_path, route="source-obligation-review"))
    if review_required is False and not reconciliation.get("not_required_reason"):
        errors.append(err("E_SCOPE_RECONCILIATION_REVIEWER_STATUS", "reviewer not-required policy needs not_required_reason", reconciliation_path, route="scope-reconciliation-recheck"))
    if reconciliation.get("reviewer_approved") is True and reviewer_status != "SHIP":
        errors.append(
            err(
                "E_SCOPE_RECONCILIATION_REVIEWER_STATUS",
                "reviewer_approved true conflicts with non-SHIP reviewer_status",
                reconciliation_path,
                route="scope-reconciliation-recheck",
            )
        )

    ledger_rows = ledger.get("coverage_rows") if isinstance(ledger, dict) and isinstance(ledger.get("coverage_rows"), list) else []
    row_by_id = {row.get("row_id"): row for row in ledger_rows if isinstance(row, dict) and isinstance(row.get("row_id"), str)}
    inventory_ids = {item["source_item_id"] for item in inventory_items}
    reconciled_by_id: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            errors.append(err("E_SCOPE_RECONCILIATION_SCHEMA", "reconciled item must be a mapping", reconciliation_path, route="scope-reconciliation-recheck"))
            continue
        source_item_id = item.get("source_item_id")
        if not isinstance(source_item_id, str) or not source_item_id:
            errors.append(err("E_SCOPE_RECONCILIATION_SCHEMA", "source_item_id must be a string", reconciliation_path, route="scope-reconciliation-recheck"))
            continue
        if source_item_id in seen:
            errors.append(
                err(
                    "E_SCOPE_RECONCILIATION_DUPLICATE_ITEM",
                    "reconciled source_item_id must be unique",
                    reconciliation_path,
                    route="scope-reconciliation-recheck",
                    source_item_id=source_item_id,
                )
            )
        seen.add(source_item_id)
        reconciled_by_id[source_item_id] = item
        if source_item_id not in inventory_ids:
            errors.append(
                err(
                    "E_SCOPE_RECONCILIATION_INVENTED_ITEM",
                    "reconciliation references a source item not in inventory",
                    reconciliation_path,
                    route="scope-reconciliation-recheck",
                    source_item_id=source_item_id,
                )
            )
        disposition = item.get("disposition")
        if disposition not in SOURCE_DISPOSITIONS:
            errors.append(
                err(
                    "E_SCOPE_RECONCILIATION_SCHEMA",
                    "disposition is invalid",
                    reconciliation_path,
                    route="scope-reconciliation-recheck",
                    source_item_id=source_item_id,
                )
            )
            continue
        obligation_ids = string_list(item.get("obligation_ids", []))
        row_ids = string_list(item.get("coverage_row_ids", []))
        if disposition == "included":
            if not obligation_ids or not row_ids or set(obligation_ids) != set(row_ids):
                errors.append(
                    err(
                        "E_SCOPE_RECONCILIATION_INCLUDED_MAPPING",
                        "included items need matching obligation_ids and coverage_row_ids",
                        reconciliation_path,
                        route="scope-reconciliation-recheck",
                        source_item_id=source_item_id,
                    )
                )
            for row_id in row_ids or []:
                if row_id not in row_by_id:
                    errors.append(
                        err(
                            "E_SOURCE_LEDGER_ROW_MISSING",
                            "included item references a missing ledger row",
                            ledger_path,
                            row_id=row_id,
                            ledger_row_id=row_id,
                            route="coverage-ledger-repair",
                            source_item_id=source_item_id,
                        )
                    )
        elif not item.get("rationale"):
            errors.append(
                err(
                    "E_SCOPE_RECONCILIATION_RATIONALE",
                    "non-included items need structured rationale",
                    reconciliation_path,
                    route="scope-reconciliation-recheck",
                    source_item_id=source_item_id,
                )
            )
    for source_item_id in sorted(inventory_ids - set(reconciled_by_id)):
        errors.append(
            err(
                "E_SCOPE_RECONCILIATION_MISSING_ITEM",
                "inventory item is missing from reconciliation",
                reconciliation_path,
                route="scope-reconciliation-recheck",
                source_item_id=source_item_id,
            )
        )

    scope_digest = canonical_scope_digest([item for item in items if isinstance(item, dict) and isinstance(item.get("source_item_id"), str)])
    if reconciliation.get("accepted_scope_digest") != scope_digest:
        errors.append(
            err(
                "E_SOURCE_LINEAGE_STALE",
                "accepted scope digest does not match reconciled items",
                reconciliation_path,
                route="scope-reconciliation-recheck",
                expected=scope_digest,
                actual=str(reconciliation.get("accepted_scope_digest")),
            )
        )
    if isinstance(decision, dict):
        trigger = decision.get("trigger_evaluation")
        if isinstance(trigger, dict) and trigger.get("accepted_scope_digest") not in {None, scope_digest}:
            errors.append(
                err(
                    "E_SOURCE_LINEAGE_STALE",
                    "coverage decision accepted_scope_digest does not match reconciliation",
                    req_dir_path(reconciliation_path),
                    route="requirement-clarifier-post-review-recheck",
                    expected=scope_digest,
                    actual=str(trigger.get("accepted_scope_digest")),
                )
            )
    if isinstance(ledger, dict):
        first_row_id = next(
            (str(row.get("row_id")) for row in ledger_rows if isinstance(row, dict) and isinstance(row.get("row_id"), str)),
            None,
        )
        if ledger.get("source_inventory_digest") != source_digest:
            errors.append(
                err(
                    "E_SOURCE_LINEAGE_MISSING",
                    "coverage ledger source_inventory_digest is missing or stale",
                    ledger_path,
                    row_id=first_row_id,
                    ledger_row_id=first_row_id,
                    route="coverage-ledger-repair",
                    expected=str(source_digest),
                    actual=str(ledger.get("source_inventory_digest")),
                )
            )
        if ledger.get("source_inventory_version") != inventory_version:
            errors.append(
                err(
                    "E_SOURCE_LINEAGE_STALE",
                    "coverage ledger source_inventory_version is missing or stale",
                    ledger_path,
                    row_id=first_row_id,
                    ledger_row_id=first_row_id,
                    route="coverage-ledger-repair",
                    expected=str(inventory_version),
                    actual=str(ledger.get("source_inventory_version")),
                )
            )
        if ledger.get("accepted_scope_digest") != scope_digest:
            errors.append(
                err(
                    "E_SOURCE_LINEAGE_MISSING",
                    "coverage ledger accepted_scope_digest is missing or stale",
                    ledger_path,
                    row_id=first_row_id,
                    ledger_row_id=first_row_id,
                    route="coverage-ledger-repair",
                    expected=scope_digest,
                    actual=str(ledger.get("accepted_scope_digest")),
                )
            )
        if ledger.get("reconciliation_version") != reconciliation.get("reconciliation_version"):
            errors.append(
                err(
                    "E_SOURCE_LINEAGE_STALE",
                    "coverage ledger reconciliation_version is missing or stale",
                    ledger_path,
                    row_id=first_row_id,
                    ledger_row_id=first_row_id,
                    route="coverage-ledger-repair",
                    expected=str(reconciliation.get("reconciliation_version")),
                    actual=str(ledger.get("reconciliation_version")),
                )
            )
        expected_row_sources: dict[str, set[str]] = {}
        for item in items:
            if not isinstance(item, dict) or item.get("disposition") != "included":
                continue
            source_item_id = item.get("source_item_id")
            for row_id in item.get("coverage_row_ids", []) if isinstance(item.get("coverage_row_ids"), list) else []:
                expected_row_sources.setdefault(str(row_id), set()).add(str(source_item_id))
        row_source_fields_present = any(isinstance(row, dict) and "source_item_ids" in row for row in ledger_rows)
        if row_source_fields_present:
            for row in ledger_rows:
                if not isinstance(row, dict):
                    continue
                row_id = str(row.get("row_id", "unknown"))
                actual_sources = string_list(row.get("source_item_ids", []))
                if actual_sources is None:
                    errors.append(err("E_SOURCE_LEDGER_SOURCE_MISMATCH", "source_item_ids must be a string list", ledger_path, row_id=row_id, ledger_row_id=row_id, route="coverage-ledger-repair"))
                    continue
                for source_item_id in actual_sources:
                    if source_item_id not in inventory_ids:
                        errors.append(
                            err(
                                "E_SOURCE_LEDGER_INVENTED_ITEM",
                                "ledger row references a source item not in inventory",
                                ledger_path,
                                row_id=row_id,
                                ledger_row_id=row_id,
                                route="coverage-ledger-repair",
                                source_item_id=source_item_id,
                            )
                        )
                expected_sources = expected_row_sources.get(row_id, set())
                if set(actual_sources) != expected_sources:
                    errors.append(
                        err(
                            "E_SOURCE_LEDGER_SOURCE_MISMATCH",
                            "ledger row source_item_ids do not match reconciliation mappings",
                            ledger_path,
                            row_id=row_id,
                            ledger_row_id=row_id,
                            route="coverage-ledger-repair",
                            expected=",".join(sorted(expected_sources)),
                            actual=",".join(sorted(actual_sources)),
                        )
                    )
    return errors


def req_dir_path(path: Path) -> Path:
    return path.parent / "coverage-decision.yml"


def validate_source_state(
    req_dir: Path,
    decision: dict[str, Any] | None,
    ledger: dict[str, Any] | None,
    ledger_path: Path,
) -> list[Error]:
    if not source_validation_active(req_dir, decision, ledger):
        return []
    errors: list[Error] = []
    inventory_path = req_dir / "source-inventory.yml"
    reconciliation_path = req_dir / "scope-reconciliation.yml"
    if not inventory_path.exists():
        errors.append(err("E_SOURCE_INVENTORY_REQUIRED", "source-inventory.yml is required", inventory_path, route="source-inventory-rebuild"))
    if not reconciliation_path.exists():
        errors.append(
            err(
                "E_SCOPE_RECONCILIATION_REQUIRED",
                "scope-reconciliation.yml is required",
                reconciliation_path,
                route="scope-reconciliation-recheck",
            )
        )
    if errors:
        return errors
    inventory, inventory_errors = load_yaml_file(inventory_path)
    reconciliation, reconciliation_errors = load_yaml_file(reconciliation_path)
    errors.extend(inventory_errors)
    errors.extend(reconciliation_errors)
    if errors:
        return errors
    assert isinstance(inventory, dict)
    assert isinstance(reconciliation, dict)
    inventory_items, source_digest, inventory_validation_errors = validate_source_inventory(inventory, inventory_path)
    errors.extend(inventory_validation_errors)
    if inventory_items:
        errors.extend(
            validate_source_reconciliation(
                reconciliation,
                reconciliation_path,
                inventory_items,
                inventory.get("inventory_version"),
                source_digest,
                ledger,
                ledger_path,
                decision,
            )
        )
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
            errors.extend(validate_source_state(req_dir, decision, ledger, ledger_path))
    else:
        errors.extend(validate_source_state(req_dir, decision, None, ledger_path))
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
    errors.extend(validate_source_state(req_dir, decision, ledger, ledger_path))
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
    decision: dict[str, Any] | None = None
    if decision_path.exists():
        loaded_decision, decision_errors = load_yaml_file(decision_path)
        errors.extend(decision_errors)
        if isinstance(loaded_decision, dict):
            decision = loaded_decision
            errors.extend(validate_decision(req_dir, decision, decision_path))
    if ledger_path.exists():
        ledger, ledger_errors = load_yaml_file(ledger_path)
        errors.extend(ledger_errors)
        if isinstance(ledger, dict):
            errors.extend(validate_ledger_schema(req_dir, ledger, ledger_path))
            errors.extend(validate_source_state(req_dir, decision if isinstance(decision, dict) else None, ledger, ledger_path))
    elif isinstance(decision, dict):
        errors.extend(validate_source_state(req_dir, decision, None, ledger_path))
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
