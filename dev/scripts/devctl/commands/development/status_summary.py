"""Top-level status and summary policy for ``devctl develop`` reports."""

from __future__ import annotations


def status_for_report(
    *,
    blockers: tuple[str, ...],
    continuation,
) -> str:
    if blockers:
        return "blocked"
    if getattr(continuation, "continuation_required", False):
        return "continue_required"
    return "ready"


def summary_for_action(
    action: str,
    *,
    blockers: tuple[str, ...],
    lifecycle_actions: set[str] | frozenset[str],
    continuation=None,
    drain_packets: bool = False,
    dry_run: bool = False,
) -> str:
    if blockers:
        return "Develop controller request failed closed before execution."
    if getattr(continuation, "continuation_required", False):
        return getattr(continuation, "summary", "") or (
            "Continuation required before /develop may stop."
        )
    if action == "audit-packets":
        return _audit_packets_summary(
            drain_packets=drain_packets,
            dry_run=dry_run,
        )
    fixed_summary = _ACTION_SUMMARIES.get(action)
    if fixed_summary:
        return fixed_summary
    if action in lifecycle_actions:
        return f"Rendered read-only /develop {action} lifecycle guidance."
    if action in {"pause", "resume"}:
        return f"Rendered a read-only {action} request without mutating controller state."
    return "Rendered typed develop controller status."


_ACTION_SUMMARIES = {
    "next": "Selected the next bounded typed development slice.",
    "audit-guards": "Rendered guard/probe learning inputs for development mode.",
    "launch": "Rendered one read-only develop controller cycle without mutation.",
}


def _audit_packets_summary(
    *,
    drain_packets: bool,
    dry_run: bool,
) -> str:
    if not drain_packets:
        return "Rendered packet carry-forward durable-ingestion debt."
    if dry_run:
        return "Previewed eligible packet carry-forward durable-ingestion debt."
    return "Applied eligible packet carry-forward durable-ingestion debt."


__all__ = ["status_for_report", "summary_for_action"]
