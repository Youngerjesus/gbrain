from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable


class LifecycleState(str, Enum):
    STARTED = "started"
    WAIT_COMPLETED = "wait_completed"
    TIMED_OUT = "timed_out"
    STALE = "stale"
    INTERRUPTED = "interrupted"
    RESULTLESS = "resultless"
    ABANDONED = "abandoned"
    FALLBACK_RECORDED = "fallback_recorded"
    CLEANUP_PENDING = "cleanup_pending"
    CLEANUP_COMPLETED = "cleanup_completed"


class FallbackAction(str, Enum):
    PARENT_FALLBACK = "parent_fallback"
    REPLACEMENT_SUBAGENT = "replacement_subagent"
    STRUCTURED_BLOCKED = "structured_blocked"
    USER_ESCALATION = "user_escalation"


class CleanupStatus(str, Enum):
    NOT_NEEDED = "not_needed"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCEL_FAILED = "cancel_failed"
    CLEANUP_PENDING = "cleanup_pending"


class FallbackResolutionStatus(str, Enum):
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    ESCALATED = "escalated"
    DIAGNOSTIC = "diagnostic"


class LateResultStatus(str, Enum):
    QUARANTINED = "quarantined"
    IGNORED = "ignored"


class FallbackPolicyMismatch(ValueError):
    pass


@dataclass(frozen=True)
class FallbackPolicy:
    gate: str
    action: FallbackAction
    rationale: str


@dataclass(frozen=True)
class SubagentWaitResult:
    subagent_id: str
    timed_out: bool
    observed_status: Any
    artifact: Any
    wait_deadline_ms: int


@dataclass(frozen=True)
class LifecycleRecord:
    subagent_id: str
    gate: str
    requirement_id: str
    wait_deadline_ms: int
    observed_status: Any
    reason: str
    timestamp: str
    fallback_action: FallbackAction
    lifecycle_state: LifecycleState
    evidence_ref: str

    @classmethod
    def abandoned(
        cls,
        *,
        subagent_id: str,
        gate: str,
        requirement_id: str,
        wait_deadline_ms: int,
        observed_status: Any,
        reason: str,
        timestamp: str,
        fallback_action: FallbackAction,
        evidence_ref: str,
    ) -> "LifecycleRecord":
        return cls(
            subagent_id=subagent_id,
            gate=gate,
            requirement_id=requirement_id,
            wait_deadline_ms=wait_deadline_ms,
            observed_status=observed_status,
            reason=reason,
            timestamp=timestamp,
            fallback_action=fallback_action,
            lifecycle_state=LifecycleState.ABANDONED,
            evidence_ref=evidence_ref,
        )

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["fallback_action"] = self.fallback_action.value
        raw["lifecycle_state"] = self.lifecycle_state.value
        return raw


@dataclass(frozen=True)
class LifecycleDecision:
    record: LifecycleRecord
    fallback_action: FallbackAction
    usable_result: bool


@dataclass(frozen=True)
class FallbackResolution:
    status: FallbackResolutionStatus
    reason: str
    cleanup_visible: bool = False
    spawn_duplicate: bool = False


@dataclass(frozen=True)
class LateResultResolution:
    status: LateResultStatus
    reason: str


@dataclass(frozen=True)
class CloseResult:
    status: CleanupStatus


@dataclass(frozen=True)
class CompanionResult:
    lens: str
    usable: bool
    required: bool


@dataclass(frozen=True)
class ResumeState:
    lifecycle_state: LifecycleState
    deadline_expired: bool
    fallback_action: FallbackAction | None
    has_fallback_evidence: bool
    cleanup_status: CleanupStatus


