#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

import behavior_text_contract as contract_validator


SUPPORTED_EVIDENCE_LEVELS = {"deterministic", "promptfoo"}


def diag(code: str, problem: str, cause: str, fix: str) -> contract_validator.Diagnostic:
    return contract_validator.diag(code, problem, cause, fix)


def print_diagnostics(diagnostics: list[contract_validator.Diagnostic]) -> None:
    contract_validator.print_diagnostics(diagnostics)


def toml_bool(value: bool) -> str:
    return "true" if value else "false"


def toml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return toml_bool(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_scalar(str(item)) for item in value) + "]"
    return json.dumps(str(value))


def render_table(name: str, values: dict[str, Any]) -> list[str]:
    lines = [f"[{name}]"]
    for key in sorted(values):
        lines.append(f"{key} = {toml_scalar(values[key])}")
    return lines


def resolve_contract_relative(contract_ref: str) -> Path | None:
    ref_path = Path(contract_ref)
    if contract_validator.ID_RE.match(contract_ref):
        return contract_validator.canonical_contract_relative(contract_ref)
    if contract_validator.has_path_escape(ref_path):
        return None
    return ref_path


def validate_run_id(run_id: str) -> list[contract_validator.Diagnostic]:
    if not contract_validator.ID_RE.match(run_id):
        return [
            diag(
                "E_RUN_ID",
                "run id must be lowercase kebab-case",
                f"got {run_id!r}",
                "use a run id like deterministic-pass",
            )
        ]
    return []


def load_valid_contract(root: Path, rel_path: Path) -> tuple[dict[str, Any] | None, list[contract_validator.Diagnostic]]:
    diagnostics = contract_validator.validate_contract_file(root, rel_path.as_posix())
    if diagnostics:
        return None, diagnostics
    text = (root / rel_path).read_text(encoding="utf-8")
    data, parse_errors = contract_validator.parse_frontmatter(text)
    if parse_errors:
        return None, parse_errors
    return data, []


def contract_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_relative_path(contract_id: str, run_id: str) -> Path:
    return Path("behavior-texts") / contract_id / "evals" / run_id / "result.toml"


def contract_id_hint(contract_ref: str, rel_contract: Path) -> str | None:
    if contract_validator.ID_RE.match(contract_ref):
        return contract_ref
    if len(rel_contract.parts) == 3 and rel_contract.parts[0] == "behavior-texts" and rel_contract.parts[2] == "contract.md":
        candidate = rel_contract.parts[1]
        if contract_validator.ID_RE.match(candidate):
            return candidate
    return None


def make_result(
    *,
    contract_id: str,
    digest: str,
    status: str,
    evidence_mode: str,
    evidence_strength: str,
    targeted_result: str,
    regression_result: str,
    regression_rationale: str,
    provider: str,
    execution_mode: str,
    block_reason: str,
    downgrade_state: str,
    downgrade_approved: bool,
    behavior_verification_claimed: bool,
    contract_data: dict[str, Any],
    command_text: str,
    artifact_path: Path,
    gaps: list[str],
    checks: list[str],
) -> str:
    result_table = {
        "contract_id": contract_id,
        "contract_sha256": digest,
        "status": status,
        "evidence_mode": evidence_mode,
        "evidence_strength": evidence_strength,
        "targeted_result": targeted_result,
        "regression_result": regression_result,
        "regression_rationale": regression_rationale,
        "provider": provider,
        "execution_mode": execution_mode,
        "block_reason": block_reason,
        "downgrade_state": downgrade_state,
        "downgrade_approved": downgrade_approved,
        "behavior_verification_claimed": behavior_verification_claimed,
    }
    lines: list[str] = []
    lines.extend(render_table("result", result_table))
    lines.append("")
    lines.extend(render_table("contract_source", contract_data["source"]))
    lines.append("")
    lines.extend(render_table("contract_behavior", contract_data["behavior"]))
    lines.append("")
    lines.extend(render_table("contract_verification", contract_data["verification"]))
    lines.append("")
    lines.extend(render_table("contract_impact", contract_data["impact"]))
    lines.append("")
    lines.extend(render_table("commands", {"run": [command_text]}))
    lines.append("")
    lines.extend(render_table("checks", {"items": checks}))
    lines.append("")
    lines.extend(render_table("artifacts", {"paths": [artifact_path.as_posix()]}))
    lines.append("")
    lines.extend(render_table("gaps", {"items": gaps}))
    lines.append("")
    return "\n".join(lines)


