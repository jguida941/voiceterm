"""Failure-envelope -> action_request packet router (Plan r2 Slice 0).

Thin adapter over the existing AI governance platform — zero new
decision logic. When a typed `ActionResult` reports `ok=False AND
auto_executable=True AND remediation != ""`, this module builds an
`action_request` packet event matching the shape that
`safe_auto_apply.append_safe_auto_apply_events` already accepts. The
allowlist (``SAFE_AUTO_APPLY_ACTION_REQUESTS``) is the single source of
truth for which remediations auto-fire.

Architectural intent: every typed FAIL envelope that names its own
`remediation` becomes auto-replayable by adding ONE entry to the
allowlist plus ONE setter at the producer. No bespoke dispatcher; no
new decision tree; no logic duplication. `/develop` and any other
caller (governed_executor, event_post_wake, etc.) consume the same
router.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..time_utils import utc_timestamp
from .event_store import (
    ReviewChannelArtifactPaths,
    append_event,
    idempotency_key,
    next_event_id,
)
from .safe_auto_apply import (
    SAFE_AUTO_APPLY_ACTION_REQUESTS,
    append_safe_auto_apply_events,
)


@dataclass(frozen=True)
class FailureRouterContext:
    """Bundle of inputs the router needs to emit a packet event.

    Bundled so caller signatures stay under the parameter-count guard
    threshold and so tests can build a fixture context once and reuse
    it across the FAIL-envelope shapes a repo produces.
    """

    repo_root: Path
    artifact_paths: ReviewChannelArtifactPaths
    project_id: str
    plan_id: str = "MP-377"
    session_id: str = "system"
    controller_run_id: str = ""


def route_action_result_failure(
    *,
    result: Mapping[str, object],
    context: FailureRouterContext,
    existing_events: list[dict[str, object]],
    target_ref: str = "",
    full_guard_bundle_evidence: str = "",
    completed_handoff_session_id: str = "",
) -> list[dict[str, object]]:
    """Convert a FAIL ActionResult into auto-applied transition events.

    Returns the list of events written to the event log (the original
    packet_posted plus the safe_auto_apply ack+apply transitions).
    Returns an empty list when the result is not eligible for auto
    routing — caller should treat that as "no auto remediation
    available, fall back to operator/agent decision".

    Eligibility (all must hold):
    - result.ok is False
    - result.auto_executable is True
    - result.remediation is non-empty AND in
      ``SAFE_AUTO_APPLY_ACTION_REQUESTS``

    Once the packet event lands, the existing
    ``append_safe_auto_apply_events`` primitive handles ack + apply
    transitions. No new decision logic is added by this module.
    """
    if not _result_is_routable(result):
        return []

    packet_event = _build_action_request_event(
        result=result,
        context=context,
        existing_events=existing_events,
        target_ref=target_ref,
        full_guard_bundle_evidence=full_guard_bundle_evidence,
        completed_handoff_session_id=completed_handoff_session_id,
    )

    events = list(existing_events)
    written_packet = append_event(
        Path(context.artifact_paths.event_log_path),
        packet_event,
        existing_events=events,
    )
    events.append(written_packet)

    transitions = append_safe_auto_apply_events(
        repo_root=context.repo_root,
        artifact_paths=context.artifact_paths,
        packet_event=written_packet,
        existing_events=events,
    )
    return [written_packet, *transitions]


def _result_is_routable(result: Mapping[str, object]) -> bool:
    """Return True when ActionResult opts in to auto-replay routing."""
    if bool(result.get("ok")):
        return False
    if not bool(result.get("auto_executable")):
        return False
    remediation = str(result.get("remediation") or "").strip()
    if not remediation:
        return False
    return remediation in SAFE_AUTO_APPLY_ACTION_REQUESTS


def _build_action_request_event(
    *,
    result: Mapping[str, object],
    context: FailureRouterContext,
    existing_events: list[dict[str, object]],
    target_ref: str,
    full_guard_bundle_evidence: str,
    completed_handoff_session_id: str,
) -> dict[str, object]:
    """Build a packet_posted event shaped for safe_auto_apply allowlist."""
    timestamp = utc_timestamp()
    remediation = str(result.get("remediation") or "").strip()
    action_id = str(result.get("action_id") or "").strip()
    reason = str(result.get("reason") or "").strip()
    target_ref_value = target_ref or _default_target_ref(action_id, reason)
    evidence_value = full_guard_bundle_evidence or _default_evidence(result)
    handoff_session = (
        completed_handoff_session_id or context.session_id or "system"
    )
    packet_id = _packet_id_for_result(result, action_id=action_id, timestamp=timestamp)
    return dict(
        schema_version=1,
        event_id=next_event_id(existing_events),
        session_id=context.session_id or "system",
        project_id=context.project_id,
        packet_id=packet_id,
        trace_id=_trace_id(packet_id, timestamp),
        timestamp_utc=timestamp,
        source="failure_packet_router",
        plan_id=context.plan_id,
        controller_run_id=context.controller_run_id,
        event_type="packet_posted",
        from_agent="system",
        to_agent="claude",
        kind="action_request",
        policy_hint="safe_auto_apply",
        approval_required=False,
        requested_action=remediation,
        target_kind="runtime",
        target_ref=target_ref_value,
        full_guard_bundle_evidence=evidence_value,
        evidence_refs=[
            f"agent_session_outcome:{handoff_session}",
            f"action_result:{action_id or remediation}",
        ],
        idempotency_key=idempotency_key(
            packet_id, "packet_posted", timestamp,
        ),
    )


def _default_target_ref(action_id: str, reason: str) -> str:
    """Build a target_ref that satisfies safe_auto_apply's prefix check."""
    suffix_parts = [part for part in (action_id, reason) if part]
    suffix = ":".join(suffix_parts) if suffix_parts else "auto_executable_failure"
    return f"devctl_commit:{suffix}"


def _default_evidence(result: Mapping[str, object]) -> str:
    """Synthesize a guard-bundle-evidence string from the result envelope."""
    reason_chain = result.get("reason_chain")
    if isinstance(reason_chain, (list, tuple)) and reason_chain:
        chain_text = ",".join(str(part) for part in reason_chain if part)
        if chain_text:
            return f"failure_envelope:{chain_text}"
    reason = str(result.get("reason") or "auto_executable_failure").strip()
    return f"failure_envelope:{reason}"


def _packet_id_for_result(
    result: Mapping[str, object],
    *,
    action_id: str,
    timestamp: str,
) -> str:
    """Deterministic packet_id derived from the result + clock."""
    suffix_parts = [
        part
        for part in (
            action_id,
            str(result.get("reason") or "").strip(),
            timestamp,
        )
        if part
    ]
    return "auto_pkt:" + ":".join(suffix_parts)


def _trace_id(packet_id: str, timestamp: str) -> str:
    return f"trace:{packet_id}:{timestamp}"
