"""Tests for `devctl governance-export` helpers and parser wiring."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl import cli, governance_export_support
from dev.scripts.devctl.commands.governance import export as governance_export


class GovernanceExportSupportTests(unittest.TestCase):
    def test_build_export_rejects_destination_inside_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "AGENTS.md").write_text("agents\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                governance_export_support.build_governance_export(
                    governance_export_support.GovernanceExportRequest(
                        export_base_dir=root / "exports",
                        snapshot_name="snapshot",
                        policy_path=None,
                        since_ref=None,
                        create_zip=False,
                    ),
                    repo_root=root,
                )

    def test_build_export_copies_sources_and_creates_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            export_root = Path(tmp_dir) / "exports"
            (repo_root / "AGENTS.md").parent.mkdir(parents=True, exist_ok=True)
            (repo_root / "AGENTS.md").write_text("agents\n", encoding="utf-8")
            (repo_root / "DEV_INDEX.md").write_text("index\n", encoding="utf-8")
            (repo_root / "dev" / "README.md").parent.mkdir(parents=True, exist_ok=True)
            (repo_root / "dev" / "README.md").write_text("dev\n", encoding="utf-8")
            (repo_root / "dev" / "active").mkdir(parents=True, exist_ok=True)
            (repo_root / "dev" / "active" / "portable_code_governance.md").write_text(
                "plan\n",
                encoding="utf-8",
            )
            (repo_root / "dev" / "config").mkdir(parents=True, exist_ok=True)
            (repo_root / "dev" / "guides").mkdir(parents=True, exist_ok=True)
            for relative in (
                "dev/guides/DEVELOPMENT.md",
                "dev/guides/MCP_DEVCTL_ALIGNMENT.md",
                "dev/guides/PORTABLE_CODE_GOVERNANCE.md",
                "dev/history/ENGINEERING_EVOLUTION.md",
                "dev/scripts/README.md",
                "dev/scripts/devctl.py",
            ):
                path = repo_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")
            (repo_root / "dev" / "scripts" / "checks").mkdir(parents=True, exist_ok=True)
            (repo_root / "dev" / "scripts" / "checks" / "probe_one.py").write_text(
                "print('ok')\n",
                encoding="utf-8",
            )
            (repo_root / "dev" / "scripts" / "devctl").mkdir(
                parents=True,
                exist_ok=True,
            )
            (repo_root / "dev" / "scripts" / "devctl" / "__init__.py").write_text(
                "\n",
                encoding="utf-8",
            )
            (repo_root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
            (repo_root / ".github" / "workflows" / "tooling.yml").write_text(
                "name: tooling\n",
                encoding="utf-8",
            )

            def _fake_generated_artifacts(**kwargs):
                output_dir = kwargs["snapshot_dir"] / "generated"
                output_dir.mkdir(parents=True, exist_ok=True)
                path = output_dir / "quality_policy.md"
                path.write_text("policy\n", encoding="utf-8")
                return {"quality_policy_md": str(path)}

            with patch.object(
                governance_export_support,
                "write_generated_artifacts",
                side_effect=_fake_generated_artifacts,
            ):
                result = governance_export_support.build_governance_export(
                    governance_export_support.GovernanceExportRequest(
                        export_base_dir=export_root,
                        snapshot_name="portable_demo",
                        policy_path=None,
                        since_ref=None,
                        create_zip=True,
                    ),
                    repo_root=repo_root,
                )

            snapshot_dir = Path(result.snapshot_dir)
            self.assertTrue((snapshot_dir / "AGENTS.md").exists())
            self.assertTrue(
                (snapshot_dir / "dev" / "scripts" / "checks" / "probe_one.py").exists()
            )
            self.assertTrue(
                (snapshot_dir / "generated" / "snapshot_manifest.json").exists()
            )
            self.assertTrue(result.zip_path is not None)
            self.assertTrue(Path(str(result.zip_path)).exists())


class GovernanceExportCommandTests(unittest.TestCase):
    def test_cli_parser_accepts_governance_export_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "governance-export",
                "--quality-policy",
                "/tmp/policy.json",
                "--export-base-dir",
                "/tmp/exports",
                "--snapshot-name",
                "portable-demo",
                "--since-ref",
                "origin/develop",
                "--head-ref",
                "HEAD~1",
                "--no-zip",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "governance-export")
        self.assertEqual(args.quality_policy, "/tmp/policy.json")
        self.assertEqual(args.export_base_dir, "/tmp/exports")
        self.assertEqual(args.snapshot_name, "portable-demo")
        self.assertEqual(args.since_ref, "origin/develop")
        self.assertEqual(args.head_ref, "HEAD~1")
        self.assertFalse(args.adoption_scan)
        self.assertTrue(args.no_zip)
        self.assertIs(cli.COMMAND_HANDLERS["governance-export"], governance_export.run)

    def test_command_writes_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "export.json"
            with patch(
                "dev.scripts.devctl.commands.governance.export.build_governance_export"
            ) as mock_export:
                mock_export.return_value = governance_export_support.GovernanceExportResult(
                    snapshot_dir="/tmp/snapshot",
                    zip_path="/tmp/snapshot.zip",
                    copied_sources=("AGENTS.md",),
                    generated_artifacts={"quality_policy_md": "/tmp/quality.md"},
                    policy_path="/tmp/policy.json",
                    created_at_utc="2026-03-11T00:00:00Z",
                )
                args = cli.build_parser().parse_args(
                    [
                        "governance-export",
                        "--format",
                        "json",
                        "--output",
                        str(output_path),
                    ]
                )

                rc = governance_export.run(args)
                payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(payload["command"], "governance-export")
        self.assertEqual(payload["snapshot_dir"], "/tmp/snapshot")
        self.assertEqual(
            payload["generated_artifacts"]["quality_policy_md"],
            "/tmp/quality.md",
        )

    def test_command_rejects_conflicting_scan_modes(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "governance-export",
                "--since-ref",
                "origin/develop",
                "--adoption-scan",
            ]
        )

        rc = governance_export.run(args)

        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
