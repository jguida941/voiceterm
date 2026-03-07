"""Tests for workflow_shell_bridge workflow helper script."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


class WorkflowShellBridgeTests(unittest.TestCase):
    """Protect workflow-shell bridge behavior used by CI workflows."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "workflow_shell_bridge",
            "dev/scripts/workflow_shell_bridge.py",
        )

    def test_evaluate_user_docs_gate_runs_when_threshold_met(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            changed_files_input = tmp_root / "changed.txt"
            changed_files_input.write_text(
                "\n".join(
                    [
                        "README.md",
                        "QUICK_START.md",
                        "guides/USAGE.md",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            output = tmp_root / "github_output.txt"
            args = self.script.argparse.Namespace(
                changed_files_input=changed_files_input,
                github_output=output,
            )

            rc = self.script.evaluate_user_docs_gate(args)

            self.assertEqual(rc, 0)
            self.assertEqual(
                output.read_text(encoding="utf-8").splitlines(),
                [
                    "run_user_facing_strict=true",
                    "user_doc_change_count=3",
                    "cli_schema_changed=false",
                    "reason=user-doc-threshold",
                ],
            )

    def test_evaluate_user_docs_gate_runs_when_cli_schema_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            changed_files_input = tmp_root / "changed.txt"
            changed_files_input.write_text(
                "rust/src/bin/voiceterm/config/cli.rs\n",
                encoding="utf-8",
            )
            output = tmp_root / "github_output.txt"
            args = self.script.argparse.Namespace(
                changed_files_input=changed_files_input,
                github_output=output,
            )

            rc = self.script.evaluate_user_docs_gate(args)

            self.assertEqual(rc, 0)
            self.assertIn(
                "run_user_facing_strict=true", output.read_text(encoding="utf-8")
            )
            self.assertIn(
                "reason=cli-schema-change", output.read_text(encoding="utf-8")
            )

    def test_resolve_security_scope_zero_sha_is_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "github_output.txt"
            args = self.script.argparse.Namespace(
                event_name="push",
                push_before="0" * 40,
                push_head="abc123",
                pr_base="",
                pr_head="",
                github_output=output,
            )

            rc = self.script.resolve_security_scope(args)

            self.assertEqual(rc, 0)
            self.assertEqual(
                output.read_text(encoding="utf-8").splitlines(),
                [
                    "since_ref=",
                    "head_ref=abc123",
                ],
            )

    def test_prepare_failure_artifact_dir_slugifies_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            output = tmp_root / "github_output.txt"
            args = self.script.argparse.Namespace(
                workflow_name="Failure Triage!",
                run_id="123",
                run_attempt="2",
                root=tmp_root / "bundles",
                github_output=output,
            )

            rc = self.script.prepare_failure_artifact_dir(args)

            self.assertEqual(rc, 0)
            self.assertIn(
                "workflow_slug=failure-triage", output.read_text(encoding="utf-8")
            )
            self.assertIn(
                "artifact_dir="
                + (
                    tmp_root / "bundles" / "failure-triage" / "run-123-attempt-2"
                ).as_posix(),
                output.read_text(encoding="utf-8"),
            )

    def test_find_first_file_returns_sorted_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "artifacts"
            (root / "b").mkdir(parents=True)
            (root / "a").mkdir(parents=True)
            (root / "b" / "backlog-medium.json").write_text("{}", encoding="utf-8")
            (root / "a" / "backlog-medium.json").write_text("{}", encoding="utf-8")
            args = self.script.argparse.Namespace(
                search_root=root,
                pattern="backlog-medium.json",
                allow_missing=False,
                github_output=None,
                output_key=None,
            )

            with mock.patch("sys.stdout.write") as mock_stdout:
                rc = self.script.find_first_file(args)

            self.assertEqual(rc, 0)
            self.assertIn(
                (root / "a" / "backlog-medium.json").as_posix(),
                "".join(call.args[0] for call in mock_stdout.call_args_list),
            )

    def test_resolve_range_falls_back_to_head_when_refs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            changed_files_output = tmp_root / "changed.txt"
            github_output = tmp_root / "github_output.txt"
            args = self.script.argparse.Namespace(
                event_name="push",
                push_before="",
                push_head="deadbeef",
                pr_base="",
                pr_head="",
                changed_files_output=changed_files_output,
                github_output=github_output,
            )

            with mock.patch.object(self.script, "_git_ref_exists", return_value=False):
                with mock.patch.object(
                    self.script.subprocess,
                    "run",
                    return_value=self.script.subprocess.CompletedProcess(
                        args=[],
                        returncode=0,
                        stdout="README.md\nAGENTS.md\n",
                        stderr="",
                    ),
                ):
                    rc = self.script.resolve_range(args)

            self.assertEqual(rc, 0)
            self.assertEqual(
                changed_files_output.read_text(encoding="utf-8"),
                "README.md\nAGENTS.md\n",
            )
            self.assertIn("since=HEAD", github_output.read_text(encoding="utf-8"))
            self.assertIn("head=HEAD", github_output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
