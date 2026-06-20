#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_SECTIONS = ["## Workflow", "## Anti-Patterns"]


def validate_skill_file(path: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    text = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    expected_name = path.parent.name
    if frontmatter.get("name") != expected_name:
        issues.append({"code": "name_mismatch", "message": f"name must be {expected_name}"})
    if not frontmatter.get("description"):
        issues.append({"code": "missing_description", "message": "description is required"})
    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append({"code": "missing_section", "message": f"{section} is required"})
    return {"ok": not issues, "path": str(path), "issues": issues}


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
    parser = argparse.ArgumentParser(description="Validate one Codex SKILL.md file")
    parser.add_argument("skill_file", type=Path)
    args = parser.parse_args()
    report = validate_skill_file(args.skill_file.resolve())
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
