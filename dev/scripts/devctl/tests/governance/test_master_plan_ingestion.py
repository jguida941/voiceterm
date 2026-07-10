"""Coverage for typed master-plan ingestion and JSONL authority."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.governance.master_plan_ingestion import (
    MarkdownChecklistAdapter,
    build_explain_back_receipt,
    ingest_master_plan_markdown,
)
from dev.scripts.devctl.runtime.master_plan_store import (
    read_plan_rows_jsonl,
    upsert_plan_row_jsonl,
)


def test_markdown_checklist_ingests_mp_rows_and_explainback(tmp_path: Path) -> None:
    master_plan = tmp_path / "docs/plans/MASTER_PLAN.md"
    master_plan.parent.mkdir(parents=True, exist_ok=True)
    master_plan.write_text(
        "\n".join(
            [
                "# Master Plan",
                "- [x] `MP377-P0-T08A` Close packet lifecycle shape",
                "- [ ] `MP377-P0-T08B` Normalize read-only status",
            ]
        ),
        encoding="utf-8",
    )

    plan = ingest_master_plan_markdown(
        repo_id="adopter",
        source_path=master_plan,
        source_rel="docs/plans/MASTER_PLAN.md",
        typed_store_rel="dev/state/plan_index.jsonl",
    )
    receipt = build_explain_back_receipt(
        master_plan=plan,
        repo_pack_id="adopter-pack",
        receipt_id="explainback-1",
    )

    assert [row.row_id for row in plan.rows] == [
        "MP377-P0-T08A",
        "MP377-P0-T08B",
    ]
    assert plan.rows[0].status == "applied"
    assert plan.rows[1].status == "open"
    assert plan.rows[0].provenance.contract_id == "IngestionProvenance"
    assert plan.rows[0].provenance.source_file == "docs/plans/MASTER_PLAN.md"
    assert plan.rows[0].provenance.source_line == 2
    assert plan.rows[0].provenance.source_kind == "MarkdownChecklistAdapter"
    assert plan.rows[0].provenance.source_hash.startswith("sha256:")
    assert plan.rows[0].provenance.observed_at_utc
    assert plan.rows[0].provenance.section_authority == "owner_doc"
    assert receipt.contract_id == "ExplainBackReceipt"
    assert receipt.derived_plan_rows == (
        "MP377-P0-T08A",
        "MP377-P0-T08B",
    )


def test_plan_jsonl_upsert_uses_row_id_authority(tmp_path: Path) -> None:
    master_plan = tmp_path / "MASTER_PLAN.md"
    master_plan.write_text("- [ ] `MP377-P0-T08B` Normalize status\n", encoding="utf-8")
    plan = ingest_master_plan_markdown(
        repo_id="adopter",
        source_path=master_plan,
        source_rel="MASTER_PLAN.md",
        typed_store_rel="dev/state/plan_index.jsonl",
    )
    store = tmp_path / "dev/state/plan_index.jsonl"

    status, _ = upsert_plan_row_jsonl(store, plan.rows[0])
    second, _ = upsert_plan_row_jsonl(store, plan.rows[0])

    assert status == "inserted"
    assert second == "already_present"
    assert [row.row_id for row in read_plan_rows_jsonl(store)] == ["MP377-P0-T08B"]


def test_markdown_checklist_rejects_historical_and_code_block_authority() -> None:
    adapter = MarkdownChecklistAdapter()

    accepted = adapter.ingest_doc(
        "\n".join(
            [
                "# Active Plan",
                "- [ ] `MP377-P0-T08C` Ship provenance receipt proof",
            ]
        ),
        "PROJECT_PLAN.md",
    )
    historical = adapter.ingest_doc(
        "\n".join(
            [
                "# 2026-03 retrospective",
                "- [ ] `MP377-P0-T08D` This old next action is not live",
            ]
        ),
        "PROJECT_PLAN.md",
    )
    fixture = adapter.ingest_doc(
        "\n".join(
            [
                "# Active Plan",
                "```md",
                "- [ ] `MP377-P0-T08E` Example row must not leak",
                "```",
            ]
        ),
        "PROJECT_PLAN.md",
    )

    assert accepted.status == "accepted"
    assert accepted.rows[0].row_id == "MP377-P0-T08C"
    assert historical.status == "rejected_unauthorized_section"
    assert historical.rows == ()
    assert "not live authority" in historical.reason
    assert fixture.status == "rejected_unauthorized_section"
    assert fixture.rows == ()
    assert "code block" in fixture.reason
