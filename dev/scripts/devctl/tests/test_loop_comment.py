"""Tests for shared loop comment upsert helpers."""

from __future__ import annotations

import unittest
from typing import Any

from dev.scripts.devctl.loop_comment import upsert_comment


class LoopCommentUpsertTests(unittest.TestCase):
    def test_upsert_create_commit_comment_does_not_use_repo_flag(self) -> None:
        captured_cmds: list[list[str]] = []

        def fake_gh_json(_repo: str, _cmd: list[str]) -> tuple[Any | None, str | None]:
            return [], None

        def fake_run_capture(cmd: list[str]) -> tuple[int, str, str]:
            captured_cmds.append(cmd)
            return 0, '{"id": 101, "html_url": "https://example.invalid/c/101"}', ""

        payload, error = upsert_comment(
            "owner/repo",
            {"kind": "commit", "id": "abc123"},
            marker="marker",
            body="body",
            gh_json_fn=fake_gh_json,
            run_capture_fn=fake_run_capture,
        )

        self.assertIsNone(error)
        self.assertEqual(payload.get("action"), "created")
        self.assertEqual(len(captured_cmds), 1)
        command = captured_cmds[0]
        self.assertNotIn("--repo", command)
        self.assertIn("/repos/owner/repo/commits/abc123/comments", command)

    def test_upsert_update_pr_comment_does_not_use_repo_flag(self) -> None:
        captured_cmds: list[list[str]] = []

        def fake_gh_json(_repo: str, _cmd: list[str]) -> tuple[Any | None, str | None]:
            return [{"id": 55, "body": "prefix marker suffix"}], None

        def fake_run_capture(cmd: list[str]) -> tuple[int, str, str]:
            captured_cmds.append(cmd)
            return 0, '{"id": 55, "html_url": "https://example.invalid/pr/55"}', ""

        payload, error = upsert_comment(
            "owner/repo",
            {"kind": "pr", "id": 88},
            marker="marker",
            body="updated body",
            gh_json_fn=fake_gh_json,
            run_capture_fn=fake_run_capture,
        )

        self.assertIsNone(error)
        self.assertEqual(payload.get("action"), "updated")
        self.assertEqual(len(captured_cmds), 1)
        command = captured_cmds[0]
        self.assertNotIn("--repo", command)
        self.assertIn("/repos/owner/repo/issues/comments/55", command)


if __name__ == "__main__":
    unittest.main()
