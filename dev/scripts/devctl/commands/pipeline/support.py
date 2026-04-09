"""Shared loaders, writers, and pure state logic for the pipeline command.

Keeping the raw-JSON IO, the HEAD probe, and the recommendation function
in one place lets each action handler stay short and test the business
rules (not the filesystem plumbing) directly.

The pipeline artifact is read and written as a plain dict rather than
through the typed :class:`RemoteCommitPipelineContract` model. This is
deliberate: the recovery command must never drop unknown fields on the
floor when a future schema adds them, and the typed model today does
not guarantee round-trip preservation of every optional field.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...repo_packs import active_path_config
from ...runtime.pipeline_recovery_receipt import (
    PipelineRecoveryReceipt,
    utc_now_iso,
)

PIPELINE_FILENAME = "commit_pipeline.json"
ABANDONED_RECEIPT_FILENAME = "pipeline_abandoned_receipt.json"
RECOVER_RECEIPT_FILENAME = "pipeline_recover_receipt.json"
REFRESH_RECEIPT_FILENAME = "pipeline_refresh_authorization_receipt.json"

# Authorization lifetime when recover / refresh reissues the window.
AUTHORIZATION_TTL_MINUTES = 30

# States where a commit has been recorded but remote publication is not
# yet acknowledged. These are the states where ``recover`` is allowed to
# re-bind the authorization to a new HEAD.
RECOVERABLE_STATES: frozenset[str] = frozenset({
    "commit_recorded",
    "push_blocked",
})

# States where a fresh authorization window is semantically meaningful.
REFRESHABLE_STATES: frozenset[str] = frozenset({
    "commit_recorded",
    "push_blocked",
    "awaiting_push",
})

# States that ``abandon`` refuses because there is no live pipeline.
TERMINAL_STATES: frozenset[str] = frozenset({
    "push_completed",
    "abandoned",
})


@dataclass(frozen=True, slots=True)
class PipelinePaths:
    """Resolved filesystem paths the pipeline command writes to."""

    repo_root: Path
    pipeline_path: Path
    receipts_root: Path


def resolve_pipeline_paths(
    *,
    repo_root: Path | None = None,
    pipeline_root_override: Path | None = None,
    receipts_root_override: Path | None = None,
) -> PipelinePaths:
    """Resolve canonical pipeline artifact + receipt output paths."""
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    config = active_path_config()
    # Canonical pipeline artifact lives under the projections/latest dir
    # (the same path the governed executor writes to). Tests may override.
    if pipeline_root_override is not None:
        pipeline_dir = Path(pipeline_root_override)
    else:
        pipeline_dir = root / config.review_projections_dir_rel
    if receipts_root_override is not None:
        receipts_dir = Path(receipts_root_override)
    else:
        receipts_dir = root / config.review_status_dir_rel
    return PipelinePaths(
        repo_root=root,
        pipeline_path=pipeline_dir / PIPELINE_FILENAME,
        receipts_root=receipts_dir,
    )


def load_pipeline_payload(paths: PipelinePaths) -> dict[str, Any]:
    """Load the pipeline JSON dict or return ``{}`` when it is missing."""
    if not paths.pipeline_path.exists():
        return {}
    try:
        raw = paths.pipeline_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_pipeline_payload(
    paths: PipelinePaths,
    payload: dict[str, Any],
) -> None:
    """Write the pipeline JSON dict to disk, creating parent dirs."""
    paths.pipeline_path.parent.mkdir(parents=True, exist_ok=True)
    paths.pipeline_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def write_receipt(
    paths: PipelinePaths,
    receipt: PipelineRecoveryReceipt,
    *,
    filename: str,
) -> Path:
    """Persist a typed :class:`PipelineRecoveryReceipt` under the receipts dir."""
    paths.receipts_root.mkdir(parents=True, exist_ok=True)
    receipt_path = paths.receipts_root / filename
    receipt_path.write_text(
        json.dumps(receipt.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    return receipt_path


def resolve_current_head(*, repo_root: Path) -> str:
    """Return the current HEAD sha for the given repo root.

    Tests can bypass the git invocation by setting
    ``DEVCTL_PIPELINE_FAKE_HEAD`` in the environment. Returning an empty
    string signals "HEAD not available" so the calling action can choose
    a safe branch.
    """
    fake = os.environ.get("DEVCTL_PIPELINE_FAKE_HEAD")
    if fake is not None:
        return fake.strip()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def pipeline_id_of(payload: dict[str, Any]) -> str:
    """Safely pull the pipeline id from a payload dict."""
    value = payload.get("pipeline_id")
    return str(value) if isinstance(value, str) else ""


def pipeline_state_of(payload: dict[str, Any]) -> str:
    """Safely pull the pipeline state from a payload dict."""
    value = payload.get("state")
    return str(value) if isinstance(value, str) else ""


def authorization_of(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the ``push_authorization`` sub-dict, or an empty dict."""
    auth = payload.get("push_authorization")
    return auth if isinstance(auth, dict) else {}


