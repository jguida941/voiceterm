"""Unit tests for check-router path classification helpers."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl.commands.check_router_support import (
    classify_lane,
    detect_risk_addons,
)


class CheckRouterSupportTests(TestCase):
    def test_active_docs_route_to_tooling_lane(self) -> None:
        report = classify_lane(["dev/active/operator_console.md"])

        self.assertEqual(report["lane"], "tooling")
        self.assertEqual(
            report["categories"]["tooling_paths"],
            ["dev/active/operator_console.md"],
        )
        self.assertEqual(report["categories"]["docs_paths"], [])

    def test_policy_override_can_reclassify_paths_and_addons(self) -> None:
        policy_payload = {
            "schema_version": 1,
            "repo_governance": {
                "check_router": {
                    "runtime_prefixes": ["src/"],
                    "tooling_prefixes": ["tools/"],
                    "docs_prefixes": ["handbook/"],
                    "risk_addons": [
                        {
                            "id": "custom-runtime-hotspot",
                            "label": "Custom runtime hotspot",
                            "tokens": ["src/hotspot/"],
                            "commands": ["python3 tools/check-hotspot.py"],
                        }
                    ],
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.json"
            policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")

            report = classify_lane(
                ["src/hotspot/lib.rs"],
                policy_path=str(policy_path),
            )
            addons = detect_risk_addons(
                ["src/hotspot/lib.rs"],
                policy_path=str(policy_path),
            )

        self.assertEqual(report["lane"], "runtime")
        self.assertEqual(report["categories"]["runtime_paths"], ["src/hotspot/lib.rs"])
        self.assertEqual(addons, [
            {
                "id": "custom-runtime-hotspot",
                "label": "Custom runtime hotspot",
                "matched_paths": ["src/hotspot/lib.rs"],
                "commands": ["python3 tools/check-hotspot.py"],
            }
        ])
