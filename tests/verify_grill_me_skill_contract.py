#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".codex/skills/grill-me/SKILL.md"
PLUGIN = ROOT / ".codex/skills/grill-me/agents/openai.yaml"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label} missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label} still contains {needle!r}")


def assert_batch_mode_contract() -> None:
    text = read(SKILL)
    required = [
        "Batch mode",
        "Treat prior `Batch-5 mode` wording as a legacy alias only",
        "Use `Batch mode` only when the user explicitly asks",
        "with or without a registered agent refresh",
        "Do not run a refresh round merely because batch mode was requested",
        "If a registered agent refresh round is used for batch construction, preserve the existing fail-closed semantics",
        "Each batched question must independently pass the criticality gate",
        "answer any subset",
        "The default 5-question budget does not apply in `Batch mode`",
        "Do not pad the batch to 5 questions",
        "Do not cap the batch at 5 questions",
        "Batch question count is limited by the criticality gate, not by a numeric budget",
        "A batch may contain 10 or 15 questions when each question is handoff-changing",
        "Order batched questions by priority and dependency",
        "Number the questions in that order",
    ]
    for needle in required:
        assert_contains(text, needle, "grill-me batch mode contract")
    forbidden = [
        "Ask at most 5 pressure questions in one message",
        "Support an explicit `Batch-5 mode`",
        "Use `Batch-5 mode` only when the user explicitly asks",
        "Number the questions `Q1` through `Q5`",
        "After the batched answers are processed, apply the same 5-question extension gate",
        "do not exceed the current remaining budget",
        "fire the same extension gate when the first 5 answered pressure questions have been used",
    ]
    for needle in forbidden:
        assert_not_contains(text, needle, "grill-me batch mode contract")


def assert_default_prompt_exposes_batch_mode() -> None:
    text = read(PLUGIN)
    assert_contains(
        text,
        "If I ask for batch mode, ask the critical questions at once without applying the default 5-question budget",
        "grill-me plugin default prompt",
    )
    assert_not_contains(
        text,
        "If I ask for batch mode, ask up to 5 critical questions at once",
        "grill-me plugin default prompt",
    )


def main() -> None:
    assert_batch_mode_contract()
    assert_default_prompt_exposes_batch_mode()
    print("OK grill-me skill contract")


if __name__ == "__main__":
    main()
