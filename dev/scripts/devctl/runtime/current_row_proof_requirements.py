"""Proof requirement rows for current-row proof mode."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .current_row_proof_config import (
    REQUIRED_DOGFOOD_COMMANDS,
    REQUIRED_GUARD_IDS,
)
from .current_row_proof_utils import ProofUtils as U


def proof_requirements(
    *,
    plan_row: Mapping[str, object],
    snapshot: Mapping[str, object],
    ingestion_receipt: Mapping[str, object],
    guard_statuses: Mapping[str, Mapping[str, object]],
    dogfood_statuses: Mapping[str, object],
    final_gate_status: Mapping[str, object],
    feature_proof: Mapping[str, object],
    closure: Mapping[str, object],
    collaboration: Mapping[str, object],
) -> list[dict[str, object]]:
    def requirement(
        requirement_id: str,
        description: str,
        command: str,
        status: str,
        proof_ref: str,
    ) -> dict[str, object]:
        return {
            "id": requirement_id,
            "description": description,
            "command": command,
            "status": status,
            "proof_ref": proof_ref,
        }

    rows = [
        requirement(
            "plan_row",
            "PlanRow exists and is current-row typed state.",
            "typed_state:dev/state/plan_index.jsonl",
            "passed" if plan_row else "missing",
            "dev/state/plan_index.jsonl",
        ),
        requirement(
            "source_snapshot",
            "PlanSourceSnapshot captures the staging source hash.",
            "typed_state:dev/state/plan_source_snapshots.jsonl",
            "passed" if snapshot else "missing",
            str(snapshot.get("snapshot_id") or ""),
        ),
        requirement(
            "ingestion_receipt",
            "PlanIntentIngestionReceipt amends the existing current row.",
            "typed_state:dev/state/plan_ingestion_receipts.jsonl",
            "passed" if ingestion_receipt else "missing",
            str(ingestion_receipt.get("receipt_id") or ""),
        ),
    ]
    for guard_id in REQUIRED_GUARD_IDS:
        status = guard_statuses.get(guard_id, {})
        rows.append(
            requirement(
                guard_id,
                f"{guard_id} typed guard output passed.",
                U.guard_command(guard_id),
                str(status.get("status") or "missing"),
                str(status.get("proof_ref") or ""),
            )
        )
    rows.extend(
        [
            requirement(
                "dogfood",
                "Required dogfood route passed for the current row.",
                REQUIRED_DOGFOOD_COMMANDS[0],
                str(dogfood_statuses.get("status") or "missing"),
                str(dogfood_statuses.get("proof_ref") or ""),
            ),
            requirement(
                "typed_collaboration",
                "Claude/Codex collaboration proof is typed packet/session evidence.",
                "typed_state:review_channel",
                str(collaboration.get("status") or "missing"),
                str(collaboration.get("proof_ref") or ""),
            ),
            requirement(
                "feature_proof_receipt",
                "FeatureProofReceipt(proven_passed) names the exact pytest node id.",
                "typed_state:dev/reports/feature_proof_receipts",
                str(feature_proof.get("status") or "missing"),
                str(feature_proof.get("receipt_id") or ""),
            ),
            requirement(
                "final_gate",
                "Final response gate is satisfied after proof bundle completion.",
                "python3 dev/scripts/devctl.py develop next --actor codex "
                "--enforce-final-response-gate --format json",
                str(final_gate_status.get("status") or "missing"),
                str(final_gate_status.get("proof_ref") or ""),
            ),
            requirement(
                "closure_receipt",
                "PlanRowClosureReceipt records successful typed closure.",
                "typed_state:dev/state/plan_row_closure_receipts.jsonl",
                str(closure.get("status") or "missing"),
                str(closure.get("receipt_id") or ""),
            ),
        ]
    )
    return rows


def execution_items() -> list[dict[str, object]]:
    return [
        {"id": guard_id, "kind": "guard", "command": U.guard_command(guard_id)}
        for guard_id in REQUIRED_GUARD_IDS
    ] + [
        {"id": "dogfood", "kind": "dogfood", "command": REQUIRED_DOGFOOD_COMMANDS[0]},
        {
            "id": "final_gate",
            "kind": "final_gate",
            "command": (
                "python3 dev/scripts/devctl.py develop next --actor codex "
                "--enforce-final-response-gate --format json"
            ),
        },
    ]


def failures_from_requirements(requirements: Sequence[Mapping[str, object]]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for requirement in requirements:
        if requirement.get("status") == "passed":
            continue
        reason = f"{requirement.get('id')}_missing_typed_proof"
        if requirement.get("status") == "failed":
            reason = f"{requirement.get('id')}_failed"
        elif requirement.get("status") == "blocked":
            reason = f"{requirement.get('id')}_blocked"
        failures.append(
            failure(
                reason,
                f"{requirement.get('description')} Status={requirement.get('status')!r}.",
                "Provide typed proof evidence; do not mark markdown checkboxes manually.",
                str(requirement.get("id") or ""),
            )
        )
    return failures


def next_bounded_command(
    requirements: Sequence[Mapping[str, object]],
    failures: Sequence[Mapping[str, object]],
) -> str:
    if not failures:
        return ""
    failed_id = str(failures[0].get("target") or "")
    for requirement in requirements:
        if str(requirement.get("id") or "") == failed_id:
            return str(requirement.get("command") or "")
    return "python3 dev/scripts/checks/check_current_row_proof_bundle.py --format json"


def failure(reason: str, detail: str, remediation: str, target: str) -> dict[str, str]:
    return {
        "reason": reason,
        "detail": detail,
        "remediation": remediation,
        "target": target,
    }
