#!/usr/bin/env python3
"""Fail when a child actor acts outside delegated scope or attempts forbidden mutations.

Implements A18 G33: child implementation actors do not get commit or push
authority, do not close PlanRows, do not rewrite receipt stores or generated
surfaces unless the delegation explicitly grants that scope, do not stage,
and do not spawn grand-children without explicit authority. Child actors
submit patch/proof output to the parent role coordinator instead.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _iter_jsonl,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _iter_jsonl,
        utc_timestamp,
    )


COMMAND = "check_child_actor_scope"
CONTRACT_ID = "ChildActorScopeGuard"

RULE_ACTED_OUTSIDE_DELEGATED_SCOPE = "child_acted_outside_delegated_scope"
RULE_CHILD_ATTEMPTED_STAGE = "child_attempted_stage"
RULE_CHILD_ATTEMPTED_COMMIT = "child_attempted_commit"
RULE_CHILD_ATTEMPTED_PUSH = "child_attempted_push"
RULE_CHILD_ATTEMPTED_ROW_CLOSURE = "child_attempted_row_closure"
RULE_CHILD_ATTEMPTED_PLAN_ROW_MUTATION = "child_attempted_plan_row_mutation"
RULE_CHILD_ATTEMPTED_RECEIPT_STORE_MUTATION = (
    "child_attempted_receipt_store_mutation"
)
RULE_CHILD_ATTEMPTED_GENERATED_SURFACE_REWRITE = (
    "child_attempted_generated_surface_rewrite"
)
RULE_CHILD_ATTEMPTED_GRAND_CHILD_SPAWN_WITHOUT_AUTHORITY = (
    "child_attempted_grand_child_spawn_without_authority"
)

DISPLAY_TEXT = (
    "Child actor scope violation. Child actors must stay inside the delegated "
    "scope (paths, capabilities, target row) and submit patch/proof to the "
    "parent role coordinator. Stage/commit/push, PlanRow closure or mutation, "
    "receipt-store mutation, generated-surface rewrite, and grand-child spawn "
    "require explicit delegation authority."
)

# Event types this guard recognizes.
EVENT_CHILD_ACTION_ATTEMPTED = "child_action_attempted"

# Action kinds that the child may attempt and that this guard inspects.
ACTION_STAGE = "stage"
ACTION_COMMIT = "commit"
ACTION_PUSH = "push"
ACTION_ROW_CLOSURE = "row_closure"
ACTION_PLAN_ROW_MUTATION = "plan_row_mutation"
ACTION_RECEIPT_STORE_MUTATION = "receipt_store_mutation"
ACTION_GENERATED_SURFACE_REWRITE = "generated_surface_rewrite"
ACTION_SPAWN_CHILD = "spawn_child"
ACTION_EDIT = "edit"

# Map forbidden default child actions to their corresponding rule ids.
_FORBIDDEN_ACTION_RULES: Mapping[str, str] = {
    ACTION_STAGE: RULE_CHILD_ATTEMPTED_STAGE,
    ACTION_COMMIT: RULE_CHILD_ATTEMPTED_COMMIT,
    ACTION_PUSH: RULE_CHILD_ATTEMPTED_PUSH,
    ACTION_ROW_CLOSURE: RULE_CHILD_ATTEMPTED_ROW_CLOSURE,
    ACTION_PLAN_ROW_MUTATION: RULE_CHILD_ATTEMPTED_PLAN_ROW_MUTATION,
    ACTION_RECEIPT_STORE_MUTATION: RULE_CHILD_ATTEMPTED_RECEIPT_STORE_MUTATION,
    ACTION_GENERATED_SURFACE_REWRITE: (
        RULE_CHILD_ATTEMPTED_GENERATED_SURFACE_REWRITE
    ),
}

# Delegation scope keys that explicitly extend the child's allowed actions.
_SCOPE_OVERRIDE_KEYS: Mapping[str, str] = {
    ACTION_STAGE: "may_stage",
    ACTION_COMMIT: "may_commit",
    ACTION_PUSH: "may_push",
    ACTION_ROW_CLOSURE: "may_close_rows",
    ACTION_PLAN_ROW_MUTATION: "may_mutate_plan_rows",
    ACTION_RECEIPT_STORE_MUTATION: "may_mutate_receipt_stores",
    ACTION_GENERATED_SURFACE_REWRITE: "may_rewrite_generated_surfaces",
    ACTION_SPAWN_CHILD: "may_spawn_grand_children",
}


@dataclass(frozen=True, slots=True)
class ChildActorScopeViolation:
    rule_id: str
    actor_id: str
    role_id: str
    parent_role_occupancy_id: str
    delegation_id: str
    action_kind: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    events: Sequence[Mapping[str, object]] | None = None,
    event_log_path: Path | None = None,
    row_id_filter: str = "",
    actor_id_filter: Sequence[str] = (),
) -> dict[str, object]:
    warnings: list[str] = []
    source_path: Path | None = None
    if events is None:
        source_path = event_log_path or _default_event_log_path()
        events = tuple(_iter_jsonl(source_path, warnings=warnings))
    else:
        events = tuple(events)

    actor_filter = _normalized_str_tuple(actor_id_filter)
    violations: list[ChildActorScopeViolation] = []
    checked_event_count = 0
    checked_actor_ids: list[str] = []
    seen_actors: set[str] = set()

    for event in events:
        event_type = str(event.get("event_type") or "").strip()
        if event_type != EVENT_CHILD_ACTION_ATTEMPTED:
            continue
        if not _is_child_actor(event):
            continue
        actor_id = str(event.get("actor_id") or "").strip()
        if actor_filter and actor_id not in actor_filter:
            continue
        if row_id_filter and not _matches_row(event, row_id_filter):
            continue
        checked_event_count += 1
        if actor_id and actor_id not in seen_actors:
            seen_actors.add(actor_id)
            checked_actor_ids.append(actor_id)
        violations.extend(_violations_for_event(event))

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "event_log_path": str(source_path) if source_path is not None else "",
        "row_id_filter": row_id_filter,
        "actor_id_filter": list(actor_filter),
        "checked_event_count": checked_event_count,
        "checked_actor_ids": checked_actor_ids,
        "violation_count": len(violations),
        "violations": [v.to_dict() for v in violations],
        "warnings": warnings,
    }


def _violations_for_event(
    event: Mapping[str, object],
) -> tuple[ChildActorScopeViolation, ...]:
    action_kind = str(event.get("action_kind") or "").strip().lower()
    if not action_kind:
        return ()
    actor_id = str(event.get("actor_id") or "").strip()
    role_id = str(event.get("role_id") or "").strip()
    parent_role_occupancy_id = str(
        event.get("parent_role_occupancy_id") or ""
    ).strip()
    delegation = event.get("delegation")
    delegation_id = ""
    delegation_map: Mapping[str, object] = {}
    if isinstance(delegation, Mapping):
        delegation_map = delegation
        delegation_id = str(delegation.get("delegation_id") or "").strip()

    violations: list[ChildActorScopeViolation] = []

    # First, check explicit forbidden action kinds and grand-child spawn.
    if action_kind == ACTION_SPAWN_CHILD:
        if not _has_scope_override(
            delegation_map, ACTION_SPAWN_CHILD
        ):
            violations.append(
                ChildActorScopeViolation(
                    rule_id=(
                        RULE_CHILD_ATTEMPTED_GRAND_CHILD_SPAWN_WITHOUT_AUTHORITY
                    ),
                    actor_id=actor_id,
                    role_id=role_id,
                    parent_role_occupancy_id=parent_role_occupancy_id,
                    delegation_id=delegation_id,
                    action_kind=action_kind,
                    detail=(
                        f"child actor {actor_id!r} attempted to spawn a "
                        f"grand-child without delegation."
                        f"{_SCOPE_OVERRIDE_KEYS[ACTION_SPAWN_CHILD]}=true"
                    ),
                    remediation=(
                        "Routing fanout through the parent role coordinator "
                        "or extending the delegation with "
                        f"{_SCOPE_OVERRIDE_KEYS[ACTION_SPAWN_CHILD]}=true."
                    ),
                )
            )
    elif action_kind in _FORBIDDEN_ACTION_RULES:
        if not _has_scope_override(delegation_map, action_kind):
            violations.append(
                ChildActorScopeViolation(
                    rule_id=_FORBIDDEN_ACTION_RULES[action_kind],
                    actor_id=actor_id,
                    role_id=role_id,
                    parent_role_occupancy_id=parent_role_occupancy_id,
                    delegation_id=delegation_id,
                    action_kind=action_kind,
                    detail=(
                        f"child actor {actor_id!r} attempted "
                        f"{action_kind!r} without explicit delegation "
                        f"{_SCOPE_OVERRIDE_KEYS[action_kind]}=true"
                    ),
                    remediation=(
                        "Submit patch/proof to the parent role coordinator "
                        f"or extend delegation with "
                        f"{_SCOPE_OVERRIDE_KEYS[action_kind]}=true."
                    ),
                )
            )

    # Finally, verify the action remained inside delegated path/capability
    # scope. This applies to every action, including edit, so a child whose
    # delegation only allows path X cannot touch path Y even if the action is
    # otherwise allowed.
    out_of_scope_detail = _out_of_scope_detail(event, delegation_map)
    if out_of_scope_detail:
        violations.append(
            ChildActorScopeViolation(
                rule_id=RULE_ACTED_OUTSIDE_DELEGATED_SCOPE,
                actor_id=actor_id,
                role_id=role_id,
                parent_role_occupancy_id=parent_role_occupancy_id,
                delegation_id=delegation_id,
                action_kind=action_kind,
                detail=out_of_scope_detail,
                remediation=(
                    "Restrict the child actor to its delegated paths, "
                    "capabilities, and target row, or extend the delegation."
                ),
            )
        )

    return tuple(violations)


def _is_child_actor(event: Mapping[str, object]) -> bool:
    if str(event.get("parent_role_occupancy_id") or "").strip():
        return True
    actor_kind = str(event.get("actor_kind") or "").strip().lower()
    return actor_kind in {"child", "child_actor", "subagent", "sub_agent"}


def _has_scope_override(
    delegation: Mapping[str, object], action_kind: str
) -> bool:
    key = _SCOPE_OVERRIDE_KEYS.get(action_kind)
    if not key:
        return False
    raw = delegation.get(key)
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _out_of_scope_detail(
    event: Mapping[str, object], delegation: Mapping[str, object]
) -> str:
    if not delegation:
        # No delegation supplied: only forbidden-action rules apply; scope-
        # path checks are not enforceable here.
        return ""

    target_paths = _normalized_str_tuple(event.get("target_paths") or ())
    allowed_paths = _normalized_str_tuple(delegation.get("allowed_paths") or ())
    if allowed_paths and target_paths:
        out_of_scope = tuple(
            p for p in target_paths if not _path_in_scope(p, allowed_paths)
        )
        if out_of_scope:
            return (
                f"target_paths {list(out_of_scope)!r} fall outside "
                f"delegated allowed_paths {list(allowed_paths)!r}"
            )

    capability = str(event.get("capability") or "").strip()
    allowed_caps = _normalized_str_tuple(
        delegation.get("allowed_capabilities") or ()
    )
    if capability and allowed_caps and capability not in allowed_caps:
        return (
            f"capability {capability!r} is outside delegated "
            f"allowed_capabilities {list(allowed_caps)!r}"
        )

    target_ref = str(event.get("target_ref") or "").strip()
    delegated_row = str(delegation.get("plan_row_id") or "").strip()
    if delegated_row and target_ref and delegated_row not in target_ref:
        plan_id = str(event.get("plan_id") or "").strip()
        if plan_id and plan_id != delegated_row:
            return (
                f"event target plan/row ({target_ref!r}, plan_id={plan_id!r}) "
                f"does not match delegated plan_row_id {delegated_row!r}"
            )
    return ""


def _path_in_scope(path: str, allowed: Sequence[str]) -> bool:
    for prefix in allowed:
        if not prefix:
            continue
        if path == prefix:
            return True
        if prefix.endswith("/") and path.startswith(prefix):
            return True
        if path.startswith(prefix.rstrip("/") + "/"):
            return True
    return False


def _matches_row(event: Mapping[str, object], row_id_filter: str) -> bool:
    target_ref = str(event.get("target_ref") or "").strip()
    if target_ref and row_id_filter in target_ref:
        return True
    plan_id = str(event.get("plan_id") or "").strip()
    if plan_id and row_id_filter == plan_id:
        return True
    delegation = event.get("delegation")
    if isinstance(delegation, Mapping):
        delegated_row = str(delegation.get("plan_row_id") or "").strip()
        if delegated_row and row_id_filter == delegated_row:
            return True
    return False


def _normalized_str_tuple(values: Iterable[object]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return tuple(normalized)


def _default_event_log_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/events/trace.ndjson"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- checked_event_count: {report.get('checked_event_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("row_id_filter"):
        lines.append(f"- row_id_filter: `{report.get('row_id_filter')}`")
    actor_filter = report.get("actor_id_filter")
    if (
        isinstance(actor_filter, Sequence)
        and not isinstance(actor_filter, (str, bytes))
        and actor_filter
    ):
        rendered = ", ".join(f"`{actor}`" for actor in actor_filter)
        lines.append(f"- actor_id_filter: {rendered}")
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
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
                f"- {violation.get('rule_id')}: actor="
                f"{violation.get('actor_id')!r} action="
                f"{violation.get('action_kind')!r} "
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
        "--event-log-path",
        type=Path,
        default=_default_event_log_path(),
        help="Review-channel event log (NDJSON).",
    )
    parser.add_argument(
        "--row-id",
        default="",
        help=(
            "If set, only check child-actor events whose target_ref, "
            "plan_id, or delegated plan_row_id matches this row id."
        ),
    )
    parser.add_argument(
        "--actor-id",
        action="append",
        default=[],
        help="Limit validation to one child actor id. Repeat for multiple actors.",
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            event_log_path=args.event_log_path,
            row_id_filter=args.row_id,
            actor_id_filter=tuple(args.actor_id),
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
