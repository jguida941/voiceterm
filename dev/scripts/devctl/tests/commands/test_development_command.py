"""Tests for the read-only ``devctl develop`` command."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands import development
from dev.scripts.devctl.commands.development import (
    orchestration_system_picture as orchestration_system_picture_module,
)
from dev.scripts.devctl.commands.development import packet_debt as development_packet_debt
from dev.scripts.devctl.commands.development.models import DevelopmentPacketAttention
from dev.scripts.devctl.commands.development.next_slice import select_next_slice
from dev.scripts.devctl.commands.development.orchestration_inputs import (
    orchestration_snapshot,
)
from dev.scripts.devctl.commands.development.packet_attention import (
    packet_attention_from_review_state,
)
from dev.scripts.devctl.commands.development.watcher.lease import watcher_lease_status
from dev.scripts.devctl.runtime.master_plan_contract import PlanRow, SDLCStage


def test_develop_command_is_registered_read_only() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["develop", "--status", "--format", "json"])

    assert args.command == "develop"
    assert args.action_flag == "status"
    assert "develop" in cli.READ_ONLY_COMMANDS
    assert cli.COMMAND_HANDLERS["develop"] is development.run


def test_develop_status_renders_topology_and_scaling(capsys) -> None:
    args = cli.build_parser().parse_args(["develop", "--status", "--format", "json"])

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "develop"
    assert payload["action"] == "status"
    assert payload["controller_state"] == "read_only"
    assert payload["topology"]["topology_id"] == "develop-default"
    assert "next_step_command" in payload
    assert "packet_attention" in payload
    assert payload["runtime"]["authority_source"] == (
        "AgentWorkBoardProjection+AgentSyncProjection"
    )
    assert "discovered_session_count" in payload["runtime"]
    assert "unregistered_session_count" in payload["runtime"]
    assert "session_discovery" in payload["runtime"]
    assert payload["peer_minds"]
    assert payload["peer_minds"][0]["authority_policy"] == "auxiliary_context_only"
    assert payload["peer_minds"][0]["coverage_scope"] == "provider_latest_projection"
    assert payload["orchestration"]["authority_policy"] == (
        "consume_existing_agent_loop_and_system_picture"
    )
    assert "watcher_lease" in payload
    assert "--follow --terminal none --format json" in (
        payload["watcher_lease"]["next_report_command"]
    )
    assert "--max-follow-snapshots 1" not in (
        payload["watcher_lease"]["next_report_command"]
    )
    assert "continuation" in payload
    assert payload["continuation"]["stop_policy"] == (
        "stop_only_when_typed_controller_closed"
    )
    assert "intake_fanout" in payload["topology"]["scaling"]["mode_ids"]
    assert "WorkerPacket" in payload["topology"]["scaling"]["route_outputs"]


def test_develop_launch_is_read_only_preview(capsys) -> None:
    args = cli.build_parser().parse_args(
        ["develop", "launch", "--dry-run", "--max-cycles", "1", "--format", "json"]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "launch"
    assert payload["controller_state"] == "read_only_launch_preview"
    assert payload["inputs"]["dry_run"] is True
    assert any("no worker process is spawned" in item for item in payload["warnings"])


def test_watcher_lease_uses_live_watcher_heartbeat_when_actor_row_is_idle(
    tmp_path: Path,
) -> None:
    watcher_path = (
        tmp_path / "dev/reports/review_channel/watchers/watch_claude__pending.json"
    )
    watcher_path.parent.mkdir(parents=True, exist_ok=True)
    watcher_path.write_text(
        json.dumps(
            {
                "watch_key": "watch_claude__pending",
                "target": "claude",
                "last_heartbeat_utc": datetime.now(timezone.utc).isoformat(),
                "stop_reason": "",
            }
        ),
        encoding="utf-8",
    )
    review_state = {
        "authority_snapshot": {"packet_target": {"agent": "claude"}},
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "idle_seconds": 999,
                    "confidence_class": "direct_typed_event",
                    "source_event_id": "rev_evt_1",
                }
            ]
        },
    }

    lease = watcher_lease_status(tmp_path, review_state, actor="codex")

    assert lease.status == "live"
    assert lease.stale_seconds <= 300


def test_develop_watch_is_actor_scoped_lifecycle_preview(capsys) -> None:
    args = cli.build_parser().parse_args(
        ["develop", "watch", "--actor", "claude", "--format", "json"]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "watch"
    assert payload["inputs"]["actor"] == "claude"
    assert payload["lifecycle"]["actor"] == "claude"
    assert payload["lifecycle"]["state"] == "preview_only"
    commands = [step["command"] for step in payload["lifecycle"]["steps"]]
    assert any("--target claude --actor claude" in command for command in commands)


def test_develop_watch_markdown_includes_collaboration_sections(capsys) -> None:
    args = cli.build_parser().parse_args(["develop", "watch", "--format", "md"])

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    output = capsys.readouterr().out
    assert "## Runtime" in output
    assert "## Peer Mind" in output
    assert "## Orchestration Inputs" in output
    assert "## Watcher Lease" in output
    assert "## Continuation" in output
    assert "authority_policy: auxiliary_context_only" in output
    assert "coverage_scope: provider_latest_projection" in output


def test_develop_verify_lists_required_checks(capsys) -> None:
    args = cli.build_parser().parse_args(["develop", "verify", "--format", "json"])

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "verify"
    assert payload["controller_state"] == "read_only_verify_preview"
    assert payload["lifecycle"]["steps"][0]["step_id"] == "check-1"
    assert payload["required_checks"][0] in payload["lifecycle"]["steps"][0]["command"]


def test_develop_audit_packets_renders_debt_report(capsys) -> None:
    args = cli.build_parser().parse_args(
        ["develop", "audit-packets", "--max-packets", "3", "--format", "json"]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "audit-packets"
    assert payload["controller_state"] == "read_only_packet_debt_audit"
    assert payload["packet_debt_remediation"]["contract_id"] == (
        "PacketDebtRemediationReport"
    )
    assert payload["packet_debt_remediation"]["write_enabled"] is False


def test_develop_audit_packets_drain_uses_existing_writer(monkeypatch, capsys) -> None:
    class _FakeDebtReport:
        def to_dict(self) -> dict[str, object]:
            return {
                "contract_id": "PacketDebtRemediationReport",
                "write_enabled": True,
                "rows": [],
            }

    calls: dict[str, object] = {}

    def fake_report(inputs):
        calls["write"] = inputs.write
        return _FakeDebtReport()

    monkeypatch.setattr(
        development_packet_debt,
        "packet_debt_remediation_report",
        fake_report,
    )
    args = cli.build_parser().parse_args(
        ["develop", "audit-packets", "--drain-packets", "--format", "json"]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert calls["write"] is True
    assert payload["controller_state"] == "packet_debt_drain"
    assert payload["inputs"]["drain_packets"] is True
    assert payload["packet_debt_remediation"]["write_enabled"] is True


def test_develop_audit_packets_dry_run_suppresses_drain_writer(
    monkeypatch,
    capsys,
) -> None:
    class _FakeDebtReport:
        def to_dict(self) -> dict[str, object]:
            return {
                "contract_id": "PacketDebtRemediationReport",
                "write_enabled": False,
                "rows": [],
            }

    calls: dict[str, object] = {}

    def fake_report(inputs):
        calls["write"] = inputs.write
        return _FakeDebtReport()

    monkeypatch.setattr(
        development_packet_debt,
        "packet_debt_remediation_report",
        fake_report,
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "audit-packets",
            "--drain-packets",
            "--dry-run",
            "--format",
            "json",
        ]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert calls["write"] is False
    assert payload["controller_state"] == "read_only_packet_debt_drain_preview"
    assert payload["inputs"]["dry_run"] is True
    assert payload["packet_debt_remediation"]["write_enabled"] is False
    assert any("--dry-run suppresses" in item for item in payload["warnings"])


def test_develop_drain_packets_only_valid_for_audit_packets() -> None:
    args = cli.build_parser().parse_args(
        ["develop", "status", "--drain-packets", "--format", "json"]
    )

    report = development.build_report(args)

    assert report.ok is False
    assert "--drain-packets is only valid with audit-packets." in report.blockers


def test_develop_orchestration_inputs_consume_existing_surfaces(tmp_path) -> None:
    summary_path = tmp_path / "dev/reports/system_picture/latest/summary.json"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(
        json.dumps(
            {
                "sections": [
                    {
                        "section_id": "graph",
                        "title": "Context Graph",
                        "status": "stale",
                        "source_command": (
                            "python3 dev/scripts/devctl.py context-graph "
                            "--mode bootstrap --format md"
                        ),
                        "notes": ["Latest graph snapshot is older than HEAD."],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    review_state = {
        "agent_loop_decisions": [
            {
                "actor_id": "codex",
                "actor_role": "dashboard",
                "session_id": "session-1",
                "lifecycle_state": "blocked",
                "required_action": "wait_for_review",
                "loop_mode": "run_or_report_blocker",
                "should_continue_loop": True,
                "safe_to_continue": False,
                "may_mutate": False,
                "proof_state": "satisfied",
                "top_blocker": "655 expired unresolved review packet(s)",
                "next_loop_command": (
                    "python3 dev/scripts/devctl.py agent-loop --format json"
                ),
            }
        ]
    }

    snapshot = orchestration_snapshot(tmp_path, review_state, actor="codex")

    assert snapshot.status == "stale_inputs"
    assert snapshot.stale_projection_count == 1
    assert snapshot.action_required_count == 2
    assert snapshot.signals[0].source == "system-picture"
    assert snapshot.signals[0].source_surface == "system-picture"
    assert snapshot.signals[0].severity == "medium"
    assert snapshot.signals[0].recommended_action == "refresh_context_graph"
    assert snapshot.signals[0].closure_check_command == (
        "python3 dev/scripts/checks/check_system_picture_freshness.py --format md"
    )
    assert snapshot.signals[1].source == "agent-loop"
    assert snapshot.signals[1].source_surface == "agent-loop"
    assert snapshot.signals[1].severity == "medium"
    assert snapshot.signals[1].recommended_action == "wait_for_review"
    assert snapshot.signals[1].closure_check_command == (
        "python3 dev/scripts/devctl.py agent-loop --format json"
    )
    assert snapshot.agent_loop_decisions[0].top_blocker.startswith("655 expired")


def test_develop_orchestration_closes_stale_summary_when_live_section_current(
    tmp_path,
    monkeypatch,
) -> None:
    summary_path = tmp_path / "dev/reports/system_picture/latest/summary.json"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(
        json.dumps(
            {
                "sections": [
                    {
                        "section_id": "graph",
                        "title": "Context Graph",
                        "status": "stale",
                        "source_command": "python3 dev/scripts/devctl.py context-graph",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        orchestration_system_picture_module,
        "_current_system_picture_sections_by_id",
        lambda _repo_root: {
            "graph": {
                "section_id": "graph",
                "title": "Context Graph",
                "status": "current",
            }
        },
    )

    snapshot = orchestration_snapshot(tmp_path, {}, actor="codex")

    assert snapshot.signal_count == 0
    assert snapshot.stale_projection_count == 0
    assert snapshot.status == "current"


def test_develop_orchestration_refreshes_cached_agent_loop_decisions(
    tmp_path,
) -> None:
    review_state = {
        "attention": {"status": "checkpoint_required"},
        "recovery_assessment": {
            "diagnosis": {
                "supporting_causes": ["checkpoint_budget_exhausted"],
            },
            "decision": {
                "command": "python3 dev/scripts/devctl.py commit -m x",
            },
        },
        "current_session": {"current_instruction_revision": "rev-current"},
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_1",
                "snapshot_id": "agent-runtime-clock:rev_evt_1",
            },
            "packet_attention": {},
        },
        "authority_snapshot": {
            "actor_authorities": [
                {
                    "actor_id": "codex",
                    "granted_capabilities": ["runtime.observe"],
                }
            ],
            "allowed_actions": ["startup-context.summary"],
            "blocked_actions": ["vcs.stage", "vcs.commit", "vcs.push"],
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "dashboard",
                    "session_id": "s-codex",
                    "status": "idle",
                    "source_event_id": "rev_evt_1",
                    "confidence_class": "direct_typed_event",
                }
            ]
        },
        "agent_loop_decisions": [
            {
                "actor_id": "codex",
                "actor_role": "dashboard",
                "session_id": "s-codex",
                "lifecycle_state": "blocked",
                "required_action": "wait_for_review",
                "should_continue_loop": True,
                "safe_to_continue": False,
                "proof_state": "satisfied",
                "top_blocker": "655 expired unresolved review packet(s)",
            }
        ],
        "packets": [],
    }

    snapshot = orchestration_snapshot(tmp_path, review_state, actor="codex")

    assert snapshot.agent_loop_decisions
    assert snapshot.agent_loop_decisions[0].top_blocker == (
        "startup authority: staged_index_budget_exceeded"
    )
    assert not snapshot.agent_loop_decisions[0].top_blocker.startswith("655 expired")


def test_develop_orchestration_uses_dashboard_blocker_when_available(
    tmp_path,
) -> None:
    review_state = {
        "attention": {"status": "checkpoint_required"},
        "recovery_assessment": {
            "diagnosis": {
                "supporting_causes": ["checkpoint_budget_exhausted"],
            },
        },
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_1",
                "snapshot_id": "agent-runtime-clock:rev_evt_1",
            },
            "packet_attention": {},
        },
        "authority_snapshot": {
            "allowed_actions": ["startup-context.summary"],
            "blocked_actions": ["vcs.stage", "vcs.commit", "vcs.push"],
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "dashboard",
                    "session_id": "s-codex",
                    "status": "idle",
                    "source_event_id": "rev_evt_1",
                    "confidence_class": "direct_typed_event",
                }
            ]
        },
        "packets": [],
    }
    dashboard = {
        "control_plane": {
            "top_blocker": "startup authority: import_index_atomicity",
            "next_action": (
                "checkpoint_blocked_by_startup_authority:import_index_atomicity"
            ),
        },
        "now": {
            "top_blocker": "startup authority: import_index_atomicity",
            "next_action": (
                "checkpoint_blocked_by_startup_authority:import_index_atomicity"
            ),
        },
    }

    snapshot = orchestration_snapshot(
        tmp_path,
        review_state,
        actor="codex",
        dashboard=dashboard,
    )

    assert snapshot.agent_loop_decisions
    assert snapshot.agent_loop_decisions[0].top_blocker == (
        "startup authority: import_index_atomicity"
    )


def test_develop_rejects_unknown_fleet() -> None:
    args = cli.build_parser().parse_args(
        ["develop", "--status", "--fleet", "experimental", "--format", "json"]
    )

    report = development.build_report(args)

    assert report.ok is False
    assert report.status == "blocked"
    assert "Only the default DevelopmentModeTopology fleet is implemented." in (
        report.blockers
    )


def test_develop_next_prefers_packet_attention_plan_row() -> None:
    ordinary = PlanRow(
        row_id="MP377-IN-PROGRESS",
        title="Ordinary in-progress row",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    packet_row = PlanRow(
        row_id="PKT-BIND-REV-PKT-9999",
        title="Packet-owned finding row",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        sourced_from_packets=("rev_pkt_9999",),
        target_ref="plan:MP-377",
    )
    attention = DevelopmentPacketAttention(
        attention_required=True,
        attention_status="review_needed",
        wake_reason="finding_pending",
        latest_finding_packet_id="rev_pkt_9999",
        durable_plan_row_id="PKT-BIND-REV-PKT-9999",
    )

    selected = select_next_slice(
        (ordinary, packet_row),
        packet_attention=attention,
    )

    assert selected.slice_id == "PKT-BIND-REV-PKT-9999"
    assert "packet attention" in selected.reason.lower()


def test_packet_attention_includes_latest_finding_as_actionable() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_9999",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    attention = packet_attention_from_review_state(review_state, rows=())

    assert attention.attention_required is True
    assert attention.latest_finding_packet_id == "rev_pkt_9999"
    assert attention.pending_actionable_packet_ids == ("rev_pkt_9999",)
    assert attention.required_command == (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_9999 --terminal none --format md"
    )


def test_packet_attention_does_not_revive_acked_latest_finding() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_old",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "posted_at": "2000-01-01T00:00:00Z",
                "expires_at_utc": "2000-01-01T00:30:00Z",
            },
            {
                "packet_id": "rev_pkt_new",
                "to_agent": "codex",
                "kind": "finding",
                "status": "acked",
                "posted_at": "2999-01-01T00:00:00Z",
                "expires_at_utc": "2999-01-01T00:30:00Z",
            },
        ]
    }
    packet_row = PlanRow(
        row_id="PKT-BIND-REV-PKT-NEW",
        title="Acked packet-owned finding row",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        sourced_from_packets=("rev_pkt_new",),
        target_ref="plan:MP-377",
    )

    attention = packet_attention_from_review_state(review_state, rows=(packet_row,))
    selected = select_next_slice((packet_row,), packet_attention=attention)

    assert attention.attention_required is True
    assert attention.wake_reason == "expired_unresolved_packet"
    assert attention.latest_finding_packet_id == ""
    assert attention.pending_actionable_packet_ids == ()
    assert attention.durable_plan_row_id == ""
    assert attention.required_command == (
        "python3 dev/scripts/devctl.py develop audit-packets --format md"
    )
    assert "Packet debt audit" in attention.summary
    assert selected.slice_id == "packet-debt-audit"
