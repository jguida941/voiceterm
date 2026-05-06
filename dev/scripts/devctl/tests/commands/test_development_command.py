"""Tests for the read-only ``devctl develop`` command."""

from __future__ import annotations

import json
import shlex
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands import development
from dev.scripts.devctl.commands.development import (
    design_preflight as design_preflight_module,
    orchestration_system_picture as orchestration_system_picture_module,
)
from dev.scripts.devctl.commands.development import packet_debt as development_packet_debt
from dev.scripts.devctl.commands.development import plan_intake
from dev.scripts.devctl.commands.development import report as development_report
from dev.scripts.devctl.commands.development.actor_resolution import resolve_actor
from dev.scripts.devctl.commands.development.models import (
    DevelopmentPacketAttention,
    DevelopmentPeerMindSnapshot,
)
from dev.scripts.devctl.commands.development.continuation import continuation_signal
from dev.scripts.devctl.commands.development.orchestration_models import (
    DevelopmentContinuationRequiredSignal,
    DevelopmentOrchestrationSnapshot,
    DevelopmentWatcherLease,
)
from dev.scripts.devctl.commands.development.next_slice import select_next_slice
from dev.scripts.devctl.commands.development.orchestration_inputs import (
    orchestration_snapshot,
)
from dev.scripts.devctl.commands.development.packet_attention import (
    packet_attention_from_review_state,
)
from dev.scripts.devctl.commands.development.status_summary import (
    status_for_report,
    summary_for_action,
)
from dev.scripts.devctl.commands.development.watcher.lease import watcher_lease_status
from dev.scripts.devctl.runtime.master_plan_contract import PlanRow, SDLCStage
from dev.scripts.devctl.runtime.development_role_adapters import (
    build_develop_role_adapter_matrix,
)
from dev.scripts.devctl.runtime.development_packet_pressure_models import (
    PacketBacklogPressure,
)
from dev.scripts.devctl.runtime.runtime_truth_snapshot import RuntimeTruthSnapshot


def _packet_pressure(
    *,
    live_total: int,
    actionable_total: int,
) -> PacketBacklogPressure:
    return PacketBacklogPressure(
        live_total=live_total,
        actionable_total=actionable_total,
        near_ttl_total=0,
        expired_unresolved_total=0,
        carry_forward_total=0,
        durable_owner_gap_total=0,
        per_kind={},
        per_role={},
        selected_packet_ids=(),
        pressure_state="below_budget",
        soft_attention_budget=12,
        hard_attention_budget=15,
        near_ttl_minutes=10,
    )


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
    assert "attention_reason" in payload["packet_attention"]
    assert "wake_reason" in payload["packet_attention"]
    assert payload["runtime"]["authority_source"] == (
        "AgentWorkBoardProjection+AgentSyncProjection"
    )
    assert "discovered_session_count" in payload["runtime"]
    assert "unregistered_session_count" in payload["runtime"]
    assert "session_discovery" in payload["runtime"]
    assert payload["peer_minds"]
    assert payload["peer_minds"][0]["authority_policy"] == "auxiliary_context_only"
    assert payload["peer_minds"][0]["coverage_scope"] == "provider_latest_projection"
    assert "attention_hint" in payload["peer_minds"][0]
    assert "wake_hint" in payload["peer_minds"][0]
    assert payload["orchestration"]["authority_policy"] == (
        "consume_existing_agent_loop_and_system_picture"
    )
    assert payload["collaboration_mode"]["contract_id"] == "CollaborationModeTopology"
    assert payload["collaboration_mode"]["selected_mode_id"] == "solo"
    assert payload["collaboration_mode"]["selected_role_preset_id"] == "dashboard"
    assert payload["collaboration_mode"]["default_worker_fanout"] == 0
    assert payload["collaboration_mode"]["packet_pressure_policy"] == {
        "budget_behavior": (
            "crossing a packet budget triggers classification and receipt "
            "coverage, never blind autodrain"
        ),
        "durable_intent_policy": (
            "classify durable intent as soon as detected and route to typed "
            "owner or terminal receipt"
        ),
        "hard_attention_budget": 15,
        "near_ttl_minutes": 10,
        "soft_attention_budget": 12,
    }
    assert payload["packet_pressure"]["contract_id"] == "PacketBacklogPressure"
    assert payload["packet_ingestion_decision"]["contract_id"] == (
        "PacketAttentionIngestionDecision"
    )
    assert isinstance(payload["selected_packet_classifications"], list)
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


