"""Typed reconciliation for stale governed remote-control attachments.

This module intentionally operates below the `session_liveness_*` signal and
count projections. The launch incidents were caused by persisted
remote-control attachment files outliving their real processes, and those
files are the layer that carries PID identity and detach-write authority.
Dry-run mode reports stale attachments without mutation; `kill_stale` detaches
stale artifacts and may terminate a live stale PID through the injected
`ProcessKiller`. Review-channel liveness signals remain downstream read models
over the repaired attachment state, not a second cleanup authority.
"""

from __future__ import annotations

import json
import os
import signal
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import NamedTuple

from ..review_channel.remote_control_attachment_artifact import (
    REMOTE_CONTROL_ATTACHMENT_FILENAME_SUFFIX,
    persist_remote_control_attachment,
)
from ..time_utils import utc_timestamp
from .remote_control_attachment_builder import (
    RemoteControlAttachmentBuildInput,
    build_remote_control_attachment_state,
)
from .remote_control_attachment_models import (
    RemoteControlAttachmentState,
    remote_control_attachment_from_mapping,
)
from .remote_control_attachment_status import (
    remote_attachment_expired,
    remote_attachment_has_physical_identity,
    remote_attachment_status,
)

SESSION_LIVENESS_RECONCILER_CONTRACT_ID = "SessionLivenessReconciler"
SESSION_LIVENESS_RECONCILER_SCHEMA_VERSION = 1

ProcessProbe = Callable[[int], bool | None]
ProcessKiller = Callable[[int], str]


class SessionLivenessReconcilerRow(NamedTuple):
    """One persisted session artifact considered by the reconciler."""

    provider: str
    role: str
    source_path: str
    record_kind: str
    session_name: str = ""
    attachment_id: str = ""
    host_pid: int | None = None
    process_live: bool | None = None
    before_status: str = ""
    after_status: str = ""
    stale: bool = False
    action: str = "none"
    reason: str = ""
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = self._asdict()
        payload["evidence_refs"] = list(self.evidence_refs)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True, slots=True)
