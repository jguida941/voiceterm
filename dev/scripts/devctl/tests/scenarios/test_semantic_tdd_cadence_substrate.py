"""Scenario tests for the typed adaptive cadence-mode substrate (A38.1 S1.A).

These are RED-FIRST tests for the typed contract shipped in
``dev/scripts/devctl/runtime/semantic_tdd_cadence.py``. The canonical
2a/2b shape:

- ``test_*`` (no marker) — current-safety invariants. Must GREEN once
  the substrate module lands; will fail loudly if the contract drifts.
- ``test_*`` with ``@pytest.mark.xfail(strict=True)`` — target-architecture
  invariants that stay RED-as-visible-debt until later slices wire the
  reducer into the live develop-next pipeline (S1.D dogfood). Strict so
  they cannot be silently "fixed" by removing assertions.

Substrate boundary (this file):
- Pure-reducer invariants (no subprocess, no live state).
- Persistence smoke tests via ``tmp_path``.
- One xfail-strict invariant on the live jsonl store path.

NOT in this file (delegated to later S1 slices):
- CLI tests (S1.C).
- evidence-log guard relaxation tests (S1.B).
- End-to-end develop-next cadence dogfood (S1.D).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_outcome(
    *,
    slice_id: str,
    catches: tuple,
    mode_used=None,
    cost_seconds: int = 1,
    timestamp_utc: str = "1970-01-01T00:00:00Z",
):
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchOutcome,
        SemanticTDDCadenceMode,
    )

    return CatchOutcome(
        slice_id=slice_id,
        mode_used=mode_used or SemanticTDDCadenceMode.STANDARD,
        catches_found=catches,
        cost_seconds=cost_seconds,
        timestamp_utc=timestamp_utc,
    )


def _state_with_outcomes(outcomes, **overrides):
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        SemanticTDDCadenceState,
    )

    return SemanticTDDCadenceState(
        recent_outcomes=tuple(outcomes),
        **overrides,
    )


# ---------------------------------------------------------------------------
# 2a — current-safety invariants (must GREEN once substrate lands)
# ---------------------------------------------------------------------------


def test_cadence_mode_enum_has_five_modes():
    """Typed enum carries exactly the operator-authored 5 modes."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        SemanticTDDCadenceMode,
    )

    assert set(SemanticTDDCadenceMode) == {
        SemanticTDDCadenceMode.FULL,
        SemanticTDDCadenceMode.STANDARD,
        SemanticTDDCadenceMode.LIGHT,
        SemanticTDDCadenceMode.SKIP_NEXT,
        SemanticTDDCadenceMode.ADAPTIVE_AUTO,
    }


def test_catch_kind_enum_carries_six_typed_categories():
    """Typed CatchKind taxonomy matches evidence.md catch-class survey."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import CatchKind

    assert set(CatchKind) == {
        CatchKind.RED_FIRST_CATCH,
        CatchKind.CASCADE_CATCH,
        CatchKind.CONNECTIVITY_AFTER,
        CatchKind.XFAIL_TRANSITION,
        CatchKind.TYPE_INTROSPECTION,
        CatchKind.NONE,
    }


def test_catch_outcome_and_state_dataclasses_are_frozen_and_slots():
    """The dataclasses must be immutable and slot-bounded.

    Per the substrate non-negotiable: ``frozen=True, slots=True``. The
    surface of these objects is the contract; ad-hoc field assignment
    would let mutations bypass the typed reducer.
    """
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchOutcome,
        SemanticTDDCadenceState,
    )

    outcome = _make_outcome(slice_id="s1", catches=())
    with pytest.raises((AttributeError, TypeError)):
        outcome.slice_id = "mutated"  # type: ignore[misc]
    state = SemanticTDDCadenceState()
    with pytest.raises((AttributeError, TypeError)):
        state.consecutive_skip_count = 99  # type: ignore[misc]
    # __slots__ presence is the cheap-to-check structural guarantee.
    assert hasattr(CatchOutcome, "__slots__")
    assert hasattr(SemanticTDDCadenceState, "__slots__")


def test_catch_rate_computes_correctly_from_sample_outcomes():
    """6 catches / 10 outcomes -> rate 0.6."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        compute_catch_rate,
    )

    catches_kind = (CatchKind.RED_FIRST_CATCH,)
    no_catch = (CatchKind.NONE,)
    outcomes = tuple(
        _make_outcome(slice_id=f"s{idx}", catches=catches_kind if idx < 6 else no_catch)
        for idx in range(10)
    )
    assert compute_catch_rate(outcomes, 10) == pytest.approx(0.6)


