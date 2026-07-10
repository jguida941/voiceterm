"""Regression tests for dashboard NOW section next_action priority model.

Per Codex rev_pkt_2388: ``next_action`` must NOT report
``await_checkpoint`` while pending unacked reviewer packets remain or
while startup authority preconditions (import-index atomicity, staged-
index budget) are still failing. The typed pending-blocker count and
startup-authority blocker kind must dominate the legacy
``BlockerSnapshot`` next_action_override so the operator/runtime do not
believe checkpoint is the next step when it is explicitly blocked.
"""

from __future__ import annotations

# Pre-load the commands package so cross-package imports resolve in CLI
# order and avoid the pre-existing circular import in
# commands.review_channel_bridge_render.
from dev.scripts.devctl import cli as _cli  # noqa: F401

from dev.scripts.devctl.commands.dashboard_builders import (
    NowSectionContext,
    _build_now_section,
)
from dev.scripts.devctl.commands.dashboard import _startup_authority_blocker_kind


def _base_ctx(**overrides) -> NowSectionContext:
    base = {
        "bridge": {"reviewer_mode": "single_agent"},
        "reviewer": {"job_state": "polling", "provider": "codex"},
        "implementer": {"job_state": "implementing", "provider": "claude"},
        "session": {"implementer_status": "- working"},
        "instruction_text": "rev_pkt_2288",
        "top_blocker": "guard fail: push-preflight",
        "last_change_age": 5,
        "coordination": {},
        "runtime_counts": {
            "live_reviewer_count": 1,
            "live_implementer_count": 1,
        },
        "next_action_override": "await_checkpoint",
    }
    base.update(overrides)
    return NowSectionContext(**base)


def test_pending_review_blocker_dominates_await_checkpoint() -> None:
    ctx = _base_ctx(pending_review_blocker_count=3)
    section = _build_now_section(ctx)
    assert section["next_action"] == (
        "checkpoint_blocked_by_pending_review_packets:3_pending"
    )
    assert section["next_action_reason"] == "pending_review_blockers"
    # Override is preserved on the typed reason path; legacy must NOT win.
    assert section["next_action"] != "await_checkpoint"


def test_startup_authority_blocker_dominates_pending_review() -> None:
    ctx = _base_ctx(
        pending_review_blocker_count=3,
        startup_authority_blocker_kind="import_index_atomicity",
    )
    section = _build_now_section(ctx)
    assert section["next_action"] == (
        "checkpoint_blocked_by_startup_authority:import_index_atomicity"
    )
    assert section["next_action_reason"] == "startup_authority_blocker"


def test_staged_index_budget_blocker_dominates_await_checkpoint() -> None:
    ctx = _base_ctx(
        startup_authority_blocker_kind="staged_index_budget_exceeded",
    )
    section = _build_now_section(ctx)
    assert section["next_action"] == (
        "checkpoint_blocked_by_startup_authority:staged_index_budget_exceeded"
    )
    assert section["next_action_reason"] == "startup_authority_blocker"


def test_startup_authority_blocker_reads_startup_context_not_only_review_state() -> None:
    kind = _startup_authority_blocker_kind(
        {},
        startup_context={
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": True,
                    "safe_to_continue_editing": False,
                    "checkpoint_reason": "staged_index_budget_exceeded",
                }
            }
        },
    )

    assert kind == "staged_index_budget_exceeded"


def test_startup_authority_blocker_prefers_live_context_over_stale_receipt() -> None:
    kind = _startup_authority_blocker_kind(
        {},
        startup_context={
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": True,
                    "safe_to_continue_editing": False,
                    "checkpoint_reason": "staged_index_budget_exceeded",
                }
            }
        },
        receipt={
            "startup_authority_ok": False,
            "startup_authority_errors": [
                "runtime.py: imported module missing from git index (staged)."
            ],
            "checkpoint_required": True,
            "safe_to_continue_editing": False,
            "push_reason": "staged_index_budget_exceeded",
        },
    )

    assert kind == "staged_index_budget_exceeded"


def test_startup_authority_blocker_uses_receipt_import_atomicity_without_live_context() -> None:
    kind = _startup_authority_blocker_kind(
        {},
        receipt={
            "startup_authority_ok": False,
            "startup_authority_errors": [
                "runtime.py: imported module missing from git index (staged)."
            ],
            "checkpoint_required": True,
            "safe_to_continue_editing": False,
            "push_reason": "staged_index_budget_exceeded",
        },
    )

    assert kind == "import_index_atomicity"


def test_no_blockers_renders_legacy_override() -> None:
    ctx = _base_ctx(
        pending_review_blocker_count=0,
        startup_authority_blocker_kind="",
        next_action_override="await_checkpoint",
    )
    section = _build_now_section(ctx)
    assert section["next_action"] == "await_checkpoint"
    assert section["next_action_reason"] == ""


def test_unknown_startup_authority_blocker_kind_falls_through() -> None:
    """Only typed blocker kinds dominate — bare strings fall through."""
    ctx = _base_ctx(startup_authority_blocker_kind="something_else")
    section = _build_now_section(ctx)
    # Falls through to override path because the kind isn't recognized.
    assert "checkpoint_blocked_by_startup_authority" in section["next_action"]
    # Confirm the unknown kind echoed verbatim — fail-loud rather than silent.
    assert "something_else" in section["next_action"]
