"""Builder and artifact writers for the generated system-picture surface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..common import resolve_repo_path
from ..common_io import display_path
from ..config import get_repo_root
from ..context_graph.snapshot_store import (
    format_context_graph_snapshot_path,
    list_context_graph_snapshots,
    load_context_graph_snapshot,
)
from ..governance.push_state import current_head_commit_sha
from ..repo_packs import active_path_config
from ..review_channel.heartbeat import compute_non_audit_worktree_hash
from ..runtime.review_state_locator import (
    load_current_review_state,
    resolve_review_state_path,
)
from ..runtime.startup_authority import build_startup_authority_report
from ..runtime.startup_context import build_startup_context
from ..runtime.startup_receipt import (
    load_startup_receipt,
    startup_receipt_path,
)
from ..runtime.startup_signals import load_startup_quality_signals
from ..time_utils import utc_timestamp
from .system_picture_models import (
    SYSTEM_PICTURE_CONTRACT_ID,
    SYSTEM_PICTURE_SCHEMA_VERSION,
    SystemPictureSection,
    SystemPictureSnapshot,
)
from .system_picture_render import (
    render_system_picture_ledger_markdown,
    render_system_picture_markdown,
)

_STARTUP_CONTEXT_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --format summary"
)
_CONTEXT_GRAPH_COMMAND = (
    "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"
)
_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json"
)
_SYSTEM_PICTURE_HISTORY_NAME = "snapshots.jsonl"
_SYSTEM_PICTURE_LEDGER_NAME = "proof_ledger.md"


def resolve_system_picture_output_root(
    raw_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the managed system-picture output root."""
    resolved_root = _resolve_repo_root(repo_root)
    output_root = resolve_repo_path(
        raw_path,
        default=Path(active_path_config().system_picture_output_root_rel),
        repo_root=resolved_root,
    )
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def resolve_system_picture_ledger_path(
    raw_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the tracked markdown proof-ledger projection path."""
    resolved_root = _resolve_repo_root(repo_root)
    return resolve_repo_path(
        raw_path,
        default=Path(active_path_config().system_picture_ledger_rel),
        repo_root=resolved_root,
    )


def build_system_picture_snapshot(
    *,
    repo_root: Path | None = None,
) -> SystemPictureSnapshot:
    """Build the bounded startup/runtime/evidence reducer snapshot."""
    resolved_root = _resolve_repo_root(repo_root)
    generated_at = utc_timestamp()

    startup_context = build_startup_context(repo_root=resolved_root)
    startup_authority = build_startup_authority_report(repo_root=resolved_root)
    startup_receipt = load_startup_receipt(
        governance=startup_context.governance,
        repo_root=resolved_root,
    )
    startup_receipt_file = startup_receipt_path(
        governance=startup_context.governance,
        repo_root=resolved_root,
    )

    current_branch = (
        getattr(getattr(startup_context.governance, "repo_identity", None), "current_branch", "")
        or getattr(startup_receipt, "current_branch", "")
        or ""
    )
    head_commit = (
        current_head_commit_sha(repo_root=resolved_root)
        or getattr(startup_receipt, "head_commit_sha", "")
        or ""
    )
    tree_hash = compute_non_audit_worktree_hash(
        repo_root=resolved_root,
        excluded_rel_paths=(),
    )

    sections = [
        _build_startup_section(
            repo_root=resolved_root,
            head_commit=head_commit,
            startup_context=startup_context,
            startup_authority=startup_authority,
            startup_receipt=startup_receipt,
            startup_receipt_file=startup_receipt_file,
        ),
        _build_graph_section(
            repo_root=resolved_root,
            head_commit=head_commit,
        ),
        _build_review_runtime_section(
            repo_root=resolved_root,
            governance=startup_context.governance,
        ),
        _build_quality_signals_section(
            repo_root=resolved_root,
        ),
        _build_governance_review_section(
            repo_root=resolved_root,
        ),
        _build_external_findings_section(
            repo_root=resolved_root,
        ),
        _build_data_science_section(
            repo_root=resolved_root,
        ),
    ]

    section_hashes = {section.section_id: section.section_hash for section in sections}
    snapshot_id = _content_hash(
        {
            "repo_name": resolved_root.name,
            "current_branch": current_branch,
            "head_commit_sha": head_commit,
            "tree_hash": tree_hash,
            "section_hashes": section_hashes,
        }
    )[:16]
    current_count = sum(1 for section in sections if section.status == "current")
    stale_count = sum(1 for section in sections if section.status == "stale")
    missing_count = sum(1 for section in sections if section.status == "missing")
    return SystemPictureSnapshot(
        schema_version=SYSTEM_PICTURE_SCHEMA_VERSION,
        contract_id=SYSTEM_PICTURE_CONTRACT_ID,
        snapshot_id=f"sys-{snapshot_id}",
        generated_at_utc=generated_at,
        repo_name=resolved_root.name,
        repo_root=str(resolved_root),
        current_branch=current_branch,
        head_commit_sha=head_commit,
        tree_hash=tree_hash,
        section_hashes=section_hashes,
        current_section_count=current_count,
        stale_section_count=stale_count,
        missing_section_count=missing_count,
        sections=tuple(sections),
    )


def write_system_picture_artifacts(
    snapshot: SystemPictureSnapshot,
    *,
    output_root: Path,
) -> dict[str, str]:
    """Write managed latest/history artifacts for one system-picture snapshot."""
    latest_dir = output_root / "latest"
    history_dir = output_root / "history"
    latest_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    summary_json = latest_dir / "summary.json"
    summary_md = latest_dir / "summary.md"
    ledger_preview_md = latest_dir / _SYSTEM_PICTURE_LEDGER_NAME
    history_jsonl = history_dir / _SYSTEM_PICTURE_HISTORY_NAME

    payload = snapshot.to_dict()
    summary_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    summary_md.write_text(
        render_system_picture_markdown(snapshot),
        encoding="utf-8",
    )
    ledger_preview_md.write_text(
        render_system_picture_ledger_markdown(snapshot),
        encoding="utf-8",
    )
    with history_jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")

    return {
        "summary_json": str(summary_json),
        "summary_md": str(summary_md),
        "ledger_preview_md": str(ledger_preview_md),
        "history_jsonl": str(history_jsonl),
    }


def write_system_picture_ledger(
    snapshot: SystemPictureSnapshot,
    *,
    ledger_path: Path,
) -> str:
    """Write the tracked markdown proof-ledger projection."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        render_system_picture_ledger_markdown(snapshot),
        encoding="utf-8",
    )
    return str(ledger_path)