def fallback_policies() -> dict[str, FallbackPolicy]:
    return {
        "requirement-clarifier-post-draft-review": FallbackPolicy(
            "requirement-clarifier-post-draft-review",
            FallbackAction.PARENT_FALLBACK,
            "Ordinary non-production reviewer unavailability may use explicit self-review fallback.",
        ),
        "context-loading": FallbackPolicy(
            "context-loading",
            FallbackAction.PARENT_FALLBACK,
            "Parent may inspect locally and record residual context risk.",
        ),
        "plan-design-review": FallbackPolicy(
            "plan-design-review",
            FallbackAction.STRUCTURED_BLOCKED,
            "Triggered UI planning review cannot be silently bypassed.",
        ),
        "plan-ux-review": FallbackPolicy(
            "plan-ux-review",
            FallbackAction.STRUCTURED_BLOCKED,
            "Triggered user experience planning review cannot be silently bypassed.",
        ),
        "plan-devex-review": FallbackPolicy(
            "plan-devex-review",
            FallbackAction.STRUCTURED_BLOCKED,
            "Triggered developer experience planning review cannot be silently bypassed.",
        ),
        "plan-eng-review": FallbackPolicy(
            "plan-eng-review",
            FallbackAction.STRUCTURED_BLOCKED,
            "Missing plan engineering evidence is not no-findings.",
        ),
        "scenario-brake": FallbackPolicy(
            "scenario-brake",
            FallbackAction.STRUCTURED_BLOCKED,
            "Missing scenario evidence is not no-findings.",
        ),
        "visual-qa-hardening": FallbackPolicy(
            "visual-qa-hardening",
            FallbackAction.STRUCTURED_BLOCKED,
            "UI-bearing review cannot be silently bypassed.",
        ),
        "ux-review": FallbackPolicy(
            "ux-review",
            FallbackAction.STRUCTURED_BLOCKED,
            "Triggered live user experience review cannot be silently bypassed.",
        ),
        "devex-review": FallbackPolicy(
            "devex-review",
            FallbackAction.STRUCTURED_BLOCKED,
            "Triggered live developer experience review cannot be silently bypassed.",
        ),
        "implementation-brake": FallbackPolicy(
            "implementation-brake",
            FallbackAction.STRUCTURED_BLOCKED,
            "Ship readiness cannot depend on a missing companion result.",
        ),
        "closeout": FallbackPolicy(
            "closeout",
            FallbackAction.PARENT_FALLBACK,
            "Cleanup-only handles must not block recorded gate evidence.",
        ),
    }


def select_fallback_policy(
    gate: str,
    *,
    requirement_context: dict[str, bool] | None = None,
) -> FallbackPolicy:
    policies = fallback_policies()
    if gate not in policies:
        raise FallbackPolicyMismatch(f"unknown fallback gate {gate}")
    policy = policies[gate]
    if gate != "requirement-clarifier-post-draft-review":
        return policy

    context = requirement_context or {}
    strict_requirement = any(
        context.get(key) is True
        for key in [
            "production_bound",
            "launch_bound",
            "mvp_bound",
            "irreversible_or_safety_critical",
        ]
    )
    if strict_requirement:
        return FallbackPolicy(
            gate,
            FallbackAction.STRUCTURED_BLOCKED,
            "Production, launch, MVP, irreversible, or safety-critical reviewer unavailability blocks acceptance.",
        )
    return policy


def assert_policy_action_matches(policy: FallbackPolicy, action: FallbackAction) -> None:
    if policy.action != action:
        raise FallbackPolicyMismatch(
            f"{policy.gate} configured {policy.action.value}, got {action.value}"
        )


def validate_gate_artifact(artifact: Any, result_context: dict[str, str]) -> bool:
    if not isinstance(artifact, dict):
        return False
    required = {
        "requirement_id",
        "gate",
        "lens",
        "lifecycle_record_id",
        "checkpoint_id",
        "artifact_path",
        "result",
    }
    if required - set(artifact):
        return False
    for key in ["requirement_id", "gate", "lens", "lifecycle_record_id", "checkpoint_id"]:
        if artifact.get(key) != result_context.get(key):
            return False
    if not isinstance(artifact.get("artifact_path"), str) or not artifact["artifact_path"]:
        return False
    expected_path = result_context.get("artifact_path")
    if not isinstance(expected_path, str) or not expected_path:
        return False
    if artifact.get("artifact_path") != expected_path:
        return False
    return isinstance(artifact.get("result"), dict)


