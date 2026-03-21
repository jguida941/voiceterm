"""Repo-owned reviewer heartbeat and checkpoint writers for the markdown bridge."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .bridge_file import rewrite_bridge_markdown
from .heartbeat import (
    NON_AUDIT_HASH_EXCLUDED_PREFIXES,
    compute_non_audit_worktree_hash,
)
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
from .write_preconditions import assert_expected_instruction_revision
from .peer_liveness import ReviewerMode, normalize_reviewer_mode

REVIEWER_MODE_RE = re.compile(r"(?m)^- Reviewer mode:\s*`.*?`\s*$")
_BRIDGE_EXCLUDED_REL_PATHS = ("bridge.md",)

@dataclass(frozen=True)
class ReviewerCheckpointUpdate:
    """Reviewer-owned section updates for one checkpoint write."""

    current_verdict: str
    open_findings: str
    current_instruction: str
    reviewed_scope_items: tuple[str, ...]
    rotate_instruction_revision: bool = False
    expected_instruction_revision: str | None = None

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
    current_hash = compute_non_audit_worktree_hash(
        repo_root=repo_root,
        excluded_rel_paths=_BRIDGE_EXCLUDED_REL_PATHS,
        excluded_prefixes=NON_AUDIT_HASH_EXCLUDED_PREFIXES,
    )
    reviewed_scope_body = _format_markdown_list(checkpoint.reviewed_scope_items)
    validate_reviewer_checkpoint_sections(
        current_verdict=checkpoint.current_verdict.strip(),
        open_findings=checkpoint.open_findings.strip(),
        current_instruction=checkpoint.current_instruction.strip(),
        reviewed_scope_body=reviewed_scope_body,
    )
    write: ReviewerStateWrite | None = None

    def transform(bridge_text: str) -> str:
        nonlocal write
        assert_expected_instruction_revision(
            bridge_text=bridge_text,
            expected_instruction_revision=checkpoint.expected_instruction_revision,
            action="reviewer-checkpoint",
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
        updated_text, write = _rewrite_reviewer_metadata(
            bridge_text=bridge_text,
            repo_root=repo_root,
            bridge_path=bridge_path,
            update=ReviewerMetadataUpdate(
                reviewer_mode=normalized_mode,
                reason=reason,
                action="reviewer-checkpoint",
                worktree_hash=current_hash,
                current_instruction_revision=instruction_revision,
                poll_note=(
                    "Reviewer checkpoint updated through repo-owned tooling "
                    f"(mode: {normalized_mode}; reason: {reason}; tree: {current_hash[:12]}; instruction-rev: {effective_instruction_revision})."
                ),
            ),
        )
        updated_text = _replace_section(
            updated_text,
            heading="Current Verdict",
            body=checkpoint.current_verdict.strip(),
        )
        updated_text = _replace_section(
            updated_text,
            heading="Open Findings",
            body=checkpoint.open_findings.strip(),
        )
        updated_text = _replace_section(
            updated_text,
            heading="Current Instruction For Claude",
            body=checkpoint.current_instruction.strip(),
        )
        return _replace_section(
            updated_text,
            heading="Last Reviewed Scope",
            body=reviewed_scope_body,
        )

    rewrite_bridge_markdown(bridge_path, transform=transform)
    assert write is not None
    _refresh_projections_after_checkpoint(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    return write


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
    mode_match = REVIEWER_MODE_RE.search(bridge_text)
    raw_mode = ""
    if mode_match:
        line = mode_match.group(0)
        if "`" in line:
            raw_mode = line.split("`", 2)[1]
    return normalize_reviewer_mode(raw_mode)
