"""Builder and artifact writers for the generated system-picture surface."""

from __future__ import annotations

import json
from pathlib import Path

from ..common import resolve_repo_path
from ..config import get_repo_root
from ..context_graph.snapshot_store import (
    format_context_graph_snapshot_path,
    list_context_graph_snapshots,
    load_context_graph_snapshot,
)
from ..governance.push_state import current_head_commit_sha
from ..repo_packs import active_path_config
from ..review_channel.heartbeat import compute_non_audit_worktree_hash
from ..runtime.control_plane_read_model import build_control_plane_read_model
from ..runtime.governance_scan import scan_repo_governance_safely
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
from .coordination_snapshot import build_coordination_snapshot
from .system_picture_models import (
    SYSTEM_PICTURE_CONTRACT_ID,
    SYSTEM_PICTURE_SCHEMA_VERSION,
    SystemPictureSnapshot,
)
from .system_picture_render import (
    render_system_picture_ledger_markdown,
    render_system_picture_markdown,
)
from .system_picture_sections import (
    _content_hash,
    build_graph_section,
    build_quality_signals_section,
    build_review_runtime_section,
    build_startup_section,
)
from .system_picture_sections_coordination import build_coordination_section
from .system_picture_sections_control_plane import build_control_plane_section
from .system_picture_sections_artifacts import (
    build_data_science_section,
    build_external_findings_section,
    build_governance_review_section,
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

    resolved_governance = scan_repo_governance_safely(resolved_root)
    review_state = load_current_review_state(
        resolved_root,
        governance=resolved_governance,
    )
    startup_context = build_startup_context(
        repo_root=resolved_root,
        governance=resolved_governance,
        review_state=review_state,
    )
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

    snapshot_paths = list_context_graph_snapshots(repo_root=resolved_root)
    review_state_path_val = resolve_review_state_path(resolved_root, governance=startup_context.governance)
    quality_signals = load_startup_quality_signals(resolved_root)
    control_plane = build_control_plane_read_model(
        resolved_root,
        governance=resolved_governance,
        review_state=review_state,
    )
    coordination_snapshot = build_coordination_snapshot(
        repo_root=resolved_root,
        startup_context=startup_context,
        review_state=review_state,
    )

    sections = [
        build_startup_section(
            repo_root=resolved_root,
            head_commit=head_commit,
            startup_context=startup_context,
            startup_authority=startup_authority,
            startup_receipt=startup_receipt,
            startup_receipt_file=startup_receipt_file,
        ),
        build_graph_section(
            repo_root=resolved_root,
            head_commit=head_commit,
            snapshot_paths=snapshot_paths,
            load_snapshot_fn=load_context_graph_snapshot,
            format_path_fn=format_context_graph_snapshot_path,
        ),
        build_review_runtime_section(
            repo_root=resolved_root,
            review_state=review_state,
            review_state_path=review_state_path_val,
        ),
        build_coordination_section(
            repo_root=resolved_root,
            snapshot=coordination_snapshot,
            review_state_path=review_state_path_val,
        ),
        build_control_plane_section(
            repo_root=resolved_root,
            control_plane=control_plane,
            review_state_path=review_state_path_val,
        ),
        build_quality_signals_section(
            signals=quality_signals,
        ),
        build_governance_review_section(
            repo_root=resolved_root,
        ),
        build_external_findings_section(
            repo_root=resolved_root,
        ),
        build_data_science_section(
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


def _resolve_repo_root(repo_root: Path | None) -> Path:
    return (repo_root or get_repo_root()).resolve()
