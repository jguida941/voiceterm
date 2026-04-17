"""Recover action for ``devctl pipeline --action recover``.

Re-binds the current pipeline authorization to the current HEAD when
the pipeline state permits it. This is the narrow recovery lane for
the exact wedge the root-cause analysis called out: a
``commit_recorded`` pipeline whose authorized_head_sha no longer
matches HEAD because later commits landed on top.

The action refuses to mutate state in any case where the outcome would
not be an unambiguous "rebind to current HEAD". In those cases it
returns a typed ``reason_refused`` string and recommends the next
action the operator should try.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from ...runtime.pipeline_recovery_receipt import build_receipt
from .support import (
    PipelinePaths,
    RECOVERABLE_STATES,
    RECOVER_RECEIPT_FILENAME,
    authorization_of,
    authorized_head_sha_of,
    head_has_moved,
    load_pipeline_payload,
    make_refreshed_authorization,
    pipeline_id_of,
    pipeline_state_of,
    refresh_pipeline_projections,
    resolve_current_head,
    resolve_pipeline_paths,
    write_pipeline_payload,
    write_receipt,
)


def run_recover(args) -> int:
    """Entry point for ``devctl pipeline --action recover``."""
    paths = resolve_pipeline_paths(
        repo_root=getattr(args, "repo_root_override", None),
        pipeline_root_override=_maybe_path(
            getattr(args, "pipeline_root_override", None)
        ),
        receipts_root_override=_maybe_path(
            getattr(args, "receipts_root_override", None)
        ),
    )
    reason = str(getattr(args, "reason", "") or "").strip() or (
        "rebind authorization to current HEAD"
    )
    operator_actor = str(
        getattr(args, "operator_actor", None) or "operator"
    )
    result = _apply_recover(
        paths=paths,
        reason=reason,
        operator_actor=operator_actor,
    )
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        print(json.dumps(result, indent=2))
    else:
        print(_render_markdown(result))
    if not result.get("ok"):
        return 1
    return 0


def _apply_recover(
    *,
    paths: PipelinePaths,
    reason: str,
    operator_actor: str,
) -> dict[str, Any]:
    payload = load_pipeline_payload(paths)
    if not payload:
        return _refused(
            paths,
            reason_refused="no_pipeline_artifact",
            recommended="none",
        )
    state = pipeline_state_of(payload)
    if state not in RECOVERABLE_STATES:
        return _refused(
            paths,
            reason_refused=f"pipeline_state_not_recoverable:{state}",
            recommended="abandon",
            pipeline_id=pipeline_id_of(payload),
        )
    current_head = resolve_current_head(repo_root=paths.repo_root)
    if not current_head:
        return _refused(
            paths,
            reason_refused="current_head_unavailable",
            recommended="none",
            pipeline_id=pipeline_id_of(payload),
        )
    if not head_has_moved(payload, current_head=current_head):
        return _refused(
            paths,
            reason_refused="head_matches_authorized_head",
            recommended="refresh-authorization",
            pipeline_id=pipeline_id_of(payload),
        )

    updated = dict(payload)
    updated["push_authorization"] = make_refreshed_authorization(
        authorization_of(payload),
        operator_actor=operator_actor,
        new_head_sha=current_head,
    )
    updated["blocked_reason"] = ""
    updated["commit_sha"] = current_head

    receipt = build_receipt(
        action="recover",
        pipeline_id=pipeline_id_of(payload) or "unknown",
        previous_state=state,
        new_state=state,
        reason=reason,
        operator_actor=operator_actor,
        artifact_paths=(str(paths.pipeline_path),),
    )
    write_pipeline_payload(paths, updated)
    receipt_path = write_receipt(
        paths,
        receipt,
        filename=RECOVER_RECEIPT_FILENAME,
    )
    warnings = refresh_pipeline_projections(paths)
    return {
        "ok": True,
        "action": "recover",
        "pipeline_id": pipeline_id_of(payload),
        "previous_state": state,
        "new_state": state,
        "previous_authorized_head_sha": authorized_head_sha_of(payload),
        "new_authorized_head_sha": current_head,
        "pipeline_artifact_path": str(paths.pipeline_path),
        "receipt_path": str(receipt_path),
        "warnings": warnings,
    }


def _refused(
    paths: PipelinePaths,
    *,
    reason_refused: str,
    recommended: str,
    pipeline_id: str = "",
) -> dict[str, Any]:
    return {
        "ok": False,
        "action": "recover",
        "reason_refused": reason_refused,
        "recommended_next_action": recommended,
        "pipeline_id": pipeline_id,
        "pipeline_artifact_path": str(paths.pipeline_path),
    }


def _render_markdown(result: dict[str, Any]) -> str:
    lines: list[str] = ["# pipeline recover", ""]
    if not result.get("ok"):
        lines.extend([
            "- ok: `false`",
            f"- refused: `{result.get('reason_refused','unknown')}`",
            f"- recommended: `{result.get('recommended_next_action','none')}`",
            f"- artifact: `{result.get('pipeline_artifact_path','')}`",
        ])
        if result.get("pipeline_id"):
            lines.append(f"- pipeline_id: `{result['pipeline_id']}`")
        return "\n".join(lines) + "\n"
    lines.extend([
        "- ok: `true`",
        f"- pipeline_id: `{result['pipeline_id']}`",
        f"- state: `{result['new_state']}`",
        f"- previous_authorized_head_sha: `{result['previous_authorized_head_sha']}`",
        f"- new_authorized_head_sha: `{result['new_authorized_head_sha']}`",
        f"- artifact: `{result['pipeline_artifact_path']}`",
        f"- receipt: `{result['receipt_path']}`",
    ])
    return "\n".join(lines) + "\n"


def _maybe_path(value: Any) -> Path | None:
    if value is None:
        return None
    return Path(value)
