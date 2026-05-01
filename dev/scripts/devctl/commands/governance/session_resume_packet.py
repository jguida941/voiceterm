"""Packet and cache helpers for the governed session-resume command."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ...platform.coordination_snapshot_models import (
    CoordinationSnapshot,
    coordination_snapshot_from_mapping,
)
from ...runtime.authority_snapshot import (
    AuthoritySnapshot,
    authority_snapshot_from_mapping,
)
from ...runtime.agent_session_continuation_models import AgentSessionContinuationState
from ...runtime.agent_session_continuation_parse import (
    agent_session_continuation_from_mapping,
)
from ...runtime.review_state_models import (
    PacketInboxState,
    ReviewCandidateRecord,
    packet_inbox_from_mapping,
    review_candidate_from_mapping,
)
from ...runtime.packet_intent_anchor import (
    PacketIntentAnchor,
    packet_intent_anchors_from_value,
)
from ...runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    remote_control_attachment_from_mapping,
)
from ...runtime.session_posture import SessionPosture, session_posture_from_mapping
from ...runtime.work_intake_models import SessionContinuityState
from ...runtime.surface_provenance import (
    SurfaceProvenance,
    attach_surface_provenance,
    surface_provenance_from_mapping,
)

SESSION_CACHE_RELATIVE_DIR = Path("dev/reports/session_cache/latest")
SESSION_CACHE_FILENAME = "cache.json"
SESSION_CACHE_PACKET_SCHEMA_VERSION = 7

# Typed continuity states that invalidate a cached session packet even when
# head/role/mtime all match. `alignment_status` values outside this set
# (for example `aligned`, `scope_aligned`, `instruction_aligned`) leave the
# cache intact. Keep this set in sync with
# ``runtime.work_intake_continuity.build_continuity`` outputs.
_STALE_CONTINUITY_STATUSES: frozenset[str] = frozenset(
    {"needs_review", "plan_only", "review_only", "missing"}
)


@dataclass(frozen=True, slots=True)
class SessionCachePacket:
    """Compact session state replacing full bootstrap output."""

    schema_version: int = SESSION_CACHE_PACKET_SCHEMA_VERSION
    contract_id: str = "SessionCachePacket"
    generated_at_utc: str = ""
    role: str = "implementer"
    branch: str = ""
    head_sha: str = ""
    snapshot_id: str = ""
    zref: str = ""
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
    session_posture: SessionPosture | None = None
    coordination: CoordinationSnapshot | None = None
    authority_snapshot: AuthoritySnapshot | None = None
    attention_status: str = "n/a"
    attention_summary: str = "n/a"
    attention_revision: str = ""
    packet_inbox: PacketInboxState | None = None
    packet_intent_anchors: tuple[PacketIntentAnchor, ...] = ()
    connectivity_registry: dict[str, object] = field(default_factory=dict)
    runtime_spine_closure: dict[str, object] = field(default_factory=dict)
    packet_continuity_index: dict[str, object] = field(default_factory=dict)
    packet_carry_forward_debt: tuple[dict[str, object], ...] = ()
    continuity_attention: dict[str, object] = field(default_factory=dict)
    key_surfaces: tuple[str, ...] = ()
    agent_session_continuation: AgentSessionContinuationState | None = None
    provenance: SurfaceProvenance | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("provenance", None)
        payload["key_rules"] = list(self.key_rules)
        payload["connectivity_registry"] = dict(self.connectivity_registry)
        payload["runtime_spine_closure"] = dict(self.runtime_spine_closure)
        payload["packet_continuity_index"] = dict(self.packet_continuity_index)
        payload["packet_carry_forward_debt"] = [
            dict(row) for row in self.packet_carry_forward_debt
        ]
        payload["continuity_attention"] = dict(self.continuity_attention)
        payload["key_surfaces"] = list(self.key_surfaces)
        if self.coordination is not None:
            payload["coordination"] = self.coordination.to_dict()
        if self.session_posture is not None:
            payload["session_posture"] = self.session_posture.to_dict()
        if self.authority_snapshot is not None:
            payload["authority_snapshot"] = self.authority_snapshot.to_dict()
        if self.agent_session_continuation is not None:
            payload["agent_session_continuation"] = (
                self.agent_session_continuation.to_dict()
            )
        if self.packet_intent_anchors:
            payload["packet_intent_anchors"] = [
                anchor.to_dict() for anchor in self.packet_intent_anchors
            ]
        result = attach_surface_provenance(payload, provenance=self.provenance)
        result.setdefault("snapshot_id", self.snapshot_id)
        result.setdefault("zref", self.zref)
        return result


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
    if int(payload.get("schema_version") or 0) != SESSION_CACHE_PACKET_SCHEMA_VERSION:
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


def packet_from_mapping(payload: dict[str, object]) -> SessionCachePacket:
    return SessionCachePacket(
        schema_version=int(
            payload.get("schema_version") or SESSION_CACHE_PACKET_SCHEMA_VERSION
        ),
        contract_id=str(payload.get("contract_id") or "SessionCachePacket").strip(),
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        role=str(payload.get("role") or "implementer").strip(),
        branch=str(payload.get("branch") or "").strip(),
        head_sha=str(payload.get("head_sha") or "").strip(),
        snapshot_id=str(payload.get("snapshot_id") or "").strip(),
        zref=str(payload.get("zref") or "").strip(),
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
            str(rule).strip() for rule in payload.get("key_rules", ()) if str(rule).strip()
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
        session_posture=session_posture_from_mapping(payload.get("session_posture")),
        coordination=coordination_snapshot_from_mapping(payload.get("coordination")),
        authority_snapshot=authority_snapshot_from_mapping(
            payload.get("authority_snapshot")
        ),
        attention_status=str(payload.get("attention_status") or "n/a").strip() or "n/a",
        attention_summary=str(payload.get("attention_summary") or "n/a").strip() or "n/a",
        attention_revision=str(payload.get("attention_revision") or "").strip(),
        packet_inbox=packet_inbox_from_mapping(payload.get("packet_inbox")),
        packet_intent_anchors=packet_intent_anchors_from_value(
            payload.get("packet_intent_anchors")
        ),
        connectivity_registry=_dict_field(payload.get("connectivity_registry")),
        runtime_spine_closure=_dict_field(payload.get("runtime_spine_closure")),
        packet_continuity_index=_dict_field(payload.get("packet_continuity_index")),
        packet_carry_forward_debt=tuple(
            _dict_rows(payload.get("packet_carry_forward_debt"))
        ),
        continuity_attention=_dict_field(payload.get("continuity_attention")),
        key_surfaces=tuple(
            str(surface).strip()
            for surface in payload.get("key_surfaces", ())
            if str(surface).strip()
        ),
        agent_session_continuation=agent_session_continuation_from_mapping(
            payload.get("agent_session_continuation")
        ),
        provenance=surface_provenance_from_mapping(payload),
    )


def _dict_field(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _dict_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [dict(row) for row in value if isinstance(row, dict)]
