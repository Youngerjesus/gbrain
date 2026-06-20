#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


def normalize_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise ValueError("skill name must contain at least one letter or digit")
    return slug


def init_skill(root: Path, name: str, description: str) -> Path:
    slug = normalize_slug(name)
    skill_dir = root / ".codex" / "skills" / slug
    skill_dir.mkdir(parents=True, exist_ok=False)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(render_skill(slug, description), encoding="utf-8")
    return skill_file


def render_skill(slug: str, description: str) -> str:
    clean_description = " ".join(description.split()).strip()
    if not clean_description:
        raise ValueError("description is required")
    return f"""---
name: {slug}
description: {clean_description}
---

# {title_from_slug(slug)}

Use this skill when [state the concrete trigger condition].

## Contract

- [Guarantee one.]
- [Guarantee two.]

## Workflow

1. [First action.]
2. [Second action.]
3. Run the relevant verification.

## Output Format

Report the files changed, verification evidence, and any known gaps.

## Anti-Patterns

- [Thing to avoid.]
- [Another thing to avoid.]
"""


def title_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a Codex skill skeleton")
    parser.add_argument("name")
    parser.add_argument("description")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(init_skill(args.root.resolve(), args.name, args.description))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
