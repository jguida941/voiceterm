"""Typed per-session activity log contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace

from .evidence_archive import (
    EvidenceArchivePolicy,
    default_evidence_archive_policy,
)
from .value_coercion import coerce_mapping, coerce_string, coerce_string_items

SESSION_ACTIVITY_ENTRY_CONTRACT_ID = "SessionActivityEntry"
SESSION_ACTIVITY_LOG_CONTRACT_ID = "SessionActivityLog"
SESSION_ACTIVITY_LOG_SCHEMA_VERSION = 1
SESSION_ACTIVITY_LOG_REF_PREFIX = "session_activity_log:"


@dataclass(frozen=True, slots=True)
class SessionActivityEntry:
    """One typed action, receipt, or observation recorded for a session."""

    entry_id: str
    session_id: str
    actor_id: str
    occurred_at_utc: str
    activity_type: str
    summary: str
    status: str = "recorded"
    target_ref: str = ""
    evidence_refs: tuple[str, ...] = ()
    artifact_paths: tuple[str, ...] = ()
    changed_files: tuple[str, ...] = ()
    command_refs: tuple[str, ...] = ()
    packet_refs: tuple[str, ...] = ()
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""
    schema_version: int = SESSION_ACTIVITY_LOG_SCHEMA_VERSION
    contract_id: str = SESSION_ACTIVITY_ENTRY_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["artifact_paths"] = list(self.artifact_paths)
        payload["changed_files"] = list(self.changed_files)
        payload["command_refs"] = list(self.command_refs)
        payload["packet_refs"] = list(self.packet_refs)
        return payload


@dataclass(frozen=True, slots=True)
class SessionActivityLog:
    """Per-session operator-readable trail of typed activity evidence."""

    log_id: str
    session_id: str
    actor_id: str
    role: str = ""
    lifecycle_status: str = "open"
    started_at_utc: str = ""
    finished_at_utc: str = ""
    summary: str = ""
    entries: tuple[SessionActivityEntry, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    evidence_archive_ref: str = ""
    schema_version: int = SESSION_ACTIVITY_LOG_SCHEMA_VERSION
    contract_id: str = SESSION_ACTIVITY_LOG_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["entries"] = [entry.to_dict() for entry in self.entries]
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


def session_activity_log_ref(log_id: object) -> str:
    """Return the canonical evidence ref for a session activity log."""
    value = coerce_string(log_id)
    return f"{SESSION_ACTIVITY_LOG_REF_PREFIX}{value}" if value else ""


def session_activity_archive_policy(
    *,
    retention_days: object = 30,
    archive_root: object = "dev/reports/archive",
) -> EvidenceArchivePolicy:
    """Return the standard non-deleting archive policy for session logs."""
    return default_evidence_archive_policy(
        "session_activity_log",
        retention_days=retention_days,
        archive_root=archive_root,
    )


def append_session_activity_entry(
    log: SessionActivityLog,
    entry: SessionActivityEntry,
) -> SessionActivityLog:
    """Append an entry only when it belongs to this log's session and actor."""
    if not entry_belongs_to_session(entry, log.session_id, log.actor_id):
        return log
    evidence_refs = tuple(
        dict.fromkeys(
            (
                *log.evidence_refs,
                *entry.evidence_refs,
                *entry.packet_refs,
                *(f"artifact:{path}" for path in entry.artifact_paths),
            )
        )
    )
    return replace(log, entries=(*log.entries, entry), evidence_refs=evidence_refs)


def entry_belongs_to_session(
    entry: SessionActivityEntry,
    session_id: object,
    actor_id: object = "",
) -> bool:
    """Return whether an entry belongs to the requested session and optional actor."""
    session = coerce_string(session_id)
    actor = coerce_string(actor_id)
    return bool(entry.session_id and session and entry.session_id == session) and (
        not actor or not entry.actor_id or entry.actor_id == actor
    )


