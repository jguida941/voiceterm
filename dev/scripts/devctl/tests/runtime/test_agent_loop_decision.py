"""Tests for typed per-agent loop decisions."""

from __future__ import annotations

from dev.scripts.devctl.runtime.checkpoint_repair_authority import (
    CHECKPOINT_REPAIR_AUTHORITY_CONTRACT_ID,
    GOVERNED_CHECKPOINT_COMMIT,
    GOVERNED_CHECKPOINT_COMMIT_COMMAND,
    REPAIR_VERIFIED,
)
from dev.scripts.devctl.runtime.agent_loop_decision import build_agent_loop_decision
from dev.scripts.devctl.runtime.agent_loop_blocker_actions import (
    required_action_for_blocker,
)
from dev.scripts.devctl.runtime.agent_loop_operator_override import (
    AgentLoopOperatorOverride,
    EDIT_ONLY_AUTHORITY_SOURCE,
    EDIT_ONLY_EFFECTIVE_ROLE,
    EDIT_ONLY_EFFECTIVE_WORKSTREAM,
    EDIT_ONLY_OVERRIDE_SCOPE,
    OPERATOR_OVERRIDE_REQUESTOR,
    OPERATOR_OVERRIDE_SOURCE,
    apply_operator_override_actions,
    operator_override_from_bypass_lifecycle,
)
from dev.scripts.devctl.runtime.peer_collaboration_edge import (
    DevelopRole,
    PeerRelation,
    resolve_peer_collaboration_edge,
)
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BypassAuthorityScope,
    BypassEvaluationInput,
    BypassRequest,
    evaluate_bypass_request,
)
from dev.scripts.devctl.runtime.session_termination_policy import (
    CONTINUATION_ANCHOR_MISSING_ERROR,
    CONTINUATION_ANCHOR_PACKET_KIND,
    PACKET_ATTENTION_PENDING_ERROR,
    PENDING_REVIEW_PACKET_ERROR,
    SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
)
from dev.scripts.devctl.runtime.startup_blocker_decision import (
    STARTUP_AUTHORITY_NEXT_ACTION_PREFIX,
)
from dev.scripts.devctl.review_channel.packet_body_observation import (
    packet_body_digest,
)


def _packet(
    *,
    packet_id: str,
    from_agent: str = "codex",
    to_agent: str = "claude",
    kind: str = "action_request",
    body: str = "",
    lifecycle_current_state: str = "delivery_pending",
    status: str = "pending",
    latest_event_id: str = "rev_evt_100",
    target_role: str = "",
    target_session_id: str = "",
    target_ref: str = "",
    attention_urgency: str = "",
    attention_class: str = "",
) -> dict[str, object]:
    row = {
        "packet_id": packet_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "kind": kind,
        "body": body,
        "lifecycle_current_state": lifecycle_current_state,
        "status": status,
        "latest_event_id": latest_event_id,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "target_ref": target_ref,
    }
    if attention_urgency:
        row["attention_urgency"] = attention_urgency
    if attention_class:
        row["attention_class"] = attention_class
    return row


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


def _authority(
    *,
    actor_id: str,
    role: str,
    session_id: str,
    capabilities: tuple[str, ...],
    target_ref: str = "MP-377",
) -> dict[str, object]:
    return {
        "actor_id": actor_id,
        "provider": actor_id,
        "role": role,
        "live": True,
        "status": "live",
        "source": "test",
        "source_contract": "CollaborationSession",
        "session_id": session_id,
        "grants": [
            {
                "capability": capability,
                "granted": True,
                "source": "test",
                "target_kind": "plan",
                "target_ref": target_ref,
            }
            for capability in capabilities
        ],
    }


