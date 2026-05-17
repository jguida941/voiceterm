from dev.scripts.checks.control_decision_obeyed.command import (
    build_report,
    render_markdown,
)


def test_control_decision_obeyed_fails_transcript_regression() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": {
                "decision": "wait",
                "required_action": "wait_for_scoped_packet",
                "may_mutate": False,
                "can_run_next_command": False,
                "operator_override": {
                    "requested": True,
                    "active": False,
                    "state": "target_required",
                },
                "next_action": "run_devctl_push",
                "top_blocker": "none",
            },
            "attempted_action": {
                "command": "python3 dev/scripts/devctl.py raw-git commit",
                "mutates": True,
            },
        }
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "mutation_attempt_after_may_mutate_false" in reasons
    assert "non_observation_action_after_wait_decision" in reasons


def test_control_decision_obeyed_empty_input_fails() -> None:
    report = build_report(report_override={})

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "no_control_decision_input" in reasons
    assert "no_attempted_action_input" in reasons


def test_control_decision_obeyed_markdown_lists_violation() -> None:
    report = build_report(report_override={})

    rendered = render_markdown(report)

    assert "# check_control_decision_obeyed" in rendered
    assert "no_control_decision_input" in rendered
