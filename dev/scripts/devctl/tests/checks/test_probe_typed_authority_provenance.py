"""Tests for typed-authority provenance probe."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import load_repo_module

SCRIPT = load_repo_module(
    "probe_typed_authority_provenance_script",
    "dev/scripts/checks/probe_typed_authority_provenance.py",
)


class ProbeTypedAuthorityProvenanceTests(unittest.TestCase):
    def test_plan_row_without_provenance_becomes_hint(self) -> None:
        repo_root = self._repo_with_plan_row({"row_id": "MP377-P0-T08A"})

        hints = SCRIPT.build_provenance_hints(repo_root)

        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].risk_type, "typed_authority_missing_provenance")
        self.assertIn("row_id=MP377-P0-T08A", hints[0].signals)

    def test_complete_queue_source_is_clean(self) -> None:
        repo_root = self._repo_with_review_state(
            {
                "queue": {
                    "derived_next_instruction": "Priority action_request: run it",
                    "derived_next_instruction_source": {
                        "packet_id": "rev_pkt_1",
                        "provenance": {
                            "schema_version": 1,
                            "contract_id": "IngestionProvenance",
                            "source_file": "dev/reports/review_channel/events/trace.ndjson",
                            "source_line": 0,
                            "source_kind": "ReviewPacketEvent",
                            "source_hash": "sha256:abc",
                            "observed_at_utc": "2026-04-29T03:00:00Z",
                            "section_authority": "review_packet",
                        },
                    },
                    "instruction_priority_decision": {
                        "schema_version": 1,
                        "contract_id": "InstructionPriorityDecision",
                        "selected_instruction_id": "rev_pkt_1",
                        "selected_source_kind": "packet",
                        "rule_id": "action_request_priority",
                        "rejected_alternatives": [],
                        "rejection_reasons": [],
                        "decided_at_utc": "2026-04-29T03:00:00Z",
                    },
                }
            }
        )

        self.assertEqual(SCRIPT.build_provenance_hints(repo_root), [])

    def _repo_with_plan_row(self, row: dict[str, object]) -> Path:
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        repo_root = Path(tmp_dir.name)
        store = repo_root / "dev/state/plan_index.jsonl"
        store.parent.mkdir(parents=True, exist_ok=True)
        store.write_text(json.dumps(row) + "\n", encoding="utf-8")
        return repo_root

    def _repo_with_review_state(self, payload: dict[str, object]) -> Path:
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        repo_root = Path(tmp_dir.name)
        path = repo_root / "dev/reports/review_channel/projections/latest/review_state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return repo_root


if __name__ == "__main__":
    unittest.main()
