"""Tests for typed per-agent loop decisions."""

from __future__ import annotations

from dev.scripts.devctl.runtime.checkpoint_repair_authority import (
    CHECKPOINT_REPAIR_AUTHORITY_CONTRACT_ID,
    GOVERNED_CHECKPOINT_COMMIT,
    GOVERNED_CHECKPOINT_COMMIT_COMMAND,
    REPAIR_VERIFIED,
)
from dev.scripts.devctl.runtime.agent_loop_decision import build_agent_loop_decision
from dev.scripts.devctl.runtime.session_termination_policy import (
    CONTINUATION_ANCHOR_PACKET_KIND,
    SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
)


def _packet(
    *,
    packet_id: str,
    to_agent: str = "claude",
    kind: str = "action_request",
    lifecycle_current_state: str = "delivery_pending",
    status: str = "pending",
    latest_event_id: str = "rev_evt_100",
    target_role: str = "",
    target_session_id: str = "",
    target_ref: str = "",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "to_agent": to_agent,
        "kind": kind,
        "lifecycle_current_state": lifecycle_current_state,
        "status": status,
        "latest_event_id": latest_event_id,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "target_ref": target_ref,
    }


def _state(*packets: dict[str, object]) -> dict[str, object]:
    return {
        "packets": list(packets),
        "agent_sync": {},
        "agent_work_board": {"rows": []},
        "current_session": {
            "current_instruction_revision": "rev_current",
        },
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_100",
                "snapshot_id": "agent-runtime-clock:rev_evt_100",
            }
        },
    }


def _checkpoint_repair_transition() -> dict[str, object]:
    return {
        "contract_id": CHECKPOINT_REPAIR_AUTHORITY_CONTRACT_ID,
        "schema_version": 1,
        "pipeline_id": "pipeline-guard-repair",
        "generation_id": "generation-2",
        "original_block_reason": "guard_bundle_failed",
        "result": REPAIR_VERIFIED,
        "next_authorized_action": GOVERNED_CHECKPOINT_COMMIT,
        "source_action_id": "guard-action-2",
        "validation_receipt_id": "validation-receipt-2",
        "staged_tree_hash": "tree-2",
        "selected_paths": ["dev/scripts/devctl/runtime/checkpoint_repair_authority.py"],
        "checkpoint_sufficient": True,
        "blocked_raw_actions": ["git.commit", "vcs.push"],
    }


def test_dashboard_loop_observes_legacy_unscoped_packet_without_claiming_work() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(_packet(packet_id="rev_pkt_1")),
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="dashboard",
    )
    assert decision.loop_state == "observe"
    assert decision.required_action == "observe_typed_runtime"
    assert decision.active_packet_id == ""
    assert decision.legacy_unscoped_packet_id == "rev_pkt_1"
    assert decision.may_mutate is False
    assert decision.should_continue_loop is True
    assert decision.lifecycle_state == "idle"
    assert decision.decision == "wait"
    assert decision.loop_mode == "typed_event_wait"
    assert decision.recommended_cadence_seconds == 600
    assert decision.can_run_next_command is False
    assert decision.dogfood_record_allowed is False
    assert decision.proof_state == "satisfied"
    assert decision.required_proofs == ("typed_runtime_clock",)
    assert decision.next_loop_command == (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor claude --role dashboard"
    )


def test_implementer_loop_requires_session_when_multiple_sessions_exist() -> None:
    review_state = _state(_packet(packet_id="rev_pkt_1"))
    review_state["agent_work_board"] = {
        "rows": [
            {"actor_id": "claude", "role": "implementer", "session_id": "s1"},
            {"actor_id": "claude", "role": "implementer", "session_id": "s2"},
        ]
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
    )
    assert decision.loop_state == "blocked"
    assert decision.required_action == "provide_session_identity"
    assert decision.lifecycle_state == "blocked"
    assert decision.decision == "run_next_command"
    assert decision.reason == "session_identity_required"
    assert decision.should_continue_loop is False
    assert decision.loop_mode == "blocked_wait"
    assert decision.can_run_next_command is False


def test_scoped_implementer_loop_claims_matching_packet() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_scoped",
            target_role="coder",
            target_session_id="s1",
            target_ref="MP377-P0-T21",
        )
    )
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "claude",
                "role": "implementer",
                "session_id": "s1",
                "active_packet_id": "rev_pkt_scoped",
                "attention_packet_id": "rev_pkt_scoped",
                "source_event_id": "rev_evt_100",
                "mutation_mode": "live_tree",
                "granted_capabilities": ["repo.stage"],
            }
        ]
    }
    review_state["collaboration"] = {
        "actor_authorities": [
            {
                "actor_id": "claude",
                "provider": "claude",
                "live": True,
                "grants": [
                    {
                        "capability": "repo.stage",
                        "granted": True,
                    }
                ],
            }
        ]
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )
    assert decision.loop_state == "work"
    assert decision.required_action == "execute_active_packet"
    assert decision.lifecycle_state == "needs_attention"
    assert decision.decision == "pivot_to_packet"
    assert decision.active_packet_id == "rev_pkt_scoped"
    assert decision.attention_packet_id == "rev_pkt_scoped"
    assert decision.plan_target_ref == "MP377-P0-T21"
    assert decision.may_mutate is True
    assert decision.granted_capabilities == ("repo.stage",)
    assert decision.current_instruction_revision == "rev_current"
    assert decision.source_latest_event_id == "rev_evt_100"
    assert decision.loop_mode == "pivot_to_packet"
    assert decision.can_run_next_command is True
    assert decision.recommended_cadence_seconds == 30
    assert decision.proof_state == "satisfied"
    assert decision.required_proofs == (
        "typed_runtime_clock",
        "scoped_packet_target",
        "wake_or_attention_evidence",
    )


