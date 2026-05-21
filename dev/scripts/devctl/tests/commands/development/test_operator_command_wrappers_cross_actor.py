"""Phase 0.6.A v4.30 link 9 follow-up (rev_pkt_4703) wrapper cross-actor refusal.

Codex's rev_pkt_4703 verdict: ``develop next --actor codex`` was still
rendering executable Operator Command Wrappers for peer-owned commands
like ``campaign.claude_next_command: ... --actor claude --role implementer ...``.
A Codex reviewer-facing wrapper must NOT emit a Claude-owned executable
command without typed proxy authority.

v4.31 (rev_pkt_4705): cross-actor refusal converged on the typed
``classify_command_envelope`` substrate. Helper-level tests moved to
``test_command_envelope_classification.py``; this file keeps the
wrapper-builder behavioral coverage plus a new proxy-positive case.
"""

from __future__ import annotations

from dev.scripts.devctl.commands.development.operator_command_wrappers import (
    MAX_OPERATOR_COMMAND_INLINE_LENGTH,
    build_operator_command_wrappers,
)


def _long_command_for(actor: str, role: str = "implementer") -> str:
    """Build a wrapper-eligible command (length > threshold) scoped to actor."""
    base = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        f"--actor {actor} --role {role} "
        "--session-id 2a5b3528-aaa6-4615-b83b-5b1d3598509b"
    )
    assert len(base) > MAX_OPERATOR_COMMAND_INLINE_LENGTH, (
        "test fixture must be long enough to trigger wrapper threshold"
    )
    return base


def test_wrapper_builder_filters_cross_actor_commands() -> None:
    """v4.30 (rev_pkt_4703): wrapper builder suppresses peer-lane commands
    when current_actor differs from the command's --actor.

    Codex's exact reproduction: ``campaign.claude_next_command`` rendering
    a Claude-targeted agent-loop wrapper while ``develop next --actor codex``
    was active.
    """
    sources = (
        ("campaign.claude_next_command", _long_command_for("claude")),
        ("agent_loop.current", _long_command_for("codex", role="reviewer")),
    )
    wrappers = build_operator_command_wrappers(sources, current_actor="codex")
    # Only the codex-scoped wrapper survives; the claude one is refused
    assert len(wrappers) == 1
    assert all("--actor codex" in w.original_command for w in wrappers)
    assert all("--actor claude" not in w.original_command for w in wrappers)


def test_wrapper_builder_preserves_legacy_behavior_without_current_actor() -> None:
    """v4.30: callers that don't plumb current_actor (or pass "") keep the
    legacy behavior — no silent filtering. This ensures existing call sites
    that haven't adopted the param don't unexpectedly drop wrappers."""
    sources = (
        ("campaign.claude_next_command", _long_command_for("claude")),
        ("agent_loop.current", _long_command_for("codex", role="reviewer")),
    )
    wrappers = build_operator_command_wrappers(sources)
    # Both wrappers survive without current_actor plumbing
    assert len(wrappers) == 2


def test_wrapper_builder_same_actor_passes_through() -> None:
    """v4.30: same-actor commands wrap normally."""
    sources = (
        ("agent_loop.current", _long_command_for("codex", role="reviewer")),
    )
    wrappers = build_operator_command_wrappers(sources, current_actor="codex")
    assert len(wrappers) == 1
    assert "--actor codex" in wrappers[0].original_command


def test_wrapper_builder_short_commands_skip_filter() -> None:
    """v4.30: commands below the threshold are skipped before the cross-actor
    filter even runs. This preserves the existing threshold semantics."""
    short_cross_actor = "python3 cmd.py --actor claude"
    assert len(short_cross_actor) <= MAX_OPERATOR_COMMAND_INLINE_LENGTH
    wrappers = build_operator_command_wrappers(
        ((short_cross_actor, short_cross_actor),), current_actor="codex"
    )
    # Below threshold: no wrapper built (independent of cross-actor)
    assert wrappers == ()


