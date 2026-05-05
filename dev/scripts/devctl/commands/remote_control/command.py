"""Typed remote-control lifecycle controller."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from types import SimpleNamespace
from typing import Any

from ...common import emit_output, write_output
from ...config import REPO_ROOT
from ...runtime.remote_control_invocation_receipt import classify_state_change
from ...time_utils import utc_timestamp
from ._hook import (
    hook_report as _hook_report,
    load_hook_payload as _load_hook_payload,
    wait_for_hook_source_proof as _wait_for_hook_source_proof,
)
from ._hook_source_proof import hook_prompt_action
from ._lifecycle_state_resolution import (
    EVIDENCE_MISSING_STATUS,
    before_state_from_attachment as _capture_before_state_from_attachment,
    before_state_from_report as _capture_before_state,
    resolve_lifecycle_attachment_status as _resolve_attachment_status,
)
from ._render import (
    doctor_payload as _doctor_payload,
    render_markdown as _render_markdown,
)
from ._runtime_io import (
    action as _action,
    args_with_source_proof as _args_with_source_proof,
    load_attachment as _load_attachment,
    persist_attachment as _persist_attachment,
    record_invocation as _record_invocation,
    refresh_status_snapshot_if_possible as _refresh_status_snapshot_if_possible,
    status_report as _runtime_status_report,
)
from ._source_proof import (
    resolve_lifecycle_source_proof,
)

REMOTE_CONTROL_CONTRACT_ID = "RemoteControlLifecycleReceipt"


def run(args: Any) -> int:
    """Run one remote-control lifecycle action."""
    action = _action(args)
    if action == "dry-run":
        args.dry_run = True
        action = "start"
    if action == "start":
        report, rc = _start(args)
    elif action in {"enter", "heartbeat"}:
        report, rc = _enter_or_heartbeat(args, action=action)
    elif action == "hook":
        report, rc = _hook(args)
    elif action == "exit":
        report, rc = _exit(args)
    elif action == "doctor":
        report, rc = _status_report(args, action="doctor")
        report["doctor"] = _doctor_payload(report)
    else:
        report, rc = _status_report(args, action="status")

    output = json.dumps(report, indent=2, sort_keys=True)
    if getattr(args, "format", "md") != "json":
        output = _render_markdown(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return rc


def _start(args: Any) -> tuple[dict[str, Any], int]:
    dry_run = bool(getattr(args, "dry_run", False))
    report, _rc = _status_report(args, action="start")
    report["dry_run"] = dry_run
    report["launcher_command"] = []
    report["bootstrap_review_channel_requested"] = bool(
        getattr(args, "bootstrap_review_channel", False)
    )
    before = _capture_before_state(report)
    if dry_run:
        report["ok"] = True
        report["state_change"] = "preview"
        _record_invocation(
            args,
            action="start",
            attachment=None,
            report=report,
            before=before,
            state_change="preview",
        )
        return report, 0
    if str(getattr(args, "provider", "claude") or "claude") != "claude":
        report["ok"] = False
        report["errors"] = ["only claude remote-control launch is implemented"]
        _record_invocation(
            args,
            action="start",
            attachment=None,
            report=report,
            before=before,
            state_change="evidence_missing",
        )
        return report, 2
    existing = _load_attachment(args)
    status = _resolve_attachment_status(args, current=existing)
    if status != EVIDENCE_MISSING_STATUS:
        attachment, artifact_path = _persist_attachment(
            args,
            status=status,
            existing=existing,
        )
        _refresh_status_snapshot_if_possible(args)
        report, _rc = _status_report(args, action="start")
        report["attachment"] = asdict(attachment)
        report["artifact_path"] = str(artifact_path)
        report["state_change"] = classify_state_change(
            before_status=before.attachment_status,
            after_status=attachment.status,
            before_attachment_id=before.attachment_id,
            after_attachment_id=attachment.attachment_id,
        )
        report["ok"] = True
        report["warnings"] = (report.get("warnings") or []) + [
            "no Claude CLI remote-control launch was attempted; typed state "
            "was recorded from supplied physical remote-control identity"
        ]
        _record_invocation(
            args,
            action="start",
            attachment=attachment,
            report=report,
            before=before,
            state_change=report["state_change"],
        )
        return report, 0
    report["ok"] = False
    report["state_change"] = "evidence_missing"
    report["errors"] = [
        "Claude remote-control is a built-in slash command, not a "
        "validated CLI launch. Run Claude's built-in /remote-control or /rc, "
        "then attach typed state with a real provider session URL if the hook "
        "did not mirror it automatically."
    ]
    _record_invocation(
        args,
        action="start",
        attachment=None,
        report=report,
        before=before,
        state_change="evidence_missing",
    )
    return report, 2


def _enter_or_heartbeat(
    args: Any,
    *,
    action: str,
    proof: Any | None = None,
) -> tuple[dict[str, Any], int]:
    existing = _load_attachment(args)
    before = _capture_before_state_from_attachment(existing)
    if proof is None:
        proof = resolve_lifecycle_source_proof(
            args,
            repo_root=REPO_ROOT,
            now_utc=utc_timestamp(),
        )
    lifecycle_args = _args_with_source_proof(args, proof)
    status = _resolve_attachment_status(lifecycle_args, current=existing)
    attachment, artifact_path = _persist_attachment(
        lifecycle_args,
        status=status,
        existing=existing,
    )
    _refresh_status_snapshot_if_possible(lifecycle_args)
    report, _rc = _status_report(lifecycle_args, action=action)
    report["attachment"] = asdict(attachment)
    report["artifact_path"] = str(artifact_path)
    if proof.proven_source_kind != "unspecified":
        report["source_proof"] = proof.to_dict()
    if status == EVIDENCE_MISSING_STATUS:
        report["state_change"] = "evidence_missing"
        report["warnings"] = (report.get("warnings") or []) + [
            "remote-control invocation lacks current session identity; "
            "operator_interaction_mode left unchanged"
        ]
    else:
        # Per rev_pkt_3023 P1/P0 #4: first identity-bound enter must
        # classify as ``created``, not ``heartbeat_refreshed``. Delegate
        # to ``classify_state_change`` so the canonical receipt classifier
        # decides based on observable before/after fields rather than
        # action verb.
        report["state_change"] = classify_state_change(
            before_status=before.attachment_status,
            after_status=attachment.status,
            before_attachment_id=before.attachment_id,
            after_attachment_id=attachment.attachment_id,
        )
    report["ok"] = True
    _record_invocation(
        lifecycle_args,
        action=action,
        attachment=attachment,
        report=report,
        before=before,
        state_change=report["state_change"],
    )
    return report, 0


def _hook(args: Any) -> tuple[dict[str, Any], int]:
    payload = _load_hook_payload(args)
    prompt_action = hook_prompt_action(payload)
    if prompt_action == "ignore":
        return _hook_report(payload=payload, action=prompt_action), 0
    hook_args = _hook_lifecycle_args(args)
    started = time.monotonic()
    proof = _wait_for_hook_source_proof(
        payload,
        poll_seconds=float(getattr(hook_args, "hook_poll_seconds", 30.0) or 0.0),
    )
    poll_elapsed_ms = int((time.monotonic() - started) * 1000)
    lifecycle_args = _args_with_source_proof(hook_args, proof)
    deduped = _hook_already_recorded(lifecycle_args, proof, prompt_action)
    if deduped:
        report, rc = _status_report(lifecycle_args, action="hook")
        report["state_change"] = "no_op"
        report["source_proof"] = proof.to_dict()
    elif prompt_action == "exit":
        report, rc = _exit(lifecycle_args)
    else:
        report, rc = _enter_or_heartbeat(
            lifecycle_args,
            action="enter",
            proof=proof,
        )
    hook = _hook_report(payload=payload, action=prompt_action)
    hook["hook_dedupe_key"] = proof.hook_dedupe_key
    hook["poll_elapsed_ms"] = poll_elapsed_ms
    hook["poll_timeout"] = (
        prompt_action == "enter"
        and not proof.session_url
        and float(getattr(hook_args, "hook_poll_seconds", 30.0) or 0.0) > 0.0
    )
    hook["deduped"] = deduped
    report["hook"] = hook
    return report, rc


def _hook_already_recorded(
    args: Any,
    proof: Any,
    prompt_action: str,
) -> bool:
    if prompt_action != "enter" or not proof.hook_dedupe_key:
        return False
    existing = _load_attachment(args)
    if existing is None:
        return False
    return (
        existing.status == "attached"
        and existing.source_hook_dedupe_key == proof.hook_dedupe_key
    )


def _hook_lifecycle_args(args: Any) -> Any:
    values = dict(vars(args)) if hasattr(args, "__dict__") else {}
    if not values:
        return args
    if str(values.get("entrypoint") or "").strip() in {
        "",
        "/project:remote-control",
        "remote-control",
    }:
        values["entrypoint"] = "claude_builtin_remote_control"
    if str(values.get("launcher_source") or "").strip() == "remote-control":
        values["launcher_source"] = "claude_builtin_slash"
    return SimpleNamespace(**values)


def _exit(args: Any) -> tuple[dict[str, Any], int]:
    existing = _load_attachment(args)
    before = _capture_before_state_from_attachment(existing)
    if existing is None:
        report, _rc = _status_report(args, action="exit")
        report["ok"] = True
        report["state_change"] = "already_detached"
        _record_invocation(
            args,
            action="exit",
            attachment=None,
            report=report,
            before=before,
            state_change="already_detached",
        )
        return report, 0
    attachment, artifact_path = _persist_attachment(
        args,
        status="detached",
        existing=existing,
    )
    _refresh_status_snapshot_if_possible(args)
    report, _rc = _status_report(args, action="exit")
    report["attachment"] = asdict(attachment)
    report["artifact_path"] = str(artifact_path)
    report["state_change"] = "detached"
    report["ok"] = True
    _record_invocation(
        args,
        action="exit",
        attachment=attachment,
        report=report,
        before=before,
        state_change="detached",
    )
    return report, 0


def _status_report(args: Any, *, action: str) -> tuple[dict[str, Any], int]:
    return _runtime_status_report(
        args,
        action=action,
        contract_id=REMOTE_CONTROL_CONTRACT_ID,
    )


__all__ = ["REMOTE_CONTROL_CONTRACT_ID", "run"]
