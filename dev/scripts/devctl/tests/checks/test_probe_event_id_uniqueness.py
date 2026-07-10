"""Tests for the review-channel event-id uniqueness probe."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.checks.review_probes.probe_event_id_uniqueness import (
    duplicate_event_id_hints,
)


def test_duplicate_event_id_hints_flag_reused_event_id(tmp_path: Path) -> None:
    log_path = tmp_path / "trace.ndjson"
    log_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "event_id": "rev_evt_dup",
                        "event_type": "packet_dismissed",
                        "packet_id": "rev_pkt_1",
                    }
                ),
                json.dumps(
                    {
                        "event_id": "rev_evt_dup",
                        "event_type": "packet_dismissed",
                        "packet_id": "rev_pkt_2",
                    }
                ),
                json.dumps(
                    {
                        "event_id": "rev_evt_unique",
                        "event_type": "packet_posted",
                        "packet_id": "rev_pkt_3",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    hints = duplicate_event_id_hints(log_path)

    assert len(hints) == 1
    assert hints[0].symbol == "rev_evt_dup"
    assert "occurrences=2" in hints[0].signals
    assert "event_types=packet_dismissed" in hints[0].signals


def test_duplicate_event_id_hints_pass_when_ids_are_unique(tmp_path: Path) -> None:
    log_path = tmp_path / "trace.ndjson"
    log_path.write_text(
        "\n".join(
            [
                json.dumps({"event_id": "rev_evt_1", "event_type": "packet_posted"}),
                json.dumps({"event_id": "rev_evt_2", "event_type": "packet_acked"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert duplicate_event_id_hints(log_path) == []