def is_usable_result(
    wait_result: SubagentWaitResult,
    result_context: dict[str, str],
    result_validator: Callable[[Any, dict[str, str]], bool],
) -> bool:
    if wait_result.timed_out:
        return False
    status = wait_result.observed_status
    if not isinstance(status, dict) or not status:
        return False
    if status.get("stale") is True:
        return False
    if status.get("state") in {"interrupted", "turn_aborted", "shutdown"}:
        return False
    return result_validator(wait_result.artifact, result_context)


def _reason_for_no_result(wait_result: SubagentWaitResult) -> str:
    status = wait_result.observed_status
    if wait_result.timed_out:
        return "timeout"
    if isinstance(status, dict) and status.get("stale") is True:
        return "stale"
    if isinstance(status, dict) and status.get("state") in {"interrupted", "turn_aborted", "shutdown"}:
        return str(status["state"])
    return "no_usable_result"


def handle_wait_result(
    *,
    wait_result: SubagentWaitResult,
    requirement_id: str,
    gate: str,
    fallback_policy: FallbackPolicy,
    result_context: dict[str, str],
    result_validator: Callable[[Any, dict[str, str]], bool],
    now_iso: str,
    close_agent: Callable[[str], Any] | None = None,
) -> LifecycleDecision:
    if fallback_policy.gate != gate:
        raise FallbackPolicyMismatch(
            f"{gate} cannot use fallback policy for {fallback_policy.gate}"
        )
    if result_context.get("gate") != gate:
        raise FallbackPolicyMismatch(
            f"{gate} cannot validate artifact for context gate {result_context.get('gate')}"
        )
    if result_context.get("requirement_id") != requirement_id:
        raise FallbackPolicyMismatch(
            f"{gate} context requirement does not match {requirement_id}"
        )
    evidence_ref = result_context.get("evidence_ref")
    if not isinstance(evidence_ref, str) or not evidence_ref:
        raise FallbackPolicyMismatch(f"{gate} context missing durable evidence_ref")
    usable = is_usable_result(wait_result, result_context, result_validator)
    if usable:
        record = LifecycleRecord(
            subagent_id=wait_result.subagent_id,
            gate=gate,
            requirement_id=requirement_id,
            wait_deadline_ms=wait_result.wait_deadline_ms,
            observed_status=wait_result.observed_status,
            reason="usable_result",
            timestamp=now_iso,
            fallback_action=fallback_policy.action,
            lifecycle_state=LifecycleState.WAIT_COMPLETED,
            evidence_ref=evidence_ref,
        )
        return LifecycleDecision(record, fallback_policy.action, True)

    record = LifecycleRecord.abandoned(
        subagent_id=wait_result.subagent_id,
        gate=gate,
        requirement_id=requirement_id,
        wait_deadline_ms=wait_result.wait_deadline_ms,
        observed_status=wait_result.observed_status,
        reason=_reason_for_no_result(wait_result),
        timestamp=now_iso,
        fallback_action=fallback_policy.action,
        evidence_ref=evidence_ref,
    )
    return LifecycleDecision(record, fallback_policy.action, False)


def record_replacement_result(
    *,
    original_record: LifecycleRecord,
    replacement_result: SubagentWaitResult,
    result_context: dict[str, str],
    result_validator: Callable[[Any, dict[str, str]], bool],
) -> FallbackResolution:
    if original_record.lifecycle_state != LifecycleState.ABANDONED:
        return FallbackResolution(FallbackResolutionStatus.BLOCKED, "original_not_abandoned")
    if original_record.fallback_action != FallbackAction.REPLACEMENT_SUBAGENT:
        return FallbackResolution(FallbackResolutionStatus.BLOCKED, "replacement_not_allowed")
    if result_context.get("requirement_id") != original_record.requirement_id:
        return FallbackResolution(FallbackResolutionStatus.BLOCKED, "replacement_requirement_mismatch")
    if result_context.get("gate") != original_record.gate:
        return FallbackResolution(FallbackResolutionStatus.BLOCKED, "replacement_gate_mismatch")
    if is_usable_result(replacement_result, result_context, result_validator):
        return FallbackResolution(FallbackResolutionStatus.ACCEPTED, "replacement_result")
    return FallbackResolution(FallbackResolutionStatus.BLOCKED, "replacement_no_usable_result")


