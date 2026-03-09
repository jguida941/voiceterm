"""Tests for check_review_channel_bridge governance script."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_review_channel_bridge.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "check_review_channel_bridge_script", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_review_channel_bridge.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_code_audit_text(script) -> str:
    lines = [
        "# Code Audit Channel",
        "",
        "## Start-Of-Conversation Rules",
        "",
        "Codex is the reviewer. Claude is the coder.",
        "At conversation start, both agents must bootstrap repo authority in this order before acting: `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and `dev/active/review_channel.md`.",
        "Codex must poll non-`code_audit.md` worktree changes every 2-3 minutes while code is moving.",
        "Codex must exclude `code_audit.md` itself when computing the reviewed worktree hash.",
        "Each meaningful review must include an operator-visible chat update.",
        "Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
        "Claude should start from `Current Verdict`, `Open Findings`, and `Current Instruction For Claude`, then acknowledge the active instruction in `Claude Ack` before coding.",
        "When the current slice is accepted and scoped plan work remains, Codex must derive the next highest-priority unchecked plan item from the active-plan chain and rewrite `Current Instruction For Claude` for the next slice instead of idling at \"all green so far.\"",
        "Only the Codex conductor may update the Codex-owned sections in this file.",
        "Only the Claude conductor may update the Claude-owned sections in this file.",
        "Specialist workers should wake on owned-path changes or explicit conductor request instead of every worker polling the full tree blindly on the same cadence.",
        "Codex must emit an operator-visible heartbeat every 5 minutes while code is moving, even when the blocker set is unchanged.",
        "",
        "- Last Codex poll: `2026-03-08T04:58:19Z`",
        "- Last Codex poll (Local America/New_York): `2026-03-07 23:58:19 EST`",
        f"- Last non-audit worktree hash: `{'a' * 64}`",
        "",
    ]
    for heading in script.REQUIRED_CODE_AUDIT_H2[1:]:
        lines.append(f"## {heading}")
        lines.append("")
        if heading == "Current Instruction For Claude":
            lines.append("- continue with the next scoped task")
        elif heading == "Last Reviewed Scope":
            lines.append("- app/operator_console/theme/theme_engine.py")
        else:
            lines.append("placeholder")
        lines.append("")
    return "\n".join(lines)


def _valid_review_channel_text(script) -> str:
    return "\n".join(
        [
            "# Review Channel + Shared Screen Plan",
            "",
            "## Transitional Markdown Bridge (Current Operating Mode)",
            "",
            "`code_audit.md` is the temporary bridge.",
            "In autonomous mode `MASTER_PLAN.md` remains the canonical tracker and",
            "   `INDEX.md` remains the router for the minimal active docs set.",
            "For the current operator-facing loop, each meaningful Codex reviewer write to",
            "   `code_audit.md` must also emit a concise operator-visible chat update.",
            "Bridge writes stay conductor-owned: only one Codex conductor updates the Codex-owned bridge",
            "sections while specialist workers report back instead of editing the bridge directly.",
            "The reviewer should emit an operator-visible",
            "heartbeat every five minutes even when the blocker set is unchanged.",
            "Default multi-agent wakeups should be change-routed instead of brute-force.",
            "The header should expose `last_poll_local` for the operator.",
            "Until the structured path lands, `check_review_channel_bridge.py` guards this bridge.",
            "The repo-native continuous fallback is `devctl swarm_run --continuous`.",
            "Completion stall is a named failure mode that the bridge must prevent.",
        ]
    )


def _inactive_review_channel_text() -> str:
    return "\n".join(
        [
            "# Review Channel + Shared Screen Plan",
            "",
            "## Structured Review Channel (Planned Mode)",
            "",
            "The markdown bridge has been retired for this scenario.",
        ]
    )


class CheckReviewChannelBridgeTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()
        cls.fixed_now = datetime(2026, 3, 8, 5, 0, 0, tzinfo=timezone.utc)

    def _temp_path(self, name: str, text: str) -> Path:
        tmp_dir = tempfile.TemporaryDirectory(dir=REPO_ROOT)
        self.addCleanup(tmp_dir.cleanup)
        path = Path(tmp_dir.name) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_build_report_ok_for_complete_bridge_contract(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=True), patch.object(
            self.script, "_current_utc", return_value=self.fixed_now
        ):
            report = self.script.build_report()
        self.assertTrue(report["ok"])
        self.assertTrue(report["review_bridge_active"])
        self.assertEqual(report["code_audit"]["missing_h2"], [])
        self.assertEqual(report["code_audit"]["missing_markers"], [])
        self.assertEqual(report["review_channel"]["missing_markers"], [])

    def test_build_report_allows_missing_code_audit_when_bridge_is_inactive(self) -> None:
        missing_code_audit = REPO_ROOT / "code_audit-does-not-exist.md"
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _inactive_review_channel_text(),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", missing_code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ):
            report = self.script.build_report()
        self.assertTrue(report["ok"])
        self.assertFalse(report["review_bridge_active"])
        self.assertFalse(report["code_audit"]["active"])
        self.assertNotIn("error", report["code_audit"])

    def test_build_report_fails_for_untracked_code_audit_when_bridge_is_active(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=False), patch.object(
            self.script, "_current_utc", return_value=self.fixed_now
        ):
            report = self.script.build_report()
        self.assertFalse(report["ok"])
        self.assertTrue(report["review_bridge_active"])
        self.assertTrue(report["code_audit"].get("untracked", False))
        self.assertIn("untracked", report["code_audit"].get("error", ""))

    def test_build_report_ok_for_tracked_files_when_bridge_is_active(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=True), patch.object(
            self.script, "_current_utc", return_value=self.fixed_now
        ):
            report = self.script.build_report()
        self.assertTrue(report["ok"])
        self.assertTrue(report["review_bridge_active"])
        self.assertNotIn("untracked", report["code_audit"])
        self.assertNotIn("untracked", report["review_channel"])

    def test_build_report_skips_tracking_check_when_bridge_is_inactive(self) -> None:
        missing_code_audit = REPO_ROOT / "code_audit-does-not-exist.md"
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _inactive_review_channel_text(),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", missing_code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=False) as mock_tracked:
            report = self.script.build_report()
        self.assertTrue(report["ok"])
        mock_tracked.assert_not_called()

    def test_build_report_flags_missing_code_audit_start_rule(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script).replace(
                "Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.\n",
                "",
            ),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=True), patch.object(
            self.script, "_current_utc", return_value=self.fixed_now
        ):
            report = self.script.build_report()
        self.assertFalse(report["ok"])
        self.assertIn(
            "Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
            report["code_audit"]["missing_markers"],
        )

    def test_build_report_flags_missing_review_channel_bridge_guard_marker(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script).replace(
                "Until the structured path lands, `check_review_channel_bridge.py` guards this bridge.",
                "",
            ),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=True), patch.object(
            self.script, "_current_utc", return_value=self.fixed_now
        ):
            report = self.script.build_report()
        self.assertFalse(report["ok"])
        self.assertIn(
            "`check_review_channel_bridge.py`",
            report["review_channel"]["missing_markers"],
        )

    def test_build_report_flags_stale_last_codex_poll(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script),
        )
        stale_now = datetime(2026, 3, 8, 6, 0, 0, tzinfo=timezone.utc)
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=True), patch.object(
            self.script, "_current_utc", return_value=stale_now
        ):
            report = self.script.build_report()
        self.assertFalse(report["ok"])
        self.assertIn("metadata_errors", report["code_audit"])
        self.assertTrue(
            any("stale" in error for error in report["code_audit"]["metadata_errors"])
        )

    def test_build_report_flags_invalid_worktree_hash(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script).replace("a" * 64, "abc123"),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=True), patch.object(
            self.script, "_current_utc", return_value=self.fixed_now
        ):
            report = self.script.build_report()
        self.assertFalse(report["ok"])
        self.assertIn("metadata_errors", report["code_audit"])
        self.assertTrue(
            any("worktree hash" in error.lower() for error in report["code_audit"]["metadata_errors"])
        )

    def test_build_report_flags_missing_last_reviewed_scope_state(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script).replace(
                "- app/operator_console/theme/theme_engine.py",
                "",
            ),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=True), patch.object(
            self.script, "_current_utc", return_value=self.fixed_now
        ):
            report = self.script.build_report()
        self.assertFalse(report["ok"])
        self.assertIn("state_errors", report["code_audit"])
        self.assertTrue(
            any(
                "Last Reviewed Scope" in error
                for error in report["code_audit"]["state_errors"]
            )
        )

    def test_build_report_flags_idle_current_instruction_state(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script).replace(
                "- continue with the next scoped task",
                "placeholder",
            ),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=True), patch.object(
            self.script, "_current_utc", return_value=self.fixed_now
        ):
            report = self.script.build_report()
        self.assertFalse(report["ok"])
        self.assertIn("state_errors", report["code_audit"])
        self.assertTrue(
            any(
                "Current Instruction For Claude" in error
                for error in report["code_audit"]["state_errors"]
            )
        )

    def test_build_report_flags_resolved_bridge_without_promoted_next_task(self) -> None:
        code_audit = self._temp_path(
            "code_audit.md",
            _valid_code_audit_text(self.script)
            .replace("## Current Verdict\n\nplaceholder", "## Current Verdict\n\n- resolved")
            .replace("## Open Findings\n\nplaceholder", "## Open Findings\n\n- (none)")
            .replace("- continue with the next scoped task", "- all green so far"),
        )
        review_channel = self._temp_path(
            "dev/active/review_channel.md",
            _valid_review_channel_text(self.script),
        )
        with patch.object(self.script, "CODE_AUDIT_PATH", code_audit), patch.object(
            self.script, "REVIEW_CHANNEL_PATH", review_channel
        ), patch.object(self.script, "_is_tracked_by_git", return_value=True), patch.object(
            self.script, "_current_utc", return_value=self.fixed_now
        ):
            report = self.script.build_report()
        self.assertFalse(report["ok"])
        self.assertIn("state_errors", report["code_audit"])
        self.assertTrue(
            any(
                "promote the next scoped task" in error
                for error in report["code_audit"]["state_errors"]
            )
        )
