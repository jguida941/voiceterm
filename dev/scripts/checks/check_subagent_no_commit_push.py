#!/usr/bin/env python3
"""Fail when a child/sub-agent attempts commit, push, row closure, generated-surface rewrite, or receipt-store mutation outside explicit authority.

Per A18/G39 of the GuardIR governance plan, child/sub-agent actors do not get
commit, push, row closure, generated-surface rewrite, or receipt-store
mutation authority by default. Governed commit/push must travel through the
parent/transport/approval route. Remote control is transport/approval routing
only -- it is never role authority. This guard inspects attempted sub-agent
actions and fails closed when any attempt lacks an explicit typed authority
chain through the parent role coordinator.
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
        iter_jsonl as _shared_iter_jsonl,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _shared_iter_jsonl,
        utc_timestamp,
    )


COMMAND = "check_subagent_no_commit_push"
CONTRACT_ID = "SubagentNoCommitPushGuard"

RULE_SUBAGENT_ATTEMPTED_COMMIT = "subagent_attempted_commit"
RULE_SUBAGENT_ATTEMPTED_PUSH = "subagent_attempted_push"
RULE_SUBAGENT_ATTEMPTED_ROW_CLOSURE = "subagent_attempted_row_closure"
RULE_SUBAGENT_ATTEMPTED_GENERATED_SURFACE_REWRITE = (
    "subagent_attempted_generated_surface_rewrite"
)
RULE_SUBAGENT_ATTEMPTED_RECEIPT_STORE_MUTATION = (
    "subagent_attempted_receipt_store_mutation"
)
RULE_REMOTE_CONTROL_TREATED_AS_AUTHORITY = (
    "remote_control_treated_as_authority"
)

DISPLAY_TEXT = (
    "Sub-agent authority violation. Child/sub-agent actors do not get commit, "
    "push, row closure, generated-surface rewrite, or receipt-store mutation "
    "authority by default. Governed commit/push must travel through the typed "
    "parent/transport/approval route, and remote control remains "
    "transport/approval routing only -- never role authority."
)

DEFAULT_SUBAGENT_ACTIONS_PATH = (
    REPO_ROOT / "dev/state/subagent_action_attempts.jsonl"
)

ACTION_KIND_COMMIT = "commit"
ACTION_KIND_PUSH = "push"
ACTION_KIND_ROW_CLOSURE = "row_closure"
ACTION_KIND_GENERATED_SURFACE_REWRITE = "generated_surface_rewrite"
ACTION_KIND_RECEIPT_STORE_MUTATION = "receipt_store_mutation"

_ACTION_KIND_TO_RULE: dict[str, str] = {
    ACTION_KIND_COMMIT: RULE_SUBAGENT_ATTEMPTED_COMMIT,
    ACTION_KIND_PUSH: RULE_SUBAGENT_ATTEMPTED_PUSH,
    ACTION_KIND_ROW_CLOSURE: RULE_SUBAGENT_ATTEMPTED_ROW_CLOSURE,
    ACTION_KIND_GENERATED_SURFACE_REWRITE: (
        RULE_SUBAGENT_ATTEMPTED_GENERATED_SURFACE_REWRITE
    ),
    ACTION_KIND_RECEIPT_STORE_MUTATION: (
        RULE_SUBAGENT_ATTEMPTED_RECEIPT_STORE_MUTATION
    ),
}

# Routes that prove governed commit/push traveled through the parent role
# coordinator's transport/approval path rather than a raw sub-agent shortcut.
SANCTIONED_PARENT_ROUTE_KINDS = frozenset(
    {
        "parent_role_coordinator",
        "parent_transport_approval",
        "parent_merge_gate",
        "governed_push_adapter",
    }
)

# Authority-source labels that prove the remote-control surface was correctly
# treated as transport-only routing rather than as role authority.
REMOTE_CONTROL_TRANSPORT_LABELS = frozenset(
    {
        "remote_control_transport",
        "remote_control_routing",
        "transport_only",
        "approval_routing_only",
    }
)

# Authority-source labels that promote the remote-control surface into a
# mutation-authority role -- always a violation under the A18 invariant
# "remote control is only transport/approval routing".
REMOTE_CONTROL_AUTHORITY_LABELS = frozenset(
    {
        "remote_control",
        "remote_control_authority",
        "remote_control_role",
        "remote-control",
    }
)


@dataclass(frozen=True, slots=True)
class SubagentAuthorityViolation:
    rule_id: str
    attempt_id: str
    child_actor_id: str
    parent_role_occupancy_id: str
    action_kind: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    actions: Sequence[Mapping[str, object]] | None = None,
    actions_path: Path | None = None,
    row_id_filter: str = "",
) -> dict[str, object]:
    """Build the typed sub-agent authority report.

    Each action describes an attempt by a child/sub-agent to commit, push,
    close a row, rewrite a generated surface, or mutate a receipt store. The
    guard fails closed if the attempt lacks a typed parent/transport/approval
    route, or if the authority source treats remote control as role authority
    rather than transport routing only.
    """

    warnings: list[str] = []
    checked_surfaces: list[str] = []
    if actions is None:
        source_path = actions_path or DEFAULT_SUBAGENT_ACTIONS_PATH
        checked_surfaces.append(str(source_path))
        actions = tuple(_iter_jsonl(source_path, warnings=warnings))
    else:
        actions = tuple(actions)

    violations: list[SubagentAuthorityViolation] = []
    checked_attempt_ids: list[str] = []
    checked_attempt_count = 0
    for action in actions:
        if row_id_filter and not _action_matches_row(action, row_id_filter):
            continue
        attempt_id = _attempt_id(action)
        checked_attempt_ids.append(attempt_id)
        checked_attempt_count += 1
        violations.extend(_violations_for_action(action))

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "row_id_filter": row_id_filter,
        "checked_attempt_count": checked_attempt_count,
        "checked_attempt_ids": checked_attempt_ids,
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "checked_surfaces": checked_surfaces,
        "warnings": warnings,
    }


def _violations_for_action(
    action: Mapping[str, object],
) -> tuple[SubagentAuthorityViolation, ...]:
    violations: list[SubagentAuthorityViolation] = []
    if not _actor_is_subagent(action):
        return ()

    attempt_id = _attempt_id(action)
    child_actor = str(action.get("child_actor_id") or action.get("actor_id") or "").strip()
    parent_id = str(action.get("parent_role_occupancy_id") or "").strip()
    action_kind = _normalized_action_kind(action)

    # Remote-control-as-authority is checked independently of the per-kind
    # rules so it surfaces even on attempts that would otherwise pass.
    if _remote_control_treated_as_authority(action):
        violations.append(
            SubagentAuthorityViolation(
                rule_id=RULE_REMOTE_CONTROL_TREATED_AS_AUTHORITY,
                attempt_id=attempt_id,
                child_actor_id=child_actor,
                parent_role_occupancy_id=parent_id,
                action_kind=action_kind,
                detail=(
                    "Sub-agent attempt cites remote control as mutation "
                    "authority. Remote control is transport/approval routing "
                    "only and is never role authority."
                ),
                remediation=(
                    "Route the action through the parent role coordinator's "
                    "typed transport/approval path. Replace the "
                    "remote-control authority claim with a typed "
                    "RoleOccupancyAssignment or governed-push receipt."
                ),
            )
        )

    rule_id = _ACTION_KIND_TO_RULE.get(action_kind)
    if rule_id is None:
        return tuple(violations)

    if _has_explicit_parent_authority(action):
        return tuple(violations)

    violations.append(
        SubagentAuthorityViolation(
            rule_id=rule_id,
            attempt_id=attempt_id,
            child_actor_id=child_actor,
            parent_role_occupancy_id=parent_id,
            action_kind=action_kind,
            detail=(
                f"Child/sub-agent {child_actor!r} attempted "
                f"action_kind={action_kind!r} without a typed parent/transport/"
                f"approval route or explicit authority refs."
            ),
            remediation=_remediation_for_rule(rule_id),
        )
    )
    return tuple(violations)


def _actor_is_subagent(action: Mapping[str, object]) -> bool:
    if _coerce_bool(action.get("is_subagent")):
        return True
    if _coerce_bool(action.get("is_child_actor")):
        return True
    actor_kind = str(action.get("actor_kind") or "").strip().lower()
    if actor_kind in {"child", "subagent", "sub_agent", "sub-agent"}:
        return True
    # A populated `child_actor_id` or `parent_role_occupancy_id` is a strong
    # signal that the actor sits below a typed parent role coordinator.
    if str(action.get("child_actor_id") or "").strip():
        return True
    if str(action.get("parent_role_occupancy_id") or "").strip():
        return True
    return False


def _has_explicit_parent_authority(action: Mapping[str, object]) -> bool:
    route = str(action.get("route_kind") or action.get("route") or "").strip().lower()
    if route in SANCTIONED_PARENT_ROUTE_KINDS:
        return _authority_refs_present(action)
    if _coerce_bool(action.get("parent_route_used")):
        return _authority_refs_present(action)
    return False


def _authority_refs_present(action: Mapping[str, object]) -> bool:
    refs = action.get("authority_refs")
    if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
        return any(str(ref).strip() for ref in refs)
    if isinstance(refs, str):
        return bool(refs.strip())
    return False


def _remote_control_treated_as_authority(action: Mapping[str, object]) -> bool:
    source = str(action.get("authority_source") or "").strip().lower()
    if source in REMOTE_CONTROL_AUTHORITY_LABELS:
        return True
    sources = action.get("authority_sources")
    if isinstance(sources, Sequence) and not isinstance(sources, (str, bytes)):
        for value in sources:
            label = str(value or "").strip().lower()
            if label in REMOTE_CONTROL_AUTHORITY_LABELS:
                return True
    # `remote_control_role=true` is a positive flag that the actor is
    # asserting remote-control as a mutation-authority role.
    if _coerce_bool(action.get("remote_control_as_authority")):
        return True
    return False


def _normalized_action_kind(action: Mapping[str, object]) -> str:
    value = str(action.get("action_kind") or action.get("kind") or "").strip().lower()
    if value in _ACTION_KIND_TO_RULE:
        return value
    if value in {"git_commit", "repo.commit"}:
        return ACTION_KIND_COMMIT
    if value in {"git_push", "repo.push"}:
        return ACTION_KIND_PUSH
    if value in {"close_row", "plan_row_closure", "row_close"}:
        return ACTION_KIND_ROW_CLOSURE
    if value in {"surface_rewrite", "render_surfaces", "generated_surface_write"}:
        return ACTION_KIND_GENERATED_SURFACE_REWRITE
    if value in {"receipt_store_write", "receipt_mutation"}:
        return ACTION_KIND_RECEIPT_STORE_MUTATION
    return value


def _remediation_for_rule(rule_id: str) -> str:
    if rule_id == RULE_SUBAGENT_ATTEMPTED_COMMIT:
        return (
            "Submit the patch/proof output to the parent role coordinator. "
            "Governed commits travel through the typed parent/transport/"
            "approval route, not a raw sub-agent commit."
        )
    if rule_id == RULE_SUBAGENT_ATTEMPTED_PUSH:
        return (
            "Route the push through the governed push adapter under the "
            "parent role coordinator's approval. Sub-agents do not get "
            "direct push authority."
        )
    if rule_id == RULE_SUBAGENT_ATTEMPTED_ROW_CLOSURE:
        return (
            "Only the parent role coordinator closes PlanRows. Submit "
            "completion proof and let the parent emit the closure receipt."
        )
    if rule_id == RULE_SUBAGENT_ATTEMPTED_GENERATED_SURFACE_REWRITE:
        return (
            "Generated-surface rewrites must be performed by an actor with "
            "explicit surface-rewrite authority (typed delegation scope), "
            "not by an unauthorized sub-agent."
        )
    if rule_id == RULE_SUBAGENT_ATTEMPTED_RECEIPT_STORE_MUTATION:
        return (
            "Receipt-store mutations require explicit typed authority. "
            "Route the receipt write through the parent role coordinator "
            "or a sanctioned receipt-emit pipeline."
        )
    return (
        "Submit the action to the parent role coordinator's typed "
        "transport/approval route before retrying."
    )


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    return False


def _attempt_id(action: Mapping[str, object]) -> str:
    for field in ("attempt_id", "action_id", "id"):
        value = str(action.get(field) or "").strip()
        if value:
            return value
    return ""


def _action_matches_row(action: Mapping[str, object], row_id_filter: str) -> bool:
    for field in ("target_plan_row_id", "plan_row_id", "target_ref", "plan_id"):
        value = str(action.get(field) or "").strip()
        if value and row_id_filter in value:
            return True
    return False


def _iter_jsonl(
    path: Path, *, warnings: list[str]
) -> Iterable[Mapping[str, object]]:
    return _shared_iter_jsonl(
        path,
        warnings=warnings,
        missing_label="sub-agent action ledger missing",
    )


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- checked_attempt_count: {report.get('checked_attempt_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("row_id_filter"):
        lines.append(f"- row_id_filter: `{report.get('row_id_filter')}`")
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
                f"- {violation.get('attempt_id')}: {violation.get('rule_id')} "
                f"(child={violation.get('child_actor_id')}, "
                f"action_kind={violation.get('action_kind')}): "
                f"{violation.get('detail')}"
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
        "--actions-path",
        type=Path,
        default=DEFAULT_SUBAGENT_ACTIONS_PATH,
        help="Typed SubagentActionAttempt ledger (JSONL).",
    )
    parser.add_argument(
        "--row-id",
        default="",
        help=(
            "If set, only check attempts whose PlanRow target contains this "
            "row id."
        ),
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            actions_path=args.actions_path,
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