def _collaboration_authority() -> dict[str, object]:
    return {
        "contract_id": "CollaborationSession",
        "schema_version": 1,
        "current_slice": "MP-377",
        "mutation_owner": "claude",
        "verification_owner": "codex",
        "watcher_owner": "claude",
        "actor_authorities": [
            _authority(
                actor_id="claude",
                role="implementer",
                session_id="claude-impl",
                capabilities=("repo.stage", "repo.commit"),
            ),
            _authority(
                actor_id="codex",
                role="reviewer",
                session_id="codex-review",
                capabilities=("review.checkpoint", "review.finding"),
            ),
        ],
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


def test_blocker_action_prefers_typed_startup_authority_next_action() -> None:
    required_action = required_action_for_blocker(
        "human text changed",
        next_action=f"{STARTUP_AUTHORITY_NEXT_ACTION_PREFIX}import_index_atomicity",
    )

    assert required_action == "repair_startup_authority"


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
    assert decision.decision == "continue_to_goal"
    assert decision.active_packet_id == "rev_pkt_scoped"
    assert decision.attention_packet_id == "rev_pkt_scoped"
    assert decision.plan_target_ref == "MP377-P0-T21"
    assert decision.may_mutate is True
    assert decision.granted_capabilities == ("repo.stage",)
    assert decision.current_instruction_revision == "rev_current"
    assert decision.source_latest_event_id == "rev_evt_100"
    assert decision.loop_mode == "continue_to_goal"
    assert decision.can_run_next_command is True
    assert decision.recommended_cadence_seconds == 30
    assert decision.proof_state == "satisfied"
    assert decision.required_proofs == (
        "typed_runtime_clock",
        "scoped_packet_target",
        "packet_attention_evidence",
    )


def test_loop_blocks_mutation_until_peer_packet_body_is_opened() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_unread",
            from_agent="claude",
            to_agent="codex",
            kind="task_progress",
            body="Ranked architectural findings that Codex must read.",
            latest_event_id="rev_evt_101",
        )
    )

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {"next_command": "python3 dev/scripts/devctl.py push --execute"}},
        actor_id="codex",
        actor_role="implementer",
        session_id="codex-main",
    )

    assert decision.required_action == "open_packet_body"
    assert decision.safe_to_continue is False
    assert decision.may_mutate is False
    assert decision.active_packet_id == "rev_pkt_unread"
    assert decision.next_command == (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_unread --actor codex --terminal none --format md "
        "--target-role implementer --target-session-id codex-main"
    )
    assert decision.proof_state == "missing"


def test_digest_sidecar_toggle_blocks_blind_continuation_after_packet_open() -> None:
    packet = _packet(
        packet_id="rev_pkt_digest",
        from_agent="claude",
        to_agent="codex",
        kind="action_request",
        body="Operator-proxy digest is required before more implementation.",
        latest_event_id="rev_evt_101",
        target_role="implementer",
        target_session_id="codex-main",
    )
    packet["body_observation_events"] = [
        {
            "body_observed_by": "codex",
            "body_observed_role": "implementer",
            "body_observed_session_id": "codex-main",
            "body_digest": packet_body_digest(packet),
        }
    ]
    review_state = _state(packet)
    review_state["peer_awareness_policy"] = {
        "digest_sidecar_enabled": True,
        "work_class": "long_running_subprocess",
        "peer_provider": "claude",
        "digest_sidecar_provider": "claude",
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {"next_command": "python3 dev/scripts/devctl.py push --execute"}},
        actor_id="codex",
        actor_role="implementer",
        session_id="codex-main",
    )

    assert decision.required_action == "launch_peer_digest_sidecar"
    assert decision.reason_code == "peer_digest_sidecar_required"
    assert decision.safe_to_continue is False
    assert decision.may_mutate is False
    assert decision.active_packet_id == "rev_pkt_digest"
    assert "agent-mind --agent claude" in decision.next_command
    assert "--since-cursor" in decision.next_command
    assert decision.proof_state == "missing"
    assert "packet_attention_evidence" in decision.satisfied_proofs
    assert "peer_digest_sidecar_observation" in decision.missing_proofs


def test_digest_sidecar_derives_peer_from_typed_owner_lanes() -> None:
    packet = _packet(
        packet_id="rev_pkt_digest",
        from_agent="claude",
        to_agent="codex",
        kind="action_request",
        body="Opened packet still requires peer digest before continuation.",
        latest_event_id="rev_evt_101",
        target_role="reviewer",
        target_session_id="codex-review",
    )
    packet["body_observation_events"] = [
        {
            "body_observed_by": "codex",
            "body_observed_role": "reviewer",
            "body_observed_session_id": "codex-review",
            "body_digest": packet_body_digest(packet),
        }
    ]
    review_state = _state(packet)
    review_state["peer_awareness_policy"] = {
        "digest_sidecar_enabled": True,
        "work_class": "long_running_subprocess",
    }
    review_state["collaboration"] = _collaboration_authority()

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
        session_id="codex-review",
    )

    assert decision.required_action == "launch_peer_digest_sidecar"
    assert "agent-mind --agent claude" in decision.next_command


