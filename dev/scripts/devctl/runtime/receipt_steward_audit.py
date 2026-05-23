"""Receipt-steward audit engine (A38.2 S2 — pure-function reducer).

This module is the pure-function audit reducer the receipt-steward
role invokes per slice. It consumes typed inputs (slice_id,
plan_row_id, commit_sha, repo_root) plus an optional active scope
claim, performs the seven discovery + verification probes documented
in the role substrate, and returns a typed
:class:`ReceiptStewardAuditReceipt` (defined in the sibling
`receipt_steward_role` module).

All I/O happens here against the repo on disk, but no mutation: the
engine READS evidence and EMITS a typed observation. The CLI surface
that wraps this engine is responsible for persisting any audit
output; the engine never writes.

7-value missing_items taxonomy:

- ``missing_completely`` — FeatureProofReceipt absent for commit_sha
- ``missing_pytest_node`` — receipt present but no `::` node id in tests_run
- ``stale_commit_reference`` — receipt's commit_sha not in local git history
- ``dangling_plan_row`` — plan_row_id not found in plan_index.jsonl
- ``no_evidence_case`` — no matching `## Case` heading in evidence.md
- ``pytest_node_unresolvable`` — node id present but pytest --collect-only
  cannot resolve it (advisory only)
- ``dirty_tree_at_audit`` — worktree had uncommitted changes when audit ran
  (advisory only)
"""

from __future__ import annotations

import json
import secrets
import subprocess
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from .receipt_steward_role import (
    RECEIPT_STEWARD_ROLE_ID,
    ReceiptStewardAuditReceipt,
    ReceiptStewardAuditTargets,
)
from .receipt_steward_scope_claim import (
    ReceiptStewardScopeClaim,
    claim_is_active,
)


# Blocking taxonomy values.
MISSING_COMPLETELY = "missing_completely"
MISSING_PYTEST_NODE = "missing_pytest_node"
STALE_COMMIT_REFERENCE = "stale_commit_reference"
DANGLING_PLAN_ROW = "dangling_plan_row"
NO_EVIDENCE_CASE = "no_evidence_case"
# Advisory-only taxonomy values.
PYTEST_NODE_UNRESOLVABLE = "pytest_node_unresolvable"
DIRTY_TREE_AT_AUDIT = "dirty_tree_at_audit"

MISSING_ITEMS_TAXONOMY: tuple[str, ...] = (
    MISSING_COMPLETELY,
    MISSING_PYTEST_NODE,
    STALE_COMMIT_REFERENCE,
    DANGLING_PLAN_ROW,
    NO_EVIDENCE_CASE,
    PYTEST_NODE_UNRESOLVABLE,
    DIRTY_TREE_AT_AUDIT,
)

ADVISORY_MISSING_ITEMS: frozenset[str] = frozenset(
    {PYTEST_NODE_UNRESOLVABLE, DIRTY_TREE_AT_AUDIT}
)


