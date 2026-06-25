#!/usr/bin/env python3
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

SKILLS = [
    "benchmark",
    "browse",
    "devex-review",
    "plan-devex-review",
    "plan-ux-review",
    "ux-review",
    "cso",
    "ios-sync",
    "ios-qa",
    "ios-fix",
    "ios-design-review",
    "ios-clean",
    "setup-browser-cookies",
    "make-pdf",
]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label} missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label} still contains {needle!r}")


def assert_skill_frontmatter() -> None:
    for skill in SKILLS:
        text = read(f".codex/skills/{skill}/SKILL.md")
        if not text.startswith("---\n"):
            raise AssertionError(f"{skill} missing frontmatter start")
        end = text.find("\n---\n", 4)
        if end == -1:
            raise AssertionError(f"{skill} missing frontmatter end")
        frontmatter = text[4:end]
        assert_contains(frontmatter, f"name: {skill}", skill)
        assert_contains(frontmatter, "description: ", skill)


def assert_references_exist() -> None:
    required = [
        ".codex/skills/cso/references/audit-phases.md",
        ".codex/skills/devex-review/references/review-sections.md",
        ".codex/skills/devex-review/references/dx-hall-of-fame.md",
        ".codex/skills/plan-devex-review/references/review-sections.md",
        ".codex/skills/plan-devex-review/references/dx-hall-of-fame.md",
        ".codex/skills/plan-ux-review/references/review-sections.md",
        ".codex/skills/ux-review/references/review-sections.md",
        ".codex/skills/ios-qa/references/tailscale-acl-example.md",
        ".codex/skills/ios-qa/templates/Bridges.swift.template",
        ".codex/skills/ios-qa/templates/DebugBridgeManager.swift.template",
        ".codex/skills/ios-qa/templates/DebugBridgeWiring.swift.template",
        ".codex/skills/ios-qa/templates/Package.swift.template",
        ".codex/skills/ios-qa/templates/StateServer.swift.template",
    ]
    for relative_path in required:
        if not (ROOT / relative_path).is_file():
            raise AssertionError(f"missing required skill asset: {relative_path}")


def assert_no_machine_specific_paths() -> None:
    for skill in SKILLS:
        skill_dir = ROOT / ".codex" / "skills" / skill
        for path in iter_installable_skill_files(skill_dir):
            text = path.read_text(encoding="utf-8")
            assert_not_contains(text, "/Users/", str(path))
            assert_not_contains(text, "Downloads/projects/gstack", str(path))
            assert_not_contains(text, ".claude/skills", str(path))
            assert_not_contains(text, "Claude Code (local)", str(path))
            assert_not_contains(text, "tag:claude", str(path))


def assert_skill_local_references_are_one_hop(skill: str) -> None:
    skill_dir = ROOT / ".codex" / "skills" / skill
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        if not target.startswith("./references/"):
            raise AssertionError(f"{skill} local reference {label!r} must be one-hop ./references path, got {target}")
        relative = Path(target.removeprefix("./"))
        if len(relative.parts) != 2:
            raise AssertionError(f"{skill} local reference {target} must not be deeper than one hop")
        if not (skill_dir / relative).is_file():
            raise AssertionError(f"{skill} local reference target does not exist: {target}")


def assert_recursive_forbidden_tokens(skill: str, forbidden: list[str]) -> None:
    skill_dir = ROOT / ".codex" / "skills" / skill
    for path in iter_installable_skill_files(skill_dir):
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            assert_not_contains(text, needle, str(path))


def iter_installable_skill_files(skill_dir: Path) -> list[Path]:
    files = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(skill_dir)
        if relative.parts and relative.parts[0] == "skillopt":
            continue
        if relative == Path("proposed.md"):
            continue
        files.append(path)
    return sorted(files)


