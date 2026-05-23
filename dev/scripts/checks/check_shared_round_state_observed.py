#!/usr/bin/env python3
"""A18 G34 guard: shared round state observation before mutation.

Per delete_after_ingest.md A18 lines 1113-1117 (and shared worker awareness
requirements at lines 938-950), this guard fails closed when an actor starts
mutation without observing the current shared round digest. The full digest
must include:

- current PlanRow id (the row authority lane the actor mutates)
- source_hash (the typed source-hash of that PlanRow)
- peer occupancies (live peer role occupancies for the same row)
- peer write leases (active write leases held by peers on the row)
- active packets (packet/action_request/finding refs the actor must know)
- blockers (typed blockers on the row)
- proof obligations (typed proof obligations on the row)
- ``observed_at`` evidence (a fresh observation timestamp within the freshness
  budget; otherwise the digest is stale and is not proof of awareness)

This is a pre-mutation guard: it must run before write, not only at
commit/push time. It does not depend on the commit gate.

Machine reasons are stable across releases so router/policy/CI tools can
match on them directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        parse_utc as _parse_utc,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        parse_utc as _parse_utc,
        utc_timestamp,
    )


COMMAND = "check_shared_round_state_observed"
CONTRACT_ID = "SharedRoundStateObservedGuard"

DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
DEFAULT_FRESHNESS_WINDOW_SECONDS = 5 * 60

RULE_MISSING_PLAN_ROW_OBSERVATION = "missing_plan_row_observation"
RULE_MISSING_SOURCE_HASH_OBSERVATION = "missing_source_hash_observation"
RULE_MISSING_PEER_OCCUPANCY_OBSERVATION = "missing_peer_occupancy_observation"
RULE_MISSING_PEER_LEASE_OBSERVATION = "missing_peer_lease_observation"
RULE_MISSING_ACTIVE_PACKET_OBSERVATION = "missing_active_packet_observation"
RULE_MISSING_BLOCKER_OBSERVATION = "missing_blocker_observation"
RULE_MISSING_PROOF_OBLIGATION_OBSERVATION = "missing_proof_obligation_observation"
RULE_STALE_OBSERVED_AT = "stale_observed_at"

DISPLAY_TEXT = (
    "Shared round state not observed. The actor cannot start mutation without "
    "first observing the current shared round digest: PlanRow, source hash, "
    "peer occupancies, peer write leases, active packets, blockers, proof "
    "obligations, and a fresh observed_at timestamp."
)


@dataclass(frozen=True, slots=True)
class SharedRoundViolation:
    rule_id: str
    detail: str
    remediation: str
    actor_id: str = ""
    row_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SharedRoundObservation:
    """Typed view of an actor's pre-mutation shared round observation."""

    actor_id: str
    row_id: str
    plan_row_observed: bool
    source_hash_observed: str
    peer_occupancies_observed: tuple[str, ...]
    peer_write_leases_observed: tuple[str, ...]
    active_packets_observed: tuple[str, ...]
    blockers_observed: tuple[str, ...]
    proof_obligations_observed: tuple[str, ...]
    observed_at_utc: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "SharedRoundObservation":
        return cls(
            actor_id=str(payload.get("actor_id") or "").strip(),
            row_id=str(payload.get("row_id") or "").strip(),
            plan_row_observed=bool(payload.get("plan_row_observed")),
            source_hash_observed=str(payload.get("source_hash_observed") or "").strip(),
            peer_occupancies_observed=tuple(
                _as_str_tuple(payload.get("peer_occupancies_observed"))
            ),
            peer_write_leases_observed=tuple(
                _as_str_tuple(payload.get("peer_write_leases_observed"))
            ),
            active_packets_observed=tuple(
                _as_str_tuple(payload.get("active_packets_observed"))
            ),
            blockers_observed=tuple(_as_str_tuple(payload.get("blockers_observed"))),
            proof_obligations_observed=tuple(
                _as_str_tuple(payload.get("proof_obligations_observed"))
            ),
            observed_at_utc=str(payload.get("observed_at_utc") or "").strip(),
        )