def audit_slice(
    *,
    slice_id: str,
    plan_row_id: str,
    commit_sha: str,
    repo_root: Path,
    active_claim: ReceiptStewardScopeClaim | None = None,
    pytest_collect: bool = True,
) -> ReceiptStewardAuditReceipt:
    """Audit one slice and return a typed audit receipt.

    Fails closed by raising ``ValueError`` when ``active_claim`` is
    provided but inactive. Pass ``active_claim=None`` only from
    test/dogfood contexts that have already validated the claim
    upstream.
    """
    if active_claim is not None and not claim_is_active(active_claim):
        raise ValueError(
            "receipt_steward_audit_requires_active_claim:"
            f" claim_id={active_claim.claim_id!r}"
            f" status={active_claim.status!r}"
        )

    slice_id_text = (slice_id or "").strip()
    plan_row_id_text = (plan_row_id or "").strip()
    commit_sha_text = (commit_sha or "").strip()
    now = _now_utc()

    missing: list[str] = []

    # Step 1: FeatureProofReceipt discovery.
    fpr_path, fpr_payload = _discover_feature_proof_receipt(
        repo_root=repo_root,
        commit_sha=commit_sha_text,
    )
    receipt_present = fpr_payload is not None
    if not receipt_present:
        missing.append(MISSING_COMPLETELY)

    # Step 2: pytest node detection.
    tests_run = _tests_run_entries(fpr_payload)
    pytest_node_ids = _pytest_node_ids(tests_run)
    pytest_node_resolvable_flag = False
    if receipt_present:
        if not pytest_node_ids:
            missing.append(MISSING_PYTEST_NODE)
        else:
            pytest_node_resolvable_flag = True
            if pytest_collect and not _pytest_nodes_resolvable(
                repo_root=repo_root,
                node_ids=pytest_node_ids,
            ):
                missing.append(PYTEST_NODE_UNRESOLVABLE)
                pytest_node_resolvable_flag = False

    # Step 3: commit_sha presence in git history.
    commit_sha_linked = _commit_sha_in_git_history(
        repo_root=repo_root,
        commit_sha=commit_sha_text,
    )
    if commit_sha_text and not commit_sha_linked:
        missing.append(STALE_COMMIT_REFERENCE)

    # Step 4: plan_row presence in plan_index.jsonl.
    plan_row_linked = _plan_row_present(
        repo_root=repo_root,
        plan_row_id=plan_row_id_text,
    )
    if plan_row_id_text and not plan_row_linked:
        missing.append(DANGLING_PLAN_ROW)

    # Step 5: evidence.md case heading match.
    feature_id = _coerce_string(fpr_payload.get("feature_id")) if fpr_payload else ""
    evidence_case_resolvable = _evidence_case_heading_present(
        repo_root=repo_root,
        slice_id=slice_id_text,
        feature_id=feature_id,
    )
    if not evidence_case_resolvable:
        missing.append(NO_EVIDENCE_CASE)

    # Step 6: dirty-tree advisory.
    if _worktree_is_dirty(repo_root=repo_root):
        missing.append(DIRTY_TREE_AT_AUDIT)

    # Step 7: real-life test status sanity.
    real_life_status_valid = _real_life_status_valid(fpr_payload, pytest_node_ids)

    targets = ReceiptStewardAuditTargets(
        receipt_present=receipt_present,
        pytest_node_resolvable=pytest_node_resolvable_flag,
        commit_sha_linked=commit_sha_linked,
        plan_row_linked=plan_row_linked,
        evidence_path_resolvable=evidence_case_resolvable,
        real_life_test_status_valid=real_life_status_valid,
        status=_targets_status(missing),
    )

    audit_id = _build_audit_id(now)
    feature_proof_receipt_path = (
        str(_relative_to_repo(fpr_path, repo_root))
        if fpr_path is not None and receipt_present
        else ""
    )

    return ReceiptStewardAuditReceipt(
        audit_id=audit_id,
        slice_id=slice_id_text,
        plan_row_id=plan_row_id_text,
        commit_sha=commit_sha_text,
        audited_at_utc=now,
        targets=targets,
        missing_items=tuple(missing),
        feature_proof_receipt_path=feature_proof_receipt_path,
        actor_role=RECEIPT_STEWARD_ROLE_ID,
    )


