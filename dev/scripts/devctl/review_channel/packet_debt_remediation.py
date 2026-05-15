"""Deterministic remediation for review-packet carry-forward debt."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from ..runtime.master_plan_store import read_plan_rows_jsonl
from ..runtime.derived_state_invalidation import (
    DerivedStateInvalidationInput,
    PACKET_DURABLE_INGESTION_INVALIDATION_SOURCE,
    REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS,
    derived_state_invalidation_payload,
)
from ..runtime.packet_carry_forward import (
    durable_packet_ids_from_finding_rows,
    durable_packet_ids_from_plan_rows,
    packet_carry_forward_debts,
)
from ..time_utils import utc_timestamp
from .event_store import ReviewChannelArtifactPaths, append_event, load_events
from .packet_creation_binding_plan import bind_packet_to_plan_row
from .packet_debt_remediation_contracts import (
    PACKET_DURABLE_INGESTION_EVENT_TYPES,
    PacketDebtRemediationReport,
    PacketDebtRemediationRow,
    durable_ingestion_event,
    receipt_from_binding,
)
from .packet_debt_triage import decided_packet_debt_detector, packet_batch_triage

DEFAULT_PACKET_DEBT_REMEDIATION_LIMIT = 30
_PLAN_INGESTIBLE_KINDS = frozenset(
    {
        "draft",
        "finding",
        "plan_gap_review",
        "plan_patch_review",
    }
)
_DURABLE_INTENT_TOKENS = frozenset(
    {
        "architecture",
        "bug",
        "finding",
        "fix",
        "guard",
        "ingest",
        "issue",
        "master plan",
        "plan",
        "probe",
        "route",
    }
)


@dataclass(frozen=True, slots=True)
class PacketDebtRemediationInputs:
    """Input paths and execution options for packet-debt remediation."""

    repo_root: Path
    artifact_paths: ReviewChannelArtifactPaths
    review_state_path: Path
    plan_store_path: Path
    finding_log_path: Path | None = None
    limit: int = DEFAULT_PACKET_DEBT_REMEDIATION_LIMIT
    write: bool = False


def packet_debt_remediation_report(
    inputs: PacketDebtRemediationInputs,
) -> PacketDebtRemediationReport:
    """Return and optionally apply deterministic packet-debt remediation."""
    packets = _review_state_packets(inputs.review_state_path)
    durable_packet_ids = _durable_packet_ids(
        plan_store_path=inputs.plan_store_path,
        finding_log_path=inputs.finding_log_path,
    )
    debts = packet_carry_forward_debts(
        packets,
        durable_packet_ids=durable_packet_ids,
    )
    packet_by_id = {_text(packet.get("packet_id")): packet for packet in packets}
    rows = [
        _remediation_row(
            repo_root=inputs.repo_root,
            artifact_paths=inputs.artifact_paths,
            packet=packet_by_id.get(debt.packet_id, {}),
            debt=debt,
            write=inputs.write,
        )
        for debt in debts[: max(0, inputs.limit)]
    ]
    triage = packet_batch_triage(
        debts=debts,
        packet_by_id=packet_by_id,
        target_ref_for_packet=_target_ref,
        action_for_packet=_recommended_action,
        cluster_id_for=_cluster_id,
    )
    return PacketDebtRemediationReport(
        generated_at_utc=utc_timestamp(),
        source_review_state_path=_repo_relative(
            inputs.review_state_path,
            repo_root=inputs.repo_root,
        ),
        write_enabled=inputs.write,
        rows=tuple(rows),
        total_debt_count=len(debts),
        decided_packet_debt=decided_packet_debt_detector(debts),
        batch_triage=triage,
    )


def _remediation_row(
    *,
    repo_root: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    packet: Mapping[str, object],
    debt,
    write: bool,
) -> PacketDebtRemediationRow:
    target_ref = _target_ref(packet)
    action = _recommended_action(packet)
    receipt = None
    if write and action == "ingest_plan_row":
        binding = bind_packet_to_plan_row(
            repo_root=repo_root,
            artifact_paths=artifact_paths,
            packet_event=packet,
        )
        receipt = receipt_from_binding(
            binding=binding,
            target_kind="plan_row",
            target_ref=target_ref,
        )
        receipt = _append_durable_ingestion_event(
            artifact_paths=artifact_paths,
            packet=packet,
            receipt=receipt,
        )

    return PacketDebtRemediationRow(
        packet_id=debt.packet_id,
        reason=debt.reason,
        kind=debt.kind,
        status=debt.status,
        lifecycle_state=debt.lifecycle_state,
        cluster_id=_cluster_id(debt.reason, target_ref, debt.kind),
        recommended_action=action,
        target_ref=target_ref,
        summary=debt.summary,
        receipt=receipt,
    )


def _append_durable_ingestion_event(
    *,
    artifact_paths: ReviewChannelArtifactPaths,
    packet: Mapping[str, object],
    receipt,
) -> object:
    status = _text(getattr(receipt, "status", ""))
    event_type = (
        "packet_durable_ingestion_recorded"
        if status in {"inserted", "updated", "already_present"}
        else "packet_durable_ingestion_failed"
    )
    event = durable_ingestion_event(
        packet=dict(packet),
        receipt=receipt,
        event_type=event_type,
        timestamp_utc=utc_timestamp(),
    )
    event["derived_state_invalidation"] = derived_state_invalidation_payload(
        DerivedStateInvalidationInput(
            source=PACKET_DURABLE_INGESTION_INVALIDATION_SOURCE,
            producer_id="review_channel.packet_durable_ingestion",
            producer_kind="review_channel_event",
            invalidated_consumers=REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS,
            next_consumer_action=(
                "reload_packet_debt_and_work_board_before_work_decision"
            ),
            event_type=event_type,
            packet_id=_text(packet.get("packet_id")),
            source_event_id=_text(event.get("event_id")),
            status=status,
            receipt_id=_text(getattr(receipt, "event_id", "")),
            target_ref=_text(getattr(receipt, "target_ref", "")),
        )
    )
    written = append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=load_events(Path(artifact_paths.event_log_path)),
    )
    return replace(
        receipt,
        event_id=_text(written.get("event_id")),
        recorded_at_utc=_text(written.get("timestamp_utc")),
    )


def _recommended_action(packet: Mapping[str, object]) -> str:
    if _should_ingest_plan_row(packet):
        return "ingest_plan_row"
    if _text(packet.get("kind")) in {"approval_request", "commit_approval", "question"}:
        return "link_lifecycle_owner"
    return "manual_review_required"


def _should_ingest_plan_row(packet: Mapping[str, object]) -> bool:
    kind = _text(packet.get("kind"))
    if _text(packet.get("target_kind")) == "plan":
        return True
    if kind in _PLAN_INGESTIBLE_KINDS and _has_plan_context(packet):
        return True
    if _packet_outcome(packet) == "promoted_to_finding":
        return True
    return kind in {"decision", "draft"} and _has_plan_context(packet) and _has_intent(packet)


def _has_plan_context(packet: Mapping[str, object]) -> bool:
    if _text(packet.get("target_ref")) or _text(packet.get("intake_ref")):
        return True
    if _rows(packet.get("anchor_refs")):
        return True
    return bool(_text(packet.get("plan_id")))


def _has_intent(packet: Mapping[str, object]) -> bool:
    text = " ".join(
        _text(packet.get(field)).lower()
        for field in ("summary", "body", "requested_action", "policy_hint")
    )
    return any(token in text for token in _DURABLE_INTENT_TOKENS)


def _target_ref(packet: Mapping[str, object]) -> str:
    return (
        _text(packet.get("target_ref"))
        or _text(packet.get("plan_id"))
        or "plan:review-channel"
    )


def _cluster_id(reason: str, target_ref: str, kind: str) -> str:
    raw = ":".join(
        part for part in (reason, target_ref or kind or "unscoped") if part
    )
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "-", raw).strip("-").lower()
    return slug or "packet-debt"


def _durable_packet_ids(
    *,
    plan_store_path: Path,
    finding_log_path: Path | None,
) -> tuple[str, ...]:
    plan_rows = (
        read_plan_rows_jsonl(plan_store_path)
        if plan_store_path.is_file()
        else ()
    )
    finding_rows = (
        _read_jsonl_rows(finding_log_path)
        if finding_log_path is not None and finding_log_path.is_file()
        else ()
    )
    return (
        durable_packet_ids_from_plan_rows(plan_rows)
        + durable_packet_ids_from_finding_rows(finding_rows)
    )


def _review_state_packets(path: Path) -> tuple[dict[str, object], ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, Mapping):
        return ()
    packets = payload.get("packets")
    if not isinstance(packets, list):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, dict))


def _read_jsonl_rows(path: Path) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return tuple(rows)


def _packet_outcome(packet: Mapping[str, object]) -> str:
    outcome = packet.get("packet_outcome")
    return _text(outcome.get("outcome")) if isinstance(outcome, Mapping) else ""


def _rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _repo_relative(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "DEFAULT_PACKET_DEBT_REMEDIATION_LIMIT",
    "PACKET_DURABLE_INGESTION_EVENT_TYPES",
    "PacketDebtRemediationInputs",
    "packet_debt_remediation_report",
]
