from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.operator_console.help_render import render_operator_console_help
from app.operator_console.theme import available_theme_ids


class HelpRenderTests(unittest.TestCase):
    def test_help_uses_canonical_launcher_and_module_fallback(self) -> None:
        rendered = render_operator_console_help("codex", width=96, repo_root=Path("/tmp/repo"))

        self.assertIn("Usage: ./scripts/operator_console.sh [OPTIONS]", rendered)
        self.assertIn("Alt:   python3 -m app.operator_console.run [OPTIONS]", rendered)
        self.assertNotIn("python app/operator_console/run.py", rendered)

    def test_help_lists_all_registered_themes(self) -> None:
        rendered = render_operator_console_help("codex", width=96, repo_root=Path("/tmp/repo"))

        self.assertIn("Themes", rendered)
        self.assertIn("* codex", rendered)
        for theme_id in available_theme_ids():
            self.assertIn(theme_id, rendered)

    def test_help_includes_clickable_theme_and_resource_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            rendered = render_operator_console_help("codex", width=96, repo_root=repo_root)

        self.assertIn(
            "\x1b]8;;https://draculatheme.com\x1b\\[Site]\x1b]8;;\x1b\\",
            rendered,
        )
        self.assertIn((repo_root / "app/operator_console/README.md").as_uri(), rendered)
        self.assertIn((repo_root / "app/operator_console/AGENTS.md").as_uri(), rendered)
        self.assertIn((repo_root / "app/operator_console/state/README.md").as_uri(), rendered)
        self.assertIn((repo_root / "app/operator_console/views/README.md").as_uri(), rendered)
        self.assertIn((repo_root / "app/operator_console/theme/README.md").as_uri(), rendered)
        self.assertIn((repo_root / "app/operator_console/tests/README.md").as_uri(), rendered)
        self.assertIn((repo_root / "scripts/operator_console.sh").as_uri(), rendered)

    def test_none_theme_disables_color_codes_but_keeps_links(self) -> None:
        rendered = render_operator_console_help("none", width=96, repo_root=Path("/tmp/repo"))

        self.assertNotIn("\x1b[38;2;", rendered)
        self.assertIn("\x1b]8;;file:///tmp/repo/app/operator_console/README.md\x1b\\", rendered)


if __name__ == "__main__":
    unittest.main()
