"""Focused tests for `review-channel --action bridge-poll`."""

from __future__ import annotations

import json
from datetime import datetime, timezone
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
from dev.scripts.devctl.review_channel.current_session_projection import (
    compute_implementer_state_hash,
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
        last_codex_poll = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
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
            "When `Reviewer mode` is `active_dual_agent`, this file is the live reviewer/coder authority. Codex stays reviewer-only by default: missing worker worktrees, absent fanout, or a promising fix are not permission to start local implementation.",
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


def _run_bridge_poll(
    tmp_path: Path,
    bridge_text: str,
    *,
    typed_review_state: dict[str, object] | None = None,
) -> tuple[int, dict[str, object]]:
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
        with patch(
            "dev.scripts.devctl.commands.review_channel._bridge_poll.load_typed_poll_authority",
            return_value=typed_review_state,
        ):
            rc = review_channel_command.run(args)

    return rc, json.loads(output_path.read_text(encoding="utf-8"))


def _typed_review_state(
    *,
    snapshot_id: str = "snap-123",
    reviewer_mode: str = "active_dual_agent",
    effective_reviewer_mode: str = "active_dual_agent",
    launch_truth: str = "live_runtime",
    attention_status: str = "healthy",
    implementation_blocked: bool = False,
    implementation_block_reason: str = "",
    recovery_action_allowed: str = "",
    reviewed_hash_current: bool = True,
    review_needed: bool = False,
    instruction_revision: str = "56bcd5d01510",
    implementer_status: str = "- waiting for reviewer poll",
    implementer_questions: str = "- none",
    accepted_implementer_state_hash: str = "",
) -> dict[str, object]:
    implementer_ack = f"- acknowledged; instruction-rev: `{instruction_revision}`"
    implementer_state_hash = compute_implementer_state_hash(
        implementer_status=implementer_status,
        implementer_questions=implementer_questions,
        implementer_ack=implementer_ack,
    )
    return {
        "snapshot_id": snapshot_id,
        "zref": "zref_12345678_deadbeef",
        "review": {
            "bridge_path": "bridge.md",
            "review_channel_path": "dev/active/review_channel.md",
        },
        "queue": {
            "pending_total": 0,
            "pending_codex": 0,
            "pending_claude": 0,
            "pending_cursor": 0,
            "pending_operator": 0,
            "stale_packet_count": 0,
            "derived_next_instruction": "",
            "derived_next_instruction_source": {},
        },
        "current_session": {
            "current_instruction": "- Implement the bridge-poll action.",
            "current_instruction_revision": instruction_revision,
            "implementer_status": implementer_status,
            "implementer_ack": implementer_ack,
            "implementer_ack_revision": instruction_revision,
            "implementer_ack_state": "current",
            "implementer_state_hash": implementer_state_hash,
            "open_findings": "- none",
            "last_reviewed_scope": "- bridge.md",
        },
        "bridge": {
            "reviewer_mode": reviewer_mode,
            "effective_reviewer_mode": effective_reviewer_mode,
            "reviewer_freshness": "fresh",
            "launch_truth": launch_truth,
            "claude_ack_current": True,
            "current_instruction_revision": instruction_revision,
            "claude_ack_revision": instruction_revision,
            "implementer_state_hash": implementer_state_hash,
            "reviewed_hash_current": reviewed_hash_current,
            "review_needed": review_needed,
        },
        "attention": {
            "status": attention_status,
            "summary": attention_status,
            "recommended_action": "inspect",
        },
        "reviewer_runtime": {
            "reviewer_mode": reviewer_mode,
            "effective_reviewer_mode": effective_reviewer_mode,
            "reviewer_freshness": "fresh",
            "stale_reason": (
                "" if attention_status == "healthy" else attention_status
            ),
            "implementer_ack_current": True,
            "implementation_blocked": implementation_blocked,
            "implementation_block_reason": implementation_block_reason,
            "last_poll": {
                "last_codex_poll_utc": "2026-04-03T00:00:00Z",
                "last_codex_poll_age_seconds": 5,
            },
            "rollover": {
                "rollover_id": "",
                "ack_pending": False,
                "trigger": "",
            },
            "session_owner": {
                "provider": "codex",
                "session_name": "codex-conductor",
                "session_pid": 1,
                "terminal_window_id": 1,
                "script_path": "/tmp/codex.sh",
            },
            "recovery_action_allowed": recovery_action_allowed,
            "review_acceptance": {
                "current_verdict": "- accepted",
                "open_findings": "- none",
                "review_accepted": True,
                "reviewer_accepted_implementer_state_hash": (
                    accepted_implementer_state_hash
                ),
            },
            "publish_clear": False,
        },
    }


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
    assert payload["implementer_state_hash"] == compute_implementer_state_hash(
        implementer_status="- waiting for reviewer poll",
        implementer_questions="- none",
        implementer_ack="- acknowledged; instruction-rev: `c5d49df4cfd1`",
    )
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

    assert rc == 1
    assert payload["ok"] is False
    assert payload["errors"] == [
        "Live implementer ACK (`Implementer Ack`) revision does not match the current reviewer instruction revision."
    ]
    assert payload["claude_ack_current"] is False
    assert payload["changed_since_last_ack"] is True
    assert payload["poll_status"] == "- active reviewer loop"
    assert payload["current_verdict"] == "- reviewer accepted prior slice"
    assert payload["open_findings"] == "- keep this slice limited to bridge-poll"
    assert payload["implementer_state_hash"]
    assert payload["next_turn_required"] is True
    assert payload["next_turn_role"] == "implementer"
    assert payload["next_turn_reason"] == "implementer_ack_stale"
    assert payload["turn_state_token"]


def test_bridge_poll_surfaces_typed_revision_reuse_warning(tmp_path: Path) -> None:
    new_instruction = "- Start the re-reviewed parity guard repair slice."
    derived_revision = "9d0be0ca64ec"
    typed_review_state = _typed_review_state(
        instruction_revision=derived_revision,
    )
    typed_review_state["warnings"] = [
        "Current reviewer instruction text changed while `Current instruction revision` stayed at `c5d49df4cfd1`."
    ]
    typed_review_state["current_session"]["current_instruction"] = new_instruction
    typed_review_state["current_session"]["current_instruction_revision"] = derived_revision
    typed_review_state["current_session"]["implementer_ack"] = (
        "- acknowledged; instruction-rev: `c5d49df4cfd1`"
    )
    typed_review_state["current_session"]["implementer_ack_revision"] = "c5d49df4cfd1"
    typed_review_state["current_session"]["implementer_ack_state"] = "stale"
    typed_review_state["bridge"]["current_instruction_revision"] = derived_revision
    typed_review_state["bridge"]["claude_ack_revision"] = "c5d49df4cfd1"
    typed_review_state["bridge"]["claude_ack_current"] = False
    typed_review_state["reviewer_runtime"]["implementer_ack_current"] = False

    rc, payload = _run_bridge_poll(
        tmp_path,
        _build_bridge_text(
            instruction_revision="c5d49df4cfd1",
            claude_ack_revision="c5d49df4cfd1",
            current_instruction=new_instruction,
        ),
        typed_review_state=typed_review_state,
    )

    assert rc == 1
    assert any(
        "Assigned-role progress does not match the current reviewer instruction revision"
        in error
        for error in payload["errors"]
    )
    assert payload["warnings"] == [
        "Current reviewer instruction text changed while `Current instruction revision` stayed at `c5d49df4cfd1`."
    ]
    assert payload["current_instruction_revision"] == derived_revision
    assert payload["claude_ack_current"] is False
    assert payload["changed_since_last_ack"] is True


def test_bridge_poll_reports_reviewer_wait_state_when_hold_steady_is_acked() -> None:
    result = build_bridge_poll_result(
        _build_bridge_text(
            current_instruction=(
                "- Hold steady while Codex commits/pushes the current tree."
            ),
            current_verdict="- accepted",
            open_findings="- none",
            claude_ack_revision="56bcd5d01510",
        ),
        current_worktree_hash="a" * 64,
    )

    assert result.claude_ack_current is True
    assert result.reviewed_hash_current is True
    assert result.review_needed is False
    assert result.next_turn_required is True
    assert result.next_turn_role == "reviewer"
    assert result.next_turn_reason == "reviewer_wait_state"
    assert result.turn_state_token


def test_bridge_poll_prefers_typed_runtime_authority_for_dead_dual_agent_loop() -> None:
    typed_review_state = _typed_review_state(
        effective_reviewer_mode="tools_only",
        launch_truth="detached_runtime_only",
        attention_status="review_loop_relaunch_required",
        implementation_blocked=True,
        implementation_block_reason="review_loop_relaunch_required",
        recovery_action_allowed="python3 dev/scripts/devctl.py review-channel --action launch",
        reviewed_hash_current=True,
        review_needed=False,
        instruction_revision="aabbccdd1122",
    )

    result = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="aabbccdd1122",
        ),
        current_worktree_hash="a" * 64,
        typed_review_state=typed_review_state,
    )

    assert result.snapshot_id == "snap-123"
    assert result.zref == "zref_12345678_deadbeef"
    assert result.effective_reviewer_mode == "tools_only"
    assert result.launch_truth == "detached_runtime_only"
    assert result.attention_status == "review_loop_relaunch_required"
    assert result.implementation_blocked is True
    assert result.implementation_block_reason == "review_loop_relaunch_required"
    assert (
        result.recovery_action_allowed
        == "python3 dev/scripts/devctl.py review-channel --action launch"
    )
    assert result.next_turn_required is False
    assert result.next_turn_role == ""
    assert result.next_turn_reason == "inactive"
    assert result.turn_state_token


