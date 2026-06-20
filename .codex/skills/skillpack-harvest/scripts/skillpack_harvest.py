#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


PRIVATE_PATTERNS = [
    re.compile(r"/Users/"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"#[a-z0-9][a-z0-9_-]+", re.IGNORECASE),
    re.compile(r"\bprivate-fork-name\b|\bprivate-deployment-name\b|\bprivate-bot-name\b", re.IGNORECASE),
]


def harvest_skill(
    source_root: Path,
    dest_root: Path,
    slug: str,
    *,
    dry_run: bool = False,
    lint: bool = True,
    overwrite_local: bool = False,
) -> dict[str, Any]:
    source_dir = resolve_source_skill(source_root, slug)
    dest_dir = dest_root / ".codex" / "skills" / slug
    files = collect_files(source_dir)
    findings = lint_files(files, source_dir) if lint else []
    planned = [str((dest_dir / path.relative_to(source_dir)).relative_to(dest_root)) for path in files]
    if findings:
        return {"status": "lint_failed", "slug": slug, "files": planned, "findings": findings}
    if dry_run:
        return {"status": "dry_run", "slug": slug, "files": planned, "findings": []}
    if dest_dir.exists() and not overwrite_local:
        return {"status": "slug_collision", "slug": slug, "files": planned, "findings": []}
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    for source in files:
        rel = source.relative_to(source_dir)
        target = dest_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return {"status": "harvested", "slug": slug, "files": planned, "findings": []}


def resolve_source_skill(source_root: Path, slug: str) -> Path:
    candidates = [
        source_root / ".codex" / "skills" / slug,
        source_root / "skills" / slug,
        source_root / slug,
    ]
    for candidate in candidates:
        if (candidate / "SKILL.md").is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"cannot find skill {slug} under {source_root}")


def collect_files(source_dir: Path) -> list[Path]:
    root = source_dir.resolve()
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if any(part == "__pycache__" for part in path.parts) or path.suffix == ".pyc":
            continue
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"path escape rejected: {path}") from exc
        if path.is_symlink():
            raise ValueError(f"symlink rejected: {path}")
        if path.is_file():
            files.append(path)
    return files


def lint_files(files: list[Path], source_dir: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in PRIVATE_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    {
                        "file": str(path.relative_to(source_dir)),
                        "pattern": pattern.pattern,
                        "match": match.group(0),
                    }
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Harvest a Codex skill into this skillpack")
    parser.add_argument("slug")
    parser.add_argument("--from", dest="source", type=Path, required=True)
    parser.add_argument("--to", dest="dest", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-lint", action="store_true")
    parser.add_argument("--overwrite-local", action="store_true")
    args = parser.parse_args()
    result = harvest_skill(
        args.source.resolve(),
        args.dest.resolve(),
        args.slug,
        dry_run=args.dry_run,
        lint=not args.no_lint,
        overwrite_local=args.overwrite_local,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in {"dry_run", "harvested"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
