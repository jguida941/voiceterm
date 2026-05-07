"""Repo-owned reviewer heartbeat and checkpoint writers for the markdown bridge."""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from pathlib import Path

from .bridge_file import rewrite_bridge_markdown
from .heartbeat import (
    bridge_excluded_rel_paths,
    compute_non_audit_worktree_hash,
    non_audit_hash_excluded_prefixes,
)
from .instruction_reset import reset_implementer_sections_on_instruction_change
from .reviewer_state_support import (
    EnsureHeartbeatResult,
    ReviewerMetadataUpdate,
    ReviewerStateWrite,
    _format_markdown_list,
    _normalize_open_findings_for_live_state,
    _replace_section,
    _rewrite_reviewer_metadata,
    current_instruction_revision_from_bridge_text,
    current_reviewed_hash,
    reviewer_state_write_to_dict,
    select_instruction_revision,
    validate_reviewer_checkpoint_sections,
)
from .write_preconditions import (
    assert_expected_implementer_state_hash,
    assert_expected_instruction_revision,
    assert_reviewer_inbox_empty,
)
from .current_session_projection import bridge_implementer_state_hash
from .handoff import extract_bridge_snapshot
from .peer_liveness import ReviewerMode, normalize_reviewer_mode
from .reviewer_head_tracking import (
    compute_review_range as compute_review_range,
    current_head_sha as _current_head_sha,
)
REVIEWER_MODE_RE = re.compile(r"(?m)^- Reviewer mode:\s*`.*?`\s*$")
DECLARED_REVIEWER_MODE_RE = re.compile(
    r"(?m)^- Declared reviewer mode:\s*`.*?`\s*$"
)


DEFAULT_REVIEWER_ACTOR = "codex"


@dataclass(frozen=True)
class ReviewerCheckpointUpdate:
    """Reviewer-owned section updates for one checkpoint write."""

    current_verdict: str
    open_findings: str
    current_instruction: str
    reviewed_scope_items: tuple[str, ...]
    rotate_instruction_revision: bool = False
    expected_instruction_revision: str | None = None
    expected_implementer_state_hash: str | None = None
    actor: str = DEFAULT_REVIEWER_ACTOR
    allow_unread_inbox: bool = False

