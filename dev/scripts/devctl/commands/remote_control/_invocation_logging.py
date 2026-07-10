"""Lifecycle invocation logging for the remote-control command surface.

Per rev_pkt_2987 / rev_pkt_2988 priority #3: every start/enter/heartbeat/
exit invocation leaves a typed ``RemoteControlInvocationReceipt`` so silent
slash-adapter failures are distinguishable from "never invoked." Extracted
from ``command.py`` to keep that module under the shape budget.

Per rev_pkt_2996 finding #2 (schema_version=2): receipts now capture
before/after attachment_status and operator_interaction_mode plus a typed
``state_change``. Per finding #4: receipt write success/failure is
surfaced into the lifecycle report so audit-evidence loss is visible
rather than silently swallowed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...runtime.remote_control_invocation_receipt import (
    DEFAULT_REMOTE_CONTROL_INVOCATION_REL,
    RemoteControlInvocationInput,
    record_remote_control_invocation,
)
from ...runtime.reviewer_runtime_models import RemoteControlAttachmentState
from ...time_utils import utc_timestamp


@dataclass(frozen=True, slots=True)
class LifecycleBeforeState:
    """Pre-invocation snapshot captured before an upsert mutates state.

    Carried into ``record_lifecycle_invocation`` so receipts prove what the
    typed attachment looked like immediately before this lifecycle call,
    independent of the call's outcome.
    """

    attachment_status: str = ""
    attachment_id: str = ""
    operator_interaction_mode: str = ""


@dataclass(frozen=True, slots=True)
class LifecycleInvocationRecord:
    action: str
    attachment: RemoteControlAttachmentState | None
    report: dict[str, Any]
    before: LifecycleBeforeState
    state_change: str = ""
    error_message: str = ""


def record_lifecycle_invocation(
    args: Any,
    *,
    record: LifecycleInvocationRecord,
    repo_root: Path,
    status_dir: Path,
) -> None:
    """Append a typed RemoteControlInvocationReceipt for one lifecycle action.

    Best-effort with explicit accounting: receipt write must not break the
    lifecycle action even if the state dir is unavailable, but the lifecycle
    report carries ``invocation_receipt_recorded``, ``invocation_receipt_path``,
    and ``invocation_receipt_error`` so silent loss of audit evidence is
    visible to readers (per rev_pkt_2996 finding #4).
    """
    receipt_root = _receipt_root(repo_root=repo_root, status_dir=status_dir)
    receipt_path = receipt_root / DEFAULT_REMOTE_CONTROL_INVOCATION_REL
    record.report["invocation_receipt_path"] = str(receipt_path)
    snapshot = record.before
    try:
        record_remote_control_invocation(
            RemoteControlInvocationInput(
                repo_root=receipt_root,
                invocation_at_utc=str(
                    record.report.get("observed_at_utc") or utc_timestamp()
                ),
                action=record.action,
                provider=str(getattr(args, "provider", "claude") or "claude"),
                entrypoint=str(getattr(args, "entrypoint", "") or "").strip(),
                launcher_source=str(
                    getattr(args, "launcher_source", "") or ""
                ).strip(),
                target_status_dir=str(status_dir),
                attachment=record.attachment,
                operator_interaction_mode=str(
                    record.report.get("operator_interaction_mode") or ""
                ),
                before_attachment_status=snapshot.attachment_status,
                before_operator_interaction_mode=(
                    snapshot.operator_interaction_mode
                ),
                before_attachment_id=snapshot.attachment_id,
                state_change=record.state_change,
                ok=bool(record.report.get("ok", True)),
                dry_run=bool(record.report.get("dry_run", False)),
                invocation_source=str(
                    getattr(args, "entrypoint", "") or ""
                ).strip(),
                proven_source_kind=str(
                    getattr(args, "proven_source_kind", "") or ""
                ).strip(),
                invocation_origin=str(
                    getattr(args, "proven_source_kind", "") or ""
                ).strip(),
                error_message=record.error_message,
                proof_channel=str(
                    getattr(args, "source_proof_channel", "") or ""
                ).strip(),
                physical_confirmation_method=_physical_confirmation_method(
                    args=args,
                    attachment=record.attachment,
                ),
                hook_event_name=str(
                    getattr(args, "source_hook_event_name", "") or ""
                ).strip(),
                hook_prompt=str(getattr(args, "source_hook_prompt", "") or "").strip(),
                hook_command_name=str(
                    getattr(args, "source_hook_command_name", "") or ""
                ).strip(),
                hook_session_id=str(
                    getattr(args, "source_hook_session_id", "") or ""
                ).strip(),
                hook_transcript_path=str(
                    getattr(args, "source_hook_transcript_path", "") or ""
                ).strip(),
                hook_dedupe_key=str(
                    getattr(args, "source_hook_dedupe_key", "") or ""
                ).strip(),
            ),
        )
    except OSError as exc:
        record.report["invocation_receipt_recorded"] = False
        record.report["invocation_receipt_error"] = str(exc)
        return
    record.report["invocation_receipt_recorded"] = True
    record.report["invocation_receipt_error"] = ""


def _receipt_root(*, repo_root: Path, status_dir: Path) -> Path:
    """Keep test/portable status-dir receipts out of repo-global state."""
    try:
        status_dir.relative_to(repo_root)
    except ValueError:
        return status_dir
    return repo_root


def _physical_confirmation_method(
    *,
    args: Any,
    attachment: RemoteControlAttachmentState | None,
) -> str:
    method = str(getattr(args, "physical_confirmation_method", "") or "").strip()
    if not method and attachment is not None:
        method = str(attachment.physical_confirmation_method or "").strip()
    return method or "none"


__all__ = [
    "LifecycleBeforeState",
    "LifecycleInvocationRecord",
    "record_lifecycle_invocation",
]
