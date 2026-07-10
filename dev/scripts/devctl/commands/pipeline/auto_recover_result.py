"""Result builders for ``devctl pipeline --action auto-recover``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ...runtime.pipeline_auto_recovery_contracts import (
    CHOSEN_ACTION_BAILED,
    CHOSEN_ACTION_NONE,
    CLASSIFICATION_AMBIGUOUS,
    PipelineAutoRecoveryClassification,
    PipelineAutoRecoveryReceipt,
)
from .support import PipelinePaths


AUTO_RECOVERY_RECEIPT_FILENAME = "pipeline_auto_recovery_receipt.json"


@dataclass(frozen=True, slots=True)
class AutoRecoveryContext:
    """Shared context every auto-recover result finalizer needs."""

    paths: PipelinePaths
    classification: PipelineAutoRecoveryClassification
    pipeline_id: str
    previous_state: str
    operator_actor: str


@dataclass(frozen=True, slots=True)
class AutoRecoverySubAction:
    """Sub-action result metadata for a dispatched recovery action."""

    chosen_action: str
    result: dict[str, Any]
    receipt_key: str
    reason: str


def finalize_noop(context: AutoRecoveryContext) -> dict[str, Any]:
    """Write an already-clean receipt and return the public result."""
    receipt = _receipt(
        context,
        chosen_action=CHOSEN_ACTION_NONE,
        reason=context.classification.reason,
        new_state=context.previous_state,
    )
    receipt_path = write_composite_receipt(context.paths, receipt)
    return _base_result(
        context,
        ok=True,
        chosen_action=CHOSEN_ACTION_NONE,
        new_state=context.previous_state,
        receipt_path=receipt_path,
    ) | {"sub_action_result": None}


def finalize_bailed(
    context: AutoRecoveryContext,
    *,
    override_reason: str = "",
) -> dict[str, Any]:
    """Write a fail-closed receipt for ambiguous or unsupported states."""
    reason = override_reason or context.classification.reason
    receipt = _receipt(
        context,
        chosen_action=CHOSEN_ACTION_BAILED,
        reason=reason,
        new_state=context.previous_state,
        classification=CLASSIFICATION_AMBIGUOUS,
    )
    receipt_path = write_composite_receipt(context.paths, receipt)
    return _base_result(
        context,
        ok=False,
        chosen_action=CHOSEN_ACTION_BAILED,
        new_state=context.previous_state,
        receipt_path=receipt_path,
    ) | {
        "reason_refused": reason,
        "sub_action_result": None,
    }


def finalize_sub_action(
    context: AutoRecoveryContext,
    sub_action: AutoRecoverySubAction,
) -> dict[str, Any]:
    """Write a composite receipt after a recover/refresh/abandon sub-action."""
    sub_ok = bool(sub_action.result.get("ok"))
    chosen_action = (
        sub_action.chosen_action if sub_ok else CHOSEN_ACTION_BAILED
    )
    sub_receipt_path = str(
        sub_action.result.get(sub_action.receipt_key, "") or ""
    )
    new_state = (
        str(sub_action.result.get("new_state") or context.previous_state)
        if sub_ok
        else context.previous_state
    )
    receipt = _receipt(
        context,
        chosen_action=chosen_action,
        reason=sub_action.reason or context.classification.reason,
        new_state=new_state,
        sub_receipt_path=sub_receipt_path,
    )
    receipt_path = write_composite_receipt(context.paths, receipt)
    return _base_result(
        context,
        ok=sub_ok,
        chosen_action=chosen_action,
        new_state=new_state,
        receipt_path=receipt_path,
    ) | {
        "sub_receipt_path": sub_receipt_path,
        "sub_action_result": sub_action.result,
    }


def write_composite_receipt(
    paths: PipelinePaths,
    receipt: PipelineAutoRecoveryReceipt,
) -> Path:
    """Persist the composite auto-recovery receipt next to sub receipts."""
    paths.receipts_root.mkdir(parents=True, exist_ok=True)
    receipt_path = paths.receipts_root / AUTO_RECOVERY_RECEIPT_FILENAME
    receipt_path.write_text(
        json.dumps(receipt.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    return receipt_path


def render_markdown(result: dict[str, Any]) -> str:
    """Render a compact markdown result for CLI callers."""
    lines: list[str] = ["# pipeline auto-recover", ""]
    classification = result.get("classification") or {}
    lines.extend([
        f"- ok: `{str(bool(result.get('ok'))).lower()}`",
        f"- classification: `{classification.get('classification','')}`",
        f"- classification_reason: `{classification.get('reason','')}`",
        f"- chosen_action: `{result.get('chosen_action','')}`",
        f"- pipeline_id: `{result.get('pipeline_id','')}`",
        f"- previous_state: `{result.get('previous_state','')}`",
        f"- new_state: `{result.get('new_state','')}`",
        f"- head_has_moved: `{classification.get('head_has_moved', False)}`",
        f"- head_movement_classification: `{classification.get('head_movement_classification','')}`",
        f"- managed_receipt_parent_sha: `{classification.get('managed_receipt_parent_sha','')}`",
        f"- authorization_expired: `{classification.get('authorization_expired', False)}`",
        f"- artifact: `{result.get('pipeline_artifact_path','')}`",
        f"- receipt: `{result.get('receipt_path','')}`",
    ])
    if result.get("sub_receipt_path"):
        lines.append(f"- sub_receipt: `{result['sub_receipt_path']}`")
    if not result.get("ok") and result.get("reason_refused"):
        lines.append(f"- reason_refused: `{result['reason_refused']}`")
    return "\n".join(lines) + "\n"


def _receipt(
    context: AutoRecoveryContext,
    *,
    chosen_action: str,
    reason: str,
    new_state: str,
    classification: str = "",
    sub_receipt_path: str = "",
) -> PipelineAutoRecoveryReceipt:
    return PipelineAutoRecoveryReceipt(
        classification=classification or context.classification.classification,
        chosen_action=chosen_action,
        reason=reason,
        pipeline_id=context.pipeline_id or "unknown",
        previous_state=context.previous_state,
        new_state=new_state,
        operator_actor=context.operator_actor,
        generated_at_utc=datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
        artifact_paths=(str(context.paths.pipeline_path),),
        sub_receipt_path=sub_receipt_path,
    )


def _base_result(
    context: AutoRecoveryContext,
    *,
    ok: bool,
    chosen_action: str,
    new_state: str,
    receipt_path: Path,
) -> dict[str, Any]:
    return dict((
        ("ok", ok),
        ("action", "auto-recover"),
        ("classification", context.classification.to_dict()),
        ("chosen_action", chosen_action),
        ("pipeline_id", context.pipeline_id),
        ("previous_state", context.previous_state),
        ("new_state", new_state),
        ("pipeline_artifact_path", str(context.paths.pipeline_path)),
        ("receipt_path", str(receipt_path)),
    ))
