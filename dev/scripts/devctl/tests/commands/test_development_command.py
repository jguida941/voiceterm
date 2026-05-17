"""Tests for the read-only ``devctl develop`` command."""

from __future__ import annotations

import json
import shlex
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands import development
from dev.scripts.devctl.commands.development import command as development_command
from dev.scripts.devctl.commands.development import (
    baseline_inventory as baseline_inventory_module,
    design_preflight as design_preflight_module,
    orchestration_agent_supervise as orchestration_agent_supervise_module,
    orchestration_system_picture as orchestration_system_picture_module,
)
from dev.scripts.devctl.commands.development import packet_debt as development_packet_debt
from dev.scripts.devctl.commands.development import plan_intake
from dev.scripts.devctl.commands.development import plan_intake_phase0
from dev.scripts.devctl.commands.development import report as development_report
from dev.scripts.devctl.commands.development.operator_command_wrappers import (
    build_operator_command_wrappers,
)
from dev.scripts.devctl.commands.development.actor_resolution import resolve_actor
from dev.scripts.devctl.commands.development.campaign import campaign_report
from dev.scripts.devctl.commands.development.models import (
    DevelopmentPacketAttention,
    DevelopmentPeerMindSnapshot,
)
from dev.scripts.devctl.commands.development.continuation import continuation_signal
from dev.scripts.devctl.commands.development.final_response_gate import (
    enforce_final_response_gate,
)
from dev.scripts.devctl.commands.development.orchestration_models import (
    DevelopmentAgentLoopInput,
    DevelopmentContinuationRequiredSignal,
    DevelopmentOrchestrationSignal,
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
from dev.scripts.devctl.commands.development.plan_intake_decomposition import (
    decomposed_packet_rows,
)
from dev.scripts.devctl.commands.development.status_summary import (
    status_for_report,
    summary_for_action,
)
from dev.scripts.devctl.commands.development.watcher.lease import watcher_lease_status
from dev.scripts.devctl.runtime.master_plan_contract import PlanRow, SDLCStage
from dev.scripts.devctl.runtime.agent_supervise_driver import AgentSuperviseReport
from dev.scripts.devctl.runtime.baseline_authority_inventory import (
    DEFAULT_BASELINE_AUTHORITY_INVENTORY_REL,
    read_baseline_authority_inventory_receipts,
)
from dev.scripts.devctl.runtime.master_plan_store import write_plan_rows_jsonl
from dev.scripts.devctl.runtime.plan_intent_ingestion import (
    plan_intent_receipt_ref,
    typed_action_ref,
)
from dev.scripts.devctl.runtime.development_role_adapters import (
    build_develop_role_adapter_matrix,
)
from dev.scripts.devctl.runtime.development_packet_pressure_models import (
    PacketAttentionIngestionDecision,
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
    assert "--follow-inactivity-timeout-seconds 0" in (
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
    assert "operator_command_wrappers" in payload


def test_operator_command_wrappers_wrap_long_commands() -> None:
    long_command = (
        "python3 dev/scripts/devctl.py develop collaboration-profile "
        "--collaboration-mode agent_sync --role-preset architect --format md"
    )

    wrappers = build_operator_command_wrappers(
        (
            ("short", "python3 dev/scripts/devctl.py develop next --format md"),
            ("long", long_command),
            ("duplicate", long_command),
        )
    )

    assert len(wrappers) == 1
    wrapper = wrappers[0]
    assert wrapper.contract_id == "OperatorCommandWrapper"
    assert wrapper.source == "long"
    assert wrapper.original_command == long_command
    assert wrapper.command_length > wrapper.threshold
    assert " \\\n  " in wrapper.wrapped_command


def test_develop_report_emits_wrappers_for_long_operator_commands(capsys) -> None:
    args = cli.build_parser().parse_args(
        ["develop", "collaboration-profile", "--format", "json"]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    wrappers = payload["operator_command_wrappers"]
    assert wrappers
    assert any(wrapper["command_length"] > 100 for wrapper in wrappers)
    assert all(
        wrapper["contract_id"] == "OperatorCommandWrapper"
        for wrapper in wrappers
    )
    assert any(" \\\n  " in wrapper["wrapped_command"] for wrapper in wrappers)


def test_develop_report_renders_operator_command_wrappers(capsys) -> None:
    args = cli.build_parser().parse_args(
        ["develop", "collaboration-profile", "--format", "md"]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    output = capsys.readouterr().out
    assert "## Operator Command Wrappers" in output
    assert "```sh" in output
    assert " \\\n  " in output


def test_develop_report_passes_proposed_response_text_to_shape_gate(
    monkeypatch, capsys
) -> None:
    captured: dict[str, object] = {}

    def fake_reviewer_response_shape_for_gate(gate, **kwargs):
        captured["gate"] = gate
        captured.update(kwargs)
        return {
            "contract_id": "ReviewerResponseShape",
            "status": "blocked",
            "violations": ["status_marker:markdown_table"],
        }

    monkeypatch.setattr(
        development_report,
        "reviewer_response_shape_for_gate",
        fake_reviewer_response_shape_for_gate,
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "--status",
            "--proposed-response-text",
            "| Status | Detail |\n| --- | --- |\n| holding position | waiting |",
            "--format",
            "json",
        ]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    capsys.readouterr()
    assert captured["proposed_response_text"].startswith("| Status | Detail |")
    assert captured["proposed_response_text_source"] == "cli_arg:proposed_response_text"


def test_next_commands_with_attention_uses_registered_peer_hints() -> None:
    commands = development_report._next_commands_with_attention(
        ("python3 dev/scripts/devctl.py develop launch --dry-run --max-cycles 1",),
        packet_attention=DevelopmentPacketAttention(
            attention_required=True,
            required_command="python3 dev/scripts/devctl.py review-channel --action show --packet-id rev_pkt_1 --terminal none --format md",
            authority_affecting=True,
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


def test_next_commands_routes_communication_packet_as_advisory() -> None:
    commands = development_report._next_commands_with_attention(
        ("python3 dev/scripts/devctl.py develop launch --dry-run --max-cycles 1",),
        packet_attention=DevelopmentPacketAttention(
            attention_required=True,
            required_command="python3 dev/scripts/devctl.py review-channel --action show --packet-id rev_pkt_1 --terminal none --format md",
            authority_affecting=False,
        ),
        peer_minds=(),
    )

    assert commands == (
        "python3 dev/scripts/devctl.py develop launch --dry-run --max-cycles 1",
        "python3 dev/scripts/devctl.py review-channel --action show --packet-id rev_pkt_1 --terminal none --format md",
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


def test_develop_collaboration_profile_accepts_agent_sync_role_counts(
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        development_report,
        "review_state_payload",
        lambda _repo: {
            "packets": [
                {
                    "packet_id": "rev_pkt_target",
                    "status": "acked",
                    "lifecycle_current_state": "acknowledged",
                }
            ],
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "attention_status": "wake_required",
                        "wake_reason": "packet_arrival",
                        "pending_actionable_packet_ids": ["rev_pkt_wake"],
                    }
                ]
            },
            "collaboration": {
                "contract_id": "CollaborationSession",
                "session_id": "cmd-collab-session",
                "status": "active",
                "topology_mode": "paired_remote_control",
                "mutation_owner": "claude",
                "verification_owner": "codex",
                "watcher_owner": "claude",
                "peer_review": {
                    "current_instruction": "full instruction text omitted",
                    "current_instruction_revision": "cmd-rev-1",
                    "open_findings": "0",
                    "implementer_status": "active",
                    "implementer_ack_state": "current",
                },
                "arbitration": {
                    "status": "clear",
                    "owner": "system",
                },
                "ready_gates": [
                    {
                        "gate_id": "runtime_truth",
                        "status": "ready",
                        "summary": "typed state loaded",
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(
        development_report,
        "_review_channel_events",
        lambda _repo: (
            {
                "event_type": "packet_posted",
                "event_id": "evt-wake",
                "timestamp_utc": "2026-05-10T05:50:00Z",
                "to_agent": "claude",
                "target_role": "implementer",
                "target_session_id": "impl-session",
                "packet_id": "rev_pkt_wake",
            },
        ),
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "collaboration-profile",
            "--collaboration-mode",
            "agent_sync",
            "--role-preset",
            "architect",
            "--profile",
            "agent-sync",
            "--provider",
            "codex",
            "--provider",
            "claude",
            "--role-binding",
            "implementer=claude:impl-session",
            "--role-binding",
            "reviewer=codex",
            "--role-binding",
            "architect=codex",
            "--role-count",
            "architect=3",
            "--role-count",
            "researcher=2",
            "--role-count",
            "watcher=1",
            "--role-count",
            "tester=4",
            "--agent-mind-provider",
            "claude",
            "--remote-provider",
            "claude",
            "--source-packet-id",
            "rev_pkt_source",
            "--target-packet-id",
            "rev_pkt_target",
            "--stop-at-packet",
            "rev_pkt_target",
            "--emit-profile-template",
            "--validate-profile",
            "--format",
            "json",
        ]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    profile = payload["collaboration_mode"]["profile"]
    budgets = {row["role"]: row for row in profile["resolved_role_budgets"]}
    assert payload["action"] == "collaboration-profile"
    assert payload["controller_state"] == "read_only_collaboration_profile_validation"
    assert profile["contract_id"] == "AgentCollaborationProfile"
    assert profile["selected_mode_id"] == "agent_sync"
    assert profile["selected_role_preset_id"] == "architect"
    assert profile["providers"] == ["codex", "claude"]
    assert profile["agent_mind_providers"] == ["claude"]
    assert profile["remote_provider"] == "claude"
    assert profile["stop_at_packet_id"] == "rev_pkt_target"
    assert profile["stop_anchor_request"]["stop_at_packet_id"] == "rev_pkt_target"
    assert profile["stop_anchor_request"]["stop_packet_kind"] == "stop_anchor"
    assert profile["collaboration_session"]["contract_id"] == "CollaborationSession"
    assert profile["collaboration_session"]["owners"]["mutation_owner"] == "claude"
    assert profile["collaboration_session"]["peer_review"][
        "current_instruction_revision"
    ] == "cmd-rev-1"
    assert "current_instruction" not in profile["collaboration_session"][
        "peer_review"
    ]
    assert "full instruction text omitted" not in json.dumps(
        profile["collaboration_session"]
    )
    assert profile["advisory_wake_evidence"][0]["latest_relevant_packet_id"] == (
        "rev_pkt_wake"
    )
    assert any(
        "--action inbox --target claude --actor claude" in command
        for command in profile["command_plan"]
    )
    assert any(
        "--actor claude --role implementer --session-id impl-session "
        "--packet rev_pkt_wake" in command
        for command in profile["command_plan"]
    )
    assert profile["coordination_surfaces"] == [
        "AgentMindSlice",
        "PacketInboxState",
        "ReviewPacketState",
        "AgentWorkBoardProjection",
        "AgentLoopDecision",
        "CollaborationSessionState",
    ]
    assert budgets["architect"]["resolved_count"] == 3
    assert budgets["researcher"]["resolved_count"] == 2
    assert budgets["watcher"]["resolved_count"] == 1
    assert budgets["tester"]["resolved_count"] == 4
    assert "never grant mutation" in profile["authority_policy"]
    assert profile["ok"] is True
    assert profile["validation_errors"] == []
    assert "python3 dev/scripts/devctl.py probe-report --format md" in (
        payload["required_checks"]
    )


def test_develop_collaboration_profile_validate_profile_fails_invalid_stop_target(
    capsys,
) -> None:
    args = cli.build_parser().parse_args(
        [
            "develop",
            "collaboration-profile",
            "--collaboration-mode",
            "solo",
            "--role-preset",
            "dashboard",
            "--stop-at-packet",
            "rev_pkt_done",
            "--validate-profile",
            "--format",
            "json",
        ]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    profile = payload["collaboration_mode"]["profile"]
    assert payload["ok"] is False
    assert payload["status"] == "blocked"
    assert profile["ok"] is False
    assert profile["stop_anchor_request"]["status"] == "invalid_stop_anchor_target"
    assert "packet_ack_or_apply" in profile["validation_errors"][0]
    assert all("--kind stop_anchor" not in command for command in profile["command_plan"])


def test_develop_collaboration_profile_compiles_chain_flags(capsys) -> None:
    args = cli.build_parser().parse_args(
        [
            "develop",
            "collaboration-profile",
            "--collaboration-mode",
            "agent_sync",
            "--role-preset",
            "architect",
            "--agents",
            "3",
            "--dogfood",
            "--chain-phase",
            "researcher",
            "--chain-scope",
            "plan:MP-377",
            "--chain-receipt-ref",
            "run:architect",
            "--chain-receipt-ref",
            "dogfood:green",
            "--validate-profile",
            "--format",
            "json",
        ]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    profile = payload["collaboration_mode"]["profile"]
    mode_chain = payload["collaboration_mode"]["mode_chain"]
    budgets = {row["role"]: row for row in profile["resolved_role_budgets"]}
    requests = {row["role"]: row for row in profile["role_count_requests"]}
    assert budgets["architect"]["requested_count"] == 3
    assert requests["architect"]["source"] == "request"
    assert mode_chain["ok"] is True
    assert [phase["role_preset"] for phase in mode_chain["phases"]] == [
        "architect",
        "researcher",
        "tester",
    ]
    assert mode_chain["phases"][1]["scope_inherited_from"] == "phase-1-primary"
    assert mode_chain["receipt_refs"] == ["run:architect", "dogfood:green"]
    assert mode_chain["policy"]["lane_cardinality"]["max_independent_next_derivers"] == 1


def test_develop_collaboration_profile_rejects_chain_cardinality(capsys) -> None:
    args = cli.build_parser().parse_args(
        [
            "develop",
            "collaboration-profile",
            "--collaboration-mode",
            "agent_sync",
            "--role-preset",
            "architect",
            "--chain-phase",
            "researcher",
            "--chain-phase",
            "reviewer",
            "--chain-phase",
            "tester",
            "--chain-phase",
            "watcher",
            "--validate-profile",
            "--format",
            "json",
        ]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    mode_chain = payload["collaboration_mode"]["mode_chain"]
    assert payload["status"] == "blocked"
    assert mode_chain["ok"] is False
    assert "D-DevelopNext cardinality" in mode_chain["validation_errors"][0]


def test_develop_collaboration_profile_chain_cardinality_fails_without_validate(
    capsys,
) -> None:
    args = cli.build_parser().parse_args(
        [
            "develop",
            "collaboration-profile",
            "--collaboration-mode",
            "agent_sync",
            "--role-preset",
            "architect",
            "--chain-phase",
            "researcher",
            "--chain-phase",
            "reviewer",
            "--chain-phase",
            "tester",
            "--chain-phase",
            "watcher",
            "--format",
            "json",
        ]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    mode_chain = payload["collaboration_mode"]["mode_chain"]
    assert payload["ok"] is False
    assert mode_chain["ok"] is False
    assert "D-DevelopNext cardinality" in mode_chain["validation_errors"][0]


def test_develop_campaign_parser_action_is_read_only() -> None:
    args = cli.build_parser().parse_args(["develop", "campaign", "--format", "json"])

    assert args.command == "develop"
    assert args.action == "campaign"
    assert "develop" in cli.READ_ONLY_COMMANDS


def test_develop_campaign_fails_closed_on_mode_drift() -> None:
    now = datetime.now(timezone.utc).isoformat()
    review_state = {
        "effective_reviewer_mode": "single_agent",
        "coordination_state": {
            "coordination_topology": "multi_agent_active",
            "legacy_reviewer_mode": "single_agent",
        },
        "reviewer_runtime": {
            "session_posture": {"interaction_mode": "local_terminal"},
            "remote_control_attachment": {
                "provider": "claude",
                "status": "attached",
                "remote_session_id": "session_remote",
                "last_seen_utc": now,
                "physical_remote_control_confirmed": True,
            },
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "implementer",
                    "session_id": "codex-session",
                    "status": "idle",
                    "mutation_mode": "live_tree",
                }
            ]
        },
        "agent_loop_decisions": [
            {
                "actor_id": "codex",
                "actor_role": "implementer",
                "session_id": "codex-session",
                "may_mutate": True,
                "required_action": "continue_current_execution",
                "proof_state": "satisfied",
                "next_loop_command": "python3 dev/scripts/devctl.py agent-loop --format json --actor codex",
            }
        ],
    }

    report = campaign_report(
        review_state,
        packet_attention=DevelopmentPacketAttention(),
    )

    assert report.remote_control_active is True
    assert report.mode_drift is True
    assert report.fail_closed is True
    assert report.mutation_allowed is False
    assert report.status == "blocked_mode_drift"


def test_develop_campaign_pending_packet_blocks_review_claim() -> None:
    report = campaign_report(
        {
            "reviewer_runtime": {"session_posture": {"interaction_mode": "remote_control"}},
            "coordination_state": {
                "coordination_topology": "multi_agent_active",
                "legacy_reviewer_mode": "active_dual_agent",
            },
        },
        packet_attention=DevelopmentPacketAttention(
            latest_attention_packet_id="rev_pkt_3096",
            required_command=(
                "python3 dev/scripts/devctl.py review-channel --action inbox "
                "--target claude --actor claude --status pending --terminal none --format md"
            ),
        ),
    )

    assert report.status == "blocked_pending_packet_goal"
    assert report.pending_packet_id == "rev_pkt_3096"
    assert report.fail_closed is True
    assert report.claude_next_command.endswith("--format md")


def test_develop_campaign_folds_bypass_retirement_into_lane(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc).isoformat()
    report = campaign_report(
        {
            "governance": {
                "push_enforcement": {
                    "current_head_commit": "abc123",
                    "worktree_dirty": False,
                    "selected_push_report_path": "dev/reports/push/latest_push_report.json",
                    "selected_push_report_status": "post_push_green",
                    "selected_push_report_head_commit": "abc123",
                    "selected_push_report_published_remote": True,
                    "selected_push_report_post_push_green": True,
                    "selected_push_report_matches_current_head": True,
                }
            },
            "reviewer_runtime": {
                "session_posture": {"interaction_mode": "remote_control"},
                "remote_control_attachment": {
                    "provider": "claude",
                    "status": "attached",
                    "remote_session_id": "session_remote",
                    "last_seen_utc": now,
                    "physical_remote_control_confirmed": True,
                },
            },
            "coordination_state": {
                "coordination_topology": "multi_agent_active",
                "legacy_reviewer_mode": "active_dual_agent",
            },
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "codex",
                        "role": "implementer",
                        "session_id": "codex-session",
                        "status": "idle",
                        "mutation_mode": "live_tree",
                    }
                ]
            },
            "agent_loop_decisions": [
                {
                    "actor_id": "codex",
                    "actor_role": "implementer",
                    "session_id": "codex-session",
                    "may_mutate": True,
                    "required_action": "continue_current_execution",
                    "proof_state": "satisfied",
                }
            ],
        },
        packet_attention=DevelopmentPacketAttention(),
        exception_store_path=tmp_path / "missing.jsonl",
    )

    assert report.bypass_posture == "retired_governed_push_green"
    assert report.bypass_publication_transport_retired is True
    assert report.governed_exception_status == "clear"
    assert report.governed_exception_pending_count == 0
    assert report.latest_push_report_status == "post_push_green"
    assert report.latest_push_report_matches_current_head is True
    assert "MP377-P0-EXC-S1" in report.folded_plan_row_ids
    assert "MP377-P0-ROLE-MATRIX-DOGFOOD-S1" in report.folded_plan_row_ids


def test_develop_campaign_fails_closed_on_open_governed_exception(
    tmp_path: Path,
) -> None:
    store_path = tmp_path / "governed_exception_lifecycles.jsonl"
    store_path.write_text(
        json.dumps({"lifecycle_id": "gel:vcs.push:test", "status": "open"}) + "\n",
        encoding="utf-8",
    )

    report = campaign_report(
        {
            "reviewer_runtime": {"session_posture": {"interaction_mode": "remote_control"}},
            "coordination_state": {
                "coordination_topology": "multi_agent_active",
                "legacy_reviewer_mode": "active_dual_agent",
            },
        },
        packet_attention=DevelopmentPacketAttention(),
        exception_store_path=store_path,
    )

    assert report.status == "blocked_governed_exception_debt"
    assert report.current_phase == "governed_exception_repair"
    assert report.fail_closed is True
    assert report.governed_exception_status == "open_exception_debt"
    assert report.governed_exception_pending_count == 1
    assert report.bypass_posture == "blocked_open_governed_exception_debt"
    assert report.bypass_publication_transport_retired is False


def test_develop_campaign_treats_commit_anchor_closure_as_terminal(
    tmp_path: Path,
) -> None:
    store_path = tmp_path / "governed_exception_lifecycles.jsonl"
    store_path.write_text(
        json.dumps(
            {
                "lifecycle_id": "gel:raw-git:test",
                "status": "closed_via_commit_anchor",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = campaign_report(
        {
            "reviewer_runtime": {"session_posture": {"interaction_mode": "remote_control"}},
            "coordination_state": {
                "coordination_topology": "multi_agent_active",
                "legacy_reviewer_mode": "active_dual_agent",
            },
        },
        packet_attention=DevelopmentPacketAttention(),
        exception_store_path=store_path,
    )

    assert report.governed_exception_status == "clear"
    assert report.governed_exception_pending_count == 0


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


def test_continuation_signal_blocks_final_response_when_anchor_is_live() -> None:
    signal = continuation_signal(
        packet_attention=DevelopmentPacketAttention(),
        orchestration=DevelopmentOrchestrationSnapshot(),
        watcher_lease=DevelopmentWatcherLease(status="live"),
        packet_pressure=_packet_pressure(live_total=0, actionable_total=0),
        review_state={
            "packets": [
                {
                    "packet_id": "rev_pkt_anchor",
                    "kind": "continuation_anchor",
                    "to_agent": "codex",
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                    "posted_at": "2026-05-12T03:00:00Z",
                }
            ]
        },
        actor="codex",
        current_action="next",
        fallback_commands=("python3 dev/scripts/devctl.py develop next --format md",),
    )

    assert signal.continuation_required is True
    assert signal.final_response_allowed is False
    assert signal.continuation_anchor_packet_id == "rev_pkt_anchor"
    assert signal.reasons == ("continuation_anchor_active:rev_pkt_anchor",)
    assert signal.next_required_command.endswith("--actor codex --format md")


def test_continuation_signal_ignores_unstructured_stop_anchor_body_scope() -> None:
    signal = continuation_signal(
        packet_attention=DevelopmentPacketAttention(),
        orchestration=DevelopmentOrchestrationSnapshot(
            agent_loop_decisions=(
                DevelopmentAgentLoopInput(
                    actor_id="codex",
                    actor_role="reviewer",
                    session_id="live-session",
                    lifecycle_state="blocked",
                    required_action="resolve_blocker",
                    loop_mode="blocked",
                    should_continue_loop=True,
                    safe_to_continue=False,
                    may_mutate=False,
                    proof_state="satisfied",
                ),
            ),
        ),
        watcher_lease=DevelopmentWatcherLease(status="live"),
        packet_pressure=_packet_pressure(live_total=0, actionable_total=0),
        review_state={
            "packets": [
                {
                    "packet_id": "rev_pkt_anchor",
                    "kind": "continuation_anchor",
                    "to_agent": "codex",
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                    "posted_at": "2026-05-12T03:00:00Z",
                },
                {
                    "packet_id": "rev_pkt_stop",
                    "kind": "stop_anchor",
                    "to_agent": "codex",
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                    "body": "Target session: dead-session",
                    "posted_at": "2026-05-12T03:01:00Z",
                },
            ]
        },
        actor="codex",
        current_action="next",
        fallback_commands=("python3 dev/scripts/devctl.py develop next --format md",),
    )

    assert signal.continuation_required is True
    assert signal.final_response_allowed is False
    assert signal.continuation_anchor_packet_id == "rev_pkt_anchor"
    assert "continuation_anchor_active:rev_pkt_anchor" in signal.reasons


def test_continuation_signal_ignores_dead_session_stop_anchor() -> None:
    signal = continuation_signal(
        packet_attention=DevelopmentPacketAttention(),
        orchestration=DevelopmentOrchestrationSnapshot(
            agent_loop_decisions=(
                DevelopmentAgentLoopInput(
                    actor_id="codex",
                    actor_role="reviewer",
                    session_id="live-session",
                    lifecycle_state="blocked",
                    required_action="resolve_blocker",
                    loop_mode="blocked",
                    should_continue_loop=True,
                    safe_to_continue=False,
                    may_mutate=False,
                    proof_state="satisfied",
                ),
            ),
        ),
        watcher_lease=DevelopmentWatcherLease(status="live"),
        packet_pressure=_packet_pressure(live_total=0, actionable_total=0),
        review_state={
            "packets": [
                {
                    "packet_id": "rev_pkt_anchor",
                    "kind": "continuation_anchor",
                    "to_agent": "codex",
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                    "posted_at": "2026-05-12T03:00:00Z",
                },
                {
                    "packet_id": "rev_pkt_stop",
                    "kind": "stop_anchor",
                    "to_agent": "codex",
                    "target_session_id": "dead-session",
                    "anchor_scope": "session",
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                    "posted_at": "2026-05-12T03:01:00Z",
                },
            ]
        },
        actor="codex",
        current_action="next",
        fallback_commands=("python3 dev/scripts/devctl.py develop next --format md",),
    )

    assert signal.continuation_required is True
    assert signal.final_response_allowed is False
    assert signal.continuation_anchor_packet_id == "rev_pkt_anchor"
    assert "continuation_anchor_active:rev_pkt_anchor" in signal.reasons


def test_continuation_signal_honors_matching_plan_scoped_stop_anchor() -> None:
    signal = continuation_signal(
        packet_attention=DevelopmentPacketAttention(),
        orchestration=DevelopmentOrchestrationSnapshot(
            agent_loop_decisions=(
                DevelopmentAgentLoopInput(
                    actor_id="codex",
                    actor_role="reviewer",
                    session_id="live-session",
                    lifecycle_state="blocked",
                    required_action="resolve_blocker",
                    loop_mode="blocked",
                    should_continue_loop=True,
                    safe_to_continue=False,
                    may_mutate=False,
                    proof_state="satisfied",
                    target_kind="plan",
                    target_ref="plan:MP-377",
                ),
            ),
        ),
        watcher_lease=DevelopmentWatcherLease(status="live"),
        packet_pressure=_packet_pressure(live_total=0, actionable_total=0),
        review_state={
            "packets": [
                {
                    "packet_id": "rev_pkt_anchor",
                    "kind": "continuation_anchor",
                    "to_agent": "codex",
                    "target_kind": "plan",
                    "target_ref": "MP-377",
                    "anchor_scope": "plan",
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                    "posted_at": "2026-05-12T03:00:00Z",
                },
                {
                    "packet_id": "rev_pkt_stop",
                    "kind": "stop_anchor",
                    "to_agent": "codex",
                    "target_kind": "plan",
                    "target_ref": "MP-377",
                    "anchor_scope": "plan",
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                    "posted_at": "2026-05-12T03:01:00Z",
                },
            ]
        },
        actor="codex",
        current_action="next",
        fallback_commands=("python3 dev/scripts/devctl.py develop next --format md",),
    )

    assert signal.continuation_required is False
    assert signal.final_response_allowed is True
    assert signal.reasons == ()


def test_continuation_signal_requires_packet_post_command_for_anchor() -> None:
    signal = continuation_signal(
        packet_attention=DevelopmentPacketAttention(),
        orchestration=DevelopmentOrchestrationSnapshot(
            status="action_required",
            signal_count=1,
            action_required_count=1,
            agent_loop_decisions=(
                DevelopmentAgentLoopInput(
                    actor_id="codex",
                    actor_role="reviewer",
                    session_id="session-1",
                    lifecycle_state="blocked",
                    required_action="post_continuation_anchor",
                    loop_mode="blocked",
                    should_continue_loop=True,
                    safe_to_continue=False,
                    may_mutate=False,
                    proof_state="missing",
                ),
            ),
        ),
        watcher_lease=DevelopmentWatcherLease(status="live"),
        packet_pressure=_packet_pressure(live_total=0, actionable_total=0),
        current_action="next",
        fallback_commands=("python3 dev/scripts/devctl.py develop next --format md",),
    )

    parts = shlex.split(signal.required_packet_command)

    assert signal.required_packet_kind == "continuation_anchor"
    assert signal.required_final_response_action == "post_continuation"
    assert parts[:5] == ["python3", "dev/scripts/devctl.py", "review-channel", "--action", "post"]
    assert "--kind" in parts
    assert parts[parts.index("--kind") + 1] == "continuation_anchor"
    assert "--target-role" in parts
    assert parts[parts.index("--target-role") + 1] == "reviewer"
    assert "--target-role-scoped" in parts
    assert "--target-session-id" in parts
    assert parts[parts.index("--target-session-id") + 1] == "session-1"
    assert signal.next_required_command.endswith("develop next --format md")


def test_develop_audit_packets_report_promotes_packet_decision_command(
    monkeypatch,
) -> None:
    packet_command = (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_3087 --terminal none --format md"
    )
    review_state = {"packets": []}

    def fake_packet_pressure(*_args, **_kwargs):
        return (
            _packet_pressure(live_total=0, actionable_total=1).to_dict(),
            [],
            PacketAttentionIngestionDecision(
                decision="continue_to_goal_review",
                reason_code="expired_unresolved",
                required_action="review_selected_packets",
                fail_closed=False,
                selected_packet_ids=("rev_pkt_3087",),
                next_command=packet_command,
            ).to_dict(),
        )

    monkeypatch.setattr(development_report, "read_plan_rows_jsonl", lambda _path: ())
    monkeypatch.setattr(development_report, "review_state_payload", lambda _repo: review_state)
    monkeypatch.setattr(development_report, "_orchestration_dashboard", lambda _repo: {})
    monkeypatch.setattr(
        development_report,
        "orchestration_snapshot",
        lambda *_args, **_kwargs: DevelopmentOrchestrationSnapshot(
            status="action_required",
            signal_count=1,
            action_required_count=1,
        ),
    )
    monkeypatch.setattr(development_report, "packet_pressure_report", fake_packet_pressure)
    monkeypatch.setattr(
        development_report,
        "watcher_lease_status",
        lambda *_args, **_kwargs: DevelopmentWatcherLease(
            watched_actor="claude",
            status="live",
            next_report_command=(
                "python3 dev/scripts/devctl.py review-channel --action watch"
            ),
        ),
    )
    args = cli.build_parser().parse_args(
        ["develop", "audit-packets", "--actor", "codex", "--format", "json"]
    )

    report = development_report.build_report(args)

    assert report.continuation.next_required_command == packet_command
    assert report.next_step_command == packet_command
    assert report.next_commands[0] == packet_command


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


def test_develop_final_response_gate_returns_nonzero_when_continuation_required(
    monkeypatch,
    capsys,
) -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        status="continue_required",
        final_response_allowed=False,
        final_response_gate_allowed=False,
        required_final_response_action="run_next_command",
        reasons=("orchestration_action_required:1",),
        next_required_command=(
            "python3 dev/scripts/devctl.py agent-loop --format json "
            "--actor codex --role reviewer --session-id s1"
        ),
        stop_policy="stop_only_when_typed_controller_closed",
    )
    report = SimpleNamespace(
        ok=True,
        continuation=continuation,
        final_response_gate=enforce_final_response_gate(continuation),
        to_dict=lambda: {
            "command": "develop",
            "continuation": {
                "continuation_required": True,
                "final_response_allowed": False,
                "final_response_gate_allowed": False,
                "required_final_response_action": "run_next_command",
                "next_required_command": continuation.next_required_command,
            },
        },
    )
    monkeypatch.setattr(development_command, "build_report", lambda _args: report)
    args = cli.build_parser().parse_args(
        ["develop", "next", "--enforce-final-response-gate", "--format", "json"]
    )

    rc = development_command.run(args)

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["continuation"]["final_response_allowed"] is False
    assert payload["continuation"]["final_response_gate_allowed"] is False
    assert payload["continuation"]["next_required_command"].endswith(
        "--session-id s1"
    )


def test_develop_final_response_gate_uses_live_packet_attention(
    monkeypatch,
    capsys,
) -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    packet_attention = DevelopmentPacketAttention(
        attention_required=True,
        wake_reason="task_progress_pending",
        latest_attention_packet_id="rev_pkt_3617",
        required_command=(
            "python3 dev/scripts/devctl.py review-channel --action inbox "
            "--target codex --actor codex --status pending --terminal none --format md"
        ),
    )
    report = SimpleNamespace(
        ok=True,
        continuation=continuation,
        packet_attention=packet_attention,
        orchestration=DevelopmentOrchestrationSnapshot(),
        final_response_gate=enforce_final_response_gate(
            continuation,
            packet_attention=packet_attention,
            orchestration=DevelopmentOrchestrationSnapshot(),
        ),
        to_dict=lambda: {
            "command": "develop",
            "continuation": {
                "continuation_required": False,
                "final_response_allowed": True,
                "final_response_gate_allowed": True,
            },
            "packet_attention": {
                "attention_required": True,
                "latest_attention_packet_id": "rev_pkt_3617",
            },
        },
    )
    monkeypatch.setattr(development_command, "build_report", lambda _args: report)
    args = cli.build_parser().parse_args(
        ["develop", "next", "--enforce-final-response-gate", "--format", "json"]
    )

    rc = development_command.run(args)

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["continuation"]["final_response_allowed"] is True
    assert payload["packet_attention"]["latest_attention_packet_id"] == "rev_pkt_3617"


def test_final_response_gate_requires_next_command_when_controller_is_not_closed() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        status="continue_required",
        final_response_allowed=False,
        final_response_gate_allowed=False,
        required_final_response_action="post_continuation",
        required_packet_kind="continuation_anchor",
        required_packet_command=(
            "python3 dev/scripts/devctl.py review-channel --action post "
            "--from-agent codex --to-agent codex --kind continuation_anchor"
        ),
        reasons=("orchestration_action_required:1",),
        next_required_command=(
            "python3 dev/scripts/devctl.py develop next --actor codex --format md"
        ),
    )

    result = enforce_final_response_gate(continuation)

    assert result.allow_final_response is False
    assert result.action == "post_continuation"
    assert result.required_packet_kind == "continuation_anchor"
    assert "review-channel --action post" in result.required_packet_command
    assert result.next_required_command.endswith("--actor codex --format md")


def test_final_response_gate_denies_live_packet_attention_when_cached_closed() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    packet_attention = DevelopmentPacketAttention(
        attention_required=True,
        wake_reason="task_progress_pending",
        latest_attention_packet_id="rev_pkt_3617",
        required_command=(
            "python3 dev/scripts/devctl.py review-channel --action inbox "
            "--target codex --actor codex --status pending --terminal none --format md"
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        packet_attention=packet_attention,
        orchestration=DevelopmentOrchestrationSnapshot(),
    )

    assert result.allow_final_response is False
    assert result.action == "continue_to_goal"
    assert result.reason == "packet_attention:task_progress_pending"
    assert result.blocking_packet_id == "rev_pkt_3617"
    assert "review-channel --action inbox" in result.next_required_command


def test_final_response_gate_denies_live_agent_loop_when_cached_closed() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="session-1",
                lifecycle_state="blocked",
                required_action="post_continuation_anchor",
                loop_mode="blocked",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="missing",
                next_loop_command=(
                    "python3 dev/scripts/devctl.py develop next "
                    "--actor codex --format md"
                ),
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
    )

    assert result.allow_final_response is False
    assert result.action == "post_continuation"
    assert result.reason == "agent_loop:post_continuation_anchor"
    assert result.required_packet_kind == "continuation_anchor"
    assert result.next_required_command.endswith("--actor codex --format md")


def test_final_response_gate_prefers_agent_loop_remediation_command() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    remediation = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor codex --role reviewer --mode plan --plan MP377-P0-T22AN-AC "
        "--operator-override --override-scope edit-only "
        "--override-reason typed-repair --override-by operator"
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="session-1",
                lifecycle_state="blocked",
                required_action="resolve_blocker",
                loop_mode="blocked",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                next_command=remediation,
                next_loop_command=(
                    "python3 dev/scripts/devctl.py agent-loop --format json "
                    "--actor codex --role reviewer"
                ),
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
    )

    assert result.allow_final_response is False
    assert result.reason == "agent_loop:resolve_blocker"
    assert result.next_required_command == remediation
    assert "--operator-override" in result.next_required_command


def test_final_response_gate_builds_scoped_plan_override_from_next_slice() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    loop_command = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor codex --role reviewer"
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="session-1",
                lifecycle_state="blocked",
                required_action="resolve_blocker",
                loop_mode="blocked",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="guard fail: bundle.tooling",
                next_command=loop_command,
                next_loop_command=loop_command,
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
        next_slice_id="MP377-P0-T22AN-AC",
    )

    assert result.allow_final_response is False
    assert "develop next" in result.next_required_command
    assert "--slice-id MP377-P0-T22AN-AC" in result.next_required_command
    assert "--operator-override" in result.next_required_command
    assert "--override-scope edit-only" in result.next_required_command
    assert "bundle.tooling" in result.next_required_command


def test_final_response_gate_prioritizes_peer_packet_body_before_local_repair() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    local_loop_command = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor codex --role reviewer --session-id codex-session"
    )
    peer_packet_command = (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_peer --actor claude --terminal none --format md "
        "--target-role implementer --target-session-id claude-session"
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="codex-session",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="observer_wait",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="startup authority: import_index_atomicity",
                next_command=local_loop_command,
                next_loop_command=local_loop_command,
            ),
            DevelopmentAgentLoopInput(
                actor_id="claude",
                actor_role="implementer",
                session_id="claude-session",
                lifecycle_state="needs_attention",
                required_action="open_packet_body",
                loop_mode="continue_to_goal",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="missing",
                active_packet_id="rev_pkt_peer",
                attention_packet_id="rev_pkt_peer",
                next_command=peer_packet_command,
                next_loop_command=(
                    "python3 dev/scripts/devctl.py agent-loop --format json "
                    "--actor claude --role implementer --session-id claude-session"
                ),
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
        next_slice_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
    )

    assert result.allow_final_response is False
    assert result.reason == "agent_loop:open_packet_body"
    assert result.blocking_packet_id == "rev_pkt_peer"
    assert result.next_required_command == peer_packet_command
    assert "--operator-override" not in result.next_required_command


def test_final_response_gate_reports_packet_body_command_packet_as_blocker() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    peer_packet_command = (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_command --actor claude --terminal none --format md "
        "--target-role implementer --target-session-id claude-session"
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="claude",
                actor_role="implementer",
                session_id="claude-session",
                lifecycle_state="needs_attention",
                required_action="open_packet_body",
                loop_mode="continue_to_goal",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="missing",
                active_packet_id="rev_pkt_attention",
                attention_packet_id="rev_pkt_attention",
                next_command=peer_packet_command,
                next_loop_command=(
                    "python3 dev/scripts/devctl.py agent-loop --format json "
                    "--actor claude --role implementer --session-id claude-session"
                ),
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
    )

    assert result.reason == "agent_loop:open_packet_body"
    assert result.blocking_packet_id == "rev_pkt_command"
    assert result.next_required_command == peer_packet_command


def test_final_response_gate_prioritizes_packet_body_before_peer_continue_loop() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    dashboard_loop = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor claude --role dashboard --packet rev_pkt_dashboard"
    )
    peer_packet_command = (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_body --actor claude --terminal none --format md "
        "--target-role implementer --target-session-id claude-session"
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="claude",
                actor_role="",
                session_id="",
                lifecycle_state="needs_attention",
                required_action="continue_to_goal",
                loop_mode="continue_to_goal",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                pending_packet_count=15,
                active_packet_id="rev_pkt_dashboard",
                attention_packet_id="rev_pkt_dashboard",
                next_command=dashboard_loop,
                next_loop_command=dashboard_loop,
            ),
            DevelopmentAgentLoopInput(
                actor_id="claude",
                actor_role="implementer",
                session_id="claude-session",
                lifecycle_state="needs_attention",
                required_action="open_packet_body",
                loop_mode="run_or_report_blocker",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="missing",
                active_packet_id="rev_pkt_body",
                attention_packet_id="rev_pkt_body",
                next_command=peer_packet_command,
                next_loop_command=(
                    "python3 dev/scripts/devctl.py agent-loop --format json "
                    "--actor claude --role implementer --session-id claude-session"
                ),
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
        next_slice_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
    )

    assert result.allow_final_response is False
    assert result.reason == "agent_loop:open_packet_body"
    assert result.blocking_packet_id == "rev_pkt_body"
    assert result.next_required_command == peer_packet_command


def test_final_response_gate_prefers_mutation_owner_startup_repair() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    observer_loop_command = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor codex --role reviewer --session-id codex-session"
    )
    mutation_repair = 'python3 dev/scripts/devctl.py commit -m "checkpoint"'
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="codex-session",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="observer_wait",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="startup authority: import_index_atomicity",
                next_command=observer_loop_command,
                next_loop_command=observer_loop_command,
            ),
            DevelopmentAgentLoopInput(
                actor_id="claude",
                actor_role="implementer",
                session_id="claude-session",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="startup_repair",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=True,
                proof_state="satisfied",
                top_blocker="startup authority: import_index_atomicity",
                next_command=mutation_repair,
                next_loop_command=(
                    "python3 dev/scripts/devctl.py agent-loop --format json "
                    "--actor claude --role implementer --session-id claude-session"
                ),
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
        next_slice_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
    )

    assert result.allow_final_response is False
    assert result.reason == "agent_loop:repair_startup_authority"
    assert result.next_required_command == mutation_repair
    assert "--operator-override" not in result.next_required_command


def test_final_response_gate_prefers_scoped_repair_over_status_probe() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    observer_loop_command = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor codex --role reviewer --session-id codex-session"
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="codex-session",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="observer_wait",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="startup authority: dirty_and_untracked_budget_exceeded",
                next_command=observer_loop_command,
                next_loop_command=observer_loop_command,
            ),
            DevelopmentAgentLoopInput(
                actor_id="claude",
                actor_role="implementer",
                session_id="claude-session",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="startup_repair",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=True,
                proof_state="satisfied",
                top_blocker="startup authority: dirty_and_untracked_budget_exceeded",
                next_command=(
                    "python3 dev/scripts/devctl.py review-channel --action status "
                    "--terminal none --format json"
                ),
                next_loop_command=(
                    "python3 dev/scripts/devctl.py agent-loop --format json "
                    "--actor claude --role implementer --session-id claude-session"
                ),
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
        next_slice_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
    )

    assert result.allow_final_response is False
    assert result.reason == "agent_loop:repair_startup_authority"
    assert "--actor codex" in result.next_required_command
    assert "--operator-override" in result.next_required_command
    assert "review-channel --action status" not in result.next_required_command


def test_final_response_gate_prefers_scoped_repair_over_prose_peer_repair() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    observer_loop_command = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor codex --role reviewer --session-id codex-session"
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="codex-session",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="observer_wait",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="startup authority: import_index_atomicity",
                next_command=observer_loop_command,
                next_loop_command=observer_loop_command,
            ),
            DevelopmentAgentLoopInput(
                actor_id="claude",
                actor_role="implementer",
                session_id="claude-session",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="startup_repair",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=True,
                proof_state="satisfied",
                top_blocker="startup authority: import_index_atomicity",
                next_command=(
                    "stage missing imported file(s), then rerun "
                    "python3 dev/scripts/devctl.py startup-context --format summary"
                ),
                next_loop_command=(
                    "python3 dev/scripts/devctl.py agent-loop --format json "
                    "--actor claude --role implementer --session-id claude-session"
                ),
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
        next_slice_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
    )

    assert result.allow_final_response is False
    assert result.reason == "agent_loop:repair_startup_authority"
    assert "--actor codex" in result.next_required_command
    assert "--operator-override" in result.next_required_command
    assert "stage missing imported file" not in result.next_required_command


def test_final_response_gate_prefers_scoped_repair_over_raw_git_peer_repair() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    observer_loop_command = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor codex --role reviewer --session-id codex-session"
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="codex-session",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="observer_wait",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="startup authority: import_index_atomicity",
                next_command=observer_loop_command,
                next_loop_command=observer_loop_command,
            ),
            DevelopmentAgentLoopInput(
                actor_id="claude",
                actor_role="implementer",
                session_id="claude-session",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="startup_repair",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=True,
                proof_state="satisfied",
                top_blocker="startup authority: import_index_atomicity",
                next_command='git commit -m "checkpoint"',
                next_loop_command=(
                    "python3 dev/scripts/devctl.py agent-loop --format json "
                    "--actor claude --role implementer --session-id claude-session"
                ),
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
        next_slice_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
    )

    assert result.allow_final_response is False
    assert result.reason == "agent_loop:repair_startup_authority"
    assert "--actor codex" in result.next_required_command
    assert "--operator-override" in result.next_required_command
    assert "git commit" not in result.next_required_command
    assert result.gate_failure is not None
    assert result.gate_failure.contract_id == "TypedGateFailure"
    assert result.gate_failure.bypass_invocation == result.next_required_command


def test_final_response_gate_surfaces_plan_override_for_waiting_loop() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        final_response_allowed=False,
        final_response_gate_allowed=False,
        next_required_command=(
            "python3 dev/scripts/devctl.py agent-loop --format json "
            "--actor codex --role implementer"
        ),
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="implementer",
                session_id="session-1",
                lifecycle_state="waiting",
                required_action="wait_for_scoped_packet",
                loop_mode="typed_event_wait",
                should_continue_loop=True,
                safe_to_continue=True,
                may_mutate=False,
                proof_state="satisfied",
                why_not_done="no scoped active packet",
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
        next_slice_id="PKT-BIND-REV-PKT-3140",
    )

    assert result.allow_final_response is False
    assert result.reason == "agent_loop:wait_for_scoped_packet"
    assert "--operator-override" in result.next_required_command
    assert "--slice-id PKT-BIND-REV-PKT-3140" in result.next_required_command
    assert result.gate_failure is not None
    assert result.gate_failure.gate_id == "agent_loop.wait_for_scoped_packet"
    assert result.gate_failure.bypass_receipt_kind == "BypassReceipt"
    assert result.gate_failure.bypass_invocation == result.next_required_command


