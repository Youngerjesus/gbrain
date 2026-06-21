#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required for sandbox fixture verification") from exc


ROOT = Path(__file__).resolve().parents[1]
SANDBOX = ROOT / "sandbox" / "mompick-find-main-reference-parity"
CLI = ROOT / "scripts" / "coverage_ledger.py"
EXPECTED_OBLIGATIONS = [
    ("search-entry", "Search entry field", "src.find.search_entry", True),
    ("recent-products", "Recent product rail", "src.find.recent_product_rail", False),
    ("grouped-categories", "Grouped category rows", "src.find.grouped_category_rows", False),
    ("category-drilldown", "Category drilldown affordance", "src.find.category_drilldown", False),
    ("first-viewport-structure", "First viewport structure", "src.find.first_viewport_structure", False),
]
GENERIC_SETUP_ERROR_CODES = {
    "E_DECISION_REQUIRED",
    "E_DECISION_MISSING_RECHECK",
    "E_LEDGER_REQUIRED_MISSING",
    "E_YAML_ROOT",
    "E_YAML_PARSE",
    "E_EVIDENCE_PATH_MISSING",
    "E_EVIDENCE_PATH_ESCAPE",
}


def load_manifest() -> dict[str, Any]:
    path = SANDBOX / "manifest.yml"
    if not path.is_file():
        raise AssertionError(f"missing fixture file: {path.relative_to(ROOT)}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError("manifest must be a mapping")
    return data


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
    canonical = []
    for item in sorted(items, key=lambda value: value["source_item_id"]):
        canonical.append(
            {
                "source_item_id": item["source_item_id"],
                "disposition": item["disposition"],
                "obligation_ids": sorted(set(item.get("obligation_ids", []))),
                "coverage_row_ids": sorted(set(item.get("coverage_row_ids", []))),
                "rationale": item.get("rationale", ""),
            }
        )
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def obligation_tuples(manifest: dict[str, Any]) -> list[tuple[str, str, str, bool]]:
    obligations = manifest.get("obligations")
    if not isinstance(obligations, list):
        raise AssertionError("manifest obligations must be a list")
    return [
        (item.get("obligation_id"), item.get("label"), item.get("source_item_id"), item.get("search_only_subset"))
        for item in obligations
        if isinstance(item, dict)
    ]


def source_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source_item_id": source_item_id,
            "source_method": "human_manifest",
            "source_refs": ["sandbox/mompick-find-main-reference-parity/manifest.yml#obligations"],
            "metadata": {
                "obligation_id": obligation_id,
                "label": label,
                "search_only_subset": is_search_only,
            },
        }
        for obligation_id, label, source_item_id, is_search_only in obligation_tuples(manifest)
    ]


def run_validator(requirement_dir: Path) -> tuple[int, dict[str, Any]]:
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "validate",
            "--mode",
            "readiness",
            "--requirement-dir",
            str(requirement_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout.strip() or result.stderr.strip())
    return result.returncode, payload


