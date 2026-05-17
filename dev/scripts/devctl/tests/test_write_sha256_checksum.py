"""Tests for sha256 checksum helper script."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def load_module(name: str, relative_path: str):
    """Load a repository script as a module for unit tests."""
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WriteSha256ChecksumTests(unittest.TestCase):
    """Protect release checksum sidecar file format."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.helper = load_module(
            "write_sha256_checksum",
            "dev/scripts/artifacts/sha256.py",
        )

    def test_write_checksum_file_uses_expected_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            artifact = tmp_root / "artifact.tar.gz"
            artifact.write_bytes(b"voiceterm-test")
            checksum = tmp_root / "artifact.tar.gz.sha256"

            self.helper.write_checksum_file(artifact, checksum)

            rendered = checksum.read_text(encoding="utf-8")
            digest = self.helper.compute_sha256(artifact)
            self.assertEqual(rendered, f"{digest}  artifact.tar.gz\n")


if __name__ == "__main__":
    unittest.main()
