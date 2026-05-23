import json
import sys
from pathlib import Path

from dev.scripts.checks import check_role_lane_mutation_authority as role_guard
from dev.scripts.checks.check_role_lane_mutation_authority import (
    ROLE_LANE_MUTATION_REASON,
    SAFE_TO_CONTINUE_FALSE_REASON,
    UNSAFE_CONTINUE_WITH_EDIT_GRANT_REASON,
    build_report,
)


def _decision(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_id": "AgentLoopDecision",
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "session-1",
        "may_mutate": False,
        "can_run_next_command": False,
        "allowed_actions": [],
        "blocked_actions": [],
        "granted_capabilities": [],
        "operator_override": {"requested": False, "active": False},
        "source_snapshot_id": "agent-runtime-clock:rev_evt_1",
        "source_latest_event_id": "rev_evt_1",
    }
    payload.update(overrides)
    return payload


def _action(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "action_kind": "implementation_edit",
        "command": "apply_patch",
        "actor": "codex",
        "role": "reviewer",
        "session_id": "session-1",
        "mutates": True,
        "writes_state": True,
        "executes_command": True,
    }
    payload.update(overrides)
    return payload


def _reasons(report: dict[str, object]) -> set[str]:
    return {
        str(violation["reason"])
        for violation in report["violations"]
        if isinstance(violation, dict)
    }


def test_claude_pre_tool_hook_runs_role_lane_guard() -> None:
    settings = json.loads(Path(".claude/settings.json").read_text(encoding="utf-8"))
    pre_tool_hooks = settings["hooks"]["PreToolUse"]
    commands = [
        hook["command"]
        for entry in pre_tool_hooks
        if entry.get("matcher") == "Edit|Write|MultiEdit"
        for hook in entry.get("hooks", [])
    ]

    assert any("check_role_lane_mutation_authority.py" in command for command in commands)
    assert any("--mode pre_mutation" in command for command in commands)
    assert any("--tool-input-stdin" in command for command in commands)


def test_reviewer_mutation_without_typed_authority_fails() -> None:
    for actor_id in ("codex", "claude", "gemini", "cursor", "reviewer_agent"):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(
                    actor_id=actor_id,
                    actor_role="reviewer",
                    session_id=f"{actor_id}-session",
                ),
                "attempted_action": _action(
                    actor=actor_id,
                    role="reviewer",
                    session_id=f"{actor_id}-session",
                ),
            }
        )

        assert report["ok"] is False, actor_id
        assert ROLE_LANE_MUTATION_REASON in _reasons(report), actor_id


def test_orchestrator_mutation_without_typed_authority_fails() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(actor_role="orchestrator"),
            "attempted_action": _action(role="orchestrator"),
        }
    )

    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_reviewer_with_typed_mutation_lease_passes() -> None:
    for actor_id in ("codex", "claude", "gemini", "cursor", "reviewer_agent"):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(
                    actor_id=actor_id,
                    actor_role="reviewer",
                    session_id=f"{actor_id}-session",
                    mutation_mode="live_tree",
                    work_scope_lease_id=f"lease-role-lane-{actor_id}",
                    may_mutate=True,
                    allowed_actions=["implementation.edit"],
                ),
                "attempted_action": _action(
                    actor=actor_id,
                    role="reviewer",
                    session_id=f"{actor_id}-session",
                ),
            }
        )

        assert report["ok"] is True, actor_id


def test_reviewer_with_bound_proxy_authority_passes() -> None:
    for reviewer, implementer in (
        ("codex", "claude"),
        ("claude", "codex"),
        ("gemini", "cursor"),
        ("reviewer_agent", "worker_agent"),
    ):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(
                    actor_id=reviewer,
                    actor_role="reviewer",
                    session_id=f"{reviewer}-session",
                    source_latest_event_id="rev_evt_55",
                ),
                "attempted_action": _action(
                    actor=implementer,
                    role="implementer",
                    session_id=f"{implementer}-session",
                    executor_actor=reviewer,
                    executor_role="reviewer",
                    executor_session_id=f"{reviewer}-session",
                    subject_actor=implementer,
                    subject_role="implementer",
                    subject_session_id=f"{implementer}-session",
                    proxy_execution=True,
                    proxy_authority_ref="rev_evt_55",
                ),
            }
        )

        assert report["ok"] is True, reviewer


