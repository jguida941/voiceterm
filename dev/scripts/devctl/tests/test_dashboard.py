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
        "no_color": False,
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


def _rich_bridge_text() -> str:
    """Bridge text with all reviewer-owned sections for codex_activity tests."""
    return (
        "# Review Bridge\n\n"
        "- Last Codex poll: `2026-04-04T01:52:56Z`\n"
        "- Reviewer mode: `active_dual_agent`\n\n"
        "## Current Verdict\n\n"
        "- Launch ACK bypass found: typed launch truth substitutes for fresh poll\n"
        "- Change Summary: the optimization weakens the live-launch ACK contract\n\n"
        "## Open Findings\n\n"
        "- F1: handoff.py accepts launch success with stale poll\n"
        "- F2: test coverage missing for fail-closed path\n\n"
        "## Current Instruction For Claude\n\n"
        "- Tighten wait_for_codex_poll_refresh so typed launch truth requires fresh turn\n"
        "- Add focused regression test for fail-closed behavior\n\n"
        "## Last Reviewed Scope\n\n"
        "- dev/scripts/devctl/commands/review_channel/bridge_launch_control.py\n"
        "- dev/scripts/devctl/review_channel/handoff.py\n"
        "- dev/scripts/devctl/review_channel/launch_truth.py\n"
        "- dev/scripts/devctl/review_channel/session_probe.py\n"
        "- dev/scripts/devctl/review_channel/peer_liveness.py\n"
        "- dev/scripts/devctl/tests/review_channel/test_review_channel.py\n"
        "- dev/active/review_channel.md\n"
        "- dev/active/MASTER_PLAN.md\n"
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
            "session": "45m",
            "ahead": 5,
            "behind": 0,
            "dirty_files": 0,
            "recent_commits": [
                {"sha": "abc1234", "message": "Bridge: launch ACK fix complete"},
                {"sha": "bff99a8", "message": "Tighten launch ACK: require fresh Codex poll"},
                {"sha": "0a83eaf", "message": "Bridge: ack instruction 4885340b6f96"},
            ],
        },
        "now": {
            "owner": "Reviewer",
            "owner_provider": "codex",
            "next_action": "review worker results and checkpoint",
            "top_blocker": "code-shape debt in common_io.py",
            "last_change_age_s": 42,
            "last_change_label": "42s ago",
            "instruction_text": "Tighten wait_for_codex_poll_refresh so typed launch truth requires fresh turn",
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
            "findings_detail": [
                {"id": "F1", "summary": "handoff.py accepts launch success with stale poll"},
                {"id": "F2", "summary": "test coverage missing for fail-closed path"},
            ],
            "pending": 0,
        },
        "findings": [
            {"id": "F1", "summary": "handoff.py accepts launch success with stale poll"},
            {"id": "F2", "summary": "test coverage missing for fail-closed path"},
        ],
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
            "session_age": "45m",
            "session_started": "03:05:00",
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
            "codex_conductor": {"pid": 12345, "alive": False},
            "claude_conductor": {"pid": 67890, "alive": True},
            "attention_status": "inactive",
            "attention_summary": "loop in inactive mode",
            "active_daemons": 0,
        },
        "codex_activity": {
            "last_poll_age": "12m ago",
            "last_verdict": "Launch ACK bypass found: typed launch truth substitutes for fresh poll...",
            "reviewed_files": 8,
            "instruction_summary": "Tighten wait_for_codex_poll_refresh so typed launch truth requires fres...",
            "findings_posted": 2,
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
                "coordination", "codex_activity", "flow", "timeline",
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
        self.assertIn("REVIEWER (Codex)", output)
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
        self.assertIn("## Reviewer (Codex)", output)
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
                "coordination", "codex_activity", "flow", "timeline",
            }
            self.assertTrue(required.issubset(snapshot.keys()))

            # Codex activity degrades gracefully when bridge has no sections
            activity = snapshot["codex_activity"]
            self.assertEqual(activity["last_verdict"], "n/a")
            self.assertEqual(activity["reviewed_files"], 0)
            self.assertEqual(activity["findings_posted"], 0)
            self.assertEqual(activity["instruction_summary"], "n/a")

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


