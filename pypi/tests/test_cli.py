"""Unit tests for PyPI launcher bootstrap helpers."""

from __future__ import annotations

import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from voiceterm import cli


class BootstrapModeTests(unittest.TestCase):
    def test_default_mode_is_binary_only(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(cli._bootstrap_mode(), "binary-only")

    def test_invalid_mode_raises(self) -> None:
        with patch.dict(os.environ, {"VOICETERM_BOOTSTRAP_MODE": "nope"}, clear=True):
            with self.assertRaises(RuntimeError):
                cli._bootstrap_mode()


class PlatformTripletTests(unittest.TestCase):
    def test_linux_amd64_mapping(self) -> None:
        with patch("platform.system", return_value="Linux"), patch(
            "platform.machine", return_value="x86_64"
        ):
            self.assertEqual(cli._target_platform_triplet(), ("linux", "amd64"))

    def test_darwin_arm64_mapping(self) -> None:
        with patch("platform.system", return_value="Darwin"), patch(
            "platform.machine", return_value="arm64"
        ):
            self.assertEqual(cli._target_platform_triplet(), ("darwin", "arm64"))

    def test_unknown_platform_raises(self) -> None:
        with patch("platform.system", return_value="Plan9"), patch(
            "platform.machine", return_value="mips"
        ):
            with self.assertRaises(RuntimeError):
                cli._target_platform_triplet()


class ReleaseAssetTests(unittest.TestCase):
    def test_release_asset_names_follow_platform_triplet(self) -> None:
        with patch(
            "voiceterm.cli._target_platform_triplet", return_value=("linux", "amd64")
        ):
            archive, checksum = cli._release_asset_names("1.2.3")
        self.assertEqual(archive, "voiceterm-1.2.3-linux-amd64.tar.gz")
        self.assertEqual(checksum, "voiceterm-1.2.3-linux-amd64.tar.gz.sha256")

    def test_parse_checksum_file_accepts_standard_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset.sha256"
            path.write_text("a" * 64 + "  voiceterm-1.2.3-linux-amd64.tar.gz\n")
            self.assertEqual(cli._parse_checksum_file(path), "a" * 64)

    def test_install_binary_from_tarball_extracts_voiceterm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            binary_source = tmp_path / "voiceterm"
            binary_source.write_text("#!/bin/sh\necho hello\n")
            archive_path = tmp_path / "asset.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar_handle:
                tar_handle.add(binary_source, arcname="bin/voiceterm")
            destination = tmp_path / "native" / "bin" / "voiceterm"
            cli._install_binary_from_tarball(archive_path, destination)
            self.assertTrue(destination.exists())
            self.assertTrue(os.access(destination, os.X_OK))


class ResolveManifestDirTests(unittest.TestCase):
    def test_prefers_rust_workspace_path_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            rust = repo / "rust"
            src = repo / "src"
            rust.mkdir()
            src.mkdir()
            (rust / "Cargo.toml").write_text("[package]\nname='x'\nversion='0.1.0'\n")
            (src / "Cargo.toml").write_text("[package]\nname='y'\nversion='0.1.0'\n")
            self.assertEqual(cli._resolve_manifest_dir(repo), rust)

    def test_uses_legacy_src_path_when_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            src = repo / "src"
            src.mkdir(parents=True)
            (src / "Cargo.toml").write_text("[package]\nname='x'\nversion='0.1.0'\n")
            self.assertEqual(cli._resolve_manifest_dir(repo), src)

    def test_errors_when_no_manifest_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                cli._resolve_manifest_dir(Path(tmp))


if __name__ == "__main__":
    unittest.main()
