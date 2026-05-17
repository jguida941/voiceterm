"""Focused tests for reviewer-follow restore policy helpers."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.reviewer_follow_restore_policy import (
    auto_relaunch_allowed,
)


def test_auto_relaunch_allowed_for_relaunch_review_loop_auto_fix() -> None:
    report = {
        "recovery_assessment": {
            "decision": {
                "action_id": "relaunch_review_loop",
                "can_auto_fix": True,
                "requires_approval": False,
            }
        }
    }

    assert auto_relaunch_allowed(report) is True


def test_auto_relaunch_allowed_refuses_relaunch_when_approval_required() -> None:
    report = {
        "recovery_assessment": {
            "decision": {
                "action_id": "relaunch_review_loop",
                "can_auto_fix": False,
                "requires_approval": True,
            }
        }
    }

    assert auto_relaunch_allowed(report) is False


def test_auto_relaunch_allowed_fails_closed_when_decision_missing() -> None:
    assert auto_relaunch_allowed({}) is False