def test_digest_sidecar_derives_peer_bidirectionally_from_typed_owner_lanes() -> None:
    packet = _packet(
        packet_id="rev_pkt_digest",
        from_agent="codex",
        to_agent="claude",
        kind="action_request",
        body="Opened packet still requires peer digest before continuation.",
        latest_event_id="rev_evt_101",
        target_role="implementer",
        target_session_id="claude-impl",
    )
    packet["body_observation_events"] = [
        {
            "body_observed_by": "claude",
            "body_observed_role": "implementer",
            "body_observed_session_id": "claude-impl",
            "body_digest": packet_body_digest(packet),
        }
    ]
    review_state = _state(packet)
    review_state["peer_awareness_policy"] = {
        "digest_sidecar_enabled": True,
        "work_class": "long_running_subprocess",
    }
    review_state["collaboration"] = _collaboration_authority()

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="claude",
        actor_role="implementer",
        session_id="claude-impl",
    )

    assert decision.required_action == "launch_peer_digest_sidecar"
    assert "agent-mind --agent codex" in decision.next_command


def test_digest_sidecar_does_not_invent_codex_claude_peer_without_typed_topology() -> None:
    packet = _packet(
        packet_id="rev_pkt_digest",
        from_agent="claude",
        to_agent="codex",
        kind="action_request",
        body="Opened packet can continue when no typed peer topology exists.",
        latest_event_id="rev_evt_101",
        target_role="reviewer",
        target_session_id="codex-review",
    )
    packet["body_observation_events"] = [
        {
            "body_observed_by": "codex",
            "body_observed_role": "reviewer",
            "body_observed_session_id": "codex-review",
            "body_digest": packet_body_digest(packet),
        }
    ]
    review_state = _state(packet)
    review_state["peer_awareness_policy"] = {
        "digest_sidecar_enabled": True,
        "work_class": "long_running_subprocess",
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
        session_id="codex-review",
    )

    assert decision.required_action == "execute_active_packet"
    assert "agent-mind --agent claude" not in decision.next_command


def test_peer_collaboration_edge_carries_typed_authority_evidence() -> None:
    edge = resolve_peer_collaboration_edge(
        actor="codex",
        actor_role="reviewer",
        session_id="codex-review",
        sources=(("review_state.collaboration", _collaboration_authority()),),
    )

    assert edge is not None
    assert edge.actor.actor_id == "codex"
    assert edge.peer.actor_id == "claude"
    assert edge.actor_role == DevelopRole.REVIEWER
    assert edge.peer_role == DevelopRole.IMPLEMENTER
    assert edge.relation == PeerRelation.REVIEWS
    assert edge.scope_ref == "current_slice:MP-377"
    assert "current_slice:MP-377" in edge.evidence_refs
    assert "CollaborationSession:actor_authorities" in edge.evidence_refs


def test_peer_collaboration_edge_requires_shared_scope_evidence() -> None:
    collaboration = _collaboration_authority()
    collaboration.pop("current_slice")
    collaboration["actor_authorities"] = [
        _authority(
            actor_id="claude",
            role="implementer",
            session_id="claude-impl",
            capabilities=("repo.stage", "repo.commit"),
            target_ref="MP-400",
        ),
        _authority(
            actor_id="codex",
            role="reviewer",
            session_id="codex-review",
            capabilities=("review.checkpoint", "review.finding"),
            target_ref="MP-377",
        ),
    ]

    edge = resolve_peer_collaboration_edge(
        actor="codex",
        actor_role="reviewer",
        session_id="codex-review",
        sources=(("review_state.collaboration", collaboration),),
    )

    assert edge is None


def test_peer_collaboration_edge_does_not_resolve_from_owner_strings_only() -> None:
    edge = resolve_peer_collaboration_edge(
        actor="codex",
        actor_role="reviewer",
        session_id="codex-review",
        sources=(
            (
                "review_state.collaboration",
                {
                    "mutation_owner": "claude",
                    "verification_owner": "codex",
                    "watcher_owner": "claude",
                },
            ),
        ),
    )

    assert edge is None


def test_digest_sidecar_toggle_off_keeps_existing_packet_execution_path() -> None:
    packet = _packet(
        packet_id="rev_pkt_digest",
        from_agent="claude",
        to_agent="codex",
        kind="action_request",
        body="Opened packet can become the active work when digest is off.",
        latest_event_id="rev_evt_101",
        target_role="implementer",
        target_session_id="codex-main",
    )
    packet["body_observation_events"] = [
        {
            "body_observed_by": "codex",
            "body_observed_role": "implementer",
            "body_observed_session_id": "codex-main",
            "body_digest": packet_body_digest(packet),
        }
    ]

    decision = build_agent_loop_decision(
        review_state=_state(packet),
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="implementer",
        session_id="codex-main",
    )

    assert decision.required_action == "execute_active_packet"
    assert decision.active_packet_id == "rev_pkt_digest"
    assert decision.safe_to_continue is True