def _build_startup_section(
    *,
    repo_root: Path,
    head_commit: str,
    startup_context,
    startup_authority: dict[str, object],
    startup_receipt,
    startup_receipt_file: Path,
) -> SystemPictureSection:
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


def _build_graph_section(
    *,
    repo_root: Path,
    head_commit: str,
) -> SystemPictureSection:
    snapshot_paths = list_context_graph_snapshots(repo_root=repo_root)
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
    snapshot = load_context_graph_snapshot(latest_path)
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
        source_path=format_context_graph_snapshot_path(latest_path),
        source_command=_CONTEXT_GRAPH_COMMAND,
        generated_at_utc=snapshot.generated_at_utc,
        notes=notes,
    )


def _build_review_runtime_section(
    *,
    repo_root: Path,
    governance,
) -> SystemPictureSection:
    review_state = load_current_review_state(repo_root, governance=governance)
    review_state_path = resolve_review_state_path(repo_root, governance=governance)
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


def _build_quality_signals_section(
    *,
    repo_root: Path,
) -> SystemPictureSection:
    signals = load_startup_quality_signals(repo_root)
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


def _build_governance_review_section(
    *,
    repo_root: Path,
) -> SystemPictureSection:
    path = repo_root / active_path_config().governance_review_summary_root_rel / "review_summary.json"
    payload = _load_json(path)
    if not payload:
        return _build_section(
            section_id="governance_review",
            title="Governance Review",
            status="missing",
            summary={},
            source_path=display_path(path, repo_root=repo_root),
            source_command="python3 dev/scripts/devctl.py governance-review --format md",
            generated_at_utc="",
            notes=("No latest governance-review summary artifact is present.",),
        )
    stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
    summary = {
        "total_findings": stats.get("total_findings"),
        "open_finding_count": stats.get("open_finding_count"),
        "fixed_count": stats.get("fixed_count"),
        "cleanup_rate_pct": stats.get("cleanup_rate_pct"),
        "false_positive_rate_pct": stats.get("false_positive_rate_pct"),
    }
    return _build_section(
        section_id="governance_review",
        title="Governance Review",
        status="current",
        summary=summary,
        source_path=display_path(path, repo_root=repo_root),
        source_command="python3 dev/scripts/devctl.py governance-review --format md",
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        notes=(),
    )