def test_next_commands_with_attention_uses_registered_peer_hints() -> None:
    commands = development_report._next_commands_with_attention(
        ("python3 dev/scripts/devctl.py develop launch --dry-run --max-cycles 1",),
        packet_attention=DevelopmentPacketAttention(
            attention_required=True,
            required_command="python3 dev/scripts/devctl.py review-channel --action show --packet-id rev_pkt_1 --terminal none --format md",
        ),
        peer_minds=(
            DevelopmentPeerMindSnapshot(
                provider="claude",
                attention_hint="refresh_agent_mind",
                wake_hint="refresh_agent_mind",
                suggested_command="python3 dev/scripts/devctl.py agent-mind --agent claude --since-cursor --project --format md --limit 20",
            ),
            DevelopmentPeerMindSnapshot(
                provider="codex",
                attention_hint="peer_recent_activity",
                wake_hint="peer_recent_activity",
                suggested_command="ignored",
            ),
        ),
    )

    assert commands == (
        "python3 dev/scripts/devctl.py review-channel --action show --packet-id rev_pkt_1 --terminal none --format md",
        "python3 dev/scripts/devctl.py develop launch --dry-run --max-cycles 1",
        "python3 dev/scripts/devctl.py agent-mind --agent claude --since-cursor --project --format md --limit 20",
    )


def test_peer_mind_alias_divergence_is_reported() -> None:
    warnings = development_report._peer_mind_alias_warnings(
        (
            DevelopmentPeerMindSnapshot(
                provider="claude",
                attention_hint="peer_packet_activity",
                wake_hint="refresh_agent_mind",
            ),
        )
    )

    assert warnings == (
        "peer_mind_hint_alias_diverged:"
        "claude:attention_hint=peer_packet_activity:wake_hint=refresh_agent_mind",
    )