def test_digest_sidecar_toggle_continues_after_current_digest_observation() -> None:
    packet = _packet(
        packet_id="rev_pkt_digest",
        from_agent="claude",
        to_agent="codex",
        kind="action_request",
        body="Opened packet can continue once the sidecar digest is current.",
        latest_event_id="rev_evt_101",
        target_role="implementer",
        target_session_id="codex-main",
    )
    packet["body_observation_events"] = [
        {
            "body_observed_by": "codex",
            "body_observed_role": "implementer",
            "body_observed_session_id": "codex-main",
            "body_digest": packet_body_digest(packet),
        }
    ]
    review_state = _state(packet)
    review_state["peer_awareness_policy"] = {
        "digest_sidecar_enabled": True,
        "work_class": "long_running_subprocess",
        "peer_provider": "claude",
        "digest_sidecar_provider": "claude",
    }
    review_state["agent_minds"] = {
        "codex": {
            "peer_awareness": {
                "due": False,
                "last_peer_poll_at_utc": "2026-05-16T06:45:00Z",
            }
        }
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="implementer",
        session_id="codex-main",
    )

    assert decision.required_action == "execute_active_packet"
    assert decision.active_packet_id == "rev_pkt_digest"
    assert decision.safe_to_continue is True


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
    assert decision.required_action == "continue_to_goal"
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
    assert "packet_attention_evidence" in decision.satisfied_proofs
    assert "packet_attention_evidence" not in decision.missing_proofs


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


def test_actor_loop_attention_prefers_urgent_peer_packet_over_stale_active_focus() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_old",
            to_agent="codex",
            kind="task_progress",
            lifecycle_current_state="task_progress",
            latest_event_id="rev_evt_101",
            target_role="reviewer",
            target_session_id="s1",
        ),
        _packet(
            packet_id="rev_pkt_urgent",
            to_agent="codex",
            kind="task_progress",
            lifecycle_current_state="task_progress",
            latest_event_id="rev_evt_103",
            target_role="observer",
            target_session_id="s1",
            attention_urgency="urgent",
            attention_class="decision",
        ),
    )
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "codex",
                "role": "reviewer",
                "session_id": "s1",
                "active_packet_id": "rev_pkt_old",
                "attention_packet_id": "rev_pkt_old",
                "source_event_id": "rev_evt_101",
                "mutation_mode": "read_only",
                "granted_capabilities": [],
            }
        ]
    }
    review_state["agent_sync"] = {
        "agents": {
            "codex": {
                "last_consumed_event_id_lower_bound": "rev_evt_100",
            }
        }
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
        session_id="s1",
    )

    assert decision.required_action == "continue_to_goal"
    assert decision.continuation_goal == "rev_pkt_urgent"
    assert decision.active_packet_id == "rev_pkt_urgent"
    assert decision.attention_packet_id == "rev_pkt_urgent"
    assert decision.latest_inbox_event_id == "rev_evt_103"
    assert decision.pending_packet_count == 2
    assert decision.wake_required is True
    assert decision.pivot_required is True


def test_actor_loop_attention_prefers_newer_collaboration_packet_over_old_finding() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_old_finding",
            to_agent="codex",
            kind="finding",
            lifecycle_current_state="pending",
            latest_event_id="rev_evt_101",
            target_role="reviewer",
            target_session_id="s1",
        ),
        _packet(
            packet_id="rev_pkt_new_progress",
            to_agent="codex",
            kind="task_progress",
            lifecycle_current_state="task_progress",
            latest_event_id="rev_evt_103",
            target_role="reviewer",
            target_session_id="s1",
        ),
    )
    review_state["agent_sync"] = {
        "agents": {
            "codex": {
                "last_consumed_event_id_lower_bound": "rev_evt_100",
            }
        }
    }

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
        session_id="s1",
    )

    assert decision.required_action == "continue_to_goal"
    assert decision.continuation_goal == "rev_pkt_new_progress"
    assert decision.active_packet_id == "rev_pkt_new_progress"
    assert decision.attention_packet_id == "rev_pkt_new_progress"


