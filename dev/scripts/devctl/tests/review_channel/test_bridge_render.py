"""Focused tests for bridge projection render/repair."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import review_channel as review_channel_command
from dev.scripts.devctl.review_channel.bridge_section_validation import (
    find_embedded_markdown_headings,
)
from dev.scripts.devctl.review_channel.current_session_projection import (
    bridge_implementer_state_hash,
)
from dev.scripts.devctl.review_channel.handoff import extract_bridge_snapshot
from dev.scripts.devctl.review_channel.bridge_sanitize import (
    BRIDGE_SECTION_LINE_LIMITS,
    sanitize_bridge_sections,
)
from dev.scripts.devctl.review_channel.bridge_projection import (
    bridge_hygiene_errors,
    bridge_projection_state_to_dict,
    build_bridge_projection_state,
    render_bridge_projection,
)
from dev.scripts.devctl.review_channel.promotion_support import (
    InstructionRewriteContext,
    rewrite_instruction_and_metadata,
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
            "Codex uses `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary` and Claude uses `python3 dev/scripts/devctl.py startup-context --role implementer --format summary` first before coding or relaunching conductor work.",
            "Then Codex uses `python3 dev/scripts/devctl.py session-resume --role reviewer --format bootstrap` and Claude uses `python3 dev/scripts/devctl.py session-resume --role implementer --format bootstrap` as the canonical role bootstrap packet.",
            "Then run `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md` for slim startup context.",
            "Keep chat bootstrap acknowledgements concise: blocker state plus next step, not a replay of the packet, unless the operator asks for the detail.",
            "Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
            "Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.",
            "Claude must read `Last Codex poll` / `Poll Status` first on each repoll.",
            "When `Reviewer mode` is `active_dual_agent`, this file is the live reviewer/coder authority. Codex stays reviewer-only by default: missing worker worktrees, absent fanout, or a promising fix are not permission to start local implementation.",
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
            "- Planned lanes are capacity hints, not proof of live worker sessions.",
            "",
            "## Operator Direction",
            "",
            "Owner: operator (human). Both agents read this section. Do not modify.",
            "",
            "### ROLE ENFORCEMENT (read first, every session)",
            "",
            "Codex stays reviewer-only unless the operator explicitly authorizes takeover.",
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


def _typed_review_state(bridge_text: str) -> dict[str, object]:
    projection_state = build_bridge_projection_state(
        bridge_text=bridge_text,
        bridge_liveness={},
    )
    return {
        "_compat": {
            "bridge_projection": bridge_projection_state_to_dict(projection_state),
        }
    }


def _write_pending_packet(root: Path) -> None:
    path = root / "dev/reports/review_channel/events/trace.ndjson"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": 1,
        "event_id": "rev_evt_0001",
        "packet_id": "rev_pkt_0001",
        "trace_id": "trace_0001",
        "event_type": "packet_posted",
        "status": "pending",
        "from_agent": "claude",
        "to_agent": "codex",
        "kind": "finding",
        "summary": "Keep the prior reviewer finding visible before render-bridge.",
    }
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")


def test_sanitize_bridge_sections_rewrites_live_state_sections() -> None:
    sections = {
        "Claude Status": "\n".join(
            [
                "- current slice is clean",
                "- prior slice that should be dropped",
            ]
        ),
        "Claude Ack": "\n".join(
            [
                "- acknowledged; instruction-rev: `abc123`",
                "- prior slice that should be dropped",
            ]
        ),
    }

    sanitized, mutated = sanitize_bridge_sections(
        sections,
        section_line_limits=BRIDGE_SECTION_LINE_LIMITS,
    )

    assert sanitized["Claude Status"] == "- current slice is clean"
    assert sanitized["Claude Ack"] == "- acknowledged; instruction-rev: `abc123`"
    assert "Claude Status" in mutated
    assert "Claude Ack" in mutated


def test_render_bridge_projection_drops_transcript_noise_and_extra_sections() -> None:
    rendered, result = render_bridge_projection(
        review_state=_typed_review_state(_bridge_text()),
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
    assert "## Operator Direction" in rendered
    assert "### ROLE ENFORCEMENT (read first, every session)" in rendered
    assert bridge_hygiene_errors(rendered) == []


def test_render_bridge_projection_projects_bound_action_request_packets() -> None:
    review_state = _typed_review_state(_bridge_text())
    review_state["packets"] = [
        {
            "packet_id": "rev_pkt_0001",
            "kind": "action_request",
            "status": "pending",
            "requested_action": "run_check",
            "summary": "Run focused bridge check",
            "body": "python3 dev/scripts/checks/check_review_channel_bridge.py",
            "target_kind": "runtime",
            "target_ref": "guard:check_review_channel_bridge",
            "target_revision": "tree-123",
        },
        {
            "packet_id": "rev_pkt_0002",
            "kind": "action_request",
            "status": "pending",
            "requested_action": "commit",
            "body": "-m 'unbound legacy commit'",
        },
    ]

    rendered, _ = render_bridge_projection(
        review_state=review_state,
        last_worktree_hash="b" * 64,
    )

    action_requests = extract_bridge_snapshot(rendered).sections["Action Requests"]
    assert "rev_pkt_0001" in action_requests
    assert "guard:check_review_channel_bridge" in action_requests
    assert "rev_pkt_0002" not in action_requests
    assert len(action_requests.splitlines()) <= 12
    assert bridge_hygiene_errors(rendered) == []


def test_render_bridge_projection_falls_back_when_fixed_sections_missing() -> None:
    review_state = {
        "timestamp": "2026-04-07T22:15:00Z",
        "current_session": {
            "current_instruction": "- Keep the review-channel bridge live.",
            "current_instruction_revision": "abc123",
        },
        "reviewer_runtime": {
            "review_acceptance": {
                "current_verdict": "- changes_requested",
                "open_findings": "- F25: bridge projection must not fail closed.",
            }
        },
        "_compat": {
            "bridge_projection": {
                "metadata": {"current_instruction_revision": "abc123"},
                "sections": {},
            },
        },
        "packets": [],
    }

    rendered, _ = render_bridge_projection(
        review_state=review_state,
        last_worktree_hash="b" * 64,
    )

    assert "## Poll Status" in rendered
    assert "## Current Verdict" in rendered
    assert "## Open Findings" in rendered
    assert "- Keep the review-channel bridge live." in rendered
    assert bridge_hygiene_errors(rendered) == []


def test_render_bridge_projection_tracks_swapped_reviewer_and_implementer() -> None:
    review_state = _typed_review_state(_bridge_text())
    review_state["collaboration"] = {
        "role_assignments": [
            {"role_id": "review_agent", "provider": "claude"},
            {"role_id": "coding_agent", "provider": "codex"},
        ]
    }

    rendered, _ = render_bridge_projection(
        review_state=review_state,
        last_worktree_hash="c" * 64,
    )

    assert "Claude is the reviewer. Codex is the coder." in rendered
    assert "Live shared review channel for Claude <-> Codex coordination" in rendered
    assert (
        "Only the Claude conductor may update the reviewer-owned sections, "
        "including the `Last Codex poll` compatibility heartbeat in this file."
    ) in rendered
    assert (
        "Only the Codex conductor may update the implementer-owned compatibility "
        "sections (`Claude Status`, `Claude Questions`, `Claude Ack`) in this"
    ) in rendered


def test_render_bridge_projection_drops_duplicate_packet_heading_and_stays_idempotent() -> None:
    dirty_bridge = _bridge_text().replace(
        "## Last Reviewed Scope",
        "\n".join(
            [
                "## Context Recovery Packet",
                "",
                "- Trigger: `review-channel-promotion`",
                "",
                "## Last Reviewed Scope",
            ]
        ),
        1,
    )

    rendered_once, result_once = render_bridge_projection(
        review_state=_typed_review_state(dirty_bridge),
        last_worktree_hash="b" * 64,
    )
    rendered_twice, result_twice = render_bridge_projection(
        review_state=_typed_review_state(rendered_once),
        last_worktree_hash="b" * 64,
    )

    assert "Context Recovery Packet" in result_once.dropped_headings
    assert "## Context Recovery Packet" not in rendered_once
    assert rendered_twice == rendered_once
    assert "Context Recovery Packet" not in result_twice.dropped_headings
    assert bridge_hygiene_errors(rendered_twice) == []


def test_find_embedded_markdown_headings_detects_flat_bridge_contract_violation() -> None:
    assert find_embedded_markdown_headings(
        "\n".join(
            [
                "- Next scoped task.",
                "## Context Recovery Packet",
                "- Trigger: `review-channel-promotion`",
            ]
        )
    ) == ("## Context Recovery Packet",)


def test_instruction_rewrite_rejects_embedded_markdown_headings() -> None:
    with pytest.raises(
        ValueError,
        match="embedded markdown headings in `Current Instruction For Claude`",
    ):
        rewrite_instruction_and_metadata(
            bridge_text=_bridge_text(),
            instruction="\n".join(
                [
                    "- Next scoped task.",
                    "## Context Recovery Packet",
                    "- Trigger: `review-channel-promotion`",
                ]
            ),
            context=InstructionRewriteContext(
                repo_root=Path("/tmp/repo"),
                bridge_path=Path("/tmp/repo/bridge.md"),
                reviewer_mode="active_dual_agent",
                reason="next-plan-item",
            ),
        )


def test_instruction_rewrite_rejects_stale_implementer_state_hash() -> None:
    baseline_bridge = _bridge_text()

    with pytest.raises(
        ValueError,
        match="expected implementer state hash",
    ):
        rewrite_instruction_and_metadata(
            bridge_text=baseline_bridge.replace(
                "## Claude Questions\n\n- None recorded.",
                "## Claude Questions\n\n- New blocker from Claude.",
            ),
            instruction="- Next scoped task.",
            context=InstructionRewriteContext(
                repo_root=Path("/tmp/repo"),
                bridge_path=Path("/tmp/repo/bridge.md"),
                reviewer_mode="active_dual_agent",
                reason="next-plan-item",
                expected_implementer_state_hash=bridge_implementer_state_hash(
                    extract_bridge_snapshot(baseline_bridge)
                ),
            ),
        )


def test_render_bridge_projection_rejects_embedded_markdown_headings_in_typed_sections() -> None:
    review_state = _typed_review_state(_bridge_text())
    review_state["_compat"]["bridge_projection"]["sections"][
        "Current Instruction For Claude"
    ] = "\n".join(
        [
            "- Next scoped task.",
            "## Context Recovery Packet",
            "- Trigger: `review-channel-promotion`",
        ]
    )

    with pytest.raises(
        ValueError,
        match="embedded markdown headings in fixed sections",
    ):
        render_bridge_projection(
            review_state=review_state,
            last_worktree_hash="b" * 64,
        )


def test_render_bridge_projection_includes_full_reviewer_startup_contract() -> None:
    """Rendered bridge must include every canonical reviewer non-zero startup
    semantic from prompt_guards.startup_context_follow_up(): read summary fields,
    review_pending exception, status poll, heartbeat refresh, and repair boundary."""
    rendered, _ = render_bridge_projection(
        review_state=_typed_review_state(_bridge_text()),
        last_worktree_hash="d" * 64,
    )

    assert "review_pending" in rendered
    assert "review_pending_before_push" in rendered
    assert "review-channel --action status" in rendered
    assert "read the summary fields" in rendered
    assert "before widening scope" in rendered
    assert "heartbeat before attempting repair" in rendered
    assert "repair_reviewer_loop" in rendered
    assert "checkpoint/budget blockers" in rendered
    assert "stale/non-live reviewer runtime" in rendered
    assert "repair or relaunch boundary" in rendered


def test_review_channel_render_bridge_action_rewrites_live_bridge(tmp_path: Path) -> None:
    root = tmp_path
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(_bridge_text(), encoding="utf-8")
    status_dir = root / "dev/reports/review_channel/latest"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / "review_state.json").write_text(
        json.dumps(_typed_review_state(_bridge_text()), indent=2),
        encoding="utf-8",
    )
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


def test_review_channel_render_bridge_fails_closed_with_pending_reviewer_packets(
    tmp_path: Path,
) -> None:
    root = tmp_path
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    original = _bridge_text()
    bridge_path.write_text(original, encoding="utf-8")
    status_dir = root / "dev/reports/review_channel/latest"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / "review_state.json").write_text(
        json.dumps(_typed_review_state(original), indent=2),
        encoding="utf-8",
    )
    _write_pending_packet(root)
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
    assert rc == 1
    assert "pending review packet" in payload["errors"][0]
    assert bridge_path.read_text(encoding="utf-8") == original