def test_develop_status_accepts_collaboration_mode_and_role_preset(capsys) -> None:
    args = cli.build_parser().parse_args(
        [
            "develop",
            "--status",
            "--collaboration-mode",
            "dogfood_campaign",
            "--role-preset",
            "tester",
            "--max-workers",
            "2",
            "--format",
            "json",
        ]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    collaboration = payload["collaboration_mode"]
    assert collaboration["requested_mode"] == "dogfood_campaign"
    assert collaboration["requested_role_preset"] == "tester"
    assert collaboration["selected_mode_id"] == "dogfood_campaign"
    assert collaboration["selected_role_preset_id"] == "tester"
    assert collaboration["selected_role_preset"]["mutation_policy"] == "evidence_only"
    assert collaboration["mutable_fanout_status"] == "blocked_by_read_model_mode"


def test_develop_design_preflight_records_ground_truth_receipt(
    monkeypatch,
    tmp_path,
) -> None:
    class FakeConnectivity:
        def to_dict(self):
            return {
                "contract_id": "ConnectivityRegistrySnapshot",
                "connected_contracts": [
                    {"contract_id": "RemoteControlAttachmentState"},
                ],
                "warnings": [],
            }

    recorded = {}

    def fake_append(receipt, *, repo_root, receipt_path=None):
        recorded["receipt"] = receipt
        return repo_root / "dev/state/ground_truth_probe_receipts.jsonl"

    monkeypatch.setattr(
        design_preflight_module,
        "build_connectivity_registry_snapshot",
        lambda repo_root: FakeConnectivity(),
    )
    monkeypatch.setattr(
        design_preflight_module,
        "load_startup_quality_signals",
        lambda repo_root: {"probe_report": {"risk_hints": 0}},
    )
    monkeypatch.setattr(
        design_preflight_module,
        "build_runtime_truth_snapshot",
        lambda **kwargs: RuntimeTruthSnapshot(
            interaction_mode="remote_control",
            remote_control_active=True,
            remote_control_method="claude_session_state_bridge",
            remote_control_session_id="session_123",
            agent_mind_providers=("claude",),
        ),
    )
    monkeypatch.setattr(
        design_preflight_module,
        "collect_git_status",
        lambda **kwargs: {
            "changes": [
                {"path": "dev/scripts/devctl/runtime/new_contract.py"},
            ],
        },
    )
    monkeypatch.setattr(
        design_preflight_module,
        "detect_ground_truth_trigger_paths",
        lambda **kwargs: ("dev/scripts/devctl/runtime/new_contract.py",),
    )
    monkeypatch.setattr(
        design_preflight_module,
        "append_ground_truth_probe_receipt",
        fake_append,
    )

    args = SimpleNamespace(
        action="design-preflight",
        action_flag=None,
        topic="remote control active",
        record_ground_truth_receipt=True,
        since_ref="",
    )

    report = design_preflight_module.build_design_preflight(
        args=args,
        repo_root=tmp_path,
        review_state={},
    )

    assert report is not None
    assert report.routing_decision == "reuse_existing_surface"
    assert report.receipt_path == "dev/state/ground_truth_probe_receipts.jsonl"
    assert report.receipt_verdict == "satisfied"
    assert recorded["receipt"].contract_id == "GroundTruthProbeRunReceipt"


def test_develop_role_slash_adapters_forward_to_typed_request_model() -> None:
    matrix = build_develop_role_adapter_matrix(extra_args="")
    providers = {row.provider_id for row in matrix}
    roles_by_provider = {
        provider: {row.role_preset for row in matrix if row.provider_id == provider}
        for provider in providers
    }

    assert providers == {"codex", "claude"}
    assert roles_by_provider["codex"] == roles_by_provider["claude"]
    assert roles_by_provider["codex"] == {
        "dashboard",
        "implementer",
        "reviewer",
        "architect",
        "researcher",
        "intake",
        "tester",
        "watcher",
        "operator",
    }

    for row in matrix:
        args = cli.build_parser().parse_args(shlex.split(row.adapter_command)[2:])
        assert args.command == "develop"
        assert args.actor == row.provider_id
        assert args.role_preset == row.role_preset
        assert args.collaboration_mode == row.collaboration_mode

    root = Path(__file__).resolve().parents[5]
    develop_adapter = (root / ".claude" / "commands" / "develop.md").read_text(
        encoding="utf-8",
    )
    rendered_catalog = (root / "dev/templates/slash/develop/roles.md").read_text(
        encoding="utf-8",
    )

    assert "development_role_adapters.py" in develop_adapter
    assert "role shortcuts must not fork" in develop_adapter
    assert "--actor codex --role-preset dashboard" in rendered_catalog
    assert "--actor claude --role-preset dashboard" in rendered_catalog
    assert "repo-local path authority" in rendered_catalog


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


def test_stopped_watcher_does_not_block_when_packet_pressure_is_clear() -> None:
    signal = continuation_signal(
        packet_attention=DevelopmentPacketAttention(),
        orchestration=DevelopmentOrchestrationSnapshot(),
        watcher_lease=DevelopmentWatcherLease(
            watched_actor="claude",
            status="stopped",
            next_report_command=(
                "python3 dev/scripts/devctl.py review-channel --action watch"
            ),
        ),
        packet_pressure=_packet_pressure(live_total=0, actionable_total=0),
        current_action="status",
        fallback_commands=("python3 dev/scripts/devctl.py develop next --format md",),
    )

    assert signal.continuation_required is False
    assert signal.final_response_allowed is True
    assert signal.next_required_command == ""
    assert signal.reasons == ()


def test_stopped_watcher_blocks_when_packet_pressure_is_missing() -> None:
    signal = continuation_signal(
        packet_attention=DevelopmentPacketAttention(),
        orchestration=DevelopmentOrchestrationSnapshot(),
        watcher_lease=DevelopmentWatcherLease(
            watched_actor="claude",
            status="stopped",
            next_report_command=(
                "python3 dev/scripts/devctl.py review-channel --action watch"
            ),
        ),
        current_action="status",
        fallback_commands=("python3 dev/scripts/devctl.py develop next --format md",),
    )

    assert signal.continuation_required is True
    assert signal.final_response_allowed is False
    assert signal.reasons == ("watcher_stopped:claude",)
    assert signal.next_required_command.endswith("review-channel --action watch")


def test_stopped_watcher_blocks_when_live_packet_pressure_exists() -> None:
    signal = continuation_signal(
        packet_attention=DevelopmentPacketAttention(),
        orchestration=DevelopmentOrchestrationSnapshot(),
        watcher_lease=DevelopmentWatcherLease(
            watched_actor="claude",
            status="stopped",
            next_report_command=(
                "python3 dev/scripts/devctl.py review-channel --action watch"
            ),
        ),
        packet_pressure=_packet_pressure(live_total=1, actionable_total=0),
        current_action="status",
        fallback_commands=("python3 dev/scripts/devctl.py develop next --format md",),
    )

    assert signal.continuation_required is True
    assert signal.final_response_allowed is False
    assert signal.reasons == ("watcher_stopped:claude",)
    assert signal.next_required_command.endswith("review-channel --action watch")


def test_develop_report_status_does_not_render_ready_when_continuation_required() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        status="continue_required",
        final_response_allowed=False,
        reasons=("packet_attention:action_request_pending",),
        next_required_command=(
            "python3 dev/scripts/devctl.py review-channel --action inbox "
            "--target claude --actor claude --status pending --terminal none --format md"
        ),
        stop_policy="stop_only_when_typed_controller_closed",
        summary=(
            "Do not stop here; run `python3 dev/scripts/devctl.py "
            "review-channel --action inbox --target claude --actor claude "
            "--status pending --terminal none --format md` next."
        ),
    )

    assert status_for_report(
        blockers=(),
        continuation=continuation,
    ) == "continue_required"
    assert "Do not stop here" in summary_for_action(
        "status",
        blockers=(),
        continuation=continuation,
        lifecycle_actions=frozenset(),
    )


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
    assert "## Collaboration Mode" in output
    assert "## Packet Pressure" in output
    assert "## Watcher Lease" in output
    assert "## Continuation" in output
    assert "authority_policy: auxiliary_context_only" in output
    assert "coverage_scope: provider_latest_projection" in output
    assert "attention_hint=" in output


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