def test_proxy_authority_does_not_float_across_actor_session_role() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="codex",
                actor_role="reviewer",
                session_id="codex-session",
                source_latest_event_id="rev_evt_55",
            ),
            "attempted_action": _action(
                actor="malicious_agent",
                role="future_role",
                session_id="other-session",
                executor_actor="malicious_agent",
                executor_role="future_role",
                executor_session_id="other-session",
                subject_actor="malicious_agent",
                subject_role="future_role",
                subject_session_id="other-session",
                proxy_execution=True,
                proxy_authority_ref="rev_evt_55",
            ),
        }
    )

    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_implementer_with_typed_authority_passes() -> None:
    for actor_id in ("codex", "claude", "gemini", "cursor", "worker_agent", "new_ai_agent"):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(
                    actor_id=actor_id,
                    actor_role="implementer",
                    session_id=f"{actor_id}-session",
                    may_mutate=True,
                    allowed_actions=["implementation.edit"],
                    granted_capabilities=["repo.stage"],
                    mutation_mode="live_tree",
                    work_scope_lease_id=f"lease-implementer-{actor_id}",
                ),
                "attempted_action": _action(
                    actor=actor_id,
                    role="implementer",
                    session_id=f"{actor_id}-session",
                ),
            }
        )

        assert report["ok"] is True, actor_id


def test_typed_authority_does_not_float_across_actor_session() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="codex",
                actor_role="implementer",
                session_id="codex-implementer-session",
                may_mutate=True,
                allowed_actions=["implementation.edit"],
                granted_capabilities=["repo.stage"],
                mutation_mode="live_tree",
                work_scope_lease_id="lease-implementer-codex",
            ),
            "attempted_action": _action(
                actor="claude",
                role="implementer",
                session_id="claude-implementer-session",
            ),
        }
    )

    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_provider_identity_alone_never_authorizes_mutation() -> None:
    for actor_id, actor_role in (
        ("codex", "implementer"),
        ("claude", "implementer"),
        ("codex", "reviewer"),
        ("claude", "reviewer"),
    ):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(
                    actor_id=actor_id,
                    actor_role=actor_role,
                    session_id=f"{actor_id}-{actor_role}-session",
                    may_mutate=False,
                ),
                "attempted_action": _action(
                    actor=actor_id,
                    role=actor_role,
                    session_id=f"{actor_id}-{actor_role}-session",
                ),
            }
        )

        assert report["ok"] is False, f"{actor_id}:{actor_role}"
        assert ROLE_LANE_MUTATION_REASON in _reasons(report), (
            f"{actor_id}:{actor_role}"
        )


def test_cached_hammock_read_only_roles_need_typed_authority_to_mutate() -> None:
    for role in (
        "architecture_review",
        "duplicate_scope_guard",
        "dogfood_test",
        "governance_receipt",
        "watcher",
        "codex_research",
        "orchestrator",
        "plan_steward",
        "plan-steward",
    ):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(
                    actor_id=f"{role}_agent",
                    actor_role=role,
                    session_id=f"{role}-session",
                ),
                "attempted_action": _action(
                    actor=f"{role}_agent",
                    role=role,
                    session_id=f"{role}-session",
                ),
            }
        )

        assert report["ok"] is False, role
        assert ROLE_LANE_MUTATION_REASON in _reasons(report), role


