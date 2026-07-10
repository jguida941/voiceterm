from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.checks.plan_gold_claims_resolve.command import (
    collect_gold_claim_references,
    evaluate_plan_gold_claims_resolve,
    render_markdown,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _jsonl(path: Path, row: dict[str, object]) -> None:
    _write(path, json.dumps(row) + "\n")


def test_gold_claim_fails_when_named_class_is_absent(tmp_path: Path) -> None:
    _jsonl(
        tmp_path / "dev/state/plan_index.jsonl",
        {"title": "VERIFIED GOLD: P31 SchemaMigrationLifecycle is complete."},
    )
    _write(
        tmp_path / "dev/scripts/devctl/platform/schema_migration_spine.py",
        "class SchemaMigrationSpine:\n    pass\n",
    )

    report = evaluate_plan_gold_claims_resolve(repo_root=tmp_path)

    assert report["ok"] is False
    assert report["violations"][0]["token"] == "SchemaMigrationLifecycle"


def test_gold_claim_passes_when_symbol_is_registered_contract(tmp_path: Path) -> None:
    _jsonl(
        tmp_path / "dev/state/plan_index.jsonl",
        {"title": "VERIFIED GOLD: P179 AffectedTestSelection exists."},
    )
    _jsonl(
        tmp_path / "dev/state/contract_registry.jsonl",
        {"contract_id": "AffectedTestSelection"},
    )

    report = evaluate_plan_gold_claims_resolve(repo_root=tmp_path)

    assert report["ok"] is True
    assert report["claim_reference_count"] == 1


def test_gold_claim_fails_when_symbol_only_resolves_to_proposal_stub(
    tmp_path: Path,
) -> None:
    _jsonl(
        tmp_path / "dev/state/plan_index.jsonl",
        {"title": "VERIFIED GOLD: PacketReadReceipt is shipped substrate."},
    )
    _jsonl(
        tmp_path / "dev/state/contract_registry.jsonl",
        {
            "contract_id": "PacketReadReceipt",
            "python_owner_path": (
                "dev/scripts/devctl/runtime/governance_proposed_contracts.py"
            ),
        },
    )
    _write(
        tmp_path / "dev/scripts/devctl/runtime/governance_proposed_contracts.py",
        "class PacketReadReceipt:\n    pass\n",
    )

    report = evaluate_plan_gold_claims_resolve(repo_root=tmp_path)

    assert report["ok"] is False
    assert report["violations"][0]["token"] == "PacketReadReceipt"
    assert "proposal-stub" in report["violations"][0]["detail"]


def test_gold_claim_passes_when_symbol_is_python_assignment(tmp_path: Path) -> None:
    _jsonl(
        tmp_path / "dev/state/plan_index.jsonl",
        {"summary": "VERIFIED GOLD: P58.5 ROLE_PRESETS is live."},
    )
    _write(
        tmp_path / "dev/scripts/devctl/runtime/development_collaboration_modes.py",
        "ROLE_PRESETS = {}\n",
    )

    report = evaluate_plan_gold_claims_resolve(repo_root=tmp_path)

    assert report["ok"] is True


def test_gold_claim_resolves_bare_file_by_basename(tmp_path: Path) -> None:
    _jsonl(
        tmp_path / "dev/state/plan_index.jsonl",
        {"summary": "GOLD-STANDARD: role_customization.py is the model citizen."},
    )
    _write(tmp_path / "dev/scripts/devctl/runtime/role_customization.py", "")

    report = evaluate_plan_gold_claims_resolve(repo_root=tmp_path)

    assert report["ok"] is True


def test_negative_gold_audit_line_does_not_become_positive_claim(tmp_path: Path) -> None:
    _jsonl(
        tmp_path / "dev/state/plan_index.jsonl",
        {
            "summary": (
                "GOLD-AUDIT REQUIRED: P31 SchemaMigrationLifecycle promoted to GOLD "
                "but FILE MISSING."
            )
        },
    )

    references = collect_gold_claim_references(repo_root=tmp_path)

    assert references == []


def test_render_markdown_names_unresolved_symbol() -> None:
    rendered = render_markdown({
        "ok": False,
        "source_count": 1,
        "claim_reference_count": 1,
        "symbol_count": 0,
        "shipped_symbol_count": 0,
        "proposal_stub_symbol_count": 0,
        "path_count": 0,
        "violations": [{
            "source_path": "dev/state/plan_index.jsonl",
            "line": 7,
            "field": "summary",
            "token": "SchemaMigrationLifecycle",
            "token_kind": "symbol",
        }],
    })

    assert "# check_plan_gold_claims_resolve" in rendered
    assert "SchemaMigrationLifecycle" in rendered
    assert "dev/state/plan_index.jsonl:7" in rendered
