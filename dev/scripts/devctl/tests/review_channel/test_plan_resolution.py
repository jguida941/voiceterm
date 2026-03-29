"""Focused regressions for plan_resolution shared-parser migration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.review_channel.plan_resolution import (
    resolve_promotion_plan_path,
)


def _write_index(repo_root: Path, rows: list[str]) -> None:
    """Write a minimal INDEX.md with the given table rows."""
    index_dir = repo_root / "dev" / "active"
    index_dir.mkdir(parents=True, exist_ok=True)
    header = (
        "| Path | Role | Execution authority | MP scope | When agents read |\n"
        "|---|---|---|---|---|\n"
    )
    (index_dir / "INDEX.md").write_text(header + "\n".join(rows) + "\n")


def _write_master(repo_root: Path, scope: str) -> None:
    """Write a minimal MASTER_PLAN.md with a current main product lane."""
    active_dir = repo_root / "dev" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "MASTER_PLAN.md").write_text(
        f"# Master Plan\n\n- Current main product lane: `{scope}`\n"
    )


class TestPlanResolutionFromTracker(unittest.TestCase):
    """Verify the shared parse_index_registry path works for plan resolution."""

    def test_resolves_mp_scope_from_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan_path = repo / "dev" / "active" / "test_plan.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# Test Plan\n")
            _write_master(repo, "MP-100")
            _write_index(repo, [
                "| `dev/active/test_plan.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-100` | always |",
            ])
            result = resolve_promotion_plan_path(
                repo_root=repo, bridge_path=None, explicit_plan_path=None,
            )
            self.assertEqual(result.source, "tracker_scope")
            self.assertIsNotNone(result.path)

    def test_missing_index_falls_through(self) -> None:
        """When index is missing and bridge is None, bridge detail takes priority."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write_master(repo, "MP-100")
            result = resolve_promotion_plan_path(
                repo_root=repo, bridge_path=None, explicit_plan_path=None,
            )
            self.assertIsNone(result.path)
            self.assertIn(result.source, ("bridge_missing", "bridge_scope_missing", "index_missing"))

    def test_unmatched_scope_falls_through(self) -> None:
        """When scope doesn't match any index row and bridge is None, bridge detail takes priority."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write_master(repo, "MP-999")
            _write_index(repo, [
                "| `dev/active/other.md` | `spec` | `mirrored` | `MP-100` | always |",
            ])
            result = resolve_promotion_plan_path(
                repo_root=repo, bridge_path=None, explicit_plan_path=None,
            )
            self.assertIsNone(result.path)
            self.assertIn(result.source, ("bridge_missing", "bridge_scope_missing", "tracker_scope_unmapped"))


if __name__ == "__main__":
    unittest.main()
