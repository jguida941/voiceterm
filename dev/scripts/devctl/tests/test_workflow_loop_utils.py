"""Tests for shared workflow loop GitHub helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from dev.scripts.checks import workflow_loop_utils


class WorkflowLoopUtilsTests(unittest.TestCase):
    @patch("dev.scripts.checks.workflow_loop_utils.run_capture")
    def test_gh_json_non_api_appends_repo(self, run_capture_mock) -> None:
        run_capture_mock.return_value = (0, "[]", "")
        payload, error = workflow_loop_utils.gh_json(
            "owner/repo",
            ["run", "list", "--limit", "1"],
        )

        self.assertIsNone(error)
        self.assertEqual(payload, [])
        command = run_capture_mock.call_args.args[0]
        self.assertIn("--repo", command)
        self.assertIn("owner/repo", command)

    @patch("dev.scripts.checks.workflow_loop_utils.run_capture")
    def test_gh_json_api_does_not_append_repo(self, run_capture_mock) -> None:
        run_capture_mock.return_value = (0, "[]", "")
        payload, error = workflow_loop_utils.gh_json(
            "owner/repo",
            ["api", "/repos/owner/repo/issues/1/comments"],
        )

        self.assertIsNone(error)
        self.assertEqual(payload, [])
        command = run_capture_mock.call_args.args[0]
        self.assertNotIn("--repo", command)


if __name__ == "__main__":
    unittest.main()
