#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".codex" / "skills" / "gbrain-protocol"
SKILL = SKILL_DIR / "SKILL.md"
REFERENCES = [
    "cli-and-mcp.md",
    "page-writing.md",
    "project-task-cards.md",
    "source-path-patterns.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label} missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label} still contains {needle!r}")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise AssertionError("gbrain-protocol missing frontmatter start")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError("gbrain-protocol missing frontmatter end")
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip("'\"")
    return result


def assert_skill_shape() -> None:
    text = read(SKILL)
    frontmatter = parse_frontmatter(text)
    if frontmatter.get("name") != "gbrain-protocol":
        raise AssertionError("gbrain-protocol frontmatter name mismatch")
    assert_contains(frontmatter.get("description", ""), "GBrain memory", "description")
    for required in [
        "## Contract",
        "## Tool Selection",
        "## Workflow",
        "## Named Source And Path Lookup",
        "## Broad-To-Final Retrieval",
        "## Source Selection",
        "## Verification",
        "## Output Format",
        "## Anti-Patterns",
        "sources_list",
        "get_page",
        "put_page",
        "source-bound",
        "slug/title inventory scan",
        "source-root file path",
        "derive the repo-like slug",
        "federated top hits",
        "wide candidate pool",
        "filter and rerank",
        "top 10",
        "distinctive phrase",
        "Project Task Card Memory",
    ]:
        assert_contains(text, required, "gbrain-protocol SKILL.md")
    for moved_detail in [
        "## Project Task Cards",
        "Global template or policy",
        "Project-specific memory",
        "When updating a Task Card, fold in only durable conclusions",
    ]:
        assert_not_contains(text, moved_detail, "gbrain-protocol SKILL.md")


def assert_references_are_one_hop() -> None:
    text = read(SKILL)
    for _, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        if not target.startswith("./references/"):
            raise AssertionError(f"local reference must use ./references/: {target}")
        relative = Path(target.removeprefix("./"))
        if len(relative.parts) != 2:
            raise AssertionError(f"local reference must be one hop: {target}")
        if not (SKILL_DIR / relative).is_file():
            raise AssertionError(f"local reference target missing: {target}")


def assert_reference_contracts() -> None:
    for name in REFERENCES:
        path = SKILL_DIR / "references" / name
        if not path.is_file():
            raise AssertionError(f"missing gbrain-protocol reference: {name}")
    cli = read(SKILL_DIR / "references" / "cli-and-mcp.md")
    page = read(SKILL_DIR / "references" / "page-writing.md")
    task_cards = read(SKILL_DIR / "references" / "project-task-cards.md")
    paths = read(SKILL_DIR / "references" / "source-path-patterns.md")
    for required in [
        "sources_list",
        "sources_status",
        "get_page",
        "put_page",
        "recall",
        "gbrain search",
        "gbrain query",
        "gbrain get",
        "--source <source-id>",
        "rg --files <source-root>",
        "slug-derived-from-source-root-path",
        "Broad-to-final retrieval flow",
        "final top 10 relevant pages",
        "MCP `put_page` does not expose `source_id`",
    ]:
        assert_contains(cli, required, "cli-and-mcp reference")
    for required in [
        "durable compiled truth",
        "one primary subject",
        "source_note",
        "[Source: User, 2026-06-24]",
        "Search for a distinctive phrase",
    ]:
        assert_contains(page, required, "page-writing reference")
    for required in [
        "compact working memory",
        "projects/task-card-template",
        "projects/<project-id>/task-card",
        "Goal / Outcome",
        "Inputs",
        "Verification",
        "Constraints",
        "Decisions",
        "requirement-clarifier",
        "goal-requirement-orchestrator",
    ]:
        assert_contains(task_cards, required, "project-task-cards reference")
    for required in [
        "`default`",
        "`ai-notes`",
        "`business-notes`",
        "`mindset-notes`",
        "`projects/*`",
        "Verify live state",
    ]:
        assert_contains(paths, required, "source-path-patterns reference")


def assert_no_host_or_legacy_tokens() -> None:
    forbidden = [
        "/Users/",
        ".claude/skills",
        "AskUserQuestion",
        "allowed-tools:",
        "Claude Code",
    ]
    for path in [SKILL, *(SKILL_DIR / "references").glob("*.md")]:
        text = read(path)
        for needle in forbidden:
            assert_not_contains(text, needle, str(path))


def assert_repo_verify_runs_this_contract() -> None:
    verify = read(ROOT / "scripts" / "verify")
    assert_contains(
        verify,
        '"$PYTHON" tests/verify_gbrain_protocol_skill_contract.py',
        "scripts/verify",
    )


def main() -> None:
    assert_skill_shape()
    assert_references_are_one_hop()
    assert_reference_contracts()
    assert_no_host_or_legacy_tokens()
    assert_repo_verify_runs_this_contract()
    print("OK gbrain-protocol skill contract")


if __name__ == "__main__":
    main()