def test_develop_ingest_plan_body_writes_row_and_receipt(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--plan-row-id",
            "MP377-P0-T22AN-W",
            "--title",
            "Typed plan-ingestion closure for every planning source",
            "--body",
            "Any agent-authored plan must reach typed plan authority.",
            "--source-kind",
            "chat",
            "--source-ref",
            "chat://test-plan",
            "--target-ref",
            "plan:MP-377",
            "--anchor-ref",
            "section:MP-377",
            "--format",
            "json",
        ]
    )

    rc = plan_intake.run_ingest_plan(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    receipt = payload["receipt"]
    rows = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_index.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    receipt_rows = [
        json.loads(line)
        for line in (
            tmp_path / "dev/state/plan_ingestion_receipts.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert receipt["contract_id"] == "PlanIntentIngestionReceipt"
    assert receipt["status"] == "accepted"
    assert receipt["row_ids"] == ["MP377-P0-T22AN-W"]
    assert rows[0]["row_id"] == "MP377-P0-T22AN-W"
    assert rows[0]["provenance"]["source_kind"] == "PlanIntentIngestion:chat"
    assert any(
        ref.startswith("plan_source_snapshot:")
        for ref in rows[0]["work_evidence_ids"]
    )
    snapshots = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_source_snapshots.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert snapshots[0]["plan_row_id"] == "MP377-P0-T22AN-W"
    assert snapshots[0]["source_text"] == (
        "Any agent-authored plan must reach typed plan authority."
    )
    assert receipt["source_snapshot_ids"] == [snapshots[0]["snapshot_id"]]
    assert receipt["source_retention_status"] == "snapshotted"
    assert receipt["source_integrity_status"] == "ok"
    assert receipt_rows[0]["row_ids"] == ["MP377-P0-T22AN-W"]


def test_develop_ingest_intent_alias_writes_typed_plan_receipt(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-intent",
            "--plan-row-id",
            "MP377-P0-T22AN-X",
            "--title",
            "Packet-aware develop closure",
            "--body",
            "Claude dogfood packet feedback must become typed receipts.",
            "--source-kind",
            "chat",
            "--source-ref",
            "chat://test-ingest-intent",
            "--target-ref",
            "plan:MP-377",
            "--format",
            "json",
        ]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "ingest-intent"
    assert payload["receipt"]["row_ids"] == ["MP377-P0-T22AN-X"]


def test_develop_ingest_plan_file_accepts_checklist_rows(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    source = tmp_path / "plan.md"
    source.write_text(
        "# Typed Plan\n\n- [ ] `MP377-P0-T22AN-X` File-backed planning row\n",
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--body-file",
            str(source),
            "--source-kind",
            "file",
            "--target-ref",
            "plan:MP-377",
            "--format",
            "json",
        ]
    )

    receipt = plan_intake.ingest_plan_intent(args, repo_root=tmp_path)
    rows = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_index.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert receipt.status == "accepted"
    assert receipt.row_ids == ("MP377-P0-T22AN-X",)
    assert rows[0]["title"] == "File-backed planning row"
    assert rows[0]["target_ref"] == "plan:MP-377"


def test_develop_ingest_intent_source_defaults_to_markdown_plan_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    source = tmp_path / "plan.md"
    source.write_text(
        "# MP-377\n\n- [ ] `MP377-P0-T22AN-X` Source-backed planning row\n",
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-intent",
            "--source",
            str(source),
            "--target-ref",
            "plan:MP377-P0-T22AN-X",
            "--mutation-op",
            "append_acceptance_extension",
            "--format",
            "json",
        ]
    )

    receipt = plan_intake.ingest_plan_intent(args, repo_root=tmp_path)
    rows = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_index.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert receipt.status == "accepted"
    assert receipt.source_kind == "markdown_plan_file"
    assert receipt.row_ids == ("MP377-P0-T22AN-X",)
    assert rows[0]["provenance"]["source_kind"] == (
        "PlanIntentIngestion:markdown_plan_file"
    )
    assert rows[0]["mutation_op"] == "append_acceptance_extension"


def test_develop_ingest_plan_packet_uses_packet_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    state_path = (
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json"
    )
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "packet_id": "rev_pkt_9001",
                        "kind": "plan_patch_review",
                        "summary": "Packet-backed plan row",
                        "body": "Patch review body",
                        "expires_at_utc": "2026-05-06T00:00:00Z",
                        "target_ref": "plan:MP-377",
                        "mutation_op": "append_progress_log",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        ["develop", "ingest-plan", "--packet-id", "rev_pkt_9001", "--format", "json"]
    )

    receipt = plan_intake.ingest_plan_intent(args, repo_root=tmp_path)
    rows = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_index.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    receipt_rows = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_ingestion_receipts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert receipt.status == "accepted"
    assert receipt.packet_id == "rev_pkt_9001"
    assert receipt.row_ids == ("PKT-BIND-REV-PKT-9001",)
    assert receipt.source_retention_status == "snapshotted"
    assert receipt.source_integrity_status == "ok"
    assert receipt.source_packet_expires_at_utc == "2026-05-06T00:00:00Z"
    assert receipt_rows[0]["packet_id"] == "rev_pkt_9001"
    assert receipt_rows[0]["source_snapshot_ids"] == list(receipt.source_snapshot_ids)
    assert rows[0]["sourced_from_packets"] == ["rev_pkt_9001"]
    assert rows[0]["work_evidence_ids"][0] == "packet:rev_pkt_9001"
    assert any(
        ref.startswith("plan_source_snapshot:")
        for ref in rows[0]["work_evidence_ids"]
    )
    snapshots = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_source_snapshots.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert snapshots[0]["plan_row_id"] == "PKT-BIND-REV-PKT-9001"
    assert snapshots[0]["source_packet_id"] == "rev_pkt_9001"
    assert snapshots[0]["packet_expires_at_utc"] == "2026-05-06T00:00:00Z"
    assert "Patch review body" in snapshots[0]["source_text"]


def test_develop_ingest_plan_rejects_unowned_chat_plan(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--body",
            "A plan without a PlanRow id or checklist authority.",
            "--source-kind",
            "chat",
            "--source-ref",
            "chat://missing-row",
            "--format",
            "json",
        ]
    )

    receipt = plan_intake.ingest_plan_intent(args, repo_root=tmp_path)

    assert receipt.status == "rejected"
    assert receipt.terminal_status == "rejected"
    assert not (tmp_path / "dev/state/plan_index.jsonl").exists()
    assert (
        tmp_path / "dev/state/plan_ingestion_receipts.jsonl"
    ).read_text(encoding="utf-8")


