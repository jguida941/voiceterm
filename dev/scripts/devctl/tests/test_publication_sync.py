"""Tests for publication-sync helpers and command wiring."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.publication_sync import core as publication_sync_helpers
from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import publication_sync
from dev.scripts.devctl.commands import hygiene_audits


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _commit_all(root: Path, message: str) -> None:
    _git(root, "add", ".")
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test User",
            "commit",
            "-m",
            message,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


def _write_registry(root: Path, *, source_ref: str, watched_paths: list[str]) -> Path:
    registry_path = root / "dev/config/publication_sync_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "publications": [
                    {
                        "id": "paper-site",
                        "title": "Paper Site",
                        "public_url": "https://example.test/paper",
                        "external_repo": "https://github.com/example/paper.git",
                        "external_branch": "main",
                        "source_ref": source_ref,
                        "watched_paths": watched_paths,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return registry_path


class PublicationSyncParserTests(unittest.TestCase):
    def test_cli_accepts_publication_sync_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "publication-sync",
                "--publication",
                "paper-site",
                "--head-ref",
                "HEAD~1",
                "--fail-on-stale",
                "--record-source-ref",
                "HEAD",
                "--record-external-ref",
                "abc1234",
                "--record-synced-at",
                "2026-03-07T00:00:00Z",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "publication-sync")
        self.assertEqual(args.publication, "paper-site")
        self.assertEqual(args.head_ref, "HEAD~1")
        self.assertTrue(args.fail_on_stale)
        self.assertEqual(args.record_source_ref, "HEAD")
        self.assertEqual(args.record_external_ref, "abc1234")
        self.assertEqual(args.record_synced_at, "2026-03-07T00:00:00Z")
        self.assertEqual(args.format, "json")


class PublicationSyncHelperTests(unittest.TestCase):
    def test_build_report_detects_stale_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _git(root, "init")
            (root / "AGENTS.md").write_text("initial\n", encoding="utf-8")
            _commit_all(root, "initial")
            source_ref = _git(root, "rev-parse", "HEAD")

            (root / "AGENTS.md").write_text("updated\n", encoding="utf-8")
            _commit_all(root, "update-agents")
            registry_path = _write_registry(
                root,
                source_ref=source_ref,
                watched_paths=["AGENTS.md"],
            )

            report = publication_sync_helpers.build_publication_sync_report(
                repo_root=root,
                registry_path=registry_path,
            )

            self.assertFalse(report["ok"])
            self.assertEqual(report["stale_publication_count"], 1)
            self.assertEqual(report["publication_count"], 1)
            self.assertEqual(report["publications"][0]["impacted_paths"], ["AGENTS.md"])

    def test_build_report_detects_dirty_worktree_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _git(root, "init")
            (root / "AGENTS.md").write_text("initial\n", encoding="utf-8")
            _commit_all(root, "initial")
            source_ref = _git(root, "rev-parse", "HEAD")

            # Registry points to current HEAD — no committed drift
            registry_path = _write_registry(
                root,
                source_ref=source_ref,
                watched_paths=["AGENTS.md"],
            )
            _commit_all(root, "add-registry")

            # Dirty the watched file without committing
            (root / "AGENTS.md").write_text("dirty edit\n", encoding="utf-8")

            report = publication_sync_helpers.build_publication_sync_report(
                repo_root=root,
                registry_path=registry_path,
            )

            self.assertFalse(report["ok"])
            self.assertEqual(report["stale_publication_count"], 1)
            pub = report["publications"][0]
            self.assertTrue(pub["stale"])
            self.assertIn("AGENTS.md", pub["impacted_paths"])
            self.assertIn("AGENTS.md", pub["dirty_impacted_paths"])

    def test_build_report_detects_untracked_file_under_watched_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _git(root, "init")
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "index.md").write_text("initial\n", encoding="utf-8")
            _commit_all(root, "initial")
            source_ref = _git(root, "rev-parse", "HEAD")

            registry_path = _write_registry(
                root,
                source_ref=source_ref,
                watched_paths=["docs"],
            )
            _commit_all(root, "add-registry")

            # Create an untracked file under the watched directory
            (docs_dir / "new.md").write_text("brand new\n", encoding="utf-8")

            report = publication_sync_helpers.build_publication_sync_report(
                repo_root=root,
                registry_path=registry_path,
            )

            self.assertFalse(report["ok"])
            self.assertEqual(report["stale_publication_count"], 1)
            pub = report["publications"][0]
            self.assertTrue(pub["stale"])
            self.assertIn("docs/new.md", pub["impacted_paths"])
            self.assertIn("docs/new.md", pub["dirty_impacted_paths"])

    def test_record_publication_sync_updates_source_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _git(root, "init")
            (root / "AGENTS.md").write_text("initial\n", encoding="utf-8")
            _commit_all(root, "initial")
            old_ref = _git(root, "rev-parse", "HEAD")

            (root / "AGENTS.md").write_text("updated\n", encoding="utf-8")
            _commit_all(root, "update-agents")
            head_ref = _git(root, "rev-parse", "HEAD")
            registry_path = _write_registry(
                root,
                source_ref=old_ref,
                watched_paths=["AGENTS.md"],
            )

            record = publication_sync_helpers.record_publication_sync(
                publication_id="paper-site",
                source_ref="HEAD",
                external_ref="site-commit-123",
                repo_root=root,
                registry_path=registry_path,
            )
            report = publication_sync_helpers.build_publication_sync_report(
                repo_root=root,
                registry_path=registry_path,
            )

            self.assertEqual(record["source_ref"], head_ref)
            self.assertEqual(record["external_ref"], "site-commit-123")
            self.assertTrue(report["ok"])
            self.assertEqual(report["stale_publication_count"], 0)

    def test_hygiene_audit_warns_when_publication_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _git(root, "init")
            (root / "AGENTS.md").write_text("initial\n", encoding="utf-8")
            _commit_all(root, "initial")
            source_ref = _git(root, "rev-parse", "HEAD")

            (root / "AGENTS.md").write_text("updated\n", encoding="utf-8")
            _commit_all(root, "update-agents")
            _write_registry(
                root,
                source_ref=source_ref,
                watched_paths=["AGENTS.md"],
            )

            report = hygiene_audits.audit_publication_sync(root)

            self.assertEqual(report["publication_count"], 1)
            self.assertEqual(report["stale_publication_count"], 1)
            self.assertFalse(report["warnings"])
            self.assertTrue(report["notices"])
            self.assertIn("Publication drift detected", report["notices"][0])


class PublicationSyncCommandTests(unittest.TestCase):
    def _args(self, **overrides) -> SimpleNamespace:
        base = {
            "publication": None,
            "registry_path": "dev/config/publication_sync_registry.json",
            "head_ref": "HEAD",
            "fail_on_stale": False,
            "record_source_ref": None,
            "record_external_ref": None,
            "record_synced_at": None,
            "format": "json",
            "output": None,
            "pipe_command": None,
            "pipe_args": None,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @patch("dev.scripts.devctl.commands.publication_sync.write_output")
    @patch("dev.scripts.devctl.commands.publication_sync.build_publication_sync_report")
    def test_command_returns_zero_for_stale_report_when_not_blocking(
        self,
        build_report_mock,
        write_output_mock,
    ) -> None:
        build_report_mock.return_value = {
            "ok": False,
            "registry_path": "dev/config/publication_sync_registry.json",
            "schema_version": 1,
            "head_ref": "HEAD",
            "resolved_head_ref": "abc123",
            "publication_filter": None,
            "publication_count": 1,
            "stale_publication_count": 1,
            "error_count": 0,
            "errors": [],
            "publications": [
                {
                    "id": "paper-site",
                    "title": "Paper Site",
                    "public_url": "https://example.test/paper",
                    "external_repo": "https://github.com/example/paper.git",
                    "external_branch": "main",
                    "watched_paths": ["AGENTS.md"],
                    "changed_path_count": 1,
                    "impacted_path_count": 1,
                    "source_ref": "old",
                    "resolved_source_ref": "old",
                    "external_ref": "",
                    "last_synced_at": "",
                    "notes": "",
                    "errors": [],
                    "impacted_paths": ["AGENTS.md"],
                    "stale": True,
                }
            ],
        }

        rc = publication_sync.run(self._args(fail_on_stale=False))

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["exit_ok"])

    @patch("dev.scripts.devctl.commands.publication_sync.write_output")
    @patch("dev.scripts.devctl.commands.publication_sync.record_publication_sync")
    @patch("dev.scripts.devctl.commands.publication_sync.build_publication_sync_report")
    def test_command_records_sync_before_rendering_report(
        self,
        build_report_mock,
        record_mock,
        write_output_mock,
    ) -> None:
        record_mock.return_value = {
            "publication": "paper-site",
            "source_ref": "new-head",
            "external_ref": "site-commit",
            "last_synced_at": "2026-03-07T00:00:00Z",
            "registry_path": "dev/config/publication_sync_registry.json",
        }
        build_report_mock.return_value = {
            "ok": True,
            "registry_path": "dev/config/publication_sync_registry.json",
            "schema_version": 1,
            "head_ref": "HEAD",
            "resolved_head_ref": "new-head",
            "publication_filter": "paper-site",
            "publication_count": 1,
            "stale_publication_count": 0,
            "error_count": 0,
            "errors": [],
            "publications": [
                {
                    "id": "paper-site",
                    "title": "Paper Site",
                    "public_url": "https://example.test/paper",
                    "external_repo": "https://github.com/example/paper.git",
                    "external_branch": "main",
                    "watched_paths": ["AGENTS.md"],
                    "changed_path_count": 0,
                    "impacted_path_count": 0,
                    "source_ref": "new-head",
                    "resolved_source_ref": "new-head",
                    "external_ref": "site-commit",
                    "last_synced_at": "2026-03-07T00:00:00Z",
                    "notes": "",
                    "errors": [],
                    "impacted_paths": [],
                    "stale": False,
                }
            ],
        }

        rc = publication_sync.run(
            self._args(
                publication="paper-site",
                record_source_ref="HEAD",
                record_external_ref="site-commit",
            )
        )

        self.assertEqual(rc, 0)
        record_mock.assert_called_once()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["record_update"]["publication"], "paper-site")


if __name__ == "__main__":
    unittest.main()
