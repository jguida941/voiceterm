"""Tests for the architecture connectivity probe."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.platform.connectivity_registry_models import (
    ConnectivityRegistrySnapshot,
    MissingConnectionFinding,
)
from dev.scripts.devctl.tests.conftest import load_repo_module

SCRIPT = load_repo_module(
    "probe_architecture_connectivity_script",
    "dev/scripts/checks/probe_architecture_connectivity.py",
)


class ProbeArchitectureConnectivityTests(unittest.TestCase):
    def test_missing_connection_finding_becomes_architecture_hint(self) -> None:
        registry = ConnectivityRegistrySnapshot(
            schema_version=1,
            contract_id="ConnectivityRegistrySnapshot",
            source_contract_count=1,
            connected_contracts=(),
            governed_surface_ids=(),
        )
        finding = MissingConnectionFinding(
            contract_id="ReviewPacket",
            declared_reader_surface="claude_loop",
            expected_evidence_kind="field_reader",
            suggested_wire_locations=("dev/scripts/devctl/commands/reporting/claude_loop.py",),
            classification="mistakenly_declared",
            justification="reader is declared but no field evidence was found",
        )

        hints = SCRIPT.build_architecture_hints(
            registry=registry,
            findings=(finding,),
        )

        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].review_lens, "architecture")
        self.assertEqual(hints[0].severity, "high")
        self.assertEqual(hints[0].risk_type, "architecture_connectivity_gap")
        self.assertIn("contract=ReviewPacket", hints[0].signals)
        self.assertIn(
            "ConnectivityRegistrySnapshot",
            hints[0].ai_instruction,
        )

    def test_registry_warning_becomes_architecture_hint(self) -> None:
        registry = ConnectivityRegistrySnapshot(
            schema_version=1,
            contract_id="ConnectivityRegistrySnapshot",
            source_contract_count=1,
            connected_contracts=(),
            governed_surface_ids=(),
            warnings=("ReviewPacket.status has 2 source writers",),
        )

        hints = SCRIPT.build_architecture_hints(
            registry=registry,
            findings=(),
        )

        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].risk_type, "architecture_registry_warning")
        self.assertIn("ReviewPacket.status has 2 source writers", hints[0].signals)


if __name__ == "__main__":
    unittest.main()