@dataclass(frozen=True, slots=True)
class SharedRoundExpectation:
    """Typed view of what the live shared round digest demands an actor observe."""

    row_id: str
    source_hash: str
    requires_peer_occupancies: bool = True
    requires_peer_write_leases: bool = True
    requires_active_packets: bool = True
    requires_blockers: bool = True
    requires_proof_obligations: bool = True


def evaluate_observation(
    *,
    observation: SharedRoundObservation,
    expectation: SharedRoundExpectation,
    now: datetime | None = None,
    freshness_window_seconds: int = DEFAULT_FRESHNESS_WINDOW_SECONDS,
) -> tuple[SharedRoundViolation, ...]:
    """Evaluate one actor's shared-round observation against expected digest."""
    now_utc = now or datetime.now(timezone.utc)
    actor_id = observation.actor_id
    row_id = expectation.row_id or observation.row_id
    violations: list[SharedRoundViolation] = []

    if not observation.plan_row_observed or observation.row_id != expectation.row_id:
        violations.append(
            SharedRoundViolation(
                rule_id=RULE_MISSING_PLAN_ROW_OBSERVATION,
                detail=(
                    f"actor={actor_id!r} did not observe current PlanRow "
                    f"{expectation.row_id!r} before mutation"
                ),
                remediation=(
                    "Load the current PlanRow into the shared-round digest "
                    "before any mutation; pre-mutation observation is required."
                ),
                actor_id=actor_id,
                row_id=row_id,
            )
        )

    if not observation.source_hash_observed:
        violations.append(
            SharedRoundViolation(
                rule_id=RULE_MISSING_SOURCE_HASH_OBSERVATION,
                detail=(
                    f"actor={actor_id!r} did not observe source_hash for row "
                    f"{expectation.row_id!r}"
                ),
                remediation=(
                    "Record the typed PlanRow source_hash in the shared-round "
                    "digest; mutation cannot proceed against an unknown source."
                ),
                actor_id=actor_id,
                row_id=row_id,
            )
        )
    elif expectation.source_hash and observation.source_hash_observed != expectation.source_hash:
        violations.append(
            SharedRoundViolation(
                rule_id=RULE_MISSING_SOURCE_HASH_OBSERVATION,
                detail=(
                    f"actor={actor_id!r} observed stale source_hash "
                    f"{observation.source_hash_observed!r}; expected "
                    f"{expectation.source_hash!r}"
                ),
                remediation=(
                    "Re-read the typed PlanRow source_hash; the digest is "
                    "behind live state."
                ),
                actor_id=actor_id,
                row_id=row_id,
            )
        )

    if expectation.requires_peer_occupancies and not observation.peer_occupancies_observed:
        violations.append(
            SharedRoundViolation(
                rule_id=RULE_MISSING_PEER_OCCUPANCY_OBSERVATION,
                detail=(
                    f"actor={actor_id!r} did not observe peer occupancies "
                    f"for row {expectation.row_id!r}"
                ),
                remediation=(
                    "Load typed peer role occupancies before mutation so "
                    "shared workers can coordinate."
                ),
                actor_id=actor_id,
                row_id=row_id,
            )
        )

    if expectation.requires_peer_write_leases and not observation.peer_write_leases_observed:
        violations.append(
            SharedRoundViolation(
                rule_id=RULE_MISSING_PEER_LEASE_OBSERVATION,
                detail=(
                    f"actor={actor_id!r} did not observe peer write leases "
                    f"for row {expectation.row_id!r}"
                ),
                remediation=(
                    "Load active peer write leases; mutating without lease "
                    "visibility risks overwriting another actor's work."
                ),
                actor_id=actor_id,
                row_id=row_id,
            )
        )

    if expectation.requires_active_packets and not observation.active_packets_observed:
        violations.append(
            SharedRoundViolation(
                rule_id=RULE_MISSING_ACTIVE_PACKET_OBSERVATION,
                detail=(
                    f"actor={actor_id!r} did not observe active "
                    "packet/action_request/finding refs for row "
                    f"{expectation.row_id!r}"
                ),
                remediation=(
                    "Load active packets into the shared-round digest before "
                    "mutation; unobserved packets often carry blockers."
                ),
                actor_id=actor_id,
                row_id=row_id,
            )
        )

    if expectation.requires_blockers and not observation.blockers_observed:
        violations.append(
            SharedRoundViolation(
                rule_id=RULE_MISSING_BLOCKER_OBSERVATION,
                detail=(
                    f"actor={actor_id!r} did not observe blockers for row "
                    f"{expectation.row_id!r}"
                ),
                remediation=(
                    "Load typed blockers into the digest; mutation must not "
                    "race past unobserved blockers."
                ),
                actor_id=actor_id,
                row_id=row_id,
            )
        )

    if expectation.requires_proof_obligations and not observation.proof_obligations_observed:
        violations.append(
            SharedRoundViolation(
                rule_id=RULE_MISSING_PROOF_OBLIGATION_OBSERVATION,
                detail=(
                    f"actor={actor_id!r} did not observe proof obligations "
                    f"for row {expectation.row_id!r}"
                ),
                remediation=(
                    "Load typed proof obligations so the actor commits to "
                    "the proof chain the row requires."
                ),
                actor_id=actor_id,
                row_id=row_id,
            )
        )

    observed_at = _parse_utc(observation.observed_at_utc)
    if observed_at is None:
        violations.append(
            SharedRoundViolation(
                rule_id=RULE_STALE_OBSERVED_AT,
                detail=(
                    f"actor={actor_id!r} did not record an observed_at "
                    "timestamp for the shared-round digest"
                ),
                remediation=(
                    "Stamp observed_at_utc with a fresh ISO-8601 timestamp "
                    "before mutation; missing evidence is not proof."
                ),
                actor_id=actor_id,
                row_id=row_id,
            )
        )
    else:
        delta = now_utc - observed_at
        if delta > timedelta(seconds=freshness_window_seconds):
            violations.append(
                SharedRoundViolation(
                    rule_id=RULE_STALE_OBSERVED_AT,
                    detail=(
                        f"actor={actor_id!r} observed shared round digest at "
                        f"{observation.observed_at_utc!r}, but that is older "
                        f"than the freshness window of "
                        f"{freshness_window_seconds}s"
                    ),
                    remediation=(
                        "Re-observe the shared-round digest within the "
                        "freshness window before mutation."
                    ),
                    actor_id=actor_id,
                    row_id=row_id,
                )
            )

    return tuple(violations)


