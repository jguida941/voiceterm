from __future__ import annotations

from dev.scripts.devctl.runtime.session_activity_log import (
    SessionActivityEntry,
    append_session_activity_entry,
    entry_belongs_to_session,
    session_activity_archive_policy,
    session_activity_entry_from_receipt,
    session_activity_log_from_entries,
    session_activity_log_ref,
)


def test_session_activity_log_is_scoped_to_one_session() -> None:
    matching = SessionActivityEntry(
        entry_id="entry-1",
        session_id="session-a",
        actor_id="codex",
        occurred_at_utc="2026-05-11T22:30:00Z",
        activity_type="dogfood_self_check",
        summary="Added activity log contract",
        evidence_refs=("receipt:entry-1",),
    )
    other_session = SessionActivityEntry(
        entry_id="entry-2",
        session_id="session-b",
        actor_id="codex",
        occurred_at_utc="2026-05-11T22:31:00Z",
        activity_type="dogfood_self_check",
        summary="Should not leak into session-a",
    )

    log = session_activity_log_from_entries(
        log_id="log-session-a",
        session_id="session-a",
        actor_id="codex",
        role="implementer",
        entries=(matching, other_session),
    )

    assert [entry.entry_id for entry in log.entries] == ["entry-1"]
    assert log.evidence_refs == ("receipt:entry-1",)
    assert entry_belongs_to_session(matching, "session-a", "codex") is True
    assert entry_belongs_to_session(other_session, "session-a", "codex") is False


def test_append_session_activity_entry_preserves_artifact_packet_and_receipt_refs() -> None:
    entry = SessionActivityEntry(
        entry_id="entry-1",
        session_id="session-a",
        actor_id="codex",
        occurred_at_utc="2026-05-11T22:30:00Z",
        activity_type="reviewer_audit",
        summary="Claude accepted the slice",
        evidence_refs=("receipt:audit-1",),
        artifact_paths=("dev/reports/governance/audit_receipts/audit.json",),
        packet_refs=("packet:rev_pkt_3733",),
    )
    log = session_activity_log_from_entries(
        log_id="log-session-a",
        session_id="session-a",
        actor_id="codex",
    )

    updated = append_session_activity_entry(log, entry)

    assert updated.entries == (entry,)
    assert updated.evidence_refs == (
        "receipt:audit-1",
        "packet:rev_pkt_3733",
        "artifact:dev/reports/governance/audit_receipts/audit.json",
    )


def test_session_activity_entry_from_dogfood_receipt() -> None:
    entry = session_activity_entry_from_receipt(
        {
            "contract_id": "DogfoodSelfCheckReceipt",
            "slice_id": "MP377-SESSION-ACTIVITY-LOG-S1",
            "produced_at_utc": "2026-05-11T22:30:00Z",
            "summary": "Added session activity log support.",
            "changed_files": ["dev/scripts/devctl/runtime/session_activity_log.py"],
            "commands": [{"command": "python3 -m py_compile ..."}],
        },
        session_id="session-a",
        actor_id="codex",
        artifact_path="dev/reports/dogfood/runs/activity.json",
    )

    assert entry.contract_id == "SessionActivityEntry"
    assert entry.activity_type == "dogfood_self_check"
    assert entry.entry_id == "MP377-SESSION-ACTIVITY-LOG-S1"
    assert entry.target_ref == "MP377-SESSION-ACTIVITY-LOG-S1"
    assert entry.artifact_paths == ("dev/reports/dogfood/runs/activity.json",)
    assert entry.changed_files == (
        "dev/scripts/devctl/runtime/session_activity_log.py",
    )
    assert entry.command_refs == ("python3 -m py_compile ...",)


def test_session_activity_entry_from_reviewer_audit_receipt() -> None:
    entry = session_activity_entry_from_receipt(
        {
            "contract_id": "ReviewerAuditReceipt",
            "audit_id": "audit:activity-log",
            "observed_at_utc": "2026-05-11T22:32:00Z",
            "audit_actor_id": "claude",
            "audit_target_slice_id": "MP377-SESSION-ACTIVITY-LOG-S1",
            "audit_subject_packet_ids": ["rev_pkt_3734"],
            "audit_outcome": "PASS - typed log observed",
        },
        session_id="session-a",
        actor_id="codex",
        artifact_path="dev/reports/governance/audit_receipts/activity.json",
    )

    assert entry.activity_type == "reviewer_audit"
    assert entry.entry_id == "audit:activity-log"
    assert entry.status == "pass"
    assert entry.summary == "PASS - typed log observed"
    assert entry.packet_refs == ("packet:rev_pkt_3734",)
    assert "packet:rev_pkt_3734" in entry.evidence_refs


def test_session_activity_log_serializes_and_uses_non_deleting_archive_policy() -> None:
    log = session_activity_log_from_entries(
        log_id="log-session-a",
        session_id="session-a",
        actor_id="codex",
        evidence_archive_ref="evidence_archive:session-a",
    )
    policy = session_activity_archive_policy()

    payload = log.to_dict()

    assert payload["contract_id"] == "SessionActivityLog"
    assert payload["entries"] == []
    assert session_activity_log_ref(log.log_id) == "session_activity_log:log-session-a"
    assert policy.evidence_kind == "session_activity_log"
    assert policy.delete_source_after_archive is False