def assert_cso_reference_is_codex_native() -> None:
    text = read(".codex/skills/cso/references/audit-phases.md")
    for forbidden in [
        "Claude Code skills",
        ".claude/skills",
        "AskUserQuestion",
        "Use Grep",
        "Grep tool",
    ]:
        assert_not_contains(text, forbidden, "cso audit phases")
    assert_contains(text, ".codex/skills", "cso audit phases")
    assert_contains(text, "ask the user in chat", "cso audit phases")
    assert_contains(text, "`rg`", "cso audit phases")


def assert_decision_skills_require_metric_approval() -> None:
    decision = read(".codex/skills/decision-brake/SKILL.md")
    lenses = read(".codex/skills/decision-brake/references/review-lenses.md")
    root_cause = read(".codex/skills/root-cause-solution/SKILL.md")
    template_decision = read(".codex/skills/project-bootstrap/templates/root/.codex/skills/decision-brake/SKILL.md")
    template_lenses = read(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/decision-brake/references/review-lenses.md"
    )

    if template_decision != decision:
        raise AssertionError("project-bootstrap decision-brake SKILL.md template drifted from runtime skill")
    if template_lenses != lenses:
        raise AssertionError("project-bootstrap decision-brake review-lenses.md template drifted from runtime skill")

    for label, text in [
        ("decision-brake", decision),
        ("decision-brake review lenses", lenses),
        ("root-cause-solution", root_cause),
    ]:
        for required in [
            "first-principles decision-quality metrics",
            "human approval",
            "[NEEDS METRIC APPROVAL]",
        ]:
            assert_contains(text, required, label)

    for label, text in [
        ("decision-brake", decision),
        ("root-cause-solution", root_cause),
    ]:
        assert_contains(text, "승인 후에는 승인된 metrics 를 기준으로만", label)
        assert_contains(text, "평가 중 metric 을 바꿔야 하면 다시 human approval", label)


def assert_devex_skills_preserve_gstack_review_shape() -> None:
    plan = read(".codex/skills/plan-devex-review/SKILL.md")
    live = read(".codex/skills/devex-review/SKILL.md")
    sections = read(".codex/skills/plan-devex-review/references/review-sections.md")
    hof = read(".codex/skills/plan-devex-review/references/dx-hall-of-fame.md")
    live_sections = read(".codex/skills/devex-review/references/review-sections.md")
    live_hof = read(".codex/skills/devex-review/references/dx-hall-of-fame.md")

    for required in [
        "Developer Persona",
        "Empathy Narrative",
        "Competitive Benchmark",
        "Magical Moment",
        "DX EXPANSION",
        "DX POLISH",
        "DX TRIAGE",
        "Implementation Tasks",
        "GO WITH CHANGES",
    ]:
        assert_contains(plan, required, "plan-devex-review")

    for required in [
        "Measure, do not guess",
        "TTHW",
        "Boomerang",
        "DX LIVE AUDIT - SCORECARD",
        "TESTED",
        "INFERRED",
    ]:
        assert_contains(live, required, "devex-review")

    for pass_number in range(1, 9):
        assert_contains(sections, f"## Pass {pass_number}:", "plan devex sections")
        assert_contains(hof, f"## Pass {pass_number}:", "dx hall of fame")
        assert_contains(live_sections, f"## Pass {pass_number}:", "live devex sections")
        assert_contains(live_hof, f"## Pass {pass_number}:", "live dx hall of fame")

    for forbidden in [
        ".claude/skills",
        "AskUserQuestion",
        "gstack-review-log",
        "gstack-config",
        "allowed-tools:",
        "preamble-tier",
    ]:
        assert_not_contains(plan, forbidden, "plan-devex-review")
        assert_not_contains(live, forbidden, "devex-review")
    for skill in ["plan-devex-review", "devex-review"]:
        assert_skill_local_references_are_one_hop(skill)
        assert_recursive_forbidden_tokens(
            skill,
            [
                ".claude/skills",
                "AskUserQuestion",
                "gstack-review-log",
                "gstack-config",
                "allowed-tools:",
                "preamble-tier",
            ],
        )


