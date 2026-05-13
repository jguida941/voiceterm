"""Guard-error detail extraction for packet lifecycle reports."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import json


PACKET_GUARD_ERROR_DETAIL_CONTRACT_ID = "PacketGuardErrorDetail"

_FAILURE_STATUSES = frozenset(
    {
        "block",
        "blocked",
        "error",
        "fail",
        "failed",
        "failure",
    }
)


@dataclass(frozen=True, slots=True)
class PacketGuardErrorDetail:
    """Structured guard or execution error detail for a packet lifecycle edge."""

    packet_id: str
    action: str
    reason: str
    failure_source: str
    event_id: str = ""
    actor: str = ""
    status: str = ""
    guard_results_summary: str = ""
    full_guard_bundle_evidence: str = ""
    errors: tuple[str, ...] = ()
    reason_chain: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = PACKET_GUARD_ERROR_DETAIL_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return _drop_empty(asdict(self))


def guard_error_detail_from_event(
    event: Mapping[str, object],
    packet: Mapping[str, object],
    *,
    action: str,
    reason: str,
) -> dict[str, object]:
    """Build guard-error detail from an explicit lifecycle transition event."""
    metadata = _mapping(event.get("metadata"))
    return PacketGuardErrorDetail(
        packet_id=_text(packet.get("packet_id")) or _text(event.get("packet_id")),
        action=_text(action),
        reason=_text(reason) or _text(metadata.get("reason")),
        failure_source="action_request_lifecycle_event",
        event_id=_text(event.get("event_id")),
        actor=_text(metadata.get("actor")),
        status=_text(event.get("status")),
        guard_results_summary=(
            _text(event.get("guard_results_summary"))
            or _text(packet.get("guard_results_summary"))
        ),
        full_guard_bundle_evidence=(
            _text(event.get("full_guard_bundle_evidence"))
            or _text(packet.get("full_guard_bundle_evidence"))
        ),
        errors=(
            *_string_tuple(metadata.get("errors")),
            *_string_tuple(metadata.get("guard_errors")),
            *_string_tuple(event.get("errors")),
        ),
        reason_chain=(
            *_string_tuple(metadata.get("reason_chain")),
            *_string_tuple(event.get("reason_chain")),
        ),
    ).to_dict()


def guard_error_detail_from_packet(
    packet: Mapping[str, object],
    *,
    action: str = "",
    reason: str = "",
    failure_source: str = "packet_fields",
) -> dict[str, object]:
    """Build guard-error detail from reduced packet fields when present."""
    metadata = _mapping(packet.get("metadata"))
    summary = _text(packet.get("guard_results_summary"))
    evidence = _text(packet.get("full_guard_bundle_evidence"))
    errors = (
        *_string_tuple(metadata.get("errors")),
        *_string_tuple(metadata.get("guard_errors")),
        *_string_tuple(packet.get("errors")),
    )
    reason_chain = (
        *_string_tuple(metadata.get("reason_chain")),
        *_string_tuple(packet.get("reason_chain")),
    )
    failure_reason = (
        _text(reason)
        or _text(packet.get("execution_failed_reason"))
        or _text(packet.get("apply_pending_after_execution_reason"))
        or _text(metadata.get("reason"))
    )
    failure_action = (
        _text(action)
        or ("failed" if _text(packet.get("execution_failed_at_utc")) else "")
        or (
            "apply_pending_after_execution"
            if _text(packet.get("apply_pending_after_execution_at_utc"))
            else ""
        )
        or ("failed" if _summary_or_evidence_indicates_failure(summary, evidence) else "")
    )
    if not (
        failure_reason
        or errors
        or reason_chain
        or _summary_or_evidence_indicates_failure(summary, evidence)
    ):
        return {}
    return PacketGuardErrorDetail(
        packet_id=_text(packet.get("packet_id")),
        action=failure_action or "failed",
        reason=failure_reason or "guard_failure_evidence_present",
        failure_source=failure_source,
        actor=(
            _text(packet.get("execution_failed_by"))
            or _text(packet.get("apply_pending_after_execution_by"))
        ),
        status=_text(packet.get("status")),
        guard_results_summary=summary,
        full_guard_bundle_evidence=evidence,
        errors=errors,
        reason_chain=reason_chain,
    ).to_dict()


def guard_error_detail_from_action_event(
    event: Mapping[str, object],
) -> dict[str, object]:
    """Return guard-error detail previously attached to a lifecycle event."""
    detail = event.get("guard_error_detail")
    return dict(detail) if isinstance(detail, Mapping) else {}


def guard_summary_or_evidence_indicates_failure(packet: Mapping[str, object]) -> bool:
    """Return True when guard fields are explicit failure evidence."""
    return _summary_or_evidence_indicates_failure(
        _text(packet.get("guard_results_summary")),
        _text(packet.get("full_guard_bundle_evidence")),
    )


def _summary_or_evidence_indicates_failure(summary: str, evidence: str) -> bool:
    if evidence.startswith("failure_envelope:"):
        return True
    if not summary:
        return False
    parsed = _parse_json_object(summary)
    if parsed and _parsed_guard_summary_failed(parsed):
        return True
    lowered = summary.lower()
    return any(
        token in lowered
        for token in (
            "status=fail",
            "status: fail",
            "status failed",
            "status=error",
            "guard_failed",
            "guard failed",
        )
    )


def _parsed_guard_summary_failed(value: object) -> bool:
    if isinstance(value, Mapping):
        status = _text(value.get("status")).lower()
        ok = value.get("ok")
        if status in _FAILURE_STATUSES:
            return True
        if ok is False:
            return True
        return any(_parsed_guard_summary_failed(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_parsed_guard_summary_failed(item) for item in value)
    return False


def _parse_json_object(value: str) -> object:
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _drop_empty(payload: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if value not in {"", (), None}
    }


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "PACKET_GUARD_ERROR_DETAIL_CONTRACT_ID",
    "PacketGuardErrorDetail",
    "guard_error_detail_from_action_event",
    "guard_error_detail_from_event",
    "guard_error_detail_from_packet",
    "guard_summary_or_evidence_indicates_failure",
]
