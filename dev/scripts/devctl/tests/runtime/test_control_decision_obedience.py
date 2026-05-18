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


def test_allowed_post_finding_obeys_controller_action_routing() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_finding"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action post "
                    "--kind finding --actor codex --actor-role reviewer "
                    "--session-id codex-session"
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    assert report.ok is True


def test_allowed_post_finding_uses_argv_tokens_not_substrings() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_finding"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action post "
                    "--kind task_progress-finding --actor codex "
                    "--actor-role reviewer --session-id codex-session"
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "mutation_attempt_after_may_mutate_false" in reasons
    assert "command_attempt_after_can_run_next_command_false" in reasons


def test_allowed_post_action_request_requires_exact_stage_commit_shape() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_action_request"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "argv": (
                    "review-channel",
                    "--action",
                    "post",
                    "--kind",
                    "action_request",
                    "--requested-action",
                    "stage_commit_pipeline",
                    "--target-kind",
                    "runtime",
                    "--target-ref",
                    "devctl_commit:lifecycle_proxy_absorb_checkpoint",
                    "--target-revision",
                    "HEAD",
                    "--full-guard-bundle-evidence",
                    "bundle.tooling",
                    "--actor",
                    "codex",
                    "--actor-role",
                    "reviewer",
                    "--session-id",
                    "codex-session",
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    assert report.ok is True


def test_post_finding_does_not_authorize_action_request() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_finding"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "argv": (
                    "review-channel",
                    "--action",
                    "post",
                    "--kind",
                    "action_request",
                    "--requested-action",
                    "stage_commit_pipeline",
                    "--target-kind",
                    "runtime",
                    "--target-ref",
                    "devctl_commit:lifecycle_proxy_absorb_checkpoint",
                    "--target-revision",
                    "HEAD",
                    "--full-guard-bundle-evidence",
                    "bundle.tooling",
                    "--actor",
                    "codex",
                    "--actor-role",
                    "reviewer",
                    "--session-id",
                    "codex-session",
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "mutation_attempt_after_may_mutate_false" in reasons
    assert "command_attempt_after_can_run_next_command_false" in reasons


def test_post_action_request_rejects_wrong_requested_action() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_action_request"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "argv": (
                    "review-channel",
                    "--action",
                    "post",
                    "--kind",
                    "action_request",
                    "--requested-action",
                    "push",
                    "--target-kind",
                    "runtime",
                    "--target-ref",
                    "devctl_commit:lifecycle_proxy_absorb_checkpoint",
                    "--target-revision",
                    "HEAD",
                    "--full-guard-bundle-evidence",
                    "bundle.tooling",
                    "--actor",
                    "codex",
                    "--actor-role",
                    "reviewer",
                    "--session-id",
                    "codex-session",
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "mutation_attempt_after_may_mutate_false" in reasons
    assert "command_attempt_after_can_run_next_command_false" in reasons


def test_post_action_request_rejects_non_commit_target_ref() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_action_request"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "argv": (
                    "review-channel",
                    "--action",
                    "post",
                    "--kind",
                    "action_request",
                    "--requested-action",
                    "stage_commit_pipeline",
                    "--target-kind",
                    "runtime",
                    "--target-ref",
                    "checkpoint_authority",
                    "--target-revision",
                    "HEAD",
                    "--full-guard-bundle-evidence",
                    "bundle.tooling",
                    "--actor",
                    "codex",
                    "--actor-role",
                    "reviewer",
                    "--session-id",
                    "codex-session",
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "mutation_attempt_after_may_mutate_false" in reasons
    assert "command_attempt_after_can_run_next_command_false" in reasons


def test_allowed_post_stop_anchor_obeys_controller_action_routing() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_stop_anchor"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "argv": (
                    "review-channel",
                    "--action",
                    "post",
                    "--kind",
                    "stop_anchor",
                    "--actor",
                    "codex",
                    "--actor-role",
                    "reviewer",
                    "--session-id",
                    "codex-session",
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    assert report.ok is True


def test_post_stop_anchor_requires_stop_anchor_allowed_action() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_finding"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "argv": (
                    "review-channel",
                    "--action",
                    "post",
                    "--kind",
                    "stop_anchor",
                    "--actor",
                    "codex",
                    "--actor-role",
                    "reviewer",
                    "--session-id",
                    "codex-session",
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "mutation_attempt_after_may_mutate_false" in reasons
    assert "command_attempt_after_can_run_next_command_false" in reasons


def test_allowed_post_continuation_anchor_obeys_controller_action_routing() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_continuation_anchor"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "argv": (
                    "review-channel",
                    "--action",
                    "post",
                    "--kind",
                    "continuation_anchor",
                    "--actor",
                    "codex",
                    "--actor-role",
                    "reviewer",
                    "--session-id",
                    "codex-session",
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    assert report.ok is True


