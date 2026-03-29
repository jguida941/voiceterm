"""Internal helper machinery for reviewer-state bridge writes."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..common import display_path
from .heartbeat import (
    CURRENT_INSTRUCTION_REVISION_RE,
    LAST_CODEX_POLL_LOCAL_RE,
    LAST_CODEX_POLL_RE,
    LAST_WORKTREE_HASH_RE,
    _format_new_york_timestamp,
    _replace_or_insert_metadata_line,
    _rewrite_poll_status,
)
from .handoff import extract_bridge_snapshot, summarize_bridge_liveness
from .bridge_section_validation import find_embedded_markdown_headings
from .handoff_constants import find_suspicious_bridge_text_lines
from .peer_liveness import ReviewerMode, normalize_reviewer_mode

REVIEWER_MODE_RE = re.compile(r"(?m)^- Reviewer mode:\s*`.*?`\s*$")
MERGED_REVIEWER_MODE_RE = re.compile(
    r"(?m)^(- Last non-audit worktree hash:\s*`[^`]+`)(- Reviewer mode:\s*`[^`]+`\s*)$"
)
SECTION_RE_TEMPLATE = r"(^## {heading}[ \t]*$\n)(.*?)(?=^##\s+|\Z)"
_OPEN_FINDINGS_HEADING = "Open Findings"


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
    current_instruction_revision: str = ""


@dataclass(frozen=True)
class ReviewerMetadataUpdate:
    """Metadata-only bridge update request."""

    reviewer_mode: ReviewerMode
    reason: str
    action: str
    worktree_hash: str | None
    current_instruction_revision: str | None
    poll_note: str


@dataclass(frozen=True)
class EnsureHeartbeatResult:
    """Outcome of one ensure-heartbeat cycle."""

    refreshed: bool
    reviewer_mode: str
    reason: str
    state_write: ReviewerStateWrite | None
    error: str | None


def reviewer_state_write_to_dict(
    write: ReviewerStateWrite | None,
) -> dict[str, object] | None:
    if write is None:
        return None
    return asdict(write)


def current_reviewed_hash(bridge_text: str) -> str:
    match = LAST_WORKTREE_HASH_RE.search(bridge_text)
    if match is None:
        return ""
    raw_line = match.group(0)
    return raw_line.split("`", 2)[1]


def current_instruction_revision_from_bridge_text(bridge_text: str) -> str:
    match = CURRENT_INSTRUCTION_REVISION_RE.search(bridge_text)
    if match is None:
        return ""
    raw_line = match.group(0)
    return raw_line.split("`", 2)[1]


def write_reviewer_metadata(
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
    current_bridge_hash = current_reviewed_hash(bridge_text)
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
    current_instruction_revision = current_instruction_revision_from_bridge_text(
        bridge_text
    )
    if update.worktree_hash is not None:
        updated_text = _replace_or_insert_metadata_line(
            updated_text,
            pattern=LAST_WORKTREE_HASH_RE,
            replacement=f"- Last non-audit worktree hash: `{update.worktree_hash}`",
        )
        effective_hash = update.worktree_hash
    if update.current_instruction_revision is not None:
        updated_text = _replace_or_insert_metadata_line(
            updated_text,
            pattern=CURRENT_INSTRUCTION_REVISION_RE,
            replacement=(
                "- Current instruction revision: "
                f"`{update.current_instruction_revision}`"
            ),
        )
        current_instruction_revision = update.current_instruction_revision
    updated_text = _rewrite_poll_status(updated_text, note=f"- {update.poll_note}")
    return updated_text, ReviewerStateWrite(
        bridge_path=display_path(bridge_path, repo_root=repo_root),
        action=update.action,
        reviewer_mode=update.reviewer_mode,
        reason=update.reason,
        last_codex_poll_utc=last_codex_poll_utc,
        last_codex_poll_local=last_codex_poll_local,
        last_worktree_hash=effective_hash,
        current_instruction_revision=current_instruction_revision,
    )


def _rewrite_reviewer_metadata(
    *,
    bridge_text: str,
    repo_root: Path,
    bridge_path: Path,
    update: ReviewerMetadataUpdate,
) -> tuple[str, ReviewerStateWrite]:
    return write_reviewer_metadata(
        bridge_text=bridge_text,
        repo_root=repo_root,
        bridge_path=bridge_path,
        update=update,
    )


def select_instruction_revision(
    *,
    bridge_text: str,
    current_instruction: str,
    rotate_instruction_revision: bool,
) -> str | None:
    normalized_new = _normalize_instruction_body(current_instruction)
    if not normalized_new:
        return ""

    existing_revision = current_instruction_revision_from_bridge_text(bridge_text)
    existing_instruction = _current_instruction_body_from_bridge_text(bridge_text)

    if (
        not rotate_instruction_revision
        and existing_revision
        and existing_instruction
        and normalized_new == existing_instruction
    ):
        return None

    if rotate_instruction_revision:
        rotation_seed = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        return _instruction_revision(f"{normalized_new}\n{rotation_seed}")

    return _instruction_revision(normalized_new)


def _normalize_metadata_layout(bridge_text: str) -> str:
    return MERGED_REVIEWER_MODE_RE.sub(r"\1\n\2", bridge_text)


def _replace_section(text: str, *, heading: str, body: str) -> str:
    pattern = re.compile(
        SECTION_RE_TEMPLATE.format(heading=re.escape(heading)),
        re.MULTILINE | re.DOTALL,
    )

    def replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}\n{body.strip()}\n\n"

    rewritten, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError(f"Unable to locate `{heading}` in the markdown bridge.")
    return rewritten


def _format_markdown_list(items: Iterable[str]) -> str:
    rows = [item.strip() for item in items if item.strip()]
    if not rows:
        return "- (none)"
    return "\n".join(f"- {row}" for row in rows)


def validate_reviewer_checkpoint_sections(
    *,
    current_verdict: str,
    open_findings: str,
    current_instruction: str,
    reviewed_scope_body: str,
) -> None:
    """Reject terminal/status contamination before it becomes reviewer authority."""
    section_bodies = (
        ("Current Verdict", current_verdict),
        ("Open Findings", open_findings),
        ("Current Instruction For Claude", current_instruction),
        ("Last Reviewed Scope", reviewed_scope_body),
    )
    for heading, body in section_bodies:
        suspicious_lines = find_suspicious_bridge_text_lines(body)
        if suspicious_lines:
            quoted = "; ".join(f"`{line}`" for line in suspicious_lines)
            raise ValueError(
                "Reviewer checkpoint rejected suspicious terminal/status text in "
                f"`{heading}`: {quoted}"
            )
        heading_lines = find_embedded_markdown_headings(body)
        if heading_lines:
            quoted = "; ".join(f"`{line}`" for line in heading_lines)
            raise ValueError(
                "Reviewer checkpoint rejected embedded markdown headings in "
                f"`{heading}`: {quoted}"
            )


def _current_instruction_body_from_bridge_text(bridge_text: str) -> str:
    match = re.search(
        SECTION_RE_TEMPLATE.format(
            heading=re.escape("Current Instruction For Claude"),
        ),
        bridge_text,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        return ""
    return _normalize_instruction_body(match.group(2))


def _normalize_instruction_body(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    normalized = "\n".join(lines).strip()
    return normalized


def _instruction_revision(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def _normalize_open_findings_for_live_state(bridge_text: str) -> str:
    """Drop stale ACK-mismatch findings once the live ACK is current."""
    snapshot = extract_bridge_snapshot(bridge_text)
    open_findings = snapshot.sections.get(_OPEN_FINDINGS_HEADING, "").strip()
    if not open_findings:
        return bridge_text
    liveness = summarize_bridge_liveness(snapshot)
    normalized_findings = _prune_resolved_open_findings(
        open_findings=open_findings,
        claude_ack_current=liveness.claude_ack_current,
    )
    if normalized_findings == open_findings:
        return bridge_text
    return _replace_section(
        bridge_text,
        heading=_OPEN_FINDINGS_HEADING,
        body=normalized_findings,
    )


def _prune_resolved_open_findings(
    *,
    open_findings: str,
    claude_ack_current: bool,
) -> str:
    if not claude_ack_current:
        return open_findings
    items = _split_markdown_items(open_findings)
    kept = [item for item in items if not _is_ack_stale_finding(item)]
    if not kept:
        return "- none"
    return "\n".join(kept)


def _split_markdown_items(text: str) -> list[str]:
    """Split a markdown list body into top-level bullet blocks."""
    lines = text.splitlines()
    if not any(line.lstrip().startswith("- ") for line in lines):
        return [text.strip()] if text.strip() else []
    items: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.lstrip().startswith("- "):
            if current:
                items.append(current)
            current = [line]
            continue
        if current:
            current.append(line)
    if current:
        items.append(current)
    return ["\n".join(block).strip() for block in items if "\n".join(block).strip()]


def _is_ack_stale_finding(item: str) -> bool:
    lower = item.lower()
    if "claude ack" not in lower:
        return False
    return (
        "stale" in lower
        or "does not match" in lower
        or "instruction revision" in lower
        or "instruction-rev" in lower
    )
