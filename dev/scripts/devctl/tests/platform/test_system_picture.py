"""Tests for `devctl system-picture`."""

from __future__ import annotations

import json
import tempfile
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands import listing, system_picture
from dev.scripts.devctl.platform.system_picture import build_system_picture_snapshot
from dev.scripts.devctl.platform.coordination_snapshot_models import (
    CoordinationSnapshot,
)
from dev.scripts.devctl.runtime.control_plane_read_model import (
    ControlPlaneReadModel,
)
from dev.scripts.devctl.runtime.control_plane_read_model_support import (
    ControlPlaneReadModelOptions,
)
from dev.scripts.devctl.platform.system_picture_models import (
    SystemPictureSection,
    SystemPictureSnapshot,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sample_snapshot(*, repo_root: Path) -> SystemPictureSnapshot:
    return SystemPictureSnapshot(
        snapshot_id="sys-1234",
        generated_at_utc="2026-04-03T12:00:00Z",
        repo_name="codex-voice",
        repo_root=str(repo_root),
        current_branch="feature/system-picture",
        head_commit_sha="abc123",
        tree_hash="tree456",
        section_hashes={"startup": "hash-startup", "graph": "hash-graph"},
        current_section_count=2,
        stale_section_count=0,
        missing_section_count=0,
        sections=(
            SystemPictureSection(
                section_id="startup",
                title="Startup Authority",
                status="current",
                summary={"advisory_action": "await_review"},
                source_path="dev/reports/startup/latest/receipt.json",
                source_command="python3 dev/scripts/devctl.py startup-context --format summary",
                generated_at_utc="2026-04-03T11:59:00Z",
                section_hash="hash-startup",
                notes=(),
            ),
            SystemPictureSection(
                section_id="graph",
                title="Context Graph",
                status="current",
                summary={"node_count": 2411},
                source_path="dev/reports/graph_snapshots/latest.json",
                source_command="python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md",
                generated_at_utc="2026-04-03T12:00:00Z",
                section_hash="hash-graph",
                notes=(),
            ),
        ),
    )


def _command_args(
    *,
    output_root: str,
    format: str = "md",
    output: str | None = None,
    json_output: str | None = None,
    ledger_path: str | None = None,
    write_ledger: bool = False,
) -> Namespace:
    return Namespace(
        command="system-picture",
        output_root=output_root,
        ledger_path=ledger_path,
        write_ledger=write_ledger,
        format=format,
        output=output,
        json_output=json_output,
        pipe_command=None,
        pipe_args=None,
    )


def test_system_picture_parser_and_listing_include_command() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "system-picture",
            "--output-root",
            "/tmp/system-picture",
            "--ledger-path",
            "/tmp/proof-ledger.md",
            "--write-ledger",
            "--json-output",
            "/tmp/system-picture.json",
        ]
    )
    assert args.command == "system-picture"
    assert args.output_root == "/tmp/system-picture"
    assert args.ledger_path == "/tmp/proof-ledger.md"
    assert args.write_ledger is True
    assert args.json_output == "/tmp/system-picture.json"
    assert "system-picture" in listing.COMMANDS


