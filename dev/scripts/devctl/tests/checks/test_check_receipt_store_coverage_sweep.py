from pathlib import Path

from dev.scripts.checks import check_receipt_store_coverage_sweep as guard


def test_store_with_schema_guard_and_provenance_passes(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    schema_guard = tmp_path / "dev/scripts/checks/check_example_receipts.py"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")
    schema_guard.parent.mkdir(parents=True)
    schema_guard.write_text("# test schema guard\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(
            guard.ReceiptStoreCoverage(
                store_path="dev/state/example_receipts.jsonl",
                writer_refs=("writer.append_example_receipt",),
                reader_refs=("reader.load_example_receipts",),
                schema_guard_refs=("dev/scripts/checks/check_example_receipts.py",),
                provenance_refs=("PlanIntentIngestionReceipt",),
            ),
        ),
    )

    assert report["ok"] is True
    assert report["store_count"] == 1


def test_writer_reader_without_schema_guard_fails(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(
            guard.ReceiptStoreCoverage(
                store_path="dev/state/example_receipts.jsonl",
                writer_refs=("writer.append_example_receipt",),
                reader_refs=("reader.load_example_receipts",),
                schema_guard_refs=(),
                provenance_refs=("PlanIntentIngestionReceipt",),
            ),
        ),
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "receipt_store_without_schema_guard" in reasons


def test_writer_reader_without_provenance_or_archive_disposition_fails(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(
            guard.ReceiptStoreCoverage(
                store_path="dev/state/example_receipts.jsonl",
                writer_refs=("writer.append_example_receipt",),
                reader_refs=("reader.load_example_receipts",),
                schema_guard_refs=("dev/scripts/checks/check_example_receipts.py",),
                provenance_refs=(),
                archive_disposition_refs=(),
            ),
        ),
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "receipt_store_without_provenance_or_archive_disposition" in reasons


def test_schema_guard_ref_must_resolve_when_it_names_repo_path(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(
            guard.ReceiptStoreCoverage(
                store_path="dev/state/example_receipts.jsonl",
                writer_refs=("writer.append_example_receipt",),
                reader_refs=("reader.load_example_receipts",),
                schema_guard_refs=("dev/scripts/checks/check_missing_receipt.py",),
                provenance_refs=("PlanIntentIngestionReceipt",),
            ),
        ),
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "receipt_store_schema_guard_ref_unresolved" in reasons


def test_archive_disposition_satisfies_provenance_requirement(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    schema_guard = tmp_path / "dev/scripts/checks/check_example_receipts.py"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")
    schema_guard.parent.mkdir(parents=True)
    schema_guard.write_text("# test schema guard\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(
            guard.ReceiptStoreCoverage(
                store_path="dev/state/example_receipts.jsonl",
                writer_refs=("writer.append_example_receipt",),
                reader_refs=("reader.load_example_receipts",),
                schema_guard_refs=("dev/scripts/checks/check_example_receipts.py",),
                provenance_refs=(),
                archive_disposition_refs=("archive_or_consumer_pending:blocker-1",),
            ),
        ),
    )

    assert report["ok"] is True


def test_unclassified_receipt_store_fails(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/new_receipts.jsonl"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(),
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "receipt_store_missing_coverage_classification" in reasons


def test_git_status_parser_preserves_leading_dev_path() -> None:
    assert (
        guard._path_from_git_status_line(" M dev/state/example_receipts.jsonl")
        == "dev/state/example_receipts.jsonl"
    )
