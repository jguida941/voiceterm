#!/usr/bin/env python3
"""Fail when a role actor spawns child actors without typed delegation authority.

Per A18/G30 of the GuardIR governance plan, a role actor that spawns child
actors must carry typed `RoleDelegationGrant` fields linking the parent
occupancy, an allowed child role, a PlanRow, authority refs, and an
unexpired window. This guard inspects delegation-grant rows and live actor
state and emits a typed report enumerating each violating spawn.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _shared_iter_jsonl,
        parse_utc as _parse_utc,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _shared_iter_jsonl,
        parse_utc as _parse_utc,
        utc_timestamp,
    )


COMMAND = "check_role_delegation_authority"
CONTRACT_ID = "RoleDelegationAuthorityGuard"

RULE_MISSING_PARENT_ROLE_OCCUPANCY = "missing_parent_role_occupancy"
RULE_PARENT_NOT_LIVE = "parent_not_live"
RULE_MISSING_DELEGATION_CAPABILITY = "missing_delegation_capability"
RULE_CHILD_ROLE_NOT_ALLOWED = "child_role_not_allowed"
RULE_MISSING_AUTHORITY_REFS = "missing_authority_refs"
RULE_EXPIRED_DELEGATION = "expired_delegation"
RULE_MISSING_PLAN_ROW = "missing_plan_row"

DISPLAY_TEXT = (
    "Role delegation authority violation. A role actor spawned a child actor "
    "without typed RoleDelegationGrant authority. Parent occupancy, live "
    "parent actor, delegation capability, allowed child role_id, current or "
    "delegated PlanRow, authority_refs, and an unexpired window are required."
)

DEFAULT_DELEGATION_STATE_PATH = (
    REPO_ROOT / "dev/state/role_delegation_grants.jsonl"
)
DEFAULT_ACTOR_STATE_PATH = (
    REPO_ROOT / "dev/reports/review_channel/state/latest.json"
)

PARENT_LIVENESS_LIVE = "live"
PARENT_LIVENESS_RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class DelegationViolation:
    rule_id: str
    grant_id: str
    parent_role_occupancy_id: str
    child_actor_id: str
    child_role_id: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    grants: Sequence[Mapping[str, object]] | None = None,
    live_actors: Sequence[Mapping[str, object]] | None = None,
    delegation_state_path: Path | None = None,
    actor_state_path: Path | None = None,
    row_id_filter: str = "",
    now: datetime | None = None,
) -> dict[str, object]:
    """Build the typed delegation-authority report.

    Each grant describes an attempted parent->child delegation. The guard
    fails closed if any required field is missing, the parent is not live,
    delegation capability is absent, the child role is not in the allowed
    set, the PlanRow is missing, the grant has no `authority_refs`, or
    `expires_at_utc` lies at-or-before `now`.
    """

    warnings: list[str] = []
    checked_surfaces: list[str] = []
    if grants is None:
        delegation_path = delegation_state_path or DEFAULT_DELEGATION_STATE_PATH
        checked_surfaces.append(str(delegation_path))
        grants = tuple(_iter_jsonl(delegation_path, warnings=warnings))
    else:
        grants = tuple(grants)
    if live_actors is None:
        actor_path = actor_state_path or DEFAULT_ACTOR_STATE_PATH
        checked_surfaces.append(str(actor_path))
        live_actors = tuple(_actors_from_state(actor_path, warnings))
    else:
        live_actors = tuple(live_actors)

    now_utc = now or datetime.now(timezone.utc)
    live_index = _index_live_actors(live_actors)

    violations: list[DelegationViolation] = []
    checked_grant_ids: list[str] = []
    for grant in grants:
        grant_id = str(grant.get("grant_id") or grant.get("delegation_id") or "")
        if row_id_filter and not _grant_matches_row(grant, row_id_filter):
            continue
        checked_grant_ids.append(grant_id)
        violations.extend(_violations_for_grant(grant, live_index, now_utc))

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "row_id_filter": row_id_filter,
        "checked_grant_count": len(checked_grant_ids),
        "checked_grant_ids": checked_grant_ids,
        "live_actor_count": len(live_index),
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "checked_surfaces": checked_surfaces,
        "warnings": warnings,
    }


def _violations_for_grant(
    grant: Mapping[str, object],
    live_index: Mapping[str, Mapping[str, object]],
    now_utc: datetime,
) -> tuple[DelegationViolation, ...]:
    violations: list[DelegationViolation] = []
    grant_id = str(grant.get("grant_id") or grant.get("delegation_id") or "")
    parent_id = str(grant.get("parent_role_occupancy_id") or "").strip()
    child_actor = str(grant.get("child_actor_id") or "").strip()
    child_role = str(grant.get("role_id") or grant.get("child_role_id") or "").strip()

    if not parent_id:
        violations.append(
            DelegationViolation(
                rule_id=RULE_MISSING_PARENT_ROLE_OCCUPANCY,
                grant_id=grant_id,
                parent_role_occupancy_id="",
                child_actor_id=child_actor,
                child_role_id=child_role,
                detail=(
                    "RoleDelegationGrant is missing parent_role_occupancy_id; "
                    "cannot bind delegation to a typed parent role actor."
                ),
                remediation=(
                    "Populate parent_role_occupancy_id from the live "
                    "RoleOccupancyAssignment that owns this delegation."
                ),
            )
        )
        return tuple(violations)

    parent = live_index.get(parent_id)
    if parent is None or _liveness(parent) != PARENT_LIVENESS_LIVE:
        violations.append(
            DelegationViolation(
                rule_id=RULE_PARENT_NOT_LIVE,
                grant_id=grant_id,
                parent_role_occupancy_id=parent_id,
                child_actor_id=child_actor,
                child_role_id=child_role,
                detail=(
                    f"parent_role_occupancy_id={parent_id!r} is not live; "
                    "retired or unknown parents cannot grant delegation."
                ),
                remediation=(
                    "Restart the delegation under a live parent occupancy "
                    "or supersede this grant with a typed reassignment."
                ),
            )
        )
        return tuple(violations)

    if not _parent_can_delegate(parent, child_role):
        violations.append(
            DelegationViolation(
                rule_id=RULE_MISSING_DELEGATION_CAPABILITY,
                grant_id=grant_id,
                parent_role_occupancy_id=parent_id,
                child_actor_id=child_actor,
                child_role_id=child_role,
                detail=(
                    f"parent {parent_id!r} lacks delegation_capability=true "
                    "in its RoleOccupancyAssignment."
                ),
                remediation=(
                    "Grant delegation capability on the parent occupancy "
                    "via typed role-profile authority before spawning."
                ),
            )
        )

    if child_role and not _child_role_allowed(parent, child_role):
        violations.append(
            DelegationViolation(
                rule_id=RULE_CHILD_ROLE_NOT_ALLOWED,
                grant_id=grant_id,
                parent_role_occupancy_id=parent_id,
                child_actor_id=child_actor,
                child_role_id=child_role,
                detail=(
                    f"child role_id={child_role!r} is not in the parent's "
                    "allowed_child_role_ids set."
                ),
                remediation=(
                    "Restrict child role to a typed allowed_child_role_ids "
                    "entry or extend the parent's allowed set via policy."
                ),
            )
        )

    if not _has_plan_row(grant):
        violations.append(
            DelegationViolation(
                rule_id=RULE_MISSING_PLAN_ROW,
                grant_id=grant_id,
                parent_role_occupancy_id=parent_id,
                child_actor_id=child_actor,
                child_role_id=child_role,
                detail=(
                    "RoleDelegationGrant is missing a current or delegated "
                    "PlanRow (target_plan_row_id/plan_row_id)."
                ),
                remediation=(
                    "Bind delegation to a typed PlanRow before child actor "
                    "begins work."
                ),
            )
        )

    if not _has_authority_refs(grant):
        violations.append(
            DelegationViolation(
                rule_id=RULE_MISSING_AUTHORITY_REFS,
                grant_id=grant_id,
                parent_role_occupancy_id=parent_id,
                child_actor_id=child_actor,
                child_role_id=child_role,
                detail=(
                    "RoleDelegationGrant has empty authority_refs; "
                    "no typed authority chain anchors this delegation."
                ),
                remediation=(
                    "Populate authority_refs with typed contract/receipt "
                    "anchors (e.g. RoleOccupancyAssignment, dispatch packet)."
                ),
            )
        )

    expiry = _parse_utc(str(grant.get("expires_at_utc") or ""))
    if expiry is None:
        violations.append(
            DelegationViolation(
                rule_id=RULE_EXPIRED_DELEGATION,
                grant_id=grant_id,
                parent_role_occupancy_id=parent_id,
                child_actor_id=child_actor,
                child_role_id=child_role,
                detail=(
                    "RoleDelegationGrant is missing expires_at_utc; "
                    "delegation must carry an explicit window."
                ),
                remediation=(
                    "Set expires_at_utc on the grant (typed RoleDelegation "
                    "TTL) before the child actor spawns."
                ),
            )
        )
    elif expiry <= now_utc:
        violations.append(
            DelegationViolation(
                rule_id=RULE_EXPIRED_DELEGATION,
                grant_id=grant_id,
                parent_role_occupancy_id=parent_id,
                child_actor_id=child_actor,
                child_role_id=child_role,
                detail=(
                    f"RoleDelegationGrant expired at {expiry.isoformat()}; "
                    f"now={now_utc.isoformat()}."
                ),
                remediation=(
                    "Refresh the delegation under typed governance, or "
                    "supersede with a new RoleDelegationGrant."
                ),
            )
        )

    return tuple(violations)


def _index_live_actors(
    actors: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    index: dict[str, Mapping[str, object]] = {}
    for actor in actors:
        occupancy_id = str(
            actor.get("role_occupancy_id")
            or actor.get("occupancy_id")
            or actor.get("actor_id")
            or ""
        ).strip()
        if not occupancy_id:
            continue
        index.setdefault(occupancy_id, actor)
    return index


def _liveness(actor: Mapping[str, object]) -> str:
    raw = str(actor.get("liveness") or actor.get("status") or "").strip().lower()
    if raw in {"live", "active"}:
        return PARENT_LIVENESS_LIVE
    if raw:
        return raw
    return PARENT_LIVENESS_LIVE


def _parent_can_delegate(parent: Mapping[str, object], child_role: str) -> bool:
    capability = parent.get("delegation_capability")
    if isinstance(capability, bool):
        return capability
    if isinstance(capability, str):
        return capability.strip().lower() in {"true", "yes", "1"}
    allowed = parent.get("allowed_child_role_ids")
    if isinstance(allowed, Sequence) and not isinstance(allowed, (str, bytes)):
        return bool(tuple(allowed))
    return False


def _child_role_allowed(parent: Mapping[str, object], child_role: str) -> bool:
    allowed = parent.get("allowed_child_role_ids")
    if not isinstance(allowed, Sequence) or isinstance(allowed, (str, bytes)):
        return False
    normalized = {str(role).strip() for role in allowed if str(role).strip()}
    return child_role in normalized


def _has_plan_row(grant: Mapping[str, object]) -> bool:
    for field in ("target_plan_row_id", "plan_row_id", "target_ref"):
        value = str(grant.get(field) or "").strip()
        if value:
            return True
    return False


def _has_authority_refs(grant: Mapping[str, object]) -> bool:
    refs = grant.get("authority_refs")
    if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
        return any(str(ref).strip() for ref in refs)
    if isinstance(refs, str):
        return bool(refs.strip())
    return False


def _grant_matches_row(grant: Mapping[str, object], row_id_filter: str) -> bool:
    for field in ("target_plan_row_id", "plan_row_id", "target_ref"):
        value = str(grant.get(field) or "").strip()
        if value and row_id_filter in value:
            return True
    return False


def _iter_jsonl(
    path: Path, *, warnings: list[str]
) -> Iterable[Mapping[str, object]]:
    return _shared_iter_jsonl(
        path, warnings=warnings, missing_label="delegation state missing"
    )


def _actors_from_state(
    path: Path, warnings: list[str]
) -> tuple[Mapping[str, object], ...]:
    if not path.exists():
        warnings.append(f"actor state missing: {path}")
        return ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"actor state load failed: {exc}")
        return ()
    if not isinstance(payload, Mapping):
        return ()
    actors = payload.get("role_occupancies")
    if not isinstance(actors, list):
        actors = payload.get("actors") if isinstance(payload.get("actors"), list) else []
    return tuple(actor for actor in actors if isinstance(actor, Mapping))


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- checked_grant_count: {report.get('checked_grant_count')}")
    lines.append(f"- live_actor_count: {report.get('live_actor_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("row_id_filter"):
        lines.append(f"- row_id_filter: `{report.get('row_id_filter')}`")
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('grant_id')}: {violation.get('rule_id')} "
                f"(child={violation.get('child_actor_id')}, "
                f"role={violation.get('child_role_id')}): "
                f"{violation.get('detail')}"
            )
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delegation-state-path",
        type=Path,
        default=DEFAULT_DELEGATION_STATE_PATH,
        help="Typed RoleDelegationGrant ledger (JSONL).",
    )
    parser.add_argument(
        "--actor-state-path",
        type=Path,
        default=DEFAULT_ACTOR_STATE_PATH,
        help="Live RoleOccupancyAssignment state (JSON).",
    )
    parser.add_argument(
        "--row-id",
        default="",
        help="If set, only check grants whose PlanRow target contains this row id.",
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            delegation_state_path=args.delegation_state_path,
            actor_state_path=args.actor_state_path,
            row_id_filter=args.row_id,
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
