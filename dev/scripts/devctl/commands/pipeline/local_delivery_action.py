"""Mark a local pipeline commit as delivered but unpublished."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from ...runtime.pipeline_recovery_receipt import build_receipt, utc_now_iso
from ...runtime.pipeline_local_delivery_receipts import (
    LOCAL_DELIVERY_RECEIPT_FILENAME,
)
from ...runtime.remote_commit_pipeline_state import (
    STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
    eligible_for_local_delivery,
)
from .abandon_action import MIN_REASON_LENGTH
from .refusal import refused_pipeline_result
from .support import (
    PipelinePaths,
    load_pipeline_payload,
    pipeline_id_of,
    pipeline_state_of,
    refresh_pipeline_projections,
    resolve_current_head,
    resolve_pipeline_paths,
    write_pipeline_payload,
    write_receipt,
)


def run_mark_delivered_local(args) -> int:
    """Entry point for ``devctl pipeline --action mark-delivered-local``."""
    reason = str(getattr(args, "reason", "") or "").strip()
    if not reason:
        print(
            "error: --reason is required for --action mark-delivered-local",
            file=sys.stderr,
        )
        return 2
    if len(reason) < MIN_REASON_LENGTH:
        print(
            "error: --reason must be at least "
            f"{MIN_REASON_LENGTH} characters (got {len(reason)})",
            file=sys.stderr,
        )
        return 2

    paths = resolve_pipeline_paths(
        repo_root=getattr(args, "repo_root_override", None),
        pipeline_root_override=_maybe_path(
            getattr(args, "pipeline_root_override", None)
        ),
        receipts_root_override=_maybe_path(
            getattr(args, "receipts_root_override", None)
        ),
    )
    result = _apply_mark_delivered_local(
        paths=paths,
        reason=reason,
        operator_actor=str(getattr(args, "operator_actor", None) or "operator"),
    )
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        print(json.dumps(result, indent=2))
    else:
        print(_render_markdown(result))
    return 0 if result.get("ok") else 1


def _apply_mark_delivered_local(
    *,
    paths: PipelinePaths,
    reason: str,
    operator_actor: str,
) -> dict[str, Any]:
    payload = load_pipeline_payload(paths)
    if not payload:
        return refused_pipeline_result(
            action="mark-delivered-local",
            reason_refused="no_pipeline_artifact",
            pipeline_artifact_path=paths.pipeline_path,
        )
    current_head = resolve_current_head(repo_root=paths.repo_root)
    state = pipeline_state_of(payload)
    pipeline_id = pipeline_id_of(payload)
    if not eligible_for_local_delivery(payload, current_head=current_head):
        return refused_pipeline_result(
            action="mark-delivered-local",
            reason_refused="pipeline_not_eligible_for_local_delivery",
            pipeline_id=pipeline_id,
            pipeline_artifact_path=paths.pipeline_path,
            extra={
                "pipeline_state": state,
                "current_head_sha": current_head,
            },
        )

    receipt = build_receipt(
        action="mark-delivered-local",
        pipeline_id=pipeline_id or "unknown",
        previous_state=state,
        new_state=STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
        reason=reason,
        operator_actor=operator_actor,
        artifact_paths=(str(paths.pipeline_path),),
    )
    receipt_path = write_receipt(
        paths,
        receipt,
        filename=LOCAL_DELIVERY_RECEIPT_FILENAME,
    )
    updated = dict(payload)
    updated["state"] = STATE_DELIVERED_LOCALLY_PENDING_PUBLISH
    updated["blocked_reason"] = ""
    updated["recovery_action_allowed"] = ""
    updated["local_delivery_receipt_path"] = str(receipt_path)
    updated["local_delivery_reason"] = reason
    updated["delivered_at_utc"] = utc_now_iso()
    updated["delivered_by"] = operator_actor

    warnings = refresh_pipeline_projections(paths)
    # Refreshing projections can regenerate commit_pipeline.json from older
    # event state. Materialize the receipt-backed state after refresh so the
    # immediate read model and the written artifact converge.
    write_pipeline_payload(paths, updated)
    return {
        "ok": True,
        "action": "mark-delivered-local",
        "pipeline_id": pipeline_id,
        "previous_state": state,
        "new_state": STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
        "pipeline_artifact_path": str(paths.pipeline_path),
        "receipt_path": str(receipt_path),
        "reason": reason,
        "warnings": warnings,
    }


def _render_markdown(result: dict[str, Any]) -> str:
    lines: list[str] = ["# pipeline mark-delivered-local", ""]
    if not result.get("ok"):
        lines.append("- ok: `false`")
        lines.append(f"- refused: `{result.get('reason_refused','unknown')}`")
        lines.append(f"- artifact: `{result.get('pipeline_artifact_path','')}`")
        if "pipeline_id" in result:
            lines.append(f"- pipeline_id: `{result['pipeline_id']}`")
        return "\n".join(lines) + "\n"
    lines.extend([
        "- ok: `true`",
        f"- pipeline_id: `{result['pipeline_id']}`",
        f"- previous_state: `{result['previous_state']}`",
        f"- new_state: `{result['new_state']}`",
        f"- reason: `{result['reason']}`",
        f"- artifact: `{result['pipeline_artifact_path']}`",
        f"- receipt: `{result['receipt_path']}`",
    ])
    return "\n".join(lines) + "\n"


def _maybe_path(value: Any) -> Path | None:
    if value is None:
        return None
    return Path(value)


__all__ = [
    "LOCAL_DELIVERY_RECEIPT_FILENAME",
    "_apply_mark_delivered_local",
    "run_mark_delivered_local",
]
