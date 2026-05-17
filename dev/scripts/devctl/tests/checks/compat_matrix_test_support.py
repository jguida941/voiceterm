"""Shared assertions for compatibility-matrix script tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch


def write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")


def assert_load_matrix_accepts_yaml_map_syntax(*, script, repo_root: Path) -> None:
    with tempfile.TemporaryDirectory(dir=repo_root) as temp_dir:
        matrix_path = Path(temp_dir) / "matrix.yaml"
        write_lines(
            matrix_path,
            [
                "hosts:",
                "  - id: cursor",
                "providers: []",
                "matrix: []",
            ],
        )
        with patch.object(script, "yaml", None):
            payload, error = script._load_matrix(matrix_path)
    assert error is None
    assert isinstance(payload, dict)
    assert payload is not None
    assert payload["hosts"][0]["id"] == "cursor"


def assert_missing_file_outside_repo_returns_error(*, script) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        missing_path = Path(temp_dir) / "missing_matrix.yaml"
        payload, error = script._load_matrix(missing_path)
    assert payload is None
    assert error is not None
    assert "missing matrix file" in error
    assert missing_path.as_posix() in error