def test_rev_pkt_4703_live_shape_refuses_claude_wrapper_for_codex_runner() -> None:
    """v4.30 (rev_pkt_4703 critical regression): the exact shape codex
    observed — ``campaign.claude_next_command`` rendering a Claude
    agent-loop command while a Codex reviewer is running ``develop next`` —
    must NOT produce a wrapper.

    Codex's observed pre-fix output:
        campaign.claude_next_command:
        python3 dev/scripts/devctl.py agent-loop --format json
            --actor claude --role implementer
            --session-id 2a5b3528-aaa6-4615-b83b-5b1d3598509b

    After this fix, no wrapper is rendered for that source/command pair
    when current_actor=codex.
    """
    rev_pkt_4703_stale_wrapper_command = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor claude --role implementer "
        "--session-id 2a5b3528-aaa6-4615-b83b-5b1d3598509b"
    )
    wrappers = build_operator_command_wrappers(
        (("campaign.claude_next_command", rev_pkt_4703_stale_wrapper_command),),
        current_actor="codex",
    )
    assert wrappers == ()
    # Defense in depth: ensure no wrapper carries the offending substrings
    for w in wrappers:  # empty tuple iterates as no-op, but kept for clarity
        assert "--actor claude" not in w.original_command
        assert "campaign.claude_next_command" not in w.source


def test_wrapper_builder_handles_mixed_actor_command_sources() -> None:
    """v4.30: a realistic mix — system (no --actor), claude, codex commands —
    only the cross-actor ones get filtered; the rest pass through."""
    sources = (
        (
            "system.status_check",
            "python3 dev/scripts/devctl.py review-channel --action status "
            "--format md --terminal none --target codex",
        ),
        ("campaign.claude_next_command", _long_command_for("claude")),
        ("agent_loop.current", _long_command_for("codex", role="reviewer")),
    )
    wrappers = build_operator_command_wrappers(sources, current_actor="codex")
    sources_in_wrappers = {w.source for w in wrappers}
    # claude wrapper filtered out; the other two pass (status has no --actor,
    # current is for codex)
    assert "campaign.claude_next_command" not in sources_in_wrappers
    assert "agent_loop.current" in sources_in_wrappers


def test_wrapper_builder_proxy_authority_allows_cross_actor_wrapping() -> None:
    """v4.32 (rev_pkt_4706): a cross-actor command becomes
    ``proxy_authorized_executable`` and the wrapper SHOULD render WHEN the
    proxy_authority_ref is BOUND to the active decision's authority refs."""
    sources = (
        ("campaign.claude_next_command", _long_command_for("claude")),
    )
    wrappers = build_operator_command_wrappers(
        sources,
        current_actor="codex",
        proxy_authority_ref="decision:proxied_codex_to_claude_2026_05_21",
        decision_authority_refs=(
            "decision:proxied_codex_to_claude_2026_05_21",
            "snapshot:cps_2026_05_21",
        ),
    )
    assert len(wrappers) == 1
    assert "--actor claude" in wrappers[0].original_command
    assert wrappers[0].source == "campaign.claude_next_command"


def test_wrapper_builder_unbound_proxy_ref_does_not_render_cross_actor() -> None:
    """v4.32 closure: a proxy_authority_ref alone is NOT enough. Without
    decision_authority_refs (or with non-matching refs), the cross-actor
    command stays as peer_lane_status_only and is filtered."""
    sources = (
        ("campaign.claude_next_command", _long_command_for("claude")),
    )
    # No decision_authority_refs → unbound → filtered
    wrappers = build_operator_command_wrappers(
        sources,
        current_actor="codex",
        proxy_authority_ref="decision:claimed_but_unverified",
    )
    assert wrappers == ()
    # decision_authority_refs supplied but ref doesn't match → still filtered
    wrappers_mismatched = build_operator_command_wrappers(
        sources,
        current_actor="codex",
        proxy_authority_ref="decision:claimed",
        decision_authority_refs=("decision:something_else",),
    )
    assert wrappers_mismatched == ()


def test_wrapper_builder_proxy_ref_does_not_unlock_when_same_actor() -> None:
    """v4.31: proxy_authority_ref on a same-actor command is harmless — the
    command was already executable, so proxy is a no-op (not an error)."""
    sources = (
        ("agent_loop.current", _long_command_for("codex", role="reviewer")),
    )
    wrappers = build_operator_command_wrappers(
        sources,
        current_actor="codex",
        proxy_authority_ref="decision:irrelevant_same_actor",
        decision_authority_refs=("decision:irrelevant_same_actor",),
    )
    assert len(wrappers) == 1
    assert "--actor codex" in wrappers[0].original_command