def test_same_provider_reviewer_session_does_not_inherit_implementer_grants() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_review",
            to_agent="codex",
            target_role="reviewer",
            target_session_id="codex-review",
        ),
        _packet(
            packet_id="rev_pkt_impl",
            to_agent="codex",
            target_role="implementer",
            target_session_id="codex-impl",
        ),
    )
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "codex",
                "role": "reviewer",
                "session_id": "codex-review",
                "active_packet_id": "rev_pkt_review",
                "source_event_id": "rev_evt_100",
                "mutation_mode": "read_only",
                "granted_capabilities": [],
            },
            {
                "actor_id": "codex",
                "role": "implementer",
                "session_id": "codex-impl",
                "active_packet_id": "rev_pkt_impl",
                "source_event_id": "rev_evt_100",
                "mutation_mode": "live_tree",
                "granted_capabilities": ["repo.stage"],
            },
        ]
    }
    review_state["collaboration"] = {
        "actor_authorities": [
            {
                "actor_id": "codex",
                "provider": "codex",
                "live": True,
                "grants": [{"capability": "repo.stage", "granted": True}],
            }
        ]
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
        session_id="codex-review",
    )

    assert decision.active_packet_id == "rev_pkt_review"
    assert decision.granted_capabilities == ()
    assert decision.may_mutate is False


def test_same_provider_implementer_session_uses_own_mutation_grant() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_impl",
            to_agent="codex",
            target_role="implementer",
            target_session_id="codex-impl",
        )
    )
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "codex",
                "role": "implementer",
                "session_id": "codex-impl",
                "active_packet_id": "rev_pkt_impl",
                "source_event_id": "rev_evt_100",
                "mutation_mode": "live_tree",
                "granted_capabilities": ["repo.stage"],
            }
        ]
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="implementer",
        session_id="codex-impl",
    )

    assert decision.active_packet_id == "rev_pkt_impl"
    assert decision.granted_capabilities == ("repo.stage",)
    assert decision.may_mutate is True


def test_dashboard_session_surfaces_unroutable_role_scoped_packet() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_stale_role",
            to_agent="codex",
            target_role="implementer",
            target_session_id="codex-session",
        )
    )
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "codex",
                "role": "dashboard",
                "session_id": "codex-session",
                "source_event_id": "rev_evt_100",
                "mutation_mode": "read_only",
                "granted_capabilities": [],
            }
        ]
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="dashboard",
        session_id="codex-session",
    )

    assert decision.loop_state == "work"
    assert decision.required_action == "pivot_to_attention_packet"
    assert decision.attention_packet_id == "rev_pkt_stale_role"
    assert decision.pending_packet_count == 1
    assert decision.may_mutate is False


def test_plan_mode_uses_typed_plan_row_authority() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(),
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
        loop_intent="plan",
        requested_plan_ref="MP-377",
        master_plan={
            "contract_id": "MasterPlan",
            "rows": [
                {
                    "contract_id": "PlanRow",
                    "row_id": "MP377-GUARDIR-V21",
                    "target_ref": "MP377-P0-T22",
                    "anchor_refs": ["MP-377"],
                    "status": "active",
                }
            ],
        },
    )

    assert decision.target_kind == "plan"
    assert decision.target_ref == "MP-377"
    assert "plan_target" in decision.satisfied_proofs
    assert "plan_target" not in decision.missing_proofs


def test_plan_mode_rejects_string_echo_without_plan_row() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(),
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
        loop_intent="plan",
        requested_plan_ref="MP-999",
        master_plan={
            "contract_id": "MasterPlan",
            "rows": [
                {
                    "contract_id": "PlanRow",
                    "row_id": "MP377-GUARDIR-V21",
                    "target_ref": "MP377-P0-T22",
                    "anchor_refs": ["MP-377"],
                    "status": "active",
                }
            ],
        },
    )

    assert decision.target_kind == "plan"
    assert decision.target_ref == "MP-999"
    assert "plan_target" in decision.missing_proofs
    assert "plan_target" not in decision.satisfied_proofs


def test_plan_wake_proof_uses_reported_scoped_attention() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(
            _packet(
                packet_id="rev_pkt_plan",
                to_agent="codex",
                kind="finding",
                lifecycle_current_state="pending",
            )
        ),
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
        loop_intent="plan",
        requested_plan_ref="MP-377",
        master_plan={
            "contract_id": "MasterPlan",
            "rows": [
                {
                    "contract_id": "PlanRow",
                    "row_id": "MP377-GUARDIR-V21",
                    "anchor_refs": ["MP-377"],
                    "status": "active",
                }
            ],
        },
    )

    assert decision.pivot_required is True
    assert "wake_or_attention_evidence" in decision.satisfied_proofs
    assert "wake_or_attention_evidence" not in decision.missing_proofs


