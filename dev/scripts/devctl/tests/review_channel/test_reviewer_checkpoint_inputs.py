"""Focused tests for safe reviewer-checkpoint input handling."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import review_channel as review_channel_command
from dev.scripts.devctl.commands.review_channel_command.helpers import _validate_args
from dev.scripts.devctl.review_channel.reviewer_state import (
    ReviewerCheckpointUpdate,
    write_reviewer_checkpoint,
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
            "For the current operator-facing loop, each meaningful Codex reviewer write to",
            "   `bridge.md` must also emit a concise operator-visible chat update.",
            "Bridge writes stay conductor-owned: only one Codex conductor updates the Codex-owned bridge",
            "sections while specialist workers report back instead of editing the bridge directly.",
            "Bridge behavior is mode-aware. When `Reviewer mode` is `active_dual_agent`, Claude must treat `bridge.md` as the live reviewer/coder authority and keep polling it instead of waiting for the operator to restate the process.",
            "If reviewer-owned bridge state says `hold steady`, `waiting for reviewer promotion`, `Codex committing/pushing`, or equivalent wait-state language, Claude must stay in polling mode. It must not mine plan docs for side work or self-promote the next slice until a reviewer-owned section changes.",
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
            "| `AGENT-1` | Codex reviewer | `dev/active/review_channel.md` | `MP-355` | `../wt-codex` | `feature/codex` |",
            "| `AGENT-9` | Claude coder | `dev/active/review_channel.md` | `MP-355` | `../wt-claude` | `feature/claude` |",
        ]
    )


def _build_bridge_text() -> str:
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
            "- Last Codex poll (Local America/New_York): `2026-03-20 00:00:00 EDT`",
            "- Reviewer mode: `active_dual_agent`",
            f"- Last non-audit worktree hash: `{'a' * 64}`",
            "- Current instruction revision: `56bcd5d01510`",
            "",
            "## Protocol",
            "",
            "- Poll target: every 5 minutes when code is moving (operator-directed live loop cadence)",
            "- Only unresolved findings, current verdicts, current ack state, and next instructions should stay live here.",
            "",
            "## Poll Status",
            "",
            "- active reviewer loop",
            "",
            "## Current Verdict",
            "",
            "- still in progress",
            "",
            "## Open Findings",
            "",
            "- bridge needs hardening",
            "",
            "## Current Instruction For Claude",
            "",
            "- hold steady",
            "",
            "## Claude Status",
            "",
            "- waiting",
            "",
            "## Claude Questions",
            "",
            "- none",
            "",
            "## Claude Ack",
            "",
            "- acknowledged; instruction-rev: `56bcd5d01510`",
            "",
            "## Last Reviewed Scope",
            "",
            "- bridge.md",
            "",
        ]
    )


def _reviewer_args() -> SimpleNamespace:
    return SimpleNamespace(
        action="reviewer-checkpoint",
        execution_mode="auto",
        terminal="none",
        terminal_profile="auto-dark",
        rollover_threshold_pct=50,
        rollover_trigger="context-threshold",
        await_ack_seconds=180,
        codex_workers=8,
        claude_workers=8,
        dangerous=False,
        approval_mode="balanced",
        reviewer_mode="active_dual_agent",
        reason="test-review",
        expected_instruction_revision="56bcd5d01510",
        verdict=None,
        verdict_file=None,
        open_findings=None,
        open_findings_file=None,
        instruction=None,
        instruction_file=None,
        checkpoint_payload_file=None,
        reviewed_scope_item=["bridge.md"],
        rotate_instruction_revision=False,
        follow=False,
        start_publisher_if_missing=False,
        format="json",
        output=None,
        pipe_command=None,
        pipe_args=None,
    )


def test_validate_args_accepts_file_backed_reviewer_checkpoint_fields() -> None:
    args = _reviewer_args()
    args.verdict_file = "verdict.md"
    args.open_findings_file = "findings.md"
    args.instruction_file = "instruction.md"

    _validate_args(args)


def test_validate_args_rejects_inline_and_file_for_same_checkpoint_field() -> None:
    args = _reviewer_args()
    args.verdict = "- inline"
    args.verdict_file = "verdict.md"
    args.open_findings_file = "findings.md"
    args.instruction_file = "instruction.md"

    with pytest.raises(
        ValueError,
        match="exactly one of --verdict or --verdict-file",
    ):
        _validate_args(args)


def test_validate_args_rejects_missing_expected_instruction_revision() -> None:
    args = _reviewer_args()
    args.expected_instruction_revision = None
    args.verdict = "- accepted"
    args.open_findings_file = "findings.md"
    args.instruction_file = "instruction.md"

    with pytest.raises(
        ValueError,
        match="--expected-instruction-revision",
    ):
        _validate_args(args)


def test_validate_args_accepts_checkpoint_payload_file() -> None:
    args = _reviewer_args()
    args.checkpoint_payload_file = "checkpoint.json"
    args.reviewed_scope_item = []

    _validate_args(args)


def test_validate_args_rejects_mixed_checkpoint_payload_modes() -> None:
    args = _reviewer_args()
    args.checkpoint_payload_file = "checkpoint.json"
    args.instruction_file = "instruction.md"

    with pytest.raises(
        ValueError,
        match="does not allow --checkpoint-payload-file",
    ):
        _validate_args(args)


def test_run_reviewer_checkpoint_reads_file_backed_markdown_fields(
    tmp_path: Path,
) -> None:
    root = tmp_path
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_build_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
    status_dir = root / "dev/reports/review_channel/latest"
    status_dir.mkdir(parents=True, exist_ok=True)
    output_path = root / "report.json"
    verdict_path = root / "verdict.md"
    findings_path = root / "findings.md"
    instruction_path = root / "instruction.md"
    verdict_text = (
        "- Accepted `check_startup_authority_contract.py`.\n"
        "- Promote the next bounded Phase 1 slice."
    )
    findings_text = (
        "- Raw markdown polling is still brittle.\n"
        "- Keep unrelated drift outside this slice."
    )
    instruction_text = (
        "- Implement `python3 dev/scripts/devctl.py review-channel --action bridge-poll --terminal none --format json`.\n"
        "- Preserve `current_instruction_revision` and `changed_since_last_ack`."
    )
    verdict_path.write_text(verdict_text, encoding="utf-8")
    findings_path.write_text(findings_text, encoding="utf-8")
    instruction_path.write_text(instruction_text, encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(
        [
            "review-channel",
            "--action",
            "reviewer-checkpoint",
            "--terminal",
            "none",
            "--format",
            "json",
            "--review-channel-path",
            str(review_channel_path.relative_to(root)),
            "--bridge-path",
            str(bridge_path.relative_to(root)),
            "--status-dir",
            str(status_dir.relative_to(root)),
            "--verdict-file",
            str(verdict_path.relative_to(root)),
            "--open-findings-file",
            str(findings_path.relative_to(root)),
            "--instruction-file",
            str(instruction_path.relative_to(root)),
            "--expected-instruction-revision",
            "56bcd5d01510",
            "--reviewed-scope-item",
            "dev/scripts/devctl/commands/review_channel/_reviewer.py",
            "--output",
            str(output_path),
        ]
    )

    with (
        patch.object(review_channel_command, "REPO_ROOT", root),
        patch.object(
            review_channel_command,
            "_ensure_reviewer_supervisor_running",
            return_value={"attempted": False, "started": False, "reason": "already_running"},
        ),
    ):
        rc = review_channel_command.run(args)

    assert rc == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    updated_bridge = bridge_path.read_text(encoding="utf-8")
    assert verdict_text in updated_bridge
    assert findings_text in updated_bridge
    assert instruction_text in updated_bridge
    assert "Please run /login" not in updated_bridge


def test_run_reviewer_checkpoint_reads_typed_payload_file(
    tmp_path: Path,
) -> None:
    root = tmp_path
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_build_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
    status_dir = root / "dev/reports/review_channel/latest"
    status_dir.mkdir(parents=True, exist_ok=True)
    output_path = root / "report.json"
    payload_path = root / "checkpoint.json"
    verdict_text = (
        "- Accepted `check_startup_authority_contract.py`.\n"
        "- Promote the next bounded Phase 1 slice."
    )
    findings_text = (
        "- Raw markdown polling is still brittle.\n"
        "- Keep unrelated drift outside this slice."
    )
    instruction_text = (
        "- Implement `python3 dev/scripts/devctl.py review-channel --action bridge-poll --terminal none --format json`.\n"
        "- Preserve `current_instruction_revision` and `changed_since_last_ack`."
    )
    payload_path.write_text(
        json.dumps(
            {
                "verdict": verdict_text,
                "open_findings": findings_text,
                "instruction": instruction_text,
                "reviewed_scope_items": [
                    "dev/scripts/devctl/commands/review_channel/_reviewer.py",
                    "dev/scripts/devctl/review_channel/parser_bridge_controls.py",
                ],
            }
        ),
        encoding="utf-8",
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "review-channel",
            "--action",
            "reviewer-checkpoint",
            "--terminal",
            "none",
            "--format",
            "json",
            "--review-channel-path",
            str(review_channel_path.relative_to(root)),
            "--bridge-path",
            str(bridge_path.relative_to(root)),
            "--status-dir",
            str(status_dir.relative_to(root)),
            "--checkpoint-payload-file",
            str(payload_path.relative_to(root)),
            "--expected-instruction-revision",
            "56bcd5d01510",
            "--output",
            str(output_path),
        ]
    )

    with (
        patch.object(review_channel_command, "REPO_ROOT", root),
        patch.object(
            review_channel_command,
            "_ensure_reviewer_supervisor_running",
            return_value={"attempted": False, "started": False, "reason": "already_running"},
        ),
    ):
        rc = review_channel_command.run(args)

    assert rc == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    updated_bridge = bridge_path.read_text(encoding="utf-8")
    assert verdict_text in updated_bridge
    assert findings_text in updated_bridge
    assert instruction_text in updated_bridge
    assert (
        "dev/scripts/devctl/review_channel/parser_bridge_controls.py"
        in updated_bridge
    )


def test_write_reviewer_checkpoint_normalizes_leading_blank_padding(
    tmp_path: Path,
) -> None:
    root = tmp_path
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_build_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    padded_bridge = _build_bridge_text().replace(
        "## Current Instruction For Claude\n\n- hold steady",
        "## Current Instruction For Claude\n\n\n\n\n- hold steady",
    )
    bridge_path.write_text(padded_bridge, encoding="utf-8")

    with patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot"):
        write_reviewer_checkpoint(
            repo_root=root,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="normalize-padding",
            checkpoint=ReviewerCheckpointUpdate(
                current_verdict="- accepted",
                open_findings="- none",
                current_instruction="- next task",
                reviewed_scope_items=("bridge.md",),
            ),
        )

    updated_bridge = bridge_path.read_text(encoding="utf-8")
    assert (
        "## Current Instruction For Claude\n\n- next task\n\n## Claude Status"
        in updated_bridge
    )


def test_write_reviewer_checkpoint_rewrites_poll_status_immediately_under_heading(
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

    with patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot"):
        write_reviewer_checkpoint(
            repo_root=root,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="test-checkpoint-padding",
            checkpoint=ReviewerCheckpointUpdate(
                current_verdict="- accepted",
                open_findings="- none",
                current_instruction="- next task",
                reviewed_scope_items=("bridge.md",),
            ),
        )

    updated_bridge = bridge_path.read_text(encoding="utf-8")
    assert (
        "## Poll Status\n\n- Reviewer checkpoint updated through repo-owned tooling"
        in updated_bridge
    )
    assert "oldrev12345678" not in updated_bridge
    assert "continue the old slice" not in updated_bridge


def test_write_reviewer_checkpoint_rejects_stale_expected_instruction_revision(
    tmp_path: Path,
) -> None:
    root = tmp_path
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_build_review_channel_text(), encoding="utf-8")
    bridge_path = root / "bridge.md"
    bridge_path.write_text(_build_bridge_text(), encoding="utf-8")

    with (
        patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot"),
        pytest.raises(ValueError, match="refused stale bridge write"),
    ):
        write_reviewer_checkpoint(
            repo_root=root,
            bridge_path=bridge_path,
            reviewer_mode="active_dual_agent",
            reason="stale-write",
            checkpoint=ReviewerCheckpointUpdate(
                current_verdict="- accepted",
                open_findings="- none",
                current_instruction="- next task",
                reviewed_scope_items=("bridge.md",),
                expected_instruction_revision="deadbeefcafe",
            ),
        )