def assert_ux_skills_preserve_gstack_review_shape_without_design_overlap() -> None:
    plan = read(".codex/skills/plan-ux-review/SKILL.md")
    live = read(".codex/skills/ux-review/SKILL.md")
    plan_sections = read(".codex/skills/plan-ux-review/references/review-sections.md")
    live_sections = read(".codex/skills/ux-review/references/review-sections.md")

    for required in [
        "User Persona",
        "First-Value Target",
        "Empathy Narrative",
        "Scenario Set",
        "UX EXPANSION",
        "UX POLISH",
        "UX TRIAGE",
        "Implementation Tasks",
        "GO WITH CHANGES",
    ]:
        assert_contains(plan, required, "plan-ux-review")

    for required in [
        "Test like a user",
        "Task Flow",
        "Boomerang",
        "UX LIVE AUDIT - SCORECARD",
        "Gate Output",
        "gate_status",
        "completion_impact",
        "blocked_until_evidence",
        "TESTED",
        "INFERRED",
    ]:
        assert_contains(live, required, "ux-review")

    for pass_number in range(1, 9):
        assert_contains(plan_sections, f"## Pass {pass_number}:", "plan ux sections")
        assert_contains(live_sections, f"## Pass {pass_number}:", "live ux sections")

    for required in [
        "Use `plan-design-review`",
        "Use `design-review`",
        "task success",
        "Recovery And Re-entry",
        "Trust, Safety, And Clarity",
    ]:
        assert_contains(plan + live + plan_sections + live_sections, required, "ux review skills")

    for forbidden in [
        ".claude/skills",
        "AskUserQuestion",
        "gstack-review-log",
        "gstack-config",
        "allowed-tools:",
        "preamble-tier",
    ]:
        assert_not_contains(plan, forbidden, "plan-ux-review")
        assert_not_contains(live, forbidden, "ux-review")
    for skill in ["plan-ux-review", "ux-review"]:
        assert_skill_local_references_are_one_hop(skill)
        assert_recursive_forbidden_tokens(
            skill,
            [
                ".claude/skills",
                "AskUserQuestion",
                "gstack-review-log",
                "gstack-config",
                "allowed-tools:",
                "preamble-tier",
            ],
        )


def assert_ios_templates_compose() -> None:
    wiring = read(".codex/skills/ios-qa/templates/DebugBridgeWiring.swift.template")
    manager = read(".codex/skills/ios-qa/templates/DebugBridgeManager.swift.template")
    accessor = read(".codex/skills/ios-qa/templates/StateAccessor.swift.template")

    assert_contains(wiring, "import DebugBridgeCore", "DebugBridgeWiring")
    assert_contains(wiring, "import DebugBridgeUI", "DebugBridgeWiring")
    assert_contains(wiring, "DebugBridgeUIWiring.installAll()", "DebugBridgeWiring")
    for private_symbol in [
        "AccessibilityScanner",
        "SnapshotCapture",
        "MutationDispatcher",
        "start(appState: appState, recording:",
    ]:
        assert_not_contains(wiring, private_symbol, "DebugBridgeWiring")

    assert_contains(manager, "public func start()", "DebugBridgeManager")
    assert_not_contains(manager, "public func start(appState: AppState)", "DebugBridgeManager")
    assert_not_contains(manager, "AppStateAccessor", "DebugBridgeManager")
    assert_not_contains(manager, "public func start(appState: AppState, recording:", "DebugBridgeManager")

    assert_contains(wiring, "AppStateAccessor.register(appState)", "DebugBridgeWiring")
    assert_contains(wiring, "DebugBridgeManager.shared.start()", "DebugBridgeWiring")
    if wiring.index("AppStateAccessor.register(appState)") > wiring.index("DebugBridgeManager.shared.start()"):
        raise AssertionError("DebugBridgeWiring must register generated accessors before starting StateServer")

    assert_contains(accessor, "import DebugBridgeCore", "StateAccessor")
    assert_contains(accessor, "public enum AppStateAccessor", "StateAccessor")
    assert_contains(accessor, "public static func register(_ state: AppState)", "StateAccessor")
    assert_contains(accessor, "guard let state = state as? {{CLASS_NAME}} else { return }", "StateAccessor")
    assert_not_contains(accessor, "public enum {{CLASS_NAME}}Accessor", "StateAccessor")