def test_catch_rate_zero_when_no_outcomes():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        compute_catch_rate,
    )

    assert compute_catch_rate((), 10) == 0.0


def test_catch_rate_handles_partial_window():
    """3 catches / 4 outcomes when window=10 -> rate 0.75 (effective denom)."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        compute_catch_rate,
    )

    outcomes = (
        _make_outcome(slice_id="s0", catches=(CatchKind.RED_FIRST_CATCH,)),
        _make_outcome(slice_id="s1", catches=(CatchKind.CASCADE_CATCH,)),
        _make_outcome(slice_id="s2", catches=(CatchKind.NONE,)),
        _make_outcome(slice_id="s3", catches=(CatchKind.TYPE_INTROSPECTION,)),
    )
    assert compute_catch_rate(outcomes, 10) == pytest.approx(0.75)


def test_auto_select_mode_locks_full_when_catch_rate_above_60_percent():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        auto_select_cadence_mode,
    )

    catches = (CatchKind.RED_FIRST_CATCH,)
    no_catch = (CatchKind.NONE,)
    # 7 catches / 10 -> 0.70 >= 0.60 -> FULL
    outcomes = tuple(
        _make_outcome(slice_id=f"s{idx}", catches=catches if idx < 7 else no_catch)
        for idx in range(10)
    )
    state = _state_with_outcomes(outcomes)
    assert auto_select_cadence_mode(state) == SemanticTDDCadenceMode.FULL


def test_auto_select_mode_returns_standard_when_catch_rate_between_30_and_60():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        auto_select_cadence_mode,
    )

    catches = (CatchKind.RED_FIRST_CATCH,)
    no_catch = (CatchKind.NONE,)
    # 4 catches / 10 -> 0.40
    outcomes = tuple(
        _make_outcome(slice_id=f"s{idx}", catches=catches if idx < 4 else no_catch)
        for idx in range(10)
    )
    state = _state_with_outcomes(outcomes)
    assert auto_select_cadence_mode(state) == SemanticTDDCadenceMode.STANDARD


def test_auto_select_mode_returns_light_when_catch_rate_between_10_and_30():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        auto_select_cadence_mode,
    )

    catches = (CatchKind.RED_FIRST_CATCH,)
    no_catch = (CatchKind.NONE,)
    # 2 catches / 10 -> 0.20
    outcomes = tuple(
        _make_outcome(slice_id=f"s{idx}", catches=catches if idx < 2 else no_catch)
        for idx in range(10)
    )
    state = _state_with_outcomes(outcomes)
    assert auto_select_cadence_mode(state) == SemanticTDDCadenceMode.LIGHT


def test_auto_select_mode_returns_skip_next_when_below_10_percent():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        auto_select_cadence_mode,
    )

    no_catch = (CatchKind.NONE,)
    outcomes = tuple(_make_outcome(slice_id=f"s{idx}", catches=no_catch) for idx in range(10))
    state = _state_with_outcomes(outcomes)
    assert auto_select_cadence_mode(state) == SemanticTDDCadenceMode.SKIP_NEXT


def test_periodic_full_revalidation_fires_at_fifth_consecutive_skip():
    """consecutive_skip_count >= 5 + rate < 0.10 -> FULL (periodic revalidation)."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        auto_select_cadence_mode,
    )

    no_catch = (CatchKind.NONE,)
    outcomes = tuple(_make_outcome(slice_id=f"s{idx}", catches=no_catch) for idx in range(10))
    state = _state_with_outcomes(outcomes, consecutive_skip_count=5)
    assert auto_select_cadence_mode(state) == SemanticTDDCadenceMode.FULL