def test_final_response_gate_does_not_repeat_active_edit_only_override() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    loop_command = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor codex --role reviewer --mode packet --packet rev_pkt_1 "
        "--operator-override --override-scope edit-only "
        "--override-reason typed-repair --override-by operator"
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="session-1",
                lifecycle_state="blocked",
                required_action="repair_startup_authority",
                loop_mode="operator_override_edit",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=True,
                proof_state="satisfied",
                active_packet_id="rev_pkt_1",
                attention_packet_id="rev_pkt_1",
                top_blocker="startup authority: import_index_atomicity",
                next_command=loop_command,
                next_loop_command=loop_command,
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
        next_slice_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
    )

    assert result.allow_final_response is False
    assert result.action == "continue_to_goal"
    assert result.reason == "agent_loop:repair_startup_authority"
    assert result.blocking_packet_id == "rev_pkt_1"
    assert result.next_required_command == ""
    assert result.user_action == "Continue scoped implementation edits"
    assert "operator override" in result.why_not_done.lower()


def test_report_next_step_command_does_not_fall_back_after_active_override() -> None:
    final_gate = SimpleNamespace(
        allow_final_response=False,
        action="continue_to_goal",
        next_required_command="",
        user_action="Continue scoped implementation edits",
        why_not_done=(
            "Edit-only operator override is active; continue implementation edits."
        ),
    )
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        final_response_allowed=False,
        next_required_command=(
            "python3 dev/scripts/devctl.py develop next --actor codex --format md"
        ),
    )

    assert (
        development_report._next_step_command_for_report(
            final_response_gate=final_gate,
            continuation=continuation,
            packet_attention_required=False,
            packet_attention_command="",
            next_commands=("python3 dev/scripts/devctl.py develop launch --dry-run",),
        )
        == ""
    )


