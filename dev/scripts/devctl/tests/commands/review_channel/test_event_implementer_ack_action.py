from __future__ import annotations

from dev.scripts.devctl.commands.review_channel.event_implementer_ack_action import (
    _actor_is_assigned_implementer,
)


def test_implementer_ack_uses_implementation_capability_not_old_role_id() -> None:
    review_state = {
        "collaboration": {
            "role_assignments": [
                {
                    "provider": "claude",
                    "role_id": "implementation",
                    "live": True,
                }
            ]
        }
    }

    assert _actor_is_assigned_implementer(review_state, "claude") is True


def test_implementer_ack_does_not_promote_tdd_role_to_implementation() -> None:
    review_state = {
        "collaboration": {
            "role_assignments": [
                {
                    "provider": "codex",
                    "role_id": "tdd_first_role",
                    "live": True,
                }
            ]
        }
    }

    assert _actor_is_assigned_implementer(review_state, "codex") is False


def test_implementer_ack_accepts_explicit_mutation_grant_on_custom_role() -> None:
    review_state = {
        "collaboration": {
            "role_assignments": [
                {
                    "provider": "agent-x",
                    "role_id": "custom_repair_role",
                    "live": True,
                    "grants": [{"capability": "repo.write", "granted": True}],
                }
            ]
        }
    }

    assert _actor_is_assigned_implementer(review_state, "agent-x") is True
