#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "coverage_ledger.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )


def parse_result(result: subprocess.CompletedProcess[str]) -> dict:
    stream = result.stdout if result.stdout.strip() else result.stderr
    try:
        return json.loads(stream)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"validator did not emit JSON: {stream}") from exc


def decision_text(*, required: bool = True, stale: bool = False, ledger_path: str = "coverage-ledger.yml") -> str:
    if required:
        branch = f'ledger_path: "{ledger_path}"'
    else:
        branch = """
ledger_not_required:
  reason: "Small mechanical copy edits only."
  risk_assessment: "low"
  accepted_scope_refs:
    - requirements/demo/requirements.md#scope
        """
    updated = "2026-06-19T10:00:00Z" if stale else "2026-06-20T10:00:00Z"
    return f"""requirement_id: demo
decision_version: 1
ledger_required: {str(required).lower()}
decided_by_gate: requirement-clarifier
decided_at: "{updated}"
trigger_evaluation:
  accepted_scope_digest: "current-scope"
  signals:
    many_acceptance_criteria: {str(required).lower()}
  broad_work_detected: {str(required).lower()}
source_refs:
  - requirements/demo/requirements.md#Acceptance-Criteria
{branch}
"""


def closed_ledger_text(evidence_path: str = "evidence/ui.txt", evidence_hash: str | None = None) -> str:
    hash_line = f'\n            artifact_hash: "{evidence_hash}"' if evidence_hash else ""
    return f"""
    requirement_id: demo
    ledger_version: 1
    ledger_required: true
    status: verified
    last_updated_by_gate: implementation
    last_updated_at: "2026-06-20T10:10:00Z"
    closure_policy:
      allowed_closed_statuses:
        - verified
        - not_required_with_reason
        - deferred_with_user_acceptance
      blocking_statuses:
        - planned
        - missing
        - blocked
        - stale_needs_recheck
      evidence_rule: typed_evidence_required
    coverage_rows:
      - row_id: ui.ingredient.states
        required: true
        obligation_type: ui_state
        description: Ingredient UI states are represented with DOM and screenshot evidence.
        source_refs:
          - requirements/demo/requirements.md#AC-1
        data_condition: caution chips and grouped ingredients are rendered
        required_evidence:
          - dom_assertion
          - screenshot
        status: verified
        evidence_refs:
          - type: dom_assertion
            ref: dom-check
            recorded_in: requirements/demo/evidence.md
            path: evidence/dom.txt
          - type: screenshot
            ref: screenshot-check
            recorded_in: requirements/demo/evidence.md
            path: {evidence_path}{hash_line}
        recorded_in:
          - requirements/demo/evidence.md
    """


def canonical_source_inventory_digest(items: list[dict]) -> str:
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


def canonical_scope_digest(items: list[dict]) -> str:
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


def source_inventory_text(items: list[dict], digest: str | None = None, inventory_version: int = 1) -> str:
    digest = digest or canonical_source_inventory_digest(items)
    lines = [
        "requirement_id: demo",
        f"inventory_version: {inventory_version}",
        f"source_inventory_digest: {digest}",
        "source_items:",
    ]
    for item in items:
        lines.extend(
            [
                f"  - source_item_id: {item['source_item_id']}",
                f"    title: {item.get('title', item['source_item_id'])}",
                f"    source_method: {item['source_method']}",
                "    source_refs:",
            ]
        )
        lines.extend(f"      - {ref}" for ref in item["source_refs"])
        if "metadata" in item:
            lines.append("    metadata:")
            for key, value in item["metadata"].items():
                lines.append(f"      {key}: {value}")
    return "\n".join(lines) + "\n"


def source_reconciliation_text(
    *,
    source_inventory_digest: str,
    source_inventory_version: int = 1,
    accepted_scope_digest: str,
    reconciliation_version: int = 1,
    items: list[dict],
    reviewer_status: str = "SHIP",
    review_required: bool = True,
    not_required_reason: str | None = None,
    reviewer_approved: bool | None = None,
) -> str:
    lines = [
        "requirement_id: demo",
        f"reconciliation_version: {reconciliation_version}",
        f"source_inventory_digest: {source_inventory_digest}",
        f"source_inventory_version: {source_inventory_version}",
        f"accepted_scope_digest: {accepted_scope_digest}",
        f"reviewer_status: {reviewer_status}",
        f"source_obligation_review_required: {str(review_required).lower()}",
    ]
    if reviewer_approved is not None:
        lines.append(f"reviewer_approved: {str(reviewer_approved).lower()}")
    if not_required_reason:
        lines.append(f"not_required_reason: {not_required_reason}")
    lines.append("reconciled_items:")
    for item in items:
        lines.extend([f"  - source_item_id: {item['source_item_id']}", f"    disposition: {item['disposition']}"])
        if "obligation_ids" in item:
            lines.append("    obligation_ids:")
            lines.extend(f"      - {row_id}" for row_id in item.get("obligation_ids", []))
        if "coverage_row_ids" in item:
            lines.append("    coverage_row_ids:")
            lines.extend(f"      - {row_id}" for row_id in item.get("coverage_row_ids", []))
        if item.get("rationale"):
            lines.append(f"    rationale: {item['rationale']}")
    return "\n".join(lines) + "\n"