def test_requested_packet_focus_does_not_pivot_to_higher_priority_packet() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_urgent",
            to_agent="claude",
            kind="finding",
            lifecycle_current_state="pending",
            latest_event_id="rev_evt_103",
            target_role="implementer",
            target_session_id="s1",
            attention_urgency="blocking",
        ),
        _packet(
            packet_id="rev_pkt_requested",
            to_agent="claude",
            kind="finding",
            lifecycle_current_state="pending",
            latest_event_id="rev_evt_102",
            target_role="implementer",
            target_session_id="s1",
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
        requested_packet_id="rev_pkt_requested",
    )

    assert decision.required_action == "execute_active_packet"
    assert decision.decision == "continue_to_goal"
    assert decision.active_packet_id == "rev_pkt_requested"
    assert decision.attention_packet_id == "rev_pkt_requested"
    assert decision.continuation_goal == "rev_pkt_requested"


def test_requested_observed_receipt_packet_does_not_pivot_to_other_packet() -> None:
    requested = _packet(
        packet_id="rev_pkt_requested",
        to_agent="claude",
        kind="task_produced",
        body="Observed communication-only receipt.",
        lifecycle_current_state="task_produced",
        latest_event_id="rev_evt_102",
        target_role="implementer",
        target_session_id="s1",
    )
    requested["packet_creation_binding"] = {
        "binding_target_kind": "communication_only",
    }
    requested["body_observation_events"] = [
        {
            "body_observed_by": "claude",
            "body_observed_role": "implementer",
            "body_observed_session_id": "s1",
            "body_digest": packet_body_digest(requested),
        }
    ]
    review_state = _state(
        _packet(
            packet_id="rev_pkt_other",
            to_agent="claude",
            kind="finding",
            lifecycle_current_state="pending",
            latest_event_id="rev_evt_103",
            target_role="implementer",
            target_session_id="s1",
            attention_urgency="blocking",
        ),
        requested,
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
        requested_packet_id="rev_pkt_requested",
    )

    assert decision.required_action == "wait_for_scoped_packet"
    assert decision.active_packet_id == ""
    assert decision.attention_packet_id == ""
    assert decision.continuation_goal == "typed controller goal"


def test_requested_unobserved_receipt_opens_body_before_startup_repair() -> None:
    requested = _packet(
        packet_id="rev_pkt_requested",
        from_agent="codex",
        to_agent="operator",
        kind="goal_progress",
        body="Progress receipt body.",
        lifecycle_current_state="goal_progress",
        latest_event_id="rev_evt_102",
    )
    requested["packet_creation_binding"] = {
        "binding_target_kind": "communication_only",
    }

    decision = build_agent_loop_decision(
        review_state=_state(requested),
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: import_index_atomicity",
            }
        },
        actor_id="operator",
        actor_role="operator",
        requested_packet_id="rev_pkt_requested",
    )

    assert decision.required_action == "open_packet_body"
    assert decision.reason_code == "packet_body_open_required"
    assert decision.active_packet_id == "rev_pkt_requested"
    assert decision.attention_packet_id == "rev_pkt_requested"
    assert decision.may_mutate is False
    assert decision.next_command == (
        "python3 dev/scripts/devctl.py review-channel --action show "
        "--packet-id rev_pkt_requested --actor operator --terminal none --format md "
        "--target-role operator"
    )


def test_requested_observed_receipt_does_not_become_startup_repair_packet() -> None:
    requested = _packet(
        packet_id="rev_pkt_requested",
        from_agent="codex",
        to_agent="operator",
        kind="goal_progress",
        body="Progress receipt body.",
        lifecycle_current_state="goal_progress",
        latest_event_id="rev_evt_102",
    )
    requested["packet_creation_binding"] = {
        "binding_target_kind": "communication_only",
    }
    requested["body_observation_events"] = [
        {
            "body_observed_by": "operator",
            "body_observed_role": "operator",
            "body_observed_session_id": "",
            "body_digest": packet_body_digest(requested),
        }
    ]

    decision = build_agent_loop_decision(
        review_state=_state(requested),
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: import_index_atomicity",
            }
        },
        actor_id="operator",
        actor_role="operator",
        requested_packet_id="rev_pkt_requested",
    )

    assert decision.required_action == "repair_startup_authority"
    assert decision.active_packet_id == ""
    assert decision.attention_packet_id == ""
    assert "--packet rev_pkt_requested" not in decision.next_command


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
    assert decision.next_loop_command == (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor claude --role implementer --session-id s1"
    )
    assert decision.next_command == decision.next_loop_command
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
        "checkpoint_repair_authority": _checkpoint_repair_transition(),
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


def test_agent_loop_keeps_legacy_checkpoint_repair_transition_fallback() -> None:
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

    assert decision.required_action == GOVERNED_CHECKPOINT_COMMIT
    assert decision.next_command == GOVERNED_CHECKPOINT_COMMIT_COMMAND


