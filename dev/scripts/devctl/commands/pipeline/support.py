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
from ...review_channel.event_reducer import refresh_event_bundle
from ...review_channel.event_store import resolve_artifact_paths
from ...review_channel.state import refresh_status_snapshot
from ...runtime.pipeline_recovery_receipt import (
    PipelineRecoveryReceipt,
    utc_now_iso,
)
from ...runtime.pipeline_local_delivery_receipts import (
    apply_local_delivery_receipt,
)
from ...runtime.remote_commit_pipeline_state import (
    RECOVERABLE_PIPELINE_STATES,
    REFRESHABLE_PIPELINE_STATES,
    TERMINAL_PIPELINE_STATES,
    eligible_for_local_delivery,
)
from .head_movement import head_has_moved

PIPELINE_FILENAME = "commit_pipeline.json"
ABANDONED_RECEIPT_FILENAME = "pipeline_abandoned_receipt.json"
RECOVER_RECEIPT_FILENAME = "pipeline_recover_receipt.json"
REFRESH_RECEIPT_FILENAME = "pipeline_refresh_authorization_receipt.json"

# Authorization lifetime when recover / refresh reissues the window.
AUTHORIZATION_TTL_MINUTES = 30

# States where a commit has been recorded but remote publication is not
# yet acknowledged. These are the states where ``recover`` is allowed to
# re-bind the authorization to a new HEAD.
RECOVERABLE_STATES: frozenset[str] = RECOVERABLE_PIPELINE_STATES

# States where a fresh authorization window is semantically meaningful.
REFRESHABLE_STATES: frozenset[str] = REFRESHABLE_PIPELINE_STATES

# States that ``abandon`` refuses because there is no live pipeline.
TERMINAL_STATES: frozenset[str] = TERMINAL_PIPELINE_STATES

_PUSH_EXECUTE_COMMAND = "python3 dev/scripts/devctl.py push --execute"
_PIPELINE_ABANDON_COMMAND = (
    'python3 dev/scripts/devctl.py pipeline --action abandon --reason '
    '"<descriptive reason>" --format json'
)
_PIPELINE_RECOVER_COMMAND = (
    "python3 dev/scripts/devctl.py pipeline --action recover --format json"
)
_PIPELINE_REFRESH_AUTHORIZATION_COMMAND = (
    "python3 dev/scripts/devctl.py pipeline --action refresh-authorization --format json"
)
_PIPELINE_MARK_DELIVERED_LOCAL_COMMAND = (
    'python3 dev/scripts/devctl.py pipeline --action mark-delivered-local --reason '
    '"<descriptive reason>" --format json'
)
_PIPELINE_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py pipeline --action status --format json"
)


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
    if not isinstance(payload, dict):
        return {}
    return apply_local_delivery_receipt(
        payload,
        receipts_root=paths.receipts_root,
        pipeline_path=paths.pipeline_path,
    )


def write_pipeline_payload(
    paths: PipelinePaths,
    payload: dict[str, Any],
) -> None:
    """Write the pipeline JSON dict to disk, creating parent dirs.

    Per Codex rev_pkt_2424/2428: ``commit_pipeline.json`` has three
    production writers (``projection_bundle.write_projection_bundle``,
    ``remote_commit_pipeline_artifact.persist_remote_commit_pipeline_contract``,
    and this one). All three must use the same atomic-replace contract
    so concurrent readers (``check_review_surface_consistency``) never
    observe a half-written file.
    """
    from ...review_channel.projection_bundle import _atomic_write_text

    paths.pipeline_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(
        paths.pipeline_path,
        json.dumps(payload, indent=2) + "\n",
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


def refresh_pipeline_projections(paths: PipelinePaths) -> list[str]:
    """Refresh review-channel projections after a direct pipeline mutation."""
    warnings: list[str] = []
    config = active_path_config()
    review_channel_path = paths.repo_root / config.review_channel_rel
    if not review_channel_path.exists():
        return warnings
    bridge_path = paths.repo_root / config.bridge_rel
    try:
        artifact_paths = resolve_artifact_paths(repo_root=paths.repo_root)
        event_log = Path(artifact_paths.event_log_path)
        state_path = Path(artifact_paths.state_path)
        if event_log.exists() or state_path.exists():
            refresh_event_bundle(
                repo_root=paths.repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
        elif bridge_path.exists():
            refresh_status_snapshot(
                repo_root=paths.repo_root,
                bridge_path=bridge_path,
                review_channel_path=review_channel_path,
                output_root=paths.pipeline_path.parent,
            )
    except (OSError, ValueError) as exc:
        warnings.append(f"projection_refresh_failed: {exc}")
    return warnings


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


def recommended_next_action(
    payload: dict[str, Any],
    *,
    current_head: str,
    receipt_parent_sha: str = "",
    now: datetime | None = None,
) -> str:
    """Return the single recommended recovery action string for status output."""
    state = pipeline_state_of(payload)
    if not payload:
        return "none"
    expired = authorization_is_expired(payload, now=now)
    if state in TERMINAL_STATES and not (
        expired and state in REFRESHABLE_STATES
    ):
        return "none"
    if head_has_moved(
        payload,
        current_head=current_head,
        receipt_parent_sha=receipt_parent_sha,
    ):
        return "recover"
    if eligible_for_local_delivery(payload, current_head=current_head):
        return "mark-delivered-local"
    if state == "push_blocked":
        return "abandon"
    if expired and state in REFRESHABLE_STATES:
        return "refresh-authorization"
    return "none"


def recommended_next_command(
    payload: dict[str, Any],
    *,
    current_head: str,
    receipt_parent_sha: str = "",
    now: datetime | None = None,
) -> str:
    """Return the exact devctl command an operator/agent should run next."""
    state = pipeline_state_of(payload)
    if not payload:
        return ""
    expired = authorization_is_expired(payload, now=now)
    if state in TERMINAL_STATES and not (
        expired and state in REFRESHABLE_STATES
    ):
        return ""
    if head_has_moved(
        payload,
        current_head=current_head,
        receipt_parent_sha=receipt_parent_sha,
    ):
        return _PIPELINE_RECOVER_COMMAND
    if eligible_for_local_delivery(payload, current_head=current_head):
        return _PIPELINE_MARK_DELIVERED_LOCAL_COMMAND
    if state == "push_blocked":
        return _PIPELINE_ABANDON_COMMAND
    if expired and state in REFRESHABLE_STATES:
        return _PIPELINE_REFRESH_AUTHORIZATION_COMMAND
    if state in {"commit_recorded", "push_pending"}:
        return _PUSH_EXECUTE_COMMAND
    if state in RECOVERABLE_STATES:
        return _PIPELINE_STATUS_COMMAND
    return ""


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