def test_bridge_poll_command_uses_typed_turn_authority_projection(
    tmp_path: Path,
) -> None:
    typed_review_state = _typed_review_state(
        effective_reviewer_mode="tools_only",
        launch_truth="detached_runtime_only",
        attention_status="review_loop_relaunch_required",
        implementation_blocked=True,
        implementation_block_reason="review_loop_relaunch_required",
        recovery_action_allowed="python3 dev/scripts/devctl.py review-channel --action launch",
        reviewed_hash_current=True,
        review_needed=False,
        instruction_revision="aabbccdd1122",
    )

    rc, payload = _run_bridge_poll(
        tmp_path,
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="aabbccdd1122",
        ),
        typed_review_state=typed_review_state,
    )

    assert rc == 0
    assert payload["snapshot_id"] == "snap-123"
    assert payload["zref"] == "zref_12345678_deadbeef"
    assert payload["effective_reviewer_mode"] == "tools_only"
    assert payload["launch_truth"] == "detached_runtime_only"
    assert payload["attention_status"] == "review_loop_relaunch_required"
    assert payload["next_turn_role"] == ""
    assert payload["next_turn_reason"] == "inactive"


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


def test_bridge_poll_requires_reviewer_when_implementer_state_differs_from_accepted_baseline() -> None:
    typed_review_state = _typed_review_state(
        reviewed_hash_current=True,
        review_needed=False,
        instruction_revision="aabbccdd1122",
        implementer_status="- updated Claude status after bridge-only change",
        accepted_implementer_state_hash=compute_implementer_state_hash(
            implementer_status="- waiting for reviewer poll",
            implementer_questions="- none",
            implementer_ack="- acknowledged; instruction-rev: `aabbccdd1122`",
        ),
    )

    result = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="aabbccdd1122",
        ),
        current_worktree_hash="a" * 64,
        typed_review_state=typed_review_state,
    )

    assert result.reviewed_hash_current is True
    assert result.review_needed is False
    assert result.next_turn_required is True
    assert result.next_turn_role == "reviewer"
    assert result.next_turn_reason == "implementer_state_changed"
    assert result.reviewer_accepted_implementer_state_hash


