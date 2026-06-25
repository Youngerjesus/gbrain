#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".codex" / "skills" / "requirement-stress-questioner"
SKILL = SKILL_DIR / "SKILL.md"


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label} missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label} must not contain {needle!r}")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise AssertionError("requirement-stress-questioner missing frontmatter start")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError("requirement-stress-questioner missing frontmatter end")
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip("'\"")
    return result


def section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise AssertionError(f"missing section: {heading}")
    return match.group("body")


def assert_skill_shape(text: str) -> None:
    frontmatter = parse_frontmatter(text)
    if frontmatter.get("name") != "requirement-stress-questioner":
        raise AssertionError("frontmatter name mismatch")
    description = frontmatter.get("description", "")
    for required in [
        "already-written requirements",
        "stress questions",
        "intent-contraction",
    ]:
        assert_contains(description, required, "frontmatter description")
    for required_section in [
        "When To Use",
        "Relationship To Nearby Skills",
        "Contract",
        "Workflow",
        "Question Lenses",
        "Output Format",
        "Verification Helper",
        "Companion Review",
        "Anti-Patterns",
    ]:
        section(text, required_section)


def assert_trigger_and_relationship(text: str) -> None:
    trigger = section(text, "When To Use")
    for required in [
        "already-written requirement draft",
        "PRD",
        "spec",
        "feature brief",
        "requirements/<id>/requirements.md",
        "after initial requirement creation",
    ]:
        assert_contains(trigger, required, "trigger section")
    for forbidden in [
        "Use this skill to interrogate raw ideas",
        "Use this skill before requirements exist",
    ]:
        assert_not_contains(trigger, forbidden, "trigger section")

    relationship = section(text, "Relationship To Nearby Skills")
    for required in [
        "`grill-me` interrogates early ideas",
        "`requirement-clarifier` creates or revises requirement contracts",
        "this skill generates post-draft stress questions",
        "does not rewrite by default",
    ]:
        assert_contains(relationship, required, "relationship section")


def assert_intent_contraction(text: str) -> None:
    lenses = section(text, "Question Lenses")
    assert_contains(lenses, "Intent-contraction lens", "question lenses")
    for required in [
        "original intent",
        "plausible weaker interpretation",
        "impacted requirement field or evidence level",
        "answer would block the downgrade",
        "narrower artifact",
        "weaker behavior",
        "lower evidence level",
        "smaller execution boundary",
        "reduced fidelity",
        "unapproved substitute",
    ]:
        assert_contains(lenses, required, "intent-contraction lens")


def assert_required_lenses(text: str) -> None:
    lenses = section(text, "Question Lenses")
    expected = {
        "Failure lens": [
            "fail even if implemented as written",
            "failure would look like",
            "assumption would break first",
        ],
        "Ambiguity lens": [
            "terms, outputs, actors, states, priorities, or quality bars",
            "implementation-valid ways",
        ],
        "Missing-scenarios lens": [
            "entry paths, user types, data shapes, states, retries, errors, re-entry flows, or edge cases",
            "not covered by the current acceptance criteria",
        ],
        "Verification lens": [
            "observable evidence proves completion",
            "evidence disproves it",
            "deterministic versus judgment-based",
            "evidence level matches",
        ],
        "Scope lens": [
            "explicitly in scope",
            "out of scope",
            "accidentally added",
            "accidentally removed",
        ],
        "User-value lens": [
            "user pain or desired outcome",
            "feature is only a proxy",
            "result would make the work valuable",
        ],
        "Dependency lens": [
            "external systems, source documents, prior requirements, permissions, data availability, model behavior, runtime capabilities, or sequencing assumptions",
        ],
        "Decision-boundary lens": [
            "next agent may make alone",
            "require user confirmation",
            "assumptions must remain explicit",
        ],
        "Handoff-readiness lens": [
            "planning or implementation agent",
            "without inventing product decisions",
            "weakening the artifact class",
            "lowering evidence",
            "losing source/reference obligations",
        ],
    }
    for lens_name, responsibilities in expected.items():
        assert_contains(lenses, lens_name, "question lenses")
        for responsibility in responsibilities:
            assert_contains(lenses, responsibility, lens_name)
    assert_contains(lenses, "Each emitted question must carry a lens label", "question lenses")


