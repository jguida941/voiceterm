"""Session-resume preamble builder for conductor prompts.

Conductor prompts prepend a structured JSON block from session-resume so
reviewer and implementer sessions both start from typed repo state
instead of stale bridge prose.
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
    """Build a session-resume JSON preamble for reviewer or implementer prompts."""
    resolved_role = (normalize_tandem_role(role) or role_for_provider(provider)).value
    packet = session_resume_packet or _try_build_session_resume(
        repo_root,
        role=resolved_role,
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
    """Render the session-resume JSON block plus role-aware coordination hints."""
    role = str(packet.role or "").strip().lower()
    lines = [
        "## Session Resume State (source of truth)",
        "",
        "IGNORE stale bridge prose. Start from this session-resume state.",
        "",
        "```json",
        json.dumps(packet.to_dict(), indent=2),
        "```",
    ]
    coordination = packet.coordination
    if coordination is not None:
        lines.extend([
            "",
            (
                "Coordination: "
                f"`{coordination.declared_topology}` / "
                f"`{coordination.observed_topology}` -> "
                f"`{coordination.recommended_topology}`"
            ),
            (
                "Fanout posture: "
                f"`{coordination.fanout_posture}` | "
                f"safe_to_fanout={coordination.safe_to_fanout}"
            ),
            (
                "Resync required: "
                f"{coordination.resync_required}"
                + (
                    " (" + ", ".join(coordination.resync_reasons) + ")"
                    if coordination.resync_reasons
                    else ""
                )
            ),
        ])
        if coordination.current_slice:
            lines.append(f"Current governed slice: `{coordination.current_slice}`")
    candidate = packet.review_candidate
    head = packet.head_sha.strip()
    last_reviewed = packet.last_reviewed_sha.strip()
    if role == "reviewer" and candidate is not None and candidate.valid and candidate.ready_for_review:
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
    elif role == "reviewer" and head and last_reviewed and head != last_reviewed:
        lines.extend([
            "",
            f"Unreviewed changes detected: `{last_reviewed[:12]}..{head[:12]}`",
            f"Review the diff with: `git diff {last_reviewed}..{head}`",
        ])
    elif role == "reviewer" and head and not last_reviewed:
        lines.extend([
            "",
            "No previous review SHA recorded. Review all pending changes.",
        ])
    return "\n".join(lines)