def audit_recent_commits(
    *,
    repo_root: Path,
    since_commit: str,
    limit: int = 5,
    pytest_collect: bool = False,
) -> tuple[ReceiptStewardAuditReceipt, ...]:
    """Audit the most recent N commits walking back from HEAD.

    ``since_commit`` is exclusive: results stop once the walk reaches
    it. The reducer uses the FeatureProofReceipt found alongside each
    commit to populate the slice_id/plan_row_id when available; both
    fields fall back to empty when the receipt is absent or carries
    no plan-row context.
    """
    commits = _recent_commit_shas(
        repo_root=repo_root,
        since_commit=(since_commit or "").strip(),
        limit=max(1, int(limit)),
    )
    receipts: list[ReceiptStewardAuditReceipt] = []
    for sha in commits:
        fpr_path, fpr_payload = _discover_feature_proof_receipt(
            repo_root=repo_root,
            commit_sha=sha,
        )
        feature_id = (
            _coerce_string(fpr_payload.get("feature_id")) if fpr_payload else ""
        )
        plan_row_id = (
            _coerce_string(fpr_payload.get("plan_row_id")) if fpr_payload else ""
        )
        receipt = audit_slice(
            slice_id=feature_id,
            plan_row_id=plan_row_id,
            commit_sha=sha,
            repo_root=repo_root,
            pytest_collect=pytest_collect,
        )
        receipts.append(receipt)
    return tuple(receipts)


