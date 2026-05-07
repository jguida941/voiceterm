"""Reviewer-follow helpers for typed reviewer-runtime projections."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .current_session_projection import build_bridge_current_session
from .handoff import extract_bridge_snapshot
from .remote_commit_pipeline_artifact import load_remote_commit_pipeline_contract
from .reviewer_runtime_contract import (
    ReviewerRuntimeInputs,
    build_reviewer_doctor_surface,
    build_reviewer_runtime_contract,
    reviewer_runtime_contract_to_dict,
)


def attach_reviewer_runtime_contract(
    *,
    report: dict[str, object],
    bridge_path: Path,
    status_dir: object,
) -> None:
    """Attach the typed reviewer-runtime contract to one follow-loop report."""
    bridge_liveness = report.get("bridge_liveness")
    if not isinstance(bridge_liveness, dict):
        return
    bridge_text = bridge_path.read_text(encoding="utf-8")
    snapshot = extract_bridge_snapshot(bridge_text)
    current_session = build_bridge_current_session(snapshot, bridge_liveness)
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=snapshot,
            bridge_liveness=bridge_liveness,
            current_session=current_session,
            attention=(
                report.get("attention")
                if isinstance(report.get("attention"), dict)
                else None
            ),
            session_output_root=status_dir if isinstance(status_dir, Path) else None,
            rollover_dir=(
                status_dir.parent / "rollovers"
                if isinstance(status_dir, Path) and status_dir.parent is not None
                else None
            ),
            bridge_text=bridge_text,
            repo_root=bridge_path.parent,
            rollover_state_override=(
                report.get("auto_rollover")
                if isinstance(report.get("auto_rollover"), dict)
                else None
            ),
        )
    )
    attention = report.get("attention") if isinstance(report.get("attention"), dict) else None
    commit_pipeline = (
        load_remote_commit_pipeline_contract(output_root=status_dir)
        if isinstance(status_dir, Path)
        else None
    )
    report["reviewer_runtime"] = reviewer_runtime_contract_to_dict(contract)
    if commit_pipeline is not None:
        report["commit_pipeline"] = asdict(commit_pipeline)
    report["doctor"] = build_reviewer_doctor_surface(
        contract=contract,
        collaboration=(
            report.get("collaboration")
            if isinstance(report.get("collaboration"), dict)
            else None
        ),
        attention=attention,
        commit_pipeline=commit_pipeline,
        push_enforcement=bridge_liveness.get("push_enforcement"),
        runtime_state={
            "publisher": report.get("publisher"),
            "reviewer_supervisor": report.get("reviewer_supervisor"),
        },
    )


def reviewer_progress_token(
    *,
    reviewer_runtime: dict[str, object],
    bridge_liveness: dict[str, object],
    attention_status: str,
) -> str:
    """Build the dedupe key used by stale-reviewer auto-rollover."""
    reviewer_mode = (
        reviewer_runtime_text(reviewer_runtime, "effective_reviewer_mode")
        or str(
            bridge_liveness.get("effective_reviewer_mode")
            or bridge_liveness.get("reviewer_mode")
            or ""
        )
    ).strip()
    launch_truth = str(bridge_liveness.get("launch_truth") or "").strip()
    current_instruction_revision = str(
        bridge_liveness.get("current_instruction_revision") or ""
    ).strip()
    reviewer_turn_token = ""
    last_poll = reviewer_runtime.get("last_poll")
    if isinstance(last_poll, dict):
        reviewer_turn_token = str(last_poll.get("last_codex_poll_utc") or "").strip()
    if not reviewer_turn_token and not bool(bridge_liveness.get("poll_status_automation_only")):
        reviewer_turn_token = str(
            bridge_liveness.get("last_codex_poll_utc") or ""
        ).strip()
    payload = "\0".join(
        field
        for field in (
            attention_status,
            reviewer_mode,
            launch_truth,
            str(bool(bridge_liveness.get("codex_conductor_active"))),
            reviewer_turn_token,
            current_instruction_revision,
        )
        if field
    )
    return payload.strip("\0")


def reviewer_runtime_mapping(report: dict[str, object]) -> dict[str, object]:
    """Return the reviewer-runtime mapping when present on one report."""
    runtime = report.get("reviewer_runtime")
    return runtime if isinstance(runtime, dict) else {}


def reviewer_runtime_text(
    reviewer_runtime: dict[str, object],
    field_name: str,
) -> str:
    """Return one text field from the report-level reviewer-runtime mapping."""
    return str(reviewer_runtime.get(field_name) or "").strip()
