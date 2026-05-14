"""Command surface for governed bypass lifecycle receipts."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ...common import (
    add_standard_output_arguments,
    display_path,
    emit_output,
    resolve_repo_path,
    write_output,
)
from ...config import REPO_ROOT
from ...runtime.lifetime_bypass_mode import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    BypassAuthorityScope,
    BypassEvaluationInput,
    BypassRequest,
    active_bypass_lifecycle_for_receipt_id,
    evaluate_bypass_request,
)
from ...runtime.classifier_safety_attestation import (
    DEFAULT_CLAUDE_SETTINGS_LOCAL_REL,
    ClassifierSafetyAttestation,
    build_classifier_safety_attestation,
    project_classifier_safety_attestation,
)
from ...runtime.state_store_authority import append_json_mapping

_SCOPE_BY_CLI_VALUE = {
    "edit-only": BypassAuthorityScope.EDIT_ONLY,
    "edit-and-commit": BypassAuthorityScope.EDIT_AND_COMMIT,
    "edit-commit-and-publish": BypassAuthorityScope.EDIT_COMMIT_AND_PUSH,
}


def add_parser(sub) -> None:
    """Register the ``bypass`` command."""
    parser = sub.add_parser(
        "bypass",
        help="Issue governed BypassLifecycle receipts",
    )
    action_sub = parser.add_subparsers(dest="bypass_action", required=True)
    grant = action_sub.add_parser(
        "grant",
        help="Grant and persist a typed BypassLifecycle receipt",
    )
    grant.add_argument(
        "--scope",
        choices=tuple(_SCOPE_BY_CLI_VALUE),
        required=True,
        help="Bounded bypass authority scope to grant.",
    )
    grant.add_argument(
        "--reason",
        required=True,
        help="Typed operator reason for the bypass grant.",
    )
    grant.add_argument(
        "--evaluator-actor-id",
        default="operator",
        help="Actor evaluating and granting the bypass. Defaults to operator.",
    )
    grant.add_argument(
        "--request-id",
        default="",
        help="Optional stable request id. Defaults to a timestamped grant id.",
    )
    grant.add_argument(
        "--target-role",
        default="implementer",
        help="Target role for the bypass lifecycle.",
    )
    grant.add_argument(
        "--target-session-id",
        default="",
        help="Optional target session id for the bypass lifecycle.",
    )
    grant.add_argument(
        "--target-surface",
        default="review-channel-launch",
        help="Target surface expected to consume the bypass receipt.",
    )
    grant.add_argument(
        "--evidence-ref",
        action="append",
        default=None,
        help="Repeatable evidence ref attached to the bypass request.",
    )
    grant.add_argument(
        "--operator-signature",
        default="",
        help="Optional operator signature evidence. Defaults to evaluator actor id.",
    )
    grant.add_argument(
        "--ai-approval-evidence",
        default="",
        help="Optional AI-side approval evidence ref. Defaults to this CLI command.",
    )
    grant.add_argument(
        "--expires-in-hours",
        type=float,
        default=24.0,
        help="Receipt lifetime in hours. Use 0 for no explicit expiry.",
    )
    grant.add_argument(
        "--store-path",
        default=str(DEFAULT_BYPASS_LIFECYCLE_STORE_REL),
        help="Bypass lifecycle JSONL store path.",
    )
    grant.add_argument(
        "--classifier-settings-path",
        default=str(DEFAULT_CLAUDE_SETTINGS_LOCAL_REL),
        help=(
            "Claude settings.local.json path receiving the "
            "ClassifierSafetyAttestation projection."
        ),
    )
    grant.add_argument(
        "--skip-classifier-attestation",
        action="store_true",
        help="Persist the bypass lifecycle without updating Claude classifier settings.",
    )
    add_standard_output_arguments(
        grant,
        format_choices=("json", "md"),
        default_format="json",
    )

    attest = action_sub.add_parser(
        "attest",
        help="Project an active BypassLifecycle receipt into Claude settings",
    )
    attest.add_argument(
        "--receipt-id",
        required=True,
        help="Active typed BypassReceipt id to project.",
    )
    attest.add_argument(
        "--target-role",
        default="implementer",
        help="Target role for active lifecycle lookup.",
    )
    attest.add_argument(
        "--store-path",
        default=str(DEFAULT_BYPASS_LIFECYCLE_STORE_REL),
        help="Bypass lifecycle JSONL store path.",
    )
    attest.add_argument(
        "--classifier-settings-path",
        default=str(DEFAULT_CLAUDE_SETTINGS_LOCAL_REL),
        help="Claude settings.local.json path receiving the attestation projection.",
    )
    add_standard_output_arguments(
        attest,
        format_choices=("json", "md"),
        default_format="json",
    )


def run(args: Any) -> int:
    """Run one bypass command action."""
    action = str(getattr(args, "bypass_action", "") or "").strip()
    if action == "grant":
        report, rc = grant_action(args)
    elif action == "attest":
        report, rc = attest_action(args)
    else:
        report, rc = _error_report(action)

    output = json.dumps(report, indent=2, sort_keys=True)
    if getattr(args, "format", "json") != "json":
        output = _render_markdown(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return rc


def grant_action(args: Any) -> tuple[dict[str, object], int]:
    """Evaluate and persist one governed bypass lifecycle grant."""
    now = _now_utc()
    request_id = _request_id(args, now)
    evaluator_actor_id = _required_text(
        getattr(args, "evaluator_actor_id", ""),
        field="evaluator_actor_id",
    )
    reason = _required_text(getattr(args, "reason", ""), field="reason")
    store_path = resolve_repo_path(
        getattr(args, "store_path", ""),
        DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
        repo_root=REPO_ROOT,
    )
    request = BypassRequest(
        request_id=request_id,
        scope=_scope_from_args(args),
        reason=reason,
        actor=evaluator_actor_id,
        requested_at_utc=now,
        target_role=str(getattr(args, "target_role", "") or "").strip(),
        target_session_id=str(getattr(args, "target_session_id", "") or "").strip(),
        target_surface=str(getattr(args, "target_surface", "") or "").strip(),
        evidence_refs=tuple(
            ref.strip()
            for ref in getattr(args, "evidence_ref", ()) or ()
            if str(ref).strip()
        ),
    )
    evidence = BypassEvaluationInput(
        operator_signature=(
            str(getattr(args, "operator_signature", "") or "").strip()
            or evaluator_actor_id
        ),
        ai_approval_evidence=(
            str(getattr(args, "ai_approval_evidence", "") or "").strip()
            or f"devctl:bypass:grant:{request_id}"
        ),
        evaluated_at_utc=now,
        evaluator_actor_id=evaluator_actor_id,
        expires_at_utc=_expires_at_utc(args, now),
        policy_evidence_refs=("ProjectGovernance", "repo-pack-policy"),
    )
    lifecycle = evaluate_bypass_request(request, evidence)
    if lifecycle.receipt is None:
        return _denied_report(lifecycle, store_path), 1

    payload = lifecycle.to_dict()
    write_result = append_json_mapping(
        store_path,
        payload,
        store_id="BypassLifecycle",
    )
    classifier_report = _classifier_attestation_report(args, lifecycle)
    report = {
        "command": "bypass",
        "action": "grant",
        "ok": True,
        "receipt_id": lifecycle.receipt.receipt_id,
        "lifecycle_id": lifecycle.lifecycle_id,
        "state": lifecycle.state.value,
        "scope": lifecycle.receipt.requested_authority_scope.value,
        "expires_at_utc": lifecycle.receipt.expires_at_utc,
        "store_path": display_path(store_path),
        "write_result": write_result.to_dict(),
        "classifier_safety_attestation": classifier_report,
    }
    return report, 0 if classifier_report.get("ok") is not False else 1


def attest_action(args: Any) -> tuple[dict[str, object], int]:
    """Project an existing active bypass receipt into Claude settings."""
    receipt_id = _required_text(getattr(args, "receipt_id", ""), field="receipt_id")
    store_path = resolve_repo_path(
        getattr(args, "store_path", ""),
        DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
        repo_root=REPO_ROOT,
    )
    lifecycle = active_bypass_lifecycle_for_receipt_id(
        receipt_id,
        store_path=store_path,
        target_role=str(getattr(args, "target_role", "") or "").strip(),
        required_scope=BypassAuthorityScope.EDIT_ONLY,
    )
    if lifecycle is None:
        return (
            {
                "command": "bypass",
                "action": "attest",
                "ok": False,
                "error": "active_bypass_receipt_not_found",
                "receipt_id": receipt_id,
                "store_path": display_path(store_path),
            },
            1,
        )
    classifier_report = _classifier_attestation_report(args, lifecycle)
    return (
        {
            "command": "bypass",
            "action": "attest",
            "ok": classifier_report.get("ok") is not False,
            "receipt_id": receipt_id,
            "lifecycle_id": lifecycle.lifecycle_id,
            "store_path": display_path(store_path),
            "classifier_safety_attestation": classifier_report,
        },
        0 if classifier_report.get("ok") is not False else 1,
    )


def _error_report(action: str) -> tuple[dict[str, object], int]:
    return (
        {
            "command": "bypass",
            "action": action,
            "ok": False,
            "error": "unknown_bypass_action",
        },
        1,
    )


def _denied_report(lifecycle: Any, store_path: Path) -> dict[str, object]:
    return {
        "command": "bypass",
        "action": "grant",
        "ok": False,
        "lifecycle_id": lifecycle.lifecycle_id,
        "state": lifecycle.state.value,
        "reason": lifecycle.evaluation.reason if lifecycle.evaluation else "",
        "store_path": display_path(store_path),
    }


def _render_markdown(report: dict[str, object]) -> str:
    lines = ["# devctl bypass", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- action: {report.get('action')}")
    if report.get("receipt_id"):
        lines.append(f"- receipt_id: {report.get('receipt_id')}")
    if report.get("lifecycle_id"):
        lines.append(f"- lifecycle_id: {report.get('lifecycle_id')}")
    if report.get("state"):
        lines.append(f"- state: {report.get('state')}")
    if report.get("scope"):
        lines.append(f"- scope: {report.get('scope')}")
    if report.get("expires_at_utc"):
        lines.append(f"- expires_at_utc: {report.get('expires_at_utc')}")
    if report.get("store_path"):
        lines.append(f"- store_path: {report.get('store_path')}")
    classifier_report = report.get("classifier_safety_attestation")
    if isinstance(classifier_report, dict):
        lines.append(
            "- classifier_safety_attestation: "
            f"{classifier_report.get('attestation_id') or classifier_report.get('status') or classifier_report.get('error')}"
        )
    if report.get("reason"):
        lines.append(f"- reason: {report.get('reason')}")
    if report.get("error"):
        lines.append(f"- error: {report.get('error')}")
    return "\n".join(lines)


def _scope_from_args(args: Any) -> BypassAuthorityScope:
    raw_scope = str(getattr(args, "scope", "") or "").strip()
    try:
        return _SCOPE_BY_CLI_VALUE[raw_scope]
    except KeyError as exc:
        raise ValueError(f"unknown_bypass_scope: {raw_scope}") from exc


def _request_id(args: Any, now: str) -> str:
    raw = str(getattr(args, "request_id", "") or "").strip()
    if raw:
        return raw
    compact = (
        now.replace("-", "")
        .replace(":", "")
        .replace(".", "")
        .replace("Z", "")
    )
    return f"grant-{compact}"


def _expires_at_utc(args: Any, now: str) -> str:
    hours = float(getattr(args, "expires_in_hours", 24.0) or 0.0)
    if hours <= 0:
        return ""
    now_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
    return (now_dt + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _required_text(value: object, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field}_required")
    return text


def _classifier_attestation_report(
    args: Any,
    lifecycle: Any,
) -> dict[str, object]:
    if getattr(args, "skip_classifier_attestation", False):
        return {"ok": True, "status": "skipped"}
    raw_path = getattr(args, "classifier_settings_path", None)
    if raw_path is None:
        return {"ok": True, "status": "not_requested"}
    settings_path = resolve_repo_path(
        raw_path,
        DEFAULT_CLAUDE_SETTINGS_LOCAL_REL,
        repo_root=REPO_ROOT,
    )
    try:
        attestation: ClassifierSafetyAttestation | None = (
            build_classifier_safety_attestation(
                lifecycle,
                settings_path=settings_path,
            )
        )
        if attestation is None:
            return {
                "ok": False,
                "error": "active_bypass_lifecycle_required",
                "settings_path": display_path(settings_path),
            }
        write_result = project_classifier_safety_attestation(
            settings_path,
            attestation,
        )
    except (OSError, ValueError) as exc:
        return {
            "ok": False,
            "error": str(exc),
            "settings_path": display_path(settings_path),
        }
    return {
        "ok": True,
        "attestation": attestation.to_dict(),
        **{
            key: (
                display_path(Path(value))
                if key in {"settings_path", "lock_path"} and isinstance(value, str)
                else value
            )
            for key, value in write_result.items()
        },
    }


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


__all__ = ["add_parser", "attest_action", "grant_action", "run"]
