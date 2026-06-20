#!/usr/bin/env python3
from __future__ import annotations

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

    def test_valid_schema_readiness_and_closure_pass_from_external_cwd(self) -> None:
        self.assert_cli_ok("schema")
        self.assert_cli_ok("readiness")
        with tempfile.TemporaryDirectory() as other:
            self.assert_cli_ok("closure", cwd=Path(other))

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
