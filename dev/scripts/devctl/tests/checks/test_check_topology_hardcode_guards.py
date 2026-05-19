"""Tests for Phase 0.6.C topology/provider hardcode guards."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.checks.guardir_extraction_plan_artifacts.command import (
    build_report as build_artifact_report,
)
from dev.scripts.checks.topology_hardcode.command import (
    INVENTORY_REL_PATH,
    build_report as build_topology_report,
    write_inventory,
)
from dev.scripts.devctl.config import REPO_ROOT


class TopologyHardcodeGuardTests(unittest.TestCase):
    def _repo(self) -> Path:
        tmp_dir = tempfile.TemporaryDirectory(dir=REPO_ROOT)
        self.addCleanup(tmp_dir.cleanup)
        return Path(tmp_dir.name)

    def _write(self, root: Path, rel_path: str, text: str) -> Path:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_current_repo_phase06c_artifacts_are_present(self) -> None:
        artifact_report = build_artifact_report(repo_root=REPO_ROOT)
        provider_report = build_topology_report(repo_root=REPO_ROOT, mode="provider")
        count_report = build_topology_report(repo_root=REPO_ROOT, mode="count")

        self.assertTrue(artifact_report["ok"], artifact_report["violations"])
        self.assertTrue(provider_report["ok"], provider_report["violations"])
        self.assertTrue(count_report["ok"], count_report["violations"])

    def test_artifact_guard_flags_checked_off_missing_inventory(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md",
            "✅ `TopologyHardcodeInventory` emitted at "
            "`dev/state/topology_hardcode_inventory.jsonl`\n",
        )

        report = build_artifact_report(repo_root=root)

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["check"],
            "checked_plan_artifact_missing",
        )

    def test_provider_guard_flags_uninventoried_provider_literal(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/runtime/role_profile.py",
            'DEFAULT_PROVIDER = "codex"\n',
        )
        self._write(root, INVENTORY_REL_PATH.as_posix(), "")

        report = build_topology_report(repo_root=root, mode="provider")

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["check"],
            "new_uninventoried_topology_hardcode",
        )

    def test_count_guard_flags_uninventoried_count_coupled_literal(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/runtime/reviewer_mode.py",
            'SINGLE_AGENT = "single_agent"\n',
        )
        self._write(root, INVENTORY_REL_PATH.as_posix(), "")

        report = build_topology_report(repo_root=root, mode="count")

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["check"],
            "new_uninventoried_topology_hardcode",
        )

    def test_written_inventory_satisfies_provider_guard(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/runtime/role_profile.py",
            'DEFAULT_PROVIDER = "codex"\n',
        )

        write_inventory(repo_root=root)
        report = build_topology_report(repo_root=root, mode="provider")
        rows = [
            json.loads(line)
            for line in (root / INVENTORY_REL_PATH).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(rows[0]["contract_id"], "TopologyHardcodeInventory")


if __name__ == "__main__":
    unittest.main()