def build_report(
    *,
    observations: Sequence[Mapping[str, object]] | Sequence[SharedRoundObservation] | None = None,
    expectation: SharedRoundExpectation | Mapping[str, object] | None = None,
    state_path: Path | None = None,
    current_row_id: str = DEFAULT_ROW_ID,
    freshness_window_seconds: int = DEFAULT_FRESHNESS_WINDOW_SECONDS,
    now: datetime | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    checked_surfaces: list[str] = []
    now_utc = now or datetime.now(timezone.utc)

    if observations is None or expectation is None:
        path = state_path or _default_state_path()
        checked_surfaces.append(str(path))
        loaded_observations, loaded_expectation = _load_state(path, warnings)
        if observations is None:
            observations = loaded_observations
        if expectation is None:
            expectation = loaded_expectation

    if expectation is None:
        expectation = SharedRoundExpectation(row_id=current_row_id, source_hash="")
    elif isinstance(expectation, Mapping):
        expectation = SharedRoundExpectation(
            row_id=str(expectation.get("row_id") or current_row_id),
            source_hash=str(expectation.get("source_hash") or "").strip(),
            requires_peer_occupancies=bool(expectation.get("requires_peer_occupancies", True)),
            requires_peer_write_leases=bool(expectation.get("requires_peer_write_leases", True)),
            requires_active_packets=bool(expectation.get("requires_active_packets", True)),
            requires_blockers=bool(expectation.get("requires_blockers", True)),
            requires_proof_obligations=bool(expectation.get("requires_proof_obligations", True)),
        )

    typed_observations: list[SharedRoundObservation] = []
    for entry in observations or ():
        if isinstance(entry, SharedRoundObservation):
            typed_observations.append(entry)
        elif isinstance(entry, Mapping):
            typed_observations.append(SharedRoundObservation.from_mapping(entry))
        else:
            warnings.append(f"skipped non-mapping observation: {type(entry).__name__}")

    failures: list[SharedRoundViolation] = []
    for observation in typed_observations:
        failures.extend(
            evaluate_observation(
                observation=observation,
                expectation=expectation,
                now=now_utc,
                freshness_window_seconds=freshness_window_seconds,
            )
        )

    rule_counts: dict[str, int] = {}
    for violation in failures:
        rule_counts[violation.rule_id] = rule_counts.get(violation.rule_id, 0) + 1

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not failures,
        "display_text": DISPLAY_TEXT if failures else "",
        "current_plan_row_id": expectation.row_id,
        "expected_source_hash": expectation.source_hash,
        "freshness_window_seconds": freshness_window_seconds,
        "observation_count": len(typed_observations),
        "failure_count": len(failures),
        "rule_counts": rule_counts,
        "checked_surfaces": checked_surfaces,
        "failures": [violation.to_dict() for violation in failures],
        "warnings": warnings,
    }


