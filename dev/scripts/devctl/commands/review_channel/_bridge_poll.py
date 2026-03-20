"""Typed implementer-facing bridge poll action for `devctl review-channel`."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

from ...approval_mode import normalize_approval_mode
from ...review_channel.bridge_validation import validate_live_bridge_contract
from ...review_channel.handoff import (
    BridgeLiveness,
    BridgeSnapshot,
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
from ...review_channel.peer_liveness import CodexPollState, reviewer_mode_is_active
from ...runtime.role_profile import TandemRole
from ...time_utils import utc_timestamp
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths

_BRIDGE_HASH_EXCLUDED_PATHS = ("code_audit.md",)
_ACK_ONLY_ERROR_PREFIXES = (
    "Live `Claude Ack` must include `instruction-rev:",
    "Live `Claude Ack` revision does not match the current reviewer instruction revision.",
)


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


def build_bridge_poll_result(
    bridge_text: str,
    *,
    current_worktree_hash: str | None = None,
) -> BridgePollResult:
    """Build the typed bridge-poll payload from markdown bridge content."""
    snapshot = extract_bridge_snapshot(bridge_text)
    liveness = summarize_bridge_liveness(
        snapshot,
        current_worktree_hash=current_worktree_hash,
    )
    current_instruction_revision = liveness.current_instruction_revision
    claude_ack_revision = liveness.claude_ack_revision
    review_needed = _review_needed(liveness)
    next_turn_required, next_turn_role, next_turn_reason = _derive_next_turn(liveness)
    turn_state_token = _build_turn_state_token(
        snapshot=snapshot,
        liveness=liveness,
        review_needed=review_needed,
        next_turn_role=next_turn_role,
        next_turn_reason=next_turn_reason,
    )
    return BridgePollResult(
        poll_status=_section_text(snapshot, "Poll Status"),
        current_verdict=_section_text(snapshot, "Current Verdict"),
        open_findings=_section_text(snapshot, "Open Findings"),
        current_instruction=_section_text(snapshot, "Current Instruction For Claude"),
        current_instruction_revision=current_instruction_revision,
        reviewer_mode=liveness.reviewer_mode,
        reviewer_freshness=liveness.reviewer_freshness,
        claude_ack_revision=claude_ack_revision,
        claude_ack_current=liveness.claude_ack_current,
        changed_since_last_ack=bool(current_instruction_revision)
        and current_instruction_revision != claude_ack_revision,
        reviewed_hash_current=liveness.reviewed_hash_current,
        review_needed=review_needed,
        next_turn_required=next_turn_required,
        next_turn_role=next_turn_role,
        next_turn_reason=next_turn_reason,
        turn_state_token=turn_state_token,
    )


def run_bridge_poll_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[dict[str, object], int]:
    """Run the typed bridge-poll action."""
    runtime_paths = _coerce_runtime_paths(paths)
    bridge_path = runtime_paths.bridge_path
    if not isinstance(bridge_path, Path):
        return _bridge_poll_error(
            args,
            "review-channel bridge-poll requires a resolved bridge path.",
        )
    if not bridge_path.exists():
        return _bridge_poll_error(
            args,
            f"Markdown bridge path does not exist: {bridge_path}",
        )

    try:
        bridge_text = bridge_path.read_text(encoding="utf-8")
    except OSError as exc:
        return _bridge_poll_error(
            args,
            f"Unable to read markdown bridge: {exc}",
        )

    snapshot = extract_bridge_snapshot(bridge_text)
    errors = _bridge_poll_errors(snapshot)
    payload = build_bridge_poll_result(
        bridge_text,
        current_worktree_hash=_current_worktree_hash(repo_root),
    )
    exit_code = 1 if errors else 0
    report: dict[str, object] = {}
    report["command"] = "review-channel"
    report["timestamp"] = utc_timestamp()
    report["action"] = args.action
    report["ok"] = not errors
    report["exit_ok"] = not errors
    report["exit_code"] = exit_code
    report["execution_mode"] = (
        "markdown-bridge"
        if getattr(args, "execution_mode", "auto") in {"auto", "markdown-bridge"}
        else getattr(args, "execution_mode", "auto")
    )
    report["terminal"] = getattr(args, "terminal", "terminal-app")
    report["terminal_profile_requested"] = getattr(args, "terminal_profile", None)
    report["approval_mode"] = normalize_approval_mode(
        getattr(args, "approval_mode", None),
        dangerous=bool(getattr(args, "dangerous", False)),
    )
    report["dangerous"] = bool(getattr(args, "dangerous", False))
    report["bridge_active"] = True
    report["warnings"] = []
    report["errors"] = errors
    report.update(payload.to_dict())
    return report, exit_code


def _section_text(snapshot: BridgeSnapshot, section_name: str) -> str:
    return snapshot.sections.get(section_name, "").strip()


def _current_worktree_hash(repo_root: Path) -> str | None:
    try:
        return compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=_BRIDGE_HASH_EXCLUDED_PATHS,
        )
    except (OSError, ValueError):
        return None


def _bridge_poll_errors(snapshot: BridgeSnapshot) -> list[str]:
    return [
        error
        for error in validate_live_bridge_contract(snapshot)
        if not error.startswith(_ACK_ONLY_ERROR_PREFIXES)
    ]


def _review_needed(liveness: BridgeLiveness) -> bool | None:
    reviewed_hash_current = liveness.reviewed_hash_current
    if reviewed_hash_current is None:
        return None
    return not reviewed_hash_current


def _derive_next_turn(liveness: BridgeLiveness) -> tuple[bool, str, str]:
    if not reviewer_mode_is_active(liveness.reviewer_mode):
        return False, "", "inactive"
    if liveness.codex_poll_state in {CodexPollState.MISSING, CodexPollState.STALE}:
        return True, TandemRole.REVIEWER.value, "reviewer_heartbeat_stale"
    if not liveness.next_action_present:
        return True, TandemRole.REVIEWER.value, "reviewer_instruction_missing"
    if not liveness.claude_status_present:
        return True, TandemRole.IMPLEMENTER.value, "implementer_status_missing"
    if not liveness.claude_ack_present:
        return True, TandemRole.IMPLEMENTER.value, "implementer_ack_missing"
    if not liveness.claude_ack_current:
        return True, TandemRole.IMPLEMENTER.value, "implementer_ack_stale"
    if liveness.reviewed_hash_current is False:
        return True, TandemRole.REVIEWER.value, "reviewed_hash_stale"
    return False, "", "up_to_date"


def _build_turn_state_token(
    *,
    snapshot: BridgeSnapshot,
    liveness: BridgeLiveness,
    review_needed: bool | None,
    next_turn_role: str,
    next_turn_reason: str,
) -> str:
    payload = "\0".join(
        [
            _section_text(snapshot, "Poll Status"),
            _section_text(snapshot, "Current Verdict"),
            _section_text(snapshot, "Open Findings"),
            liveness.current_instruction_revision,
            liveness.reviewer_mode,
            _optional_bool_token(liveness.claude_ack_current),
            _optional_bool_token(liveness.reviewed_hash_current),
            _optional_bool_token(review_needed),
            next_turn_role,
            next_turn_reason,
        ]
    ).strip("\0")
    if not payload:
        return ""
    return sha256(payload.encode("utf-8")).hexdigest()[:12]


def _optional_bool_token(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "true" if value else "false"


def _bridge_poll_error(args, message: str) -> tuple[dict[str, object], int]:
    report: dict[str, object] = {}
    report["command"] = "review-channel"
    report["timestamp"] = utc_timestamp()
    report["action"] = getattr(args, "action", "bridge-poll")
    report["ok"] = False
    report["exit_ok"] = False
    report["exit_code"] = 2
    report["execution_mode"] = getattr(args, "execution_mode", "auto")
    report["terminal"] = getattr(args, "terminal", "terminal-app")
    report["terminal_profile_requested"] = getattr(args, "terminal_profile", None)
    report["approval_mode"] = normalize_approval_mode(
        getattr(args, "approval_mode", None),
        dangerous=bool(getattr(args, "dangerous", False)),
    )
    report["dangerous"] = bool(getattr(args, "dangerous", False))
    report["bridge_active"] = False
    report["warnings"] = []
    report["errors"] = [message]
    return report, 2
