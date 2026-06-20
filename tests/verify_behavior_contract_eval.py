#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_CLI = ROOT / "scripts" / "behavior_text_contract.py"
EVAL_CLI = ROOT / "scripts" / "behavior_contract_eval.py"


BASE_ARGS = [
    "--purpose",
    "Prevent silent behavior downgrades.",
    "--target-behavior",
    "Stop before replacing a requested execution boundary with a weaker substitute.",
    "--input",
    "Prompt or AGENTS.md behavior change request.",
    "--required-action",
    "State the gap and ask for explicit approval before downgrading.",
    "--non-goal",
    "Do not implement prompt optimization.",
    "--failure-mode",
    "Agent silently substitutes documentation or a proxy implementation.",
    "--decision-boundary",
    "Agent may choose contract wording but must not expand source classes.",
    "--verification-expectation",
    "Deterministic validation plus scripts/verify.",
    "--handoff-route",
    "requirements/003-behavior-contract-eval/requirements.md",
    "--execution-boundary",
    "contract eval gate",
    "--artifact-class",
    "behavior-contract-eval-result",
    "--allowed-substitution",
    "Promptfoo blocked evidence may prove only that promptfoo could not run.",
    "--disallowed-substitution",
    "Documentation-only intent.",
    "--downgrade-approval-rule",
    "Ask the user before weakening the accepted contract.",
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_contract(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CONTRACT_CLI), "--root", str(root), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def run_eval(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(EVAL_CLI), "--root", str(root), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def read_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def replace_contract_text(contract_path: Path, old: str, new: str) -> None:
    text = contract_path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"missing text to replace: {old}")
    contract_path.write_text(text.replace(old, new), encoding="utf-8")


class BehaviorContractEvalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root / "prompts" / "agent.prompt.md", "System prompt fixture\n")
        write(self.root / "AGENTS.md", "# AGENTS\n\nRules\n")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def create_contract(
        self,
        contract_id: str,
        *,
        source_kind: str = "agents_md",
        source: str = "AGENTS.md",
        evidence_level: str = "deterministic",
    ) -> Path:
        args = [
            "create",
            "--id",
            contract_id,
            "--source",
            source,
            "--source-kind",
            source_kind,
            "--evidence-level",
            evidence_level,
            *BASE_ARGS,
        ]
        if source_kind == "prompt":
            args.extend(["--prompt-role", "behavior"])
        result = run_contract(self.root, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.root / "behavior-texts" / contract_id / "contract.md"

    def result_path(self, contract_id: str, run_id: str) -> Path:
        return self.root / "behavior-texts" / contract_id / "evals" / run_id / "result.toml"

    def test_deterministic_success_schema_and_entry_forms(self) -> None:
        contract_path = self.create_contract("agents-boundary")
        by_id = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "id-entry")
        self.assertEqual(by_id.returncode, 0, by_id.stderr)
        self.assertIn("status=pass", by_id.stdout)

        by_path = run_eval(
            self.root,
            "evaluate",
            "--contract",
            "behavior-texts/agents-boundary/contract.md",
            "--run-id",
            "path-entry",
        )
        self.assertEqual(by_path.returncode, 0, by_path.stderr)

        result = read_toml(self.result_path("agents-boundary", "id-entry"))
        self.assertEqual(result["result"]["contract_id"], "agents-boundary")
        self.assertRegex(result["result"]["contract_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(result["result"]["status"], "pass")
        self.assertEqual(result["result"]["evidence_mode"], "deterministic")
        self.assertEqual(result["result"]["evidence_strength"], "deterministic")
        self.assertEqual(result["result"]["block_reason"], "none")
        self.assertEqual(result["result"]["downgrade_state"], "none")
        self.assertTrue(result["result"]["behavior_verification_claimed"])
        self.assertEqual(result["contract_source"]["kind"], "agents_md")
        self.assertEqual(result["contract_source"]["path"], "AGENTS.md")
        self.assertEqual(result["contract_behavior"]["target_behavior"], "Stop before replacing a requested execution boundary with a weaker substitute.")
        self.assertIn("State the gap", result["contract_behavior"]["required_actions"][0])
        self.assertIn("proxy implementation", result["contract_behavior"]["failure_modes"][0])
        self.assertIn("source classes", result["contract_behavior"]["decision_boundaries"][0])
        self.assertIn("Deterministic validation", result["contract_verification"]["expectations"][0])
        self.assertEqual(result["contract_verification"]["handoff_route"], "requirements/003-behavior-contract-eval/requirements.md")
        self.assertEqual(result["contract_impact"]["evidence_level"], "deterministic")
        self.assertIn("Promptfoo blocked", result["contract_impact"]["allowed_substitutions"][0])
        self.assertIn("Documentation-only", result["contract_impact"]["disallowed_substitutions"][0])
        self.assertIn("Ask the user", result["contract_impact"]["downgrade_approval_rule"])
        self.assertIn("behavior-texts/agents-boundary/evals/id-entry/result.toml", result["artifacts"]["paths"])
        self.assertIn("evaluate", result["commands"]["run"][0])
        self.assertNotIn(str(self.root), result["commands"]["run"][0])
        self.assertNotIn(sys.executable, result["commands"]["run"][0])
        self.assertIn("contract_validation", result["checks"]["items"])
        self.assertIn("result_schema_parse", result["checks"]["items"])
        self.assertEqual(contract_path.name, "contract.md")

    def test_result_toml_preserves_validator_accepted_multiline_payloads(self) -> None:
        contract_path = self.create_contract("multiline-boundary")
        replace_contract_text(
            contract_path,
            'target_behavior = "Stop before replacing a requested execution boundary with a weaker substitute."',
            'target_behavior = """Stop before replacing\\na requested execution boundary."""',
        )
        replace_contract_text(
            contract_path,
            'required_actions = ["State the gap and ask for explicit approval before downgrading."]',
            'required_actions = ["""State the gap\\nand ask for explicit approval."""]',
        )

        result = run_eval(self.root, "evaluate", "--contract", "multiline-boundary", "--run-id", "multiline-pass")
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = read_toml(self.result_path("multiline-boundary", "multiline-pass"))
        self.assertEqual(parsed["contract_behavior"]["target_behavior"], "Stop before replacing\na requested execution boundary.")
        self.assertEqual(parsed["contract_behavior"]["required_actions"], ["State the gap\nand ask for explicit approval."])

    def test_promptfoo_blocked_and_downgrade_states_do_not_claim_behavior(self) -> None:
        self.create_contract(
            "prompt-boundary",
            source_kind="prompt",
            source="prompts/agent.prompt.md",
            evidence_level="promptfoo",
        )

        blocked = run_eval(self.root, "evaluate", "--contract", "prompt-boundary", "--run-id", "blocked-auto")
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("promptfoo_execution_blocked", blocked.stdout)
        blocked_result = read_toml(self.result_path("prompt-boundary", "blocked-auto"))
        self.assertEqual(blocked_result["result"]["status"], "blocked")
        self.assertEqual(blocked_result["result"]["block_reason"], "promptfoo_execution_blocked")
        self.assertFalse(blocked_result["result"]["behavior_verification_claimed"])

        unapproved = run_eval(
            self.root,
            "evaluate",
            "--contract",
            "prompt-boundary",
            "--run-id",
            "forced-deterministic",
            "--mode",
            "deterministic",
        )
        self.assertNotEqual(unapproved.returncode, 0)
        unapproved_result = read_toml(self.result_path("prompt-boundary", "forced-deterministic"))
        self.assertEqual(unapproved_result["result"]["block_reason"], "unapproved_downgrade")
        self.assertEqual(unapproved_result["result"]["downgrade_state"], "unapproved_blocked")
        self.assertFalse(unapproved_result["result"]["behavior_verification_claimed"])

        approved = run_eval(
            self.root,
            "evaluate",
            "--contract",
            "prompt-boundary",
            "--run-id",
            "approved-downgrade",
            "--mode",
            "deterministic",
            "--approve-downgrade",
        )
        self.assertEqual(approved.returncode, 0, approved.stderr)
        approved_result = read_toml(self.result_path("prompt-boundary", "approved-downgrade"))
        self.assertEqual(approved_result["result"]["downgrade_state"], "approved")
        self.assertTrue(approved_result["result"]["downgrade_approved"])
        self.assertEqual(approved_result["result"]["evidence_strength"], "weaker_approved_no_behavior_claim")
        self.assertFalse(approved_result["result"]["behavior_verification_claimed"])

    def test_invalid_unsupported_and_stale_result_paths_are_blocked(self) -> None:
        contract_path = self.create_contract("agents-boundary")
        first = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "single-use")
        self.assertEqual(first.returncode, 0, first.stderr)
        original_result = self.result_path("agents-boundary", "single-use").read_text(encoding="utf-8")

        duplicate = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "single-use")
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("E_RESULT_EXISTS", duplicate.stderr)
        self.assertEqual(self.result_path("agents-boundary", "single-use").read_text(encoding="utf-8"), original_result)

        replace_contract_text(contract_path, 'path = "AGENTS.md"', 'path = "../AGENTS.md"')
        invalid_stale = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "single-use")
        self.assertNotEqual(invalid_stale.returncode, 0)
        self.assertIn("E_RESULT_EXISTS", invalid_stale.stderr)
        self.assertEqual(self.result_path("agents-boundary", "single-use").read_text(encoding="utf-8"), original_result)

        invalid = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "invalid-contract")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("E_SOURCE_PATH_CONTAINMENT", invalid.stderr)
        self.assertFalse(self.result_path("agents-boundary", "invalid-contract").exists())

        replace_contract_text(contract_path, 'path = "../AGENTS.md"', 'path = "AGENTS.md"')
        replace_contract_text(contract_path, 'evidence_level = "deterministic"', 'evidence_level = "live_provider_required"')
        unsupported = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "unsupported-evidence")
        self.assertNotEqual(unsupported.returncode, 0)
        unsupported_result = read_toml(self.result_path("agents-boundary", "unsupported-evidence"))
        self.assertEqual(unsupported_result["result"]["block_reason"], "unsupported_evidence_level")
        self.assertFalse(unsupported_result["result"]["behavior_verification_claimed"])

        bad_run = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "../escape")
        self.assertNotEqual(bad_run.returncode, 0)
        self.assertIn("E_RUN_ID", bad_run.stderr)

        bad_path = run_eval(self.root, "evaluate", "--contract", "../contract.md", "--run-id", "bad-path")
        self.assertNotEqual(bad_path.returncode, 0)
        self.assertIn("E_CONTRACT_PATH", bad_path.stderr)

    def test_markdown_is_non_authoritative_but_structured_fields_drive_results(self) -> None:
        contract_path = self.create_contract("agents-boundary")
        baseline = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "baseline")
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        baseline_result = read_toml(self.result_path("agents-boundary", "baseline"))

        contract_path.write_text(
            contract_path.read_text(encoding="utf-8") + "\nMarkdown-only note that should not alter state.\n",
            encoding="utf-8",
        )
        markdown = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "markdown-only")
        self.assertEqual(markdown.returncode, 0, markdown.stderr)
        markdown_result = read_toml(self.result_path("agents-boundary", "markdown-only"))
        self.assertEqual(markdown_result["contract_behavior"], baseline_result["contract_behavior"])
        self.assertEqual(markdown_result["contract_verification"], baseline_result["contract_verification"])
        self.assertEqual(markdown_result["contract_impact"], baseline_result["contract_impact"])

        replace_contract_text(
            contract_path,
            "State the gap and ask for explicit approval before downgrading.",
            "State the gap, name the missing live boundary, and ask for approval.",
        )
        payload = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "payload-change")
        self.assertEqual(payload.returncode, 0, payload.stderr)
        payload_result = read_toml(self.result_path("agents-boundary", "payload-change"))
        self.assertIn("missing live boundary", payload_result["contract_behavior"]["required_actions"][0])

        replace_contract_text(contract_path, 'evidence_level = "deterministic"', 'evidence_level = "promptfoo"')
        classification = run_eval(self.root, "evaluate", "--contract", "agents-boundary", "--run-id", "classification-change")
        self.assertNotEqual(classification.returncode, 0)
        classification_result = read_toml(self.result_path("agents-boundary", "classification-change"))
        self.assertEqual(classification_result["result"]["block_reason"], "promptfoo_execution_blocked")


if __name__ == "__main__":
    unittest.main(verbosity=2)
