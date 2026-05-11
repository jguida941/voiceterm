"""Operator-runnable typed demos for governance repair slices."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from ..common import add_standard_output_arguments, write_output
from .development.final_response_gate import enforce_final_response_gate
from .development.orchestration_models import (
    DevelopmentContinuationRequiredSignal,
)
from ..runtime.agent_loop_operator_override import (
    AgentLoopOperatorOverride,
    EDIT_ONLY_AUTHORITY_SOURCE,
    EDIT_ONLY_EFFECTIVE_ROLE,
    EDIT_ONLY_EFFECTIVE_WORKSTREAM,
    EDIT_ONLY_OVERRIDE_SCOPE,
    OPERATOR_OVERRIDE_REQUESTOR,
    OPERATOR_OVERRIDE_SOURCE,
)

DEMO_REPORT_CONTRACT_ID = "DevctlDemoVerificationReport"
DEMO_REPORT_SCHEMA_VERSION = 1


def add_parser(sub) -> None:
    """Register the ``demo`` subcommand."""
    cmd = sub.add_parser(
        "demo",
        help="Run operator-facing typed verification demos.",
    )
    cmd.add_argument(
        "action",
        choices=("verify-override", "verify-final-response-gate"),
        help="Demo to run.",
    )
    cmd.add_argument(
        "--reason",
        default="operator demo verification",
        help="Reason text used in the typed demo receipt.",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md"),
        default_format="md",
    )


def run(args: Any) -> int:
    """Run one typed demo and return nonzero when its proof fails."""
    if args.action == "verify-override":
        report = _verify_override(args)
    else:
        report = _verify_final_response_gate(args)
    output = json.dumps(report, indent=2) if args.format == "json" else _render_md(report)
    write_output(output, getattr(args, "output", None))
    return 0 if report["ok"] else 1


def _verify_override(args: Any) -> dict[str, object]:
    override = AgentLoopOperatorOverride(
        requested=True,
        active=True,
        state="active",
        source=OPERATOR_OVERRIDE_SOURCE,
        requested_by=OPERATOR_OVERRIDE_REQUESTOR,
        scope=EDIT_ONLY_OVERRIDE_SCOPE,
        reason=str(args.reason or "").strip(),
        target_kind="packet",
        target_ref="demo_packet",
        effective_actor_role=EDIT_ONLY_EFFECTIVE_ROLE,
        effective_workstream_id=EDIT_ONLY_EFFECTIVE_WORKSTREAM,
        effective_authority_source=EDIT_ONLY_AUTHORITY_SOURCE,
        allowed_actions=("implementation.edit",),
        blocked_actions=("vcs.stage", "vcs.commit", "vcs.push"),
    )
    ok = (
        override.edit_allowed
        and "implementation.edit" in override.allowed_actions
        and {"vcs.stage", "vcs.commit", "vcs.push"}.issubset(
            set(override.blocked_actions)
        )
    )
    return _base_report(
        action="verify-override",
        ok=ok,
        proof={
            "operator_override": override.to_dict(),
            "edit_allowed": override.edit_allowed,
            "stage_blocked": "vcs.stage" in override.blocked_actions,
            "commit_blocked": "vcs.commit" in override.blocked_actions,
            "push_blocked": "vcs.push" in override.blocked_actions,
        },
    )


def _verify_final_response_gate(args: Any) -> dict[str, object]:
    continuation = DevelopmentContinuationRequiredSignal(
        continuation_required=True,
        status="continue_required",
        final_response_allowed=False,
        final_response_gate_allowed=False,
        required_final_response_action="run_next_command",
        reasons=("demo_continuation_required",),
        next_required_command=(
            "python3 dev/scripts/devctl.py develop next --actor codex --format md"
        ),
        summary="Final response denied until the typed continuation command runs.",
    )
    gate = enforce_final_response_gate(continuation)
    ok = (
        not gate.allow_final_response
        and gate.next_required_command == continuation.next_required_command
    )
    return _base_report(
        action="verify-final-response-gate",
        ok=ok,
        proof={
            "continuation": asdict(continuation),
            "final_response_gate": gate.to_dict(),
            "reason": str(args.reason or "").strip(),
        },
    )


def _base_report(
    *,
    action: str,
    ok: bool,
    proof: dict[str, object],
) -> dict[str, object]:
    return {
        "contract_id": DEMO_REPORT_CONTRACT_ID,
        "schema_version": DEMO_REPORT_SCHEMA_VERSION,
        "command": "demo",
        "action": action,
        "ok": ok,
        "receipt": {
            "contract_id": "DemoValidationReceipt",
            "schema_version": 1,
            "action": action,
            "proof_state": "satisfied" if ok else "missing",
        },
        "proof": proof,
    }


def _render_md(report: dict[str, object]) -> str:
    receipt = report["receipt"] if isinstance(report.get("receipt"), dict) else {}
    lines = [
        "# devctl demo",
        "",
        f"- ok: {report.get('ok')}",
        f"- action: {report.get('action')}",
        f"- receipt_contract: {receipt.get('contract_id') or '(none)'}",
        f"- proof_state: {receipt.get('proof_state') or '(none)'}",
    ]
    proof = report.get("proof")
    if isinstance(proof, dict):
        lines.extend(["", "## Proof", ""])
        for key, value in proof.items():
            if isinstance(value, (dict, list, tuple)):
                lines.append(f"- {key}: {json.dumps(value, sort_keys=True)}")
            else:
                lines.append(f"- {key}: {value}")
    return "\n".join(lines)


__all__ = ["add_parser", "run"]
