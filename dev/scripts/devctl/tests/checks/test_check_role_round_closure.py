"""Tests for `check_role_round_closure` (A18 G38)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dev.scripts.checks import check_role_round_closure as guard


_NOW = datetime(2026, 5, 22, 23, 0, 0, tzinfo=timezone.utc)


def _utc(seconds_ago: int) -> str:
    return (_NOW - timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def _child(
    *,
    child_id: str = "child-claude-A",
    status: str = "applied",
    blocker: str = "",
    observed_seconds_ago: int = 60,
    merge_status: str = "merged",
    proof_receipt_id: str = "rcpt-proof-x",
    patch_disposition: str = "accepted",
    extra: dict | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "child_id": child_id,
        "status": status,
        "blocker": blocker,
        "observed_at_utc": _utc(observed_seconds_ago),
        "merge_status": merge_status,
        "proof_receipt_id": proof_receipt_id,
        "patch_disposition": patch_disposition,
    }
    if extra:
        payload.update(extra)
    return payload


def _round(
    *,
    round_id: str = "round-A",
    role_id: str = "implementer",
    status: str = "complete",
    role_level_receipt_id: str = "rcpt-round-A",
    children: list[dict] | None = None,
    extra: dict | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "round_id": round_id,
        "role_id": role_id,
        "status": status,
        "role_level_receipt_id": role_level_receipt_id,
        "children": children if children is not None else [_child()],
    }
    if extra:
        payload.update(extra)
    return payload


def test_green_complete_round_with_proven_merged_child_passes():
    report = guard.build_report(rounds=[_round()], now=_NOW)
    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["rounds_evaluated_count"] == 1
    assert report["rounds_complete_claimed_count"] == 1
    assert report["children_evaluated_count"] == 1


def test_rule_children_pending_fails():
    rounds = [
        _round(
            children=[
                _child(
                    child_id="child-pending",
                    status="pending",
                    patch_disposition="",
                    merge_status="",
                    proof_receipt_id="",
                )
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILDREN_PENDING in rule_ids
    pending = next(
        v for v in report["violations"] if v["rule_id"] == guard.RULE_CHILDREN_PENDING
    )
    assert "child-pending" in pending["child_ids"]


def test_rule_children_blocked_fails():
    rounds = [
        _round(
            children=[
                _child(
                    child_id="child-blocked",
                    status="blocked",
                    blocker="merge_conflict",
                    patch_disposition="",
                    merge_status="",
                    proof_receipt_id="",
                )
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILDREN_BLOCKED in rule_ids
    # Blocked child must not also be counted under "pending"
    blocked = next(
        v for v in report["violations"] if v["rule_id"] == guard.RULE_CHILDREN_BLOCKED
    )
    assert "child-blocked" in blocked["child_ids"]


def test_rule_children_stale_fails():
    rounds = [
        _round(
            children=[
                _child(
                    child_id="child-stale",
                    status="applied",
                    observed_seconds_ago=guard.DEFAULT_FRESHNESS_WINDOW_SECONDS + 60,
                )
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILDREN_STALE in rule_ids


def test_rule_children_stale_skipped_for_pending_child():
    # A child with no observation_at + pending state should be reported as
    # CHILDREN_PENDING but not double-counted as CHILDREN_STALE.
    rounds = [
        _round(
            children=[
                {
                    "child_id": "child-no-obs",
                    "status": "pending",
                    "merge_status": "",
                    "proof_receipt_id": "",
                    "patch_disposition": "",
                }
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILDREN_PENDING in rule_ids
    assert guard.RULE_CHILDREN_STALE not in rule_ids


def test_rule_children_unmerged_fails():
    rounds = [
        _round(
            children=[
                _child(
                    child_id="child-unmerged",
                    status="applied",
                    merge_status="",
                )
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILDREN_UNMERGED in rule_ids
    unmerged = next(
        v for v in report["violations"] if v["rule_id"] == guard.RULE_CHILDREN_UNMERGED
    )
    assert "child-unmerged" in unmerged["child_ids"]


def test_rule_children_unproven_fails():
    rounds = [
        _round(
            children=[
                _child(
                    child_id="child-unproven",
                    status="applied",
                    proof_receipt_id="",
                )
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILDREN_UNPROVEN in rule_ids


def test_rule_missing_patch_disposition_fails():
    rounds = [
        _round(
            children=[
                _child(
                    child_id="child-no-disposition",
                    status="applied",
                    patch_disposition="",
                )
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_PATCH_DISPOSITION in rule_ids


def test_rule_missing_role_level_receipt_fails():
    rounds = [_round(role_level_receipt_id="")]
    report = guard.build_report(rounds=rounds, now=_NOW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_ROLE_LEVEL_RECEIPT in rule_ids


def test_open_round_is_not_evaluated_for_closure():
    rounds = [
        _round(
            status="in_progress",
            role_level_receipt_id="",
            children=[
                _child(
                    child_id="child-pending",
                    status="pending",
                    merge_status="",
                    proof_receipt_id="",
                    patch_disposition="",
                )
            ],
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    assert report["ok"] is True
    assert report["rounds_complete_claimed_count"] == 0
    assert report["children_evaluated_count"] == 0
    assert report["violation_count"] == 0


def test_closed_boolean_flag_treated_as_complete():
    rounds = [
        _round(
            status="in_progress",
            role_level_receipt_id="",
            extra={"closed": True},
            children=[
                _child(
                    child_id="child-pending",
                    status="pending",
                    merge_status="",
                    proof_receipt_id="",
                    patch_disposition="",
                )
            ],
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILDREN_PENDING in rule_ids
    assert guard.RULE_MISSING_ROLE_LEVEL_RECEIPT in rule_ids


def test_multiple_violations_collected_across_children():
    rounds = [
        _round(
            children=[
                _child(
                    child_id="child-pending",
                    status="pending",
                    merge_status="",
                    proof_receipt_id="",
                    patch_disposition="",
                ),
                _child(
                    child_id="child-unmerged",
                    status="applied",
                    merge_status="",
                ),
                _child(
                    child_id="child-unproven",
                    status="applied",
                    proof_receipt_id="",
                ),
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILDREN_PENDING in rule_ids
    assert guard.RULE_CHILDREN_UNMERGED in rule_ids
    assert guard.RULE_CHILDREN_UNPROVEN in rule_ids


def test_rejected_disposition_accepted_as_typed_disposition():
    # A typed `rejected` disposition counts as a real disposition; the round
    # may still close on it provided merge/proof routing is also typed.
    rounds = [
        _round(
            children=[
                _child(
                    child_id="child-rejected",
                    status="applied",
                    patch_disposition="rejected",
                    merge_status="merged",
                    proof_receipt_id="rcpt-x",
                )
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_PATCH_DISPOSITION not in rule_ids


def test_output_schema_matches_plan_spec():
    report = guard.build_report(rounds=[], now=_NOW)
    for field in (
        "ok",
        "schema_version",
        "contract_id",
        "command",
        "timestamp",
        "freshness_window_seconds",
        "rounds_evaluated_count",
        "rounds_complete_claimed_count",
        "children_evaluated_count",
        "violation_count",
        "checked_surfaces",
        "violations",
        "warnings",
    ):
        assert field in report, f"missing required field {field!r}"


def test_render_markdown_includes_violations():
    rounds = [
        _round(
            children=[
                _child(
                    child_id="child-unmerged",
                    status="applied",
                    merge_status="",
                )
            ]
        )
    ]
    report = guard.build_report(rounds=rounds, now=_NOW)
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert guard.RULE_CHILDREN_UNMERGED in md
    assert "child-unmerged" in md


def test_render_markdown_passes_when_ok():
    report = guard.build_report(rounds=[_round()], now=_NOW)
    md = guard.render_markdown(report)
    assert "## Violations" not in md
    assert "ok: True" in md