class SessionLivenessReconciler:
    """Typed answer for stale persisted session attachment cleanup."""

    generated_at_utc: str
    kill_stale: bool
    dry_run: bool
    session_output_root: str
    stale_count: int
    cleared_attachment_count: int
    killed_pid_count: int
    rows: tuple[SessionLivenessReconcilerRow, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    schema_version: int = SESSION_LIVENESS_RECONCILER_SCHEMA_VERSION
    contract_id: str = SESSION_LIVENESS_RECONCILER_CONTRACT_ID

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["ok"] = self.ok
        payload["rows"] = [row.to_dict() for row in self.rows]
        payload["warnings"] = list(self.warnings)
        payload["errors"] = list(self.errors)
        return payload


def reconcile_session_liveness(
    *,
    session_output_root: Path,
    kill_stale: bool = False,
    dry_run: bool = False,
    generated_at_utc: str | None = None,
    process_probe: ProcessProbe | None = None,
    process_killer: ProcessKiller | None = None,
) -> SessionLivenessReconciler:
    """Return the typed cleanup report for persisted attachment liveness.

    The reducer scans `session_output_root/sessions/*-remote-control.json`,
    classifies each attachment with heartbeat, expiry, physical-identity, and
    process-probe evidence, and returns a `SessionLivenessReconciler` containing
    per-artifact rows plus stale/cleared/killed counts. `dry_run=True` never
    mutates attachments. `kill_stale=True` detaches stale attachments and calls
    `process_killer(pid)` only when the attachment still names a live PID.
    Supplying `process_probe` and `process_killer` keeps tests deterministic and
    makes the host-process side effects explicit at the call site.
    """
    timestamp = generated_at_utc or utc_timestamp()
    probe = process_probe or _pid_live
    killer = process_killer or _terminate_pid
    rows: list[SessionLivenessReconcilerRow] = []
    warnings: list[str] = []
    errors: list[str] = []
    cleared = 0
    killed = 0

    for path, attachment in _load_remote_control_attachment_files(session_output_root):
        row, kill_error = _reconcile_attachment(
            attachment=attachment,
            path=path,
            session_output_root=session_output_root,
            now_utc=timestamp,
            kill_stale=kill_stale,
            dry_run=dry_run,
            process_probe=probe,
            process_killer=killer,
        )
        rows.append(row)
        if row.action in {"detached", "would_detach"}:
            cleared += 1 if row.action == "detached" else 0
        if row.action in {"killed_and_detached", "would_kill_and_detach"}:
            cleared += 1 if row.action == "killed_and_detached" else 0
            killed += 1 if row.action == "killed_and_detached" else 0
        if kill_error:
            errors.append(kill_error)

    stale_count = sum(1 for row in rows if row.stale)
    if not session_output_root.exists():
        warnings.append(f"session_output_root_missing:{session_output_root}")
    return SessionLivenessReconciler(
        generated_at_utc=timestamp,
        kill_stale=bool(kill_stale),
        dry_run=bool(dry_run),
        session_output_root=session_output_root.as_posix(),
        stale_count=stale_count,
        cleared_attachment_count=cleared,
        killed_pid_count=killed,
        rows=tuple(rows),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def _reconcile_attachment(
    *,
    attachment: RemoteControlAttachmentState,
    path: Path,
    session_output_root: Path,
    now_utc: str,
    kill_stale: bool,
    dry_run: bool,
    process_probe: ProcessProbe,
    process_killer: ProcessKiller,
) -> tuple[SessionLivenessReconcilerRow, str]:
    host_pid = attachment.host_pid
    process_live = process_probe(host_pid) if host_pid is not None else None
    stale, reason = _attachment_stale_reason(
        attachment=attachment,
        process_live=process_live,
    )
    before_status = remote_attachment_status(attachment)
    after_status = before_status
    action = "none"
    error = ""

    if stale and kill_stale:
        should_kill = host_pid is not None and process_live is True
        if should_kill:
            if dry_run:
                action = "would_kill_and_detach"
                after_status = "detached"
            else:
                error = process_killer(host_pid)
                if not error:
                    killed_attachment = _detached_attachment(
                        attachment=attachment,
                        now_utc=now_utc,
                    )
                    persist_remote_control_attachment(
                        killed_attachment,
                        output_root=session_output_root,
                    )
                    after_status = "detached"
                    action = "killed_and_detached"
                else:
                    action = "kill_failed"
        elif dry_run:
            action = "would_detach"
            after_status = "detached"
        else:
            detached = _detached_attachment(
                attachment=attachment,
                now_utc=now_utc,
            )
            persist_remote_control_attachment(detached, output_root=session_output_root)
            after_status = "detached"
            action = "detached"
    elif stale:
        action = "stale"

    return (
        SessionLivenessReconcilerRow(
            provider=attachment.provider,
            role=attachment.role,
            source_path=path.as_posix(),
            record_kind="remote_control_attachment",
            session_name=attachment.session_name,
            attachment_id=attachment.attachment_id,
            host_pid=host_pid,
            process_live=process_live,
            before_status=before_status,
            after_status=after_status,
            stale=stale,
            action=action,
            reason=reason or "attachment_current",
            evidence_refs=(
                f"remote_control_attachment:{attachment.attachment_id}",
                f"path:{path.as_posix()}",
            ),
        ),
        error,
    )


def _attachment_stale_reason(
    *,
    attachment: RemoteControlAttachmentState,
    process_live: bool | None,
) -> tuple[bool, str]:
    status = remote_attachment_status(attachment)
    if status != "attached":
        return False, "attachment_not_active_status"
    if attachment.host_pid is not None and process_live is False:
        return True, "attachment_pid_not_alive"
    if remote_attachment_expired(attachment):
        return True, "attachment_heartbeat_expired"
    if attachment.host_pid is None and not remote_attachment_has_physical_identity(
        attachment
    ):
        return True, "attachment_missing_liveness_identity"
    return False, "attachment_liveness_current"


def _detached_attachment(
    *,
    attachment: RemoteControlAttachmentState,
    now_utc: str,
) -> RemoteControlAttachmentState:
    detached = build_remote_control_attachment_state(
        RemoteControlAttachmentBuildInput(
            now_utc=now_utc,
            provider=attachment.provider,
            role=attachment.role,
            status="detached",
            session_name=attachment.session_name,
            remote_session_id=attachment.remote_session_id,
            session_url=attachment.session_url,
            metadata_path=attachment.metadata_path,
            launcher_source=attachment.launcher_source,
            host_pid=attachment.host_pid,
            host_session_label=attachment.host_session_label,
            heartbeat_ttl_seconds=attachment.heartbeat_ttl_seconds,
            previous_operator_mode=attachment.previous_operator_mode,
            entrypoint=attachment.entrypoint,
            existing=attachment,
            refresh_existing_identity=True,
        )
    )
    return replace(detached, metadata_path=attachment.metadata_path)


def _load_remote_control_attachment_files(
    output_root: Path,
) -> tuple[tuple[Path, RemoteControlAttachmentState], ...]:
    sessions_dir = output_root / "sessions"
    if not sessions_dir.is_dir():
        return ()
    rows: list[tuple[Path, RemoteControlAttachmentState]] = []
    for path in sorted(sessions_dir.glob(f"*{REMOTE_CONTROL_ATTACHMENT_FILENAME_SUFFIX}")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        attachment = remote_control_attachment_from_mapping(payload)
        if attachment is None:
            continue
        rows.append((path, replace(attachment, metadata_path=path.as_posix())))
    return tuple(rows)


def _pid_live(pid: int) -> bool | None:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None
    return True


def _terminate_pid(pid: int) -> str:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return ""
    except PermissionError:
        return f"permission_denied_killing_pid:{pid}"
    except OSError as exc:
        return f"failed_killing_pid:{pid}:{exc}"
    return ""


__all__ = [
    "SESSION_LIVENESS_RECONCILER_CONTRACT_ID",
    "SESSION_LIVENESS_RECONCILER_SCHEMA_VERSION",
    "SessionLivenessReconciler",
    "SessionLivenessReconcilerRow",
    "reconcile_session_liveness",
]
