"""Tests for the shared TERMINAL_LIFECYCLE_STATES canonical constant.

Covers R313 A8 Slice 1: extract the 4x-duplicated `_TERMINAL_LIFECYCLE_STATES`
into `packet_terminal_lifecycle_states` and recognize the two new states
emitted by the R297-#175 FOURTH LEG GovernedTransitionTypeChecker
(``closed_via_commit_anchor`` / ``closed_via_bypass_expiry``).
"""

from __future__ import annotations

import pytest

from dev.scripts.devctl.review_channel import (
    active_packet_authority,
    agent_packet_attention_scope,
    agent_sync_packet_classification,
    agent_work_board_packets,
)
from dev.scripts.devctl.review_channel.packet_terminal_lifecycle_states import (
    CONTRACT_ID,
    GOVERNED_TRANSITION_TERMINAL_STATES,
    SCHEMA_VERSION,
    TERMINAL_LIFECYCLE_STATES,
    is_terminal_lifecycle,
)


ORIGINAL_TERMINAL_STATES = (
    "applied",
    "dismissed",
    "failed",
    "archived",
    "expired",
)

R297_175_FOURTH_LEG_NEW_STATES = (
    "closed_via_commit_anchor",
    "closed_via_bypass_expiry",
)


def test_contract_metadata_present() -> None:
    assert CONTRACT_ID == "PacketTerminalLifecycleStates"
    assert isinstance(SCHEMA_VERSION, int)
    assert SCHEMA_VERSION == 1


def test_canonical_set_is_frozenset() -> None:
    # Immutability matters: consumers in 4 sites alias the same object.
    assert isinstance(TERMINAL_LIFECYCLE_STATES, frozenset)
    assert isinstance(GOVERNED_TRANSITION_TERMINAL_STATES, frozenset)


@pytest.mark.parametrize("state", ORIGINAL_TERMINAL_STATES)
def test_original_terminal_states_recognized(state: str) -> None:
    assert state in TERMINAL_LIFECYCLE_STATES
    assert is_terminal_lifecycle(state) is True


@pytest.mark.parametrize("state", R297_175_FOURTH_LEG_NEW_STATES)
def test_governed_transition_terminal_states_recognized(state: str) -> None:
    assert state in TERMINAL_LIFECYCLE_STATES
    assert state in GOVERNED_TRANSITION_TERMINAL_STATES
    assert is_terminal_lifecycle(state) is True


@pytest.mark.parametrize(
    "state",
    [
        "",
        "pending",
        "in_progress",
        "delivery_pending",
        "execution_pending",
        "acknowledged",
        "apply_pending_after_execution",
        "operator_routed",
        "task_progress",
        "totally_made_up_state",
        "Closed_Via_Commit_Anchor",  # case-sensitive negative
    ],
)
def test_non_terminal_states_not_recognized(state: str) -> None:
    assert state not in TERMINAL_LIFECYCLE_STATES
    assert is_terminal_lifecycle(state) is False


@pytest.mark.parametrize(
    "bogus",
    [None, 0, 1, 1.0, [], {}, object()],
)
def test_is_terminal_lifecycle_rejects_non_string(bogus: object) -> None:
    assert is_terminal_lifecycle(bogus) is False  # type: ignore[arg-type]


def test_four_consumer_modules_share_canonical_object() -> None:
    """All four amendment sites must alias the same canonical frozenset.

    Identity (`is`) check ensures no consumer accidentally re-derives a
    parallel set that could drift from the canonical authority.
    """
    assert active_packet_authority.TERMINAL_LIFECYCLE_STATES is TERMINAL_LIFECYCLE_STATES
    assert agent_work_board_packets.TERMINAL_LIFECYCLE_STATES is TERMINAL_LIFECYCLE_STATES
    assert (
        agent_packet_attention_scope.TERMINAL_LIFECYCLE_STATES
        is TERMINAL_LIFECYCLE_STATES
    )
    assert (
        agent_sync_packet_classification.TERMINAL_LIFECYCLE_STATES
        is TERMINAL_LIFECYCLE_STATES
    )


def test_consumer_predicate_treats_new_states_as_terminal() -> None:
    """Exercise the actual consumer path (agent_sync_packet_classification).

    ``_is_live_action_request_for_agent`` returns False once the lifecycle
    is terminal, so a row in the new R297-#175 state must be filtered out.
    """
    from dev.scripts.devctl.review_channel.agent_sync_packet_classification import (
        _is_live_action_request_for_agent,
    )

    base_row: dict[str, object] = {
        "packet_id": "rev_pkt_test_1",
        "to_agent": "claude",
        "kind": "action_request",
        "latest_event_id": "evt_000000001",
    }

    for terminal_state in (
        "closed_via_commit_anchor",
        "closed_via_bypass_expiry",
        "applied",
        "dismissed",
    ):
        row = {**base_row, "lifecycle_current_state": terminal_state}
        assert _is_live_action_request_for_agent(row, "claude") is False, (
            f"terminal state {terminal_state!r} must not count as live"
        )

    live_row = {**base_row, "lifecycle_current_state": "in_progress"}
    assert _is_live_action_request_for_agent(live_row, "claude") is True


def test_governed_transition_states_match_runtime_emitter() -> None:
    """The shared module must stay in sync with the runtime emitter.

    ``runtime.raw_git_bypass_lifecycle_closure.RAW_GIT_COMMIT_ANCHOR_STATUS``
    is the canonical writer of ``closed_via_commit_anchor``.
    """
    from dev.scripts.devctl.runtime.raw_git_bypass_lifecycle_closure import (
        RAW_GIT_COMMIT_ANCHOR_STATUS,
    )

    assert RAW_GIT_COMMIT_ANCHOR_STATUS in GOVERNED_TRANSITION_TERMINAL_STATES
    assert RAW_GIT_COMMIT_ANCHOR_STATUS in TERMINAL_LIFECYCLE_STATES
    assert is_terminal_lifecycle(RAW_GIT_COMMIT_ANCHOR_STATUS)
