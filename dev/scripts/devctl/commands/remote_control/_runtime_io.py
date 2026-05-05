"""Runtime/status/IO helpers for the remote-control lifecycle command."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ...common import resolve_repo_path
from ...config import REPO_ROOT
from ...repo_packs import active_path_config
from ...review_channel.remote_control_attachment_artifact import (
    load_remote_control_attachment,
)
from ...review_channel.state import refresh_status_snapshot
from ...runtime.remote_control_attachment_status import (
    remote_attachment_active,
    remote_attachment_age_seconds,
    remote_attachment_expired,
    remote_attachment_ttl_seconds,
)
from ...runtime.remote_control_slash_adapters import (
    build_remote_control_slash_adapter_catalog,
)
from ...runtime.reviewer_runtime_models import RemoteControlAttachmentState
from ...time_utils import utc_timestamp
from ._attachment_upsert import persist_lifecycle_attachment
from ._invocation_logging import (
    LifecycleBeforeState,
    LifecycleInvocationRecord,
    record_lifecycle_invocation,
)
from ._proof_types import RemoteControlSourceProof
from ._session_state_proof import (
    SESSION_STATE_PHYSICAL_METHOD,
    SESSION_STATE_PROOF_CHANNEL,
    ClaudeSessionStateBridgeProof,
    resolve_latest_live_session_state_bridge_proof,
)

TRUSTED_PHYSICAL_CONFIRMATION_METHODS = frozenset(
    {"claude_hook_transcript", "claude_session_state_bridge"}
)


def status_report(
    args: Any,
    *,
    action: str,
    contract_id: str,
) -> tuple[dict[str, Any], int]:
    attachment = load_attachment(args)
    if action in {"status", "doctor"}:
        attachment = reconcile_status_attachment_from_session_state(
            args,
            current=attachment,
        )
    active = remote_attachment_active(attachment)
    expired = remote_attachment_expired(attachment)
    report: dict[str, Any] = {}
    report["command"] = "remote-control"
    report["action"] = action
    report["ok"] = True
    report["contract_id"] = contract_id
    report["observed_at_utc"] = utc_timestamp()
    report["provider"] = str(getattr(args, "provider", "claude") or "claude")
    report["operator_interaction_mode"] = (
        "remote_control" if active else "local_terminal"
    )
    report["attachment_active"] = active
    report["attachment_expired"] = expired
    report["attachment_age_seconds"] = remote_attachment_age_seconds(attachment)
    report["heartbeat_ttl_seconds"] = remote_attachment_ttl_seconds(attachment)
    report["status_dir"] = str(status_dir(args))
    report["slash_entrypoints"] = slash_entrypoints()
    report["launcher_command"] = []
    report["provider_remote_control_command"] = "/remote-control"
    report["attachment"] = asdict(attachment) if attachment is not None else None
    if expired:
        report["warnings"] = ["remote-control attachment heartbeat expired"]
    return report, 0


def persist_attachment(
    args: Any,
    *,
    status: str,
    existing: RemoteControlAttachmentState | None = None,
) -> tuple[RemoteControlAttachmentState, Path]:
    """Resolve current attachment + status_dir, then delegate."""
    return persist_lifecycle_attachment(
        args,
        status=status,
        status_dir=status_dir(args),
        existing=existing or load_attachment(args),
    )


def load_attachment(args: Any) -> RemoteControlAttachmentState | None:
    return load_remote_control_attachment(
        output_root=status_dir(args),
        provider=str(getattr(args, "provider", "claude") or "claude"),
    )


def record_invocation(
    args: Any,
    *,
    action: str,
    attachment: RemoteControlAttachmentState | None,
    report: dict[str, Any],
    before: LifecycleBeforeState | None = None,
    state_change: str = "",
) -> None:
    error_message = _error_message_from_report(report)
    record_lifecycle_invocation(
        args,
        record=LifecycleInvocationRecord(
            action=action,
            attachment=attachment,
            report=report,
            before=before or LifecycleBeforeState(),
            state_change=state_change,
            error_message=error_message,
        ),
        repo_root=REPO_ROOT,
        status_dir=status_dir(args),
    )


def slash_entrypoints() -> list[str]:
    """Return the canonical + alias slash commands from the typed catalog."""
    rows = build_remote_control_slash_adapter_catalog()
    canonical = [row.slash_command for row in rows if not row.compatibility_alias]
    aliases = [row.slash_command for row in rows if row.compatibility_alias]
    return canonical + aliases


def status_dir(args: Any) -> Path:
    override = str(getattr(args, "status_dir", "") or "").strip()
    if override:
        return resolve_repo_path(override, repo_root=REPO_ROOT)
    return REPO_ROOT / active_path_config().review_status_dir_rel


def refresh_status_snapshot_if_possible(args: Any) -> bool:
    config = active_path_config()
    bridge_path = REPO_ROOT / config.bridge_rel
    review_channel_path = REPO_ROOT / config.review_channel_rel
    if not bridge_path.exists() or not review_channel_path.exists():
        return False
    refresh_status_snapshot(
        repo_root=REPO_ROOT,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir(args),
        execution_mode="markdown-bridge",
        warnings=[],
        errors=[],
    )
    return True


def reconcile_status_attachment_from_session_state(
    args: Any,
    *,
    current: RemoteControlAttachmentState | None,
) -> RemoteControlAttachmentState | None:
    """Refresh status/doctor from Claude's live session-state bridge proof."""
    if str(getattr(args, "provider", "claude") or "claude") != "claude":
        return current
    proof = resolve_latest_live_session_state_bridge_proof(
        now_utc=utc_timestamp(),
        expected_cwd=str(REPO_ROOT),
        max_age_seconds=remote_attachment_ttl_seconds(current),
    )
    if proof is not None:
        proof_args = _args_with_session_state_proof(args, proof)
        refreshed, _artifact_path = persist_attachment(
            proof_args,
            status="attached",
            existing=current,
        )
        refresh_status_snapshot_if_possible(proof_args)
        return refreshed
    if _session_state_owned_attachment(current):
        cleared, _artifact_path = persist_attachment(
            args,
            status="evidence_missing",
            existing=current,
        )
        refresh_status_snapshot_if_possible(args)
        return cleared
    return current


