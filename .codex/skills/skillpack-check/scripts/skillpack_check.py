#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_SECTIONS = ["## Workflow", "## Anti-Patterns"]
FORBIDDEN_LEAKS = ["/Users/", ".claude/skills", "AskUserQuestion", "$B", "allowed-tools:"]


def check_skillpack(root: Path) -> dict[str, Any]:
    skills_dir = root / ".codex" / "skills"
    issues: list[dict[str, Any]] = []
    skill_files = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.exists() else []
    for skill_file in skill_files:
        skill = skill_file.parent.name
        text = skill_file.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)
        if frontmatter.get("name") != skill:
            issues.append(issue(skill, "critical", "frontmatter_name", f"name must be {skill}"))
        if not frontmatter.get("description"):
            issues.append(issue(skill, "major", "frontmatter_description", "description is required"))
        for section in REQUIRED_SECTIONS:
            if section not in text:
                issues.append(issue(skill, "major", "missing_section", f"{section} is required"))
        for leak in FORBIDDEN_LEAKS:
            if leak in text:
                issues.append(issue(skill, "major", "host_specific_leak", f"forbidden host-specific token {leak!r}"))
    verify = (root / "scripts" / "verify").read_text(encoding="utf-8") if (root / "scripts" / "verify").exists() else ""
    lifecycle_present = any((skills_dir / name / "SKILL.md").exists() for name in ["skill-optimizer", "skillify", "skillpack-check"])
    if lifecycle_present and "tests/verify_skill_lifecycle_pack.py" not in verify:
        issues.append(issue("repo", "major", "verify_missing_lifecycle", "scripts/verify must run lifecycle verification"))
    actions = [format_action(row) for row in issues if row["severity"] in {"critical", "major"}]
    healthy = not actions
    return {
        "healthy": healthy,
        "summary": "Codex skillpack healthy" if healthy else f"Codex skillpack needs attention: {len(actions)} action(s)",
        "actions": actions,
        "skills_checked": len(skill_files),
        "issues": issues,
    }


def issue(skill: str, severity: str, code: str, message: str) -> dict[str, str]:
    return {"skill": skill, "severity": severity, "code": code, "message": message}


def format_action(row: dict[str, str]) -> str:
    return f"Fix {row['skill']}: {row['message']}"


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip("'\"")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Codex skillpack health")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    report = check_skillpack(args.root.resolve())
    if not args.quiet or not report["healthy"]:
        print(json.dumps(report, indent=2))
    return 0 if report["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