def test_turn_state_token_changes_when_accepted_implementer_baseline_changes() -> None:
    common_kwargs = {
        "reviewed_hash_current": True,
        "review_needed": False,
        "instruction_revision": "aabbccdd1122",
        "implementer_status": "- updated Claude status after bridge-only change",
    }
    first = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="aabbccdd1122",
        ),
        current_worktree_hash="a" * 64,
        typed_review_state=_typed_review_state(
            **common_kwargs,
            accepted_implementer_state_hash=compute_implementer_state_hash(
                implementer_status="- waiting for reviewer poll",
                implementer_questions="- none",
                implementer_ack="- acknowledged; instruction-rev: `aabbccdd1122`",
            ),
        ),
    )
    second = build_bridge_poll_result(
        _build_bridge_text(
            instruction_revision="aabbccdd1122",
            claude_ack_revision="aabbccdd1122",
        ),
        current_worktree_hash="a" * 64,
        typed_review_state=_typed_review_state(
            **common_kwargs,
            accepted_implementer_state_hash=compute_implementer_state_hash(
                implementer_status="- different accepted baseline",
                implementer_questions="- none",
                implementer_ack="- acknowledged; instruction-rev: `aabbccdd1122`",
            ),
        ),
    )

    assert first.next_turn_reason == "implementer_state_changed"
    assert second.next_turn_reason == "implementer_state_changed"
    assert first.turn_state_token != second.turn_state_token


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


