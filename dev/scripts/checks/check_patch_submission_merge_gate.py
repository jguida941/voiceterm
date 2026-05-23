#!/usr/bin/env python3
"""Fail when child implementation output bypasses the parent role coordinator.

G36 patch-submission merge gate: every child implementation output must enter
the parent role coordinator's merge gate so the parent can run the conflict
check, emit combined proof, and produce a role-level result. Direct
child-to-mutation paths without the parent coordinator are denied.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
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


COMMAND = "check_patch_submission_merge_gate"
CONTRACT_ID = "PatchSubmissionMergeGateGuard"

RULE_CHILD_OUTPUT_BYPASSED_PARENT = "child_output_bypassed_parent"
RULE_MISSING_PATCH_SUBMISSION_RECEIPT = "missing_patch_submission_receipt"
RULE_MISSING_CONFLICT_CHECK = "missing_conflict_check"
RULE_MISSING_COMBINED_PROOF = "missing_combined_proof"
RULE_MISSING_ROLE_LEVEL_RESULT = "missing_role_level_result"

DISPLAY_TEXT = (
    "Patch submission merge gate violation. Child implementation output must "
    "submit to the parent role coordinator for conflict check, combined "
    "proof, and role-level result. Direct child mutation paths that bypass "
    "the parent merge gate are denied."
)

CHILD_OUTPUT_EVENT_TYPE = "child_implementation_output"
PATCH_SUBMISSION_EVENT_TYPE = "patch_submission_received"
CONFLICT_CHECK_EVENT_TYPE = "merge_gate_conflict_check"
COMBINED_PROOF_EVENT_TYPE = "merge_gate_combined_proof"
ROLE_LEVEL_RESULT_EVENT_TYPE = "merge_gate_role_level_result"


@dataclass(frozen=True, slots=True)
class MergeGateViolation:
    child_actor_id: str
    parent_role_coordinator_id: str
    rule_id: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _ChildOutputIndex:
    child_actor_id: str
    parent_role_coordinator_id: str
    patch_id: str
    row_id: str
    event: Mapping[str, object]


def build_report(
    *,
    events: Sequence[Mapping[str, object]] | None = None,
    event_log_path: Path | None = None,
    row_id_filter: str = "",
    child_actor_ids: Sequence[str] = (),
) -> dict[str, object]:
    warnings: list[str] = []
    source_path: Path | None = None
    if events is None:
        source_path = event_log_path or _default_event_log_path()
        events = tuple(_iter_jsonl(source_path, warnings=warnings))
    else:
        events = tuple(events)

    (
        child_outputs,
        submissions_by_patch,
        conflict_checks_by_patch,
        combined_proofs_by_patch,
        role_results_by_patch,
    ) = _index_events(events)

    actor_filter = _normalized_actor_ids(child_actor_ids)
    violations: list[MergeGateViolation] = []
    checked_child_ids: list[str] = []
    checked_child_count = 0
    for output in child_outputs:
        if actor_filter and output.child_actor_id not in actor_filter:
            continue
        if row_id_filter and not _row_matches_filter(
            output.event, row_id_filter
        ):
            continue
        checked_child_ids.append(output.child_actor_id)
        checked_child_count += 1
        violations.extend(
            _violations_for_output(
                output=output,
                submissions=submissions_by_patch.get(output.patch_id, ()),
                conflict_checks=conflict_checks_by_patch.get(output.patch_id, ()),
                combined_proofs=combined_proofs_by_patch.get(output.patch_id, ()),
                role_results=role_results_by_patch.get(output.patch_id, ()),
            )
        )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "event_log_path": str(source_path) if source_path is not None else "",
        "row_id_filter": row_id_filter,
        "child_actor_ids": list(actor_filter),
        "checked_child_actor_ids": checked_child_ids,
        "checked_child_output_count": checked_child_count,
        "patch_submission_event_count": sum(
            len(events_) for events_ in submissions_by_patch.values()
        ),
        "conflict_check_event_count": sum(
            len(events_) for events_ in conflict_checks_by_patch.values()
        ),
        "combined_proof_event_count": sum(
            len(events_) for events_ in combined_proofs_by_patch.values()
        ),
        "role_level_result_event_count": sum(
            len(events_) for events_ in role_results_by_patch.values()
        ),
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def _violations_for_output(
    *,
    output: _ChildOutputIndex,
    submissions: Sequence[Mapping[str, object]],
    conflict_checks: Sequence[Mapping[str, object]],
    combined_proofs: Sequence[Mapping[str, object]],
    role_results: Sequence[Mapping[str, object]],
) -> tuple[MergeGateViolation, ...]:
    violations: list[MergeGateViolation] = []
    parent = output.parent_role_coordinator_id

    if not parent:
        violations.append(
            MergeGateViolation(
                child_actor_id=output.child_actor_id,
                parent_role_coordinator_id="",
                rule_id=RULE_CHILD_OUTPUT_BYPASSED_PARENT,
                detail=(
                    f"child implementation output from actor "
                    f"{output.child_actor_id!r} declares no "
                    "parent_role_coordinator_id"
                ),
                remediation=(
                    "Route the child implementation output through the parent "
                    "role coordinator. Direct child mutation bypasses the "
                    "merge gate."
                ),
            )
        )
        return tuple(violations)

    if not _has_matching_event(
        events=submissions,
        parent=parent,
        patch_id=output.patch_id,
        child_actor=output.child_actor_id,
    ):
        violations.append(
            MergeGateViolation(
                child_actor_id=output.child_actor_id,
                parent_role_coordinator_id=parent,
                rule_id=RULE_MISSING_PATCH_SUBMISSION_RECEIPT,
                detail=(
                    f"no patch_submission_received event from parent {parent!r} "
                    f"for child {output.child_actor_id!r} / patch "
                    f"{output.patch_id!r}"
                ),
                remediation=(
                    "Parent role coordinator must emit a "
                    "patch_submission_received event before the child output "
                    "can proceed."
                ),
            )
        )

    if not _has_matching_event(
        events=conflict_checks,
        parent=parent,
        patch_id=output.patch_id,
        child_actor=output.child_actor_id,
    ):
        violations.append(
            MergeGateViolation(
                child_actor_id=output.child_actor_id,
                parent_role_coordinator_id=parent,
                rule_id=RULE_MISSING_CONFLICT_CHECK,
                detail=(
                    f"no merge_gate_conflict_check event from parent "
                    f"{parent!r} for patch {output.patch_id!r}"
                ),
                remediation=(
                    "Parent role coordinator must run the conflict check and "
                    "emit a merge_gate_conflict_check event."
                ),
            )
        )

    if not _has_matching_event(
        events=combined_proofs,
        parent=parent,
        patch_id=output.patch_id,
        child_actor=output.child_actor_id,
    ):
        violations.append(
            MergeGateViolation(
                child_actor_id=output.child_actor_id,
                parent_role_coordinator_id=parent,
                rule_id=RULE_MISSING_COMBINED_PROOF,
                detail=(
                    f"no merge_gate_combined_proof event from parent "
                    f"{parent!r} for patch {output.patch_id!r}"
                ),
                remediation=(
                    "Parent role coordinator must publish a "
                    "merge_gate_combined_proof event combining child + parent "
                    "evidence."
                ),
            )
        )

    if not _has_matching_event(
        events=role_results,
        parent=parent,
        patch_id=output.patch_id,
        child_actor=output.child_actor_id,
    ):
        violations.append(
            MergeGateViolation(
                child_actor_id=output.child_actor_id,
                parent_role_coordinator_id=parent,
                rule_id=RULE_MISSING_ROLE_LEVEL_RESULT,
                detail=(
                    f"no merge_gate_role_level_result event from parent "
                    f"{parent!r} for patch {output.patch_id!r}"
                ),
                remediation=(
                    "Parent role coordinator must emit a "
                    "merge_gate_role_level_result event with accepted/rejected "
                    "disposition before role round closure."
                ),
            )
        )

    return tuple(violations)


def _has_matching_event(
    *,
    events: Sequence[Mapping[str, object]],
    parent: str,
    patch_id: str,
    child_actor: str,
) -> bool:
    for event in events:
        event_parent = str(event.get("parent_role_coordinator_id") or "").strip()
        event_patch = str(event.get("patch_id") or "").strip()
        event_child = str(event.get("child_actor_id") or "").strip()
        if event_parent != parent:
            continue
        if patch_id and event_patch and event_patch != patch_id:
            continue
        if child_actor and event_child and event_child != child_actor:
            continue
        return True
    return False


def _index_events(
    events: Sequence[Mapping[str, object]],
) -> tuple[
    list[_ChildOutputIndex],
    dict[str, list[Mapping[str, object]]],
    dict[str, list[Mapping[str, object]]],
    dict[str, list[Mapping[str, object]]],
    dict[str, list[Mapping[str, object]]],
]:
    child_outputs: list[_ChildOutputIndex] = []
    submissions: dict[str, list[Mapping[str, object]]] = {}
    conflict_checks: dict[str, list[Mapping[str, object]]] = {}
    combined_proofs: dict[str, list[Mapping[str, object]]] = {}
    role_results: dict[str, list[Mapping[str, object]]] = {}

    for event in events:
        event_type = str(event.get("event_type") or "").strip()
        patch_id = str(event.get("patch_id") or "").strip()
        if event_type == CHILD_OUTPUT_EVENT_TYPE:
            child_outputs.append(
                _ChildOutputIndex(
                    child_actor_id=str(event.get("child_actor_id") or "").strip(),
                    parent_role_coordinator_id=str(
                        event.get("parent_role_coordinator_id") or ""
                    ).strip(),
                    patch_id=patch_id,
                    row_id=_row_from_event(event),
                    event=event,
                )
            )
        elif event_type == PATCH_SUBMISSION_EVENT_TYPE:
            submissions.setdefault(patch_id, []).append(event)
        elif event_type == CONFLICT_CHECK_EVENT_TYPE:
            conflict_checks.setdefault(patch_id, []).append(event)
        elif event_type == COMBINED_PROOF_EVENT_TYPE:
            combined_proofs.setdefault(patch_id, []).append(event)
        elif event_type == ROLE_LEVEL_RESULT_EVENT_TYPE:
            role_results.setdefault(patch_id, []).append(event)

    return child_outputs, submissions, conflict_checks, combined_proofs, role_results


def _row_from_event(event: Mapping[str, object]) -> str:
    target_ref = str(event.get("target_ref") or "").strip()
    if target_ref:
        return target_ref
    return str(event.get("plan_id") or "").strip()


def _row_matches_filter(event: Mapping[str, object], row_id_filter: str) -> bool:
    target_ref = str(event.get("target_ref") or "").strip()
    if target_ref and row_id_filter in target_ref:
        return True
    plan_id = str(event.get("plan_id") or "").strip()
    return row_id_filter == plan_id


def _normalized_actor_ids(actor_ids: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for actor_id in actor_ids:
        value = str(actor_id or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _default_event_log_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/events/trace.ndjson"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(
        f"- checked_child_output_count: {report.get('checked_child_output_count')}"
    )
    lines.append(
        f"- patch_submission_event_count: {report.get('patch_submission_event_count')}"
    )
    lines.append(
        f"- conflict_check_event_count: {report.get('conflict_check_event_count')}"
    )
    lines.append(
        f"- combined_proof_event_count: {report.get('combined_proof_event_count')}"
    )
    lines.append(
        f"- role_level_result_event_count: {report.get('role_level_result_event_count')}"
    )
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("row_id_filter"):
        lines.append(f"- row_id_filter: `{report.get('row_id_filter')}`")
    actor_ids = report.get("child_actor_ids")
    if (
        isinstance(actor_ids, Sequence)
        and not isinstance(actor_ids, (str, bytes))
        and actor_ids
    ):
        rendered = ", ".join(f"`{actor_id}`" for actor_id in actor_ids)
        lines.append(f"- child_actor_ids: {rendered}")
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
                f"- {violation.get('child_actor_id')} -> "
                f"{violation.get('parent_role_coordinator_id') or '<none>'}: "
                f"{violation.get('rule_id')} ({violation.get('detail')})"
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
            "If set, only check child outputs whose target_ref/plan_id "
            "matches this row id."
        ),
    )
    parser.add_argument(
        "--child-actor-id",
        action="append",
        default=[],
        help="Limit validation to one child actor id. Repeat for multiples.",
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            event_log_path=args.event_log_path,
            row_id_filter=args.row_id,
            child_actor_ids=tuple(args.child_actor_id),
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
