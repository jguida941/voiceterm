"""Tests for devctl shared path configuration."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dev.scripts.devctl.config import resolve_src_dir


class ConfigPathTests(unittest.TestCase):
    def test_resolve_src_dir_prefers_rust_workspace(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            rust_dir = repo_root / "rust"
            legacy_src_dir = repo_root / "src"
            rust_dir.mkdir(parents=True)
            legacy_src_dir.mkdir(parents=True)
            (rust_dir / "Cargo.toml").write_text("[package]\nname='x'\nversion='0.1.0'\n")
            (legacy_src_dir / "Cargo.toml").write_text(
                "[package]\nname='legacy'\nversion='0.1.0'\n"
            )

            resolved = resolve_src_dir(repo_root)
            self.assertEqual(resolved, rust_dir)

    def test_resolve_src_dir_falls_back_to_legacy_src_workspace(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            legacy_src_dir = repo_root / "src"
            legacy_src_dir.mkdir(parents=True)
            (legacy_src_dir / "Cargo.toml").write_text(
                "[package]\nname='legacy'\nversion='0.1.0'\n"
            )

            resolved = resolve_src_dir(repo_root)
            self.assertEqual(resolved, legacy_src_dir)

    def test_resolve_src_dir_defaults_to_rust_layout(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            resolved = resolve_src_dir(repo_root)
            self.assertEqual(resolved, repo_root / "rust")


if __name__ == "__main__":
    unittest.main()
