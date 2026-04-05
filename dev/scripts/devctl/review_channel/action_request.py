"""Typed action-request surface for bridge-mediated remote control.

When the operator is on a mobile device and cannot interact with Terminal.app
dialog prompts, Codex (the reviewer) can POST typed action requests into the
``## Action Requests`` bridge section.  Claude (the implementer) reads pending
requests and executes them on Codex's behalf.

This module owns the parsing, validation, rendering, and packet-projection
helpers for that surface.  The canonical source of truth for action requests
is ``kind="action_request"`` packets in the event store; the markdown regex
parser is kept as a **legacy compatibility** path for bridge-only sessions
that predate the packet transport.

It does NOT own execution -- Claude reads the bridge and acts manually for now.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

ACTION_REQUEST_LINE_RE = re.compile(
    r"^-\s*\[(?P<id>[^\]]+)\]\s+(?P<action>\S+):\s+(?P<payload>.+?)"
    r"\s+\(status:\s*(?P<status>pending|completed|failed)\)\s*$"
)

SECTION_HEADING = "Action Requests"

# Line budget for the bridge section (keeps the bridge compact).
SECTION_LINE_LIMIT = 12


class ActionKind(str, Enum):
    """Supported bridge action-request types."""

    COMMIT = "commit"
    RUN_CHECK = "run_check"
    PUSH = "push"
    KILL_PROCESS = "kill_process"


VALID_ACTION_KINDS = frozenset(member.value for member in ActionKind)


class ActionStatus(str, Enum):
    """Lifecycle status for a single action request."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ActionRequest:
    """One parsed action-request line from the bridge."""

    id: str
    action: str
    payload: str
    status: str


def parse_action_requests(text: str) -> list[ActionRequest]:
    """Parse all action-request lines from a bridge section body.

    Lines that do not match the canonical format are silently skipped so a
    malformed bridge never crashes the reader.
    """
    results: list[ActionRequest] = []
    for raw_line in text.splitlines():
        match = ACTION_REQUEST_LINE_RE.match(raw_line.strip())
        if match is None:
            continue
        results.append(
            ActionRequest(
                id=match.group("id").strip(),
                action=match.group("action").strip(),
                payload=match.group("payload").strip(),
                status=match.group("status").strip(),
            )
        )
    return results


def pending_action_requests(text: str) -> list[ActionRequest]:
    """Return only the ``pending`` action requests from a section body."""
    return [
        req for req in parse_action_requests(text)
        if req.status == ActionStatus.PENDING.value
    ]


def validate_action_request(request: ActionRequest) -> list[str]:
    """Return validation errors for one parsed action request."""
    errors: list[str] = []
    if not request.id:
        errors.append("Action request is missing an id.")
    if request.action not in VALID_ACTION_KINDS:
        errors.append(
            f"Unsupported action kind `{request.action}`; "
            f"valid kinds: {', '.join(sorted(VALID_ACTION_KINDS))}."
        )
    if not request.payload:
        errors.append("Action request is missing a payload.")
    if request.status not in {s.value for s in ActionStatus}:
        errors.append(f"Invalid action status `{request.status}`.")
    return errors


def render_action_request_line(request: ActionRequest) -> str:
    """Render one action request as a canonical bridge markdown line."""
    return (
        f"- [{request.id}] {request.action}: "
        f"{request.payload} (status: {request.status})"
    )


def render_action_requests_section(requests: list[ActionRequest]) -> str:
    """Render the full body of an Action Requests bridge section."""
    if not requests:
        return "- No pending action requests."
    return "\n".join(render_action_request_line(req) for req in requests)


def default_section_body() -> str:
    """Return the default empty-state body for the Action Requests section."""
    return "- No pending action requests."


# ---------------------------------------------------------------------------
# Packet-projection helpers: canonical source of truth for action requests
# ---------------------------------------------------------------------------

def action_requests_from_packets(
    packets: list[dict[str, object]],
) -> list[ActionRequest]:
    """Project ``ActionRequest`` rows from pending ``kind="action_request"`` packets.

    Each qualifying packet carries ``packet_id``, ``requested_action``, and
    ``body`` which map onto the ``id``, ``action``, and ``payload`` fields of
    an ``ActionRequest``.  Only packets whose ``status`` equals ``"pending"``
    are included, so the projection always represents the live work queue.
    """
    results: list[ActionRequest] = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("kind") or "") != "action_request":
            continue
        if str(packet.get("status") or "") != ActionStatus.PENDING.value:
            continue
        results.append(
            ActionRequest(
                id=str(packet.get("packet_id") or ""),
                action=str(packet.get("requested_action") or ""),
                payload=str(packet.get("body") or "").strip(),
                status=ActionStatus.PENDING.value,
            )
        )
    return results


def render_action_requests_from_packets(
    packets: list[dict[str, object]],
) -> str:
    """Render the ``## Action Requests`` bridge section body from packet state.

    Returns the canonical markdown body (same format as
    ``render_action_requests_section``) so the bridge projection uses the
    packet transport as the single source of truth.
    """
    projected = action_requests_from_packets(packets)
    return render_action_requests_section(projected)
