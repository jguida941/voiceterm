from pathlib import Path

from dev.scripts.checks import check_receipt_store_has_active_consumer as guard


def test_changed_store_with_named_reader_passes(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(
            guard.ReceiptStoreClassification(
                store_path="dev/state/example_receipts.jsonl",
                writer_refs=("writer.append_example_receipt",),
                reader_refs=("reader.load_example_receipts",),
            ),
        ),
    )

    assert report["ok"] is True
    assert report["store_count"] == 1


def test_changed_store_without_reader_or_disposition_fails(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(
            guard.ReceiptStoreClassification(
                store_path="dev/state/example_receipts.jsonl",
                writer_refs=("writer.append_example_receipt",),
                reader_refs=(),
            ),
        ),
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "receipt_store_without_active_consumer" in reasons


def test_classified_store_without_writer_fails(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(
            guard.ReceiptStoreClassification(
                store_path="dev/state/example_receipts.jsonl",
                writer_refs=(),
                reader_refs=("reader.load_example_receipts",),
            ),
        ),
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "receipt_store_without_named_writer" in reasons


def test_evidence_only_disposition_passes_without_reader(tmp_path: Path) -> None:
    store = tmp_path / "dev/state/example_receipts.jsonl"
    store.parent.mkdir(parents=True)
    store.write_text("{}\n", encoding="utf-8")

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(store,),
        classifications=(
            guard.ReceiptStoreClassification(
                store_path="dev/state/example_receipts.jsonl",
                writer_refs=("writer.append_example_receipt",),
                reader_refs=(),
                disposition="evidence_only",
            ),
        ),
    )

    assert report["ok"] is True
    assert report["stores"][0]["disposition"] == "evidence_only"


def test_unclassified_changed_receipt_store_fails(tmp_path: Path) -> None:
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
    assert "receipt_store_missing_consumer_classification" in reasons


def test_git_status_parser_preserves_leading_dev_path() -> None:
    assert (
        guard._path_from_git_status_line(" M dev/state/example_receipts.jsonl")
        == "dev/state/example_receipts.jsonl"
    )
