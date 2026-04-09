"""F1: startup-context must route coordination through the shared loader.

Before MP-384/MP-387, ``build_startup_context`` constructed its own
``CoordinationSnapshot`` via a direct ``build_coordination_snapshot`` call
while ``session_resume_support`` and ``control_plane_read_model`` went
through ``coordination_loader.load_coordination_snapshot``. Live proof on
the affected tree showed ``startup-context --format json`` reporting a
different ``observed_topology`` from ``session-resume --format json`` and
``dashboard --format json`` even with matching inputs.

These tests lock in the structural fix: ``build_startup_context`` now
delegates to the shared loader and returns whatever snapshot the loader
produces. A mock-based test proves the wiring; a real-repo parity test
proves the three read surfaces cannot diverge on the same tree.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

# Import runtime first so runtime/__init__.py finishes eagerly loading
# control_plane_read_model before we touch platform.coordination_snapshot_models.
# Importing platform first would re-enter an already-loading runtime package
# and trigger a partial-module ImportError.
from dev.scripts.devctl.runtime.control_plane_read_model import (
    build_control_plane_read_model,
)
from dev.scripts.devctl.runtime.coordination_loader import (
    load_coordination_snapshot,
)
from dev.scripts.devctl.runtime.review_state_locator import (
    load_current_review_state,
)
from dev.scripts.devctl.runtime.startup_context import (
    _detect_reviewer_gate_from_review_state,
    build_startup_context,
)
from dev.scripts.devctl.platform.coordination_snapshot_models import (
    CoordinationSnapshot,
)


# tests/runtime/test_coordination_loader_wiring.py lives five parents
# below the repo root: runtime -> tests -> devctl -> scripts -> dev -> repo_root.
REPO_ROOT = Path(__file__).resolve().parents[5]


class TestStartupContextRoutesThroughLoader(unittest.TestCase):
    """Structural: build_startup_context must call load_coordination_snapshot."""

    def test_startup_context_returns_loader_snapshot(self) -> None:
        """The loader's return value must surface as ``ctx.coordination``.

        We patch at the import source so the lazy ``from .coordination_loader
        import load_coordination_snapshot`` inside ``build_startup_context``
        resolves to the mock. If a future refactor bypasses the loader, this
        test fails immediately.
        """
        sentinel = CoordinationSnapshot(
            generated_at_utc="2026-04-08T00:00:00Z",
            repo_name="loader-sentinel",
            repo_root="/tmp/loader-sentinel",
            ownership_status="SENTINEL_OWNERSHIP_STATUS",
            declared_topology="multi_agent_orchestrated",
            observed_topology="dual_agent",
            recommended_topology="single_agent",
            resync_reasons=("sentinel:loader_was_called",),
            current_slice="SENTINEL_CURRENT_SLICE",
        )
        with patch(
            "dev.scripts.devctl.runtime.coordination_loader.load_coordination_snapshot",
            return_value=sentinel,
        ) as mock_loader:
            ctx = build_startup_context(repo_root=REPO_ROOT)

        self.assertGreaterEqual(
            mock_loader.call_count,
            1,
            "build_startup_context must call load_coordination_snapshot",
        )
        self.assertIs(ctx.coordination, sentinel)


class TestCoordinationLoaderThreeSurfaceParity(unittest.TestCase):
    """End-to-end: startup-context and ControlPlaneReadModel must agree."""

    def test_startup_context_matches_control_plane_read_model(self) -> None:
        """Both surfaces must see identical structural coordination fields.

        ``generated_at_utc`` is intentionally excluded because the two calls
        happen at different wall-clock moments; only the reducer-derived
        fields (topology, ownership_status, resync_reasons, current_slice)
        must agree to prove the three proof surfaces share one reducer.
        """
        ctx = build_startup_context(repo_root=REPO_ROOT)
        model = build_control_plane_read_model(
            REPO_ROOT,
            governance=ctx.governance,
        )
        startup_snapshot = ctx.coordination
        model_snapshot = model.coordination
        self.assertIsNotNone(startup_snapshot)
        self.assertIsNotNone(model_snapshot)
        assert startup_snapshot is not None and model_snapshot is not None
        for field in (
            "declared_topology",
            "observed_topology",
            "recommended_topology",
            "ownership_status",
            "resync_reasons",
            "current_slice",
            "fanout_posture",
            "safe_to_fanout",
            "worktree_strategy",
        ):
            self.assertEqual(
                getattr(startup_snapshot, field),
                getattr(model_snapshot, field),
                f"field {field!r} diverged: startup_context vs read_model",
            )

    def test_typed_review_state_skips_bridge_refresh_in_read_model(self) -> None:
        """F1 / MP-384 structural contract: passing a typed ``review_state``
        into ``build_control_plane_read_model`` must short-circuit
        ``load_current_review_state_payload`` so the read model never re-runs
        bridge reprojection mid-tick. Without this contract, three sequential
        parity calls (startup-context, dashboard, session-resume) can drift
        because each one rewrites ``review_state.json`` as a side effect.
        """
        from dev.scripts.devctl.governance.draft import scan_repo_governance

        governance = scan_repo_governance(REPO_ROOT)
        review_state = load_current_review_state(
            REPO_ROOT, governance=governance,
        )
        self.assertIsNotNone(review_state, "test requires a real review state")
        with patch(
            "dev.scripts.devctl.runtime.review_state_locator.load_current_review_state_payload",
        ) as mock_loader:
            model = build_control_plane_read_model(
                REPO_ROOT,
                governance=governance,
                review_state=review_state,
            )
        self.assertIsNotNone(model.coordination)
        mock_loader.assert_not_called()

    def test_startup_context_matches_direct_loader_call(self) -> None:
        """A direct loader call with the same inputs must match ctx.coordination."""
        from dev.scripts.devctl.governance.draft import scan_repo_governance

        ctx = build_startup_context(repo_root=REPO_ROOT)
        governance = scan_repo_governance(REPO_ROOT)
        review_state = load_current_review_state(
            REPO_ROOT, governance=governance,
        )
        governance_mode = str(
            governance.bridge_config.operator_interaction_mode or ""
        ).strip()
        gate = _detect_reviewer_gate_from_review_state(
            review_state, governance_mode=governance_mode,
        )
        direct = load_coordination_snapshot(
            repo_root=REPO_ROOT,
            sources={},
            governance=governance,
            review_state=review_state,
            reviewer_gate=gate,
        )
        self.assertIsNotNone(direct)
        startup_snapshot = ctx.coordination
        self.assertIsNotNone(startup_snapshot)
        assert direct is not None and startup_snapshot is not None
        for field in (
            "declared_topology",
            "observed_topology",
            "recommended_topology",
            "ownership_status",
            "resync_reasons",
            "current_slice",
        ):
            self.assertEqual(
                getattr(startup_snapshot, field),
                getattr(direct, field),
                f"field {field!r} diverged: startup_context vs direct loader call",
            )


if __name__ == "__main__":
    unittest.main()