def test_final_response_gate_denies_dict_packet_attention_fields() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )

    result = enforce_final_response_gate(
        continuation,
        packet_attention={
            "pending_packet_count": 1,
            "wake_required": True,
            "latest_attention_packet_id": "rev_pkt_3617",
            "required_command": (
                "python3 dev/scripts/devctl.py review-channel --action inbox "
                "--target codex --actor codex --status pending --terminal none --format md"
            ),
        },
    )

    assert result.allow_final_response is False
    assert result.source == "packet_attention"
    assert result.blocking_packet_id == "rev_pkt_3617"
    assert "review-channel --action inbox" in result.next_required_command


def test_final_response_gate_synthesizes_packet_attention_next_command() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )

    result = enforce_final_response_gate(
        continuation,
        packet_attention=DevelopmentPacketAttention(
            attention_required=True,
            agent="codex",
            wake_reason="task_progress_pending",
            latest_attention_packet_id="rev_pkt_3617",
        ),
    )

    assert result.allow_final_response is False
    assert result.next_required_command == (
        "python3 dev/scripts/devctl.py develop next --actor codex --format md"
    )


def test_final_response_gate_synthesizes_agent_loop_next_command() -> None:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=False,
        final_response_allowed=True,
        final_response_gate_allowed=True,
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="session-1",
                lifecycle_state="blocked",
                required_action="run_next_command",
                loop_mode="blocked",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="missing",
            ),
        ),
    )

    result = enforce_final_response_gate(
        continuation,
        orchestration=orchestration,
    )

    assert result.allow_final_response is False
    assert result.next_required_command == (
        "python3 dev/scripts/devctl.py develop next --actor codex --format md"
    )


