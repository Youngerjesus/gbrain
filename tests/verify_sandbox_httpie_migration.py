#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required for sandbox fixture verification") from exc


ROOT = Path(__file__).resolve().parents[1]
SANDBOX = ROOT / "sandbox" / "httpie-python-rust-migration"
CLI = ROOT / "scripts" / "coverage_ledger.py"
PINNED_COMMIT = "5b604c37c6c67e18e7c3e9aee6c88a8c22b98345"
MANIFEST_DIGEST = "sha256:5f0b4991a7898602d56a2587f956afef11879fdceef1ddf450b25fdcc0eac180"
OMITTED_PATH = "httpie/core.py"
GENERIC_SETUP_ERROR_CODES = {
    "E_DECISION_REQUIRED",
    "E_DECISION_MISSING_RECHECK",
    "E_LEDGER_REQUIRED_MISSING",
    "E_YAML_ROOT",
    "E_YAML_PARSE",
    "E_EVIDENCE_PATH_MISSING",
    "E_EVIDENCE_PATH_ESCAPE",
}


def load_manifest() -> dict[str, Any]:
    path = SANDBOX / "manifest.yml"
    if not path.is_file():
        raise AssertionError(f"missing fixture file: {path.relative_to(ROOT)}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError("manifest must be a mapping")
    return data


def source_item_id(path: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", path).strip("_").lower()
    return f"src.file.{token}"


def canonical_source_inventory_digest(items: list[dict[str, Any]]) -> str:
    canonical = [
        {
            "source_item_id": item["source_item_id"],
            "source_method": item["source_method"],
            "source_refs": sorted(set(item["source_refs"])),
            "metadata": item.get("metadata", {}),
        }
        for item in sorted(items, key=lambda value: value["source_item_id"])
    ]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def canonical_scope_digest(items: list[dict[str, Any]]) -> str:
    canonical = []
    for item in sorted(items, key=lambda value: value["source_item_id"]):
        canonical.append(
            {
                "source_item_id": item["source_item_id"],
                "disposition": item["disposition"],
                "obligation_ids": sorted(set(item.get("obligation_ids", []))),
                "coverage_row_ids": sorted(set(item.get("coverage_row_ids", []))),
                "rationale": item.get("rationale", ""),
            }
        )
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def run_validator(requirement_dir: Path) -> tuple[int, dict[str, Any]]:
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "validate",
            "--mode",
            "readiness",
            "--requirement-dir",
            str(requirement_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    stream = result.stdout.strip() or result.stderr.strip()
    try:
        payload = json.loads(stream)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"validator did not emit JSON: {stream}") from exc
    return result.returncode, payload


def source_items(files: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "source_item_id": source_item_id(path),
            "source_method": "extracted",
            "source_refs": ["sandbox/httpie-python-rust-migration/manifest.yml#source_files"],
            "metadata": {
                "path": path,
                "commit": PINNED_COMMIT,
                "extraction_count": len(files),
                "extraction_digest": MANIFEST_DIGEST,
            },
        }
        for path in files
    ]


def build_fixture(root: Path, files: list[str], *, omit_path: str | None = None) -> None:
    items = source_items(files)
    source_digest = canonical_source_inventory_digest(items)
    reconciled = [
        {
            "source_item_id": source_item_id(path),
            "disposition": "included",
            "obligation_ids": ["migration.full_port"],
            "coverage_row_ids": ["migration.full_port"],
            "rationale": "HTTPie source file is included in the Rust migration obligation universe.",
        }
        for path in files
        if path != omit_path
    ]
    scope_digest = canonical_scope_digest(reconciled)
    write(root / "requirements.md", "# HTTPie Migration Fixture\n")
    write(root / "evidence.md", "# Evidence\n")
    write(
        root / "coverage-decision.yml",
        f"""
        requirement_id: httpie-migration-fixture
        decision_version: 1
        ledger_required: true
        ledger_path: coverage-ledger.yml
        decided_by_gate: requirement-clarifier
        decided_at: "2026-06-21T21:35:00+09:00"
        trigger_evaluation:
          accepted_scope_digest: {scope_digest}
          signals:
            source_obligation_inventory_required: true
            codebase_migration: true
            file_count: {len(files)}
          broad_work_detected: true
        source_refs:
          - sandbox/httpie-python-rust-migration/manifest.yml#source_files
        """,
    )
    lines = [
        "requirement_id: httpie-migration-fixture",
        "inventory_version: 1",
        f"source_inventory_digest: {source_digest}",
        "source_items:",
    ]
    for item in items:
        lines.extend(
            [
                f"  - source_item_id: {item['source_item_id']}",
                f"    title: {item['metadata']['path']}",
                "    source_method: extracted",
                "    source_refs:",
                "      - sandbox/httpie-python-rust-migration/manifest.yml#source_files",
                "    metadata:",
                f"      path: {item['metadata']['path']}",
                f"      commit: {PINNED_COMMIT}",
                f"      extraction_count: {len(files)}",
                f"      extraction_digest: {MANIFEST_DIGEST}",
            ]
        )
    write(root / "source-inventory.yml", "\n".join(lines) + "\n")
    lines = [
        "requirement_id: httpie-migration-fixture",
        "reconciliation_version: 1",
        f"source_inventory_digest: {source_digest}",
        "source_inventory_version: 1",
        f"accepted_scope_digest: {scope_digest}",
        "reviewer_status: SHIP",
        "source_obligation_review_required: true",
        "reconciled_items:",
    ]
    for item in reconciled:
        lines.extend(
            [
                f"  - source_item_id: {item['source_item_id']}",
                "    disposition: included",
                "    obligation_ids:",
                "      - migration.full_port",
                "    coverage_row_ids:",
                "      - migration.full_port",
                f"    rationale: {item['rationale']}",
            ]
        )
    write(root / "scope-reconciliation.yml", "\n".join(lines) + "\n")
    row_sources = [source_item_id(path) for path in files if path != omit_path]
    lines = [
        "requirement_id: httpie-migration-fixture",
        "ledger_version: 1",
        "ledger_required: true",
        "status: verified",
        "last_updated_by_gate: sandbox-fixture",
        'last_updated_at: "2026-06-21T21:35:00+09:00"',
        f"source_inventory_digest: {source_digest}",
        "source_inventory_version: 1",
        f"accepted_scope_digest: {scope_digest}",
        "reconciliation_version: 1",
        "closure_policy:",
        "  allowed_closed_statuses:",
        "    - verified",
        "    - not_required_with_reason",
        "    - deferred_with_user_acceptance",
        "  blocking_statuses:",
        "    - planned",
        "    - missing",
        "    - blocked",
        "    - stale_needs_recheck",
        "  evidence_rule: typed_evidence_required",
        "coverage_rows:",
        "  - row_id: migration.full_port",
        "    required: true",
        "    obligation_type: migration",
        "    description: HTTPie Python source files map to Rust migration obligations.",
        "    source_refs:",
        "      - sandbox/httpie-python-rust-migration/manifest.yml#source_files",
        "    source_item_ids:",
    ]
    lines.extend(f"      - {source_id}" for source_id in row_sources)
    lines.extend(
        [
            "    data_condition: all source files represented",
            "    required_evidence:",
            "      - row_count",
            "      - checksum",
            "    status: verified",
            "    evidence_refs:",
            "      - type: row_count",
            f"        ref: {len(row_sources)} mapped source files",
            "        recorded_in: sandbox/httpie-python-rust-migration/generated",
            "      - type: checksum",
            f"        ref: {MANIFEST_DIGEST}",
            "        recorded_in: sandbox/httpie-python-rust-migration/generated",
            "    recorded_in:",
            "      - sandbox/httpie-python-rust-migration/generated",
        ]
    )
    write(root / "coverage-ledger.yml", "\n".join(lines) + "\n")


class HttpieMigrationSandboxTest(unittest.TestCase):
    def test_manifest_is_pinned_complete_and_stable(self) -> None:
        manifest = load_manifest()
        files = manifest.get("source_files")
        self.assertEqual(manifest.get("repo_url"), "https://github.com/httpie/cli")
        self.assertEqual(manifest.get("commit"), PINNED_COMMIT)
        self.assertIsInstance(files, list)
        self.assertEqual(len(files), 78)
        self.assertEqual(len(set(files)), 78)
        self.assertTrue(all(isinstance(path, str) and path.startswith("httpie/") and path.endswith(".py") for path in files))
        digest = "sha256:" + hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(manifest.get("source_manifest_digest"), digest)
        self.assertEqual(digest, MANIFEST_DIGEST)
        self.assertIn(OMITTED_PATH, files)

    def test_positive_generated_fixture_passes_readiness(self) -> None:
        files = load_manifest()["source_files"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "positive"
            build_fixture(root, files)
            returncode, payload = run_validator(root)
        self.assertEqual(returncode, 0, payload)
        self.assertEqual(payload["status"], "pass")

    def test_negative_generated_fixture_fails_for_omitted_source_file(self) -> None:
        files = load_manifest()["source_files"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "negative"
            build_fixture(root, files, omit_path=OMITTED_PATH)
            returncode, payload = run_validator(root)
        self.assertNotEqual(returncode, 0, payload)
        self.assertEqual(payload["status"], "fail")
        codes = set(payload.get("error_codes", []))
        self.assertIn("E_SCOPE_RECONCILIATION_MISSING_ITEM", codes)
        self.assertTrue(codes.isdisjoint(GENERIC_SETUP_ERROR_CODES), payload)
        self.assertIn("scope-reconciliation-recheck", set(payload.get("routes", [])))
        missing = {
            error.get("source_item_id")
            for error in payload.get("errors", [])
            if error.get("code") == "E_SCOPE_RECONCILIATION_MISSING_ITEM"
        }
        self.assertIn(source_item_id(OMITTED_PATH), missing)


if __name__ == "__main__":
    unittest.main()
