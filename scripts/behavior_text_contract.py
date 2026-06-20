#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


ALLOWED_SOURCE_KINDS = {"prompt", "agents_md"}
ALLOWED_PROMPT_ROLES = {"behavior", "task_instruction", "user_template"}
FORBIDDEN_PROMPT_ROLES = {"judge", "optimizer", "orchestrator", "skill"}
FORBIDDEN_SNAPSHOT_KEYS = {
    "source_body",
    "body_snapshot",
    "full_text",
    "source_text",
    "prompt_body",
    "agents_body",
}
PROMPT_SUFFIXES = (".prompt", ".prompt.txt", ".prompt.md")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_SCHEMA_KEYS = {
    "contract": {"id", "version", "purpose"},
    "source": {"kind", "path", "prompt_role", "section", "heading", "line_range", "range_note"},
    "behavior": {"target_behavior", "inputs", "required_actions", "non_goals", "failure_modes", "decision_boundaries"},
    "verification": {"expectations", "handoff_route"},
    "impact": {
        "execution_boundary",
        "artifact_class",
        "evidence_level",
        "allowed_substitutions",
        "disallowed_substitutions",
        "downgrade_approval_rule",
    },
}


class Diagnostic:
    def __init__(self, code: str, problem: str, cause: str, fix: str) -> None:
        self.code = code
        self.problem = problem
        self.cause = cause
        self.fix = fix

    def render(self) -> str:
        return f"{self.code}: problem={self.problem}; cause={self.cause}; fix={self.fix}"


def diag(code: str, problem: str, cause: str, fix: str) -> Diagnostic:
    return Diagnostic(code, problem, cause, fix)


def repo_relative_path(value: str) -> Path:
    return Path(value)


def has_path_escape(path: Path) -> bool:
    return path.is_absolute() or any(part == ".." for part in path.parts)


def contract_path_for(root: Path, contract_id: str) -> Path:
    return root / "behavior-texts" / contract_id / "contract.md"


def canonical_contract_relative(contract_id: str) -> Path:
    return Path("behavior-texts") / contract_id / "contract.md"


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    if not text.startswith("+++\n"):
        return None, [
            diag(
                "E_FRONTMATTER",
                "contract is missing TOML frontmatter",
                "contract.md must start with +++",
                "add TOML frontmatter delimited by +++",
            )
        ]
    end = text.find("\n+++\n", 4)
    if end == -1:
        return None, [
            diag(
                "E_FRONTMATTER",
                "contract frontmatter is not closed",
                "closing +++ delimiter is missing",
                "add a closing +++ line after TOML fields",
            )
        ]
    try:
        return tomllib.loads(text[4:end]), []
    except tomllib.TOMLDecodeError as exc:
        return None, [
            diag(
                "E_TOML",
                "contract frontmatter is not valid TOML",
                str(exc),
                "fix TOML syntax before validating the contract",
            )
        ]


