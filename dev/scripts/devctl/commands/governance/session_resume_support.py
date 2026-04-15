"""Support helpers for the session-resume command: data contract, cache, rendering."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...platform.coordination_snapshot_models import (
    CoordinationSnapshot,
    coordination_snapshot_from_mapping,
)
from ...runtime.control_plane_read_model import (
    ControlPlaneReadModel,
    build_control_plane_read_model,
)
from ...runtime.authority_snapshot import (
    AuthoritySnapshot,
    authority_snapshot_from_mapping,
    build_authority_snapshot,
    summary_blockers_csv,
    summary_next_command,
)
from ...runtime.control_topology import derive_startup_control_truth
from ...runtime.review_state_parser import review_state_from_payload
from ...runtime.review_state_models import (
    packet_inbox_from_mapping,
    PacketInboxState,
    ReviewCandidateRecord,
    review_candidate_from_mapping,
)
from ...runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    has_active_remote_control_attachment,
    remote_control_attachment_from_mapping,
)
from ...runtime.control_plane_resolve import (
    load_git_state,
    load_sources,
    read_json_artifact,
)
from ...runtime.value_coercion import coerce_bool, coerce_string
from ...runtime.work_intake_models import SessionContinuityState
from ...time_utils import utc_timestamp
from . import session_resume_git as _session_resume_git
from .session_resume_authority_payload import (
    build_session_resume_review_state_context,
    SessionResumeAuthorityPayload,
    SessionResumeCurrentSessionPayload,
    SessionResumePacketInboxPayload,
)
from .session_resume_paths import (
    get_review_state_mtime,
    governance_interaction_mode,
    resolve_source_paths,
)
if TYPE_CHECKING:
    from ...runtime.project_governance import ProjectGovernance
    from ...runtime.review_state_models import ReviewState

SESSION_CACHE_RELATIVE_DIR = Path("dev/reports/session_cache/latest")
SESSION_CACHE_FILENAME = "cache.json"

# Typed continuity states that invalidate a cached session packet even when
# head/role/mtime all match. `alignment_status` values outside this set
# (for example `aligned`, `scope_aligned`, `instruction_aligned`) leave the
# cache intact. Keep this set in sync with
# ``runtime.work_intake_continuity.build_continuity`` outputs.
_STALE_CONTINUITY_STATUSES: frozenset[str] = frozenset(
    {"needs_review", "plan_only", "review_only", "missing"}
)

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


@dataclass(frozen=True, slots=True)  # noqa: too-many-instance-attributes
class SessionCachePacket:
    """Compact session state replacing full bootstrap output."""

    schema_version: int = 3
    contract_id: str = "SessionCachePacket"
    generated_at_utc: str = ""
    role: str = "implementer"
    branch: str = ""
    head_sha: str = ""
    advisory_action: str = ""
    advisory_reason: str = ""
    blockers: str = "none"
    interaction_mode: str = "unresolved"
    current_instruction: str = ""
    instruction_revision: str = ""
    ack_state: str = "missing"
    open_findings: str = ""
    last_guard_ok: bool = True
    review_state_mtime: float = 0.0
    last_reviewed_sha: str = ""
    done_summary: str = ""
    next_action: str = ""
    key_rules: tuple[str, ...] = ()
    head_at_push_time: str = ""
    operator_interaction_mode: str = "unresolved"
    resolved_phase: str = "idle"
    next_guard_bundle: str = ""
    next_recommended_command: str = ""
    reviewer_observation_status: str = ""
    review_candidate: ReviewCandidateRecord | None = None
    remote_control_attachment: RemoteControlAttachmentState | None = None
    coordination: CoordinationSnapshot | None = None
    authority_snapshot: AuthoritySnapshot | None = None
    attention_status: str = "n/a"
    attention_summary: str = "n/a"
    attention_revision: str = ""
    packet_inbox: PacketInboxState | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["key_rules"] = list(self.key_rules)
        if self.coordination is not None:
            payload["coordination"] = self.coordination.to_dict()
        if self.authority_snapshot is not None:
            payload["authority_snapshot"] = self.authority_snapshot.to_dict()
        return payload


def try_cache_hit(
    repo_root: Path,
    *,
    head_sha: str,
    role: str,
    review_state_mtime: float = 0.0,
    continuity: SessionContinuityState | None = None,
) -> SessionCachePacket | None:
    """Return the cached packet when head, role, and review state still match."""
    cache_path = repo_root / SESSION_CACHE_RELATIVE_DIR / SESSION_CACHE_FILENAME
    if not cache_path.is_file():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("head_sha") or "").strip() != head_sha:
        return None
    if str(payload.get("role") or "").strip() != role:
        return None
    cached_mtime = float(payload.get("review_state_mtime") or 0.0)
    if review_state_mtime != cached_mtime:
        return None
    if continuity is not None and continuity.alignment_status in _STALE_CONTINUITY_STATUSES:
        return None
    return packet_from_mapping(payload)


def write_cache(repo_root: Path, packet: SessionCachePacket) -> None:
    cache_dir = repo_root / SESSION_CACHE_RELATIVE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / SESSION_CACHE_FILENAME
    cache_path.write_text(
        json.dumps(packet.to_dict(), indent=2),
        encoding="utf-8",
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
    sources = sources_override if sources_override is not None else _load_governed_sources(
        repo_root,
        governance=governance,
        review_state=review_state,
    )
    git = load_git_state(repo_root) if sources_override is None else {
        "branch": "unknown", "head": head_sha, "clean": True, "ahead": 0,
    }
    model = read_model_override or build_control_plane_read_model(
        repo_root,
        sources_override=sources,
        git_override=git,
        governance=governance,
        review_state=review_state,
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

    last_reviewed_sha = _extract_last_reviewed_sha(sources)
    head_at_push_time = _extract_head_at_push_time(sources)
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
    next_cmd = (_str_field(_nested_dict(recovery_payload, "decision"), "command")
        or _str_field(attention_payload, "recommended_command")
        or model.next_command or model.next_action)
    review_state_context = build_session_resume_review_state_context(
        review_state_payload,
        fallback_open_findings=_str_field(session, "open_findings"),
        role=role,
    )
    packet_inbox = review_state_context.packet_inbox
    open_findings = review_state_context.open_findings
    observed_control_topology, implementation_permission = derive_startup_control_truth(
        typed_review_state
    ) if typed_review_state is not None else ("", "")
    authority_payload = SessionResumeAuthorityPayload(
        reviewer_mode=model.reviewer_mode,
        reviewer_freshness=model.reviewer_freshness,
        operator_interaction_mode=model.operator_interaction_mode,
        observed_control_topology=observed_control_topology,
        implementation_permission=implementation_permission,
        attention=attention_payload,
        recovery_assessment=recovery_payload,
        current_session=SessionResumeCurrentSessionPayload(
            current_instruction=current_instruction,
            current_instruction_revision=instruction_revision,
            implementer_ack_state=ack_state,
        ),
        coordination=coordination,
        packet_inbox=SessionResumePacketInboxPayload.from_state(packet_inbox),
        next_command=next_cmd,
        governance=push_governance,
    ).to_dict()
    shared_blockers = summary_blockers_csv(authority_payload)
    top_blocker = model.top_blocker
    if top_blocker == _str_field(session, "open_findings"):
        top_blocker = open_findings
    blockers = _resolve_blockers(receipt, top_blocker, shared_blockers)
    if shared_blockers != "none": authority_payload["next_command"] = summary_next_command(authority_payload)
    authority_snapshot = build_authority_snapshot(authority_payload)
    return SessionCachePacket(
        generated_at_utc=utc_timestamp(),
        role=role,
        branch=model.branch,
        head_sha=head_sha,
        advisory_action=model.next_action,
        advisory_reason=top_blocker,
        blockers=blockers,
        interaction_mode=model.operator_interaction_mode,
        current_instruction=current_instruction,
        instruction_revision=instruction_revision,
        ack_state=ack_state,
        open_findings=open_findings,
        last_guard_ok=model.last_guard_ok,
        last_reviewed_sha=last_reviewed_sha,
        review_state_mtime=rs_mtime,
        done_summary=next_cmd,
        next_action=next_cmd,
        key_rules=key_rules,
        head_at_push_time=head_at_push_time,
        operator_interaction_mode=model.operator_interaction_mode,
        resolved_phase=model.resolved_phase,
        next_guard_bundle=guard_bundle,
        next_recommended_command=next_cmd,
        reviewer_observation_status=obs_status,
        review_candidate=review_candidate,
        remote_control_attachment=getattr(model, "remote_control_attachment", None),
        coordination=coordination,
        authority_snapshot=authority_snapshot,
        attention_status=_str_field(attention_payload, "status") or model.attention_status,
        attention_summary=_str_field(attention_payload, "summary") or model.attention_summary,
        attention_revision=(
            packet_inbox.attention_revision if packet_inbox is not None else ""
        ),
        packet_inbox=packet_inbox,
    )


def _extract_current_session(sources: dict[str, Any]) -> dict[str, Any] | None:
    review_state = sources.get("review_state")
    session = _nested_dict(review_state, "current_session")
    if session:
        return session
    compact = sources.get("compact_json")
    return _nested_dict(compact, "current_session")


def _extract_attention_payload(
    sources: dict[str, Any],
    *,
    default_status: str,
    default_summary: str,
) -> dict[str, Any]:
    for key in ("review_state", "compact_json", "full_json"):
        attention = _nested_dict(sources.get(key), "attention")
        if attention:
            return attention
    payload: dict[str, Any] = {}
    if default_status:
        payload["status"] = default_status
    if default_summary:
        payload["summary"] = default_summary
    return payload


def _extract_recovery_assessment_payload(sources: dict[str, Any]) -> dict[str, Any]:
    for key in ("review_state", "full_json", "compact_json"):
        recovery = _nested_dict(sources.get(key), "recovery_assessment")
        if recovery:
            return recovery
    return {}


def _extract_head_at_push_time(sources: dict[str, Any]) -> str:
    for key in ("review_state", "compact_json"):
        bridge = _nested_dict(sources.get(key), "bridge")
        sha = _str_field(bridge, "head_at_push_time")
        if sha:
            return sha
    return ""


def _extract_review_candidate(
    sources: dict[str, Any],
) -> ReviewCandidateRecord | None:
    """Return the current typed review candidate from governed status sources."""
    for key in ("review_state", "compact_json", "full_json"):
        payload = sources.get(key)
        if not isinstance(payload, dict):
            continue
        candidate = review_candidate_from_mapping(payload.get("review_candidate"))
        if candidate is not None:
            return candidate
        review_state = payload.get("review_state")
        if isinstance(review_state, dict):
            candidate = review_candidate_from_mapping(review_state.get("review_candidate"))
            if candidate is not None:
                return candidate
    return None


def _extract_coordination(
    sources: dict[str, Any],
    *,
    repo_root: Path,
    governance: "ProjectGovernance | None",
) -> CoordinationSnapshot | None:
    """Return governed coordination truth via the shared loader."""
    from ...runtime.coordination_loader import load_coordination_snapshot

    fresh = load_coordination_snapshot(
        repo_root=repo_root,
        sources=sources,
        governance=governance,
    )
    if fresh is not None:
        return fresh
    try:
        from ...runtime.startup_context import build_startup_context
    except ImportError:
        return None
    startup_context = build_startup_context(repo_root=repo_root)
    return startup_context.coordination

_extract_last_reviewed_sha = _extract_head_at_push_time

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

def packet_from_mapping(payload: dict[str, Any]) -> SessionCachePacket:
    return SessionCachePacket(
        schema_version=int(payload.get("schema_version") or 3),
        contract_id=str(payload.get("contract_id") or "SessionCachePacket").strip(),
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        role=str(payload.get("role") or "implementer").strip(),
        branch=str(payload.get("branch") or "").strip(),
        head_sha=str(payload.get("head_sha") or "").strip(),
        advisory_action=str(payload.get("advisory_action") or "").strip(),
        advisory_reason=str(payload.get("advisory_reason") or "").strip(),
        blockers=str(payload.get("blockers") or "none").strip(),
        interaction_mode=str(payload.get("interaction_mode") or "unresolved").strip(),
        current_instruction=str(payload.get("current_instruction") or "").strip(),
        instruction_revision=str(payload.get("instruction_revision") or "").strip(),
        ack_state=str(payload.get("ack_state") or "missing").strip(),
        open_findings=str(payload.get("open_findings") or "").strip(),
        last_guard_ok=bool(payload.get("last_guard_ok", True)),
        last_reviewed_sha=str(payload.get("last_reviewed_sha") or "").strip(),
        review_state_mtime=float(payload.get("review_state_mtime") or 0.0),
        done_summary=str(payload.get("done_summary") or "").strip(),
        next_action=str(payload.get("next_action") or "").strip(),
        key_rules=tuple(
            str(r).strip() for r in payload.get("key_rules", ()) if str(r).strip()
        ),
        head_at_push_time=str(payload.get("head_at_push_time") or "").strip(),
        operator_interaction_mode=str(
            payload.get("operator_interaction_mode") or "unresolved"
        ).strip(),
        resolved_phase=str(payload.get("resolved_phase") or "idle").strip(),
        next_guard_bundle=str(payload.get("next_guard_bundle") or "").strip(),
        next_recommended_command=str(payload.get("next_recommended_command") or "").strip(),
        reviewer_observation_status=str(payload.get("reviewer_observation_status") or "").strip(),
        review_candidate=review_candidate_from_mapping(payload.get("review_candidate")),
        remote_control_attachment=remote_control_attachment_from_mapping(
            payload.get("remote_control_attachment")
        ),
        coordination=coordination_snapshot_from_mapping(payload.get("coordination")),
        authority_snapshot=authority_snapshot_from_mapping(
            payload.get("authority_snapshot")
        ),
        attention_status=str(payload.get("attention_status") or "n/a").strip() or "n/a",
        attention_summary=str(payload.get("attention_summary") or "n/a").strip() or "n/a",
        attention_revision=str(payload.get("attention_revision") or "").strip(),
        packet_inbox=packet_inbox_from_mapping(payload.get("packet_inbox")),
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

def _load_governed_sources(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
    review_state: "ReviewState | None" = None,
) -> dict[str, Any]:
    """Load governed sources without reprojecting review state mid-read."""
    base = load_sources(
        repo_root,
        governance=governance,
        review_state_override=review_state,
    )
    if review_state is not None:
        base["review_state"] = review_state.to_dict()
    gov_paths = resolve_source_paths(repo_root, governance=governance)
    compact_path = repo_root / gov_paths["compact"]
    base["compact_json"] = read_json_artifact(compact_path)
    return base

def _nested_dict(data: dict[str, Any] | None, key: str) -> dict[str, Any] | None:
    if data is None:
        return None
    value = data.get(key)
    return dict(value) if isinstance(value, dict) else None

def _str_field(data: dict[str, Any] | None, key: str) -> str:
    if data is None:
        return ""
    return str(data.get(key) or "").strip()
