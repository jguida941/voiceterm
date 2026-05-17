"""Tests for the SYSTEM_MAP contract-registry coverage guard."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.checks.systemmap_covers_contract_registry.command import (
    build_report,
    evaluate_systemmap_contract_coverage,
    render_md,
)
from dev.scripts.devctl.platform.system_map import (
    GENERATED_BLOCK_BEGIN,
    GENERATED_BLOCK_END,
    build_system_map_snapshot,
    render_system_map_markdown,
)


def test_systemmap_contract_coverage_passes_matching_generated_block(
    tmp_path: Path,
) -> None:
    _write_registry(tmp_path, "DemoOne", "DemoTwo")
    _write_system_map(tmp_path, render_system_map_markdown(build_system_map_snapshot(repo_root=tmp_path)))

    coverage, violations = evaluate_systemmap_contract_coverage(repo_root=tmp_path)

    assert coverage["ok"] is True
    assert coverage["unique_contract_count"] == 2
    assert coverage["generated_block_current"] is True
    assert violations == ()


def test_systemmap_contract_coverage_flags_missing_contract_id(
    tmp_path: Path,
) -> None:
    _write_registry(tmp_path, "DemoOne", "DemoTwo")
    block = render_system_map_markdown(build_system_map_snapshot(repo_root=tmp_path))
    _write_system_map(tmp_path, block.replace("`DemoTwo`", "`OtherContract`"))

    coverage, violations = evaluate_systemmap_contract_coverage(repo_root=tmp_path)

    assert coverage["ok"] is False
    assert "DemoTwo" in coverage["missing_contract_ids"]
    assert any(
        violation.rule == "missing-contract-id"
        and violation.contract_id == "DemoTwo"
        for violation in violations
    )


def test_systemmap_contract_coverage_flags_stale_generated_block(
    tmp_path: Path,
) -> None:
    _write_registry(tmp_path, "DemoOne")
    block = render_system_map_markdown(build_system_map_snapshot(repo_root=tmp_path))
    _write_system_map(tmp_path, block.replace("registry_contract_count: 1", "registry_contract_count: 99"))

    coverage, violations = evaluate_systemmap_contract_coverage(repo_root=tmp_path)

    assert coverage["ok"] is False
    assert coverage["generated_block_current"] is False
    assert any(violation.rule == "stale-generated-system-map-block" for violation in violations)


def test_systemmap_contract_coverage_flags_missing_generated_markers(
    tmp_path: Path,
) -> None:
    _write_registry(tmp_path, "DemoOne")
    system_map_path = tmp_path / "dev/guides/SYSTEM_MAP.md"
    system_map_path.parent.mkdir(parents=True)
    system_map_path.write_text("# SYSTEM_MAP\n\n`DemoOne`\n", encoding="utf-8")

    coverage, violations = evaluate_systemmap_contract_coverage(repo_root=tmp_path)

    assert coverage["ok"] is False
    assert coverage["generated_block_present"] is False
    assert any(violation.rule == "missing-generated-system-map-block" for violation in violations)


def test_systemmap_contract_coverage_reports_authority_contract_id_without_registry_row(
    tmp_path: Path,
) -> None:
    _write_registry(tmp_path, "DemoOne")
    _write_authority_file(
        tmp_path,
        """
DEMO_AUTHORITY_CONTRACT_ID = "DemoAuthority"

def rows():
    return ContractSpec(contract_id="DemoOne")
""",
    )
    _write_system_map(tmp_path, render_system_map_markdown(build_system_map_snapshot(repo_root=tmp_path)))

    coverage, violations = evaluate_systemmap_contract_coverage(repo_root=tmp_path)

    assert coverage["ok"] is True
    assert violations == ()
    assert coverage["authority_contract_id_coverage_report_only"] is True
    assert coverage["authority_contract_id_coverage_would_fail"] is True
    assert coverage["authority_contract_missing_ids"] == ("DemoAuthority",)
    authority_violations = coverage["authority_contract_id_violations"]
    assert isinstance(authority_violations, tuple)
    assert authority_violations[0]["contract_id"] == "DemoAuthority"
    assert authority_violations[0]["rule"] == "missing-registry-row"


def test_systemmap_contract_coverage_accepts_authority_contract_id_with_registry_row(
    tmp_path: Path,
) -> None:
    _write_registry(tmp_path, "DemoAuthority")
    _write_authority_file(tmp_path, 'DEMO_AUTHORITY_CONTRACT_ID = "DemoAuthority"\n')
    _write_system_map(tmp_path, render_system_map_markdown(build_system_map_snapshot(repo_root=tmp_path)))

    coverage, violations = evaluate_systemmap_contract_coverage(repo_root=tmp_path)

    assert coverage["ok"] is True
    assert violations == ()
    assert coverage["authority_contract_id_coverage_ok"] is True
    assert coverage["authority_contract_id_coverage_would_fail"] is False
    assert coverage["authority_contract_missing_ids"] == ()


def test_systemmap_contract_coverage_markdown_lists_refresh_command(
    tmp_path: Path,
) -> None:
    _write_registry(tmp_path, "DemoOne")
    _write_system_map(tmp_path, "## Generated Connectivity Snapshot\n")

    report = build_report(repo_root=tmp_path)
    markdown = render_md(report)

    assert "check_systemmap_covers_contract_registry" in markdown
    assert "render-surfaces --write --surface system_map_index" in markdown
    assert "`DemoOne` [missing-contract-id]" in markdown


def _write_registry(root: Path, *contract_ids: str) -> None:
    registry_path = root / "dev/state/contract_registry.jsonl"
    registry_path.parent.mkdir(parents=True)
    rows = [_registry_row(contract_id) for contract_id in contract_ids]
    registry_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _registry_row(contract_id: str) -> dict[str, object]:
    return {
        "contract_id": contract_id,
        "entry_kind": "shared_contract",
        "python_owner_path": "dev/demo.py",
        "rust_owner_path": "",
        "fixture_path": f"dev/test_data/schema_fixtures/{contract_id}/1",
        "schema_version": 1,
        "ownership_mode": "python_only",
        "parity_command": "python3 dev/scripts/checks/check_platform_contract_closure.py --format json",
        "registry_path": "dev/state/contract_registry.jsonl",
        "registry_row_contract_id": "PlatformContractRegistryRow",
        "registry_row_schema_version": 1,
    }


def _write_system_map(root: Path, block: str) -> None:
    path = root / "dev/guides/SYSTEM_MAP.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"# SYSTEM_MAP.md\n\n{GENERATED_BLOCK_BEGIN}\n{block}\n{GENERATED_BLOCK_END}\n",
        encoding="utf-8",
    )


def _write_authority_file(root: Path, text: str) -> None:
    path = root / "dev/scripts/devctl/platform/demo_authority.py"
    path.parent.mkdir(parents=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")
