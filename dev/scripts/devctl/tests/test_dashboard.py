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
        "fetch_step": {"duration_s": 0.59},
        "preflight_step": {"returncode": 1, "duration_s": 23.87, "failure_output": "dev/scripts/devctl/common_io.py exceeded limit"},
        "push_step": None,
        "push_stages": {"post_push_green": False, "published_remote": False, "validation_ready": False},
    }


def _minimal_governance_review() -> dict:
    return {
        "stats": {
            "total_findings": 121,
            "fixed_count": 68,
            "cleanup_rate_pct": 56.2,
            "open_finding_count": 39,
        }
    }


def _minimal_probe_summary() -> dict:
    return {
        "summary": {
            "probe_count": 25,
            "files_scanned": 16,
            "risk_hints": 7,
            "hints_by_severity": {"high": 5, "medium": 2},
        }
    }


def _minimal_data_science() -> dict:
    return {
        "watchdog_stats": {"avg_time_to_green_seconds": 16.547},
        "event_stats": {"total_events": 19903, "success_rate_pct": 81.7},
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
            "timers": {"fetch_s": 0.59, "preflight_s": 23.87, "push_s": "n/a"},
        },
        "quality": {
            "docs_gate": "PASS",
            "plan_sync": "PASS",
            "bridge": "PASS",
            "code_shape": "FAIL",
            "instr_sync": "PASS",
            "clippy": "n/a",
            "failing": ["dev/scripts/devctl/common_io.py"],
            "probes": {
                "risk_hints": 7, "high": 5, "medium": 2,
                "probes_enabled": 25, "files_scanned": 16,
            },
        },
        "audit": {
            "total_findings": 121, "fixed_count": 68,
            "cleanup_rate_pct": 56.2, "open_finding_count": 39,
        },
        "analytics": {
            "avg_time_to_green_s": 16.547, "total_events": 19903,
            "command_success_rate_pct": 81.7,
        },
        "coordination": {
            "pending_packets": 0,
            "instruction_rev": "f7f80b28c5fe",
            "reviewer_age": "18s ago",
            "implementer_state": "current",
            "pending_findings": "2 findings",
            "next_action": "run_devctl_push",
        },
        "health": {
            "publisher": {
                "running": False, "pid": 85205,
                "last_heartbeat": "2026-04-04T01:10:00Z",
                "last_heartbeat_age": "2h ago", "snapshots": 54,
            },
            "supervisor": {
                "running": False, "pid": 19237,
                "last_heartbeat": "2026-04-04T01:10:00Z",
                "last_heartbeat_age": "2h ago", "snapshots": 46,
            },
            "attention_status": "inactive",
            "attention_summary": "loop in inactive mode",
            "active_daemons": 0,
        },
        "flow": {
            "review": "pass",
            "implement": "active",
            "verify": "unknown",
            "checkpoint": "pass",
            "push": "blocked",
        },
        "timeline": [
            {"time": "02:05:46", "command": "push", "result": "FAIL", "duration": "71.1s"},
            {"time": "02:03:12", "command": "startup-context", "result": "PASS", "duration": "14.9s"},
            {"time": "02:01:45", "command": "docs-check", "result": "PASS", "duration": "3.3s"},
        ],
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

            required = {
                "repo", "now", "health", "review", "workers", "plan",
                "publication", "quality", "audit", "analytics",
                "coordination", "flow", "timeline",
            }
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
        self.assertIn("## Audit", output)
        self.assertIn("## Analytics", output)
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
            # All sections present (including enrichments)
            required = {
                "repo", "now", "health", "review", "workers", "plan",
                "publication", "quality", "audit", "analytics",
                "coordination", "flow", "timeline",
            }
            self.assertTrue(required.issubset(snapshot.keys()))

            # New enrichment sections degrade to n/a when artifacts missing
            self.assertEqual(snapshot["audit"]["total_findings"], "n/a")
            self.assertEqual(snapshot["analytics"]["total_events"], "n/a")
            self.assertEqual(snapshot["quality"]["probes"]["probes_enabled"], "n/a")
            timers = snapshot["publication"]["timers"]
            self.assertEqual(timers["fetch_s"], "n/a")

            # Health degrades gracefully
            self.assertFalse(snapshot["health"]["publisher"]["running"])
            self.assertEqual(snapshot["health"]["active_daemons"], 0)
            self.assertEqual(snapshot["health"]["attention_status"], "n/a")
            # Timeline is empty when no events file exists
            self.assertEqual(snapshot["timeline"], [])

            # Both renderers work on degraded snapshot
            terminal = dashboard_render.render_terminal(snapshot)
            self.assertIn("GOVERNANCE DASHBOARD", terminal)
            md = dashboard_render.render_markdown(snapshot)
            self.assertIn("# Governance Dashboard", md)
            raw = dashboard_render.render_json(snapshot)
            parsed = json.loads(raw)
            self.assertIn("repo", parsed)