def test_agent_loop_edit_only_override_blocks_governed_checkpoint_commit() -> None:
    review_state = _state()
    review_state["commit_pipeline"] = {
        "checkpoint_repair_authority": _checkpoint_repair_transition(),
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
    assert decision.actor_role == "implementer"
    assert decision.effective_actor_role == "implementer"
    assert decision.effective_workstream_id == "builder"
    assert decision.effective_authority_source == "operator_override_edit_only_repair"
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
    assert decision.required_action == "continue_to_goal"
    assert decision.lifecycle_state == "needs_attention"
    assert decision.decision == "continue_to_goal"
    assert decision.loop_mode == "continue_to_goal"
    assert decision.policy_reason == "continue_to_goal_preempts_terminal_response"
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
    assert decision.actor_role == "reviewer"
    assert decision.effective_actor_role == "implementer"
    assert decision.effective_workstream_id == "builder"
    assert decision.effective_authority_source == "operator_override_edit_only_repair"
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
    assert decision.next_command == ""
    assert "operator override active" not in decision.next_command
    assert "--operator-override" in decision.next_loop_command
    assert "--packet rev_pkt_1" in decision.next_loop_command


def test_operator_override_projects_from_active_bypass_lifecycle() -> None:
    lifecycle = evaluate_bypass_request(
        BypassRequest(
            request_id="override-projection",
            scope=BypassAuthorityScope.EDIT_ONLY,
            reason="operator approved scoped repair",
            actor="operator",
            requested_at_utc="2026-05-12T16:10:00Z",
            target_surface="packet:rev_pkt_1",
            evidence_refs=("packet:rev_pkt_1",),
        ),
        BypassEvaluationInput(
            operator_signature="operator",
            ai_approval_evidence="packet:rev_pkt_3847",
            evaluated_at_utc="2026-05-12T16:10:01Z",
        ),
    )

    override = operator_override_from_bypass_lifecycle(lifecycle)

    assert override.edit_allowed is True
    assert override.target_kind == "packet"
    assert override.target_ref == "rev_pkt_1"
    assert override.effective_authority_source == EDIT_ONLY_AUTHORITY_SOURCE
    assert override.allowed_actions == (
        "startup-context.summary",
        "review-channel.status",
        "review-channel.post_finding",
        "implementation.edit",
    )


def test_operator_override_without_effective_role_does_not_grant_edit() -> None:
    override = AgentLoopOperatorOverride(
        requested=True,
        active=True,
        state="active",
        allowed_actions=("implementation.edit",),
        blocked_actions=("vcs.stage", "vcs.commit", "vcs.push"),
    )

    allowed, blocked = apply_operator_override_actions(
        allowed_actions=(),
        blocked_actions=("implementation.edit", "vcs.stage"),
        operator_override=override,
    )

    assert override.edit_allowed is False
    assert "implementation.edit" not in allowed
    assert "implementation.edit" in blocked


def test_operator_override_without_receipt_shape_does_not_grant_edit() -> None:
    override = AgentLoopOperatorOverride(
        requested=True,
        active=True,
        state="active",
        source=OPERATOR_OVERRIDE_SOURCE,
        requested_by=OPERATOR_OVERRIDE_REQUESTOR,
        scope=EDIT_ONLY_OVERRIDE_SCOPE,
        reason="operator repair",
        target_kind="packet",
        target_ref="rev_pkt_1",
        effective_actor_role=EDIT_ONLY_EFFECTIVE_ROLE,
        effective_workstream_id=EDIT_ONLY_EFFECTIVE_WORKSTREAM,
        allowed_actions=("implementation.edit",),
        blocked_actions=("vcs.stage", "vcs.commit", "vcs.push"),
    )

    assert override.edit_allowed is False


def test_operator_override_without_target_does_not_grant_edit() -> None:
    override = AgentLoopOperatorOverride(
        requested=True,
        active=True,
        state="active",
        source=OPERATOR_OVERRIDE_SOURCE,
        requested_by=OPERATOR_OVERRIDE_REQUESTOR,
        scope=EDIT_ONLY_OVERRIDE_SCOPE,
        reason="operator repair",
        effective_actor_role=EDIT_ONLY_EFFECTIVE_ROLE,
        effective_workstream_id=EDIT_ONLY_EFFECTIVE_WORKSTREAM,
        effective_authority_source=EDIT_ONLY_AUTHORITY_SOURCE,
        allowed_actions=("implementation.edit",),
        blocked_actions=("vcs.stage", "vcs.commit", "vcs.push"),
    )

    assert override.edit_allowed is False


def test_operator_override_packet_target_requires_typed_packet_evidence() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(),
        dashboard={
            "control_plane": {
                "top_blocker": "startup authority: dirty_and_untracked_budget_exceeded",
            }
        },
        actor_id="codex",
        actor_role="reviewer",
        loop_intent="packet",
        requested_packet_id="rev_pkt_1",
        operator_override_requested=True,
        operator_override_reason="operator directed architecture repair",
    )

    assert decision.operator_override.edit_allowed is True
    assert decision.proof_state == "missing"
    assert "scoped_packet_target" not in decision.satisfied_proofs
    assert "scoped_packet_target" in decision.missing_proofs


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
    assert decision.actor_role == "reviewer"
    assert decision.effective_actor_role == "implementer"
    assert decision.effective_workstream_id == "builder"
    assert decision.may_mutate is True
    assert decision.can_run_next_command is False
    assert decision.safe_to_continue is False
    assert decision.target_kind == "plan"
    assert decision.target_ref == "MP-377"
    assert decision.proof_state == "satisfied"
    assert "plan_target" in decision.satisfied_proofs
    assert "packet_attention_evidence" in decision.satisfied_proofs
    assert decision.missing_proofs == ()
    assert "vcs.commit" in decision.blocked_actions


