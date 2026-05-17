"""Typed audit-trail receipt for remote-control lifecycle invocations.

Per rev_pkt_2988 priority #3: every remote-control lifecycle action
(start/enter/heartbeat/exit) leaves a typed receipt so silent fails
are distinguishable from "never invoked." This addresses the rev_pkt_2987
diagnostic gap where the slash adapter could fail to fire and there was
no event-log evidence to tell whether enter/heartbeat ever ran.

Per rev_pkt_2996 finding #2 (schema_version=2): receipts now carry an
explicit before/after snapshot of attachment_status and
operator_interaction_mode plus a typed ``state_change`` classifier, so a
reader can prove whether an enter call created a new attachment, refreshed
an existing one, no-op'd because nothing changed, or fail-closed because
identity evidence was missing.

Receipts are append-only JSONL under dev/state/remote_control/
invocations.jsonl. Readers can replay them to reconstruct the lifecycle
without trusting the in-memory attachment artifact alone.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from .relaunch_loop_store import append_jsonl
from .remote_control_invocation_classifiers import (
    DEFAULT_REMOTE_CONTROL_INVOCATION_REL,
    REMOTE_CONTROL_INVOCATION_ACTIONS,
    REMOTE_CONTROL_INVOCATION_SOURCE_KINDS,
    REMOTE_CONTROL_INVOCATION_STATE_CHANGES,
    classify_claimed_source_kind,
    classify_state_change,
    resolve_invocation_origin,
)
from .typed_string_field import read_string_field


@dataclass(frozen=True, slots=True)
class RemoteControlInvocationReceipt:
    """Append-only audit row for one remote-control lifecycle invocation.

    schema_version=2 carries before/after snapshots so readers can prove
    whether the lifecycle call mutated typed state. Legacy
    ``attachment_status`` and ``operator_interaction_mode`` mirror the
    ``after_*`` fields for backward-compatible JSONL readers.
    """

    contract_id: str = "RemoteControlInvocationReceipt"
    schema_version: int = 2
    invocation_at_utc: str = ""
    action: str = ""
    provider: str = ""
    entrypoint: str = ""
    launcher_source: str = ""
    target_status_dir: str = ""
    attachment_id: str = ""
    attachment_status: str = ""
    operator_interaction_mode: str = ""
    before_attachment_status: str = ""
    after_attachment_status: str = ""
    before_operator_interaction_mode: str = ""
    after_operator_interaction_mode: str = ""
    state_change: str = ""
    claimed_source_kind: str = "unspecified"
    proven_source_kind: str = "unspecified"
    invocation_origin: str = ""
    ok: bool = True
    dry_run: bool = False
    invocation_source: str = ""
    error_message: str = ""
    proof_channel: str = ""
    physical_confirmation_method: str = "none"
    hook_event_name: str = ""
    hook_prompt: str = ""
    hook_command_name: str = ""
    hook_session_id: str = ""
    hook_transcript_path: str = ""
    hook_dedupe_key: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RemoteControlInvocationInput:
    repo_root: Path
    invocation_at_utc: str
    action: Literal["start", "enter", "heartbeat", "exit"]
    provider: str
    entrypoint: str
    launcher_source: str = ""
    target_status_dir: str = ""
    attachment: object | None = None
    operator_interaction_mode: str = ""
    before_attachment_status: str = ""
    before_operator_interaction_mode: str = ""
    before_attachment_id: str = ""
    state_change: str = ""
    claimed_source_kind: str = ""
    proven_source_kind: str = ""
    invocation_origin: str = ""
    ok: bool = True
    dry_run: bool = False
    invocation_source: str = ""
    error_message: str = ""
    proof_channel: str = ""
    physical_confirmation_method: str = "none"
    hook_event_name: str = ""
    hook_prompt: str = ""
    hook_command_name: str = ""
    hook_session_id: str = ""
    hook_transcript_path: str = ""
    hook_dedupe_key: str = ""


def record_remote_control_invocation(
    record: RemoteControlInvocationInput,
) -> RemoteControlInvocationReceipt:
    """Build + append a typed invocation receipt; returns the receipt.

    ``attachment`` is the post-invocation snapshot (RemoteControlAttachmentState
    dataclass or Mapping); ``before_*`` arguments capture the pre-invocation
    snapshot so the receipt proves the state change. ``source_kind`` and
    ``invocation_origin`` (rev_pkt_3021 P1 #5) classify whether the call
    came from a trusted Claude/Codex project slash, the review-channel
    attach action, or direct CLI. Receipts are appended even on failure
    paths so silent-fail vs never-invoked is distinguishable.
    """
    after_status = read_string_field(record.attachment, "status")
    after_attachment_id = read_string_field(record.attachment, "attachment_id")
    resolved_state_change = record.state_change or classify_state_change(
        before_status=record.before_attachment_status,
        after_status=after_status,
        before_attachment_id=record.before_attachment_id,
        after_attachment_id=after_attachment_id,
        error_message=record.error_message,
    )
    # Per rev_pkt_3023 P1/P0 #4: emission-time validation against the
    # closed canonical enum so a stray non-canonical string in a caller
    # cannot leak through into the JSONL ledger. ``unclassified`` is
    # only valid as a deserialization fallback in ``receipt_from_mapping``,
    # never as an emitted value.
    if resolved_state_change not in REMOTE_CONTROL_INVOCATION_STATE_CHANGES:
        raise ValueError(
            f"state_change={resolved_state_change!r} is not in the closed enum "
            f"{REMOTE_CONTROL_INVOCATION_STATE_CHANGES!r}; "
            "every receipt emission must use a canonical value."
        )
    resolved_claimed = record.claimed_source_kind or classify_claimed_source_kind(
        entrypoint=record.entrypoint,
        launcher_source=record.launcher_source,
        invocation_origin=record.invocation_origin,
    )
    if resolved_claimed not in REMOTE_CONTROL_INVOCATION_SOURCE_KINDS:
        raise ValueError(
            f"claimed_source_kind={resolved_claimed!r} is not in the closed enum "
            f"{REMOTE_CONTROL_INVOCATION_SOURCE_KINDS!r}; "
            "every receipt emission must use a canonical value."
        )
    # Per rev_pkt_3025 P0-2: ``proven_source_kind`` stays ``unspecified``
    # until non-user-controllable evidence (env-var attestation,
    # transcript correlation) lands. Callers may set it explicitly when
    # they have a real proof source; the default reflects "no proof".
    resolved_proven = record.proven_source_kind or "unspecified"
    if resolved_proven not in REMOTE_CONTROL_INVOCATION_SOURCE_KINDS:
        raise ValueError(
            f"proven_source_kind={resolved_proven!r} is not in the closed enum "
            f"{REMOTE_CONTROL_INVOCATION_SOURCE_KINDS!r}."
        )
    receipt = RemoteControlInvocationReceipt(
        invocation_at_utc=record.invocation_at_utc,
        action=record.action,
        provider=record.provider,
        entrypoint=record.entrypoint,
        launcher_source=record.launcher_source,
        target_status_dir=record.target_status_dir,
        attachment_id=after_attachment_id,
        attachment_status=after_status,
        operator_interaction_mode=record.operator_interaction_mode,
        before_attachment_status=record.before_attachment_status,
        after_attachment_status=after_status,
        before_operator_interaction_mode=record.before_operator_interaction_mode,
        after_operator_interaction_mode=record.operator_interaction_mode,
        state_change=resolved_state_change,
        claimed_source_kind=resolved_claimed,
        proven_source_kind=resolved_proven,
        # Per rev_pkt_3027: ``invocation_origin`` must NOT mirror the
        # spoofable claimed value. It's derived from proven_source_kind
        # so a direct CLI passing ``--launcher-source claude_project_slash``
        # cannot get ``invocation_origin=claude_project_slash`` under an
        # authoritative-sounding field name. When the caller supplies an
        # explicit invocation_origin AND it matches proven_source_kind,
        # trust it. Otherwise default to ``direct_cli`` (no proof).
        invocation_origin=resolve_invocation_origin(
            caller_supplied=record.invocation_origin,
            proven_source_kind=resolved_proven,
        ),
        ok=record.ok,
        dry_run=record.dry_run,
        invocation_source=record.invocation_source,
        error_message=record.error_message,
        proof_channel=record.proof_channel,
        physical_confirmation_method=record.physical_confirmation_method or "none",
        hook_event_name=record.hook_event_name,
        hook_prompt=record.hook_prompt,
        hook_command_name=record.hook_command_name,
        hook_session_id=record.hook_session_id,
        hook_transcript_path=record.hook_transcript_path,
        hook_dedupe_key=record.hook_dedupe_key,
    )
    append_jsonl(
        record.repo_root / DEFAULT_REMOTE_CONTROL_INVOCATION_REL,
        receipt.to_dict(),
    )
    return receipt


def receipt_from_mapping(
    payload: Mapping[str, object],
) -> RemoteControlInvocationReceipt:
    """Deserialize one JSONL row back into the typed receipt dataclass."""
    after_status = read_string_field(payload, "after_attachment_status") or (
        read_string_field(payload, "attachment_status")
    )
    after_mode = read_string_field(payload, "after_operator_interaction_mode") or (
        read_string_field(payload, "operator_interaction_mode")
    )
    return RemoteControlInvocationReceipt(
        schema_version=int(payload.get("schema_version", 1) or 1),
        invocation_at_utc=read_string_field(payload, "invocation_at_utc"),
        action=read_string_field(payload, "action"),
        provider=read_string_field(payload, "provider"),
        entrypoint=read_string_field(payload, "entrypoint"),
        launcher_source=read_string_field(payload, "launcher_source"),
        target_status_dir=read_string_field(payload, "target_status_dir"),
        attachment_id=read_string_field(payload, "attachment_id"),
        attachment_status=read_string_field(payload, "attachment_status"),
        operator_interaction_mode=read_string_field(
            payload, "operator_interaction_mode"
        ),
        before_attachment_status=read_string_field(
            payload, "before_attachment_status"
        ),
        after_attachment_status=after_status,
        before_operator_interaction_mode=read_string_field(
            payload, "before_operator_interaction_mode"
        ),
        after_operator_interaction_mode=after_mode,
        state_change=read_string_field(payload, "state_change") or "unclassified",
        # Per rev_pkt_3025 P0-2: legacy rows used ``source_kind`` for the
        # claimed value; new rows split into ``claimed_source_kind`` +
        # ``proven_source_kind``. Read either, fall back to the legacy
        # field, default to "unspecified".
        claimed_source_kind=(
            read_string_field(payload, "claimed_source_kind")
            or read_string_field(payload, "source_kind")
            or "unspecified"
        ),
        proven_source_kind=(
            read_string_field(payload, "proven_source_kind") or "unspecified"
        ),
        invocation_origin=read_string_field(payload, "invocation_origin"),
        ok=bool(payload.get("ok", True)),
        dry_run=bool(payload.get("dry_run", False)),
        invocation_source=read_string_field(payload, "invocation_source"),
        error_message=read_string_field(payload, "error_message"),
        proof_channel=read_string_field(payload, "proof_channel"),
        physical_confirmation_method=(
            read_string_field(payload, "physical_confirmation_method") or "none"
        ),
        hook_event_name=read_string_field(payload, "hook_event_name"),
        hook_prompt=read_string_field(payload, "hook_prompt"),
        hook_command_name=read_string_field(payload, "hook_command_name"),
        hook_session_id=read_string_field(payload, "hook_session_id"),
        hook_transcript_path=read_string_field(payload, "hook_transcript_path"),
        hook_dedupe_key=read_string_field(payload, "hook_dedupe_key"),
    )


__all__ = [
    "REMOTE_CONTROL_INVOCATION_ACTIONS",
    "REMOTE_CONTROL_INVOCATION_SOURCE_KINDS",
    "REMOTE_CONTROL_INVOCATION_STATE_CHANGES",
    "classify_claimed_source_kind",
    "DEFAULT_REMOTE_CONTROL_INVOCATION_REL",
    "RemoteControlInvocationInput",
    "RemoteControlInvocationReceipt",
    "classify_state_change",
    "record_remote_control_invocation",
    "receipt_from_mapping",
]
