#!/usr/bin/env python3
"""Validate plan_index PlanRow contract refs resolve in contract_registry.

P122 guard (R130 fleet finding): the prior 53.8% PlanRow->Contract orphan rate
came from `provenance.contract_id` references that were never registered in
`contract_registry.jsonl`. Codex shipped IngestionProvenance + BridgeSeparationGuard
registry rows in R128/R129, but no guard was preventing the next orphan-class
from accumulating silently. This guard surfaces orphans every round so the
authority-composition seam stays closed.

Composes with:
- check_plan_index_commit_continuity.py (sibling guard on PlanRow content)
- IngestionProvenance contract row (closed the original DEF_B orphan rate)

Report-only mode initially (per P188 discipline) until baseline known clean.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


COMMAND = "check_plan_row_contract_refs_resolve"
PLAN_ROW_CONTRACT_REFS_GUARD_ID = "PlanRowContractRefsResolve"
PLAN_ROW_CONTRACT_REFS_RESOLVE_CONTRACT_ID = "PlanRowContractRefsResolveGuard"
DEFAULT_PLAN_INDEX_REL = "dev/state/plan_index.jsonl"
DEFAULT_CONTRACT_REGISTRY_REL = "dev/state/contract_registry.jsonl"


@dataclass(frozen=True, slots=True)
class PlanRowContractRefsResolveGuard:
    """Registry-facing contract for the plan_row contract-refs guard report."""

    guard_id: str
    ok: bool
    report_only: bool
    would_fail: bool
    plan_row_count: int = 0
    registered_contract_count: int = 0
    orphan_count: int = 0
    orphan_rate: float = 0.0
    orphans: tuple[dict[str, object], ...] = field(default_factory=tuple)
    schema_version: int = 1
    contract_id: str = "PlanRowContractRefsResolveGuard"
    command: str = "check_plan_row_contract_refs_resolve"


@dataclass(frozen=True)
class ContractRefOrphan:
    line_number: int
    row_id: str
    ref_kind: str
    contract_id: str
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "line_number": self.line_number,
            "row_id": self.row_id,
            "ref_kind": self.ref_kind,
            "contract_id": self.contract_id,
            "detail": self.detail,
        }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _registered_contract_ids(registry_rows: list[dict[str, object]]) -> set[str]:
    ids: set[str] = set()
    for row in registry_rows:
        contract_id = row.get("contract_id")
        if isinstance(contract_id, str) and contract_id:
            ids.add(contract_id)
    return ids


def _scan_plan_row_for_orphans(
    *,
    line_number: int,
    row: dict[str, object],
    registered: set[str],
) -> list[ContractRefOrphan]:
    orphans: list[ContractRefOrphan] = []
    row_id = str(row.get("row_id", "?"))
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        prov_cid = provenance.get("contract_id")
        if isinstance(prov_cid, str) and prov_cid and prov_cid not in registered:
            orphans.append(
                ContractRefOrphan(
                    line_number=line_number,
                    row_id=row_id,
                    ref_kind="provenance.contract_id",
                    contract_id=prov_cid,
                    detail=(
                        f"PlanRow provenance.contract_id={prov_cid!r} not registered "
                        "in contract_registry.jsonl"
                    ),
                )
            )
    return orphans


def evaluate_plan_row_contract_refs_resolve(
    *,
    repo_root: Path = REPO_ROOT,
    plan_index_rel: str = DEFAULT_PLAN_INDEX_REL,
    registry_rel: str = DEFAULT_CONTRACT_REGISTRY_REL,
) -> PlanRowContractRefsResolveGuard:
    plan_rows = _read_jsonl(repo_root / plan_index_rel)
    registry_rows = _read_jsonl(repo_root / registry_rel)
    registered = _registered_contract_ids(registry_rows)

    orphans: list[ContractRefOrphan] = []
    for index, row in enumerate(plan_rows, start=1):
        orphans.extend(
            _scan_plan_row_for_orphans(
                line_number=index,
                row=row,
                registered=registered,
            )
        )

    plan_count = len(plan_rows)
    orphan_count = len(orphans)
    orphan_rate = (orphan_count / plan_count) if plan_count else 0.0

    return PlanRowContractRefsResolveGuard(
        guard_id=PLAN_ROW_CONTRACT_REFS_GUARD_ID,
        ok=True,
        report_only=True,
        would_fail=bool(orphans),
        plan_row_count=plan_count,
        registered_contract_count=len(registered),
        orphan_count=orphan_count,
        orphan_rate=orphan_rate,
        orphans=tuple(orphan.to_dict() for orphan in orphans[:50]),
    )


def _render_md(report: PlanRowContractRefsResolveGuard) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- report_only: {report.report_only}")
    lines.append(f"- would_fail: {report.would_fail}")
    lines.append(f"- plan_row_count: {report.plan_row_count}")
    lines.append(f"- registered_contract_count: {report.registered_contract_count}")
    lines.append(f"- orphan_count: {report.orphan_count}")
    lines.append(f"- orphan_rate: {report.orphan_rate:.4f}")
    if report.orphans:
        lines.append("")
        lines.append("## Orphans (first 50)")
        for orphan in report.orphans:
            if not isinstance(orphan, dict):
                continue
            lines.append(
                "- "
                f"row_id={orphan.get('row_id')!r} "
                f"ref={orphan.get('ref_kind')} "
                f"missing_contract_id={orphan.get('contract_id')!r}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = evaluate_plan_row_contract_refs_resolve()
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(_render_md(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
