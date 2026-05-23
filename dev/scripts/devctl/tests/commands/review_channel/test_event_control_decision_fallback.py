from __future__ import annotations

from dev.scripts.devctl.commands.review_channel.event_control_decision_fallback import (
    decision_allows_action,
    required_post_allowed_action,
    should_prefer_dashboard_control_decision,
)


def _args(*, action: str = "post", kind: str = "task_progress"):
    return type("Args", (), {"action": action, "kind": kind})()


def test_required_post_allowed_action_maps_packet_kind() -> None:
    assert (
        required_post_allowed_action(
            _args(kind="plan_gap_review"),
            (
                "python3",
                "dev/scripts/devctl.py",
                "review-channel",
                "--action",
                "post",
            ),
        )
        == "review-channel.post_plan_gap_review"
    )


def test_required_post_allowed_action_ignores_non_post() -> None:
    assert required_post_allowed_action(_args(action="show"), ()) == ""


def test_should_prefer_dashboard_decision_when_projection_is_stale() -> None:
    assert (
        should_prefer_dashboard_control_decision(
            args=_args(kind="task_blocked"),
            projected_decision={"allowed_actions": []},
            dashboard_decision={"allowed_actions": ["review-channel.post_task_blocked"]},
            attempted_argv=("review-channel", "--action", "post"),
        )
        is True
    )


def test_should_not_prefer_dashboard_when_projection_already_allows() -> None:
    assert (
        should_prefer_dashboard_control_decision(
            args=_args(kind="task_blocked"),
            projected_decision={"allowed_actions": ["review-channel.post_task_blocked"]},
            dashboard_decision={"allowed_actions": ["review-channel.post_task_blocked"]},
            attempted_argv=("review-channel", "--action", "post"),
        )
        is False
    )


def test_decision_allows_action_normalizes_case() -> None:
    assert decision_allows_action(
        {"allowed_actions": ["Review-Channel.Post_Task_Progress"]},
        "review-channel.post_task_progress",
    )
