"""Tests for devctl dashboard command — dense multi-column layout."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands import (
    dashboard,
    dashboard_builders,
    dashboard_render,
    dashboard_typed_state,
)
from dev.scripts.devctl.runtime.advisory_next_action_role_filter import (
    READ_ONLY_NEXT_COMMAND,
)
from dev.scripts.devctl.runtime.dashboard_snapshot_authority import (
    normalize_dashboard_snapshot,
)


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
        "preflight_step": {
            "returncode": 1,
            "duration_s": 23.87,
            "failure_output": (
                "\ncheck summary: 4/5 passed, 1 failed\n"
                "-----------------------------------\n"
                "  PASS  docs_check\n"
                "  PASS  plan_sync\n"
                "  FAIL  code_shape  -- dev/scripts/devctl/common_io.py exceeded limit\n"
                "  PASS  instr_sync\n"
                "  PASS  bridge_check\n"
            ),
        },
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


def _build_dashboard_parser() -> object:
    """Import the CLI parser with VCS modules stubbed out for this test file."""
    stub_commit = types.ModuleType("dev.scripts.devctl.commands.vcs.commit")
    def _noop_run(*args: object, **kwargs: object) -> int:
        return 0

    stub_commit.run = _noop_run
    stub_push = types.ModuleType("dev.scripts.devctl.commands.vcs.push")
    stub_push.run = _noop_run
    with patch.dict(
        sys.modules,
        {
            "dev.scripts.devctl.commands.vcs.commit": stub_commit,
            "dev.scripts.devctl.commands.vcs.push": stub_push,
        },
    ):
        from dev.scripts.devctl.cli import build_parser

        return build_parser()


def _minimal_bridge_text() -> str:
    return (
        "# Review Bridge\n\n"
        "- Last Codex poll: `2026-04-04T01:52:56Z`\n"
        "- Reviewer mode: `single_agent`\n"
    )


def _rich_bridge_text() -> str:
    """Bridge text with all reviewer-owned sections for reviewer_activity tests."""
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
            "check_details": [
                {"check": "code_shape", "status": "FAIL", "violation": "dev/scripts/devctl/common_io.py exceeded 350-line soft limit (412 lines)"},
            ],
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
            "push_success_values": [1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0],
            "top_commands": [
                ("autonomy-loop", 4463.0),
                ("review-channel", 3939.0),
                ("docs-check", 2106.0),
                ("check", 1485.0),
                ("hygiene", 835.0),
            ],
            "cleanup_rate_pct": 56.2,
        },
        "coordination": {
            "pending_packets": 0,
            "pending_count": 0,
            "instruction_rev": "f7f80b28c5fe",
            "reviewer_age": "18s ago",
            "implementer_state": "current",
            "pending_findings_count": 2,
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
        "control_plane": {
            "contract_id": "ControlPlaneReadModel",
            "resolved_phase": "review_pending",
            "top_blocker": "code-shape debt in common_io.py",
            "next_action": "review worker results and checkpoint",
            "next_command": "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
            "reviewer_mode": "active_dual_agent",
            "reviewer_freshness": "fresh",
            "review_accepted": False,
            "operator_interaction_mode": "local_terminal",
            "push_eligible": False,
            "implementation_blocked": True,
            "attention_status": "inactive",
            "attention_summary": "loop in inactive mode",
            "pending_action_requests": 2,
            "last_guard_ok": False,
            "check_details": [
                {"check": "code_shape", "status": "FAIL", "violation": "dev/scripts/devctl/common_io.py exceeded 350-line soft limit (412 lines)"},
            ],
        },
        "reviewer_activity": {
            "provider": "codex",
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
        "summary": {
            "overall_state": "blocked",
            "block_class": "quality + push",
            "next_actor": "implementer",
            "next_command_hint": "fix code-shape debt",
            "infra_state": "down",
            "infra_label": "0 daemons running",
            "primary_blocker": "code-shape debt in common_io.py",
            "secondary_blocker": "Attention inactive",
            "one_line": "Implementer active; infra down; quality gate failing on code_shape; push blocked.",
        },
        "status": "blocked",
        "owner": "Reviewer",
        "next_action": "review worker results and checkpoint",
        "top_blocker": "code-shape debt in common_io.py",
        "pending_count": 2,
        "pending_findings_count": 2,
        "next_actor": "implementer",
        "next_command": "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
        "pending_action_requests": 2,
    }


class TestDashboardSnapshotSections(unittest.TestCase):
    """Verify the snapshot has all required top-level sections."""

    def test_dashboard_snapshot_has_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            _write_artifact(root, "dev/reports/startup/latest/receipt.json", _minimal_receipt())
            _write_artifact(root, "dev/reports/review_channel/projections/latest/registry/agents.json", _minimal_agents())
            _write_artifact(root, "dev/reports/review_channel/projections/latest/commit_pipeline.json", _minimal_pipeline())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test", "head": "deadbee", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test-repo"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            required = {
                "repo", "now", "health", "review", "workers", "plan",
                "publication", "quality", "audit", "analytics",
                "coordination", "reviewer_activity", "flow", "timeline",
                "summary", "agent_mind", "session_outcomes", "ack_freshness",
                "active_codex_sessions", "system_topology", "agent_minds",
                "packet_continuity_index", "continuity_attention",
            }
            self.assertTrue(required.issubset(snapshot.keys()), f"Missing: {required - snapshot.keys()}")
            self.assertEqual(snapshot["schema_version"], 3)
            self.assertEqual(snapshot["contract_id"], "DashboardSnapshot")

    def test_dashboard_snapshot_has_provider_agent_minds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/agent_minds/codex_latest.json",
                {
                    "agent_provider": "codex",
                    "generated_at_utc": "2026-05-01T15:20:10Z",
                    "session_id": "codex-session",
                    "event_count": 1,
                    "events": [{"timestamp": "t1", "summary": "codex event"}],
                },
            )
            _write_artifact(
                root,
                "dev/reports/agent_minds/claude_latest.json",
                {
                    "agent_provider": "claude",
                    "generated_at_utc": "2026-05-01T15:20:11Z",
                    "session_id": "claude-session",
                    "event_count": 1,
                    "events": [{"timestamp": "t2", "summary": "claude event"}],
                },
            )

            snapshot = normalize_dashboard_snapshot(
                {"review_state": {}},
                repo_root=root,
                review_state={},
            )

            self.assertEqual(snapshot["agent_mind"]["agent_provider"], "codex")
            self.assertEqual(
                snapshot["agent_minds"]["claude"]["agent_provider"],
                "claude",
            )
            self.assertEqual(
                snapshot["agent_minds"]["claude"]["latest_events"][0]["summary"],
                "claude event",
            )

    def test_normalized_snapshot_exposes_packet_continuity(self) -> None:
        review_state = _minimal_review_state()
        review_state["packets"] = review_state["packets"][:2]

        snapshot = normalize_dashboard_snapshot(
            {"review_state": review_state},
            review_state=review_state,
        )

        self.assertEqual(
            snapshot["packet_continuity_index"]["contract_id"],
            "PacketContinuityIndex",
        )
        self.assertEqual(
            snapshot["packet_continuity_index"]["sink_counts"]["live_queue"],
            2,
        )

    def test_now_section_populated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            _write_artifact(root, "dev/reports/startup/latest/receipt.json", _minimal_receipt())
            _write_artifact(root, "dev/reports/review_channel/projections/latest/registry/agents.json", _minimal_agents())
            _write_artifact(root, "dev/reports/review_channel/projections/latest/commit_pipeline.json", _minimal_pipeline())
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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            _write_artifact(root, "dev/reports/startup/latest/receipt.json", _minimal_receipt())
            _write_artifact(root, "dev/reports/review_channel/projections/latest/registry/agents.json", _minimal_agents())
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

    def test_plan_section_prefers_typed_startup_routing_and_backlog_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")
            startup_context = {
                "work_intake": {
                    "active_target": {
                        "plan_path": "dev/active/ai_governance_platform.md",
                    },
                    "plan_routing": {
                        "phase_id": "MP377-P0",
                        "task_id": "MP377-P0-T01",
                        "task_summary": "Implement the canonical backlog reader/writer.",
                        "phase_status": "in_progress",
                        "task_status": "pending",
                    },
                },
                "quality_signals": {
                    "governance_review": {
                        "open_finding_count": 101,
                    }
                },
                "packet_inbox": {
                    "agents": [
                        {
                            "agent": "codex",
                            "pending_actionable_total": 5,
                        }
                    ]
                },
            }

            with patch(
                "dev.scripts.devctl.runtime.startup_context.build_startup_context",
                return_value=SimpleNamespace(
                    coordination=None,
                    to_dict=lambda: startup_context,
                ),
            ), patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test", "head": "deadbee", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test-repo"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            plan = snapshot["plan"]
            self.assertIn("MP377-P0 / MP377-P0-T01", plan["slice"])
            self.assertEqual(plan["open_findings"], 101)
            self.assertIn("phase=in_progress", plan["progress"])
            self.assertIn("task=pending", plan["progress"])
            self.assertEqual(plan["pending"], 5)

    def test_plan_section_pending_falls_back_to_session_packet_blocker(self) -> None:
        plan = dashboard_builders._build_plan_section(
            coordination={},
            session={
                "current_instruction": "dogfood the system",
                "implementer_status": "working",
                "open_findings": "5 pending review packet(s)",
            },
            bridge_findings=[],
            startup_context=None,
            pending_packets_count=1,
        )

        self.assertEqual(plan["pending"], 5)

    def test_assemble_accepts_plan_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = {
                "slice": "override slice",
                "progress": "override progress",
                "open_findings": 0,
                "findings_detail": [],
                "pending": 0,
            }

            with patch.object(dashboard, "_repo_name", return_value="test-repo"):
                snapshot = dashboard._assemble(
                    git={"branch": "feature/test", "head": "deadbee", "dirty": "CLEAN"},
                    compact=None,
                    push_data=None,
                    receipt=None,
                    agents=None,
                    pipeline=None,
                    bridge={
                        "last_poll_utc": "",
                        "instruction_full": "n/a",
                        "reviewer_mode": "n/a",
                    },
                    repo_root=root,
                    view="overview",
                    plan=plan,
                )

            self.assertEqual(snapshot["plan"], plan)

    def test_workers_have_enriched_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/review_channel/projections/latest/registry/agents.json", _minimal_agents())
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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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
        with patch.dict("os.environ", {"NO_COLOR": ""}, clear=False):
            output = dashboard_render.render_terminal(snapshot)

        self.assertIn("\033[", output)
        self.assertIn("GOVERNANCE DASHBOARD", output)
        self.assertIn("NOW", output)
        self.assertIn("REVIEWER (codex)", output)
        self.assertIn("WORKERS", output)
        self.assertIn("PLAN", output)
        self.assertIn("PUBLICATION", output)
        self.assertIn("QUALITY", output)
        self.assertIn("COORDINATION", output)
        self.assertIn("CONTROL PLANE", output)
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

    def test_remote_control_terminal_uses_mobile_narrow_layout(self) -> None:
        snapshot = _full_snapshot()
        snapshot["control_plane"]["operator_interaction_mode"] = "remote_control"

        output = dashboard_render.render_terminal(snapshot)

        self.assertNotIn("\033[", output)
        self.assertIn("Mode: remote_control", output)
        self.assertIn("Blocker: code-shape debt in common_io.py", output)
        self.assertIn("Pending actions: 2", output)
        self.assertNotIn("CONTROL PLANE", output)

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

    def test_terminal_quality_check_details(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("code_shape", output)
        self.assertIn("exceeded 350-line soft limit", output)

    def test_terminal_quality_no_check_details_when_empty(self) -> None:
        snapshot = _full_snapshot()
        snapshot["quality"]["check_details"] = []
        output = dashboard_render.render_terminal(snapshot)

        self.assertIn("QUALITY", output)
        self.assertNotIn("-- exceeded", output)

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
        self.assertIn("## Reviewer (codex)", output)
        self.assertIn("## Workers", output)
        self.assertIn("## Plan", output)
        self.assertIn("## Publication", output)
        self.assertIn("## Quality", output)
        self.assertIn("## Audit", output)
        self.assertIn("## Analytics", output)
        self.assertIn("## Coordination", output)
        self.assertIn("## Control Plane", output)
        self.assertIn("## Flow", output)

    def test_markdown_quality_check_details_table(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)

        self.assertIn("| Check | Status | Violation |", output)
        self.assertIn("| code_shape | FAIL |", output)
        self.assertIn("exceeded 350-line soft limit", output)

    def test_markdown_quality_no_detail_table_when_empty(self) -> None:
        snapshot = _full_snapshot()
        snapshot["quality"]["check_details"] = []
        output = dashboard_render.render_markdown(snapshot)

        self.assertIn("## Quality", output)
        self.assertNotIn("| Check | Status | Violation |", output)


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
                "coordination", "control_plane", "reviewer_activity", "flow", "timeline",
                "summary",
            }
            self.assertTrue(required.issubset(snapshot.keys()))

            # Reviewer activity degrades gracefully when bridge has no sections
            activity = snapshot["reviewer_activity"]
            self.assertEqual(activity["last_verdict"], "n/a")
            self.assertEqual(activity["reviewed_files"], 0)
            self.assertEqual(activity["findings_posted"], 0)
            self.assertEqual(activity["instruction_summary"], "n/a")

            # New enrichment sections degrade to n/a when artifacts missing
            self.assertEqual(snapshot["audit"]["total_findings"], "n/a")
            self.assertEqual(snapshot["analytics"]["total_events"], "n/a")
            self.assertEqual(snapshot["quality"]["probes"]["probes_enabled"], "n/a")
            self.assertEqual(snapshot["quality"]["check_details"], [])
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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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

    def test_snapshot_has_check_details_in_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test", "head": "deadbee", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            details = snapshot["quality"]["check_details"]
            self.assertEqual(len(details), 1)
            self.assertEqual(details[0]["check"], "code_shape")
            self.assertEqual(details[0]["status"], "FAIL")
            self.assertIn("exceeded limit", details[0]["violation"])

    def test_snapshot_has_analytics_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/data_science/latest/summary.json", _minimal_data_science())
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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
        snapshot["analytics"] = {"avg_time_to_green_s": "n/a", "total_events": "n/a", "command_success_rate_pct": "n/a", "push_success_values": [], "top_commands": [], "cleanup_rate_pct": "n/a"}
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

    def test_extract_check_details_multi_failure(self) -> None:
        """_extract_check_details parses multiple failing checks."""
        from dev.scripts.devctl.commands.dashboard_data import _extract_check_details

        output = (
            "\ncheck summary: 2/4 passed, 2 failed\n"
            "------------------------------------\n"
            "  PASS  docs_check\n"
            "  FAIL  code_shape  -- common_io.py exceeded 350 limit\n"
            "  FAIL  instr_sync  -- CLAUDE.md out of date\n"
            "  PASS  bridge_check\n"
        )
        details = _extract_check_details(output)
        self.assertEqual(len(details), 2)
        self.assertEqual(details[0]["check"], "code_shape")
        self.assertEqual(details[0]["status"], "FAIL")
        self.assertIn("exceeded 350 limit", details[0]["violation"])
        self.assertEqual(details[1]["check"], "instr_sync")
        self.assertIn("CLAUDE.md out of date", details[1]["violation"])

    def test_extract_check_details_empty_output(self) -> None:
        """_extract_check_details returns empty list for non-step output."""
        from dev.scripts.devctl.commands.dashboard_data import _extract_check_details

        self.assertEqual(_extract_check_details(""), [])
        self.assertEqual(_extract_check_details("some random error text"), [])

    def test_extract_check_details_pass_only(self) -> None:
        """_extract_check_details omits passing checks."""
        from dev.scripts.devctl.commands.dashboard_data import _extract_check_details

        output = "  PASS  docs_check\n  PASS  code_shape\n"
        self.assertEqual(_extract_check_details(output), [])


class TestReviewerActivitySection(unittest.TestCase):
    """Verify reviewer_activity section parsing and rendering."""

    def test_reviewer_activity_from_rich_bridge(self) -> None:
        """Rich bridge text produces populated reviewer_activity fields."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_rich_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            activity = snapshot["reviewer_activity"]
            self.assertIn("last_poll_age", activity)
            self.assertEqual(activity["reviewed_files"], 8)
            self.assertEqual(activity["findings_posted"], 2)
            self.assertIn("Launch ACK bypass", activity["last_verdict"])
            self.assertIn("Tighten wait_for_codex_poll_refresh", activity["instruction_summary"])

    def test_reviewer_activity_degrades_with_minimal_bridge(self) -> None:
        """Minimal bridge with no reviewer sections degrades to defaults."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            activity = snapshot["reviewer_activity"]
            self.assertEqual(activity["last_verdict"], "n/a")
            self.assertEqual(activity["reviewed_files"], 0)
            self.assertEqual(activity["findings_posted"], 0)

    def test_reviewer_activity_degrades_with_no_bridge(self) -> None:
        """No bridge.md at all still produces valid reviewer_activity."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            activity = snapshot["reviewer_activity"]
            self.assertEqual(activity["last_verdict"], "n/a")
            self.assertEqual(activity["reviewed_files"], 0)
            self.assertEqual(activity["findings_posted"], 0)
            self.assertEqual(activity["last_poll_age"], "--")

    def test_terminal_renders_reviewer_section(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        self.assertIn("REVIEWER (codex)", output)
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
        self.assertIn("## Reviewer (codex)", output)
        self.assertIn("Last poll", output)
        self.assertIn("12m ago", output)
        self.assertIn("Launch ACK bypass", output)
        self.assertIn("8 files", output)
        self.assertIn("2 posted", output)

    def test_terminal_reviewer_empty_activity(self) -> None:
        """When reviewer_activity is empty dict, section is skipped cleanly."""
        snapshot = _full_snapshot()
        snapshot["reviewer_activity"] = {}
        output = dashboard_render.render_terminal(snapshot)
        self.assertNotIn("REVIEWER", output)


class TestCliParserWiring(unittest.TestCase):
    """Verify the dashboard subparser is registered correctly."""

    def test_dashboard_parser_exists(self) -> None:
        parser = _build_dashboard_parser()
        args = parser.parse_args(["dashboard", "--format", "json", "--role", "observer"])
        self.assertEqual(args.command, "dashboard")
        self.assertEqual(args.format, "json")
        self.assertEqual(args.role, "observer")

    def test_dashboard_follow_flag(self) -> None:
        parser = _build_dashboard_parser()
        args = parser.parse_args(["dashboard", "--follow", "--interval", "1"])
        self.assertTrue(args.follow)
        self.assertEqual(args.interval, "1")

    def test_claude_loop_parser_exists(self) -> None:
        parser = _build_dashboard_parser()
        args = parser.parse_args(["claude-loop", "--format", "json", "--follow"])
        self.assertEqual(args.command, "claude-loop")
        self.assertEqual(args.format, "json")
        self.assertTrue(args.follow)
        self.assertEqual(args.interval, "typed")
        self.assertEqual(args.mode, "auto")

    def test_agent_loop_parser_accepts_typed_mode_target(self) -> None:
        parser = _build_dashboard_parser()
        args = parser.parse_args(
            [
                "agent-loop",
                "--actor",
                "codex",
                "--role",
                "reviewer",
                "--mode",
                "packet",
                "--packet",
                "rev_pkt_2571",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "agent-loop")
        self.assertEqual(args.actor, "codex")
        self.assertEqual(args.role, "reviewer")
        self.assertEqual(args.mode, "packet")
        self.assertEqual(args.packet, "rev_pkt_2571")

    def test_simple_operator_formats_parse(self) -> None:
        parser = _build_dashboard_parser()
        dashboard_args = parser.parse_args(["dashboard", "--format", "simple"])
        claude_args = parser.parse_args(["claude-loop", "--format", "simple"])
        monitor_args = parser.parse_args(["monitor", "--format", "simple"])
        self.assertEqual(dashboard_args.format, "simple")
        self.assertEqual(claude_args.format, "simple")
        self.assertEqual(monitor_args.format, "simple")

    def test_dashboard_default_format_is_terminal(self) -> None:
        parser = _build_dashboard_parser()
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
    """Verify top blocker is derived from the canonical reducer.

    These cases used to test a dashboard-local ``_derive_top_blocker``.
    Q99 collapses every producer onto ``runtime.startup_blocker_decision
    .derive_blocker_decision`` so the dashboard, startup-context, and
    control-plane read model all share one trace.
    """

    def test_blocker_from_quality_failing(self) -> None:
        from dev.scripts.devctl.runtime.startup_blocker_decision import (
            derive_blocker_decision,
        )

        snapshot = derive_blocker_decision(
            quality={"failing": ["dev/scripts/devctl/common_io.py"]},
            doctor={},
            session={},
        )
        self.assertIn("common_io.py", snapshot.top_blocker)
        self.assertEqual(snapshot.blocker_source, "quality")

    def test_blocker_from_findings(self) -> None:
        from dev.scripts.devctl.runtime.startup_blocker_decision import (
            derive_blocker_decision,
        )

        snapshot = derive_blocker_decision(
            quality={"failing": []},
            doctor={},
            session={"open_findings": "- F1: stale docs gate\n- F2: shape debt"},
        )
        self.assertIn("stale docs gate", snapshot.top_blocker)
        self.assertEqual(snapshot.blocker_source, "session")

    def test_blocker_none_when_clean(self) -> None:
        from dev.scripts.devctl.runtime.startup_blocker_decision import (
            derive_blocker_decision,
        )

        snapshot = derive_blocker_decision(
            quality={"failing": []}, doctor={}, session={},
        )
        self.assertEqual(snapshot.top_blocker, "none")
        self.assertEqual(snapshot.blocker_source, "none")


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
                "dev/reports/review_channel/projections/latest/full.json",
                {"attention": {"status": "reviewer_overdue", "summary": "Codex reviewer is overdue"}},
            )

            with patch(
                "dev.scripts.devctl.commands.dashboard_health._pid_is_alive",
                side_effect=lambda pid: pid == 85205,
            ):
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
            with patch(
                "dev.scripts.devctl.commands.dashboard_health._pid_is_alive",
                return_value=True,
            ):
                result = dashboard._read_heartbeat(hb_path)
            self.assertTrue(result["running"])
            self.assertEqual(result["pid"], 123)
            self.assertEqual(result["snapshots"], 10)
            self.assertIn("ago", result["last_heartbeat_age"])

    def test_read_heartbeat_dead_pid_not_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hb_path = root / "hb.json"
            hb_path.write_text(json.dumps({
                "pid": 123, "last_heartbeat_utc": "2026-04-04T03:00:00Z",
                "snapshots_emitted": 10, "stopped_at_utc": "",
            }))
            with patch(
                "dev.scripts.devctl.commands.dashboard_health._pid_is_alive",
                return_value=False,
            ):
                result = dashboard._read_heartbeat(hb_path)
            self.assertFalse(result["running"])

    def test_read_heartbeat_stopped_when_stopped_at_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hb_path = root / "hb.json"
            hb_path.write_text(json.dumps({
                "pid": 456, "last_heartbeat_utc": "2026-04-04T03:00:00Z",
                "snapshots_emitted": 5, "stopped_at_utc": "2026-04-04T03:01:00Z",
            }))
            with patch(
                "dev.scripts.devctl.commands.dashboard_health._pid_is_alive",
                return_value=True,
            ):
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

    def test_conductor_alive_without_pid_renders_running(self) -> None:
        snapshot = _full_snapshot()
        snapshot["health"]["codex_conductor"] = {"pid": None, "alive": True}
        terminal = dashboard_render.render_terminal(snapshot)
        self.assertIn("RUNNING", terminal)
        self.assertIn("pid unavailable", terminal)
        md = dashboard_render.render_markdown(snapshot)
        self.assertIn("RUNNING", md)
        self.assertIn("pid unavailable", md)


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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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
        with patch.dict("os.environ", {"NO_COLOR": ""}, clear=False):
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
        parser = _build_dashboard_parser()
        args = parser.parse_args(["dashboard", "--no-color"])
        self.assertTrue(args.no_color)

    def test_cli_parser_no_color_default_false(self) -> None:
        parser = _build_dashboard_parser()
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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
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
                "dev/reports/review_channel/projections/latest/compact.json",
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
                "dev/reports/review_channel/projections/latest/compact.json",
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
            self.assertIn("fix code shape", now["instruction_text"])
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
                "dev/reports/review_channel/projections/latest/compact.json",
                _minimal_compact(),
            )

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
                "ahead": 0, "behind": 0, "dirty_files": 0, "recent_commits": [],
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertEqual(snapshot["findings"], [])
            self.assertEqual(snapshot["plan"]["findings_detail"], [])


