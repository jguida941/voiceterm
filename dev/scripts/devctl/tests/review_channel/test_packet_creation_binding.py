"""Tests for creation-time review-packet durable binding."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.review_channel.event_reducer import reduce_events
from dev.scripts.devctl.review_channel.events import post_packet, resolve_artifact_paths
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketPostRequest,
    PacketTargetFields,
)
from dev.scripts.devctl.review_channel.packet_creation_binding import (
    bind_packet_at_creation,
)
from dev.scripts.devctl.runtime.packet_carry_forward import (
    packet_carry_forward_debts,
)


def _review_channel_path(root: Path) -> Path:
    path = root / "dev/active/review_channel.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Review Channel + Shared Screen Plan",
                "",
                "| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |",
                "|---|---|---|---|---|---|",
                "| `codex` | reviewer | `dev/active/ai_governance_platform.md` | MP-377 | . | feature/test |",
                "| `claude` | dashboard | `dev/active/ai_governance_platform.md` | MP-377 | . | feature/test |",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _master_plan(root: Path) -> Path:
    path = root / "dev/active/MASTER_PLAN.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Master Plan\n", encoding="utf-8")
    return path


def test_finding_packet_binds_to_plan_row_at_creation(tmp_path: Path) -> None:
    master_plan = _master_plan(tmp_path)
    review_channel_path = _review_channel_path(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)

    bundle, event = post_packet(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="claude",
            to_agent="codex",
            kind="finding",
            plan_id="MP-377",
            summary="Packet binding should be durable",
            body="A repeated runtime finding must become typed plan state at post time.",
            evidence_refs=("dev/scripts/devctl/review_channel/events.py",),
            target=PacketTargetFields.from_values(
                anchor_refs=("MP-377",),
                intake_ref="audit:packet-binding-test",
            ),
        ),
    )

    packet = next(
        row
        for row in bundle.review_state["packets"]
        if row["packet_id"] == event["packet_id"]
    )
    binding = packet["packet_creation_binding"]
    store_rows = [
        json.loads(line)
        for line in (tmp_path / "dev/state/plan_index.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert event["packet_creation_binding_event_id"]
    assert binding["contract_id"] == "PacketCreationBinding"
    assert binding["status"] == "inserted"
    assert binding["binding_target_kind"] == "plan_row"
    assert store_rows[0]["sourced_from_packets"] == [event["packet_id"]]
    assert store_rows[0]["row_id"].startswith("PKT-BIND-")
    assert "Generated Review Packet Creation Bindings" in master_plan.read_text(
        encoding="utf-8"
    )


def test_system_notice_with_plan_words_does_not_bind_to_plan_row(
    tmp_path: Path,
) -> None:
    _master_plan(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)

    binding = bind_packet_at_creation(
        repo_root=tmp_path,
        artifact_paths=artifact_paths,
        packet_event={
            "event_type": "packet_posted",
            "packet_id": "rev_pkt_notice",
            "kind": "system_notice",
            "plan_id": "MP-377",
            "summary": "Plan status packet",
            "body": "This packet mentions plan and guard state but is only status.",
        },
    )

    assert binding["status"] == "skipped"
    assert not (tmp_path / "dev/state/plan_index.jsonl").exists()


def test_post_packet_records_communication_only_classification(
    tmp_path: Path,
) -> None:
    _master_plan(tmp_path)
    review_channel_path = _review_channel_path(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)

    bundle, event = post_packet(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="codex",
            to_agent="claude",
            kind="system_notice",
            plan_id="MP-377",
            summary="Status only",
            body="Plan and guard status only; no new durable work item.",
            target=PacketTargetFields.from_values(
                anchor_refs=("section:MP-377",),
            ),
        ),
    )

    packet = next(
        row
        for row in bundle.review_state["packets"]
        if row["packet_id"] == event["packet_id"]
    )

    assert event["packet_creation_binding_event_id"]
    assert packet["packet_creation_binding"]["status"] == "skipped"
    assert packet["packet_creation_binding"]["binding_target_kind"] == (
        "communication_only"
    )
    assert packet["packet_creation_binding"]["reason"] == (
        "communication_only_system_notice_plan_context_advisory"
    )
    assert packet["packet_creation_binding"]["advisory_plan_context_present"] is True
    assert "section:MP-377" in packet["packet_creation_binding"]["plan_context_refs"]
    assert not (tmp_path / "dev/state/plan_index.jsonl").exists()


def test_system_notice_with_plan_target_binds_to_plan_row(tmp_path: Path) -> None:
    _master_plan(tmp_path)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)

    binding = bind_packet_at_creation(
        repo_root=tmp_path,
        artifact_paths=artifact_paths,
        packet_event={
            "event_type": "packet_posted",
            "event_id": "rev_evt_0001",
            "packet_id": "rev_pkt_notice_plan",
            "kind": "system_notice",
            "plan_id": "MP-377",
            "target_kind": "plan",
            "target_ref": "plan:MP-377",
            "summary": "Architecture follow-up",
            "body": "This notice intentionally targets the durable plan.",
        },
    )

    assert binding["status"] == "inserted"
    assert binding["binding_target_kind"] == "plan_row"


def test_bound_stale_packet_expires_without_carry_forward_debt(
    tmp_path: Path,
) -> None:
    posted = {
        "schema_version": 1,
        "event_id": "rev_evt_0001",
        "session_id": "local-review",
        "project_id": "test",
        "packet_id": "rev_pkt_bound",
        "trace_id": "trace_bound",
        "timestamp_utc": "2000-01-01T00:00:00Z",
        "source": "review_channel",
        "plan_id": "MP-377",
        "event_type": "packet_posted",
        "from_agent": "claude",
        "to_agent": "codex",
        "kind": "finding",
        "summary": "Bound packet",
        "body": "Durable finding already has typed ownership.",
        "evidence_refs": [],
        "guidance_refs": [],
        "context_pack_refs": [],
        "confidence": 1.0,
        "requested_action": "review_only",
        "policy_hint": "review_only",
        "approval_required": False,
        "status": "pending",
        "expires_at_utc": "2000-01-01T00:30:00Z",
    }
    binding = {
        **posted,
        "event_id": "rev_evt_0002",
        "event_type": "packet_creation_binding_recorded",
        "timestamp_utc": "2000-01-01T00:00:01Z",
        "packet_creation_binding": {
            "contract_id": "PacketCreationBinding",
            "status": "inserted",
            "reason": "packet_bound_to_plan_row_at_creation",
            "packet_id": "rev_pkt_bound",
            "binding_target_kind": "plan_row",
            "binding_target": "PKT-BIND-REV-PKT-BOUND",
        },
    }

    review_state, _ = reduce_events(
        events=[posted, binding],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )
    packet = review_state["packets"][0]

    assert review_state["queue"]["stale_packet_count"] == 0
    assert packet["status"] == "pending"
    assert packet["lifecycle_current_state"] == "pending"
    assert packet["disposition"]["sink"] == "queued"
    assert packet_carry_forward_debts([packet]) == ()
