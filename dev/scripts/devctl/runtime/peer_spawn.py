"""Canonical typed peer-spawn driver.

This module is the single repo-owned entry point for launching or terminating
a provider conductor (codex / claude / cursor) as a peer session. It composes
the existing canonical launch path (`build_launch_sessions` +
`launch_sessions_headless`) under a typed BypassReceipt gate and emits typed
`AgentSpawnRequest` / `AgentSpawnReceipt` / `AgentTerminationReceipt` events
into the review-channel event log.

The CLI surface is `devctl peer-spawn` / `devctl peer-terminate`; both are thin
wrappers around the functions defined here. No subprocess.Popen call to a
provider CLI should live outside this module's `compose_peer_spawn` path.

Design contract:

- Bypass authority is enforced via the typed BypassReceipt (scope must include
  `agent_spawn_only`). Without an active receipt, the driver fails closed and
  emits an `AgentSpawnReceipt` with `status="denied_bypass_missing"`.
- The trace event log path is configurable for tests; default resolves to the
  canonical review-channel `events/trace.ndjson`.
- Spawn delegates to `launch_sessions_headless`; terminate signals the running
  PID with SIGTERM by default and emits a typed receipt either way.
"""

from __future__ import annotations

import json
import os
import signal as _signal_mod
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Optional

from ..config import REPO_ROOT
from ..time_utils import utc_timestamp
from .bypass_lifecycle_registry import (
    BypassAuthorityScope,
    BypassReceipt,
    bypass_receipt_active,
    bypass_receipt_grants_scope,
)

AGENT_SPAWN_REQUEST_CONTRACT_ID = "AgentSpawnRequest"
AGENT_SPAWN_RECEIPT_CONTRACT_ID = "AgentSpawnReceipt"
AGENT_TERMINATION_RECEIPT_CONTRACT_ID = "AgentTerminationReceipt"
PEER_SPAWN_SCHEMA_VERSION = 1

DEFAULT_PEER_SPAWN_TRACE_REL = Path("dev/reports/review_channel/events/trace.ndjson")

SUPPORTED_PROVIDERS: tuple[str, ...] = ("codex", "claude", "cursor")
SUPPORTED_ROLES: tuple[str, ...] = ("implementer", "reviewer", "observer")
DEFAULT_PEER_SPAWN_ACTOR = "operator"


@dataclass(frozen=True, slots=True)
class AgentSpawnRequest:
    """Typed request to spawn a provider conductor as a peer session."""

    provider: str
    role: str
    bypass_receipt_id: str
    row_id: str
    actor: str
    requested_at_utc: str
    reason: str = ""
    interaction_mode: str = "remote_control"
    headless: bool = True
    schema_version: int = PEER_SPAWN_SCHEMA_VERSION
    contract_id: str = AGENT_SPAWN_REQUEST_CONTRACT_ID

    def to_event(self) -> dict[str, object]:
        return {
            "event_type": "agent_spawn_requested",
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "provider": self.provider,
            "role": self.role,
            "bypass_receipt_id": self.bypass_receipt_id,
            "row_id": self.row_id,
            "actor": self.actor,
            "requested_at_utc": self.requested_at_utc,
            "reason": self.reason,
            "interaction_mode": self.interaction_mode,
            "headless": self.headless,
        }