class TestCodexActivitySection(unittest.TestCase):
    """Verify codex_activity section parsing and rendering."""

    def test_codex_activity_from_rich_bridge(self) -> None:
        """Rich bridge text produces populated codex_activity fields."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_rich_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            activity = snapshot["codex_activity"]
            self.assertIn("last_poll_age", activity)
            self.assertEqual(activity["reviewed_files"], 8)
            self.assertEqual(activity["findings_posted"], 2)
            self.assertIn("Launch ACK bypass", activity["last_verdict"])
            self.assertIn("Tighten wait_for_codex_poll_refresh", activity["instruction_summary"])

    def test_codex_activity_degrades_with_minimal_bridge(self) -> None:
        """Minimal bridge with no reviewer sections degrades to defaults."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            activity = snapshot["codex_activity"]
            self.assertEqual(activity["last_verdict"], "n/a")
            self.assertEqual(activity["reviewed_files"], 0)
            self.assertEqual(activity["findings_posted"], 0)

    def test_codex_activity_degrades_with_no_bridge(self) -> None:
        """No bridge.md at all still produces valid codex_activity."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            activity = snapshot["codex_activity"]
            self.assertEqual(activity["last_verdict"], "n/a")
            self.assertEqual(activity["reviewed_files"], 0)
            self.assertEqual(activity["findings_posted"], 0)
            self.assertEqual(activity["last_poll_age"], "--")

    def test_terminal_renders_reviewer_section(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("REVIEWER (Codex)", output)
        self.assertIn("Last poll", output)
        self.assertIn("12m ago", output)
        self.assertIn("Verdict", output)
        self.assertIn("Launch ACK bypass", output)
        self.assertIn("8 files", output)
        self.assertIn("Instruction", output)
        self.assertIn("2 posted", output)

    def test_markdown_renders_reviewer_section(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("## Reviewer (Codex)", output)
        self.assertIn("Last poll", output)
        self.assertIn("12m ago", output)
        self.assertIn("Launch ACK bypass", output)
        self.assertIn("8 files", output)
        self.assertIn("2 posted", output)

    def test_terminal_reviewer_empty_activity(self) -> None:
        """When codex_activity is empty dict, section is skipped cleanly."""
        snapshot = _full_snapshot()
        snapshot["codex_activity"] = {}
        output = dashboard_render.render_terminal(snapshot)
        self.assertNotIn("REVIEWER (Codex)", output)


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
            # Conductors degrade to pid=None, alive=False
            self.assertIsNone(health["codex_conductor"]["pid"])
            self.assertFalse(health["codex_conductor"]["alive"])
            self.assertIsNone(health["claude_conductor"]["pid"])
            self.assertFalse(health["claude_conductor"]["alive"])

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

    def test_health_terminal_renders_conductor_rows(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("Codex", output)
        self.assertIn("Claude", output)
        self.assertIn("DEAD", output)
        self.assertIn("12345", output)
        self.assertIn("process not found", output)
        self.assertIn("67890", output)

    def test_health_markdown_renders_conductor_rows(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("Codex", output)
        self.assertIn("DEAD", output)
        self.assertIn("12345", output)
        self.assertIn("process not found", output)
        self.assertIn("Claude", output)
        self.assertIn("67890", output)

    def test_conductor_no_session_renders_gracefully(self) -> None:
        snapshot = _full_snapshot()
        snapshot["health"]["codex_conductor"] = {"pid": None, "alive": False}
        snapshot["health"]["claude_conductor"] = {"pid": None, "alive": False}
        terminal = dashboard_render.render_terminal(snapshot)
        self.assertIn("NO SESSION", terminal)
        md = dashboard_render.render_markdown(snapshot)
        self.assertIn("NO SESSION", md)


class TestConductorLiveness(unittest.TestCase):
    """Verify conductor session reading and PID liveness probing."""

    def test_conductor_with_session_pid_alive(self) -> None:
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            my_pid = os.getpid()
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/sessions/codex-conductor.json",
                {"session_pid": my_pid, "provider": "codex"},
            )
            result = dashboard._read_conductor_liveness(
                root / "dev/reports/review_channel/latest/sessions/codex-conductor.json"
            )
            self.assertEqual(result["pid"], my_pid)
            self.assertTrue(result["alive"])

    def test_conductor_with_dead_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/sessions/claude-conductor.json",
                {"session_pid": 999999999, "provider": "claude"},
            )
            result = dashboard._read_conductor_liveness(
                root / "dev/reports/review_channel/latest/sessions/claude-conductor.json"
            )
            self.assertEqual(result["pid"], 999999999)
            self.assertFalse(result["alive"])

    def test_conductor_missing_session_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/sessions/codex-conductor.json",
                {"provider": "codex"},
            )
            result = dashboard._read_conductor_liveness(
                root / "dev/reports/review_channel/latest/sessions/codex-conductor.json"
            )
            self.assertIsNone(result["pid"])
            self.assertFalse(result["alive"])

    def test_conductor_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = dashboard._read_conductor_liveness(
                root / "nonexistent.json"
            )
            self.assertIsNone(result["pid"])
            self.assertFalse(result["alive"])

    def test_health_section_includes_conductors(self) -> None:
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            my_pid = os.getpid()
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/sessions/codex-conductor.json",
                {"session_pid": my_pid, "provider": "codex"},
            )
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/sessions/claude-conductor.json",
                {"session_pid": 999999999, "provider": "claude"},
            )
            health = dashboard._build_health_section(root, None)
            self.assertEqual(health["codex_conductor"]["pid"], my_pid)
            self.assertTrue(health["codex_conductor"]["alive"])
            self.assertEqual(health["claude_conductor"]["pid"], 999999999)
            self.assertFalse(health["claude_conductor"]["alive"])

    def test_pid_is_alive_current_process(self) -> None:
        import os
        self.assertTrue(dashboard._pid_is_alive(os.getpid()))

    def test_pid_is_alive_nonexistent(self) -> None:
        self.assertFalse(dashboard._pid_is_alive(999999999))


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


class TestGitStateDetails(unittest.TestCase):
    """Verify ahead/behind, dirty file count, and recent commits in repo section."""

    def test_parse_ahead_behind_ahead_only(self) -> None:
        ahead, behind = dashboard._parse_ahead_behind(
            "main...origin/main [ahead 5]"
        )
        self.assertEqual(ahead, 5)
        self.assertEqual(behind, 0)

    def test_parse_ahead_behind_both(self) -> None:
        ahead, behind = dashboard._parse_ahead_behind(
            "main...origin/main [ahead 3, behind 2]"
        )
        self.assertEqual(ahead, 3)
        self.assertEqual(behind, 2)

    def test_parse_ahead_behind_behind_only(self) -> None:
        ahead, behind = dashboard._parse_ahead_behind(
            "main...origin/main [behind 1]"
        )
        self.assertEqual(ahead, 0)
        self.assertEqual(behind, 1)

    def test_parse_ahead_behind_none(self) -> None:
        ahead, behind = dashboard._parse_ahead_behind(
            "main...origin/main"
        )
        self.assertEqual(ahead, 0)
        self.assertEqual(behind, 0)

    def test_snapshot_repo_has_git_state_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            git_data = {
                "branch": "feature/test", "head": "abc1234", "dirty": "DIRTY",
                "ahead": 5, "behind": 0, "dirty_files": 12,
                "recent_commits": [
                    {"sha": "abc1234", "message": "First commit"},
                    {"sha": "def5678", "message": "Second commit"},
                ],
            }
            with patch.object(dashboard, "_git_short", return_value=git_data), \
                 patch.object(dashboard, "_repo_name", return_value="test-repo"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            repo = snapshot["repo"]
            self.assertEqual(repo["ahead"], 5)
            self.assertEqual(repo["behind"], 0)
            self.assertEqual(repo["dirty_files"], 12)
            self.assertEqual(len(repo["recent_commits"]), 2)
            self.assertEqual(repo["recent_commits"][0]["sha"], "abc1234")

    def test_terminal_renders_ahead_and_dirty_count(self) -> None:
        snapshot = _full_snapshot()
        snapshot["repo"]["ahead"] = 5
        snapshot["repo"]["dirty_files"] = 12
        snapshot["repo"]["worktree"] = "DIRTY"
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("Ahead: 5", output)
        self.assertIn("Dirty: 12 files", output)
        self.assertIn("Worktree:", output)

    def test_terminal_renders_ahead_behind(self) -> None:
        snapshot = _full_snapshot()
        snapshot["repo"]["ahead"] = 3
        snapshot["repo"]["behind"] = 2
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("Ahead: 3", output)
        self.assertIn("Behind: 2", output)

    def test_terminal_renders_recent_commits(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("RECENT COMMITS", output)
        self.assertIn("abc1234", output)
        self.assertIn("Bridge: launch ACK fix complete", output)
        self.assertIn("bff99a8", output)
        self.assertIn("0a83eaf", output)

    def test_terminal_no_recent_commits_when_empty(self) -> None:
        snapshot = _full_snapshot()
        snapshot["repo"]["recent_commits"] = []
        output = dashboard_render.render_terminal(snapshot)

        self.assertNotIn("RECENT COMMITS", output)

    def test_terminal_singular_dirty_file(self) -> None:
        snapshot = _full_snapshot()
        snapshot["repo"]["dirty_files"] = 1
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("Dirty: 1 file", output)
        # Should not say "1 files"
        self.assertNotIn("1 files", output)

    def test_markdown_renders_ahead_and_dirty(self) -> None:
        snapshot = _full_snapshot()
        snapshot["repo"]["ahead"] = 5
        snapshot["repo"]["dirty_files"] = 12
        output = dashboard_render.render_markdown(snapshot)

        self.assertIn("| Ahead | 5 |", output)
        self.assertIn("| Dirty | 12 files |", output)

    def test_markdown_renders_recent_commits(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)

        self.assertIn("### Recent Commits", output)
        self.assertIn("`abc1234`", output)
        self.assertIn("Bridge: launch ACK fix complete", output)

    def test_markdown_no_recent_commits_when_empty(self) -> None:
        snapshot = _full_snapshot()
        snapshot["repo"]["recent_commits"] = []
        output = dashboard_render.render_markdown(snapshot)

        self.assertNotIn("### Recent Commits", output)


class TestNoColorFlag(unittest.TestCase):
    """Verify --no-color flag and NO_COLOR env var strip ANSI codes."""

    def test_strip_ansi_removes_escape_sequences(self) -> None:
        raw = "\033[1mBOLD\033[0m \033[31mRED\033[0m plain"
        result = dashboard_render.strip_ansi(raw)
        self.assertEqual(result, "BOLD RED plain")
        self.assertNotIn("\033[", result)

    def test_strip_ansi_preserves_plain_text(self) -> None:
        plain = "no escape codes here"
        self.assertEqual(dashboard_render.strip_ansi(plain), plain)

    def test_render_terminal_no_color_flag(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot, no_color=True)
        self.assertNotIn("\033[", output)
        self.assertIn("GOVERNANCE DASHBOARD", output)
        self.assertIn("NOW", output)
        self.assertIn("WORKERS", output)

    def test_render_terminal_default_has_ansi(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("\033[", output)

    def test_no_color_env_var(self) -> None:
        snapshot = _full_snapshot()
        with patch.dict("os.environ", {"NO_COLOR": "1"}):
            output = dashboard_render.render_terminal(snapshot)
        self.assertNotIn("\033[", output)
        self.assertIn("GOVERNANCE DASHBOARD", output)

    def test_no_color_env_var_empty_string_does_not_strip(self) -> None:
        snapshot = _full_snapshot()
        with patch.dict("os.environ", {"NO_COLOR": ""}, clear=False):
            output = dashboard_render.render_terminal(snapshot)
        self.assertIn("\033[", output)

    def test_cli_parser_has_no_color_flag(self) -> None:
        from dev.scripts.devctl.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["dashboard", "--no-color"])
        self.assertTrue(args.no_color)

    def test_cli_parser_no_color_default_false(self) -> None:
        from dev.scripts.devctl.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["dashboard"])
        self.assertFalse(args.no_color)

    def test_run_passes_no_color_to_renderer(self) -> None:
        with patch.object(dashboard, "build_snapshot") as mock_build:
            mock_build.return_value = _full_snapshot()
            args = _make_args(format="terminal", no_color=True)
            with patch("dev.scripts.devctl.commands.dashboard.emit_output") as mock_emit:
                dashboard.run(args)
                output = mock_emit.call_args[0][0]
                self.assertNotIn("\033[", output)
                self.assertIn("GOVERNANCE DASHBOARD", output)



class TestSessionDuration(unittest.TestCase):
    """Verify session/loop duration from publisher heartbeat."""

    def test_format_duration_seconds(self) -> None:
        self.assertEqual(dashboard._format_duration(42), "42s")

    def test_format_duration_minutes(self) -> None:
        self.assertEqual(dashboard._format_duration(2700), "45m")

    def test_format_duration_hours_and_minutes(self) -> None:
        self.assertEqual(dashboard._format_duration(8100), "2h 15m")

    def test_format_duration_exact_hours(self) -> None:
        self.assertEqual(dashboard._format_duration(7200), "2h")

    def test_format_duration_none(self) -> None:
        self.assertEqual(dashboard._format_duration(None), "--")

    def test_session_age_from_heartbeat(self) -> None:
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
                    "stopped_at_utc": "",
                },
            )
            result = dashboard._session_age(root)
            self.assertIsNotNone(result["session_age_s"])
            self.assertNotEqual(result["session_label"], "--")
            self.assertEqual(result["started_time"], "02:43:30")

    def test_session_age_missing_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = dashboard._session_age(root)
            self.assertIsNone(result["session_age_s"])
            self.assertEqual(result["session_label"], "--")
            self.assertEqual(result["started_time"], "")

    def test_snapshot_repo_has_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/publisher_heartbeat.json",
                {
                    "pid": 100,
                    "started_at_utc": "2026-04-04T02:00:00Z",
                    "last_heartbeat_utc": "2026-04-04T02:30:00Z",
                    "snapshots_emitted": 10,
                    "stopped_at_utc": "",
                },
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertIn("session", snapshot["repo"])
            self.assertNotEqual(snapshot["repo"]["session"], "--")

    def test_coordination_has_session_age(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/latest/compact.json", _minimal_compact())
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/publisher_heartbeat.json",
                {
                    "pid": 100,
                    "started_at_utc": "2026-04-04T02:00:00Z",
                    "last_heartbeat_utc": "2026-04-04T02:30:00Z",
                    "snapshots_emitted": 10,
                    "stopped_at_utc": "",
                },
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            coord = snapshot["coordination"]
            self.assertIn("session_age", coord)
            self.assertIn("session_started", coord)
            self.assertNotEqual(coord["session_age"], "--")
            self.assertEqual(coord["session_started"], "02:00:00")

    def test_terminal_renders_session_in_header(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("Session:", output)
        self.assertIn("45m", output)

    def test_terminal_renders_session_in_coordination(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        # Coordination section should show session age with start time
        self.assertIn("Session    45m", output)
        self.assertIn("started 03:05:00 UTC", output)

    def test_markdown_renders_session_in_header(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("| Session | 45m |", output)

    def test_markdown_renders_session_in_coordination(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("**Session age**: 45m", output)
        self.assertIn("started 03:05:00 UTC", output)

    def test_session_degrades_when_no_heartbeat(self) -> None:
        snapshot = _full_snapshot()
        snapshot["repo"]["session"] = "--"
        snapshot["coordination"]["session_age"] = "--"
        snapshot["coordination"]["session_started"] = ""
        terminal = dashboard_render.render_terminal(snapshot)
        self.assertIn("Session:", terminal)
        md = dashboard_render.render_markdown(snapshot)
        self.assertIn("| Session | -- |", md)


class TestParseBridgeFindings(unittest.TestCase):
    """Verify _parse_bridge_findings extracts structured finding detail."""

    def test_parses_findings_from_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = Path(tmp) / "bridge.md"
            bridge.write_text(_rich_bridge_text(), encoding="utf-8")
            findings = dashboard._parse_bridge_findings(bridge)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["id"], "F1")
        self.assertIn("handoff.py", findings[0]["summary"])
        self.assertEqual(findings[1]["id"], "F2")
        self.assertIn("test coverage", findings[1]["summary"])

    def test_returns_empty_when_no_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = Path(tmp) / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")
            findings = dashboard._parse_bridge_findings(bridge)
        self.assertEqual(findings, [])

    def test_returns_empty_when_file_missing(self) -> None:
        findings = dashboard._parse_bridge_findings(Path("/nonexistent/bridge.md"))
        self.assertEqual(findings, [])

    def test_truncates_long_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = Path(tmp) / "bridge.md"
            long_desc = "x" * 120
            bridge.write_text(
                f"# Bridge\n\n## Open Findings\n\n- F1: {long_desc}\n\n## Next\n",
                encoding="utf-8",
            )
            findings = dashboard._parse_bridge_findings(bridge)
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0]["summary"].endswith("..."))
        self.assertLessEqual(len(findings[0]["summary"]), 84)

    def test_auto_numbers_findings_without_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = Path(tmp) / "bridge.md"
            bridge.write_text(
                "# Bridge\n\n## Open Findings\n\n"
                "- first issue here\n- second issue\n\n## Next\n",
                encoding="utf-8",
            )
            findings = dashboard._parse_bridge_findings(bridge)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["id"], "F1")
        self.assertEqual(findings[1]["id"], "F2")


class TestFindingsInSnapshot(unittest.TestCase):
    """Verify findings flow from bridge to snapshot and renderers."""

    def test_snapshot_includes_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/compact.json",
                _minimal_compact(),
            )
            bridge = root / "bridge.md"
            bridge.write_text(_rich_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
                "ahead": 0, "behind": 0, "dirty_files": 0, "recent_commits": [],
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertIn("findings", snapshot)
            self.assertEqual(len(snapshot["findings"]), 2)
            self.assertEqual(snapshot["findings"][0]["id"], "F1")
            self.assertEqual(snapshot["plan"]["open_findings"], 2)
            self.assertEqual(len(snapshot["plan"]["findings_detail"]), 2)

    def test_snapshot_now_has_instruction_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/compact.json",
                _minimal_compact(),
            )
            bridge = root / "bridge.md"
            bridge.write_text(_rich_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
                "ahead": 0, "behind": 0, "dirty_files": 0, "recent_commits": [],
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            now = snapshot["now"]
            self.assertIn("instruction_text", now)
            self.assertIn("Tighten", now["instruction_text"])
            self.assertLessEqual(len(now["instruction_text"]), 104)

    def test_terminal_renders_findings_section(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("FINDINGS", output)
        self.assertIn("F1", output)
        self.assertIn("F2", output)
        self.assertIn("handoff.py", output)
        self.assertIn("test coverage", output)

    def test_terminal_renders_instruction_in_now(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("Instruction", output)
        self.assertIn("Tighten", output)

    def test_markdown_renders_findings_section(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("## Findings", output)
        self.assertIn("**F1**", output)
        self.assertIn("**F2**", output)
        self.assertIn("handoff.py", output)

    def test_markdown_renders_instruction_in_now(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("**Instruction**", output)
        self.assertIn("Tighten", output)

    def test_no_findings_skips_section(self) -> None:
        snapshot = _full_snapshot()
        snapshot["findings"] = []
        output = dashboard_render.render_terminal(snapshot)
        self.assertNotIn("FINDINGS", output)

    def test_snapshot_no_findings_when_bridge_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/latest/compact.json",
                _minimal_compact(),
            )

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
                "ahead": 0, "behind": 0, "dirty_files": 0, "recent_commits": [],
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertEqual(snapshot["findings"], [])
            self.assertEqual(snapshot["plan"]["findings_detail"], [])


if __name__ == "__main__":
    unittest.main()