def test_final_response_gate_default_continuation_fails_closed() -> None:
    result = enforce_final_response_gate(DevelopmentContinuationRequiredSignal())

    assert result.allow_final_response is False
    assert result.reason == "continuation_signal_missing"
    assert result.action == "run_next_command"
    assert result.next_required_command == (
        "python3 dev/scripts/devctl.py develop next --format md"
    )


def test_develop_report_embeds_materialized_final_response_gate() -> None:
    args = cli.build_parser().parse_args(["develop", "next", "--format", "json"])

    report = development_report.build_report(args)
    payload = report.to_dict()

    assert "final_response_gate" in payload
    assert payload["final_response_gate"]["contract_id"] == "FinalResponseGateResult"
    assert payload["final_response_gate"]["stop_policy"] == (
        "stop_only_when_typed_controller_closed"
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
    assert receipt["action_id"].startswith("plan-intent-action-")
    assert rows[0]["row_id"] == "MP377-P0-T22AN-W"
    assert rows[0]["provenance"]["source_kind"] == "PlanIntentIngestion:chat"
    assert receipt["schema_limit_warning"]
    assert receipt["repo_state_fingerprint"]["worktree_identity"] == str(
        tmp_path.resolve()
    )
    assert receipt["derived_state_invalidated"] is True
    assert receipt["derived_state_invalidation"]["source"] == "plan_ingestion_event"
    assert receipt["derived_state_invalidation"]["producer_id"] == (
        "develop.plan_ingestion"
    )
    assert "develop.next" in receipt["derived_state_invalidation"][
        "invalidated_consumers"
    ]
    assert receipt["receipt_coverage_inventory"]["total_mp377_rows"] == 0
    assert receipt["composition_disposition_matrix"][0]["row_id"] == "MP377-P0-T22AN-W"
    assert any(
        ref.startswith("plan_source_snapshot:")
        for ref in rows[0]["work_evidence_ids"]
    )
    assert plan_intent_receipt_ref(receipt["receipt_id"]) in rows[0]["work_evidence_ids"]
    assert typed_action_ref(receipt["action_id"]) in rows[0]["work_evidence_ids"]
    snapshots = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_source_snapshots.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert snapshots[0]["plan_row_id"] == "MP377-P0-T22AN-W"
    assert snapshots[0]["receipt_id"] == receipt["receipt_id"]
    assert snapshots[0]["action_id"] == receipt["action_id"]
    assert snapshots[0]["composition_disposition"] == "new_closure_row"
    assert snapshots[0]["schema_limit_warning"]
    assert snapshots[0]["source_text"] == (
        "Any agent-authored plan must reach typed plan authority."
    )
    assert receipt["source_snapshot_ids"] == [snapshots[0]["snapshot_id"]]
    assert receipt["source_retention_status"] == "snapshotted"
    assert receipt["source_integrity_status"] == "ok"
    assert receipt_rows[0]["row_ids"] == ["MP377-P0-T22AN-W"]
    assert receipt_rows[0]["derived_state_invalidated"] is True


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


def test_develop_ingest_plan_file_accepts_rows_to_ingest_section(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    source = tmp_path / "plan.md"
    source.write_text(
        "\n".join(
            (
                "# MP-377 Consolidation Repair Plan",
                "",
                "Required existing-row composition anchors:",
                "",
                "- `MP377-P0-EXC-S1`, `MP377-P0-CHECKPOINT-AUTOMATION-S1`, `MP377-P0-DEVELOP-NEXT-DECISION-SCHEMA-S1`, `MP377-P0-GUARD-CADENCE-S1`",
                "",
                "Required packet-binding citations:",
                "",
                "- `PKT-BIND-REV-PKT-3505`",
                "",
                "Rows to ingest from this plan:",
                "",
                "- `MP377-CONSOLIDATION-PLAN-INGEST-S1` Ingest the consolidated repair plan.",
                "- `MP377-FINAL-AUDIT-MT-COMPOSITION-S1` Fold the audit amendments into typed authority.",
                "",
                "Existing today:",
                "",
                "```bash",
                "python3 dev/scripts/devctl.py develop ingest-plan --dry-run --source <plan> --target-ref plan:MP-377 --format json",
                "```",
                "",
                "Aspirational until implemented by the named phases:",
                "",
                "```bash",
                "python3 dev/scripts/checks/check_plan_composition_disposition.py --format json",
                "```",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--source",
            str(source),
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
    snapshots = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_source_snapshots.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert receipt.status == "accepted"
    assert receipt.row_ids == (
        "MP377-CONSOLIDATION-PLAN-INGEST-S1",
        "MP377-FINAL-AUDIT-MT-COMPOSITION-S1",
    )
    assert receipt.source_kind == "markdown_plan_file"
    assert receipt.repo_state_fingerprint.worktree_identity == str(tmp_path.resolve())
    assert receipt.receipt_coverage_inventory.total_mp377_rows == 0
    assert receipt.composition_disposition_matrix[0].row_id == (
        "MP377-CONSOLIDATION-PLAN-INGEST-S1"
    )
    assert receipt.composition_disposition_matrix[1].disposition == (
        "amends_existing_owner_row"
    )
    assert receipt.command_manifest_proofs[0].proof_status == "registered_command"
    assert receipt.command_manifest_proofs[1].proof_status == "planned"
    assert receipt.guard_maturity_records[0].maturity == "planned"
    assert {
        row["row_id"] for row in rows
    } == {
        "MP377-CONSOLIDATION-PLAN-INGEST-S1",
        "MP377-FINAL-AUDIT-MT-COMPOSITION-S1",
    }
    assert snapshots[0]["existing_owner_row_refs"]
    assert snapshots[0]["packet_binding_refs"] == ["PKT-BIND-REV-PKT-3505"]
    assert snapshots[1]["composition_disposition"] == "amends_existing_owner_row"


def test_develop_ingest_plan_marks_existing_rows_as_amendments(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    store = tmp_path / "dev/state/plan_index.jsonl"
    write_plan_rows_jsonl(
        store,
        (
            PlanRow(
                row_id="MP377-STALE-EVIDENCE-POLICY-GUARD-S1",
                title="Existing stale evidence policy row",
                status="queued",
                sdlc_stage=SDLCStage.SPEC,
                target_ref="plan:MP-377",
            ),
        ),
    )
    source = tmp_path / "codesmell-plan.md"
    source.write_text(
        "\n".join(
            (
                "# MP-377 Codesmell Intake",
                "",
                "Required packet-binding citations:",
                "",
                "- `PKT-BIND-REV-PKT-3596`",
                "",
                "Rows to ingest from this plan:",
                "",
                "- `MP377-STALE-EVIDENCE-POLICY-GUARD-S1` Amend stale projection race evidence.",
                "- `MP377-CHECK-CLI-TEST-PARITY-S1` Add CLI/test parity closure.",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--dry-run",
            "--source",
            str(source),
            "--target-ref",
            "plan:MP-377",
            "--format",
            "json",
        ]
    )

    receipt = plan_intake.ingest_plan_intent(args, repo_root=tmp_path)
    matrix = {
        entry.row_id: entry for entry in receipt.composition_disposition_matrix
    }

    assert receipt.status == "preview"
    assert (
        matrix["MP377-STALE-EVIDENCE-POLICY-GUARD-S1"].disposition
        == "amends_existing_owner_row"
    )
    assert matrix["MP377-STALE-EVIDENCE-POLICY-GUARD-S1"].existing_owner_row_refs == (
        "MP377-STALE-EVIDENCE-POLICY-GUARD-S1",
    )
    assert (
        matrix["MP377-CHECK-CLI-TEST-PARITY-S1"].disposition
        == "new_closure_row"
    )


def test_phase0_validation_rejects_existing_row_as_new_closure() -> None:
    rows = (
        PlanRow(
            row_id="MP377-STALE-EVIDENCE-POLICY-GUARD-S1",
            title="Stale evidence policy",
            status="queued",
            sdlc_stage=SDLCStage.SPEC,
            target_ref="plan:MP-377",
        ),
    )
    metadata = plan_intake_phase0.Phase0IntakeMetadata(
        composition_disposition_matrix=(
            plan_intake_phase0.PlanCompositionDispositionEntry(
                row_id="MP377-STALE-EVIDENCE-POLICY-GUARD-S1",
                disposition="new_closure_row",
                owning_mp_family="MP-377",
                existing_owner_row_refs=(
                    "MP377-STALE-EVIDENCE-POLICY-GUARD-S1",
                ),
            ),
        ),
        command_manifest_proofs=(),
        guard_maturity_records=(),
        repo_state_fingerprint=plan_intake_phase0.RepoStateFingerprint(),
        receipt_coverage_inventory=plan_intake_phase0.ReceiptCoverageInventory(),
    )

    try:
        plan_intake_phase0.validate_phase0_metadata(
            rows=rows,
            metadata=metadata,
            sections=plan_intake_phase0.ParsedPlanAuthoritySections(
                rows_section_present=True,
                rows_to_ingest=(
                    plan_intake_phase0.ParsedPlanAuthorityRow(
                        row_id="MP377-STALE-EVIDENCE-POLICY-GUARD-S1",
                        title="Stale evidence policy",
                        source_line=1,
                    ),
                ),
            ),
            existing_rows=rows,
        )
    except plan_intake_phase0.PlanIntakePhase0ValidationError as exc:
        assert str(exc) == "phase0_existing_owner_row_marked_new_closure"
    else:
        raise AssertionError("existing plan row was allowed as new_closure_row")


def test_develop_ingest_plan_rolls_back_rows_when_snapshot_write_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    source = tmp_path / "plan.md"
    source.write_text(
        "# MP-377\n\n- [ ] `MP377-P0-TXN-S1` Transaction rollback proof row\n",
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--source",
            str(source),
            "--target-ref",
            "plan:MP-377",
            "--format",
            "json",
        ]
    )

    def _raise_snapshot_failure(*_args, **_kwargs):
        raise RuntimeError("simulated snapshot write failure")

    monkeypatch.setattr(plan_intake, "write_source_snapshots", _raise_snapshot_failure)

    receipt = plan_intake.ingest_plan_intent(args, repo_root=tmp_path)
    receipt_rows = [
        json.loads(line)
        for line in (
            tmp_path / "dev/state/plan_ingestion_receipts.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert receipt.status == "rejected"
    assert receipt.reason == "plan_ingestion_rolled_back_after_source_snapshot_failure"
    assert receipt.store_statuses == ("rolled_back:inserted",)
    assert receipt.row_ids == ("MP377-P0-TXN-S1",)
    assert not (tmp_path / "dev/state/plan_index.jsonl").exists()
    assert not (tmp_path / "dev/state/plan_source_snapshots.jsonl").exists()
    assert receipt_rows[-1]["reason"] == receipt.reason
    assert receipt_rows[-1]["store_statuses"] == list(receipt.store_statuses)


def test_develop_ingest_plan_rolls_back_existing_row_when_snapshot_write_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    store = tmp_path / "dev/state/plan_index.jsonl"
    write_plan_rows_jsonl(
        store,
        (
            PlanRow(
                row_id="MP377-P0-TXN-S2",
                title="Original transaction row",
                status="queued",
                sdlc_stage=SDLCStage.SPEC,
                target_ref="plan:MP-377",
            ),
        ),
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--plan-row-id",
            "MP377-P0-TXN-S2",
            "--title",
            "Updated transaction row",
            "--body",
            "This update must roll back if the snapshot stage fails.",
            "--source-kind",
            "chat",
            "--source-ref",
            "chat://rollback-existing",
            "--target-ref",
            "plan:MP-377",
            "--format",
            "json",
        ]
    )

    def _raise_snapshot_failure(*_args, **_kwargs):
        raise RuntimeError("simulated snapshot write failure")

    monkeypatch.setattr(plan_intake, "write_source_snapshots", _raise_snapshot_failure)

    receipt = plan_intake.ingest_plan_intent(args, repo_root=tmp_path)
    rows = [
        json.loads(line)
        for line in store.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert receipt.status == "rejected"
    assert receipt.reason == "plan_ingestion_rolled_back_after_source_snapshot_failure"
    assert receipt.store_statuses == ("rolled_back:updated",)
    assert rows[0]["row_id"] == "MP377-P0-TXN-S2"
    assert rows[0]["title"] == "Original transaction row"
    assert rows[0]["status"] == "queued"
    assert rows[0]["sdlc_stage"] == "spec"
    assert not (tmp_path / "dev/state/plan_source_snapshots.jsonl").exists()


def test_phase0_supported_state_vocab_matches_plan() -> None:
    assert plan_intake_phase0.SUPPORTED_PLAN_DISPOSITIONS == {
        "new_closure_row",
        "amends_existing_owner_row",
        "existing_owner_citation_only",
        "adjacent_mp_dependency",
        "portability_blocker",
        "security_blocker",
        "aspirational_until_implemented",
        "deferred_followup",
        "do_not_ingest",
    }
    assert plan_intake_phase0.SUPPORTED_GUARD_MATURITY_STATES == {
        "planned",
        "implemented_unregistered",
        "registered_advisory",
        "registered_blocking",
        "retired",
    }


def test_develop_baseline_inventory_writes_typed_receipt(tmp_path: Path) -> None:
    writer_path = tmp_path / "dev/scripts/devctl/runtime/demo_store.py"
    writer_path.parent.mkdir(parents=True, exist_ok=True)
    writer_path.write_text(
        "\n".join(
            (
                "from pathlib import Path",
                "",
                "def write_demo(path: Path) -> None:",
                "    path.write_text('ok', encoding='utf-8')",
                "",
                "def read_demo(path: Path) -> str:",
                "    return path.read_text(encoding='utf-8')",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "dev/state").mkdir(parents=True, exist_ok=True)
    (tmp_path / "dev/state/plan_index.jsonl").write_text("", encoding="utf-8")
    workflow_path = tmp_path / ".github/workflows/ci.yml"
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text("name: ci\n", encoding="utf-8")

    args = cli.build_parser().parse_args(
        [
            "develop",
            "baseline-inventory",
            "--format",
            "json",
        ]
    )

    exit_code = baseline_inventory_module.run_baseline_inventory(args, repo_root=tmp_path)
    receipts = read_baseline_authority_inventory_receipts(
        tmp_path / DEFAULT_BASELINE_AUTHORITY_INVENTORY_REL
    )

    assert exit_code == 0
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt.contract_id == "BaselineAuthorityInventoryReceipt"
    assert receipt.status == "accepted"
    assert "dev/state/plan_index.jsonl" in receipt.state_files
    assert ".github/workflows/ci.yml" in receipt.workflow_surfaces
    assert any(site.path == "dev/scripts/devctl/runtime/demo_store.py" for site in receipt.direct_write_sites)
    assert any(site.path == "dev/scripts/devctl/runtime/demo_store.py" for site in receipt.direct_read_sites)
    assert "build_system_catalog()" in receipt.search_patterns


def test_develop_ingest_plan_rejects_unparseable_rows_to_ingest_section(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    source = tmp_path / "plan.md"
    source.write_text(
        "\n".join(
            (
                "# MP-377 Consolidation Repair Plan",
                "",
                "Rows to ingest from this plan:",
                "",
                "- `MP377-CONSOLIDATION-PLAN-INGEST-S1` Ingest the consolidated repair plan.",
                "- not-a-typed-row This bullet must fail instead of silently disappearing.",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--dry-run",
            "--source",
            str(source),
            "--target-ref",
            "plan:MP-377",
            "--format",
            "json",
        ]
    )

    receipt = plan_intake.ingest_plan_intent(args, repo_root=tmp_path)

    assert receipt.status == "rejected"
    assert receipt.terminal_status == "rejected"
    assert receipt.reason == "rows_to_ingest_contains_unparseable_bullets"
    assert not (tmp_path / "dev/state/plan_index.jsonl").exists()


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
    assert receipt.action_id.startswith("plan-intent-action-")
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
    assert plan_intent_receipt_ref(receipt.receipt_id) in rows[0]["work_evidence_ids"]
    assert typed_action_ref(receipt.action_id) in rows[0]["work_evidence_ids"]
    snapshots = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_source_snapshots.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert snapshots[0]["plan_row_id"] == "PKT-BIND-REV-PKT-9001"
    assert snapshots[0]["receipt_id"] == receipt.receipt_id
    assert snapshots[0]["action_id"] == receipt.action_id
    assert snapshots[0]["source_packet_id"] == "rev_pkt_9001"
    assert snapshots[0]["packet_expires_at_utc"] == "2026-05-06T00:00:00Z"
    assert "Patch review body" in snapshots[0]["source_text"]


def test_develop_ingest_plan_packet_materializes_mp_new_rows(
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
                        "packet_id": "rev_pkt_9101",
                        "kind": "task_progress",
                        "summary": "Meta-capture decomposer request",
                        "body": "\n".join(
                            [
                                "MP-NEW-P208 verdict is context, not a row.",
                                "MP-NEW-P210-SYSTEM-PICTURE-EXTENSION family is context, not a closure row.",
                                "For rev_pkt_4106 -> MP-NEW-P204-S1..S3",
                                "- `MP-NEW-P206-REPO-SEMANTIC-CLASSIFIER-S1` - Repo semantic classifier",
                                '{ "slice_id": "MP-NEW-P209-SESSION-PROBLEM-LOGGER-S1",',
                                '  "title": "SessionProblemLog contract + StrEnum + jsonl storage" }',
                            ]
                        ),
                        "target_ref": "plan:MP-377",
                        "requested_action": "review_only",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        ["develop", "ingest-plan", "--packet-id", "rev_pkt_9101", "--format", "json"]
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
    assert receipt.row_ids == (
        "MP-NEW-P204-S1",
        "MP-NEW-P204-S2",
        "MP-NEW-P204-S3",
        "MP-NEW-P206-REPO-SEMANTIC-CLASSIFIER-S1",
        "MP-NEW-P209-SESSION-PROBLEM-LOGGER-S1",
    )
    assert [row["row_id"] for row in rows] == list(receipt.row_ids)
    assert all(row["sourced_from_packets"] == ["rev_pkt_9101"] for row in rows)
    assert rows[-1]["title"] == "SessionProblemLog contract + StrEnum + jsonl storage"
    assert not any(row["row_id"].startswith("PKT-BIND-") for row in rows)


def test_decomposed_packet_rows_range_titles_strip_matched_range_token() -> None:
    rows = decomposed_packet_rows(
        "\n".join(
            [
                "- MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1..S3 - Extend system picture graph",
                "For rev_pkt_4106 -> MP-NEW-P204-S1..S2",
            ]
        )
    )
    rows_by_id = {row.row_id: row for row in rows}

    assert tuple(rows_by_id) == (
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1",
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S2",
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S3",
        "MP-NEW-P204-S1",
        "MP-NEW-P204-S2",
    )
    for row_id in (
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1",
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S2",
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S3",
    ):
        assert rows_by_id[row_id].title == "Extend system picture graph"
    for row in rows:
        assert not row.title.startswith("..")
        assert "S1..S" not in row.title
    assert rows_by_id["MP-NEW-P204-S1"].title == (
        "Materialize packet closure row MP-NEW-P204-S1"
    )


def test_develop_ingest_plan_packet_falls_back_to_event_log(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    events_path = tmp_path / "dev/reports/review_channel/events/trace.ndjson"
    events_path.parent.mkdir(parents=True)
    events_path.write_text(
        json.dumps(
            {
                "event_id": "rev_evt_9002",
                "event_type": "packet_posted",
                "packet_id": "rev_pkt_9002",
                "trace_id": "trace_9002",
                "from_agent": "reviewer",
                "to_agent": "codex",
                "kind": "plan_patch_review",
                "status": "pending",
                "summary": "Event-backed packet plan row",
                "body": "Event log fallback body",
                "target_ref": "plan:MP-377",
                "mutation_op": "append_progress_log",
                "timestamp_utc": "2026-05-06T00:00:00Z",
                "expires_at_utc": "2026-05-06T00:30:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        ["develop", "ingest-plan", "--packet-id", "rev_pkt_9002", "--format", "json"]
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
    assert receipt.packet_id == "rev_pkt_9002"
    assert receipt.row_ids == ("PKT-BIND-REV-PKT-9002",)
    assert rows[0]["sourced_from_packets"] == ["rev_pkt_9002"]
    assert rows[0]["title"] == "Packet plan intent: Event-backed packet plan row"


def test_develop_ingest_plan_merges_packet_evidence_into_existing_row(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(plan_intake, "REPO_ROOT", tmp_path)
    store = tmp_path / "dev/state/plan_index.jsonl"
    write_plan_rows_jsonl(
        store,
        (
            PlanRow(
                row_id="MP377-GUARDIR-V21-A5",
                title="Existing universal lifecycle row",
                status="in_progress",
                sdlc_stage=SDLCStage.TEST,
                anchor_refs=("packet:rev_pkt_3114",),
                sourced_from_packets=("rev_pkt_3114",),
                target_ref="MP377-P0-T22A",
                work_evidence_ids=("packet:rev_pkt_3114",),
            ),
        ),
    )
    state_path = (
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json"
    )
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "packet_id": "rev_pkt_3112",
                        "kind": "instruction",
                        "summary": "Universal GovernanceLifecycle correction",
                        "body": "Fold this into MP377-GUARDIR-V21-A5.",
                        "target_ref": "plan:MP-377",
                        "requested_action": "review_only",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "develop",
            "ingest-plan",
            "--packet-id",
            "rev_pkt_3112",
            "--plan-row-id",
            "MP377-GUARDIR-V21-A5",
            "--format",
            "json",
        ]
    )

    receipt = plan_intake.ingest_plan_intent(args, repo_root=tmp_path)
    rows = [
        json.loads(line)
        for line in store.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert receipt.status == "accepted"
    assert receipt.row_ids == ("MP377-GUARDIR-V21-A5",)
    assert receipt.store_statuses == ("updated",)
    assert rows[0]["title"] == "Existing universal lifecycle row"
    assert rows[0]["status"] == "in_progress"
    assert rows[0]["sdlc_stage"] == "test"
    assert rows[0]["target_ref"] == "MP377-P0-T22A"
    assert rows[0]["sourced_from_packets"] == ["rev_pkt_3114", "rev_pkt_3112"]
    assert "packet:rev_pkt_3114" in rows[0]["anchor_refs"]
    assert "packet:rev_pkt_3112" in rows[0]["anchor_refs"]


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
                "can_run_next_command": False,
                "advance_allowed": True,
                "effective_authority_source": "operator_override_edit_only_repair",
                "top_blocker": "655 expired unresolved review packet(s)",
                "active_packet_id": "rev_pkt_anchor",
                "attention_packet_id": "rev_pkt_attention",
                "allowed_actions": ["implementation.edit"],
                "blocked_actions": ["vcs.stage", "vcs.commit", "vcs.push"],
                "operator_override": {
                    "active": True,
                    "scope": "edit-only",
                    "target_kind": "packet",
                    "target_ref": "rev_pkt_anchor",
                    "allowed_actions": ["implementation.edit"],
                    "blocked_actions": ["vcs.stage", "vcs.commit", "vcs.push"],
                },
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
    assert snapshot.agent_loop_decisions[0].active_packet_id == "rev_pkt_anchor"
    assert snapshot.agent_loop_decisions[0].attention_packet_id == "rev_pkt_attention"
    assert snapshot.agent_loop_decisions[0].advance_allowed is True
    assert (
        snapshot.agent_loop_decisions[0].effective_authority_source
        == "operator_override_edit_only_repair"
    )
    assert snapshot.agent_loop_decisions[0].operator_override_active is True
    assert snapshot.agent_loop_decisions[0].operator_override_edit_allowed is True
    assert snapshot.agent_loop_decisions[0].operator_override_target_ref == "rev_pkt_anchor"
    assert "vcs.commit" in snapshot.agent_loop_decisions[0].blocked_actions


def test_develop_orchestration_carries_operator_override_into_fresh_rows(
    tmp_path,
) -> None:
    review_state = {
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "reviewer",
                    "session_id": "session-1",
                    "status": "live",
                    "confidence_class": "fresh",
                },
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "session_id": "session-2",
                    "status": "live",
                    "confidence_class": "fresh",
                },
            ]
        },
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "state": "satisfied",
                "source_latest_event_id": "rev_evt_1",
                "snapshot_id": "agent-runtime-clock:rev_evt_1",
            },
            "packet_attention": {
                "observation_actor_id": "codex",
                "observation_session_id": "session-1",
            },
        },
    }
    dashboard = {
        "control_plane": {
            "top_blocker": "startup authority: dirty_and_untracked_budget_exceeded",
            "next_action": (
                "checkpoint_blocked_by_startup_authority:"
                "dirty_and_untracked_budget_exceeded"
            ),
        },
        "now": {
            "top_blocker": "startup authority: dirty_and_untracked_budget_exceeded",
            "next_action": (
                "checkpoint_blocked_by_startup_authority:"
                "dirty_and_untracked_budget_exceeded"
            ),
        },
    }

    snapshot = orchestration_snapshot(
        tmp_path,
        review_state,
        actor="codex",
        dashboard=dashboard,
        master_plan={
            "contract_id": "MasterPlan",
            "rows": [
                {
                    "contract_id": "PlanRow",
                    "row_id": "MP377-P0-CHECKPOINT-AUTOMATION-S1",
                    "anchor_refs": ["plan:MP-377"],
                    "target_ref": "plan:MP-377",
                    "status": "queued",
                }
            ],
        },
        loop_intent="plan",
        requested_plan_ref="MP377-P0-CHECKPOINT-AUTOMATION-S1",
        operator_override_requested=True,
        operator_override_reason="operator approved scoped repair",
        operator_override_scope="edit-only",
        operator_override_by="operator",
    )

    codex = next(row for row in snapshot.agent_loop_decisions if row.actor_id == "codex")
    claude = next(row for row in snapshot.agent_loop_decisions if row.actor_id == "claude")
    assert codex.loop_mode == "operator_override_edit"
    assert codex.may_mutate is True
    assert codex.operator_override_active is True
    assert codex.operator_override_edit_allowed is True
    assert codex.operator_override_target_kind == "plan"
    assert codex.operator_override_target_ref == "MP377-P0-CHECKPOINT-AUTOMATION-S1"
    assert codex.target_kind == "plan"
    assert codex.target_ref == "MP377-P0-CHECKPOINT-AUTOMATION-S1"
    assert codex.proof_state == "satisfied"
    assert claude.operator_override_active is False
    assert claude.may_mutate is False


def test_develop_orchestration_consumes_agent_supervise_report(
    tmp_path,
    monkeypatch,
) -> None:
    summary_path = tmp_path / "dev/reports/system_picture/latest/summary.json"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(json.dumps({"sections": []}), encoding="utf-8")
    captured_thresholds: list[int] = []

    def fake_evaluate(inputs):
        captured_thresholds.append(inputs.staleness_threshold_seconds)
        return AgentSuperviseReport(
            status="blocked",
            actor=inputs.actor,
            provider=inputs.provider,
            role=inputs.role,
            process_state="detached_runtime_only",
            process_exit_detected=False,
            freeze_detected=True,
            session_id=inputs.session_id,
            continuation_anchor_live=True,
            continuation_anchor_packet_id="rev_pkt_anchor",
            staleness_threshold_seconds=inputs.staleness_threshold_seconds,
            trigger_reason=(
                "freeze_detected:"
                f"{inputs.staleness_threshold_seconds + 1}s"
                f">=threshold:{inputs.staleness_threshold_seconds}s"
            ),
            blocked_reasons=("bypass_receipt_missing",),
        )

    monkeypatch.setattr(
        orchestration_agent_supervise_module,
        "evaluate_agent_supervision",
        fake_evaluate,
    )
    monkeypatch.setattr(
        orchestration_system_picture_module,
        "_current_system_picture_sections_by_id",
        lambda _repo_root: {},
    )
    review_state = {
        "agent_loop_decisions": [
            {
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "session-1",
                "lifecycle_state": "idle",
                "required_action": "observe_typed_runtime",
                "loop_mode": "typed_event_wait",
                "should_continue_loop": True,
                "safe_to_continue": True,
                "may_mutate": False,
                "proof_state": "satisfied",
                "next_loop_command": (
                    "python3 dev/scripts/devctl.py agent-loop --format json"
                ),
            }
        ]
    }

    snapshot = orchestration_snapshot(tmp_path, review_state, actor="codex")

    supervise = snapshot.signals[0]
    assert supervise.source == "agent-supervise"
    assert supervise.status == "blocked"
    assert supervise.severity == "medium"
    assert "detached_runtime_only" in supervise.summary
    assert "rev_pkt_anchor" in supervise.summary
    assert "devctl.py agent-supervise" in supervise.closure_check_command
    assert "--staleness-threshold-seconds 600" in supervise.closure_check_command
    assert captured_thresholds == [600]
    assert snapshot.action_required_count == 1


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


def test_develop_next_returns_to_plan_after_packet_ingestion() -> None:
    ordinary = PlanRow(
        row_id="MP377-IN-PROGRESS",
        title="Ordinary in-progress row",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    packet_row = PlanRow(
        row_id="MP377-PACKET-FINDING",
        title="Ingested packet finding",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        sourced_from_packets=("rev_pkt_9999",),
        target_ref="plan:MP-377",
    )
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

    attention = packet_attention_from_review_state(
        review_state,
        rows=(ordinary, packet_row),
    )
    selected = select_next_slice(
        (ordinary, packet_row),
        packet_attention=attention,
    )

    assert attention.attention_required is False
    assert attention.latest_attention_packet_id == ""
    assert attention.latest_finding_packet_id == ""
    assert attention.pending_actionable_packet_ids == ()
    assert attention.pending_delivery_packet_ids == ()
    assert attention.summary.startswith("no pending attention")
    assert selected.slice_id == "MP377-IN-PROGRESS"
    assert "typed master-plan rows" in selected.reason


def test_develop_next_treats_packet_anchor_as_ingested() -> None:
    ordinary = PlanRow(
        row_id="MP377-IN-PROGRESS",
        title="Ordinary in-progress row",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    packet_row = PlanRow(
        row_id="MP377-PACKET-FINDING",
        title="Ingested packet finding",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        anchor_refs=("packet:rev_pkt_9999",),
        target_ref="plan:MP-377",
    )
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

    attention = packet_attention_from_review_state(
        review_state,
        rows=(ordinary, packet_row),
    )
    selected = select_next_slice(
        (ordinary, packet_row),
        packet_attention=attention,
    )

    assert attention.attention_required is False
    assert selected.slice_id == "MP377-IN-PROGRESS"


def test_develop_next_selects_active_leaf_plan_row() -> None:
    parent = PlanRow(
        row_id="MP377-GUARDIR-PACKET-DURABLE-INGESTION",
        title="Durable packet ingestion parent",
        status="in_progress",
        sdlc_stage=SDLCStage.TEST,
    )
    scheduler = PlanRow(
        row_id="MP377-P0-PACKET-INTAKE-SCHEDULER-S1",
        title="Make packet intake resolve before next-action selection",
        status="in_progress",
        sdlc_stage=SDLCStage.SPEC,
        anchor_refs=("MP377-GUARDIR-PACKET-DURABLE-INGESTION",),
        target_ref="plan:MP377-GUARDIR-PACKET-DURABLE-INGESTION",
    )
    concrete = PlanRow(
        row_id="MP377-P0-ACTIVE-WORK-ENVELOPE-S1",
        title="Add canonical ActiveWorkEnvelope compiler for develop next",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        anchor_refs=(
            "MP377-P0-PACKET-INTAKE-SCHEDULER-S1",
            "MP377-GUARDIR-PACKET-DURABLE-INGESTION",
        ),
        target_ref="dev/scripts/devctl/commands/development/next_slice.py",
    )

    selected = select_next_slice((parent, scheduler, concrete))

    assert selected.slice_id == "MP377-P0-ACTIVE-WORK-ENVELOPE-S1"
    assert "active leaf rows" in selected.reason


def test_develop_next_does_not_schedule_packet_binding_as_leaf_child() -> None:
    parent = PlanRow(
        row_id="MP377-P0-PACKET-INTAKE-SCHEDULER-S1",
        title="Make packet intake resolve before next-action selection",
        status="in_progress",
        sdlc_stage=SDLCStage.SPEC,
    )
    packet_binding = PlanRow(
        row_id="PKT-BIND-REV-PKT-3151",
        title="Packet binding row",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        anchor_refs=("MP377-P0-PACKET-INTAKE-SCHEDULER-S1",),
        sourced_from_packets=("rev_pkt_3151",),
    )

    selected = select_next_slice((parent, packet_binding))

    assert selected.slice_id == "MP377-P0-PACKET-INTAKE-SCHEDULER-S1"


def test_develop_next_maps_topology_blocker_to_typed_repair_row() -> None:
    active_general = PlanRow(
        row_id="MP377-P0-T22AN-AB",
        title="Bound Python test execution through typed validation policy",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    topology_repair = PlanRow(
        row_id="MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1",
        title="Make next selection topology-neutral and repair-oriented",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        anchor_refs=("MP377-P0-ACTIVE-WORK-ENVELOPE-S1",),
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        status="action_required",
        action_required_count=1,
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="s1",
                lifecycle_state="blocked",
                required_action="resolve_blocker",
                loop_mode="run_or_report_blocker",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker=(
                    "Reviewer mode active_dual_agent is inactive with "
                    "observed topology no_live_agents"
                ),
            ),
        ),
    )

    selected = select_next_slice(
        (active_general, topology_repair),
        orchestration=orchestration,
    )

    assert selected.slice_id == "MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1"
    assert "compatibility topology labels" in selected.reason


def test_develop_next_maps_checkpoint_blocker_to_checkpoint_automation_row() -> None:
    active_general = PlanRow(
        row_id="MP377-P0-T22AN-AB",
        title="Bound Python test execution through typed validation policy",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    checkpoint_repair = PlanRow(
        row_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
        title="Automate governed checkpoint projection and sandbox recovery",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        anchor_refs=("MP377-P0-T22AN-AB",),
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        status="action_required",
        action_required_count=1,
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="s1",
                lifecycle_state="blocked",
                required_action="resolve_blocker",
                loop_mode="run_or_report_blocker",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="git_index_write_blocked while staging managed projection",
            ),
        ),
    )

    selected = select_next_slice(
        (active_general, checkpoint_repair),
        orchestration=orchestration,
    )

    assert selected.slice_id == "MP377-P0-CHECKPOINT-AUTOMATION-S1"


def test_develop_next_maps_agent_supervise_blocker_to_checkpoint_automation_row() -> None:
    active_general = PlanRow(
        row_id="MP377-P0-T22AN-AB",
        title="Bound Python test execution through typed validation policy",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    checkpoint_repair = PlanRow(
        row_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
        title="Automate governed checkpoint projection and sandbox recovery",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        anchor_refs=("MP377-P0-T22AN-AB",),
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        status="action_required",
        action_required_count=1,
        signals=(
            DevelopmentOrchestrationSignal(
                source="agent-supervise",
                signal_id="agent-supervise:codex:reviewer:s1",
                status="blocked",
                summary=(
                    "agent-supervise codex:reviewer status=blocked "
                    "process_state=detached_runtime_only "
                    "trigger=freeze_detected:901s>=threshold:900s"
                ),
                recommended_action="resolve_agent_supervision_blocker",
            ),
        ),
    )

    selected = select_next_slice(
        (active_general, checkpoint_repair),
        orchestration=orchestration,
    )

    assert selected.slice_id == "MP377-P0-CHECKPOINT-AUTOMATION-S1"


def test_develop_next_maps_long_quality_blocker_to_smart_check_deferral_row() -> None:
    active_general = PlanRow(
        row_id="MP377-P0-T22AN-AB",
        title="Bound Python test execution through typed validation policy",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    smart_scheduler = PlanRow(
        row_id="MP377-P0-SMART-CHECK-DEFERRAL-S1",
        title="Schedule smart checks and governed deferrals for development loops",
        status="in_progress",
        sdlc_stage=SDLCStage.SPEC,
        anchor_refs=("MP377-P0-GUARD-DEFERRAL-S1",),
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        status="action_required",
        action_required_count=1,
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="s1",
                lifecycle_state="blocked",
                required_action="resolve_blocker",
                loop_mode="run_or_report_blocker",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="code-shape debt from push_preflight_running",
            ),
        ),
    )

    selected = select_next_slice(
        (active_general, smart_scheduler),
        orchestration=orchestration,
    )

    assert selected.slice_id == "MP377-P0-SMART-CHECK-DEFERRAL-S1"


def test_develop_next_maps_startup_checkpoint_blocker_to_checkpoint_row() -> None:
    active_general = PlanRow(
        row_id="MP377-P0-T22AN-AC",
        title="Repair import index atomicity guard",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    checkpoint_repair = PlanRow(
        row_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
        title="Automate governed checkpoint projection and sandbox recovery",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        anchor_refs=("MP377-P0-T22AN-AB",),
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        status="action_required",
        action_required_count=1,
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="s1",
                lifecycle_state="blocked",
                required_action="resolve_blocker",
                loop_mode="run_or_report_blocker",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker=(
                    "startup authority: import_index_atomicity "
                    "dirty_path_budget_exceeded"
                ),
            ),
        ),
    )

    selected = select_next_slice(
        (active_general, checkpoint_repair),
        orchestration=orchestration,
    )

    assert selected.slice_id == "MP377-P0-CHECKPOINT-AUTOMATION-S1"


def test_develop_next_prefers_orchestration_blocker_over_communication_packet() -> None:
    active_general = PlanRow(
        row_id="MP377-P0-T22AN-AB",
        title="Bound Python test execution through typed validation policy",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    topology_repair = PlanRow(
        row_id="MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1",
        title="Make next selection topology-neutral and repair-oriented",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
    )
    attention = DevelopmentPacketAttention(
        attention_required=True,
        attention_status="wake_required",
        wake_reason="system_notice_pending",
        latest_attention_packet_id="rev_pkt_notice",
        required_command=(
            "python3 dev/scripts/devctl.py review-channel --action show "
            "--packet-id rev_pkt_notice --terminal none --format md"
        ),
        packet_kind="system_notice",
        authority_affecting=False,
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        status="action_required",
        action_required_count=1,
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="s1",
                lifecycle_state="blocked",
                required_action="resolve_blocker",
                loop_mode="run_or_report_blocker",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="review_loop_relaunch_required with no_live_agents",
            ),
        ),
    )

    selected = select_next_slice(
        (active_general, topology_repair),
        packet_attention=attention,
        orchestration=orchestration,
    )

    assert selected.slice_id == "MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1"


def test_develop_next_lets_action_request_close_checkpoint_blocker() -> None:
    checkpoint_repair = PlanRow(
        row_id="MP377-P0-CHECKPOINT-AUTOMATION-S1",
        title="Automate governed checkpoint projection and sandbox recovery",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
    )
    attention = DevelopmentPacketAttention(
        attention_required=True,
        attention_status="wake_required",
        wake_reason="action_request_pending",
        latest_attention_packet_id="rev_pkt_stage",
        required_command=(
            "python3 dev/scripts/devctl.py review-channel --action show "
            "--packet-id rev_pkt_stage --terminal none --format md"
        ),
        packet_kind="action_request",
        requested_action="stage_commit_pipeline",
        authority_affecting=True,
    )
    orchestration = DevelopmentOrchestrationSnapshot(
        status="action_required",
        action_required_count=1,
        agent_loop_decisions=(
            DevelopmentAgentLoopInput(
                actor_id="codex",
                actor_role="reviewer",
                session_id="s1",
                lifecycle_state="blocked",
                required_action="resolve_blocker",
                loop_mode="run_or_report_blocker",
                should_continue_loop=True,
                safe_to_continue=False,
                may_mutate=False,
                proof_state="satisfied",
                top_blocker="checkpoint_required dirty_path_budget_exceeded vcs.stage",
            ),
        ),
    )

    selected = select_next_slice(
        (checkpoint_repair,),
        packet_attention=attention,
        orchestration=orchestration,
    )

    assert selected.slice_id == "communication-packet-attention"
    assert selected.target_ref.endswith("--packet-id rev_pkt_stage --terminal none --format md")


def test_ingested_action_request_still_requires_lifecycle_attention() -> None:
    packet_row = PlanRow(
        row_id="PKT-BIND-REV-PKT-9999",
        title="Ingested action request",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        sourced_from_packets=("rev_pkt_9999",),
        target_ref="runtime:commit",
    )
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_9999",
                "to_agent": "codex",
                "kind": "action_request",
                "requested_action": "stage_commit_pipeline",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(packet_row,),
    )

    assert attention.attention_required is True
    assert attention.latest_attention_packet_id == "rev_pkt_9999"
    assert attention.pending_delivery_packet_ids == ("rev_pkt_9999",)
    assert attention.packet_kind == "action_request"
    assert attention.requested_action == "stage_commit_pipeline"
    assert attention.authority_affecting is True


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
        "--packet-id rev_pkt_9999 --actor codex --terminal none --format md"
    )


def test_packet_attention_requires_body_open_for_peer_progress_packet() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_3662",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "task_progress",
                "status": "pending",
                "lifecycle_current_state": "task_progress",
                "latest_event_id": "rev_evt_3662",
                "body": "Ranked candidates that must be read before mutation.",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    attention = packet_attention_from_review_state(review_state, rows=())

    assert attention.attention_required is True
    assert attention.latest_attention_packet_id == "rev_pkt_3662"
    assert attention.wake_reason == "packet_body_open_required"
    assert attention.required_command == (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_3662 --actor codex --terminal none --format md"
    )


def test_packet_attention_ignores_delivery_for_dead_target_route() -> None:
    review_state = {
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "reviewer",
                    "session_id": "live-reviewer-session",
                    "status": "polling",
                    "confidence_class": "derived_typed_event",
                }
            ]
        },
        "packets": [
            {
                "packet_id": "rev_pkt_dead_route",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "review_accepted",
                "status": "pending",
                "lifecycle_current_state": "review_accepted",
                "requested_action": "review_only",
                "policy_hint": "review_only",
                "target_role": "implementer",
                "target_session_id": "dead-implementer-session",
                "body": "Historical review acceptance for a dead implementer session.",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ],
    }

    attention = packet_attention_from_review_state(review_state, rows=())

    assert attention.attention_required is False
    assert attention.latest_attention_packet_id == ""
    assert attention.pending_delivery_packet_ids == ()


def test_packet_attention_ignores_lifecycle_review_acceptance_delivery() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_review_accepted",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "review_accepted",
                "status": "pending",
                "lifecycle_current_state": "review_accepted",
                "requested_action": "review_only",
                "policy_hint": "review_only",
                "body": "Historical lifecycle acceptance with no active action.",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ],
    }

    attention = packet_attention_from_review_state(review_state, rows=())

    assert attention.attention_required is False
    assert attention.latest_attention_packet_id == ""
    assert attention.pending_delivery_packet_ids == ()


def test_packet_attention_ignores_stale_wake_without_live_packets() -> None:
    review_state = {
        "packet_inbox": {
            "agents": [
                {
                    "agent": "codex",
                    "attention_status": "wake_required",
                    "wake_reason": "urgent_attention",
                    "required_command": (
                        "python3 dev/scripts/devctl.py review-channel "
                        "--action inbox --target codex --actor codex "
                        "--status pending --terminal none --format md"
                    ),
                }
            ]
        },
        "packets": [
            {
                "packet_id": "rev_pkt_review_accepted",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "review_accepted",
                "status": "pending",
                "lifecycle_current_state": "review_accepted",
                "requested_action": "review_only",
                "policy_hint": "review_only",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ],
    }

    attention = packet_attention_from_review_state(review_state, rows=())

    assert attention.attention_required is False
    assert attention.wake_reason == ""
    assert attention.required_command == ""


def test_packet_attention_keeps_delivery_for_matching_fresh_route() -> None:
    review_state = {
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "reviewer",
                    "session_id": "live-reviewer-session",
                    "status": "polling",
                    "confidence_class": "derived_typed_event",
                }
            ]
        },
        "packets": [
            {
                "packet_id": "rev_pkt_live_route",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "system_notice",
                "status": "pending",
                "target_role": "reviewer",
                "target_session_id": "live-reviewer-session",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ],
    }

    attention = packet_attention_from_review_state(review_state, rows=())

    assert attention.attention_required is True
    assert attention.latest_attention_packet_id == "rev_pkt_live_route"
    assert attention.pending_delivery_packet_ids == ("rev_pkt_live_route",)


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


def test_packet_attention_treats_plan_owned_clock_expired_packet_as_provenance() -> None:
    packet_row = PlanRow(
        row_id="MP377-P0-EXC-S1",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        anchor_refs=("packet:rev_pkt_3111",),
    )
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_3111",
                "to_agent": "codex",
                "kind": "finding",
                "status": "expired",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "lifecycle_current_state": "archived",
                "disposition": {
                    "sink": "archived",
                    "archive_classification": "clock_expired_without_disposition",
                    "resolution_anchor": (
                        "archive_classification:clock_expired_without_disposition"
                    ),
                },
            }
        ]
    }

    attention = packet_attention_from_review_state(review_state, rows=(packet_row,))
    selected = select_next_slice((packet_row,), packet_attention=attention)

    assert attention.attention_required is False
    assert attention.expired_unresolved_count == 0
    assert attention.required_command == ""
    assert attention.summary.startswith("no pending attention")
    assert selected.slice_id == "MP377-P0-EXC-S1"


