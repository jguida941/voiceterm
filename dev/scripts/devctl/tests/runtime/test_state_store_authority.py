"""Tests for the shared governed state-store authority helpers."""

from __future__ import annotations

import multiprocessing
from pathlib import Path

from dev.scripts.devctl.runtime.master_plan_contract import PlanRow, SDLCStage
from dev.scripts.devctl.runtime.master_plan_store import (
    read_plan_rows_jsonl,
    upsert_plan_row_jsonl,
)
from dev.scripts.devctl.runtime.plan_index_authority import upsert_plan_index_row
from dev.scripts.devctl.runtime import state_store_authority
from dev.scripts.devctl.runtime.state_store_authority import (
    StateStoreCorruptionError,
    append_json_mapping,
    read_json_mappings_strict,
    transform_json_mappings,
)


def _append_rows(path_text: str, writer: str, count: int) -> None:
    path = Path(path_text)
    for index in range(count):
        append_json_mapping(
            path,
            {"writer": writer, "index": index},
            store_id="test_jsonl",
        )


def test_transform_json_mappings_fails_closed_on_corrupt_row(tmp_path) -> None:
    path = tmp_path / "corrupt.jsonl"
    path.write_text('{"ok": 1}\nnot-json\n', encoding="utf-8")

    try:
        transform_json_mappings(
            path,
            transform=lambda rows: rows,
            store_id="corrupt_jsonl",
        )
    except StateStoreCorruptionError as exc:
        assert "invalid JSON object" in str(exc)
    else:
        raise AssertionError("expected corruption error")


def test_append_json_mapping_serializes_concurrent_process_writers(tmp_path) -> None:
    path = tmp_path / "concurrent.jsonl"
    try:
        ctx = multiprocessing.get_context("fork")
    except ValueError:
        ctx = multiprocessing.get_context("spawn")
    workers = [
        ctx.Process(target=_append_rows, args=(str(path), "left", 25)),
        ctx.Process(target=_append_rows, args=(str(path), "right", 25)),
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=30)
        assert worker.exitcode == 0

    rows = read_json_mappings_strict(path)

    assert len(rows) == 50
    assert {row["writer"] for row in rows} == {"left", "right"}


def test_append_json_mapping_fsyncs_parent_directory_after_append(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "append.jsonl"
    calls: list[Path] = []

    def _record_parent(path: Path) -> None:
        calls.append(path)

    monkeypatch.setattr(state_store_authority, "_fsync_directory", _record_parent)

    append_json_mapping(path, {"writer": "solo"}, store_id="append_parent_fsync")

    assert calls == [path.parent]


def test_append_json_mapping_returns_lineage_fields(tmp_path) -> None:
    path = tmp_path / "lineage.jsonl"

    result = append_json_mapping(
        path,
        {"writer": "lineage"},
        store_id="lineage_store",
        correlation_id="corr-test",
        causation_id="cause-test",
        run_id="run-test",
    )

    assert result.correlation_id == "corr-test"
    assert result.causation_id == "cause-test"
    assert result.run_id == "run-test"


def test_upsert_plan_row_jsonl_preserves_single_row_snapshot(tmp_path) -> None:
    path = tmp_path / "plan_index.jsonl"
    first = PlanRow(
        row_id="MP377-STATE-STORE-AUTHORITY-SPINE-S1",
        title="Initial title",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
    )
    updated = PlanRow(
        row_id="MP377-STATE-STORE-AUTHORITY-SPINE-S1",
        title="Updated title",
        status="in_progress",
        sdlc_stage=SDLCStage.IMPL,
    )

    status1, stored1 = upsert_plan_row_jsonl(path, first)
    status2, stored2 = upsert_plan_row_jsonl(path, updated)
    rows = read_plan_rows_jsonl(path)

    assert status1 == "inserted"
    assert stored1.title == "Initial title"
    assert status2 == "updated"
    assert stored2.title == "Updated title"
    assert len(rows) == 1
    assert rows[0].title == "Updated title"


def test_plan_index_authority_reports_locked_upsert_result(tmp_path) -> None:
    path = tmp_path / "plan_index.jsonl"
    row = PlanRow(
        row_id="MP377-PLAN-INDEX-AUTHORITY-S1",
        title="Canonical locked writer",
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
    )

    result = upsert_plan_index_row(path, row)

    assert result.status == "inserted"
    assert result.stored_row.row_id == row.row_id
    assert result.row_count == 1
    assert result.authority_path == str(path)
