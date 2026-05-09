"""Typed implementer-facing bridge poll action for `devctl review-channel`."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...approval_mode import normalize_approval_mode
from ...review_channel.ack_contract import ACK_REVISION_REQUIREMENT_PREFIX
from ...review_channel.bridge_validation import validate_live_bridge_contract
from ...review_channel.handoff import (
    BridgeSnapshot,
    extract_bridge_snapshot,
)
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
from ...time_utils import utc_timestamp
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
from ._bridge_poll_support import (
    BridgePollResult,
    build_bridge_poll_result,
    load_typed_poll_authority,
)

_ACK_ONLY_ERROR_PREFIXES = (
    ACK_REVISION_REQUIREMENT_PREFIX,
    "Live implementer ACK (`Implementer Ack`) revision does not match the current reviewer instruction revision.",
    "Live `Claude Ack` revision does not match the current reviewer instruction revision.",
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
    typed_review_state = load_typed_poll_authority(
        repo_root=repo_root,
        paths=runtime_paths,
    )
    errors = _bridge_poll_errors(snapshot, typed_review_state=typed_review_state)
    warnings = _bridge_poll_warnings(typed_review_state)
    payload = build_bridge_poll_result(
        bridge_text,
        current_worktree_hash=_current_worktree_hash(
            repo_root, bridge_rel=str(bridge_path.relative_to(repo_root)),
        ),
        typed_review_state=typed_review_state,
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
    report["warnings"] = warnings
    report["errors"] = errors
    report.update(payload.to_dict())
    return report, exit_code


def _section_text(snapshot: BridgeSnapshot, section_name: str) -> str:
    return snapshot.sections.get(section_name, "").strip()


def _current_worktree_hash(repo_root: Path, *, bridge_rel: str) -> str | None:
    try:
        return compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=(bridge_rel,),
        )
    except (OSError, ValueError):
        return None


def _bridge_poll_errors(
    snapshot: BridgeSnapshot,
    *,
    typed_review_state: Mapping[str, object] | None = None,
) -> list[str]:
    errors = [
        error
        for error in validate_live_bridge_contract(snapshot)
        if not error.startswith(_ACK_ONLY_ERROR_PREFIXES)
    ]
    for error in _typed_messages(typed_review_state, field_name="errors"):
        if error not in errors:
            errors.append(error)
    return errors


def _bridge_poll_warnings(
    typed_review_state: Mapping[str, object] | None,
) -> list[str]:
    return _typed_messages(typed_review_state, field_name="warnings")


def _typed_messages(
    typed_review_state: Mapping[str, object] | None,
    *,
    field_name: str,
) -> list[str]:
    if not isinstance(typed_review_state, Mapping):
        return []
    values = typed_review_state.get(field_name)
    if not isinstance(values, list):
        return []
    messages: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in messages:
            messages.append(text)
    return messages


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
