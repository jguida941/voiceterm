"""Focused tests for the inbox-first prompt rendering + trusted-by-default
approval-mode auto-elevation in headless remote-control launches.

Both changes target the persistence-loop / sandbox-escalation root cause
empirically observed across rev_pkt_1496/1510/1512: codex sessions in
headless `--terminal none` mode silently deadlock on sandbox-escalation
prompts, and codex sessions consistently delay inbox-poll behind their
reviewer-bootstrap, so operator-authority packets never get acted on.
"""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.review_channel.core import (
    DEFAULT_ROLLOVER_THRESHOLD_PCT,
    REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
)
from dev.scripts.devctl.review_channel.prompt import build_conductor_prompt


def _build_codex_prompt() -> str:
    root = Path("/fake/repo")
    return build_conductor_prompt(
        provider="codex",
        provider_name="Codex",
        other_name="Claude",
        repo_root=root,
        review_channel_path=root / "dev/active/review_channel.md",
        bridge_path=root / "bridge.md",
        lanes=[],
        codex_workers=8,
        claude_workers=8,
        dangerous=False,
        rollover_threshold_pct=DEFAULT_ROLLOVER_THRESHOLD_PCT,
        await_ack_seconds=180,
        retirement_note=REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
        rollover_command="python3 dev/scripts/devctl.py review-channel --action rollover",
        promote_command="python3 dev/scripts/devctl.py review-channel --action promote",
        bridge_liveness=None,
        handoff_bundle=None,
    )


def test_inbox_poll_renders_after_bootstrap_but_before_operating_contract() -> None:
    """Closes the inbox-blind investigation habit at the prompt-template source
    while preserving the canonical Step 0 bootstrap contract from bridge.md.

    Per rev_pkt_1519 F1: the inbox-poll cannot render BEFORE startup-context
    / session-resume / context-graph (the bootstrap chain), because the repo's
    Start-Of-Conversation Rules in bridge.md require startup-context first.
    Instead, the inbox-drain instruction renders AFTER bootstrap but BEFORE the
    Operating contract section so it gates all reviewer activity that follows.
    """
    prompt = _build_codex_prompt()

    bootstrap_section_idx = prompt.find("Bootstrap in this exact order before acting")
    inbox_section_idx = prompt.find(
        "After bootstrap, FIRST drain the review-channel inbox"
    )
    inbox_command_idx = prompt.find(
        "review-channel --action inbox --target codex --status pending --terminal none --format md"
    )
    operating_contract_idx = prompt.find("Operating contract:")

    assert bootstrap_section_idx >= 0, "rendered prompt must include bootstrap section"
    assert inbox_section_idx >= 0, "rendered prompt must include inbox-drain section"
    assert inbox_command_idx >= 0, "rendered prompt must include inbox-poll command"
    assert operating_contract_idx >= 0, "rendered prompt must include operating contract"

    assert bootstrap_section_idx < inbox_section_idx, (
        "inbox-drain section must render AFTER bootstrap (Step 0 contract)"
    )
    assert inbox_section_idx < operating_contract_idx, (
        "inbox-drain section must render BEFORE operating contract so it "
        "gates reviewer activity that follows"
    )
    assert inbox_command_idx < operating_contract_idx


def test_inbox_drain_includes_ack_step_for_provider() -> None:
    """The inbox-drain instruction must also tell codex to ack pending
    instruction-class packets, so operator-authority packets actually flip
    to acked state instead of being read but ignored."""
    prompt = _build_codex_prompt()

    assert (
        "review-channel --action ack --packet-id <id> --actor codex"
    ) in prompt


def _make_args(approval_mode_arg: object, dangerous: bool = False):
    """Minimal argparse.Namespace stand-in for build_launch_session_descriptors."""
    from argparse import Namespace

    return Namespace(
        approval_mode=approval_mode_arg,
        dangerous=dangerous,
        action="launch",
        rollover_provider="",
        codex_workers=8,
        claude_workers=8,
        cursor_workers=0,
        rollover_threshold_pct=20,
        await_ack_seconds=180,
    )


