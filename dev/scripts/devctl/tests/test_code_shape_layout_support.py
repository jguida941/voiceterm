"""Tests for code-shape namespace layout guard support."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import init_temp_repo_root, load_repo_module

SCRIPT = load_repo_module(
    "code_shape_layout_support",
    "dev/scripts/checks/code_shape_layout_support.py",
)


class CodeShapeLayoutSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_temp_repo_root(
            self,
            "dev/scripts/devctl",
            "dev/scripts/devctl/review_channel",
            "dev/scripts",
            "dev/guides",
            "dev/active",
        )
        self._write("AGENTS.md", "# Agents\n")
        self._write("dev/scripts/README.md", "# Scripts\n")
        self._write("dev/guides/DEVELOPMENT.md", "# Development\n")
        self._write("dev/active/MASTER_PLAN.md", "# Master Plan\n")

    def _write(self, relative_path: str, text: str = "pass\n") -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_flags_new_flat_file_for_crowded_review_channel_family(self) -> None:
        for idx in range(8):
            self._write(f"dev/scripts/devctl/review_channel_{idx}.py")
        self._write("dev/scripts/devctl/review_channel_new.py")

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del path
            del ref
            return None

        violations, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel_new.py")],
            read_text_from_ref=_read_text_from_ref,
            since_ref=None,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["reason"],
            "new_flat_namespace_module_in_crowded_family",
        )
        self.assertIn("dev/scripts/devctl/review_channel", violations[0]["guidance"])

    def test_ignores_existing_flat_file_modification(self) -> None:
        for idx in range(8):
            self._write(f"dev/scripts/devctl/review_channel_{idx}.py")

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del ref
            if path.as_posix() == "dev/scripts/devctl/review_channel_2.py":
                return "existing content\n"
            return None

        violations, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel_2.py")],
            read_text_from_ref=_read_text_from_ref,
            since_ref=None,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(violations, [])

    def test_ignores_files_already_under_namespace_directory(self) -> None:
        for idx in range(8):
            self._write(f"dev/scripts/devctl/review_channel_{idx}.py")
        self._write("dev/scripts/devctl/review_channel/new_parser.py")

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del path
            del ref
            return None

        violations, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel/new_parser.py")],
            read_text_from_ref=_read_text_from_ref,
            since_ref="origin/develop",
        )

        self.assertEqual(scanned, 0)
        self.assertEqual(violations, [])

    def test_flags_docs_sync_when_new_namespace_path_lacks_doc_token(self) -> None:
        self._write("dev/scripts/devctl/review_channel/new_lane.py")

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del path
            del ref
            return None

        violations, scanned = SCRIPT.collect_namespace_docs_sync_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel/new_lane.py")],
            read_text_from_ref=_read_text_from_ref,
            read_text_from_worktree=lambda path: (self.root / path).read_text(
                encoding="utf-8"
            ),
            since_ref=None,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["reason"], "new_namespace_path_missing_docs_reference"
        )

    def test_docs_sync_passes_when_required_token_is_documented(self) -> None:
        self._write(
            "dev/scripts/README.md",
            "# Scripts\n\n- Namespace: `dev/scripts/devctl/review_channel`\n",
        )
        self._write("dev/scripts/devctl/review_channel/new_lane.py")

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del path
            del ref
            return None

        violations, scanned = SCRIPT.collect_namespace_docs_sync_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel/new_lane.py")],
            read_text_from_ref=_read_text_from_ref,
            read_text_from_worktree=lambda path: (self.root / path).read_text(
                encoding="utf-8"
            ),
            since_ref=None,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
