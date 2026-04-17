"""Refresh-authorization action for ``devctl pipeline``.

Reissues a fresh authorization record (new id, new timestamps, new
expiry window) for the existing pipeline without rewriting the commit
binding. This is the minimal recovery move when HEAD has not moved but
the authorization has ticked past ``expires_at_utc``.

The action refuses to touch pipelines that are already terminal or
that have no authorization sub-record to refresh.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from ...runtime.pipeline_recovery_receipt import build_receipt
from .support import (
    PipelinePaths,
    REFRESHABLE_STATES,
    REFRESH_RECEIPT_FILENAME,
    authorization_of,
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

_RECOVER_RECOMMENDATION = "recover"


def run_refresh_authorization(args) -> int:
    """Entry point for ``devctl pipeline --action refresh-authorization``."""
    result = apply_refresh_authorization(
        repo_root=getattr(args, "repo_root_override", None),
        pipeline_root_override=_maybe_path(
            getattr(args, "pipeline_root_override", None)
        ),
        receipts_root_override=_maybe_path(
            getattr(args, "receipts_root_override", None)
        ),
        operator_actor=str(getattr(args, "operator_actor", None) or "operator"),
        reason=str(getattr(args, "reason", "") or "").strip() or (
            "reissue fresh authorization window"
        ),
    )
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        print(json.dumps(result, indent=2))
    else:
        print(_render_markdown(result))
    return 0 if result.get("ok") else 1


def apply_refresh_authorization(
    *,
    repo_root: Path | None = None,
    pipeline_root_override: Path | None = None,
    receipts_root_override: Path | None = None,
    operator_actor: str = "operator",
    reason: str = "reissue fresh authorization window",
) -> dict[str, Any]:
    """Refresh the current pipeline authorization window and return the typed result."""
    paths = resolve_pipeline_paths(
        repo_root=repo_root,
        pipeline_root_override=pipeline_root_override,
        receipts_root_override=receipts_root_override,
    )
    return _apply_refresh(
        paths=paths,
        reason=reason,
        operator_actor=operator_actor,
    )


def _apply_refresh(
    *,
    paths: PipelinePaths,
    reason: str,
    operator_actor: str,
) -> dict[str, Any]:
    payload = load_pipeline_payload(paths)
    if not payload:
        return _refused(paths, "no_pipeline_artifact", pipeline_id="")
    state = pipeline_state_of(payload)
    pipeline_id = pipeline_id_of(payload)
    if state not in REFRESHABLE_STATES:
        return _refused(
            paths,
            f"pipeline_state_not_refreshable:{state}",
            pipeline_id=pipeline_id,
        )
    existing_auth = authorization_of(payload)
    if not existing_auth:
        return _refused(
            paths,
            "no_push_authorization_subrecord",
            pipeline_id=pipeline_id,
        )

    current_head = resolve_current_head(repo_root=paths.repo_root)
    if not current_head:
        return _refused(
            paths,
            "current_head_unavailable",
            pipeline_id=pipeline_id,
            recommended_next_action="none",
        )
    if head_has_moved(payload, current_head=current_head):
        return _refused(
            paths,
            "head_moved_since_authorization",
            pipeline_id=pipeline_id,
            recommended_next_action=_RECOVER_RECOMMENDATION,
        )

    previous_auth_id = str(existing_auth.get("authorization_id") or "")
    previous_expires = str(existing_auth.get("expires_at_utc") or "")

    updated = dict(payload)
    updated["push_authorization"] = make_refreshed_authorization(
        existing_auth,
        operator_actor=operator_actor,
    )

    receipt = build_receipt(
        action="refresh-authorization",
        pipeline_id=pipeline_id or "unknown",
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
        filename=REFRESH_RECEIPT_FILENAME,
    )
    warnings = refresh_pipeline_projections(paths)
    new_auth = updated["push_authorization"]
    return {
        "ok": True,
        "action": "refresh-authorization",
        "pipeline_id": pipeline_id,
        "previous_state": state,
        "new_state": state,
        "previous_authorization_id": previous_auth_id,
        "new_authorization_id": new_auth.get("authorization_id", ""),
        "previous_expires_at_utc": previous_expires,
        "new_expires_at_utc": new_auth.get("expires_at_utc", ""),
        "pipeline_artifact_path": str(paths.pipeline_path),
        "receipt_path": str(receipt_path),
        "warnings": warnings,
    }


def _refused(
    paths: PipelinePaths,
    reason_refused: str,
    *,
    pipeline_id: str,
    recommended_next_action: str = "",
) -> dict[str, Any]:
    result = {
        "ok": False,
        "action": "refresh-authorization",
        "reason_refused": reason_refused,
        "pipeline_id": pipeline_id,
        "pipeline_artifact_path": str(paths.pipeline_path),
    }
    if recommended_next_action:
        result["recommended_next_action"] = recommended_next_action
    return result


def _render_markdown(result: dict[str, Any]) -> str:
    lines: list[str] = ["# pipeline refresh-authorization", ""]
    if not result.get("ok"):
        lines.extend([
            "- ok: `false`",
            f"- refused: `{result.get('reason_refused','unknown')}`",
            f"- recommended: `{result.get('recommended_next_action','')}`",
            f"- artifact: `{result.get('pipeline_artifact_path','')}`",
        ])
        if result.get("pipeline_id"):
            lines.append(f"- pipeline_id: `{result['pipeline_id']}`")
        return "\n".join(lines) + "\n"
    lines.extend([
        "- ok: `true`",
        f"- pipeline_id: `{result['pipeline_id']}`",
        f"- state: `{result['new_state']}`",
        f"- previous_authorization_id: `{result['previous_authorization_id']}`",
        f"- new_authorization_id: `{result['new_authorization_id']}`",
        f"- previous_expires_at_utc: `{result['previous_expires_at_utc']}`",
        f"- new_expires_at_utc: `{result['new_expires_at_utc']}`",
        f"- artifact: `{result['pipeline_artifact_path']}`",
        f"- receipt: `{result['receipt_path']}`",
    ])
    return "\n".join(lines) + "\n"


def _maybe_path(value: Any) -> Path | None:
    if value is None:
        return None
    return Path(value)
