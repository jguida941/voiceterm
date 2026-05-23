from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.check_plan_row_contract_refs_resolve import (
    evaluate_plan_row_contract_refs_resolve,
)
from dev.scripts.devctl.tests.checks._test_jsonl_helpers import write_jsonl as _write_jsonl


def test_plan_row_contract_refs_guard_reports_orphan_refs(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "dev/state/plan_index.jsonl",
        (
            {
                "row_id": "MP-1",
                "provenance": {"contract_id": "RegisteredContract"},
            },
            {
                "row_id": "MP-2",
                "provenance": {"contract_id": "MissingContract"},
            },
        ),
    )
    _write_jsonl(
        tmp_path / "dev/state/contract_registry.jsonl",
        ({"contract_id": "RegisteredContract"},),
    )

    report = evaluate_plan_row_contract_refs_resolve(repo_root=tmp_path)

    assert report.plan_row_count == 2
    assert report.registered_contract_count == 1
    assert report.orphan_count == 1
    assert report.orphans[0]["row_id"] == "MP-2"
    assert report.orphans[0]["contract_id"] == "MissingContract"

