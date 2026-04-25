"""Support helpers for the session-resume command: data contract, cache, rendering."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...platform.connectivity_registry import build_connectivity_registry_summary
from ...runtime.authority_snapshot import (
    build_authority_snapshot,
    summary_blockers_csv,
    summary_next_command,
)
from ...runtime.control_plane_read_model import (
    ControlPlaneReadModel,
    build_control_plane_read_model,
)
from ...runtime.control_plane_resolve import (
    load_git_state,
    load_sources,
    read_json_artifact,
)
from ...runtime.control_topology import derive_startup_control_truth
from ...runtime.review_state_parser import review_state_from_payload
from ...runtime.reviewer_runtime_models import (
    has_active_remote_control_attachment,
    remote_control_attachment_from_mapping,
)
from ...runtime.surface_provenance import (
    attach_surface_provenance,
    surface_provenance_from_object,
)
from ...runtime.value_coercion import coerce_bool, coerce_string
from . import session_resume_git as _session_resume_git
from .session_resume_authority_payload import build_session_resume_review_state_context
from .session_resume_cache_packet_builder import (
    SessionCachePacketBuildContext,
    SessionCachePacketFields,
    build_session_cache_packet,
)
from .session_resume_packet import (
    SessionCachePacket,
    packet_from_mapping,
    try_cache_hit,
    write_cache,
)
from .session_resume_paths import (
    get_review_state_mtime,
    governance_interaction_mode,
    resolve_source_paths,
)
from .session_resume_role_projection import project_packet_next_command_for_role
from .session_resume_source_helpers import (
    AuthorityPayloadInputs,
    _load_session_resume_sources_and_model,
    _nested_dict,
    _str_field,
)
from .session_resume_source_helpers import (
    build_authority_payload as _build_authority_payload,
)
from .session_resume_source_helpers import (
    extract_attention_payload as _extract_attention_payload,
)
from .session_resume_source_helpers import extract_coordination as _extract_coordination
from .session_resume_source_helpers import (
    extract_current_session as _extract_current_session,
)
from .session_resume_source_helpers import (
    extract_head_at_push_time as _extract_head_at_push_time,
)
from .session_resume_source_helpers import (
    extract_recovery_assessment_payload as _extract_recovery_assessment_payload,
)
from .session_resume_source_helpers import (
    extract_review_candidate as _extract_review_candidate,
)
from .session_resume_source_helpers import (
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
        repo_root,
        changed_paths,
        head_sha=head_sha,
        last_reviewed_sha=last_reviewed_sha,
    )
    obs_status = (
        model.reviewer_observation.status
        if model.reviewer_observation is not None
        else ""
    )
    coordination = model.coordination or _extract_coordination(
        sources,
        repo_root=repo_root,
        governance=governance,
    )
    review_state_payload = (
        sources.get("review_state")
        if isinstance(sources.get("review_state"), dict)
        else {}
    )
    typed_review_state = review_state or review_state_from_payload(review_state_payload)
    attention_payload = _extract_attention_payload(
        sources,
        default_status=model.attention_status,
        default_summary=model.attention_summary,
    )
    recovery_payload = _extract_recovery_assessment_payload(sources)
    recovery_command = _str_field(_nested_dict(recovery_payload, "decision"), "command")
    attention_command = _str_field(attention_payload, "recommended_command")
    next_cmd = (
        recovery_command or attention_command or model.next_command or model.next_action
    )
    review_state_context = build_session_resume_review_state_context(
        review_state_payload,
        fallback_open_findings=_str_field(session, "open_findings"),
        role=role,
    )
    packet_inbox = review_state_context.packet_inbox
    connectivity_registry = _session_connectivity_registry(repo_root)
    key_surfaces = _session_key_surfaces(governance)
    open_findings = _resolve_open_findings(
        repo_root=repo_root,
        governance=governance,
        fallback=review_state_context.open_findings,
    )
    observed_control_topology, implementation_permission = (
        derive_startup_control_truth(typed_review_state)
        if typed_review_state is not None
        else ("", "")
    )
    collaboration_payload = _collaboration_payload_from_review_state(
        typed_review_state,
        review_state_payload,
    )
    visible_next_cmd = project_packet_next_command_for_role(
        role=role,
        command=next_cmd,
    )
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
            next_command=visible_next_cmd,
            push_governance=push_governance,
            collaboration=collaboration_payload,
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
    visible_next_cmd = project_packet_next_command_for_role(
        role=role,
        command=str(authority_payload.get("next_command") or visible_next_cmd),
    )
    authority_payload["next_command"] = visible_next_cmd
    authority_snapshot = build_authority_snapshot(
        authority_payload,
        caller_role=role,
    )
    packet_fields = _packet_fields_from_context(locals())
    return build_session_cache_packet(
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
            connectivity_registry=connectivity_registry,
            key_surfaces=key_surfaces,
            fields=packet_fields,
        ),
    )


def _session_key_surfaces(governance: "ProjectGovernance | None") -> tuple[str, ...]:
    if governance is None:
        return ()
    surfaces: list[str] = []
    for entry in governance.doc_registry.entries:
        if entry.artifact_role != "connectivity_index":
            continue
        if entry.consumer_scope and entry.consumer_scope != "startup_default":
            continue
        if entry.path and entry.path not in surfaces:
            surfaces.append(entry.path)
    return tuple(surfaces)


def _session_connectivity_registry(repo_root: Path) -> dict[str, object]:
    return build_connectivity_registry_summary(repo_root=repo_root).to_dict()


def _packet_fields_from_context(context: dict[str, Any]) -> SessionCachePacketFields:
    return SessionCachePacketFields(
        ack_state=str(context["ack_state"]),
        blockers=str(context["blockers"]),
        current_instruction=str(context["current_instruction"]),
        guard_bundle=str(context["guard_bundle"]),
        head_at_push_time=str(context["head_at_push_time"]),
        instruction_revision=str(context["instruction_revision"]),
        key_rules=tuple(context["key_rules"]),
        last_reviewed_sha=str(context["last_reviewed_sha"]),
        next_cmd=str(context["next_cmd"]),
        observation_status=str(context["obs_status"]),
        open_findings=str(context["open_findings"]),
        review_state_mtime=float(context["rs_mtime"]),
        top_blocker=str(context["top_blocker"]),
        visible_next_cmd=str(context["visible_next_cmd"]),
    )


def _collaboration_payload_from_review_state(
    typed_review_state: object | None,
    review_state_payload: dict[str, object],
) -> dict[str, object]:
    if typed_review_state is None:
        return {}
    collaboration = getattr(typed_review_state, "collaboration", None)
    if collaboration is not None:
        return asdict(collaboration)
    payload_collaboration = review_state_payload.get("collaboration")
    if isinstance(payload_collaboration, dict):
        return dict(payload_collaboration)
    to_dict = getattr(typed_review_state, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, dict) and isinstance(payload.get("collaboration"), dict):
            return dict(payload["collaboration"])
    return {}


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
                True
                if receipt.get("safe_to_continue_editing") is None
                else coerce_bool(receipt.get("safe_to_continue_editing"))
            ),
            "checkpoint_reason": _str_field(receipt, "checkpoint_reason"),
        }
    else:
        return {}, True, False
    return (
        {"push_enforcement": push_payload},
        (
            True
            if push_payload.get("safe_to_continue_editing") is None
            else coerce_bool(push_payload.get("safe_to_continue_editing"))
        ),
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


from .session_resume_render import render_bootstrap  # noqa: F401
from .session_resume_render import (
    render_markdown,
    render_summary,
)


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