def test_cached_hammock_roles_can_do_non_mutating_audit_work() -> None:
    for role in (
        "architecture_review",
        "duplicate_scope_guard",
        "dogfood_test",
        "governance_receipt",
        "watcher",
        "codex_research",
        "orchestrator",
        "plan_steward",
        "plan-steward",
    ):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(
                    actor_id=f"{role}_agent",
                    actor_role=role,
                    session_id=f"{role}-session",
                ),
                "attempted_action": _action(
                    action_kind="role_audit",
                    command="python3 dev/scripts/devctl.py review-channel --action status",
                    actor=f"{role}_agent",
                    role=role,
                    session_id=f"{role}-session",
                    mutates=False,
                    writes_state=False,
                    executes_command=True,
                ),
            }
        )

        assert report["ok"] is True, role


def test_unknown_unbound_role_mutation_fails() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(actor_role="future_role"),
            "attempted_action": _action(role="future_role"),
        }
    )

    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_chat_only_instruction_does_not_authorize_role_switch() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_role="reviewer",
                may_mutate=True,
                allowed_actions=["implementation.edit"],
                authority_source="chat",
            ),
            "attempted_action": _action(role="implementer", authority_source="chat"),
        }
    )

    assert report["ok"] is False
    assert "projection_or_chat_authority_not_typed" in _reasons(report)


def test_controller_projection_does_not_authorize_role_switch() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_role="reviewer",
                may_mutate=True,
                allowed_actions=["implementation.edit"],
                authority_source="develop_next",
            ),
            "attempted_action": _action(
                role="implementer",
                authority_source="campaign",
            ),
        }
    )

    assert report["ok"] is False
    assert "projection_or_chat_authority_not_typed" in _reasons(report)


def test_typed_role_switch_does_not_authorize_unbound_actor_session_role() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="codex",
                actor_role="reviewer",
                session_id="codex-session",
                may_mutate=True,
                allowed_actions=["implementation.edit"],
                typed_role_switch={
                    "contract_id": "CognitiveRoleFleetAssignment",
                    "active": True,
                    "authority_source": "typed_role_session",
                    "actor_id": "codex",
                    "actor_role": "reviewer",
                    "session_id": "codex-session",
                },
            ),
            "attempted_action": _action(
                actor="other_agent",
                role="future_role",
                session_id="other-session",
            ),
        }
    )

    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_operator_override_does_not_authorize_unbound_actor_session_role() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="codex",
                actor_role="reviewer",
                session_id="codex-session",
                operator_override={
                    "requested": True,
                    "active": True,
                    "state": "active",
                    "scope": "edit-only",
                    "target_ref": "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
                    "allowed_actions": ["implementation.edit"],
                },
            ),
            "attempted_action": _action(
                actor="other_agent",
                role="future_role",
                session_id="other-session",
            ),
        }
    )

    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_loose_provider_instruction_without_review_channel_state_fails() -> None:
    for provider in ("claude", "codex", "new_ai_agent"):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(actor_role="reviewer"),
                "attempted_action": _action(
                    role="implementer",
                    instruction_source=provider,
                    target_role="implementer",
                    packet_id="",
                    source_latest_event_id="",
                ),
            }
        )

        assert report["ok"] is False, provider
        assert (
            "loose_provider_instruction_without_typed_review_channel_state"
            in _reasons(report)
        ), provider


def test_reviewer_non_runtime_action_request_handoff_transport_passes() -> None:
    for actor_id, target_actor in (("codex", "claude"), ("claude", "codex")):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(
                    actor_id=actor_id,
                    actor_role="reviewer",
                    session_id=f"{actor_id}-reviewer-session",
                    allowed_actions=["review-channel.post_action_request"],
                ),
                "attempted_action": _action(
                    action_kind="review-channel.post",
                    command=(
                        "python3 dev/scripts/devctl.py review-channel --action post "
                        f"--actor {actor_id} --actor-role reviewer "
                        f"--to-agent {target_actor} "
                        "--kind action_request --requested-action implementer_handoff "
                        "--target-kind plan --target-ref "
                        "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1 "
                        "--target-role implementer"
                    ),
                    argv=[
                        "review-channel",
                        "--action",
                        "post",
                        "--actor",
                        actor_id,
                        "--actor-role",
                        "reviewer",
                        "--to-agent",
                        target_actor,
                        "--kind",
                        "action_request",
                        "--requested-action",
                        "implementer_handoff",
                        "--target-kind",
                        "plan",
                        "--target-ref",
                        "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
                        "--target-role",
                        "implementer",
                    ],
                    actor=actor_id,
                    role="reviewer",
                    session_id=f"{actor_id}-reviewer-session",
                    mutates=True,
                    writes_state=True,
                ),
            }
        )

        assert report["ok"] is True, actor_id