def test_actor_loop_attention_uses_typed_packet_rows_over_ambiguous_singleton() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_old",
            to_agent="codex",
            kind="finding",
            lifecycle_current_state="pending",
            latest_event_id="rev_evt_101",
        ),
        _packet(
            packet_id="rev_pkt_new",
            to_agent="codex",
            kind="finding",
            lifecycle_current_state="pending",
            latest_event_id="rev_evt_103",
        ),
    )
    review_state["agent_sync"] = {
        "agents": {
            "codex": {
                "last_consumed_event_id_lower_bound": "rev_evt_100",
            }
        }
    }
    review_state["reviewer_runtime"]["packet_attention"] = {
        "observation_actor_id": "",
        "pending_packet_count": 0,
        "pivot_required": True,
        "stale_reason": "actor_identity_ambiguous",
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
    )

    assert decision.pending_packet_count == 2
    assert decision.latest_inbox_event_id == "rev_evt_103"
    assert decision.last_observed_event_id == "rev_evt_100"
    assert decision.attention_packet_id == "rev_pkt_new"
    assert decision.pivot_required is True
    assert decision.wake_required is True
    assert decision.lifecycle_state == "needs_attention"


def test_actor_loop_attention_respects_role_and_session_scope() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_match",
            to_agent="claude",
            target_role="coder",
            target_session_id="s1",
            latest_event_id="rev_evt_101",
        ),
        _packet(
            packet_id="rev_pkt_other_session",
            to_agent="claude",
            target_role="coder",
            target_session_id="s2",
            latest_event_id="rev_evt_103",
        ),
    )
    review_state["agent_sync"] = {
        "agents": {
            "claude": {
                "last_consumed_event_id_lower_bound": "rev_evt_100",
            }
        }
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )

    assert decision.pending_packet_count == 1
    assert decision.latest_inbox_event_id == "rev_evt_101"
    assert decision.attention_packet_id == "rev_pkt_match"


def test_agent_loop_ignores_stale_sync_packet_count_when_rows_are_authority() -> None:
    review_state = _state()
    review_state["agent_sync"] = {
        "agents": {
            "claude": {
                "last_consumed_event_id_lower_bound": "rev_evt_100",
                "pending_packets_to_me": [
                    "rev_pkt_3149",
                    "rev_pkt_3150",
                    "rev_pkt_3151",
                ],
            }
        }
    }
    review_state["reviewer_runtime"]["packet_attention"] = {
        "observation_actor_id": "claude",
        "observation_session_id": "s1",
        "latest_inbox_event_id": "rev_evt_101",
        "latest_attention_packet_id": "rev_pkt_3150",
        "last_observed_event_id": "rev_evt_100",
        "pending_packet_count": 3,
        "wake_required": True,
        "pivot_required": True,
        "stale_reason": "wake_required",
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: staged_index_budget_exceeded",
                "next_command": "python3.11 dev/scripts/devctl.py commit -m checkpoint",
            }
        },
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )

    assert decision.required_action == "repair_startup_authority"
    assert decision.reason_code == "repair_startup_authority"
    assert decision.decision == "run_next_command"
    assert decision.pending_packet_count == 0
    assert decision.latest_inbox_event_id == ""
    assert decision.active_packet_id == ""
    assert decision.attention_packet_id == ""


def test_agent_loop_does_not_pivot_to_archived_work_board_packet() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_3150",
            lifecycle_current_state="archived",
            status="applied",
            target_role="implementer",
            target_session_id="s1",
        )
    )
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "claude",
                "role": "implementer",
                "session_id": "s1",
                "active_packet_id": "rev_pkt_3150",
                "attention_packet_id": "rev_pkt_3150",
                "source_event_id": "rev_evt_101",
                "mutation_mode": "live_tree",
                "granted_capabilities": ["repo.stage"],
            }
        ]
    }
    review_state["reviewer_runtime"]["packet_attention"] = {
        "observation_actor_id": "claude",
        "observation_session_id": "s1",
        "latest_inbox_event_id": "rev_evt_101",
        "latest_attention_packet_id": "rev_pkt_3150",
        "last_observed_event_id": "rev_evt_100",
        "pending_packet_count": 1,
        "wake_required": True,
        "pivot_required": True,
        "stale_reason": "wake_required",
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )

    assert decision.required_action == "wait_for_scoped_packet"
    assert decision.decision == "wait"
    assert decision.pending_packet_count == 0
    assert decision.latest_inbox_event_id == ""
    assert decision.active_packet_id == ""
    assert decision.attention_packet_id == ""


