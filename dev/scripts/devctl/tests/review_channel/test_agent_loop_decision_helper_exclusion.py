"""v4.55.2 (rev_pkt_4769/4770) regression tests for `_row_has_loop_authority`.

When `agent_work_board_projection._build_codex_session_rows` demotes a
non-conductor codex session to subagent (role_source =
"helper_session_demotion"), that row must NOT enter the agent-loop
decision set unless an explicit packet binding ties live work to that
exact helper session. Otherwise `develop next` / `develop launch`
dry-run surface a dead helper sidecar as a final-gate blocker on a
stale packet, which is precisely the rev_pkt_4767/4770 failure mode.
"""

from __future__ import annotations

from dev.scripts.devctl.review_channel.agent_loop_decision_projection import (
    _row_has_loop_authority,
)


def _helper_row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "actor_id": "codex",
        "role": "subagent",
        "role_source": "helper_session_demotion",
        "session_id": "019e4a6c-aa9b-7e03-9f83-19cf47628cf4",
        "active_packet_id": "",
        "attention_packet_id": "",
        "executing_packet_id": "",
        "confidence_class": "live",
        "stale_after_seconds": 0,
        "idle_seconds": 0,
    }
    base.update(overrides)
    return base


def _reviewer_row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "actor_id": "codex",
        "role": "reviewer",
        "role_source": "actor_authority",
        "session_id": "019e46cb-dd3c-7121-bf2f-eff8cc5fc815",
        "active_packet_id": "",
        "attention_packet_id": "",
        "executing_packet_id": "",
        "confidence_class": "live",
        "stale_after_seconds": 0,
        "idle_seconds": 0,
    }
    base.update(overrides)
    return base


def test_v4552_helper_subagent_row_without_packet_binding_lacks_loop_authority() -> None:
    """A demoted helper row with no live packet binding must not create
    an AgentLoopDecision. This closes rev_pkt_4769/4770: helper
    subagent rows are evidence-only.
    """
    assert _row_has_loop_authority(_helper_row()) is False


def test_v4552_helper_subagent_row_with_active_packet_keeps_authority() -> None:
    """An explicitly packet-bound helper row (codex's stated exception)
    still produces a decision so deliberate helper-bound work is not
    silently dropped.
    """
    assert (
        _row_has_loop_authority(_helper_row(active_packet_id="rev_pkt_4299"))
        is True
    )


def test_v4552_helper_subagent_row_with_attention_packet_keeps_authority() -> None:
    """`attention_packet_id` is also a valid packet binding signal."""
    assert (
        _row_has_loop_authority(_helper_row(attention_packet_id="rev_pkt_4299"))
        is True
    )


def test_v4552_helper_subagent_row_with_executing_packet_keeps_authority() -> None:
    """`executing_packet_id` is also a valid packet binding signal."""
    assert (
        _row_has_loop_authority(_helper_row(executing_packet_id="rev_pkt_4299"))
        is True
    )


def test_v4552_real_reviewer_row_keeps_loop_authority() -> None:
    """The real Codex reviewer (role_source='actor_authority') must NOT
    be affected by the helper-exclusion gate. Live freeze-and-spawn
    flows still need to surface as controller blockers.
    """
    assert _row_has_loop_authority(_reviewer_row()) is True


def test_v4552_non_helper_subagent_role_source_keeps_authority() -> None:
    """A subagent role from declared_role='subagent' (e.g. Claude
    subagent task files) is NOT a helper_session_demotion row and
    should retain its normal authority semantics if not stale.
    """
    row = _helper_row(role_source="session_declared_role")
    assert _row_has_loop_authority(row) is True


def test_v4552_stale_helper_row_still_excluded() -> None:
    """A helper row that is also stale stays excluded — the role_source
    check fires before the stale check.
    """
    row = _helper_row(confidence_class="stale")
    assert _row_has_loop_authority(row) is False


def test_v4552_idle_helper_row_still_excluded() -> None:
    """A helper row past idle threshold stays excluded (was already
    excluded by idle alone; this asserts the helper check also fires).
    """
    row = _helper_row(stale_after_seconds=60, idle_seconds=120)
    assert _row_has_loop_authority(row) is False
