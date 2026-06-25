#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "Source reviewed",
    "Readiness summary",
    "Highest-risk gaps",
    "Prioritized good questions",
    "Skipped-lens rationale",
    "Recommended next step",
]

ALLOWED_LENSES = {
    "intent-contraction",
    "failure",
    "ambiguity",
    "missing-scenarios",
    "verification",
    "scope",
    "user-value",
    "dependency",
    "decision-boundary",
    "handoff-readiness",
}

ALLOWED_PRIORITIES = {
    "blocker",
    "high-risk ambiguity",
    "verification gap",
    "refinement",
}


class ValidationError(Exception):
    pass


def section_body(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^\*\*{re.escape(heading)}\*\*\s*\n(?P<body>.*?)(?=^\*\*[^*\n]+\*\*\s*$|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValidationError(f"missing section: {heading}")
    body = match.group("body").strip()
    if not body:
        raise ValidationError(f"empty section: {heading}")
    return body


def normalize_lens(raw: str) -> str:
    return raw.strip().lower().replace(" lens", "")


def validate_questions(body: str) -> list[str]:
    starts = list(re.finditer(r"(?m)^\d+\.\s+Lens:\s*(?P<lens>[^\n]+)\n", body))
    if not starts:
        raise ValidationError("no prioritized questions found")

    errors: list[str] = []
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(body)
        block = body[start.start() : end].strip()
        lens = normalize_lens(start.group("lens"))
        if lens not in ALLOWED_LENSES:
            errors.append(f"question {index + 1}: unsupported lens {start.group('lens')!r}")

        fields = {
            "Priority": rf"(?m)^\s+Priority:\s*(?P<value>[^\n]+)$",
            "Question": rf"(?m)^\s+Question:\s*(?P<value>[^\n]+)$",
            "Why it matters": rf"(?m)^\s+Why it matters:\s*(?P<value>[^\n]+)$",
            "Answer impact": rf"(?m)^\s+Answer impact:\s*(?P<value>[^\n]+)$",
        }
        for field, pattern in fields.items():
            match = re.search(pattern, block)
            if not match:
                errors.append(f"question {index + 1}: missing {field}")
                continue
            value = match.group("value").strip()
            if not value:
                errors.append(f"question {index + 1}: empty {field}")
            if field == "Priority" and value.lower() not in ALLOWED_PRIORITIES:
                errors.append(f"question {index + 1}: unsupported priority {value!r}")
    return errors


def validate_text(text: str) -> None:
    for heading in REQUIRED_SECTIONS:
        section_body(text, heading)
    question_errors = validate_questions(section_body(text, "Prioritized good questions"))
    if question_errors:
        raise ValidationError("; ".join(question_errors))


def validate_file(path: Path) -> None:
    if not path.is_file():
        raise ValidationError(f"missing output file: {path}")
    validate_text(path.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_output.py <requirement-stress-questioner-output.md>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    try:
        validate_file(path)
    except ValidationError as exc:
        print(f"invalid requirement stress questioner output: {exc}", file=sys.stderr)
        return 1
    print(f"OK requirement stress questioner output: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
