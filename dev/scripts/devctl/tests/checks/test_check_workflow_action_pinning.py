"""Tests for check_workflow_action_pinning guard script."""

import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.tests.checks.script_loader_support import (
    load_module_from_repo_path,
)

REPO_ROOT = Path(__file__).resolve().parents[5]


class CheckWorkflowActionPinningTests(unittest.TestCase):
    """Protect workflow action-pinning policy detection."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module_from_repo_path(
            module_name="check_workflow_action_pinning",
            repo_root=REPO_ROOT,
            relative_path="dev/scripts/checks/check_workflow_action_pinning.py",
        )

    def test_scan_file_flags_non_sha_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "sample.yml"
            workflow_file.write_text(
                "steps:\n"
                "  - uses: actions/checkout@v4\n"
                "  - uses: actions/setup-python@main\n",
                encoding="utf-8",
            )

            violations = self.script._scan_file(workflow_file)
            rules = [item["rule"] for item in violations]

            self.assertEqual(rules, ["non-sha-ref", "non-sha-ref"])

    def test_scan_file_skips_local_and_docker_uses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "sample.yml"
            workflow_file.write_text(
                "steps:\n"
                "  - uses: ./.github/actions/local\n"
                "  - uses: docker://alpine:3.20\n",
                encoding="utf-8",
            )

            violations = self.script._scan_file(workflow_file)
            self.assertEqual(violations, [])

    def test_scan_file_supports_rule_level_suppression(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_file = Path(tmpdir) / "sample.yml"
            workflow_file.write_text(
                "steps:\n"
                "  - uses: actions/checkout@v4 # workflow-action-pinning: allow=non-sha-ref\n"
                "  - uses: actions/setup-python@main\n",
                encoding="utf-8",
            )

            violations = self.script._scan_file(workflow_file)
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]["rule"], "non-sha-ref")

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

            self.assertEqual([path.name for path in discovered], ["a.yml", "b.yaml"])


if __name__ == "__main__":
    unittest.main()
