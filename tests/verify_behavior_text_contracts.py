#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "behavior_text_contract.py"


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
    "contract authoring only",
    "--artifact-class",
    "behavior-text-contract",
    "--evidence-level",
    "deterministic",
    "--allowed-substitution",
    "None without explicit user approval.",
    "--disallowed-substitution",
    "Documentation-only intent.",
    "--downgrade-approval-rule",
    "Ask the user before weakening the accepted contract.",
]


def run_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(root), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_contract(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("+++\n"):
        raise AssertionError("missing TOML frontmatter")
    end = text.find("\n+++\n", 4)
    if end == -1:
        raise AssertionError("missing TOML frontmatter end")
    return tomllib.loads(text[4:end])


class BehaviorTextContractCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root / "prompts" / "agent.prompt.md", "System prompt fixture\n")
        write(self.root / "AGENTS.md", "# AGENTS\n\nRules\n")
        write(self.root / ".codex" / "skills" / "demo" / "SKILL.md", "# Demo skill\n")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def create_prompt(self, contract_id: str = "prompt-boundary", *extra: str) -> subprocess.CompletedProcess[str]:
        return run_cli(
            self.root,
            "create",
            "--id",
            contract_id,
            "--source",
            "prompts/agent.prompt.md",
            "--source-kind",
            "prompt",
            "--prompt-role",
            "behavior",
            *BASE_ARGS,
            *extra,
        )

    def test_creates_and_validates_prompt_contract(self) -> None:
        result = self.create_prompt()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("behavior-texts/prompt-boundary/contract.md", result.stdout)

        contract_path = self.root / "behavior-texts" / "prompt-boundary" / "contract.md"
        data = read_contract(contract_path)
        self.assertEqual(data["contract"]["id"], "prompt-boundary")
        self.assertEqual(data["source"]["kind"], "prompt")
        self.assertEqual(data["source"]["prompt_role"], "behavior")
        self.assertIn("execution_boundary", data["impact"])

        validate = run_cli(self.root, "validate", "behavior-texts/prompt-boundary/contract.md")
        self.assertEqual(validate.returncode, 0, validate.stderr)
        self.assertIn("OK", validate.stdout)

    def test_creates_and_validates_agents_md_contract(self) -> None:
        result = run_cli(
            self.root,
            "create",
            "--id",
            "agents-boundary",
            "--source",
            "AGENTS.md",
            "--source-kind",
            "agents_md",
            *BASE_ARGS,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = read_contract(self.root / "behavior-texts" / "agents-boundary" / "contract.md")
        self.assertEqual(data["source"]["kind"], "agents_md")
        self.assertNotIn("prompt_role", data["source"])

    def test_rejects_unsupported_sources_without_creating_contract(self) -> None:
        unsupported_kind = run_cli(
            self.root,
            "create",
            "--id",
            "unsupported-kind",
            "--source",
            ".codex/skills/demo/SKILL.md",
            "--source-kind",
            "skill",
            *BASE_ARGS,
        )
        self.assertNotEqual(unsupported_kind.returncode, 0)
        self.assertIn("E_SOURCE_KIND", unsupported_kind.stderr)
        self.assertFalse((self.root / "behavior-texts" / "unsupported-kind" / "contract.md").exists())

        result = run_cli(
            self.root,
            "create",
            "--id",
            "skill-boundary",
            "--source",
            ".codex/skills/demo/SKILL.md",
            "--source-kind",
            "prompt",
            "--prompt-role",
            "behavior",
            *BASE_ARGS,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("E_SOURCE_PROMPT_PATH", result.stderr)
        self.assertFalse((self.root / "behavior-texts" / "skill-boundary" / "contract.md").exists())

        judge = self.create_prompt("judge-boundary", "--prompt-role", "judge")
        self.assertNotEqual(judge.returncode, 0)
        self.assertIn("E_SOURCE_PROMPT_ROLE", judge.stderr)
        self.assertFalse((self.root / "behavior-texts" / "judge-boundary" / "contract.md").exists())
        judge_dir = self.root / "behavior-texts" / "judge-boundary"
        if judge_dir.exists():
            self.assertEqual(list(judge_dir.glob(".contract.*.tmp")), [])

        stale_role = run_cli(
            self.root,
            "create",
            "--id",
            "agents-stale-role",
            "--source",
            "AGENTS.md",
            "--source-kind",
            "agents_md",
            "--prompt-role",
            "behavior",
            *BASE_ARGS,
        )
        self.assertNotEqual(stale_role.returncode, 0)
        self.assertIn("E_SOURCE_PROMPT_ROLE", stale_role.stderr)
        self.assertFalse((self.root / "behavior-texts" / "agents-stale-role" / "contract.md").exists())

    def test_validate_rejects_hand_edited_unsupported_source_and_snapshot_keys(self) -> None:
        self.assertEqual(self.create_prompt().returncode, 0)
        contract_path = self.root / "behavior-texts" / "prompt-boundary" / "contract.md"
        text = contract_path.read_text(encoding="utf-8")
        text = text.replace('prompt_role = "behavior"', 'prompt_role = "optimizer"')
        text = text.replace('path = "prompts/agent.prompt.md"', 'path = "prompts/agent.prompt.md"\nsection = 123\nbody = "copied prompt body"')
        text = text.replace("[verification]", "[forbidden]\nsource_body = \"copied body\"\n\n[verification]")
        contract_path.write_text(text, encoding="utf-8")

        result = run_cli(self.root, "validate", "behavior-texts/prompt-boundary/contract.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("E_SOURCE_PROMPT_ROLE", result.stderr)
        self.assertIn("E_FORBIDDEN_SNAPSHOT_KEY", result.stderr)
        self.assertIn("E_UNKNOWN_FIELD", result.stderr)
        self.assertIn("E_OPTIONAL_FIELD_TYPE", result.stderr)

    def test_rejects_path_escape_and_noncanonical_registry_paths(self) -> None:
        escaped = run_cli(
            self.root,
            "create",
            "--id",
            "escaped-agents",
            "--source",
            "../AGENTS.md",
            "--source-kind",
            "agents_md",
            *BASE_ARGS,
        )
        self.assertNotEqual(escaped.returncode, 0)
        self.assertIn("E_SOURCE_PATH_CONTAINMENT", escaped.stderr)

        absolute = run_cli(
            self.root,
            "create",
            "--id",
            "absolute-agents",
            "--source",
            str(self.root / "AGENTS.md"),
            "--source-kind",
            "agents_md",
            *BASE_ARGS,
        )
        self.assertNotEqual(absolute.returncode, 0)
        self.assertIn("E_SOURCE_PATH_CONTAINMENT", absolute.stderr)
        self.assertFalse((self.root / "behavior-texts" / "absolute-agents" / "contract.md").exists())

        self.assertEqual(self.create_prompt().returncode, 0)
        canonical = self.root / "behavior-texts" / "prompt-boundary" / "contract.md"
        noncanonical = self.root / "tmp" / "prompt-boundary" / "contract.md"
        noncanonical.parent.mkdir(parents=True)
        shutil.copyfile(canonical, noncanonical)
        result = run_cli(self.root, "validate", "tmp/prompt-boundary/contract.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("E_CONTRACT_PATH", result.stderr)

    def test_rejects_duplicate_create_and_preserves_existing_contracts(self) -> None:
        first = self.create_prompt()
        self.assertEqual(first.returncode, 0, first.stderr)
        contract_path = self.root / "behavior-texts" / "prompt-boundary" / "contract.md"
        original = contract_path.read_text(encoding="utf-8")

        duplicate = self.create_prompt()
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("E_CONTRACT_EXISTS", duplicate.stderr)
        self.assertEqual(contract_path.read_text(encoding="utf-8"), original)

        failed_update = self.create_prompt("prompt-boundary", "--update", "--prompt-role", "optimizer")
        self.assertNotEqual(failed_update.returncode, 0)
        self.assertIn("E_SOURCE_PROMPT_ROLE", failed_update.stderr)
        self.assertEqual(contract_path.read_text(encoding="utf-8"), original)

    def test_repairs_invalid_existing_contract_only_with_valid_update(self) -> None:
        self.assertEqual(self.create_prompt().returncode, 0)
        contract_path = self.root / "behavior-texts" / "prompt-boundary" / "contract.md"
        contract_path.write_text("invalid\n", encoding="utf-8")
        invalid_original = contract_path.read_text(encoding="utf-8")

        failed_repair = self.create_prompt("prompt-boundary", "--update", "--prompt-role", "optimizer")
        self.assertNotEqual(failed_repair.returncode, 0)
        self.assertEqual(contract_path.read_text(encoding="utf-8"), invalid_original)

        repaired = self.create_prompt("prompt-boundary", "--update")
        self.assertEqual(repaired.returncode, 0, repaired.stderr)
        validate = run_cli(self.root, "validate", "behavior-texts/prompt-boundary/contract.md")
        self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_reports_multiple_diagnostic_codes_for_malformed_contract(self) -> None:
        bad = self.root / "behavior-texts" / "bad-contract" / "contract.md"
        write(
            bad,
            textwrap.dedent(
                """\
                +++
                [contract]
                id = "wrong-id"
                +++
                # Bad
                """
            ),
        )
        result = run_cli(self.root, "validate", "behavior-texts/bad-contract/contract.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("E_CONTRACT_ID_PATH", result.stderr)
        self.assertIn("E_REQUIRED_FIELD", result.stderr)

        no_frontmatter = self.root / "behavior-texts" / "no-frontmatter" / "contract.md"
        write(no_frontmatter, "# Missing frontmatter\n")
        malformed = run_cli(self.root, "validate", "behavior-texts/no-frontmatter/contract.md")
        self.assertNotEqual(malformed.returncode, 0)
        self.assertIn("E_FRONTMATTER", malformed.stderr)


if __name__ == "__main__":
    unittest.main()