def test_mutation_authority_respects_action_routing_blocks() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_scoped",
            target_role="coder",
            target_session_id="s1",
        )
    )
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "claude",
                "role": "implementer",
                "session_id": "s1",
                "active_packet_id": "rev_pkt_scoped",
                "source_event_id": "rev_evt_100",
            }
        ]
    }
    review_state["collaboration"] = {
        "actor_authorities": [
            {
                "actor_id": "claude",
                "provider": "claude",
                "live": True,
                "grants": [{"capability": "repo.stage", "granted": True}],
            }
        ]
    }
    review_state["action_routing"] = {
        "allowed_actions": ["review-channel.status"],
        "blocked_actions": ["implementation.edit", "vcs.stage"],
        "agent_lane": {"edit_gate": {"edit_allowed": False}},
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )
    assert decision.may_mutate is False
    assert decision.blocked_actions == ("implementation.edit", "vcs.stage")


def test_executing_packet_continues_current_execution() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_scoped",
            target_role="coder",
            target_session_id="s1",
            target_ref="MP377-P0-T21",
        )
    )
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "claude",
                "role": "implementer",
                "session_id": "s1",
                "active_packet_id": "rev_pkt_scoped",
                "attention_packet_id": "rev_pkt_scoped",
                "executing_packet_id": "rev_pkt_scoped",
                "source_event_id": "rev_evt_100",
            }
        ]
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )
    assert decision.lifecycle_state == "executing"
    assert decision.decision == "continue_current_execution"
    assert decision.required_action == "continue_current_execution"
    assert decision.executing_packet_id == "rev_pkt_scoped"
    assert decision.may_mutate is False
    assert decision.loop_mode == "continue_current_execution"
    assert decision.can_run_next_command is True


def test_startup_blocker_overrides_work_packet_but_keeps_loop_alive() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(
            _packet(
                packet_id="rev_pkt_1",
                lifecycle_current_state="applied",
                status="applied",
            )
        ),
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: import_index_atomicity",
                "next_action": "checkpoint_blocked_by_startup_authority:import_index_atomicity",
                "next_command": "stage missing imported file(s)",
            }
        },
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )
    assert decision.loop_state == "blocked"
    assert decision.required_action == "repair_startup_authority"
    assert decision.lifecycle_state == "blocked"
    assert decision.decision == "run_next_command"
    assert decision.should_continue_loop is True
    assert decision.safe_to_continue is False
    assert decision.may_mutate is False
    assert decision.next_command == ""
    assert decision.loop_mode == "observer_wait"
    assert decision.can_run_next_command is False
    assert decision.policy_reason == "repair_startup_authority_requires_mutation_authority"


def test_startup_repair_uses_stage_commit_capabilities_without_edit_permission() -> None:
    review_state = _state()
    review_state["collaboration"] = {
        "actor_authorities": [
            {
                "actor_id": "claude",
                "provider": "claude",
                "live": True,
                "grants": [
                    {"capability": "repo.stage", "granted": True},
                    {"capability": "repo.commit", "granted": True},
                ],
            }
        ]
    }
    review_state["action_routing"] = {
        "allowed_actions": ["startup-context.summary", "review-channel.status"],
        "blocked_actions": [
            "implementation.edit",
            "vcs.stage",
            "vcs.commit",
            "vcs.push",
        ],
        "agent_lane": {"edit_gate": {"edit_allowed": False}},
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: staged_index_budget_exceeded",
                "next_action": (
                    "checkpoint_blocked_by_startup_authority:"
                    "staged_index_budget_exceeded"
                ),
                "next_command": 'python3 dev/scripts/devctl.py commit -m "checkpoint"',
            }
        },
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )

    assert decision.loop_state == "blocked"
    assert decision.required_action == "repair_startup_authority"
    assert decision.may_mutate is True
    assert decision.can_run_next_command is True
    assert decision.next_command == 'python3 dev/scripts/devctl.py commit -m "checkpoint"'
    assert decision.loop_mode == "startup_repair"
    assert "vcs.stage" in decision.allowed_actions
    assert "vcs.commit" in decision.allowed_actions
    assert "vcs.stage" not in decision.blocked_actions
    assert "vcs.commit" not in decision.blocked_actions
    assert "implementation.edit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions


def test_agent_loop_promotes_verified_checkpoint_repair_to_governed_commit() -> None:
    review_state = _state()
    review_state["commit_pipeline"] = {
        "push_failure_transition": _checkpoint_repair_transition(),
    }
    review_state["collaboration"] = {
        "actor_authorities": [
            {
                "actor_id": "claude",
                "provider": "claude",
                "live": True,
                "grants": [
                    {"capability": "repo.stage", "granted": True},
                    {"capability": "repo.commit", "granted": True},
                ],
            }
        ]
    }
    review_state["action_routing"] = {
        "allowed_actions": ["startup-context.summary", "review-channel.status"],
        "blocked_actions": [
            "implementation.edit",
            "vcs.stage",
            "vcs.commit",
            "vcs.push",
        ],
        "agent_lane": {"edit_gate": {"edit_allowed": False}},
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: guard_bundle_failed",
                "next_action": (
                    "checkpoint_blocked_by_startup_authority:"
                    "guard_bundle_failed"
                ),
                "next_command": "python3 dev/scripts/devctl.py startup-context --repair",
            }
        },
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )

    assert decision.loop_state == "blocked"
    assert decision.required_action == GOVERNED_CHECKPOINT_COMMIT
    assert decision.next_action == GOVERNED_CHECKPOINT_COMMIT
    assert decision.next_command == GOVERNED_CHECKPOINT_COMMIT_COMMAND
    assert decision.can_run_next_command is True
    assert decision.loop_mode == GOVERNED_CHECKPOINT_COMMIT
    assert (
        decision.policy_reason
        == "checkpoint_repair_receipts_authorize_governed_commit"
    )
    assert "vcs.commit" in decision.allowed_actions
    assert "vcs.commit" not in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions


