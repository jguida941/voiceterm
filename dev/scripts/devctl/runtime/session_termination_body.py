"""Packet body-observation helpers for session termination policy."""

from __future__ import annotations

import hashlib
import shlex
from collections.abc import Mapping, Sequence

from .session_route_scope import normalize_route_role


def packet_body_observed_by_route(
    packet: Mapping[str, object],
    *,
    actor: str,
    actor_role: str,
    session_id: str,
) -> bool:
    body = _text(packet.get("body"))
    if not body:
        return True
    if not actor:
        return False
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if body_observation_row_matches(
        packet,
        actor=actor,
        actor_role=actor_role,
        session_id=session_id,
        body_digest=digest,
        allow_event_session_fallback=False,
    ):
        return True
    events = packet.get("body_observation_events")
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        return False
    return any(
        isinstance(event, Mapping)
        and body_observation_row_matches(
            event,
            actor=actor,
            actor_role=actor_role,
            session_id=session_id,
            body_digest=digest,
            allow_event_session_fallback=True,
        )
        for event in events
    )


def body_observation_row_matches(
    row: Mapping[str, object],
    *,
    actor: str,
    actor_role: str,
    session_id: str,
    body_digest: str,
    allow_event_session_fallback: bool,
) -> bool:
    if _text(row.get("body_observed_by")) != actor:
        return False
    if _text(row.get("body_digest")) != body_digest:
        return False
    if actor_role:
        observed_role = _text(row.get("body_observed_role"))
        if allow_event_session_fallback and not observed_role:
            observed_role = _text(row.get("target_role"))
        if normalize_route_role(observed_role) != actor_role:
            return False
    if session_id:
        observed_session = _text(row.get("body_observed_session_id"))
        if allow_event_session_fallback and not observed_session:
            observed_session = _text(
                row.get("target_session_id") or row.get("session_id")
            )
        if observed_session != session_id:
            return False
    return True


def packet_body_show_command(
    packet: Mapping[str, object],
    *,
    actor: str,
    actor_role: str,
    session_id: str,
) -> str:
    packet_id = _text(packet.get("packet_id"))
    target_actor = _text(actor) or _text(packet.get("to_agent"))
    if not packet_id:
        return ""
    parts = [
        "python3",
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        "show",
        "--packet-id",
        packet_id,
    ]
    if target_actor:
        parts.extend(("--actor", target_actor))
    parts.extend(("--terminal", "none", "--format", "md"))
    if actor_role:
        parts.extend(("--target-role", actor_role))
    if session_id:
        parts.extend(("--target-session-id", session_id))
    return " ".join(shlex.quote(part) for part in parts)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
