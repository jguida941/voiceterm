"""Regression tests for claude-loop typed convergence and freshness gating.

Per Codex rev_pkt_2376: claude-loop must render explicit ``unavailable`` /
``stale`` when the typed snapshot is missing, instead of rendering 0/0
typed counts as if they were current truth. This caused Codex to see a
regression where ``codex_sessions: 0 live / 0 (typed work-board)`` looked
like an accurate empty work-board, but was actually a stale read.

The renderer must also surface ``typed_snapshot_freshness`` evidence so
consumers know which event_id/refresh the typed counts were observed at.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from dev.scripts.devctl.commands.reporting.claude_loop_proof import (
    build_loop_proof_evidence,
    compact_master_plan_authority,
)
from dev.scripts.devctl.commands.reporting import claude_loop
from dev.scripts.devctl.commands.reporting.claude_loop_render import (
    render,
    render_markdown,
)


def _payload_with_typed_snapshot(state: str = "available") -> dict:
    return {
        "schema_version": 1,
        "command": "claude-loop",
        "now": {
            "owner": "Implementer",
            "next_action": "await_checkpoint",
            "top_blocker": "n/a",
        },
        "ack_freshness": {"available": True, "is_current": False},
        "pending_packets": [],
        "control_packets": [],
        "active_codex_sessions": {
            "live_count": 5,
            "count": 5,
            "typed_live_count": 1,
            "typed_session_count": 1,
        },
        "coordination_state": {
            "contract_id": "CoordinationStateProjection",
            "coordination_topology": "multi_agent_active",
            "authority_mode": "single_writer",
            "recovery_eligibility": "remote_only",
            "observed_runtime": {
                "active_actor_count": 3,
                "active_runtime_providers": ["codex", "claude"],
                "active_operator_channels": ["manual"],
            },
        },
        "canonical_active_packet_for_claude": "rev_pkt_2288",
        "typed_snapshot_freshness": {
            "source_latest_event_id": "rev_evt_45000",
            "refreshed_at_utc": "2026-04-30T05:00:00Z",
            "typed_snapshot_state": state,
        },
    }


def test_render_markdown_uses_typed_counts_when_freshness_available() -> None:
    payload = _payload_with_typed_snapshot(state="available")
    text = render_markdown(payload)
    assert "1 live / 1 (typed work-board)" in text
    assert "coordination_topology: multi_agent_active" in text
    assert "active_packet (claude, typed): rev_pkt_2288" in text


def test_render_markdown_renders_unavailable_when_typed_snapshot_missing() -> None:
    payload = _payload_with_typed_snapshot(state="unavailable")
    text = render_markdown(payload)
    assert "typed work-board unavailable" in text
    assert "0 live / 0 (typed work-board)" not in text
    assert "coordination_topology: unavailable" in text


def test_render_markdown_demotes_legacy_reviewer_mode_warning() -> None:
    payload = _payload_with_typed_snapshot(state="available")
    payload["coordination_state"]["legacy_reviewer_mode"] = "single_agent"
    text = render_markdown(payload)
    assert "WARNING: legacy_reviewer_mode='single_agent'" in text
    assert "multi_agent_active per typed work-board" in text


def test_render_markdown_does_not_claim_legacy_unscoped_packet() -> None:
    payload = _payload_with_typed_snapshot(state="available")
    payload["canonical_active_packet_for_claude"] = ""
    payload["legacy_unscoped_packet_for_claude"] = "rev_pkt_2547"
    payload["agent_loop_decision"] = {
        "actor_id": "claude",
        "actor_role": "dashboard",
        "session_id": "",
        "loop_state": "blocked",
        "required_action": "repair_startup_authority",
        "loop_mode": "observer_wait",
        "loop_intent": "auto",
        "target_kind": "",
        "target_ref": "",
        "recommended_cadence_seconds": 600,
        "can_run_next_command": False,
        "dogfood_record_allowed": False,
        "advance_allowed": True,
        "proof_state": "satisfied",
        "required_proofs": ["typed_runtime_clock"],
        "missing_proofs": [],
        "wake_source": "agent_runtime_clock",
        "loop_driver_agent": "claude",
        "policy_reason": "repair_startup_authority_requires_mutation_authority",
        "next_loop_command": (
            "python3 dev/scripts/devctl.py agent-loop --format json "
            "--actor claude --role dashboard"
        ),
        "should_continue_loop": True,
        "may_mutate": False,
        "active_packet_id": "",
        "legacy_unscoped_packet_id": "rev_pkt_2547",
    }
    text = render_markdown(payload)
    assert "active_packet (claude, typed): none" in text
    assert "legacy_unscoped_packet (not claimable): rev_pkt_2547" in text
    assert "loop_policy: observer_wait | intent=auto | cadence=600s" in text
    assert "loop_target: none:none | advance=True | proof=satisfied" in text
    assert "next_loop_command: python3 dev/scripts/devctl.py agent-loop" in text
    assert "priority_decision (legacy)" not in text


def test_loop_proof_evidence_compacts_master_plan_rows_for_output() -> None:
    master_plan = {
        "authority_state": "available",
        "typed_store_path": "dev/state/plan_index.jsonl",
        "rows": [
            {
                "row_id": "MP377-GUARDIR-V21",
                "status": "active",
                "target_ref": "MP377-P0-T22",
                "anchor_refs": ["MP-377"],
                "title": "Long text should not be required in loop output",
            },
            {
                "row_id": "MP377-OTHER",
                "status": "queued",
                "target_ref": "MP377-P0-T99",
                "anchor_refs": [],
            },
        ],
    }

    authority = compact_master_plan_authority(master_plan, target_ref="MP-377")
    proof = build_loop_proof_evidence(
        loop_decision={
            "proof_state": "satisfied",
            "required_proofs": ["typed_runtime_clock", "plan_target"],
            "satisfied_proofs": ["typed_runtime_clock", "plan_target"],
            "missing_proofs": [],
            "source_latest_event_id": "rev_evt_1",
            "source_snapshot_id": "agent-runtime-clock:rev_evt_1",
        },
        master_plan_authority=authority,
        review_state={},
    )

    assert authority["row_count"] == 2
    assert authority["target_state"] == "satisfied"
    assert authority["matched_rows"] == [
        {
            "row_id": "MP377-GUARDIR-V21",
            "status": "active",
            "target_ref": "MP377-P0-T22",
            "anchor_refs": ["MP-377"],
            "source_doc_path": "",
            "source_line": 0,
        }
    ]
    assert "rows" not in authority
    assert proof["plan_target"]["state"] == "satisfied"
    assert proof["proofs"]["plan_target"]["state"] == "satisfied"


def test_render_markdown_surfaces_proof_evidence_near_decision() -> None:
    payload = _payload_with_typed_snapshot(state="available")
    payload["agent_loop_decision"] = {
        "actor_id": "codex",
        "actor_role": "reviewer",
        "loop_state": "blocked",
        "required_action": "repair_startup_authority",
        "loop_mode": "observer_wait",
        "loop_intent": "plan",
        "target_kind": "plan",
        "target_ref": "MP-377",
        "recommended_cadence_seconds": 30,
        "can_run_next_command": False,
        "dogfood_record_allowed": False,
        "advance_allowed": False,
        "proof_state": "missing",
        "required_proofs": ["typed_runtime_clock", "plan_target"],
        "missing_proofs": [],
        "wake_source": "agent_runtime_clock",
        "loop_driver_agent": "codex",
        "policy_reason": "startup_blocker",
        "next_loop_command": "python3 dev/scripts/devctl.py agent-loop --format json",
    }
    payload["proof_evidence"] = {
        "proof_state": "missing",
        "satisfied_proofs": ["typed_runtime_clock", "plan_target"],
        "missing_proofs": ["wake_or_attention_evidence"],
        "runtime_clock": {
            "state": "satisfied",
            "source_latest_event_id": "rev_evt_48184",
        },
        "plan_target": {
            "state": "satisfied",
            "target_ref": "MP-377",
            "row_count": 139,
            "matched_rows": [{"row_id": "MP377-GUARDIR-V21"}],
        },
        "round_proof": {"state": "not_required", "row_count": 29, "matched_rows": []},
    }

    text = render_markdown(payload)

    assert "proof_evidence: state=missing" in text
    assert "proof_runtime_clock: satisfied | event=rev_evt_48184" in text
    assert "proof_plan_target: satisfied | target=MP-377 | rows=139" in text
    assert "matches=MP377-GUARDIR-V21" in text


def test_agent_loop_json_is_compact_proof_contract() -> None:
    payload = _payload_with_typed_snapshot(state="available")
    payload.update(
        {
            "command": "agent-loop",
            "control_plane": {"large": "diagnostic"},
            "session_posture": {"large": "diagnostic"},
            "agent_mind": {"large": "diagnostic"},
            "agent_minds": {"claude": {"large": "diagnostic"}},
            "system_topology": {"large": "diagnostic"},
            "master_plan": {"rows": [{"row_id": "too-large"}]},
            "agent_loop_decision": {
                "contract_id": "AgentLoopDecision",
                "proof_state": "satisfied",
            },
            "proof_evidence": {"contract_id": "AgentLoopProofEvidence"},
            "pending_packets": [
                {
                    "packet_id": "rev_pkt_1",
                    "plan_id": "MP-377",
                    "anchor_refs": ["section:MP-377"],
                    "intake_ref": "plan://MP-377",
                    "summary": "short",
                    "body": "raw packet body must not be in agent-loop output",
                }
            ],
        }
    )

    rendered = render(SimpleNamespace(format="json"), payload)
    compact = json.loads(rendered)

    assert compact["contract_id"] == "AgentLoopOutput"
    assert "agent_loop_decision" in compact
    assert "proof_evidence" in compact
    for broad_key in (
        "control_plane",
        "session_posture",
        "agent_mind",
        "agent_minds",
        "system_topology",
        "master_plan",
    ):
        assert broad_key not in compact
    assert "body" not in compact["pending_packets"][0]
    assert compact["pending_packets"][0]["plan_id"] == "MP-377"
    assert compact["pending_packets"][0]["anchor_refs"] == ["section:MP-377"]
    assert compact["pending_packets"][0]["intake_ref"] == "plan://MP-377"


def test_agent_loop_snapshot_does_not_mix_pending_packets_with_ambiguous_attention(
    monkeypatch,
    tmp_path,
) -> None:
    packet = {
        "packet_id": "rev_pkt_new",
        "to_agent": "codex",
        "from_agent": "claude",
        "kind": "finding",
        "status": "pending",
        "lifecycle_current_state": "pending",
        "summary": "typed output mismatch",
        "latest_event_id": "rev_evt_103",
        "posted_at": "2026-05-01T00:00:00Z",
    }
    review_state = {
        "packets": [packet],
        "agent_sync": {
            "agents": {
                "codex": {
                    "last_consumed_event_id_lower_bound": "rev_evt_100",
                }
            }
        },
        "agent_work_board": {"rows": []},
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_103",
                "snapshot_id": "agent-runtime-clock:rev_evt_103",
            },
            "packet_attention": {
                "observation_actor_id": "",
                "pending_packet_count": 0,
                "pivot_required": True,
                "stale_reason": "actor_identity_ambiguous",
            },
        },
    }

    captured_dashboard_kwargs: dict[str, object] = {}

    def fake_dashboard_snapshot(**kwargs) -> dict:
        captured_dashboard_kwargs.update(kwargs)
        return {
            "contract_id": "DashboardSnapshot",
            "schema_version": 3,
            "timestamp": "2026-05-01T00:00:00Z",
            "now": {},
            "pending_packets": [packet],
            "control_packets": [],
        }

    monkeypatch.setattr(
        claude_loop,
        "build_dashboard_snapshot",
        fake_dashboard_snapshot,
    )
    monkeypatch.setattr(claude_loop, "load_review_state", lambda _: review_state)
    monkeypatch.setattr(claude_loop, "load_master_plan_authority", lambda _: {})
    monkeypatch.setattr(claude_loop, "_recent_instruction_transitions", lambda _: [])

    payload = claude_loop.build_claude_loop_snapshot(
        SimpleNamespace(
            repo_root=tmp_path,
            actor="codex",
            role="reviewer",
            session_id="",
            mode="auto",
            plan="",
            packet="",
            plan377=False,
            execute=False,
            command="agent-loop",
            operator_override=False,
            override_reason="",
            override_scope="edit-only",
            override_by="operator",
        )
    )

    assert [row["packet_id"] for row in payload["pending_packets"]] == [
        "rev_pkt_new"
    ]
    assert captured_dashboard_kwargs["role"] == "reviewer"
    assert payload["packet_attention"]["observation_actor_id"] == "codex"
    assert payload["packet_attention"]["pending_packet_count"] == 1
    assert payload["packet_attention"]["latest_attention_packet_id"] == "rev_pkt_new"

    compact = json.loads(render(SimpleNamespace(format="json"), payload))
    assert compact["packet_attention"]["pending_packet_count"] == len(
        compact["pending_packets"]
    )


def test_claude_loop_snapshot_preserves_provider_agent_minds(
    monkeypatch,
    tmp_path,
) -> None:
    review_state = {
        "agent_work_board": {"rows": []},
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_104",
                "snapshot_id": "agent-runtime-clock:rev_evt_104",
            },
        },
    }
    minds = {
        "codex": {
            "available": True,
            "agent_provider": "codex",
            "event_count": 2,
            "latest_events": [{"summary": "codex read typed state"}],
        },
        "claude": {
            "available": True,
            "agent_provider": "claude",
            "event_count": 3,
            "latest_events": [{"summary": "claude watched codex"}],
        },
    }

    def fake_dashboard_snapshot(**_kwargs) -> dict:
        return {
            "contract_id": "DashboardSnapshot",
            "schema_version": 3,
            "timestamp": "2026-05-01T00:00:00Z",
            "now": {},
            "pending_packets": [],
            "control_packets": [],
            "agent_mind": minds["codex"],
            "agent_minds": minds,
        }

    monkeypatch.setattr(
        claude_loop,
        "build_dashboard_snapshot",
        fake_dashboard_snapshot,
    )
    monkeypatch.setattr(claude_loop, "load_review_state", lambda _: review_state)
    monkeypatch.setattr(claude_loop, "load_master_plan_authority", lambda _: {})
    monkeypatch.setattr(claude_loop, "_recent_instruction_transitions", lambda _: [])

    payload = claude_loop.build_claude_loop_snapshot(
        SimpleNamespace(
            repo_root=tmp_path,
            actor="claude",
            role="implementer",
            session_id="session-claude",
            mode="auto",
            plan="",
            packet="",
            plan377=False,
            execute=False,
            command="claude-loop",
            operator_override=False,
            override_reason="",
            override_scope="edit-only",
            override_by="operator",
        )
    )

    assert set(payload["agent_minds"]) == {"codex", "claude"}
    assert payload["agent_mind"]["agent_provider"] == "codex"
    assert payload["agent_minds"]["claude"]["event_count"] == 3


def test_agent_loop_pending_packet_list_respects_route_discriminator(
    monkeypatch,
    tmp_path,
) -> None:
    packet = {
        "packet_id": "rev_pkt_scoped",
        "to_agent": "claude",
        "from_agent": "codex",
        "kind": "instruction",
        "status": "pending",
        "lifecycle_current_state": "pending",
        "summary": "scoped implementer ping",
        "target_role": "implementer",
        "target_session_id": "session-claude",
        "latest_event_id": "rev_evt_104",
        "posted_at": "2026-05-01T00:01:00Z",
    }
    review_state = {
        "packets": [packet],
        "agent_sync": {
            "agents": {
                "claude": {
                    "last_consumed_event_id_lower_bound": "rev_evt_100",
                }
            }
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "session_id": "session-claude",
                }
            ]
        },
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_104",
                "snapshot_id": "agent-runtime-clock:rev_evt_104",
            },
        },
    }

    def fake_dashboard_snapshot(**_kwargs) -> dict:
        return {
            "contract_id": "DashboardSnapshot",
            "schema_version": 3,
            "timestamp": "2026-05-01T00:01:00Z",
            "now": {},
            "pending_packets": [packet],
            "control_packets": [],
        }

    monkeypatch.setattr(
        claude_loop,
        "build_dashboard_snapshot",
        fake_dashboard_snapshot,
    )
    monkeypatch.setattr(claude_loop, "load_review_state", lambda _: review_state)
    monkeypatch.setattr(claude_loop, "load_master_plan_authority", lambda _: {})
    monkeypatch.setattr(claude_loop, "_recent_instruction_transitions", lambda _: [])

    dashboard_payload = claude_loop.build_claude_loop_snapshot(
        SimpleNamespace(
            repo_root=tmp_path,
            actor="claude",
            role="dashboard",
            session_id="",
            mode="auto",
            plan="",
            packet="",
            plan377=False,
            execute=False,
            command="agent-loop",
            operator_override=False,
            override_reason="",
            override_scope="edit-only",
            override_by="operator",
        )
    )
    implementer_payload = claude_loop.build_claude_loop_snapshot(
        SimpleNamespace(
            repo_root=tmp_path,
            actor="claude",
            role="implementer",
            session_id="session-claude",
            mode="auto",
            plan="",
            packet="",
            plan377=False,
            execute=False,
            command="agent-loop",
            operator_override=False,
            override_reason="",
            override_scope="edit-only",
            override_by="operator",
        )
    )

    assert dashboard_payload["pending_packets"] == []
    assert [row["packet_id"] for row in implementer_payload["pending_packets"]] == [
        "rev_pkt_scoped"
    ]
    assert implementer_payload["pending_packets"][0]["target_role"] == "implementer"
    assert (
        implementer_payload["pending_packets"][0]["target_session_id"]
        == "session-claude"
    )


def test_claude_loop_snapshot_exposes_continuity_from_dashboard(
    monkeypatch,
    tmp_path,
) -> None:
    continuity = {
        "contract_id": "PacketContinuityIndex",
        "sink_counts": {"live_queue": 1},
        "digest": "sha256:continuity",
        "rows": [{"packet_id": "rev_pkt_2671", "sink": "live_queue"}],
    }
    attention = {
        "contract_id": "StartupContinuityAttention",
        "packet_continuity_digest": "sha256:continuity",
    }

    def fake_dashboard_snapshot(**_kwargs) -> dict:
        return {
            "contract_id": "DashboardSnapshot",
            "schema_version": 3,
            "timestamp": "2026-05-01T00:01:00Z",
            "now": {},
            "pending_packets": [],
            "control_packets": [],
            "_review_state": {"packets": []},
            "packet_continuity_index": continuity,
            "continuity_attention": attention,
        }

    monkeypatch.setattr(
        claude_loop,
        "build_dashboard_snapshot",
        fake_dashboard_snapshot,
    )
    def fail_reload(_repo_root):
        raise AssertionError("claude-loop must use dashboard frozen review_state")

    monkeypatch.setattr(claude_loop, "load_review_state", fail_reload)
    monkeypatch.setattr(claude_loop, "load_master_plan_authority", lambda _: {})
    monkeypatch.setattr(claude_loop, "_recent_instruction_transitions", lambda _: [])

    payload = claude_loop.build_claude_loop_snapshot(
        SimpleNamespace(
            repo_root=tmp_path,
            actor="claude",
            role="implementer",
            session_id="session-claude",
            mode="auto",
            plan="",
            packet="",
            plan377=False,
            execute=False,
            command="agent-loop",
            operator_override=False,
            override_reason="",
            override_scope="edit-only",
            override_by="operator",
        )
    )

    assert payload["packet_continuity_index"]["digest"] == "sha256:continuity"
    assert (
        payload["continuity_attention"]["packet_continuity_digest"]
        == "sha256:continuity"
    )


def test_loop_proof_evidence_has_entry_for_every_required_proof() -> None:
    required = [
        "typed_runtime_clock",
        "plan_target",
        "scoped_packet_target",
        "wake_or_attention_evidence",
        "implementer_handoff",
        "guard_bundle_or_attestation",
        "reviewer_semantic_review",
        "round_proof",
    ]
    authority = {
        "target_state": "satisfied",
        "target_ref": "MP-377",
        "typed_store_path": "dev/state/plan_index.jsonl",
        "row_count": 1,
        "matched_rows": [{"row_id": "MP377-GUARDIR-V21"}],
    }

    proof = build_loop_proof_evidence(
        loop_decision={
            "target_ref": "MP-377",
            "proof_state": "satisfied",
            "required_proofs": required,
            "satisfied_proofs": required,
            "missing_proofs": [],
            "source_latest_event_id": "rev_evt_1",
            "active_packet_id": "rev_pkt_1",
            "wake_required": True,
        },
        master_plan_authority=authority,
        review_state={
            "round_proofs": [
                {
                    "proof_id": "round-1",
                    "status": "accepted",
                    "actor_id": "claude",
                    "target_ref": "MP-377",
                }
            ]
        },
    )

    assert set(proof["proofs"]) == set(required)
    assert all(row["state"] == "satisfied" for row in proof["proofs"].values())


def test_round_proof_evidence_accepts_runtime_status_aliases() -> None:
    proof = build_loop_proof_evidence(
        loop_decision={
            "target_ref": "rev_pkt_done",
            "required_proofs": ["round_proof"],
            "satisfied_proofs": ["round_proof"],
            "missing_proofs": [],
        },
        master_plan_authority={},
        review_state={
            "round_proofs": [
                {
                    "proof_id": "round-accepted",
                    "status": "accepted",
                    "actor_id": "claude",
                    "handoff_packet_id": "rev_pkt_done",
                }
            ]
        },
    )

    assert proof["round_proof"]["state"] == "satisfied"
    assert proof["proofs"]["round_proof"]["state"] == "satisfied"


def test_wake_proof_evidence_names_operator_override_source() -> None:
    proof = build_loop_proof_evidence(
        loop_decision={
            "target_ref": "MP-377",
            "proof_state": "satisfied",
            "required_proofs": ["wake_or_attention_evidence"],
            "satisfied_proofs": ["wake_or_attention_evidence"],
            "missing_proofs": [],
            "operator_override": {
                "active": True,
                "source": "agent_loop_cli",
                "target_kind": "plan",
                "target_ref": "MP-377",
            },
        },
        master_plan_authority={},
        review_state={},
    )

    evidence = proof["proofs"]["wake_or_attention_evidence"]["evidence"]
    assert evidence["operator_override_active"] is True
    assert evidence["operator_override_source"] == "agent_loop_cli"
    assert evidence["operator_override_target_kind"] == "plan"
    assert evidence["operator_override_target_ref"] == "MP-377"
