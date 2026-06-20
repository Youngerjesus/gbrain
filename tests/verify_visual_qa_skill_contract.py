#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / ".codex" / "skills" / "visual-qa-hardening" / "SKILL.md"
BENCHMARK_PATH = ROOT / ".codex" / "skills" / "visual-qa-hardening" / "skillopt-benchmark.jsonl"
TEMPLATE_BENCHMARK_PATH = (
    ROOT
    / ".codex"
    / "skills"
    / "project-bootstrap"
    / "templates"
    / "root"
    / ".codex"
    / "skills"
    / "visual-qa-hardening"
    / "skillopt-benchmark.jsonl"
)


def parse_markdown_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return {heading: "\n".join(lines).strip() for heading, lines in sections.items()}


class VisualQaSkillContractTest(unittest.TestCase):
    def test_visual_qa_skill_has_skillified_contract_sections(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")
        sections = parse_markdown_sections(text)
        for heading in [
            "When To Run",
            "Required Inputs",
            "Workflow",
            "Companion Reviewer Contract",
            "No-Subagent Fallback Approval",
            "Review Checklist",
            "Verdicts",
            "Evidence Output",
            "Anti-Patterns",
        ]:
            self.assertIn(heading, sections)

    def test_no_subagent_fallback_requires_structured_approval_record(self) -> None:
        sections = parse_markdown_sections(SKILL_PATH.read_text(encoding="utf-8"))
        fallback = sections["No-Subagent Fallback Approval"]
        required_fields = {
            "requested_companion",
            "unavailable_reason",
            "approval_source",
            "scope",
            "substitute_evidence",
            "risk_accepted",
            "recorded_in",
        }
        for field in required_fields:
            self.assertRegex(fallback, rf"`{field}`")
        self.assertRegex(fallback, r"\[VISUAL QA BLOCKED\].*fallback approval", fallback)

    def test_visual_qa_skillopt_benchmark_artifacts_are_removed(self) -> None:
        self.assertFalse(BENCHMARK_PATH.exists())
        self.assertFalse(TEMPLATE_BENCHMARK_PATH.exists())


if __name__ == "__main__":
    unittest.main()
