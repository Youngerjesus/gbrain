#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]

GATE_ORDER = [
    "requirement-clarifier",
    "research",
    "technical-design",
    "plan-design-review",
    "plan-ux-review",
    "plan-devex-review",
    "plan-eng-review",
    "scenario-brake",
    "secondary-plan",
    "ux-review",
    "devex-review",
]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def read_toml(relative_path: str) -> dict:
    return tomllib.loads(read(relative_path))


def load_module(relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load module at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise AssertionError(f"missing section: {heading}")
    return match.group("body")


def inline_code_tokens(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def assert_subsequence(tokens: list[str], expected: list[str], label: str) -> None:
    cursor = 0
    for token in tokens:
        if cursor < len(expected) and token == expected[cursor]:
            cursor += 1
    if cursor != len(expected):
        raise AssertionError(
            f"{label} does not preserve gate order {expected}; observed tokens: {tokens}"
        )


def assert_section_mentions(path: str, heading: str, required: list[str]) -> None:
    body = section(read(path), heading)
    missing = [item for item in required if item not in body]
    if missing:
        raise AssertionError(f"{path} #{heading} missing {missing}")


def assert_agents_gate_order(path: str) -> None:
    body = section(read(path), "Execution Source Selection")
    gate_bullets = [
        line
        for line in body.splitlines()
        if line.startswith("- ")
        and "For each goal-requirements slice" in line
        and "conditional hard gates" in line
    ]
    if len(gate_bullets) != 1:
        raise AssertionError(f"{path} must declare exactly one goal gate order bullet")
    assert_subsequence(inline_code_tokens(gate_bullets[0]), GATE_ORDER, path)
    required_policy = [
        "plan-design-review",
        "UI-bearing",
        "before `plan-eng-review`",
        "visual-qa-hardening",
    ]
    missing = [item for item in required_policy if item not in body]
    if missing:
        raise AssertionError(f"{path} execution policy missing {missing}")
    forbidden = "UI-bearing work must also have passed or explicitly skipped"
    if forbidden in body:
        raise AssertionError(f"{path} weakens UI-bearing plan-design-review with skipped wording")
    production_required = [
        "production-readiness",
        "sequence-level",
        "before marking the goal sequence complete",
    ]
    missing = [item for item in production_required if item not in body]
    if missing:
        raise AssertionError(f"{path} execution policy missing production readiness {missing}")


def assert_orchestrator_contract(path: str) -> None:
    text = read(path)
    execution = section(text, "Execution Gates")
    assert_subsequence(inline_code_tokens(execution), GATE_ORDER, f"{path} execution gates")
    worktree = section(text, "Worktree Execution Policy")
    required_worktree_policy = [
        "scripts/init_worktree.sh",
        "If `scripts/init_worktree.sh` is missing",
        "create it before treating worktree setup as available",
        "idempotent",
        "accept the task worktree path as its first argument",
        "avoid writing external automation runtime state into the repo",
    ]
    missing = [item for item in required_worktree_policy if item not in worktree]
    if missing:
        raise AssertionError(f"{path} worktree setup policy missing {missing}")
    forbidden_worktree_policy = [
        "project_manager",
        "scheduler setup",
        "worktree_env_files",
    ]
    present = [item for item in forbidden_worktree_policy if item in worktree]
    if present:
        raise AssertionError(f"{path} worktree setup policy still delegates to {present}")
    required_bootstrap_policy = [
        "## Sequence Outcome",
        "outcome:",
        "create this requirements file only when this slice starts",
        "requirement-clarifier-post-draft-reviewer",
        "structured `reviewer_status`",
        "rerun or revalidate the post-draft reviewer gate",
    ]
    missing = [item for item in required_bootstrap_policy if item not in text]
    if missing:
        raise AssertionError(f"{path} missing sequence outcome or first requirement policy {missing}")
    assert_section_mentions(
        path,
        "Execution Gates",
        [
            "When all listed requirements are checked complete",
            "`production-readiness`",
            "sequence-level",
            "before marking the goal sequence complete",
        ],
    )
    assert_section_mentions(
        path,
        "Blocked Rules",
        [
            "plan-design-review",
            "UI-bearing",
            "before `plan-eng-review`",
            "production-readiness",
        ],
    )
    assert_section_mentions(
        path,
        "Completion Contract",
        [
            "plan-design-review",
            "plan-ux-review",
            "plan-devex-review",
            "ux-review",
            "devex-review",
            "visual-qa-hardening",
            "production-readiness",
            "ready",
        ],
    )
    assert_section_mentions(
        path,
        "Execution Gates",
        [
            "plans/<plan-id>/reviews/plan-design-review.md",
            "plans/<plan-id>/reviews/plan-ux-review.md",
            "plans/<plan-id>/reviews/plan-devex-review.md",
            "plans/<plan-id>/reviews/plan-eng-review.md",
            "plan-ux-review",
            "user-facing experience",
            "plan-devex-review",
            "developer-facing experience",
            "ux-review",
            "live user experience",
            "devex-review",
            "live developer experience",
        ],
    )
    assert_section_mentions(
        path,
        "State Update Rules",
        [
            "plans/<plan-id>/reviews/plan-design-review.md",
            "plans/<plan-id>/reviews/plan-ux-review.md",
            "plans/<plan-id>/reviews/plan-devex-review.md",
            "plans/<plan-id>/reviews/plan-eng-review.md",
            "plan-ux-review",
            "plan-devex-review",
            "ux-review",
            "devex-review",
        ],
    )
    assert_section_mentions(
        path,
        "Blocked Rules",
        [
            "plan-ux-review",
            "plan-devex-review",
            "ux-review",
            "devex-review",
        ],
    )
    assert_section_mentions(
        path,
        "Delegated Subagent Lifecycle",
        [
            "hard deadline",
            "timeout",
            "cancel_failed",
            "`close_agent`",
            "best-effort cleanup",
            "short timeout",
            "progress.md",
            "evidence.md",
            "must not wait without a bounded timeout",
        ],
    )


def assert_orchestrator_state_templates(
    progress_path: str,
    evidence_path: str,
    decisions_path: str,
) -> None:
    progress = read(progress_path)
    progress_required = [
        "## Delegated Subagent Lifecycle",
        "Companion wait status",
        "running | completed | partial | timeout | cancel_requested | cancel_failed | unavailable",
        "`close_agent` cleanup status",
        "short timeout",
        "Next action or blocker",
        "## Experience Review Gate State",
        "Review artifact path: plans/<plan-id>/reviews/plan-design-review.md | Missing | Not required",
        "Review artifact path: plans/<plan-id>/reviews/plan-ux-review.md | Missing | Not required",
        "Review artifact path: plans/<plan-id>/reviews/plan-devex-review.md | Missing | Not required",
        "### plan-eng-review",
        "Review artifact path: plans/<plan-id>/reviews/plan-eng-review.md | Missing",
        "plan-ux-review",
        "plan-devex-review",
        "ux-review",
        "devex-review",
    ]
    missing = [item for item in progress_required if item not in progress]
    if missing:
        raise AssertionError(f"{progress_path} missing delegated lifecycle fields {missing}")

    evidence = read(evidence_path)
    evidence_required = [
        "delegated subagent lifecycle evidence",
        "hard deadline",
        "timeout",
        "cancel_failed",
        "`close_agent`",
        "best-effort cleanup",
        "`close_agent` cleanup result: not_needed | completed | timeout | cancel_failed | cleanup_pending",
        "experience review evidence",
        "plans/<plan-id>/reviews/plan-design-review.md",
        "plans/<plan-id>/reviews/plan-ux-review.md",
        "plans/<plan-id>/reviews/plan-devex-review.md",
        "plans/<plan-id>/reviews/plan-eng-review.md",
        "plan-ux-review",
        "plan-devex-review",
        "ux-review",
        "devex-review",
    ]
    missing = [item for item in evidence_required if item not in evidence]
    if missing:
        raise AssertionError(f"{evidence_path} missing delegated lifecycle evidence {missing}")
    forbidden = [
        "chat-only review outcome",
        "plan-design-review outcome",
    ]
    present = [item for item in forbidden if item in progress or item in evidence]
    if present:
        raise AssertionError(f"{progress_path} or {evidence_path} weakens review artifact guidance with {present}")

    decisions = read(decisions_path)
    decisions_required = [
        "plans/<plan-id>/reviews/plan-design-review.md",
        "plans/<plan-id>/reviews/plan-ux-review.md",
        "plans/<plan-id>/reviews/plan-devex-review.md",
        "plans/<plan-id>/reviews/plan-eng-review.md",
        "conditional plan-stage reviews",
    ]
    missing = [item for item in decisions_required if item not in decisions]
    if missing:
        raise AssertionError(f"{decisions_path} missing review artifact decision guidance {missing}")


def assert_sequence_progress_template(path: str) -> None:
    progress = read(path)
    required = [
        "## Outcome Contract",
        "Sequence outcome",
        "First requirement path",
        "First requirement acceptance status",
        "Later requirement files deferred until reached: yes | no",
    ]
    missing = [item for item in required if item not in progress]
    if missing:
        raise AssertionError(f"{path} missing sequence outcome recovery fields {missing}")


def assert_subagent_lifecycle_policy_projection(path: str, lifecycle_module) -> None:
    projection = section(read(path), "Executable Subagent Lifecycle Policy")
    required = [
        "scripts/subagent_lifecycle.py",
        "fallback_policies()",
        "canonical",
        "operator-facing projection",
        "not semantic authority",
        "cleanup evidence only",
        "valid fallback artifact",
        "replacement result",
        "structured blocker",
        "escalation record",
    ]
    missing = [item for item in required if item not in projection]
    if missing:
        raise AssertionError(f"{path} lifecycle policy projection missing {missing}")
    for gate, policy in lifecycle_module.fallback_policies().items():
        expected = f"- `{gate}`: `{policy.action.value}`"
        if expected not in projection:
            raise AssertionError(f"{path} missing projected fallback policy {expected}")


def assert_mirrored_file_parity(source_path: str, mirror_path: str) -> None:
    source = read(source_path)
    mirror = read(mirror_path)
    if source != mirror:
        raise AssertionError(f"{mirror_path} must match {source_path}")


def assert_secondary_plan_reconciles_design_review(skill_path: str, template_path: str) -> None:
    skill = read(skill_path)
    required = [
        "plans/<plan-id>/reviews/plan-design-review.md",
        "plans/<plan-id>/reviews/plan-ux-review.md",
        "plans/<plan-id>/reviews/plan-devex-review.md",
        "plans/<plan-id>/reviews/plan-eng-review.md",
        "plan-design-review",
        "plan-ux-review",
        "plan-devex-review",
        "plan-eng-review",
        "scenario-brake",
    ]
    missing = [item for item in required if item not in skill]
    if missing:
        raise AssertionError(f"{skill_path} missing review reconciliation for {missing}")
    template = read(template_path)
    if "Plan design review" not in template:
        raise AssertionError(f"{template_path} must preserve plan design review notes")
    if "Plan UX review" not in template:
        raise AssertionError(f"{template_path} must preserve plan UX review notes")
    if "Plan DevEx review" not in template:
        raise AssertionError(f"{template_path} must preserve plan DevEx review notes")


def assert_orchestrator_rehydrates_experience_gates(path: str) -> None:
    blocked = section(read(path), "Blocked Rules")
    required_phrase = (
        "lacks the `research`, `technical-design`, UI-bearing `plan-design-review`, "
        "user-facing `plan-ux-review`, developer-facing `plan-devex-review`, "
        "live `ux-review`, or live `devex-review` gate text"
    )
    if required_phrase not in blocked:
        raise AssertionError(f"{path} older sequence rehydration rule must name all experience gates")


def assert_manifest_declares_orchestrator_scripts() -> None:
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    required = [
        ".codex/skills/goal-requirement-orchestrator/scripts/subagent_lifecycle.py",
    ]
    missing = [item for item in required if item not in manifest]
    if missing:
        raise AssertionError(f"project-bootstrap manifest missing orchestrator scripts {missing}")


def assert_bootstrap_installs_plan_design_review() -> None:
    expected_path = (
        ROOT
        / ".codex/skills/project-bootstrap/templates/root/.codex/skills/plan-design-review/SKILL.md"
    )
    if not expected_path.exists():
        raise AssertionError("project-bootstrap template must include plan-design-review skill")
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    bundle = read(".codex/skills/project-bootstrap/references/curated-bundle.md")
    for source, label in [(manifest, "manifest"), (bundle, "curated bundle")]:
        if "plan-design-review" not in source:
            raise AssertionError(f"project-bootstrap {label} must list plan-design-review")


def assert_bootstrap_installs_experience_review_skills() -> None:
    skills = ["plan-devex-review", "devex-review", "plan-ux-review", "ux-review"]
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    bundle = read(".codex/skills/project-bootstrap/references/curated-bundle.md")
    for skill in skills:
        expected_path = ROOT / ".codex/skills/project-bootstrap/templates/root/.codex/skills" / skill / "SKILL.md"
        if not expected_path.exists():
            raise AssertionError(f"project-bootstrap template must include {skill} skill")
        if skill not in bundle:
            raise AssertionError(f"project-bootstrap curated bundle must list {skill}")
        manifest_path = f".codex/skills/{skill}/SKILL.md"
        if manifest_path not in manifest:
            raise AssertionError(f"project-bootstrap manifest must list {manifest_path}")


def assert_experience_skill_template_parity() -> None:
    for skill in ["plan-devex-review", "devex-review", "plan-ux-review", "ux-review"]:
        source_dir = ROOT / ".codex/skills" / skill
        mirror_dir = ROOT / ".codex/skills/project-bootstrap/templates/root/.codex/skills" / skill
        source_files = _installable_skill_files(source_dir)
        mirror_files = _installable_skill_files(mirror_dir)
        if source_files != mirror_files:
            raise AssertionError(f"project-bootstrap {skill} files must match source files")
        for relative_path in source_files:
            assert_mirrored_file_parity(
                str(source_dir / relative_path),
                str(mirror_dir / relative_path),
            )


def _installable_skill_files(skill_dir: Path) -> list[Path]:
    files = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(skill_dir)
        if relative.parts and relative.parts[0] == "skillopt":
            continue
        if relative == Path("proposed.md"):
            continue
        files.append(relative)
    return sorted(files)


def assert_bootstrap_installs_production_readiness() -> None:
    expected_path = (
        ROOT
        / ".codex/skills/project-bootstrap/templates/root/.codex/skills/production-readiness/SKILL.md"
    )
    if not expected_path.exists():
        raise AssertionError("project-bootstrap template must include production-readiness skill")
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    bundle = read(".codex/skills/project-bootstrap/references/curated-bundle.md")
    for source, label in [(manifest, "manifest"), (bundle, "curated bundle")]:
        if "production-readiness" not in source:
            raise AssertionError(f"project-bootstrap {label} must list production-readiness")


def assert_production_readiness_skill(path: str) -> None:
    text = read(path)
    required = [
        "name: production-readiness",
        "MVP",
        "sequence-level",
        "implementation-brake",
        "closeout",
        "ready_with_external_handoff",
        "blocked_internal",
        "blocked_external",
        "deferred_non_goal",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"{path} missing production readiness contract {missing}")


def assert_agent_registration(config_path: str, agent_name: str) -> None:
    config = read_toml(config_path)
    agents = config.get("agents", {})
    if agent_name not in agents:
        raise AssertionError(f"{config_path} must register {agent_name}")
    expected_config = f"agents/{agent_name}.toml"
    actual_config = agents[agent_name].get("config_file")
    if actual_config != expected_config:
        raise AssertionError(
            f"{config_path} {agent_name} config_file must be {expected_config}, got {actual_config}"
        )
    agent_file = ROOT / Path(config_path).parent / expected_config
    if not agent_file.exists():
        raise AssertionError(f"{config_path} registered missing agent file {agent_file}")


def assert_agent_registration_unique(config_path: str, agent_name: str) -> None:
    text = read(config_path)
    header = f"[agents.{agent_name}]"
    count = text.count(header)
    if count != 1:
        raise AssertionError(f"{config_path} must contain exactly one {header}, got {count}")
    assert_agent_registration(config_path, agent_name)


def assert_bootstrap_metadata_unique(agent_name: str) -> None:
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    manifest_path = f".codex/agents/{agent_name}.toml"
    manifest_count = manifest.count(f"| `{manifest_path}` |")
    if manifest_count != 1:
        raise AssertionError(
            f"project-bootstrap manifest must list {manifest_path} exactly once, got {manifest_count}"
        )
    bundle = read(".codex/skills/project-bootstrap/references/curated-bundle.md")
    bundle_count = bundle.count(f"- `{agent_name}`")
    if bundle_count != 1:
        raise AssertionError(
            f"project-bootstrap curated bundle must list {agent_name} exactly once, got {bundle_count}"
        )


def assert_requirement_clarifier_quality_gate(path: str) -> None:
    text = read(path)
    required = [
        "## Requirement Quality Gate",
        "AC-to-verification mapping",
        "Evidence Reviewed",
        "session_provenance",
        "Decision Boundaries",
        "reviewer_status",
        "Risky but usable",
        "production-bound",
        "self-review fallback",
        "must not silently claim external reviewer approval",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"{path} missing requirement quality gate contract {missing}")
    finalization = section(text, "7. Finalization")
    front_matter_required = [
        "---",
        "requirement_id:",
        "session_provenance:",
        "readiness_status:",
        "reviewer_status:",
    ]
    missing = [item for item in front_matter_required if item not in finalization]
    if missing:
        raise AssertionError(f"{path} finalization template missing front matter {missing}")


def assert_post_draft_reviewer_contract(agent_path: str) -> None:
    agent = read_toml(agent_path)
    if agent.get("sandbox_mode") != "read-only":
        raise AssertionError(f"{agent_path} must be read-only")
    instructions = agent.get("developer_instructions", "")
    required = [
        "reviewer_result_status",
        '"SHIP"',
        '"FINDINGS"',
        '"BLOCKED_INVALID"',
        '"BLOCKED_UNAVAILABLE"',
        "Requirement Quality Gate",
        "AC-to-verification mapping",
        "Evidence Reviewed",
        "provenance",
        "Decision Boundaries",
        "must not claim external reviewer approval",
    ]
    missing = [item for item in required if item not in instructions]
    if missing:
        raise AssertionError(f"{agent_path} missing post-draft reviewer contract {missing}")


def assert_requirement_acceptance_gate(path: str) -> None:
    text = read(path)
    execution = section(text, "Execution Gates")
    acceptance_index = execution.find("Requirement Acceptance Gate")
    research_index = execution.find("Evaluate the `research` gate")
    if acceptance_index < 0:
        raise AssertionError(f"{path} missing Requirement Acceptance Gate")
    if research_index < 0 or acceptance_index > research_index:
        raise AssertionError(f"{path} must place Requirement Acceptance Gate before research")
    required = [
        "file existence alone is insufficient",
        "Ready",
        "Risky but usable",
        "reviewer_status",
        "reviewer_status: SHIP",
        "fallback status",
        "production/launch/MVP-bound",
        "blocks acceptance",
        "stale_needs_recheck",
        "missing, stale, invalid, or unaccepted",
        "do not proceed to research",
    ]
    missing = [item for item in required if item not in execution]
    if missing:
        raise AssertionError(f"{path} requirement acceptance gate missing {missing}")
    blocked = section(text, "Blocked Rules")
    blocked_required = [
        "Requirement recheck is an exception path",
        "stale_needs_recheck",
        "only when new evidence materially changes scope, verification, safety, design direction, decision boundaries, or handoff path",
        "do not silently reinterpret or patch accepted requirements",
        "old plan/review/conformance evidence",
        "rerun or explicitly revalidated",
    ]
    missing = [item for item in blocked_required if item not in blocked]
    if missing:
        raise AssertionError(f"{path} stale recheck blocker policy missing {missing}")


def assert_conformance_observability(progress_path: str, evidence_path: str) -> None:
    progress = read(progress_path)
    progress_required = [
        "## Requirement Review And Conformance State",
        "reviewer_status",
        "reviewer_fallback_status",
        "conformance_result_status",
        "CONFORMANT | FINDINGS | BLOCKED_INVALID | BLOCKED_UNAVAILABLE",
        "conformance_fallback_status",
        "none | FALLBACK_SELF_REVIEW_USED | production_bound_blocker | unavailable_no_policy",
        "AC coverage summary",
        "partial_contract_state | cleanup_pending | ready_after_parity_pass",
    ]
    missing = [item for item in progress_required if item not in progress]
    if missing:
        raise AssertionError(f"{progress_path} missing conformance observability fields {missing}")
    bad_enum = "conformance_result_status = CONFORMANT | FINDINGS | BLOCKED_INVALID | BLOCKED_UNAVAILABLE | FALLBACK_SELF_REVIEW_USED"
    if bad_enum in progress:
        raise AssertionError(f"{progress_path} must not include fallback as conformance_result_status")
    evidence = read(evidence_path)
    evidence_required = [
        "requirement reviewer fallback evidence",
        "conformance review evidence",
        "conformance_result_status",
        "conformance_fallback_status",
        "AC coverage summary",
        "FALLBACK_SELF_REVIEW_USED",
        "partial_contract_state",
    ]
    missing = [item for item in evidence_required if item not in evidence]
    if missing:
        raise AssertionError(f"{evidence_path} missing conformance evidence fields {missing}")


def assert_conformance_reviewer_agent(agent_path: str) -> None:
    agent = read_toml(agent_path)
    if agent.get("model") != "gpt-5.5":
        raise AssertionError(f"{agent_path} must use gpt-5.5")
    if agent.get("model_reasoning_effort") != "high":
        raise AssertionError(f"{agent_path} must use high reasoning effort")
    if agent.get("sandbox_mode") != "read-only":
        raise AssertionError(f"{agent_path} must be read-only")
    instructions = agent.get("developer_instructions", "")
    required = [
        "conformance_result_status",
        '"CONFORMANT"',
        '"FINDINGS"',
        '"BLOCKED_INVALID"',
        '"BLOCKED_UNAVAILABLE"',
        "acceptance coverage",
        "AC coverage",
        "non-goal",
        "Decision Boundaries",
        "residual risk",
        "prose-only approval",
        "CONFORMANT plus unresolved material findings",
        "implementation-brake owns final",
    ]
    missing = [item for item in required if item not in instructions]
    if missing:
        raise AssertionError(f"{agent_path} missing conformance reviewer contract {missing}")
    allowed_statuses = {"CONFORMANT", "FINDINGS", "BLOCKED_INVALID", "BLOCKED_UNAVAILABLE"}
    fixtures = [
        ({}, False),
        ({"conformance_result_status": "SHIP"}, False),
        ({"summary": "CONFORMANT"}, False),
        ({"conformance_result_status": "CONFORMANT", "findings": [{"issue": "gap"}]}, False),
        ({"conformance_result_status": "CONFORMANT", "findings": []}, True),
        ({"conformance_result_status": "FINDINGS", "findings": [{"issue": "gap"}]}, True),
        ({"conformance_result_status": "BLOCKED_INVALID", "findings": []}, True),
        ({"conformance_result_status": "BLOCKED_UNAVAILABLE", "findings": []}, True),
    ]
    for payload, expected in fixtures:
        actual = conformance_result_valid(payload, allowed_statuses)
        if actual is not expected:
            raise AssertionError(f"{agent_path} conformance fixture {payload} expected {expected}")


def conformance_result_valid(payload: dict, allowed_statuses: set[str]) -> bool:
    status = payload.get("conformance_result_status")
    if status not in allowed_statuses:
        return False
    findings = payload.get("findings", [])
    if status == "CONFORMANT" and findings:
        return False
    return True


def assert_implementation_brake_conformance_contract(path: str) -> None:
    text = read(path)
    required = [
        "requirement-conformance-reviewer",
        "conformance_result_status",
        "AC coverage",
        "FALLBACK_SELF_REVIEW_USED",
        "BLOCKED_UNAVAILABLE",
        "production/launch-bound",
        "missing conformance result",
        "cannot treat",
        "main `implementation-brake`",
        "final ship-readiness verdict",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"{path} missing implementation conformance contract {missing}")


def assert_requirement_quality_gate_contracts() -> None:
    for skill_path in [
        ".codex/skills/requirement-clarifier/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/requirement-clarifier/SKILL.md",
    ]:
        assert_requirement_clarifier_quality_gate(skill_path)

    for agent_path in [
        ".codex/agents/requirement-clarifier-post-draft-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/requirement-clarifier-post-draft-reviewer.toml",
    ]:
        assert_post_draft_reviewer_contract(agent_path)

    for orchestrator_path in [
        ".codex/skills/goal-requirement-orchestrator/SKILL.md",
        ".codex/skills/goal-requirement-orchestrator/references/sequence_template.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/sequence_template.md",
    ]:
        assert_requirement_acceptance_gate(orchestrator_path)

    for progress_path, evidence_path in [
        (
            ".codex/skills/goal-requirement-orchestrator/references/requirement_progress_template.md",
            ".codex/skills/goal-requirement-orchestrator/references/evidence_template.md",
        ),
        (
            ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/requirement_progress_template.md",
            ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/evidence_template.md",
        ),
    ]:
        assert_conformance_observability(progress_path, evidence_path)

    for config_path in [
        ".codex/config.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/config.toml",
    ]:
        assert_agent_registration_unique(config_path, "requirement-conformance-reviewer")

    for agent_path in [
        ".codex/agents/requirement-conformance-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/requirement-conformance-reviewer.toml",
    ]:
        assert_conformance_reviewer_agent(agent_path)

    assert_mirrored_file_parity(
        ".codex/agents/requirement-conformance-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/requirement-conformance-reviewer.toml",
    )
    assert_mirrored_file_parity(
        ".codex/agents/requirement-clarifier-post-draft-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/requirement-clarifier-post-draft-reviewer.toml",
    )
    assert_bootstrap_metadata_unique("requirement-conformance-reviewer")

    for skill_path in [
        ".codex/skills/implementation-brake/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/implementation-brake/SKILL.md",
    ]:
        assert_implementation_brake_conformance_contract(skill_path)


def assert_reference_fidelity_agent(agent_path: str) -> None:
    agent = read_toml(agent_path)
    if agent.get("model") != "gpt-5.5":
        raise AssertionError(f"{agent_path} must use gpt-5.5")
    if agent.get("model_reasoning_effort") != "high":
        raise AssertionError(f"{agent_path} must use high reasoning effort")
    if agent.get("sandbox_mode") != "read-only":
        raise AssertionError(f"{agent_path} must be read-only")
    instructions = agent.get("developer_instructions", "")
    required = [
        "You are the Reference Fidelity Reviewer",
        "detailed similarity",
        "Accepted differences inspected",
        "[REFERENCE FIDELITY PASS]",
        "[REFERENCE FIDELITY FIX REQUIRED]",
        "[REFERENCE FIDELITY BLOCKED]",
        "The main `visual-qa-hardening` skill owns final",
    ]
    missing = [item for item in required if item not in instructions]
    if missing:
        raise AssertionError(f"{agent_path} missing reference fidelity contract {missing}")


def assert_visual_qa_delegates_reference_fidelity(agent_path: str) -> None:
    agent = read_toml(agent_path)
    instructions = agent.get("developer_instructions", "")
    required = [
        "reference-driven work 에서는 detailed similarity 판정을 `reference-fidelity-reviewer`가 맡습니다.",
        "reference-only prototype chrome, debug UI leakage, or missing reference evidence",
        "[VISUAL QA PASS]",
        "[VISUAL QA FIX REQUIRED]",
        "[VISUAL QA BLOCKED]",
    ]
    missing = [item for item in required if item not in instructions]
    if missing:
        raise AssertionError(f"{agent_path} missing delegated visual QA contract {missing}")
    forbidden = "reference fidelity gaps in layout order, density, hierarchy, and state treatment"
    if forbidden in instructions:
        raise AssertionError(f"{agent_path} must not retain detailed reference fidelity ownership")


def assert_visual_qa_hardening_companions(skill_path: str) -> None:
    text = read(skill_path)
    contract = section(text, "Companion Reviewer Contract")
    required = [
        "`visual-qa-reviewer`",
        "`reference-fidelity-reviewer`",
        "reference-driven",
        "[VISUAL QA BLOCKED]",
    ]
    missing = [item for item in required if item not in contract]
    if missing:
        raise AssertionError(f"{skill_path} companion contract missing {missing}")
    if "invoke exactly one read-only companion reviewer" in contract:
        raise AssertionError(f"{skill_path} must allow the reference fidelity companion")


def assert_visual_qa_policy_mentions_reference_fidelity(path: str) -> None:
    body = section(read(path), "Execution Source Selection")
    required = [
        "`visual-qa-reviewer`",
        "`reference-fidelity-reviewer`",
        "reference-driven",
    ]
    missing = [item for item in required if item not in body]
    if missing:
        raise AssertionError(f"{path} execution policy missing reference fidelity routing {missing}")


def assert_bootstrap_installs_reference_fidelity_reviewer() -> None:
    expected_path = (
        ROOT
        / ".codex/skills/project-bootstrap/templates/root/.codex/agents/reference-fidelity-reviewer.toml"
    )
    if not expected_path.exists():
        raise AssertionError("project-bootstrap template must include reference-fidelity-reviewer agent")
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    bundle = read(".codex/skills/project-bootstrap/references/curated-bundle.md")
    for source, label in [(manifest, "manifest"), (bundle, "curated bundle")]:
        if "reference-fidelity-reviewer" not in source:
            raise AssertionError(
                f"project-bootstrap {label} must list reference-fidelity-reviewer"
            )


def assert_visual_qa_contracts() -> None:
    for config_path in [
        ".codex/config.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/config.toml",
    ]:
        assert_agent_registration(config_path, "reference-fidelity-reviewer")

    for agent_path in [
        ".codex/agents/reference-fidelity-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/reference-fidelity-reviewer.toml",
    ]:
        assert_reference_fidelity_agent(agent_path)

    for agent_path in [
        ".codex/agents/visual-qa-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/visual-qa-reviewer.toml",
    ]:
        assert_visual_qa_delegates_reference_fidelity(agent_path)

    for skill_path in [
        ".codex/skills/visual-qa-hardening/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/visual-qa-hardening/SKILL.md",
    ]:
        assert_visual_qa_hardening_companions(skill_path)

    assert_mirrored_file_parity(
        ".codex/agents/reference-fidelity-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/reference-fidelity-reviewer.toml",
    )
    assert_mirrored_file_parity(
        ".codex/agents/visual-qa-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/visual-qa-reviewer.toml",
    )
    assert_mirrored_file_parity(
        ".codex/skills/visual-qa-hardening/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/visual-qa-hardening/SKILL.md",
    )
    assert_visual_qa_policy_mentions_reference_fidelity("AGENTS.md")
    assert_visual_qa_policy_mentions_reference_fidelity(
        ".codex/skills/project-bootstrap/templates/root/AGENTS.md"
    )
    assert_bootstrap_installs_reference_fidelity_reviewer()


def main() -> int:
    lifecycle = load_module(
        ".codex/skills/goal-requirement-orchestrator/scripts/subagent_lifecycle.py"
    )
    assert_agents_gate_order("AGENTS.md")
    assert_agents_gate_order(".codex/skills/project-bootstrap/templates/root/AGENTS.md")
    assert_orchestrator_contract(".codex/skills/goal-requirement-orchestrator/SKILL.md")
    assert_orchestrator_rehydrates_experience_gates(".codex/skills/goal-requirement-orchestrator/SKILL.md")
    assert_subagent_lifecycle_policy_projection(
        ".codex/skills/goal-requirement-orchestrator/SKILL.md",
        lifecycle,
    )
    assert_orchestrator_contract(
        ".codex/skills/goal-requirement-orchestrator/references/sequence_template.md"
    )
    assert_orchestrator_rehydrates_experience_gates(
        ".codex/skills/goal-requirement-orchestrator/references/sequence_template.md"
    )
    assert_subagent_lifecycle_policy_projection(
        ".codex/skills/goal-requirement-orchestrator/references/sequence_template.md",
        lifecycle,
    )
    assert_orchestrator_contract(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/SKILL.md"
    )
    assert_orchestrator_rehydrates_experience_gates(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/SKILL.md"
    )
    assert_subagent_lifecycle_policy_projection(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/SKILL.md",
        lifecycle,
    )
    assert_orchestrator_contract(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/sequence_template.md"
    )
    assert_orchestrator_rehydrates_experience_gates(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/sequence_template.md"
    )
    assert_subagent_lifecycle_policy_projection(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/sequence_template.md",
        lifecycle,
    )
    assert_orchestrator_state_templates(
        ".codex/skills/goal-requirement-orchestrator/references/requirement_progress_template.md",
        ".codex/skills/goal-requirement-orchestrator/references/evidence_template.md",
        ".codex/skills/goal-requirement-orchestrator/references/decisions_template.md",
    )
    assert_orchestrator_state_templates(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/requirement_progress_template.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/evidence_template.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/decisions_template.md",
    )
    assert_sequence_progress_template(
        ".codex/skills/goal-requirement-orchestrator/references/sequence_progress_template.md"
    )
    assert_sequence_progress_template(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/sequence_progress_template.md"
    )
    assert_mirrored_file_parity(
        ".codex/skills/goal-requirement-orchestrator/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/SKILL.md",
    )
    assert_mirrored_file_parity(
        ".codex/skills/goal-requirement-orchestrator/references/sequence_template.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/sequence_template.md",
    )
    assert_mirrored_file_parity(
        ".codex/skills/goal-requirement-orchestrator/references/requirement_progress_template.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/requirement_progress_template.md",
    )
    assert_mirrored_file_parity(
        ".codex/skills/goal-requirement-orchestrator/references/evidence_template.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/evidence_template.md",
    )
    assert_mirrored_file_parity(
        ".codex/skills/goal-requirement-orchestrator/references/sequence_progress_template.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/sequence_progress_template.md",
    )
    assert_mirrored_file_parity(
        ".codex/skills/goal-requirement-orchestrator/scripts/subagent_lifecycle.py",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/scripts/subagent_lifecycle.py",
    )
    assert_secondary_plan_reconciles_design_review(
        ".codex/skills/secondary-plan/SKILL.md",
        ".codex/skills/secondary-plan/references/secondary_plan_template.md",
    )
    assert_secondary_plan_reconciles_design_review(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/secondary-plan/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/secondary-plan/references/secondary_plan_template.md",
    )
    assert_bootstrap_installs_plan_design_review()
    assert_manifest_declares_orchestrator_scripts()
    assert_bootstrap_installs_experience_review_skills()
    assert_experience_skill_template_parity()
    assert_bootstrap_installs_production_readiness()
    assert_production_readiness_skill(".codex/skills/production-readiness/SKILL.md")
    assert_production_readiness_skill(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/production-readiness/SKILL.md"
    )
    assert_mirrored_file_parity(
        ".codex/skills/production-readiness/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/production-readiness/SKILL.md",
    )
    assert_visual_qa_contracts()
    assert_requirement_quality_gate_contracts()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"policy verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
