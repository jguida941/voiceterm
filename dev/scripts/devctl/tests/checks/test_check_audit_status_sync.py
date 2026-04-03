"""Tests for AUDIT_STATUS sync guard."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.tests.conftest import load_repo_module


class CheckAuditStatusSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_repo_module(
            "check_audit_status_sync",
            "dev/scripts/checks/check_audit_status_sync.py",
        )

    def test_build_report_fails_when_completed_rows_stay_open_in_audit(self) -> None:
        report = self.script.build_report(
            audit_text="\n".join(
                [
                    "| D | contract_ownership_map in StartupContext | NOT CODED |",
                    "| F | Audit file auto-sync guard | NOT CODED |",
                    "| I | Cross-surface consistency proof | NOT CODED |",
                    "| K | Prove clean end-to-end path | NOT TESTED |",
                    "| L | Prove rescue end-to-end path | NOT TESTED |",
                ]
            ),
            code_signals={
                "contract_ownership_map": True,
                "surface_consistency_guard": True,
                "audit_sync_guard": True,
                "phase4_clean_path": True,
                "phase4_rescue_path": True,
                "phase4_convergence": True,
                "phase4_remote_session": True,
                "phase4_all": True,
            },
        )

        self.assertFalse(report["ok"])
        self.assertEqual(len(report["stale_rows"]), 5)

    def test_build_report_passes_when_audit_text_is_current(self) -> None:
        report = self.script.build_report(
            audit_text="Phase 4 integration coverage is current.\n",
            code_signals={
                "contract_ownership_map": True,
                "surface_consistency_guard": True,
                "audit_sync_guard": True,
                "phase4_clean_path": True,
                "phase4_rescue_path": True,
                "phase4_convergence": True,
                "phase4_remote_session": True,
                "phase4_all": True,
            },
        )

        self.assertTrue(report["ok"])
        self.assertEqual(report["stale_rows"], [])


if __name__ == "__main__":
    unittest.main()
