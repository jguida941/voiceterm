"""Tests for devctl dashboard command."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands import dashboard, dashboard_render


def _make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
        "follow": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _write_artifact(root: Path, rel_path: str, data: dict) -> None:
    full = root / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(json.dumps(data), encoding="utf-8")


def _minimal_compact() -> dict:
    return {
        "current_session": {
            "current_instruction": "fix code shape",
            "current_instruction_revision": "abc123",
            "implementer_status": "working on it",
            "open_findings": "None",
        }
    }


def _minimal_push() -> dict:
    return {
        "ok": False,
        "status": "blocked",
        "reason": "validation_failed",
        "branch": "feature/test",
        "head_commit": "deadbeef1234567",
        "preflight_step": {"returncode": 1},
        "push_stages": {"post_push_green": False},
    }


def _minimal_receipt() -> dict:
    return {
        "push_action": "run_devctl_push",
        "push_eligible_now": True,
        "review_gate_allows_push": True,
        "safe_to_continue_editing": True,
    }


def _minimal_agents() -> dict:
    return {
        "agents": [
            {
                "agent_id": "codex",
                "provider": "codex",
                "lane_title": "Reviewer",
                "job_state": "review_needed",
            },
            {
                "agent_id": "claude",
                "provider": "claude",
                "lane_title": "Implementer",
                "job_state": "implementing",
            },
        ]
    }


def _minimal_pipeline() -> dict:
    return {"state": "push_blocked", "blocked_reason": "pipeline_unavailable"}


def _minimal_bridge_text() -> str:
    return (
        "# Review Bridge\n\n"
        "- Last Codex poll: `2026-04-04T01:52:56Z`\n"
        "- Reviewer mode: `single_agent`\n"
    )


class TestDashboardSnapshotSections(unittest.TestCase):
    """Verify the snapshot has all required top-level sections."""

    def test_dashboard_snapshot_has_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            _write_artifact(root, "dev/reports/startup/latest/receipt.json", _minimal_receipt())
            _write_artifact(root, "dev/reports/review_channel/latest/registry/agents.json", _minimal_agents())
            _write_artifact(root, "dev/reports/review_channel/latest/commit_pipeline.json", _minimal_pipeline())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test", "head": "deadbee", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test-repo"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            required = {"repo", "review", "workers", "publication", "quality", "coordination", "flow"}
            self.assertTrue(required.issubset(snapshot.keys()), f"Missing: {required - snapshot.keys()}")
            self.assertEqual(snapshot["schema_version"], 1)
            self.assertEqual(snapshot["contract_id"], "DashboardSnapshot")


class TestDashboardJsonOutput(unittest.TestCase):
    """Verify JSON output has all sections and is valid JSON."""

    def test_run_produces_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_file = root / "out.json"
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            _write_artifact(root, "dev/reports/startup/latest/receipt.json", _minimal_receipt())
            _write_artifact(root, "dev/reports/review_channel/latest/registry/agents.json", _minimal_agents())
            _write_artifact(root, "dev/reports/review_channel/latest/commit_pipeline.json", _minimal_pipeline())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "build_snapshot") as mock_build:
                mock_build.return_value = {
                    "schema_version": 1,
                    "contract_id": "DashboardSnapshot",
                    "timestamp": "2026-04-04T00:00:00Z",
                    "repo": {"name": "test", "branch": "main", "head": "abc", "worktree": "CLEAN"},
                    "review": {"mode": "single_agent", "reviewer_state": "idle"},
                    "workers": [],
                    "publication": {"effective": "n/a"},
                    "quality": {"docs_gate": "n/a", "plan_sync": "n/a", "code_shape": "n/a"},
                    "coordination": {"pending_findings": "None", "next_action": "n/a", "instruction_rev": "n/a"},
                    "flow": {"review": "unknown", "implement": "unknown", "verify": "unknown", "checkpoint": "unknown", "push": "unknown"},
                }
                args = _make_args(format="json", output=str(output_file))
                rc = dashboard.run(args)

            self.assertEqual(rc, 0)
            data = json.loads(output_file.read_text(encoding="utf-8"))
            self.assertIn("repo", data)
            self.assertIn("review", data)
            self.assertIn("publication", data)


class TestDashboardTerminalOutput(unittest.TestCase):
    """Verify terminal output contains ANSI codes."""

    def test_run_produces_terminal_output(self) -> None:
        snapshot = {
            "schema_version": 1,
            "contract_id": "DashboardSnapshot",
            "timestamp": "2026-04-04T00:00:00Z",
            "repo": {"name": "test-repo", "branch": "main", "head": "abc1234", "worktree": "CLEAN"},
            "review": {
                "reviewer_state": "review_needed",
                "reviewer_provider": "codex",
                "implementer_state": "implementing",
                "implementer_provider": "claude",
                "current_turn": "Implementer",
                "instruction": "fix tests",
                "last_poll": "2026-04-04T01:52:56Z",
                "mode": "single_agent",
            },
            "workers": [
                {"id": "codex", "role": "Reviewer", "provider": "codex", "state": "review_needed"},
            ],
            "publication": {"effective": "NOT CURRENT", "why": "push failed", "post_push": "FAIL", "evidence": "dev/reports/push/latest.json"},
            "quality": {"docs_gate": "n/a", "plan_sync": "n/a", "code_shape": "FAIL"},
            "coordination": {"pending_findings": "None", "next_action": "run_devctl_push", "instruction_rev": "abc123"},
            "flow": {"review": "pass", "implement": "active", "verify": "unknown", "checkpoint": "pass", "push": "blocked"},
        }
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("\033[", output)
        self.assertIn("GOVERNANCE DASHBOARD", output)
        self.assertIn("REVIEW", output)
        self.assertIn("PUBLICATION", output)
        self.assertIn("QUALITY", output)
        self.assertIn("COORDINATION", output)
        self.assertIn("FLOW", output)
        self.assertIn("test-repo", output)


class TestDashboardMissingArtifacts(unittest.TestCase):
    """Verify graceful degradation when files do not exist."""

    def test_run_handles_missing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "0000000", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="empty-repo"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertEqual(snapshot["repo"]["name"], "empty-repo")
            self.assertEqual(snapshot["publication"]["effective"], "n/a")
            self.assertEqual(snapshot["quality"]["docs_gate"], "n/a")
            self.assertEqual(snapshot["quality"]["code_shape"], "n/a")
            # Should not crash; all sections present
            required = {"repo", "review", "workers", "publication", "quality", "coordination", "flow"}
            self.assertTrue(required.issubset(snapshot.keys()))

            # Both renderers should work on degraded snapshot
            terminal = dashboard_render.render_terminal(snapshot)
            self.assertIn("GOVERNANCE DASHBOARD", terminal)
            md = dashboard_render.render_markdown(snapshot)
            self.assertIn("# Governance Dashboard", md)
            raw = dashboard_render.render_json(snapshot)
            parsed = json.loads(raw)
            self.assertIn("repo", parsed)


class TestCliParserWiring(unittest.TestCase):
    """Verify the dashboard subparser is registered correctly."""

    def test_dashboard_parser_exists(self) -> None:
        from dev.scripts.devctl.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["dashboard", "--format", "json"])
        self.assertEqual(args.command, "dashboard")
        self.assertEqual(args.format, "json")

    def test_dashboard_follow_flag(self) -> None:
        from dev.scripts.devctl.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["dashboard", "--follow"])
        self.assertTrue(args.follow)

    def test_dashboard_default_format_is_terminal(self) -> None:
        from dev.scripts.devctl.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["dashboard"])
        self.assertEqual(args.format, "terminal")


if __name__ == "__main__":
    unittest.main()
