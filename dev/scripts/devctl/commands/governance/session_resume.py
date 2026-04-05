"""devctl session-resume command: fast cached session bootstrap (~500 tokens)."""

from __future__ import annotations

from ...common import add_standard_output_arguments
from ...config import get_repo_root
from .common import emit_governance_command_output
from .session_resume_paths import get_review_state_mtime, resolve_governance
from .session_resume_support import (
    SessionCachePacket,
    build_from_sources,
    current_head,
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
    add_standard_output_arguments(cmd, format_choices=("json", "md", "summary"))


def run(args) -> int:
    """Emit cached session state or rebuild from source artifacts."""
    repo_root = get_repo_root()
    role = getattr(args, "role", "implementer") or "implementer"
    head_sha = current_head(repo_root)
    governance = resolve_governance(repo_root)
    rs_mtime = get_review_state_mtime(repo_root, governance=governance)

    cached = try_cache_hit(
        repo_root,
        head_sha=head_sha,
        role=role,
        review_state_mtime=rs_mtime,
    )
    if cached is not None:
        return _emit_packet(args, cached)

    packet = build_from_sources(repo_root, role=role, head_sha=head_sha)
    write_cache(repo_root, packet)
    return _emit_packet(args, packet)


def _emit_packet(args, packet: SessionCachePacket) -> int:
    fmt = getattr(args, "format", "md")
    if fmt == "summary":
        human = render_summary(packet)
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