def test_agent_loop_edit_only_override_blocks_governed_checkpoint_commit() -> None:
    review_state = _state()
    review_state["commit_pipeline"] = {
        "push_failure_transition": _checkpoint_repair_transition(),
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: guard_bundle_failed",
                "next_action": (
                    "checkpoint_blocked_by_startup_authority:"
                    "guard_bundle_failed"
                ),
                "next_command": "python3 dev/scripts/devctl.py startup-context --repair",
            }
        },
        actor_id="codex",
        actor_role="implementer",
        requested_plan_ref="MP377-P0-CHECKPOINT-FAILURE-CLASSIFICATION-S1",
        operator_override_requested=True,
        operator_override_reason="operator requested scoped repair work",
    )

    assert decision.required_action == GOVERNED_CHECKPOINT_COMMIT
    assert decision.next_action == GOVERNED_CHECKPOINT_COMMIT
    assert decision.loop_mode == "operator_override_edit"
    assert decision.can_run_next_command is False
    assert decision.next_command == ""
    assert decision.operator_override.active is True
    assert "implementation.edit" in decision.allowed_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions
    assert (
        decision.policy_reason
        == "operator_override_edit_only_blocks_governed_checkpoint_commit"
    )


def test_remote_control_implementer_participant_grants_checkpoint_vcs_only() -> None:
    review_state = _state()
    review_state["collaboration"] = {
        "participants": [
            {
                "agent_id": "claude",
                "provider": "claude",
                "role": "operator",
                "live": True,
                "status": "live",
                "capture_mode": "remote-control",
            }
        ],
        "actor_authorities": [
            {
                "actor_id": "claude",
                "provider": "claude",
                "role": "reviewer",
                "live": True,
                "grants": [
                    {"capability": "repo.stage_handoff", "granted": True},
                    {"capability": "review.checkpoint", "granted": True},
                ],
            }
        ],
    }
    review_state["action_routing"] = {
        "allowed_actions": ["startup-context.summary", "review-channel.status"],
        "blocked_actions": [
            "implementation.edit",
            "vcs.stage",
            "vcs.commit",
            "vcs.push",
        ],
        "agent_lane": {"edit_gate": {"edit_allowed": False}},
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: staged_index_budget_exceeded",
                "next_action": (
                    "checkpoint_blocked_by_startup_authority:"
                    "staged_index_budget_exceeded"
                ),
                "next_command": 'python3 dev/scripts/devctl.py commit -m "checkpoint"',
            }
        },
        actor_id="claude",
        actor_role="implementer",
        session_id="remote-session",
    )

    assert decision.loop_mode == "startup_repair"
    assert decision.may_mutate is True
    assert decision.can_run_next_command is True
    assert "repo.stage" in decision.granted_capabilities
    assert "repo.commit" in decision.granted_capabilities
    assert "vcs.stage" in decision.allowed_actions
    assert "vcs.commit" in decision.allowed_actions
    assert "implementation.edit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions


def test_remote_control_checkpoint_grants_survive_empty_scoped_work_board_row() -> None:
    review_state = _state()
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "claude",
                "role": "implementer",
                "session_id": "remote-session",
                "mutation_mode": "read_only",
                "granted_capabilities": [],
            }
        ]
    }
    review_state["collaboration"] = {
        "participants": [
            {
                "agent_id": "claude",
                "provider": "claude",
                "role": "operator",
                "live": True,
                "capture_mode": "remote-control",
            }
        ],
        "actor_authorities": [
            {
                "actor_id": "claude",
                "provider": "claude",
                "role": "implementer",
                "live": True,
                "grants": [
                    {"capability": "repo.stage", "granted": True},
                    {"capability": "repo.commit", "granted": True},
                ],
            }
        ],
    }
    review_state["action_routing"] = {
        "allowed_actions": ["startup-context.summary", "review-channel.status"],
        "blocked_actions": [
            "implementation.edit",
            "vcs.stage",
            "vcs.commit",
            "vcs.push",
        ],
        "agent_lane": {"edit_gate": {"edit_allowed": False}},
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: import_index_atomicity",
                "next_action": (
                    "checkpoint_blocked_by_startup_authority:"
                    "import_index_atomicity"
                ),
                "next_command": 'python3 dev/scripts/devctl.py commit -m "checkpoint"',
            }
        },
        actor_id="claude",
        actor_role="implementer",
        session_id="remote-session",
    )

    assert decision.loop_mode == "startup_repair"
    assert decision.may_mutate is True
    assert decision.can_run_next_command is True
    assert "repo.stage" in decision.granted_capabilities
    assert "repo.commit" in decision.granted_capabilities
    assert "vcs.stage" in decision.allowed_actions
    assert "vcs.commit" in decision.allowed_actions
    assert "vcs.stage" not in decision.blocked_actions
    assert "vcs.commit" not in decision.blocked_actions
    assert "implementation.edit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions


def test_remote_control_reviewer_participant_does_not_gain_checkpoint_vcs() -> None:
    review_state = _state()
    review_state["collaboration"] = {
        "participants": [
            {
                "agent_id": "claude",
                "provider": "claude",
                "role": "operator",
                "live": True,
                "status": "live",
                "capture_mode": "remote-control",
            }
        ],
        "actor_authorities": [
            {
                "actor_id": "claude",
                "provider": "claude",
                "role": "reviewer",
                "live": True,
                "grants": [
                    {"capability": "repo.stage_handoff", "granted": True},
                    {"capability": "review.checkpoint", "granted": True},
                ],
            }
        ],
    }
    review_state["action_routing"] = {
        "allowed_actions": ["startup-context.summary", "review-channel.status"],
        "blocked_actions": [
            "implementation.edit",
            "vcs.stage",
            "vcs.commit",
            "vcs.push",
        ],
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: staged_index_budget_exceeded",
                "next_action": (
                    "checkpoint_blocked_by_startup_authority:"
                    "staged_index_budget_exceeded"
                ),
                "next_command": 'python3 dev/scripts/devctl.py commit -m "checkpoint"',
            }
        },
        actor_id="claude",
        actor_role="reviewer",
        session_id="remote-session",
    )

    assert decision.loop_mode == "observer_wait"
    assert decision.may_mutate is False
    assert "repo.stage" not in decision.granted_capabilities
    assert "repo.commit" not in decision.granted_capabilities
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions


def test_packet_attention_preempts_startup_blocker_without_mutation() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_attention",
            to_agent="codex",
            kind="finding",
            lifecycle_current_state="pending",
            latest_event_id="rev_evt_201",
        )
    )
    review_state["reviewer_runtime"]["packet_attention"] = {
        "observation_actor_id": "codex",
        "latest_inbox_event_id": "rev_evt_201",
        "latest_attention_packet_id": "rev_pkt_attention",
        "last_observed_event_id": "rev_evt_100",
        "pending_packet_count": 1,
        "wake_required": True,
        "pivot_required": True,
        "stale_reason": "wake_required",
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: staged_index_budget_exceeded",
                "next_action": (
                    "checkpoint_blocked_by_startup_authority:"
                    "staged_index_budget_exceeded"
                ),
                "next_command": "run checkpoint",
            }
        },
        actor_id="codex",
        actor_role="reviewer",
    )

    assert decision.loop_state == "blocked"
    assert decision.required_action == "triage_pending_packet"
    assert decision.lifecycle_state == "needs_attention"
    assert decision.decision == "pivot_to_packet"
    assert decision.loop_mode == "pivot_to_packet"
    assert decision.policy_reason == "packet_attention_triage_preempts_blocked_mutation"
    assert decision.safe_to_continue is False
    assert decision.may_mutate is False
    assert decision.can_run_next_command is False
    assert decision.attention_packet_id == "rev_pkt_attention"
    assert decision.wake_required is True
    assert decision.top_blocker == "startup authority: staged_index_budget_exceeded"


def test_operator_override_allows_scoped_edit_without_publication() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(_packet(packet_id="rev_pkt_1", to_agent="codex")),
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: import_index_atomicity",
                "next_action": "checkpoint_blocked_by_startup_authority:import_index_atomicity",
                "next_command": "stage missing imported file(s)",
            }
        },
        actor_id="codex",
        actor_role="reviewer",
        requested_packet_id="rev_pkt_1",
        operator_override_requested=True,
        operator_override_reason="operator directed architecture repair",
    )
    assert decision.loop_state == "blocked"
    assert decision.safe_to_continue is False
    assert decision.may_mutate is True
    assert decision.loop_mode == "operator_override_edit"
    assert decision.can_run_next_command is False
    assert decision.proof_state == "satisfied"
    assert decision.operator_override.active is True
    assert decision.operator_override.target_kind == "packet"
    assert decision.operator_override.target_ref == "rev_pkt_1"
    assert "implementation.edit" in decision.allowed_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions
    assert "do not stage, commit, or push" in decision.next_command
    assert "--operator-override" in decision.next_loop_command
    assert "--packet rev_pkt_1" in decision.next_loop_command


def test_operator_override_satisfies_plan_wake_proof_without_packet() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(),
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: staged_index_budget_exceeded",
                "next_action": (
                    "checkpoint_blocked_by_startup_authority:"
                    "staged_index_budget_exceeded"
                ),
                "next_command": "run checkpoint",
            }
        },
        actor_id="codex",
        actor_role="reviewer",
        loop_intent="plan",
        requested_plan_ref="MP-377",
        master_plan={
            "contract_id": "MasterPlan",
            "rows": [
                {
                    "contract_id": "PlanRow",
                    "row_id": "MP377-GUARDIR-V21",
                    "anchor_refs": ["MP-377"],
                    "status": "active",
                }
            ],
        },
        operator_override_requested=True,
        operator_override_reason="operator requested bypass proof",
    )

    assert decision.loop_mode == "operator_override_edit"
    assert decision.may_mutate is True
    assert decision.can_run_next_command is False
    assert decision.safe_to_continue is False
    assert decision.target_kind == "plan"
    assert decision.target_ref == "MP-377"
    assert decision.proof_state == "satisfied"
    assert "plan_target" in decision.satisfied_proofs
    assert "wake_or_attention_evidence" in decision.satisfied_proofs
    assert decision.missing_proofs == ()
    assert "vcs.commit" in decision.blocked_actions


