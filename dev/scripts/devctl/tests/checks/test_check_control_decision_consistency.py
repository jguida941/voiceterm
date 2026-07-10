from dev.scripts.checks.control_decision_consistency.command import (
    build_report,
    render_markdown,
)


def test_control_decision_consistency_report_fails_contradictory_agent_loop() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": {
                "decision": "wait",
                "required_action": "wait_for_scoped_packet",
                "may_mutate": False,
                "can_run_next_command": False,
                "operator_override": {"requested": True, "active": False},
                "next_action": "run_devctl_push",
                "top_blocker": "none",
            }
        }
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "push_projected_while_mutation_blocked" in reasons
    assert "mutation_projected_while_override_inactive" in reasons


def test_control_decision_consistency_markdown_lists_violation() -> None:
    report = build_report(
        report_override={
            "agent_loop_decision": {
                "decision": "wait",
                "top_blocker": "none",
            }
        }
    )

    rendered = render_markdown(report)

    assert "# check_control_decision_consistency" in rendered
    assert "wait_decision_without_blocker" in rendered


def test_control_decision_consistency_empty_input_fails() -> None:
    report = build_report(report_override={})

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "no_control_decision_input"
