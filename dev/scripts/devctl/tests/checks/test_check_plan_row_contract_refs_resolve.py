from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.checks.check_plan_row_contract_refs_resolve import (
    evaluate_plan_row_contract_refs_resolve,
)


def _write_jsonl(path: Path, rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


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