def test_operator_override_request_command_surfaces_for_scoped_blocker() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(),
        dashboard={
            "control_plane": {
                "top_blocker": "613 expired unresolved review packet(s)",
                "next_action": "run_devctl_push",
            }
        },
        actor_id="codex",
        actor_role="reviewer",
        loop_intent="plan",
        requested_plan_ref="MP-377",
        master_plan={
            "contract_id": "MasterPlan",
            "rows": [
                {
                    "contract_id": "PlanRow",
                    "row_id": "MP377-P0-T22AN-AC",
                    "anchor_refs": ["MP-377"],
                    "status": "in_progress",
                }
            ],
        },
    )

    assert decision.required_action == "wait_for_review"
    assert decision.loop_state == "blocked"
    assert decision.may_mutate is False
    assert decision.operator_override.requested is False
    assert "--operator-override" in decision.next_command
    assert "--override-scope edit-only" in decision.next_command
    assert "--plan MP-377" in decision.next_command
    assert "expired unresolved review packet" in decision.next_command


def test_operator_override_requires_reason_and_scope_target() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(),
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: import_index_atomicity",
            }
        },
        actor_id="codex",
        actor_role="reviewer",
        operator_override_requested=True,
        operator_override_reason="",
    )
    assert decision.may_mutate is False
    assert decision.loop_mode == "observer_wait"
    assert decision.operator_override.requested is True
    assert decision.operator_override.active is False
    assert decision.operator_override.state == "reason_required"


def test_completed_handoff_stops_when_no_new_work_arrived() -> None:
    review_state = _state()
    review_state["collaboration"] = {
        "session_outcomes": [
            {
                "outcome": "completed_handoff",
                "provider": "claude",
                "session_actor_id": "claude",
                "session_actor_role": "implementer",
                "session_id": "s1",
                "source_event_id": "rev_evt_099",
                "reason": "completed_handoff",
            }
        ]
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )
    assert decision.loop_state == "done"
    assert decision.lifecycle_state == "completed"
    assert decision.decision == "stop_no_work"
    assert decision.required_action == "stop_no_work"
    assert decision.should_continue_loop is False
    assert decision.safe_to_continue is False
    assert decision.loop_mode == "await_round_proof"
    assert decision.recommended_cadence_seconds == 30
    assert decision.proof_state == "missing"
    assert "guard_bundle_or_attestation" in decision.missing_proofs
    assert "reviewer_semantic_review" in decision.missing_proofs


def test_completed_handoff_stops_only_when_round_proofs_are_satisfied() -> None:
    packet = _packet(packet_id="rev_pkt_done")
    packet["full_guard_bundle_evidence"] = "quality.guard_bundle"
    packet["lifecycle_current_state"] = "applied"
    packet["status"] = "applied"
    review_state = _state(packet)
    review_state["reviewer_runtime"]["duty_proof"] = {
        "state": "healthy",
        "semantic_review_claimed": True,
        "reviewed_diff_hash": "tree-hash",
    }
    review_state["collaboration"] = {
        "session_outcomes": [
            {
                "outcome": "completed_handoff",
                "provider": "claude",
                "session_actor_id": "claude",
                "session_actor_role": "implementer",
                "session_id": "s1",
                "source_event_id": "rev_evt_099",
                "handoff_packet_id": "rev_pkt_done",
                "reason": "completed_handoff",
            }
        ]
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
        loop_intent="iterate",
    )
    assert decision.loop_mode == "await_round_proof"
    assert decision.advance_allowed is False
    assert decision.proof_state == "missing"
    assert decision.missing_proofs == ("round_proof",)
    assert decision.recommended_cadence_seconds == 30


def test_agent_mind_review_hint_does_not_satisfy_round_review_proof() -> None:
    packet = _packet(packet_id="rev_pkt_done")
    packet["full_guard_bundle_evidence"] = "quality.guard_bundle"
    packet["lifecycle_current_state"] = "applied"
    packet["status"] = "applied"
    review_state = _state(packet)
    review_state["reviewer_runtime"]["duty_proof"] = {
        "state": "healthy",
        "semantic_review_claimed": True,
        "semantic_review_source": "agent_mind_auxiliary",
        "reviewed_diff_hash": "tree-hash",
    }
    review_state["collaboration"] = {
        "session_outcomes": [
            {
                "outcome": "completed_handoff",
                "provider": "claude",
                "session_actor_id": "claude",
                "session_actor_role": "implementer",
                "session_id": "s1",
                "handoff_packet_id": "rev_pkt_done",
            }
        ]
    }
    review_state["round_proofs"] = [
        {
            "contract_id": "RoundProof",
            "status": "accepted",
            "actor_id": "claude",
            "role": "implementer",
            "session_id": "s1",
            "handoff_packet_id": "rev_pkt_done",
        }
    ]
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
        loop_intent="iterate",
    )
    assert decision.proof_state == "missing"
    assert decision.missing_proofs == ("reviewer_semantic_review",)


