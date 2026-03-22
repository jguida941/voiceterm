"""Unit tests for the CodeRabbit collection helper."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[4]


def load_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CodeRabbitCollectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "coderabbit_collect",
            "dev/scripts/coderabbit/collect.py",
        )

    def test_review_comment_findings_include_structured_path_and_line(self) -> None:
        event = {"pull_request": {"head": {"sha": "abc123"}}}
        review_comments = [
            {
                "user": {"login": "coderabbitai[bot]"},
                "body": "Unused import in auth.rs",
                "commit_id": "abc123",
                "path": "rust/src/auth.rs",
                "line": 12,
            }
        ]

        with mock.patch.object(
            self.script,
            "gh_api",
            side_effect=[review_comments, [], [], {}],
        ):
            findings, head_sha = self.script.collect_findings(
                event=event,
                event_name="pull_request",
                repo="owner/repo",
                pr_number="123",
                pushed_sha="",
                warnings=[],
            )

        self.assertEqual(head_sha, "abc123")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["path"], "rust/src/auth.rs")
        self.assertEqual(findings[0]["line"], 12)
        self.assertTrue(findings[0]["summary"].startswith("rust/src/auth.rs:12 - "))
