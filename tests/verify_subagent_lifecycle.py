#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT / ".codex/skills/goal-requirement-orchestrator/scripts/subagent_lifecycle.py"
)
MIRROR_HELPER_PATH = (
    ROOT
    / ".codex/skills/project-bootstrap/templates/root/.codex/skills/goal-requirement-orchestrator/scripts/subagent_lifecycle.py"
)


def load_lifecycle():
    spec = importlib.util.spec_from_file_location("subagent_lifecycle", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load helper at {HELPER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_artifact(**overrides):
    artifact = {
        "requirement_id": "001-subagent-nonblocking-fallback",
        "gate": "plan-eng-review",
        "lens": "scope-reuse",
        "lifecycle_record_id": "record-1",
        "checkpoint_id": "checkpoint-current",
        "artifact_path": "requirements/001-subagent-nonblocking-fallback/evidence.md",
        "result": {"recommendation": "GO WITH CHANGES", "findings": []},
    }
    artifact.update(overrides)
    return artifact


def context(**overrides):
    base = {
        "requirement_id": "001-subagent-nonblocking-fallback",
        "gate": "plan-eng-review",
        "lens": "scope-reuse",
        "lifecycle_record_id": "record-1",
        "checkpoint_id": "checkpoint-current",
        "artifact_path": "requirements/001-subagent-nonblocking-fallback/evidence.md",
        "evidence_ref": "requirements/001-subagent-nonblocking-fallback/evidence.md#2026-06-19-1257-kst",
    }
    base.update(overrides)
    return base


class CloseWouldHang(Exception):
    pass


class FakeAdapter:
    def __init__(self):
        self.close_calls = []

    def close_agent(self, subagent_id):
        self.close_calls.append(subagent_id)
        raise CloseWouldHang(subagent_id)


def assert_timeout_records_abandoned_without_close(lifecycle) -> None:
    adapter = FakeAdapter()
    result = lifecycle.SubagentWaitResult(
        subagent_id="agent-timeout",
        timed_out=True,
        observed_status={},
        artifact=None,
        wait_deadline_ms=10000,
    )
    decision = lifecycle.handle_wait_result(
        wait_result=result,
        requirement_id="001-subagent-nonblocking-fallback",
        gate="plan-eng-review",
        fallback_policy=lifecycle.fallback_policies()["plan-eng-review"],
        result_context=context(),
        result_validator=lifecycle.validate_gate_artifact,
        now_iso="2026-06-19T12:30:00+09:00",
        close_agent=adapter.close_agent,
    )
    if adapter.close_calls:
        raise AssertionError("close_agent must not be called before timeout fallback")
    if decision.record.lifecycle_state != lifecycle.LifecycleState.ABANDONED:
        raise AssertionError(f"expected abandoned, got {decision.record.lifecycle_state}")
    if decision.fallback_action != lifecycle.FallbackAction.STRUCTURED_BLOCKED:
        raise AssertionError(f"unexpected fallback action {decision.fallback_action}")
    if decision.record.evidence_ref != context()["evidence_ref"]:
        raise AssertionError("abandoned record must preserve durable evidence_ref")
    required = {
        "subagent_id",
        "gate",
        "requirement_id",
        "wait_deadline_ms",
        "observed_status",
        "reason",
        "timestamp",
        "fallback_action",
        "evidence_ref",
    }
    missing = required - set(decision.record.to_dict())
    if missing:
        raise AssertionError(f"lifecycle record missing required fields {sorted(missing)}")


def assert_result_shape_and_provenance(lifecycle) -> None:
    invalid_results = [
        lifecycle.SubagentWaitResult("agent-empty", False, {}, None, 10000),
        lifecycle.SubagentWaitResult("agent-prose", False, {"state": "completed"}, "SHIP", 10000),
        lifecycle.SubagentWaitResult("agent-no-artifact", False, {"state": "completed"}, None, 10000),
        lifecycle.SubagentWaitResult("agent-interrupted", False, {"state": "interrupted"}, None, 10000),
        lifecycle.SubagentWaitResult("agent-aborted", False, {"state": "turn_aborted"}, None, 10000),
        lifecycle.SubagentWaitResult("agent-shutdown", False, {"state": "shutdown"}, None, 10000),
        lifecycle.SubagentWaitResult("agent-stale", False, {"state": "live", "stale": True}, None, 10000),
        lifecycle.SubagentWaitResult(
            "agent-wrong-requirement",
            False,
            {"state": "completed"},
            valid_artifact(requirement_id="other"),
            10000,
        ),
        lifecycle.SubagentWaitResult(
            "agent-wrong-gate",
            False,
            {"state": "completed"},
            valid_artifact(gate="scenario-brake"),
            10000,
        ),
        lifecycle.SubagentWaitResult(
            "agent-wrong-lens",
            False,
            {"state": "completed"},
            valid_artifact(lens="verification"),
            10000,
        ),
        lifecycle.SubagentWaitResult(
            "agent-stale-artifact",
            False,
            {"state": "completed"},
            valid_artifact(checkpoint_id="checkpoint-old"),
            10000,
        ),
        lifecycle.SubagentWaitResult(
            "agent-wrong-artifact-path",
            False,
            {"state": "completed"},
            valid_artifact(artifact_path="requirements/other/evidence.md"),
            10000,
        ),
    ]
    for wait_result in invalid_results:
        if lifecycle.is_usable_result(wait_result, context(), lifecycle.validate_gate_artifact):
            raise AssertionError(f"{wait_result.subagent_id} must not be usable")

    missing_expected_path_context = context()
    missing_expected_path_context.pop("artifact_path")
    wrong_path_without_expected_context = lifecycle.SubagentWaitResult(
        "agent-wrong-artifact-path-without-context",
        False,
        {"state": "completed"},
        valid_artifact(artifact_path="requirements/other/evidence.md"),
        10000,
    )
    if lifecycle.is_usable_result(
        wrong_path_without_expected_context,
        missing_expected_path_context,
        lifecycle.validate_gate_artifact,
    ):
        raise AssertionError("artifact path provenance context must be required")

    valid = lifecycle.SubagentWaitResult(
        "agent-valid",
        False,
        {"state": "completed"},
        valid_artifact(),
        10000,
    )
    if not lifecycle.is_usable_result(valid, context(), lifecycle.validate_gate_artifact):
        raise AssertionError("valid structured artifact should be usable")


def assert_fallback_policies(lifecycle) -> None:
    policies = lifecycle.fallback_policies()
    expected = {
        "requirement-clarifier-post-draft-review",
        "context-loading",
        "plan-design-review",
        "plan-ux-review",
        "plan-devex-review",
        "plan-eng-review",
        "scenario-brake",
        "visual-qa-hardening",
        "ux-review",
        "devex-review",
        "implementation-brake",
        "closeout",
    }
    if set(policies) != expected:
        raise AssertionError(f"fallback policies drifted: {sorted(policies)}")
    for gate, policy in policies.items():
        if policy.gate != gate:
            raise AssertionError(f"{gate} policy gate mismatch")
        if policy.action not in set(lifecycle.FallbackAction):
            raise AssertionError(f"{gate} has invalid action {policy.action}")
    lifecycle.assert_policy_action_matches(
        policies["plan-eng-review"],
        lifecycle.FallbackAction.STRUCTURED_BLOCKED,
    )
    for gate in [
        "plan-design-review",
        "plan-ux-review",
        "plan-devex-review",
        "ux-review",
        "devex-review",
    ]:
        lifecycle.assert_policy_action_matches(
            policies[gate],
            lifecycle.FallbackAction.STRUCTURED_BLOCKED,
        )
    lifecycle.assert_policy_action_matches(
        policies["context-loading"],
        lifecycle.FallbackAction.PARENT_FALLBACK,
    )
    try:
        lifecycle.assert_policy_action_matches(
            policies["plan-eng-review"],
            lifecycle.FallbackAction.PARENT_FALLBACK,
        )
    except lifecycle.FallbackPolicyMismatch:
        pass
    else:
        raise AssertionError("policy/action mismatch must be rejected")


def assert_requirement_reviewer_policy_context(lifecycle) -> None:
    ordinary = lifecycle.select_fallback_policy(
        "requirement-clarifier-post-draft-review",
        requirement_context={"production_bound": False},
    )
    lifecycle.assert_policy_action_matches(
        ordinary,
        lifecycle.FallbackAction.PARENT_FALLBACK,
    )

    strict_contexts = [
        {"production_bound": True},
        {"launch_bound": True},
        {"mvp_bound": True},
        {"irreversible_or_safety_critical": True},
    ]
    for strict_context in strict_contexts:
        strict = lifecycle.select_fallback_policy(
            "requirement-clarifier-post-draft-review",
            requirement_context=strict_context,
        )
        lifecycle.assert_policy_action_matches(
            strict,
            lifecycle.FallbackAction.STRUCTURED_BLOCKED,
        )


def assert_handle_wait_result_rejects_policy_context_mismatch(lifecycle) -> None:
    valid = lifecycle.SubagentWaitResult(
        "agent-valid",
        False,
        {"state": "completed"},
        valid_artifact(),
        10000,
    )
    try:
        lifecycle.handle_wait_result(
            wait_result=valid,
            requirement_id="001-subagent-nonblocking-fallback",
            gate="plan-eng-review",
            fallback_policy=lifecycle.fallback_policies()["context-loading"],
            result_context=context(gate="context-loading", lens="context-loader"),
            result_validator=lifecycle.validate_gate_artifact,
            now_iso="2026-06-19T12:30:00+09:00",
        )
    except lifecycle.FallbackPolicyMismatch:
        pass
    else:
        raise AssertionError("handle_wait_result must reject mismatched gate policy/context")


def assert_replacement_and_late_result_paths(lifecycle) -> None:
    original = lifecycle.LifecycleRecord.abandoned(
        subagent_id="agent-original",
        gate="context-loading",
        requirement_id="001-subagent-nonblocking-fallback",
        wait_deadline_ms=10000,
        observed_status={"timed_out": True},
        reason="timeout",
        timestamp="2026-06-19T12:30:00+09:00",
        fallback_action=lifecycle.FallbackAction.REPLACEMENT_SUBAGENT,
        evidence_ref="requirements/001-subagent-nonblocking-fallback/evidence.md#replacement-original",
    )
    replacement_success = lifecycle.record_replacement_result(
        original_record=original,
        replacement_result=lifecycle.SubagentWaitResult(
            "agent-replacement",
            False,
            {"state": "completed"},
            valid_artifact(gate="context-loading", lens="context-loader"),
            10000,
        ),
        result_context=context(gate="context-loading", lens="context-loader"),
        result_validator=lifecycle.validate_gate_artifact,
    )
    if replacement_success.status != lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("valid replacement should be accepted")

    replacement_timeout = lifecycle.record_replacement_result(
        original_record=original,
        replacement_result=lifecycle.SubagentWaitResult(
            "agent-replacement-timeout",
            True,
            {},
            None,
            10000,
        ),
        result_context=context(gate="context-loading", lens="context-loader"),
        result_validator=lifecycle.validate_gate_artifact,
    )
    if replacement_timeout.status != lifecycle.FallbackResolutionStatus.BLOCKED:
        raise AssertionError("replacement timeout must become structured blocked")

    wrong_action_original = lifecycle.LifecycleRecord.abandoned(
        subagent_id="agent-wrong-action-original",
        gate="plan-eng-review",
        requirement_id="001-subagent-nonblocking-fallback",
        wait_deadline_ms=10000,
        observed_status={"timed_out": True},
        reason="timeout",
        timestamp="2026-06-19T12:30:00+09:00",
        fallback_action=lifecycle.FallbackAction.STRUCTURED_BLOCKED,
        evidence_ref="requirements/001-subagent-nonblocking-fallback/evidence.md#wrong-action",
    )
    wrong_action_replacement = lifecycle.record_replacement_result(
        original_record=wrong_action_original,
        replacement_result=lifecycle.SubagentWaitResult(
            "agent-replacement",
            False,
            {"state": "completed"},
            valid_artifact(),
            10000,
        ),
        result_context=context(),
        result_validator=lifecycle.validate_gate_artifact,
    )
    if wrong_action_replacement.status == lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("non-replacement fallback action must not accept replacement result")

    wrong_gate_replacement = lifecycle.record_replacement_result(
        original_record=original,
        replacement_result=lifecycle.SubagentWaitResult(
            "agent-replacement-wrong-gate",
            False,
            {"state": "completed"},
            valid_artifact(gate="plan-eng-review"),
            10000,
        ),
        result_context=context(gate="plan-eng-review"),
        result_validator=lifecycle.validate_gate_artifact,
    )
    if wrong_gate_replacement.status == lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("replacement context gate must match original record")

    wrong_requirement_replacement = lifecycle.record_replacement_result(
        original_record=original,
        replacement_result=lifecycle.SubagentWaitResult(
            "agent-replacement-wrong-requirement",
            False,
            {"state": "completed"},
            valid_artifact(
                requirement_id="002-other",
                gate="context-loading",
                lens="context-loader",
            ),
            10000,
        ),
        result_context=context(
            requirement_id="002-other",
            gate="context-loading",
            lens="context-loader",
        ),
        result_validator=lifecycle.validate_gate_artifact,
    )
    if wrong_requirement_replacement.status == lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("replacement context requirement must match original record")

    replacement_unavailable = lifecycle.record_replacement_unavailable(
        original_record=original,
        reason="usage_limit",
    )
    if replacement_unavailable.status != lifecycle.FallbackResolutionStatus.ESCALATED:
        raise AssertionError("replacement unavailable should escalate")

    late = lifecycle.handle_late_original_result(
        original_record=original,
        accepted_resolution=replacement_success,
        late_result=lifecycle.SubagentWaitResult(
            "agent-original",
            False,
            {"state": "completed"},
            valid_artifact(gate="context-loading", lens="context-loader"),
            10000,
        ),
        result_context=context(gate="context-loading", lens="context-loader"),
        result_validator=lifecycle.validate_gate_artifact,
    )
    if late.status != lifecycle.LateResultStatus.QUARANTINED:
        raise AssertionError("late original result must be quarantined")


def assert_partial_companion_and_resume_paths(lifecycle) -> None:
    required_results = [
        lifecycle.CompanionResult("scope", usable=True, required=True),
        lifecycle.CompanionResult("architecture", usable=False, required=True),
        lifecycle.CompanionResult("verification", usable=True, required=True),
    ]
    partial = lifecycle.evaluate_companion_set(required_results)
    if partial.status != lifecycle.FallbackResolutionStatus.BLOCKED:
        raise AssertionError("missing required companion must block")

    optional_results = [
        lifecycle.CompanionResult("core", usable=True, required=True),
        lifecycle.CompanionResult("optional", usable=False, required=False),
    ]
    optional = lifecycle.evaluate_companion_set(optional_results)
    if optional.status != lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("missing optional companion should not block")

    expired_started = lifecycle.reconcile_resume_state(
        lifecycle.ResumeState(
            lifecycle_state=lifecycle.LifecycleState.STARTED,
            deadline_expired=True,
            fallback_action=None,
            has_fallback_evidence=False,
            cleanup_status=lifecycle.CleanupStatus.NOT_NEEDED,
        )
    )
    if expired_started.status != lifecycle.FallbackResolutionStatus.BLOCKED:
        raise AssertionError("expired started state needs explicit fallback recovery")

    fallback_action_only = lifecycle.reconcile_resume_state(
        lifecycle.ResumeState(
            lifecycle_state=lifecycle.LifecycleState.FALLBACK_RECORDED,
            deadline_expired=True,
            fallback_action=lifecycle.FallbackAction.PARENT_FALLBACK,
            has_fallback_evidence=False,
            cleanup_status=lifecycle.CleanupStatus.NOT_NEEDED,
        )
    )
    if fallback_action_only.status != lifecycle.FallbackResolutionStatus.BLOCKED:
        raise AssertionError("fallback action alone must not be accepted")

    cleanup_pending = lifecycle.reconcile_resume_state(
        lifecycle.ResumeState(
            lifecycle_state=lifecycle.LifecycleState.FALLBACK_RECORDED,
            deadline_expired=True,
            fallback_action=lifecycle.FallbackAction.PARENT_FALLBACK,
            has_fallback_evidence=True,
            cleanup_status=lifecycle.CleanupStatus.CLEANUP_PENDING,
        )
    )
    if cleanup_pending.status != lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("cleanup pending should not block valid fallback evidence")
    if not cleanup_pending.cleanup_visible:
        raise AssertionError("cleanup pending must remain visible")
    if cleanup_pending.spawn_duplicate:
        raise AssertionError("resume with fallback evidence must not spawn duplicate companion")


def assert_close_success_is_not_acceptance(lifecycle) -> None:
    resolution = lifecycle.evaluate_gate_acceptance(
        fallback_action=lifecycle.FallbackAction.PARENT_FALLBACK,
        has_fallback_artifact=False,
        has_replacement_result=False,
        has_structured_blocker=False,
        has_escalation_record=False,
        close_result=lifecycle.CloseResult(status=lifecycle.CleanupStatus.COMPLETED),
    )
    if resolution.status == lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("close success alone must not satisfy gate acceptance")

    accepted = lifecycle.evaluate_gate_acceptance(
        fallback_action=lifecycle.FallbackAction.PARENT_FALLBACK,
        has_fallback_artifact=True,
        has_replacement_result=False,
        has_structured_blocker=False,
        has_escalation_record=False,
        close_result=lifecycle.CloseResult(status=lifecycle.CleanupStatus.CLEANUP_PENDING),
    )
    if accepted.status != lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("fallback artifact should satisfy gate acceptance")
    if not accepted.cleanup_visible:
        raise AssertionError("cleanup pending must remain visible")

    structured_wrong = lifecycle.evaluate_gate_acceptance(
        fallback_action=lifecycle.FallbackAction.STRUCTURED_BLOCKED,
        has_fallback_artifact=True,
        has_replacement_result=False,
        has_structured_blocker=False,
        has_escalation_record=False,
        close_result=None,
    )
    if structured_wrong.status == lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("structured-blocked gates must not pass via parent fallback artifact")

    structured_blocked = lifecycle.evaluate_gate_acceptance(
        fallback_action=lifecycle.FallbackAction.STRUCTURED_BLOCKED,
        has_fallback_artifact=False,
        has_replacement_result=False,
        has_structured_blocker=True,
        has_escalation_record=False,
        close_result=None,
    )
    if structured_blocked.status != lifecycle.FallbackResolutionStatus.ACCEPTED:
        raise AssertionError("structured blocker should satisfy structured-blocked gate acceptance")


def assert_helper_mirror_parity() -> None:
    source = HELPER_PATH.read_text(encoding="utf-8")
    mirror = MIRROR_HELPER_PATH.read_text(encoding="utf-8")
    if source != mirror:
        raise AssertionError("bootstrap helper must match root helper")


def main() -> int:
    lifecycle = load_lifecycle()
    assert_helper_mirror_parity()
    assert_timeout_records_abandoned_without_close(lifecycle)
    assert_result_shape_and_provenance(lifecycle)
    assert_fallback_policies(lifecycle)
    assert_requirement_reviewer_policy_context(lifecycle)
    assert_handle_wait_result_rejects_policy_context_mismatch(lifecycle)
    assert_replacement_and_late_result_paths(lifecycle)
    assert_partial_companion_and_resume_paths(lifecycle)
    assert_close_success_is_not_acceptance(lifecycle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
