"""Finalize session-resume authority payloads and blocker state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...runtime.authority_snapshot import (
    build_authority_snapshot,
    summary_blockers_csv,
    summary_next_command,
)
from ...runtime.value_coercion import coerce_string
from .session_resume_role_projection import project_packet_next_command_for_role


@dataclass(frozen=True, slots=True)
class AuthorityFinalizeInputs:
    authority_payload: dict[str, Any]
    top_blocker: str
    open_findings: str
    session_open_findings: str
    recovery_command: str
    attention_command: str
    visible_next_cmd: str
    role: str
    receipt: dict[str, Any] | None


def finalize_authority_payload(
    inputs: AuthorityFinalizeInputs,
) -> tuple[dict[str, Any], str, str, str, object]:
    authority_payload = inputs.authority_payload
    shared_blockers = summary_blockers_csv(authority_payload)
    resolved_top_blocker = inputs.top_blocker
    if resolved_top_blocker == inputs.session_open_findings:
        resolved_top_blocker = inputs.open_findings
    blockers = resolve_blockers(inputs.receipt, resolved_top_blocker, shared_blockers)
    explicit_runtime_command = bool(inputs.recovery_command or inputs.attention_command)
    if shared_blockers != "none" and not explicit_runtime_command:
        authority_payload["next_command"] = summary_next_command(authority_payload)
    resolved_visible_next = project_packet_next_command_for_role(
        role=inputs.role,
        command=coerce_string(authority_payload.get("next_command"))
        or inputs.visible_next_cmd,
    )
    authority_payload["next_command"] = resolved_visible_next
    authority_snapshot = build_authority_snapshot(
        authority_payload,
        caller_role=inputs.role,
    )
    return (
        authority_payload,
        resolved_top_blocker,
        blockers,
        resolved_visible_next,
        authority_snapshot,
    )


def resolve_blockers(
    receipt: dict[str, Any] | None,
    top_blocker: str,
    shared_blockers: str = "none",
) -> str:
    """Return the effective blocker string, failing closed without a receipt."""
    if receipt is None:
        return "bootstrap_required"
    blockers: list[str] = []
    for raw in (top_blocker, shared_blockers):
        for token in str(raw or "").split(","):
            blocker = token.strip()
            if (
                not blocker
                or blocker == "none"
                or _is_advisory_backlog_open_findings(blocker)
                or blocker in blockers
            ):
                continue
            blockers.append(blocker)
    return ",".join(blockers) if blockers else "none"


def _is_advisory_backlog_open_findings(blocker: str) -> bool:
    """Backlog-sized finding counts are planning debt, not bootstrap blockers."""
    normalized = blocker.lower()
    return "open finding" in normalized and normalized.endswith("(backlog)")
