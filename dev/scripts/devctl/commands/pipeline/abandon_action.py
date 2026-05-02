"""Abandon action for ``devctl pipeline --action abandon``.

Marks a wedged pipeline ``abandoned`` so the next ``devctl commit`` can
open a fresh pipeline. The operator is required to supply a non-trivial
``--reason`` string so the typed receipt captures why the abandon was
legitimate and a later audit can adjudicate it.

This action intentionally refuses to abandon a pipeline that has
already reached a terminal state — that would overwrite history rather
than unblock work.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from ...runtime.pipeline_recovery_receipt import build_receipt, utc_now_iso
from .refusal import refused_pipeline_result
from .support import (
    ABANDONED_RECEIPT_FILENAME,
    PipelinePaths,
    TERMINAL_STATES,
    load_pipeline_payload,
    pipeline_id_of,
    pipeline_state_of,
    refresh_pipeline_projections,
    resolve_pipeline_paths,
    write_pipeline_payload,
    write_receipt,
)


MIN_REASON_LENGTH = 10


def run_abandon(args) -> int:
    """Entry point for ``devctl pipeline --action abandon``."""
    reason = str(getattr(args, "reason", "") or "").strip()
    if not reason:
        print(
            "error: --reason is required for --action abandon",
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
    result = _apply_abandon(
        paths=paths,
        reason=reason,
        operator_actor=str(
            getattr(args, "operator_actor", None) or "operator"
        ),
    )
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        print(json.dumps(result, indent=2))
    else:
        print(_render_markdown(result))
    return 0 if result.get("ok") else 1


def _apply_abandon(
    *,
    paths: PipelinePaths,
    reason: str,
    operator_actor: str,
) -> dict[str, Any]:
    payload = load_pipeline_payload(paths)
    if not payload:
        return refused_pipeline_result(
            action="abandon",
            reason_refused="no_pipeline_artifact",
            pipeline_artifact_path=paths.pipeline_path,
        )
    state = pipeline_state_of(payload)
    pipeline_id = pipeline_id_of(payload)
    if state in TERMINAL_STATES:
        return refused_pipeline_result(
            action="abandon",
            reason_refused=f"pipeline_state_terminal:{state}",
            pipeline_id=pipeline_id,
            pipeline_artifact_path=paths.pipeline_path,
        )

    updated = dict(payload)
    updated["state"] = "abandoned"
    updated["blocked_reason"] = "pipeline_abandoned_by_operator"
    updated["abandoned_at_utc"] = utc_now_iso()
    updated["abandoned_reason"] = reason
    updated["abandoned_by"] = operator_actor

    receipt = build_receipt(
        action="abandon",
        pipeline_id=pipeline_id or "unknown",
        previous_state=state,
        new_state="abandoned",
        reason=reason,
        operator_actor=operator_actor,
        artifact_paths=(str(paths.pipeline_path),),
    )
    write_pipeline_payload(paths, updated)
    receipt_path = write_receipt(
        paths,
        receipt,
        filename=ABANDONED_RECEIPT_FILENAME,
    )
    warnings = refresh_pipeline_projections(paths)
    return {
        "ok": True,
        "action": "abandon",
        "pipeline_id": pipeline_id,
        "previous_state": state,
        "new_state": "abandoned",
        "pipeline_artifact_path": str(paths.pipeline_path),
        "receipt_path": str(receipt_path),
        "reason": reason,
        "warnings": warnings,
    }


def _render_markdown(result: dict[str, Any]) -> str:
    lines: list[str] = ["# pipeline abandon", ""]
    if not result.get("ok"):
        lines.append(f"- ok: `false`")
        lines.append(
            f"- refused: `{result.get('reason_refused','unknown')}`"
        )
        lines.append(
            f"- artifact: `{result.get('pipeline_artifact_path','')}`"
        )
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