def test_bridge_poll_fallback_reads_last_known_review_state(tmp_path: Path) -> None:
    """load_typed_poll_authority falls back to review_state.json on disk when refresh fails."""
    from dev.scripts.devctl.commands.review_channel._bridge_poll_support import (
        load_typed_poll_authority,
    )
    from dev.scripts.devctl.commands.review_channel_command import RuntimePaths

    status_dir = tmp_path / "dev" / "reports" / "review_channel" / "latest"
    status_dir.mkdir(parents=True, exist_ok=True)
    projection_dir = status_dir.parent / "projections" / status_dir.name
    projection_dir.mkdir(parents=True, exist_ok=True)

    typed_state = _typed_review_state(
        effective_reviewer_mode="tools_only",
        launch_truth="detached_runtime_only",
        attention_status="review_loop_relaunch_required",
    )
    (projection_dir / "review_state.json").write_text(
        json.dumps(typed_state), encoding="utf-8"
    )

    paths = RuntimePaths(
        bridge_path=tmp_path / "bridge.md",
        review_channel_path=tmp_path / "dev" / "active" / "review_channel.md",
        status_dir=status_dir,
        promotion_plan_path=tmp_path / "promo.md",
    )

    with patch(
        "dev.scripts.devctl.commands.review_channel._bridge_poll_support.refresh_status_snapshot",
        side_effect=OSError("simulated snapshot refresh failure"),
    ):
        result = load_typed_poll_authority(repo_root=tmp_path, paths=paths)

    assert result is not None
    assert result["bridge"]["effective_reviewer_mode"] == "tools_only"
    assert result["bridge"]["launch_truth"] == "detached_runtime_only"
    assert result["attention"]["status"] == "review_loop_relaunch_required"


