"""Typed adaptive cadence-mode substrate for the semantic-TDD ritual.

Sibling to :mod:`semantic_tdd_role` (which carries the 9-step ritual phases).
This module carries the ADAPTIVE-CADENCE controller that picks which subset
of those phases fires for the next slice based on a rolling-window of typed
catch outcomes.

Design references:
- ``delete_after_ingest.md`` A38.1 ("Adaptive Semantic-TDD Cadence Mode").
- ``evidence.md`` Cases 1-11 (the typed ``CatchKind`` taxonomy below maps
  to the catch-classes those cases demonstrated).

Substrate boundaries (this module):
- Pure typed dataclasses + enums (all ``frozen=True, slots=True``).
- Pure reducer functions (``compute_catch_rate``, ``auto_select_cadence_mode``,
  ``firing_matrix``, ``apply_outcome``) — no I/O, no globals.
- Locked-write persistence helpers (``load_cadence_state``,
  ``persist_cadence_state``) wrap :mod:`state_store_authority` and the
  governed ``PathRoots.state`` field — they NEVER mutate state values, they
  only serialize / deserialize them.

NOT in this module (explicit non-goals for S1.A):
- CLI surface (``devctl semantic-tdd cadence …``) — S1.C.
- Guard integration (``check_semantic_tdd_evidence_log.py`` LIGHT relaxation)
  — S1.B.
- Mode-change transition packet emission — S1.C.
- Dogfood case in ``evidence.md`` — orchestrator integration step.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .enum_compat import StrEnum
from .project_governance_contract import PathRoots
from .state_store_authority import (
    StateStoreWriteResult,
    append_json_mapping,
    read_json_mappings_strict,
)

CADENCE_STATE_CONTRACT_ID = "SemanticTDDCadenceState"
CADENCE_STATE_SCHEMA_VERSION = 1
CADENCE_STATE_STORE_FILENAME = "semantic_tdd_cadence.jsonl"
DEFAULT_ROLLING_WINDOW_SIZE = 10
PERIODIC_FULL_REVALIDATION_THRESHOLD = 5
CONNECTIVITY_AFTER_FORCE_PROMOTE_SLICES = 2

# Catch-rate auto-selection thresholds (operator-authored A38.1 numbers).
RATE_FULL_FLOOR = 0.60
RATE_STANDARD_FLOOR = 0.30
RATE_LIGHT_FLOOR = 0.10


class SemanticTDDCadenceMode(StrEnum):
    """Typed cadence modes for the semantic-TDD ritual.

    Each mode gates a different subset of the 8-step firing matrix. See
    :func:`firing_matrix` for the exact rail-by-rail truth table.
    """

    FULL = "full"
    STANDARD = "standard"
    LIGHT = "light"
    SKIP_NEXT = "skip_next"
    ADAPTIVE_AUTO = "adaptive_auto"


class CatchKind(StrEnum):
    """Typed catch taxonomy used to score whether a slice "caught" something.

    Categories correspond to the catch-classes observed in
    ``evidence.md`` Cases 1-11. ``NONE`` is the sentinel for slices that
    ran the ritual but did not surface a catchable signal.
    """

    RED_FIRST_CATCH = "red_first_catch"
    CASCADE_CATCH = "cascade_catch"
    CONNECTIVITY_AFTER = "connectivity_after_finding"
    XFAIL_TRANSITION = "xfail_strict_transition"
    TYPE_INTROSPECTION = "type_introspection_catch"
    NONE = "no_catch"


@dataclass(frozen=True, slots=True)
class CatchOutcome:
    """One observed slice outcome in the rolling cadence window.

    The reducer state stores a tuple of these, newest-first. Truncated to
    ``rolling_window_size`` rows on every :func:`apply_outcome` call.
    """

    slice_id: str
    mode_used: SemanticTDDCadenceMode
    catches_found: tuple[CatchKind, ...]
    cost_seconds: int
    timestamp_utc: str
    blast_radius_hint: str = "unknown"  # v2 hook for slice-blast-radius signals

    def to_dict(self) -> dict[str, object]:
        return {
            "slice_id": self.slice_id,
            "mode_used": str(self.mode_used),
            "catches_found": [str(kind) for kind in self.catches_found],
            "cost_seconds": int(self.cost_seconds),
            "timestamp_utc": self.timestamp_utc,
            "blast_radius_hint": self.blast_radius_hint,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "CatchOutcome":
        raw_catches = payload.get("catches_found") or ()
        if isinstance(raw_catches, (list, tuple)):
            catches: tuple[CatchKind, ...] = tuple(
                _catch_kind_from_value(item) for item in raw_catches
            )
        else:
            catches = ()
        return cls(
            slice_id=str(payload.get("slice_id") or ""),
            mode_used=_cadence_mode_from_value(payload.get("mode_used")),
            catches_found=catches,
            cost_seconds=int(payload.get("cost_seconds") or 0),
            timestamp_utc=str(payload.get("timestamp_utc") or ""),
            blast_radius_hint=str(payload.get("blast_radius_hint") or "unknown"),
        )


@dataclass(frozen=True, slots=True)
class SemanticTDDCadenceState:
    """Persisted cadence controller state.

    Mutations must go through :func:`apply_outcome` (which returns a new
    instance — these dataclasses are frozen). Persistence is via
    :func:`persist_cadence_state`; load via :func:`load_cadence_state`.
    """

    contract_id: str = CADENCE_STATE_CONTRACT_ID
    schema_version: int = CADENCE_STATE_SCHEMA_VERSION
    current_mode: SemanticTDDCadenceMode = SemanticTDDCadenceMode.ADAPTIVE_AUTO
    rolling_window_size: int = DEFAULT_ROLLING_WINDOW_SIZE
    recent_outcomes: tuple[CatchOutcome, ...] = field(default_factory=tuple)
    auto_mode_override: SemanticTDDCadenceMode | None = None
    operator_pin_reason: str = ""
    operator_pin_slices_remaining: int = 0
    last_full_run_slice_id: str = ""
    consecutive_skip_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "schema_version": int(self.schema_version),
            "current_mode": str(self.current_mode),
            "rolling_window_size": int(self.rolling_window_size),
            "recent_outcomes": [outcome.to_dict() for outcome in self.recent_outcomes],
            "auto_mode_override": (
                str(self.auto_mode_override) if self.auto_mode_override is not None else None
            ),
            "operator_pin_reason": self.operator_pin_reason,
            "operator_pin_slices_remaining": int(self.operator_pin_slices_remaining),
            "last_full_run_slice_id": self.last_full_run_slice_id,
            "consecutive_skip_count": int(self.consecutive_skip_count),
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "SemanticTDDCadenceState":
        raw_outcomes = payload.get("recent_outcomes") or ()
        if isinstance(raw_outcomes, (list, tuple)):
            outcomes = tuple(
                CatchOutcome.from_mapping(item)
                for item in raw_outcomes
                if isinstance(item, Mapping)
            )
        else:
            outcomes = ()
        raw_override = payload.get("auto_mode_override")
        override: SemanticTDDCadenceMode | None
        if raw_override in (None, "", "null"):
            override = None
        else:
            override = _cadence_mode_from_value(raw_override)
        return cls(
            contract_id=str(payload.get("contract_id") or CADENCE_STATE_CONTRACT_ID),
            schema_version=int(payload.get("schema_version") or CADENCE_STATE_SCHEMA_VERSION),
            current_mode=_cadence_mode_from_value(payload.get("current_mode")),
            rolling_window_size=int(
                payload.get("rolling_window_size") or DEFAULT_ROLLING_WINDOW_SIZE
            ),
            recent_outcomes=outcomes,
            auto_mode_override=override,
            operator_pin_reason=str(payload.get("operator_pin_reason") or ""),
            operator_pin_slices_remaining=int(
                payload.get("operator_pin_slices_remaining") or 0
            ),
            last_full_run_slice_id=str(payload.get("last_full_run_slice_id") or ""),
            consecutive_skip_count=int(payload.get("consecutive_skip_count") or 0),
        )


# ---------------------------------------------------------------------------
# Pure reducer functions (no I/O, no globals).
# ---------------------------------------------------------------------------


def compute_catch_rate(
    outcomes: tuple[CatchOutcome, ...],
    window: int,
) -> float:
    """Fraction of recent outcomes that contained at least one real catch.

    A "catch" is any ``CatchKind`` other than ``NONE``. The denominator is
    ``min(len(outcomes), window)`` so a half-full window still returns a
    valid ratio. Empty window returns ``0.0``.
    """
    if window <= 0 or not outcomes:
        return 0.0
    effective = min(len(outcomes), window)
    if effective <= 0:
        return 0.0
    sample = outcomes[:effective]
    caught = sum(1 for outcome in sample if _has_real_catch(outcome.catches_found))
    return caught / effective


def auto_select_cadence_mode(
    state: SemanticTDDCadenceState,
) -> SemanticTDDCadenceMode:
    """Pure auto-selection reducer.

    Precedence (highest first):

    1. Operator pin: if ``auto_mode_override`` is set and
       ``operator_pin_slices_remaining > 0`` -> return the override.
       (Decrement happens in :func:`apply_outcome`, not here.)
    2. Last-outcome force-promote: an ``XFAIL_TRANSITION`` or
       ``CONNECTIVITY_AFTER`` finding in the most recent outcome forces
       ``FULL`` regardless of rolling rate.
    3. Rolling-rate thresholds:
       - rate >= 0.60 -> FULL
       - 0.30 <= rate < 0.60 -> STANDARD
       - 0.10 <= rate < 0.30 -> LIGHT
       - rate < 0.10 -> SKIP_NEXT, BUT
         if ``consecutive_skip_count >= 5`` -> FULL (periodic revalidation).
    """
    if (
        state.auto_mode_override is not None
        and state.operator_pin_slices_remaining > 0
    ):
        return state.auto_mode_override

    if state.recent_outcomes:
        last_outcome = state.recent_outcomes[0]
        if CatchKind.XFAIL_TRANSITION in last_outcome.catches_found:
            return SemanticTDDCadenceMode.FULL
        if CatchKind.CONNECTIVITY_AFTER in last_outcome.catches_found:
            return SemanticTDDCadenceMode.FULL

    rate = compute_catch_rate(state.recent_outcomes, state.rolling_window_size)
    if rate >= RATE_FULL_FLOOR:
        return SemanticTDDCadenceMode.FULL
    if rate >= RATE_STANDARD_FLOOR:
        return SemanticTDDCadenceMode.STANDARD
    if rate >= RATE_LIGHT_FLOOR:
        return SemanticTDDCadenceMode.LIGHT
    # rate < 0.10
    if state.consecutive_skip_count >= PERIODIC_FULL_REVALIDATION_THRESHOLD:
        return SemanticTDDCadenceMode.FULL
    return SemanticTDDCadenceMode.SKIP_NEXT


def firing_matrix(mode: SemanticTDDCadenceMode) -> Mapping[str, bool]:
    """Per-mode truth table for the 8-step ritual + cheap-rail invariants.

    The 8 ritual steps mirror :class:`SemanticTDDRolePhase` plus
    auxiliary rails:

    - ``discovery``, ``red_first``, ``code_apply``, ``green_verify``,
      ``reinforce``, ``dogfood_proof``, ``receipt``, ``review`` -> the
      consolidated semantic-TDD role's phases.
    - ``xfail_ratchet_check``, ``connectivity_sweep`` -> CHEAP rails;
      these ALWAYS fire under every mode (including ``SKIP_NEXT``)
      because they're fast file-glob style invariants whose value is
      worth the per-slice cost (operator A38.1 design note).
    - ``evidence_log_case_add`` -> cheap rail, but expected to relax to
      "case append optional" under LIGHT/SKIP_NEXT in S1.B integration.
      Here in S1.A we expose the typed bit; the actual relaxation lives
      in ``check_semantic_tdd_evidence_log.py`` (S1.B).

    Mode semantics:

    - ``FULL`` -> everything fires; the canonical 9-step ritual.
    - ``STANDARD`` -> all but ``review`` (reviewer-packet) fires; reviewer
      handoff is deferred to a later slice.
    - ``LIGHT`` -> cheap rails + discovery + red_first + code_apply +
      green_verify only. ``reinforce`` / ``dogfood_proof`` / ``receipt`` /
      ``review`` are deferred (this is the steady-state savings).
    - ``SKIP_NEXT`` -> the work itself still happens (``code_apply``) and
      cheap rails still fire (``xfail_ratchet_check``,
      ``connectivity_sweep``), but expensive + discovery rails are
      skipped. Emergency-bypass-style: used when the rolling catch rate
      is so low the ritual is overhead. ``consecutive_skip_count >= 5``
      forces periodic FULL revalidation per :func:`auto_select_cadence_mode`.
    - ``ADAPTIVE_AUTO`` -> NOT a firing mode itself; this enum value means
      "use :func:`auto_select_cadence_mode` to pick FULL / STANDARD /
      LIGHT / SKIP_NEXT". If a caller passes ADAPTIVE_AUTO straight into
      the matrix we treat it as STANDARD as a safe fallback (callers
      should route through auto-select first; this branch exists so the
      function is total).
    """
    if mode is SemanticTDDCadenceMode.FULL:
        return _FIRING_FULL
    if mode is SemanticTDDCadenceMode.STANDARD:
        return _FIRING_STANDARD
    if mode is SemanticTDDCadenceMode.LIGHT:
        return _FIRING_LIGHT
    if mode is SemanticTDDCadenceMode.SKIP_NEXT:
        return _FIRING_SKIP_NEXT
    # ADAPTIVE_AUTO fallback -> STANDARD shape.
    return _FIRING_STANDARD


def apply_outcome(
    state: SemanticTDDCadenceState,
    outcome: CatchOutcome,
) -> SemanticTDDCadenceState:
    """Pure reducer: fold one outcome into the rolling state.

    Returns a NEW ``SemanticTDDCadenceState`` (frozen dataclasses are not
    mutated). The new state:

    - Prepends ``outcome`` to ``recent_outcomes``, truncated to
      ``rolling_window_size``.
    - Increments ``consecutive_skip_count`` if ``outcome.mode_used ==
      SKIP_NEXT``, otherwise resets to ``0``.
    - Decrements ``operator_pin_slices_remaining`` if it was ``> 0``; once
      it hits ``0`` the ``auto_mode_override`` is cleared.
    - Updates ``last_full_run_slice_id`` if the outcome's mode was FULL.
    """
    new_outcomes = (outcome,) + state.recent_outcomes
    if len(new_outcomes) > state.rolling_window_size:
        new_outcomes = new_outcomes[: state.rolling_window_size]

    if outcome.mode_used is SemanticTDDCadenceMode.SKIP_NEXT:
        next_skip_count = state.consecutive_skip_count + 1
    else:
        next_skip_count = 0

    if state.operator_pin_slices_remaining > 0:
        next_pin = state.operator_pin_slices_remaining - 1
    else:
        next_pin = 0
    if next_pin <= 0:
        next_override: SemanticTDDCadenceMode | None = None
        next_pin = 0
    else:
        next_override = state.auto_mode_override

    if outcome.mode_used is SemanticTDDCadenceMode.FULL:
        next_full_slice = outcome.slice_id or state.last_full_run_slice_id
    else:
        next_full_slice = state.last_full_run_slice_id

    return SemanticTDDCadenceState(
        contract_id=state.contract_id,
        schema_version=state.schema_version,
        current_mode=state.current_mode,
        rolling_window_size=state.rolling_window_size,
        recent_outcomes=new_outcomes,
        auto_mode_override=next_override,
        operator_pin_reason=state.operator_pin_reason if next_pin > 0 else "",
        operator_pin_slices_remaining=next_pin,
        last_full_run_slice_id=next_full_slice,
        consecutive_skip_count=next_skip_count,
    )


# ---------------------------------------------------------------------------
# Persistence helpers (I/O — kept separate from the pure reducers).
# ---------------------------------------------------------------------------


def cadence_state_path(repo_root: Path) -> Path:
    """Resolve the governed jsonl store path under ``PathRoots.state``."""
    state_root = PathRoots().state
    return Path(repo_root) / state_root / CADENCE_STATE_STORE_FILENAME


def load_cadence_state(repo_root: Path) -> SemanticTDDCadenceState:
    """Read the most-recent persisted cadence state, or return defaults.

    Empty / missing store returns a fresh default state with
    ``current_mode == ADAPTIVE_AUTO`` and an empty rolling window. The
    "latest row wins" semantics mirror how :mod:`state_store_authority`
    treats append-only state stores: each ``persist_cadence_state`` call
    appends one row, and the loader replays the last one.
    """
    path = cadence_state_path(repo_root)
    if not path.exists():
        return SemanticTDDCadenceState()
    rows = read_json_mappings_strict(path)
    if not rows:
        return SemanticTDDCadenceState()
    return SemanticTDDCadenceState.from_mapping(rows[-1])


def persist_cadence_state(
    state: SemanticTDDCadenceState,
    repo_root: Path,
) -> Path:
    """Append the state row to the governed jsonl store.

    The locked-write semantics come from
    :func:`append_json_mapping`; this helper just wraps the path
    resolution and ``store_id`` tagging.
    """
    path = cadence_state_path(repo_root)
    append_json_mapping(
        path,
        state.to_dict(),
        store_id=CADENCE_STATE_CONTRACT_ID,
    )
    return path


# ---------------------------------------------------------------------------
# Private helpers.
# ---------------------------------------------------------------------------


def _has_real_catch(catches: tuple[CatchKind, ...]) -> bool:
    """True iff at least one entry is a non-NONE catch.

    Spec note: an outcome list that is ``(CatchKind.NONE,)`` or empty is
    NOT a catch; anything else counts.
    """
    if not catches:
        return False
    for kind in catches:
        if kind is not CatchKind.NONE:
            return True
    return False


def _cadence_mode_from_value(value: Any) -> SemanticTDDCadenceMode:
    if isinstance(value, SemanticTDDCadenceMode):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        for mode in SemanticTDDCadenceMode:
            if mode.value == lowered:
                return mode
    return SemanticTDDCadenceMode.ADAPTIVE_AUTO


def _catch_kind_from_value(value: Any) -> CatchKind:
    if isinstance(value, CatchKind):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        for kind in CatchKind:
            if kind.value == lowered:
                return kind
    return CatchKind.NONE


# Pre-computed firing-matrix maps. Cheap rails always True; mode-gated rails
# follow the operator A38.1 truth table.
_FIRING_FULL: Mapping[str, bool] = {
    "discovery": True,
    "red_first": True,
    "code_apply": True,
    "green_verify": True,
    "reinforce": True,
    "dogfood_proof": True,
    "receipt": True,
    "review": True,
    "xfail_ratchet_check": True,
    "connectivity_sweep": True,
    "evidence_log_case_add": True,
}

_FIRING_STANDARD: Mapping[str, bool] = {
    "discovery": True,
    "red_first": True,
    "code_apply": True,
    "green_verify": True,
    "reinforce": True,
    "dogfood_proof": True,
    "receipt": True,
    "review": False,
    "xfail_ratchet_check": True,
    "connectivity_sweep": True,
    "evidence_log_case_add": True,
}

_FIRING_LIGHT: Mapping[str, bool] = {
    "discovery": True,
    "red_first": True,
    "code_apply": True,
    "green_verify": True,
    "reinforce": False,
    "dogfood_proof": False,
    "receipt": False,
    "review": False,
    "xfail_ratchet_check": True,
    "connectivity_sweep": True,
    "evidence_log_case_add": True,
}

_FIRING_SKIP_NEXT: Mapping[str, bool] = {
    "discovery": False,
    "red_first": False,
    "code_apply": True,  # the work itself still has to happen
    "green_verify": False,
    "reinforce": False,
    "dogfood_proof": False,
    "receipt": False,
    "review": False,
    "xfail_ratchet_check": True,  # cheap rail, never skips
    "connectivity_sweep": True,  # cheap rail, never skips
    "evidence_log_case_add": False,
}


__all__ = [
    "CADENCE_STATE_CONTRACT_ID",
    "CADENCE_STATE_SCHEMA_VERSION",
    "CADENCE_STATE_STORE_FILENAME",
    "CONNECTIVITY_AFTER_FORCE_PROMOTE_SLICES",
    "DEFAULT_ROLLING_WINDOW_SIZE",
    "PERIODIC_FULL_REVALIDATION_THRESHOLD",
    "RATE_FULL_FLOOR",
    "RATE_LIGHT_FLOOR",
    "RATE_STANDARD_FLOOR",
    "CatchKind",
    "CatchOutcome",
    "SemanticTDDCadenceMode",
    "SemanticTDDCadenceState",
    "apply_outcome",
    "auto_select_cadence_mode",
    "cadence_state_path",
    "compute_catch_rate",
    "firing_matrix",
    "load_cadence_state",
    "persist_cadence_state",
]
