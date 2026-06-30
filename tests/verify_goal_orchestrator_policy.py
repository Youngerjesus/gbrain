#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]

GATE_ORDER = [
    "research",
    "design_depth",
    "plan-design-review",
    "plan-ux-review",
    "plan-devex-review",
    "plan-eng-review",
    "scenario-brake",
    "secondary-plan",
    "ux-review",
    "devex-review",
]

THREE_MAIN_GATES = ["Plan", "Impl", "Review"]
DESIGN_DEPTH_OPTIONS = ["none", "inline", "full_artifact_required"]
REVIEW_LENSES = ["visual", "ux", "devex"]


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


def assert_three_gate_contract(path: str) -> None:
    contract = read_toml(path)
    if contract.get("main_gates") != THREE_MAIN_GATES:
        raise AssertionError(f"{path} must define main_gates as {THREE_MAIN_GATES}")

    preconditions = contract.get("preconditions", {})
    if "requirement_acceptance" not in preconditions.get("outside_three_gates", []):
        raise AssertionError(f"{path} must keep requirement acceptance outside the three gates")

    lifecycle = contract.get("lifecycle_completion", {})
    for required in ["closeout", "production_readiness"]:
        if required not in lifecycle.get("outside_three_gates", []):
            raise AssertionError(f"{path} must keep {required} outside the three gates")

    plan = contract.get("plan", {})
    if plan.get("skill") != "planning-orchestrator":
        raise AssertionError(f"{path} Plan skill must be planning-orchestrator")
    if plan.get("design_depth_options") != DESIGN_DEPTH_OPTIONS:
        raise AssertionError(f"{path} must define design depth options {DESIGN_DEPTH_OPTIONS}")
    if plan.get("top_level_removed_gates", {}).get("technical-design") != "design_depth.full_artifact_required":
        raise AssertionError(f"{path} must relocate technical-design into Plan design-depth")
    for required in [
        "research",
        "design_depth",
        "plan-design-review",
        "plan-ux-review",
        "plan-devex-review",
        "plan-eng-review",
        "scenario-brake",
        "secondary-plan",
    ]:
        if required not in plan.get("owned_subdecisions", []):
            raise AssertionError(f"{path} Plan must own {required}")
    handoff = plan.get("handoff", {})
    for required in [
        "accepted_plan_path",
        "design_depth",
        "invoked_subreviews",
        "deferred_items",
        "blockers",
        "verification_strategy",
        "stale_recheck_routing",
    ]:
        if required not in handoff.get("required_fields", []):
            raise AssertionError(f"{path} Plan handoff missing field {required}")

    impl = contract.get("impl", {})
    if impl.get("skill") != "impl-orchestrator":
        raise AssertionError(f"{path} Impl skill must be impl-orchestrator")
    for required in [
        "accepted_plan_handoff",
        "worktree_preflight",
        "scripts/init_worktree.sh",
        "context-loading",
        "tdd-workflow",
    ]:
        if required not in impl.get("requires", []):
            raise AssertionError(f"{path} Impl missing required obligation {required}")

    review = contract.get("review", {})
    if review.get("skill") != "review-orchestrator":
        raise AssertionError(f"{path} Review skill must be review-orchestrator")
    if review.get("lenses") != REVIEW_LENSES:
        raise AssertionError(f"{path} Review lenses must be {REVIEW_LENSES}")
    if not review.get("subagent_review_required_when_any_lens_triggers"):
        raise AssertionError(f"{path} must require subagent review when any Review lens triggers")
    if not review.get("parallel_lens_execution_supported"):
        raise AssertionError(f"{path} must allow triggered Review lenses to run in parallel")
    if not review.get("implementation_brake_consumes_review_evidence"):
        raise AssertionError(f"{path} must require implementation-brake to consume Review evidence")
    if review.get("implementation_brake") != "required_after_post_implementation_reviews":
        raise AssertionError(f"{path} must require implementation-brake after post-implementation reviews")
    if review.get("ship_prerequisite") != "implementation-brake [SHIP]":
        raise AssertionError(f"{path} closeout prerequisite must be implementation-brake [SHIP]")

    fixtures = contract.get("fixtures", {})
    observed_depth = [item["design_depth"] for item in fixtures.get("design_depth", [])]
    if observed_depth != DESIGN_DEPTH_OPTIONS:
        raise AssertionError(f"{path} design-depth fixtures must cover {DESIGN_DEPTH_OPTIONS}")
    observed_lenses = [item["id"] for item in fixtures.get("review_lens", [])]
    for required in ["visual_only", "ux_only", "devex_only", "multi_lens", "not_required"]:
        if required not in observed_lenses:
            raise AssertionError(f"{path} review lens fixtures missing {required}")
    assert_plan_handoff_fixtures(path, contract)
    assert_review_state_fixtures(path, contract)


