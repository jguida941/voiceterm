"""Session-resume preamble builder for reviewer conductor prompts.

When the provider is the reviewer (codex), the conductor prompt is
prepended with a structured JSON block from session-resume so the
reviewer starts from typed repo state instead of prose docs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from ..runtime.role_profile import normalize_tandem_role, role_for_provider

if TYPE_CHECKING:
    from ..commands.governance.session_resume_support import SessionCachePacket


def build_session_resume_preamble(
    *,
    provider: str,
    role: str | None = None,
    repo_root: Path,
    session_resume_packet: "SessionCachePacket | None" = None,
) -> str:
    """Build a session-resume JSON preamble for the reviewer (codex) prompt.

    When ``provider`` is codex (the reviewer), this returns a structured
    preamble containing the session-resume packet JSON so the reviewer
    starts from typed state instead of prose docs. Includes a diff-review
    hint when ``last_reviewed_sha`` differs from ``head_sha``.

    Returns empty string for non-reviewer providers or when no packet is
    available.
    """
    resolved_role = normalize_tandem_role(role) or role_for_provider(provider)
    if resolved_role != "reviewer":
        return ""
    packet = session_resume_packet or _try_build_session_resume(
        repo_root,
        role=resolved_role.value,
    )
    if packet is None:
        return ""
    return _format_session_resume_preamble(packet)


def _try_build_session_resume(
    repo_root: Path,
    *,
    role: str,
) -> "SessionCachePacket | None":
    """Attempt to build a SessionCachePacket from repo sources.

    Returns None when the import or build fails so the prompt degrades
    gracefully to the existing prose-based bootstrap.
    """
    try:
        from ..commands.governance.session_resume_support import (
            build_from_sources,
            current_head,
        )
        from ..commands.governance.session_resume_paths import resolve_governance
    except ImportError:
        return None
    try:
        head_sha = current_head(repo_root)
        if not head_sha:
            return None
        governance = resolve_governance(repo_root)
        return build_from_sources(
            repo_root,
            role=role,
            head_sha=head_sha,
            governance=governance,
        )
    except Exception:  # broad-except: allow reason=graceful degradation to prose-based bootstrap fallback=return None
        return None


def _format_session_resume_preamble(packet: "SessionCachePacket") -> str:
    """Render the session-resume JSON block plus diff-review hint."""
    lines = [
        "## Session Resume State (source of truth)",
        "",
        "IGNORE old bridge verdicts. Start from this session-resume state.",
        "",
        "```json",
        json.dumps(packet.to_dict(), indent=2),
        "```",
    ]
    candidate = packet.review_candidate
    head = packet.head_sha.strip()
    last_reviewed = packet.last_reviewed_sha.strip()
    if candidate is not None and candidate.valid and candidate.ready_for_review:
        lines.extend([
            "",
            f"Frozen review candidate: `{candidate.candidate_id}` ({candidate.artifact_kind})",
        ])
        if candidate.changed_paths:
            lines.append(
                "Review these candidate paths first: "
                + ", ".join(f"`{path}`" for path in candidate.changed_paths[:8])
            )
        if candidate.artifact_kind == "dirty_tree":
            lines.append(
                "This slice currently lives in dirty-tree state; prefer the candidate "
                "path set and worktree hash over raw commit-range review."
            )
        if candidate.invalidation_reason:
            lines.append(
                f"Candidate warning: `{candidate.invalidation_reason}`"
            )
    elif head and last_reviewed and head != last_reviewed:
        lines.extend([
            "",
            f"Unreviewed changes detected: `{last_reviewed[:12]}..{head[:12]}`",
            f"Review the diff with: `git diff {last_reviewed}..{head}`",
        ])
    elif head and not last_reviewed:
        lines.extend([
            "",
            "No previous review SHA recorded. Review all pending changes.",
        ])
    return "\n".join(lines)