def get_nested(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def require_string(data: dict[str, Any], field: str, diagnostics: list[Diagnostic]) -> None:
    value = get_nested(data, field)
    if not isinstance(value, str) or not value.strip():
        diagnostics.append(
            diag(
                "E_REQUIRED_FIELD",
                f"{field} is required",
                "field is missing or empty",
                f"set non-empty string field {field}",
            )
        )


def require_int(data: dict[str, Any], field: str, diagnostics: list[Diagnostic]) -> None:
    if not isinstance(get_nested(data, field), int):
        diagnostics.append(
            diag(
                "E_REQUIRED_FIELD",
                f"{field} is required",
                "field is missing or not an integer",
                f"set integer field {field}",
            )
        )


def require_list(data: dict[str, Any], field: str, diagnostics: list[Diagnostic]) -> None:
    value = get_nested(data, field)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        diagnostics.append(
            diag(
                "E_REQUIRED_FIELD",
                f"{field} is required",
                "field is missing, empty, or contains non-string values",
                f"set {field} to a non-empty list of strings",
            )
        )


def find_forbidden_keys(value: Any, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if str(key) in FORBIDDEN_SNAPSHOT_KEYS:
                found.append(child_path)
            found.extend(find_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_forbidden_keys(child, f"{path}[{index}]"))
    return found


def validate_known_schema(data: dict[str, Any]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for table, value in data.items():
        if table not in ALLOWED_SCHEMA_KEYS:
            diagnostics.append(
                diag(
                    "E_UNKNOWN_FIELD",
                    "contract contains an unknown top-level table",
                    f"found {table}",
                    "remove fields outside contract, source, behavior, verification, and impact",
                )
            )
            continue
        if not isinstance(value, dict):
            diagnostics.append(
                diag(
                    "E_REQUIRED_FIELD",
                    f"{table} must be a TOML table",
                    f"found {type(value).__name__}",
                    f"make {table} a TOML table",
                )
            )
            continue
        allowed = ALLOWED_SCHEMA_KEYS[table]
        for key in value:
            if key not in allowed:
                diagnostics.append(
                    diag(
                        "E_UNKNOWN_FIELD",
                        "contract contains a field outside the executable schema",
                        f"found {table}.{key}",
                        "remove unknown fields or add them through a later accepted schema change",
                    )
                )
    return diagnostics


def validate_source_file(root: Path, data: dict[str, Any], diagnostics: list[Diagnostic]) -> None:
    source_kind = get_nested(data, "source.kind")
    source_path_value = get_nested(data, "source.path")
    if source_kind not in ALLOWED_SOURCE_KINDS:
        diagnostics.append(
            diag(
                "E_SOURCE_KIND",
                "source.kind is unsupported",
                f"got {source_kind!r}",
                "use source.kind prompt or agents_md",
            )
        )
        return
    if not isinstance(source_path_value, str) or not source_path_value.strip():
        diagnostics.append(
            diag(
                "E_REQUIRED_FIELD",
                "source.path is required",
                "source.path is missing or empty",
                "set source.path to a repo-relative file path",
            )
        )
        return
    for selector in ["source.section", "source.heading", "source.line_range", "source.range_note"]:
        value = get_nested(data, selector)
        if value is not None and not isinstance(value, str):
            diagnostics.append(
                diag(
                    "E_OPTIONAL_FIELD_TYPE",
                    f"{selector} must be a string when present",
                    f"got {type(value).__name__}",
                    f"remove {selector} or set it to a string",
                )
            )

    source_path = repo_relative_path(source_path_value)
    if has_path_escape(source_path):
        diagnostics.append(
            diag(
                "E_SOURCE_PATH_CONTAINMENT",
                "source.path must stay inside the selected root",
                f"got {source_path_value!r}",
                "use a repo-relative path without absolute roots or .. segments",
            )
        )
        return
    if not (root / source_path).is_file():
        diagnostics.append(
            diag(
                "E_SOURCE_MISSING",
                "source file does not exist",
                f"{source_path_value!r} was not found under the selected root",
                "point source.path at an existing prompt file or AGENTS.md",
            )
        )

    prompt_role = get_nested(data, "source.prompt_role")
    if source_kind == "agents_md":
        if source_path.name != "AGENTS.md":
            diagnostics.append(
                diag(
                    "E_SOURCE_AGENTS_PATH",
                    "agents_md source must target AGENTS.md",
                    f"got {source_path_value!r}",
                    "set source.path to AGENTS.md or another repo-relative AGENTS.md file",
                )
            )
        if prompt_role is not None:
            diagnostics.append(
                diag(
                    "E_SOURCE_PROMPT_ROLE",
                    "agents_md source must not include source.prompt_role",
                    "prompt_role is prompt-only",
                    "remove source.prompt_role for agents_md contracts",
                )
            )
        return

    if prompt_role not in ALLOWED_PROMPT_ROLES:
        diagnostics.append(
            diag(
                "E_SOURCE_PROMPT_ROLE",
                "prompt source has unsupported prompt_role",
                f"got {prompt_role!r}",
                f"use one of {', '.join(sorted(ALLOWED_PROMPT_ROLES))}",
            )
        )
    path_text = source_path.as_posix()
    positive_path = (
        path_text.startswith("prompts/")
        or path_text.startswith(".codex/prompts/")
        or any(path_text.endswith(suffix) for suffix in PROMPT_SUFFIXES)
    )
    if not positive_path:
        diagnostics.append(
            diag(
                "E_SOURCE_PROMPT_PATH",
                "prompt source path is not under an allowed prompt location",
                f"got {source_path_value!r}",
                "use prompts/, .codex/prompts/, or a .prompt/.prompt.txt/.prompt.md file",
            )
        )


def validate_contract_data(root: Path, data: dict[str, Any], rel_path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    contract_id = get_nested(data, "contract.id")
    if not isinstance(contract_id, str) or not ID_RE.match(contract_id):
        diagnostics.append(
            diag(
                "E_CONTRACT_ID",
                "contract.id must be kebab-case",
                f"got {contract_id!r}",
                "use a lowercase kebab-case contract id",
            )
        )
    elif rel_path != canonical_contract_relative(contract_id):
        diagnostics.append(
            diag(
                "E_CONTRACT_ID_PATH",
                "contract.id must match behavior-texts/<id>/contract.md",
                f"id {contract_id!r} does not match path {rel_path.as_posix()!r}",
                f"move the file to behavior-texts/{contract_id}/contract.md or update contract.id",
            )
        )

    if len(rel_path.parts) != 3 or rel_path.parts[0] != "behavior-texts" or rel_path.parts[2] != "contract.md":
        diagnostics.append(
            diag(
                "E_CONTRACT_PATH",
                "contract path is not canonical",
                f"got {rel_path.as_posix()!r}",
                "validate files at behavior-texts/<id>/contract.md",
            )
        )

    for field in [
        "contract.purpose",
        "source.kind",
        "source.path",
        "behavior.target_behavior",
        "verification.handoff_route",
        "impact.execution_boundary",
        "impact.artifact_class",
        "impact.evidence_level",
        "impact.downgrade_approval_rule",
    ]:
        require_string(data, field, diagnostics)
    require_int(data, "contract.version", diagnostics)
    for field in [
        "behavior.inputs",
        "behavior.required_actions",
        "behavior.non_goals",
        "behavior.failure_modes",
        "behavior.decision_boundaries",
        "verification.expectations",
        "impact.allowed_substitutions",
        "impact.disallowed_substitutions",
    ]:
        require_list(data, field, diagnostics)

    for key_path in find_forbidden_keys(data):
        diagnostics.append(
            diag(
                "E_FORBIDDEN_SNAPSHOT_KEY",
                "contract contains a forbidden source-body snapshot field",
                f"found {key_path}",
                "remove source body snapshots and keep only source references",
            )
        )

    diagnostics.extend(validate_known_schema(data))
    validate_source_file(root, data, diagnostics)
    return diagnostics


def validate_contract_file(root: Path, rel_path_text: str) -> list[Diagnostic]:
    rel_path = Path(rel_path_text)
    diagnostics: list[Diagnostic] = []
    if has_path_escape(rel_path):
        return [
            diag(
                "E_CONTRACT_PATH",
                "contract path is not contained under the selected root",
                f"got {rel_path_text!r}",
                "use behavior-texts/<id>/contract.md",
            )
        ]
    full_path = root / rel_path
    if not full_path.is_file():
        return [
            diag(
                "E_CONTRACT_MISSING",
                "contract file does not exist",
                f"{rel_path_text!r} was not found",
                "create the contract or pass the correct behavior-texts/<id>/contract.md path",
            )
        ]
    data, parse_errors = parse_frontmatter(full_path.read_text(encoding="utf-8"))
    diagnostics.extend(parse_errors)
    if data is not None:
        diagnostics.extend(validate_contract_data(root, data, rel_path))
    elif len(rel_path.parts) != 3 or rel_path.parts[0] != "behavior-texts" or rel_path.parts[2] != "contract.md":
        diagnostics.append(
            diag(
                "E_CONTRACT_PATH",
                "contract path is not canonical",
                f"got {rel_path.as_posix()!r}",
                "validate files at behavior-texts/<id>/contract.md",
            )
        )
    return diagnostics


def toml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def toml_list(values: list[str]) -> str:
    return "[" + ", ".join(toml_quote(value) for value in values) + "]"


def build_contract(args: argparse.Namespace) -> str:
    lines = [
        "+++",
        "[contract]",
        f"id = {toml_quote(args.contract_id)}",
        "version = 1",
        f"purpose = {toml_quote(args.purpose)}",
        "",
        "[source]",
        f"kind = {toml_quote(args.source_kind)}",
        f"path = {toml_quote(args.source)}",
    ]
    if args.prompt_role:
        lines.append(f"prompt_role = {toml_quote(args.prompt_role)}")
    for attr, key in [
        ("section", "section"),
        ("heading", "heading"),
        ("line_range", "line_range"),
        ("range_note", "range_note"),
    ]:
        value = getattr(args, attr)
        if value:
            lines.append(f"{key} = {toml_quote(value)}")
    lines.extend(
        [
            "",
            "[behavior]",
            f"target_behavior = {toml_quote(args.target_behavior)}",
            f"inputs = {toml_list(args.inputs)}",
            f"required_actions = {toml_list(args.required_actions)}",
            f"non_goals = {toml_list(args.non_goals)}",
            f"failure_modes = {toml_list(args.failure_modes)}",
            f"decision_boundaries = {toml_list(args.decision_boundaries)}",
            "",
            "[verification]",
            f"expectations = {toml_list(args.verification_expectations)}",
            f"handoff_route = {toml_quote(args.handoff_route)}",
            "",
            "[impact]",
            f"execution_boundary = {toml_quote(args.execution_boundary)}",
            f"artifact_class = {toml_quote(args.artifact_class)}",
            f"evidence_level = {toml_quote(args.evidence_level)}",
            f"allowed_substitutions = {toml_list(args.allowed_substitutions)}",
            f"disallowed_substitutions = {toml_list(args.disallowed_substitutions)}",
            f"downgrade_approval_rule = {toml_quote(args.downgrade_approval_rule)}",
            "+++",
            "",
            f"# Behavior Text Contract: {args.contract_id}",
            "",
            "This markdown body is human-readable context only. The TOML frontmatter is the executable contract boundary.",
            "",
        ]
    )
    return "\n".join(lines)


def print_diagnostics(diagnostics: list[Diagnostic]) -> None:
    for item in diagnostics:
        print(item.render(), file=sys.stderr)


def create_contract(root: Path, args: argparse.Namespace) -> int:
    if not ID_RE.match(args.contract_id):
        print_diagnostics(
            [
                diag(
                    "E_CONTRACT_ID",
                    "contract id must be lowercase kebab-case",
                    f"got {args.contract_id!r}",
                    "choose an id like prompt-boundary",
                )
            ]
        )
        return 1
    rel_path = canonical_contract_relative(args.contract_id)
    full_path = root / rel_path
    if full_path.exists() and not args.update:
        existing_errors = validate_contract_file(root, rel_path.as_posix())
        if existing_errors:
            print_diagnostics(
                [
                    diag(
                        "E_CONTRACT_EXISTS_INVALID",
                        "existing contract is invalid",
                        "target contract exists but does not validate",
                        "rerun with --update and valid fields to repair it",
                    )
                ]
                + existing_errors
            )
        else:
            print_diagnostics(
                [
                    diag(
                        "E_CONTRACT_EXISTS",
                        "contract already exists and validates",
                        rel_path.as_posix(),
                        "run validate or rerun create with --update to replace it",
                    )
                ]
            )
        return 1

    candidate = build_contract(args)
    data, parse_errors = parse_frontmatter(candidate)
    diagnostics = list(parse_errors)
    if data is not None:
        diagnostics.extend(validate_contract_data(root, data, rel_path))
    if diagnostics:
        print_diagnostics(diagnostics)
        return 1

    full_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".contract.", suffix=".tmp", dir=str(full_path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(candidate)
        os.replace(tmp_name, full_path)
    finally:
        tmp_path = Path(tmp_name)
        if tmp_path.exists():
            tmp_path.unlink()
    print(f"created {rel_path.as_posix()}")
    return 0


def validate_command(root: Path, args: argparse.Namespace) -> int:
    diagnostics = validate_contract_file(root, args.contract_path)
    if diagnostics:
        print_diagnostics(diagnostics)
        return 1
    print(f"OK {args.contract_path}")
    return 0


def add_common_create_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", dest="contract_id", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--source-kind", required=True)
    parser.add_argument("--prompt-role")
    parser.add_argument("--section")
    parser.add_argument("--heading")
    parser.add_argument("--line-range")
    parser.add_argument("--range-note")
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--target-behavior", required=True)
    parser.add_argument("--input", dest="inputs", action="append", required=True)
    parser.add_argument("--required-action", dest="required_actions", action="append", required=True)
    parser.add_argument("--non-goal", dest="non_goals", action="append", required=True)
    parser.add_argument("--failure-mode", dest="failure_modes", action="append", required=True)
    parser.add_argument("--decision-boundary", dest="decision_boundaries", action="append", required=True)
    parser.add_argument("--verification-expectation", dest="verification_expectations", action="append", required=True)
    parser.add_argument("--handoff-route", required=True)
    parser.add_argument("--execution-boundary", required=True)
    parser.add_argument("--artifact-class", required=True)
    parser.add_argument("--evidence-level", required=True)
    parser.add_argument("--allowed-substitution", dest="allowed_substitutions", action="append", required=True)
    parser.add_argument("--disallowed-substitution", dest="disallowed_substitutions", action="append", required=True)
    parser.add_argument("--downgrade-approval-rule", required=True)
    parser.add_argument("--update", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and validate behavior text contracts.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="Create or update a behavior-text contract.")
    add_common_create_args(create)
    validate = subparsers.add_parser("validate", help="Validate a behavior-text contract.")
    validate.add_argument("contract_path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if args.command == "create":
        return create_contract(root, args)
    if args.command == "validate":
        return validate_command(root, args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