def _make_context(*, interaction_mode: str):
    """Minimal BridgeSessionContext stand-in for the launch-session builder."""
    from pathlib import Path

    from dev.scripts.devctl.commands.review_channel.bridge_action_support import (
        BridgeSessionContext,
    )

    return BridgeSessionContext(
        repo_root=Path("/fake/repo"),
        review_channel_path=Path("/fake/repo/dev/active/review_channel.md"),
        bridge_path=Path("/fake/repo/bridge.md"),
        bridge_liveness={},
        codex_lanes=[],
        claude_lanes=[],
        cursor_lanes=[],
        handoff_bundle=None,
        promotion_plan_path=None,
        script_dir=None,
        status_dir=Path("/fake/repo/dev/reports/review_channel"),
        interaction_mode=interaction_mode,
    )


def test_remote_control_auto_elevates_to_trusted_when_no_explicit_mode() -> None:
    """rev_pkt_1510/1512 fix: in headless remote-control mode the launcher must
    auto-elevate approval_mode to `trusted` so codex doesn't silently deadlock
    on sandbox-escalation prompts (e.g. on `ps`, `pgrep`) that the headless
    terminal cannot render. This is the smallest possible change that closes
    the empirical wedge observed in sessions 019dacd1 (balanced → wedge) vs.
    019dace3/019dad14 (trusted → productive)."""
    from dev.scripts.devctl.commands.review_channel.bridge_action_support import (
        build_bridge_sessions,
    )

    captured: dict[str, object] = {}

    def fake_resolve_cli_path(provider: str) -> str:
        return f"/fake/{provider}"

    def fake_build_launch_sessions(*, request, **_kwargs) -> list[dict[str, object]]:
        captured["approval_mode"] = request.approval_mode
        return []

    args = _make_args(approval_mode_arg=None)
    context = _make_context(interaction_mode="remote_control")

    build_bridge_sessions(
        args=args,
        context=context,
        resolve_cli_path_fn=fake_resolve_cli_path,
        build_launch_sessions_fn=fake_build_launch_sessions,
    )

    assert captured["approval_mode"] == "trusted", (
        "headless remote-control launches with no explicit --approval-mode "
        "must auto-elevate to trusted; otherwise the sandbox-escalation deadlock "
        "(rev_pkt_1510, rev_pkt_1512) reproduces every spawn"
    )


def test_local_terminal_keeps_balanced_default_when_no_explicit_mode() -> None:
    """The auto-elevate must be scoped to remote-control only. Local-terminal
    sessions stay on the existing `balanced` default so operator-visible
    permission prompts continue to work as designed."""
    from dev.scripts.devctl.commands.review_channel.bridge_action_support import (
        build_bridge_sessions,
    )

    captured: dict[str, object] = {}

    def fake_resolve_cli_path(provider: str) -> str:
        return f"/fake/{provider}"

    def fake_build_launch_sessions(*, request, **_kwargs) -> list[dict[str, object]]:
        captured["approval_mode"] = request.approval_mode
        return []

    args = _make_args(approval_mode_arg=None)
    context = _make_context(interaction_mode="local_terminal")

    build_bridge_sessions(
        args=args,
        context=context,
        resolve_cli_path_fn=fake_resolve_cli_path,
        build_launch_sessions_fn=fake_build_launch_sessions,
    )

    assert captured["approval_mode"] == "balanced"


