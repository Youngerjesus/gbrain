#!/usr/bin/env python3
from pathlib import Path, PurePosixPath
import unittest


ROOT = Path(__file__).resolve().parents[1]

ACTIVE_MARKDOWN_SURFACES = (
    ROOT / "AGENTS.md",
    ROOT / "README.md",
    ROOT / "GETTING_STARTED.md",
    ROOT / "docs",
    ROOT / ".codex",
)

SKIPPED_PARTS = {
    ".git",
    "__pycache__",
    "history_archives",
}


def iter_markdown_files():
    for surface in ACTIVE_MARKDOWN_SURFACES:
        if not surface.exists():
            continue
        if surface.is_file():
            yield surface
            continue
        for path in surface.rglob("*.md"):
            if SKIPPED_PARTS.intersection(path.relative_to(ROOT).parts):
                continue
            yield path


def iter_code_spans(text):
    index = 0
    while index < len(text):
        if text[index] != "`":
            index += 1
            continue

        tick_count = 1
        while index + tick_count < len(text) and text[index + tick_count] == "`":
            tick_count += 1

        close = index + tick_count
        while close < len(text):
            if text[close] != "`":
                close += 1
                continue
            candidate_count = 1
            while (
                close + candidate_count < len(text)
                and text[close + candidate_count] == "`"
            ):
                candidate_count += 1
            if candidate_count == tick_count:
                yield text[index + tick_count : close].strip()
                index = close + candidate_count
                break
            close += candidate_count
        else:
            index += tick_count


def normalized_path_token(code_span):
    if not code_span or "\n" in code_span:
        return None
    if " " in code_span:
        return None
    token = code_span.strip().strip("/")
    if not token:
        return None
    return PurePosixPath(token)


def points_to_removed_work_queue_artifact(path_token):
    parts = path_token.parts
    if parts and parts[0] == "main":
        parts = parts[1:]
    return bool(parts) and parts[0] == "work_queue"


class RemovedArtifactContractTest(unittest.TestCase):
    def test_active_guidance_does_not_reference_removed_root_work_queue(self):
        offenders = []
        for path in iter_markdown_files():
            text = path.read_text(encoding="utf-8")
            for code_span in iter_code_spans(text):
                path_token = normalized_path_token(code_span)
                if path_token and points_to_removed_work_queue_artifact(path_token):
                    offenders.append(
                        f"{path.relative_to(ROOT)} references `{path_token.as_posix()}`"
                    )

        if offenders:
            formatted = "\n".join(f"- {offender}" for offender in offenders)
            raise AssertionError(
                "Active guidance must not reference the removed root work_queue "
                f"progress artifact:\n{formatted}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
