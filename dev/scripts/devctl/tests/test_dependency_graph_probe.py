"""Tests for dependency_graph_probe workflow helper script."""

import importlib.util
import subprocess
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


class DependencyGraphProbeTests(unittest.TestCase):
    """Protect dependency graph probe behavior used by dependency_review workflow."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "dependency_graph_probe",
            "dev/scripts/dependency_graph_probe.py",
        )

    def test_probe_enabled_status_returns_true(self) -> None:
        def fake_runner(*_args, **_kwargs):
            return subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"security_and_analysis":{"dependency_graph":{"status":"enabled"}}}',
                stderr="",
            )

        enabled, stderr_lines = self.script.probe_dependency_graph_status(
            "owner/repo", runner=fake_runner
        )
        self.assertTrue(enabled)
        self.assertEqual(stderr_lines, [])

    def test_probe_non_enabled_status_returns_false(self) -> None:
        def fake_runner(*_args, **_kwargs):
            return subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"security_and_analysis":{"dependency_graph":{"status":"disabled"}}}',
                stderr="",
            )

        enabled, stderr_lines = self.script.probe_dependency_graph_status(
            "owner/repo", runner=fake_runner
        )
        self.assertFalse(enabled)
        self.assertEqual(stderr_lines, [])

    def test_probe_failure_returns_false_and_stderr_lines(self) -> None:
        def fake_runner(*_args, **_kwargs):
            return subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="first line\nsecond line\n",
            )

        enabled, stderr_lines = self.script.probe_dependency_graph_status(
            "owner/repo", runner=fake_runner
        )
        self.assertFalse(enabled)
        self.assertEqual(stderr_lines, ["first line", "second line"])

    def test_append_enabled_output_writes_lowercase_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "github_output.txt"
            self.script.append_enabled_output(output_path, True)
            self.script.append_enabled_output(output_path, False)
            self.assertEqual(
                output_path.read_text(encoding="utf-8").splitlines(),
                ["enabled=true", "enabled=false"],
            )


if __name__ == "__main__":
    unittest.main()