def test_build_system_picture_snapshot_reads_typed_sources() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        resolved_root = repo_root.resolve()
        _write_json(
            repo_root / "dev/reports/governance/latest/review_summary.json",
            {
                "generated_at_utc": "2026-04-03T12:02:00Z",
                "stats": {
                    "total_findings": 8,
                    "open_finding_count": 2,
                    "fixed_count": 5,
                    "cleanup_rate_pct": 62.5,
                    "false_positive_rate_pct": 12.5,
                },
            },
        )
        _write_json(
            repo_root
            / "dev/reports/governance/external_findings_latest/external_findings_summary.json",
            {
                "generated_at_utc": "2026-04-03T12:03:00Z",
                "stats": {
                    "total_findings": 6,
                    "unique_repo_count": 2,
                    "reviewed_count": 4,
                    "adjudication_coverage_pct": 66.7,
                    "fixed_count": 2,
                    "confirmed_issue_count": 3,
                },
            },
        )
        _write_json(
            repo_root / "dev/reports/data_science/latest/summary.json",
            {
                "generated_at": "2026-04-03T12:04:00Z",
                "event_stats": {
                    "total_events": 25,
                    "success_rate_pct": 96.0,
                    "p95_duration_seconds": 12.0,
                },
                "watchdog_stats": {
                    "total_episodes": 5,
                    "success_rate_pct": 80.0,
                },
                "external_finding_stats": {
                    "unique_repo_count": 2,
                },
            },
        )
        startup_context = SimpleNamespace(
            governance=SimpleNamespace(
                repo_identity=SimpleNamespace(current_branch="feature/system-picture"),
                push_enforcement=SimpleNamespace(
                    ahead_of_upstream_commits=4,
                    checkpoint_required=False,
                    safe_to_continue_editing=True,
                ),
            ),
            reviewer_gate=SimpleNamespace(
                implementation_blocked=False,
                implementation_block_reason="",
                review_gate_allows_push=True,
            ),
            push_decision=SimpleNamespace(
                action="await_review",
                reason="review_pending_before_push",
                push_eligible_now=False,
                publication_backlog=SimpleNamespace(backlog_state="queued"),
                publication_guidance="publish after review",
            ),
            advisory_action="await_review",
            advisory_reason="review_pending_before_push",
        )
        startup_receipt = SimpleNamespace(
            head_commit_sha="abc123",
            generated_at_utc="2026-04-03T12:00:00Z",
        )
        graph_snapshot = SimpleNamespace(
            branch="feature/system-picture",
            commit_hash="abc123",
            node_count=2411,
            edge_count=53166,
            nodes_by_kind={"guard": 69, "probe": 25, "plan": 19},
            temperature_distribution=SimpleNamespace(average=0.32),
            generated_at_utc="2026-04-03T12:01:00Z",
        )
        review_state = SimpleNamespace(
            attention=SimpleNamespace(status="review_follow_up_required", owner="codex"),
            reviewer_runtime=SimpleNamespace(publish_clear=False),
            bridge=SimpleNamespace(
                reviewer_mode="active_dual_agent",
                effective_reviewer_mode="active_dual_agent",
                reviewer_freshness="fresh",
                review_needed=True,
                review_accepted=False,
            ),
            current_session=SimpleNamespace(
                current_instruction_revision=12,
                implementer_ack_state="acknowledged",
            ),
            commit_pipeline=SimpleNamespace(state="push_blocked", blocked_reason="review_pending"),
            timestamp="2026-04-03T12:01:30Z",
            warnings=("warning-one",),
            errors=(),
        )
        control_plane = ControlPlaneReadModel(
            timestamp="2026-04-03T12:01:40Z",
            branch="feature/system-picture",
            head_sha="abc123",
            worktree_clean=False,
            ahead_of_upstream=4,
            resolved_phase="review_pending",
            push_eligible=False,
            implementation_blocked=True,
            top_blocker="review_pending_before_push",
            next_action="await_review",
            next_command="python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
            reviewer_mode="active_dual_agent",
            operator_interaction_mode="remote_control",
            reviewer_freshness="fresh",
            review_accepted=False,
            last_reviewed_sha="abc122",
            attention_status="review_follow_up_required",
            attention_summary="review follow-up required",
            publisher_running=False,
            supervisor_running=False,
            codex_conductor_alive=True,
            claude_conductor_alive=False,
            pending_action_requests=2,
            last_guard_ok=True,
            check_details=({"check": "code_shape", "status": "FAIL"},),
        )

        with (
            patch(
                "dev.scripts.devctl.platform.system_picture.scan_repo_governance_safely",
                return_value=startup_context.governance,
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.build_startup_context",
                return_value=startup_context,
            ) as mock_build_startup_context,
            patch(
                "dev.scripts.devctl.platform.system_picture.build_startup_authority_report",
                return_value={"ok": True, "errors": (), "warnings": ("warn",)},
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.load_startup_receipt",
                return_value=startup_receipt,
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.startup_receipt_path",
                return_value=repo_root / "dev/reports/startup/latest/receipt.json",
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.current_head_commit_sha",
                return_value="abc123",
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.compute_non_audit_worktree_hash",
                return_value="tree456",
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.list_context_graph_snapshots",
                return_value=(repo_root / "dev/reports/graph_snapshots/latest.json",),
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.load_context_graph_snapshot",
                return_value=graph_snapshot,
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.resolve_review_state_path",
                return_value=repo_root / "dev/reports/review_channel/latest/review_state.json",
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.load_current_review_state",
                return_value=review_state,
            ) as mock_load_current_review_state,
            patch(
                "dev.scripts.devctl.platform.system_picture.load_startup_quality_signals",
                return_value={"probe_report_status": "current"},
            ),
            patch(
                "dev.scripts.devctl.platform.system_picture.build_control_plane_read_model",
                return_value=control_plane,
            ) as mock_build_control_plane,
            patch(
                "dev.scripts.devctl.platform.system_picture.build_coordination_snapshot",
                return_value=CoordinationSnapshot(
                    generated_at_utc="2026-04-03T12:01:45Z",
                    repo_name="codex-voice",
                    repo_root=str(repo_root),
                    current_branch="feature/system-picture",
                    head_commit_sha="abc123",
                    declared_topology="multi_agent_orchestrated",
                    observed_topology="dual_agent",
                    recommended_topology="single_agent",
                    fanout_posture="planned_not_live",
                    safe_to_fanout=False,
                    worktree_strategy="isolated_worker_worktrees",
                    resync_required=True,
                    resync_reasons=("runtime_truth:blocked",),
                    observed_active_participant_count=2,
                    declared_participant_count=2,
                    planned_delegated_worker_count=1,
                    live_delegated_worker_count=0,
                ),
            ),
        ):
            snapshot = build_system_picture_snapshot(repo_root=repo_root)

        mock_load_current_review_state.assert_called_once_with(
            resolved_root,
            governance=startup_context.governance,
        )
        mock_build_startup_context.assert_called_once_with(
            repo_root=resolved_root,
            governance=startup_context.governance,
            review_state=review_state,
        )
        mock_build_control_plane.assert_called_once()
        control_plane_args, control_plane_kwargs = mock_build_control_plane.call_args
        assert control_plane_args == (resolved_root,)
        assert control_plane_kwargs == {
            "options": ControlPlaneReadModelOptions(
                governance=startup_context.governance,
                review_state=review_state,
            )
        }

    sections = {section.section_id: section for section in snapshot.sections}
    assert snapshot.contract_id == "SystemPicture"
    assert snapshot.current_branch == "feature/system-picture"
    assert snapshot.head_commit_sha == "abc123"
    assert snapshot.current_section_count == 9
    assert snapshot.stale_section_count == 0
    assert snapshot.missing_section_count == 0
    assert sections["startup"].summary["startup_receipt_fresh"] is True
    assert sections["graph"].summary["node_count"] == 2411
    assert sections["review_runtime"].summary["review_needed"] is True
    assert sections["coordination"].summary["recommended_topology"] == "single_agent"
    assert sections["control_plane"].summary["next_command"].startswith("python3 dev/scripts/devctl.py review-channel")
    assert sections["control_plane"].summary["operator_interaction_mode"] == "remote_control"
    assert sections["control_plane"].summary["attention_status"] == "review_follow_up_required"
    assert sections["governance_review"].summary["total_findings"] == 8
    assert sections["external_findings"].summary["unique_repo_count"] == 2
    assert sections["data_science"].summary["total_events"] == 25


