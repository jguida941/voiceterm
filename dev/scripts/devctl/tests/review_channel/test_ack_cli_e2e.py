"""End-to-end CLI regression tests for packet acknowledgement."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]


def _review_channel_base_args(tmp_path: Path) -> list[str]:
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(
        "# Review Channel\n\nCodex is the reviewer. Claude is the coder.\n",
        encoding="utf-8",
    )

    return [
        sys.executable,
        "dev/scripts/devctl.py",
        "review-channel",
        "--terminal",
        "none",
        "--review-channel-path",
        str(review_channel_path),
        "--bridge-path",
        str(tmp_path / "bridge.md"),
        "--rollover-dir",
        str(tmp_path / "rollovers"),
        "--status-dir",
        str(tmp_path / "status"),
        "--artifact-root",
        str(tmp_path / "artifacts"),
        "--state-json",
        str(tmp_path / "state/latest.json"),
        "--emit-projections",
        str(tmp_path / "projections/latest"),
    ]


def _run_json(args: list[str]) -> dict[str, object]:
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def test_review_channel_ack_cli_records_lifecycle_transition(tmp_path: Path) -> None:
    """`review-channel --action ack` must work through the real CLI dispatcher."""

    base_args = _review_channel_base_args(tmp_path)
    post_report = _run_json(
        [
            *base_args,
            "--action",
            "post",
            "--from-agent",
            "claude",
            "--to-agent",
            "codex",
            "--kind",
            "system_notice",
            "--summary",
            "Ack CLI regression packet",
            "--body",
            "Exercise the real ack dispatcher.",
            "--format",
            "json",
        ]
    )
    packet = post_report["packet"]
    assert isinstance(packet, dict)
    packet_id = str(packet["packet_id"])

    ack_report = _run_json(
        [
            *base_args,
            "--action",
            "ack",
            "--packet-id",
            packet_id,
            "--actor",
            "codex",
            "--format",
            "json",
        ]
    )

    assert ack_report["action"] == "ack"
    event = ack_report["event"]
    assert isinstance(event, dict)
    assert event["event_type"] == "packet_acked"
    assert event["packet_id"] == packet_id
    assert event["metadata"] == {"actor": "codex"}

    acked_packet = ack_report["packet"]
    assert isinstance(acked_packet, dict)
    assert acked_packet["status"] == "acked"
    assert acked_packet["lifecycle_current_state"] == "acknowledged"
    assert acked_packet["acked_by"] == "codex"
    acknowledged_events = acked_packet["acknowledged_events"]
    assert isinstance(acknowledged_events, list)
    assert acknowledged_events[-1]["by_agent"] == "codex"
    assert acknowledged_events[-1]["reason"] == "packet_acknowledged"

    inbox_report = _run_json(
        [
            *base_args,
            "--action",
            "inbox",
            "--target",
            "codex",
            "--status",
            "pending",
            "--format",
            "json",
        ]
    )
    assert packet_id not in {
        str(row.get("packet_id"))
        for row in inbox_report["packets"]
        if isinstance(row, dict)
    }

    event_log = tmp_path / "artifacts/events/trace.ndjson"
    transition_events = [
        json.loads(line)
        for line in event_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(
        row.get("event_type") == "packet_acked"
        and row.get("packet_id") == packet_id
        for row in transition_events
    )