def test_xfail_transition_in_last_outcome_force_promotes_to_full():
    """XPASS<->XFAIL movement is high-signal: force FULL regardless of rate."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        auto_select_cadence_mode,
    )

    no_catch = (CatchKind.NONE,)
    # Build a state where rate would otherwise select SKIP_NEXT.
    older = tuple(_make_outcome(slice_id=f"s{idx}", catches=no_catch) for idx in range(9))
    latest = _make_outcome(slice_id="s_latest", catches=(CatchKind.XFAIL_TRANSITION,))
    state = _state_with_outcomes((latest,) + older)
    assert auto_select_cadence_mode(state) == SemanticTDDCadenceMode.FULL


def test_connectivity_after_finding_in_last_outcome_force_promotes_to_full():
    """A fresh AFTER-sweep connectivity finding forces FULL on next slice."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        auto_select_cadence_mode,
    )

    no_catch = (CatchKind.NONE,)
    older = tuple(_make_outcome(slice_id=f"s{idx}", catches=no_catch) for idx in range(9))
    latest = _make_outcome(
        slice_id="s_latest", catches=(CatchKind.CONNECTIVITY_AFTER,)
    )
    state = _state_with_outcomes((latest,) + older)
    assert auto_select_cadence_mode(state) == SemanticTDDCadenceMode.FULL


def test_operator_pin_override_wins_over_rate():
    """Active operator pin (slices_remaining > 0) overrides any rate signal."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        auto_select_cadence_mode,
    )

    catches = (CatchKind.RED_FIRST_CATCH,)
    # Rate would normally pick FULL, but operator pinned LIGHT for 3 slices.
    outcomes = tuple(_make_outcome(slice_id=f"s{idx}", catches=catches) for idx in range(10))
    state = _state_with_outcomes(
        outcomes,
        auto_mode_override=SemanticTDDCadenceMode.LIGHT,
        operator_pin_slices_remaining=3,
        operator_pin_reason="operator-test-pin",
    )
    assert auto_select_cadence_mode(state) == SemanticTDDCadenceMode.LIGHT


def test_firing_matrix_full_mode_includes_all_eight_steps():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        SemanticTDDCadenceMode,
        firing_matrix,
    )

    matrix = firing_matrix(SemanticTDDCadenceMode.FULL)
    for step in (
        "discovery",
        "red_first",
        "code_apply",
        "green_verify",
        "reinforce",
        "dogfood_proof",
        "receipt",
        "review",
    ):
        assert matrix[step] is True, f"FULL must fire {step!r}"


def test_firing_matrix_standard_mode_skips_only_review():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        SemanticTDDCadenceMode,
        firing_matrix,
    )

    matrix = firing_matrix(SemanticTDDCadenceMode.STANDARD)
    assert matrix["reinforce"] is True
    assert matrix["dogfood_proof"] is True
    assert matrix["receipt"] is True
    assert matrix["review"] is False
    assert matrix["xfail_ratchet_check"] is True
    assert matrix["connectivity_sweep"] is True


def test_firing_matrix_light_mode_skips_reinforce_and_dogfood_and_receipt():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        SemanticTDDCadenceMode,
        firing_matrix,
    )

    matrix = firing_matrix(SemanticTDDCadenceMode.LIGHT)
    assert matrix["reinforce"] is False
    assert matrix["dogfood_proof"] is False
    assert matrix["receipt"] is False
    assert matrix["red_first"] is True  # still required if new invariant
    assert matrix["xfail_ratchet_check"] is True  # cheap rail, never skips
    assert matrix["connectivity_sweep"] is True  # cheap rail, never skips


def test_firing_matrix_skip_next_disables_almost_everything_but_ratchet_rails():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        SemanticTDDCadenceMode,
        firing_matrix,
    )

    matrix = firing_matrix(SemanticTDDCadenceMode.SKIP_NEXT)
    assert matrix["discovery"] is False
    assert matrix["red_first"] is False
    assert matrix["code_apply"] is True  # the work itself still happens
    assert matrix["xfail_ratchet_check"] is True
    assert matrix["connectivity_sweep"] is True


def test_firing_matrix_keys_match_across_modes():
    """All modes must expose the same key set; only values differ."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        SemanticTDDCadenceMode,
        firing_matrix,
    )

    keys_full = set(firing_matrix(SemanticTDDCadenceMode.FULL).keys())
    for mode in (
        SemanticTDDCadenceMode.STANDARD,
        SemanticTDDCadenceMode.LIGHT,
        SemanticTDDCadenceMode.SKIP_NEXT,
        SemanticTDDCadenceMode.ADAPTIVE_AUTO,
    ):
        assert set(firing_matrix(mode).keys()) == keys_full


