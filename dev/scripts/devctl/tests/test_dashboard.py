"""Tests for devctl dashboard command — dense multi-column layout."""

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
            "implementer_ack_state": "current",
            "open_findings": "- F1: code-shape debt\n- F2: stale docs",
        }
    }


def _minimal_push() -> dict:
    return {
        "ok": False,
        "status": "blocked",
        "reason": "validation_failed",
        "branch": "feature/test",
        "head_commit": "deadbeef1234567",
        "preflight_step": {"returncode": 1, "failure_output": "dev/scripts/devctl/common_io.py exceeded limit"},
        "push_stages": {"post_push_green": False, "published_remote": False, "validation_ready": False},
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
                "waiting_on": "worktree",
                "updated_at": "2026-04-04T01:50:00Z",
            },
            {
                "agent_id": "claude",
                "provider": "claude",
                "lane_title": "Implementer",
                "job_state": "implementing",
                "waiting_on": "reviewer",
                "updated_at": "2026-04-04T01:52:00Z",
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


def _full_snapshot() -> dict:
    """A fully populated snapshot for terminal rendering tests."""
    return {
        "schema_version": 2,
        "contract_id": "DashboardSnapshot",
        "timestamp": "2026-04-04T00:00:00Z",
        "repo": {
            "name": "test-repo",
            "branch": "feature/governance-quality-sweep",
            "head": "abc1234",
            "worktree": "CLEAN",
        },
        "now": {
            "owner": "Reviewer",
            "owner_provider": "codex",
            "next_action": "review worker results and checkpoint",
            "top_blocker": "code-shape debt in common_io.py",
            "last_change_age_s": 42,
            "last_change_label": "42s ago",
        },
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
            {"id": "W1", "agent_id": "codex", "scope": "Reviewer", "provider": "codex", "state": "REVIEW_NEEDED", "age": "12m ago", "last_update": "worktree"},
            {"id": "W2", "agent_id": "claude", "scope": "Implementer", "provider": "claude", "state": "IMPLEMENTING", "age": "8m ago", "last_update": "reviewer"},
        ],
        "plan": {
            "slice": "MP-377 publication-target parity",
            "progress": "3/3 sub-slices complete",
            "open_findings": 2,
            "pending": 0,
        },
        "publication": {
            "state": "NOT_PUBLISHED",
            "effective": "NOT CURRENT",
            "why": "validation_failed",
            "post_push": "FAIL",
            "evidence": "dev/reports/push/latest.json",
            "target_match": {"branch": True, "head": False, "target": False, "remote": False},
        },
        "quality": {
            "docs_gate": "PASS",
            "plan_sync": "PASS",
            "bridge": "PASS",
            "code_shape": "FAIL",
            "instr_sync": "PASS",
            "clippy": "n/a",
            "failing": ["dev/scripts/devctl/common_io.py"],
        },
        "coordination": {
            "pending_packets": 0,
            "instruction_rev": "f7f80b28c5fe",
            "reviewer_age": "18s ago",
            "implementer_state": "current",
            "pending_findings": "2 findings",
            "next_action": "run_devctl_push",
        },
        "flow": {
            "review": "pass",
            "implement": "active",
            "verify": "unknown",
            "checkpoint": "pass",
            "push": "blocked",
        },
    }


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

            required = {"repo", "now", "review", "workers", "plan", "publication", "quality", "coordination", "flow"}
            self.assertTrue(required.issubset(snapshot.keys()), f"Missing: {required - snapshot.keys()}")
            self.assertEqual(snapshot["schema_version"], 2)
            self.assertEqual(snapshot["contract_id"], "DashboardSnapshot")

    def test_now_section_populated(self) -> None:
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

            now = snapshot["now"]
            self.assertIn("owner", now)
            self.assertIn("next_action", now)
            self.assertIn("top_blocker", now)
            self.assertIn("last_change_label", now)

    def test_plan_section_populated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            _write_artifact(root, "dev/reports/startup/latest/receipt.json", _minimal_receipt())
            _write_artifact(root, "dev/reports/review_channel/latest/registry/agents.json", _minimal_agents())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test", "head": "deadbee", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test-repo"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            plan = snapshot["plan"]
            self.assertIn("slice", plan)
            self.assertIn("progress", plan)
            self.assertIn("open_findings", plan)
            self.assertEqual(plan["open_findings"], 2)

    def test_workers_have_enriched_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/review_channel/latest/registry/agents.json", _minimal_agents())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            workers = snapshot["workers"]
            self.assertEqual(len(workers), 2)
            self.assertEqual(workers[0]["id"], "W1")
            self.assertIn("scope", workers[0])
            self.assertIn("age", workers[0])
            self.assertIn("state", workers[0])

    def test_publication_has_target_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            # Use a HEAD that differs from push head_commit[:7] ("deadbee")
            with patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test", "head": "abc1234", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            pub = snapshot["publication"]
            self.assertIn("target_match", pub)
            self.assertIn("state", pub)
            tm = pub["target_match"]
            self.assertTrue(tm["branch"])
            self.assertFalse(tm["head"])

    def test_quality_has_extended_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test", "head": "deadbee", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            quality = snapshot["quality"]
            for gate in ("docs_gate", "plan_sync", "bridge", "code_shape", "instr_sync", "clippy"):
                self.assertIn(gate, quality, f"Missing gate: {gate}")
            self.assertIn("failing", quality)

    def test_coordination_compact_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/startup/latest/receipt.json", _minimal_receipt())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            coord = snapshot["coordination"]
            self.assertIn("pending_packets", coord)
            self.assertIn("instruction_rev", coord)
            self.assertIn("reviewer_age", coord)
            self.assertIn("implementer_state", coord)


