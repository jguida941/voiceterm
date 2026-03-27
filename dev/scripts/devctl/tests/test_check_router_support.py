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

    def test_custom_governed_layout_routes_markdown_to_tooling_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "docs" / "plans").mkdir(parents=True)
            (repo_root / "docs" / "engineering").mkdir(parents=True)
            (repo_root / "tools").mkdir(parents=True)

            (repo_root / "CONTRIBUTING.md").write_text("# Process\n", encoding="utf-8")
            (repo_root / "docs" / "plans" / "INDEX.md").write_text(
                "# Index\n"
                "| `docs/plans/MASTER_PLAN.md` | `tracker` | `canonical` | all active execution | always |\n",
                encoding="utf-8",
            )
            (repo_root / "docs" / "plans" / "MASTER_PLAN.md").write_text(
                "# Master Plan\n"
                "Execution plan contract: required\n"
                "## Scope\ntext\n"
                "## Execution Checklist\n- [ ] item\n"
                "## Progress Log\n- started\n"
                "## Session Resume\n- next\n"
                "## Audit Evidence\n- proof\n",
                encoding="utf-8",
            )
            (repo_root / "docs" / "plans" / "next_slice.md").write_text(
                "# Slice\n",
                encoding="utf-8",
            )
            (repo_root / "docs" / "engineering" / "DEVELOPMENT.md").write_text(
                "# Development\n",
                encoding="utf-8",
            )
            policy_payload = {
                "schema_version": 1,
                "repo_governance": {
                    "surface_generation": {
                        "context": {
                            "process_doc": "CONTRIBUTING.md",
                            "execution_tracker_doc": "docs/plans/MASTER_PLAN.md",
                            "active_registry_doc": "docs/plans/INDEX.md",
                            "development_doc": "docs/engineering/DEVELOPMENT.md",
                            "python_tooling": "tools/",
                        }
                    }
                },
            }
            policy_path = repo_root / "policy.json"
            policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")

            report = classify_lane(
                ["docs/plans/next_slice.md"],
                repo_root=repo_root,
                policy_path=str(policy_path),
            )

        self.assertEqual(report["lane"], "tooling")
        self.assertEqual(
            report["categories"]["tooling_paths"],
            ["docs/plans/next_slice.md"],
        )

    def test_deleted_custom_governed_markdown_uses_governed_prefix_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "docs" / "plans").mkdir(parents=True)

            (repo_root / "CONTRIBUTING.md").write_text("# Process\n", encoding="utf-8")
            (repo_root / "docs" / "plans" / "INDEX.md").write_text(
                "# Index\n"
                "| `docs/plans/MASTER_PLAN.md` | `tracker` | `canonical` | all active execution | always |\n",
                encoding="utf-8",
            )
            (repo_root / "docs" / "plans" / "MASTER_PLAN.md").write_text(
                "# Master Plan\n"
                "Execution plan contract: required\n"
                "## Scope\ntext\n"
                "## Execution Checklist\n- [ ] item\n"
                "## Progress Log\n- started\n"
                "## Session Resume\n- next\n"
                "## Audit Evidence\n- proof\n",
                encoding="utf-8",
            )
            policy_payload = {
                "schema_version": 1,
                "repo_governance": {
                    "surface_generation": {
                        "context": {
                            "process_doc": "CONTRIBUTING.md",
                            "execution_tracker_doc": "docs/plans/MASTER_PLAN.md",
                            "active_registry_doc": "docs/plans/INDEX.md",
                        }
                    }
                },
            }
            policy_path = repo_root / "policy.json"
            policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")

            report = classify_lane(
                ["docs/plans/deleted_plan.md"],
                repo_root=repo_root,
                policy_path=str(policy_path),
            )

        self.assertEqual(report["lane"], "tooling")
        self.assertEqual(
            report["categories"]["tooling_paths"],
            ["docs/plans/deleted_plan.md"],
        )