def test_bridge_poll_turn_authority_uses_lifecycle_fallback_when_present() -> None:
    """build_reviewer_turn_authority uses reviewer_mode as effective_reviewer_mode without lifecycle."""
    from dev.scripts.devctl.review_channel.handoff import (
        BridgeLiveness,
        extract_bridge_snapshot,
    )
    from dev.scripts.devctl.review_channel.turn_authority import (
        build_reviewer_turn_authority,
    )

    bridge_text = _build_bridge_text()
    snapshot = extract_bridge_snapshot(bridge_text)
    liveness = BridgeLiveness(
        overall_state="active",
        reviewer_mode="active_dual_agent",
        codex_poll_state="current",
        last_codex_poll_utc="2026-04-03T00:00:00Z",
        last_codex_poll_age_seconds=5,
        last_reviewed_scope_present=True,
        next_action_present=True,
        open_findings_present=True,
        claude_status_present=True,
        claude_ack_present=True,
        claude_ack_current=True,
        current_instruction_revision="56bcd5d01510",
        claude_ack_revision="56bcd5d01510",
        reviewed_hash_current=True,
        reviewer_freshness="fresh",
    )

    authority = build_reviewer_turn_authority(
        snapshot=snapshot,
        bridge_liveness=liveness,
        typed_review_state=None,
    )

    # Without lifecycle fields (publisher_running, reviewer_supervisor_running)
    # the fallback classifiers are skipped.  effective_reviewer_mode should
    # fall through to reviewer_mode ("active_dual_agent"), NOT a false
    # runtime_missing downgrade.
    assert authority.effective_reviewer_mode == "active_dual_agent"
    assert authority.reviewer_mode == "active_dual_agent"


def test_bridge_poll_partial_typed_state_skips_defaulted_authority() -> None:
    """Partial typed state (scaffolding but no launch_truth) must not use defaulted fields."""
    from dev.scripts.devctl.review_channel.handoff import (
        BridgeLiveness,
        extract_bridge_snapshot,
    )
    from dev.scripts.devctl.review_channel.turn_authority import (
        build_reviewer_turn_authority,
    )

    bridge_text = _build_bridge_text(
        instruction_revision="aabbccdd1122",
        claude_ack_revision="aabbccdd1122",
    )

    # Partial typed state: has review/queue/bridge scaffolding but bridge
    # section has NO launch_truth — simulates a payload that was NOT produced
    # by refresh_status_snapshot().
    partial_typed_state: dict[str, object] = {
        "review": {"bridge_path": "bridge.md", "review_channel_path": "dev/active/review_channel.md"},
        "queue": {"pending_total": 0, "pending_codex": 0, "pending_claude": 0,
                  "pending_cursor": 0, "pending_operator": 0, "stale_packet_count": 0,
                  "derived_next_instruction": "", "derived_next_instruction_source": {}},
        "current_session": {
            "current_instruction": "- Implement the bridge-poll action.",
            "current_instruction_revision": "aabbccdd1122",
            "implementer_status": "- waiting for reviewer poll",
            "implementer_ack": "- acknowledged; instruction-rev: `aabbccdd1122`",
            "implementer_ack_revision": "aabbccdd1122",
            "implementer_ack_state": "current",
            "implementer_state_hash": "",
            "open_findings": "- none",
            "last_reviewed_scope": "- bridge.md",
        },
        "bridge": {
            "reviewer_mode": "active_dual_agent",
            # NOTE: no launch_truth, no effective_reviewer_mode — partial state
        },
    }

    snapshot = extract_bridge_snapshot(bridge_text)
    liveness = BridgeLiveness(
        overall_state="active",
        reviewer_mode="active_dual_agent",
        codex_poll_state="current",
        last_codex_poll_utc="2026-04-03T00:00:00Z",
        last_codex_poll_age_seconds=5,
        last_reviewed_scope_present=True,
        next_action_present=True,
        open_findings_present=True,
        claude_status_present=True,
        claude_ack_present=True,
        claude_ack_current=True,
        current_instruction_revision="aabbccdd1122",
        claude_ack_revision="aabbccdd1122",
        reviewed_hash_current=True,
        reviewer_freshness="fresh",
    )

    authority = build_reviewer_turn_authority(
        snapshot=snapshot,
        bridge_liveness=liveness,
        typed_review_state=partial_typed_state,
    )

    # Partial state has no launch_truth so _typed_authority_complete=False.
    # Authority must NOT use defaulted reviewer_runtime fields.
    # effective_reviewer_mode should come from bridge_liveness (fallback chain)
    # not from the partial state's defaulted "active_dual_agent".
    assert authority.effective_reviewer_mode == "active_dual_agent"
    assert authority.reviewer_mode == "active_dual_agent"
    # launch_truth should be empty (no lifecycle data in BridgeLiveness)
    assert authority.launch_truth == ""
    # attention_status should be empty (no lifecycle → no fallback attention)
    assert authority.attention_status == ""


