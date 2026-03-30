"""Focused helpers for typed bridge-poll authority."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path

from ...review_channel.handoff import (
    BridgeLiveness,
    BridgeSnapshot,
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from ...review_channel.peer_liveness import (
    CodexPollState,
    REVIEWER_WAIT_STATE_MARKERS,
    reviewer_mode_is_active,
)
from ...review_channel.state import refresh_status_snapshot
from ...runtime.role_profile import TandemRole
from ..review_channel_command import RuntimePaths


@dataclass(frozen=True, slots=True)
class BridgePollResult:
    """Typed reviewer-owned fields needed by implementer polling."""

    poll_status: str
    current_verdict: str
    open_findings: str
    current_instruction: str
    current_instruction_revision: str
    reviewer_mode: str
    reviewer_freshness: str
    claude_ack_revision: str
    claude_ack_current: bool
    changed_since_last_ack: bool
    reviewed_hash_current: bool | None
    review_needed: bool | None
    next_turn_required: bool
    next_turn_role: str
    next_turn_reason: str
    turn_state_token: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _BridgePollAuthority:
    current_instruction: str
    current_instruction_revision: str
    claude_ack_revision: str
    claude_ack_current: bool
    reviewed_hash_current: bool | None
    review_needed: bool | None


@dataclass(frozen=True, slots=True)
class _BridgeTurnState:
    required: bool
    role: str
    reason: str


def build_bridge_poll_result(
    bridge_text: str,
    *,
    current_worktree_hash: str | None = None,
    typed_review_state: Mapping[str, object] | None = None,
) -> BridgePollResult:
    """Build the typed bridge-poll payload from markdown bridge content."""
    snapshot = extract_bridge_snapshot(bridge_text)
    liveness = summarize_bridge_liveness(
        snapshot,
        current_worktree_hash=current_worktree_hash,
    )
    authority = _bridge_poll_authority(
        snapshot=snapshot,
        liveness=liveness,
        typed_review_state=typed_review_state,
    )
    next_turn = _derive_next_turn_state(
        snapshot=snapshot,
        liveness=liveness,
        authority=authority,
    )
    return BridgePollResult(
        poll_status=_section_text(snapshot, "Poll Status"),
        current_verdict=_section_text(snapshot, "Current Verdict"),
        open_findings=_section_text(snapshot, "Open Findings"),
        current_instruction=authority.current_instruction,
        current_instruction_revision=authority.current_instruction_revision,
        reviewer_mode=liveness.reviewer_mode,
        reviewer_freshness=liveness.reviewer_freshness,
        claude_ack_revision=authority.claude_ack_revision,
        claude_ack_current=authority.claude_ack_current,
        changed_since_last_ack=bool(authority.current_instruction_revision)
        and authority.current_instruction_revision != authority.claude_ack_revision,
        reviewed_hash_current=authority.reviewed_hash_current,
        review_needed=authority.review_needed,
        next_turn_required=next_turn.required,
        next_turn_role=next_turn.role,
        next_turn_reason=next_turn.reason,
        turn_state_token=_build_turn_state_token(
            snapshot=snapshot,
            liveness=liveness,
            authority=authority,
            next_turn=next_turn,
        ),
    )


def load_typed_poll_authority(
    *,
    repo_root: Path,
    paths: RuntimePaths,
) -> dict[str, object] | None:
    bridge_path = paths.bridge_path if isinstance(paths.bridge_path, Path) else None
    review_channel_path = (
        paths.review_channel_path if isinstance(paths.review_channel_path, Path) else None
    )
    status_dir = paths.status_dir if isinstance(paths.status_dir, Path) else None
    if bridge_path is None or review_channel_path is None or status_dir is None:
        return None
    try:
        snapshot = refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=status_dir,
            promotion_plan_path=paths.promotion_plan_path,
            execution_mode="markdown-bridge",
        )
        payload = json.loads(
            Path(snapshot.projection_paths.review_state_path).read_text(
                encoding="utf-8"
            )
        )
    except (OSError, TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _bridge_poll_authority(
    *,
    snapshot: BridgeSnapshot,
    liveness: BridgeLiveness,
    typed_review_state: Mapping[str, object] | None,
) -> _BridgePollAuthority:
    typed_review_state = typed_review_state or {}
    current_session = _mapping(typed_review_state.get("current_session"))
    bridge_state = _mapping(typed_review_state.get("bridge"))
    claude_ack_current = _typed_bool(bridge_state, "claude_ack_current")
    if claude_ack_current is None:
        claude_ack_current = liveness.claude_ack_current
    reviewed_hash_current = _typed_bool(bridge_state, "reviewed_hash_current")
    if reviewed_hash_current is None:
        reviewed_hash_current = liveness.reviewed_hash_current
    review_needed = _typed_bool(bridge_state, "review_needed")
    if review_needed is None:
        review_needed = _review_needed(liveness)
    return _BridgePollAuthority(
        current_instruction=(
            str(current_session.get("current_instruction") or "").strip()
            or _section_text(snapshot, "Current Instruction For Claude")
        ),
        current_instruction_revision=(
            str(current_session.get("current_instruction_revision") or "").strip()
            or liveness.current_instruction_revision
        ),
        claude_ack_revision=(
            str(current_session.get("implementer_ack_revision") or "").strip()
            or liveness.claude_ack_revision
        ),
        claude_ack_current=claude_ack_current,
        reviewed_hash_current=reviewed_hash_current,
        review_needed=review_needed,
    )


def _review_needed(liveness: BridgeLiveness) -> bool | None:
    reviewed_hash_current = liveness.reviewed_hash_current
    if reviewed_hash_current is None:
        return None
    return not reviewed_hash_current


def _derive_next_turn_state(
    *,
    snapshot: BridgeSnapshot,
    liveness: BridgeLiveness,
    authority: _BridgePollAuthority,
) -> _BridgeTurnState:
    if not reviewer_mode_is_active(liveness.reviewer_mode):
        return _BridgeTurnState(False, "", "inactive")
    if liveness.codex_poll_state in {CodexPollState.MISSING, CodexPollState.STALE}:
        return _BridgeTurnState(
            True,
            TandemRole.REVIEWER.value,
            "reviewer_heartbeat_stale",
        )
    if not liveness.next_action_present:
        return _BridgeTurnState(
            True,
            TandemRole.REVIEWER.value,
            "reviewer_instruction_missing",
        )
    if not liveness.claude_status_present:
        return _BridgeTurnState(
            True,
            TandemRole.IMPLEMENTER.value,
            "implementer_status_missing",
        )
    if not liveness.claude_ack_present:
        return _BridgeTurnState(
            True,
            TandemRole.IMPLEMENTER.value,
            "implementer_ack_missing",
        )
    if not authority.claude_ack_current:
        return _BridgeTurnState(
            True,
            TandemRole.IMPLEMENTER.value,
            "implementer_ack_stale",
        )
    if authority.reviewed_hash_current is False:
        return _BridgeTurnState(
            True,
            TandemRole.REVIEWER.value,
            "review_follow_up_required",
        )
    if _reviewer_wait_state(snapshot=snapshot, authority=authority):
        return _BridgeTurnState(
            True,
            TandemRole.REVIEWER.value,
            "reviewer_wait_state",
        )
    return _BridgeTurnState(False, "", "up_to_date")


def _reviewer_wait_state(
    *,
    snapshot: BridgeSnapshot,
    authority: _BridgePollAuthority,
) -> bool:
    if not authority.claude_ack_current:
        return False
    haystack = "\n".join(
        [
            authority.current_instruction,
            _section_text(snapshot, "Poll Status"),
        ]
    ).lower()
    return any(marker in haystack for marker in REVIEWER_WAIT_STATE_MARKERS)


def _build_turn_state_token(
    *,
    snapshot: BridgeSnapshot,
    liveness: BridgeLiveness,
    authority: _BridgePollAuthority,
    next_turn: _BridgeTurnState,
) -> str:
    payload = "\0".join(
        [
            _section_text(snapshot, "Poll Status"),
            _section_text(snapshot, "Current Verdict"),
            _section_text(snapshot, "Open Findings"),
            authority.current_instruction_revision,
            liveness.reviewer_mode,
            _optional_bool_token(authority.claude_ack_current),
            _optional_bool_token(authority.reviewed_hash_current),
            _optional_bool_token(authority.review_needed),
            next_turn.role,
            next_turn.reason,
        ]
    ).strip("\0")
    if not payload:
        return ""
    return sha256(payload.encode("utf-8")).hexdigest()[:12]


def _section_text(snapshot: BridgeSnapshot, section_name: str) -> str:
    return snapshot.sections.get(section_name, "").strip()


def _optional_bool_token(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "true" if value else "false"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _typed_bool(mapping: Mapping[str, object], key: str) -> bool | None:
    value = mapping.get(key)
    if isinstance(value, bool):
        return value
    return None