def test_develop_ingest_plan_missing_row_markdown_names_corrected_shape(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--dry-run",
            "--actor",
            "claude",
            "--body",
            "A prose plan without row authority.",
            "--source-kind",
            "chat",
            "--source-ref",
            "chat://missing-row",
            "--target-ref",
            "plan:MP-377",
            "--format",
            "md",
        ]
    )

    rc = plan_intake.run_ingest_plan(args)

    assert rc == 0
    output = capsys.readouterr().out
    assert "missing_plan_row_or_checklist_authority" in output
    assert "--plan-row-id '<PLAN_ROW_ID>'" in output
    assert "checklist row" in output
    assert "develop ingest-plan --actor claude --plan-row-id" in output


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


def test_develop_orchestration_treats_idle_observer_wait_as_current(
    tmp_path,
    monkeypatch,
) -> None:
    summary_path = tmp_path / "dev/reports/system_picture/latest/summary.json"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(json.dumps({"sections": []}), encoding="utf-8")
    monkeypatch.setattr(
        orchestration_system_picture_module,
        "_current_system_picture_sections_by_id",
        lambda _repo_root: {},
    )
    review_state = {
        "agent_loop_decisions": [
            {
                "actor_id": "codex",
                "actor_role": "dashboard",
                "session_id": "session-1",
                "lifecycle_state": "idle",
                "required_action": "observe_typed_runtime",
                "loop_mode": "typed_event_wait",
                "should_continue_loop": True,
                "safe_to_continue": True,
                "may_mutate": False,
                "proof_state": "satisfied",
                "pending_packet_count": 0,
                "top_blocker": "none",
                "next_loop_command": (
                    "python3 dev/scripts/devctl.py agent-loop --format json"
                ),
            }
        ],
        "packets": [],
    }

    snapshot = orchestration_snapshot(tmp_path, review_state, actor="codex")

    assert snapshot.status == "current"
    assert snapshot.action_required_count == 0
    assert snapshot.signal_count == 0
    assert snapshot.agent_loop_decisions[0].required_action == "observe_typed_runtime"


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
    assert attention.pending_delivery_packet_ids == ("rev_pkt_9999",)
    assert attention.latest_attention_packet_id == "rev_pkt_9999"
    assert attention.required_command == (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_9999 --terminal none --format md"
    )