def test_implementer_cannot_self_authorize_handoff_transport_from_role_name() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="codex",
                actor_role="implementer",
                session_id="codex-implementer-session",
                allowed_actions=["review-channel.post_action_request"],
            ),
            "attempted_action": _action(
                action_kind="review-channel.post",
                argv=[
                    "review-channel",
                    "--action",
                    "post",
                    "--actor",
                    "codex",
                    "--actor-role",
                    "implementer",
                    "--to-agent",
                    "claude",
                    "--kind",
                    "action_request",
                    "--requested-action",
                    "implementer_handoff",
                    "--target-kind",
                    "plan",
                    "--target-ref",
                    "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
                    "--target-role",
                    "implementer",
                ],
                actor="codex",
                role="implementer",
                session_id="codex-implementer-session",
                mutates=True,
                writes_state=True,
            ),
        }
    )

    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_reviewer_runtime_action_request_still_requires_mutation_authority() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_role="reviewer",
                allowed_actions=["review-channel.post_action_request"],
            ),
            "attempted_action": _action(
                action_kind="review-channel.post",
                command=(
                    "python3 dev/scripts/devctl.py review-channel --action post "
                    "--kind action_request --requested-action commit "
                    "--target-kind runtime --target-ref remote_commit_pipeline:p1 "
                    "--target-revision HEAD"
                ),
                argv=[
                    "review-channel",
                    "--action",
                    "post",
                    "--kind",
                    "action_request",
                    "--requested-action",
                    "commit",
                    "--target-kind",
                    "runtime",
                    "--target-ref",
                    "remote_commit_pipeline:p1",
                    "--target-revision",
                    "HEAD",
                ],
                role="reviewer",
                mutates=True,
                writes_state=True,
            ),
        }
    )

    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_non_mutating_reviewer_audit_action_passes() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(actor_role="reviewer"),
            "attempted_action": _action(
                action_kind="review_audit",
                command="python3 dev/scripts/devctl.py review-channel --action status",
                role="reviewer",
                mutates=False,
                writes_state=False,
            ),
        }
    )

    assert report["ok"] is True


def test_typed_packet_absorption_control_action_passes_for_dashboard_lane() -> None:
    for actor_id in ("claude", "codex", "dashboard_agent"):
        report = build_report(
            report_override={
                "agent_loop_decision": _decision(
                    actor_id=actor_id,
                    actor_role="dashboard",
                    session_id=f"{actor_id}-dashboard-session",
                    decision="run_next_command",
                    may_mutate=False,
                    can_run_next_command=False,
                    required_action="absorb_packet",
                    absorption_required=True,
                    absorption_packet_id="rev_pkt_4793",
                    attention_packet_id="rev_pkt_4793",
                    active_packet_id="rev_pkt_4793",
                ),
                "attempted_action": _action(
                    action_kind="next_command",
                    command=(
                        "python3 dev/scripts/devctl.py review-channel --action absorb "
                        f"--packet-id rev_pkt_4793 --actor {actor_id} --terminal none "
                        "--format md --target-role dashboard "
                        f"--target-session-id {actor_id}-dashboard-session"
                    ),
                    actor=actor_id,
                    role="dashboard",
                    session_id=f"{actor_id}-dashboard-session",
                    mutates=False,
                    writes_state=False,
                    executes_command=True,
                ),
            }
        )

        assert report["ok"] is True, actor_id


