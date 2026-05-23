#!/usr/bin/env python3
"""Fail when live role occupancy violates A18 role-cardinality bounds.

A18 (delete_after_ingest.md lines 904-916) makes the cached-hammock
N-agents x M-roles rule executable: each ``role_id`` has typed
``min_actors``, ``desired_actors``, ``max_actors`` bounds plus a
``fallback_policy`` (``block``, ``degrade``, ``queue``, or
``operator_decision``). This guard fails when live actors for a
``role_id`` violate those bounds or when an overflow exists without a
typed merge owner, preventing silent drift such as "one implementer
expected, three implementers active, and no typed merge owner."
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        coerce_string as _coerce_string,
        emit_runtime_error,
        report_to_dict as _report_to_dict,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        coerce_string as _coerce_string,
        emit_runtime_error,
        report_to_dict as _report_to_dict,
        utc_timestamp,
    )


COMMAND = "check_role_cardinality_bounds"
CONTRACT_ID = "RoleCardinalityBoundsGuard"

RULE_BELOW_MIN_ACTORS = "live_actors_below_min_actors"
RULE_ABOVE_MAX_ACTORS = "live_actors_above_max_actors"
RULE_MISSING_FALLBACK_POLICY = "role_assignment_missing_fallback_policy"
RULE_NO_MERGE_OWNER_FOR_OVERFLOW = "overflow_actors_without_typed_merge_owner"

VALID_FALLBACK_POLICIES = frozenset(
    {"block", "degrade", "queue", "operator_decision"}
)

DISPLAY_TEXT = (
    "Role cardinality bounds violation. A role_id assignment has live "
    "actors outside [min_actors, max_actors], lacks a typed fallback "
    "policy, or carries overflow occupancy with no typed merge owner. "
    "Silent fanout drift (one expected, three active, no merge gate) "
    "will not be tolerated."
)

DEFAULT_ROLE_STATE_PATH = (
    REPO_ROOT / "dev/reports/review_channel/state/role_cardinality.json"
)


@dataclass(frozen=True, slots=True)
class RoleCardinalityViolation:
    rule_id: str
    role_id: str
    detail: str
    remediation: str
    live_actor_count: int = 0
    min_actors: int = 0
    desired_actors: int = 0
    max_actors: int = 0
    fallback_policy: str = ""
    evidence_actor_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_actor_ids"] = list(self.evidence_actor_ids)
        return payload


@dataclass(frozen=True, slots=True)
class RoleCardinalityReport:
    ok: bool
    evaluated_role_count: int
    violation_count: int
    checked_surfaces: tuple[str, ...]
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    command: str = COMMAND
    timestamp: str = ""
    schema_version: int = 1
    contract_id: str = CONTRACT_ID
    display_text: str = ""

    def to_dict(self) -> dict[str, object]:
        return _report_to_dict(self)


def build_report(
    *,
    role_assignments: Sequence[Mapping[str, object]] | None = None,
    role_occupancies: Sequence[Mapping[str, object]] | None = None,
    role_state_path: Path | None = None,
) -> dict[str, object]:
    """Build the role-cardinality bounds report.

    Inputs may be supplied directly via ``role_assignments`` and
    ``role_occupancies``, or loaded from ``role_state_path`` (default
    ``dev/reports/review_channel/state/role_cardinality.json``).
    """
    warnings: list[str] = []
    checked_surfaces: list[str] = []
    if role_assignments is None or role_occupancies is None:
        source_path = role_state_path or DEFAULT_ROLE_STATE_PATH
        checked_surfaces.append(str(source_path))
        loaded_assignments, loaded_occupancies = _load_role_state(
            source_path, warnings
        )
        if role_assignments is None:
            role_assignments = loaded_assignments
        if role_occupancies is None:
            role_occupancies = loaded_occupancies

    assignments_by_role = _index_assignments(role_assignments)
    occupancies_by_role = _index_occupancies(role_occupancies)
    role_ids = sorted(set(assignments_by_role) | set(occupancies_by_role))

    violations: list[RoleCardinalityViolation] = []
    for role_id in role_ids:
        assignment = assignments_by_role.get(role_id, {})
        occupancies = occupancies_by_role.get(role_id, ())
        violations.extend(
            _violations_for_role(
                role_id=role_id,
                assignment=assignment,
                occupancies=occupancies,
            )
        )

    ok = not violations
    report = RoleCardinalityReport(
        ok=ok,
        evaluated_role_count=len(role_ids),
        violation_count=len(violations),
        checked_surfaces=tuple(checked_surfaces),
        violations=tuple(v.to_dict() for v in violations),
        warnings=tuple(warnings),
        timestamp=utc_timestamp(),
        display_text="" if ok else DISPLAY_TEXT,
    )
    return report.to_dict()


def _violations_for_role(
    *,
    role_id: str,
    assignment: Mapping[str, object],
    occupancies: Sequence[Mapping[str, object]],
) -> list[RoleCardinalityViolation]:
    violations: list[RoleCardinalityViolation] = []
    live_occupancies = tuple(_filter_live(occupancies))
    live_count = len(live_occupancies)
    evidence_ids = _actor_ids(live_occupancies)
    fallback_policy = _coerce_string(assignment.get("fallback_policy"))
    min_actors = _coerce_int(assignment.get("min_actors"))
    desired_actors = _coerce_int(assignment.get("desired_actors"))
    max_actors_raw = assignment.get("max_actors")
    max_actors = _coerce_int(max_actors_raw)
    has_max_bound = max_actors_raw is not None and max_actors > 0

    if assignment and fallback_policy not in VALID_FALLBACK_POLICIES:
        violations.append(
            RoleCardinalityViolation(
                rule_id=RULE_MISSING_FALLBACK_POLICY,
                role_id=role_id,
                detail=(
                    f"role_id={role_id!r} assignment fallback_policy="
                    f"{fallback_policy!r} is not one of "
                    f"{sorted(VALID_FALLBACK_POLICIES)}."
                ),
                remediation=(
                    "Set fallback_policy to one of block, degrade, queue, "
                    "or operator_decision in the typed role assignment."
                ),
                live_actor_count=live_count,
                min_actors=min_actors,
                desired_actors=desired_actors,
                max_actors=max_actors,
                fallback_policy=fallback_policy,
            )
        )

    if min_actors > 0 and live_count < min_actors:
        violations.append(
            RoleCardinalityViolation(
                rule_id=RULE_BELOW_MIN_ACTORS,
                role_id=role_id,
                detail=(
                    f"role_id={role_id!r} has live_actor_count={live_count} "
                    f"< min_actors={min_actors}."
                ),
                remediation=(
                    "Recruit additional actors for this role or apply the "
                    "typed fallback policy (block/degrade/queue/"
                    "operator_decision)."
                ),
                live_actor_count=live_count,
                min_actors=min_actors,
                desired_actors=desired_actors,
                max_actors=max_actors,
                fallback_policy=fallback_policy,
                evidence_actor_ids=evidence_ids,
            )
        )

    if has_max_bound and live_count > max_actors:
        violations.append(
            RoleCardinalityViolation(
                rule_id=RULE_ABOVE_MAX_ACTORS,
                role_id=role_id,
                detail=(
                    f"role_id={role_id!r} has live_actor_count={live_count} "
                    f"> max_actors={max_actors}."
                ),
                remediation=(
                    "Retire surplus actors or raise max_actors with a typed "
                    "assignment update; do not let unbounded fanout drift."
                ),
                live_actor_count=live_count,
                min_actors=min_actors,
                desired_actors=desired_actors,
                max_actors=max_actors,
                fallback_policy=fallback_policy,
                evidence_actor_ids=evidence_ids,
            )
        )
        if not _has_merge_owner(assignment, live_occupancies):
            violations.append(
                RoleCardinalityViolation(
                    rule_id=RULE_NO_MERGE_OWNER_FOR_OVERFLOW,
                    role_id=role_id,
                    detail=(
                        f"role_id={role_id!r} has live_actor_count="
                        f"{live_count} > max_actors={max_actors} but no "
                        "typed merge owner is declared. Silent fanout (e.g. "
                        "one implementer expected, three active) without a "
                        "typed merge coordinator is forbidden."
                    ),
                    remediation=(
                        "Declare a typed merge_owner_role_id / "
                        "merge_owner_actor_id on the assignment or on one "
                        "of the live occupancies before allowing overflow."
                    ),
                    live_actor_count=live_count,
                    min_actors=min_actors,
                    desired_actors=desired_actors,
                    max_actors=max_actors,
                    fallback_policy=fallback_policy,
                    evidence_actor_ids=evidence_ids,
                )
            )

    return violations


def _filter_live(
    occupancies: Iterable[Mapping[str, object]],
) -> Iterable[Mapping[str, object]]:
    for occupancy in occupancies:
        if not isinstance(occupancy, Mapping):
            continue
        live_value = occupancy.get("live")
        if live_value is False:
            continue
        if isinstance(live_value, str) and live_value.strip().lower() in {
            "false",
            "0",
            "no",
        }:
            continue
        yield occupancy


def _has_merge_owner(
    assignment: Mapping[str, object],
    occupancies: Sequence[Mapping[str, object]],
) -> bool:
    for key in (
        "merge_owner_role_id",
        "merge_owner_actor_id",
        "merge_coordinator_role_id",
        "merge_coordinator_actor_id",
    ):
        if _coerce_string(assignment.get(key)):
            return True
    for occupancy in occupancies:
        for key in (
            "merge_owner_role_id",
            "merge_owner_actor_id",
            "merge_coordinator_role_id",
            "merge_coordinator_actor_id",
            "is_merge_owner",
        ):
            value = occupancy.get(key)
            if isinstance(value, bool):
                if value:
                    return True
                continue
            if _coerce_string(value):
                return True
    return False


def _index_assignments(
    assignments: Sequence[Mapping[str, object]] | None,
) -> dict[str, Mapping[str, object]]:
    if not assignments:
        return {}
    indexed: dict[str, Mapping[str, object]] = {}
    for entry in assignments:
        if not isinstance(entry, Mapping):
            continue
        role_id = _coerce_string(entry.get("role_id"))
        if not role_id:
            continue
        indexed[role_id] = entry
    return indexed


def _index_occupancies(
    occupancies: Sequence[Mapping[str, object]] | None,
) -> dict[str, tuple[Mapping[str, object], ...]]:
    if not occupancies:
        return {}
    indexed: dict[str, list[Mapping[str, object]]] = {}
    for entry in occupancies:
        if not isinstance(entry, Mapping):
            continue
        role_id = _coerce_string(entry.get("role_id"))
        if not role_id:
            continue
        indexed.setdefault(role_id, []).append(entry)
    return {role_id: tuple(items) for role_id, items in indexed.items()}


def _load_role_state(
    path: Path, warnings: list[str]
) -> tuple[tuple[Mapping[str, object], ...], tuple[Mapping[str, object], ...]]:
    if not path.exists():
        warnings.append(f"role state missing: {path}")
        return ((), ())
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"role state load failed: {exc}")
        return ((), ())
    if not isinstance(payload, Mapping):
        warnings.append(f"role state payload not a JSON object: {path}")
        return ((), ())
    assignments = payload.get("role_assignments")
    occupancies = payload.get("role_occupancies")
    return (
        _filter_mapping_sequence(assignments),
        _filter_mapping_sequence(occupancies),
    )


def _filter_mapping_sequence(
    value: object,
) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _actor_ids(
    occupancies: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    return tuple(
        _coerce_string(item.get("actor_id"))
        for item in occupancies
        if _coerce_string(item.get("actor_id"))
    )


def _coerce_int(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        try:
            return int(text)
        except ValueError:
            return 0
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- evaluated_role_count: {report.get('evaluated_role_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations")
    if (
        isinstance(violations, Sequence)
        and not isinstance(violations, (str, bytes))
        and violations
    ):
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('role_id')}: {violation.get('rule_id')} "
                f"({violation.get('detail')})"
            )
    warnings = report.get("warnings")
    if (
        isinstance(warnings, Sequence)
        and not isinstance(warnings, (str, bytes))
        and warnings
    ):
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--role-state-path",
        type=Path,
        default=DEFAULT_ROLE_STATE_PATH,
        help=(
            "JSON file containing role_assignments + role_occupancies "
            "arrays (typed role-cardinality state)."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
    )
    args = parser.parse_args(argv)
    try:
        report = build_report(role_state_path=args.role_state_path)
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