def test_packet_attention_keeps_unowned_expired_transport_as_runtime_debt() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_unowned",
                "to_agent": "codex",
                "kind": "action_request",
                "status": "pending",
                "expires_at_utc": "2000-01-01T00:00:00Z",
            }
        ]
    }

    attention = packet_attention_from_review_state(review_state, rows=())
    selected = select_next_slice((), packet_attention=attention)

    assert attention.attention_required is True
    assert attention.expired_unresolved_count == 1
    assert attention.required_command == (
        "python3 dev/scripts/devctl.py develop audit-packets --format md"
    )
    assert attention.summary == "Packet debt audit requires 1 expired unresolved packet(s)."
    assert selected.slice_id == "packet-debt-audit"


def test_packet_attention_treats_class_owned_clock_expired_packet_as_plan_evidence() -> None:
    packet_owner = PlanRow(
        row_id="MP377-P0-PACKET-INTAKE-SCHEDULER-S1",
        title="Make packet intake resolve before next-action selection",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
        target_ref="plan:MP377-GUARDIR-PACKET-DURABLE-INGESTION",
    )
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_3130",
                "to_agent": "codex",
                "kind": "finding",
                "status": "expired",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "lifecycle_current_state": "archived",
                "disposition": {
                    "sink": "archived",
                    "archive_classification": "clock_expired_without_disposition",
                    "resolution_anchor": (
                        "archive_classification:clock_expired_without_disposition"
                    ),
                },
            }
        ]
    }

    attention = packet_attention_from_review_state(review_state, rows=(packet_owner,))
    selected = select_next_slice((packet_owner,), packet_attention=attention)

    assert attention.attention_required is False
    assert attention.expired_unresolved_count == 0
    assert attention.required_command == ""
    assert selected.slice_id == packet_owner.row_id


