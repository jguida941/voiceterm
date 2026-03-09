"""Unit tests for check-router path classification helpers."""

from __future__ import annotations

from unittest import TestCase

from dev.scripts.devctl.commands.check_router_support import classify_lane


class CheckRouterSupportTests(TestCase):
    def test_active_docs_route_to_tooling_lane(self) -> None:
        report = classify_lane(["dev/active/operator_console.md"])

        self.assertEqual(report["lane"], "tooling")
        self.assertEqual(
            report["categories"]["tooling_paths"],
            ["dev/active/operator_console.md"],
        )
        self.assertEqual(report["categories"]["docs_paths"], [])

