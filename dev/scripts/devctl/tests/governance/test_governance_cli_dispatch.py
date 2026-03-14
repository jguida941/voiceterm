"""Dispatch-level CLI stability tests for governance package commands."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl import cli, governance_bootstrap_support, governance_export_support


class GovernanceCliDispatchTests(unittest.TestCase):
    def _parse_args(self, *argv: str) -> tuple[object, Path]:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        output_path = Path(tempdir.name) / "output.json"
        args = cli.build_parser().parse_args(
            [*argv, "--format", "json", "--output", str(output_path)]
        )
        return args, output_path

    def test_governance_bootstrap_dispatch_emits_machine_output(self) -> None:
        args, output_path = self._parse_args(
            "governance-bootstrap",
            "--target-repo",
            "/tmp/portable-pilot",
        )
        result = governance_bootstrap_support.GovernanceBootstrapResult(
            target_repo="/tmp/portable-pilot",
            git_state="valid",
            repaired_git_file=False,
            initialized_git_repo=False,
            broken_gitdir_hint=None,
            starter_policy_path="/tmp/portable-pilot/dev/config/devctl_repo_policy.json",
            starter_policy_written=True,
            starter_policy_preset="portable_python",
            starter_policy_warnings=(),
            starter_setup_guide_path="/tmp/portable-pilot/dev/guides/PORTABLE_GOVERNANCE_SETUP.md",
            starter_setup_guide_written=True,
            next_steps=("python3 dev/scripts/devctl.py render-surfaces --write --format json",),
            created_at_utc="2026-03-13T00:00:00Z",
        )

        with patch(
            "dev.scripts.devctl.commands.governance.bootstrap.bootstrap_governance_pilot_repo",
            return_value=result,
        ):
            rc = cli.COMMAND_HANDLERS[args.command](args)

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(rc, 0)
        self.assertEqual(payload["command"], "governance-bootstrap")
        self.assertEqual(payload["target_repo"], "/tmp/portable-pilot")

    def test_governance_export_dispatch_emits_machine_output(self) -> None:
        args, output_path = self._parse_args("governance-export")
        result = governance_export_support.GovernanceExportResult(
            snapshot_dir="/tmp/snapshot",
            zip_path="/tmp/snapshot.zip",
            copied_sources=("AGENTS.md",),
            generated_artifacts={"quality_policy_md": "/tmp/quality.md"},
            policy_path="/tmp/policy.json",
            created_at_utc="2026-03-13T00:00:00Z",
        )

        with patch(
            "dev.scripts.devctl.commands.governance.export.build_governance_export",
            return_value=result,
        ):
            rc = cli.COMMAND_HANDLERS[args.command](args)

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(rc, 0)
        self.assertEqual(payload["command"], "governance-export")
        self.assertEqual(payload["snapshot_dir"], "/tmp/snapshot")

    def test_governance_review_dispatch_emits_machine_output(self) -> None:
        args, output_path = self._parse_args("governance-review")
        report = {
            "ok": True,
            "stats": {"total_rows": 2, "fixed_count": 1},
            "recent_findings": [{"finding_id": "finding-1", "verdict": "fixed"}],
        }

        with patch(
            "dev.scripts.devctl.commands.governance.review.resolve_governance_review_log_path",
            return_value=Path("/tmp/reviews.jsonl"),
        ), patch(
            "dev.scripts.devctl.commands.governance.review.resolve_governance_review_summary_root",
            return_value=Path("/tmp/review-summary"),
        ), patch(
            "dev.scripts.devctl.commands.governance.review.build_governance_review_report",
            return_value=report,
        ), patch(
            "dev.scripts.devctl.commands.governance.review.write_governance_review_summary",
            return_value={"json": "/tmp/review-summary/review_summary.json"},
        ):
            rc = cli.COMMAND_HANDLERS[args.command](args)

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(rc, 0)
        self.assertEqual(payload["command"], "governance-review")
        self.assertEqual(payload["stats"]["fixed_count"], 1)

    def test_render_surfaces_dispatch_emits_machine_output(self) -> None:
        args, output_path = self._parse_args(
            "render-surfaces",
            "--surface",
            "claude_instructions",
        )
        report = {
            "ok": True,
            "surface_count": 1,
            "surfaces": [{"surface_id": "claude_instructions"}],
        }

        with patch(
            "dev.scripts.devctl.commands.governance.render_surfaces.build_surface_report",
            return_value=report,
        ):
            rc = cli.COMMAND_HANDLERS[args.command](args)

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(rc, 0)
        self.assertEqual(payload["command"], "render-surfaces")
        self.assertEqual(payload["surface_count"], 1)


if __name__ == "__main__":
    unittest.main()