def test_apply_outcome_prepends_and_truncates_window():
    """Newest outcome at index 0; rolling window respects size cap."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceState,
        apply_outcome,
    )

    state = SemanticTDDCadenceState(rolling_window_size=3)
    for idx in range(5):
        state = apply_outcome(
            state,
            _make_outcome(slice_id=f"s{idx}", catches=(CatchKind.NONE,)),
        )
    assert len(state.recent_outcomes) == 3
    assert state.recent_outcomes[0].slice_id == "s4"
    assert state.recent_outcomes[-1].slice_id == "s2"


def test_apply_outcome_increments_skip_count_on_skip_mode():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        SemanticTDDCadenceState,
        apply_outcome,
    )

    state = SemanticTDDCadenceState()
    state = apply_outcome(
        state,
        _make_outcome(
            slice_id="s1",
            catches=(CatchKind.NONE,),
            mode_used=SemanticTDDCadenceMode.SKIP_NEXT,
        ),
    )
    state = apply_outcome(
        state,
        _make_outcome(
            slice_id="s2",
            catches=(CatchKind.NONE,),
            mode_used=SemanticTDDCadenceMode.SKIP_NEXT,
        ),
    )
    assert state.consecutive_skip_count == 2


def test_apply_outcome_resets_skip_count_on_non_skip_mode():
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        SemanticTDDCadenceState,
        apply_outcome,
    )

    state = SemanticTDDCadenceState(consecutive_skip_count=4)
    state = apply_outcome(
        state,
        _make_outcome(
            slice_id="s_full",
            catches=(CatchKind.RED_FIRST_CATCH,),
            mode_used=SemanticTDDCadenceMode.FULL,
        ),
    )
    assert state.consecutive_skip_count == 0
    assert state.last_full_run_slice_id == "s_full"


def test_apply_outcome_decrements_operator_pin_and_clears_at_zero():
    """Pin counts down; when it hits 0 the override is cleared."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        SemanticTDDCadenceState,
        apply_outcome,
    )

    state = SemanticTDDCadenceState(
        auto_mode_override=SemanticTDDCadenceMode.LIGHT,
        operator_pin_slices_remaining=2,
        operator_pin_reason="t",
    )
    state = apply_outcome(
        state,
        _make_outcome(
            slice_id="s1",
            catches=(CatchKind.NONE,),
            mode_used=SemanticTDDCadenceMode.LIGHT,
        ),
    )
    assert state.operator_pin_slices_remaining == 1
    assert state.auto_mode_override == SemanticTDDCadenceMode.LIGHT
    state = apply_outcome(
        state,
        _make_outcome(
            slice_id="s2",
            catches=(CatchKind.NONE,),
            mode_used=SemanticTDDCadenceMode.LIGHT,
        ),
    )
    assert state.operator_pin_slices_remaining == 0
    assert state.auto_mode_override is None
    assert state.operator_pin_reason == ""


def test_load_cadence_state_returns_default_when_jsonl_missing(tmp_path):
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        SemanticTDDCadenceMode,
        load_cadence_state,
    )

    state = load_cadence_state(tmp_path)
    assert state.current_mode == SemanticTDDCadenceMode.ADAPTIVE_AUTO
    assert state.recent_outcomes == ()
    assert state.consecutive_skip_count == 0


def test_persist_then_load_round_trips(tmp_path):
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CatchKind,
        SemanticTDDCadenceMode,
        SemanticTDDCadenceState,
        apply_outcome,
        load_cadence_state,
        persist_cadence_state,
    )

    state = SemanticTDDCadenceState(current_mode=SemanticTDDCadenceMode.STANDARD)
    state = apply_outcome(
        state,
        _make_outcome(
            slice_id="round-trip",
            catches=(CatchKind.RED_FIRST_CATCH, CatchKind.CASCADE_CATCH),
            mode_used=SemanticTDDCadenceMode.FULL,
            cost_seconds=42,
            timestamp_utc="2026-05-23T00:00:00Z",
        ),
    )
    persist_cadence_state(state, tmp_path)
    loaded = load_cadence_state(tmp_path)
    assert loaded.current_mode == SemanticTDDCadenceMode.STANDARD
    assert loaded.last_full_run_slice_id == "round-trip"
    assert len(loaded.recent_outcomes) == 1
    outcome = loaded.recent_outcomes[0]
    assert outcome.slice_id == "round-trip"
    assert outcome.catches_found == (
        CatchKind.RED_FIRST_CATCH,
        CatchKind.CASCADE_CATCH,
    )
    assert outcome.cost_seconds == 42


