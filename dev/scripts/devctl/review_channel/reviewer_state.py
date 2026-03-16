"""Repo-owned reviewer heartbeat and checkpoint writers for the markdown bridge."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..common import display_path
from .heartbeat import (
    LAST_CODEX_POLL_LOCAL_RE,
    LAST_CODEX_POLL_RE,
    LAST_WORKTREE_HASH_RE,
    NON_AUDIT_HASH_EXCLUDED_PREFIXES,
    _format_new_york_timestamp,
    _replace_or_insert_metadata_line,
    _rewrite_poll_status,
    compute_non_audit_worktree_hash,
)
from .peer_liveness import ReviewerMode, normalize_reviewer_mode

REVIEWER_MODE_RE = re.compile(r"(?m)^- Reviewer mode:\s*`.*?`\s*$")
MERGED_REVIEWER_MODE_RE = re.compile(
    r"(?m)^(- Last non-audit worktree hash:\s*`[^`]+`)(- Reviewer mode:\s*`[^`]+`\s*)$"
)
_SECTION_RE_TEMPLATE = r"(^## {heading}\s*$\n)(.*?)(?=^##\s+|\Z)"
_BRIDGE_EXCLUDED_REL_PATHS = ("code_audit.md",)


@dataclass(frozen=True)
class ReviewerStateWrite:
    """One repo-owned reviewer state write applied to the bridge."""

    bridge_path: str
    action: str
    reviewer_mode: str
    reason: str
    last_codex_poll_utc: str
    last_codex_poll_local: str
    last_worktree_hash: str


@dataclass(frozen=True)
class ReviewerCheckpointUpdate:
    """Reviewer-owned section updates for one checkpoint write."""

    current_verdict: str
    open_findings: str
    current_instruction: str
    reviewed_scope_items: tuple[str, ...]


@dataclass(frozen=True)
class ReviewerMetadataUpdate:
    """Metadata-only bridge update request."""

    reviewer_mode: ReviewerMode
    reason: str
    action: str
    worktree_hash: str | None
    poll_note: str


def reviewer_state_write_to_dict(
    write: ReviewerStateWrite | None,
) -> dict[str, object] | None:
    if write is None:
        return None
    return asdict(write)


def write_reviewer_heartbeat(
    *,
    repo_root: Path,
    bridge_path: Path,
    reviewer_mode: str,
    reason: str,
) -> ReviewerStateWrite:
    """Refresh only reviewer liveness metadata without claiming a new review."""
    bridge_text = bridge_path.read_text(encoding="utf-8")
    normalized_mode = normalize_reviewer_mode(reviewer_mode)
    existing_hash = _current_reviewed_hash(bridge_text)
    updated_text, write = _rewrite_reviewer_metadata(
        bridge_text=bridge_text,
        repo_root=repo_root,
        bridge_path=bridge_path,
        update=ReviewerMetadataUpdate(
            reviewer_mode=normalized_mode,
            reason=reason,
            action="reviewer-heartbeat",
            worktree_hash=None,
            poll_note=(
                "Reviewer heartbeat refreshed through repo-owned tooling "
                f"(mode: {normalized_mode}; reason: {reason}; reviewed-tree: {existing_hash[:12]})."
            ),
        ),
    )
    bridge_path.write_text(updated_text, encoding="utf-8")
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
    bridge_text = bridge_path.read_text(encoding="utf-8")
    normalized_mode = normalize_reviewer_mode(reviewer_mode)
    current_hash = compute_non_audit_worktree_hash(
        repo_root=repo_root,
        excluded_rel_paths=_BRIDGE_EXCLUDED_REL_PATHS,
        excluded_prefixes=NON_AUDIT_HASH_EXCLUDED_PREFIXES,
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
            poll_note=(
                "Reviewer checkpoint updated through repo-owned tooling "
                f"(mode: {normalized_mode}; reason: {reason}; tree: {current_hash[:12]})."
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
    updated_text = _replace_section(
        updated_text,
        heading="Last Reviewed Scope",
        body=_format_markdown_list(checkpoint.reviewed_scope_items),
    )
    bridge_path.write_text(updated_text, encoding="utf-8")
    return write


def _rewrite_reviewer_metadata(
    *,
    bridge_text: str,
    repo_root: Path,
    bridge_path: Path,
    update: ReviewerMetadataUpdate,
) -> tuple[str, ReviewerStateWrite]:
    now_utc = datetime.now(timezone.utc)
    last_codex_poll_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    last_codex_poll_local = _format_new_york_timestamp(now_utc)
    updated_text = _normalize_metadata_layout(bridge_text)
    current_bridge_hash = _current_reviewed_hash(bridge_text)
    updated_text = _replace_or_insert_metadata_line(
        updated_text,
        pattern=LAST_CODEX_POLL_RE,
        replacement=f"- Last Codex poll: `{last_codex_poll_utc}`",
    )
    updated_text = _replace_or_insert_metadata_line(
        updated_text,
        pattern=LAST_CODEX_POLL_LOCAL_RE,
        replacement=(
            "- Last Codex poll (Local America/New_York): "
            f"`{last_codex_poll_local}`"
        ),
    )
    updated_text = _replace_or_insert_metadata_line(
        updated_text,
        pattern=REVIEWER_MODE_RE,
        replacement=f"- Reviewer mode: `{update.reviewer_mode}`",
    )
    effective_hash = current_bridge_hash
    if update.worktree_hash is not None:
        updated_text = _replace_or_insert_metadata_line(
            updated_text,
            pattern=LAST_WORKTREE_HASH_RE,
            replacement=f"- Last non-audit worktree hash: `{update.worktree_hash}`",
        )
        effective_hash = update.worktree_hash
    updated_text = _rewrite_poll_status(updated_text, note=f"- {update.poll_note}")
    return updated_text, ReviewerStateWrite(
        bridge_path=display_path(bridge_path, repo_root=repo_root),
        action=update.action,
        reviewer_mode=update.reviewer_mode,
        reason=update.reason,
        last_codex_poll_utc=last_codex_poll_utc,
        last_codex_poll_local=last_codex_poll_local,
        last_worktree_hash=effective_hash,
    )


def _current_reviewed_hash(bridge_text: str) -> str:
    match = LAST_WORKTREE_HASH_RE.search(bridge_text)
    if match is None:
        return ""
    raw_line = match.group(0)
    return raw_line.split("`", 2)[1]


def _normalize_metadata_layout(bridge_text: str) -> str:
    return MERGED_REVIEWER_MODE_RE.sub(r"\1\n\2", bridge_text)


def _replace_section(text: str, *, heading: str, body: str) -> str:
    pattern = re.compile(
        _SECTION_RE_TEMPLATE.format(heading=re.escape(heading)),
        re.MULTILINE | re.DOTALL,
    )

    def replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}\n{body.strip()}\n\n"

    rewritten, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError(f"Unable to locate `{heading}` in the markdown bridge.")
    return rewritten


@dataclass(frozen=True)
class EnsureHeartbeatResult:
    """Outcome of one ensure-heartbeat cycle."""

    refreshed: bool
    reviewer_mode: str
    reason: str
    state_write: ReviewerStateWrite | None
    error: str | None


def ensure_reviewer_heartbeat(
    *,
    repo_root: Path,
    bridge_path: Path,
    reason: str = "ensure",
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
    mode_match = REVIEWER_MODE_RE.search(bridge_text)
    raw_mode = ""
    if mode_match:
        line = mode_match.group(0)
        if "`" in line:
            raw_mode = line.split("`", 2)[1]
    current_mode = normalize_reviewer_mode(raw_mode)
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


def _format_markdown_list(items: Iterable[str]) -> str:
    rows = [item.strip() for item in items if item.strip()]
    if not rows:
        return "- (none)"
    return "\n".join(f"- {row}" for row in rows)
