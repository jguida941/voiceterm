"""Startup-context collaboration and authority projection helpers."""

from __future__ import annotations

from .packet_intent_anchor import PacketIntentAnchor
from .startup_context_actor_authority_output import (
    startup_actor_authority_dict,
    startup_actor_authority_summary_dict,
    startup_actor_authority_summary_from_mapping,
    startup_capability_grant_dict,
)
from .startup_context_authority_snapshot_output import startup_authority_snapshot_dict
from .startup_context_collaboration_session_output import (
    startup_collaboration_dict,
    startup_collaboration_summary_dict,
)
from .startup_context_participant_output import (
    startup_participant_dict,
    startup_participant_summary_dict,
    startup_role_assignment_dict,
)


def startup_packet_intent_anchor_dict(anchor: PacketIntentAnchor) -> dict[str, object]:
    """Compact startup projection of a packet-derived plan anchor."""
    return {
        "packet_id": anchor.packet_id,
        "target_plan": anchor.target_plan,
        "anchor_refs": list(anchor.anchor_refs),
        "lifecycle_state": anchor.lifecycle_state,
    }


__all__ = [
    "startup_actor_authority_dict",
    "startup_actor_authority_summary_dict",
    "startup_actor_authority_summary_from_mapping",
    "startup_authority_snapshot_dict",
    "startup_capability_grant_dict",
    "startup_collaboration_dict",
    "startup_collaboration_summary_dict",
    "startup_packet_intent_anchor_dict",
    "startup_participant_dict",
    "startup_participant_summary_dict",
    "startup_role_assignment_dict",
]