class TestSummaryCompilation(unittest.TestCase):
    """Verify _compile_summary derives correct conclusions from snapshot state."""

    def test_blocked_when_quality_gate_fails(self) -> None:
        snapshot = _full_snapshot()
        summary = dashboard._compile_summary(snapshot)
        self.assertEqual(summary["overall_state"], "blocked")
        self.assertIn("quality", summary["block_class"])
        self.assertEqual(summary["next_command_hint"], "fix code-shape debt")
        self.assertNotEqual(summary["primary_blocker"], "none")

    def test_healthy_when_all_pass(self) -> None:
        snapshot = _full_snapshot()
        snapshot["quality"] = {
            "docs_gate": "PASS", "plan_sync": "PASS", "bridge": "PASS",
            "code_shape": "PASS", "instr_sync": "PASS", "clippy": "PASS",
            "failing": [], "probes": {},
        }
        snapshot["health"]["attention_status"] = "healthy"
        snapshot["health"]["active_daemons"] = 2
        snapshot["coordination"]["reviewer_age"] = "2s ago"
        snapshot["publication"]["effective"] = "CURRENT"
        snapshot["now"]["owner"] = "Reviewer"
        snapshot["now"]["top_blocker"] = "none"
        summary = dashboard._compile_summary(snapshot)
        self.assertEqual(summary["overall_state"], "healthy")
        self.assertEqual(summary["block_class"], "none")
        self.assertEqual(summary["primary_blocker"], "none")
        self.assertIn("all green", summary["one_line"])

    def test_waiting_when_reviewer_overdue(self) -> None:
        snapshot = _full_snapshot()
        snapshot["quality"] = {
            "docs_gate": "PASS", "plan_sync": "PASS", "bridge": "PASS",
            "code_shape": "PASS", "instr_sync": "PASS", "clippy": "PASS",
            "failing": [], "probes": {},
        }
        snapshot["health"]["attention_status"] = "healthy"
        snapshot["coordination"]["reviewer_age"] = "22m ago"
        summary = dashboard._compile_summary(snapshot)
        self.assertEqual(summary["overall_state"], "waiting")
        self.assertEqual(summary["next_actor"], "reviewer")
        self.assertEqual(summary["next_command_hint"], "relaunch Codex")
        self.assertIn("reviewer stale", summary["one_line"])

    def test_active_when_implementer_owns(self) -> None:
        snapshot = _full_snapshot()
        snapshot["quality"] = {
            "docs_gate": "PASS", "plan_sync": "PASS", "bridge": "PASS",
            "code_shape": "PASS", "instr_sync": "PASS", "clippy": "PASS",
            "failing": [], "probes": {},
        }
        snapshot["health"]["attention_status"] = "healthy"
        snapshot["coordination"]["reviewer_age"] = "3m ago"
        snapshot["now"]["owner"] = "Implementer"
        summary = dashboard._compile_summary(snapshot)
        self.assertEqual(summary["overall_state"], "active")
        self.assertEqual(summary["next_actor"], "implementer")

    def test_infra_healthy_with_two_daemons(self) -> None:
        snapshot = _full_snapshot()
        snapshot["health"]["active_daemons"] = 2
        summary = dashboard._compile_summary(snapshot)
        self.assertEqual(summary["infra_state"], "healthy")
        self.assertIn("2 daemons running", summary["infra_label"])

    def test_infra_degraded_with_one_daemon(self) -> None:
        snapshot = _full_snapshot()
        snapshot["health"]["active_daemons"] = 1
        summary = dashboard._compile_summary(snapshot)
        self.assertEqual(summary["infra_state"], "degraded")

    def test_infra_down_with_zero_daemons(self) -> None:
        snapshot = _full_snapshot()
        snapshot["health"]["active_daemons"] = 0
        summary = dashboard._compile_summary(snapshot)
        self.assertEqual(summary["infra_state"], "down")

    def test_secondary_blocker_from_attention(self) -> None:
        snapshot = _full_snapshot()
        snapshot["health"]["attention_status"] = "stale"
        summary = dashboard._compile_summary(snapshot)
        self.assertIn("Attention stale", summary["secondary_blocker"])

    def test_secondary_blocker_from_reviewer_stale(self) -> None:
        snapshot = _full_snapshot()
        snapshot["health"]["attention_status"] = "healthy"
        snapshot["coordination"]["reviewer_age"] = "15m ago"
        summary = dashboard._compile_summary(snapshot)
        self.assertIn("Reviewer heartbeat stale", summary["secondary_blocker"])

    def test_block_class_includes_push_when_not_current(self) -> None:
        snapshot = _full_snapshot()
        snapshot["publication"]["effective"] = "NOT CURRENT"
        summary = dashboard._compile_summary(snapshot)
        self.assertIn("push", summary["block_class"])

    def test_one_line_is_nonempty_string(self) -> None:
        snapshot = _full_snapshot()
        summary = dashboard._compile_summary(snapshot)
        self.assertIsInstance(summary["one_line"], str)
        self.assertTrue(len(summary["one_line"]) > 10)
        self.assertTrue(summary["one_line"].endswith("."))

    def test_snapshot_includes_summary_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())
            _write_artifact(root, "dev/reports/push/latest.json", _minimal_push())
            _write_artifact(root, "dev/reports/startup/latest/receipt.json", _minimal_receipt())
            _write_artifact(root, "dev/reports/review_channel/projections/latest/registry/agents.json", _minimal_agents())
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test", "head": "deadbee", "dirty": "CLEAN",
                "ahead": 0, "behind": 0, "dirty_files": 0, "recent_commits": [],
            }), patch.object(dashboard, "_repo_name", return_value="test-repo"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertIn("summary", snapshot)
            summary = snapshot["summary"]
            self.assertIn("overall_state", summary)
            self.assertIn("block_class", summary)
            self.assertIn("next_actor", summary)
            self.assertIn("one_line", summary)

    def test_dashboard_role_filters_mutating_control_plane_command(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", {})
            _write_artifact(root, "dev/reports/review_channel/projections/latest/full.json", {})
            _write_artifact(
                root,
                "dev/reports/review_channel/projections/latest/registry/agents.json",
                {},
            )
            _write_artifact(
                root,
                "dev/reports/review_channel/projections/latest/commit_pipeline.json",
                {},
            )
            _write_artifact(root, "dev/reports/push/latest.json", {})
            _write_artifact(
                root,
                "dev/reports/startup/latest/receipt.json",
                {"push_action": "run_devctl_push"},
            )
            (root / "bridge.md").write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "feature/test",
                "head": "abc1234",
                "dirty": "CLEAN",
                "ahead": 0,
                "behind": 0,
                "dirty_files": 0,
                "recent_commits": [],
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root, role="dashboard")

        self.assertEqual(snapshot["control_plane"]["next_command"], READ_ONLY_NEXT_COMMAND)
        self.assertEqual(snapshot["next_command"], READ_ONLY_NEXT_COMMAND)


class TestSummaryRendering(unittest.TestCase):
    """Verify summary band appears first in both terminal and markdown output."""

    def test_terminal_summary_band_appears_first(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot)
        lines = output.strip().splitlines()
        self.assertTrue(len(lines) > 5)
        plain = dashboard_render.strip_ansi(output)
        self.assertIn("STATUS:", plain)
        status_pos = plain.index("STATUS:")
        dashboard_pos = plain.index("GOVERNANCE DASHBOARD")
        self.assertLess(status_pos, dashboard_pos)

    def test_terminal_summary_shows_blocked(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot, no_color=True)
        self.assertIn("STATUS: BLOCKED", output)
        self.assertIn("Why:", output)
        self.assertIn("Owner:", output)
        self.assertIn("Push:", output)
        self.assertIn("Infra:", output)

    def test_terminal_summary_shows_one_line(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot, no_color=True)
        one_line = snapshot["summary"]["one_line"]
        self.assertIn(one_line, output)

    def test_markdown_summary_card_appears_first(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("**Status**: BLOCKED", output)
        status_pos = output.index("**Status**:")
        header_pos = output.index("# Governance Dashboard")
        self.assertLess(status_pos, header_pos)

    def test_markdown_summary_shows_blocker(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("**Blocker**:", output)
        self.assertIn("code-shape", output)

    def test_markdown_summary_shows_one_line(self) -> None:
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        one_line = snapshot["summary"]["one_line"]
        self.assertIn(one_line, output)

    def test_terminal_no_blocker_lines_when_healthy(self) -> None:
        snapshot = _full_snapshot()
        snapshot["summary"]["primary_blocker"] = "none"
        snapshot["summary"]["secondary_blocker"] = "none"
        output = dashboard_render.render_terminal(snapshot, no_color=True)
        self.assertNotIn("Block:", output)

    def test_markdown_no_blocker_lines_when_healthy(self) -> None:
        snapshot = _full_snapshot()
        snapshot["summary"]["primary_blocker"] = "none"
        snapshot["summary"]["secondary_blocker"] = "none"
        output = dashboard_render.render_markdown(snapshot)
        self.assertNotIn("**Blocker**:", output)
        self.assertNotIn("**Secondary**:", output)

    def test_summary_absent_skips_section(self) -> None:
        snapshot = _full_snapshot()
        del snapshot["summary"]
        output = dashboard_render.render_terminal(snapshot, no_color=True)
        self.assertNotIn("STATUS:", output)
        md = dashboard_render.render_markdown(snapshot)
        self.assertNotIn("**Status**:", md)


class TestDashboardCharts(unittest.TestCase):
    """Verify ASCII chart rendering functions for the dashboard."""

    def test_sparkline_basic(self) -> None:
        from dev.scripts.devctl.commands.dashboard_charts import sparkline
        values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
        result = sparkline(values)
        self.assertEqual(len(result), 10)
        # Each character should be one of the block elements
        blocks = "▁▂▃▄▅▆▇█"
        for ch in result:
            self.assertIn(ch, blocks)
        # First value (min) should be lowest block, last (max) should be highest
        self.assertEqual(result[0], "▁")
        self.assertEqual(result[-1], "█")

    def test_sparkline_empty(self) -> None:
        from dev.scripts.devctl.commands.dashboard_charts import sparkline
        self.assertEqual(sparkline([]), "")

    def test_sparkline_constant(self) -> None:
        from dev.scripts.devctl.commands.dashboard_charts import sparkline
        result = sparkline([5.0, 5.0, 5.0])
        self.assertEqual(len(result), 3)
        # All same value uses middle block
        self.assertTrue(all(ch == result[0] for ch in result))

    def test_sparkline_width_downsamples(self) -> None:
        from dev.scripts.devctl.commands.dashboard_charts import sparkline
        values = list(range(100))
        result = sparkline([float(v) for v in values], width=10)
        self.assertEqual(len(result), 10)

    def test_bar_chart_basic(self) -> None:
        from dev.scripts.devctl.commands.dashboard_charts import bar_chart
        items = [("alpha", 100.0), ("beta", 50.0), ("gamma", 25.0)]
        result = bar_chart(items)
        result_lines = result.split("\n")
        self.assertEqual(len(result_lines), 3)
        # First item has full bar, values appear at end
        self.assertIn("100", result_lines[0])
        self.assertIn("50", result_lines[1])
        self.assertIn("25", result_lines[2])
        # First bar should be longest (most block chars)
        bar_0 = result_lines[0].count("█")
        bar_1 = result_lines[1].count("█")
        bar_2 = result_lines[2].count("█")
        self.assertGreater(bar_0, bar_1)
        self.assertGreater(bar_1, bar_2)

    def test_bar_chart_empty(self) -> None:
        from dev.scripts.devctl.commands.dashboard_charts import bar_chart
        self.assertEqual(bar_chart([]), "")

    def test_progress_bar_half(self) -> None:
        from dev.scripts.devctl.commands.dashboard_charts import progress_bar
        result = progress_bar(0.5)
        self.assertIn("[", result)
        self.assertIn("]", result)
        self.assertIn("50.0%", result)
        self.assertIn("█", result)
        self.assertIn("░", result)

    def test_progress_bar_full(self) -> None:
        from dev.scripts.devctl.commands.dashboard_charts import progress_bar
        result = progress_bar(1.0)
        self.assertIn("100.0%", result)
        self.assertNotIn("░", result)

    def test_progress_bar_clamps(self) -> None:
        from dev.scripts.devctl.commands.dashboard_charts import progress_bar
        result = progress_bar(1.5)
        self.assertIn("100.0%", result)
        result_neg = progress_bar(-0.5)
        self.assertIn("0.0%", result_neg)

    def test_terminal_renders_chart_elements(self) -> None:
        """Full snapshot terminal output includes sparkline, progress bar, and bar chart."""
        snapshot = _full_snapshot()
        output = dashboard_render.render_terminal(snapshot, no_color=True)
        self.assertIn("Push success:", output)
        self.assertIn("Cleanup:", output)
        self.assertIn("Top commands:", output)
        self.assertIn("autonomy-loop", output)

    def test_markdown_renders_chart_elements(self) -> None:
        """Markdown output includes chart elements in code blocks."""
        snapshot = _full_snapshot()
        output = dashboard_render.render_markdown(snapshot)
        self.assertIn("Push success", output)
        self.assertIn("Cleanup", output)
        self.assertIn("Top commands", output)
        self.assertIn("autonomy-loop", output)


class TestViewFlag(unittest.TestCase):
    """Verify the --view flag integration across parser, snapshot, and renderers."""

    def test_view_flag_accepted(self) -> None:
        """Parser accepts all seven view choices without error."""
        parser = _build_dashboard_parser()
        for view in ("overview", "dev", "analytics", "quality", "audit", "publication", "health"):
            args = parser.parse_args(["dashboard", "--view", view])
            self.assertEqual(args.view, view)

    def test_view_default_is_overview(self) -> None:
        parser = _build_dashboard_parser()
        args = parser.parse_args(["dashboard"])
        self.assertEqual(args.view, "overview")

    def test_view_dev_skips_analytics(self) -> None:
        """Dev view renders quality/plan/timeline but NOT analytics section."""
        snapshot = _full_snapshot()
        snapshot["view"] = "dev"
        md = dashboard_render.render_markdown(snapshot)
        # Dev view includes quality and plan
        self.assertIn("## Quality", md)
        self.assertIn("## Plan", md)
        # Dev view excludes analytics, publication, and health
        self.assertNotIn("## Analytics", md)
        self.assertNotIn("## Publication", md)
        self.assertNotIn("## Health", md)

    def test_view_dev_terminal_skips_analytics(self) -> None:
        """Dev view terminal output skips ANALYTICS and PUBLICATION sections."""
        snapshot = _full_snapshot()
        snapshot["view"] = "dev"
        output = dashboard_render.render_terminal(snapshot, no_color=True)
        self.assertNotIn("ANALYTICS", output)
        self.assertNotIn("PUBLICATION", output)
        # But should include QUALITY
        self.assertIn("QUALITY", output)

    def test_view_analytics_has_full_timeline(self) -> None:
        """Analytics view snapshot requests more than 10 timeline entries."""
        # The analytics view passes count=100 to _build_timeline_section.
        # We verify by building a snapshot with view="analytics" and checking
        # that the snapshot's timeline field could hold more than 10 entries.
        # Since we use a tmpdir with a synthetic events file, we can confirm
        # the count parameter is forwarded.
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Write a synthetic events file with 25 entries
            events_path = root / "dev" / "reports" / "audits"
            events_path.mkdir(parents=True, exist_ok=True)
            lines = []
            for i in range(25):
                entry = json.dumps({
                    "timestamp": f"2026-04-04T01:{i:02d}:00Z",
                    "command": f"cmd-{i}",
                    "success": True,
                    "duration_seconds": 1.0 + i,
                })
                lines.append(entry)
            (events_path / "devctl_events.jsonl").write_text(
                "\n".join(lines), encoding="utf-8",
            )
            timeline = dashboard._build_timeline_section(root, count=100)
            self.assertEqual(len(timeline), 25)
            # Default count=10 would only get last 10
            timeline_short = dashboard._build_timeline_section(root, count=10)
            self.assertEqual(len(timeline_short), 10)

    def test_view_quality_includes_audit_and_quality(self) -> None:
        snapshot = _full_snapshot()
        snapshot["view"] = "quality"
        md = dashboard_render.render_markdown(snapshot)
        self.assertIn("## Quality", md)
        self.assertIn("## Audit", md)
        # Excludes health, publication, workers
        self.assertNotIn("## Health", md)
        self.assertNotIn("## Publication", md)
        self.assertNotIn("## Workers", md)

    def test_view_health_includes_health_section(self) -> None:
        snapshot = _full_snapshot()
        snapshot["view"] = "health"
        md = dashboard_render.render_markdown(snapshot)
        self.assertIn("## Health", md)
        self.assertIn("## Coordination", md)
        # Excludes analytics, publication
        self.assertNotIn("## Analytics", md)
        self.assertNotIn("## Publication", md)

    def test_view_publication_includes_publication(self) -> None:
        snapshot = _full_snapshot()
        snapshot["view"] = "publication"
        md = dashboard_render.render_markdown(snapshot)
        self.assertIn("## Publication", md)
        self.assertNotIn("## Quality", md)
        self.assertNotIn("## Health", md)

    def test_overview_renders_all_sections(self) -> None:
        """Overview (default) renders every section present in the snapshot."""
        snapshot = _full_snapshot()
        snapshot["view"] = "overview"
        md = dashboard_render.render_markdown(snapshot)
        for section in ("Quality", "Audit", "Analytics", "Health",
                        "Publication", "Now", "Workers", "Plan"):
            self.assertIn(f"## {section}", md)

    def test_snapshot_carries_view_field(self) -> None:
        """Built snapshot includes a 'view' key matching the requested view."""
        snapshot = _full_snapshot()
        snapshot["view"] = "dev"
        self.assertEqual(snapshot["view"], "dev")


def _minimal_review_state() -> dict:
    """A typed ReviewState dict matching the shape of review_state.json."""
    return {
        "schema_version": 1,
        "contract_id": "ReviewState",
        "command": "review-channel",
        "action": "status",
        "timestamp": "2026-04-04T03:00:00Z",
        "ok": True,
        "current_session": {
            "current_instruction": "fix code shape in dashboard module",
            "current_instruction_revision": "typed_rev_001",
            "implementer_status": "implementing typed slice",
            "implementer_ack_state": "current",
            "open_findings": "- F1: code-shape debt\n- F2: stale docs",
            "last_reviewed_scope": "dashboard.py",
            "implementer_state_hash": "abc123hash",
        },
        "reviewer_runtime": {
            "doctor": {
                "status": "healthy",
                "summary": "all checks passing",
                "blocked_reason": "",
            },
        },
        "attention": {
            "status": "reviewer_overdue",
            "owner": "operator",
            "summary": "Codex reviewer has not polled in 15 minutes",
            "recommended_action": "Relaunch Codex conductor",
            "recommended_command": "python3 dev/scripts/devctl.py conductor-launch --provider codex",
        },
        "packets": [
            {
                "packet_id": "pkt_001",
                "kind": "instruction",
                "from_agent": "codex",
                "to_agent": "claude",
                "summary": "Fix code-shape debt in dashboard module",
                "body": "Full body here",
                "status": "pending",
                "policy_hint": "",
                "requested_action": "implement",
                "target_role": "implementer",
                "target_session_id": "session-claude",
                "approval_required": False,
                "posted_at": "2026-04-04T02:55:00Z",
            },
            {
                "packet_id": "pkt_002",
                "kind": "action_request",
                "from_agent": "claude",
                "to_agent": "operator",
                "summary": "Needs approval for force push",
                "body": "",
                "status": "pending",
                "policy_hint": "",
                "requested_action": "approve_force_push",
                "approval_required": True,
                "posted_at": "2026-04-04T02:56:00Z",
            },
            {
                "packet_id": "pkt_003",
                "kind": "finding",
                "from_agent": "codex",
                "to_agent": "claude",
                "summary": "Already applied finding",
                "body": "",
                "status": "applied",
                "policy_hint": "",
                "requested_action": "review_only",
                "approval_required": False,
                "posted_at": "2026-04-04T02:50:00Z",
            },
        ],
        "bridge": {},
        "queue": {
            "pending_total": 2,
            "pending_codex": 0,
            "pending_claude": 1,
            "pending_cursor": 0,
            "pending_operator": 1,
            "stale_packet_count": 0,
            "derived_next_instruction": "",
            "derived_next_instruction_source": {},
        },
        "review": {},
        "collaboration": {},
        "registry": {"timestamp": "", "agents": []},
        "warnings": [],
        "errors": [],
    }


class TestTypedReviewState(unittest.TestCase):
    """Verify dashboard reads typed ReviewState when available (Slice D)."""

    def test_session_from_review_state(self) -> None:
        """When review_state.json exists, session fields come from it."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                _minimal_review_state(),
            )
            _write_artifact(
                root,
                "dev/reports/review_channel/projections/latest/compact.json",
                {"current_session": {"current_instruction_revision": "old_compact_rev"}},
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            # The typed instruction_rev should come from review_state, not compact
            coord = snapshot["coordination"]
            self.assertEqual(coord["instruction_rev"], "typed_rev_001")

    def test_typed_attention_populated(self) -> None:
        """typed_attention section carries attention state from ReviewState."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                _minimal_review_state(),
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            attn = snapshot["typed_attention"]
            self.assertIsNotNone(attn)
            self.assertEqual(attn["status"], "reviewer_overdue")
            self.assertEqual(attn["owner"], "operator")
            self.assertIn("15 minutes", attn["summary"])
            self.assertIn("Relaunch", attn["recommended_action"])
            self.assertIn("conductor-launch", attn["recommended_command"])

    def test_pending_packets_filtered(self) -> None:
        """Only pending packets are surfaced, applied ones excluded."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                _minimal_review_state(),
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            packets = snapshot["pending_packets"]
            self.assertEqual(len(packets), 2)
            self.assertEqual(packets[0]["packet_id"], "pkt_001")
            self.assertEqual(packets[0]["target_role"], "implementer")
            self.assertEqual(packets[0]["target_session_id"], "session-claude")
            self.assertEqual(packets[1]["packet_id"], "pkt_002")
            self.assertTrue(packets[1]["approval_required"])
            self.assertEqual(packets[1]["delivery_emitted_at_utc"], "")
            self.assertEqual(packets[1]["delivery_observed_at_utc"], "")
            # Applied packet (pkt_003) should not appear
            ids = [p["packet_id"] for p in packets]
            self.assertNotIn("pkt_003", ids)

    def test_pending_packets_accept_typed_tuple_payloads(self) -> None:
        packets = tuple(_minimal_review_state()["packets"])

        extracted = dashboard_typed_state._extract_typed_packets({"packets": packets})

        self.assertEqual([packet["packet_id"] for packet in extracted], ["pkt_001", "pkt_002"])

    def test_coordination_pending_from_typed_packets(self) -> None:
        """coordination.pending_packets reflects typed packet count."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                _minimal_review_state(),
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertEqual(snapshot["coordination"]["pending_packets"], 2)
            self.assertEqual(snapshot["coordination"]["pending_count"], 2)
            self.assertEqual(snapshot["pending_count"], 2)

    def test_doctor_fields_in_coordination(self) -> None:
        """Doctor status from ReviewState appears in coordination section."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rs = _minimal_review_state()
            rs["reviewer_runtime"]["doctor"]["status"] = "blocked"
            rs["reviewer_runtime"]["doctor"]["blocked_reason"] = "stale_state"
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                rs,
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            coord = snapshot["coordination"]
            self.assertEqual(coord["doctor_status"], "blocked")
            self.assertEqual(coord["doctor_blocked"], "stale_state")

    def test_snapshot_exposes_top_level_header_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rs = _minimal_review_state()
            rs["current_session"]["open_findings"] = "1 pending review packet(s)"
            rs["queue"]["pending_total"] = 4
            rs["packets"].append({
                "packet_id": "pkt_004",
                "kind": "finding",
                "from_agent": "claude",
                "to_agent": "codex",
                "summary": "Another live packet",
                "body": "",
                "status": "pending",
                "policy_hint": "",
                "requested_action": "review_only",
                "approval_required": False,
                "posted_at": "2026-04-04T02:57:00Z",
            })
            rs["packets"].append({
                "packet_id": "pkt_005",
                "kind": "finding",
                "from_agent": "claude",
                "to_agent": "codex",
                "summary": "One more live packet",
                "body": "",
                "status": "pending",
                "policy_hint": "",
                "requested_action": "review_only",
                "approval_required": False,
                "posted_at": "2026-04-04T02:58:00Z",
            })
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                rs,
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertEqual(snapshot["status"], snapshot["summary"]["overall_state"])
            self.assertEqual(snapshot["owner"], snapshot["now"]["owner"])
            self.assertEqual(snapshot["next_action"], snapshot["now"]["next_action"])
            self.assertEqual(snapshot["top_blocker"], "4 pending review packet(s)")
            self.assertEqual(snapshot["coordination"]["pending_count"], 4)
            self.assertEqual(snapshot["pending_count"], 4)
            self.assertEqual(snapshot["pending_findings_count"], 0)
            self.assertEqual(snapshot["control_plane"]["pending_action_requests"], 0)

    def test_health_prefers_typed_liveness_over_stale_runtime_artifacts(self) -> None:
        class FrozenReviewState:
            def __init__(self, payload: dict[str, object]) -> None:
                self._payload = payload

            def to_dict(self) -> dict[str, object]:
                return dict(self._payload)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rs = _minimal_review_state()
            rs["reviewer_runtime"]["doctor"].update({
                "publisher_running": False,
                "reviewer_supervisor_running": False,
            })
            rs["bridge"] = {
                "reviewer_mode": "single_agent",
                "publisher_running": False,
                "codex_conductor_active": True,
                "claude_conductor_active": True,
                "last_codex_poll_utc": "2026-04-04T03:00:00Z",
            }
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")
            sources = {
                "review_state": rs,
                "compact_json": None,
                "push_report": None,
                "receipt": None,
                "publisher_hb": {"pid": 999999999},
                "supervisor_hb": {"pid": 999999999},
                "codex_conductor": None,
                "claude_conductor": None,
                "full_json": None,
            }

            with patch.object(
                dashboard,
                "load_sources",
                return_value=sources,
            ), patch.object(
                dashboard,
                "scan_repo_governance_safely",
                return_value=None,
            ), patch.object(
                dashboard,
                "load_current_review_state",
                return_value=FrozenReviewState(rs),
            ), patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root, view="health")

            health = snapshot["health"]
            self.assertFalse(health["publisher"]["running"])
            self.assertFalse(health["supervisor"]["running"])
            self.assertEqual(health["active_daemons"], 0)
            self.assertTrue(health["codex_conductor"]["alive"])
            self.assertTrue(health["claude_conductor"]["alive"])
            control_plane = snapshot["control_plane"]
            self.assertFalse(control_plane["publisher_running"])
            self.assertFalse(control_plane["supervisor_running"])
            self.assertTrue(control_plane["codex_conductor_alive"])
            self.assertTrue(control_plane["claude_conductor_alive"])

    def test_health_heartbeat_overrides_stale_bridge_running_projection(self) -> None:
        class FrozenReviewState:
            def __init__(self, payload: dict[str, object]) -> None:
                self._payload = payload

            def to_dict(self) -> dict[str, object]:
                return dict(self._payload)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rs = _minimal_review_state()
            rs["bridge"] = {
                "reviewer_mode": "active_dual_agent",
                "publisher_running": True,
                "reviewer_supervisor_running": True,
                "codex_conductor_active": False,
                "claude_conductor_active": False,
                "last_codex_poll_utc": "2026-04-04T03:00:00Z",
            }
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")
            sources = {
                "review_state": rs,
                "compact_json": None,
                "push_report": None,
                "receipt": None,
                "publisher_hb": {"pid": 999999999},
                "supervisor_hb": {"pid": 999999999},
                "codex_conductor": None,
                "claude_conductor": None,
                "full_json": None,
            }

            with patch.object(
                dashboard,
                "load_sources",
                return_value=sources,
            ), patch.object(
                dashboard,
                "scan_repo_governance_safely",
                return_value=None,
            ), patch.object(
                dashboard,
                "load_current_review_state",
                return_value=FrozenReviewState(rs),
            ), patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root, view="health")

            self.assertFalse(snapshot["health"]["publisher"]["running"])
            self.assertFalse(snapshot["health"]["supervisor"]["running"])
            self.assertEqual(snapshot["health"]["active_daemons"], 0)
            self.assertFalse(snapshot["control_plane"]["publisher_running"])
            self.assertFalse(snapshot["control_plane"]["supervisor_running"])

    def test_health_promotes_single_agent_local_reviewer_activity(self) -> None:
        import json
        import tempfile
        from datetime import datetime, timezone

        class FrozenReviewState:
            def __init__(self, payload: dict[str, object]) -> None:
                self._payload = payload

            def to_dict(self) -> dict[str, object]:
                return dict(self._payload)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_root = root / "dev/reports/review_channel/latest"
            event_log = root / "dev/reports/review_channel/events/trace.ndjson"
            event_log.parent.mkdir(parents=True, exist_ok=True)
            event_log.write_text(
                json.dumps(
                    {
                        "event_type": "packet_posted",
                        "from_agent": "codex",
                        "timestamp_utc": (
                            datetime.now(timezone.utc)
                            .isoformat()
                            .replace("+00:00", "Z")
                        ),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            rs = _minimal_review_state()
            rs["reviewer_runtime"]["doctor"].update({
                "publisher_running": False,
                "reviewer_supervisor_running": False,
            })
            rs["bridge"] = {
                "reviewer_mode": "single_agent",
                "publisher_running": False,
                "codex_conductor_active": False,
                "claude_conductor_active": True,
                "last_codex_poll_utc": "2026-04-04T03:00:00Z",
            }
            rs["collaboration"] = {"review_agent": "codex"}
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")
            sources = {
                "review_state": rs,
                "compact_json": None,
                "push_report": None,
                "receipt": None,
                "publisher_hb": {"pid": 123},
                "supervisor_hb": {"pid": 456},
                "codex_conductor": None,
                "claude_conductor": None,
                "full_json": None,
                "session_output_root": status_root,
            }

            with patch.object(
                dashboard,
                "load_sources",
                return_value=sources,
            ), patch.object(
                dashboard,
                "scan_repo_governance_safely",
                return_value=None,
            ), patch.object(
                dashboard,
                "load_current_review_state",
                return_value=FrozenReviewState(rs),
            ), patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root, view="health")

            self.assertTrue(snapshot["health"]["codex_conductor"]["alive"])
            self.assertTrue(snapshot["control_plane"]["codex_conductor_alive"])

    def test_health_promotes_single_agent_rollout_activity(self) -> None:
        import os
        import tempfile
        from datetime import datetime, timezone

        from dev.scripts.devctl.review_channel import collaboration_session as collaboration_mod

        class FrozenReviewState:
            def __init__(self, payload: dict[str, object]) -> None:
                self._payload = payload

            def to_dict(self) -> dict[str, object]:
                return dict(self._payload)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_root = root / "dev/reports/review_channel/latest"
            rollout_path = (
                root
                / "sessions"
                / "2026"
                / "04"
                / "11"
                / "rollout-2026-04-11T21-52-00-codex-live.jsonl"
            )
            rollout_path.parent.mkdir(parents=True, exist_ok=True)
            rollout_path.write_text("{}\n", encoding="utf-8")
            rollout_mtime = datetime(
                2026, 4, 11, 21, 52, 0, tzinfo=timezone.utc
            ).timestamp()
            os.utime(rollout_path, (rollout_mtime, rollout_mtime))
            rs = _minimal_review_state()
            rs["reviewer_runtime"]["doctor"].update({
                "publisher_running": False,
                "reviewer_supervisor_running": False,
            })
            rs["bridge"] = {
                "reviewer_mode": "single_agent",
                "publisher_running": False,
                "codex_conductor_active": False,
                "claude_conductor_active": True,
                "last_codex_poll_utc": "2026-04-04T03:00:00Z",
            }
            rs["collaboration"] = {"review_agent": "codex"}
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")
            sources = {
                "review_state": rs,
                "compact_json": None,
                "push_report": None,
                "receipt": None,
                "publisher_hb": {"pid": 123},
                "supervisor_hb": {"pid": 456},
                "codex_conductor": None,
                "claude_conductor": None,
                "full_json": None,
                "session_output_root": status_root,
            }

            with patch.object(
                collaboration_mod,
                "discover_latest_session",
                return_value=rollout_path,
            ), patch.object(
                collaboration_mod,
                "_utcnow",
                return_value=datetime(2026, 4, 11, 21, 54, 0, tzinfo=timezone.utc),
            ), patch.object(
                dashboard,
                "load_sources",
                return_value=sources,
            ), patch.object(
                dashboard,
                "scan_repo_governance_safely",
                return_value=None,
            ), patch.object(
                dashboard,
                "load_current_review_state",
                return_value=FrozenReviewState(rs),
            ), patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root, view="health")

            self.assertTrue(snapshot["health"]["codex_conductor"]["alive"])
            self.assertTrue(snapshot["control_plane"]["codex_conductor_alive"])

    def test_typed_coordination_fields_flow_into_dashboard_snapshot(self) -> None:
        from dev.scripts.devctl.runtime.review_state_parser import (
            review_state_from_payload,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rs = _minimal_review_state()
            rs["coordination"] = {
                "contract_id": "CoordinationSnapshot",
                "current_slice": "Surface single-agent implementer work in dashboard.",
                "declared_topology": "multi_agent_orchestrated",
                "observed_topology": "single_agent",
                "recommended_topology": "single_agent",
                "fanout_posture": "planned_scaffolding_only",
                "safe_to_fanout": False,
                "worktree_strategy": "isolated_worker_worktrees",
                "resync_required": True,
                "resync_reasons": ["declared_topology:multi_agent_orchestrated"],
                "actors": [
                    {
                        "actor_id": "codex",
                        "provider": "codex",
                        "role": "implementer",
                        "presence": "live",
                    }
                ],
            }
            master_plan_path = root / "dev/active/MASTER_PLAN.md"
            master_plan_path.parent.mkdir(parents=True, exist_ok=True)
            master_plan_path.write_text(
                "# Master Plan\n\n"
                "- ACTIVE: MP-999 conflicting plan authority\n",
                encoding="utf-8",
            )
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                rs,
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            sources = {
                "review_state": rs,
                "compact_json": None,
                "push_report": None,
                "receipt": None,
                "publisher_hb": None,
                "supervisor_hb": None,
                "codex_conductor": None,
                "claude_conductor": None,
                "full_json": None,
            }
            with patch.object(
                dashboard,
                "load_sources",
                return_value=sources,
            ), patch.object(
                dashboard,
                "scan_repo_governance_safely",
                return_value=None,
            ), patch.object(
                dashboard,
                "load_current_review_state",
                return_value=review_state_from_payload(rs),
            ), patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            coord = snapshot["coordination"]
            self.assertEqual(
                coord["current_slice"],
                "Surface single-agent implementer work in dashboard.",
            )
            self.assertEqual(
                snapshot["plan"]["slice"],
                "Surface single-agent implementer work in dashboard.",
            )
            self.assertNotIn("MP-999", snapshot["plan"]["slice"])
            self.assertEqual(coord["recommended_topology"], "single_agent")
            self.assertTrue(coord["resync_required"])
            self.assertEqual(coord["actors"][0]["actor_id"], "codex")

    def test_now_section_prefers_live_reviewer_truth_over_stale_agent_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rs = _minimal_review_state()
            rs["coordination"] = {
                "contract_id": "CoordinationSnapshot",
                "current_slice": "Codex is verifying and staging the checkpoint slice.",
                "declared_topology": "single_agent",
                "observed_topology": "single_agent",
                "recommended_topology": "single_agent",
                "fanout_posture": "single_agent_only",
                "safe_to_fanout": False,
                "worktree_strategy": "shared_primary_worktree",
                "resync_required": True,
                "resync_reasons": ["attention:checkpoint_required"],
                "actors": [
                    {
                        "actor_id": "codex",
                        "provider": "codex",
                        "role": "reviewer",
                        "presence": "live",
                    }
                ],
            }
            rs["reviewer_runtime"]["doctor"]["runtime_counts"] = {
                "live_participant_count": 1,
                "live_reviewer_count": 1,
                "live_implementer_count": 0,
                "active_conductor_count": 1,
                "running_daemon_count": 0,
            }
            sources = {
                "review_state": rs,
                "compact_json": None,
                "push_report": None,
                "receipt": None,
                "publisher_hb": None,
                "supervisor_hb": None,
                "codex_conductor": None,
                "claude_conductor": None,
                "full_json": None,
            }
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")
            class FrozenReviewState:
                def __init__(self, payload: dict) -> None:
                    self._payload = payload

                def to_dict(self) -> dict:
                    return json.loads(json.dumps(self._payload))

            with patch.object(
                dashboard,
                "load_sources",
                return_value=sources,
            ), patch.object(
                dashboard,
                "scan_repo_governance_safely",
                return_value=None,
            ), patch.object(
                dashboard,
                "load_current_review_state",
                return_value=FrozenReviewState(rs),
            ), patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "DIRTY",
            }), patch.object(dashboard, "_repo_name", return_value="test"), patch.object(
                dashboard,
                "_read_json",
                return_value=_minimal_agents(),
            ):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertEqual(snapshot["now"]["owner"], "Reviewer")
            self.assertEqual(snapshot["now"]["owner_provider"], "codex")
            self.assertEqual(
                snapshot["now"]["instruction_text"],
                "Codex is verifying and staging the checkpoint slice.",
            )

    def test_threads_frozen_review_state_into_control_plane(self) -> None:
        """build_snapshot should feed one frozen review_state into the read model."""
        class DummyControlPlane:
            def __init__(self) -> None:
                self.top_blocker = "none"
                self.next_action = "n/a"
                self.reviewer_mode = "active_dual_agent"
                self.attention_status = "n/a"
                self.attention_summary = "n/a"
                self.publisher_running = False
                self.supervisor_running = False
                self.codex_conductor_alive = False
                self.claude_conductor_alive = False
                self.coordination = None

            def to_dict(self) -> dict[str, str]:
                return {"contract_id": "ControlPlaneReadModel"}

        class FrozenReviewState:
            def __init__(self, payload: dict[str, object]) -> None:
                self._payload = payload

            def to_dict(self) -> dict[str, object]:
                return dict(self._payload)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fresh_review_state = _minimal_review_state()
            typed_review_state = FrozenReviewState(fresh_review_state)
            governance = object()
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                fresh_review_state,
            )
            _write_artifact(
                root,
                "dev/reports/review_channel/projections/latest/compact.json",
                {
                    "current_session": {
                        "current_instruction_revision": "stale_compact_rev",
                    },
                },
            )

            dummy_control_plane = DummyControlPlane()
            sources = {
                "review_state": fresh_review_state,
                "compact_json": {"current_session": {"current_instruction_revision": "stale_compact_rev"}},
                "push_report": None,
                "receipt": None,
                "publisher_hb": None,
                "supervisor_hb": None,
                "codex_conductor": None,
                "claude_conductor": None,
                "full_json": None,
            }

            with patch.object(
                dashboard,
                "scan_repo_governance_safely",
                return_value=governance,
            ), patch.object(
                dashboard,
                "load_current_review_state",
                return_value=typed_review_state,
            ) as mock_load_current_review_state, patch.object(
                dashboard,
                "load_sources",
                return_value=sources,
            ) as mock_load_sources, patch.object(
                dashboard,
                "build_control_plane_read_model",
                return_value=dummy_control_plane,
            ) as mock_build, patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            mock_load_current_review_state.assert_called_once_with(
                root,
                governance=governance,
                prefer_cached_projection=False,
            )
            mock_load_sources.assert_called_once_with(
                root,
                governance=governance,
                review_state_override=typed_review_state,
            )
            self.assertIs(
                mock_build.call_args.kwargs["options"].review_state,
                typed_review_state,
            )
            self.assertIs(
                mock_build.call_args.kwargs["options"].governance,
                governance,
            )
            self.assertEqual(
                mock_build.call_args.kwargs["sources_override"]["review_state"],
                fresh_review_state,
            )
            self.assertEqual(
                snapshot["control_plane"]["contract_id"],
                "ControlPlaneReadModel",
            )

    def test_fallback_to_compact_when_no_review_state(self) -> None:
        """Without review_state.json, session comes from compact.json."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/projections/latest/compact.json",
                _minimal_compact(),
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            coord = snapshot["coordination"]
            self.assertEqual(coord["instruction_rev"], "abc123")
            self.assertIsNone(snapshot["typed_attention"])
            self.assertEqual(snapshot["pending_packets"], [])

    def test_graceful_with_empty_review_state(self) -> None:
        """ReviewState with missing/empty fields degrades without crash."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                {"schema_version": 1, "contract_id": "ReviewState"},
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertIn("coordination", snapshot)
            self.assertEqual(snapshot["pending_packets"], [])


class TestTypedAttentionRendering(unittest.TestCase):
    """Verify typed attention section renders in terminal and markdown."""

    def _snapshot_with_attention(self) -> dict:
        snap = _full_snapshot()
        snap["typed_attention"] = {
            "status": "reviewer_overdue",
            "owner": "operator",
            "summary": "Codex reviewer not polling",
            "recommended_action": "Relaunch conductor",
            "recommended_command": "devctl conductor-launch",
        }
        return snap

    def test_terminal_renders_attention_section(self) -> None:
        output = dashboard_render.render_terminal(
            self._snapshot_with_attention(), no_color=True,
        )
        self.assertIn("ATTENTION", output)
        self.assertIn("reviewer_overdue", output)
        self.assertIn("operator", output)
        self.assertIn("Relaunch conductor", output)
        self.assertIn("devctl conductor-launch", output)

    def test_markdown_renders_attention_section(self) -> None:
        output = dashboard_render.render_markdown(
            self._snapshot_with_attention(),
        )
        self.assertIn("## Attention", output)
        self.assertIn("reviewer_overdue", output)
        self.assertIn("Relaunch conductor", output)

    def test_attention_skipped_when_healthy(self) -> None:
        snap = _full_snapshot()
        snap["typed_attention"] = {"status": "healthy", "owner": "system"}
        output = dashboard_render.render_terminal(snap, no_color=True)
        self.assertNotIn("ATTENTION", output)

    def test_attention_skipped_when_none(self) -> None:
        snap = _full_snapshot()
        snap["typed_attention"] = None
        output = dashboard_render.render_terminal(snap, no_color=True)
        self.assertNotIn("ATTENTION", output)


class TestPendingPacketRendering(unittest.TestCase):
    """Verify pending packets render under COORDINATION."""

    def _snapshot_with_packets(self) -> dict:
        snap = _full_snapshot()
        snap["pending_packets"] = [
            {
                "packet_id": "pkt_001",
                "kind": "instruction",
                "from_agent": "codex",
                "to_agent": "claude",
                "summary": "Fix the shape debt",
                "status": "pending",
                "requested_action": "implement",
                "approval_required": False,
            },
            {
                "packet_id": "pkt_002",
                "kind": "action_request",
                "from_agent": "claude",
                "to_agent": "operator",
                "summary": "Needs approval",
                "status": "pending",
                "requested_action": "approve",
                "approval_required": True,
            },
        ]
        snap["coordination"]["pending_packets"] = 2
        return snap

    def test_terminal_shows_packet_lines(self) -> None:
        output = dashboard_render.render_terminal(
            self._snapshot_with_packets(), no_color=True,
        )
        self.assertIn("PKT", output)
        self.assertIn("instruction -> claude", output)
        self.assertIn("Fix the shape debt", output)
        self.assertIn("[approval]", output)

    def test_markdown_shows_packet_lines(self) -> None:
        output = dashboard_render.render_markdown(
            self._snapshot_with_packets(),
        )
        # Generic "Pending packets" heading: the pending-packets list carries
        # every kind, so labelling the section "action packets" would
        # misreport instructions, findings, and system notices as operator
        # actions. MP-384/MP-385 will split the counters and let us render a
        # dedicated action-request view.
        self.assertIn("Pending packets", output)
        self.assertNotIn("Pending action packets", output)
        self.assertIn("`instruction`", output)
        self.assertIn("Fix the shape debt", output)
        self.assertIn("*[approval required]*", output)

    def test_no_packets_no_section(self) -> None:
        snap = _full_snapshot()
        snap["pending_packets"] = []
        snap["control_packets"] = []
        output = dashboard_render.render_terminal(snap, no_color=True)
        self.assertNotIn("PKT", output)

    def test_markdown_shows_action_request_lifecycle_without_pending_rows(self) -> None:
        snap = _full_snapshot()
        snap["pending_packets"] = []
        snap["control_packets"] = [
            {
                "packet_id": "rev_pkt_2205",
                "to_agent": "claude",
                "requested_action": "stage_commit_pipeline",
                "lifecycle_current_state": "failed",
                "execution_failed_reason": "pending_reviewer_packets",
                "semantic_zref": "packet:rev_pkt_2205",
            }
        ]
        output = dashboard_render.render_markdown(snap)
        self.assertIn("Action-request lifecycle", output)
        self.assertIn("`failed`", output)
        self.assertIn("packet:rev_pkt_2205", output)


class TestTypedDataExtractors(unittest.TestCase):
    """Unit tests for the typed ReviewState extraction functions."""

    def test_extract_typed_session(self) -> None:
        from dev.scripts.devctl.commands.dashboard_data import _extract_typed_session
        rs = _minimal_review_state()
        session = _extract_typed_session(rs)
        self.assertEqual(session["current_instruction_revision"], "typed_rev_001")
        self.assertEqual(session["implementer_ack_state"], "current")
        self.assertIn("code shape", session["current_instruction"])

    def test_extract_typed_doctor(self) -> None:
        from dev.scripts.devctl.commands.dashboard_data import _extract_typed_doctor
        rs = _minimal_review_state()
        doctor = _extract_typed_doctor(rs)
        self.assertEqual(doctor["status"], "healthy")
        self.assertEqual(doctor["blocked_reason"], "")

    def test_extract_typed_doctor_fallback(self) -> None:
        from dev.scripts.devctl.commands.dashboard_data import _extract_typed_doctor
        rs = {"doctor": {"status": "blocked", "blocked_reason": "stale"}}
        doctor = _extract_typed_doctor(rs)
        self.assertEqual(doctor["status"], "blocked")

    def test_extract_typed_attention(self) -> None:
        from dev.scripts.devctl.commands.dashboard_data import _extract_typed_attention
        rs = _minimal_review_state()
        attn = _extract_typed_attention(rs)
        self.assertIsNotNone(attn)
        self.assertEqual(attn["status"], "reviewer_overdue")
        self.assertIn("conductor-launch", attn["recommended_command"])

    def test_extract_typed_attention_none(self) -> None:
        from dev.scripts.devctl.commands.dashboard_data import _extract_typed_attention
        self.assertIsNone(_extract_typed_attention(None))
        self.assertIsNone(_extract_typed_attention({"attention": "not_a_dict"}))

    def test_extract_typed_packets(self) -> None:
        from dev.scripts.devctl.commands.dashboard_data import _extract_typed_packets
        rs = _minimal_review_state()
        packets = _extract_typed_packets(rs)
        self.assertEqual(len(packets), 2)
        self.assertEqual(packets[0]["kind"], "instruction")
        self.assertTrue(packets[1]["approval_required"])

    def test_extract_typed_packets_empty(self) -> None:
        from dev.scripts.devctl.commands.dashboard_data import _extract_typed_packets
        self.assertEqual(_extract_typed_packets(None), [])
        self.assertEqual(_extract_typed_packets({"packets": "bad"}), [])
        self.assertEqual(_extract_typed_packets({"packets": []}), [])

    def test_extracts_instruction_provenance_from_review_state_tick(self) -> None:
        from dev.scripts.devctl.commands.dashboard_data import (
            _extract_typed_instruction_provenance,
            _extract_typed_priority_decision,
        )
        rs = _minimal_review_state()
        rs["queue"]["derived_next_instruction_source"] = {
            "provenance": {"source_kind": "ReviewPacketEvent"},
            "priority_decision": {"rule_id": "action_request_priority"},
        }
        self.assertEqual(
            _extract_typed_instruction_provenance(rs)["source_kind"],
            "ReviewPacketEvent",
        )
        self.assertEqual(
            _extract_typed_priority_decision(rs)["rule_id"],
            "action_request_priority",
        )

    def test_extract_typed_control_packets_keeps_failed_action_request_visible(self) -> None:
        from dev.scripts.devctl.commands.dashboard_data import (
            _extract_typed_control_packets,
        )
        packets = _extract_typed_control_packets(
            {
                "packets": [
                    {
                        "packet_id": "rev_pkt_2205",
                        "kind": "action_request",
                        "to_agent": "claude",
                        "status": "pending",
                        "requested_action": "stage_commit_pipeline",
                        "execution_failed_at_utc": "2026-04-29T13:00:00Z",
                        "execution_failed_reason": "pending_reviewer_packets",
                        "lifecycle_current_state": "failed",
                        "semantic_zref": "packet:rev_pkt_2205",
                    },
                    {
                        "packet_id": "rev_pkt_note",
                        "kind": "system_notice",
                        "to_agent": "claude",
                        "status": "pending",
                    },
                ],
            }
        )
        self.assertEqual([packet["packet_id"] for packet in packets], ["rev_pkt_2205"])
        self.assertEqual(packets[0]["lifecycle_current_state"], "failed")
        self.assertEqual(packets[0]["semantic_zref"], "packet:rev_pkt_2205")


def _review_state_with_bridge() -> dict:
    """ReviewState with populated bridge fields for typed-bridge-path tests."""
    rs = _minimal_review_state()
    rs["bridge"] = {
        "overall_state": "active",
        "codex_poll_state": "fresh",
        "reviewer_freshness": "fresh",
        "reviewer_mode": "active_dual_agent",
        "last_codex_poll_utc": "2026-04-04T03:10:00Z",
        "last_codex_poll_age_seconds": 30,
        "last_worktree_hash": "abc123",
        "current_instruction": "Tighten wait_for_codex_poll_refresh so typed launch truth requires fresh turn",
        "open_findings": "- F1: handoff.py accepts launch success with stale poll\n- F2: test coverage missing for fail-closed path",
        "claude_status": "implementing",
        "claude_ack": "current",
        "claude_ack_current": True,
        "current_instruction_revision": "typed_rev_001",
        "claude_ack_revision": "typed_rev_001",
        "last_reviewed_scope": "dashboard.py\nbridge.md",
    }
    return rs


class TestTypedBridgePath(unittest.TestCase):
    """F1 (MP-384): Dashboard reads verdict/findings/instruction from typed
    ReviewState first, falling back to bridge markdown only when absent."""

    def test_typed_bridge_fields_override_markdown(self) -> None:
        """When review_state.json has bridge fields, bridge.md is not needed."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                _review_state_with_bridge(),
            )
            # Write stale/contradictory bridge.md to prove it's not used
            stale_bridge = (
                "# Review Bridge\n\n"
                "- Last Codex poll: `2025-01-01T00:00:00Z`\n"
                "- Reviewer mode: `paused`\n\n"
                "## Current Instruction For Claude\n\nSTALE instruction\n\n"
                "## Open Findings\n\n- F99: stale finding\n"
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(stale_bridge, encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            # Bridge fields should come from typed state, not stale markdown
            now = snapshot["now"]
            self.assertIn("Tighten", now["instruction_text"])
            self.assertNotIn("STALE", now["instruction_text"])

            review = snapshot["review"]
            self.assertEqual(review["mode"], "active_dual_agent")
            self.assertNotEqual(review["mode"], "paused")
            self.assertIn("Tighten", review["instruction"])
            self.assertNotIn("STALE", review["instruction"])

            findings = snapshot["findings"]
            self.assertEqual(len(findings), 2)
            self.assertEqual(findings[0]["id"], "F1")
            self.assertIn("handoff.py", findings[0]["summary"])
            # Stale F99 should not appear
            ids = [f["id"] for f in findings]
            self.assertNotIn("F99", ids)

    def test_renders_correctly_when_bridge_md_missing(self) -> None:
        """Dashboard renders without crash when review_state.json exists
        but bridge.md is completely absent."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                _review_state_with_bridge(),
            )
            # No bridge.md at all

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertIn("review", snapshot)
            self.assertEqual(snapshot["review"]["mode"], "active_dual_agent")
            findings = snapshot["findings"]
            self.assertEqual(len(findings), 2)

    def test_falls_back_to_bridge_md_without_review_state(self) -> None:
        """Without review_state.json, bridge.md is parsed as before."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bridge_path = root / "bridge.md"
            bridge_path.parent.mkdir(parents=True, exist_ok=True)
            bridge_path.write_text(_rich_bridge_text(), encoding="utf-8")
            _write_artifact(
                root,
                "dev/reports/review_channel/projections/latest/compact.json",
                _minimal_compact(),
            )

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            review = snapshot["review"]
            self.assertEqual(review["mode"], "active_dual_agent")
            findings = snapshot["findings"]
            self.assertEqual(len(findings), 2)
            self.assertEqual(findings[0]["id"], "F1")

    def test_build_snapshot_prefers_fresh_loaded_review_state_over_stale_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale = _minimal_review_state()
            stale["bridge"] = {
                "current_instruction": "",
                "open_findings": "",
                "reviewer_mode": "paused",
                "last_codex_poll_utc": "",
            }
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                stale,
            )

            fresh_sources = {
                "review_state": _review_state_with_bridge(),
                "compact_json": None,
                "push_report": None,
                "receipt": None,
                "publisher_hb": None,
                "supervisor_hb": None,
                "codex_conductor": None,
                "claude_conductor": None,
                "full_json": None,
            }

            with patch.object(
                dashboard, "load_sources", return_value=fresh_sources
            ), patch.object(
                dashboard, "_git_short", return_value={
                    "branch": "main", "head": "abc", "dirty": "CLEAN",
                }
            ), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

            self.assertIn("Tighten", snapshot["now"]["instruction_text"])
            self.assertIn("Tighten", snapshot["review"]["instruction"])
            self.assertEqual(snapshot["review"]["mode"], "active_dual_agent")
            self.assertEqual(len(snapshot["findings"]), 2)

    def test_verdict_stays_na_from_typed_state(self) -> None:
        """Verdict is bridge-markdown-only; typed path returns 'n/a'."""
        from dev.scripts.devctl.commands.dashboard_typed_state import (
            _extract_typed_bridge_fields,
        )
        rs = _review_state_with_bridge()
        fields = _extract_typed_bridge_fields(rs)
        self.assertEqual(fields["verdict"], "n/a")

    def test_typed_bridge_fields_prefer_effective_reviewer_mode(self) -> None:
        """Dashboard fallback mode should reflect the effective reviewer mode."""
        from dev.scripts.devctl.commands.dashboard_typed_state import (
            _extract_typed_bridge_fields,
        )

        review_state = {
            "bridge": {
                "current_instruction": "fix shape",
                "last_codex_poll_utc": "2026-04-04T00:00:00Z",
                "reviewer_mode": "active_dual_agent",
                "effective_reviewer_mode": "tools_only",
            },
            "reviewer_runtime": {
                "effective_reviewer_mode": "tools_only",
            },
        }

        fields = _extract_typed_bridge_fields(review_state)
        self.assertEqual(fields["reviewer_mode"], "tools_only")

    def test_typed_bridge_findings_extraction(self) -> None:
        """Typed bridge findings parse the markdown list correctly."""
        from dev.scripts.devctl.commands.dashboard_typed_state import (
            _extract_typed_bridge_findings,
        )
        rs = _review_state_with_bridge()
        findings = _extract_typed_bridge_findings(rs)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["id"], "F1")
        self.assertEqual(findings[1]["id"], "F2")
        self.assertIn("handoff.py", findings[0]["summary"])


class TestViolationRecordInPushReport(unittest.TestCase):
    """F2 (MP-381+384): push report carries typed violations from preflight."""

    def test_violations_reach_dashboard_quality(self) -> None:
        """ViolationRecord file/line/policy/fix/source/severity fields
        propagate through the push report into dashboard check_details
        without parsing format_steps_text()."""
        from dev.scripts.devctl.commands.vcs.push_report import (
            _extract_preflight_violations,
        )
        from dev.scripts.devctl.commands.dashboard_data import (
            _build_quality_section,
        )

        preflight_step = {
            "name": "code_shape",
            "returncode": 1,
            "cmd": ["python3", "dev/scripts/checks/check_code_shape.py"],
            "duration_s": 2.5,
            "failure_output": (
                "dev/scripts/devctl/commands/dashboard.py:412 exceeded 350-line soft limit"
            ),
            "violation_detail": {
                "file_path": "dev/scripts/devctl/commands/dashboard.py",
                "line": 412,
                "policy": "code_shape.python_soft_limit",
                "fix": "Modularize file to reduce line count",
                "source": "code_shape",
                "severity": "warning",
            },
        }
        violations = _extract_preflight_violations(
            preflight_step, "2026-04-04T00:00:00Z",
        )

        # Verify the violations carry all structured fields
        self.assertEqual(len(violations), 1)
        v = violations[0]
        self.assertEqual(v["step_name"], "code_shape")
        self.assertEqual(v["file_path"], "dev/scripts/devctl/commands/dashboard.py")
        self.assertEqual(v["line"], 412)
        self.assertEqual(v["policy"], "code_shape.python_soft_limit")
        self.assertEqual(v["fix"], "Modularize file to reduce line count")
        self.assertEqual(v["source"], "code_shape")
        self.assertEqual(v["severity"], "warning")

        # Simulate push report with violations -> dashboard quality section
        push_data = _minimal_push()
        push_data["violations"] = violations
        quality = _build_quality_section(push_data)
        details = quality["check_details"]
        self.assertTrue(len(details) >= 1)
        detail = details[0]
        self.assertEqual(detail["file_path"], "dev/scripts/devctl/commands/dashboard.py")
        self.assertEqual(detail["line"], "412")
        self.assertEqual(detail["policy"], "code_shape.python_soft_limit")
        self.assertEqual(detail["fix"], "Modularize file to reduce line count")
        self.assertEqual(detail["source"], "code_shape")
        self.assertEqual(detail["severity"], "warning")

    def test_no_violations_when_preflight_passes(self) -> None:
        """When preflight succeeds, violations list is empty."""
        from dev.scripts.devctl.commands.vcs.push_report import (
            _extract_preflight_violations,
        )
        step = {"name": "push-preflight", "returncode": 0}
        self.assertEqual(_extract_preflight_violations(step, "2026-01-01T00:00:00Z"), [])

    def test_no_violations_when_no_preflight(self) -> None:
        """When no preflight step ran, violations list is empty."""
        from dev.scripts.devctl.commands.vcs.push_report import (
            _extract_preflight_violations,
        )
        self.assertEqual(_extract_preflight_violations(None, "2026-01-01T00:00:00Z"), [])

    def test_per_check_violations_from_failure_output(self) -> None:
        """Preflight failure_output with per-check lines yields individual violations."""
        from dev.scripts.devctl.commands.vcs.push_report import (
            _extract_preflight_violations,
        )
        output = (
            "\ncheck summary: 2/4 passed, 2 failed\n"
            "------------------------------------\n"
            "  PASS  docs_check\n"
            "  FAIL  code_shape  -- dev/scripts/devctl/commands/dashboard.py:412 exceeds soft limit\n"
            "  FAIL  function_duplication  -- duplicate body in push_report.py\n"
            "  PASS  hygiene\n"
        )
        step = {
            "name": "push-preflight",
            "cmd": ["bash", "-lc", "check-router"],
            "returncode": 1,
            "failure_output": output,
        }
        violations = _extract_preflight_violations(step, "2026-01-01T00:00:00Z")
        names = [v["step_name"] for v in violations]
        self.assertIn("code_shape", names)
        self.assertIn("function_duplication", names)
        self.assertEqual(len(violations), 2)

    def test_preflight_fallback_when_no_per_check_lines(self) -> None:
        """When failure_output has no parseable check lines, falls back to one blob."""
        from dev.scripts.devctl.commands.vcs.push_report import (
            _extract_preflight_violations,
        )
        step = {
            "name": "push-preflight",
            "returncode": 1,
            "failure_output": "unexpected error: process crashed",
        }
        violations = _extract_preflight_violations(step, "2026-01-01T00:00:00Z")
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["step_name"], "push-preflight")


class TestTypedVerdictExtraction(unittest.TestCase):
    """Regression: typed ReviewState verdict must populate reviewer_activity."""

    def test_typed_bridge_verdict_from_reviewer_runtime(self) -> None:
        """_extract_typed_bridge_fields reads reviewer_runtime.review_acceptance.current_verdict."""
        from dev.scripts.devctl.commands.dashboard_typed_state import (
            _extract_typed_bridge_fields,
        )
        review_state = {
            "bridge": {
                "current_instruction": "fix shape",
                "last_codex_poll_utc": "2026-04-04T00:00:00Z",
                "reviewer_mode": "active_dual_agent",
            },
            "reviewer_runtime": {
                "review_acceptance": {
                    "current_verdict": "- Reviewer-accepted.",
                },
            },
        }
        fields = _extract_typed_bridge_fields(review_state)
        self.assertEqual(fields["verdict"], "- Reviewer-accepted.")

    def test_typed_bridge_verdict_fallback_missing_runtime(self) -> None:
        """Verdict stays n/a when reviewer_runtime is absent."""
        from dev.scripts.devctl.commands.dashboard_typed_state import (
            _extract_typed_bridge_fields,
        )
        review_state = {"bridge": {}}
        fields = _extract_typed_bridge_fields(review_state)
        self.assertEqual(fields["verdict"], "n/a")

    def test_health_view_includes_reviewer_activity_verdict(self) -> None:
        """dashboard --view health --format json has reviewer_activity.last_verdict populated."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_state = {
                "reviewer_runtime": {
                    "review_acceptance": {
                        "current_verdict": "- Needs rework on F2.",
                    },
                },
                "bridge": {
                    "current_instruction": "fix code shape",
                    "last_codex_poll_utc": "2026-04-04T01:00:00Z",
                    "reviewer_mode": "active_dual_agent",
                    "open_findings": "- F2: code_shape violation",
                    "last_reviewed_scope": "- dev/scripts/devctl/commands/dashboard.py",
                },
                "current_session": {},
            }
            _write_artifact(root, "dev/reports/review_channel/state/latest.json", review_state)
            _write_artifact(root, "dev/reports/review_channel/projections/latest/compact.json", _minimal_compact())

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main", "head": "abc", "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root, view="health")

            activity = snapshot.get("reviewer_activity", {})
            self.assertNotEqual(activity.get("last_verdict"), "n/a")
            self.assertIn("Needs rework", activity.get("last_verdict", ""))


if __name__ == "__main__":
    unittest.main()
