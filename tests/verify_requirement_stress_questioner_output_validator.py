#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT
    / ".codex"
    / "skills"
    / "requirement-stress-questioner"
    / "scripts"
    / "validate_output.py"
)
FIXTURES = ROOT / "tests" / "fixtures" / "requirement_stress_questioner"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_output", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load validator: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def main() -> None:
    validator = load_validator()
    valid = FIXTURES / "valid_output.md"
    invalid = FIXTURES / "invalid_missing_answer_impact.md"

    validator.validate_file(valid)

    try:
        validator.validate_file(invalid)
    except validator.ValidationError as exc:
        if "missing Answer impact" not in str(exc):
            raise AssertionError(f"unexpected validation error: {exc}") from exc
    else:
        raise AssertionError("invalid fixture unexpectedly passed")

    valid_result = run_validator(valid)
    if valid_result.returncode != 0:
        raise AssertionError(valid_result.stderr or valid_result.stdout)
    if "OK requirement stress questioner output" not in valid_result.stdout:
        raise AssertionError("validator CLI did not report success")

    invalid_result = run_validator(invalid)
    if invalid_result.returncode != 1:
        raise AssertionError("invalid fixture should fail with exit code 1")
    if "missing Answer impact" not in invalid_result.stderr:
        raise AssertionError("validator CLI did not report the missing field")

    print("OK requirement-stress-questioner output validator")


if __name__ == "__main__":
    main()