def assert_ios_package_manifest_is_valid() -> None:
    package = read(".codex/skills/ios-qa/templates/Package.swift.template")
    first_line = package.splitlines()[0]
    if first_line != "// swift-tools-version:5.9":
        raise AssertionError("Package.swift.template must start with the Swift tools-version directive")

    swift = shutil.which("swift")
    if swift is None:
        return

    with tempfile.TemporaryDirectory(prefix="codex-ios-qa-template-") as tmp:
        package_root = Path(tmp)
        (package_root / "Package.swift").write_text(package, encoding="utf-8")
        for relative_dir in [
            "Sources/DebugBridgeCore",
            "Sources/DebugBridgeTouch/include",
            "Sources/DebugBridgeUI",
            "Tests/DebugBridgeCoreTests",
        ]:
            (package_root / relative_dir).mkdir(parents=True, exist_ok=True)
        (package_root / "Sources/DebugBridgeCore/Stub.swift").write_text("public enum Stub {}\n", encoding="utf-8")
        (package_root / "Sources/DebugBridgeTouch/Stub.m").write_text('#import "DebugBridgeTouch.h"\n', encoding="utf-8")
        (package_root / "Sources/DebugBridgeTouch/include/DebugBridgeTouch.h").write_text(
            "#import <Foundation/Foundation.h>\n", encoding="utf-8"
        )
        (package_root / "Sources/DebugBridgeUI/Stub.swift").write_text("public enum UIStub {}\n", encoding="utf-8")
        (package_root / "Tests/DebugBridgeCoreTests/StubTests.swift").write_text(
            "import Testing\n@Test func stub() {}\n", encoding="utf-8"
        )
        result = subprocess.run(
            [swift, "package", "dump-package"],
            cwd=package_root,
            env={**os.environ, "SWIFTPM_DISABLE_SANDBOX": "1"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        if result.returncode != 0:
            raise AssertionError(f"Package.swift.template is not a valid SwiftPM manifest:\n{result.stderr}")


def assert_ios_clean_uses_authoritative_release_evidence() -> None:
    text = read(".codex/skills/ios-clean/SKILL.md")
    assert_not_contains(text, '! rg "DebugBridge"', "ios-clean")
    assert_not_contains(text, '! rg "@Snapshotable"', "ios-clean")
    assert_contains(text, "discovery only", "ios-clean")
    assert_contains(text, "Package.swift", "ios-clean")
    assert_contains(text, "swift build -c release", "ios-clean")
    assert_contains(text, "nm -j", "ios-clean")


def assert_repo_verify_runs_this_contract() -> None:
    verify = read("scripts/verify")
    assert_contains(verify, '"$PYTHON" tests/verify_gstack_skill_contracts.py', "scripts/verify")


def main() -> None:
    assert_skill_frontmatter()
    assert_references_exist()
    assert_no_machine_specific_paths()
    assert_cso_reference_is_codex_native()
    assert_decision_skills_require_metric_approval()
    assert_devex_skills_preserve_gstack_review_shape()
    assert_ux_skills_preserve_gstack_review_shape_without_design_overlap()
    assert_ios_templates_compose()
    assert_ios_package_manifest_is_valid()
    assert_ios_clean_uses_authoritative_release_evidence()
    assert_repo_verify_runs_this_contract()


if __name__ == "__main__":
    main()
