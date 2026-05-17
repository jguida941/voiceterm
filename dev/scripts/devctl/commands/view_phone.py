"""Phone surface renderers for devctl view.

Derives state from the single ControlPlaneReadModel instead of building
a full dashboard snapshot.  Keeps the phone surface consistent with every
other governance surface that reads from the same frozen read model.
"""

from __future__ import annotations

import json
from typing import Any

from ..config import REPO_ROOT
from ..runtime.control_plane_read_model import (
    ControlPlaneReadModel,
    build_control_plane_read_model,
)
from ..time_utils import utc_timestamp


def render_phone_summary(args) -> str:
    """Compact mobile-optimized view from the ControlPlaneReadModel."""
    model = build_control_plane_read_model(REPO_ROOT)
    payload = phone_payload_from_read_model(model)

    if args.format == "json":
        return json.dumps(payload, indent=2)
    return _phone_markdown(payload)


def phone_payload_from_read_model(model: ControlPlaneReadModel) -> dict[str, Any]:
    """Build a slim JSON payload for the phone surface from the read model."""
    infra_count = sum([model.publisher_running, model.supervisor_running])
    infra_label = f"{infra_count} daemon{'s' if infra_count != 1 else ''} running"
    next_actor = _derive_next_actor(model)
    return {
        "command": "view",
        "surface": "phone",
        "mode": "summary",
        "timestamp": utc_timestamp(),
        "resolved_phase": model.resolved_phase,
        "top_blocker": model.top_blocker,
        "next_actor": next_actor,
        "next_action": model.next_action,
        "next_command": model.next_command,
        "infra_label": infra_label,
        "pending_actions": model.pending_action_requests,
        "reviewer_age": model.reviewer_freshness,
        "push_eligible": model.push_eligible,
        "review_accepted": model.review_accepted,
        "last_guard_ok": model.last_guard_ok,
    }


def _derive_next_actor(model: ControlPlaneReadModel) -> str:
    """Determine who needs to act next from the read model."""
    if model.implementation_blocked:
        return "operator"
    if not model.last_guard_ok:
        return "implementer"
    if model.reviewer_freshness not in ("--", "n/a", "fresh", "recent"):
        return "reviewer"
    if model.push_eligible:
        return "operator"
    return "implementer"


def _phone_markdown(payload: dict[str, Any]) -> str:
    """Render phone-optimized compact markdown from the payload."""
    phase = str(payload.get("resolved_phase", "unknown")).upper()
    blocker = payload.get("top_blocker", "none")
    actor = payload.get("next_actor", "unknown")
    action = payload.get("next_action", "")
    infra = payload.get("infra_label", "")
    pending = payload.get("pending_actions", 0)
    reviewer_age = payload.get("reviewer_age", "--")
    lines = [
        f"## {phase}",
        f"Blocker: {blocker}",
        f"Next: {actor} -- {action}",
        f"Infra: {infra}",
        f"Reviewer: {reviewer_age} | Pending: {pending}",
    ]
    return "\n".join(lines)