def test_auto_elevated_approval_mode_helper_remote_control_path() -> None:
    """rev_pkt_1522 F1 fix: extracted helper auto_elevated_approval_mode is the
    single source of truth for the auto-elevation logic, shared between launch/
    rollover (build_bridge_sessions) and recover (_recover.py) paths so both
    entry points eliminate the same sandbox-escalation deadlock."""
    from dev.scripts.devctl.approval_mode import auto_elevated_approval_mode

    # No explicit mode + remote_control → trusted
    assert (
        auto_elevated_approval_mode(
            explicit_mode=None, interaction_mode="remote_control"
        )
        == "trusted"
    )
    # No explicit mode + local_terminal → None (caller normalizes to balanced default)
    assert (
        auto_elevated_approval_mode(
            explicit_mode=None, interaction_mode="local_terminal"
        )
        is None
    )
    # Explicit mode wins regardless of interaction_mode
    assert (
        auto_elevated_approval_mode(
            explicit_mode="balanced", interaction_mode="remote_control"
        )
        == "balanced"
    )
    assert (
        auto_elevated_approval_mode(
            explicit_mode="strict", interaction_mode="remote_control"
        )
        == "strict"
    )


def test_real_parser_default_is_none_so_auto_elevation_fires_in_production() -> None:
    """rev_pkt_1521 F1 fix: prove the auto-elevation actually fires under the
    REAL parser (not a fabricated Namespace). Codex correctly identified that
    parser.py was defaulting --approval-mode to 'balanced', which made the
    bridge_action_support.py 'is None' branch dead in production. Parser
    default is now None so the launcher's typed-state-driven selection fires.
    """
    import argparse

    from dev.scripts.devctl.review_channel.parser import (
        add_review_channel_parser,
    )

    root_parser = argparse.ArgumentParser()
    subparsers = root_parser.add_subparsers(dest="command")
    add_review_channel_parser(subparsers)

    args = root_parser.parse_args(["review-channel", "--action", "launch"])

    assert args.approval_mode is None, (
        "real parser must leave --approval-mode unset (None) so the launcher "
        "can auto-select trusted vs balanced based on typed interaction_mode; "
        "Codex's rev_pkt_1521 finding was that defaulting to 'balanced' in the "
        "parser made the auto-elevation dead in production"
    )


def test_reviewer_wake_resolves_to_trusted_under_remote_control() -> None:
    """rev_pkt_1528 fix: the reviewer-wake path in reviewer_follow_guard.py must
    route through auto_elevated_approval_mode so a remote-control reviewer
    relaunched by ensure-follow does not silently wedge on the same hidden
    sandbox-escalation prompt the launch/recover paths now avoid."""
    from argparse import Namespace

    from dev.scripts.devctl.review_channel.reviewer_follow_guard import (
        _resolved_wake_approval_mode,
    )

    args_unset = Namespace(approval_mode=None)
    assert (
        _resolved_wake_approval_mode(
            args=args_unset, interaction_mode="remote_control"
        )
        == "trusted"
    )

    # Local-terminal stays empty (downstream normalize falls back to balanced).
    assert (
        _resolved_wake_approval_mode(
            args=args_unset, interaction_mode="local_terminal"
        )
        == ""
    )

    # Explicit operator override wins regardless of interaction_mode.
    args_explicit = Namespace(approval_mode="balanced")
    assert (
        _resolved_wake_approval_mode(
            args=args_explicit, interaction_mode="remote_control"
        )
        == "balanced"
    )


def test_explicit_approval_mode_arg_wins_even_in_remote_control() -> None:
    """An explicit --approval-mode on the command line must always win over
    the remote-control auto-elevation, so operators retain final say."""
    from dev.scripts.devctl.commands.review_channel.bridge_action_support import (
        build_bridge_sessions,
    )

    captured: dict[str, object] = {}

    def fake_resolve_cli_path(provider: str) -> str:
        return f"/fake/{provider}"

    def fake_build_launch_sessions(*, request, **_kwargs) -> list[dict[str, object]]:
        captured["approval_mode"] = request.approval_mode
        return []

    args = _make_args(approval_mode_arg="balanced")
    context = _make_context(interaction_mode="remote_control")

    build_bridge_sessions(
        args=args,
        context=context,
        resolve_cli_path_fn=fake_resolve_cli_path,
        build_launch_sessions_fn=fake_build_launch_sessions,
    )

    assert captured["approval_mode"] == "balanced", (
        "explicit operator-supplied --approval-mode must override the "
        "remote-control auto-elevation"
    )