class TestDashboardJsonOutput(unittest.TestCase):
    """Verify JSON output has all sections and is valid JSON."""

    def test_run_produces_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_file = root / "out.json"

            with patch.object(dashboard, "build_snapshot") as mock_build:
                mock_build.return_value = _full_snapshot()
                args = _make_args(format="json", output=str(output_file))
                rc = dashboard.run(args)

            self.assertEqual(rc, 0)
            data = json.loads(output_file.read_text(encoding="utf-8"))
            self.assertIn("repo", data)
            self.assertIn("now", data)
            self.assertIn("review", data)
            self.assertIn("workers", data)
            self.assertIn("plan", data)
            self.assertIn("publication", data)


class TestDashboardTerminalOutput(unittest.TestCase):
    """Verify terminal output contains all dense layout sections."""

    def test_terminal_has_all_sections(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("\033[", output)
        self.assertIn("GOVERNANCE DASHBOARD", output)
        self.assertIn("NOW", output)
        self.assertIn("WORKERS", output)
        self.assertIn("PLAN", output)
        self.assertIn("PUBLICATION", output)
        self.assertIn("QUALITY", output)
        self.assertIn("COORDINATION", output)
        self.assertIn("FLOW", output)
        self.assertIn("test-repo", output)

    def test_terminal_now_section_content(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("Owner", output)
        self.assertIn("Next action", output)
        self.assertIn("Top blocker", output)
        self.assertIn("Last change", output)
        self.assertIn("42s ago", output)

    def test_terminal_workers_table(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("W1", output)
        self.assertIn("W2", output)
        self.assertIn("Scope", output)
        self.assertIn("State", output)

    def test_terminal_plan_section(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("Slice", output)
        self.assertIn("Progress", output)
        self.assertIn("Open findings", output)

    def test_terminal_quality_multi_column(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("Docs", output)
        self.assertIn("Shape", output)
        self.assertIn("Clippy", output)
        self.assertIn("Failing", output)
        self.assertIn("common_io.py", output)

    def test_terminal_publication_target_match(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("Target match", output)
        self.assertIn("branch", output)
        self.assertIn("head", output)

    def test_terminal_coordination_compact(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("Packets", output)
        self.assertIn("Instruction rev", output)
        self.assertIn("Reviewer", output)
        self.assertIn("Implementer", output)

    def test_terminal_flow_pipeline(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("Review", output)
        self.assertIn("Implement", output)
        self.assertIn("Verify", output)
        self.assertIn("Checkpoint", output)
        self.assertIn("Push", output)

    def test_terminal_empty_workers(self) -> None:
        snapshot = _full_snapshot()
        snapshot["workers"] = []
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("WORKERS", output)
        self.assertIn("no workers registered", output)


class TestDashboardMarkdownOutput(unittest.TestCase):
    """Verify markdown output covers all new sections."""

    def test_markdown_has_all_sections(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)

        self.assertIn("# Governance Dashboard", output)
        self.assertIn("## Now", output)
        self.assertIn("## Workers", output)
        self.assertIn("## Plan", output)
        self.assertIn("## Publication", output)
        self.assertIn("## Quality", output)
        self.assertIn("## Coordination", output)
        self.assertIn("## Flow", output)


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
            # All sections present
            required = {"repo", "now", "review", "workers", "plan", "publication", "quality", "coordination", "flow"}
            self.assertTrue(required.issubset(snapshot.keys()))

            # Both renderers work on degraded snapshot
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


class TestAgeHelpers(unittest.TestCase):
    """Verify age computation and formatting helpers."""

    def test_format_age_seconds(self) -> None:
        self.assertEqual(dashboard._format_age(42), "42s ago")

    def test_format_age_minutes(self) -> None:
        self.assertEqual(dashboard._format_age(720), "12m ago")

    def test_format_age_hours(self) -> None:
        self.assertEqual(dashboard._format_age(7200), "2h ago")

    def test_format_age_none(self) -> None:
        self.assertEqual(dashboard._format_age(None), "--")

    def test_age_seconds_invalid(self) -> None:
        self.assertIsNone(dashboard._age_seconds("not-a-date"))

    def test_age_seconds_empty(self) -> None:
        self.assertIsNone(dashboard._age_seconds(""))


class TestTopBlockerDerivation(unittest.TestCase):
    """Verify top blocker is derived from quality failures and findings."""

    def test_blocker_from_quality_failing(self) -> None:
        quality = {"failing": ["dev/scripts/devctl/common_io.py"]}
        result = dashboard._derive_top_blocker(quality, {}, {})
        self.assertIn("common_io.py", result)

    def test_blocker_from_findings(self) -> None:
        quality = {"failing": []}
        session = {"open_findings": "- F1: stale docs gate\n- F2: shape debt"}
        result = dashboard._derive_top_blocker(quality, session, {})
        self.assertIn("stale docs gate", result)

    def test_blocker_none_when_clean(self) -> None:
        result = dashboard._derive_top_blocker({"failing": []}, {}, {})
        self.assertEqual(result, "none")


if __name__ == "__main__":
    unittest.main()