def session_activity_entry_from_receipt(
    receipt: Mapping[str, object],
    *,
    session_id: object,
    actor_id: object,
    artifact_path: object = "",
    occurred_at_utc: object = "",
) -> SessionActivityEntry:
    """Create a session activity entry from an existing dogfood or audit receipt."""
    payload = coerce_mapping(receipt)
    contract_id = coerce_string(payload.get("contract_id"))
    target_ref = _receipt_target_ref(payload)
    path = coerce_string(artifact_path)
    first_packet_id = _first_packet_ref(payload)
    evidence_refs = tuple(
        ref
        for ref in (
            _receipt_ref(payload),
            f"artifact:{path}" if path else "",
            f"packet:{first_packet_id}" if first_packet_id else "",
        )
        if ref
    )
    return SessionActivityEntry(
        entry_id=_receipt_entry_id(payload, path),
        session_id=coerce_string(session_id),
        actor_id=coerce_string(actor_id),
        occurred_at_utc=(
            coerce_string(occurred_at_utc)
            or coerce_string(payload.get("produced_at_utc"))
            or coerce_string(payload.get("observed_at_utc"))
        ),
        activity_type=_activity_type_for_receipt(contract_id),
        summary=(
            coerce_string(payload.get("summary"))
            or coerce_string(payload.get("audit_outcome"))
            or target_ref
            or contract_id
        ),
        status=_receipt_status(payload),
        target_ref=target_ref,
        evidence_refs=evidence_refs,
        artifact_paths=(path,) if path else (),
        changed_files=coerce_string_items(payload.get("changed_files")),
        command_refs=_command_refs(payload),
        packet_refs=_packet_refs(payload),
        correlation_id=coerce_string(payload.get("correlation_id")),
        causation_id=coerce_string(payload.get("causation_id")),
        run_id=coerce_string(payload.get("run_id")),
    )


def session_activity_log_from_entries(
    *,
    log_id: object,
    session_id: object,
    actor_id: object,
    entries: tuple[SessionActivityEntry, ...] = (),
    role: object = "",
    started_at_utc: object = "",
    finished_at_utc: object = "",
    lifecycle_status: object = "open",
    summary: object = "",
    evidence_archive_ref: object = "",
) -> SessionActivityLog:
    """Build a per-session log, filtering out entries from other sessions."""
    log = SessionActivityLog(
        log_id=coerce_string(log_id),
        session_id=coerce_string(session_id),
        actor_id=coerce_string(actor_id),
        role=coerce_string(role),
        lifecycle_status=coerce_string(lifecycle_status) or "open",
        started_at_utc=coerce_string(started_at_utc),
        finished_at_utc=coerce_string(finished_at_utc),
        summary=coerce_string(summary),
        evidence_archive_ref=coerce_string(evidence_archive_ref),
    )
    for entry in entries:
        log = append_session_activity_entry(log, entry)
    return log


def _activity_type_for_receipt(contract_id: str) -> str:
    if contract_id == "DogfoodSelfCheckReceipt":
        return "dogfood_self_check"
    if contract_id == "ReviewerAuditReceipt":
        return "reviewer_audit"
    return "typed_receipt"


def _receipt_entry_id(payload: Mapping[str, object], artifact_path: str) -> str:
    return (
        coerce_string(payload.get("receipt_id"))
        or coerce_string(payload.get("audit_id"))
        or coerce_string(payload.get("slice_id"))
        or artifact_path
        or coerce_string(payload.get("contract_id"))
    )


def _receipt_ref(payload: Mapping[str, object]) -> str:
    entry_id = _receipt_entry_id(payload, "")
    return f"receipt:{entry_id}" if entry_id else ""


def _receipt_target_ref(payload: Mapping[str, object]) -> str:
    return (
        coerce_string(payload.get("slice_id"))
        or coerce_string(payload.get("audit_target_slice_id"))
        or coerce_string(payload.get("target_ref"))
    )


def _receipt_status(payload: Mapping[str, object]) -> str:
    return (
        coerce_string(payload.get("status"))
        or coerce_string(payload.get("audit_outcome")).split(" ", 1)[0].lower()
        or "recorded"
    )


def _command_refs(payload: Mapping[str, object]) -> tuple[str, ...]:
    commands = payload.get("commands")
    if not isinstance(commands, (list, tuple)):
        return ()
    refs: list[str] = []
    for row in commands:
        command = coerce_string(coerce_mapping(row).get("command"))
        if command:
            refs.append(command)
    return tuple(refs)


def _packet_refs(payload: Mapping[str, object]) -> tuple[str, ...]:
    packet_ids = payload.get("audit_subject_packet_ids")
    return tuple(f"packet:{packet_id}" for packet_id in coerce_string_items(packet_ids))


def _first_packet_ref(payload: Mapping[str, object]) -> str:
    refs = _packet_refs(payload)
    if refs:
        return refs[0].removeprefix("packet:")
    return ""


__all__ = [
    "SESSION_ACTIVITY_ENTRY_CONTRACT_ID",
    "SESSION_ACTIVITY_LOG_CONTRACT_ID",
    "SESSION_ACTIVITY_LOG_REF_PREFIX",
    "SESSION_ACTIVITY_LOG_SCHEMA_VERSION",
    "SessionActivityEntry",
    "SessionActivityLog",
    "append_session_activity_entry",
    "entry_belongs_to_session",
    "session_activity_archive_policy",
    "session_activity_entry_from_receipt",
    "session_activity_log_from_entries",
    "session_activity_log_ref",
]