def test_post_finding_requires_kind_finding() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_finding"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action post "
                    "--kind task_progress --actor codex --actor-role reviewer "
                    "--session-id codex-session"
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "mutation_attempt_after_may_mutate_false" in reasons
    assert "command_attempt_after_can_run_next_command_false" in reasons


def test_post_finding_requires_allowed_action() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action post "
                    "--kind finding --actor codex --actor-role reviewer "
                    "--session-id codex-session"
                ),
                "actor": "codex",
                "role": "reviewer",
                "session_id": "codex-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "mutation_attempt_after_may_mutate_false" in reasons
    assert "command_attempt_after_can_run_next_command_false" in reasons


def test_post_finding_scope_must_match_loaded_decision() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "allowed_actions": ["review-channel.post_finding"],
    }

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action post "
                    "--kind finding --actor codex --actor-role dashboard "
                    "--session-id other-session"
                ),
                "actor": "codex",
                "role": "dashboard",
                "session_id": "other-session",
                "mutates": True,
                "writes_state": True,
                "executes_command": True,
            },
        ),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "attempted_action_role_scope_mismatch" in reasons
    assert "attempted_action_session_scope_mismatch" in reasons


def test_proxy_post_finding_authority_ref_must_match_loaded_decision() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "claude",
        "actor_role": "dashboard",
        "session_id": "claude-session",
        "source_snapshot_id": "agent-runtime-clock:rev_evt_1",
        "allowed_actions": ["review-channel.post_finding"],
    }
    receipt = build_attempted_action_receipt(
        action_kind="review-channel.post",
        command=(
            "python3 dev/scripts/devctl.py review-channel --action post "
            "--kind finding --actor claude --actor-role dashboard "
            "--session-id claude-session"
        ),
        actor="claude",
        role="dashboard",
        session_id="claude-session",
        executor_actor="codex",
        executor_role="reviewer",
        executor_session_id="codex-session",
        proxy_authority_ref="agent-runtime-clock:rev_evt_other",
        mutates=True,
        writes_state=True,
        executes_command=True,
    )

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(receipt.to_dict(),),
    )

    assert report.ok is False
    assert (
        "attempted_action_proxy_authority_mismatch"
        in {violation["reason"] for violation in report.violations}
    )


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


def test_attempted_action_scope_must_match_control_decision() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "session-a",
    }
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            {
                "command": (
                    "python3 dev/scripts/devctl.py review-channel --action show "
                    "--packet-id rev_pkt_4389"
                ),
                "packet_id": "rev_pkt_4389",
                "actor": "codex",
                "role": "reviewer",
                "session_id": "session-b",
            },
        ),
    )

    assert report.ok is False
    assert (
        "attempted_action_session_scope_mismatch"
        in {violation["reason"] for violation in report.violations}
    )


def test_proxy_attempt_requires_typed_authority_reference() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "claude",
        "actor_role": "dashboard",
        "session_id": "claude-session",
    }
    receipt = build_attempted_action_receipt(
        action_kind="review-channel.show",
        command=(
            "python3 dev/scripts/devctl.py review-channel --action show "
            "--packet-id rev_pkt_4389 --actor claude"
        ),
        argv=(
            "review-channel",
            "--action",
            "show",
            "--packet-id",
            "rev_pkt_4389",
            "--actor",
            "claude",
        ),
        actor="claude",
        role="dashboard",
        session_id="claude-session",
        executor_actor="codex",
        executor_role="reviewer",
        executor_session_id="codex-session",
        mutates=True,
        writes_state=True,
        executes_command=True,
    )

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(receipt.to_dict(),),
    )

    assert report.ok is False
    assert receipt.proxy_execution is True
    assert (
        "attempted_action_proxy_authority_missing"
        in {violation["reason"] for violation in report.violations}
    )


def test_proxy_attempt_records_executor_subject_and_allows_authorized_show() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "claude",
        "actor_role": "dashboard",
        "session_id": "claude-session",
        "source_snapshot_id": "agent-runtime-clock:rev_evt_1",
    }
    receipt = build_attempted_action_receipt(
        action_kind="review-channel.show",
        command=(
            "python3 dev/scripts/devctl.py review-channel --action show "
            "--packet-id rev_pkt_4389 --actor claude"
        ),
        argv=(
            "review-channel",
            "--action",
            "show",
            "--packet-id",
            "rev_pkt_4389",
            "--actor",
            "claude",
        ),
        actor="claude",
        role="dashboard",
        session_id="claude-session",
        executor_actor="codex",
        executor_role="reviewer",
        executor_session_id="codex-session",
        subject_actor="claude",
        subject_role="dashboard",
        subject_session_id="claude-session",
        proxy_authority_ref="agent-runtime-clock:rev_evt_1",
        mutates=True,
        writes_state=True,
        executes_command=True,
        source_snapshot_id="agent-runtime-clock:rev_evt_1",
    )

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(receipt.to_dict(),),
    )

    payload = receipt.to_dict()
    assert report.ok is True
    assert payload["executor_actor"] == "codex"
    assert payload["subject_actor"] == "claude"
    assert payload["proxy_execution"] is True
    assert payload["proxy_authority_ref"] == "agent-runtime-clock:rev_evt_1"


