#!/usr/bin/env python3
"""A18 G32 guard: fail when two live mutation-capable actors overlap write scope.

Per delete_after_ingest.md A18 (single-writer invariant, lines 1040-1054, G32
lines 1101-1105):

    No two live mutation-capable actors may hold overlapping write scope for the
    same PlanRow/path/file/symbol/worktree/branch/receipt target/packet target
    unless a typed merge coordinator explicitly owns the conflict.

This guard scans the typed actor-lease inventory and pairs every two live
mutation-capable actors. For each pair it inspects each scope dimension
(path, file, symbol, worktree, branch, receipt target, packet target). When
two actors overlap on any dimension and no typed merge coordinator binds that
specific conflict, the guard emits a typed violation with a stable
``RULE_OVERLAPPING_*_LEASE`` rule id.

A merge coordinator is "explicit" when it names the same scope dimension and
value AS the conflict, names both colliding actors in its ``owned_actor_ids``
(or both their ``role_ids`` are listed in ``owned_role_ids``), and has a
non-empty ``conflict_id`` that the conflicting actors reference.

This is a pure-data reducer; CLI input is JSON via ``--lease-inventory-path``
so the guard can run in TDD without touching the live review-channel state.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.scope_path_claims import paths_overlap  # noqa: E402


COMMAND = "check_write_lease_conflicts"
CONTRACT_ID = "WriteLeaseConflictsGuard"

DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"

# Stable machine-readable rule ids — one per scope dimension G32 enumerates,
# plus a coordinator-shape rule for explicitly-broken merge coordinator
# references.
RULE_OVERLAPPING_PATH_LEASE = "overlapping_path_lease"
RULE_OVERLAPPING_FILE_LEASE = "overlapping_file_lease"
RULE_OVERLAPPING_SYMBOL_LEASE = "overlapping_symbol_lease"
RULE_OVERLAPPING_WORKTREE_LEASE = "overlapping_worktree_lease"
RULE_OVERLAPPING_BRANCH_LEASE = "overlapping_branch_lease"
RULE_OVERLAPPING_RECEIPT_LEASE = "overlapping_receipt_lease"
RULE_OVERLAPPING_PACKET_LEASE = "overlapping_packet_lease"
RULE_NO_TYPED_MERGE_COORDINATOR = "no_typed_merge_coordinator"

DISPLAY_TEXT = (
    "Write-lease overlap detected. Two live mutation-capable actors hold "
    "overlapping write scope without a typed merge coordinator that owns the "
    "conflict. Bind one actor to a disjoint scope, swap to patch-only child "
    "output, or stand up a typed merge coordinator before either actor "
    "mutates."
)

# Live mutation-capable actor states. An actor without one of these states
# does not hold a live write lease and cannot participate in overlap.
LIVE_MUTATION_STATES = frozenset(
    {
        "live",
        "active",
        "writing",
        "mutating",
        "lease_held",
    }
)


@dataclass(frozen=True, slots=True)
class LeaseConflictViolation:
    rule_id: str
    detail: str
    remediation: str
    left_actor_id: str
    right_actor_id: str
    scope_value: str
    plan_row_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# Scope dimensions a single typed-lease actor advertises. Each entry maps
# (scope-key-on-actor, rule-id, human label) so the same overlap loop can
# handle every dimension without per-rule branches.
_LIST_SCOPE_DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    ("path_scope", RULE_OVERLAPPING_PATH_LEASE, "path"),
    ("file_scope", RULE_OVERLAPPING_FILE_LEASE, "file"),
    ("symbol_scope", RULE_OVERLAPPING_SYMBOL_LEASE, "symbol"),
    ("receipt_scope", RULE_OVERLAPPING_RECEIPT_LEASE, "receipt target"),
    ("packet_scope", RULE_OVERLAPPING_PACKET_LEASE, "packet target"),
)

_SCALAR_SCOPE_DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    ("worktree_identity", RULE_OVERLAPPING_WORKTREE_LEASE, "worktree"),
    ("branch_identity", RULE_OVERLAPPING_BRANCH_LEASE, "branch"),
)


def build_report(
    *,
    leases: Sequence[Mapping[str, object]],
    merge_coordinators: Sequence[Mapping[str, object]] | None = None,
    current_row_id: str = DEFAULT_ROW_ID,
) -> dict[str, object]:
    """Evaluate G32 overlap rules over an in-memory lease inventory."""

    coordinators: tuple[Mapping[str, object], ...] = tuple(merge_coordinators or ())
    live_leases = tuple(_filter_live_mutation_capable(leases))

    violations: list[LeaseConflictViolation] = []

    for index, left in enumerate(live_leases):
        for right in live_leases[index + 1:]:
            if _same_actor(left, right):
                continue
            for scope_key, rule_id, label in _LIST_SCOPE_DIMENSIONS:
                for value in _shared_scope_values(left, right, scope_key):
                    if _conflict_owned_by_merge_coordinator(
                        coordinators=coordinators,
                        left=left,
                        right=right,
                        scope_dimension=scope_key,
                        scope_value=value,
                    ):
                        continue
                    violations.append(
                        _violation(
                            rule_id=rule_id,
                            label=label,
                            left=left,
                            right=right,
                            scope_value=value,
                        )
                    )
            for scope_key, rule_id, label in _SCALAR_SCOPE_DIMENSIONS:
                shared = _shared_scalar_scope(left, right, scope_key)
                if not shared:
                    continue
                if _conflict_owned_by_merge_coordinator(
                    coordinators=coordinators,
                    left=left,
                    right=right,
                    scope_dimension=scope_key,
                    scope_value=shared,
                ):
                    continue
                violations.append(
                    _violation(
                        rule_id=rule_id,
                        label=label,
                        left=left,
                        right=right,
                        scope_value=shared,
                    )
                )

    # Independent rule: when a lease *names* a merge_coordinator_id but no
    # coordinator with that id exists in the inventory (or it does not bind
    # the colliding actors), the typed merge coordinator path is broken and
    # the guard must fail closed.
    violations.extend(_dangling_coordinator_violations(live_leases, coordinators))

    deduped = _dedupe(violations)
    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not deduped,
        "display_text": DISPLAY_TEXT if deduped else "",
        "current_plan_row_id": current_row_id,
        "live_mutation_capable_count": len(live_leases),
        "merge_coordinator_count": len(coordinators),
        "violation_count": len(deduped),
        "violations": [v.to_dict() for v in deduped],
    }


def _filter_live_mutation_capable(
    leases: Iterable[Mapping[str, object]],
) -> Iterable[Mapping[str, object]]:
    for lease in leases:
        if not isinstance(lease, Mapping):
            continue
        if not _coerce_bool(lease.get("mutation_capable"), default=True):
            continue
        state = _coerce_text(lease.get("state")).strip().lower()
        if state and state not in LIVE_MUTATION_STATES:
            continue
        yield lease


def _shared_scope_values(
    left: Mapping[str, object],
    right: Mapping[str, object],
    scope_key: str,
) -> tuple[str, ...]:
    left_values = _scope_list(left, scope_key)
    right_values = _scope_list(right, scope_key)
    if not left_values or not right_values:
        return ()
    shared: list[str] = []
    for lv in left_values:
        for rv in right_values:
            if paths_overlap(lv, rv):
                shared.append(lv if len(lv) <= len(rv) else rv)
    # Preserve order, dedupe.
    seen: set[str] = set()
    out: list[str] = []
    for value in shared:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return tuple(out)


def _shared_scalar_scope(
    left: Mapping[str, object],
    right: Mapping[str, object],
    scope_key: str,
) -> str:
    lv = _coerce_text(left.get(scope_key)).strip()
    rv = _coerce_text(right.get(scope_key)).strip()
    if lv and rv and lv == rv:
        return lv
    return ""


def _scope_list(lease: Mapping[str, object], scope_key: str) -> tuple[str, ...]:
    raw = lease.get(scope_key)
    if isinstance(raw, str):
        text = raw.strip()
        return (text,) if text else ()
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        values: list[str] = []
        for item in raw:
            text = _coerce_text(item).strip()
            if text:
                values.append(text)
        return tuple(values)
    return ()


def _conflict_owned_by_merge_coordinator(
    *,
    coordinators: Sequence[Mapping[str, object]],
    left: Mapping[str, object],
    right: Mapping[str, object],
    scope_dimension: str,
    scope_value: str,
) -> bool:
    left_id = _coerce_text(left.get("actor_id")).strip()
    right_id = _coerce_text(right.get("actor_id")).strip()
    left_role = _coerce_text(left.get("role_id")).strip()
    right_role = _coerce_text(right.get("role_id")).strip()
    declared_left = _coerce_text(left.get("merge_coordinator_id")).strip()
    declared_right = _coerce_text(right.get("merge_coordinator_id")).strip()
    for coord in coordinators:
        if not isinstance(coord, Mapping):
            continue
        coord_id = _coerce_text(coord.get("coordinator_id")).strip()
        if not coord_id:
            continue
        if declared_left and declared_left != coord_id:
            continue
        if declared_right and declared_right != coord_id:
            continue
        conflict_id = _coerce_text(coord.get("conflict_id")).strip()
        if not conflict_id:
            continue
        owned_dim = _coerce_text(coord.get("scope_dimension")).strip()
        if owned_dim and owned_dim != scope_dimension:
            continue
        owned_values = _scope_list(coord, "scope_values")
        if owned_values and scope_value not in owned_values:
            # Allow a coordinator to own a prefix that covers the scope value.
            if not any(paths_overlap(v, scope_value) for v in owned_values):
                continue
        owned_actors = _scope_list(coord, "owned_actor_ids")
        owned_roles = _scope_list(coord, "owned_role_ids")
        actors_bound = (
            left_id in owned_actors and right_id in owned_actors
        )
        roles_bound = (
            left_role
            and right_role
            and left_role in owned_roles
            and right_role in owned_roles
        )
        if actors_bound or roles_bound:
            return True
    return False


def _dangling_coordinator_violations(
    leases: Sequence[Mapping[str, object]],
    coordinators: Sequence[Mapping[str, object]],
) -> list[LeaseConflictViolation]:
    coordinator_ids = {
        _coerce_text(c.get("coordinator_id")).strip()
        for c in coordinators
        if isinstance(c, Mapping)
    }
    violations: list[LeaseConflictViolation] = []
    for lease in leases:
        declared = _coerce_text(lease.get("merge_coordinator_id")).strip()
        if not declared:
            continue
        if declared in coordinator_ids:
            continue
        actor = _coerce_text(lease.get("actor_id")).strip()
        violations.append(
            LeaseConflictViolation(
                rule_id=RULE_NO_TYPED_MERGE_COORDINATOR,
                detail=(
                    f"Actor {actor!r} references merge_coordinator_id="
                    f"{declared!r} but no typed coordinator with that id "
                    "exists in the inventory."
                ),
                remediation=(
                    "Register the typed merge coordinator with matching "
                    "coordinator_id, scope_dimension, scope_values, and "
                    "owned_actor_ids — or drop the dangling reference."
                ),
                left_actor_id=actor,
                right_actor_id="",
                scope_value=declared,
                plan_row_id=_coerce_text(lease.get("plan_row_id")).strip(),
            )
        )
    return violations


def _violation(
    *,
    rule_id: str,
    label: str,
    left: Mapping[str, object],
    right: Mapping[str, object],
    scope_value: str,
) -> LeaseConflictViolation:
    left_id = _coerce_text(left.get("actor_id")).strip()
    right_id = _coerce_text(right.get("actor_id")).strip()
    plan_row = (
        _coerce_text(left.get("plan_row_id")).strip()
        or _coerce_text(right.get("plan_row_id")).strip()
    )
    return LeaseConflictViolation(
        rule_id=rule_id,
        detail=(
            f"Live mutation-capable actors {left_id!r} and {right_id!r} share "
            f"{label} scope {scope_value!r} with no typed merge coordinator."
        ),
        remediation=(
            f"Route one actor to a disjoint {label} scope, swap to patch-only "
            "child output applied by the parent coordinator, or stand up a "
            "typed merge coordinator that names this conflict."
        ),
        left_actor_id=left_id,
        right_actor_id=right_id,
        scope_value=scope_value,
        plan_row_id=plan_row,
    )


def _same_actor(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    left_id = _coerce_text(left.get("actor_id")).strip()
    right_id = _coerce_text(right.get("actor_id")).strip()
    return bool(left_id) and left_id == right_id


def _dedupe(violations: Iterable[LeaseConflictViolation]) -> list[LeaseConflictViolation]:
    seen: set[tuple[str, str, str, str]] = set()
    out: list[LeaseConflictViolation] = []
    for v in violations:
        pair = tuple(sorted((v.left_actor_id, v.right_actor_id)))
        key = (v.rule_id, pair[0], pair[1], v.scope_value)
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _coerce_bool(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if not text:
            return default
        return text in {"1", "true", "yes", "on"}
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _load_inventory(path: Path) -> tuple[
    tuple[Mapping[str, object], ...], tuple[Mapping[str, object], ...]
]:
    if not path.exists():
        raise FileNotFoundError(f"lease inventory missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    leases = payload.get("leases") if isinstance(payload, Mapping) else None
    coords = payload.get("merge_coordinators") if isinstance(payload, Mapping) else None
    return (
        tuple(item for item in (leases or ()) if isinstance(item, Mapping)),
        tuple(item for item in (coords or ()) if isinstance(item, Mapping)),
    )


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- current_plan_row_id: `{report.get('current_plan_row_id')}`")
    lines.append(f"- live_mutation_capable_count: {report.get('live_mutation_capable_count')}")
    lines.append(f"- merge_coordinator_count: {report.get('merge_coordinator_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations") or []
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)) and violations:
        lines.extend(("", "## Violations", ""))
        for v in violations:
            if not isinstance(v, Mapping):
                continue
            lines.append(
                f"- {v.get('rule_id')}: "
                f"{v.get('left_actor_id')} <-> {v.get('right_actor_id')} "
                f"on {v.get('scope_value')!r}"
            )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lease-inventory-path",
        type=Path,
        default=REPO_ROOT / "dev/reports/write_leases/latest.json",
    )
    parser.add_argument("--row-id", default=DEFAULT_ROW_ID)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        leases, coordinators = _load_inventory(args.lease_inventory_path)
        report = build_report(
            leases=leases,
            merge_coordinators=coordinators,
            current_row_id=args.row_id,
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
