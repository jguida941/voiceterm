"""Phase 0.6.A v4.30 link 9 (rev_pkt_4698 + rev_pkt_4699) consumer-refusal tests.

When ``FinalResponseGateResult.repair_command_runnable=False`` the
``/develop`` report consumer MUST NOT resurrect a command from continuation,
packet_attention, or campaign next_commands as the active
``next_step_command`` -- the typed blocker (owner/target/reason/stop_anchor)
must surface instead. Codex's rev_pkt_4699 reproduction showed the
consumer emitting a Claude-owned ingest command for a stale packet even
though the gate had refused it.
"""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.commands.development.report import (
    _final_gate_repair_command_runnable,
    _next_step_command_for_report,
)


def _gate(**overrides) -> SimpleNamespace:
    """Build a FinalResponseGateResult-like namespace for the consumer."""
    base = {
        "allow_final_response": False,
        "action": "run_next_command",
        "next_required_command": "",  # gate refused
        "user_action": "",
        "why_not_done": "",
        "blocker_owner": "",
        "blocker_target": "",
        "blocker_reason": "",
        "repair_command": "",
        "stop_anchor": "",
        "repair_command_runnable": True,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _continuation(next_required_command: str = "") -> SimpleNamespace:
    return SimpleNamespace(next_required_command=next_required_command)


def test_runnable_gate_with_empty_command_falls_back_to_continuation() -> None:
    """Baseline: when runnable=True (default), the consumer still falls back to
    continuation.next_required_command if the gate didn't emit one. This is
    the pre-link-9 behavior we MUST preserve for normal cascades."""
    result = _next_step_command_for_report(
        final_response_gate=_gate(repair_command_runnable=True),
        continuation=_continuation("python3 fallback_command.py"),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
    )
    assert result == "python3 fallback_command.py"


def test_unrunnable_gate_refuses_continuation_command() -> None:
    """v4.30 (rev_pkt_4698): when gate has marked the upstream command as
    unrunnable, consumer MUST NOT fall back to continuation.next_required_command.

    Codex's exact axis: "no consumer may resurrect a command from
    continuation.next_required_command, required_packet_command, campaign
    commands, next commands, or wrapper sources as the active
    next_step_command / next_required_command."
    """
    result = _next_step_command_for_report(
        final_response_gate=_gate(
            repair_command_runnable=False,
            blocker_owner="operator",
            blocker_reason="manual_repair_required",
            stop_anchor="stop_anchor:operator_action_required",
        ),
        continuation=_continuation("python3 stale_continuation_command.py"),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
    )
    assert result == ""  # explicit refusal; blocker fields surface via render


def test_unrunnable_gate_refuses_packet_attention_command() -> None:
    """v4.30: same refusal applies to packet_attention command fallback."""
    result = _next_step_command_for_report(
        final_response_gate=_gate(repair_command_runnable=False),
        continuation=_continuation(""),
        packet_attention_required=True,
        packet_attention_command=(
            "python3 dev/scripts/devctl.py review-channel "
            "--action ingest --packet-id rev_pkt_4654 --actor claude"
        ),
        next_commands=(),
    )
    assert result == ""  # rev_pkt_4699 exact stale-ingest case refused


def test_unrunnable_gate_refuses_campaign_next_commands() -> None:
    """v4.30: campaign-supplied next_commands fallback is also refused."""
    result = _next_step_command_for_report(
        final_response_gate=_gate(repair_command_runnable=False),
        continuation=_continuation(""),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=("python3 campaign_command.py",),
    )
    assert result == ""


def test_runnable_gate_with_explicit_command_passes_through() -> None:
    """v4.30: when the gate itself emitted a runnable command, that command
    passes through (this is the link 8 path: gate emits, consumer surfaces)."""
    result = _next_step_command_for_report(
        final_response_gate=_gate(
            next_required_command="python3 dev/scripts/devctl.py session --format json",
            repair_command_runnable=True,
        ),
        continuation=_continuation("python3 ignored.py"),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
    )
    assert "devctl.py session" in result


def test_legacy_gate_without_runnable_field_keeps_true_default() -> None:
    """v4.30: a final_response_gate produced before the field existed defaults
    to runnable=True. Consumer falls back as usual.

    Avoids the ``_truthy(None) == False`` trap that would silently disable
    every legacy gate's fallback chain.
    """
    legacy = SimpleNamespace(
        allow_final_response=False,
        action="run_next_command",
        next_required_command="",
        user_action="",
        why_not_done="",
        # Intentionally NO repair_command_runnable or blocker_* fields
    )
    result = _next_step_command_for_report(
        final_response_gate=legacy,
        continuation=_continuation("python3 fallback.py"),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
    )
    assert result == "python3 fallback.py"


def test_final_gate_repair_command_runnable_helper_unit_cases() -> None:
    """v4.30: direct unit tests on the helper for JSON-projection edge cases."""
    assert _final_gate_repair_command_runnable(SimpleNamespace()) is True
    assert (
        _final_gate_repair_command_runnable(
            SimpleNamespace(repair_command_runnable=None)
        )
        is True
    )
    assert (
        _final_gate_repair_command_runnable(
            SimpleNamespace(repair_command_runnable=True)
        )
        is True
    )
    assert (
        _final_gate_repair_command_runnable(
            SimpleNamespace(repair_command_runnable=False)
        )
        is False
    )
    # JSON projection forms
    assert (
        _final_gate_repair_command_runnable(
            SimpleNamespace(repair_command_runnable="false")
        )
        is False
    )
    assert (
        _final_gate_repair_command_runnable(
            SimpleNamespace(repair_command_runnable="0")
        )
        is False
    )
    assert (
        _final_gate_repair_command_runnable(
            SimpleNamespace(repair_command_runnable="FALSE")
        )
        is False
    )
    assert (
        _final_gate_repair_command_runnable(
            SimpleNamespace(repair_command_runnable="true")
        )
        is True
    )
    assert (
        _final_gate_repair_command_runnable(
            SimpleNamespace(repair_command_runnable="1")
        )
        is True
    )


# ---------------------------------------------------------------------------
# v4.30 link 9 follow-up (rev_pkt_4701): cross-actor command refusal at the
# /develop next consumer level. (Helper-level tests for the cross-actor
# primitive moved to ``test_command_envelope_classification.py`` in v4.31.)
# ---------------------------------------------------------------------------


def test_consumer_refuses_cross_actor_gate_command() -> None:
    """v4.30 follow-up: when the gate emits a command scoped to a different
    actor, the consumer refuses to surface it as next_step_command."""
    result = _next_step_command_for_report(
        final_response_gate=_gate(
            next_required_command=(
                "python3 dev/scripts/devctl.py review-channel "
                "--action ingest --packet-id rev_pkt_4654 --actor claude"
            ),
            repair_command_runnable=True,
        ),
        continuation=_continuation(),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
        current_actor="codex",
    )
    assert result == ""  # cross-actor refusal


def test_consumer_refuses_cross_actor_continuation_fallback() -> None:
    """v4.30 follow-up: when the fallback continuation command names a
    different actor, the consumer also refuses."""
    result = _next_step_command_for_report(
        final_response_gate=_gate(repair_command_runnable=True),
        continuation=_continuation(
            "python3 dev/scripts/devctl.py review-channel "
            "--action ingest --packet-id rev_pkt_4654 --actor claude"
        ),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
        current_actor="codex",
    )
    assert result == ""  # cross-actor continuation refused


def test_consumer_refuses_cross_actor_packet_attention_command() -> None:
    """v4.30 follow-up: packet_attention command fallback also subject to
    cross-actor refusal."""
    result = _next_step_command_for_report(
        final_response_gate=_gate(repair_command_runnable=True),
        continuation=_continuation(""),
        packet_attention_required=True,
        packet_attention_command=(
            "python3 dev/scripts/devctl.py review-channel "
            "--action ingest --packet-id rev_pkt_4654 --actor claude"
        ),
        next_commands=(),
        current_actor="codex",
    )
    assert result == ""


def test_consumer_allows_same_actor_command_through_fallback() -> None:
    """v4.30 follow-up: same-actor commands pass through all fallback paths."""
    same_actor_command = (
        "python3 dev/scripts/devctl.py session --actor codex --format json"
    )
    # Through continuation
    result = _next_step_command_for_report(
        final_response_gate=_gate(repair_command_runnable=True),
        continuation=_continuation(same_actor_command),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
        current_actor="codex",
    )
    assert "--actor codex" in result


def test_legacy_consumer_without_current_actor_preserves_behavior() -> None:
    """v4.30 follow-up: callers that don't plumb current_actor (or pass "")
    keep the legacy fallback chain working. No silent refusal."""
    legacy_command = (
        "python3 dev/scripts/devctl.py review-channel "
        "--action ingest --packet-id rev_pkt_4654 --actor claude"
    )
    result = _next_step_command_for_report(
        final_response_gate=_gate(repair_command_runnable=True),
        continuation=_continuation(legacy_command),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
        # current_actor omitted → defaults to "" → no cross-actor refusal
    )
    assert "rev_pkt_4654" in result  # legacy behavior preserved


# ---------------------------------------------------------------------------
# v4.31 (rev_pkt_4705): proxy-positive tests — cross-actor with typed proxy
# authority renders normally instead of refusing.
# ---------------------------------------------------------------------------


def test_consumer_renders_cross_actor_gate_command_with_bound_proxy() -> None:
    """v4.32 (rev_pkt_4706): a Claude-targeted gate command surfaces for a
    Codex consumer when ``proxy_authority_ref`` is BOUND to the active
    decision's authority refs."""
    cross_actor_cmd = (
        "python3 dev/scripts/devctl.py review-channel "
        "--action ingest --packet-id rev_pkt_4654 --actor claude"
    )
    result = _next_step_command_for_report(
        final_response_gate=_gate(
            next_required_command=cross_actor_cmd,
            repair_command_runnable=True,
        ),
        continuation=_continuation(),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
        current_actor="codex",
        proxy_authority_ref="decision:proxied_codex_to_claude_2026_05_21",
        decision_authority_refs=(
            "decision:proxied_codex_to_claude_2026_05_21",
            "snapshot:cps_2026_05_21",
        ),
    )
    assert result == cross_actor_cmd  # bound proxy unlocked cross-actor


def test_consumer_refuses_cross_actor_gate_command_with_unbound_proxy() -> None:
    """v4.32 closure: ``proxy_authority_ref`` alone (without
    ``decision_authority_refs``) is NOT enough. The consumer must still
    refuse the cross-actor command."""
    cross_actor_cmd = (
        "python3 dev/scripts/devctl.py review-channel "
        "--action ingest --packet-id rev_pkt_4654 --actor claude"
    )
    result = _next_step_command_for_report(
        final_response_gate=_gate(
            next_required_command=cross_actor_cmd,
            repair_command_runnable=True,
        ),
        continuation=_continuation(),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
        current_actor="codex",
        proxy_authority_ref="decision:claimed_but_unverified",
        # decision_authority_refs omitted → unbound → refused
    )
    assert result == ""


def test_consumer_renders_cross_actor_continuation_with_bound_proxy() -> None:
    """v4.32: bound proxy authority also applies on the fallback
    continuation path, not just the gate."""
    cross_actor_cmd = (
        "python3 dev/scripts/devctl.py review-channel "
        "--action ingest --packet-id rev_pkt_4654 --actor claude"
    )
    result = _next_step_command_for_report(
        final_response_gate=_gate(repair_command_runnable=True),
        continuation=_continuation(cross_actor_cmd),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
        current_actor="codex",
        proxy_authority_ref="decision:proxied_codex_to_claude_2026_05_21",
        decision_authority_refs=(
            "decision:proxied_codex_to_claude_2026_05_21",
        ),
    )
    assert result == cross_actor_cmd


def test_bound_proxy_does_not_override_unrunnable_blocker() -> None:
    """v4.32: even with bound proxy authority, repair_command_runnable=False
    dominates. The typed BlockerSnapshot stop wins over proxy."""
    result = _next_step_command_for_report(
        final_response_gate=_gate(
            next_required_command=(
                "python3 dev/scripts/devctl.py review-channel "
                "--action ingest --packet-id rev_pkt_4654 --actor claude"
            ),
            repair_command_runnable=False,
        ),
        continuation=_continuation(),
        packet_attention_required=False,
        packet_attention_command="",
        next_commands=(),
        current_actor="codex",
        proxy_authority_ref="decision:proxied_codex_to_claude_2026_05_21",
        decision_authority_refs=(
            "decision:proxied_codex_to_claude_2026_05_21",
        ),
    )
    assert result == ""  # unrunnable wins over bound proxy


def test_rev_pkt_4699_live_shape_refuses_for_codex_runner() -> None:
    """v4.30 follow-up (rev_pkt_4701 critical regression): the exact
    rev_pkt_4699 live shape — a Codex reviewer running develop next with a
    Claude-targeted ingest command in the fallback chain — must NOT emit
    the command. develop next output must not contain rev_pkt_4654 or
    --actor claude.

    Codex's rev_pkt_4699 observed output:
        next_step_command:
            python3 dev/scripts/devctl.py review-channel
                --action ingest --packet-id rev_pkt_4654 --actor claude ...

    After this fix, that emission is refused when current_actor=codex.
    """
    rev_pkt_4699_stale_command = (
        "python3 dev/scripts/devctl.py review-channel --action ingest "
        "--packet-id rev_pkt_4654 --actor claude"
    )
    # Codex reviewer running develop next
    result = _next_step_command_for_report(
        final_response_gate=_gate(
            next_required_command=rev_pkt_4699_stale_command,
            repair_command_runnable=True,  # gate didn't mark unrunnable
        ),
        continuation=_continuation(rev_pkt_4699_stale_command),
        packet_attention_required=True,
        packet_attention_command=rev_pkt_4699_stale_command,
        next_commands=(rev_pkt_4699_stale_command,),
        current_actor="codex",
    )
    assert result == ""
    assert "rev_pkt_4654" not in result
    assert "--actor claude" not in result


def test_unrunnable_gate_does_not_resurrect_rev_pkt_4699_repro() -> None:
    """v4.30 (rev_pkt_4699 EXACT repro): a Claude-owned ingest command for
    rev_pkt_4654 MUST NOT surface when the gate has refused.

    Codex's live observed output (pre-fix):
        next_step_command: python3 dev/scripts/devctl.py review-channel
                           --action ingest --packet-id rev_pkt_4654 --actor claude ...

    After link 9, this fallback is refused and next_step_command stays empty.
    """
    rev_pkt_4699_stale_command = (
        "python3 dev/scripts/devctl.py review-channel --action ingest "
        "--packet-id rev_pkt_4654 --actor claude"
    )
    result = _next_step_command_for_report(
        final_response_gate=_gate(
            repair_command_runnable=False,
            blocker_owner="operator",
            blocker_reason="cross_actor_or_unrunnable",
        ),
        continuation=_continuation(rev_pkt_4699_stale_command),
        packet_attention_required=True,
        packet_attention_command=rev_pkt_4699_stale_command,
        next_commands=(rev_pkt_4699_stale_command,),
    )
    assert result == ""
    assert "rev_pkt_4654" not in result
    assert "--actor claude" not in result
