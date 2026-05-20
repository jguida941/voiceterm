from dev.scripts.devctl.runtime.control_decision_consistency import (
    evaluate_control_decision_consistency,
    extract_control_decisions,
)


def test_agent_loop_wait_output_blocks_mutation_even_if_next_action_mentions_push() -> None:
    output = {
        "decision": "wait",
        "required_action": "wait_for_scoped_packet",
        "may_mutate": False,
        "can_run_next_command": False,
        "next_action": "run_devctl_push",
        "top_blocker": "none",
    }

    report = evaluate_control_decision_consistency((output,), source="agent-loop")

    assert report.ok is False
    reasons = {violation["reason"] for violation in report.violations}
    assert "push_projected_while_mutation_blocked" in reasons
    assert "wait_decision_without_blocker" in reasons


def test_inactive_override_blocks_projected_mutation() -> None:
    output = {
        "operator_override": {"requested": True, "active": False},
        "may_mutate": False,
        "next_action": "raw_git_commit",
        "top_blocker": "startup authority",
    }

    report = evaluate_control_decision_consistency((output,), source="agent-loop")

    assert report.ok is False
    assert {
        violation["reason"] for violation in report.violations
    } >= {
        "mutation_projected_while_mutation_blocked",
        "mutation_projected_while_override_inactive",
    }


def test_blocked_next_command_fails() -> None:
    output = {
        "can_run_next_command": False,
        "next_command": "python3 dev/scripts/devctl.py push --execute",
        "top_blocker": "startup authority",
    }

    report = evaluate_control_decision_consistency((output,), source="agent-loop")

    assert report.ok is False
    assert report.violations[0]["reason"] == "next_command_projected_while_command_blocked"


def test_packet_lifecycle_command_is_allowed_when_command_blocked() -> None:
    output = {
        "can_run_next_command": False,
        "required_action": "ingest_packet_semantics",
        "semantic_ingestion_required": True,
        "semantic_ingestion_packet_id": "rev_pkt_4606",
        "target_kind": "packet",
        "target_ref": "rev_pkt_4606",
        "next_command": (
            "python3 dev/scripts/devctl.py review-channel --action ingest "
            "--packet-id rev_pkt_4606 --actor claude"
        ),
        "top_blocker": "packet_semantic_ingestion_required",
    }

    report = evaluate_control_decision_consistency((output,), source="agent-loop")

    assert report.ok is True


def test_packet_lifecycle_command_mismatch_fails() -> None:
    output = {
        "can_run_next_command": False,
        "required_action": "ingest_packet_semantics",
        "semantic_ingestion_required": True,
        "semantic_ingestion_packet_id": "rev_pkt_4606",
        "target_kind": "packet",
        "target_ref": "rev_pkt_4553",
        "next_command": (
            "python3 dev/scripts/devctl.py review-channel --action show "
            "--packet-id rev_pkt_4553 --actor claude"
        ),
        "top_blocker": "packet_semantic_ingestion_required",
    }

    report = evaluate_control_decision_consistency((output,), source="agent-loop")

    assert report.ok is False
    reasons = {violation["reason"] for violation in report.violations}
    assert "packet_lifecycle_next_command_mismatch" in reasons
    assert "packet_lifecycle_target_ref_mismatch" in reasons


def test_blocked_checkpoint_label_is_not_treated_as_mutation_projection() -> None:
    output = {
        "may_mutate": True,
        "can_run_next_command": False,
        "next_action": "checkpoint_blocked_by_startup_authority",
        "top_blocker": "startup authority: startup_authority_failed",
    }

    report = evaluate_control_decision_consistency((output,), source="agent-loop")

    assert report.ok is True


def test_extracts_agent_loop_decision_from_envelope() -> None:
    payload = {
        "agent_loop_decision": {
            "contract_id": "AgentLoopDecision",
            "decision": "wait",
            "top_blocker": "none",
        }
    }

    decisions = extract_control_decisions(payload)

    assert len(decisions) == 1
    assert decisions[0]["decision"] == "wait"