@dataclass(frozen=True, slots=True)
class AgentSpawnReceipt:
    """Typed receipt recording the outcome of one peer-spawn attempt."""

    request_id: str
    provider: str
    role: str
    bypass_receipt_id: str
    row_id: str
    status: str
    issued_at_utc: str
    pid: int = 0
    script_path: str = ""
    reason: str = ""
    error: str = ""
    schema_version: int = PEER_SPAWN_SCHEMA_VERSION
    contract_id: str = AGENT_SPAWN_RECEIPT_CONTRACT_ID

    def to_event(self) -> dict[str, object]:
        return {
            "event_type": "agent_spawn_receipt",
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "provider": self.provider,
            "role": self.role,
            "bypass_receipt_id": self.bypass_receipt_id,
            "row_id": self.row_id,
            "status": self.status,
            "issued_at_utc": self.issued_at_utc,
            "pid": self.pid,
            "script_path": self.script_path,
            "reason": self.reason,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class AgentTerminationReceipt:
    """Typed receipt recording the outcome of one peer-terminate attempt."""

    request_id: str
    provider: str
    session_id: str
    pid: int
    signal: str
    status: str
    issued_at_utc: str
    actor: str = DEFAULT_PEER_SPAWN_ACTOR
    reason: str = ""
    error: str = ""
    schema_version: int = PEER_SPAWN_SCHEMA_VERSION
    contract_id: str = AGENT_TERMINATION_RECEIPT_CONTRACT_ID

    def to_event(self) -> dict[str, object]:
        return {
            "event_type": "agent_termination_receipt",
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "provider": self.provider,
            "session_id": self.session_id,
            "pid": self.pid,
            "signal": self.signal,
            "status": self.status,
            "issued_at_utc": self.issued_at_utc,
            "actor": self.actor,
            "reason": self.reason,
            "error": self.error,
        }


@dataclass(slots=True)
class PeerSpawnReport:
    """Typed report bundle the CLI emits for one peer-spawn call."""

    ok: bool
    action: str
    request: dict[str, object] | None = None
    receipt: dict[str, object] | None = None
    trace_path: str = ""
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    canonical_command_hint: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["errors"] = list(self.errors)
        payload["warnings"] = list(self.warnings)
        return payload


def append_event(trace_path: Path, event: dict[str, object]) -> None:
    """Append one typed event row to the peer-spawn trace log."""
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, sort_keys=True) + "\n"
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def resolve_trace_path(
    trace_path: Path | str | None = None,
    *,
    repo_root: Path = REPO_ROOT,
) -> Path:
    """Resolve the trace path used by peer-spawn for typed event emission."""
    if isinstance(trace_path, Path):
        return trace_path
    raw = str(trace_path or "").strip()
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = repo_root / path
        return path
    return repo_root / DEFAULT_PEER_SPAWN_TRACE_REL


def _validate_bypass_receipt(
    receipt: BypassReceipt | None,
    *,
    required_scope: BypassAuthorityScope = BypassAuthorityScope.AGENT_SPAWN_ONLY,
) -> tuple[bool, str]:
    """Return (ok, reason) for whether the receipt grants spawn authority."""
    if receipt is None:
        return False, "bypass_receipt_missing"
    if not bypass_receipt_active(receipt):
        return False, "bypass_receipt_not_active"
    if not bypass_receipt_grants_scope(receipt, required_scope):
        return False, f"bypass_receipt_scope_insufficient:{required_scope.value}"
    return True, ""


def _request_id(*, provider: str, role: str, at_utc: str) -> str:
    stamp = at_utc.replace(":", "").replace("-", "").replace(".", "")
    return f"peer_spawn_{provider}_{role}_{stamp}"


