"""Read-only status action for ``devctl pipeline --action status``.

Reads the current commit pipeline artifact and renders a typed summary
(no mutation, no receipts). The returned payload is stable enough for
tests to snapshot and for other tooling to consume as JSON.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .support import (
    PipelinePaths,
    authorization_is_expired,
    authorized_head_sha_of,
    expires_at_of,
    head_has_moved,
    load_pipeline_payload,
    parse_iso,
    pipeline_id_of,
    pipeline_state_of,
    recommended_next_action,
    resolve_current_head,
)


def build_status_view(
    paths: PipelinePaths,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return the typed status dict without touching the filesystem twice."""
    payload = load_pipeline_payload(paths)
    current_head = resolve_current_head(repo_root=paths.repo_root)
    reference_now = now or datetime.now(timezone.utc)

    pipeline_id = pipeline_id_of(payload)
    state = pipeline_state_of(payload)
    commit_sha = str(payload.get("commit_sha") or "")
    authorized_head = authorized_head_sha_of(payload)
    expires_at = expires_at_of(payload)
    approved_at = _approved_at_of(payload)
    age_seconds = _compute_age_seconds(
        approved_at=approved_at,
        reference_now=reference_now,
    )

    return {
        "ok": bool(payload),
        "pipeline_artifact_path": str(paths.pipeline_path),
        "pipeline_exists": bool(payload),
        "pipeline_id": pipeline_id,
        "state": state,
        "commit_sha": commit_sha,
        "authorized_head_sha": authorized_head,
        "current_head_sha": current_head,
        "expires_at_utc": expires_at,
        "age_seconds": age_seconds,
        "authorization_expired": authorization_is_expired(
            payload,
            now=reference_now,
        ),
        "head_has_moved": head_has_moved(
            payload,
            current_head=current_head,
        ),
        "recommended_next_action": recommended_next_action(
            payload,
            current_head=current_head,
            now=reference_now,
        ),
    }


def _approved_at_of(payload: dict[str, Any]) -> str:
    auth = payload.get("push_authorization")
    if isinstance(auth, dict):
        value = auth.get("approved_at_utc")
        if isinstance(value, str):
            return value
    return ""


def _compute_age_seconds(
    *,
    approved_at: str,
    reference_now: datetime,
) -> int | None:
    parsed = parse_iso(approved_at)
    if parsed is None:
        return None
    delta = reference_now - parsed
    return int(delta.total_seconds())


def render_status_markdown(view: dict[str, Any]) -> str:
    """Render the status view as a compact markdown block."""
    lines: list[str] = ["# pipeline status", ""]
    if not view.get("pipeline_exists"):
        lines.append("- pipeline: (no commit_pipeline.json artifact found)")
        lines.append(f"- artifact: `{view.get('pipeline_artifact_path','')}`")
        lines.append("- recommended next action: `none`")
        return "\n".join(lines) + "\n"
    lines.extend([
        f"- artifact: `{view['pipeline_artifact_path']}`",
        f"- pipeline_id: `{view['pipeline_id']}`",
        f"- state: `{view['state']}`",
        f"- commit_sha: `{view['commit_sha']}`",
        f"- authorized_head_sha: `{view['authorized_head_sha']}`",
        f"- current_head_sha: `{view['current_head_sha']}`",
        f"- expires_at_utc: `{view['expires_at_utc']}`",
        f"- age_seconds: `{view['age_seconds']}`",
        f"- authorization_expired: `{view['authorization_expired']}`",
        f"- head_has_moved: `{view['head_has_moved']}`",
        f"- recommended next action: `{view['recommended_next_action']}`",
    ])
    return "\n".join(lines) + "\n"


def render_status_json(view: dict[str, Any]) -> str:
    """Render the status view as pretty JSON."""
    return json.dumps(view, indent=2)


def run_status(args) -> int:
    """Entry point for ``devctl pipeline --action status``."""
    from .support import resolve_pipeline_paths

    paths = resolve_pipeline_paths(
        repo_root=getattr(args, "repo_root_override", None),
        pipeline_root_override=_maybe_path(
            getattr(args, "pipeline_root_override", None)
        ),
        receipts_root_override=_maybe_path(
            getattr(args, "receipts_root_override", None)
        ),
    )
    view = build_status_view(paths)
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        print(render_status_json(view))
    else:
        print(render_status_markdown(view))
    return 0 if view["ok"] else 1


def _maybe_path(value: Any) -> Path | None:
    if value is None:
        return None
    return Path(value)