def action(args: Any) -> str:
    return str(
        getattr(args, "action_flag", "") or getattr(args, "action", "") or "status"
    ).strip()


def args_with_source_proof(
    args: Any,
    proof: RemoteControlSourceProof,
) -> Any:
    if proof.proven_source_kind == "unspecified":
        return args
    values = dict(vars(args)) if hasattr(args, "__dict__") else {}
    if not values:
        return args
    if proof.session_url and not str(values.get("session_url") or "").strip():
        values["session_url"] = proof.session_url
    if proof.remote_session_id and not str(values.get("remote_session_id") or "").strip():
        values["remote_session_id"] = proof.remote_session_id
    values["provider_session_id"] = proof.provider_session_id
    values["proven_source_kind"] = proof.proven_source_kind
    values["physical_confirmation_method"] = proof.physical_confirmation_method
    if proof.physical_confirmation_method in TRUSTED_PHYSICAL_CONFIRMATION_METHODS:
        values["physical_remote_control_confirmed"] = True
    if not str(values.get("invocation_origin") or "").strip():
        values["invocation_origin"] = proof.proven_source_kind
    values["source_proof_channel"] = proof.proof_channel
    values["source_proof_observed_at_utc"] = proof.proof_observed_at_utc
    values["source_hook_event_name"] = proof.hook_event_name
    values["source_hook_prompt"] = proof.hook_prompt
    values["source_hook_command_name"] = proof.hook_command_name
    values["source_hook_session_id"] = proof.hook_session_id
    values["source_hook_transcript_path"] = proof.hook_transcript_path
    values["source_hook_dedupe_key"] = proof.hook_dedupe_key
    return SimpleNamespace(**values)


def _args_with_session_state_proof(
    args: Any,
    proof: ClaudeSessionStateBridgeProof,
) -> Any:
    values = dict(vars(args)) if hasattr(args, "__dict__") else {}
    if not values:
        return args
    values["session_url"] = proof.session_url
    values["remote_session_id"] = proof.bridge_session_id
    values["provider_session_id"] = f"claude-code:{proof.session_id}"
    values["proven_source_kind"] = "claude_builtin_slash"
    values["physical_confirmation_method"] = SESSION_STATE_PHYSICAL_METHOD
    values["physical_remote_control_confirmed"] = True
    values["invocation_origin"] = "claude_builtin_slash"
    values["source_proof_channel"] = SESSION_STATE_PROOF_CHANNEL
    values["source_proof_observed_at_utc"] = proof.updated_at_utc
    values["source_hook_session_id"] = proof.session_id
    return SimpleNamespace(**values)


def _session_state_owned_attachment(
    attachment: RemoteControlAttachmentState | None,
) -> bool:
    if attachment is None:
        return False
    return (
        str(attachment.source_proof_channel or "").strip()
        == SESSION_STATE_PROOF_CHANNEL
    )


def _error_message_from_report(report: dict[str, Any]) -> str:
    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        return str(errors[0] or "").strip()
    return ""


__all__ = [
    "action",
    "args_with_source_proof",
    "load_attachment",
    "persist_attachment",
    "record_invocation",
    "refresh_status_snapshot_if_possible",
    "reconcile_status_attachment_from_session_state",
    "status_report",
]
