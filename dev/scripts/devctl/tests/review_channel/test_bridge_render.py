"""Focused tests for bridge projection render/repair."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import review_channel as review_channel_command
from dev.scripts.devctl.review_channel.bridge_projection import (
    bridge_hygiene_errors,
    render_bridge_projection,
)


def _review_channel_text() -> str:
    return "\n".join(
        [
            "# Review Channel + Shared Screen Plan",
            "",
            "## Transitional Markdown Bridge (Current Operating Mode)",
            "",
            "`bridge.md` is the temporary bridge.",
            "In autonomous mode `MASTER_PLAN.md` remains the canonical tracker and",
            "   `INDEX.md` remains the router for the minimal active docs set.",
            "For the current operator-facing loop, each meaningful Codex reviewer write to",
            "   `bridge.md` must also emit a concise operator-visible chat update.",
            "Bridge writes stay conductor-owned: only one Codex conductor updates the Codex-owned bridge",
            "sections while specialist workers report back instead of editing the bridge directly.",
            "Bridge behavior is mode-aware. Claude must stay in polling mode.",
            "The reviewer should emit an operator-visible",
            "heartbeat every five minutes even when the blocker set is unchanged.",
            "Default multi-agent wakeups should be change-routed instead of brute-force.",
            "The header should expose `last_poll_local` for the operator.",
            "Until the structured path lands, `check_review_channel_bridge.py` guards this bridge.",
            "The repo-native continuous fallback is `devctl swarm_run --continuous`.",
            "Completion stall is a named failure mode that the bridge must prevent.",
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


def _bridge_text() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return "\n".join(
        [
            "# Review Bridge",
            "",
            "Live shared review channel for Codex <-> Claude coordination during active work.",
            "",
            "## Start-Of-Conversation Rules",
            "",
            "Codex is the reviewer. Claude is the coder.",
            "Run `python3 dev/scripts/devctl.py startup-context --format summary` first before coding or relaunching conductor work.",
            "Then run `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md` for slim startup context.",
            "Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
            "Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.",
            "Claude must read `Last Codex poll` / `Poll Status` first on each repoll.",
            "When `Reviewer mode` is `active_dual_agent`, this file is the live reviewer/coder authority.",
            "When `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or `offline`, Claude must not assume a live Codex review loop.",
            "Codex must poll non-`bridge.md` worktree changes every 2-3 minutes while code is moving.",
            "Codex must exclude `bridge.md` itself when computing the reviewed worktree hash.",
            "Each meaningful review must include an operator-visible chat update.",
            "Only the Codex conductor may update the Codex-owned sections in this file.",
            "Only the Claude conductor may update the Claude-owned sections in this file.",
            "Specialist workers should wake on owned-path changes or explicit conductor request instead of every worker polling the full tree blindly on the same cadence.",
            "Codex must emit an operator-visible heartbeat every 5 minutes while code is moving, even when the blocker set is unchanged.",
            "",
            f"- Last Codex poll: `{now}`",
            "- Last Codex poll (Local America/New_York): `2026-03-25 21:50:00 EDT`",
            "- Reviewer mode: `active_dual_agent`",
            f"- Last non-audit worktree hash: `{'a' * 64}`",
            "- Current instruction revision: `45f861225f52`",
            "",
            "## Protocol",
            "",
            "1. Keep this file current-state only.",
            "",
            "## Swarm Mode",
            "",
            "- 8+8 lanes active.",
            "",
            "## Poll Status",
            "",
            "- Reviewer heartbeat refreshed through repo-owned tooling.",
            "",
            "## Current Verdict",
            "",
            "- reviewer checkpoint: current branch is not accepted yet.",
            "",
            "## Open Findings",
            "",
            "- M1: keep this slice bounded.",
            "- M2: rerun focused validation after the patch.",
            "",
            "## Claude Status",
            "",
            "- **Current slice — DONE, needs-review**",
            "- 42 tests green.",
            "- Prior slice: older status that should be dropped.",
            "- Session 44 / historical item that should be dropped.",
            "\u001b[?2026hraw terminal noise",
            "test writer::state::tests::foo ... ok",
            "",
            "## Claude Questions",
            "",
            "- None recorded.",
            "",
            "## Claude Ack",
            "",
            "- acknowledged; instruction-rev: `45f861225f52`",
            "- Current bounded slice complete.",
            "- acknowledged; instruction-rev: `olderrev123456`",
            "- Historical ack that should be dropped.",
            "",
            "## Current Instruction For Claude",
            "",
            "- Implement the bounded bridge cleanup slice.",
            "",
            "## Last Reviewed Scope",
            "",
            "- bridge.md",
            "- dev/scripts/devctl/review_channel/bridge_projection.py",
            "",
            "## Coverage",
            "",
            "- This whole extra report section should be dropped.",
            "",
        ]
    )


def test_render_bridge_projection_drops_transcript_noise_and_extra_sections() -> None:
    rendered, result = render_bridge_projection(
        bridge_text=_bridge_text(),
        last_worktree_hash="b" * 64,
    )

    assert "Coverage" in result.dropped_headings
    assert "Claude Status" in result.sanitized_sections
    assert "Claude Ack" in result.sanitized_sections
    assert "## Coverage" not in rendered
    assert "raw terminal noise" not in rendered
    assert "test writer::state::tests::foo ... ok" not in rendered
    assert "olderrev123456" not in rendered
    assert "Prior slice:" not in rendered
    assert "Session 44 / historical item" not in rendered
    assert bridge_hygiene_errors(rendered) == []


def test_review_channel_render_bridge_action_rewrites_live_bridge(tmp_path: Path) -> None:
    root = tmp_path
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(_bridge_text(), encoding="utf-8")
    output_path = root / "report.json"

    parser = build_parser()
    args = parser.parse_args(
        [
            "review-channel",
            "--action",
            "render-bridge",
            "--terminal",
            "none",
            "--format",
            "json",
            "--review-channel-path",
            str(review_channel_path.relative_to(root)),
            "--bridge-path",
            str(bridge_path.relative_to(root)),
            "--status-dir",
            "dev/reports/review_channel/latest",
            "--output",
            str(output_path),
        ]
    )

    with patch.object(review_channel_command, "REPO_ROOT", root):
        rc = review_channel_command.run(args)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    rewritten = bridge_path.read_text(encoding="utf-8")
    assert rc == 0
    assert "Coverage" in payload["bridge_render"]["dropped_headings"]
    assert "Claude Status" in payload["bridge_render"]["sanitized_sections"]
    assert "Claude Ack" in payload["bridge_render"]["sanitized_sections"]
    assert "## Coverage" not in rewritten
    assert "olderrev123456" not in rewritten
    assert "test writer::state::tests::foo ... ok" not in rewritten
    assert bridge_hygiene_errors(rewritten) == []