def test_persist_cadence_state_writes_under_path_roots_state(tmp_path):
    """Persistence path must resolve to ``PathRoots().state``."""
    from dev.scripts.devctl.runtime.project_governance_contract import PathRoots
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        CADENCE_STATE_STORE_FILENAME,
        SemanticTDDCadenceState,
        persist_cadence_state,
    )

    state = SemanticTDDCadenceState()
    path = persist_cadence_state(state, tmp_path)
    expected = tmp_path / PathRoots().state / CADENCE_STATE_STORE_FILENAME
    assert path == expected
    assert path.exists()


def test_load_cadence_state_replays_latest_row_when_multiple_appended(tmp_path):
    """Append-only ledger: load_cadence_state replays the last row."""
    from dev.scripts.devctl.runtime.semantic_tdd_cadence import (
        SemanticTDDCadenceMode,
        SemanticTDDCadenceState,
        load_cadence_state,
        persist_cadence_state,
    )

    first = SemanticTDDCadenceState(current_mode=SemanticTDDCadenceMode.FULL)
    persist_cadence_state(first, tmp_path)
    second = SemanticTDDCadenceState(current_mode=SemanticTDDCadenceMode.LIGHT)
    persist_cadence_state(second, tmp_path)
    loaded = load_cadence_state(tmp_path)
    assert loaded.current_mode == SemanticTDDCadenceMode.LIGHT


# ---------------------------------------------------------------------------
# 2b — target architecture, xfail-strict
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "A38.1 S1.A target: every commit touching dev/scripts/devctl/runtime/**.py "
        "should have a paired CadenceOutcome row in dev/state/semantic_tdd_cadence.jsonl. "
        "Ratchets to GREEN once the cadence reducer is wired into the develop-next "
        "pipeline (S1.D dogfood). Stays RED as visible debt until then."
    ),
)
def test_every_runtime_touching_commit_has_paired_cadence_outcome():
    """Target-architecture invariant.

    Scans the recent git log for commits that touched
    ``dev/scripts/devctl/runtime/*.py`` and asserts each commit's SHA
    appears at least once in
    ``dev/state/semantic_tdd_cadence.jsonl`` (the paired CadenceOutcome
    row's evidence ref, slice_id, or timestamp window).

    The substrate exists in S1.A but no callsite emits paired outcomes
    yet, so this stays xfail-strict until S1.D wires the controller into
    ``develop next``. Strict so the assertion cannot be silently
    removed.
    """
    log_result = subprocess.run(
        [
            "git",
            "log",
            "--since=14.days",
            "--name-only",
            "--pretty=format:%H",
            "--",
            "dev/scripts/devctl/runtime/",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if log_result.returncode != 0:
        pytest.skip(f"git log failed: {log_result.stderr.strip()!r}")

    commits: list[str] = []
    current_sha = ""
    for raw_line in log_result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            current_sha = ""
            continue
        if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
            current_sha = line
            continue
        if current_sha and line.startswith("dev/scripts/devctl/runtime/") and line.endswith(".py"):
            if current_sha not in commits:
                commits.append(current_sha)

    if not commits:
        # Tree state where no runtime-touching commits in window — the
        # invariant is vacuously true today but must still ratchet, so
        # we fail to keep the xfail-strict marker honest.
        raise AssertionError(
            "no runtime-touching commits in 14-day window; cannot demonstrate pairing"
        )

    state_path = REPO_ROOT / "dev" / "state" / "semantic_tdd_cadence.jsonl"
    if not state_path.exists():
        raise AssertionError(
            f"target cadence ledger missing at {state_path}: no outcomes paired"
        )
    ledger_text = state_path.read_text(encoding="utf-8")
    unpaired = [sha for sha in commits if sha not in ledger_text]
    assert not unpaired, (
        f"{len(unpaired)} runtime-touching commits lack a paired CadenceOutcome row: "
        f"{unpaired[:5]} (showing first 5)"
    )