def test_packet_attention_treats_terminal_plan_ingestion_receipt_as_provenance() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_3121",
                "to_agent": "codex",
                "kind": "finding",
                "status": "expired",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "lifecycle_current_state": "archived",
                "disposition": {
                    "sink": "archived",
                    "archive_classification": "clock_expired_without_disposition",
                    "resolution_anchor": (
                        "archive_classification:clock_expired_without_disposition"
                    ),
                },
            }
        ]
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(),
        terminal_receipt_by_packet={"rev_pkt_3121": "obsolete"},
    )
    selected = select_next_slice((), packet_attention=attention)

    assert attention.attention_required is False
    assert attention.expired_unresolved_count == 0
    assert attention.required_command == ""
    assert attention.summary.startswith("no pending attention")
    assert selected.slice_id != "packet-debt-audit"


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
    assert selected.slice_id == "communication-packet-attention"
    assert "without becoming an active slice id" in selected.reason


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


def test_packet_attention_review_loop_relaunch_is_not_packet_debt() -> None:
    review_state = {
        "attention": {
            "status": "review_loop_relaunch_required",
            "recommended_command": (
                "python3 dev/scripts/devctl.py review-channel --action launch "
                "--terminal none --format json"
            ),
        },
        "packets": [],
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(),
        agent="codex",
    )
    selected = select_next_slice((), packet_attention=attention)

    assert attention.attention_required is True
    assert attention.attention_status == "blocked"
    assert attention.wake_reason == "review_loop_relaunch_required"
    assert attention.expired_unresolved_count == 0
    assert attention.summary.startswith("Review loop relaunch is required")
    assert selected.slice_id == "review-loop-relaunch-required"


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


