"""Creation-time durable binding for review packets."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .event_store import (
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    ReviewChannelArtifactPaths,
    append_event,
)
from .packet_creation_binding_contracts import (
    PACKET_CREATION_BINDING_CONTRACT_ID,
    PACKET_CREATION_BINDING_EVENT_TYPES,
    PACKET_CREATION_BINDING_SECTION,
    PacketCreationBindingEvent,
    binding_result,
)
from .packet_creation_binding_plan import bind_packet_to_plan_row
from .state import project_id_for_repo
from ..time_utils import utc_timestamp

_PLAN_ROW_BINDING_KINDS = frozenset(
    {
        "finding",
        "plan_gap_review",
        "plan_patch_review",
    }
)
_LIFECYCLE_BINDING_KINDS = frozenset(
    {
        "approval_request",
        "commit_approval",
        "instruction",
        "question",
    }
)


def maybe_append_packet_creation_binding(
    *,
    repo_root: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    packet_event: Mapping[str, object],
    existing_events: list[dict[str, object]],
) -> dict[str, object] | None:
    """Append one creation-binding receipt for a newly posted packet."""
    binding = bind_packet_at_creation(
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        packet_event=packet_event,
    )
    if _text(binding.get("status")) == "skipped":
        return None

    event = _binding_event(
        repo_root=repo_root,
        packet_event=packet_event,
        binding=binding,
    )
    return append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=existing_events,
    )


def bind_packet_at_creation(
    *,
    repo_root: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    packet_event: Mapping[str, object],
) -> dict[str, object]:
    """Bind a newly posted packet to durable typed state when policy allows it."""
    if _text(packet_event.get("event_type")) != "packet_posted":
        return binding_result("skipped", "not_packet_posted")

    kind = _text(packet_event.get("kind"))
    packet_id = _text(packet_event.get("packet_id"))
    if not packet_id:
        return binding_result("failed", "missing_packet_id")

    if _should_bind_to_plan_row(packet_event):
        return bind_packet_to_plan_row(
            repo_root=repo_root,
            artifact_paths=artifact_paths,
            packet_event=packet_event,
        )

    if kind in _LIFECYCLE_BINDING_KINDS:
        return binding_result(
            "deferred",
            "lifecycle_packet_requires_lifecycle_owner",
            packet_id=packet_id,
            binding_target_kind="packet_lifecycle_row",
            binding_target="",
        )

    return binding_result("skipped", "communication_only_or_no_durable_plan_context")


def _binding_event(
    *,
    repo_root: Path,
    packet_event: Mapping[str, object],
    binding: dict[str, object],
) -> dict[str, object]:
    return PacketCreationBindingEvent(
        session_id=packet_event.get("session_id"),
        project_id=project_id_for_repo(repo_root),
        packet_id=packet_event.get("packet_id"),
        trace_id=packet_event.get("trace_id"),
        timestamp_utc=utc_timestamp(),
        plan_id=packet_event.get("plan_id"),
        controller_run_id=packet_event.get("controller_run_id"),
        event_type=_binding_event_type(binding),
        from_agent=packet_event.get("from_agent"),
        to_agent=packet_event.get("to_agent"),
        kind=packet_event.get("kind"),
        summary=packet_event.get("summary"),
        status=packet_event.get("status") or "pending",
        packet_creation_binding=binding,
        reason=_text(binding.get("reason")),
    ).to_event()


def _binding_event_type(binding: Mapping[str, object]) -> str:
    status = _text(binding.get("status"))
    if status == "deferred":
        return "packet_creation_binding_deferred"
    if status == "failed":
        return "packet_creation_binding_failed"
    return "packet_creation_binding_recorded"


def _should_bind_to_plan_row(packet_event: Mapping[str, object]) -> bool:
    kind = _text(packet_event.get("kind"))
    if kind == "system_notice":
        return False
    if _text(packet_event.get("target_kind")) == "plan":
        return True
    if _mapping(packet_event.get("plan_proposal")):
        return True
    if kind in _PLAN_ROW_BINDING_KINDS and _has_explicit_plan_context(packet_event):
        return True
    if kind == "action_request" and _has_explicit_plan_context(packet_event):
        requested = _text(packet_event.get("requested_action"))
        return requested not in {"", "review_only"}
    if kind in {"decision", "draft"}:
        return _has_explicit_plan_context(packet_event) and _has_durable_intent(
            packet_event
        )
    return False


def _has_explicit_plan_context(packet_event: Mapping[str, object]) -> bool:
    plan_id = _text(packet_event.get("plan_id"))
    if plan_id and plan_id != DEFAULT_REVIEW_CHANNEL_PLAN_ID:
        return True
    if _text(packet_event.get("target_ref")):
        return True
    if _text(packet_event.get("intake_ref")):
        return True
    return bool(_rows(packet_event.get("anchor_refs")))


def _has_durable_intent(packet_event: Mapping[str, object]) -> bool:
    haystack = " ".join(
        _text(packet_event.get(key)).lower()
        for key in (
            "kind",
            "summary",
            "body",
            "requested_action",
            "policy_hint",
            "target_ref",
        )
    )
    return any(
        token in haystack
        for token in (
            "architecture",
            "bug",
            "finding",
            "fix",
            "guard",
            "ingest",
            "issue",
            "plan",
            "probe",
        )
    )


def _rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "PACKET_CREATION_BINDING_CONTRACT_ID",
    "PACKET_CREATION_BINDING_EVENT_TYPES",
    "PACKET_CREATION_BINDING_SECTION",
    "bind_packet_at_creation",
    "maybe_append_packet_creation_binding",
]
