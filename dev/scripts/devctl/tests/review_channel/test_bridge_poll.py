"""Focused tests for `review-channel --action bridge-poll`."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import review_channel as review_channel_command
from dev.scripts.devctl.commands.review_channel._bridge_poll import (
    BridgePollResult,
    build_bridge_poll_result,
)
from dev.scripts.devctl.commands.review_channel._wait_support import (
    build_typed_reviewer_token,
)
from dev.scripts.devctl.review_channel.reviewer_state import (
    write_reviewer_heartbeat,
)


def _build_review_channel_text() -> str:
    return "\n".join(
        [
            "# Review Channel + Shared Screen Plan",
            "",
            "## Transitional Markdown Bridge (Current Operating Mode)",
            "",
            "`bridge.md` is the temporary bridge.",
            "In autonomous mode `MASTER_PLAN.md` remains the canonical tracker and",
            "   `INDEX.md` remains the router for the minimal active docs set.",
            "Bridge behavior is mode-aware. Claude must stay in polling mode.",
            "",
            "## 0) Current Execution Mode",
            "",
            "| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |",
            "|---|---|---|---|---|---|",
            "| `AGENT-1` | Codex reviewer | `dev/active/review_channel.md` | `MP-377` | `../wt-codex` | `feature/codex` |",
            "| `AGENT-9` | Claude coder | `dev/active/review_channel.md` | `MP-377` | `../wt-claude` | `feature/claude` |",
            "",
        ]
    )


def _build_bridge_text(
    *,
    last_codex_poll: str | None = None,
    instruction_revision: str = "56bcd5d01510",
    claude_ack_revision: str = "56bcd5d01510",
    current_instruction: str = "- Implement the bridge-poll action.",
    current_verdict: str = "- reviewer accepted prior slice",
    open_findings: str = "- keep this slice limited to bridge-poll",
) -> str:
    if last_codex_poll is None:
        last_codex_poll = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return "\n".join(
        [
            "# Review Bridge",
            "",
            "## Start-Of-Conversation Rules",
            "",
            "Codex is the reviewer. Claude is the coder.",
            "At conversation start, both agents must bootstrap repo authority in this order before acting: `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and `dev/active/review_channel.md`.",
            "Codex must poll non-`bridge.md` worktree changes every 2-3 minutes while code is moving.",
            "Codex must exclude `bridge.md` itself when computing the reviewed worktree hash.",
            "Each meaningful review must include an operator-visible chat update.",
            "Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
            "Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.",
            "When the structured review queue is available, Claude must also poll `review-channel --action inbox --target claude --status pending --format json` or the equivalent watch surface on the same cadence so Codex-targeted packets are not missed.",
            "Claude must read `Last Codex poll` / `Poll Status` first on each repoll.",
            "When `Reviewer mode` is `active_dual_agent`, this file is the live reviewer/coder authority.",
            "When `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or `offline`, Claude must not assume a live Codex review loop.",
            'When the current slice is accepted and scoped plan work remains, Codex must derive the next highest-priority unchecked plan item from the active-plan chain and rewrite `Current Instruction For Claude` for the next slice instead of idling at "all green so far."',
            "If `Current Instruction For Claude` or `Poll Status` says `hold steady`, `waiting for reviewer promotion`, `Codex committing/pushing`, or similar wait-state language, Claude must not mine plan docs for side work or self-promote the next slice. Keep polling until a reviewer-owned section changes.",
            "Only the Codex conductor may update the Codex-owned sections in this file.",
            "Only the Claude conductor may update the Claude-owned sections in this file.",
            "Specialist workers should wake on owned-path changes or explicit conductor request instead of every worker polling the full tree blindly on the same cadence.",
            "Codex must emit an operator-visible heartbeat every 5 minutes while code is moving, even when the blocker set is unchanged.",
            "",
            f"- Last Codex poll: `{last_codex_poll}`",
            "- Last Codex poll (Local America/New_York): `2026-03-20 00:29:40 EDT`",
            "- Reviewer mode: `active_dual_agent`",
            f"- Last non-audit worktree hash: `{'a' * 64}`",
            f"- Current instruction revision: `{instruction_revision}`",
            "",
            "## Protocol",
            "",
            "- Poll target: every 5 minutes when code is moving (operator-directed live loop cadence)",
            "",
            "## Poll Status",
            "",
            "- active reviewer loop",
            "",
            "## Current Verdict",
            "",
            current_verdict,
            "",
            "## Open Findings",
            "",
            open_findings,
            "",
            "## Current Instruction For Claude",
            "",
            current_instruction,
            "",
            "## Claude Status",
            "",
            "- waiting for reviewer poll",
            "",
            "## Claude Questions",
            "",
            "- none",
            "",
            "## Claude Ack",
            "",
            f"- acknowledged; instruction-rev: `{claude_ack_revision}`",
            "",
            "## Last Reviewed Scope",
            "",
            "- bridge.md",
            "",
        ]
    )


def _run_bridge_poll(tmp_path: Path, bridge_text: str) -> tuple[int, dict[str, object]]:
    root = tmp_path
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_build_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(bridge_text, encoding="utf-8")
    output_path = root / "report.json"
    parser = build_parser()
    args = parser.parse_args(
        [
            "review-channel",
            "--action",
            "bridge-poll",
            "--terminal",
            "none",
            "--format",
            "json",
            "--review-channel-path",
            str(review_channel_path.relative_to(root)),
            "--bridge-path",
            str(bridge_path.relative_to(root)),
            "--output",
            str(output_path),
        ]
    )

    with patch.object(review_channel_command, "REPO_ROOT", root):
        rc = review_channel_command.run(args)

    return rc, json.loads(output_path.read_text(encoding="utf-8"))


def test_build_bridge_poll_result_uses_bridge_revision_metadata() -> None:
    result = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="c5d49df4cfd1",
            claude_ack_revision="02d4a121f492",
        )
    )

    assert isinstance(result, BridgePollResult)
    assert result.current_instruction_revision == "c5d49df4cfd1"
    assert result.claude_ack_revision == "02d4a121f492"
    assert result.changed_since_last_ack is True


def test_bridge_poll_reports_unchanged_ack_state(tmp_path: Path) -> None:
    rc, payload = _run_bridge_poll(
        tmp_path,
        _build_bridge_text(
            instruction_revision="c5d49df4cfd1",
            claude_ack_revision="c5d49df4cfd1",
        ),
    )

    assert rc == 0
    assert payload["ok"] is True
    assert payload["current_instruction_revision"] == "c5d49df4cfd1"
    assert payload["claude_ack_current"] is True
    assert payload["changed_since_last_ack"] is False
    assert payload["reviewer_mode"] == "active_dual_agent"
    assert payload["reviewer_freshness"] == "fresh"
    assert payload["reviewed_hash_current"] is False
    assert payload["review_needed"] is True
    assert payload["next_turn_required"] is True
    assert payload["next_turn_role"] == "reviewer"
    assert payload["next_turn_reason"] == "review_follow_up_required"
    assert payload["turn_state_token"]


def test_bridge_poll_reports_changed_since_last_ack(tmp_path: Path) -> None:
    rc, payload = _run_bridge_poll(
        tmp_path,
        _build_bridge_text(
            instruction_revision="c5d49df4cfd1",
            claude_ack_revision="02d4a121f492",
            current_instruction="- Start MP-377 Phase 1 / Slice D on the current tree.",
        ),
    )

    assert rc == 0
    assert payload["ok"] is True
    assert payload["claude_ack_current"] is False
    assert payload["changed_since_last_ack"] is True
    assert payload["poll_status"] == "- active reviewer loop"
    assert payload["current_verdict"] == "- reviewer accepted prior slice"
    assert payload["open_findings"] == "- keep this slice limited to bridge-poll"
    assert payload["next_turn_required"] is True
    assert payload["next_turn_role"] == "implementer"
    assert payload["next_turn_reason"] == "implementer_ack_stale"
    assert payload["turn_state_token"]


def test_write_reviewer_heartbeat_rewrites_poll_status_immediately_under_heading(
    tmp_path: Path,
) -> None:
    root = tmp_path
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_build_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(
        _build_bridge_text().replace(
            "## Poll Status\n\n- active reviewer loop",
            "## Poll Status\n"
            + ("\n" * 64)
            + "- active reviewer loop\n"
            + "- Current reviewer instruction revision is `oldrev12345678`.\n"
            + "- Claude has not ACKed `oldrev12345678` yet.\n"
            + "- Claude should repoll `bridge.md` and continue the old slice.",
        ),
        encoding="utf-8",
    )

    with patch(
        "dev.scripts.devctl.review_channel.reviewer_state._refresh_projections_after_checkpoint"
    ):
        write_reviewer_heartbeat(
            repo_root=root,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="test-heartbeat-padding",
        )

    updated_bridge = bridge_path.read_text(encoding="utf-8")
    assert (
        "## Poll Status\n\n- Reviewer heartbeat refreshed through repo-owned tooling"
        in updated_bridge
    )
    assert "oldrev12345678" not in updated_bridge
    assert "continue the old slice" not in updated_bridge


def test_bridge_poll_fails_closed_on_malformed_reviewer_content(
    tmp_path: Path,
) -> None:
    rc, payload = _run_bridge_poll(
        tmp_path,
        _build_bridge_text(
            current_instruction="- Update Not logged in · Please run /login to continue.",
        ),
    )

    assert rc == 1
    assert payload["ok"] is False
    assert any("suspicious terminal/status text" in error for error in payload["errors"])


def test_bridge_poll_hold_steady_empty_instruction(tmp_path: Path) -> None:
    """When instruction is empty, changed_since_last_ack should be False."""
    rc, payload = _run_bridge_poll(
        tmp_path,
        _build_bridge_text(
            instruction_revision="56bcd5d01510",
            claude_ack_revision="56bcd5d01510",
            current_instruction="",
        ),
    )
    # Empty instruction means no change to act on
    assert payload["changed_since_last_ack"] is False


def test_bridge_poll_ack_stale_to_current_transition() -> None:
    """Verify ACK state transitions from stale to current."""
    # State 1: ACK is stale (different revisions, must be hex for regex)
    stale = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="99887766ffee",
        ),
        current_worktree_hash="a" * 64,
    )
    assert stale.claude_ack_current is False
    assert stale.changed_since_last_ack is True
    assert stale.reviewed_hash_current is True
    assert stale.review_needed is False
    assert stale.next_turn_required is True
    assert stale.next_turn_role == "implementer"
    assert stale.next_turn_reason == "implementer_ack_stale"
    assert stale.turn_state_token

    # State 2: Claude ACKs (revisions match)
    current = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="aabbccdd1122",
        ),
        current_worktree_hash="a" * 64,
    )
    assert current.claude_ack_current is True
    assert current.changed_since_last_ack is False
    assert current.reviewed_hash_current is True
    assert current.review_needed is False
    assert current.next_turn_required is False
    assert current.next_turn_role == ""
    assert current.next_turn_reason == "up_to_date"
    assert current.turn_state_token
    assert current.turn_state_token != stale.turn_state_token


def test_turn_state_token_changes_when_reviewer_turn_flips_without_new_revision() -> None:
    stale_tree = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="aabbccdd1122",
        ),
        current_worktree_hash="b" * 64,
    )
    reviewed_tree = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="aabbccdd1122",
        ),
        current_worktree_hash="a" * 64,
    )

    assert stale_tree.changed_since_last_ack is False
    assert reviewed_tree.changed_since_last_ack is False
    assert stale_tree.next_turn_role == "reviewer"
    assert stale_tree.next_turn_reason == "review_follow_up_required"
    assert reviewed_tree.next_turn_role == ""
    assert reviewed_tree.next_turn_reason == "up_to_date"
    assert stale_tree.turn_state_token != reviewed_tree.turn_state_token


def test_typed_reviewer_token_uses_turn_state_token() -> None:
    implementer_turn = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="99887766ffee",
        ),
        current_worktree_hash="a" * 64,
    )
    reviewer_turn = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="aabbccdd1122",
        ),
        current_worktree_hash="b" * 64,
    )

    assert implementer_turn.turn_state_token != reviewer_turn.turn_state_token
    assert build_typed_reviewer_token(implementer_turn) != build_typed_reviewer_token(
        reviewer_turn
    )


def test_implementer_wait_snapshot_uses_bridge_poll_fields() -> None:
    """Verify _capture_wait_snapshot routes through bridge-poll typed fields."""
    from dev.scripts.devctl.commands.review_channel._wait import (
        ImplementerWaitDeps,
        _capture_wait_snapshot,
    )
    from dev.scripts.devctl.commands.review_channel_command import (
        RuntimePaths,
    )
    from pathlib import Path
    import tempfile

    bridge_text = _build_bridge_text(
        instruction_revision="new_rev_12345",
        claude_ack_revision="old_rev_99999",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        bridge_path = root / "bridge.md"
        bridge_path.write_text(bridge_text, encoding="utf-8")

        status_report = {
            "ok": True,
            "review_needed": True,
            "bridge_liveness": {
                "claude_ack_current": False,
                "current_instruction_revision": "new_rev_12345",
                "reviewer_mode": "active_dual_agent",
            },
            "attention": {"status": "claude_ack_stale"},
        }

        deps = ImplementerWaitDeps(
            run_status_action_fn=lambda **kw: (status_report, 0),
            read_bridge_text_fn=lambda p: bridge_text,
            monotonic_fn=lambda: 0.0,
            sleep_fn=lambda s: None,
        )

        paths = RuntimePaths(
            review_channel_path=root / "dev/active/review_channel.md",
            bridge_path=bridge_path,
            rollover_dir=root / "rollover",
            status_dir=root / "status",
            promotion_plan_path=root / "promo.md",
            script_dir=root / "scripts",
        )

        class FakeArgs:
            action = "implementer-wait"
            format = "json"
            terminal = "none"

        snapshot = _capture_wait_snapshot(
            args=FakeArgs(),
            repo_root=root,
            paths=paths,
            deps=deps,
        )

        # The typed bridge-poll fields should be used
        assert snapshot.current_instruction_revision == "new_rev_12345"
        assert snapshot.claude_ack_current is False


def test_wait_snapshot_tracks_latest_pending_claude_packet() -> None:
    """implementer-wait should capture the newest pending Claude packet id."""
    from dev.scripts.devctl.commands.review_channel._wait import (
        ImplementerWaitDeps,
        _capture_wait_snapshot,
    )
    from dev.scripts.devctl.commands.review_channel_command import RuntimePaths
    import tempfile

    bridge_text = _build_bridge_text()

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        bridge_path = root / "bridge.md"
        bridge_path.write_text(bridge_text, encoding="utf-8")

        status_report = {
            "ok": True,
            "review_needed": True,
            "bridge_liveness": {
                "claude_ack_current": True,
                "current_instruction_revision": "56bcd5d01510",
                "reviewer_mode": "active_dual_agent",
            },
            "attention": {"status": "reviewed_hash_stale"},
        }

        deps = ImplementerWaitDeps(
            run_status_action_fn=lambda **kw: (status_report, 0),
            read_bridge_text_fn=lambda p: bridge_text,
            monotonic_fn=lambda: 0.0,
            sleep_fn=lambda s: None,
            pending_packets_fn=lambda repo_root, paths: [
                {"packet_id": "rev_pkt_9000"}
            ],
        )

        paths = RuntimePaths(
            review_channel_path=root / "dev/active/review_channel.md",
            bridge_path=bridge_path,
            rollover_dir=root / "rollover",
            status_dir=root / "status",
            promotion_plan_path=root / "promo.md",
            script_dir=root / "scripts",
        )

        class FakeArgs:
            action = "implementer-wait"
            format = "json"
            terminal = "none"

        snapshot = _capture_wait_snapshot(
            args=FakeArgs(),
            repo_root=root,
            paths=paths,
            deps=deps,
        )

        assert snapshot.latest_pending_packet_id == "rev_pkt_9000"


def test_malformed_bridge_fails_closed_in_wait_snapshot() -> None:
    """Malformed bridge content must cause _capture_wait_snapshot to set exit_code=1."""
    from dev.scripts.devctl.commands.review_channel._wait import (
        ImplementerWaitDeps,
        _capture_wait_snapshot,
    )
    from dev.scripts.devctl.commands.review_channel_command import RuntimePaths
    import tempfile

    # Bridge with suspicious terminal/status text in the instruction
    malformed_bridge = _build_bridge_text(
        current_instruction="- Update Not logged in · Please run /login to continue.",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        bridge_path = root / "bridge.md"
        bridge_path.write_text(malformed_bridge, encoding="utf-8")

        status_report = {
            "ok": True,
            "review_needed": True,
            "bridge_liveness": {
                "claude_ack_current": True,
                "current_instruction_revision": "56bcd5d01510",
                "reviewer_mode": "active_dual_agent",
            },
            "attention": {"status": "claude_ack_stale"},
        }

        deps = ImplementerWaitDeps(
            run_status_action_fn=lambda **kw: (status_report, 0),
            read_bridge_text_fn=lambda p: malformed_bridge,
            monotonic_fn=lambda: 0.0,
            sleep_fn=lambda s: None,
        )

        paths = RuntimePaths(
            review_channel_path=root / "dev/active/review_channel.md",
            bridge_path=bridge_path,
            rollover_dir=root / "rollover",
            status_dir=root / "status",
            promotion_plan_path=root / "promo.md",
            script_dir=root / "scripts",
        )

        class FakeArgs:
            action = "implementer-wait"
            format = "json"
            terminal = "none"

        snapshot = _capture_wait_snapshot(
            args=FakeArgs(),
            repo_root=root,
            paths=paths,
            deps=deps,
        )

        # Malformed content should force exit_code=1 (fail closed)
        assert snapshot.exit_code == 1


def test_bridge_poll_rejects_missing_instruction_revision_metadata(tmp_path: Path) -> None:
    """Active bridge without explicit `Current instruction revision` metadata must fail."""
    # Build bridge text WITHOUT the instruction revision metadata line
    bridge_lines = _build_bridge_text(
        instruction_revision="56bcd5d01510",
        claude_ack_revision="56bcd5d01510",
    ).splitlines()
    # Remove the "- Current instruction revision:" metadata line
    filtered = [
        line for line in bridge_lines
        if "Current instruction revision:" not in line
    ]
    bridge_no_rev = "\n".join(filtered)

    rc, payload = _run_bridge_poll(tmp_path, bridge_no_rev)
    # Should fail because active bridge mode requires explicit revision metadata
    assert rc == 1
    assert payload["ok"] is False
    assert any("Current instruction revision" in e for e in payload.get("errors", []))


def test_multiple_ack_lines_uses_first_as_current(tmp_path: Path) -> None:
    """When Claude Ack has multiple instruction-rev lines, the first one is current."""
    bridge = _build_bridge_text(
        instruction_revision="aabbccdd1122",
        claude_ack_revision="aabbccdd1122",  # first line matches
    )
    # Append an older ACK line to simulate multiple ACKs
    bridge = bridge.replace(
        "- acknowledged; instruction-rev: `aabbccdd1122`",
        "- acknowledged; instruction-rev: `aabbccdd1122`\n"
        "- acknowledged; instruction-rev: `99887766ffee`",
    )
    rc, payload = _run_bridge_poll(tmp_path, bridge)
    assert rc == 0
    # The first ACK line should be treated as current
    assert payload["claude_ack_revision"] == "aabbccdd1122"
    assert payload["claude_ack_current"] is True
    assert payload["changed_since_last_ack"] is False


def test_multiple_ack_lines_false_stale_when_first_is_old(tmp_path: Path) -> None:
    """When the first ACK line is stale, changed_since_last_ack should be True."""
    bridge = _build_bridge_text(
        instruction_revision="aabbccdd1122",
        claude_ack_revision="99887766ffee",  # first line is old
    )
    # Append the correct revision as a later line (should NOT be used)
    bridge = bridge.replace(
        "- acknowledged; instruction-rev: `99887766ffee`",
        "- acknowledged; instruction-rev: `99887766ffee`\n"
        "- acknowledged; instruction-rev: `aabbccdd1122`",
    )
    rc, payload = _run_bridge_poll(tmp_path, bridge)
    # First line is stale, so ACK is not current
    assert payload["claude_ack_revision"] == "99887766ffee"
    assert payload["claude_ack_current"] is False
    assert payload["changed_since_last_ack"] is True


def test_missing_revision_fails_closed_in_wait_snapshot() -> None:
    """implementer-wait must fail closed when bridge has no instruction revision metadata."""
    from dev.scripts.devctl.commands.review_channel._wait import (
        ImplementerWaitDeps,
        _capture_wait_snapshot,
    )
    from dev.scripts.devctl.commands.review_channel_command import RuntimePaths
    import tempfile

    bridge_lines = _build_bridge_text().splitlines()
    filtered = [
        line for line in bridge_lines
        if "Current instruction revision:" not in line
    ]
    bridge_no_rev = "\n".join(filtered)

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        bridge_path = root / "bridge.md"
        bridge_path.write_text(bridge_no_rev, encoding="utf-8")

        status_report = {
            "ok": True,
            "review_needed": True,
            "bridge_liveness": {
                "claude_ack_current": True,
                "current_instruction_revision": "",
                "reviewer_mode": "active_dual_agent",
            },
            "attention": {"status": "healthy"},
        }

        deps = ImplementerWaitDeps(
            run_status_action_fn=lambda **kw: (status_report, 0),
            read_bridge_text_fn=lambda p: bridge_no_rev,
            monotonic_fn=lambda: 0.0,
            sleep_fn=lambda s: None,
        )

        paths = RuntimePaths(
            review_channel_path=root / "dev/active/review_channel.md",
            bridge_path=bridge_path,
            rollover_dir=root / "rollover",
            status_dir=root / "status",
            promotion_plan_path=root / "promo.md",
            script_dir=root / "scripts",
        )

        class FakeArgs:
            action = "implementer-wait"
            format = "json"
            terminal = "none"

        snapshot = _capture_wait_snapshot(
            args=FakeArgs(),
            repo_root=root,
            paths=paths,
            deps=deps,
        )

        # Missing revision metadata = fail closed
        assert snapshot.exit_code == 1


def test_cli_parser_accepts_bridge_poll() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "review-channel",
            "--action",
            "bridge-poll",
            "--terminal",
            "none",
            "--format",
            "json",
        ]
    )
    assert getattr(args, "action") == "bridge-poll"
