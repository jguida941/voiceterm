"""Focused tests for push-state markdown rendering."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.review_channel.projection_markdown import (
    append_push_markdown,
)


def _push_enforcement(**overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "latest_push_report_path": "dev/reports/push/latest.json",
        "latest_push_report_matches_current_branch": False,
        "latest_push_report_matches_current_head": False,
        "latest_push_report_published_remote": True,
        "latest_push_report_post_push_green": False,
        "latest_push_report_status": "published_remote",
        "latest_push_report_reason": "post_push_bundle_failed",
        "checkpoint_required": False,
        "publication_backlog_state": "none",
    }
    payload.update(overrides)
    return payload


class ReviewChannelPushRenderingTests(unittest.TestCase):
    def test_append_push_markdown_renders_latest_push_receipt_fields(self) -> None:
        lines: list[str] = []
        append_push_markdown(
            lines,
            _push_enforcement(),
            {"action": "await_checkpoint", "publication_guidance": "checkpoint first"},
        )

        rendered = "\n".join(lines)
        self.assertIn("## Push", rendered)
        self.assertIn("- latest_push_report: `dev/reports/push/latest.json`", rendered)
        self.assertIn("- latest_push_matches_current_branch: False", rendered)
        self.assertIn("- latest_push_matches_current_head: False", rendered)
        self.assertIn("- published_remote: True", rendered)
        self.assertIn("- post_push_green: False", rendered)
        self.assertIn("- latest_push_status: `published_remote`", rendered)
        self.assertIn("- latest_push_reason: `post_push_bundle_failed`", rendered)