class TestDashboardEnrichments(unittest.TestCase):
    """Verify new enrichment sections: timers, audit, probes, analytics."""

    def test_snapshot_has_publication_timers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test", "head": "deadbee", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            timers = snapshot["publication"]["timers"]
            self.assertEqual(timers["fetch_s"], 0.59)
            self.assertEqual(timers["preflight_s"], 23.87)
            self.assertEqual(timers["push_s"], "n/a")

    def test_snapshot_has_audit_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/governance/latest/review_summary.json", _minimal_governance_review())
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            audit = snapshot["audit"]
            self.assertEqual(audit["total_findings"], 121)
            self.assertEqual(audit["fixed_count"], 68)
            self.assertEqual(audit["cleanup_rate_pct"], 56.2)
            self.assertEqual(audit["open_finding_count"], 39)

    def test_snapshot_has_probes_in_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/probes/latest/summary.json", _minimal_probe_summary())
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            probes = snapshot["quality"]["probes"]
            self.assertEqual(probes["risk_hints"], 7)
            self.assertEqual(probes["high"], 5)
            self.assertEqual(probes["medium"], 2)
            self.assertEqual(probes["probes_enabled"], 25)
            self.assertEqual(probes["files_scanned"], 16)

    def test_snapshot_has_analytics_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/data_science/latest/summary.json", _minimal_data_science())
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            analytics = snapshot["analytics"]
            self.assertEqual(analytics["avg_time_to_green_s"], 16.547)
            self.assertEqual(analytics["total_events"], 19903)
            self.assertEqual(analytics["command_success_rate_pct"], 81.7)

    def test_terminal_renders_audit_line(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("AUDIT", output)
        self.assertIn("Findings 121", output)
        self.assertIn("Fixed 68", output)
        self.assertIn("56.2%", output)
        self.assertIn("Open 39", output)

    def test_terminal_renders_analytics_line(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("ANALYTICS", output)
        self.assertIn("Events 19903", output)
        self.assertIn("81.7%", output)
        self.assertIn("16.5s", output)

    def test_terminal_renders_probe_line(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("Probes 25", output)
        self.assertIn("5 high", output)
        self.assertIn("2 medium", output)

    def test_terminal_renders_publication_timers(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("Preflight 23.9s", output)
        self.assertIn("Push pending", output)
        self.assertIn("Fetch 0.6s", output)

    def test_enrichments_missing_renders_without_crash(self) -> None:
        """Snapshot with n/a enrichments still renders cleanly."""
        snapshot = _full_snapshot()
        snapshot["audit"] = {"total_findings": "n/a", "fixed_count": "n/a", "cleanup_rate_pct": "n/a", "open_finding_count": "n/a"}
        snapshot["analytics"] = {"avg_time_to_green_s": "n/a", "total_events": "n/a", "command_success_rate_pct": "n/a"}
        snapshot["quality"]["probes"] = {"risk_hints": "n/a", "high": "n/a", "medium": "n/a", "probes_enabled": "n/a", "files_scanned": "n/a"}
        snapshot["publication"]["timers"] = {"fetch_s": "n/a", "preflight_s": "n/a", "push_s": "n/a"}

        # Should not raise
        terminal = dashboard_render.render_terminal(snapshot)
        self.assertIn("GOVERNANCE DASHBOARD", terminal)
        # Audit and analytics sections should be skipped when n/a
        self.assertNotIn("AUDIT", terminal)
        self.assertNotIn("ANALYTICS", terminal)

        md = dashboard_render.render_markdown(snapshot)
        self.assertIn("# Governance Dashboard", md)


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


class TestHealthSection(unittest.TestCase):
    """Verify health section building from heartbeat files and attention state."""

    def test_health_from_heartbeat_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/publisher_heartbeat.json",
                {
                    "pid": 85205,
                    "started_at_utc": "2026-04-04T02:43:30Z",
                    "last_heartbeat_utc": "2026-04-04T03:11:28Z",
                    "snapshots_emitted": 54,
                    "stop_reason": "",
                    "stopped_at_utc": "",
                },
            )
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/reviewer_supervisor_heartbeat.json",
                {
                    "pid": 19237,
                    "started_at_utc": "2026-04-04T02:48:41Z",
                    "last_heartbeat_utc": "2026-04-04T03:09:46Z",
                    "snapshots_emitted": 46,
                    "stop_reason": "graceful",
                    "stopped_at_utc": "2026-04-04T03:10:00Z",
                },
            )
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/full.json",
                {"attention": {"status": "reviewer_overdue", "summary": "Codex reviewer is overdue"}},
            )

            health = dashboard._build_health_section(root, None)
            self.assertTrue(health["publisher"]["running"])
            self.assertEqual(health["publisher"]["pid"], 85205)
            self.assertEqual(health["publisher"]["snapshots"], 54)
            self.assertFalse(health["supervisor"]["running"])
            self.assertEqual(health["supervisor"]["pid"], 19237)
            self.assertEqual(health["attention_status"], "reviewer_overdue")
            self.assertIn("overdue", health["attention_summary"])
            self.assertEqual(health["active_daemons"], 1)

    def test_health_graceful_with_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            health = dashboard._build_health_section(root, None)
            self.assertFalse(health["publisher"]["running"])
            self.assertFalse(health["supervisor"]["running"])
            self.assertEqual(health["attention_status"], "n/a")
            self.assertEqual(health["active_daemons"], 0)

    def test_read_heartbeat_running_when_not_stopped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hb_path = root / "hb.json"
            hb_path.write_text(json.dumps({
                "pid": 123, "last_heartbeat_utc": "2026-04-04T03:00:00Z",
                "snapshots_emitted": 10, "stopped_at_utc": "",
            }))
            result = dashboard._read_heartbeat(hb_path)
            self.assertTrue(result["running"])
            self.assertEqual(result["pid"], 123)
            self.assertEqual(result["snapshots"], 10)
            self.assertIn("ago", result["last_heartbeat_age"])

    def test_read_heartbeat_stopped_when_stopped_at_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hb_path = root / "hb.json"
            hb_path.write_text(json.dumps({
                "pid": 456, "last_heartbeat_utc": "2026-04-04T03:00:00Z",
                "snapshots_emitted": 5, "stopped_at_utc": "2026-04-04T03:01:00Z",
            }))
            result = dashboard._read_heartbeat(hb_path)
            self.assertFalse(result["running"])

    def test_health_terminal_render(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("HEALTH", output)
        self.assertIn("Publisher", output)
        self.assertIn("Supervisor", output)
        self.assertIn("STOPPED", output)
        self.assertIn("85205", output)
        self.assertIn("54 snapshots", output)
        self.assertIn("Attention", output)
        self.assertIn("inactive", output)

    def test_health_markdown_render(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("## Health", output)
        self.assertIn("Publisher", output)
        self.assertIn("Supervisor", output)
        self.assertIn("STOPPED", output)
        self.assertIn("Attention", output)


class TestTimelineSection(unittest.TestCase):
    """Verify timeline parsing from events JSONL and rendering."""

    def test_timeline_from_events_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events_path = root / "dev" / "reports" / "audits" / "devctl_events.jsonl"
            events_path.parent.mkdir(parents=True, exist_ok=True)
            lines = []
            for i in range(15):
                entry = {
                    "timestamp": f"2026-04-04T02:{i:02d}:00Z",
                    "command": f"cmd-{i}",
                    "success": i % 2 == 0,
                    "duration_seconds": 1.5 + i,
                }
                lines.append(json.dumps(entry))
            events_path.write_text("\n".join(lines), encoding="utf-8")

            timeline = dashboard._build_timeline_section(root)
            self.assertEqual(len(timeline), 10)
            self.assertEqual(timeline[0]["command"], "cmd-5")
            self.assertEqual(timeline[-1]["command"], "cmd-14")
            self.assertEqual(timeline[0]["result"], "FAIL")
            self.assertEqual(timeline[1]["result"], "PASS")

    def test_timeline_graceful_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            timeline = dashboard._build_timeline_section(root)
            self.assertEqual(timeline, [])

    def test_timeline_handles_malformed_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events_path = root / "dev" / "reports" / "audits" / "devctl_events.jsonl"
            events_path.parent.mkdir(parents=True, exist_ok=True)
            content = (
                'not json\n'
                '{"timestamp":"2026-04-04T02:05:46Z",'
                '"command":"push","success":false,'
                '"duration_seconds":71.1}\n'
            )
            events_path.write_text(content, encoding="utf-8")

            timeline = dashboard._build_timeline_section(root)
            self.assertEqual(len(timeline), 1)
            self.assertEqual(timeline[0]["command"], "push")
            self.assertEqual(timeline[0]["result"], "FAIL")
            self.assertEqual(timeline[0]["duration"], "71.1s")

    def test_tail_lines_reads_only_last_n(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fpath = root / "test.jsonl"
            fpath.write_text(
                "\n".join(f"line-{i}" for i in range(100)),
                encoding="utf-8",
            )
            result = dashboard._tail_lines(fpath, count=5)
            self.assertEqual(len(result), 5)
            self.assertEqual(result[0], "line-95")
            self.assertEqual(result[-1], "line-99")

    def test_extract_time_from_iso(self) -> None:
        self.assertEqual(
            dashboard._extract_time_from_iso("2026-04-04T02:05:46Z"),
            "02:05:46",
        )
        self.assertEqual(dashboard._extract_time_from_iso(""), "--:--:--")
        self.assertEqual(dashboard._extract_time_from_iso("bad"), "--:--:--")

    def test_timeline_terminal_render(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("TIMELINE", output)
        self.assertIn("last 3", output)
        self.assertIn("push", output)
        self.assertIn("startup-context", output)
        self.assertIn("FAIL", output)
        self.assertIn("PASS", output)
        self.assertIn("71.1s", output)

    def test_timeline_markdown_render(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("## Timeline", output)
        self.assertIn("push", output)
        self.assertIn("FAIL", output)
        self.assertIn("71.1s", output)

    def test_timeline_empty_render_skips_section(self) -> None:
        snapshot = _full_snapshot()
        snapshot["timeline"] = []
        output = dashboard_render.render_terminal(snapshot)
        self.assertNotIn("TIMELINE", output)


if __name__ == "__main__":
    unittest.main()