def authorized_head_sha_of(payload: dict[str, Any]) -> str:
    """Return the ``authorized_head_sha`` field from the auth sub-dict."""
    value = authorization_of(payload).get("authorized_head_sha")
    return str(value) if isinstance(value, str) else ""


def expires_at_of(payload: dict[str, Any]) -> str:
    """Return the ``expires_at_utc`` field from the auth sub-dict."""
    value = authorization_of(payload).get("expires_at_utc")
    return str(value) if isinstance(value, str) else ""


def parse_iso(timestamp: str) -> datetime | None:
    """Parse an ISO8601 ``...Z`` timestamp into a timezone-aware datetime."""
    if not timestamp:
        return None
    cleaned = timestamp.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def authorization_is_expired(
    payload: dict[str, Any],
    *,
    now: datetime | None = None,
) -> bool:
    """Return ``True`` when ``expires_at_utc`` is in the past."""
    expires_at = parse_iso(expires_at_of(payload))
    if expires_at is None:
        return False
    reference = now or datetime.now(timezone.utc)
    return expires_at < reference


def head_has_moved(payload: dict[str, Any], *, current_head: str) -> bool:
    """Return ``True`` when ``current_head`` differs from the authorized head."""
    if not current_head:
        return False
    authorized = authorized_head_sha_of(payload)
    return bool(authorized) and current_head != authorized


def recommended_next_action(
    payload: dict[str, Any],
    *,
    current_head: str,
    now: datetime | None = None,
) -> str:
    """Return the single recommended recovery action string for status output."""
    state = pipeline_state_of(payload)
    if not payload:
        return "none"
    if state in TERMINAL_STATES:
        return "none"
    if head_has_moved(payload, current_head=current_head):
        return "recover"
    if authorization_is_expired(payload, now=now):
        return "refresh-authorization"
    if state in RECOVERABLE_STATES:
        return "abandon"
    return "none"


def make_refreshed_authorization(
    existing: dict[str, Any],
    *,
    operator_actor: str,
    now_utc: str | None = None,
    new_head_sha: str | None = None,
) -> dict[str, Any]:
    """Return a new ``push_authorization`` dict with refreshed timestamps."""
    now = now_utc or utc_now_iso()
    # Derive a deterministic authorization id from the current timestamp
    # with colon/dot/dash stripping so the id is file-name safe.
    compact_now = now.replace("-", "").replace(":", "").replace(".", "")
    new_auth = dict(existing)
    new_auth["authorization_id"] = f"push-auth-{compact_now}"
    new_auth["approved_at_utc"] = now
    new_auth["approved_by"] = operator_actor or new_auth.get("approved_by", "operator")
    expires_dt = datetime.now(timezone.utc) + timedelta(
        minutes=AUTHORIZATION_TTL_MINUTES,
    )
    new_auth["expires_at_utc"] = expires_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if new_head_sha is not None:
        new_auth["authorized_head_sha"] = new_head_sha
    return new_auth
