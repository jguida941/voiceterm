"""Internal helper machinery for reviewer-state bridge writes."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..common import display_path
from .reviewer_state_normalize import (
    current_instruction_body_from_bridge_text as _current_instruction_body_from_bridge_text,
    instruction_revision as _instruction_revision,
    normalize_instruction_body as _normalize_instruction_body,
    normalize_open_findings_for_live_state as _normalize_open_findings_for_live_state,
    prune_resolved_open_findings as _prune_resolved_open_findings,
    split_markdown_items as _split_markdown_items,
    is_ack_stale_finding as _is_ack_stale_finding,
)
from .heartbeat import (
    CURRENT_INSTRUCTION_REVISION_RE,
    HEAD_AT_PUSH_TIME_RE,
    LAST_CHECKPOINT_ACTION_RE,
    LAST_CODEX_POLL_LOCAL_RE,
    LAST_CODEX_POLL_RE,
    LAST_WORKTREE_HASH_RE,
    _format_local_timestamp,
    _replace_or_insert_metadata_line,
)
from .poll_status import rewrite_poll_status as _rewrite_poll_status
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
    reviewer_accepted_implementer_state_hash: str = ""
    head_at_push_time: str = ""
    # Reviewer actor that wrote this checkpoint ("codex"/"claude"/empty for
    # legacy). Surfaced on audit payloads so operators can trace which
    # reviewer advanced the typed state.
    reviewer_actor: str = ""
    # Inbox override audit trail. Populated only when an emergency
    # `--allow-unread-inbox` bypass was used to write this checkpoint; the
    # tuple carries the unread packet ids that were present at write time.
    inbox_override_applied: bool = False
    inbox_override_unread_packet_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewerMetadataUpdate:
    """Metadata-only bridge update request."""

    reviewer_mode: ReviewerMode
    reason: str
    action: str
    worktree_hash: str | None
    current_instruction_revision: str | None
    poll_note: str
    reviewer_accepted_implementer_state_hash: str = ""
    head_at_push_time: str | None = None


@dataclass(frozen=True)
class EnsureHeartbeatResult:
    """Outcome of one ensure-heartbeat cycle."""

    refreshed: bool
    reviewer_mode: str
    reason: str
    state_write: ReviewerStateWrite | None
    error: str | None
    suppressed: bool = False


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
    last_codex_poll_local = _format_local_timestamp(now_utc)
    updated_text = _normalize_metadata_layout(bridge_text)
    current_bridge_hash = current_reviewed_hash(bridge_text)
    updated_text = _replace_or_insert_metadata_line(
        updated_text,
        pattern=LAST_CODEX_POLL_RE,
        replacement=f"- Last Codex poll: `{last_codex_poll_utc}`",
    )
    from ..repo_packs import active_path_config

    tz_label = active_path_config().display_timezone
    updated_text = _replace_or_insert_metadata_line(
        updated_text,
        pattern=LAST_CODEX_POLL_LOCAL_RE,
        replacement=(
            f"- Last Codex poll (Local {tz_label}): "
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
    if update.action == "reviewer-checkpoint":
        updated_text = _replace_or_insert_metadata_line(
            updated_text,
            pattern=LAST_CHECKPOINT_ACTION_RE,
            replacement=f"- Last checkpoint action: `{update.action}`",
        )
    effective_head_at_push = ""
    if update.head_at_push_time is not None:
        updated_text = _replace_or_insert_metadata_line(
            updated_text,
            pattern=HEAD_AT_PUSH_TIME_RE,
            replacement=f"- Head at push time: `{update.head_at_push_time}`",
        )
        effective_head_at_push = update.head_at_push_time
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
        reviewer_accepted_implementer_state_hash=getattr(
            update, "reviewer_accepted_implementer_state_hash", ""
        ),
        head_at_push_time=effective_head_at_push,
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
        ("Current Instruction For Implementer", current_instruction),
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

