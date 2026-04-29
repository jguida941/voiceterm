"""MVP typed continuity anchors for planning review packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field

_PLANNING_PACKET_KINDS = frozenset(
    {"plan_gap_review", "plan_patch_review", "plan_ready_gate"}
)


@dataclass(frozen=True, slots=True)
class PacketIntentAnchor:
    """Non-authoritative continuity pointer from a review packet to plan intent."""

    packet_id: str = ""
    target_plan: str = ""
    target_task: str = ""
    anchor_refs: tuple[str, ...] = ()
    lifecycle_state: str = "plan_anchor_pending"
    source_agent: str = ""
    disposition: str = ""
    evidence: tuple[str, ...] = ()
    packet_kind: str = ""
    summary: str = ""
    semantic_zref: str = ""
    source_identity: dict[str, str] = field(default_factory=dict)
    context_pack_refs: tuple[dict[str, object], ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["anchor_refs"] = list(self.anchor_refs)
        payload["evidence"] = list(self.evidence)
        payload["source_identity"] = dict(self.source_identity or {})
        payload["context_pack_refs"] = [dict(ref) for ref in self.context_pack_refs]
        return payload


@dataclass(frozen=True, slots=True)
class PlanIterationSession:
    """Alias view over existing plan review packet kinds."""

    schema_version: int = 1
    contract_id: str = "PlanIterationSession"
    status: str = "empty"
    packet_ids: tuple[str, ...] = ()
    anchor_refs: tuple[str, ...] = ()
    source_packet_kinds: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["packet_ids"] = list(self.packet_ids)
        payload["anchor_refs"] = list(self.anchor_refs)
        payload["source_packet_kinds"] = list(self.source_packet_kinds)
        return payload


def packet_intent_anchors_from_packets(
    packets: object,
    *,
    limit: int = 1,
) -> tuple[PacketIntentAnchor, ...]:
    """Project recent/open planning packets without granting execution authority."""
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return ()
    anchors: list[PacketIntentAnchor] = []
    for packet in packets:
        anchor = packet_intent_anchor_from_packet(packet)
        if anchor is not None:
            anchors.append(anchor)
    return tuple(anchors[:limit])


def packet_intent_anchor_from_packet(packet: object) -> PacketIntentAnchor | None:
    """Return one continuity anchor for planning packets and plan-targeted rows."""
    kind = _field(packet, "kind")
    target_kind = _field(packet, "target_kind")
    if kind not in _PLANNING_PACKET_KINDS and target_kind != "plan":
        return None
    packet_id = _field(packet, "packet_id")
    if not packet_id:
        return None
    anchor_refs = tuple(_rows(_raw(packet, "anchor_refs"))[:3])
    evidence = tuple(
        dict.fromkeys(
            (
                f"packet:{packet_id}",
                *_rows(_raw(packet, "evidence_refs")),
                _field(packet, "resolution_anchor"),
            )
        )
    )
    return PacketIntentAnchor(
        packet_id=packet_id,
        target_plan=_field(packet, "target_ref"),
        target_task=_field(packet, "intake_ref")
        or _field(packet, "mutation_op")
        or _field(packet, "requested_action"),
        anchor_refs=anchor_refs,
        lifecycle_state=_anchor_lifecycle_state(packet),
        source_agent=_field(packet, "from_agent"),
        disposition=_disposition_status(packet),
        evidence=tuple(item for item in evidence if item)[:5],
        packet_kind=kind,
        summary=_truncate(_field(packet, "summary"), limit=80),
        semantic_zref=_field(packet, "semantic_zref") or f"packet:{packet_id}",
        source_identity=_dict_of_str(_raw(packet, "source_identity")),
        context_pack_refs=tuple(_mapping_rows(_raw(packet, "context_pack_refs"))[:3]),
    )


def plan_iteration_session_from_anchors(
    anchors: tuple[PacketIntentAnchor, ...],
) -> PlanIterationSession:
    """Return the minimal status view over packet-derived plan anchors."""
    if not anchors:
        return PlanIterationSession()
    status = (
        "applied"
        if any(anchor.lifecycle_state == "applied" for anchor in anchors)
        else "plan_anchor_pending"
    )
    anchor_refs = tuple(
        dict.fromkeys(ref for anchor in anchors for ref in anchor.anchor_refs)
    )[:3]
    return PlanIterationSession(
        status=status,
        packet_ids=tuple(anchor.packet_id for anchor in anchors[:1]),
        anchor_refs=anchor_refs,
        source_packet_kinds=tuple(
            dict.fromkeys(anchor.packet_kind for anchor in anchors if anchor.packet_kind)
        ),
    )


def packet_intent_anchor_from_mapping(value: object) -> PacketIntentAnchor | None:
    if not isinstance(value, Mapping):
        return None
    packet_id = _field(value, "packet_id")
    if not packet_id:
        return None
    return PacketIntentAnchor(
        packet_id=packet_id,
        target_plan=_field(value, "target_plan"),
        target_task=_field(value, "target_task"),
        anchor_refs=tuple(_rows(value.get("anchor_refs"))),
        lifecycle_state=_field(value, "lifecycle_state") or "plan_anchor_pending",
        source_agent=_field(value, "source_agent"),
        disposition=_field(value, "disposition"),
        evidence=tuple(_rows(value.get("evidence"))),
        packet_kind=_field(value, "packet_kind"),
        summary=_field(value, "summary"),
        semantic_zref=_field(value, "semantic_zref"),
        source_identity=_dict_of_str(value.get("source_identity")),
        context_pack_refs=tuple(_mapping_rows(value.get("context_pack_refs"))),
    )


def packet_intent_anchors_from_value(
    value: object,
) -> tuple[PacketIntentAnchor, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        anchor
        for anchor in (packet_intent_anchor_from_mapping(item) for item in value)
        if anchor is not None
    )


def _anchor_lifecycle_state(packet: object) -> str:
    state = _field(packet, "lifecycle_current_state") or _field(packet, "status")
    if state == "applied" or _field(packet, "applied_at_utc"):
        return "applied"
    return "plan_anchor_pending"


def _disposition_status(packet: object) -> str:
    disposition = _raw(packet, "disposition")
    if isinstance(disposition, Mapping):
        return _field(disposition, "status")
    return ""


def _field(packet: object, key: str) -> str:
    return str(_raw(packet, key) or "").strip()


def _raw(packet: object, key: str) -> object:
    if isinstance(packet, Mapping):
        return packet.get(key)
    return getattr(packet, key, "")


def _rows(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dict_of_str(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key).strip(): str(item or "").strip()
        for key, item in value.items()
        if str(key).strip() and str(item or "").strip()
    }


def _mapping_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _truncate(value: str, *, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


__all__ = [
    "PacketIntentAnchor",
    "PlanIterationSession",
    "packet_intent_anchors_from_packets",
    "packet_intent_anchors_from_value",
    "plan_iteration_session_from_anchors",
]