def test_bridge_poll_partial_typed_state_with_lifecycle_derives_authority() -> None:
    """Partial typed state carrying raw lifecycle booleans must derive authority."""
    from dev.scripts.devctl.review_channel.handoff import (
        BridgeLiveness,
        extract_bridge_snapshot,
    )
    from dev.scripts.devctl.review_channel.turn_authority import (
        build_reviewer_turn_authority,
    )

    bridge_text = _build_bridge_text(
        instruction_revision="aabbccdd1122",
        claude_ack_revision="aabbccdd1122",
    )

    # Partial typed state with raw lifecycle booleans but no computed
    # launch_truth — simulates a payload with lifecycle data that was NOT
    # run through refresh_status_snapshot().
    partial_typed_state: dict[str, object] = {
        "review": {"bridge_path": "bridge.md", "review_channel_path": "rc.md"},
        "queue": {"pending_total": 0, "pending_codex": 0, "pending_claude": 0,
                  "pending_cursor": 0, "pending_operator": 0, "stale_packet_count": 0,
                  "derived_next_instruction": "", "derived_next_instruction_source": {}},
        "current_session": {
            "current_instruction": "- Implement the bridge-poll action.",
            "current_instruction_revision": "aabbccdd1122",
            "implementer_status": "- waiting for reviewer poll",
            "implementer_ack": "- acknowledged; instruction-rev: `aabbccdd1122`",
            "implementer_ack_revision": "aabbccdd1122",
            "implementer_ack_state": "current",
            "implementer_state_hash": "",
            "open_findings": "- none",
            "last_reviewed_scope": "- bridge.md",
        },
        "bridge": {
            "reviewer_mode": "active_dual_agent",
            # Raw lifecycle booleans present but no computed launch_truth
            "publisher_running": True,
            "codex_conductor_active": False,
            "claude_conductor_active": False,
        },
    }

    snapshot = extract_bridge_snapshot(bridge_text)
    liveness = BridgeLiveness(
        overall_state="active",
        reviewer_mode="active_dual_agent",
        codex_poll_state="current",
        last_codex_poll_utc="2026-04-03T00:00:00Z",
        last_codex_poll_age_seconds=5,
        last_reviewed_scope_present=True,
        next_action_present=True,
        open_findings_present=True,
        claude_status_present=True,
        claude_ack_present=True,
        claude_ack_current=True,
        current_instruction_revision="aabbccdd1122",
        claude_ack_revision="aabbccdd1122",
        reviewed_hash_current=True,
        reviewer_freshness="fresh",
    )

    authority = build_reviewer_turn_authority(
        snapshot=snapshot,
        bridge_liveness=liveness,
        typed_review_state=partial_typed_state,
    )

    # With publisher_running=True but both conductors inactive, classifiers
    # should derive detached_runtime_only → tools_only → relaunch required.
    assert authority.launch_truth == "detached_runtime_only"
    assert authority.effective_reviewer_mode == "tools_only"
    assert authority.attention_status == "review_loop_relaunch_required"
    assert authority.next_turn_required is False
    assert authority.next_turn_role == ""
    assert authority.next_turn_reason == "inactive"