def plan_handoff_valid(payload: dict, required_fields: list[str]) -> bool:
    if not isinstance(payload, dict):
        return False
    if any(field not in payload for field in required_fields):
        return False
    if payload.get("design_depth") not in DESIGN_DEPTH_OPTIONS:
        return False
    subreviews = payload.get("invoked_subreviews")
    if not isinstance(subreviews, list):
        return False
    for subreview in subreviews:
        if not isinstance(subreview, dict):
            return False
        if not {"name", "status", "artifact_path"}.issubset(subreview):
            return False
    if payload.get("blockers") not in ([], None):
        return False
    return True


def review_state_valid(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    lenses = payload.get("triggered_lenses", [])
    if not isinstance(lenses, list):
        return False
    if payload.get("implementation_brake_verdict") != "[SHIP]":
        return False
    if payload.get("unresolved_blockers"):
        return False
    if not lenses:
        return bool(payload.get("not_required_reason"))
    reviews = payload.get("post_implementation_reviews")
    if not isinstance(reviews, list):
        return False
    by_lens = {
        review.get("lens"): review
        for review in reviews
        if isinstance(review, dict)
    }
    for lens in lenses:
        review = by_lens.get(lens)
        if not review:
            return False
        if review.get("status") != "passed":
            return False
        if review.get("evidence_type") == "cleanup_only":
            return False
        if not review.get("artifact_path"):
            return False
    return True


def assert_plan_handoff_fixtures(path: str, contract: dict) -> None:
    fixtures = contract.get("fixtures", {}).get("plan_handoff", [])
    expected_ids = {
        "valid_full",
        "invalid_missing_required",
        "invalid_design_depth",
        "invalid_prose_only",
        "invalid_missing_subreview_structure",
    }
    observed = {item.get("id") for item in fixtures if isinstance(item, dict)}
    missing = expected_ids - observed
    if missing:
        raise AssertionError(f"{path} plan handoff fixtures missing {sorted(missing)}")
    required_fields = contract["plan"]["handoff"]["required_fields"]
    for fixture in fixtures:
        payload = fixture.get("payload")
        expected = fixture.get("expected_valid")
        actual = plan_handoff_valid(payload, required_fields)
        if actual is not expected:
            raise AssertionError(f"{path} plan handoff fixture {fixture.get('id')} expected {expected}, got {actual}")


def assert_review_state_fixtures(path: str, contract: dict) -> None:
    fixtures = contract.get("fixtures", {}).get("review_state", [])
    expected_ids = {
        "valid_not_required_ship",
        "valid_multi_lens_ship",
        "invalid_triggered_lens_missing_evidence",
        "invalid_cleanup_only_result",
        "invalid_unresolved_blocker",
        "invalid_missing_implementation_brake_ship",
    }
    observed = {item.get("id") for item in fixtures if isinstance(item, dict)}
    missing = expected_ids - observed
    if missing:
        raise AssertionError(f"{path} review state fixtures missing {sorted(missing)}")
    for fixture in fixtures:
        payload = fixture.get("payload")
        expected = fixture.get("expected_valid")
        actual = review_state_valid(payload)
        if actual is not expected:
            raise AssertionError(f"{path} review state fixture {fixture.get('id')} expected {expected}, got {actual}")


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
        if line.startswith("- ") and "three main gate surface" in line
    ]
    if len(gate_bullets) != 1:
        raise AssertionError(f"{path} must declare exactly one Plan -> Impl -> Review bullet")
    assert_subsequence(inline_code_tokens(gate_bullets[0]), THREE_MAIN_GATES, path)
    required_policy = [
        "planning-orchestrator",
        "design_depth",
        "worktree preflight",
        "implementation-brake",
        "source-obligation",
        "coverage-ledger",
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
    assert_subsequence(inline_code_tokens(execution), THREE_MAIN_GATES, f"{path} execution gates")
    for forbidden in [
        "Evaluate the `technical-design` gate",
        "Run the remaining pre-implementation review gates in order",
        "For this requirement, run the remaining pre-implementation review gates",
    ]:
        if forbidden in execution:
            raise AssertionError(f"{path} retains old top-level gate wording: {forbidden}")
    required_execution = [
        "Requirement Acceptance Gate",
        "`planning-orchestrator`",
        "`design_depth`",
        "`technical-design`",
        "Plan-internal",
        "worktree preflight",
        "`context-loading`",
        "`tdd-workflow`",
        "`visual-qa-hardening`",
        "`ux-review`",
        "`devex-review`",
        "`implementation-brake`",
        "`[SHIP]`",
        "`closeout`",
        "`production-readiness`",
    ]
    missing = [item for item in required_execution if item not in execution]
    if missing:
        raise AssertionError(f"{path} execution gates missing three-gate contract terms {missing}")
    worktree = section(text, "Worktree Execution Policy")
    required_worktree_policy = [
        "Goal-requirements implementation must run in an isolated task worktree",
        "Do not use any root-worktree exception",
        "branch is `main`",
        "scripts/init_worktree.sh",
        "run `scripts/init_worktree.sh <task-worktree-path>`",
        "idempotent",
        "accept the task worktree path as its first argument",
        "avoid writing external automation runtime state into the repo",
    ]
    missing = [item for item in required_worktree_policy if item not in worktree]
    if missing:
        raise AssertionError(f"{path} worktree setup policy missing {missing}")
    forbidden_worktree_policy = [
        "autopilot_root",
        "Autopilot root",
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
        "Create every listed requirement document during orchestration bootstrap",
        "all listed requirement documents must exist",
        "requirement-clarifier-post-draft-reviewer",
        "structured `reviewer_status`",
        "rerun or revalidate the post-draft reviewer gate",
    ]
    missing = [item for item in required_bootstrap_policy if item not in text]
    if missing:
        raise AssertionError(f"{path} missing sequence outcome or upfront requirement policy {missing}")
    forbidden_bootstrap_policy = [
        "create this requirements file only when this slice starts",
        "Later requirement documents stay deferred until their slice starts",
        "Do not write or rewrite later `requirements/<requirement-id>/requirements.md` files",
    ]
    present = [item for item in forbidden_bootstrap_policy if item in text]
    if present:
        raise AssertionError(f"{path} still defers later requirement documents {present}")
    assert_section_mentions(
        path,
        "Blocked Rules",
        [
            "Plan",
            "Impl",
            "Review",
            "production-readiness",
        ],
    )
    assert_section_mentions(
        path,
        "Completion Contract",
        [
            "Plan",
            "Impl",
            "Review",
            "implementation-brake",
            "production-readiness",
            "ready",
        ],
    )
    assert_section_mentions(
        path,
        "Execution Gates",
        [
            "plans/<plan-id>/plan_handoff.toml",
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
            "plans/<plan-id>/plan_handoff.toml",
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
        "Listed requirement paths",
        "All requirement files created during bootstrap: yes | no",
        "All requirement acceptance statuses recorded: yes | no",
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
    required_phrase = "rehydrate against the current `Plan -> Impl -> Review` contract"
    if required_phrase not in blocked:
        raise AssertionError(f"{path} older sequence rehydration rule must name the three-gate contract")


def assert_sequence_boundary_scope_contract(path: str) -> None:
    text = read(path)
    required = [
        "classify the user's requested artifact class",
        "checklist's execution unit",
        "Do not let a goal id, sequence title, or domain phrase",
        "Adding, inserting, or rewriting a requirement path in an existing sequence changes that sequence's scope",
        "ask for explicit user approval before inserting it into that sequence",
        "Do not insert a new requirement into an existing sequence because it is adjacent, prerequisite-like, or related to the sequence name",
        "Adding a related-looking requirement to an existing sequence without user approval",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"{path} missing sequence boundary scope contract {missing}")


def assert_sequence_template_boundary_contract(path: str) -> None:
    text = read(path)
    required = [
        "confirm that the user's requested artifact class matches the checklist's execution unit",
        "Do not add, insert, or rewrite requirement paths in an existing sequence merely because a new request seems related",
        "Changing a sequence checklist changes sequence scope and requires explicit user approval",
        "The outcome must name the artifact class this sequence produces",
        "do not hide a distinct reference, clone-coding, design, or input-contract deliverable as a prerequisite note inside an implementation sequence",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"{path} missing sequence template boundary contract {missing}")


def assert_manifest_declares_orchestrator_scripts() -> None:
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    required = [
        ".codex/skills/goal-requirement-orchestrator/scripts/subagent_lifecycle.py",
    ]
    missing = [item for item in required if item not in manifest]
    if missing:
        raise AssertionError(f"project-bootstrap manifest missing orchestrator scripts {missing}")


def assert_bootstrap_installs_task_card_templates() -> None:
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    required = [
        "projects/README.md",
        "projects/task-card-template.md",
        "project Task Card storage guidance",
        "global Task Card template",
    ]
    missing = [item for item in required if item not in manifest]
    if missing:
        raise AssertionError(f"project-bootstrap manifest missing Task Card entries {missing}")
    for path in [
        ROOT / ".codex/skills/project-bootstrap/templates/root/projects/README.md",
        ROOT / ".codex/skills/project-bootstrap/templates/root/projects/task-card-template.md",
    ]:
        if not path.exists():
            raise AssertionError(f"project-bootstrap template missing {path}")


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


def assert_bootstrap_installs_main_gate_orchestrators() -> None:
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    bundle = read(".codex/skills/project-bootstrap/references/curated-bundle.md")
    for skill in ["planning-orchestrator", "impl-orchestrator", "review-orchestrator"]:
        expected_path = ROOT / ".codex/skills/project-bootstrap/templates/root/.codex/skills" / skill / "SKILL.md"
        if not expected_path.exists():
            raise AssertionError(f"project-bootstrap template must include {skill} skill")
        for source, label in [(manifest, "manifest"), (bundle, "curated bundle")]:
            if skill not in source:
                raise AssertionError(f"project-bootstrap {label} must list {skill}")
        assert_mirrored_file_parity(
            f".codex/skills/{skill}/SKILL.md",
            f".codex/skills/project-bootstrap/templates/root/.codex/skills/{skill}/SKILL.md",
        )
    assert_mirrored_file_parity(
        ".codex/skills/goal-requirement-orchestrator/references/three_gate_contract.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/three_gate_contract.toml",
    )


def assert_planning_orchestrator_skill(path: str) -> None:
    text = read(path)
    required = [
        "name: planning-orchestrator",
        "Plan",
        "plans/<plan-id>/plan_handoff.toml",
        "design_depth",
        "none",
        "inline",
        "full_artifact_required",
        "technical-design",
        "Plan-internal",
        "research",
        "plan-design-review",
        "plan-ux-review",
        "plan-devex-review",
        "plan-eng-review",
        "scenario-brake",
        "secondary-plan",
        "conversation memory",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"{path} missing planning orchestrator contract {missing}")


def assert_impl_orchestrator_skill(path: str) -> None:
    text = read(path)
    required = [
        "name: impl-orchestrator",
        "Impl",
        "accepted Plan handoff",
        "worktree preflight",
        "scripts/init_worktree.sh",
        "context-loading",
        "tdd-workflow",
        "implementation evidence",
        "Review",
        "conversation memory",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"{path} missing impl orchestrator contract {missing}")


def assert_review_orchestrator_skill(path: str) -> None:
    text = read(path)
    required = [
        "name: review-orchestrator",
        "Review",
        "implementation evidence",
        "parallel",
        "same Review gate",
        "fan out",
        "visual-qa-hardening",
        "ux-review",
        "devex-review",
        "triggered lenses",
        "implementation-brake",
        "consumes the review evidence",
        "[SHIP]",
        "closeout",
        "cleanup-only",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"{path} missing review orchestrator contract {missing}")


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
        "## Original Intent Preservation",
        "## Strict Target And Flexible Clause Priority",
        "AC-to-verification mapping",
        "Evidence Reviewed",
        "session_provenance",
        "Decision Boundaries",
        "reviewer_status",
        "Risky but usable",
        "production-bound",
        "self-review fallback",
        "must not silently claim external reviewer approval",
        "Agent discretion is allowed only inside the user's strict target",
        "Interpretation may clarify intent, but it must not replace intent",
        "strict user target",
        "flexible interpretation clause",
        "deviation ledger",
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
        "Original Intent Preservation",
        "Strict Target And Flexible Clause Priority",
        "AC-to-verification mapping",
        "Evidence Reviewed",
        "provenance",
        "Decision Boundaries",
        "must not claim external reviewer approval",
        "strict target",
        "flexible interpretation clause",
        "deviation ledger",
        "material omission, distortion, invented requirement",
    ]
    missing = [item for item in required if item not in instructions]
    if missing:
        raise AssertionError(f"{agent_path} missing post-draft reviewer contract {missing}")


def assert_requirement_acceptance_gate(path: str) -> None:
    text = read(path)
    execution = section(text, "Execution Gates")
    acceptance_index = execution.find("Requirement Acceptance Gate")
    plan_index = execution.find("`Plan`")
    if acceptance_index < 0:
        raise AssertionError(f"{path} missing Requirement Acceptance Gate")
    if plan_index < 0 or acceptance_index > plan_index:
        raise AssertionError(f"{path} must place Requirement Acceptance Gate before Plan")
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
        "Escape Hatch Detection",
        "flexible clause",
        "stricter requirement",
        "unapproved substitution",
        "Only explicit accepted deviations can narrow the target",
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


def assert_source_obligation_reviewer_agent(agent_path: str) -> None:
    agent = read_toml(agent_path)
    if agent.get("name") != "Source Obligation Reviewer":
        raise AssertionError(f"{agent_path} must name Source Obligation Reviewer")
    if agent.get("model") != "gpt-5.5":
        raise AssertionError(f"{agent_path} must use gpt-5.5")
    if agent.get("model_reasoning_effort") != "high":
        raise AssertionError(f"{agent_path} must use high reasoning effort")
    if agent.get("sandbox_mode") != "read-only":
        raise AssertionError(f"{agent_path} must be read-only")
    instructions = agent.get("developer_instructions", "")
    required = [
        "source_obligation_review_status",
        '"SHIP"',
        '"FINDINGS"',
        '"BLOCKED_INVALID"',
        '"BLOCKED_UNAVAILABLE"',
        "source-inventory.yml",
        "scope-reconciliation.yml",
        "requirements.md",
        "coverage-decision.yml",
        "coverage-ledger.yml",
        "progress.md",
        "evidence.md",
        "source inventory is raw source truth",
        "scope reconciliation is the accepted-scope candidate",
        "requirements are a projection",
        "progress, evidence, reviewer prose, and closeout summaries are non-authoritative",
        "missing inventory items",
        "invented reconciliation items",
        "included items without obligation ids or coverage ledger row ids",
        "excluded, deferred, or ambiguous items without rationale",
        "stale digest or version lineage",
        "contradictory reviewer fields",
        "prose-only approval",
        "validator evidence",
        "Do not edit files",
        "Do not rewrite scope",
        "Do not invent obligations",
        "You must inspect all required source-obligation artifacts before returning SHIP",
        "If a required source-obligation artifact cannot be inspected, return BLOCKED_UNAVAILABLE",
        "missing or invalid ledger row references",
    ]
    missing = [item for item in required if item not in instructions]
    if missing:
        raise AssertionError(f"{agent_path} missing source-obligation reviewer contract {missing}")
    allowed_line = next(
        (line for line in instructions.splitlines() if "Allowed source_obligation_review_status values" in line),
        "",
    )
    forbidden_allowed = {"APPROVED", "NOT_REQUIRED", "NOT_REVIEWED", "BLOCKED"}
    allowed_tokens = set(re.findall(r'"([^"]+)"', allowed_line))
    present = sorted(forbidden_allowed & allowed_tokens)
    if present:
        raise AssertionError(f"{agent_path} allowed status line contains forbidden statuses {present}")


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
        "## Review Gate Evidence Inputs",
        "triggered review evidence",
        "visual-qa-hardening",
        "visual-qa-reviewer",
        "reference-fidelity-reviewer",
        "ux-review",
        "devex-review",
        "parallel Review lens execution",
        "main `implementation-brake`",
        "final ship-readiness verdict",
        "## Contract Downgrade Ship Gate",
        "weaker interpretation of the accepted requirement",
        "Unapproved downgrade is must-fix, not polish",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"{path} missing implementation conformance contract {missing}")


def assert_implementation_brake_reviewer_agent(agent_path: str) -> None:
    agent = read_toml(agent_path)
    if agent.get("sandbox_mode") != "read-only":
        raise AssertionError(f"{agent_path} must be read-only")
    instructions = agent.get("developer_instructions", "")
    required = [
        "Contract Downgrade Review",
        "weaker interpretation of the accepted requirement",
        "flexible wording",
        "strict user target",
        "artifact class",
        "evidence level",
        "execution boundary",
        "Only explicit accepted deviations can narrow the target",
        "Unapproved downgrade is must-fix, not polish",
    ]
    missing = [item for item in required if item not in instructions]
    if missing:
        raise AssertionError(f"{agent_path} missing implementation-brake reviewer downgrade contract {missing}")


def assert_worktree_preflight_distribution() -> None:
    script_paths = [
        "scripts/init_worktree.sh",
        ".codex/skills/project-bootstrap/templates/root/scripts/init_worktree.sh",
    ]
    for path in script_paths:
        script = read(path)
        required = [
            "usage: scripts/init_worktree.sh <task-worktree-path>",
            "primary/main worktree",
            "branch is main",
            "scripts/verify",
            "worktree setup ok",
        ]
        missing = [item for item in required if item not in script]
        if missing:
            raise AssertionError(f"{path} missing worktree preflight behavior {missing}")
    assert_mirrored_file_parity(
        "scripts/init_worktree.sh",
        ".codex/skills/project-bootstrap/templates/root/scripts/init_worktree.sh",
    )
    assert_mirrored_file_parity(
        "tests/verify_worktree_preflight.py",
        ".codex/skills/project-bootstrap/templates/root/tests/verify_worktree_preflight.py",
    )
    manifest = read(".codex/skills/project-bootstrap/references/manifest.md")
    required_manifest = [
        "`scripts/init_worktree.sh`",
        "`tests/verify_worktree_preflight.py`",
        "isolated task worktree preflight",
        "task worktree preflight tests",
    ]
    missing = [item for item in required_manifest if item not in manifest]
    if missing:
        raise AssertionError(f"project-bootstrap manifest missing worktree preflight entries {missing}")


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

    for config_path in [
        ".codex/config.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/config.toml",
    ]:
        assert_agent_registration_unique(config_path, "source-obligation-reviewer")

    for agent_path in [
        ".codex/agents/source-obligation-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/source-obligation-reviewer.toml",
    ]:
        assert_source_obligation_reviewer_agent(agent_path)

    assert_mirrored_file_parity(
        ".codex/agents/source-obligation-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/source-obligation-reviewer.toml",
    )
    assert_bootstrap_metadata_unique("source-obligation-reviewer")

    for skill_path in [
        ".codex/skills/implementation-brake/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/implementation-brake/SKILL.md",
    ]:
        assert_implementation_brake_conformance_contract(skill_path)

    for agent_path in [
        ".codex/agents/implementation-brake-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/implementation-brake-reviewer.toml",
    ]:
        assert_implementation_brake_reviewer_agent(agent_path)

    assert_mirrored_file_parity(
        ".codex/agents/implementation-brake-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/implementation-brake-reviewer.toml",
    )


def assert_source_obligation_workflow_contracts() -> None:
    for skill_path in [
        ".codex/skills/requirement-clarifier/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/requirement-clarifier/SKILL.md",
    ]:
        text = read(skill_path)
        required = [
            "## Source Obligation Gate",
            "source-inventory.yml",
            "scope-reconciliation.yml",
            "source-obligation-reviewer",
            "source_obligation_review_status",
            "scripts/coverage_ledger.py validate --mode readiness",
            "source_obligation_inventory_required",
            "structured source-obligation not-required decision",
            "prose-only",
            "source-less scope narrowing",
            "requirements are a projection",
        ]
        missing = [item for item in required if item not in text]
        if missing:
            raise AssertionError(f"{skill_path} missing source-obligation gate guidance {missing}")

    for agent_path in [
        ".codex/agents/requirement-clarifier-post-draft-reviewer.toml",
        ".codex/skills/project-bootstrap/templates/root/.codex/agents/requirement-clarifier-post-draft-reviewer.toml",
    ]:
        instructions = read_toml(agent_path).get("developer_instructions", "")
        required = [
            "source-inventory.yml",
            "scope-reconciliation.yml",
            "source-obligation-reviewer",
            "source_obligation_review_status",
            "scripts/coverage_ledger.py validate --mode readiness",
            "source_obligation_inventory_required",
            "missing, stale, failed, or unavailable",
            "prose-only",
            "Readiness Status: Ready",
        ]
        missing = [item for item in required if item not in instructions]
        if missing:
            raise AssertionError(f"{agent_path} missing source-obligation post-draft review contract {missing}")

    for orchestrator_path in [
        ".codex/skills/goal-requirement-orchestrator/SKILL.md",
        ".codex/skills/goal-requirement-orchestrator/references/sequence_template.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/sequence_template.md",
    ]:
        text = read(orchestrator_path)
        required = [
            "source-obligation reviewer `SHIP`",
            "structured source-obligation not-required decision",
            "source-inventory.yml",
            "scope-reconciliation.yml",
            "scripts/coverage_ledger.py validate --mode readiness",
            "source_obligation_inventory_required",
            "missing, stale, failed, or unavailable source-obligation",
            "source-obligation-review",
            "source-obligation state cannot be satisfied by prose",
        ]
        missing = [item for item in required if item not in text]
        if missing:
            raise AssertionError(f"{orchestrator_path} missing source-obligation orchestration contract {missing}")

    for progress_path, evidence_path, decisions_path in [
        (
            ".codex/skills/goal-requirement-orchestrator/references/requirement_progress_template.md",
            ".codex/skills/goal-requirement-orchestrator/references/evidence_template.md",
            ".codex/skills/goal-requirement-orchestrator/references/decisions_template.md",
        ),
        (
            ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/requirement_progress_template.md",
            ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/evidence_template.md",
            ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/references/decisions_template.md",
        ),
    ]:
        progress = read(progress_path)
        progress_required = [
            "## Source Obligation Gate State",
            "source-inventory.yml",
            "scope-reconciliation.yml",
            "source_obligation_review_status",
            "source_obligation_inventory_required",
            "source-obligation-review",
            "scripts/coverage_ledger.py validate --mode readiness",
        ]
        missing = [item for item in progress_required if item not in progress]
        if missing:
            raise AssertionError(f"{progress_path} missing source-obligation progress fields {missing}")
        evidence = read(evidence_path)
        evidence_required = [
            "source-obligation evidence",
            "source-inventory.yml",
            "scope-reconciliation.yml",
            "source_obligation_review_status",
            "scripts/coverage_ledger.py validate --mode readiness",
            "scripts/coverage_ledger.py validate --mode closure",
        ]
        missing = [item for item in evidence_required if item not in evidence]
        if missing:
            raise AssertionError(f"{evidence_path} missing source-obligation evidence fields {missing}")
        decisions = read(decisions_path)
        decisions_required = [
            "source-obligation decision",
            "source_obligation_inventory_required",
            "structured source-obligation not-required decision",
            "source-inventory.yml",
            "scope-reconciliation.yml",
        ]
        missing = [item for item in decisions_required if item not in decisions]
        if missing:
            raise AssertionError(f"{decisions_path} missing source-obligation decision guidance {missing}")

    for agents_path in [
        "AGENTS.md",
        ".codex/skills/project-bootstrap/templates/root/AGENTS.md",
    ]:
        text = read(agents_path)
        required = [
            "Source Obligation Gates",
            "source-inventory.yml",
            "scope-reconciliation.yml",
            "source-obligation-reviewer",
            "scripts/coverage_ledger.py validate --mode readiness",
            "scripts/coverage_ledger.py validate --mode closure",
            "source_obligation_inventory_required",
            "structured source-obligation not-required decision",
            "cannot be overridden by prose",
            "not warning-only",
        ]
        missing = [item for item in required if item not in text]
        if missing:
            raise AssertionError(f"{agents_path} missing source-obligation operating policy {missing}")

    for brake_path in [
        ".codex/skills/implementation-brake/SKILL.md",
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/implementation-brake/SKILL.md",
    ]:
        text = read(brake_path)
        required = [
            "## Source Obligation Ship Gate",
            "source-inventory.yml",
            "scope-reconciliation.yml",
            "source-obligation-reviewer",
            "source_obligation_review_status",
            "scripts/coverage_ledger.py validate --mode closure",
            "missing, stale, failed, or unavailable",
            "Do not issue `[SHIP]`",
            "prose-only",
        ]
        missing = [item for item in required if item not in text]
        if missing:
            raise AssertionError(f"{brake_path} missing source-obligation ship gate {missing}")

    scanned_paths = [
        "AGENTS.md",
        ".codex/skills/requirement-clarifier/SKILL.md",
        ".codex/agents/requirement-clarifier-post-draft-reviewer.toml",
        ".codex/skills/goal-requirement-orchestrator/SKILL.md",
        ".codex/skills/goal-requirement-orchestrator/references/sequence_template.md",
        ".codex/skills/implementation-brake/SKILL.md",
    ]
    for path in scanned_paths:
        if "coverage_inventory.py" in read(path):
            raise AssertionError(f"{path} must not introduce coverage_inventory.py")


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
        "Reference parity is concrete, not merely structural",
        "header/status-bar height",
        "safe-area treatment",
        "tab/filter density",
        "row height and list density",
        "image scale, crop, realism, and product material feel",
        "column position, alignment, width, and typography",
        "repeated-item rhythm",
        "Bounded Styling Variance",
        "Accepted Deviation Enforcement",
        "structure-level similarity",
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
        "Reference-Driven Visual QA",
        "usable, polished, unclipped, or internally consistent",
        "hierarchy, geometry, density, navigation placement, safe-area treatment, imagery treatment, or repeated-list rhythm",
        "accepted deviation",
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
    assert_three_gate_contract(
        ".codex/skills/goal-requirement-orchestrator/references/three_gate_contract.toml"
    )
    assert_agents_gate_order("AGENTS.md")
    assert_agents_gate_order(".codex/skills/project-bootstrap/templates/root/AGENTS.md")
    assert_orchestrator_contract(".codex/skills/goal-requirement-orchestrator/SKILL.md")
    assert_orchestrator_rehydrates_experience_gates(".codex/skills/goal-requirement-orchestrator/SKILL.md")
    assert_sequence_boundary_scope_contract(".codex/skills/goal-requirement-orchestrator/SKILL.md")
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
    assert_sequence_template_boundary_contract(
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
    assert_sequence_boundary_scope_contract(
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
    assert_sequence_template_boundary_contract(
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
    assert_planning_orchestrator_skill(".codex/skills/planning-orchestrator/SKILL.md")
    assert_planning_orchestrator_skill(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/planning-orchestrator/SKILL.md"
    )
    assert_impl_orchestrator_skill(".codex/skills/impl-orchestrator/SKILL.md")
    assert_impl_orchestrator_skill(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/impl-orchestrator/SKILL.md"
    )
    assert_review_orchestrator_skill(".codex/skills/review-orchestrator/SKILL.md")
    assert_review_orchestrator_skill(
        ".codex/skills/project-bootstrap/templates/root/.codex/skills/review-orchestrator/SKILL.md"
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
    assert_bootstrap_installs_main_gate_orchestrators()
    assert_manifest_declares_orchestrator_scripts()
    assert_bootstrap_installs_task_card_templates()
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
    assert_source_obligation_workflow_contracts()
    assert_worktree_preflight_distribution()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"policy verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