def source_ledger_text(
    *,
    source_inventory_digest: str | None = None,
    source_inventory_version: int | None = None,
    accepted_scope_digest: str | None = None,
    reconciliation_version: int | None = None,
    row_source_item_ids: list[str] | None = None,
) -> str:
    lines = [
        "requirement_id: demo",
        "ledger_version: 1",
        "ledger_required: true",
        "status: verified",
        'last_updated_by_gate: implementation',
        'last_updated_at: "2026-06-20T10:10:00Z"',
    ]
    if source_inventory_digest is not None:
        lines.append(f"source_inventory_digest: {source_inventory_digest}")
    if source_inventory_version is not None:
        lines.append(f"source_inventory_version: {source_inventory_version}")
    if accepted_scope_digest is not None:
        lines.append(f"accepted_scope_digest: {accepted_scope_digest}")
    if reconciliation_version is not None:
        lines.append(f"reconciliation_version: {reconciliation_version}")
    lines.extend(
        [
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
            "  - row_id: source.alpha",
            "    required: true",
            "    obligation_type: workflow_policy",
            "    description: Source alpha maps to a covered workflow policy row.",
            "    source_refs:",
            "      - requirements/demo/requirements.md#AC-source",
            "    data_condition: source alpha is included",
            "    required_evidence:",
            "      - structured_contract_fixture",
            "      - positive_negative_trigger_tests",
            "    status: verified",
        ]
    )
    if row_source_item_ids is not None:
        lines.append("    source_item_ids:")
        lines.extend(f"      - {item_id}" for item_id in row_source_item_ids)
    lines.extend(
        [
            "    evidence_refs:",
            "      - type: structured_contract_fixture",
            "        ref: source-contract",
            "        recorded_in: requirements/demo/evidence.md",
            "        path: evidence/source_contract.txt",
            "      - type: positive_negative_trigger_tests",
            "        ref: source-trigger",
            "        recorded_in: requirements/demo/evidence.md",
            "        path: evidence/trigger.txt",
            "    recorded_in:",
            "      - requirements/demo/evidence.md",
        ]
    )
    return "\n".join(lines) + "\n"


class CoverageLedgerValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.req = self.root / "requirements" / "demo"
        self.req.mkdir(parents=True)
        write(self.req / "requirements.md", "# Demo\n\n## Acceptance Criteria\n\ncurrent-scope\n")
        write(self.req / "evidence.md", "# Evidence\n")
        write(self.req / "evidence" / "dom.txt", "dom ok\n")
        write(self.req / "evidence" / "ui.txt", "screenshot ok\n")
        write(self.req / "coverage-decision.yml", decision_text())
        write(self.req / "coverage-ledger.yml", closed_ledger_text())

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def assert_cli_ok(self, mode: str, req: Path | None = None, cwd: Path | None = None) -> dict:
        result = run_cli("validate", "--mode", mode, "--requirement-dir", str(req or self.req), cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = parse_result(result)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["mode"], mode)
        return payload

    def assert_cli_fails(self, mode: str, code: str, *, row_id: str | None = None) -> dict:
        result = run_cli("validate", "--mode", mode, "--requirement-dir", str(self.req))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        payload = parse_result(result)
        self.assertEqual(payload["status"], "fail")
        self.assertIn(code, payload["error_codes"])
        if row_id is not None:
            self.assertTrue(any(error.get("row_id") == row_id for error in payload["errors"]), payload)
        self.assertTrue(all("path" in error for error in payload["errors"]), payload)
        return payload

    def install_valid_source_contract(self) -> tuple[str, str]:
        write(self.req / "evidence" / "source_contract.txt", "source contract ok\n")
        write(self.req / "evidence" / "trigger.txt", "trigger ok\n")
        items = [
            {
                "source_item_id": "SRC-001",
                "title": "Source alpha",
                "source_method": "manual",
                "source_refs": ["requirements/demo/requirements.md#AC-source"],
                "metadata": {"owner": "tests"},
            }
        ]
        source_digest = canonical_source_inventory_digest(items)
        reconciled = [
            {
                "source_item_id": "SRC-001",
                "disposition": "included",
                "obligation_ids": ["source.alpha"],
                "coverage_row_ids": ["source.alpha"],
            }
        ]
        scope_digest = canonical_scope_digest(reconciled)
        write(self.req / "source-inventory.yml", source_inventory_text(items, source_digest))
        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=scope_digest,
                items=reconciled,
            ),
        )
        write(self.req / "coverage-ledger.yml", source_ledger_text(
            source_inventory_digest=source_digest,
            source_inventory_version=1,
            accepted_scope_digest=scope_digest,
            reconciliation_version=1,
            row_source_item_ids=["SRC-001"],
        ))
        write(
            self.req / "coverage-decision.yml",
            decision_text().replace(
                "signals:\n    many_acceptance_criteria: true",
                "signals:\n    many_acceptance_criteria: true\n    source_obligation_inventory_required: true",
            ).replace('accepted_scope_digest: "current-scope"', f'accepted_scope_digest: "{scope_digest}"'),
        )
        return source_digest, scope_digest

    def test_valid_schema_readiness_and_closure_pass_from_external_cwd(self) -> None:
        self.assert_cli_ok("schema")
        self.assert_cli_ok("readiness")
        with tempfile.TemporaryDirectory() as other:
            self.assert_cli_ok("closure", cwd=Path(other))

    def test_valid_source_inventory_reconciliation_and_lineage_pass(self) -> None:
        self.install_valid_source_contract()
        self.assert_cli_ok("schema")
        self.assert_cli_ok("readiness")
        self.assert_cli_ok("closure")

    def test_source_validation_activation_requires_artifacts_and_reports_routes(self) -> None:
        write(
            self.req / "coverage-decision.yml",
            decision_text().replace(
                "signals:\n    many_acceptance_criteria: true",
                "signals:\n    many_acceptance_criteria: true\n    source_obligation_inventory_required: true",
            ),
        )
        payload = self.assert_cli_fails("readiness", "E_SOURCE_INVENTORY_REQUIRED")
        self.assertIn("E_SCOPE_RECONCILIATION_REQUIRED", payload["error_codes"])
        self.assertEqual(
            payload["routes"],
            ["scope-reconciliation-recheck", "source-inventory-rebuild"],
        )
        self.assertEqual(payload["route"], "source-inventory-rebuild")

        self.install_valid_source_contract()
        os.remove(self.req / "scope-reconciliation.yml")
        payload = self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_REQUIRED")
        self.assertTrue(any(error.get("route") == "scope-reconciliation-recheck" for error in payload["errors"]))

        os.remove(self.req / "source-inventory.yml")
        payload = self.assert_cli_fails("readiness", "E_SOURCE_INVENTORY_REQUIRED")
        self.assertIn("E_SCOPE_RECONCILIATION_REQUIRED", payload["error_codes"])

    def test_source_inventory_schema_rejects_empty_duplicate_and_coerced_item_ids(self) -> None:
        source_digest, scope_digest = self.install_valid_source_contract()
        write(
            self.req / "source-inventory.yml",
            f"""
            requirement_id: demo
            inventory_version: 1
            source_inventory_digest: {source_digest}
            source_items: []
            """,
        )
        self.assert_cli_fails("readiness", "E_SOURCE_INVENTORY_SCHEMA")

        items = [
            {
                "source_item_id": "SRC-001",
                "source_method": "manual",
                "source_refs": ["requirements/demo/requirements.md#AC-source"],
            },
            {
                "source_item_id": "SRC-001",
                "source_method": "manual",
                "source_refs": ["requirements/demo/requirements.md#AC-other"],
            },
        ]
        write(self.req / "source-inventory.yml", source_inventory_text(items, canonical_source_inventory_digest(items)))
        self.assert_cli_fails("readiness", "E_SOURCE_ITEM_ID_DUPLICATE")

        write(
            self.req / "source-inventory.yml",
            f"""
            requirement_id: demo
            inventory_version: 1
            source_inventory_digest: {source_digest}
            source_items:
              - source_item_id: 123
                source_method: manual
                source_refs:
                  - requirements/demo/requirements.md#AC-source
            """,
        )
        payload = self.assert_cli_fails("readiness", "E_SOURCE_INVENTORY_SCHEMA")
        self.assertIn("source-inventory.yml", payload["errors"][0]["path"])

        write(self.req / "source-inventory.yml", "- not a mapping\n")
        self.assert_cli_fails("readiness", "E_YAML_ROOT")

        write(
            self.req / "source-inventory.yml",
            f"""
            requirement_id: demo
            inventory_version: 1
            source_inventory_digest: {source_digest}
            source_items:
              - source_item_id: SRC-001
                source_method: manual
                source_refs: []
                metadata:
                  owner: tests
            """,
        )
        self.assert_cli_fails("readiness", "E_SOURCE_ITEM_REF_MISSING")

        write(
            self.req / "source-inventory.yml",
            f"""
            requirement_id: demo
            inventory_version: 1
            source_inventory_digest: {source_digest}
            source_items:
              - source_item_id: SRC-001
                source_method: telepathy
                source_refs:
                  - requirements/demo/requirements.md#AC-source
                metadata:
                  owner: tests
            """,
        )
        self.assert_cli_fails("readiness", "E_SOURCE_INVENTORY_SCHEMA")

        write(
            self.req / "coverage-ledger.yml",
            source_ledger_text(
                source_inventory_digest=source_digest,
                source_inventory_version=1,
                accepted_scope_digest=scope_digest,
                reconciliation_version=1,
            ),
        )

    def test_source_inventory_methods_require_required_metadata_or_extraction_evidence(self) -> None:
        for method in ["manual", "llm_observed", "human_manifest", "extracted", "hybrid"]:
            with self.subTest(method=method):
                self.install_valid_source_contract()
                items = [
                    {
                        "source_item_id": "SRC-001",
                        "source_method": method,
                        "source_refs": ["requirements/demo/requirements.md#AC-source"],
                        "metadata": {
                            "owner": "tests",
                            "extraction_count": 1,
                            "extraction_digest": "sha256:1234567890abcdef",
                        },
                    }
                ]
                source_digest = canonical_source_inventory_digest(items)
                reconciled = [
                    {
                        "source_item_id": "SRC-001",
                        "disposition": "included",
                        "obligation_ids": ["source.alpha"],
                        "coverage_row_ids": ["source.alpha"],
                    }
                ]
                scope_digest = canonical_scope_digest(reconciled)
                write(self.req / "source-inventory.yml", source_inventory_text(items, source_digest))
                write(
                    self.req / "scope-reconciliation.yml",
                    source_reconciliation_text(
                        source_inventory_digest=source_digest,
                        accepted_scope_digest=scope_digest,
                        items=reconciled,
                    ),
                )
                write(
                    self.req / "coverage-ledger.yml",
                    source_ledger_text(
                        source_inventory_digest=source_digest,
                        source_inventory_version=1,
                        accepted_scope_digest=scope_digest,
                        reconciliation_version=1,
                        row_source_item_ids=["SRC-001"],
                    ),
                )
                self.assert_cli_ok("readiness")

        self.install_valid_source_contract()
        items = [
            {
                "source_item_id": "SRC-001",
                "source_method": "extracted",
                "source_refs": ["requirements/demo/requirements.md#AC-source"],
            }
        ]
        write(self.req / "source-inventory.yml", source_inventory_text(items, canonical_source_inventory_digest(items)))
        payload = self.assert_cli_fails("readiness", "E_SOURCE_INVENTORY_SCHEMA")
        self.assertTrue(any(error.get("source_item_id") == "SRC-001" for error in payload["errors"]))

    def test_reconciliation_completeness_mapping_and_prose_override_fail(self) -> None:
        source_digest, scope_digest = self.install_valid_source_contract()
        write(self.req / "progress.md", "status: Ready\nsummary: prose says all source obligations are complete\n")
        write(self.req / "reviewer.txt", "SHIP: looks complete in prose only\n")
        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=scope_digest,
                items=[],
            ),
        )
        payload = self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_MISSING_ITEM")
        self.assertTrue(any(error.get("source_item_id") == "SRC-001" for error in payload["errors"]))

        reconciled = [
            {
                "source_item_id": "SRC-001",
                "disposition": "included",
                "obligation_ids": ["source.alpha"],
                "coverage_row_ids": ["source.missing"],
            }
        ]
        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=canonical_scope_digest(reconciled),
                items=reconciled,
            ),
        )
        payload = self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_INCLUDED_MAPPING")
        self.assertTrue(any(error.get("source_item_id") == "SRC-001" for error in payload["errors"]))
        self.assertIn("E_SOURCE_LEDGER_ROW_MISSING", payload["error_codes"])

        reconciled = [
            {
                "source_item_id": "SRC-001",
                "disposition": "included",
                "obligation_ids": ["source.alpha"],
                "coverage_row_ids": ["source.alpha"],
            }
        ]
        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=canonical_scope_digest(reconciled),
                items=reconciled,
            ),
        )
        write(
            self.req / "coverage-ledger.yml",
            source_ledger_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=canonical_scope_digest(reconciled),
                row_source_item_ids=["SRC-INVENTED"],
            ),
        )
        payload = self.assert_cli_fails("readiness", "E_SOURCE_LEDGER_SOURCE_MISMATCH")
        self.assertIn("E_SOURCE_LEDGER_INVENTED_ITEM", payload["error_codes"])

    def test_reviewer_not_required_policy_does_not_bypass_mapping_or_lineage(self) -> None:
        source_digest, scope_digest = self.install_valid_source_contract()
        reconciled = [
            {
                "source_item_id": "SRC-001",
                "disposition": "included",
                "obligation_ids": [],
                "coverage_row_ids": [],
            }
        ]
        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=canonical_scope_digest(reconciled),
                items=reconciled,
                reviewer_status="FINDINGS",
                review_required=False,
                not_required_reason="Requirement 010 owns the reviewer agent.",
            ),
        )
        payload = self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_INCLUDED_MAPPING")
        self.assertNotIn("E_SCOPE_RECONCILIATION_REVIEWER_NOT_APPROVED", payload["error_codes"])

        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=scope_digest,
                items=[
                    {
                        "source_item_id": "SRC-001",
                        "disposition": "included",
                        "obligation_ids": ["source.alpha"],
                        "coverage_row_ids": ["source.alpha"],
                    }
                ],
                reviewer_status="FINDINGS",
            ),
        )
        self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_REVIEWER_NOT_APPROVED")

    def test_reconciliation_schema_rejects_invalid_duplicate_missing_reviewer_and_missing_rationale(self) -> None:
        source_digest, scope_digest = self.install_valid_source_contract()
        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=scope_digest,
                items=[
                    {
                        "source_item_id": "SRC-001",
                        "disposition": "telepathic",
                        "obligation_ids": ["source.alpha"],
                        "coverage_row_ids": ["source.alpha"],
                    }
                ],
            ),
        )
        self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_SCHEMA")

        duplicate_items = [
            {
                "source_item_id": "SRC-001",
                "disposition": "included",
                "obligation_ids": ["source.alpha"],
                "coverage_row_ids": ["source.alpha"],
            },
            {
                "source_item_id": "SRC-001",
                "disposition": "included",
                "obligation_ids": ["source.alpha"],
                "coverage_row_ids": ["source.alpha"],
            },
        ]
        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=canonical_scope_digest(duplicate_items),
                items=duplicate_items,
            ),
        )
        payload = self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_DUPLICATE_ITEM")
        self.assertTrue(any(error.get("source_item_id") == "SRC-001" for error in payload["errors"]))

        write(
            self.req / "scope-reconciliation.yml",
            f"""
            requirement_id: demo
            reconciliation_version: 1
            accepted_scope_digest: {scope_digest}
            reviewer_status: SHIP
            source_obligation_review_required: true
            reconciled_items: []
            """,
        )
        self.assert_cli_fails("readiness", "E_REQUIRED_FIELD")

        write(
            self.req / "scope-reconciliation.yml",
            f"""
            requirement_id: demo
            reconciliation_version: 1
            source_inventory_digest: {source_digest}
            source_inventory_version: 1
            accepted_scope_digest: {scope_digest}
            source_obligation_review_required: true
            reviewer_summary: "SHIP in prose only"
            reconciled_items: []
            """,
        )
        self.assert_cli_fails("readiness", "E_REQUIRED_FIELD")

        invented = [
            {
                "source_item_id": "SRC-INVENTED",
                "disposition": "included",
                "obligation_ids": ["source.alpha"],
                "coverage_row_ids": ["source.alpha"],
            }
        ]
        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=canonical_scope_digest(invented),
                items=invented,
            ),
        )
        self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_INVENTED_ITEM")

        excluded = [
            {
                "source_item_id": "SRC-001",
                "disposition": "excluded",
            }
        ]
        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=canonical_scope_digest(excluded),
                items=excluded,
            ),
        )
        self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_RATIONALE")

        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=scope_digest,
                items=[
                    {
                        "source_item_id": "SRC-001",
                        "disposition": "included",
                        "obligation_ids": ["source.alpha"],
                        "coverage_row_ids": ["source.alpha"],
                    }
                ],
                reviewer_status="MAYBE",
            ),
        )
        self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_REVIEWER_STATUS")

        for status in ["BLOCKED_INVALID", "BLOCKED_UNAVAILABLE"]:
            with self.subTest(status=status):
                write(
                    self.req / "scope-reconciliation.yml",
                    source_reconciliation_text(
                        source_inventory_digest=source_digest,
                        accepted_scope_digest=scope_digest,
                        items=[
                            {
                                "source_item_id": "SRC-001",
                                "disposition": "included",
                                "obligation_ids": ["source.alpha"],
                                "coverage_row_ids": ["source.alpha"],
                            }
                        ],
                        reviewer_status=status,
                    ),
                )
                payload = self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_REVIEWER_NOT_APPROVED")
                self.assertNotIn("E_SCOPE_RECONCILIATION_REVIEWER_STATUS", payload["error_codes"])

        write(
            self.req / "scope-reconciliation.yml",
            source_reconciliation_text(
                source_inventory_digest=source_digest,
                accepted_scope_digest=scope_digest,
                items=[
                    {
                        "source_item_id": "SRC-001",
                        "disposition": "included",
                        "obligation_ids": ["source.alpha"],
                        "coverage_row_ids": ["source.alpha"],
                    }
                ],
                reviewer_status="FINDINGS",
                reviewer_approved=True,
            ),
        )
        self.assert_cli_fails("readiness", "E_SCOPE_RECONCILIATION_REVIEWER_STATUS")

    def test_source_lineage_detects_stale_digest_and_missing_ledger_lineage(self) -> None:
        source_digest, scope_digest = self.install_valid_source_contract()
        write(
            self.req / "source-inventory.yml",
            """
            requirement_id: demo
            inventory_version: 1
            source_inventory_digest: sha256:stale
            source_items:
              - source_item_id: SRC-001
                source_method: manual
                source_refs:
                  - requirements/demo/requirements.md#AC-source
                  - requirements/demo/requirements.md#AC-new
                metadata:
                  owner: tests
            """,
        )
        payload = self.assert_cli_fails("readiness", "E_SOURCE_LINEAGE_STALE")
        self.assertTrue(any(error.get("expected") and error.get("actual") for error in payload["errors"]))

        self.install_valid_source_contract()
        write(self.req / "coverage-ledger.yml", source_ledger_text(row_source_item_ids=["SRC-001"]))
        payload = self.assert_cli_fails("closure", "E_SOURCE_LINEAGE_MISSING")
        self.assertTrue(any(error.get("ledger_row_id") == "source.alpha" for error in payload["errors"]))

        write(
            self.req / "coverage-ledger.yml",
            source_ledger_text(
                source_inventory_digest=source_digest,
                source_inventory_version=1,
                accepted_scope_digest=scope_digest,
                reconciliation_version=1,
            ),
        )

    def test_source_lineage_rejects_inventory_and_reconciliation_version_changes(self) -> None:
        self.install_valid_source_contract()
        text = (self.req / "source-inventory.yml").read_text(encoding="utf-8")
        write(self.req / "source-inventory.yml", text.replace("inventory_version: 1", "inventory_version: 2"))
        payload = self.assert_cli_fails("closure", "E_SOURCE_LINEAGE_STALE")
        self.assertTrue(any(error.get("expected") == "2" and error.get("actual") == "1" for error in payload["errors"]))

        self.install_valid_source_contract()
        text = (self.req / "scope-reconciliation.yml").read_text(encoding="utf-8")
        write(self.req / "scope-reconciliation.yml", text.replace("reconciliation_version: 1", "reconciliation_version: 2"))
        payload = self.assert_cli_fails("closure", "E_SOURCE_LINEAGE_STALE")
        self.assertTrue(any(error.get("expected") == "2" and error.get("actual") == "1" for error in payload["errors"]))

    def test_source_artifacts_reject_yaml_constructs_and_template_test_exception_is_structured(self) -> None:
        self.install_valid_source_contract()
        write(
            self.req / "scope-reconciliation.yml",
            """
            requirement_id: demo
            reconciliation_version: 1
            source_inventory_digest: &digest sha256:any
            accepted_scope_digest: *digest
            reviewer_status: SHIP
            source_obligation_review_required: true
            reconciled_items: []
            """,
        )
        self.assert_cli_fails("readiness", "E_YAML_UNSUPPORTED_CONSTRUCT")

        template_root = ROOT / ".codex" / "skills" / "project-bootstrap" / "templates" / "root"
        root_test = (ROOT / "tests" / "verify_coverage_ledger.py").read_text(encoding="utf-8")
        template_test = (template_root / "tests" / "verify_coverage_ledger.py").read_text(encoding="utf-8")
        if root_test != template_test:
            self.assertIn("BOOTSTRAP_COVERAGE_LEDGER_TEST_PARITY_EXCEPTION", template_test)
            self.assertIn("test_valid_ledger_passes_and_missing_decision_fails", template_test)

    def test_trigger_matrix_requires_ledgers_and_allows_structured_low_risk_exception(self) -> None:
        cases = [
            ("ten_subtasks", {"subtask_count": 10}),
            ("ten_screens", {"screen_count": 10}),
            ("multi_state_ui", {"multi_state_ui": True}),
            ("bulk_migration", {"bulk_data_migration": True}),
            ("many_modules", {"module_count": 3}),
            ("many_acceptance_criteria", {"acceptance_criteria_count": 10}),
        ]
        for name, signals in cases:
            with self.subTest(name=name):
                write(
                    self.req / "coverage-decision.yml",
                    f"""
                    requirement_id: demo
                    decision_version: 1
                    ledger_required: true
                    ledger_path: coverage-ledger.yml
                    decided_by_gate: requirement-clarifier
                    decided_at: "2026-06-20T10:00:00Z"
                    trigger_evaluation:
                      accepted_scope_digest: "current-scope"
                      signals: {json.dumps(signals)}
                      broad_work_detected: true
                    source_refs:
                      - requirements/demo/requirements.md#scope
                    """,
                )
                self.assert_cli_ok("readiness")

        write(
            self.req / "coverage-decision.yml",
            """
            requirement_id: demo
            decision_version: 1
            ledger_required: false
            decided_by_gate: requirement-clarifier
            decided_at: "2026-06-20T10:00:00Z"
            trigger_evaluation:
              accepted_scope_digest: "current-scope"
              signals:
                subtask_count: 12
                low_risk_mechanical_edits: true
              broad_work_detected: false
            ledger_not_required:
              reason: "Twelve generated spelling-only edits with no semantic or state variation."
              risk_assessment: "low"
              accepted_scope_refs:
                - requirements/demo/requirements.md#scope
            source_refs:
              - requirements/demo/requirements.md#scope
            """,
        )
        os.remove(self.req / "coverage-ledger.yml")
        self.assert_cli_ok("readiness")

    def test_required_decision_without_ledger_fails_readiness(self) -> None:
        os.remove(self.req / "coverage-ledger.yml")
        self.assert_cli_fails("readiness", "E_LEDGER_REQUIRED_MISSING")

    def test_broad_work_without_ledger_or_not_required_decision_routes_to_recheck(self) -> None:
        os.remove(self.req / "coverage-decision.yml")
        os.remove(self.req / "coverage-ledger.yml")
        write(
            self.req / "progress.md",
            """
            # Progress

            coverage_gap:
              triggering_signals:
                screen_count: 12
            """,
        )
        payload = self.assert_cli_fails("readiness", "E_DECISION_MISSING_RECHECK")
        self.assertEqual(payload["route"], "requirement-clarifier-post-review-recheck")

    def test_ledger_without_decision_fails_readiness(self) -> None:
        os.remove(self.req / "coverage-decision.yml")
        self.assert_cli_fails("readiness", "E_DECISION_REQUIRED")

    def test_progress_gap_schema_and_resume_blocking_are_validated(self) -> None:
        os.remove(self.req / "coverage-decision.yml")
        os.remove(self.req / "coverage-ledger.yml")
        write(
            self.req / "progress.md",
            """
            coverage_gap:
              requirement_id: demo
              route: requirement-clarifier-post-review-recheck
              blocking_reason: broad-work signals have no ledger
              triggering_signals:
                screen_count: 12
              expected_next_gate: requirement-clarifier-post-draft-review
              closure_condition: valid coverage decision and ledger
              recorded_at: "2026-06-20T10:00:00Z"
            """,
        )
        payload = self.assert_cli_fails("readiness", "E_DECISION_MISSING_RECHECK")
        self.assertEqual(payload["route"], "requirement-clarifier-post-review-recheck")

        write(self.req / "progress.md", "coverage_gap:\n  route: requirement-clarifier-post-review-recheck\n")
        self.assert_cli_fails("readiness", "E_PROGRESS_GAP_SCHEMA")

    def test_low_risk_exception_cannot_override_qualitative_high_risk_signal(self) -> None:
        os.remove(self.req / "coverage-ledger.yml")
        write(
            self.req / "coverage-decision.yml",
            """
            requirement_id: demo
            decision_version: 1
            ledger_required: false
            decided_by_gate: requirement-clarifier
            decided_at: "2026-06-20T10:00:00Z"
            trigger_evaluation:
              accepted_scope_digest: "current-scope"
              signals:
                subtask_count: 12
                low_risk_mechanical_edits: true
                multi_state_ui: true
              broad_work_detected: true
            ledger_not_required:
              reason: "Mechanical edits, but this incorrectly includes multi-state UI."
              risk_assessment: "low"
              accepted_scope_refs:
                - requirements/demo/requirements.md#scope
            source_refs:
              - requirements/demo/requirements.md#scope
            """,
        )
        self.assert_cli_fails("readiness", "E_DECISION_STALE")

    def test_stale_not_required_decision_blocks_readiness(self) -> None:
        write(self.req / "coverage-decision.yml", decision_text(required=False, stale=True))
        self.assert_cli_fails("readiness", "E_DECISION_STALE")

    def test_split_brain_decision_and_ledger_states_fail(self) -> None:
        write(self.req / "coverage-decision.yml", decision_text(required=False))
        self.assert_cli_fails("readiness", "E_DECISION_LEDGER_CONFLICT")
        self.assert_cli_fails("closure", "E_DECISION_LEDGER_CONFLICT")

        write(self.req / "coverage-decision.yml", decision_text(required=True, ledger_path="missing.yml"))
        self.assert_cli_fails("readiness", "E_LEDGER_PATH_MISMATCH")

        write(self.req / "other-ledger.yml", closed_ledger_text())
        write(self.req / "coverage-decision.yml", decision_text(required=True, ledger_path="other-ledger.yml"))
        self.assert_cli_fails("readiness", "E_LEDGER_PATH_MISMATCH")
        self.assert_cli_fails("closure", "E_LEDGER_PATH_MISMATCH")

    def test_closure_rejects_incomplete_and_bad_status_rows(self) -> None:
        text = closed_ledger_text().replace("        status: verified", "        status: planned", 1)
        write(self.req / "coverage-ledger.yml", text)
        self.assert_cli_fails("closure", "E_ROW_BLOCKING_STATUS", row_id="ui.ingredient.states")

        text = closed_ledger_text().replace("        status: verified", "        status: not_required_with_reason", 1)
        write(self.req / "coverage-ledger.yml", text)
        self.assert_cli_fails("closure", "E_NOT_REQUIRED_REASON", row_id="ui.ingredient.states")

        text = closed_ledger_text().replace("        status: verified", "        status: deferred_with_user_acceptance", 1)
        write(self.req / "coverage-ledger.yml", text)
        self.assert_cli_fails("closure", "E_DEFERRED_ACCEPTANCE", row_id="ui.ingredient.states")

        text = closed_ledger_text().replace("        status: verified", "        status: stale_needs_recheck", 1)
        write(self.req / "coverage-ledger.yml", text)
        self.assert_cli_fails("closure", "E_ROW_BLOCKING_STATUS", row_id="ui.ingredient.states")

        text = closed_ledger_text().replace("        status: verified", "        status: mystery_done", 1)
        write(self.req / "coverage-ledger.yml", text)
        self.assert_cli_fails("closure", "E_ROW_BLOCKING_STATUS", row_id="ui.ingredient.states")

    def test_missing_required_fields_and_empty_ledger_fail_schema(self) -> None:
        text = closed_ledger_text().replace("        description: Ingredient UI states are represented with DOM and screenshot evidence.\n", "")
        write(self.req / "coverage-ledger.yml", text)
        self.assert_cli_fails("schema", "E_REQUIRED_FIELD", row_id="ui.ingredient.states")

        text = closed_ledger_text().split("coverage_rows:", 1)[0] + "coverage_rows: []\n"
        write(self.req / "coverage-ledger.yml", text)
        self.assert_cli_fails("schema", "E_EMPTY_LEDGER")

    def test_route_only_and_prose_only_evidence_do_not_satisfy_ui_state(self) -> None:
        text = closed_ledger_text().replace("type: dom_assertion", "type: route_exists")
        write(self.req / "coverage-ledger.yml", text)
        self.assert_cli_fails("closure", "E_EVIDENCE_INCOMPATIBLE", row_id="ui.ingredient.states")

        text = closed_ledger_text().replace("type: screenshot", "type: prose_note")
        write(self.req / "coverage-ledger.yml", text)
        self.assert_cli_fails("closure", "E_EVIDENCE_INCOMPATIBLE", row_id="ui.ingredient.states")

    def test_migration_and_agent_workflow_evidence_are_type_specific(self) -> None:
        migration = closed_ledger_text().replace("obligation_type: ui_state", "obligation_type: migration")
        migration = migration.replace("- dom_assertion\n          - screenshot", "- row_count\n          - checksum")
        migration = migration.replace("type: dom_assertion", "type: row_count")
        migration = migration.replace("type: screenshot", "type: screenshot")
        write(self.req / "coverage-ledger.yml", migration)
        self.assert_cli_fails("closure", "E_EVIDENCE_INCOMPATIBLE", row_id="ui.ingredient.states")

        agent = closed_ledger_text().replace("obligation_type: ui_state", "obligation_type: agent_workflow")
        agent = agent.replace("- dom_assertion\n          - screenshot", "- generated_artifact\n          - consumer_proof")
        agent = agent.replace("type: dom_assertion", "type: generated_artifact")
        agent = agent.replace("type: screenshot", "type: command_result")
        write(self.req / "coverage-ledger.yml", agent)
        self.assert_cli_fails("closure", "E_EVIDENCE_INCOMPATIBLE", row_id="ui.ingredient.states")

    def test_missing_path_escape_symlink_directory_and_stale_hash_fail(self) -> None:
        write(self.req / "coverage-ledger.yml", closed_ledger_text("evidence/missing.png"))
        self.assert_cli_fails("closure", "E_EVIDENCE_PATH_MISSING", row_id="ui.ingredient.states")

        write(self.req / "coverage-ledger.yml", closed_ledger_text("../outside.png"))
        self.assert_cli_fails("closure", "E_EVIDENCE_PATH_ESCAPE", row_id="ui.ingredient.states")

        write(self.req / "coverage-ledger.yml", closed_ledger_text("evidence"))
        self.assert_cli_fails("closure", "E_EVIDENCE_PATH_NOT_FILE", row_id="ui.ingredient.states")

        outside = self.root / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        link = self.req / "evidence" / "escape-link"
        link.symlink_to(outside)
        write(self.req / "coverage-ledger.yml", closed_ledger_text("evidence/escape-link"))
        self.assert_cli_fails("closure", "E_EVIDENCE_PATH_ESCAPE", row_id="ui.ingredient.states")

        write(self.req / "coverage-ledger.yml", closed_ledger_text("evidence/ui.txt", "sha256:not-the-real-hash"))
        self.assert_cli_fails("closure", "E_EVIDENCE_HASH_MISMATCH", row_id="ui.ingredient.states")

    def test_strict_yaml_duplicate_keys_duplicate_rows_and_multi_doc_fail(self) -> None:
        write(self.req / "coverage-decision.yml", decision_text() + "\n---\nextra: true\n")
        self.assert_cli_fails("schema", "E_YAML_MULTI_DOCUMENT")

        write(
            self.req / "coverage-decision.yml",
            """
            requirement_id: demo
            requirement_id: other
            decision_version: 1
            ledger_required: true
            ledger_path: coverage-ledger.yml
            decided_by_gate: requirement-clarifier
            decided_at: "2026-06-20T10:00:00Z"
            trigger_evaluation:
              accepted_scope_digest: "current-scope"
              signals:
                many_acceptance_criteria: true
              broad_work_detected: true
            source_refs:
              - requirements/demo/requirements.md#scope
            """,
        )
        self.assert_cli_fails("schema", "E_YAML_DUPLICATE_KEY")

        write(self.req / "coverage-decision.yml", decision_text())
        write(self.req / "coverage-ledger.yml", closed_ledger_text() + closed_ledger_text().split("coverage_rows:", 1)[1])
        self.assert_cli_fails("schema", "E_DUPLICATE_ROW_ID")

    def test_committed_fixture_requirement_ledger_schema_and_closure_pass(self) -> None:
        schema = run_cli("validate", "--mode", "schema", "--requirement-dir", str(self.req))
        self.assertEqual(schema.returncode, 0, schema.stdout + schema.stderr)
        result = run_cli("validate", "--mode", "closure", "--requirement-dir", str(self.req))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = parse_result(result)
        self.assertEqual(payload["status"], "pass")

    def test_skill_agent_and_template_surfaces_project_the_ledger_contract(self) -> None:
        root_skill = (ROOT / ".codex" / "skills" / "requirement-clarifier" / "SKILL.md").read_text(encoding="utf-8")
        template_skill = (
            ROOT
            / ".codex"
            / "skills"
            / "project-bootstrap"
            / "templates"
            / "root"
            / ".codex"
            / "skills"
            / "requirement-clarifier"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(root_skill, template_skill)
        for token in [
            "coverage-decision.yml",
            "coverage-ledger.yml",
            "ledger_required: true",
            "ledger_required: false",
            "scripts/coverage_ledger.py",
        ]:
            self.assertIn(token, root_skill)

        root_agent = tomllib.loads((ROOT / ".codex" / "agents" / "requirement-clarifier-post-draft-reviewer.toml").read_text())
        template_agent = tomllib.loads(
            (
                ROOT
                / ".codex"
                / "skills"
                / "project-bootstrap"
                / "templates"
                / "root"
                / ".codex"
                / "agents"
                / "requirement-clarifier-post-draft-reviewer.toml"
            ).read_text()
        )
        self.assertEqual(root_agent, template_agent)
        instructions = root_agent["developer_instructions"]
        self.assertIn("coverage-decision.yml", instructions)
        self.assertIn("coverage-ledger.yml", instructions)
        self.assertIn("prose-only", instructions)

        root_brake = (ROOT / ".codex" / "skills" / "implementation-brake" / "SKILL.md").read_text(encoding="utf-8")
        template_brake = (
            ROOT
            / ".codex"
            / "skills"
            / "project-bootstrap"
            / "templates"
            / "root"
            / ".codex"
            / "skills"
            / "implementation-brake"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(root_brake, template_brake)
        self.assertIn("Coverage Ledger Ship Gate", root_brake)
        self.assertIn("requirement-clarifier-post-review-recheck", root_brake)

        template_root = ROOT / ".codex" / "skills" / "project-bootstrap" / "templates" / "root"
        self.assertTrue((template_root / "scripts" / "coverage_ledger.py").exists())
        self.assertTrue((template_root / "scripts" / "verify").exists())
        self.assertTrue((template_root / "tests" / "verify_coverage_ledger.py").exists())
        self.assertEqual(
            (ROOT / "scripts" / "coverage_ledger.py").read_text(encoding="utf-8"),
            (template_root / "scripts" / "coverage_ledger.py").read_text(encoding="utf-8"),
        )

    def test_bootstrap_template_verify_runs_coverage_ledger_baseline(self) -> None:
        template_root = ROOT / ".codex" / "skills" / "project-bootstrap" / "templates" / "root"
        result = subprocess.run(
            [str(template_root / "scripts" / "verify")],
            cwd=template_root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
