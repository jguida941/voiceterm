"""Typed relaunch-loop controller command."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...runtime.relaunch_loop_builder import (
    build_relaunch_trigger,
    build_slice_closure_event,
    utc_now,
)
from ...runtime.relaunch_loop_models import (
    DEFAULT_RELAUNCH_QUEUE_REL,
    DEFAULT_RELAUNCH_RECEIPTS_REL,
    DEFAULT_RELAUNCH_TRACE_REL,
    RELAUNCH_DISPATCH_RECEIPT_CONTRACT_ID,
    RELAUNCH_QUEUED_RECEIPT_CONTRACT_ID,
    AgentRelaunchTrigger,
    AuthorityScope,
    RelaunchQuotaExceeded,
    RelaunchQuotaToken,
    RelaunchTriggerInput,
    SliceClosureEvent,
    SliceClosureInput,
    SliceTarget,
    TypedLaunchCommand,
)
from ...runtime.relaunch_loop_store import (
    append_jsonl,
    load_relaunch_triggers,
    load_slice_closure_events,
    pending_relaunch_triggers,
)
from ...common import emit_output, resolve_repo_path, write_output

RELAUNCH_LOOP_CONTRACT_TYPES = (
    SliceTarget,
    AuthorityScope,
    TypedLaunchCommand,
    RelaunchQuotaToken,
    SliceClosureEvent,
    SliceClosureInput,
    AgentRelaunchTrigger,
    RelaunchTriggerInput,
    RelaunchQuotaExceeded,
)


def run(args: Any) -> int:
    """Run one typed relaunch-loop controller action."""
    action = str(getattr(args, "action", "status") or "status").strip()
    trace_path = _path(getattr(args, "trace_path", ""), DEFAULT_RELAUNCH_TRACE_REL)
    queue_path = _path(getattr(args, "queue_path", ""), DEFAULT_RELAUNCH_QUEUE_REL)
    receipts_path = _path(
        getattr(args, "receipts_path", ""),
        DEFAULT_RELAUNCH_RECEIPTS_REL,
    )
    if action == "emit-closure":
        report, rc = _emit_closure(args, trace_path=trace_path)
    elif action == "watch-once":
        report, rc = _watch_once(
            args,
            trace_path=trace_path,
            queue_path=queue_path,
            receipts_path=receipts_path,
        )
    elif action == "dispatch-once":
        report, rc = _dispatch_once(
            args,
            queue_path=queue_path,
            receipts_path=receipts_path,
        )
    else:
        report, rc = _status(
            args,
            trace_path=trace_path,
            queue_path=queue_path,
            receipts_path=receipts_path,
        )
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


def _emit_closure(args: Any, *, trace_path: Path) -> tuple[dict[str, Any], int]:
    required = _missing(
        args,
        ("emitter_actor", "target_actor", "closed_slice_id", "next_slice_id", "plan_ref"),
    )
    if required:
        return _base_report("emit-closure", ok=False, trace_path=trace_path) | {
            "errors": [f"missing required args: {', '.join(required)}"],
        }, 2
    offset = trace_path.stat().st_size if trace_path.exists() else 0
    event = build_slice_closure_event(
        SliceClosureInput(
            emitter_actor=getattr(args, "emitter_actor", ""),
            plan_ref=str(getattr(args, "plan_ref", "") or ""),
            closed_slice_id=str(getattr(args, "closed_slice_id", "") or ""),
            next_slice_id=str(getattr(args, "next_slice_id", "") or ""),
            next_owner_actor=getattr(args, "target_actor", ""),
            next_intent=str(getattr(args, "intent", "") or ""),
            evidence_packet_ids=tuple(getattr(args, "packet_id", ()) or ()),
            push_decision_state=str(
                getattr(args, "push_decision_state", "") or "no_push_needed"
            ),
            commit_sha=str(getattr(args, "commit_sha", "") or ""),
            source_packet_id=(getattr(args, "packet_id", None) or [""])[0],
            trace_offset=offset,
        ),
    )
    event_payload = asdict(event)
    append_jsonl(trace_path, event_payload)
    report = _base_report("emit-closure", trace_path=trace_path)
    report["event"] = event_payload
    report["emitted_event_count"] = 1
    return report, 0


def _watch_once(
    args: Any,
    *,
    trace_path: Path,
    queue_path: Path,
    receipts_path: Path,
) -> tuple[dict[str, Any], int]:
    events = load_slice_closure_events(trace_path)
    queued: list[dict[str, object]] = []
    skipped: list[dict[str, str]] = []
    quota_exceeded: list[dict[str, object]] = []
    for event in events:
        trigger, quota, reason = build_relaunch_trigger(
            RelaunchTriggerInput(
                event=event,
                expected_instruction_revision=str(
                    getattr(args, "expected_instruction_revision", "") or ""
                ),
                existing_triggers=load_relaunch_triggers(queue_path),
            ),
        )
        if quota is not None:
            payload = asdict(quota)
            append_jsonl(receipts_path, payload)
            quota_exceeded.append(payload)
            continue
        if trigger is None:
            skipped.append(
                {
                    "slice_closure_event_id": event.slice_closure_event_id,
                    "reason": reason,
                }
            )
            continue
        trigger_payload = asdict(trigger)
        append_jsonl(queue_path, trigger_payload)
        receipt: dict[str, object] = {}
        receipt["contract_id"] = RELAUNCH_QUEUED_RECEIPT_CONTRACT_ID
        receipt["schema_version"] = 1
        receipt["queued_at_utc"] = trigger.queued_at_utc
        receipt["trigger_id"] = trigger.trigger_id
        receipt["parent_closure_id"] = trigger.parent_closure_id
        receipt["target_actor"] = trigger.target_actor
        receipt["result"] = "queued"
        append_jsonl(receipts_path, receipt)
        queued.append(trigger_payload)
    report = _base_report(
        "watch-once",
        trace_path=trace_path,
        queue_path=queue_path,
        receipts_path=receipts_path,
    )
    report["events_seen"] = len(events)
    report["queued_count"] = len(queued)
    report["skipped_count"] = len(skipped)
    report["quota_exceeded_count"] = len(quota_exceeded)
    report["queued"] = queued
    report["skipped"] = skipped
    report["quota_exceeded"] = quota_exceeded
    return report, 0 if not quota_exceeded else 2


def _dispatch_once(
    args: Any,
    *,
    queue_path: Path,
    receipts_path: Path,
) -> tuple[dict[str, Any], int]:
    rows = pending_relaunch_triggers(queue_path)
    limit = max(0, int(getattr(args, "limit", 20) or 20))
    dry_run = bool(getattr(args, "dry_run", False))
    previews = [asdict(row) for row in rows[:limit]]
    if not dry_run:
        report = _base_report("dispatch-once", queue_path=queue_path)
        report["ok"] = False
        report["pending_count"] = len(rows)
        report["errors"] = [
            "provider spawning is fail-closed until dispatcher registry "
            "authority lands; rerun with --dry-run for launch previews"
        ]
        return report, 2
    receipt: dict[str, object] = {}
    receipt["contract_id"] = RELAUNCH_DISPATCH_RECEIPT_CONTRACT_ID
    receipt["schema_version"] = 1
    receipt["observed_at_utc"] = utc_now()
    receipt["dry_run"] = True
    receipt["dispatched"] = False
    receipt["pending_count"] = len(rows)
    receipt["preview_count"] = len(previews)
    receipt["result"] = "preview_only"
    append_jsonl(receipts_path, receipt)
    report = _base_report(
        "dispatch-once",
        queue_path=queue_path,
        receipts_path=receipts_path,
    )
    report["dry_run"] = True
    report["pending_count"] = len(rows)
    report["preview_count"] = len(previews)
    report["dispatch_previews"] = previews
    report["receipt"] = receipt
    return report, 0


def _status(
    args: Any,
    *,
    trace_path: Path,
    queue_path: Path,
    receipts_path: Path,
) -> tuple[dict[str, Any], int]:
    events = load_slice_closure_events(trace_path)
    triggers = load_relaunch_triggers(queue_path)
    pending = [row for row in triggers if row.status == "pending"]
    limit = max(0, int(getattr(args, "limit", 20) or 20))
    report = _base_report(
        "status",
        trace_path=trace_path,
        queue_path=queue_path,
        receipts_path=receipts_path,
    )
    report["slice_closure_event_count"] = len(events)
    report["trigger_count"] = len(triggers)
    report["pending_count"] = len(pending)
    report["pending"] = [asdict(row) for row in pending[:limit]]
    return report, 0


def _path(raw: str, default: Path) -> Path:
    return resolve_repo_path(raw, default, repo_root=REPO_ROOT)


def _missing(args: Any, names: tuple[str, ...]) -> list[str]:
    return [name for name in names if not str(getattr(args, name, "") or "").strip()]


def _base_report(action: str, *, ok: bool = True, **paths: Path) -> dict[str, Any]:
    return {
        "ok": ok,
        "action": action,
        "contract_id": "RelaunchLoopController",
        "schema_version": 1,
        "paths": {name: str(path) for name, path in paths.items()},
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# devctl relaunch-loop",
        "",
        f"- ok: {report.get('ok')}",
        f"- action: {report.get('action')}",
    ]
    for key in (
        "slice_closure_event_count",
        "events_seen",
        "emitted_event_count",
        "queued_count",
        "skipped_count",
        "quota_exceeded_count",
        "trigger_count",
        "pending_count",
        "preview_count",
    ):
        if key in report:
            lines.append(f"- {key}: {report.get(key)}")
    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        lines.extend(["", "## Errors"])
        lines.extend(f"- {error}" for error in errors)
    paths = report.get("paths")
    if isinstance(paths, dict) and paths:
        lines.extend(["", "## Paths"])
        lines.extend(f"- {name}: {path}" for name, path in sorted(paths.items()))
    event = report.get("event")
    if isinstance(event, dict):
        lines.extend(["", "## Slice Closure"])
        lines.append(f"- id: {event.get('slice_closure_event_id')}")
        lines.append(f"- emitter_actor: {event.get('emitter_actor')}")
        target = event.get("next_slice_target")
        if isinstance(target, dict):
            lines.append(f"- target_actor: {target.get('owner_actor')}")
            lines.append(f"- next_slice_id: {target.get('slice_id')}")
    queued = report.get("queued")
    if isinstance(queued, list) and queued:
        lines.extend(["", "## Queued Triggers"])
        for row in queued:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('trigger_id')}: {row.get('target_actor')} "
                f"from {row.get('parent_closure_id')}"
            )
    previews = report.get("dispatch_previews")
    if isinstance(previews, list) and previews:
        lines.extend(["", "## Dispatch Preview"])
        for row in previews:
            if not isinstance(row, dict):
                continue
            launch = row.get("launch_command")
            command = launch.get("command_preview") if isinstance(launch, dict) else ""
            lines.append(f"- {row.get('trigger_id')}: {command}")
    skipped = report.get("skipped")
    if isinstance(skipped, list) and skipped:
        lines.extend(["", "## Skipped"])
        for row in skipped:
            if isinstance(row, dict):
                lines.append(
                    f"- {row.get('slice_closure_event_id')}: {row.get('reason')}"
                )
    return "\n".join(lines)


__all__ = ["run"]