def test_completed_handoff_stops_after_authoritative_round_proof() -> None:
    packet = _packet(packet_id="rev_pkt_done")
    packet["full_guard_bundle_evidence"] = "quality.guard_bundle"
    packet["lifecycle_current_state"] = "applied"
    packet["status"] = "applied"
    review_state = _state(packet)
    review_state["reviewer_runtime"]["duty_proof"] = {
        "state": "healthy",
        "semantic_review_claimed": True,
        "reviewed_diff_hash": "tree-hash",
    }
    review_state["collaboration"] = {
        "session_outcomes": [
            {
                "outcome": "completed_handoff",
                "provider": "claude",
                "session_actor_id": "claude",
                "session_actor_role": "implementer",
                "session_id": "s1",
                "source_event_id": "rev_evt_099",
                "handoff_packet_id": "rev_pkt_done",
                "reason": "completed_handoff",
            }
        ]
    }
    review_state["round_proofs"] = [
        {
            "contract_id": "RoundProof",
            "status": "accepted",
            "actor_id": "claude",
            "role": "implementer",
            "session_id": "s1",
            "handoff_packet_id": "rev_pkt_done",
        }
    ]
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
        loop_intent="iterate",
    )
    assert decision.loop_mode == "stopped"
    assert decision.advance_allowed is True
    assert decision.proof_state == "satisfied"
    assert decision.missing_proofs == ()
    assert decision.recommended_cadence_seconds == 0


def test_completed_handoff_pivots_when_new_packet_needs_attention() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_new",
            target_role="coder",
            target_session_id="s1",
            latest_event_id="rev_evt_101",
        )
    )
    review_state["reviewer_runtime"]["packet_attention"] = {
        "observation_actor_id": "claude",
        "observation_session_id": "s1",
        "latest_inbox_event_id": "rev_evt_101",
        "latest_attention_packet_id": "rev_pkt_new",
        "last_observed_event_id": "rev_evt_100",
        "pending_packet_count": 1,
        "wake_required": True,
        "pivot_required": True,
        "stale_reason": "wake_required",
    }
    review_state["collaboration"] = {
        "session_outcomes": [
            {
                "outcome": "completed_handoff",
                "provider": "claude",
                "session_actor_id": "claude",
                "session_actor_role": "implementer",
                "session_id": "s1",
                "source_event_id": "rev_evt_099",
            }
        ]
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )
    assert decision.lifecycle_state == "needs_attention"
    assert decision.decision == "pivot_to_packet"
    assert decision.required_action == "pivot_to_attention_packet"
    assert decision.active_packet_id == "rev_pkt_new"
    assert decision.wake_required is True
    assert decision.pivot_required is True
    assert decision.pending_packet_count == 1
    assert decision.latest_inbox_event_id == "rev_evt_101"
    assert decision.last_observed_event_id == "rev_evt_100"
    assert decision.loop_mode == "pivot_to_packet"


def test_completed_handoff_continues_when_policy_anchor_is_active() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_anchor",
            to_agent="claude",
            kind=CONTINUATION_ANCHOR_PACKET_KIND,
            target_role="implementer",
            target_session_id="s1",
        )
    )
    review_state["session_termination_policy"] = {
        "mode": SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
        "target_session_id": "s1",
        "anchor_packet_id": "rev_pkt_anchor",
    }
    review_state["collaboration"] = {
        "session_outcomes": [
            {
                "outcome": "completed_handoff",
                "provider": "claude",
                "session_actor_id": "claude",
                "session_actor_role": "implementer",
                "session_id": "s1",
                "source_event_id": "rev_evt_099",
            }
        ]
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )
    assert decision.loop_state == "work"
    assert decision.required_action == "continue_from_continuation_anchor"
    assert decision.lifecycle_state == "needs_attention"
    assert decision.reason_code == "continuation_anchor_active"
    assert decision.active_packet_id == "rev_pkt_anchor"
    assert decision.next_command == (
        "python3 dev/scripts/devctl.py develop next --actor claude --format md"
    )
    assert decision.loop_mode == "continue_from_continuation_anchor"
    assert decision.can_run_next_command is True
    assert decision.can_run_next_command is True


def test_unresolved_dead_session_routes_to_recovery_not_continue() -> None:
    review_state = _state()
    review_state["collaboration"] = {
        "session_outcomes": [
            {
                "outcome": "unresolved",
                "provider": "claude",
                "session_actor_id": "claude",
                "session_actor_role": "implementer",
                "session_id": "s1",
                "source_event_id": "rev_evt_099",
                "reason": "process_died",
            }
        ]
    }
    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="s1",
    )
    assert decision.lifecycle_state == "unresolved"
    assert decision.decision == "resume_or_recover"
    assert decision.required_action == "resume_or_recover_session"
    assert decision.should_continue_loop is True
    assert decision.safe_to_continue is False
    assert decision.loop_mode == "recover_or_relaunch"
    assert decision.can_run_next_command is False