def write_reviewer_heartbeat(
    *,
    repo_root: Path,
    bridge_path: Path,
    reviewer_mode: str,
    reason: str,
) -> ReviewerStateWrite:
    """Refresh only reviewer liveness metadata without claiming a new review."""
    normalized_mode = normalize_reviewer_mode(reviewer_mode)
    write: ReviewerStateWrite | None = None

    def transform(bridge_text: str) -> str:
        nonlocal write
        normalized_text = _normalize_open_findings_for_live_state(bridge_text)
        existing_hash = current_reviewed_hash(normalized_text)
        updated_text, write = _rewrite_reviewer_metadata(
            bridge_text=normalized_text,
            repo_root=repo_root,
            bridge_path=bridge_path,
            update=ReviewerMetadataUpdate(
                reviewer_mode=normalized_mode,
                reason=reason,
                action="reviewer-heartbeat",
                worktree_hash=None,
                current_instruction_revision=None,
                poll_note=(
                    "Reviewer heartbeat refreshed through repo-owned tooling "
                    f"(mode: {normalized_mode}; reason: {reason}; reviewed-tree: {existing_hash[:12]})."
                ),
            ),
        )
        return updated_text

    rewrite_bridge_markdown(bridge_path, transform=transform)
    assert write is not None
    if normalized_mode == "single_agent":
        try:
            from .remote_control_attachment_artifact import deactivate_repo_remote_control_attachments
            deactivate_repo_remote_control_attachments(repo_root=repo_root)
        except (ImportError, OSError, ValueError):
            pass
    _refresh_projections_after_checkpoint(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    return write

def write_reviewer_checkpoint(
    *,
    repo_root: Path,
    bridge_path: Path,
    reviewer_mode: str,
    reason: str,
    checkpoint: ReviewerCheckpointUpdate,
) -> ReviewerStateWrite:
    """Atomically advance reviewer truth and heartbeat for a real review pass."""
    normalized_mode = normalize_reviewer_mode(reviewer_mode)
    observed_hash = compute_non_audit_worktree_hash(
        repo_root=repo_root,
        excluded_rel_paths=bridge_excluded_rel_paths(
            repo_root=repo_root,
            bridge_path=bridge_path,
        ),
        excluded_prefixes=non_audit_hash_excluded_prefixes(),
    )
    head_sha = _current_head_sha(repo_root)
    preserve_reviewed_hash = reason.strip().lower() == "next-plan-item"
    reviewed_scope_body = _format_markdown_list(checkpoint.reviewed_scope_items)
    validate_reviewer_checkpoint_sections(
        current_verdict=checkpoint.current_verdict.strip(),
        open_findings=checkpoint.open_findings.strip(),
        current_instruction=checkpoint.current_instruction.strip(),
        reviewed_scope_body=reviewed_scope_body,
    )
    normalized_actor = (checkpoint.actor or DEFAULT_REVIEWER_ACTOR).strip()
    override_unread_ids = assert_reviewer_inbox_empty(
        repo_root=repo_root,
        reviewer_actor=normalized_actor,
        allow_unread_inbox=checkpoint.allow_unread_inbox,
        reason=reason,
    )
    write: ReviewerStateWrite | None = None

    def transform(bridge_text: str) -> str:
        nonlocal write
        assert_expected_instruction_revision(
            bridge_text=bridge_text,
            expected_instruction_revision=checkpoint.expected_instruction_revision,
            action="reviewer-checkpoint",
        )
        assert_expected_implementer_state_hash(
            bridge_text=bridge_text,
            expected_implementer_state_hash=checkpoint.expected_implementer_state_hash,
            action="reviewer-checkpoint",
        )
        preserved_hash = current_reviewed_hash(bridge_text)
        if preserve_reviewed_hash and not preserved_hash:
            raise ValueError(
                "Reviewer checkpoint with reason `next-plan-item` requires an "
                "existing reviewed hash to preserve."
            )
        effective_hash = preserved_hash if preserve_reviewed_hash else observed_hash
        previous_instruction_revision = current_instruction_revision_from_bridge_text(
            bridge_text
        )
        instruction_revision = select_instruction_revision(
            bridge_text=bridge_text,
            current_instruction=checkpoint.current_instruction,
            rotate_instruction_revision=checkpoint.rotate_instruction_revision,
        )
        effective_instruction_revision = (
            instruction_revision
            if instruction_revision is not None
            else current_instruction_revision_from_bridge_text(bridge_text)
        )
        accepted_impl_hash = bridge_implementer_state_hash(extract_bridge_snapshot(bridge_text))
        updated_text, write = _rewrite_reviewer_metadata(
            bridge_text=bridge_text,
            repo_root=repo_root,
            bridge_path=bridge_path,
            update=ReviewerMetadataUpdate(
                reviewer_mode=normalized_mode,
                reason=reason,
                action="reviewer-checkpoint",
                worktree_hash=effective_hash,
                current_instruction_revision=instruction_revision,
                reviewer_accepted_implementer_state_hash=accepted_impl_hash,
                head_at_push_time=head_sha,
                poll_note=(
                    (
                        "Reviewer checkpoint preserved reviewed baseline through "
                        "repo-owned tooling "
                        if preserve_reviewed_hash
                        else "Reviewer checkpoint updated through repo-owned tooling "
                    )
                    + f"(mode: {normalized_mode}; reason: {reason}; "
                    f"observed-tree: {observed_hash[:12]}; "
                    f"reviewed-tree: {effective_hash[:12]}; "
                    f"instruction-rev: {effective_instruction_revision})."
                ),
            ),
        )
        updated_text = _replace_reviewer_checkpoint_sections(
            updated_text,
            checkpoint=checkpoint,
            reviewed_scope_body=reviewed_scope_body,
        )
        return reset_implementer_sections_on_instruction_change(
            updated_text,
            previous_instruction_revision=previous_instruction_revision,
            next_instruction_revision=effective_instruction_revision or "",
        )

    def emit_typed_checkpoint(_: str) -> None:
        assert write is not None
        _append_typed_reviewer_checkpoint_event(
            repo_root=repo_root,
            reviewer_mode=normalized_mode,
            reason=reason,
            reviewer_actor=normalized_actor,
            current_instruction=checkpoint.current_instruction.strip(),
            current_instruction_revision=str(
                getattr(write, "current_instruction_revision", "") or ""
            ),
            open_findings=checkpoint.open_findings.strip(),
            worktree_hash=str(getattr(write, "worktree_hash", "") or ""),
        )

    rewrite_bridge_markdown(
        bridge_path,
        transform=transform,
        before_write=emit_typed_checkpoint,
    )
    assert write is not None
    write = dataclasses.replace(
        write,
        reviewer_actor=normalized_actor,
        inbox_override_applied=bool(override_unread_ids),
        inbox_override_unread_packet_ids=override_unread_ids,
    )
    _refresh_projections_after_checkpoint(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    return write


def _replace_reviewer_checkpoint_sections(
    text: str,
    *,
    checkpoint: ReviewerCheckpointUpdate,
    reviewed_scope_body: str,
) -> str:
    text = _replace_section(
        text,
        heading="Current Verdict",
        body=checkpoint.current_verdict.strip(),
    )
    text = _replace_section(
        text,
        heading="Open Findings",
        body=checkpoint.open_findings.strip(),
    )
    text = _replace_section(
        text,
        heading="Current Instruction For Claude",
        body=checkpoint.current_instruction.strip(),
    )
    return _replace_section(
        text,
        heading="Last Reviewed Scope",
        body=reviewed_scope_body,
    )


def _append_typed_reviewer_checkpoint_event(
    *,
    repo_root: Path,
    reviewer_mode: str,
    reason: str,
    reviewer_actor: str,
    current_instruction: str,
    current_instruction_revision: str,
    open_findings: str,
    worktree_hash: str,
) -> None:
    """Append a typed reviewer_checkpoint event before bridge markdown advances."""
    import secrets
    from hashlib import sha256

    from ..repo_packs import active_path_config
    from ..time_utils import utc_timestamp
    from .event_store import (
        DEFAULT_REVIEW_CHANNEL_PLAN_ID as _DEFAULT_PLAN_ID,
        DEFAULT_REVIEW_CHANNEL_SESSION_ID as _DEFAULT_SESSION_ID,
        append_event as _append,
        load_events as _load,
        resolve_artifact_paths as _resolve,
    )
    from .reviewer_authority_events import (
        REVIEWER_CHECKPOINT_EVENT_TYPE as _CHECKPOINT_TYPE,
    )
    from .state import project_id_for_repo

    config = active_path_config()
    artifact_paths = _resolve(
        repo_root=repo_root,
        artifact_root_rel=getattr(config, "review_artifact_root_rel", None),
        state_json_rel=getattr(config, "review_state_json_rel", None),
        projections_dir_rel=getattr(config, "review_projections_dir_rel", None),
    )
    events_path = Path(artifact_paths.event_log_path)
    existing_events = _load(events_path) if events_path.exists() else []
    timestamp = utc_timestamp()
    project_id = project_id_for_repo(repo_root)
    session_id, plan_id = _reviewer_checkpoint_identifiers(
        repo_root,
        default_session_id=_DEFAULT_SESSION_ID,
        default_plan_id=_DEFAULT_PLAN_ID,
    )
    # Idempotency key prevents duplicate reviewer_checkpoint events from
    # repeated checkpoint writes within the same revision/actor/instruction.
    key_material = "|".join(
        [
            _CHECKPOINT_TYPE,
            current_instruction_revision,
            reviewer_actor,
            reviewer_mode,
            sha256(current_instruction.encode("utf-8")).hexdigest()[:16],
        ]
    )
    idempotency_key = sha256(key_material.encode("utf-8")).hexdigest()[:24]
    event = {
        "event_type": _CHECKPOINT_TYPE,
        "schema_version": 1,
        "source": "review_channel",
        "session_id": session_id,
        "plan_id": plan_id,
        "project_id": project_id,
        "timestamp_utc": timestamp,
        "idempotency_key": idempotency_key,
        "nonce": secrets.token_hex(12),
        "actor": reviewer_actor,
        "reviewer_actor": reviewer_actor,
        "payload": {
            "current_instruction": current_instruction,
            "current_instruction_revision": current_instruction_revision,
            "open_findings": open_findings,
            "reviewer_mode": reviewer_mode,
            "worktree_hash": worktree_hash,
            "reviewer_actor": reviewer_actor,
            "reason": reason,
        },
    }
    _append(events_path, event, existing_events=existing_events)


def _reviewer_checkpoint_identifiers(
    repo_root: Path,
    *,
    default_session_id: str,
    default_plan_id: str,
) -> tuple[str, str]:
    try:
        from ..runtime.review_state_locator import load_current_review_state_payload

        payload = load_current_review_state_payload(
            repo_root,
            prefer_cached_projection=True,
            allow_live_refresh=False,
        )
        review = payload.get("review") if isinstance(payload, dict) else None
        if isinstance(review, dict):
            session_id = str(review.get("session_id") or "").strip()
            plan_id = str(review.get("plan_id") or "").strip()
            if session_id or plan_id:
                return (
                    session_id or default_session_id,
                    plan_id or default_plan_id,
                )
    except (ImportError, OSError, RuntimeError, ValueError):
        pass
    return default_session_id, default_plan_id


def _refresh_projections_after_checkpoint(
    *,
    repo_root: Path,
    bridge_path: Path,
) -> None:
    """Best-effort projection refresh so JSON state stays consistent with bridge markdown."""
    try:
        from .state import refresh_status_snapshot
        from ..repo_packs import active_path_config

        config = active_path_config()
        review_channel_path = repo_root / config.review_channel_rel
        output_root = repo_root / config.review_projections_dir_rel
        if not review_channel_path.exists():
            return
        output_root.mkdir(parents=True, exist_ok=True)
        refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=output_root,
            warnings=[],
            errors=[],
        )
    except (ImportError, OSError, ValueError):
        pass


def ensure_reviewer_heartbeat(
    *,
    repo_root: Path,
    bridge_path: Path,
    reason: str = "ensure",
    requested_reviewer_mode: str | None = None,
) -> EnsureHeartbeatResult:
    """Check bridge liveness and refresh heartbeat if reviewer mode is active.

    This is the shared backend seam for the persistent heartbeat publisher.
    Returns a structured result instead of raising on missing/inactive bridge
    so callers can decide how to report.
    """
    if not bridge_path.exists():
        return EnsureHeartbeatResult(
            refreshed=False,
            reviewer_mode="unknown",
            reason=reason,
            state_write=None,
            error="Bridge file does not exist",
        )
    bridge_text = bridge_path.read_text(encoding="utf-8")
    current_mode = reviewer_mode_from_bridge_text(bridge_text)
    requested_mode = normalize_reviewer_mode(
        requested_reviewer_mode or str(current_mode)
    )
    if (
        current_mode != ReviewerMode.ACTIVE_DUAL_AGENT
        and requested_mode == ReviewerMode.ACTIVE_DUAL_AGENT
    ):
        state_write = write_reviewer_heartbeat(
            repo_root=repo_root,
            bridge_path=bridge_path,
            reviewer_mode=str(requested_mode),
            reason=reason,
        )
        return EnsureHeartbeatResult(
            refreshed=True,
            reviewer_mode=str(requested_mode),
            reason=reason,
            state_write=state_write,
            error=None,
        )
    if current_mode != ReviewerMode.ACTIVE_DUAL_AGENT:
        return EnsureHeartbeatResult(
            refreshed=False,
            reviewer_mode=str(current_mode),
            reason=reason,
            state_write=None,
            error=None,
        )
    state_write = write_reviewer_heartbeat(
        repo_root=repo_root,
        bridge_path=bridge_path,
        reviewer_mode=str(current_mode),
        reason=reason,
    )
    return EnsureHeartbeatResult(
        refreshed=True,
        reviewer_mode=str(current_mode),
        reason=reason,
        state_write=state_write,
        error=None,
    )


def reviewer_mode_from_bridge_text(bridge_text: str) -> ReviewerMode:
    mode_match = DECLARED_REVIEWER_MODE_RE.search(bridge_text)
    if mode_match is None:
        mode_match = REVIEWER_MODE_RE.search(bridge_text)
    raw_mode = ""
    if mode_match:
        line = mode_match.group(0)
        if "`" in line:
            raw_mode = line.split("`", 2)[1]
    return normalize_reviewer_mode(raw_mode)
