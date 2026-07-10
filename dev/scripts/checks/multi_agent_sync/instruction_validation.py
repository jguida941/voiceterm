"""Instruction and signoff validations for the sync guard."""

from __future__ import annotations

from .markdown_tables import _normalize, _sorted_agents, _sorted_signers
from .models import (
    ALLOWED_INSTRUCTION_STATUSES,
    AgentBundle,
    SIGNOFF_DATE_PATTERN,
    UTC_Z_PATTERN,
)


def _validate_instruction_rows(
    *,
    instruction_rows: list[dict],
    required_agents: set[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    for row in instruction_rows:
        _validate_instruction_row(
            row=row,
            required_agents=required_agents,
            errors=errors,
            warnings=warnings,
        )


def _validate_instruction_row(
    *,
    row: dict,
    required_agents: set[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    instruction_id = _normalize(str(row.get("Instruction ID", "")))
    status = _normalize(str(row.get("Status", ""))).lower()
    instruction = {
        "instruction_id": instruction_id,
        "sender": _normalize(str(row.get("From", ""))).upper(),
        "target": _normalize(str(row.get("To", ""))).upper(),
        "status": status,
        "due_utc": _normalize(str(row.get("Due (UTC)", ""))),
    }
    ack_utc = _normalize(str(row.get("Ack UTC", "")))
    ack_token = _normalize(str(row.get("Ack token", "")))
    _validate_instruction_identity(
        instruction=instruction,
        required_agents=required_agents,
        errors=errors,
    )
    _validate_instruction_ack(
        instruction_id=instruction_id,
        status=status,
        ack_token=ack_token,
        ack_utc=ack_utc,
        errors=errors,
        warnings=warnings,
    )


def _validate_instruction_identity(
    *,
    instruction: dict[str, str],
    required_agents: set[str],
    errors: list[str],
) -> None:
    instruction_id = instruction["instruction_id"]
    sender = instruction["sender"]
    target = instruction["target"]
    status = instruction["status"]
    due_utc = instruction["due_utc"]
    if not instruction_id:
        errors.append("Instruction row missing Instruction ID.")
    if sender != "ORCHESTRATOR":
        errors.append(
            f"Instruction {instruction_id or '<missing>'} must originate from ORCHESTRATOR."
        )
    if target not in required_agents:
        errors.append(
            f"Instruction {instruction_id or '<missing>'} targets unexpected agent {target!r}."
        )
    if status not in ALLOWED_INSTRUCTION_STATUSES:
        errors.append(
            f"Instruction {instruction_id or '<missing>'} has invalid Status {status!r}; "
            f"expected one of {', '.join(sorted(ALLOWED_INSTRUCTION_STATUSES))}."
        )
    if not due_utc or due_utc == "pending" or not UTC_Z_PATTERN.match(due_utc):
        errors.append(
            f"Instruction {instruction_id or '<missing>'} Due (UTC) must be a full UTC timestamp."
        )


def _validate_instruction_ack(
    *,
    instruction_id: str,
    status: str,
    ack_token: str,
    ack_utc: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    if status == "pending":
        if ack_token.lower() != "pending":
            warnings.append(
                f"Instruction {instruction_id or '<missing>'} is pending but Ack token is {ack_token!r}."
            )
        if ack_utc.lower() != "pending":
            warnings.append(
                f"Instruction {instruction_id or '<missing>'} is pending but Ack UTC is {ack_utc!r}."
            )
        return
    if not ack_token or ack_token.lower() == "pending":
        errors.append(
            f"Instruction {instruction_id or '<missing>'} requires populated Ack token once status is {status!r}."
        )
    if not ack_utc or ack_utc.lower() == "pending" or not UTC_Z_PATTERN.match(ack_utc):
        errors.append(
            f"Instruction {instruction_id or '<missing>'} requires populated Ack UTC once status is {status!r}."
        )


def _validate_signoff_rows(
    *,
    agents: AgentBundle,
    errors: list[str],
) -> None:
    for signer in _sorted_signers(agents.expected_signers):
        row = agents.signoff_by_signer.get(signer)
        if not row:
            continue
        _validate_signoff_row(row=row, signer=signer, errors=errors)


def _validate_signoff_row(
    *,
    row: dict,
    signer: str,
    errors: list[str],
) -> None:
    signoff_date = _normalize(str(row.get("Date (UTC)", "")))
    signoff_result = _normalize(str(row.get("Result", ""))).lower()
    isolation = _normalize(str(row.get("Isolation verified", ""))).lower()
    bundle_ref = _normalize(str(row.get("Bundle reference", "")))
    signature = _normalize(str(row.get("Signature", "")))
    if (
        not signoff_date
        or signoff_date == "pending"
        or not SIGNOFF_DATE_PATTERN.match(signoff_date)
    ):
        errors.append(
            f"{signer} signoff Date (UTC) must be populated with YYYY-MM-DD or full UTC timestamp."
        )
    if signoff_result != "pass":
        errors.append(f"{signer} signoff Result must be `pass` after cycle completion.")
    if isolation != "yes":
        errors.append(
            f"{signer} signoff Isolation verified must be `yes` after cycle completion."
        )
    if not bundle_ref or bundle_ref == "pending":
        errors.append(f"{signer} signoff Bundle reference must be populated.")
    if not signature or signature.lower() == "pending":
        errors.append(f"{signer} signoff Signature must be populated.")