def build_fixture(root: Path, manifest: dict[str, Any], *, search_only: bool = False) -> None:
    items = source_items(manifest)
    source_digest = canonical_source_inventory_digest(items)
    reconciled = []
    for obligation_id, label, source_item_id, is_search_only in obligation_tuples(manifest):
        if search_only and not is_search_only:
            continue
        reconciled.append(
            {
                "source_item_id": source_item_id,
                "disposition": "included",
                "obligation_ids": ["find.main_reference"],
                "coverage_row_ids": ["find.main_reference"],
                "rationale": "Find main reference obligation is included.",
            }
        )
    scope_digest = canonical_scope_digest(reconciled)
    write(root / "requirements.md", "# Find Main Fixture\n")
    write(root / "evidence.md", "# Evidence\n")
    write(
        root / "coverage-decision.yml",
        f"""
        requirement_id: find-main-fixture
        decision_version: 1
        ledger_required: true
        ledger_path: coverage-ledger.yml
        decided_by_gate: requirement-clarifier
        decided_at: "2026-06-21T22:15:00+09:00"
        trigger_evaluation:
          accepted_scope_digest: {scope_digest}
          signals:
            source_obligation_inventory_required: true
            reference_parity_loss_pattern: true
          broad_work_detected: true
        source_refs:
          - sandbox/mompick-find-main-reference-parity/manifest.yml#obligations
        """,
    )
    lines = ["requirement_id: find-main-fixture", "inventory_version: 1", f"source_inventory_digest: {source_digest}", "source_items:"]
    for item in items:
        lines.extend(
            [
                f"  - source_item_id: {item['source_item_id']}",
                f"    title: {item['metadata']['label']}",
                "    source_method: human_manifest",
                "    source_refs:",
                "      - sandbox/mompick-find-main-reference-parity/manifest.yml#obligations",
                "    metadata:",
                f"      obligation_id: {item['metadata']['obligation_id']}",
                f"      label: {item['metadata']['label']}",
                f"      search_only_subset: {str(item['metadata']['search_only_subset']).lower()}",
            ]
        )
    write(root / "source-inventory.yml", "\n".join(lines) + "\n")
    lines = [
        "requirement_id: find-main-fixture",
        "reconciliation_version: 1",
        f"source_inventory_digest: {source_digest}",
        "source_inventory_version: 1",
        f"accepted_scope_digest: {scope_digest}",
        "reviewer_status: SHIP",
        "source_obligation_review_required: true",
        "reconciled_items:",
    ]
    for item in reconciled:
        lines.extend(
            [
                f"  - source_item_id: {item['source_item_id']}",
                "    disposition: included",
                "    obligation_ids:",
                "      - find.main_reference",
                "    coverage_row_ids:",
                "      - find.main_reference",
                f"    rationale: {item['rationale']}",
            ]
        )
    write(root / "scope-reconciliation.yml", "\n".join(lines) + "\n")
    row_sources = [item["source_item_id"] for item in reconciled]
    lines = [
        "requirement_id: find-main-fixture",
        "ledger_version: 1",
        "ledger_required: true",
        "status: verified",
        "last_updated_by_gate: sandbox-fixture",
        'last_updated_at: "2026-06-21T22:15:00+09:00"',
        f"source_inventory_digest: {source_digest}",
        "source_inventory_version: 1",
        f"accepted_scope_digest: {scope_digest}",
        "reconciliation_version: 1",
        "closure_policy:",
        "  allowed_closed_statuses:",
        "    - verified",
        "    - not_required_with_reason",
        "    - deferred_with_user_acceptance",
        "  blocking_statuses:",
        "    - planned",
        "    - missing",
        "    - blocked",
        "    - stale_needs_recheck",
        "  evidence_rule: typed_evidence_required",
        "coverage_rows:",
        "  - row_id: find.main_reference",
        "    required: true",
        "    obligation_type: regression_fixture",
        "    description: Find main reference obligations are mapped.",
        "    source_refs:",
        "      - sandbox/mompick-find-main-reference-parity/manifest.yml#obligations",
        "    source_item_ids:",
    ]
    lines.extend(f"      - {source_id}" for source_id in row_sources)
    lines.extend(
        [
            "    data_condition: find main obligations represented",
            "    required_evidence:",
            "      - negative_fixture_test_suite",
            "      - expected_error_assertions",
            "    status: verified",
            "    evidence_refs:",
            "      - type: negative_fixture_test_suite",
            "        ref: tests/verify_sandbox_mompick_find_main.py",
            "        recorded_in: sandbox/mompick-find-main-reference-parity/generated",
            "      - type: expected_error_assertions",
            "        ref: E_SCOPE_RECONCILIATION_MISSING_ITEM",
            "        recorded_in: sandbox/mompick-find-main-reference-parity/generated",
            "    recorded_in:",
            "      - sandbox/mompick-find-main-reference-parity/generated",
        ]
    )
    write(root / "coverage-ledger.yml", "\n".join(lines) + "\n")


class MomPickFindMainSandboxTest(unittest.TestCase):
    def test_manifest_records_exact_find_main_obligations(self) -> None:
        manifest = load_manifest()
        self.assertEqual(obligation_tuples(manifest), EXPECTED_OBLIGATIONS)
        search_only = [obligation_id for obligation_id, _, _, flag in EXPECTED_OBLIGATIONS if flag]
        self.assertEqual(manifest.get("search_only_subset_obligation_ids"), search_only)

    def test_positive_generated_fixture_passes_readiness(self) -> None:
        manifest = load_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "positive"
            build_fixture(root, manifest)
            returncode, payload = run_validator(root)
        self.assertEqual(returncode, 0, payload)
        self.assertEqual(payload["status"], "pass")

    def test_search_only_generated_fixture_fails_source_obligation_readiness(self) -> None:
        manifest = load_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "negative"
            build_fixture(root, manifest, search_only=True)
            returncode, payload = run_validator(root)
        self.assertNotEqual(returncode, 0, payload)
        self.assertEqual(payload["status"], "fail")
        codes = set(payload.get("error_codes", []))
        self.assertIn("E_SCOPE_RECONCILIATION_MISSING_ITEM", codes)
        self.assertTrue(codes.isdisjoint(GENERIC_SETUP_ERROR_CODES), payload)
        self.assertIn("scope-reconciliation-recheck", set(payload.get("routes", [])))
        missing = {
            error.get("source_item_id")
            for error in payload.get("errors", [])
            if error.get("code") == "E_SCOPE_RECONCILIATION_MISSING_ITEM"
        }
        self.assertIn("src.find.recent_product_rail", missing)
        self.assertIn("src.find.grouped_category_rows", missing)
        self.assertIn("src.find.category_drilldown", missing)
        self.assertIn("src.find.first_viewport_structure", missing)


if __name__ == "__main__":
    unittest.main()
