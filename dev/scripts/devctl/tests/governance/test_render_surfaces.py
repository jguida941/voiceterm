"""Tests for repo-pack surface generation command and policy helpers."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.checks.package_layout import instruction_surface_sync
from dev.scripts.devctl import cli
from dev.scripts.devctl.commands import listing
from dev.scripts.devctl.commands.governance import render_surfaces
from dev.scripts.devctl.governance import surface_runtime, surfaces


class RenderSurfacesParserTests(unittest.TestCase):
    def test_cli_accepts_render_surfaces_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "render-surfaces",
                "--surface",
                "codex_voice_slash",
                "--surface",
                "portable_tooling_workflow_stub",
                "--write",
                "--quality-policy",
                "/tmp/pilot-policy.json",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "render-surfaces")
        self.assertEqual(
            args.surface,
            ["codex_voice_slash", "portable_tooling_workflow_stub"],
        )
        self.assertTrue(args.write)
        self.assertEqual(args.quality_policy, "/tmp/pilot-policy.json")
        self.assertEqual(args.format, "json")

    def test_command_handler_and_listing_are_registered(self) -> None:
        self.assertIs(cli.COMMAND_HANDLERS["render-surfaces"], render_surfaces.run)
        self.assertIn("render-surfaces", listing.COMMANDS)


class RenderSurfacesPolicyTests(unittest.TestCase):
    def test_repo_policy_surface_report_is_in_sync(self) -> None:
        report = surfaces.build_surface_report(allow_missing_local_only=True)

        self.assertTrue(report["ok"])
        self.assertEqual(report["surface_count"], 6)
        self.assertIn(
            "agents_bundle_reference",
            {entry["surface_id"] for entry in report["surfaces"]},
        )

    def test_instruction_surface_guard_ignores_agents_bundle_surface(self) -> None:
        report = instruction_surface_sync.build_report()

        self.assertTrue(report["ok"])
        self.assertEqual(report["surface_count"], 5)
        self.assertNotIn(
            "agents_bundle_reference",
            {entry["surface_id"] for entry in report["surfaces"]},
        )

    def test_claude_surface_renders_blocking_post_edit_verification(self) -> None:
        policy = surfaces.load_surface_policy()
        claude_surface = next(
            entry for entry in policy.surfaces if entry.surface_id == "claude_instructions"
        )
        template_text = Path(claude_surface.template_path).read_text(encoding="utf-8")
        rendered_text, missing_context = surface_runtime._render_template_text(
            template_text,
            policy.context,
        )

        self.assertEqual(missing_context, [])
        for required_snippet in claude_surface.required_contains:
            self.assertIn(required_snippet, rendered_text)
        self.assertIn(
            "`bundle.runtime`, `bundle.docs`, `bundle.tooling`, or `bundle.release`",
            rendered_text,
        )
        self.assertIn(
            "python3 dev/scripts/devctl.py check --profile ci",
            rendered_text,
        )
        self.assertIn(
            "## Mode-aware review-channel bootstrap",
            rendered_text,
        )
        self.assertIn(
            "review-channel --action status --terminal none --format json",
            rendered_text,
        )
        self.assertIn(
            "If reviewer-owned bridge state says `hold steady`, `waiting for reviewer promotion`,",
            rendered_text,
        )
        self.assertIn(
            "On each repoll, read `Last Codex poll` / `Poll Status` first.",
            rendered_text,
        )


class RenderSurfacesCliIntegrationTests(unittest.TestCase):
    @patch("dev.scripts.devctl.cli.maybe_auto_refresh_data_science")
    @patch("dev.scripts.devctl.cli.emit_devctl_audit_event")
    @patch("dev.scripts.devctl.commands.governance.render_surfaces.build_surface_report")
    def test_cli_main_dispatches_moved_handler_and_writes_json_output(
        self,
        build_report_mock,
        emit_audit_mock,
        refresh_mock,
    ) -> None:
        build_report_mock.return_value = {
            "command": "render-surfaces",
            "ok": True,
            "policy_path": "dev/config/devctl_repo_policy.json",
            "repo_pack_id": "codex-voice",
            "repo_pack_version": "1.0.0",
            "product_name": "VoiceTerm",
            "repo_name": "codex-voice",
            "surface_count": 1,
            "warnings": [],
            "surfaces": [
                {
                    "surface_id": "codex_voice_slash",
                    "surface_type": "instruction",
                    "renderer": "template_file",
                    "output_path": "dev/templates/slash/codex/voice.md",
                    "template_path": "dev/config/templates/codex_voice_slash.template.md",
                    "description": "Codex slash-command surface",
                    "tracked": True,
                    "local_only": False,
                    "ok": True,
                    "state": "in-sync",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "render-surfaces.json"
            argv = [
                "devctl",
                "render-surfaces",
                "--surface",
                "codex_voice_slash",
                "--quality-policy",
                "/tmp/pilot-policy.json",
                "--format",
                "json",
                "--output",
                str(output_path),
            ]
            with (
                patch("sys.argv", argv),
                patch("sys.stdout", new_callable=io.StringIO),
                patch("sys.stderr", new_callable=io.StringIO),
            ):
                rc = cli.main()
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        build_report_mock.assert_called_once_with(
            surface_ids=("codex_voice_slash",),
            policy_path="/tmp/pilot-policy.json",
            write=False,
            allow_missing_local_only=True,
        )
        self.assertEqual(payload["command"], "render-surfaces")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["surface_count"], 1)
        self.assertEqual(payload["surfaces"][0]["surface_id"], "codex_voice_slash")
        emit_audit_mock.assert_called_once()
        refresh_mock.assert_called_once_with(command="render-surfaces")


if __name__ == "__main__":
    unittest.main()
