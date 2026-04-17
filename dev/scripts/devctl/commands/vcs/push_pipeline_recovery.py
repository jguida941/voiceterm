"""Helpers for governed push reuse of an existing commit pipeline."""

from __future__ import annotations

from datetime import datetime, timezone

from ...config import REPO_ROOT
from ...governance.push_state import current_head_commit_sha
from ..pipeline.refresh_authorization_action import apply_refresh_authorization


def maybe_refresh_same_head_pipeline_authorization(*, args, executor, pipeline):
    """Refresh an expired same-HEAD authorization window before governed push."""
    if not bool(getattr(args, "execute", False)):
        return pipeline
    authorization = getattr(pipeline, "push_authorization", None)
    if authorization is None:
        return pipeline
    expires_at = str(getattr(authorization, "expires_at_utc", "") or "").strip()
    if not authorization_expired(expires_at):
        return pipeline
    current_head = current_head_commit_sha(repo_root=REPO_ROOT)
    authorized_head = str(
        getattr(authorization, "authorized_head_sha", "") or ""
    ).strip()
    if not current_head or current_head != authorized_head:
        return pipeline
    result = apply_refresh_authorization(
        repo_root=REPO_ROOT,
        operator_actor="operator",
        reason="devctl.push auto-refreshed same-HEAD authorization window",
    )
    if not result.get("ok"):
        return pipeline
    return executor.load_pipeline()


def authorization_expired(expires_at_utc: str) -> bool:
    """Return True when the authorization expiry timestamp is in the past."""
    value = expires_at_utc.strip()
    if not value:
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        expires_at = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return expires_at < datetime.now(timezone.utc)