def _build_external_findings_section(
    *,
    repo_root: Path,
) -> SystemPictureSection:
    path = (
        repo_root
        / active_path_config().external_finding_summary_root_rel
        / "external_findings_summary.json"
    )
    payload = _load_json(path)
    if not payload:
        return _build_section(
            section_id="external_findings",
            title="External Findings",
            status="missing",
            summary={},
            source_path=display_path(path, repo_root=repo_root),
            source_command="python3 dev/scripts/devctl.py governance-import-findings --format md",
            generated_at_utc="",
            notes=("No latest external-findings summary artifact is present.",),
        )
    stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
    summary = {
        "total_findings": stats.get("total_findings"),
        "unique_repo_count": stats.get("unique_repo_count"),
        "reviewed_count": stats.get("reviewed_count"),
        "adjudication_coverage_pct": stats.get("adjudication_coverage_pct"),
        "fixed_count": stats.get("fixed_count"),
        "confirmed_issue_count": stats.get("confirmed_issue_count"),
    }
    return _build_section(
        section_id="external_findings",
        title="External Findings",
        status="current",
        summary=summary,
        source_path=display_path(path, repo_root=repo_root),
        source_command="python3 dev/scripts/devctl.py governance-import-findings --format md",
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        notes=(),
    )


def _build_data_science_section(
    *,
    repo_root: Path,
) -> SystemPictureSection:
    path = repo_root / active_path_config().data_science_output_root_rel / "latest" / "summary.json"
    payload = _load_json(path)
    if not payload:
        return _build_section(
            section_id="data_science",
            title="Data Science",
            status="missing",
            summary={},
            source_path=display_path(path, repo_root=repo_root),
            source_command="python3 dev/scripts/devctl.py data-science --format md",
            generated_at_utc="",
            notes=("No latest data-science summary artifact is present.",),
        )
    event_stats = payload.get("event_stats") if isinstance(payload.get("event_stats"), dict) else {}
    watchdog = payload.get("watchdog_stats") if isinstance(payload.get("watchdog_stats"), dict) else {}
    external = payload.get("external_finding_stats") if isinstance(payload.get("external_finding_stats"), dict) else {}
    summary = {
        "total_events": event_stats.get("total_events"),
        "command_success_rate_pct": event_stats.get("success_rate_pct"),
        "command_p95_duration_seconds": event_stats.get("p95_duration_seconds"),
        "watchdog_total_episodes": watchdog.get("total_episodes"),
        "watchdog_success_rate_pct": watchdog.get("success_rate_pct"),
        "external_unique_repo_count": external.get("unique_repo_count"),
    }
    return _build_section(
        section_id="data_science",
        title="Data Science",
        status="current",
        summary=summary,
        source_path=display_path(path, repo_root=repo_root),
        source_command="python3 dev/scripts/devctl.py data-science --format md",
        generated_at_utc=str(payload.get("generated_at") or "").strip(),
        notes=(),
    )


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


def _load_json(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _resolve_repo_root(repo_root: Path | None) -> Path:
    return (repo_root or get_repo_root()).resolve()


def _content_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