def test_packet_attention_keeps_unacked_older_finding_live_when_newer_is_acked() -> None:
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
    assert attention.wake_reason == "finding_pending"
    assert attention.latest_finding_packet_id == "rev_pkt_old"
    assert attention.pending_actionable_packet_ids == ("rev_pkt_old",)
    assert attention.durable_plan_row_id == ""
    assert attention.required_command == (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_old --actor codex --terminal none --format md"
    )
    assert "rev_pkt_old" in attention.summary
    assert selected.slice_id == "communication-packet-attention"


def test_unlinked_packet_attention_does_not_select_arbitrary_active_plan_row() -> None:
    ordinary = PlanRow(
        row_id="MP377-IN-PROGRESS",
        title="Ordinary in-progress row",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_review_only",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "posted_at": "2999-01-01T00:00:00Z",
                "expires_at_utc": "2999-01-01T00:30:00Z",
            }
        ]
    }

    attention = packet_attention_from_review_state(review_state, rows=(ordinary,))
    selected = select_next_slice((ordinary,), packet_attention=attention)

    assert attention.attention_required is True
    assert attention.latest_finding_packet_id == "rev_pkt_review_only"
    assert attention.durable_plan_row_id == ""
    assert selected.slice_id == "communication-packet-attention"
    assert "without becoming an active slice id" in selected.reason