def assert_workflow_and_output(text: str) -> None:
    workflow = section(text, "Workflow")
    for required in [
        "read the referenced requirement",
        "nearby docs or contracts",
        "Ask the user only for judgment, priority, intent, or unresolved decisions",
        "roughly 5-8 high-impact questions",
        "Ask fewer when fewer questions pass the criticality gate",
        "one-question-at-a-time",
        "Do not ask one question per lens mechanically",
        "blocker and downgrade-prevention questions before refinement questions",
        "scripts/validate_output.py <artifact.md>",
    ]:
        assert_contains(workflow, required, "workflow")

    output = section(text, "Output Format")
    for required in [
        "Source reviewed",
        "Readiness summary",
        "Highest-risk gaps",
        "Prioritized good questions",
        "Lens",
        "Priority",
        "Question",
        "Why it matters",
        "Answer impact",
        "Skipped-lens rationale",
        "Recommended next step",
        "blocker",
        "high-risk ambiguity",
        "verification gap",
        "refinement",
    ]:
        assert_contains(output, required, "output format")

    helper = section(text, "Verification Helper")
    for required in [
        "scripts/validate_output.py",
        "required sections",
        "supported lens labels",
        "priority values",
        "structural guard only",
    ]:
        assert_contains(helper, required, "verification helper")


def assert_companion_and_antipatterns(text: str) -> None:
    contract = section(text, "Contract")
    companion = section(text, "Companion Review")
    for required in [
        "single-agent requirement-draft review by default",
        "optional",
        "when the user asks",
        "runtime already provides compatible read-only reviewers",
        "deduplicate",
        "accept/reject",
        "evidence-needed",
        "Invalid, partial, or malformed companion output",
        "must not be mixed into authoritative results",
    ]:
        assert_contains(companion, required, "companion review")
    for forbidden in [
        "Always run companion subagents",
        "Companion approval is required",
    ]:
        assert_not_contains(companion, forbidden, "companion review")

    anti = section(text, "Anti-Patterns")
    for required in [
        "generic checklist questions",
        "praise-only review",
        "excessive question volume",
        "hidden scope downgrades",
        "silent rewriting",
        "normalizing the requirement into an easier task",
        "weaker substitute",
        "without explicit user approval",
    ]:
        assert_contains(anti, required, "anti-patterns")
    for required in [
        "avoid modifying, normalizing, narrowing, or replacing",
        "unless the user explicitly asks",
    ]:
        assert_contains(contract, required, "contract rewrite prohibition")
    for forbidden in [
        "may rewrite by default",
        "should rewrite by default",
        "can rewrite by default",
        "silent rewriting is allowed",
        "generic checklist-only output is acceptable",
        "unapproved scope narrowing is acceptable",
        "may accept a weaker substitute",
        "weaker substitute is acceptable",
    ]:
        assert_not_contains(text, forbidden, "negative contract guard")


def assert_repo_verify_runs_this_contract() -> None:
    verify = read(ROOT / "scripts" / "verify")
    assert_contains(
        verify,
        '"$PYTHON" tests/verify_requirement_stress_questioner_skill_contract.py',
        "scripts/verify",
    )
    assert_contains(
        verify,
        '"$PYTHON" tests/verify_requirement_stress_questioner_output_validator.py',
        "scripts/verify",
    )


def main() -> None:
    text = read(SKILL)
    assert_skill_shape(text)
    assert_trigger_and_relationship(text)
    assert_intent_contraction(text)
    assert_required_lenses(text)
    assert_workflow_and_output(text)
    assert_companion_and_antipatterns(text)
    assert_repo_verify_runs_this_contract()
    print("OK requirement-stress-questioner skill contract")


if __name__ == "__main__":
    main()
