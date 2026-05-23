"""`devctl receipt-steward claim` action (A38.2 S2).

Drives the typed `ReceiptStewardScopeClaim` lifecycle: request, extend,
release. Persists each transition to
`dev/state/receipt_steward_claims.jsonl` via the shared
`append_json_mapping` writer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...common import add_standard_output_arguments, display_path, resolve_repo_path
from ...config import REPO_ROOT
from ...runtime.receipt_steward_scope_claim import (
    DEFAULT_RECEIPT_STEWARD_CLAIM_STORE_REL,
    DEFAULT_RECEIPT_STEWARD_TTL_MINUTES,
    ReceiptStewardScopeClaim,
    build_scope_claim,
    evaluate_scope_claim,
    extend_scope_claim,
    release_scope_claim,
    request_scope_claim,
)
from ...runtime.state_store_authority import append_json_mapping

_CLAIM_ACTIONS = ("request", "extend", "release")


def add_claim_parser(action_sub: Any) -> None:
    """Register the `claim` sub-action."""
    claim = action_sub.add_parser(
        "claim",
        help="Manage the typed ReceiptStewardScopeClaim lifecycle.",
    )
    claim.add_argument(
        "--action",
        choices=_CLAIM_ACTIONS,
        required=True,
        help="request | extend | release",
    )
    claim.add_argument(
        "--ttl-minutes",
        type=int,
        default=DEFAULT_RECEIPT_STEWARD_TTL_MINUTES,
        help=(
            "Bounded TTL in minutes for request/extend "
            f"(default {DEFAULT_RECEIPT_STEWARD_TTL_MINUTES})."
        ),
    )
    claim.add_argument(
        "--reason",
        default="receipt-steward audit invocation",
        help="Typed reason recorded on the claim request.",
    )
    claim.add_argument(
        "--actor-session-id",
        default="receipt-steward-cli",
        help="Actor session id requesting the claim.",
    )
    claim.add_argument(
        "--claim-id",
        default="",
        help="Active claim id (required for extend/release).",
    )
    claim.add_argument(
        "--granted-by",
        choices=("auto", "operator"),
        default="auto",
        help="Evaluator role; `operator` bypasses default-scope subset check.",
    )
    claim.add_argument(
        "--expiry-reason",
        choices=("ttl_elapsed", "operator_revoked", "released_by_actor"),
        default="released_by_actor",
        help="Reason recorded on release (only used with --action release).",
    )
    claim.add_argument(
        "--store-path",
        default=str(DEFAULT_RECEIPT_STEWARD_CLAIM_STORE_REL),
        help="JSONL store path (default dev/state/receipt_steward_claims.jsonl).",
    )
    add_standard_output_arguments(
        claim,
        format_choices=("json", "md"),
        default_format="json",
    )


def claim_action(args: Any) -> tuple[dict[str, object], int]:
    """Run one claim lifecycle transition."""
    action = str(getattr(args, "action", "") or "").strip()
    store_path = resolve_repo_path(
        getattr(args, "store_path", "") or str(DEFAULT_RECEIPT_STEWARD_CLAIM_STORE_REL),
        DEFAULT_RECEIPT_STEWARD_CLAIM_STORE_REL,
        repo_root=REPO_ROOT,
    )
    try:
        if action == "request":
            return _request_claim(args, store_path)
        if action == "extend":
            return _extend_claim(args, store_path)
        if action == "release":
            return _release_claim(args, store_path)
    except ValueError as exc:
        return (
            {
                "command": "receipt-steward",
                "action": f"claim:{action}",
                "ok": False,
                "error": str(exc),
                "store_path": display_path(store_path),
            },
            1,
        )
    return (
        {
            "command": "receipt-steward",
            "action": f"claim:{action}",
            "ok": False,
            "error": "unknown_claim_action",
        },
        1,
    )


def _request_claim(args: Any, store_path: Path) -> tuple[dict[str, object], int]:
    request = request_scope_claim(
        actor_role="receipt_steward",
        actor_session_id=str(getattr(args, "actor_session_id", "") or ""),
        reason=str(getattr(args, "reason", "") or ""),
        requested_ttl_minutes=int(getattr(args, "ttl_minutes", DEFAULT_RECEIPT_STEWARD_TTL_MINUTES) or 0),
    )
    evaluation = evaluate_scope_claim(
        request,
        granted_by_role=str(getattr(args, "granted_by", "auto") or "auto"),
    )
    if not evaluation.granted:
        write_eval = append_json_mapping(
            store_path,
            _row_for_request_only(request, evaluation),
            store_id="ReceiptStewardScopeClaim",
        )
        return (
            {
                "command": "receipt-steward",
                "action": "claim:request",
                "ok": False,
                "error": "claim_denied",
                "denial_reason": evaluation.denial_reason,
                "store_path": display_path(store_path),
                "write_result": write_eval.to_dict(),
            },
            1,
        )
    claim = build_scope_claim(request, evaluation)
    row = _row_for_granted_claim(request, evaluation, claim)
    write_result = append_json_mapping(
        store_path,
        row,
        store_id="ReceiptStewardScopeClaim",
    )
    return (
        {
            "command": "receipt-steward",
            "action": "claim:request",
            "ok": True,
            "claim_id": claim.claim_id,
            "request_id": request.request_id,
            "evaluation_id": evaluation.evaluation_id,
            "actor_session_id": claim.actor_session_id,
            "issued_at_utc": claim.issued_at_utc,
            "expiry_utc": claim.expiry_utc,
            "scope_paths": list(claim.scope_paths),
            "store_path": display_path(store_path),
            "write_result": write_result.to_dict(),
        },
        0,
    )


def _extend_claim(args: Any, store_path: Path) -> tuple[dict[str, object], int]:
    claim = _load_active_claim_by_id(
        store_path,
        claim_id=str(getattr(args, "claim_id", "") or ""),
    )
    if claim is None:
        return (
            {
                "command": "receipt-steward",
                "action": "claim:extend",
                "ok": False,
                "error": "active_claim_not_found",
                "store_path": display_path(store_path),
            },
            1,
        )
    additional_minutes = int(getattr(args, "ttl_minutes", DEFAULT_RECEIPT_STEWARD_TTL_MINUTES) or 0)
    extended = extend_scope_claim(claim, additional_minutes=additional_minutes)
    row = {
        "lifecycle_phase": "claim_extension",
        "claim": extended.to_dict(),
        "previous_expiry_utc": claim.expiry_utc,
    }
    write_result = append_json_mapping(
        store_path,
        row,
        store_id="ReceiptStewardScopeClaim",
    )
    return (
        {
            "command": "receipt-steward",
            "action": "claim:extend",
            "ok": True,
            "claim_id": extended.claim_id,
            "previous_expiry_utc": claim.expiry_utc,
            "expiry_utc": extended.expiry_utc,
            "store_path": display_path(store_path),
            "write_result": write_result.to_dict(),
        },
        0,
    )


def _release_claim(args: Any, store_path: Path) -> tuple[dict[str, object], int]:
    claim = _load_active_claim_by_id(
        store_path,
        claim_id=str(getattr(args, "claim_id", "") or ""),
    )
    if claim is None:
        return (
            {
                "command": "receipt-steward",
                "action": "claim:release",
                "ok": False,
                "error": "active_claim_not_found",
                "store_path": display_path(store_path),
            },
            1,
        )
    released, expiry = release_scope_claim(
        claim,
        expiry_reason=str(getattr(args, "expiry_reason", "released_by_actor") or "released_by_actor"),
    )
    row = {
        "lifecycle_phase": "claim_release",
        "claim": released.to_dict(),
        "expiry": expiry.to_dict(),
    }
    write_result = append_json_mapping(
        store_path,
        row,
        store_id="ReceiptStewardScopeClaim",
    )
    return (
        {
            "command": "receipt-steward",
            "action": "claim:release",
            "ok": True,
            "claim_id": released.claim_id,
            "expiry_id": expiry.expiry_id,
            "expired_at_utc": expiry.expired_at_utc,
            "expiry_reason": expiry.expiry_reason,
            "status": released.status,
            "store_path": display_path(store_path),
            "write_result": write_result.to_dict(),
        },
        0,
    )


def _row_for_request_only(request, evaluation) -> dict[str, object]:
    return {
        "lifecycle_phase": "claim_request_denied",
        "request": request.to_dict(),
        "evaluation": evaluation.to_dict(),
    }


def _row_for_granted_claim(request, evaluation, claim) -> dict[str, object]:
    return {
        "lifecycle_phase": "claim_granted",
        "request": request.to_dict(),
        "evaluation": evaluation.to_dict(),
        "claim": claim.to_dict(),
    }


def _load_active_claim_by_id(
    store_path: Path, *, claim_id: str
) -> ReceiptStewardScopeClaim | None:
    if not claim_id:
        return None
    if not store_path.exists():
        return None
    try:
        text = store_path.read_text(encoding="utf-8")
    except OSError:
        return None
    latest: ReceiptStewardScopeClaim | None = None
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        candidate = row.get("claim") if isinstance(row, dict) else None
        if not isinstance(candidate, dict):
            continue
        if str(candidate.get("claim_id") or "") != claim_id:
            continue
        latest = ReceiptStewardScopeClaim.from_mapping(candidate)
    if latest is None:
        return None
    if latest.status != "active":
        return None
    return latest


def render_claim_markdown(report: dict[str, object]) -> str:
    lines = ["# devctl receipt-steward claim", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- action: {report.get('action', '')}")
    if report.get("claim_id"):
        lines.append(f"- claim_id: {report.get('claim_id')}")
    if report.get("expiry_utc"):
        lines.append(f"- expiry_utc: {report.get('expiry_utc')}")
    if report.get("status"):
        lines.append(f"- status: {report.get('status')}")
    if report.get("store_path"):
        lines.append(f"- store_path: {report.get('store_path')}")
    if report.get("error"):
        lines.append(f"- error: {report.get('error')}")
    return "\n".join(lines) + "\n"


__all__ = ["add_claim_parser", "claim_action", "render_claim_markdown"]