def test_packet_attention_uses_packet_target_ref_plan_row() -> None:
    linked = PlanRow(
        row_id="MP377-LINKED",
        title="Targeted packet owner",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
    )
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_linked",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "target_ref": "plan:MP377-LINKED",
                "posted_at": "2999-01-01T00:00:00Z",
                "expires_at_utc": "2999-01-01T00:30:00Z",
            }
        ]
    }

    attention = packet_attention_from_review_state(review_state, rows=(linked,))
    selected = select_next_slice((linked,), packet_attention=attention)

    assert attention.attention_required is True
    assert attention.latest_finding_packet_id == "rev_pkt_linked"
    assert attention.durable_plan_row_id == "MP377-LINKED"
    assert selected.slice_id == "MP377-LINKED"


def test_packet_attention_uses_plan_ingestion_receipt_row_id() -> None:
    linked = PlanRow(
        row_id="MP377-LINKED",
        title="Receipt packet owner",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
    )
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_receipted",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "posted_at": "2999-01-01T00:00:00Z",
                "expires_at_utc": "2999-01-01T00:30:00Z",
            }
        ]
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(linked,),
        durable_row_id_by_packet={"rev_pkt_receipted": "MP377-LINKED"},
    )
    selected = select_next_slice((linked,), packet_attention=attention)

    assert attention.attention_required is True
    assert attention.latest_finding_packet_id == "rev_pkt_receipted"
    assert attention.durable_plan_row_id == "MP377-LINKED"
    assert selected.slice_id == "MP377-LINKED"
