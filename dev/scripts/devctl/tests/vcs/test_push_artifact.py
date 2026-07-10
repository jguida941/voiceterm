"""Tests for governed push report artifact paths."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.vcs.push_artifact import (
    latest_push_report_relpath,
    load_latest_push_report,
    persist_latest_push_report,
)


def _path_config() -> SimpleNamespace:
    return SimpleNamespace(
        push_report_rel="dev/reports/push/latest_push_report.json",
        legacy_push_report_rels=("dev/reports/push/latest.json",),
    )


@patch("dev.scripts.devctl.commands.vcs.push_artifact.active_path_config")
def test_latest_push_report_uses_explicit_filename(path_config_mock, tmp_path) -> None:
    path_config_mock.return_value = _path_config()

    relpath = persist_latest_push_report({"status": "validation_ready"}, repo_root=tmp_path)

    assert relpath == "dev/reports/push/latest_push_report.json"
    assert latest_push_report_relpath(repo_root=tmp_path) == relpath
    assert (tmp_path / relpath).exists()
    assert not (tmp_path / "dev/reports/push/latest.json").exists()


@patch("dev.scripts.devctl.commands.vcs.push_artifact.active_path_config")
def test_load_latest_push_report_accepts_legacy_read_fallback(
    path_config_mock,
    tmp_path,
) -> None:
    path_config_mock.return_value = _path_config()
    legacy_path = tmp_path / "dev/reports/push/latest.json"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_text(json.dumps({"status": "legacy"}), encoding="utf-8")

    assert load_latest_push_report(repo_root=tmp_path) == {"status": "legacy"}