def test_operator_override_plan_target_without_packet_continues_scoped_edit() -> None:
    decision = build_agent_loop_decision(
        review_state=_state(),
        dashboard={"now": {}},
        actor_id="codex",
        actor_role="reviewer",
        loop_intent="plan",
        requested_plan_ref="MP377-P0-CHECKPOINT-AUTOMATION-S1",
        master_plan={
            "contract_id": "MasterPlan",
            "rows": [
                {
                    "contract_id": "PlanRow",
                    "row_id": "MP377-P0-CHECKPOINT-AUTOMATION-S1",
                    "status": "active",
                }
            ],
        },
        operator_override_requested=True,
        operator_override_reason="no_scoped_active_packet",
    )

    assert decision.loop_state == "work"
    assert decision.required_action == "continue_scoped_implementation_edit"
    assert decision.lifecycle_state == "needs_attention"
    assert decision.decision == "continue_to_goal"
    assert decision.reason_code == "operator_override_edit_only_plan_target"
    assert decision.loop_mode == "operator_override_edit"
    assert decision.safe_to_continue is True
    assert decision.may_mutate is True
    assert decision.can_run_next_command is False
    assert decision.next_command == ""
    assert decision.next_loop_command.startswith(
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor codex --role reviewer --mode plan "
        "--plan MP377-P0-CHECKPOINT-AUTOMATION-S1 --operator-override"
    )
    assert decision.plan_target_ref == "MP377-P0-CHECKPOINT-AUTOMATION-S1"
    assert decision.target_kind == "plan"
    assert decision.target_ref == "MP377-P0-CHECKPOINT-AUTOMATION-S1"
    assert decision.proof_state == "satisfied"
    assert decision.missing_proofs == ()
    assert decision.operator_override.active is True
    assert decision.operator_override.target_kind == "plan"
    assert decision.operator_override.target_ref == "MP377-P0-CHECKPOINT-AUTOMATION-S1"
    assert "implementation.edit" in decision.allowed_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions
    assert (
        decision.policy_reason
        == "operator_override_edit_only_allows_scoped_implementation"
    )


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
    assert decision.gate_failure is not None
    assert decision.gate_failure.contract_id == "TypedGateFailure"
    assert decision.gate_failure.gate_id == "agent_loop.wait_for_review"
    assert decision.gate_failure.bypass_receipt_kind == "BypassReceipt"
    assert decision.gate_failure.bypass_invocation == decision.next_command
    assert (
        decision.gate_failure.exception_lifecycle_class
        == "GovernedExceptionLifecycle"
    )


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