def test_packet_attention_empty_state_reports_no_pending_attention() -> None:
    attention = packet_attention_from_review_state({"packets": []}, rows=())

    assert attention.attention_required is False
    assert attention.attention_status == "none"
    assert attention.wake_reason == ""
    assert attention.latest_attention_packet_id == ""
    assert attention.latest_finding_packet_id == ""
    assert attention.pending_delivery_packet_ids == ()
    assert attention.pending_actionable_packet_ids == ()
    assert attention.expired_unresolved_count == 0
    assert attention.required_command == ""
    assert attention.summary == (
        "no pending attention; proceed with current slice or /develop "
        "dispatch-agent for next work"
    )


def test_packet_attention_treats_system_notice_as_delivery_wake() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_2757",
                "to_agent": "claude",
                "kind": "system_notice",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(),
        agent="claude",
    )

    assert attention.attention_required is True
    assert attention.attention_status == "wake_required"
    assert attention.wake_reason == "system_notice_pending"
    assert attention.latest_attention_packet_id == "rev_pkt_2757"
    assert attention.latest_finding_packet_id == ""
    assert attention.pending_delivery_packet_ids == ("rev_pkt_2757",)
    assert attention.pending_actionable_packet_ids == ()
    assert attention.required_command.endswith(
        "review-channel --action inbox --target claude --actor claude "
        "--status pending --terminal none --format md"
    )
    selected = select_next_slice((), packet_attention=attention)
    assert selected.slice_id == "packet:rev_pkt_2757"


