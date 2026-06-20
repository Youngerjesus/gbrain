#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

LIFECYCLE_SKILLS = [
    "skill-creator",
    "skill-review",
    "skillify",
    "skill-optimizer",
    "skillpack-check",
    "skillpack-harvest",
]


def load_module(relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load module at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def skillopt_benchmark_paths(skill_name: str) -> tuple[Path, Path]:
    benchmark_path = ROOT / ".codex" / "skills" / skill_name / "skillopt-benchmark.jsonl"
    template_path = (
        ROOT
        / ".codex"
        / "skills"
        / "project-bootstrap"
        / "templates"
        / "root"
        / ".codex"
        / "skills"
        / skill_name
        / "skillopt-benchmark.jsonl"
    )
    return benchmark_path, template_path


def write_demo_benchmark(path: Path, *, count: int = 15, mapping: bool = False) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx in range(1, count + 1):
        if mapping:
            checks = [
                {
                    "op": "mapping_contains",
                    "arg": {"items": [{"key": "evidence", "value": f"accepted-{idx:02d}"}]},
                }
            ]
        else:
            checks = [{"op": "contains", "arg": "improved"}]
        rows.append(
            {
                "task_id": f"demo-{idx:02d}",
                "task": f"Demo task {idx:02d}",
                "judge": {"kind": "rule", "checks": checks},
            }
        )
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return rows


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise AssertionError("missing frontmatter start")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError("missing frontmatter end")
    frontmatter = text[4:end]
    result: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []
    for line in frontmatter.splitlines():
        if line.startswith(" ") and current_key:
            current_lines.append(line.strip())
            continue
        if current_key:
            result[current_key] = "\n".join(current_lines).strip()
            current_key = None
            current_lines = []
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in {"|", ">"}:
            current_key = key
            current_lines = []
        else:
            result[key] = value.strip("'\"")
    if current_key:
        result[current_key] = "\n".join(current_lines).strip()
    return result


class SkillLifecyclePackStructureTest(unittest.TestCase):
    def test_lifecycle_skills_are_codex_native(self) -> None:
        forbidden = [
            "/Users/",
            ".claude/skills",
            "AskUserQuestion",
            "$B",
            "allowed-tools:",
        ]
        for skill in LIFECYCLE_SKILLS:
            with self.subTest(skill=skill):
                skill_file = ROOT / ".codex" / "skills" / skill / "SKILL.md"
                self.assertTrue(skill_file.is_file(), f"missing {skill_file}")
                text = skill_file.read_text(encoding="utf-8")
                frontmatter = parse_frontmatter(text)
                self.assertEqual(frontmatter.get("name"), skill)
                self.assertTrue(frontmatter.get("description"), f"{skill} missing description")
                self.assertIn("## Workflow", text)
                self.assertIn("## Anti-Patterns", text)
                for needle in forbidden:
                    self.assertNotIn(needle, text)

    def test_skill_optimizer_declares_original_gbrain_safety_gates(self) -> None:
        text = read(".codex/skills/skill-optimizer/SKILL.md")
        for required in [
            "SKILL.md as trainable parameters",
            "body-only",
            "median-of-3",
            "epsilon=0.05",
            "held-out",
            "BOOTSTRAP_PENDING_REVIEW",
            "proposed.md",
            "history.json",
            "rejected.json",
            "gpt-5.5",
            "same model for target and optimizer",
        ]:
            self.assertIn(required, text)

    def test_skill_review_preserves_gstack_meta_review_shape(self) -> None:
        text = read(".codex/skills/skill-review/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "skill-review")
        self.assertIn("Review Codex skills", frontmatter.get("description", ""))
        for required in [
            "report-only",
            "Resolve The Target",
            "Read The Skill Union",
            "Static Validation",
            "Review Rubric",
            "Required Checks",
            "findings-first scorecard",
            "Routing and discoverability",
            "Executable workflow",
            "Question gates",
            "Host and model portability",
            "READY WITH NITS",
        ]:
            self.assertIn(required, text)
        for forbidden in [
            "preamble-tier",
            "allowed-tools:",
            "AskUserQuestion",
            ".claude/skills",
            "gstack-config",
        ]:
            self.assertNotIn(forbidden, text)

    def test_scripts_verify_runs_lifecycle_contract(self) -> None:
        verify = read("scripts/verify")
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", verify)
        self.assertIn("python3 tests/verify_skill_lifecycle_pack.py", verify)
        self.assertNotIn("tests/verify_gstack_codex_skills.py", verify)


class SkillOptCoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")
        cls.runner = load_module(".codex/skills/skill-optimizer/scripts/skillopt_runner.py")
        cls.live = load_module(".codex/skills/skill-optimizer/scripts/skillopt_live.py")

    def test_benchmark_split_requires_selection_floor(self) -> None:
        rows = [
            {
                "task_id": f"t-{idx:02d}",
                "task": f"Task {idx}",
                "judge": {"kind": "rule", "checks": [{"op": "max_chars", "arg": 1000}]},
            }
            for idx in range(15)
        ]
        split = self.skillopt.split_benchmark(rows, (1, 1, 1))
        self.assertEqual((len(split.train), len(split.sel), len(split.test)), (5, 5, 5))
        with self.assertRaisesRegex(ValueError, "D_sel"):
            self.skillopt.split_benchmark(rows, (4, 1, 5))

    def test_apply_edit_preserves_frontmatter_and_rejects_code_fence(self) -> None:
        text = "---\nname: demo\n---\n# Demo\n\n## Workflow\nOld line\n\n```text\nOld code\n```\n"
        replaced = self.skillopt.apply_edit(
            text,
            {"op": "replace", "target": "Old line", "replacement": "New line"},
        )
        self.assertEqual(replaced["outcome"], "applied")
        self.assertIn("name: demo", replaced["text"])
        self.assertIn("New line", replaced["text"])
        rejected = self.skillopt.apply_edit(
            text,
            {"op": "replace", "target": "Old code", "replacement": "New code"},
        )
        self.assertEqual(rejected["outcome"], "rejected")
        self.assertEqual(rejected["reason"], "inside_code_fence")

    def test_rule_score_and_validation_gate_use_medians_and_margin(self) -> None:
        task = {
            "task_id": "r-001",
            "task": "answer compactly",
            "judge": {
                "kind": "rule",
                "checks": [
                    {"op": "contains", "arg": "Answer"},
                    {"op": "section_present", "arg": "Decision"},
                    {"op": "max_chars", "arg": 200},
                ],
            },
        }
        good = "# Decision\nAnswer\n"
        bad = "Answer only"
        self.assertEqual(self.skillopt.score_rule(good, [], task["judge"]["checks"]), 1.0)
        result = self.skillopt.validation_gate(
            [task],
            {"r-001": [bad, good, good]},
            best_score=0.90,
            epsilon=0.05,
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["sel_score"], 1.0)

    def test_rule_score_detail_reports_each_check(self) -> None:
        checks = [
            {"op": "contains", "arg": "Deterministic verification"},
            {"op": "contains", "arg": "Empirical verification"},
            {"op": "contains", "arg": "Probabilistic verification"},
            {"op": "contains", "arg": "executable acceptance criteria"},
        ]
        detail = self.skillopt.score_rule_detail(
            "Use Deterministic verification with executable acceptance criteria.",
            [],
            checks,
        )
        self.assertEqual(detail["score"], 0.5)
        self.assertEqual(
            detail["checks"],
            [
                {"op": "contains", "arg": "Deterministic verification", "passed": True},
                {"op": "contains", "arg": "Empirical verification", "passed": False},
                {"op": "contains", "arg": "Probabilistic verification", "passed": False},
                {"op": "contains", "arg": "executable acceptance criteria", "passed": True},
            ],
        )

    def test_mapping_contains_rule_scores_structured_markdown_evidence(self) -> None:
        checks = [
            {
                "op": "mapping_contains",
                "arg": {
                    "items": [
                        {"key": "tax rounding", "value": "Deterministic verification"},
                        {"key": "dashboard visual polish", "value": "Empirical verification"},
                        {"key": "LLM summary quality", "value": "Probabilistic verification"},
                    ]
                },
            }
        ]
        answer = "\n".join(
            [
                "- tax rounding: Deterministic verification",
                "- dashboard visual polish: Empirical verification",
                "- LLM summary quality: Probabilistic verification",
            ]
        )
        detail = self.skillopt.score_rule_detail(answer, [], checks)
        structured = detail["checks"][0]
        self.assertEqual(detail["score"], 1.0)
        self.assertTrue(structured["passed"])
        self.assertEqual(structured["score"], 1.0)
        self.assertTrue(all(item["passed"] for item in structured["items"]))

    def test_mapping_contains_rule_reports_fractional_item_diagnostics(self) -> None:
        checks = [
            {
                "op": "mapping_contains",
                "arg": {
                    "items": [
                        {"key": "tax rounding", "value": "Deterministic verification"},
                        {"key": "dashboard visual polish", "value": "Empirical verification"},
                        {"key": "LLM summary quality", "value": "Probabilistic verification"},
                    ]
                },
            }
        ]
        answer = "\n".join(
            [
                "| Work | Verification |",
                "| --- | --- |",
                "| tax rounding | Deterministic verification |",
                "| dashboard visual polish | Deterministic verification |",
            ]
        )
        detail = self.skillopt.score_rule_detail(answer, [], checks)
        structured = detail["checks"][0]
        self.assertAlmostEqual(detail["score"], 1 / 3)
        self.assertAlmostEqual(structured["score"], 1 / 3)
        self.assertFalse(structured["passed"])
        self.assertEqual(
            [(item["key"], item["expected"], item["actual"], item["passed"]) for item in structured["items"]],
            [
                ("tax rounding", "Deterministic verification", "Deterministic verification", True),
                ("dashboard visual polish", "Empirical verification", "Deterministic verification", False),
                ("LLM summary quality", "Probabilistic verification", None, False),
            ],
        )

    def test_benchmark_validation_accepts_and_rejects_mapping_contains_shape(self) -> None:
        valid = {
            "task_id": "map-001",
            "task": "Map work to verification strategies.",
            "judge": {
                "kind": "rule",
                "checks": [
                    {
                        "op": "mapping_contains",
                        "arg": {"items": [{"key": "tax rounding", "value": "Deterministic verification"}]},
                    }
                ],
            },
        }
        self.skillopt.validate_task(valid, 1)
        invalid = {
            **valid,
            "judge": {"kind": "rule", "checks": [{"op": "mapping_contains", "arg": {"items": [{"key": ""}]}}]},
        }
        with self.assertRaisesRegex(ValueError, "mapping_contains"):
            self.skillopt.validate_task(invalid, 2)

    def test_validation_gate_scores_tool_call_rollout_records(self) -> None:
        task = {
            "task_id": "tool-001",
            "task": "browse the requested page",
            "judge": {
                "kind": "rule",
                "checks": [{"op": "tool_called", "arg": "web.open"}],
            },
        }
        result = self.skillopt.validation_gate(
            [task],
            {
                "tool-001": [
                    {"final_text": "Done", "tool_calls": [{"name": "web.open"}]},
                    {"final_text": "Done", "tool_calls": [{"name": "web.open", "failed": False}]},
                    {"final_text": "Done", "tool_calls": [{"name": "web.open"}]},
                ]
            },
            best_score=0.50,
            epsilon=0.05,
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["sel_score"], 1.0)

    def test_validation_gate_requires_exactly_three_rollouts_per_task(self) -> None:
        task = {
            "task_id": "r-001",
            "task": "answer compactly",
            "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "Answer"}]},
        }
        with self.assertRaisesRegex(ValueError, "exactly 3 rollout"):
            self.skillopt.validation_gate([task], {"r-001": ["Answer"]}, best_score=0.0)
        with self.assertRaisesRegex(ValueError, "exactly 3 rollout"):
            self.skillopt.validation_gate([task], {}, best_score=0.0)
        with self.assertRaisesRegex(ValueError, "exactly 3 rollout"):
            self.skillopt.validation_gate([task], {"r-001": ["Answer"] * 4}, best_score=0.0)

    def test_runner_cli_dry_run_loads_core_directly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            write_demo_benchmark(skill_dir / "skillopt-benchmark.jsonl", count=28)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / ".codex" / "skills" / "skill-optimizer" / "scripts" / "skillopt_runner.py"),
                    "demo",
                    "--root",
                    str(root),
                    "--bootstrap-reviewed",
                    "--split",
                    "1:1:1",
                    "--dry-run",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["reason"], "dry_run")
            self.assertEqual(payload["split"], {"train": 9, "sel": 9, "test": 10})

    def test_runner_bootstrap_dry_run_and_candidate_acceptance_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )

            bootstrap = self.runner.bootstrap_from_skill(root, "demo", task_count=15)
            benchmark = skill_dir / "skillopt-benchmark.jsonl"
            self.assertEqual(bootstrap["status"], "bootstrapped")
            self.assertTrue(benchmark.read_text(encoding="utf-8").rstrip().endswith(self.skillopt.BOOTSTRAP_PENDING_REVIEW))
            with self.assertRaisesRegex(ValueError, "BOOTSTRAP_PENDING_REVIEW"):
                self.runner.dry_run(root, "demo", split_ratio=(1, 1, 1), bootstrap_reviewed=False)

            reviewed_text = benchmark.read_text(encoding="utf-8").replace(
                self.skillopt.BOOTSTRAP_PENDING_REVIEW,
                "",
            )
            benchmark.write_text(reviewed_text, encoding="utf-8")
            preview = self.runner.dry_run(root, "demo", split_ratio=(1, 1, 1), bootstrap_reviewed=True)
            self.assertEqual(preview["outcome"], "aborted")
            self.assertEqual(preview["split"], {"train": 5, "sel": 5, "test": 5})

            candidate = root / "candidate.md"
            candidate.write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n\n## SkillOpt Criteria\n\nInclude task, answer, and next step.\n",
                encoding="utf-8",
            )
            rollouts = root / "rollouts.json"
            sel_ids = [row["task_id"] for row in self.skillopt.split_benchmark(
                self.skillopt.load_benchmark(benchmark, bootstrap_reviewed=True),
                (1, 1, 1),
            ).sel]
            rollout_payload = {
                task_id: [
                    "task answer next step",
                    "task answer next step",
                    "task answer next step",
                ]
                for task_id in sel_ids
            }
            rollouts.write_text(json.dumps(rollout_payload), encoding="utf-8")
            result = self.runner.run_with_candidate(
                root,
                "demo",
                candidate_path=candidate,
                rollouts_path=rollouts,
                split_ratio=(1, 1, 1),
                bootstrap_reviewed=True,
                no_mutate=True,
                baseline_score=0.0,
            )
            self.assertEqual(result["outcome"], "accepted")
            self.assertFalse(result["mutated_skill_file"])
            self.assertTrue((skill_dir / "proposed.md").is_file())
            self.assertTrue((skill_dir / "skillopt" / "best.md").is_file())
            history = json.loads((skill_dir / "skillopt" / "history.json").read_text(encoding="utf-8"))
            self.assertEqual(history[-1]["outcome"], "accepted")

    def test_runner_proxy_scores_candidate_against_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            baseline = skill_dir / "SKILL.md"
            baseline.write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            self.runner.bootstrap_from_skill(root, "demo", task_count=15)
            benchmark = skill_dir / "skillopt-benchmark.jsonl"
            benchmark.write_text(
                benchmark.read_text(encoding="utf-8").replace(self.skillopt.BOOTSTRAP_PENDING_REVIEW, ""),
                encoding="utf-8",
            )
            candidate = root / "candidate.md"
            candidate.write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. task answer next step.\n",
                encoding="utf-8",
            )
            result = self.runner.run_proxy_candidate(
                root,
                "demo",
                candidate_path=candidate,
                split_ratio=(1, 1, 1),
                bootstrap_reviewed=True,
            )
            self.assertEqual(result["mode"], "proxy_from_skill_text")
            self.assertEqual(result["outcome"], "accepted")
            self.assertLess(result["baseline_sel_score"], result["candidate_sel_score"])
            self.assertIn("not live task rollouts", result["proxy_warning"])

    def test_live_runner_fake_client_closes_generator_evaluator_loop(self) -> None:
        class FakeChatClient:
            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                if model == "optimizer":
                    return json.dumps(
                        {
                            "edits": [
                                {
                                    "op": "add",
                                    "anchor": "Workflow",
                                    "content": "Always include improved in the answer.",
                                    "reason": "Selection tasks require the word improved.",
                                }
                            ]
                        }
                    )
                return "improved answer" if "Always include improved" in system else "plain answer"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "task_id": f"live-{idx:02d}",
                    "task": f"Live task {idx}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "improved"}]},
                }
                for idx in range(15)
            ]
            (skill_dir / "skillopt-benchmark.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.live.run_live_skillopt(
                root=root,
                skill_name="demo",
                models=self.live.LiveModels(target="target", optimizer="optimizer"),
                chat_client=FakeChatClient(),
                split_ratio=(1, 1, 1),
                bootstrap_reviewed=True,
                epochs=1,
                batch_size=5,
            )
            self.assertEqual(result["outcome"], "accepted")
            self.assertEqual(result["mode"], "live_closed_loop")
            self.assertEqual(result["baseline_sel_score"], 0.0)
            self.assertEqual(result["best_sel_score"], 1.0)
            self.assertEqual(result["test_score"], 1.0)
            events = [row["event"] for row in result["trace"]]
            self.assertEqual(
                events,
                ["baseline_validation", "reflect", "candidate_generated", "candidate_validation", "final_test"],
            )
            self.assertTrue((skill_dir / "skillopt" / "best.md").is_file())
            self.assertTrue(any(path.endswith(".trace.json") for path in result["files_written"]))

            receipt_path = next(Path(path) for path in result["files_written"] if path.endswith(".receipt.json"))
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["baseline_sel_score"], 0.0)
            self.assertEqual(receipt["test_score"], 1.0)
            self.assertEqual(receipt["models"], {"target": "target", "optimizer": "optimizer", "judge": None})
            self.assertEqual(receipt["split"], {"train": 5, "sel": 5, "test": 5})
            self.assertRegex(receipt["candidate_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(receipt["benchmark_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(receipt["baseline_gate"]["sel_score"], 0.0)
            self.assertEqual(receipt["validation_gate"]["sel_score"], 1.0)
            self.assertEqual(receipt["test_gate"]["sel_score"], 1.0)
            run_detail = receipt["validation_gate"]["per_task_medians"][0]["run_details"][0]
            self.assertEqual(run_detail["score"], 1.0)
            self.assertEqual(run_detail["checks"][0]["arg"], "improved")
            self.assertFalse(run_detail["contract_violation"])

    def test_live_rule_rollout_prompts_for_contract_repairs_and_records_detail(self) -> None:
        class FakeChatClient:
            def __init__(self) -> None:
                self.calls: list[tuple[str, str, str]] = []

            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                self.calls.append((model, system, user))
                if "Repair the answer" in system:
                    return "\n".join(
                        [
                            "Deterministic verification",
                            "Empirical verification",
                            "Probabilistic verification",
                            "executable acceptance criteria",
                        ]
                    )
                return "deterministic, empirical, probabilistic with criteria"

        task = {
            "task_id": "strategy-001",
            "task": "Choose strategy for tax, UI, and LLM work.",
            "judge": {
                "kind": "rule",
                "checks": [
                    {"op": "contains", "arg": "Deterministic verification"},
                    {"op": "contains", "arg": "Empirical verification"},
                    {"op": "contains", "arg": "Probabilistic verification"},
                    {"op": "contains", "arg": "executable acceptance criteria"},
                ],
            },
        }
        client = FakeChatClient()
        trajectory = self.live._run_rollout(client, "system skill", task, "target")
        self.assertIn("Deterministic contract", client.calls[0][1])
        self.assertIn("contains: Deterministic verification", client.calls[0][2])
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(trajectory["contract"]["status"], "repaired")
        self.assertEqual(trajectory["contract"]["attempts"], 1)
        self.assertEqual(trajectory["contract"]["initial_score"], 0.0)
        self.assertEqual(trajectory["contract"]["final_score"], 1.0)
        self.assertTrue(all(check["passed"] for check in trajectory["contract"]["checks"]))

    def test_live_rule_contract_describes_mapping_contains_items(self) -> None:
        task = {
            "task_id": "strategy-001",
            "task": "Choose strategy for tax, UI, and LLM work.",
            "judge": {
                "kind": "rule",
                "checks": [
                    {
                        "op": "mapping_contains",
                        "arg": {
                            "items": [
                                {"key": "tax rounding", "value": "Deterministic verification"},
                                {"key": "dashboard visual polish", "value": "Empirical verification"},
                            ]
                        },
                    }
                ],
            },
        }
        contract = self.live._rule_contract(task)
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertIn("mapping_contains", contract["user"])
        self.assertIn("tax rounding -> Deterministic verification", contract["user"])
        self.assertIn("dashboard visual polish -> Empirical verification", contract["user"])

    def test_live_rule_rollout_skips_repair_when_contract_passes(self) -> None:
        class FakeChatClient:
            def __init__(self) -> None:
                self.calls = 0

            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                self.calls += 1
                return "Deterministic verification"

        task = {
            "task_id": "strategy-001",
            "task": "Choose strategy.",
            "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "Deterministic verification"}]},
        }
        client = FakeChatClient()
        trajectory = self.live._run_rollout(client, "system skill", task, "target")
        self.assertEqual(client.calls, 1)
        self.assertEqual(trajectory["contract"]["status"], "passed")
        self.assertEqual(trajectory["contract"]["attempts"], 0)

    def test_live_rule_rollout_records_repair_failed_detail(self) -> None:
        class FakeChatClient:
            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                return "still missing"

        task = {
            "task_id": "strategy-001",
            "task": "Choose strategy.",
            "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "Deterministic verification"}]},
        }
        trajectory = self.live._run_rollout(FakeChatClient(), "system skill", task, "target")
        self.assertEqual(trajectory["contract"]["status"], "repair_failed")
        self.assertEqual(trajectory["contract"]["attempts"], 1)
        self.assertEqual(trajectory["contract"]["initial_score"], 0.0)
        self.assertEqual(trajectory["contract"]["final_score"], 0.0)
        self.assertEqual(trajectory["contract"]["missing"][0]["arg"], "Deterministic verification")

    def test_live_rule_rollout_preserves_original_tool_call_evidence_after_repair(self) -> None:
        class FakeChatClient:
            def __init__(self) -> None:
                self.last_tool_calls: list[dict[str, object]] = []
                self.calls = 0

            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                self.calls += 1
                if self.calls == 1:
                    self.last_tool_calls = [{"name": "web.open", "failed": False}]
                    return "missing text"
                self.last_tool_calls = []
                return "required text"

        task = {
            "task_id": "tool-001",
            "task": "Open the page and report required text.",
            "judge": {
                "kind": "rule",
                "checks": [
                    {"op": "tool_called", "arg": "web.open"},
                    {"op": "contains", "arg": "required text"},
                ],
            },
        }
        trajectory = self.live._run_rollout(FakeChatClient(), "system skill", task, "target")
        self.assertEqual(trajectory["contract"]["status"], "repaired")
        self.assertEqual(trajectory["contract"]["final_score"], 1.0)
        self.assertEqual(trajectory["tool_calls"], [{"name": "web.open", "failed": False}])

    def test_mixed_rule_llm_gate_keeps_rule_contract_details(self) -> None:
        class FakeJudgeClient:
            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                return json.dumps({"score": 1.0, "rationale": "ok"})

        rule_task = {
            "task_id": "rule-001",
            "task": "Include required phrase.",
            "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "required phrase"}]},
        }
        llm_task = {
            "task_id": "llm-001",
            "task": "Summarize.",
            "judge": {"kind": "llm", "rubric": "Score concise summaries."},
        }
        rollouts = {
            "rule-001": [
                {
                    "final_text": "missing",
                    "tool_calls": [],
                    "contract": {
                        "status": "repair_failed",
                        "attempts": 1,
                        "final_score": 0.0,
                        "checks": [{"op": "contains", "arg": "required phrase", "passed": False}],
                        "missing": [{"op": "contains", "arg": "required phrase", "passed": False}],
                    },
                },
                {"final_text": "missing", "tool_calls": []},
                {"final_text": "missing", "tool_calls": []},
            ],
            "llm-001": [
                {"final_text": "summary", "tool_calls": []},
                {"final_text": "summary", "tool_calls": []},
                {"final_text": "summary", "tool_calls": []},
            ],
        }
        gate = self.live._score_rollout_records(
            [rule_task, llm_task],
            rollouts,
            judge_model="judge",
            chat_client=FakeJudgeClient(),
            best_score=-1.0,
            epsilon=0.05,
        )
        rule_row = next(row for row in gate["per_task_medians"] if row["task_id"] == "rule-001")
        self.assertEqual(rule_row["runs"], [0.0, 0.0, 0.0])
        self.assertEqual(rule_row["run_details"][0]["checks"][0]["arg"], "required phrase")
        self.assertTrue(rule_row["run_details"][0]["contract_violation"])
        self.assertEqual(rule_row["run_details"][0]["contract"]["status"], "repair_failed")

    def test_live_runner_rejects_direct_mutation_without_held_out_gate(self) -> None:
        class FakeChatClient:
            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                return json.dumps({"edits": []}) if model == "optimizer" else "plain answer"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "task_id": f"live-{idx:02d}",
                    "task": f"Live task {idx}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "improved"}]},
                }
                for idx in range(15)
            ]
            (skill_dir / "skillopt-benchmark.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "held-out live gate"):
                self.live.run_live_skillopt(
                    root=root,
                    skill_name="demo",
                    models=self.live.LiveModels(target="target", optimizer="optimizer"),
                    chat_client=FakeChatClient(),
                    split_ratio=(1, 1, 1),
                    bootstrap_reviewed=True,
                    no_mutate=False,
                )

    def test_live_runner_mutates_after_passing_live_held_out_gate(self) -> None:
        class FakeChatClient:
            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                if model == "optimizer":
                    return json.dumps(
                        {
                            "edits": [
                                {
                                    "op": "add",
                                    "anchor": "Workflow",
                                    "content": "Always include improved in the answer.",
                                    "reason": "Selection and held-out tasks require the word improved.",
                                }
                            ]
                        }
                    )
                return "improved answer" if "Always include improved" in system else "plain answer"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "task_id": f"live-{idx:02d}",
                    "task": f"Live task {idx}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "improved"}]},
                }
                for idx in range(15)
            ]
            (skill_dir / "skillopt-benchmark.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            held_rows = [
                {
                    "task_id": f"held-{idx:02d}",
                    "task": f"Held out task {idx}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "improved"}]},
                }
                for idx in range(5)
            ]
            held_out = root / "held-out.jsonl"
            held_out.write_text("\n".join(json.dumps(row) for row in held_rows) + "\n", encoding="utf-8")
            result = self.live.run_live_skillopt(
                root=root,
                skill_name="demo",
                models=self.live.LiveModels(target="target", optimizer="optimizer"),
                chat_client=FakeChatClient(),
                split_ratio=(1, 1, 1),
                bootstrap_reviewed=True,
                no_mutate=False,
                held_out_path=held_out,
                epochs=1,
                batch_size=5,
            )
            self.assertEqual(result["outcome"], "accepted")
            self.assertTrue(result["mutated_skill_file"])
            self.assertIn("Always include improved", skill_file.read_text(encoding="utf-8"))
            events = [row["event"] for row in result["trace"]]
            self.assertIn("held_out_validation", events)

    def test_live_runner_mutation_write_failure_does_not_leave_accepted_artifacts(self) -> None:
        class FakeChatClient:
            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                if model == "optimizer":
                    return json.dumps(
                        {
                            "edits": [
                                {
                                    "op": "add",
                                    "anchor": "Workflow",
                                    "content": "Always include improved in the answer.",
                                    "reason": "Selection and held-out tasks require the word improved.",
                                }
                            ]
                        }
                    )
                return "improved answer" if "Always include improved" in system else "plain answer"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "task_id": f"live-{idx:02d}",
                    "task": f"Live task {idx}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "improved"}]},
                }
                for idx in range(15)
            ]
            (skill_dir / "skillopt-benchmark.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            held_rows = [
                {
                    "task_id": f"held-{idx:02d}",
                    "task": f"Held out task {idx}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "improved"}]},
                }
                for idx in range(5)
            ]
            held_out = root / "held-out.jsonl"
            held_out.write_text("\n".join(json.dumps(row) for row in held_rows) + "\n", encoding="utf-8")
            original_write_text = Path.write_text

            def failing_write_text(path: Path, data: str, *args: object, **kwargs: object) -> int:
                if path == skill_dir / "SKILL.md" and "Always include improved" in data:
                    raise OSError("simulated mutation failure")
                return original_write_text(path, data, *args, **kwargs)

            Path.write_text = failing_write_text  # type: ignore[method-assign]
            try:
                with self.assertRaisesRegex(OSError, "simulated mutation failure"):
                    self.live.run_live_skillopt(
                        root=root,
                        skill_name="demo",
                        models=self.live.LiveModels(target="target", optimizer="optimizer"),
                        chat_client=FakeChatClient(),
                        split_ratio=(1, 1, 1),
                        bootstrap_reviewed=True,
                        no_mutate=False,
                        held_out_path=held_out,
                        epochs=1,
                        batch_size=5,
                    )
            finally:
                Path.write_text = original_write_text  # type: ignore[method-assign]
            self.assertFalse((skill_dir / "skillopt" / "best.md").exists())
            self.assertFalse((skill_dir / "skillopt" / "history.json").exists())
            checkpoint = json.loads((skill_dir / "skillopt" / "live-checkpoint.json").read_text(encoding="utf-8"))
            self.assertEqual(checkpoint["state"], "mutation_failed")

    def test_live_runner_rejected_buffer_guides_next_epoch(self) -> None:
        class FakeChatClient:
            def __init__(self) -> None:
                self.optimizer_prompts: list[dict[str, object]] = []

            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                if model == "optimizer":
                    payload = json.loads(user)
                    self.optimizer_prompts.append(payload)
                    content = "Always include weak in the answer."
                    if payload.get("rejected_edits"):
                        content = "Always include improved in the answer."
                    return json.dumps(
                        {
                            "edits": [
                                {
                                    "op": "add",
                                    "anchor": "Workflow",
                                    "content": content,
                                    "reason": "Use the rejected buffer to avoid repeating failed edits.",
                                }
                            ]
                        }
                    )
                return "improved answer" if "Always include improved" in system else "plain answer"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "task_id": f"live-{idx:02d}",
                    "task": f"Live task {idx}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "improved"}]},
                }
                for idx in range(15)
            ]
            (skill_dir / "skillopt-benchmark.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            client = FakeChatClient()
            result = self.live.run_live_skillopt(
                root=root,
                skill_name="demo",
                models=self.live.LiveModels(target="target", optimizer="optimizer"),
                chat_client=client,
                split_ratio=(1, 1, 1),
                bootstrap_reviewed=True,
                epochs=2,
                batch_size=5,
            )
            self.assertEqual(result["outcome"], "accepted")
            self.assertGreaterEqual(len(client.optimizer_prompts), 2)
            self.assertFalse(client.optimizer_prompts[0].get("rejected_edits"))
            self.assertTrue(client.optimizer_prompts[1].get("rejected_edits"))
            self.assertTrue(any(row["event"] == "rejected_candidate" for row in result["trace"]))

    def test_live_runner_salvages_task_local_signals_from_rejected_candidate(self) -> None:
        class FakeChatClient:
            def __init__(self) -> None:
                self.optimizer_prompts: list[dict[str, object]] = []

            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                if model == "optimizer":
                    payload = json.loads(user)
                    self.optimizer_prompts.append(payload)
                    content = "Prefer alpha and avoid stable."
                    if payload.get("rejected_edits"):
                        return json.dumps({"edits": []})
                    return json.dumps(
                        {
                            "edits": [
                                {
                                    "op": "add",
                                    "anchor": "Workflow",
                                    "content": content,
                                    "reason": "Try to improve alpha-specific tasks.",
                                }
                            ]
                        }
                    )
                task_id = str(user).splitlines()[0].replace("Live task ", "").strip()
                if "Prefer alpha" in system:
                    return "alpha" if task_id == "06" else "missing"
                return "stable" if task_id != "06" else "missing"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "task_id": f"live-{idx:02d}",
                    "task": f"Live task {idx:02d}",
                    "judge": {
                        "kind": "rule",
                        "checks": [{"op": "contains", "arg": "alpha" if idx == 6 else "stable"}],
                    },
                }
                for idx in range(15)
            ]
            (skill_dir / "skillopt-benchmark.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            client = FakeChatClient()
            result = self.live.run_live_skillopt(
                root=root,
                skill_name="demo",
                models=self.live.LiveModels(target="target", optimizer="optimizer"),
                chat_client=client,
                split_ratio=(1, 1, 1),
                bootstrap_reviewed=True,
                epochs=2,
                batch_size=5,
            )
            self.assertEqual(result["outcome"], "no_improvement")
            self.assertEqual(result["reason"], "no_edits_applied")
            self.assertFalse((skill_dir / "proposed.md").exists())
            self.assertFalse((skill_dir / "skillopt" / "best.md").exists())
            rejected_payload = client.optimizer_prompts[1]["rejected_edits"]  # type: ignore[index]
            self.assertTrue(rejected_payload)
            salvage = rejected_payload[0]["task_signal"]  # type: ignore[index]
            self.assertEqual(salvage["improved"][0], {"task_id": "live-06", "before": 0.0, "after": 1.0})
            self.assertEqual(salvage["regressed"][0], {"task_id": "live-05", "before": 1.0, "after": 0.0})
            self.assertEqual(salvage["unchanged"], [])

            rejected_path = skill_dir / "skillopt" / "rejected.json"
            rejected = json.loads(rejected_path.read_text(encoding="utf-8"))
            persisted_signal = rejected[-1]["edits"][0]["task_signal"]
            self.assertEqual(persisted_signal["improved"][0]["task_id"], "live-06")
            self.assertEqual(persisted_signal["regressed"][0]["task_id"], "live-05")
            receipt_path = next(Path(path) for path in result["files_written"] if path.endswith(".receipt.json"))
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt_signal = receipt["rejected_edits"][0]["task_signal"]
            self.assertEqual(receipt_signal["improved"][0]["task_id"], "live-06")
            self.assertEqual(receipt_signal["regressed"][0]["task_id"], "live-05")

    def test_task_signal_classifies_unchanged_and_missing_gate_details(self) -> None:
        baseline = {
            "per_task_medians": [
                {"task_id": "same", "median": 0.5},
                {"task_id": "better", "median": 0.0},
                {"task_id": "worse", "median": 1.0},
            ]
        }
        candidate = {
            "per_task_medians": [
                {"task_id": "same", "median": 0.5},
                {"task_id": "better", "median": 1.0},
                {"task_id": "worse", "median": 0.0},
            ]
        }
        self.assertEqual(
            self.live._task_signal(baseline, candidate),
            {
                "improved": [{"task_id": "better", "before": 0.0, "after": 1.0}],
                "regressed": [{"task_id": "worse", "before": 1.0, "after": 0.0}],
                "unchanged": [{"task_id": "same", "before": 0.5, "after": 0.5}],
            },
        )
        self.assertEqual(
            self.live._task_signal({"per_task_medians": "bad"}, candidate),
            {"improved": [], "regressed": [], "unchanged": []},
        )

    def test_live_runner_enforces_llm_call_budget(self) -> None:
        class FakeChatClient:
            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                return "plain answer"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "task_id": f"live-{idx:02d}",
                    "task": f"Live task {idx}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "improved"}]},
                }
                for idx in range(15)
            ]
            (skill_dir / "skillopt-benchmark.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "LLM call budget"):
                self.live.run_live_skillopt(
                    root=root,
                    skill_name="demo",
                    models=self.live.LiveModels(target="target", optimizer="optimizer"),
                    chat_client=FakeChatClient(),
                    split_ratio=(1, 1, 1),
                    bootstrap_reviewed=True,
                    max_llm_calls=2,
                )

    def test_live_runner_rejects_duplicate_active_run_lock(self) -> None:
        class FakeChatClient:
            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                return "plain answer"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            opt_dir = skill_dir / "skillopt"
            opt_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "task_id": f"live-{idx:02d}",
                    "task": f"Live task {idx}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "improved"}]},
                }
                for idx in range(15)
            ]
            (skill_dir / "skillopt-benchmark.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            (opt_dir / ".skillopt-live.lock").write_text("active\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "active live SkillOpt run"):
                self.live.run_live_skillopt(
                    root=root,
                    skill_name="demo",
                    models=self.live.LiveModels(target="target", optimizer="optimizer"),
                    chat_client=FakeChatClient(),
                    split_ratio=(1, 1, 1),
                    bootstrap_reviewed=True,
                )

    def test_live_runner_executes_generated_benchmark_with_fake_client(self) -> None:
        class FakeChatClient:
            def __init__(self, rows: list[dict[str, object]]) -> None:
                self.rows = rows

            def chat(self, *, model: str, system: str, user: str, max_tokens: int) -> str:
                if model == "optimizer":
                    return json.dumps(
                        {
                            "edits": [
                                {
                                    "op": "add",
                                    "anchor": "Workflow",
                                    "content": "Always include SkillOpt benchmark phrases for the current TDD scenario.",
                                    "reason": "The benchmark requires explicit TDD evidence terms.",
                                }
                            ]
                        }
                    )
                if "Always include SkillOpt benchmark phrases" not in system:
                    return "plain answer"
                row = next(item for item in self.rows if str(user).startswith(str(item["task"])) or str(item["task"]) in user)
                checks = row["judge"]["checks"]  # type: ignore[index]
                lines = []
                for check in checks:  # type: ignore[union-attr]
                    if check["op"] == "mapping_contains":
                        for item in check["arg"]["items"]:
                            lines.append(f"- {item['key']}: {item['value']}")
                    else:
                        lines.append(str(check["arg"]))
                return "\n".join(lines)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copied = root / ".codex" / "skills" / "tdd-workflow"
            copied.parent.mkdir(parents=True)
            shutil.copytree(ROOT / ".codex" / "skills" / "tdd-workflow", copied)
            rows = write_demo_benchmark(copied / "skillopt-benchmark.jsonl", count=15, mapping=True)
            result = self.live.run_live_skillopt(
                root=root,
                skill_name="tdd-workflow",
                models=self.live.LiveModels(target="target", optimizer="optimizer"),
                chat_client=FakeChatClient(rows),
                split_ratio=(1, 1, 1),
                bootstrap_reviewed=True,
                epochs=1,
                batch_size=9,
            )
            self.assertEqual(result["outcome"], "accepted")
            self.assertEqual(result["baseline_sel_score"], 0.0)
            self.assertEqual(result["best_sel_score"], 1.0)
            self.assertEqual(result["test_score"], 1.0)
            self.assertFalse(result["mutated_skill_file"])
            self.assertTrue((copied / "proposed.md").is_file())

    def test_live_runner_uses_default_models_when_env_and_flags_are_absent(self) -> None:
        captured: dict[str, object] = {}

        class FakeModels:
            def __init__(self, *, target: str, optimizer: str, judge: str | None = None) -> None:
                captured["models"] = {"target": target, "optimizer": optimizer, "judge": judge}

        class FakeClient:
            def __init__(self, *, gemini_model: str | None = None) -> None:
                captured["gemini_model"] = gemini_model

        class FakeLive:
            LiveModels = FakeModels
            CliChatClient = FakeClient

            @staticmethod
            def run_live_skillopt(**kwargs: object) -> dict[str, object]:
                captured["kwargs"] = kwargs
                return {"outcome": "accepted"}

        old_loader = self.runner._load_live_module
        saved_env = {
            key: os.environ.pop(key, None)
            for key in (
                "SKILLOPT_TARGET_MODEL",
                "SKILLOPT_OPTIMIZER_MODEL",
                "SKILLOPT_JUDGE_MODEL",
                "SKILLOPT_GEMINI_MODEL",
            )
        }
        try:
            self.runner._load_live_module = lambda: FakeLive
            self.assertEqual(
                self.runner.main(["demo", "--root", "/tmp/skillopt-defaults", "--bootstrap-reviewed", "--live"]),
                0,
            )
        finally:
            self.runner._load_live_module = old_loader
            for key, value in saved_env.items():
                if value is not None:
                    os.environ[key] = value

        self.assertEqual(
            captured["models"],
            {
                "target": "gpt-5.3-codex-spark",
                "optimizer": "gpt-5.5",
                "judge": "gpt-5.3-codex-spark",
            },
        )
        self.assertEqual(captured["gemini_model"], "gemini-2.5-pro")

    def test_cli_chat_client_falls_back_to_gemini(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex = root / "codex"
            gemini = root / "gemini"
            codex.write_text("#!/usr/bin/env bash\nexit 42\n", encoding="utf-8")
            gemini.write_text("#!/usr/bin/env bash\necho gemini-fallback\n", encoding="utf-8")
            codex.chmod(0o755)
            gemini.chmod(0o755)
            client = self.live.CliChatClient(
                codex_bin=str(codex),
                gemini_bin=str(gemini),
                gemini_model="gemini-test",
                timeout=5,
            )
            self.assertEqual(
                client.chat(model="codex-test", system="system", user="user", max_tokens=10),
                "gemini-fallback",
            )

    def test_cli_chat_client_uses_supported_codex_exec_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex = root / "codex"
            argv_log = root / "argv.json"
            codex.write_text(
                "#!/usr/bin/env python3\n"
                "import json, pathlib, sys\n"
                f"pathlib.Path({str(argv_log)!r}).write_text(json.dumps(sys.argv), encoding='utf-8')\n"
                "out = pathlib.Path(sys.argv[sys.argv.index('--output-last-message') + 1])\n"
                "out.write_text('codex-ok', encoding='utf-8')\n"
                "print(json.dumps({'type':'tool_call','name':'web.open','failed':False}))\n",
                encoding="utf-8",
            )
            codex.chmod(0o755)
            client = self.live.CliChatClient(
                codex_bin=str(codex),
                gemini_bin=None,
                timeout=5,
            )
            self.assertEqual(
                client.chat(model="codex-test", system="system", user="user", max_tokens=10),
                "codex-ok",
            )
            argv = json.loads(argv_log.read_text(encoding="utf-8"))
            self.assertNotIn("--ask-for-approval", argv)
            self.assertIn("--json", argv)
            self.assertIn("--ignore-user-config", argv)
            self.assertEqual(client.last_tool_calls, [{"name": "web.open", "failed": False}])

    def test_cli_chat_client_optimizer_json_uses_json_artifact_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex = root / "codex"
            argv_log = root / "argv.json"
            prompt_log = root / "prompt.txt"
            codex.write_text(
                "#!/usr/bin/env python3\n"
                "import json, pathlib, sys\n"
                f"pathlib.Path({str(argv_log)!r}).write_text(json.dumps(sys.argv), encoding='utf-8')\n"
                "prompt = sys.stdin.read()\n"
                f"pathlib.Path({str(prompt_log)!r}).write_text(prompt, encoding='utf-8')\n"
                "out = pathlib.Path(sys.argv[sys.argv.index('--output-last-message') + 1])\n"
                "out.write_text(json.dumps({'edits': []}), encoding='utf-8')\n",
                encoding="utf-8",
            )
            codex.chmod(0o755)
            client = self.live.CliChatClient(
                codex_bin=str(codex),
                gemini_bin=None,
                timeout=5,
            )
            result = client.chat_json_object(
                model="optimizer",
                system="You are SkillOpt's optimizer.",
                user="{}",
                max_tokens=10,
                schema={"type": "object"},
                filename="optimizer-edits.json",
            )
            self.assertEqual(result, {"edits": []})
            argv = json.loads(argv_log.read_text(encoding="utf-8"))
            out_path = Path(argv[argv.index("--output-last-message") + 1])
            self.assertEqual(out_path.name, "optimizer-edits.json")
            self.assertIn("optimizer-edits.json", prompt_log.read_text(encoding="utf-8"))

    def test_cli_chat_client_gemini_fallback_uses_prompt_flag_and_clears_tool_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex = root / "codex"
            gemini = root / "gemini"
            gemini_argv = root / "gemini-argv.json"
            codex.write_text(
                "#!/usr/bin/env python3\n"
                "import json, pathlib, sys\n"
                "if pathlib.Path(sys.argv[0]).with_name('codex-once').exists():\n"
                "    print('codex failed', file=sys.stderr)\n"
                "    raise SystemExit(42)\n"
                "pathlib.Path(sys.argv[0]).with_name('codex-once').write_text('1', encoding='utf-8')\n"
                "out = pathlib.Path(sys.argv[sys.argv.index('--output-last-message') + 1])\n"
                "out.write_text('codex-ok', encoding='utf-8')\n"
                "print(json.dumps({'type':'tool_call','name':'web.open','failed':False}))\n",
                encoding="utf-8",
            )
            gemini.write_text(
                "#!/usr/bin/env python3\n"
                "import json, pathlib, sys\n"
                f"pathlib.Path({str(gemini_argv)!r}).write_text(json.dumps(sys.argv), encoding='utf-8')\n"
                "print('gemini-ok')\n",
                encoding="utf-8",
            )
            codex.chmod(0o755)
            gemini.chmod(0o755)
            client = self.live.CliChatClient(
                codex_bin=str(codex),
                gemini_bin=str(gemini),
                gemini_model="gemini-test",
                timeout=5,
            )
            self.assertEqual(client.chat(model="codex-test", system="system", user="user", max_tokens=10), "codex-ok")
            self.assertEqual(client.last_tool_calls, [{"name": "web.open", "failed": False}])
            self.assertEqual(client.chat(model="codex-test", system="system", user="user", max_tokens=10), "gemini-ok")
            argv = json.loads(gemini_argv.read_text(encoding="utf-8"))
            self.assertIn("--prompt", argv)
            self.assertEqual(client.last_tool_calls, [])

    def test_live_json_contract_parser_rejects_prose_wrapped_optimizer_output(self) -> None:
        with self.assertRaisesRegex(json.JSONDecodeError, "Expecting value"):
            self.live._parse_optimizer_response('Here is the JSON: {"edits": []}')
        self.assertEqual(
            self.live._parse_optimizer_response('```json\n{"edits": []}\n```'),
            [],
        )

    def test_codex_json_events_can_supply_tool_calls_to_rule_judges(self) -> None:
        stdout = "\n".join(
            [
                json.dumps({"type": "message", "text": "start"}),
                json.dumps({"type": "tool_call", "name": "web.open", "failed": False}),
            ]
        )
        calls = self.live._extract_codex_tool_calls(stdout)
        self.assertEqual(calls, [{"name": "web.open", "failed": False}])

    def test_runner_rejects_frontmatter_mutation_before_writing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            self.runner.bootstrap_from_skill(root, "demo", task_count=15)
            benchmark = skill_dir / "skillopt-benchmark.jsonl"
            benchmark.write_text(
                benchmark.read_text(encoding="utf-8").replace(self.skillopt.BOOTSTRAP_PENDING_REVIEW, ""),
                encoding="utf-8",
            )
            candidate = root / "candidate.md"
            candidate.write_text(
                "---\nname: renamed\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            rollouts = root / "rollouts.json"
            split = self.skillopt.split_benchmark(
                self.skillopt.load_benchmark(benchmark, bootstrap_reviewed=True),
                (1, 1, 1),
            )
            rollouts.write_text(
                json.dumps({row["task_id"]: ["task answer next step"] * 3 for row in split.sel}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "frontmatter"):
                self.runner.run_with_candidate(
                    root,
                    "demo",
                    candidate_path=candidate,
                    rollouts_path=rollouts,
                    split_ratio=(1, 1, 1),
                    bootstrap_reviewed=True,
                    no_mutate=False,
                )
            self.assertFalse((skill_dir / "proposed.md").exists())
            self.assertFalse((skill_dir / "skillopt").exists())
            self.assertIn("name: demo", skill_file.read_text(encoding="utf-8"))

    def test_runner_mutation_requires_held_out_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            self.runner.bootstrap_from_skill(root, "demo", task_count=15)
            benchmark = skill_dir / "skillopt-benchmark.jsonl"
            benchmark.write_text(
                benchmark.read_text(encoding="utf-8").replace(self.skillopt.BOOTSTRAP_PENDING_REVIEW, ""),
                encoding="utf-8",
            )
            candidate = root / "candidate.md"
            candidate.write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n\n## SkillOpt Criteria\n\nInclude task, answer, and next step.\n",
                encoding="utf-8",
            )
            split = self.skillopt.split_benchmark(
                self.skillopt.load_benchmark(benchmark, bootstrap_reviewed=True),
                (1, 1, 1),
            )
            rollouts = root / "rollouts.json"
            rollouts.write_text(
                json.dumps({row["task_id"]: ["task answer next step"] * 3 for row in split.sel}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "--mutate requires"):
                self.runner.run_with_candidate(
                    root,
                    "demo",
                    candidate_path=candidate,
                    rollouts_path=rollouts,
                    split_ratio=(1, 1, 1),
                    bootstrap_reviewed=True,
                    no_mutate=False,
                )
            self.assertFalse((skill_dir / "skillopt").exists())

    def test_runner_held_out_gate_rejects_overlap_and_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n",
                encoding="utf-8",
            )
            self.runner.bootstrap_from_skill(root, "demo", task_count=15)
            benchmark = skill_dir / "skillopt-benchmark.jsonl"
            benchmark.write_text(
                benchmark.read_text(encoding="utf-8").replace(self.skillopt.BOOTSTRAP_PENDING_REVIEW, ""),
                encoding="utf-8",
            )
            candidate = root / "candidate.md"
            candidate.write_text(
                "---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n\n## Workflow\n\n1. Answer plainly.\n\n## SkillOpt Criteria\n\nInclude task, answer, and next step.\n",
                encoding="utf-8",
            )
            split = self.skillopt.split_benchmark(
                self.skillopt.load_benchmark(benchmark, bootstrap_reviewed=True),
                (1, 1, 1),
            )
            sel_rollouts = root / "sel-rollouts.json"
            sel_rollouts.write_text(
                json.dumps({row["task_id"]: ["task answer next step"] * 3 for row in split.sel}),
                encoding="utf-8",
            )
            overlap = root / "held-out-overlap.jsonl"
            overlap.write_text(json.dumps(split.train[0]) + "\n", encoding="utf-8")
            held_out_rollouts = root / "held-out-rollouts.json"
            held_out_rollouts.write_text(json.dumps({split.train[0]["task_id"]: ["task answer next step"] * 3}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Held-out set shares"):
                self.runner.run_with_candidate(
                    root,
                    "demo",
                    candidate_path=candidate,
                    rollouts_path=sel_rollouts,
                    split_ratio=(1, 1, 1),
                    bootstrap_reviewed=True,
                    held_out_path=overlap,
                    held_out_rollouts_path=held_out_rollouts,
                    baseline_score=0.0,
                )

            held_out = root / "held-out.jsonl"
            held_rows = [
                {
                    "task_id": f"held-{index}",
                    "task": f"Held out {index}",
                    "judge": {"kind": "rule", "checks": [{"op": "contains", "arg": "must-pass"}]},
                }
                for index in range(5)
            ]
            held_out.write_text("\n".join(json.dumps(row) for row in held_rows) + "\n", encoding="utf-8")
            held_out_rollouts.write_text(
                json.dumps({row["task_id"]: ["missing"] * 3 for row in held_rows}),
                encoding="utf-8",
            )
            result = self.runner.run_with_candidate(
                root,
                "demo",
                candidate_path=candidate,
                rollouts_path=sel_rollouts,
                split_ratio=(1, 1, 1),
                bootstrap_reviewed=True,
                held_out_path=held_out,
                held_out_rollouts_path=held_out_rollouts,
                baseline_score=0.0,
            )
            self.assertEqual(result["outcome"], "no_improvement")
            self.assertEqual(result["reason"], "held_out_regression")
            self.assertTrue((skill_dir / "skillopt" / "rejected.json").is_file())


class SkillpackScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.check = load_module(".codex/skills/skillpack-check/scripts/skillpack_check.py")
        cls.harvest = load_module(".codex/skills/skillpack-harvest/scripts/skillpack_harvest.py")

    def test_skillpack_check_reports_missing_skill_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / ".codex" / "skills" / "thin" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: thin\ndescription: Thin.\n---\n# Thin\n", encoding="utf-8")
            report = self.check.check_skillpack(root)
            self.assertFalse(report["healthy"])
            self.assertEqual(report["skills_checked"], 1)
            self.assertTrue(report["actions"])

    def test_harvest_dry_run_rejects_private_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as source_tmp, tempfile.TemporaryDirectory() as dest_tmp:
            source = Path(source_tmp)
            host_skill = source / ".codex" / "skills" / "demo" / "SKILL.md"
            host_skill.parent.mkdir(parents=True)
            host_skill.write_text(
                "---\nname: demo\ndescription: Demo.\n---\n# Demo\nContact jane@example.com\n",
                encoding="utf-8",
            )
            result = self.harvest.harvest_skill(
                source,
                Path(dest_tmp),
                "demo",
                dry_run=True,
                lint=True,
            )
        self.assertEqual(result["status"], "lint_failed")
        self.assertFalse((Path(dest_tmp) / ".codex" / "skills" / "demo").exists())

    def test_harvest_dry_run_excludes_python_cache_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as source_tmp, tempfile.TemporaryDirectory() as dest_tmp:
            source = Path(source_tmp)
            skill_dir = source / ".codex" / "skills" / "demo"
            cache_dir = skill_dir / "scripts" / "__pycache__"
            cache_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo.\n---\n# Demo\n\n## Workflow\n\n1. Do it.\n\n## Anti-Patterns\n\n- Skip it.\n",
                encoding="utf-8",
            )
            (skill_dir / "scripts" / "helper.py").write_text("print('ok')\n", encoding="utf-8")
            (cache_dir / "helper.cpython-312.pyc").write_bytes(b"cache")
            result = self.harvest.harvest_skill(
                source,
                Path(dest_tmp),
                "demo",
                dry_run=True,
                lint=True,
            )
        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(result["files"], [".codex/skills/demo/SKILL.md", ".codex/skills/demo/scripts/helper.py"])


class SkillCreatorScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.init_skill = load_module(".codex/skills/skill-creator/scripts/init_skill.py")
        cls.quick_validate = load_module(".codex/skills/skill-creator/scripts/quick_validate.py")
        cls.package_skill = load_module(".codex/skills/skill-creator/scripts/package_skill.py")

    def test_init_skill_normalizes_and_writes_codex_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            created = self.init_skill.init_skill(root, "My Useful Skill", "Does one useful thing.")
            self.assertEqual(created.name, "SKILL.md")
            text = created.read_text(encoding="utf-8")
            self.assertIn("name: my-useful-skill", text)
            self.assertIn("## Workflow", text)
            report = self.quick_validate.validate_skill_file(created)
            self.assertTrue(report["ok"], report)

    def test_package_skill_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo.\n---\n# Demo\n\n## Workflow\n\n1. Do it.\n\n## Anti-Patterns\n\n- Skip it.\n",
                encoding="utf-8",
            )
            (skill_dir / "bad-link").symlink_to(skill_dir / "SKILL.md")
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.package_skill.collect_package_files(skill_dir)

    def test_package_skill_excludes_python_cache_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / ".codex" / "skills" / "demo"
            cache_dir = skill_dir / "scripts" / "__pycache__"
            cache_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo.\n---\n# Demo\n\n## Workflow\n\n1. Do it.\n\n## Anti-Patterns\n\n- Skip it.\n",
                encoding="utf-8",
            )
            (skill_dir / "scripts" / "helper.py").write_text("print('ok')\n", encoding="utf-8")
            (cache_dir / "helper.cpython-312.pyc").write_bytes(b"cache")
            files = self.package_skill.package_manifest(skill_dir)["files"]
            self.assertEqual(files, ["SKILL.md", "scripts/helper.py"])


class PlanEngReviewSkillificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")

    def test_plan_eng_review_has_skillified_contract_sections(self) -> None:
        text = read(".codex/skills/plan-eng-review/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "plan-eng-review")
        self.assertTrue(frontmatter.get("description"))
        for section in ["## Contract", "## Workflow", "## Output Format", "## Anti-Patterns"]:
            self.assertIn(section, text)
        for required in [
            "direct source of truth",
            "scope and reuse",
            "Executable Contract Compatibility Gate",
            "proof obligations",
            "Companion reviewer",
            "scenario-brake",
            "`GO`",
            "`GO WITH CHANGES`",
            "`STOP`",
        ]:
            self.assertIn(required, text)

    def test_plan_eng_review_template_copy_stays_aligned(self) -> None:
        root_skill = read(".codex/skills/plan-eng-review/SKILL.md")
        template_skill = read(".codex/skills/project-bootstrap/templates/root/.codex/skills/plan-eng-review/SKILL.md")
        self.assertEqual(template_skill, root_skill)

    def test_plan_eng_review_skillopt_benchmark_artifacts_are_removed(self) -> None:
        benchmark_path, template_path = skillopt_benchmark_paths("plan-eng-review")
        self.assertFalse(benchmark_path.exists())
        self.assertFalse(template_path.exists())


class TddWorkflowSkillificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")

    def test_tdd_workflow_has_pragmatic_exception_contract(self) -> None:
        text = read(".codex/skills/tdd-workflow/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "tdd-workflow")
        self.assertTrue(frontmatter.get("description"))
        for section in ["## Workflow", "## Pragmatic Exception Path", "## Output Format", "## Anti-Patterns"]:
            self.assertIn(section, text)
        for required in [
            "failing-test-first",
            "UI polish",
            "documentation",
            "configuration",
            "verification scripts",
            "existing tests",
            "exception evidence",
            "Deterministic verification",
            "Empirical verification",
            "Probabilistic verification",
            "executable acceptance criteria",
        ]:
            self.assertIn(required, text)

    def test_tdd_workflow_template_copy_stays_aligned(self) -> None:
        root_skill = read(".codex/skills/tdd-workflow/SKILL.md")
        template_skill = read(".codex/skills/project-bootstrap/templates/root/.codex/skills/tdd-workflow/SKILL.md")
        self.assertEqual(template_skill, root_skill)

    def test_tdd_workflow_skillopt_benchmark_artifacts_are_removed(self) -> None:
        benchmark_path, template_path = skillopt_benchmark_paths("tdd-workflow")
        self.assertFalse(benchmark_path.exists())
        self.assertFalse(template_path.exists())


class PlanDesignReviewSkillificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")

    def test_plan_design_review_has_skillified_contract_sections(self) -> None:
        text = read(".codex/skills/plan-design-review/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "plan-design-review")
        self.assertTrue(frontmatter.get("description"))
        for section in ["## Contract", "## Workflow", "## Output Format", "## Anti-Patterns"]:
            self.assertIn(section, text)
        for required in [
            "Gate Output Contract",
            "progress.md",
            "decisions.md",
            "evidence.md",
            "chat-only",
            "structured",
            "design gate status",
        ]:
            self.assertIn(required, text)

    def test_plan_design_review_template_copy_stays_aligned(self) -> None:
        root_skill = read(".codex/skills/plan-design-review/SKILL.md")
        template_skill = read(".codex/skills/project-bootstrap/templates/root/.codex/skills/plan-design-review/SKILL.md")
        self.assertEqual(template_skill, root_skill)

    def test_plan_design_review_skillopt_benchmark_artifacts_are_removed(self) -> None:
        benchmark_path, template_path = skillopt_benchmark_paths("plan-design-review")
        self.assertFalse(benchmark_path.exists())
        self.assertFalse(template_path.exists())


class TechnicalDesignSkillificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")

    def test_technical_design_has_skillified_gate_contract_sections(self) -> None:
        text = read(".codex/skills/technical-design/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "technical-design")
        self.assertTrue(frontmatter.get("description"))
        for section in ["## Contract", "## Workflow", "## Gate State Contract", "## Output Format", "## Anti-Patterns"]:
            self.assertIn(section, text)
        for required in [
            "not_required",
            "completed",
            "progress.md",
            "decisions.md",
            "evidence.md",
            "technical-design.md",
            "architecture.md",
            "Requirement Impact",
            "stale_needs_recheck",
            "plan-eng-review",
            "Workflow",
            "Anti-Patterns",
        ]:
            self.assertIn(required, text)

    def test_technical_design_template_copy_stays_aligned(self) -> None:
        root_skill = read(".codex/skills/technical-design/SKILL.md")
        template_skill = read(".codex/skills/project-bootstrap/templates/root/.codex/skills/technical-design/SKILL.md")
        self.assertEqual(template_skill, root_skill)

    def test_technical_design_skillopt_benchmark_artifacts_are_removed(self) -> None:
        benchmark_path, template_path = skillopt_benchmark_paths("technical-design")
        self.assertFalse(benchmark_path.exists())
        self.assertFalse(template_path.exists())


class GoalRequirementOrchestratorSkillificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")

    def test_goal_requirement_orchestrator_has_skillified_contract_sections(self) -> None:
        text = read(".codex/skills/goal-requirement-orchestrator/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "goal-requirement-orchestrator")
        self.assertTrue(frontmatter.get("description"))
        for section in ["## Contract", "## Output", "## Workflow", "## Anti-Patterns"]:
            self.assertIn(section, text)
        for required in [
            "one requirement",
            "not direct implementation",
            "state files",
            "Worktree Execution Policy",
            "Delegated Subagent Lifecycle",
            "giant state machine",
        ]:
            self.assertIn(required, text)

    def test_goal_requirement_orchestrator_template_copy_stays_aligned(self) -> None:
        root_skill = read(".codex/skills/goal-requirement-orchestrator/SKILL.md")
        template_skill = read(
            ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/SKILL.md"
        )
        self.assertEqual(template_skill, root_skill)

    def test_goal_requirement_orchestrator_skillopt_benchmark_artifacts_are_removed(self) -> None:
        benchmark_path, template_path = skillopt_benchmark_paths("goal-requirement-orchestrator")
        self.assertFalse(benchmark_path.exists())
        self.assertFalse(template_path.exists())


class ResearchSkillificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")

    def test_research_has_skillified_contract_sections(self) -> None:
        text = read(".codex/skills/research/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "research")
        self.assertTrue(frontmatter.get("description"))
        for section in ["## Contract", "## Workflow", "## Gate State Contract", "## Output", "## Anti-Patterns"]:
            self.assertIn(section, text)
        for required in [
            "not_required",
            "Requirement Impact",
            "stale_needs_recheck",
            "Artifact existence alone is insufficient",
            "progress.md",
            "decisions.md",
            "evidence.md",
            "blocking unresolved count",
        ]:
            self.assertIn(required, text)

    def test_research_template_copy_stays_aligned(self) -> None:
        root_skill = read(".codex/skills/research/SKILL.md")
        template_skill = read(".codex/skills/project-bootstrap/templates/root/.codex/skills/research/SKILL.md")
        self.assertEqual(template_skill, root_skill)

    def test_research_skillopt_benchmark_artifacts_are_removed(self) -> None:
        benchmark_path, template_path = skillopt_benchmark_paths("research")
        self.assertFalse(benchmark_path.exists())
        self.assertFalse(template_path.exists())


class ScenarioBrakeSkillificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")

    def test_scenario_brake_has_skillified_contract_sections(self) -> None:
        text = read(".codex/skills/scenario-brake/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "scenario-brake")
        self.assertTrue(frontmatter.get("description"))
        for section in ["## Trigger", "## Core Posture", "## Workflow", "## Output Shape", "## Constraints"]:
            self.assertIn(section, text)
        for required in [
            "baseline scenario",
            "3-7",
            "truly same path",
            "[SCENARIOS SUFFICIENT]",
            "[SCENARIOS MISSING]",
            "[PLAN NEEDS REFRAME]",
            "Companion review synthesis",
        ]:
            self.assertIn(required, text)

    def test_scenario_brake_template_copy_stays_aligned(self) -> None:
        root_skill = read(".codex/skills/scenario-brake/SKILL.md")
        template_skill = read(".codex/skills/project-bootstrap/templates/root/.codex/skills/scenario-brake/SKILL.md")
        self.assertEqual(template_skill, root_skill)

    def test_scenario_brake_skillopt_benchmark_artifacts_are_removed(self) -> None:
        benchmark_path, template_path = skillopt_benchmark_paths("scenario-brake")
        self.assertFalse(benchmark_path.exists())
        self.assertFalse(template_path.exists())


class RequirementClarifierSkillificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")

    def test_requirement_clarifier_has_skillified_contract_sections_and_clear_routes(self) -> None:
        text = read(".codex/skills/requirement-clarifier/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "requirement-clarifier")
        self.assertTrue(frontmatter.get("description"))
        for section in ["## Contract", "## Workflow", "## Handoff Routing", "## Anti-Patterns"]:
            self.assertIn(section, text)
        for route in ["design-consultation", "technical-design", "plan-eng-review", "decision-brake", "scenario-brake", "grill-me"]:
            self.assertIn(route, text)
        for unclear_route in ["ralplan", "office-hours", "spec-creator"]:
            self.assertNotIn(unclear_route, text)

    def test_requirement_clarifier_template_copy_stays_aligned(self) -> None:
        root_skill = read(".codex/skills/requirement-clarifier/SKILL.md")
        template_skill = read(".codex/skills/project-bootstrap/templates/root/.codex/skills/requirement-clarifier/SKILL.md")
        self.assertEqual(template_skill, root_skill)

    def test_requirement_clarifier_skillopt_benchmark_artifacts_are_removed(self) -> None:
        benchmark_path, template_path = skillopt_benchmark_paths("requirement-clarifier")
        self.assertFalse(benchmark_path.exists())
        self.assertFalse(template_path.exists())


class ContextLoadingSkillificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skillopt = load_module(".codex/skills/skill-optimizer/scripts/skillopt_core.py")

    def test_context_loading_declares_lifecycle_parent_fallback(self) -> None:
        text = read(".codex/skills/context-loading/SKILL.md")
        frontmatter = parse_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "context-loading")
        self.assertTrue(frontmatter.get("description"))
        for section in ["## Contract", "## Workflow", "## Fallback Policy", "## Output Format", "## Anti-Patterns"]:
            self.assertIn(section, text)
        for required in [
            "context-loading",
            "parent_fallback",
            "residual context risk",
            "same required report fields",
            "`close_agent` cleanup",
            "must not block",
        ]:
            self.assertIn(required, text)
        self.assertNotIn(
            "stop, rerun context loading, or report a blocker",
            text,
        )

    def test_context_loading_template_copy_stays_aligned(self) -> None:
        root_skill = read(".codex/skills/context-loading/SKILL.md")
        template_skill = read(".codex/skills/project-bootstrap/templates/root/.codex/skills/context-loading/SKILL.md")
        self.assertEqual(template_skill, root_skill)

    def test_context_loading_skillopt_benchmark_artifacts_are_removed(self) -> None:
        benchmark_path, template_path = skillopt_benchmark_paths("context-loading")
        self.assertFalse(benchmark_path.exists())
        self.assertFalse(template_path.exists())


if __name__ == "__main__":
    unittest.main()
