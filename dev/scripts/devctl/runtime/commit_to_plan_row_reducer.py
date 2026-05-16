"""Reduce proven commits back into typed master-plan row state."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from .feature_proof_receipt import FeatureProofReceipt
from .master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL, PlanRow
from .master_plan_store import read_plan_rows_jsonl, upsert_plan_row_jsonl
from .relaunch_loop_store import append_jsonl
from .value_coercion import coerce_string

PLAN_ROW_CLOSURE_RECEIPT_CONTRACT_ID = "PlanRowClosureReceipt"
PLAN_ROW_CLOSURE_RECEIPT_SCHEMA_VERSION = 1
DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_STORE_REL = (
    "dev/state/plan_row_closure_receipts.jsonl"
)

TRANSITIONABLE_PLAN_ROW_STATUSES = frozenset({"queued", "in_progress", "open"})
APPLIED_PLAN_ROW_STATUSES = frozenset({"applied", "completed"})


@dataclass(frozen=True, slots=True)
class PlanRowClosureReceipt:
    """Evidence that a proven commit was reduced into a PlanRow transition."""

    contract_id: ClassVar[str] = PLAN_ROW_CLOSURE_RECEIPT_CONTRACT_ID
    schema_version: ClassVar[int] = PLAN_ROW_CLOSURE_RECEIPT_SCHEMA_VERSION

    receipt_id: str
    plan_row_id: str
    commit_sha: str
    feature_proof_receipt_path: str
    previous_status: str
    next_status: str
    outcome: str
    commit_anchor_ref: str
    applied_at_utc: str
    plan_index_path: str
    reducer: str = "commit_to_plan_row_reducer"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["contract_id"] = self.contract_id
        payload["schema_version"] = self.schema_version
        return payload


@dataclass(frozen=True, slots=True)
class CommitToPlanRowReductionResult:
    """Bounded result for one commit-to-plan-row reduction attempt."""

    ok: bool
    plan_row_id: str
    commit_sha: str
    outcome: str
    changed: bool = False
    plan_index_path: str = ""
    receipt_path: str = ""
    warning: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def reduce_feature_proof_to_plan_rows(
    *,
    repo_root: Path,
    feature_proof: FeatureProofReceipt,
    feature_ids: tuple[str, ...],
    feature_proof_receipt_path: str,
    plan_index_relpath: str = DEFAULT_MASTER_PLAN_STORE_REL,
    receipt_store_relpath: str = DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_STORE_REL,
) -> tuple[CommitToPlanRowReductionResult, ...]:
    """Apply one FeatureProofReceipt to every matching plan row id."""

    commit_sha = coerce_string(feature_proof.commit_sha)
    row_ids = _unique_refs((*feature_ids, feature_proof.feature_id))
    if not commit_sha or not row_ids:
        return ()
    plan_index_path = repo_root / plan_index_relpath
    receipt_store_path = repo_root / receipt_store_relpath
    if not plan_index_path.exists():
        return tuple(
            CommitToPlanRowReductionResult(
                ok=True,
                plan_row_id=row_id,
                commit_sha=commit_sha,
                outcome="plan_index_missing",
                plan_index_path=_display_path(plan_index_path, repo_root),
                warning="plan_index_missing",
            )
            for row_id in row_ids
        )

    rows = read_plan_rows_jsonl(plan_index_path)
    by_id = {row.row_id: row for row in rows}
    results: list[CommitToPlanRowReductionResult] = []
    applied_at_utc = feature_proof.proven_at_utc or _now_utc()
    for row_id in row_ids:
        existing = by_id.get(row_id)
        if existing is None:
            receipt = _closure_receipt(
                row_id=row_id,
                commit_sha=commit_sha,
                feature_proof_receipt_path=feature_proof_receipt_path,
                previous_status="",
                next_status="",
                outcome="plan_row_missing",
                applied_at_utc=applied_at_utc,
                plan_index_path=_display_path(plan_index_path, repo_root),
            )
            append_plan_row_closure_receipt(receipt_store_path, receipt)
            results.append(
                CommitToPlanRowReductionResult(
                    ok=True,
                    plan_row_id=row_id,
                    commit_sha=commit_sha,
                    outcome=receipt.outcome,
                    plan_index_path=_display_path(plan_index_path, repo_root),
                    receipt_path=_display_path(receipt_store_path, repo_root),
                    warning="plan_row_missing",
                )
            )
            continue

        updated, outcome = _row_with_commit_closure(
            existing,
            commit_sha=commit_sha,
            applied_at_utc=applied_at_utc,
            feature_proof_receipt_path=feature_proof_receipt_path,
        )
        changed = updated.to_dict() != existing.to_dict()
        if changed:
            upsert_plan_row_jsonl(plan_index_path, updated)
            by_id[row_id] = updated
        receipt = _closure_receipt(
            row_id=row_id,
            commit_sha=commit_sha,
            feature_proof_receipt_path=feature_proof_receipt_path,
            previous_status=existing.status,
            next_status=updated.status,
            outcome=outcome,
            applied_at_utc=updated.applied_at_utc or applied_at_utc,
            plan_index_path=_display_path(plan_index_path, repo_root),
        )
        append_plan_row_closure_receipt(receipt_store_path, receipt)
        results.append(
            CommitToPlanRowReductionResult(
                ok=True,
                plan_row_id=row_id,
                commit_sha=commit_sha,
                outcome=outcome,
                changed=changed,
                plan_index_path=_display_path(plan_index_path, repo_root),
                receipt_path=_display_path(receipt_store_path, repo_root),
            )
        )
    return tuple(results)


def transition_plan_row_to_applied(
    row: PlanRow,
    *,
    commit_sha: str,
    applied_at_utc: str,
    feature_proof_receipt_path: str = "",
) -> PlanRow:
    """Return `row` transitioned to applied with commit closure evidence."""

    return _with_commit_metadata(
        replace(row, status="applied"),
        commit_sha=commit_sha,
        applied_at_utc=applied_at_utc,
        feature_proof_receipt_path=feature_proof_receipt_path,
    )


def append_plan_row_closure_receipt(
    path: Path,
    receipt: PlanRowClosureReceipt,
) -> str:
    """Append one PlanRowClosureReceipt and return the store path."""

    append_jsonl(path, receipt.to_dict())
    return str(path)


def _row_with_commit_closure(
    row: PlanRow,
    *,
    commit_sha: str,
    applied_at_utc: str,
    feature_proof_receipt_path: str,
) -> tuple[PlanRow, str]:
    if row.status in TRANSITIONABLE_PLAN_ROW_STATUSES:
        return (
            transition_plan_row_to_applied(
                row,
                commit_sha=commit_sha,
                applied_at_utc=applied_at_utc,
                feature_proof_receipt_path=feature_proof_receipt_path,
            ),
            "transitioned_to_applied",
        )
    if row.status in APPLIED_PLAN_ROW_STATUSES:
        updated = _with_commit_metadata(
            row,
            commit_sha=commit_sha,
            applied_at_utc=applied_at_utc,
            feature_proof_receipt_path=feature_proof_receipt_path,
        )
        if updated.to_dict() == row.to_dict():
            return row, "already_applied"
        return updated, "applied_metadata_hydrated"
    return row, "status_not_transitionable"


def _with_commit_metadata(
    row: PlanRow,
    *,
    commit_sha: str,
    applied_at_utc: str,
    feature_proof_receipt_path: str,
) -> PlanRow:
    commit_anchor_ref = f"commit:{commit_sha}"
    evidence_refs = (
        commit_anchor_ref,
        f"feature_proof_receipt:{feature_proof_receipt_path}"
        if feature_proof_receipt_path
        else "",
    )
    return replace(
        row,
        commit_anchor_ref=row.commit_anchor_ref or commit_anchor_ref,
        applied_at_utc=row.applied_at_utc or applied_at_utc,
        anchor_refs=_unique_refs((*row.anchor_refs, commit_anchor_ref)),
        work_evidence_ids=_unique_refs((*row.work_evidence_ids, *evidence_refs)),
    )


def _closure_receipt(
    *,
    row_id: str,
    commit_sha: str,
    feature_proof_receipt_path: str,
    previous_status: str,
    next_status: str,
    outcome: str,
    applied_at_utc: str,
    plan_index_path: str,
) -> PlanRowClosureReceipt:
    commit_anchor_ref = f"commit:{commit_sha}" if commit_sha else ""
    digest = hashlib.sha256(
        "|".join(
            (
                row_id,
                commit_sha,
                feature_proof_receipt_path,
                previous_status,
                next_status,
                outcome,
                applied_at_utc,
            )
        ).encode("utf-8")
    ).hexdigest()[:16]
    return PlanRowClosureReceipt(
        receipt_id=f"plan-row-closure:{row_id}:{commit_sha}:{digest}",
        plan_row_id=row_id,
        commit_sha=commit_sha,
        feature_proof_receipt_path=feature_proof_receipt_path,
        previous_status=previous_status,
        next_status=next_status,
        outcome=outcome,
        commit_anchor_ref=commit_anchor_ref,
        applied_at_utc=applied_at_utc,
        plan_index_path=plan_index_path,
    )


def _unique_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in values:
        ref = coerce_string(value)
        if not ref or ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return tuple(refs)


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "APPLIED_PLAN_ROW_STATUSES",
    "DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_STORE_REL",
    "PLAN_ROW_CLOSURE_RECEIPT_CONTRACT_ID",
    "PLAN_ROW_CLOSURE_RECEIPT_SCHEMA_VERSION",
    "TRANSITIONABLE_PLAN_ROW_STATUSES",
    "CommitToPlanRowReductionResult",
    "PlanRowClosureReceipt",
    "append_plan_row_closure_receipt",
    "reduce_feature_proof_to_plan_rows",
    "transition_plan_row_to_applied",
]
