#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "coverage_ledger.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT, capture_output=True, text=True)


def parse_result(result: subprocess.CompletedProcess[str]) -> dict:
    stream = result.stdout if result.stdout.strip() else result.stderr
    return json.loads(stream)


class BootstrapCoverageLedgerBaselineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.req = Path(self.tmp.name) / "requirements" / "demo"
        self.req.mkdir(parents=True)
        write(self.req / "requirements.md", "# Demo\n")
        write(self.req / "evidence.md", "# Evidence\n")
        write(self.req / "evidence" / "dom.txt", "dom ok\n")
        write(self.req / "evidence" / "screen.txt", "screen ok\n")
        write(
            self.req / "coverage-decision.yml",
            """
            requirement_id: demo
            decision_version: 1
            ledger_required: true
            ledger_path: coverage-ledger.yml
            decided_by_gate: requirement-clarifier
            decided_at: "2026-06-20T10:00:00Z"
            trigger_evaluation:
              accepted_scope_digest: "scope"
              signals:
                multi_state_ui: true
              broad_work_detected: true
            source_refs:
              - requirements/demo/requirements.md#AC-1
            """,
        )
        write(
            self.req / "coverage-ledger.yml",
            """
            requirement_id: demo
            ledger_version: 1
            ledger_required: true
            status: verified
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
              - row_id: ui.states
                required: true
                obligation_type: ui_state
                description: UI state coverage
                source_refs:
                  - requirements/demo/requirements.md#AC-1
                data_condition: state fixture
                required_evidence:
                  - dom_assertion
                  - screenshot
                status: verified
                evidence_refs:
                  - type: dom_assertion
                    ref: dom
                    recorded_in: requirements/demo/evidence.md
                    path: evidence/dom.txt
                  - type: screenshot
                    ref: screen
                    recorded_in: requirements/demo/evidence.md
                    path: evidence/screen.txt
                recorded_in:
                  - requirements/demo/evidence.md
            """,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_valid_ledger_passes_and_missing_decision_fails(self) -> None:
        valid = run_cli("validate", "--mode", "closure", "--requirement-dir", str(self.req))
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        self.assertEqual(parse_result(valid)["status"], "pass")

        (self.req / "coverage-decision.yml").unlink()
        invalid = run_cli("validate", "--mode", "readiness", "--requirement-dir", str(self.req))
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("E_DECISION_REQUIRED", parse_result(invalid)["error_codes"])


if __name__ == "__main__":
    unittest.main()