def build_audit_gap_report(
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Reduce plan_index.jsonl into a typed audit-gap report.

    Walks every PlanRow whose status is ``applied`` or ``completed``
    and whose ``commit_anchor_ref`` carries a SHA; tags rows where
    no paired FeatureProofReceipt exists.
    """
    plan_path = repo_root / "dev" / "state" / "plan_index.jsonl"
    fpr_dir = repo_root / "dev" / "reports" / "feature_proof_receipts"

    rows_without_receipts: list[dict[str, str]] = []
    rows_with_receipts: list[dict[str, str]] = []

    closing_statuses = {"applied", "completed"}
    if not plan_path.exists():
        return {
            "ok": False,
            "error": "plan_index_missing",
            "plan_index_path": str(plan_path),
            "rows_with_receipts": [],
            "rows_without_receipts": [],
        }

    for raw_line in plan_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        status = _coerce_string(row.get("status"))
        if status not in closing_statuses:
            continue
        commit_ref = _coerce_string(row.get("commit_anchor_ref"))
        if not commit_ref:
            continue
        sha = commit_ref.split(":", 1)[-1] if ":" in commit_ref else commit_ref
        sha = sha.strip()
        if not sha:
            continue
        receipt_path = fpr_dir / f"{sha}.json"
        entry = {
            "row_id": _coerce_string(row.get("row_id")),
            "commit_sha": sha,
            "status": status,
        }
        if receipt_path.exists() or any(fpr_dir.glob(f"{sha}*.json")):
            rows_with_receipts.append(entry)
        else:
            rows_without_receipts.append(entry)

    return {
        "ok": True,
        "plan_index_path": str(plan_path.relative_to(repo_root)),
        "fpr_dir_path": str(fpr_dir.relative_to(repo_root)),
        "rows_with_receipts": rows_with_receipts,
        "rows_without_receipts": rows_without_receipts,
        "coverage_pct": _coverage_pct(rows_with_receipts, rows_without_receipts),
    }


# ---------------------------------------------------------------------------
# Discovery + verification helpers (pure I/O, no mutation)
# ---------------------------------------------------------------------------


def _discover_feature_proof_receipt(
    *,
    repo_root: Path,
    commit_sha: str,
) -> tuple[Path | None, dict[str, object] | None]:
    if not commit_sha:
        return None, None
    fpr_dir = repo_root / "dev" / "reports" / "feature_proof_receipts"
    direct = fpr_dir / f"{commit_sha}.json"
    candidate: Path | None = direct if direct.exists() else None
    if candidate is None:
        # Tolerate `{sha}-suffix.json` variants observed in the directory.
        matches = sorted(fpr_dir.glob(f"{commit_sha}*.json"))
        candidate = matches[0] if matches else None
    if candidate is None:
        return None, None
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return candidate, None
    if not isinstance(payload, dict):
        return candidate, None
    return candidate, payload


def _tests_run_entries(payload: dict[str, object] | None) -> tuple[str, ...]:
    if not payload:
        return ()
    raw = payload.get("tests_run")
    if not isinstance(raw, list):
        return ()
    return tuple(str(item) for item in raw if str(item).strip())


def _pytest_node_ids(tests_run: Iterable[str]) -> tuple[str, ...]:
    return tuple(item for item in tests_run if "::" in item)


def _pytest_nodes_resolvable(
    *,
    repo_root: Path,
    node_ids: tuple[str, ...],
) -> bool:
    if not node_ids:
        return False
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "--collect-only", "-q", *node_ids],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _commit_sha_in_git_history(
    *,
    repo_root: Path,
    commit_sha: str,
) -> bool:
    if not commit_sha:
        return False
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{commit_sha}^{{commit}}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _plan_row_present(*, repo_root: Path, plan_row_id: str) -> bool:
    if not plan_row_id:
        return False
    plan_path = repo_root / "dev" / "state" / "plan_index.jsonl"
    if not plan_path.exists():
        return False
    try:
        for line in plan_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if _coerce_string(row.get("row_id")) == plan_row_id:
                return True
    except OSError:
        return False
    return False


def _evidence_case_heading_present(
    *,
    repo_root: Path,
    slice_id: str,
    feature_id: str,
) -> bool:
    evidence_path = repo_root / "evidence.md"
    if not evidence_path.exists():
        return False
    try:
        text = evidence_path.read_text(encoding="utf-8")
    except OSError:
        return False
    case_lines = [line for line in text.splitlines() if line.startswith("## Case")]
    if not case_lines:
        return False
    needles = tuple(
        candidate for candidate in (slice_id, feature_id) if candidate
    )
    if not needles:
        return False
    for line in case_lines:
        for needle in needles:
            if needle in line:
                return True
    return False


def _worktree_is_dirty(*, repo_root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())


def _real_life_status_valid(
    payload: dict[str, object] | None,
    pytest_node_ids: tuple[str, ...],
) -> bool:
    if not payload:
        return False
    status = _coerce_string(payload.get("real_life_test_status"))
    if status == "proven_passed":
        return bool(pytest_node_ids)
    return bool(status)


def _recent_commit_shas(
    *,
    repo_root: Path,
    since_commit: str,
    limit: int,
) -> tuple[str, ...]:
    try:
        result = subprocess.run(
            ["git", "log", "--format=%H", f"-{limit}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return ()
    if result.returncode != 0:
        return ()
    shas: list[str] = []
    for sha in result.stdout.splitlines():
        sha = sha.strip()
        if not sha:
            continue
        if since_commit and sha.startswith(since_commit):
            break
        shas.append(sha)
        if len(shas) >= limit:
            break
    return tuple(shas)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _build_audit_id(now: str) -> str:
    compact = (
        now.replace("-", "")
        .replace(":", "")
        .replace(".", "")
        .replace("Z", "")
    )
    return f"ReceiptStewardAuditReceipt:{compact}-{secrets.token_hex(4)}"


def _targets_status(missing: list[str]) -> str:
    if not missing:
        return "passed"
    blocking = [item for item in missing if item not in ADVISORY_MISSING_ITEMS]
    if not blocking:
        return "partial"
    return "failed"


def _relative_to_repo(path: Path, repo_root: Path) -> Path:
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except (OSError, ValueError):
        return path


def _coerce_string(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coverage_pct(
    with_receipts: list[dict[str, str]],
    without_receipts: list[dict[str, str]],
) -> float:
    total = len(with_receipts) + len(without_receipts)
    if total == 0:
        return 0.0
    return round(100.0 * len(with_receipts) / total, 2)


__all__ = [
    "ADVISORY_MISSING_ITEMS",
    "DANGLING_PLAN_ROW",
    "DIRTY_TREE_AT_AUDIT",
    "MISSING_COMPLETELY",
    "MISSING_ITEMS_TAXONOMY",
    "MISSING_PYTEST_NODE",
    "NO_EVIDENCE_CASE",
    "PYTEST_NODE_UNRESOLVABLE",
    "STALE_COMMIT_REFERENCE",
    "audit_recent_commits",
    "audit_slice",
    "build_audit_gap_report",
]
