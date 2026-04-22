"""Support helpers for the session-resume command: data contract, cache, rendering."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...platform.coordination_snapshot_models import (
    CoordinationSnapshot,
)
from ...runtime.control_plane_read_model import (
    ControlPlaneReadModel,
    build_control_plane_read_model,
)
from ...runtime.authority_snapshot import (
    AuthoritySnapshot,
    build_authority_snapshot,
    summary_blockers_csv,
    summary_next_command,
)
from ...runtime.control_topology import derive_startup_control_truth
from ...runtime.review_state_parser import review_state_from_payload
from ...runtime.review_state_models import (
    PacketInboxState,
    ReviewCandidateRecord,
)
from ...runtime.reviewer_runtime_models import (
    has_active_remote_control_attachment,
    remote_control_attachment_from_mapping,
)
from ...runtime.control_plane_resolve import (
    load_git_state,
    load_sources,
    read_json_artifact,
)
from ...runtime.value_coercion import coerce_bool, coerce_string
from ...runtime.surface_provenance import (
    attach_surface_provenance,
    surface_provenance_from_object,
)
from ...time_utils import utc_timestamp
from . import session_resume_git as _session_resume_git
from .session_resume_packet import (
    SessionCachePacket,
    packet_from_mapping,
    try_cache_hit,
    write_cache,
)
from .session_resume_authority_payload import (
    build_session_resume_review_state_context,
)
from .session_resume_paths import (
    get_review_state_mtime,
    governance_interaction_mode,
    resolve_source_paths,
)
from .session_resume_source_helpers import (
    AuthorityPayloadInputs,
    _load_session_resume_sources_and_model,
    _nested_dict,
    _str_field,
    build_authority_payload as _build_authority_payload,
    extract_attention_payload as _extract_attention_payload,
    extract_coordination as _extract_coordination,
    extract_current_session as _extract_current_session,
    extract_head_at_push_time as _extract_head_at_push_time,
    extract_recovery_assessment_payload as _extract_recovery_assessment_payload,
    extract_review_candidate as _extract_review_candidate,
    resolve_open_findings as _resolve_open_findings,
)
if TYPE_CHECKING:
    from ...runtime.project_governance import ProjectGovernance
    from ...runtime.review_state_models import ReviewState

current_head = _session_resume_git.current_head
_git_changed_paths = _session_resume_git._git_changed_paths
_git_commit_range_paths = _session_resume_git._git_commit_range_paths

def resolve_guard_bundle(
    repo_root: Path,
    changed_paths: list[str] | None,
    *,
    head_sha: str = "",
    last_reviewed_sha: str = "",
) -> str:
    _session_resume_git._git_changed_paths = _git_changed_paths
    _session_resume_git._git_commit_range_paths = _git_commit_range_paths
    return _session_resume_git.resolve_guard_bundle(
        repo_root,
        changed_paths,
        head_sha=head_sha,
        last_reviewed_sha=last_reviewed_sha,
    )


def _project_packet_next_command_for_role(*, role: str, command: str) -> str:
    """Return the role-visible next command for session-resume packet fields."""
    return str(command or "").strip()


@dataclass(frozen=True, slots=True)
class SessionCachePacketFields:
    ack_state: str
    blockers: str
    current_instruction: str
    guard_bundle: str
    head_at_push_time: str
    instruction_revision: str
    key_rules: tuple[str, ...]
    last_reviewed_sha: str
    next_cmd: str
    observation_status: str
    open_findings: str
    review_state_mtime: float
    top_blocker: str
    visible_next_cmd: str


@dataclass(frozen=True, slots=True)
class SessionCachePacketBuildContext:
    role: str
    head_sha: str
    typed_review_state: "ReviewState | None"
    coordination: CoordinationSnapshot | None
    authority_snapshot: AuthoritySnapshot | None
    review_candidate: ReviewCandidateRecord | None
    attention_payload: dict[str, Any]
    packet_inbox: PacketInboxState | None
    fields: SessionCachePacketFields


def _build_session_cache_packet(
    *,
    model: ControlPlaneReadModel,
    build_context: SessionCachePacketBuildContext,
) -> SessionCachePacket:
    fields = build_context.fields
    typed_review_state = build_context.typed_review_state
    snapshot_id = getattr(typed_review_state, "snapshot_id", "") if typed_review_state is not None else ""
    zref = getattr(typed_review_state, "zref", "") if typed_review_state is not None else ""
    provenance = (
        surface_provenance_from_object(typed_review_state)
        if typed_review_state is not None
        else None
    )
    visible_next_cmd = fields.visible_next_cmd
    next_cmd = fields.next_cmd
    return SessionCachePacket(
        generated_at_utc=utc_timestamp(),
        role=build_context.role,
        branch=model.branch,
        head_sha=build_context.head_sha,
        snapshot_id=snapshot_id,
        zref=zref,
        advisory_action=model.next_action,
        advisory_reason=fields.top_blocker,
        blockers=fields.blockers,
        interaction_mode=model.operator_interaction_mode,
        current_instruction=fields.current_instruction,
        instruction_revision=fields.instruction_revision,
        ack_state=fields.ack_state,
        open_findings=fields.open_findings,
        last_guard_ok=model.last_guard_ok,
        last_reviewed_sha=fields.last_reviewed_sha,
        review_state_mtime=fields.review_state_mtime,
        done_summary=next_cmd,
        next_action=visible_next_cmd,
        key_rules=fields.key_rules,
        head_at_push_time=fields.head_at_push_time,
        operator_interaction_mode=model.operator_interaction_mode,
        resolved_phase=model.resolved_phase,
        next_guard_bundle=fields.guard_bundle,
        next_recommended_command=visible_next_cmd,
        reviewer_observation_status=fields.observation_status,
        review_candidate=build_context.review_candidate,
        remote_control_attachment=getattr(model, "remote_control_attachment", None),
        coordination=build_context.coordination,
        authority_snapshot=build_context.authority_snapshot,
        attention_status=_str_field(build_context.attention_payload, "status") or model.attention_status,
        attention_summary=_str_field(build_context.attention_payload, "summary") or model.attention_summary,
        attention_revision=(
            build_context.packet_inbox.attention_revision
            if build_context.packet_inbox is not None
            else ""
        ),
        packet_inbox=build_context.packet_inbox,
        provenance=provenance,
    )


def build_from_sources(
    repo_root: Path,
    *,
    role: str,
    head_sha: str,
    governance: "ProjectGovernance | None" = None,
    read_model_override: "ControlPlaneReadModel | None" = None,
    sources_override: dict[str, Any] | None = None,
    changed_paths: list[str] | None = None,
    review_state: "ReviewState | None" = None,
) -> SessionCachePacket:
    """Build a fresh packet from the governed read model and shared sources."""
    sources, model = _load_session_resume_sources_and_model(
        repo_root,
        head_sha=head_sha,
        governance=governance,
        review_state=review_state,
        read_model_override=read_model_override,
        sources_override=sources_override,
    )
    session = _extract_current_session(sources)
    receipt = sources.get("receipt")
    current_instruction = _str_field(session, "current_instruction")
    instruction_revision = _str_field(session, "current_instruction_revision")
    ack_state = _str_field(session, "implementer_ack_state") or "missing"
    rs_mtime = get_review_state_mtime(repo_root, governance=governance)
    push_governance, safe_to_continue, checkpoint_required = _push_gate_state(
        governance=governance,
        receipt=receipt,
    )
    key_rules = distill_key_rules(
        safe_to_continue=safe_to_continue,
        checkpoint_required=checkpoint_required,
        ack_current=(ack_state == "current"),
        review_gate_allows_push=model.review_accepted,
        last_guard_ok=model.last_guard_ok,
    )
    last_reviewed_sha = head_at_push_time = _extract_head_at_push_time(sources)
    review_candidate = _extract_review_candidate(sources)
    guard_bundle = resolve_guard_bundle(
        repo_root, changed_paths,
        head_sha=head_sha, last_reviewed_sha=last_reviewed_sha,
    )
    obs_status = model.reviewer_observation.status if model.reviewer_observation is not None else ""
    coordination = model.coordination or _extract_coordination(
        sources,
        repo_root=repo_root,
        governance=governance,
    )
    review_state_payload = sources.get("review_state") if isinstance(sources.get("review_state"), dict) else {}
    typed_review_state = review_state or review_state_from_payload(review_state_payload)
    attention_payload = _extract_attention_payload(
        sources,
        default_status=model.attention_status,
        default_summary=model.attention_summary,
    )
    recovery_payload = _extract_recovery_assessment_payload(sources)
    recovery_command = _str_field(_nested_dict(recovery_payload, "decision"), "command")
    attention_command = _str_field(attention_payload, "recommended_command")
    next_cmd = recovery_command or attention_command or model.next_command or model.next_action
    review_state_context = build_session_resume_review_state_context(
        review_state_payload,
        fallback_open_findings=_str_field(session, "open_findings"),
        role=role,
    )
    packet_inbox = review_state_context.packet_inbox
    open_findings = _resolve_open_findings(
        repo_root=repo_root,
        governance=governance,
        fallback=review_state_context.open_findings,
    )
    observed_control_topology, implementation_permission = derive_startup_control_truth(
        typed_review_state
    ) if typed_review_state is not None else ("", "")
    authority_payload = _build_authority_payload(
        model=model,
        payload_inputs=AuthorityPayloadInputs(
            current_instruction=current_instruction,
            instruction_revision=instruction_revision,
            ack_state=ack_state,
            observed_control_topology=observed_control_topology,
            implementation_permission=implementation_permission,
            attention_payload=attention_payload,
            recovery_payload=recovery_payload,
            coordination=coordination,
            packet_inbox=packet_inbox,
            next_command=next_cmd,
            push_governance=push_governance,
        ),
    )
    _attach_review_state_provenance(authority_payload, typed_review_state)
    shared_blockers = summary_blockers_csv(authority_payload)
    top_blocker = model.top_blocker
    if top_blocker == _str_field(session, "open_findings"):
        top_blocker = open_findings
    blockers = _resolve_blockers(receipt, top_blocker, shared_blockers)
    explicit_runtime_command = bool(recovery_command or attention_command)
    if shared_blockers != "none" and not explicit_runtime_command:
        authority_payload["next_command"] = summary_next_command(authority_payload)
    authority_snapshot = build_authority_snapshot(
        authority_payload,
        caller_role=role,
    )
    packet_fields = SessionCachePacketFields(
        ack_state=ack_state,
        blockers=blockers,
        current_instruction=current_instruction,
        guard_bundle=guard_bundle,
        head_at_push_time=head_at_push_time,
        instruction_revision=instruction_revision,
        key_rules=key_rules,
        last_reviewed_sha=last_reviewed_sha,
        next_cmd=next_cmd,
        observation_status=obs_status,
        open_findings=open_findings,
        review_state_mtime=rs_mtime,
        top_blocker=top_blocker,
        visible_next_cmd=_project_packet_next_command_for_role(
            role=role,
            command=next_cmd,
        ),
    )
    return _build_session_cache_packet(
        model=model,
        build_context=SessionCachePacketBuildContext(
            role=role,
            head_sha=head_sha,
            typed_review_state=typed_review_state,
            coordination=coordination,
            authority_snapshot=authority_snapshot,
            review_candidate=review_candidate,
            attention_payload=attention_payload,
            packet_inbox=packet_inbox,
            fields=packet_fields,
        ),
    )


def _attach_review_state_provenance(
    payload: dict[str, Any],
    typed_review_state: "ReviewState | None",
) -> None:
    if typed_review_state is None:
        return
    payload.update(
        attach_surface_provenance(
            payload,
            provenance=surface_provenance_from_object(typed_review_state),
        )
    )

def _push_gate_state(
    *,
    governance: "ProjectGovernance | None",
    receipt: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool, bool]:
    """Return minimal governance payload plus the shared checkpoint booleans."""
    push_enforcement = getattr(governance, "push_enforcement", None)
    if push_enforcement is not None:
        push_payload = asdict(push_enforcement)
    elif receipt is not None and (
        "checkpoint_required" in receipt or "safe_to_continue_editing" in receipt
    ):
        push_payload = {
            "checkpoint_required": coerce_bool(receipt.get("checkpoint_required")),
            "safe_to_continue_editing": (
                True if receipt.get("safe_to_continue_editing") is None
                else coerce_bool(receipt.get("safe_to_continue_editing"))
            ),
            "checkpoint_reason": _str_field(receipt, "checkpoint_reason"),
        }
    else:
        return {}, True, False
    return (
        {"push_enforcement": push_payload},
        True
        if push_payload.get("safe_to_continue_editing") is None
        else coerce_bool(push_payload.get("safe_to_continue_editing")),
        coerce_bool(push_payload.get("checkpoint_required")),
    )

def compute_blockers(
    *,
    checkpoint_required: bool,
    safe_to_continue: bool,
    authority_ok: bool,
) -> str:
    parts: list[str] = []
    if not authority_ok:
        parts.append("startup_authority")
    if checkpoint_required:
        parts.append("checkpoint_required")
    if not safe_to_continue:
        parts.append("continuation_blocked")
    return ",".join(parts) if parts else "none"

def derive_interaction_mode(
    compact: dict[str, Any] | None,
    *,
    governance: "ProjectGovernance | None" = None,
) -> str:
    """Derive interaction mode, preferring governance BridgeConfig over compact."""
    gov_mode = governance_interaction_mode(governance)
    if gov_mode:
        return gov_mode
    if compact is None:
        return "unresolved"
    reviewer_runtime = _nested_dict(compact, "reviewer_runtime")
    if has_active_remote_control_attachment(
        remote_control_attachment_from_mapping(
            reviewer_runtime.get("remote_control_attachment")
            if reviewer_runtime
            else None
        )
    ):
        return "remote_control"
    collab = _nested_dict(compact, "collaboration")
    if not collab:
        return "unresolved"
    reviewer_mode = _str_field(collab, "reviewer_mode")
    if reviewer_mode == "active_dual_agent":
        return "dual_agent"
    if reviewer_mode == "single_agent":
        return "single_agent"
    return "unresolved"

def derive_next_action(receipt: dict[str, Any] | None, blockers: str) -> str:
    if receipt is None:
        return "run startup-context to generate receipt"
    if blockers != "none":
        cmd = _str_field(receipt, "push_next_step_command")
        if cmd:
            return cmd
        return "resolve blockers, then rerun startup-context"
    push_action = _str_field(receipt, "push_action")
    if push_action == "run_devctl_push":
        return "python3 dev/scripts/devctl.py push --execute"
    return "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"

def distill_key_rules(
    *,
    safe_to_continue: bool,
    checkpoint_required: bool,
    ack_current: bool,
    review_gate_allows_push: bool,
    last_guard_ok: bool,
) -> tuple[str, ...]:
    rules: list[str] = [
        f"safe_to_continue={safe_to_continue}",
        f"checkpoint_required={checkpoint_required}",
        f"ack_current={ack_current}",
        f"review_gate_allows_push={review_gate_allows_push}",
        f"last_guard_ok={last_guard_ok}",
    ]
    return tuple(rules)

from .session_resume_render import render_bootstrap, render_markdown, render_summary  # noqa: F401

def _resolve_blockers(
    receipt: dict[str, Any] | None,
    top_blocker: str,
    shared_blockers: str = "none",
) -> str:
    """Return the effective blocker string, failing closed without a receipt."""
    if receipt is None:
        return "bootstrap_required"
    blockers: list[str] = []
    for raw in (top_blocker, shared_blockers):
        for token in str(raw or "").split(","):
            blocker = token.strip()
            if not blocker or blocker == "none" or blocker in blockers:
                continue
            blockers.append(blocker)
    return ",".join(blockers) if blockers else "none"
