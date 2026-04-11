"""Preconditions for instruction-mutating markdown bridge writes."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .current_session_projection import bridge_implementer_state_hash
from .handoff import extract_bridge_snapshot
from .pending_packets import load_pending_reviewer_packets
from .reviewer_state_normalize import (
    instruction_revision as _normalized_instruction_revision,
    normalize_instruction_body as _normalize_instruction_body,
)
from .reviewer_state_support import current_instruction_revision_from_bridge_text


# Only these `--reason` values may bypass the reviewer-inbox gate via
# `--allow-unread-inbox`. Treated as an emergency-recovery whitelist: normal
# review passes cannot silently skip inbox consumption.
EMERGENCY_INBOX_OVERRIDE_REASONS: frozenset[str] = frozenset(
    {
        "codex-recovery-override",
        "operator-manual-override",
    }
)


def assert_reviewer_inbox_empty(
    *,
    repo_root: Path,
    reviewer_actor: str,
    allow_unread_inbox: bool = False,
    reason: str = "",
) -> tuple[str, ...]:
    """Fail closed when the reviewer has live-pending packets in their inbox.

    The typed preflight gate that stops Codex (or Claude) from writing a
    reviewer-checkpoint verdict while typed finding packets still sit unread.
    Returns the tuple of unread packet ids that were present at check time --
    empty when the inbox was clean, or populated when an emergency override
    (``allow_unread_inbox`` plus a whitelisted ``reason``) let the write
    through. Callers record the returned ids in the audit payload.
    """
    normalized_actor = (reviewer_actor or "").strip()
    if not normalized_actor:
        return ()
    pending_packets = load_pending_reviewer_packets(
        repo_root,
        fail_closed=False,
        reviewer_agent=normalized_actor,
    )
    if not pending_packets:
        return ()
    packet_ids = _pending_packet_ids(pending_packets)
    normalized_reason = (reason or "").strip().lower()
    if allow_unread_inbox and normalized_reason in EMERGENCY_INBOX_OVERRIDE_REASONS:
        return packet_ids
    if allow_unread_inbox and normalized_reason not in EMERGENCY_INBOX_OVERRIDE_REASONS:
        raise ValueError(
            "refused reviewer-checkpoint: --allow-unread-inbox requires an "
            f"emergency-recovery reason, got `{reason or '(empty)'}`. "
            "Whitelist: "
            f"{', '.join(sorted(EMERGENCY_INBOX_OVERRIDE_REASONS))}. "
            f"Unread packets targeting `{normalized_actor}`: "
            f"{', '.join(packet_ids)}."
        )
    packet_list = ", ".join(packet_ids)
    raise ValueError(
        f"refused reviewer-checkpoint: reviewer has {len(packet_ids)} unread "
        f"packets in inbox: [{packet_list}]. Run: "
        f"`devctl review-channel --action inbox --target {normalized_actor} "
        "--status pending`, then "
        f"`devctl review-channel --action ack --packet-id <id> --actor {normalized_actor}` "
        "for each unread packet (or `--action dismiss` if the packet is "
        "stale) before writing a new reviewer-checkpoint. This gate blocks "
        "the governance-platform protocol bug where typed finding packets "
        "were invisible to the reviewer loop."
    )


def _pending_packet_ids(
    packets: Iterable[object],
) -> tuple[str, ...]:
    """Return stable packet ids from a pending-packet iterable."""
    ids: list[str] = []
    for packet in packets:
        raw_id = ""
        if isinstance(packet, dict):
            raw_id = str(packet.get("packet_id") or "").strip()
        else:
            raw_id = str(getattr(packet, "packet_id", "") or "").strip()
        if raw_id:
            ids.append(raw_id)
    return tuple(ids)


def assert_expected_instruction_revision(
    *,
    bridge_text: str,
    expected_instruction_revision: str | None,
    action: str,
) -> None:
    """Fail closed when a caller tries to mutate stale live instruction state."""
    expected = (expected_instruction_revision or "").strip()
    if not expected:
        return
    live_revision = current_instruction_revision_from_bridge_text(bridge_text)
    if live_revision == expected:
        return
    snapshot = extract_bridge_snapshot(bridge_text)
    effective_revision = _normalized_instruction_revision(
        _normalize_instruction_body(
            snapshot.sections.get("Current Instruction For Claude", "")
        )
    )
    if effective_revision == expected:
        return
    raise ValueError(
        f"{action} refused stale bridge write: expected current instruction "
        f"revision `{expected}`, but live bridge revision is "
        f"`{live_revision or 'missing'}`"
        + (
            f" (effective typed revision `{effective_revision}`)."
            if effective_revision and effective_revision != live_revision
            else "."
        )
    )


def assert_expected_implementer_state_hash(
    *,
    bridge_text: str,
    expected_implementer_state_hash: str | None,
    action: str,
) -> None:
    """Fail closed when a reviewer write depends on stale Claude-owned state."""
    expected = (expected_implementer_state_hash or "").strip()
    if not expected:
        return
    live_hash = bridge_implementer_state_hash(extract_bridge_snapshot(bridge_text))
    if live_hash == expected:
        return
    raise ValueError(
        f"{action} refused stale bridge write: expected implementer state hash "
        f"`{expected}`, but live implementer state hash is "
        f"`{live_hash or 'missing'}`."
    )
