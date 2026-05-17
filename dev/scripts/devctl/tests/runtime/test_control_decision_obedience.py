from dev.scripts.devctl.runtime.control_decision_obedience import (
    ATTEMPTED_ACTION_RECEIPT_CONTRACT_ID,
    build_attempted_action_receipt,
    evaluate_control_decision_obedience,
    extract_decision_and_attempted_actions,
)


def _blocked_decision() -> dict[str, object]:
    return {
        "decision": "wait",
        "required_action": "wait_for_scoped_packet",
        "may_mutate": False,
        "can_run_next_command": False,
        "operator_override": {
            "requested": True,
            "active": False,
            "state": "target_required",
        },
        "active_packet_id": "rev_pkt_4389",
        "attention_packet_id": "rev_pkt_4389",
        "body_open_required": True,
    }


def test_may_mutate_false_then_raw_git_fails() -> None:
    report = evaluate_control_decision_obedience(
        decision=_blocked_decision(),
        attempted_actions=(
            {
                "command": "python3 dev/scripts/devctl.py raw-git commit",
                "mutates": True,
            },
        ),
    )

    assert report.ok is False
    reasons = {violation["reason"] for violation in report.violations}
    assert "mutation_attempt_after_may_mutate_false" in reasons
    assert "mutation_attempt_after_override_inactive" in reasons


def test_can_run_next_command_false_then_push_command_fails() -> None:
    decision = dict(_blocked_decision())
    decision["decision"] = "run_next_command"
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": "python3 dev/scripts/devctl.py push --execute",
            },
        ),
    )

    assert report.ok is False
    assert (
        "command_attempt_after_can_run_next_command_false"
        in {violation["reason"] for violation in report.violations}
    )


def test_wait_for_scoped_packet_allows_matching_show() -> None:
    report = evaluate_control_decision_obedience(
        decision=_blocked_decision(),
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action show "
                    "--packet-id rev_pkt_4389"
                ),
                "packet_id": "rev_pkt_4389",
            },
        ),
    )

    assert report.ok is True


def test_wait_for_scoped_packet_rejects_wrong_packet_show() -> None:
    report = evaluate_control_decision_obedience(
        decision=_blocked_decision(),
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action show "
                    "--packet-id rev_pkt_4390"
                ),
                "packet_id": "rev_pkt_4390",
            },
        ),
    )

    assert report.ok is False
    reasons = {violation["reason"] for violation in report.violations}
    assert "non_packet_attention_action_after_wait_for_scoped_packet" in reasons
    assert "non_body_open_action_after_body_open_required" in reasons


def test_wait_for_scoped_packet_rejects_wrong_packet_ack() -> None:
    report = evaluate_control_decision_obedience(
        decision=_blocked_decision(),
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action ack "
                    "--packet-id rev_pkt_4390"
                ),
                "packet_id": "rev_pkt_4390",
            },
        ),
    )

    assert report.ok is False
    assert (
        "non_packet_attention_action_after_wait_for_scoped_packet"
        in {violation["reason"] for violation in report.violations}
    )


def test_wait_for_scoped_packet_rejects_matching_packet_ack() -> None:
    report = evaluate_control_decision_obedience(
        decision=_blocked_decision(),
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action ack "
                    "--packet-id rev_pkt_4389"
                ),
                "packet_id": "rev_pkt_4389",
            },
        ),
    )

    assert report.ok is False
    reasons = {violation["reason"] for violation in report.violations}
    assert "command_attempt_after_can_run_next_command_false" in reasons
    assert "non_packet_attention_action_after_wait_for_scoped_packet" in reasons
    assert "non_body_open_action_after_body_open_required" in reasons


def test_semantic_ingestion_decision_allows_matching_ingest() -> None:
    decision = dict(_blocked_decision())
    decision["semantic_ingestion_required"] = True
    decision["semantic_ingestion_packet_id"] = "rev_pkt_4389"

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action ingest "
                    "--packet-id rev_pkt_4389"
                ),
                "packet_id": "rev_pkt_4389",
            },
        ),
    )

    assert report.ok is True


def test_semantic_ingestion_decision_rejects_wrong_ingest_packet() -> None:
    decision = dict(_blocked_decision())
    decision["semantic_ingestion_required"] = True
    decision["semantic_ingestion_packet_id"] = "rev_pkt_4389"

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action ingest "
                    "--packet-id rev_pkt_4390"
                ),
                "packet_id": "rev_pkt_4390",
            },
        ),
    )

    assert report.ok is False
    assert (
        "non_packet_attention_action_after_wait_for_scoped_packet"
        in {violation["reason"] for violation in report.violations}
    )


def test_wait_for_scoped_packet_without_packet_id_fails_closed() -> None:
    decision = dict(_blocked_decision())
    decision["active_packet_id"] = ""
    decision["attention_packet_id"] = ""
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action show "
                    "--packet-id rev_pkt_4389"
                ),
                "packet_id": "rev_pkt_4389",
            },
        ),
    )

    assert report.ok is False
    reasons = {violation["reason"] for violation in report.violations}
    assert "non_packet_attention_action_after_wait_for_scoped_packet" in reasons
    assert "non_body_open_action_after_body_open_required" in reasons


def test_control_decision_obedience_empty_input_fails() -> None:
    report = evaluate_control_decision_obedience(
        decision=None,
        attempted_actions=(),
    )

    assert report.ok is False
    reasons = {violation["reason"] for violation in report.violations}
    assert "no_control_decision_input" in reasons
    assert "no_attempted_action_input" in reasons


def test_attempted_action_receipt_can_drive_obedience_guard() -> None:
    receipt = build_attempted_action_receipt(
        action_kind="raw-git.commit",
        command="python3 dev/scripts/devctl.py raw-git commit -m slice",
        argv=("raw-git", "commit", "-m", "slice"),
        actor="codex",
        role="reviewer",
        session_id="session-1",
        mutates=True,
        writes_state=True,
        executes_command=True,
        source_snapshot_id="agent-runtime-clock:rev_evt_1",
        started_at_utc="2026-05-17T18:55:00Z",
    )
    payload = {
        "agent_loop_decision": _blocked_decision(),
        "attempted_action": receipt.to_dict(),
    }
    decision, actions = extract_decision_and_attempted_actions(payload)

    assert receipt.to_dict()["contract_id"] == ATTEMPTED_ACTION_RECEIPT_CONTRACT_ID
    assert len(actions) == 1
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=actions,
    )
    assert report.ok is False
    assert {
        "mutation_attempt_after_may_mutate_false",
        "command_attempt_after_can_run_next_command_false",
    }.issubset({violation["reason"] for violation in report.violations})
