"""Shared runtime ControlState models for mobile/review/operator surfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any, TypedDict

from .value_coercion import (
    coerce_int as _int,
    coerce_mapping as _mapping,
    coerce_string as _string,
    coerce_string_items as _string_rows,
)


@dataclass(frozen=True, slots=True)
class ApprovalPolicyState:
    mode: str
    summary: str

@dataclass(frozen=True, slots=True)
class ControlStateSources:
    phone_input_path: str
    review_channel_path: str
    bridge_path: str
    review_status_dir: str


@dataclass(frozen=True, slots=True)
class ReviewAgentState:
    agent_id: str
    status: str
    role: str


@dataclass(frozen=True, slots=True)
class ReviewBridgeState:
    overall_state: str
    codex_poll_state: str
    last_codex_poll_utc: str
    last_worktree_hash: str
    pending_total: int
    current_instruction: str
    open_findings: str
    claude_status: str
    claude_ack: str


@dataclass(frozen=True, slots=True)
class ActiveRunState:
    plan_id: str
    controller_run_id: str
    phase: str
    reason: str
    risk: str
    unresolved_count: int
    pending_total: int
    mode_effective: str
    review_bridge_state: str
    codex_poll_state: str
    current_instruction: str
    open_findings: str
    next_actions: tuple[str, ...]
    latest_working_branch: str
    source_run_url: str


@dataclass(frozen=True, slots=True)
class ControlStateContext:
    approval_policy: Mapping[str, object] | None = None
    sources: Mapping[str, object] | None = None
    timestamp: str = ""
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ControlState:
    schema_version: int
    contract_id: str
    command: str
    timestamp: str
    approvals: ApprovalPolicyState
    active_runs: tuple[ActiveRunState, ...]
    review_bridge: ReviewBridgeState
    agents: tuple[ReviewAgentState, ...]
    sources: ControlStateSources
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def primary_run(self) -> ActiveRunState | None:
        return self.active_runs[0] if self.active_runs else None

    def agent_status(self, agent_id: str) -> str:
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent.status
        return "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ControllerFields(TypedDict):
    """Typed runtime-relevant fields extracted from a controller payload."""

    plan_id: str | None
    controller_run_id: str | None
    phase: str
    reason: str
    risk: str
    unresolved_count: int
    mode_effective: str
    next_actions: list[str]
    latest_working_branch: str | None
    source_run_url: str | None


def _flatten_controller_fields(payload: Mapping[str, object]) -> ControllerFields:
    """Extract runtime-relevant fields from a controller payload.

    This avoids importing phone_status_views (frontend-owned) into the runtime
    layer.  Only the fields that build_control_state actually reads are flattened.
    """
    controller = _mapping(payload.get("controller"))
    loop_section = _mapping(payload.get("loop"))
    source_run = _mapping(payload.get("source_run"))
    next_raw = payload.get("next_actions")
    next_actions: list[str] = []
    if isinstance(next_raw, (list, tuple)):
        next_actions = [str(v).strip() for v in next_raw if str(v).strip()][:5]
    return ControllerFields(
        plan_id=_string(controller.get("plan_id")),
        controller_run_id=_string(controller.get("controller_run_id")),
        phase=_string(payload.get("phase")) or "unknown",
        reason=_string(payload.get("reason")) or "unknown",
        risk=_string(loop_section.get("risk")) or "unknown",
        unresolved_count=_int(loop_section.get("unresolved_count")),
        mode_effective=_string(controller.get("mode_effective")) or "unknown",
        next_actions=next_actions,
        latest_working_branch=_string(controller.get("latest_working_branch")),
        source_run_url=_string(source_run.get("run_url")),
    )


def build_control_state(
    *,
    controller_payload: Mapping[str, object],
    review_payload: Mapping[str, object],
    context: ControlStateContext | None = None,
) -> ControlState:
    resolved_context = context or ControlStateContext()
    compact = _flatten_controller_fields(controller_payload)
    review_state = _mapping(review_payload.get("review_state"))
    if not review_state and any(
        key in review_payload
        for key in ("review", "queue", "bridge", "packets", "agents")
    ):
        review_state = review_payload
    review_queue = _mapping(review_state.get("queue"))
    review_bridge = _mapping(review_state.get("bridge"))
    review_liveness = (
        _mapping(review_payload.get("bridge_liveness"))
        or _mapping(review_state.get("bridge_liveness"))
    )
    approval = _mapping(resolved_context.approval_policy)
    resolved_sources = _mapping(resolved_context.sources)
    bridge_state = ReviewBridgeState(
        overall_state=_string(review_liveness.get("overall_state")) or "unknown",
        codex_poll_state=_string(review_liveness.get("codex_poll_state")) or "unknown",
        last_codex_poll_utc=_string(review_bridge.get("last_codex_poll_utc")),
        last_worktree_hash=_string(review_bridge.get("last_worktree_hash")),
        pending_total=_int(review_queue.get("pending_total")),
        current_instruction=_string(review_bridge.get("current_instruction")),
        open_findings=_string(review_bridge.get("open_findings")),
        claude_status=_string(review_bridge.get("claude_status")),
        claude_ack=_string(review_bridge.get("claude_ack")),
    )
    active_run = ActiveRunState(
        plan_id=(
            _string(compact.get("plan_id"))
            or _string(_mapping(review_state.get("review")).get("plan_id"))
        ),
        controller_run_id=_string(compact.get("controller_run_id")),
        phase=_string(compact.get("phase")) or "unknown",
        reason=_string(compact.get("reason")) or "unknown",
        risk=_string(compact.get("risk")) or "unknown",
        unresolved_count=_int(compact.get("unresolved_count")),
        pending_total=bridge_state.pending_total,
        mode_effective=_string(compact.get("mode_effective")) or "unknown",
        review_bridge_state=bridge_state.overall_state,
        codex_poll_state=bridge_state.codex_poll_state,
        current_instruction=bridge_state.current_instruction,
        open_findings=bridge_state.open_findings,
        next_actions=_string_rows(compact.get("next_actions")),
        latest_working_branch=_string(compact.get("latest_working_branch")),
        source_run_url=_string(compact.get("source_run_url")),
    )
    return ControlState(
        schema_version=1,
        contract_id="ControlState",
        command="mobile-status",
        timestamp=resolved_context.timestamp,
        approvals=ApprovalPolicyState(
            mode=_string(approval.get("mode")) or "unknown",
            summary=_string(approval.get("summary")),
        ),
        active_runs=(active_run,),
        review_bridge=bridge_state,
        agents=_parse_agents(review_state.get("agents")),
        sources=ControlStateSources(
            phone_input_path=_string(resolved_sources.get("phone_input_path")),
            review_channel_path=_string(resolved_sources.get("review_channel_path")),
            bridge_path=_string(resolved_sources.get("bridge_path")),
            review_status_dir=_string(resolved_sources.get("review_status_dir")),
        ),
        warnings=resolved_context.warnings,
        errors=resolved_context.errors,
    )


def control_state_from_payload(payload: Mapping[str, object]) -> ControlState | None:
    explicit_state = _mapping(payload.get("control_state"))
    if explicit_state:
        return control_state_from_mapping(explicit_state)
    if "controller_payload" not in payload and "review_payload" not in payload:
        return None
    return build_control_state(
        controller_payload=_mapping(payload.get("controller_payload")),
        review_payload=_mapping(payload.get("review_payload")),
        context=ControlStateContext(
            approval_policy=_mapping(payload.get("approval_policy")),
            sources=_mapping(payload.get("sources")),
            timestamp=_string(payload.get("timestamp")),
            warnings=_string_rows(payload.get("warnings")),
            errors=_string_rows(payload.get("errors")),
        ),
    )


def control_state_from_mapping(payload: Mapping[str, object]) -> ControlState:
    approvals = _mapping(payload.get("approvals"))
    sources = _mapping(payload.get("sources"))
    return ControlState(
        schema_version=_int(payload.get("schema_version")) or 1,
        contract_id=_string(payload.get("contract_id")) or "ControlState",
        command=_string(payload.get("command")) or "mobile-status",
        timestamp=_string(payload.get("timestamp")),
        approvals=ApprovalPolicyState(
            mode=_string(approvals.get("mode")) or "unknown",
            summary=_string(approvals.get("summary")),
        ),
        active_runs=active_runs_from_mapping(payload.get("active_runs")),
        review_bridge=review_bridge_from_mapping(payload.get("review_bridge")),
        agents=_parse_agents(payload.get("agents")),
        sources=ControlStateSources(
            phone_input_path=_string(sources.get("phone_input_path")),
            review_channel_path=_string(sources.get("review_channel_path")),
            bridge_path=_string(sources.get("bridge_path")),
            review_status_dir=_string(sources.get("review_status_dir")),
        ),
        warnings=_string_rows(payload.get("warnings")),
        errors=_string_rows(payload.get("errors")),
    )


def active_runs_from_mapping(value: object) -> tuple[ActiveRunState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    rows: list[ActiveRunState] = []
    for row in value:
        mapping = _mapping(row)
        rows.append(
            ActiveRunState(
                plan_id=_string(mapping.get("plan_id")),
                controller_run_id=_string(mapping.get("controller_run_id")),
                phase=_string(mapping.get("phase")) or "unknown",
                reason=_string(mapping.get("reason")) or "unknown",
                risk=_string(mapping.get("risk")) or "unknown",
                unresolved_count=_int(mapping.get("unresolved_count")),
                pending_total=_int(mapping.get("pending_total")),
                mode_effective=_string(mapping.get("mode_effective")) or "unknown",
                review_bridge_state=_string(mapping.get("review_bridge_state"))
                or "unknown",
                codex_poll_state=_string(mapping.get("codex_poll_state")) or "unknown",
                current_instruction=_string(mapping.get("current_instruction")),
                open_findings=_string(mapping.get("open_findings")),
                next_actions=_string_rows(mapping.get("next_actions")),
                latest_working_branch=_string(mapping.get("latest_working_branch")),
                source_run_url=_string(mapping.get("source_run_url")),
            )
        )
    return tuple(rows)


def review_bridge_from_mapping(value: object) -> ReviewBridgeState:
    mapping = _mapping(value)
    return ReviewBridgeState(
        overall_state=_string(mapping.get("overall_state")) or "unknown",
        codex_poll_state=_string(mapping.get("codex_poll_state")) or "unknown",
        last_codex_poll_utc=_string(mapping.get("last_codex_poll_utc")),
        last_worktree_hash=_string(mapping.get("last_worktree_hash")),
        pending_total=_int(mapping.get("pending_total")),
        current_instruction=_string(mapping.get("current_instruction")),
        open_findings=_string(mapping.get("open_findings")),
        claude_status=_string(mapping.get("claude_status")),
        claude_ack=_string(mapping.get("claude_ack")),
    )


def _parse_agents(value: object) -> tuple[ReviewAgentState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    agents: list[ReviewAgentState] = []
    for row in value:
        mapping = _mapping(row)
        agent_id = _string(mapping.get("agent_id"))
        if not agent_id:
            continue
        agents.append(
            ReviewAgentState(
                agent_id=agent_id,
                status=_string(mapping.get("status")) or "unknown",
                role=_string(mapping.get("role")) or "unknown",
            )
        )
    return tuple(agents)
