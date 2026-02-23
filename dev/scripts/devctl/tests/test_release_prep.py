"""Tests for release metadata preparation helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.commands import release_prep


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ReleasePrepTests(TestCase):
    def _seed_repo_tree(self, root: Path) -> None:
        _write(
            root / "src/Cargo.toml",
            '[package]\nname = "voiceterm"\nversion = "1.0.90"\nedition = "2021"\n',
        )
        _write(
            root / "pypi/pyproject.toml",
            '[project]\nname = "voiceterm"\nversion = "1.0.90"\n',
        )
        _write(root / "pypi/src/voiceterm/__init__.py", '__version__ = "1.0.90"\n')
        _write(
            root / "app/macos/VoiceTerm.app/Contents/Info.plist",
            (
                "<plist>\n"
                "<dict>\n"
                "<key>CFBundleShortVersionString</key>\n"
                "<string>1.0.90</string>\n"
                "<key>CFBundleVersion</key>\n"
                "<string>1.0.90</string>\n"
                "</dict>\n"
                "</plist>\n"
            ),
        )
        _write(
            root / "dev/CHANGELOG.md",
            "# Changelog\n\n## [Unreleased]\n\n### UX\n\n- demo entry\n",
        )
        _write(
            root / "dev/active/MASTER_PLAN.md",
            (
                "# Master Plan (Active, Unified)\n\n"
                "## Status Snapshot (2026-02-23)\n\n"
                "- Last tagged release: `v1.0.90` (2026-02-23)\n"
                "- Current release target: `post-v1.0.90 planning`\n"
                "- Active development branch: `develop`\n"
                "- Release branch: `master`\n"
            ),
        )

    def test_prepare_release_metadata_dry_run_reports_changes_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self._seed_repo_tree(root)
            original_changelog = (root / "dev/CHANGELOG.md").read_text(encoding="utf-8")

            with patch("dev.scripts.devctl.commands.release_prep.REPO_ROOT", root):
                report = release_prep.prepare_release_metadata(
                    "1.0.91",
                    release_date="2026-02-23",
                    dry_run=True,
                )

            self.assertTrue(report["dry_run"])
            self.assertEqual(len(report["changed_files"]), 6)
            self.assertEqual(
                (root / "dev/CHANGELOG.md").read_text(encoding="utf-8"),
                original_changelog,
            )

    def test_prepare_release_metadata_writes_versions_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self._seed_repo_tree(root)

            with patch("dev.scripts.devctl.commands.release_prep.REPO_ROOT", root):
                first = release_prep.prepare_release_metadata(
                    "1.0.91",
                    release_date="2026-02-23",
                    dry_run=False,
                )
                second = release_prep.prepare_release_metadata(
                    "1.0.91",
                    release_date="2026-02-23",
                    dry_run=False,
                )

            self.assertEqual(len(first["changed_files"]), 6)
            self.assertEqual(second["changed_files"], [])
            self.assertIn("src/Cargo.toml", second["unchanged_files"])

            changelog = (root / "dev/CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("## [Unreleased]", changelog)
            self.assertIn("## [1.0.91] - 2026-02-23", changelog)
            self.assertEqual(changelog.count("## [1.0.91]"), 1)

            init_py = (root / "pypi/src/voiceterm/__init__.py").read_text(encoding="utf-8")
            self.assertIn('__version__ = "1.0.91"', init_py)

            master_plan = (root / "dev/active/MASTER_PLAN.md").read_text(encoding="utf-8")
            self.assertIn("## Status Snapshot (2026-02-23)", master_plan)
            self.assertIn("- Last tagged release: `v1.0.91` (2026-02-23)", master_plan)
            self.assertIn("- Current release target: `post-v1.0.91 planning`", master_plan)
