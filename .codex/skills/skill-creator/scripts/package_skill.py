#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def collect_package_files(skill_dir: Path) -> list[Path]:
    root = skill_dir.resolve()
    if not (root / "SKILL.md").is_file():
        raise FileNotFoundError(f"missing SKILL.md under {root}")
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if any(part == "__pycache__" for part in path.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"symlink rejected: {path}")
        if not path.is_file():
            continue
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"path escape rejected: {path}") from exc
        files.append(path)
    return files


def package_manifest(skill_dir: Path) -> dict[str, Any]:
    root = skill_dir.resolve()
    files = collect_package_files(root)
    return {
        "skill": root.name,
        "files": [str(path.relative_to(root)) for path in files],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="List files in a safe Codex skill package")
    parser.add_argument("skill_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(package_manifest(args.skill_dir.resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