def test_packet_absorption_for_wrong_packet_still_fails() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="claude",
                actor_role="dashboard",
                session_id="claude-dashboard-session",
                decision="run_next_command",
                may_mutate=False,
                can_run_next_command=False,
                required_action="absorb_packet",
                absorption_required=True,
                absorption_packet_id="rev_pkt_4793",
                attention_packet_id="rev_pkt_4793",
            ),
            "attempted_action": _action(
                action_kind="next_command",
                command=(
                    "python3 dev/scripts/devctl.py review-channel --action absorb "
                    "--packet-id rev_pkt_wrong --actor claude --terminal none "
                    "--format md --target-role dashboard "
                    "--target-session-id claude-dashboard-session"
                ),
                actor="claude",
                role="dashboard",
                session_id="claude-dashboard-session",
                mutates=False,
                writes_state=False,
                executes_command=True,
            ),
        }
    )

    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_worktree_mutation_without_logged_attempt_fails_for_reviewer() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="claude",
                actor_role="reviewer",
                session_id="claude-reviewer-session",
            ),
            "worktree_mutations": [
                {
                    "path": "dev/scripts/devctl/runtime/current_plan_authority.py",
                    "change_status": "M",
                }
            ],
        }
    )

    assert report["ok"] is False
    assert report["mutating_action_count"] == 1
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_pre_mutation_mode_blocks_reviewer_edit_against_live_dirty_diff(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    state_path = tmp_path / "latest.json"
    state_path.write_text(
        json.dumps(
            {
                "agent_loop_decision": _decision(
                    actor_id="claude",
                    actor_role="reviewer",
                    session_id="claude-reviewer-session",
                )
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        role_guard,
        "_git_worktree_mutations",
        lambda repo_root: [
            {
                "path": "dev/scripts/devctl/runtime/foo.py",
                "change_status": "M",
                "source": "git_status",
            }
        ],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_role_lane_mutation_authority.py",
            "--mode",
            "pre_mutation",
            "--live-state-path",
            str(state_path),
            "--format",
            "json",
        ],
    )

    exit_code = role_guard.main()
    report = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_target_file_pre_mutation_blocks_reviewer_before_worktree_changes(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    state_path = tmp_path / "latest.json"
    state_path.write_text(
        json.dumps(
            {
                "agent_loop_decision": _decision(
                    actor_id="claude",
                    actor_role="reviewer",
                    session_id="claude-reviewer-session",
                )
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        role_guard,
        "_git_worktree_mutations",
        lambda repo_root: [
            {
                "path": "dev/scripts/devctl/runtime/unrelated.py",
                "change_status": "M",
                "source": "git_status",
            }
        ],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_role_lane_mutation_authority.py",
            "--mode",
            "pre_mutation",
            "--target-file",
            "dev/scripts/devctl/runtime/current_plan_authority.py",
            "--live-state-path",
            str(state_path),
            "--format",
            "json",
        ],
    )

    exit_code = role_guard.main()
    report = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert report["ok"] is False
    assert report["mutating_action_count"] == 1
    assert report["violations"][0]["detail"].strip().endswith(
        "dev/scripts/devctl/runtime/current_plan_authority.py"
    )
    assert "unrelated.py" not in json.dumps(report)
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_target_file_pre_mutation_allows_reviewer_with_typed_lease(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    state_path = tmp_path / "latest.json"
    state_path.write_text(
        json.dumps(
            {
                "agent_loop_decision": _decision(
                    actor_id="claude",
                    actor_role="reviewer",
                    session_id="claude-reviewer-session",
                    may_mutate=True,
                    mutation_mode="live_tree",
                    work_scope_lease_id="lease-claude-current-row",
                    allowed_actions=["implementation.edit"],
                )
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(role_guard, "_git_worktree_mutations", lambda repo_root: [])
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_role_lane_mutation_authority.py",
            "--mode",
            "pre_mutation",
            "--target-file",
            "dev/scripts/devctl/runtime/current_plan_authority.py",
            "--live-state-path",
            str(state_path),
            "--format",
            "json",
        ],
    )

    exit_code = role_guard.main()
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert report["ok"] is True
    assert report["mutating_action_count"] == 1


def test_tool_input_stdin_blocks_reviewer_edit_before_file_changes(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    state_path = tmp_path / "latest.json"
    state_path.write_text(
        json.dumps(
            {
                "agent_loop_decision": _decision(
                    actor_id="claude",
                    actor_role="reviewer",
                    session_id="claude-reviewer-session",
                )
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.stdin", type("Input", (), {"read": lambda self: json.dumps({
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "dev/scripts/devctl/runtime/current_plan_authority.py"
        },
    })})())
    monkeypatch.setattr(role_guard, "_git_worktree_mutations", lambda repo_root: [])
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_role_lane_mutation_authority.py",
            "--mode",
            "pre_mutation",
            "--tool-input-stdin",
            "--live-state-path",
            str(state_path),
            "--format",
            "json",
        ],
    )

    exit_code = role_guard.main()
    report = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert report["ok"] is False
    assert ROLE_LANE_MUTATION_REASON in _reasons(report)


def test_tool_input_stdin_without_file_path_fails_closed(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    state_path = tmp_path / "latest.json"
    state_path.write_text(json.dumps({"agent_loop_decision": _decision()}), encoding="utf-8")
    monkeypatch.setattr("sys.stdin", type("Input", (), {"read": lambda self: json.dumps({
        "tool_name": "Edit",
        "tool_input": {},
    })})())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_role_lane_mutation_authority.py",
            "--mode",
            "pre_mutation",
            "--tool-input-stdin",
            "--live-state-path",
            str(state_path),
            "--format",
            "json",
        ],
    )

    exit_code = role_guard.main()
    report = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert report["ok"] is False
    assert "pre_tool_target_file_missing" in _reasons(report)


def test_worktree_mutation_with_typed_lease_passes_for_reviewer() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="claude",
                actor_role="reviewer",
                session_id="claude-reviewer-session",
                may_mutate=True,
                mutation_mode="live_tree",
                work_scope_lease_id="lease-claude-reviewer-current-row",
                allowed_actions=["implementation.edit"],
            ),
            "worktree_mutations": [
                {
                    "path": "dev/scripts/devctl/runtime/current_plan_authority.py",
                    "change_status": "M",
                }
            ],
        }
    )

    assert report["ok"] is True
    assert report["mutating_action_count"] == 1


