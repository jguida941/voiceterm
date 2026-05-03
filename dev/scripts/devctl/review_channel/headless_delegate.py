"""Provider wake predicates for typed packet target resolution.

Extracted from `follow_controller` so the dashboard/observer
dashboard-poll rules, worker visibility rules, and session-pid helper can
grow without inflating the host file beyond shape limits. These predicates are
the single source of truth for deciding whether a provider-targeted packet
should wait for a bound dashboard poll, launch a visible worker, or fail closed
before any headless worker is spawned.
"""

from __future__ import annotations

from .session_id_extractors import mapping_int_ids, object_int_ids

_HEADLESS_DELEGATE_TARGET_ROLES = frozenset({"dashboard", "observer"})
_HEADLESS_DELEGATE_PACKET_KINDS = frozenset(
    {"system_notice", "finding", "question"}
)
_HEADLESS_DELEGATE_REQUESTED_ACTIONS = frozenset({"", "review_only"})
_IMPLEMENTER_TARGET_ROLES = frozenset(
    {"coder", "coding", "implementation", "implementer"}
)
_REQUESTED_VISIBILITIES = frozenset({"dashboard_only", "headless", "visible"})


def packet_targets_dashboard_poll(packet: dict[str, object]) -> bool:
    """Return True when the target is a live dashboard/observer poller.

    Some provider adapters cannot be externally pushed awake. For review-only
    dashboard packets, the correct wake is typed attention for the bound
    dashboard session and that session's own polling cadence, not a fresh
    detached process.
    """
    target_role = str(packet.get("target_role") or "").strip().lower()
    if target_role not in _HEADLESS_DELEGATE_TARGET_ROLES:
        return False
    kind = str(packet.get("kind") or "").strip().lower()
    if kind not in _HEADLESS_DELEGATE_PACKET_KINDS:
        return False
    requested_action = str(packet.get("requested_action") or "").strip().lower()
    return requested_action in _HEADLESS_DELEGATE_REQUESTED_ACTIONS


def packet_targets_implementer_worker(packet: dict[str, object]) -> bool:
    """Return True when a packet targets a mutating implementer-style role."""
    target_role = str(packet.get("target_role") or "").strip().lower()
    return target_role in _IMPLEMENTER_TARGET_ROLES


def requested_worker_visibility(
    packet: dict[str, object],
    *,
    terminal_arg: object = "",
) -> str:
    """Resolve requested worker visibility from packet policy and CLI mode."""
    requested = str(
        packet.get("requested_session_visibility") or ""
    ).strip().lower()
    if requested in _REQUESTED_VISIBILITIES:
        return requested
    if packet_targets_dashboard_poll(packet):
        return "dashboard_only"
    return "visible"


def terminal_window_ids(sessions: list[dict[str, object]]) -> tuple[int, ...]:
    """Extract dedup'd Terminal.app window ids from a session list."""
    return mapping_int_ids(sessions, "terminal_window_id")


def session_pids(sessions: tuple[object, ...]) -> tuple[int, ...]:
    """Extract dedup'd session PIDs from a session probe tuple.

    Tries `session_pid` first, falling back to `pid`, accepting either
    int-coercible value. Returns an empty tuple when no live PID is
    available. Used by the wake path to attribute replaced_pids in the
    wake receipt.
    """
    return object_int_ids(sessions, ("session_pid", "pid"))
