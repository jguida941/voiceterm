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
from ...review_channel.state import refresh_status_snapshot
from ...review_channel.turn_authority import build_reviewer_turn_authority
from ..review_channel_command import RuntimePaths


@dataclass(frozen=True, slots=True)
class BridgePollResult:
    """Typed reviewer-owned fields needed by implementer polling."""

    snapshot_id: str
    poll_status: str
    current_verdict: str
    open_findings: str
    current_instruction: str
    current_instruction_revision: str
    reviewer_mode: str
    effective_reviewer_mode: str
    reviewer_freshness: str
    launch_truth: str
    attention_status: str
    recovery_action_allowed: str
    implementation_blocked: bool
    implementation_block_reason: str
    claude_ack_revision: str
    claude_ack_current: bool
    implementer_state_hash: str
    reviewer_accepted_implementer_state_hash: str
    changed_since_last_ack: bool
    reviewed_hash_current: bool | None
    review_needed: bool | None
    next_turn_required: bool
    next_turn_role: str
    next_turn_reason: str
    turn_state_token: str
    diagnosis_status: str = ""
    decision_action_id: str = ""
    decision_command: str = ""
    decision_execution_owner: str = ""
    decision_requires_approval: bool = False
    decision_can_auto_fix: bool = False
    zref: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


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
    authority = build_reviewer_turn_authority(
        snapshot=snapshot,
        bridge_liveness=liveness,
        typed_review_state=typed_review_state,
    )
    return BridgePollResult(
        snapshot_id=authority.snapshot_id,
        poll_status=_section_text(snapshot, "Poll Status"),
        current_verdict=_section_text(snapshot, "Current Verdict"),
        open_findings=_section_text(snapshot, "Open Findings"),
        current_instruction=authority.current_instruction,
        current_instruction_revision=authority.current_instruction_revision,
        reviewer_mode=liveness.reviewer_mode,
        effective_reviewer_mode=authority.effective_reviewer_mode,
        reviewer_freshness=liveness.reviewer_freshness,
        launch_truth=authority.launch_truth,
        attention_status=authority.attention_status,
        recovery_action_allowed=authority.recovery_action_allowed,
        implementation_blocked=authority.implementation_blocked,
        implementation_block_reason=authority.implementation_block_reason,
        claude_ack_revision=authority.claude_ack_revision,
        claude_ack_current=authority.claude_ack_current,
        implementer_state_hash=authority.implementer_state_hash,
        reviewer_accepted_implementer_state_hash=(
            authority.reviewer_accepted_implementer_state_hash
        ),
        changed_since_last_ack=bool(authority.current_instruction_revision)
        and authority.current_instruction_revision != authority.claude_ack_revision,
        reviewed_hash_current=authority.reviewed_hash_current,
        review_needed=authority.review_needed,
        next_turn_required=authority.next_turn_required,
        next_turn_role=authority.next_turn_role,
        next_turn_reason=authority.next_turn_reason,
        turn_state_token=_build_turn_state_token(
            snapshot=snapshot,
            liveness=liveness,
            authority=authority,
        ),
        diagnosis_status=authority.diagnosis_status,
        decision_action_id=authority.decision_action_id,
        decision_command=authority.decision_command,
        decision_execution_owner=authority.decision_execution_owner,
        decision_requires_approval=authority.decision_requires_approval,
        decision_can_auto_fix=authority.decision_can_auto_fix,
        zref=authority.zref,
    )


def load_typed_poll_authority(
    *,
    repo_root: Path,
    paths: RuntimePaths,
) -> dict[str, object] | None:
    """Load the typed review-state authority for bridge-poll turn decisions.

    Primary path: call ``refresh_status_snapshot()`` (the same function that
    ``status``/``doctor``/``startup-context`` use) and read the freshly
    written ``review_state.json``.

    Fallback: if the refresh fails, read the last-known-good
    ``review_state.json`` from disk.  This gives bridge-poll stale but
    typed authority — much better than falling through to empty-string
    heuristics that silently disagree with the rest of the stack.
    """
    bridge_path = paths.bridge_path if isinstance(paths.bridge_path, Path) else None
    review_channel_path = (
        paths.review_channel_path if isinstance(paths.review_channel_path, Path) else None
    )
    status_dir = paths.status_dir if isinstance(paths.status_dir, Path) else None
    if bridge_path is None or review_channel_path is None or status_dir is None:
        return _read_last_known_review_state(status_dir)
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
        return _read_last_known_review_state(status_dir)
    return payload if isinstance(payload, dict) else None


def _read_last_known_review_state(
    status_dir: Path | None,
) -> dict[str, object] | None:
    """Read the last-known-good review_state.json from the status directory."""
    if status_dir is None or not isinstance(status_dir, Path):
        return None
    review_state_path = status_dir / "review_state.json"
    try:
        payload = json.loads(review_state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _build_turn_state_token(
    *,
    snapshot: BridgeSnapshot,
    liveness: BridgeLiveness,
    authority,
) -> str:
    payload = "\0".join(
        [
            authority.snapshot_id,
            _section_text(snapshot, "Poll Status"),
            _section_text(snapshot, "Current Verdict"),
            _section_text(snapshot, "Open Findings"),
            authority.current_instruction_revision,
            liveness.reviewer_mode,
            authority.effective_reviewer_mode,
            authority.attention_status,
            authority.diagnosis_status,
            authority.decision_action_id,
            authority.decision_command,
            _optional_bool_token(authority.claude_ack_current),
            authority.implementer_state_hash,
            authority.reviewer_accepted_implementer_state_hash,
            _optional_bool_token(authority.reviewed_hash_current),
            _optional_bool_token(authority.review_needed),
            authority.next_turn_role,
            authority.next_turn_reason,
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
