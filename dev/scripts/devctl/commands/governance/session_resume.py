"""devctl session-resume command: fast cached session bootstrap (~500 tokens)."""

from __future__ import annotations

from ...common import add_standard_output_arguments
from ...config import get_repo_root
from ...runtime.review_state_locator import load_current_review_state
from ...runtime.work_intake_continuity import build_continuity
from ...runtime.work_intake_models import SessionContinuityState
from ...runtime.work_intake_selection import (
    load_review_state,
    select_active_plan_entry,
)
from .common import emit_governance_command_output
from .session_resume_paths import get_review_state_mtime, resolve_governance
from .session_resume_support import (
    SessionCachePacket,
    build_from_sources,
    current_head,
    render_bootstrap,
    render_markdown,
    render_summary,
    try_cache_hit,
    write_cache,
)


def add_parser(subparsers) -> None:
    """Register the session-resume CLI parser."""
    cmd = subparsers.add_parser(
        "session-resume",
        help="Emit a compact cached session-state packet (~500 tokens)",
    )
    cmd.add_argument(
        "--role",
        choices=("implementer", "reviewer"),
        default="implementer",
        help="Declare caller role (default: implementer).",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md", "summary", "bootstrap"),
    )


def run(args) -> int:
    """Emit cached session state or rebuild from source artifacts."""
    repo_root = get_repo_root()
    role = getattr(args, "role", "implementer") or "implementer"
    head_sha = current_head(repo_root)
    governance = resolve_governance(repo_root)
    rs_mtime = get_review_state_mtime(repo_root, governance=governance)
    continuity = _resolve_continuity(repo_root, governance)

    cached = try_cache_hit(
        repo_root,
        head_sha=head_sha,
        role=role,
        review_state_mtime=rs_mtime,
        continuity=continuity,
    )
    if cached is not None:
        return _emit_packet(args, cached)

    review_state = load_current_review_state(
        repo_root,
        governance=governance,
        prefer_cached_projection=False,
    )
    packet = build_from_sources(
        repo_root,
        role=role,
        head_sha=head_sha,
        governance=governance,
        review_state=review_state,
    )
    write_cache(repo_root, packet)
    return _emit_packet(args, packet)


def _resolve_continuity(repo_root, governance) -> SessionContinuityState | None:
    """Build a typed continuity state for the cache-freshness gate.

    Returns ``None`` when governance cannot be resolved so the cache gate
    falls back to the head/role/mtime-only path rather than crashing the
    CLI on empty or partially-initialized repos.
    """
    if governance is None:
        return None
    try:
        review_state = load_review_state(repo_root, governance=governance)
        active_entry = select_active_plan_entry(governance, review_state)
        return build_continuity(active_entry, review_state)
    except Exception:  # broad-except: allow reason=best-effort continuity signal fallback=cache without gate
        return None


def _emit_packet(args, packet: SessionCachePacket) -> int:
    fmt = getattr(args, "format", "md")
    if fmt == "summary":
        human = render_summary(packet)
    elif fmt == "bootstrap":
        human = render_bootstrap(packet)
    elif fmt == "md":
        human = render_markdown(packet)
    else:
        human = ""
    return emit_governance_command_output(
        args,
        command="session-resume",
        json_payload=packet.to_dict(),
        markdown_output=human,
        ok=(packet.blockers == "none"),
        exit_zero_on_non_ok=(fmt == "json"),
        summary={
            "role": packet.role,
            "blockers": packet.blockers,
            "head_sha": packet.head_sha,
            "interaction_mode": packet.interaction_mode,
            "last_guard_ok": packet.last_guard_ok,
        },
    )


__all__ = [
    "SessionCachePacket",
    "add_parser",
    "run",
]
