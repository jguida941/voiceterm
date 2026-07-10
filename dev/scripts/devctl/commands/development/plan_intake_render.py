"""Plan-intake output and remediation rendering."""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from typing import Any

from ...runtime.plan_intent_ingestion import PlanIntentIngestionReceipt
from .plan_intake_support import text


def render_plan_intake_markdown(payload: Mapping[str, object]) -> str:
    receipt = payload.get("receipt")
    data = receipt if isinstance(receipt, Mapping) else {}
    rows = data.get("row_ids") if isinstance(data.get("row_ids"), list) else []
    lines = [
        "# Plan Intent Ingestion",
        "",
        f"- status: `{data.get('status') or 'unknown'}`",
        f"- reason: `{data.get('reason') or ''}`",
        f"- source: `{data.get('source_kind') or ''}` `{data.get('source_ref') or ''}`",
        f"- target: `{data.get('target_kind') or ''}` `{data.get('target_ref') or ''}`",
        f"- path: `{data.get('path') or ''}`",
        f"- receipt_path: `{data.get('receipt_path') or ''}`",
        f"- row_ids: {', '.join(f'`{row}`' for row in rows) if rows else '(none)'}",
        f"- source_retention_status: `{data.get('source_retention_status') or ''}`",
        f"- source_integrity_status: `{data.get('source_integrity_status') or ''}`",
        f"- source_completeness_status: `{data.get('source_completeness_status') or ''}`",
    ]
    remediation = payload.get("remediation")
    if isinstance(remediation, Mapping) and remediation:
        lines.extend(_remediation_lines(remediation))
    return "\n".join(lines) + "\n"


def remediation_for_receipt(
    args: Any,
    receipt: PlanIntentIngestionReceipt,
) -> Mapping[str, str]:
    if receipt.reason != "missing_plan_row_or_checklist_authority":
        return {}
    return dict(
        (
            ("reason", _MISSING_PLAN_AUTHORITY_REASON),
            ("required_authority", _MISSING_PLAN_AUTHORITY_REQUIREMENT),
            ("corrected_command_shape", corrected_command_shape(args)),
        )
    )


def corrected_command_shape(args: Any) -> str:
    command = [
        "python3",
        "dev/scripts/devctl.py",
        "develop",
        "ingest-plan",
    ]
    actor = text(getattr(args, "actor", ""))
    if actor:
        command.extend(("--actor", actor))
    command.extend(("--plan-row-id", "<PLAN_ROW_ID>"))
    source_kind = text(getattr(args, "source_kind", ""))
    if source_kind:
        command.extend(("--source-kind", source_kind))
    source_ref = text(getattr(args, "source_ref", ""))
    if source_ref:
        command.extend(("--source-ref", source_ref))
    target_ref = text(getattr(args, "target_ref", ""))
    if target_ref:
        command.extend(("--target-ref", target_ref))
    command.extend(("--body", "<plan prose>"))
    return " ".join(shlex.quote(part) for part in command)


def _remediation_lines(remediation: Mapping[str, object]) -> list[str]:
    return [
        "",
        "## Remediation",
        "",
        f"- reason: {remediation.get('reason') or ''}",
        f"- required_authority: {remediation.get('required_authority') or ''}",
        f"- corrected_command_shape: `{remediation.get('corrected_command_shape') or ''}`",
    ]


_MISSING_PLAN_AUTHORITY_REASON = (
    "Prose plan sources are evidence, not execution authority, until "
    "they carry an explicit PlanRow id, markdown checklist row, or the bounded "
    "'Rows to ingest from this plan' authority section."
)
_MISSING_PLAN_AUTHORITY_REQUIREMENT = (
    "Add --plan-row-id <PlanRow id>, or provide a source/body-file "
    "containing a checklist row shaped like '- [ ] `MP377-...` Title' or a "
    "bounded 'Rows to ingest from this plan' bullet list."
)


__all__ = [
    "corrected_command_shape",
    "remediation_for_receipt",
    "render_plan_intake_markdown",
]