def test_completed_handoff_waits_when_round_proof_is_missing() -> None:
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
    assert decision.should_continue_loop is True
    assert decision.safe_to_continue is False
    assert decision.loop_mode == "await_round_proof"
    assert decision.recommended_cadence_seconds == 30
    assert decision.proof_state == "missing"
    assert "guard_bundle_or_attestation" in decision.missing_proofs
    assert "reviewer_semantic_review" in decision.missing_proofs
    assert decision.next_command == decision.next_loop_command
    assert "agent-loop --format json --actor claude --role implementer --session-id s1" in (
        decision.next_command
    )


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
    assert decision.should_continue_loop is True
    assert decision.next_command == decision.next_loop_command
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
    assert decision.should_continue_loop is False
    assert decision.next_command == ""
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
    assert decision.decision == "continue_to_goal"
    assert decision.required_action == "continue_to_goal"
    assert decision.reason_code == PACKET_ATTENTION_PENDING_ERROR
    assert decision.active_packet_id == "rev_pkt_new"
    assert decision.wake_required is True
    assert decision.pivot_required is True
    assert decision.pending_packet_count == 1
    assert decision.latest_inbox_event_id == "rev_evt_101"
    assert decision.last_observed_event_id == "rev_evt_100"
    assert decision.loop_mode == "continue_to_goal"


def test_completed_handoff_cannot_stop_with_unobserved_packet_attention() -> None:
    review_state = _state()
    review_state.pop("packets")
    review_state["reviewer_runtime"]["packet_attention"] = {
        "observation_actor_id": "claude",
        "observation_session_id": "s1",
        "latest_inbox_event_id": "rev_evt_101",
        "latest_attention_packet_id": "rev_pkt_wake",
        "last_observed_event_id": "rev_evt_100",
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

    assert decision.loop_state == "blocked"
    assert decision.required_action == "continue_to_goal"
    assert decision.reason_code == PACKET_ATTENTION_PENDING_ERROR
    assert decision.active_packet_id == "rev_pkt_wake"
    assert decision.should_continue_loop is True
    assert decision.safe_to_continue is False
    assert decision.wake_required is True
    assert decision.pivot_required is True
    assert decision.next_command == (
        "python3 dev/scripts/devctl.py develop next --actor claude --format md"
    )
    assert decision.decision != "stop_no_work"


def test_completed_handoff_requires_continuation_anchor_for_keep_awake_policy() -> None:
    review_state = _state()
    review_state["session_termination_policy"] = {
        "mode": SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
        "target_session_id": "s1",
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
    assert decision.loop_state == "blocked"
    assert decision.required_action == "post_continuation_anchor"
    assert decision.reason_code == CONTINUATION_ANCHOR_MISSING_ERROR
    assert decision.should_continue_loop is True
    assert decision.safe_to_continue is False
    assert decision.next_command == (
        "python3 dev/scripts/devctl.py develop next --actor claude --format md"
    )


def test_completed_handoff_pivots_when_review_packet_is_pending_in_default_policy() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_review",
            to_agent="claude",
            kind="review_started",
            lifecycle_current_state="review_in_progress",
            target_session_id="s1",
        )
    )
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
    assert decision.loop_state == "blocked"
    assert decision.required_action == "continue_to_goal"
    assert decision.reason_code == PENDING_REVIEW_PACKET_ERROR
    assert decision.should_continue_loop is True
    assert decision.safe_to_continue is False
    assert decision.active_packet_id == "rev_pkt_review"
    assert decision.next_command == (
        "python3 dev/scripts/devctl.py develop next --actor claude --format md"
    )


def test_completed_handoff_does_not_stop_when_action_request_is_pending() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_action",
            to_agent="claude",
            kind="action_request",
            lifecycle_current_state="delivery_pending",
            target_role="implementer",
            target_session_id="s1",
        )
    )
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

    assert decision.loop_state == "blocked"
    assert decision.required_action == "continue_to_goal"
    assert decision.reason_code == PACKET_ATTENTION_PENDING_ERROR
    assert decision.active_packet_id == "rev_pkt_action"
    assert decision.should_continue_loop is True
    assert decision.safe_to_continue is False
    assert decision.wake_required is True


def test_agent_loop_invalidates_cache_on_continuation_anchor_posted() -> None:
    review_state = _state(
        _packet(
            packet_id="rev_pkt_anchor",
            to_agent="claude",
            kind=CONTINUATION_ANCHOR_PACKET_KIND,
            target_role="implementer",
            target_session_id="s1",
            latest_event_id="rev_evt_102",
        )
    )
    review_state["session_termination_policy"] = {
        "mode": SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
        "target_session_id": "s1",
        "anchor_packet_id": "rev_pkt_anchor",
    }
    review_state["agent_loop_decisions"] = [
        {
            "actor_id": "claude",
            "actor_role": "implementer",
            "session_id": "s1",
            "lifecycle_state": "completed",
            "required_action": "stop_no_work",
            "should_continue_loop": False,
        }
    ]
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
    assert decision.required_action == "continue_from_continuation_anchor"
    assert decision.active_packet_id == "rev_pkt_anchor"
    assert decision.should_continue_loop is True


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