def record_replacement_unavailable(
    *,
    original_record: LifecycleRecord,
    reason: str,
) -> FallbackResolution:
    return FallbackResolution(
        FallbackResolutionStatus.ESCALATED,
        f"replacement_unavailable:{reason}",
    )


def handle_late_original_result(
    *,
    original_record: LifecycleRecord,
    accepted_resolution: FallbackResolution,
    late_result: SubagentWaitResult,
    result_context: dict[str, str],
    result_validator: Callable[[Any, dict[str, str]], bool],
) -> LateResultResolution:
    if accepted_resolution.status == FallbackResolutionStatus.ACCEPTED:
        return LateResultResolution(
            LateResultStatus.QUARANTINED,
            "late_original_quarantined",
        )
    if is_usable_result(late_result, result_context, result_validator):
        return LateResultResolution(LateResultStatus.QUARANTINED, "late_original_diagnostic")
    return LateResultResolution(LateResultStatus.IGNORED, "late_original_ignored")


def evaluate_companion_set(results: list[CompanionResult]) -> FallbackResolution:
    missing_required = [result.lens for result in results if result.required and not result.usable]
    if missing_required:
        return FallbackResolution(
            FallbackResolutionStatus.BLOCKED,
            "missing_required_companion:" + ",".join(sorted(missing_required)),
        )
    return FallbackResolution(FallbackResolutionStatus.ACCEPTED, "required_companions_usable")


def reconcile_resume_state(state: ResumeState) -> FallbackResolution:
    cleanup_visible = state.cleanup_status == CleanupStatus.CLEANUP_PENDING
    if state.lifecycle_state == LifecycleState.STARTED and state.deadline_expired:
        return FallbackResolution(
            FallbackResolutionStatus.BLOCKED,
            "expired_started_without_fallback",
            cleanup_visible=cleanup_visible,
            spawn_duplicate=False,
        )
    if state.lifecycle_state == LifecycleState.FALLBACK_RECORDED:
        if not state.has_fallback_evidence:
            return FallbackResolution(
                FallbackResolutionStatus.BLOCKED,
                "fallback_action_without_evidence",
                cleanup_visible=cleanup_visible,
                spawn_duplicate=False,
            )
        return FallbackResolution(
            FallbackResolutionStatus.ACCEPTED,
            "fallback_evidence_recorded",
            cleanup_visible=cleanup_visible,
            spawn_duplicate=False,
        )
    return FallbackResolution(
        FallbackResolutionStatus.BLOCKED,
        f"unhandled_resume_state:{state.lifecycle_state.value}",
        cleanup_visible=cleanup_visible,
        spawn_duplicate=False,
    )


def evaluate_gate_acceptance(
    *,
    fallback_action: FallbackAction,
    has_fallback_artifact: bool,
    has_replacement_result: bool,
    has_structured_blocker: bool,
    has_escalation_record: bool,
    close_result: CloseResult | None,
) -> FallbackResolution:
    cleanup_visible = (
        close_result is not None and close_result.status == CleanupStatus.CLEANUP_PENDING
    )
    accepted = False
    if fallback_action == FallbackAction.PARENT_FALLBACK:
        accepted = has_fallback_artifact or has_structured_blocker or has_escalation_record
    elif fallback_action == FallbackAction.REPLACEMENT_SUBAGENT:
        accepted = has_replacement_result or has_structured_blocker or has_escalation_record
    elif fallback_action == FallbackAction.STRUCTURED_BLOCKED:
        accepted = has_structured_blocker or has_escalation_record
    elif fallback_action == FallbackAction.USER_ESCALATION:
        accepted = has_escalation_record
    if accepted:
        return FallbackResolution(
            FallbackResolutionStatus.ACCEPTED,
            "gate_evidence_recorded",
            cleanup_visible=cleanup_visible,
        )
    return FallbackResolution(
        FallbackResolutionStatus.BLOCKED,
        "close_result_is_cleanup_only",
        cleanup_visible=cleanup_visible,
    )