def test_worktree_mutation_with_typed_implementer_authority_passes() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="new_ai_agent",
                actor_role="implementer",
                session_id="new-ai-implementer-session",
                may_mutate=True,
                mutation_mode="live_tree",
                work_scope_lease_id="lease-implementer-current-row",
                allowed_actions=["implementation.edit"],
                granted_capabilities=["repo.stage"],
            ),
            "worktree_mutations": [
                {
                    "path": "dev/scripts/devctl/runtime/current_plan_authority.py",
                    "change_status": "M",
                }
            ],
        }
    )

    assert report["ok"] is True
    assert report["mutating_action_count"] == 1


# ---------------------------------------------------------------------------
# Invariant H: ``AgentLoopDecision`` must NOT carry a mutation grant in
# ``allowed_actions`` simultaneously with ``safe_to_continue=False`` unless an
# active scoped operator override (or BypassReceipt-derived override) covers
# the lane. Captured in ``delete_after_ingest.md`` lines 1562-1569.
#
# The typed ``AgentLoopDecision`` model strips ``implementation.edit`` in
# ``__post_init__`` when this contradiction is set in-memory, but raw fixture/
# projection/dashboard JSON can still carry the contradictory shape. The guard
# fails closed with ``unsafe_continue_with_edit_grant`` so the contradiction
# cannot smuggle past the model.
# ---------------------------------------------------------------------------


