"""Tests for the generated SYSTEM_MAP connectivity snapshot."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.platform.system_map import (
    GENERATED_BLOCK_BEGIN,
    GENERATED_BLOCK_END,
    build_system_map_snapshot,
    render_system_map_document,
)


def test_system_map_snapshot_counts_architecture_roots(tmp_path: Path) -> None:
    (tmp_path / "dev/scripts/devctl/runtime").mkdir(parents=True)
    (tmp_path / "dev/scripts/devctl/runtime/model.py").write_text("", encoding="utf-8")
    (tmp_path / "dev/scripts/checks/package_layout").mkdir(parents=True)
    (tmp_path / "dev/scripts/checks/package_layout/check.py").write_text(
        "",
        encoding="utf-8",
    )
    policy_path = tmp_path / "dev/config/devctl_repo_policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(
        json.dumps(
            {
                "repo_governance": {
                    "surface_generation": {
                        "surfaces": [
                            {
                                "id": "system_map_index",
                                "renderer": "system_map_renderer",
                                "output_path": "dev/guides/SYSTEM_MAP.md",
                                "tracked": True,
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    snapshot = build_system_map_snapshot(repo_root=tmp_path)

    root_counts = {row.root: row.python_file_count for row in snapshot.tracked_roots}
    assert root_counts["dev/scripts/devctl"] == 1
    assert root_counts["dev/scripts/checks"] == 1
    assert snapshot.governed_surfaces[0].surface_id == "system_map_index"
    assert snapshot.connectivity_registry.contract_id == "ConnectivityRegistrySnapshot"
    assert snapshot.connectivity_registry.connected_contracts


def test_render_system_map_document_inserts_generated_block() -> None:
    snapshot = build_system_map_snapshot()
    current = "# SYSTEM_MAP.md\n\n## 0. Living Flowchart\n\nbody\n"

    rendered = render_system_map_document(current, snapshot)

    assert GENERATED_BLOCK_BEGIN in rendered
    assert GENERATED_BLOCK_END in rendered
    assert rendered.index(GENERATED_BLOCK_BEGIN) < rendered.index("## 0. Living Flowchart")
    assert "## Generated Connectivity Snapshot" in rendered
    assert "### Typed Connectivity Registry" in rendered


def test_system_map_registry_declares_single_source_writers() -> None:
    snapshot = build_system_map_snapshot()

    for contract in snapshot.connectivity_registry.connected_contracts:
        for field in contract.fields:
            assert field.field_kind == "source"
            assert len(field.writer_ids) == 1
