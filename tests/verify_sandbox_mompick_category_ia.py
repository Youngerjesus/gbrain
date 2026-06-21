#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - baseline dependency check.
    raise SystemExit("PyYAML is required for sandbox fixture verification") from exc


ROOT = Path(__file__).resolve().parents[1]
SANDBOX = ROOT / "sandbox" / "mompick-category-ia"
CLI = ROOT / "scripts" / "coverage_ledger.py"

GENERIC_SETUP_ERROR_CODES = {
    "E_DECISION_REQUIRED",
    "E_DECISION_MISSING_RECHECK",
    "E_LEDGER_REQUIRED_MISSING",
    "E_YAML_ROOT",
    "E_YAML_PARSE",
    "E_YAML_MULTI_DOCUMENT",
    "E_YAML_UNSUPPORTED_CONSTRUCT",
    "E_EVIDENCE_PATH_MISSING",
    "E_EVIDENCE_PATH_ESCAPE",
}

EXPECTED_CATEGORIES = [
    ("pregnancy-birth", "Pregnancy & Birth", "src.category.pregnancy_birth", True),
    ("newborn-care", "Newborn Care", "src.category.newborn_care", True),
    ("feeding", "Feeding", "src.category.feeding", True),
    ("sleep", "Sleep", "src.category.sleep", True),
    ("health", "Health", "src.category.health", False),
    ("growth", "Growth", "src.category.growth", False),
    ("play-learning", "Play & Learning", "src.category.play_learning", False),
    ("kids-education", "Kids Education", "src.category.kids_education", False),
    ("family-outings", "Family Outings", "src.category.family_outings", False),
    ("parenting-life", "Parenting Life", "src.category.parenting_life", False),
    ("shopping-gear", "Shopping Gear", "src.category.shopping_gear", False),
    ("safety", "Safety", "src.category.safety", False),
]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"missing fixture file: {path.relative_to(ROOT)}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"fixture must be a mapping: {path.relative_to(ROOT)}")
    return data


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


def category_tuples(categories: list[Any]) -> list[tuple[str, str, str, bool]]:
    tuples = []
    for category in categories:
        if not isinstance(category, dict):
            raise AssertionError(f"category entry must be a mapping: {category!r}")
        tuples.append(
            (
                category.get("category_id"),
                category.get("label"),
                category.get("source_item_id"),
                category.get("seed_subset"),
            )
        )
    return tuples


def inventory_category_tuples(requirement_dir: Path) -> list[tuple[str, str, str, bool]]:
    inventory = load_yaml(requirement_dir / "source-inventory.yml")
    items = inventory.get("source_items")
    if not isinstance(items, list):
        raise AssertionError(f"source_items must be a list in {requirement_dir.relative_to(ROOT)}")
    tuples = []
    for item in items:
        if not isinstance(item, dict):
            raise AssertionError(f"source item must be a mapping in {requirement_dir.relative_to(ROOT)}")
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            raise AssertionError(f"source item metadata must be a mapping in {requirement_dir.relative_to(ROOT)}")
        category_id = metadata.get("category_id")
        if not category_id:
            continue
        tuples.append(
            (
                category_id,
                metadata.get("category_label"),
                item.get("source_item_id"),
                metadata.get("seed_subset"),
            )
        )
    return tuples


class MomPickCategoryIaSandboxTest(unittest.TestCase):
    def test_manifest_records_full_category_universe_and_seed_subset(self) -> None:
        manifest = load_yaml(SANDBOX / "manifest.yml")
        categories = manifest.get("category_universe")
        self.assertIsInstance(categories, list)
        self.assertEqual(len(categories), 12)

        observed = category_tuples(categories)
        self.assertEqual(observed, EXPECTED_CATEGORIES)

        ids = [category_id for category_id, _, _, _ in observed]
        labels = [label for _, label, _, _ in observed]
        source_item_ids = [source_item_id for _, _, source_item_id, _ in observed]

        self.assertEqual(len(set(ids)), 12)
        self.assertEqual(len(set(labels)), 12)
        self.assertEqual(len(set(source_item_ids)), 12)
        self.assertTrue(all(isinstance(value, str) and value for value in ids))
        self.assertTrue(all(isinstance(value, str) and value for value in labels))
        self.assertTrue(all(isinstance(value, str) and value.startswith("src.category.") for value in source_item_ids))

        seed_subset = [category_id for category_id, _, _, is_seed in observed if is_seed is True]
        self.assertEqual(len(seed_subset), 4)

        negative = manifest.get("negative_fixture")
        self.assertIsInstance(negative, dict)
        self.assertEqual(negative.get("kept_category_ids"), seed_subset)
        omitted = [category_id for category_id, _, _, is_seed in observed if is_seed is False]
        self.assertEqual(negative.get("omitted_category_ids"), omitted)

    def test_fixture_inventories_match_manifest_category_universe(self) -> None:
        manifest = load_yaml(SANDBOX / "manifest.yml")
        categories = manifest.get("category_universe")
        self.assertIsInstance(categories, list)
        expected = category_tuples(categories)

        self.assertEqual(inventory_category_tuples(SANDBOX / "positive-full-universe"), expected)
        self.assertEqual(inventory_category_tuples(SANDBOX / "negative-four-category-narrowed"), expected)

    def test_positive_fixture_passes_readiness(self) -> None:
        returncode, payload = run_validator(SANDBOX / "positive-full-universe")
        self.assertEqual(returncode, 0, payload)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["mode"], "readiness")

    def test_negative_four_category_fixture_fails_source_obligation_readiness(self) -> None:
        returncode, payload = run_validator(SANDBOX / "negative-four-category-narrowed")
        self.assertNotEqual(returncode, 0, payload)
        self.assertEqual(payload["status"], "fail")

        error_codes = set(payload.get("error_codes", []))
        self.assertIn("E_SCOPE_RECONCILIATION_MISSING_ITEM", error_codes)
        self.assertTrue(error_codes.isdisjoint(GENERIC_SETUP_ERROR_CODES), payload)

        routes = set(payload.get("routes", []))
        self.assertIn("scope-reconciliation-recheck", routes)
        missing_items = {
            error.get("source_item_id")
            for error in payload.get("errors", [])
            if error.get("code") == "E_SCOPE_RECONCILIATION_MISSING_ITEM"
        }
        self.assertGreaterEqual(len(missing_items), 8)


if __name__ == "__main__":
    unittest.main()