def test_system_picture_command_writes_artifacts_and_receipt() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        output_root = repo_root / "dev/reports/system_picture"
        ledger_path = repo_root / "dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md"
        output_path = repo_root / "system-picture-command.json"
        args = _command_args(
            output_root=str(output_root),
            ledger_path=str(ledger_path),
            write_ledger=True,
            format="json",
            output=str(output_path),
        )
        stdout = StringIO()
        with (
            patch(
                "dev.scripts.devctl.platform.system_picture_command.build_system_picture_snapshot",
                return_value=_sample_snapshot(repo_root=repo_root),
            ),
            redirect_stdout(stdout),
        ):
            exit_code = system_picture.run(args)

        receipt = json.loads(stdout.getvalue().strip())
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        summary_json = output_root / "latest/summary.json"
        summary_md = output_root / "latest/summary.md"
        ledger_preview = output_root / "latest/proof_ledger.md"
        history_jsonl = output_root / "history/snapshots.jsonl"
        assert exit_code == 0
        assert receipt["command"] == "system-picture"
        assert receipt["artifact"]["path"] == str(output_path)
        assert payload["command"] == "system-picture"
        assert payload["paths"]["summary_json"] == str(summary_json)
        assert payload["ledger_path"] == str(ledger_path)
        assert summary_json.exists()
        assert summary_md.exists()
        assert ledger_preview.exists()
        assert history_jsonl.exists()
        assert ledger_path.exists()
        assert "# AI Governance Platform Proof Ledger" in ledger_path.read_text(encoding="utf-8")
