"""Tests for `devctl check` support helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl.commands import check_support


class ResolvePerfLogPathTests(TestCase):
    def test_resolve_perf_log_path_uses_tempdir(self) -> None:
        path = Path(check_support.resolve_perf_log_path())

        self.assertEqual(path.name, "voiceterm_tui.log")
        self.assertEqual(path.parent, Path(tempfile.gettempdir()))


if __name__ == "__main__":
    import unittest

    unittest.main()