def _as_str_tuple(value: object) -> Iterable[str]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        text = value.decode() if isinstance(value, bytes) else value
        text = text.strip()
        return (text,) if text else ()
    if isinstance(value, Sequence):
        out: list[str] = []
        for entry in value:
            text = str(entry or "").strip()
            if text:
                out.append(text)
        return tuple(out)
    return ()


def _load_state(
    path: Path, warnings: list[str]
) -> tuple[tuple[Mapping[str, object], ...], SharedRoundExpectation | None]:
    if not path.exists():
        warnings.append(f"shared-round state missing: {path}")
        return ((), None)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"shared-round state load failed: {exc}")
        return ((), None)
    if not isinstance(payload, Mapping):
        return ((), None)
    observations_raw = payload.get("observations")
    observations: tuple[Mapping[str, object], ...] = ()
    if isinstance(observations_raw, list):
        observations = tuple(
            entry for entry in observations_raw if isinstance(entry, Mapping)
        )
    expectation_raw = payload.get("expectation")
    expectation: SharedRoundExpectation | None = None
    if isinstance(expectation_raw, Mapping):
        expectation = SharedRoundExpectation(
            row_id=str(expectation_raw.get("row_id") or "").strip(),
            source_hash=str(expectation_raw.get("source_hash") or "").strip(),
            requires_peer_occupancies=bool(
                expectation_raw.get("requires_peer_occupancies", True)
            ),
            requires_peer_write_leases=bool(
                expectation_raw.get("requires_peer_write_leases", True)
            ),
            requires_active_packets=bool(
                expectation_raw.get("requires_active_packets", True)
            ),
            requires_blockers=bool(expectation_raw.get("requires_blockers", True)),
            requires_proof_obligations=bool(
                expectation_raw.get("requires_proof_obligations", True)
            ),
        )
    return (observations, expectation)


def _default_state_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/shared_round/latest.json"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- current_plan_row_id: `{report.get('current_plan_row_id')}`")
    lines.append(f"- observation_count: {report.get('observation_count')}")
    lines.append(f"- failure_count: {report.get('failure_count')}")
    lines.append(
        f"- freshness_window_seconds: {report.get('freshness_window_seconds')}"
    )
    failures = report.get("failures")
    if isinstance(failures, Sequence) and not isinstance(failures, (str, bytes)) and failures:
        lines.extend(("", "## Failures", ""))
        for violation in failures:
            if not isinstance(violation, Mapping):
                continue
            actor = violation.get("actor_id") or "?"
            lines.append(
                f"- {violation.get('rule_id')} (actor={actor}): "
                f"{violation.get('detail')}"
            )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-path",
        type=Path,
        default=_default_state_path(),
    )
    parser.add_argument("--row-id", default=DEFAULT_ROW_ID)
    parser.add_argument(
        "--freshness-window-seconds",
        type=int,
        default=DEFAULT_FRESHNESS_WINDOW_SECONDS,
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            state_path=args.state_path,
            current_row_id=args.row_id,
            freshness_window_seconds=args.freshness_window_seconds,
        )
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