def compose_peer_spawn(
    *,
    provider: str,
    role: str,
    bypass_receipt: Optional[BypassReceipt],
    row_id: str = "",
    actor: str = DEFAULT_PEER_SPAWN_ACTOR,
    reason: str = "",
    interaction_mode: str = "remote_control",
    headless: bool = True,
    trace_path: Path | str | None = None,
    repo_root: Path = REPO_ROOT,
    launch_callable: Callable[..., tuple[bool, int, str, str]] | None = None,
    now_utc: str | None = None,
    task_prompt: str = "",
) -> PeerSpawnReport:
    """Canonical peer-spawn composer.

    `launch_callable` is the dependency-injected boundary that talks to the
    underlying canonical launch path. It must return
    ``(launched, pid, script_path, error)``. The CLI handler injects an
    adapter that calls `build_launch_sessions` + `launch_sessions_headless`.
    """
    timestamp = now_utc or utc_timestamp()
    trace = resolve_trace_path(trace_path, repo_root=repo_root)
    canonical_hint = _canonical_hint(provider=provider, role=role)
    if provider not in SUPPORTED_PROVIDERS:
        return PeerSpawnReport(
            ok=False,
            action="peer-spawn",
            trace_path=str(trace),
            errors=(f"unsupported_provider:{provider}",),
            canonical_command_hint=canonical_hint,
        )
    if role not in SUPPORTED_ROLES:
        return PeerSpawnReport(
            ok=False,
            action="peer-spawn",
            trace_path=str(trace),
            errors=(f"unsupported_role:{role}",),
            canonical_command_hint=canonical_hint,
        )

    request = AgentSpawnRequest(
        provider=provider,
        role=role,
        bypass_receipt_id=(bypass_receipt.receipt_id if bypass_receipt else ""),
        row_id=row_id,
        actor=actor,
        requested_at_utc=timestamp,
        reason=reason,
        interaction_mode=interaction_mode,
        headless=headless,
    )
    append_event(trace, request.to_event())
    request_id = _request_id(provider=provider, role=role, at_utc=timestamp)

    ok, deny_reason = _validate_bypass_receipt(bypass_receipt)
    if not ok:
        denied = AgentSpawnReceipt(
            request_id=request_id,
            provider=provider,
            role=role,
            bypass_receipt_id=request.bypass_receipt_id,
            row_id=row_id,
            status="denied_bypass_missing",
            issued_at_utc=timestamp,
            reason=deny_reason,
        )
        append_event(trace, denied.to_event())
        return PeerSpawnReport(
            ok=False,
            action="peer-spawn",
            request=request.to_event(),
            receipt=denied.to_event(),
            trace_path=str(trace),
            errors=(deny_reason,),
            canonical_command_hint=canonical_hint,
        )

    if launch_callable is None:
        receipt = AgentSpawnReceipt(
            request_id=request_id,
            provider=provider,
            role=role,
            bypass_receipt_id=request.bypass_receipt_id,
            row_id=row_id,
            status="dry_run_no_launch_callable",
            issued_at_utc=timestamp,
            reason="no_launch_adapter_injected",
        )
        append_event(trace, receipt.to_event())
        return PeerSpawnReport(
            ok=True,
            action="peer-spawn",
            request=request.to_event(),
            receipt=receipt.to_event(),
            trace_path=str(trace),
            warnings=("no_launch_adapter_injected",),
            canonical_command_hint=canonical_hint,
        )

    try:
        launched, pid, script_path, launch_error = launch_callable(
            provider=provider,
            role=role,
            row_id=row_id,
            bypass_receipt=bypass_receipt,
            interaction_mode=interaction_mode,
            headless=headless,
            repo_root=repo_root,
            task_prompt=task_prompt,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        receipt = AgentSpawnReceipt(
            request_id=request_id,
            provider=provider,
            role=role,
            bypass_receipt_id=request.bypass_receipt_id,
            row_id=row_id,
            status="spawn_failed",
            issued_at_utc=timestamp,
            reason="launch_adapter_raised",
            error=str(exc),
        )
        append_event(trace, receipt.to_event())
        return PeerSpawnReport(
            ok=False,
            action="peer-spawn",
            request=request.to_event(),
            receipt=receipt.to_event(),
            trace_path=str(trace),
            errors=(f"launch_adapter_error:{exc}",),
            canonical_command_hint=canonical_hint,
        )

    status = "spawned" if launched else "spawn_failed"
    receipt = AgentSpawnReceipt(
        request_id=request_id,
        provider=provider,
        role=role,
        bypass_receipt_id=request.bypass_receipt_id,
        row_id=row_id,
        status=status,
        issued_at_utc=timestamp,
        pid=int(pid or 0),
        script_path=str(script_path or ""),
        reason="launch_sessions_headless" if launched else "launch_callable_returned_failure",
        error=str(launch_error or ""),
    )
    append_event(trace, receipt.to_event())
    return PeerSpawnReport(
        ok=launched,
        action="peer-spawn",
        request=request.to_event(),
        receipt=receipt.to_event(),
        trace_path=str(trace),
        errors=() if launched else (launch_error or "launch_callable_returned_failure",),
        canonical_command_hint=canonical_hint,
    )


def compose_peer_terminate(
    *,
    provider: str,
    session_id: str,
    pid: int,
    actor: str = DEFAULT_PEER_SPAWN_ACTOR,
    reason: str = "",
    signal_name: str = "SIGTERM",
    trace_path: Path | str | None = None,
    repo_root: Path = REPO_ROOT,
    kill_callable: Callable[[int, int], None] | None = None,
    now_utc: str | None = None,
) -> PeerSpawnReport:
    """Canonical peer-terminate composer.

    `kill_callable(pid, signal)` is the dependency-injected boundary; defaults
    to ``os.kill``. The driver always emits a typed
    `AgentTerminationReceipt` regardless of whether the signal succeeded.
    """
    timestamp = now_utc or utc_timestamp()
    trace = resolve_trace_path(trace_path, repo_root=repo_root)
    request_id = _request_id(provider=provider, role="terminate", at_utc=timestamp)
    if provider not in SUPPORTED_PROVIDERS:
        return PeerSpawnReport(
            ok=False,
            action="peer-terminate",
            trace_path=str(trace),
            errors=(f"unsupported_provider:{provider}",),
        )
    if pid <= 0:
        return PeerSpawnReport(
            ok=False,
            action="peer-terminate",
            trace_path=str(trace),
            errors=("pid_required_for_terminate",),
        )

    signum = _signal_number(signal_name)
    killer = kill_callable or os.kill
    status = "terminated"
    error_text = ""
    try:
        killer(pid, signum)
    except ProcessLookupError as exc:
        status = "pid_not_found"
        error_text = str(exc)
    except PermissionError as exc:
        status = "permission_denied"
        error_text = str(exc)
    except OSError as exc:
        status = "kill_failed"
        error_text = str(exc)

    receipt = AgentTerminationReceipt(
        request_id=request_id,
        provider=provider,
        session_id=session_id,
        pid=int(pid),
        signal=signal_name.upper(),
        status=status,
        issued_at_utc=timestamp,
        actor=actor,
        reason=reason,
        error=error_text,
    )
    append_event(trace, receipt.to_event())
    return PeerSpawnReport(
        ok=(status == "terminated"),
        action="peer-terminate",
        receipt=receipt.to_event(),
        trace_path=str(trace),
        errors=() if status == "terminated" else (status,),
    )


def _signal_number(signal_name: str) -> int:
    """Resolve a signal name (e.g. ``SIGTERM``) to its integer value."""
    name = signal_name.strip().upper()
    if not name:
        return getattr(_signal_mod, "SIGTERM", 15)
    if not name.startswith("SIG"):
        name = f"SIG{name}"
    candidate = getattr(_signal_mod, name, None)
    if isinstance(candidate, int):
        return candidate
    if hasattr(candidate, "value"):
        return int(candidate.value)
    return getattr(_signal_mod, "SIGTERM", 15)


def _canonical_hint(*, provider: str, role: str) -> str:
    return (
        "python3 dev/scripts/devctl.py peer-spawn "
        f"--provider {provider} --role {role} "
        "--bypass-receipt-id <id> --row-id <id> --format json"
    )


__all__ = [
    "AGENT_SPAWN_REQUEST_CONTRACT_ID",
    "AGENT_SPAWN_RECEIPT_CONTRACT_ID",
    "AGENT_TERMINATION_RECEIPT_CONTRACT_ID",
    "DEFAULT_PEER_SPAWN_TRACE_REL",
    "PEER_SPAWN_SCHEMA_VERSION",
    "SUPPORTED_PROVIDERS",
    "SUPPORTED_ROLES",
    "AgentSpawnReceipt",
    "AgentSpawnRequest",
    "AgentTerminationReceipt",
    "PeerSpawnReport",
    "append_event",
    "compose_peer_spawn",
    "compose_peer_terminate",
    "resolve_trace_path",
]
