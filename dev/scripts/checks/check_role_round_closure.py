#!/usr/bin/env python3
"""Fail when a multi-agent role round claims complete without typed closure proof.

A18 G38 guard. A "role round" is one iteration of typed work performed by a
parent role coordinator and its delegated child actors (implementer subagents,
review fan-out workers, etc). The round may only be marked complete when every
delegated child has reached typed terminal state with merged, proven, and
typed-disposition evidence, and when the parent has emitted a role-level
receipt that ties the child outputs together.

This guard fails closed if a round payload reports
`status == "complete"` (or equivalent) while any of the following are true:

- A child is still pending (RULE_CHILDREN_PENDING).
- A child reports a typed blocker (RULE_CHILDREN_BLOCKED).
- A child observation is stale beyond the configured freshness window
  (RULE_CHILDREN_STALE).
- A child patch is not yet merged into the round target
  (RULE_CHILDREN_UNMERGED).
- A child has no proof receipt covering the produced output
  (RULE_CHILDREN_UNPROVEN).
- A child has no accepted/rejected patch disposition
  (RULE_MISSING_PATCH_DISPOSITION).
- The round itself has no role-level receipt
  (RULE_MISSING_ROLE_LEVEL_RECEIPT).

Per the A18 core rule, role_id is the authority lane identity. The round
coordinator role must own the close-out; child capability_class is metadata
only and never substitutes for typed disposition + role-level receipt.
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
        coerce_string as _coerce_text,
        emit_runtime_error,
        parse_utc as _parse_utc,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        coerce_string as _coerce_text,
        emit_runtime_error,
        parse_utc as _parse_utc,
        utc_timestamp,
    )


COMMAND = "check_role_round_closure"
CONTRACT_ID = "RoleRoundClosureGuard"

DEFAULT_FRESHNESS_WINDOW_SECONDS = 24 * 3600

RULE_CHILDREN_PENDING = "children_pending"
RULE_CHILDREN_BLOCKED = "children_blocked"
RULE_CHILDREN_STALE = "children_stale"
RULE_CHILDREN_UNMERGED = "children_unmerged"
RULE_CHILDREN_UNPROVEN = "children_unproven"
RULE_MISSING_PATCH_DISPOSITION = "missing_patch_disposition"
RULE_MISSING_ROLE_LEVEL_RECEIPT = "missing_role_level_receipt"

DISPLAY_TEXT = (
    "Role round closure violation. A multi-agent role round claimed complete "
    "while children were pending, blocked, stale, unmerged, unproven, or "
    "missing accepted/rejected patch disposition or role-level receipt."
)

_PENDING_CHILD_STATES = frozenset(
    {
        "",
        "pending",
        "queued",
        "delegated",
        "in_progress",
        "in-progress",
        "running",
        "task_started",
        "task_progress",
    }
)
_BLOCKED_CHILD_STATES = frozenset(
    {
        "blocked",
        "task_blocked",
        "blocker",
        "stalled",
    }
)
_TERMINAL_ROUND_STATES = frozenset(
    {
        "complete",
        "completed",
        "closed",
        "finished",
        "done",
        "merged",
        "applied",
        "approved",
    }
)
_ACCEPTED_DISPOSITIONS = frozenset(
    {"accepted", "applied", "approved", "merged_in", "absorbed"}
)
_REJECTED_DISPOSITIONS = frozenset(
    {"rejected", "dismissed", "superseded", "withdrawn", "abandoned"}
)


@dataclass(frozen=True, slots=True)
class RoleRoundViolation:
    rule_id: str
    detail: str
    remediation: str
    round_id: str = ""
    role_id: str = ""
    child_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["child_ids"] = list(self.child_ids)
        return payload


def build_report(
    *,
    rounds: Sequence[Mapping[str, object]] | None = None,
    round_state_path: Path | None = None,
    freshness_window_seconds: int = DEFAULT_FRESHNESS_WINDOW_SECONDS,
    now: datetime | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    checked_surfaces: list[str] = []
    if rounds is None:
        path = round_state_path or _default_round_state_path()
        checked_surfaces.append(str(path))
        rounds = _rounds_from_state(path, warnings)
    else:
        rounds = tuple(rounds)
    now_utc = now or datetime.now(timezone.utc)

    violations: list[RoleRoundViolation] = []
    rounds_evaluated = 0
    rounds_complete_claimed = 0
    children_evaluated = 0
    for round_payload in rounds:
        if not isinstance(round_payload, Mapping):
            continue
        rounds_evaluated += 1
        if not _round_claims_complete(round_payload):
            continue
        rounds_complete_claimed += 1
        children = tuple(_iter_children(round_payload))
        children_evaluated += len(children)
        violations.extend(
            _violations_for_round(
                round_payload=round_payload,
                children=children,
                now=now_utc,
                freshness_window_seconds=freshness_window_seconds,
            )
        )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "freshness_window_seconds": freshness_window_seconds,
        "rounds_evaluated_count": rounds_evaluated,
        "rounds_complete_claimed_count": rounds_complete_claimed,
        "children_evaluated_count": children_evaluated,
        "violation_count": len(violations),
        "checked_surfaces": checked_surfaces,
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def _violations_for_round(
    *,
    round_payload: Mapping[str, object],
    children: Sequence[Mapping[str, object]],
    now: datetime,
    freshness_window_seconds: int,
) -> list[RoleRoundViolation]:
    violations: list[RoleRoundViolation] = []
    round_id = _coerce_text(round_payload.get("round_id"))
    role_id = _coerce_text(round_payload.get("role_id"))

    pending_ids: list[str] = []
    blocked_ids: list[str] = []
    stale_ids: list[str] = []
    unmerged_ids: list[str] = []
    unproven_ids: list[str] = []
    missing_disposition_ids: list[str] = []

    for child in children:
        child_id = _coerce_text(child.get("child_id") or child.get("actor_id"))
        state = _coerce_text(child.get("status") or child.get("state")).lower()
        if state in _BLOCKED_CHILD_STATES or _coerce_text(child.get("blocker")):
            blocked_ids.append(child_id)
        elif state in _PENDING_CHILD_STATES:
            pending_ids.append(child_id)
        if _child_is_stale(child, now=now, window_seconds=freshness_window_seconds):
            stale_ids.append(child_id)
        if not _child_is_merged(child):
            unmerged_ids.append(child_id)
        if not _child_has_proof(child):
            unproven_ids.append(child_id)
        if not _child_has_disposition(child):
            missing_disposition_ids.append(child_id)

    if pending_ids:
        violations.append(
            RoleRoundViolation(
                rule_id=RULE_CHILDREN_PENDING,
                detail=(
                    f"{len(pending_ids)} child actor(s) still pending while "
                    f"round_id={round_id!r} claims complete"
                ),
                remediation=(
                    "Wait for delegated child actors to finish or post a typed "
                    "blocker; the round coordinator cannot close while pending "
                    "children remain."
                ),
                round_id=round_id,
                role_id=role_id,
                child_ids=tuple(pending_ids),
            )
        )
    if blocked_ids:
        violations.append(
            RoleRoundViolation(
                rule_id=RULE_CHILDREN_BLOCKED,
                detail=(
                    f"{len(blocked_ids)} child actor(s) report a typed blocker "
                    f"in round_id={round_id!r}"
                ),
                remediation=(
                    "Resolve or escalate the typed blocker before closing the "
                    "round; do not silently absorb blocked child work into "
                    "the role-level result."
                ),
                round_id=round_id,
                role_id=role_id,
                child_ids=tuple(blocked_ids),
            )
        )
    if stale_ids:
        violations.append(
            RoleRoundViolation(
                rule_id=RULE_CHILDREN_STALE,
                detail=(
                    f"{len(stale_ids)} child actor(s) have no fresh observation "
                    f"within {freshness_window_seconds}s in round_id={round_id!r}"
                ),
                remediation=(
                    "Re-observe the stale child(ren) via the typed shared "
                    "round digest, or mark them blocked/withdrawn with typed "
                    "evidence before round closure."
                ),
                round_id=round_id,
                role_id=role_id,
                child_ids=tuple(stale_ids),
            )
        )
    if unmerged_ids:
        violations.append(
            RoleRoundViolation(
                rule_id=RULE_CHILDREN_UNMERGED,
                detail=(
                    f"{len(unmerged_ids)} child patch(es) remain unmerged in "
                    f"round_id={round_id!r}"
                ),
                remediation=(
                    "Route each unmerged patch through the typed merge gate "
                    "(G36) and capture conflict disposition (G37) before "
                    "closing the round."
                ),
                round_id=round_id,
                role_id=role_id,
                child_ids=tuple(unmerged_ids),
            )
        )
    if unproven_ids:
        violations.append(
            RoleRoundViolation(
                rule_id=RULE_CHILDREN_UNPROVEN,
                detail=(
                    f"{len(unproven_ids)} child patch(es) carry no typed proof "
                    f"receipt in round_id={round_id!r}"
                ),
                remediation=(
                    "Attach a typed proof receipt (test, validation, or "
                    "feature-proof receipt id) for each child patch before "
                    "round closure."
                ),
                round_id=round_id,
                role_id=role_id,
                child_ids=tuple(unproven_ids),
            )
        )
    if missing_disposition_ids:
        violations.append(
            RoleRoundViolation(
                rule_id=RULE_MISSING_PATCH_DISPOSITION,
                detail=(
                    f"{len(missing_disposition_ids)} child patch(es) lack an "
                    f"accepted/rejected typed disposition in "
                    f"round_id={round_id!r}"
                ),
                remediation=(
                    "Record a typed patch disposition (accepted, rejected, "
                    "superseded, etc.) for every child output before round "
                    "closure."
                ),
                round_id=round_id,
                role_id=role_id,
                child_ids=tuple(missing_disposition_ids),
            )
        )
    if not _round_has_role_level_receipt(round_payload):
        violations.append(
            RoleRoundViolation(
                rule_id=RULE_MISSING_ROLE_LEVEL_RECEIPT,
                detail=(
                    f"round_id={round_id!r} claims complete with no role-level "
                    f"receipt id (role_level_receipt_id / round_receipt_id)"
                ),
                remediation=(
                    "Emit a typed role-level receipt that binds child outputs "
                    "to the round result before claiming complete; provider "
                    "narration is not a receipt."
                ),
                round_id=round_id,
                role_id=role_id,
            )
        )
    return violations


def _round_claims_complete(round_payload: Mapping[str, object]) -> bool:
    status = _coerce_text(
        round_payload.get("status")
        or round_payload.get("round_status")
        or round_payload.get("state")
    ).lower()
    if status in _TERMINAL_ROUND_STATES:
        return True
    return _coerce_bool(round_payload.get("claimed_complete")) or _coerce_bool(
        round_payload.get("closed")
    )


def _iter_children(
    round_payload: Mapping[str, object],
) -> Iterable[Mapping[str, object]]:
    for key in ("children", "child_actors", "delegated_children", "subagents"):
        value = round_payload.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                if isinstance(item, Mapping):
                    yield item


def _child_is_stale(
    child: Mapping[str, object],
    *,
    now: datetime,
    window_seconds: int,
) -> bool:
    if _coerce_bool(child.get("stale")):
        return True
    observed = _coerce_text(
        child.get("observed_at")
        or child.get("observed_at_utc")
        or child.get("last_observed_at")
        or child.get("last_observed_at_utc")
    )
    parsed = _parse_utc(observed)
    if parsed is None:
        # No observation timestamp at all is treated as stale only when the
        # child is otherwise considered post-pending; pending children are
        # already reported by RULE_CHILDREN_PENDING and would double-report.
        state = _coerce_text(child.get("status") or child.get("state")).lower()
        if state in _PENDING_CHILD_STATES or state in _BLOCKED_CHILD_STATES:
            return False
        return True
    return parsed.timestamp() <= now.timestamp() - window_seconds


def _child_is_merged(child: Mapping[str, object]) -> bool:
    if _coerce_bool(child.get("merged")):
        return True
    merge_status = _coerce_text(
        child.get("merge_status") or child.get("merge_state")
    ).lower()
    if merge_status in {"merged", "applied", "absorbed", "integrated"}:
        return True
    if _coerce_text(child.get("merge_receipt_id") or child.get("merged_into")):
        return True
    return False


def _child_has_proof(child: Mapping[str, object]) -> bool:
    if _coerce_bool(child.get("proven")):
        return True
    proof = _coerce_text(
        child.get("proof_receipt_id")
        or child.get("feature_proof_receipt_id")
        or child.get("validation_receipt_id")
        or child.get("test_receipt_id")
    )
    if proof:
        return True
    proof_status = _coerce_text(
        child.get("proof_status") or child.get("test_status")
    ).lower()
    return proof_status in {"proven", "proven_passed", "passed"}


def _child_has_disposition(child: Mapping[str, object]) -> bool:
    disposition = _coerce_text(
        child.get("patch_disposition")
        or child.get("disposition")
        or child.get("disposition_state")
    ).lower()
    if not disposition:
        return False
    return (
        disposition in _ACCEPTED_DISPOSITIONS
        or disposition in _REJECTED_DISPOSITIONS
    )


def _round_has_role_level_receipt(round_payload: Mapping[str, object]) -> bool:
    for key in (
        "role_level_receipt_id",
        "round_receipt_id",
        "role_receipt_id",
        "role_level_receipt",
    ):
        if _coerce_text(round_payload.get(key)):
            return True
    return False


def _rounds_from_state(
    path: Path, warnings: list[str]
) -> tuple[Mapping[str, object], ...]:
    if not path.exists():
        warnings.append(f"round state missing: {path}")
        return ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"round state load failed: {exc}")
        return ()
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        return tuple(item for item in payload if isinstance(item, Mapping))
    if not isinstance(payload, Mapping):
        return ()
    rounds = payload.get("rounds") or payload.get("role_rounds")
    if isinstance(rounds, Sequence) and not isinstance(rounds, (str, bytes)):
        return tuple(item for item in rounds if isinstance(item, Mapping))
    return ()


def _default_round_state_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/role_rounds/latest.json"


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = _coerce_text(value).lower()
    return text in {"true", "yes", "1"}


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- rounds_evaluated_count: {report.get('rounds_evaluated_count')}")
    lines.append(
        f"- rounds_complete_claimed_count: {report.get('rounds_complete_claimed_count')}"
    )
    lines.append(f"- children_evaluated_count: {report.get('children_evaluated_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    lines.append(
        f"- freshness_window_seconds: {report.get('freshness_window_seconds')}"
    )
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            child_ids = violation.get("child_ids")
            child_render = ""
            if isinstance(child_ids, Sequence) and not isinstance(child_ids, (str, bytes)) and child_ids:
                child_render = " child_ids=" + ",".join(str(c) for c in child_ids)
            lines.append(
                f"- {violation.get('rule_id')} round_id={violation.get('round_id')!r}"
                f" role_id={violation.get('role_id')!r}{child_render}: "
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
        "--round-state-path",
        type=Path,
        default=_default_round_state_path(),
        help="JSON file containing role round payloads.",
    )
    parser.add_argument(
        "--freshness-window-seconds",
        type=int,
        default=DEFAULT_FRESHNESS_WINDOW_SECONDS,
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            round_state_path=args.round_state_path,
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
