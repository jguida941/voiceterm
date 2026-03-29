"""Tests for markdown metadata header path collection."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.checks import check_markdown_metadata_header


class CollectMarkdownPathsTests(unittest.TestCase):
    """Ensure markdown path collection ignores directory matches."""

    def test_collect_markdown_paths_skips_directories_named_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir).resolve()
            docs_dir = repo_root / "docs"
            docs_dir.mkdir()
            markdown_file = docs_dir / "note.md"
            markdown_file.write_text("# Note\n", encoding="utf-8")
            bogus_dir = repo_root / "repo_example_temp" / ".md"
            bogus_dir.mkdir(parents=True)

            with patch.object(check_markdown_metadata_header, "REPO_ROOT", repo_root):
                paths = check_markdown_metadata_header._collect_markdown_paths(
                    ["."],
                    [],
                )

        self.assertEqual(paths, [markdown_file.resolve()])


if __name__ == "__main__":
    unittest.main()
