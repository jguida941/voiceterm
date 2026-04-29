"""devctl session-resume command: fast cached session bootstrap (~500 tokens)."""

from __future__ import annotations

from pathlib import Path

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
        choices=("dashboard", "implementer", "observer", "reviewer"),
        default="implementer",
        help="Declare caller role; dashboard normalizes to the observer lane.",
    )
    cmd.add_argument(
        "--provider",
        default="",
        help="Provider/agent id proving a typed rehydration receipt.",
    )
    cmd.add_argument(
        "--session-id-or-transcript-path",
        default="",
        help="Optional provider session id, transcript path, or metadata path.",
    )
    cmd.add_argument(
        "--write-resume-receipt",
        action="store_true",
        help="Append an AgentResumeReceipt proving this session loaded typed state.",
    )
    cmd.add_argument(
        "--resume-result",
        choices=("loaded", "blocked", "failed"),
        default="loaded",
        help="State-load result recorded when --write-resume-receipt is used.",
    )
    cmd.add_argument(
        "--authority-result",
        choices=("allowed", "blocked"),
        default="",
        help=(
            "Optional authority result for the resumed session. Defaults to "
            "blocked when session blockers remain."
        ),
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md", "summary", "bootstrap"),
    )


def run(args) -> int:
    """Emit cached session state or rebuild from source artifacts."""
    repo_root = get_repo_root()
    role = _normalize_role(getattr(args, "role", "implementer"))
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
        prefer_cached_projection=True,
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
    payload = packet.to_dict()
    receipt_error = ""
    if getattr(args, "write_resume_receipt", False):
        try:
            receipt, event = _write_resume_receipt(args, packet)
            payload["agent_resume_receipt"] = receipt.to_dict()
            payload["agent_resume_receipt_event"] = event
            if human:
                human = f"{human}\n\n{_render_resume_receipt(receipt, event)}"
        except (OSError, ValueError) as exc:
            receipt_error = str(exc)
            payload["agent_resume_receipt_error"] = receipt_error
            if human:
                human = f"{human}\n\nresume_receipt_error={receipt_error}"
    return emit_governance_command_output(
        args,
        command="session-resume",
        json_payload=payload,
        markdown_output=human,
        ok=(packet.blockers == "none" and not receipt_error),
        exit_zero_on_non_ok=(fmt == "json" and not receipt_error),
        summary=_session_resume_summary(packet),
    )


def _write_resume_receipt(args, packet: SessionCachePacket):
    continuation = packet.agent_session_continuation
    if continuation is None:
        raise ValueError("SessionCachePacket lacks AgentSessionContinuation.")
    from ...review_channel.agent_session_continuation_events import (
        append_agent_resume_receipt_event,
    )
    from ...review_channel.events import resolve_artifact_paths
    from ...runtime.agent_session_continuation import build_agent_resume_receipt
    from ...time_utils import utc_timestamp

    observed_at = utc_timestamp()
    receipt = build_agent_resume_receipt(
        continuation,
        provider=getattr(args, "provider", "") or continuation.provider,
        agent_id=getattr(args, "provider", "") or continuation.agent_id,
        session_id_or_transcript_path=(
            getattr(args, "session_id_or_transcript_path", "")
            or continuation.session_id_or_transcript_path
        ),
        started_at_utc=continuation.generated_at_utc,
        observed_at_utc=observed_at,
        result=getattr(args, "resume_result", "loaded"),
        authority_result=(
            getattr(args, "authority_result", "")
            or _authority_result_for_packet(packet)
        ),
    )
    repo_root = get_repo_root()
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    event = append_agent_resume_receipt_event(
        events_path=Path(artifact_paths.event_log_path),
        receipt=receipt,
    )
    return receipt, event


def _render_resume_receipt(receipt, event: dict[str, object]) -> str:
    return "\n".join(
        [
            "### Agent Resume Receipt",
            f"- **event_id**: `{event.get('event_id', '')}`",
            f"- **receipt_id**: `{receipt.receipt_id}`",
            f"- **load_result**: `{receipt.load_result}`",
            f"- **authority_result**: `{receipt.authority_result}`",
            f"- **continuation_id**: `{receipt.continuation_id}`",
            f"- **continuation_hash**: `{receipt.continuation_hash[:16]}`",
        ]
    )


def _authority_result_for_packet(packet: SessionCachePacket) -> str:
    continuation = packet.agent_session_continuation
    if continuation is not None and continuation.authority_result:
        return continuation.authority_result
    return "allowed" if packet.blockers == "none" else "blocked"


def _session_resume_summary(packet: SessionCachePacket) -> dict[str, object]:
    continuation_id = ""
    if packet.agent_session_continuation is not None:
        continuation_id = packet.agent_session_continuation.continuation_id
    return dict(
        (
            ("role", packet.role),
            ("blockers", packet.blockers),
            ("head_sha", packet.head_sha),
            ("interaction_mode", packet.interaction_mode),
            ("last_guard_ok", packet.last_guard_ok),
            ("continuation_id", continuation_id),
        )
    )


def _normalize_role(role: object) -> str:
    normalized = str(role or "implementer").strip().lower()
    if normalized == "dashboard":
        return "observer"
    if normalized in {"implementer", "observer", "reviewer"}:
        return normalized
    return "implementer"


__all__ = [
    "SessionCachePacket",
    "add_parser",
    "run",
]