def write_result(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def classify_result(args: argparse.Namespace, data: dict[str, Any]) -> tuple[dict[str, Any], int, str]:
    evidence_level = data["impact"]["evidence_level"]
    mode = args.mode
    if evidence_level not in SUPPORTED_EVIDENCE_LEVELS:
        return (
            {
                "status": "blocked",
                "evidence_mode": "unsupported",
                "evidence_strength": "unsupported",
                "targeted_result": "blocked",
                "regression_result": "not_run",
                "regression_rationale": "unsupported evidence level blocks evaluation",
                "provider": "none",
                "execution_mode": mode,
                "block_reason": "unsupported_evidence_level",
                "downgrade_state": "none",
                "downgrade_approved": False,
                "behavior_verification_claimed": False,
                    "gaps": [f"unsupported_evidence_level:{evidence_level}"],
                    "checks": ["contract_validation"],
                },
            2,
            "blocked unsupported_evidence_level",
        )

    if evidence_level == "promptfoo" and mode == "deterministic":
        if args.approve_downgrade:
            return (
                {
                    "status": "pass",
                    "evidence_mode": "deterministic",
                    "evidence_strength": "weaker_approved_no_behavior_claim",
                    "targeted_result": "pass",
                    "regression_result": "not_applicable",
                    "regression_rationale": "approved deterministic downgrade did not run promptfoo behavior evidence",
                    "provider": "none",
                    "execution_mode": "deterministic",
                    "block_reason": "none",
                    "downgrade_state": "approved",
                    "downgrade_approved": True,
                    "behavior_verification_claimed": False,
                    "gaps": ["approved_downgrade_no_promptfoo_behavior_claim"],
                    "checks": ["contract_validation", "structured_payload_coverage", "result_schema_parse"],
                },
                0,
                "status=pass downgrade_state=approved",
            )
        return (
            {
                "status": "blocked",
                "evidence_mode": "deterministic",
                "evidence_strength": "blocked_no_behavior_claim",
                "targeted_result": "blocked",
                "regression_result": "not_run",
                "regression_rationale": "promptfoo evidence was required but deterministic mode was forced",
                "provider": "none",
                "execution_mode": "deterministic",
                "block_reason": "unapproved_downgrade",
                "downgrade_state": "unapproved_blocked",
                "downgrade_approved": False,
                "behavior_verification_claimed": False,
                "gaps": ["unapproved_downgrade"],
                "checks": ["contract_validation"],
            },
            2,
            "blocked unapproved_downgrade",
        )

    if evidence_level == "promptfoo" or mode == "promptfoo-blocked":
        return (
            {
                "status": "blocked",
                "evidence_mode": "promptfoo_blocked",
                "evidence_strength": "blocked_no_behavior_claim",
                "targeted_result": "blocked",
                "regression_result": "not_run",
                "regression_rationale": "promptfoo execution is not available in baseline verification",
                "provider": "none",
                "execution_mode": "promptfoo-blocked",
                "block_reason": "promptfoo_execution_blocked",
                "downgrade_state": "none",
                "downgrade_approved": False,
                "behavior_verification_claimed": False,
                "gaps": ["promptfoo_execution_blocked"],
                "checks": ["contract_validation"],
            },
            2,
            "blocked promptfoo_execution_blocked",
        )

    return (
        {
            "status": "pass",
            "evidence_mode": "deterministic",
            "evidence_strength": "deterministic",
            "targeted_result": "pass",
            "regression_result": "not_applicable",
            "regression_rationale": "deterministic contract fields validated and result artifact was produced",
            "provider": "none",
            "execution_mode": "deterministic",
            "block_reason": "none",
            "downgrade_state": "none",
            "downgrade_approved": False,
            "behavior_verification_claimed": True,
            "gaps": [],
            "checks": ["contract_validation", "structured_payload_coverage", "result_schema_parse"],
        },
        0,
        "status=pass evidence_mode=deterministic",
    )


def evaluate(root: Path, args: argparse.Namespace) -> int:
    run_id_errors = validate_run_id(args.run_id)
    if run_id_errors:
        print_diagnostics(run_id_errors)
        return 1

    rel_contract = resolve_contract_relative(args.contract)
    if rel_contract is None:
        print_diagnostics(
            [
                diag(
                    "E_CONTRACT_PATH",
                    "contract path is not contained under the selected root",
                    f"got {args.contract!r}",
                    "use a contract id or behavior-texts/<id>/contract.md",
                )
            ]
        )
        return 1

    hinted_contract_id = contract_id_hint(args.contract, rel_contract)
    if hinted_contract_id is not None:
        hinted_result_rel = result_relative_path(hinted_contract_id, args.run_id)
        if (root / hinted_result_rel).exists():
            print_diagnostics(
                [
                    diag(
                        "E_RESULT_EXISTS",
                        "eval result already exists for this run id",
                        hinted_result_rel.as_posix(),
                        "choose a fresh run id before rerunning evaluation",
                    )
                ]
            )
            return 1

    data, diagnostics = load_valid_contract(root, rel_contract)
    if diagnostics or data is None:
        print_diagnostics(diagnostics)
        return 1

    contract_id = data["contract"]["id"]
    result_rel = result_relative_path(contract_id, args.run_id)
    result_full = root / result_rel
    if result_full.exists():
        print_diagnostics(
            [
                diag(
                    "E_RESULT_EXISTS",
                    "eval result already exists for this run id",
                    result_rel.as_posix(),
                    "choose a fresh run id before rerunning evaluation",
                )
            ]
        )
        return 1

    result_state, exit_code, stdout_summary = classify_result(args, data)
    command_text = " ".join(
        ["python3", "scripts/behavior_contract_eval.py", "evaluate", "--contract", args.contract, "--run-id", args.run_id]
        + (["--mode", args.mode] if args.mode != "auto" else [])
        + (["--approve-downgrade"] if args.approve_downgrade else [])
    )
    digest = contract_digest(root / rel_contract)
    gaps = result_state.pop("gaps")
    checks = result_state.pop("checks")
    content = make_result(
        contract_id=contract_id,
        digest=digest,
        contract_data=data,
        command_text=command_text,
        artifact_path=result_rel,
        gaps=gaps,
        checks=checks,
        **result_state,
    )
    try:
        tomllib.loads(content)
    except tomllib.TOMLDecodeError as exc:
        print_diagnostics(
            [
                diag(
                    "E_RESULT_TOML",
                    "generated result artifact is not valid TOML",
                    str(exc),
                    "fix result serialization before treating eval evidence as complete",
                )
            ]
        )
        return 1
    write_result(result_full, content)
    print(f"{stdout_summary} result={result_rel.as_posix()}")
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate behavior-text contracts.")
    parser.add_argument("--root", default=".", help="repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    evaluate_parser = subparsers.add_parser("evaluate", help="evaluate a behavior-text contract")
    evaluate_parser.add_argument("--contract", required=True, help="contract id or behavior-texts/<id>/contract.md")
    evaluate_parser.add_argument("--run-id", required=True, help="fresh lowercase kebab-case run id")
    evaluate_parser.add_argument("--mode", choices=["auto", "deterministic", "promptfoo-blocked"], default="auto")
    evaluate_parser.add_argument("--approve-downgrade", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.command == "evaluate":
        return evaluate(root, args)
    parser.error(f"unsupported command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
