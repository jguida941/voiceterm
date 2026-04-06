"""Section builders for the system-picture snapshot reducer.

Each builder produces a single SystemPictureSection from pre-fetched data.
External dependencies are passed in as arguments so the callers in
system_picture.py control import resolution and test patching.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..common_io import display_path
from .system_picture_models import SystemPictureSection

_STARTUP_CONTEXT_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --format summary"
)
_CONTEXT_GRAPH_COMMAND = (
    "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"
)
_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json"
)


def build_startup_section(
    *,
    repo_root: Path,
    head_commit: str,
    startup_context: Any,
    startup_authority: dict[str, object],
    startup_receipt: Any,
    startup_receipt_file: Path,
) -> SystemPictureSection:
    """Build the startup-authority section from pre-fetched startup data."""
    governance = getattr(startup_context, "governance", None)
    push = getattr(governance, "push_enforcement", None)
    reviewer_gate = getattr(startup_context, "reviewer_gate", None)
    receipt_fresh = bool(
        startup_receipt is not None
        and str(getattr(startup_receipt, "head_commit_sha", "") or "").strip()
        == str(head_commit or "").strip()
    )
    notes: list[str] = []
    if startup_receipt is None:
        notes.append(
            "No managed startup receipt is present yet; rerun "
            f"`{_STARTUP_CONTEXT_COMMAND}` to persist one."
        )
    elif not receipt_fresh:
        notes.append(
            "Managed startup receipt is older than the current startup identity; "
            f"rerun `{_STARTUP_CONTEXT_COMMAND}` to refresh it."
        )
    status = "current"
    if startup_receipt is None:
        status = "missing"
    elif not receipt_fresh:
        status = "stale"
    summary = {
        "advisory_action": getattr(startup_context, "advisory_action", ""),
        "advisory_reason": getattr(startup_context, "advisory_reason", ""),
        "implementation_blocked": bool(
            getattr(reviewer_gate, "implementation_blocked", False)
        ),
        "implementation_block_reason": str(
            getattr(reviewer_gate, "implementation_block_reason", "") or ""
        ).strip(),
        "review_gate_allows_push": bool(
            getattr(reviewer_gate, "review_gate_allows_push", False)
        ),
        "push_action": str(getattr(startup_context.push_decision, "action", "") or "").strip(),
        "push_reason": str(getattr(startup_context.push_decision, "reason", "") or "").strip(),
        "push_eligible_now": bool(
            getattr(startup_context.push_decision, "push_eligible_now", False)
        ),
        "ahead_of_upstream_commits": int(
            getattr(push, "ahead_of_upstream_commits", 0) or 0
        ),
        "checkpoint_required": bool(getattr(push, "checkpoint_required", False)),
        "safe_to_continue_editing": bool(
            getattr(push, "safe_to_continue_editing", True)
        ),
        "publication_backlog_state": str(
            getattr(getattr(startup_context.push_decision, "publication_backlog", None), "backlog_state", "")
            or ""
        ).strip(),
        "publication_guidance": str(
            getattr(startup_context.push_decision, "publication_guidance", "") or ""
        ).strip(),
        "startup_authority_ok": bool(startup_authority.get("ok", False)),
        "startup_authority_error_count": len(startup_authority.get("errors", ()) or ()),
        "startup_authority_warning_count": len(
            startup_authority.get("warnings", ()) or ()
        ),
        "startup_receipt_present": startup_receipt is not None,
        "startup_receipt_fresh": receipt_fresh,
    }
    return _build_section(
        section_id="startup",
        title="Startup Authority",
        status=status,
        summary=summary,
        source_path=display_path(startup_receipt_file, repo_root=repo_root),
        source_command=_STARTUP_CONTEXT_COMMAND,
        generated_at_utc=(
            str(getattr(startup_receipt, "generated_at_utc", "") or "").strip()
            if startup_receipt is not None
            else ""
        ),
        notes=tuple(notes),
    )


def build_graph_section(
    *,
    repo_root: Path,
    head_commit: str,
    snapshot_paths: list[Path] | tuple[Path, ...],
    load_snapshot_fn: Any,
    format_path_fn: Any,
) -> SystemPictureSection:
    """Build the context-graph section from pre-fetched snapshot paths.

    Receives the snapshot-path list and loader/formatter callables so import
    resolution stays with the caller.
    """
    if not snapshot_paths:
        return _build_section(
            section_id="graph",
            title="Context Graph",
            status="missing",
            summary={},
            source_path="",
            source_command=_CONTEXT_GRAPH_COMMAND,
            generated_at_utc="",
            notes=(
                "No saved ContextGraphSnapshot artifact is present; run "
                f"`{_CONTEXT_GRAPH_COMMAND}` to refresh the bounded graph view.",
            ),
        )
    latest_path = snapshot_paths[-1]
    snapshot = load_snapshot_fn(latest_path)
    status = (
        "current"
        if not head_commit or snapshot.commit_hash == head_commit
        else "stale"
    )
    notes: tuple[str, ...] = ()
    if status == "stale":
        notes = (
            "Latest saved ContextGraphSnapshot was captured on an older commit; "
            f"rerun `{_CONTEXT_GRAPH_COMMAND}` to refresh it.",
        )
    summary = {
        "branch": snapshot.branch,
        "commit_hash": snapshot.commit_hash,
        "node_count": snapshot.node_count,
        "edge_count": snapshot.edge_count,
        "guard_count": int(snapshot.nodes_by_kind.get("guard", 0)),
        "probe_count": int(snapshot.nodes_by_kind.get("probe", 0)),
        "plan_count": int(snapshot.nodes_by_kind.get("plan", 0)),
        "temperature_average": snapshot.temperature_distribution.average,
    }
    return _build_section(
        section_id="graph",
        title="Context Graph",
        status=status,
        summary=summary,
        source_path=format_path_fn(latest_path),
        source_command=_CONTEXT_GRAPH_COMMAND,
        generated_at_utc=snapshot.generated_at_utc,
        notes=notes,
    )


def build_review_runtime_section(
    *,
    repo_root: Path,
    review_state: Any,
    review_state_path: Path | None,
) -> SystemPictureSection:
    """Build the review-runtime section from a pre-loaded review state."""
    if review_state is None or review_state_path is None:
        return _build_section(
            section_id="review_runtime",
            title="Review Runtime",
            status="missing",
            summary={},
            source_path="",
            source_command=_REVIEW_STATUS_COMMAND,
            generated_at_utc="",
            notes=(
                "No typed ReviewState artifact is available yet; run "
                f"`{_REVIEW_STATUS_COMMAND}` to refresh the governed review-state projection.",
            ),
        )
    attention = review_state.attention
    reviewer_runtime = review_state.reviewer_runtime
    summary = {
        "attention_status": attention.status if attention is not None else "",
        "attention_owner": attention.owner if attention is not None else "",
        "reviewer_mode": review_state.bridge.reviewer_mode,
        "effective_reviewer_mode": review_state.bridge.effective_reviewer_mode,
        "reviewer_freshness": review_state.bridge.reviewer_freshness,
        "review_needed": review_state.bridge.review_needed,
        "review_accepted": review_state.bridge.review_accepted,
        "current_instruction_revision": review_state.current_session.current_instruction_revision,
        "implementer_ack_state": review_state.current_session.implementer_ack_state,
        "publish_clear": getattr(reviewer_runtime, "publish_clear", False),
        "commit_pipeline_state": getattr(review_state.commit_pipeline, "state", ""),
        "push_action": review_state.commit_pipeline.blocked_reason
        if getattr(review_state.commit_pipeline, "state", "") == "push_blocked"
        else getattr(review_state.commit_pipeline, "state", ""),
    }
    return _build_section(
        section_id="review_runtime",
        title="Review Runtime",
        status="current",
        summary=summary,
        source_path=display_path(review_state_path, repo_root=repo_root),
        source_command=_REVIEW_STATUS_COMMAND,
        generated_at_utc=review_state.timestamp,
        notes=tuple(
            row for row in (review_state.warnings + review_state.errors)[:2] if row
        ),
    )


def build_quality_signals_section(
    *,
    signals: dict[str, object],
) -> SystemPictureSection:
    """Build the quality-signals section from pre-loaded signal data."""
    status = "current" if signals else "missing"
    notes: tuple[str, ...] = ()
    if not signals:
        notes = (
            "Quality signals are empty because the bounded latest artifacts are missing; "
            "refresh probe-report, governance-review, and data-science to fill this section.",
        )
    return _build_section(
        section_id="quality_signals",
        title="Quality Signals",
        status=status,
        summary=signals,
        source_path="",
        source_command="python3 dev/scripts/devctl.py probe-report --format md",
        generated_at_utc="",
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Shared helpers used by all section builders
# ---------------------------------------------------------------------------


def _build_section(
    *,
    section_id: str,
    title: str,
    status: str,
    summary: dict[str, object],
    source_path: str,
    source_command: str,
    generated_at_utc: str,
    notes: tuple[str, ...],
) -> SystemPictureSection:
    section_hash = _content_hash(
        {
            "section_id": section_id,
            "status": status,
            "summary": summary,
            "source_path": source_path,
            "source_command": source_command,
            "generated_at_utc": generated_at_utc,
            "notes": list(notes),
        }
    )
    return SystemPictureSection(
        section_id=section_id,
        title=title,
        status=status,
        summary=summary,
        source_path=source_path,
        source_command=source_command,
        generated_at_utc=generated_at_utc,
        section_hash=section_hash,
        notes=notes,
    )


def _content_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
