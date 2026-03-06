"""Tests for check_workflow_shell_hygiene guard script."""

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


class CheckWorkflowShellHygieneTests(unittest.TestCase):
    """Protect workflow-shell hygiene detection rules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "check_workflow_shell_hygiene",
            "dev/scripts/checks/check_workflow_shell_hygiene.py",
        )

    def test_scan_file_detects_find_pipe_head_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "sample.yml"
            workflow_file.write_text(
                "steps:\n  - run: OUTCOME=$(find out -name outcomes.json | head -n 1)\n",
                encoding="utf-8",
            )

            violations = self.script._scan_file(workflow_file)

            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]["rule"], "find-pipe-head")

    def test_scan_file_detects_inline_python_snippets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "sample.yml"
            workflow_file.write_text(
                "steps:\n"
                "  - run: python3 -c 'print(1)'\n"
                "  - run: python <<'PY'\n"
                "      print(2)\n"
                "    PY\n",
                encoding="utf-8",
            )

            violations = self.script._scan_file(workflow_file)
            rules = {item["rule"] for item in violations}

            self.assertIn("inline-python-c", rules)
            self.assertIn("inline-python-heredoc", rules)

    def test_scan_file_supports_rule_level_suppression(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "sample.yml"
            workflow_file.write_text(
                "steps:\n"
                "  - run: python3 -c 'print(1)' # workflow-shell-hygiene: allow=inline-python-c\n"
                "  - run: OUTCOME=$(find out -name outcomes.json | head -n 1)\n",
                encoding="utf-8",
            )

            violations = self.script._scan_file(workflow_file)
            rules = [item["rule"] for item in violations]

            self.assertEqual(rules, ["find-pipe-head"])

    def test_discover_paths_includes_yaml_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workflow_dir = root / ".github/workflows"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "a.yml").write_text("name: a\n", encoding="utf-8")
            (workflow_dir / "b.yaml").write_text("name: b\n", encoding="utf-8")
            original_root = self.script.REPO_ROOT
            self.addCleanup(setattr, self.script, "REPO_ROOT", original_root)
            self.script.REPO_ROOT = root

            discovered = self.script._discover_paths(None)

            self.assertEqual(
                [path.name for path in discovered],
                ["a.yml", "b.yaml"],
            )


if __name__ == "__main__":
    unittest.main()
