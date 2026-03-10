"""Tests for the layout persistence module: round-trip serialization,
default path resolution, edge-case handling for malformed data."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.operator_console.layout import (
    LayoutStateSnapshot,
    default_layout_state_path,
    load_layout_state,
    save_layout_state,
)
from app.operator_console.layout.layout_state import _coerce_splitter_sizes


class LayoutStateSnapshotTests(unittest.TestCase):
    """LayoutStateSnapshot dataclass construction and defaults."""

    def test_minimal_construction(self) -> None:
        snap = LayoutStateSnapshot(
            layout_mode="tabbed",
            workbench_preset="balanced",
        )
        self.assertEqual(snap.layout_mode, "tabbed")
        self.assertEqual(snap.workbench_preset, "balanced")
        self.assertIsNone(snap.workbench_surface)
        self.assertIsNone(snap.monitor_surface)
        self.assertIsNone(snap.lane_splitter_sizes)
        self.assertIsNone(snap.utility_splitter_sizes)

    def test_full_construction(self) -> None:
        snap = LayoutStateSnapshot(
            layout_mode="workbench",
            workbench_preset="full",
            workbench_surface="terminal",
            monitor_surface="diagnostics",
            lane_splitter_sizes=(100, 200, 300),
            utility_splitter_sizes=(400, 500, 600),
        )
        self.assertEqual(snap.lane_splitter_sizes, (100, 200, 300))
        self.assertEqual(snap.utility_splitter_sizes, (400, 500, 600))

    def test_frozen(self) -> None:
        snap = LayoutStateSnapshot(layout_mode="tabbed", workbench_preset="balanced")
        with self.assertRaises(AttributeError):
            snap.layout_mode = "workbench"  # type: ignore[misc]


class DefaultLayoutStatePathTests(unittest.TestCase):
    """default_layout_state_path produces the correct repo-relative path."""

    def test_returns_expected_relative_path(self) -> None:
        root = Path("/fake/repo")
        path = default_layout_state_path(root)
        self.assertEqual(
            path,
            root / "dev/reports/review_channel/operator_console/layout_state.json",
        )

    def test_path_is_child_of_repo_root(self) -> None:
        root = Path("/tmp/test-repo")
        path = default_layout_state_path(root)
        self.assertTrue(str(path).startswith(str(root)))


class SaveAndLoadLayoutStateTests(unittest.TestCase):
    """Round-trip serialization through save_layout_state / load_layout_state."""

    def test_round_trip_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = default_layout_state_path(root)
            original = LayoutStateSnapshot(
                layout_mode="workbench",
                workbench_preset="balanced",
                workbench_surface="terminal",
                monitor_surface="diagnostics",
                lane_splitter_sizes=(500, 200, 500),
                utility_splitter_sizes=(700, 250, 250),
            )
            save_layout_state(path, original)
            loaded = load_layout_state(path)

        self.assertEqual(loaded, original)

    def test_round_trip_minimal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            original = LayoutStateSnapshot(
                layout_mode="tabbed",
                workbench_preset="compact",
            )
            save_layout_state(path, original)
            loaded = load_layout_state(path)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.layout_mode, "tabbed")
        self.assertEqual(loaded.workbench_preset, "compact")
        self.assertIsNone(loaded.workbench_surface)
        self.assertIsNone(loaded.lane_splitter_sizes)

    def test_save_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            deep_path = Path(tmpdir) / "a" / "b" / "c" / "state.json"
            snap = LayoutStateSnapshot(layout_mode="tabbed", workbench_preset="balanced")
            save_layout_state(deep_path, snap)
            self.assertTrue(deep_path.exists())

    def test_saved_json_is_sorted_and_pretty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            snap = LayoutStateSnapshot(layout_mode="tabbed", workbench_preset="balanced")
            save_layout_state(path, snap)

            raw = path.read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))
            payload = json.loads(raw)
            keys = list(payload.keys())
            self.assertEqual(keys, sorted(keys))


class LoadLayoutStateEdgeCaseTests(unittest.TestCase):
    """Error handling for load_layout_state on missing or corrupt files."""

    def test_missing_file_returns_none(self) -> None:
        result = load_layout_state(Path("/tmp/nonexistent_layout_state.json"))
        self.assertIsNone(result)

    def test_invalid_json_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text("{not-json", encoding="utf-8")
            result = load_layout_state(path)

        self.assertIsNone(result)

    def test_non_dict_json_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "array.json"
            path.write_text("[1, 2, 3]", encoding="utf-8")
            result = load_layout_state(path)

        self.assertIsNone(result)

    def test_empty_dict_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.json"
            path.write_text("{}", encoding="utf-8")
            result = load_layout_state(path)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.layout_mode, "workbench")
        self.assertEqual(result.workbench_preset, "balanced")
        self.assertIsNone(result.workbench_surface)
        self.assertIsNone(result.lane_splitter_sizes)

    def test_partial_keys_fills_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "partial.json"
            path.write_text(
                json.dumps({"layout_mode": "custom"}),
                encoding="utf-8",
            )
            result = load_layout_state(path)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.layout_mode, "custom")
        self.assertEqual(result.workbench_preset, "balanced")


class CoerceSplitterSizesTests(unittest.TestCase):
    """Edge cases for the internal _coerce_splitter_sizes helper."""

    def test_valid_three_ints(self) -> None:
        self.assertEqual(_coerce_splitter_sizes([100, 200, 300]), (100, 200, 300))

    def test_valid_tuple_input(self) -> None:
        self.assertEqual(_coerce_splitter_sizes((10, 20, 30)), (10, 20, 30))

    def test_wrong_length_returns_none(self) -> None:
        self.assertIsNone(_coerce_splitter_sizes([100, 200]))
        self.assertIsNone(_coerce_splitter_sizes([100, 200, 300, 400]))

    def test_non_list_returns_none(self) -> None:
        self.assertIsNone(_coerce_splitter_sizes("not a list"))
        self.assertIsNone(_coerce_splitter_sizes(42))
        self.assertIsNone(_coerce_splitter_sizes(None))

    def test_zero_value_returns_none(self) -> None:
        self.assertIsNone(_coerce_splitter_sizes([0, 200, 300]))

    def test_negative_value_returns_none(self) -> None:
        self.assertIsNone(_coerce_splitter_sizes([-1, 200, 300]))

    def test_empty_list_returns_none(self) -> None:
        self.assertIsNone(_coerce_splitter_sizes([]))


if __name__ == "__main__":
    unittest.main()
