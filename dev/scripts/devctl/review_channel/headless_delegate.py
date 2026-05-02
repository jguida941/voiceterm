"""Headless-delegate predicates for typed wake target resolution.

Extracted from `follow_controller` so the dashboard/observer
delegation rules and the session-pid helper can grow without inflating
the host file beyond shape limits. The predicate is the single source
of truth for "is this packet safe to wake via a fresh headless
conductor instead of falsely claiming the visible session woke?".
"""

from __future__ import annotations

from ..runtime.operator_context import is_remote_mode

_HEADLESS_DELEGATE_TARGET_ROLES = frozenset({"dashboard", "observer"})
_HEADLESS_DELEGATE_PACKET_KINDS = frozenset(
    {"system_notice", "finding", "question"}
)
_HEADLESS_DELEGATE_REQUESTED_ACTIONS = frozenset({"", "review_only"})


def can_delegate_dashboard_packet_headless(
    packet: dict[str, object],
    *,
    operator_interaction_mode: str,
    headless_requested: bool = False,
) -> bool:
    """Return True when a non-codex packet is safe to wake via a delegate.

    Conditions (all must hold):
    - operator_interaction_mode is remote OR --terminal=none was requested
    - packet's target_role is in {dashboard, observer}
    - packet's kind is in {system_notice, finding, question}
    - packet's requested_action is in {empty, review_only}
    """
    if not (
        is_remote_mode(str(operator_interaction_mode or "").strip())
        or headless_requested
    ):
        return False
    target_role = str(packet.get("target_role") or "").strip().lower()
    if target_role not in _HEADLESS_DELEGATE_TARGET_ROLES:
        return False
    kind = str(packet.get("kind") or "").strip().lower()
    if kind not in _HEADLESS_DELEGATE_PACKET_KINDS:
        return False
    requested_action = str(packet.get("requested_action") or "").strip().lower()
    return requested_action in _HEADLESS_DELEGATE_REQUESTED_ACTIONS


def session_pids(sessions: tuple[object, ...]) -> tuple[int, ...]:
    """Extract dedup'd session PIDs from a session probe tuple.

    Tries `session_pid` first, falling back to `pid`, accepting either
    int-coercible value. Returns an empty tuple when no live PID is
    available. Used by the wake path to attribute replaced_pids in the
    wake receipt.
    """
    pids: list[int] = []
    for session in sessions:
        for attr in ("session_pid", "pid"):
            raw = getattr(session, attr, None)
            try:
                pid = int(raw or 0)
            except (TypeError, ValueError):
                continue
            if pid > 0:
                pids.append(pid)
                break
    return tuple(dict.fromkeys(pids))