def test_invariant_h_unsafe_continue_with_edit_grant_in_allowed_actions_fails() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="codex",
                actor_role="implementer",
                session_id="codex-implementer-session",
                safe_to_continue=False,
                may_mutate=False,
                # Contradiction: raw payload carries the mutation grant
                # while safe_to_continue=False and no override is active.
                allowed_actions=["implementation.edit"],
            ),
            "attempted_action": _action(
                actor="codex",
                role="implementer",
                session_id="codex-implementer-session",
            ),
        }
    )

    assert report["ok"] is False
    reasons = _reasons(report)
    assert UNSAFE_CONTINUE_WITH_EDIT_GRANT_REASON in reasons
    # The pre-existing per-action safe_to_continue gate must still fire on
    # the same payload — both reasons are emitted so reviewers see the
    # structural contradiction AND the per-action denial.
    assert SAFE_TO_CONTINUE_FALSE_REASON in reasons


def test_invariant_h_safe_to_continue_false_with_scoped_override_passes() -> None:
    """When ``safe_to_continue=False`` BUT a scoped, active operator
    override (or BypassReceipt-derived override) explicitly allows the
    edit lane, the new contradiction rule must not fire.
    """
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="codex",
                actor_role="implementer",
                session_id="codex-implementer-session",
                safe_to_continue=False,
                may_mutate=True,
                allowed_actions=["implementation.edit"],
                operator_override={
                    "requested": True,
                    "active": True,
                    "state": "active",
                    "scope": "edit-only",
                    "target_ref": (
                        "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
                    ),
                    "allowed_actions": ["implementation.edit"],
                },
                mutation_mode="live_tree",
                work_scope_lease_id="lease-codex-edit-only",
            ),
            "attempted_action": _action(
                actor="codex",
                role="implementer",
                session_id="codex-implementer-session",
            ),
        }
    )

    assert report["ok"] is True
    assert UNSAFE_CONTINUE_WITH_EDIT_GRANT_REASON not in _reasons(report)
    assert SAFE_TO_CONTINUE_FALSE_REASON not in _reasons(report)


def test_invariant_h_safe_to_continue_false_with_non_mutation_grant_does_not_fire() -> None:
    """``safe_to_continue=False`` paired with a non-mutation grant
    (e.g. ``review-channel.show``) must not trigger Invariant H — only
    mutation-action grants in allowed_actions are contradictory with
    ``safe_to_continue=False``.
    """
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="codex",
                actor_role="reviewer",
                session_id="codex-reviewer-session",
                safe_to_continue=False,
                may_mutate=False,
                allowed_actions=["review-channel.show"],
            ),
            "attempted_action": _action(
                action_kind="review-channel.show",
                command=(
                    "python3 dev/scripts/devctl.py review-channel "
                    "--action show --packet-id rev_pkt_4839"
                ),
                actor="codex",
                role="reviewer",
                session_id="codex-reviewer-session",
                mutates=False,
                writes_state=False,
                executes_command=True,
            ),
        }
    )

    assert UNSAFE_CONTINUE_WITH_EDIT_GRANT_REASON not in _reasons(report)


def test_invariant_h_worktree_mutation_against_contradictory_decision_fails() -> None:
    """Live worktree mutation against a contradictory decision (``
    safe_to_continue=False`` + ``implementation.edit`` in allowed_actions)
    must surface ``unsafe_continue_with_edit_grant`` so the structural
    contradiction is visible even before an attempted action is logged.
    """
    report = build_report(
        report_override={
            "agent_loop_decision": _decision(
                actor_id="codex",
                actor_role="implementer",
                session_id="codex-implementer-session",
                safe_to_continue=False,
                may_mutate=False,
                allowed_actions=["implementation.edit"],
            ),
            "worktree_mutations": [
                {
                    "path": "dev/scripts/devctl/runtime/agent_loop_decision_builder.py",
                    "change_status": "M",
                }
            ],
        }
    )

    assert report["ok"] is False
    assert UNSAFE_CONTINUE_WITH_EDIT_GRANT_REASON in _reasons(report)