def test_packet_attention_delivery_still_requires_attention_under_checkpoint() -> None:
    review_state = {
        "attention": {
            "status": "checkpoint_required",
            "recommended_command": (
                "python3 dev/scripts/devctl.py review-channel --action inbox "
                "--target claude --actor claude --status pending "
                "--terminal none --format md"
            ),
        },
        "packets": [
            {
                "packet_id": "rev_pkt_2760",
                "to_agent": "claude",
                "kind": "system_notice",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ],
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(),
        agent="claude",
    )

    assert attention.attention_required is True
    assert attention.attention_status == "checkpoint_required"
    assert attention.wake_reason == "checkpoint_required"
    assert attention.latest_attention_packet_id == "rev_pkt_2760"
    assert attention.pending_delivery_packet_ids == ("rev_pkt_2760",)
    assert attention.pending_actionable_packet_ids == ()


def test_packet_attention_checkpoint_without_packet_is_not_debt_audit() -> None:
    review_state = {
        "attention": {
            "status": "checkpoint_required",
            "recommended_command": "python3 dev/scripts/devctl.py startup-context",
        },
        "packets": [],
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(),
        agent="claude",
    )
    selected = select_next_slice((), packet_attention=attention)

    assert attention.attention_required is True
    assert attention.attention_status == "checkpoint_required"
    assert attention.pending_delivery_packet_ids == ()
    assert attention.summary.startswith("Checkpoint attention requires")
    assert selected.slice_id == "checkpoint-required"


def test_resolve_actor_prefers_single_packet_attention_over_stale_env(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DEVCTL_CALLER_AGENT", "codex")
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_9999",
                "to_agent": "claude",
                "kind": "instruction",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    actor, actor_source = resolve_actor(SimpleNamespace(actor="auto"), review_state)

    assert actor == "claude"
    assert actor_source == "packet_attention"


def test_resolve_actor_prefers_single_system_notice_delivery_over_stale_env(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DEVCTL_CALLER_AGENT", "codex")
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_2757",
                "to_agent": "claude",
                "kind": "system_notice",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    actor, actor_source = resolve_actor(SimpleNamespace(actor="auto"), review_state)

    assert actor == "claude"
    assert actor_source == "packet_attention"


def test_develop_report_auto_actor_uses_single_packet_attention(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DEVCTL_CALLER_AGENT", "codex")
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_9999",
                "to_agent": "claude",
                "kind": "instruction",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }
    monkeypatch.setattr(development_report, "read_plan_rows_jsonl", lambda _path: ())
    monkeypatch.setattr(development_report, "review_state_payload", lambda _repo: review_state)
    monkeypatch.setattr(development_report, "_orchestration_dashboard", lambda _repo: {})
    args = cli.build_parser().parse_args(
        ["develop", "audit-packets", "--max-packets", "20", "--format", "json"]
    )

    report = development_report.build_report(args)

    assert report.inputs.actor == "claude"
    assert report.inputs.actor_source == "packet_attention"
    assert report.packet_attention.pending_actionable_packet_ids == ("rev_pkt_9999",)


def test_resolve_actor_keeps_environment_when_packet_attention_is_ambiguous(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DEVCTL_CALLER_AGENT", "codex")
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_codex",
                "to_agent": "codex",
                "kind": "instruction",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
            {
                "packet_id": "rev_pkt_claude",
                "to_agent": "claude",
                "kind": "instruction",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
        ]
    }

    actor, actor_source = resolve_actor(SimpleNamespace(actor="auto"), review_state)

    assert actor == "codex"
    assert actor_source == "caller_environment"


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