def test_proxy_authority_ref_must_match_loaded_decision_authority() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "claude",
        "actor_role": "dashboard",
        "session_id": "claude-session",
        "source_snapshot_id": "agent-runtime-clock:rev_evt_1",
    }
    receipt = build_attempted_action_receipt(
        action_kind="review-channel.show",
        command=(
            "python3 dev/scripts/devctl.py review-channel --action show "
            "--packet-id rev_pkt_4389 --actor claude"
        ),
        actor="claude",
        role="dashboard",
        session_id="claude-session",
        executor_actor="codex",
        executor_session_id="codex-session",
        proxy_authority_ref="agent-runtime-clock:rev_evt_other",
        mutates=True,
        writes_state=True,
        executes_command=True,
    )

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(receipt.to_dict(),),
    )

    assert report.ok is False
    assert (
        "attempted_action_proxy_authority_mismatch"
        in {violation["reason"] for violation in report.violations}
    )


def test_proxy_authority_requires_bound_decision_authority() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "claude",
        "actor_role": "dashboard",
        "session_id": "claude-session",
    }
    receipt = build_attempted_action_receipt(
        action_kind="review-channel.show",
        command=(
            "python3 dev/scripts/devctl.py review-channel --action show "
            "--packet-id rev_pkt_4389 --actor claude"
        ),
        actor="claude",
        role="dashboard",
        session_id="claude-session",
        executor_actor="codex",
        executor_session_id="codex-session",
        proxy_authority_ref="agent-runtime-clock:rev_evt_1",
        mutates=True,
        writes_state=True,
        executes_command=True,
    )

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(receipt.to_dict(),),
    )

    assert report.ok is False
    assert (
        "attempted_action_proxy_authority_unbound"
        in {violation["reason"] for violation in report.violations}
    )


def test_proxy_authority_does_not_allow_wrong_lifecycle_action() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "claude",
        "actor_role": "dashboard",
        "session_id": "claude-session",
        "source_snapshot_id": "agent-runtime-clock:rev_evt_1",
    }
    receipt = build_attempted_action_receipt(
        action_kind="review-channel.ingest",
        command=(
            "python3 dev/scripts/devctl.py review-channel --action ingest "
            "--packet-id rev_pkt_4389 --actor claude"
        ),
        actor="claude",
        role="dashboard",
        session_id="claude-session",
        executor_actor="codex",
        executor_session_id="codex-session",
        proxy_authority_ref="agent-runtime-clock:rev_evt_1",
        mutates=True,
        writes_state=True,
        executes_command=True,
    )

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(receipt.to_dict(),),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "non_body_open_action_after_body_open_required" in reasons


def test_proxy_authority_does_not_allow_wrong_packet() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "claude",
        "actor_role": "dashboard",
        "session_id": "claude-session",
        "source_snapshot_id": "agent-runtime-clock:rev_evt_1",
    }
    receipt = build_attempted_action_receipt(
        action_kind="review-channel.show",
        command=(
            "python3 dev/scripts/devctl.py review-channel --action show "
            "--packet-id rev_pkt_wrong --actor claude"
        ),
        actor="claude",
        role="dashboard",
        session_id="claude-session",
        executor_actor="codex",
        executor_session_id="codex-session",
        proxy_authority_ref="agent-runtime-clock:rev_evt_1",
        mutates=True,
        writes_state=True,
        executes_command=True,
    )

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(receipt.to_dict(),),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "non_packet_attention_action_after_wait_for_scoped_packet" in reasons


def test_proxy_authority_does_not_allow_wrong_subject_scope() -> None:
    decision = {
        **_blocked_decision(),
        "actor_id": "claude",
        "actor_role": "dashboard",
        "session_id": "claude-session",
        "source_snapshot_id": "agent-runtime-clock:rev_evt_1",
    }
    receipt = build_attempted_action_receipt(
        action_kind="review-channel.show",
        command=(
            "python3 dev/scripts/devctl.py review-channel --action show "
            "--packet-id rev_pkt_4389 --actor claude"
        ),
        actor="claude",
        role="subagent",
        session_id="other-session",
        executor_actor="codex",
        executor_session_id="codex-session",
        proxy_authority_ref="agent-runtime-clock:rev_evt_1",
        mutates=True,
        writes_state=True,
        executes_command=True,
    )

    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(receipt.to_dict(),),
    )

    reasons = {violation["reason"] for violation in report.violations}
    assert report.ok is False
    assert "attempted_action_role_scope_mismatch" in reasons
    assert "attempted_action_session_scope_mismatch" in reasons
