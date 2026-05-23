"""Tests for `check_patch_submission_merge_gate` (A18 G36)."""

from __future__ import annotations

from dev.scripts.checks import check_patch_submission_merge_gate as guard


def _child_output_event(
    *,
    child_actor_id: str = "codex-child-A",
    parent_role_coordinator_id: str = "claude-parent",
    patch_id: str = "patch-001",
    target_ref: str = "plan:MP-ROW-A",
    plan_id: str = "MP-ROW-A",
) -> dict[str, object]:
    return {
        "event_type": guard.CHILD_OUTPUT_EVENT_TYPE,
        "event_id": f"evt-output-{patch_id}",
        "child_actor_id": child_actor_id,
        "parent_role_coordinator_id": parent_role_coordinator_id,
        "patch_id": patch_id,
        "target_ref": target_ref,
        "plan_id": plan_id,
    }


def _merge_gate_event(
    *,
    event_type: str,
    child_actor_id: str = "codex-child-A",
    parent_role_coordinator_id: str = "claude-parent",
    patch_id: str = "patch-001",
    suffix: str = "1",
) -> dict[str, object]:
    return {
        "event_type": event_type,
        "event_id": f"evt-{event_type}-{patch_id}-{suffix}",
        "child_actor_id": child_actor_id,
        "parent_role_coordinator_id": parent_role_coordinator_id,
        "patch_id": patch_id,
    }


def _full_merge_gate_events(
    *,
    child_actor_id: str = "codex-child-A",
    parent_role_coordinator_id: str = "claude-parent",
    patch_id: str = "patch-001",
) -> list[dict[str, object]]:
    return [
        _merge_gate_event(
            event_type=guard.PATCH_SUBMISSION_EVENT_TYPE,
            child_actor_id=child_actor_id,
            parent_role_coordinator_id=parent_role_coordinator_id,
            patch_id=patch_id,
        ),
        _merge_gate_event(
            event_type=guard.CONFLICT_CHECK_EVENT_TYPE,
            child_actor_id=child_actor_id,
            parent_role_coordinator_id=parent_role_coordinator_id,
            patch_id=patch_id,
        ),
        _merge_gate_event(
            event_type=guard.COMBINED_PROOF_EVENT_TYPE,
            child_actor_id=child_actor_id,
            parent_role_coordinator_id=parent_role_coordinator_id,
            patch_id=patch_id,
        ),
        _merge_gate_event(
            event_type=guard.ROLE_LEVEL_RESULT_EVENT_TYPE,
            child_actor_id=child_actor_id,
            parent_role_coordinator_id=parent_role_coordinator_id,
            patch_id=patch_id,
        ),
    ]


def test_full_merge_gate_chain_passes():
    events: list[dict[str, object]] = [
        _child_output_event(patch_id="patch-001"),
        *_full_merge_gate_events(patch_id="patch-001"),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["checked_child_output_count"] == 1
    assert report["patch_submission_event_count"] == 1
    assert report["conflict_check_event_count"] == 1
    assert report["combined_proof_event_count"] == 1
    assert report["role_level_result_event_count"] == 1


def test_child_output_without_parent_coordinator_fails():
    events = [
        _child_output_event(
            child_actor_id="codex-child-bypass",
            parent_role_coordinator_id="",
            patch_id="patch-bypass",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    assert report["violation_count"] == 1
    violation = report["violations"][0]
    assert violation["rule_id"] == guard.RULE_CHILD_OUTPUT_BYPASSED_PARENT
    assert violation["child_actor_id"] == "codex-child-bypass"


def test_missing_patch_submission_receipt_fails():
    events: list[dict[str, object]] = [
        _child_output_event(patch_id="patch-002"),
        _merge_gate_event(
            event_type=guard.CONFLICT_CHECK_EVENT_TYPE,
            patch_id="patch-002",
        ),
        _merge_gate_event(
            event_type=guard.COMBINED_PROOF_EVENT_TYPE,
            patch_id="patch-002",
        ),
        _merge_gate_event(
            event_type=guard.ROLE_LEVEL_RESULT_EVENT_TYPE,
            patch_id="patch-002",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_PATCH_SUBMISSION_RECEIPT in rule_ids


def test_missing_conflict_check_fails():
    events: list[dict[str, object]] = [
        _child_output_event(patch_id="patch-003"),
        _merge_gate_event(
            event_type=guard.PATCH_SUBMISSION_EVENT_TYPE,
            patch_id="patch-003",
        ),
        _merge_gate_event(
            event_type=guard.COMBINED_PROOF_EVENT_TYPE,
            patch_id="patch-003",
        ),
        _merge_gate_event(
            event_type=guard.ROLE_LEVEL_RESULT_EVENT_TYPE,
            patch_id="patch-003",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_CONFLICT_CHECK in rule_ids


def test_missing_combined_proof_fails():
    events: list[dict[str, object]] = [
        _child_output_event(patch_id="patch-004"),
        _merge_gate_event(
            event_type=guard.PATCH_SUBMISSION_EVENT_TYPE,
            patch_id="patch-004",
        ),
        _merge_gate_event(
            event_type=guard.CONFLICT_CHECK_EVENT_TYPE,
            patch_id="patch-004",
        ),
        _merge_gate_event(
            event_type=guard.ROLE_LEVEL_RESULT_EVENT_TYPE,
            patch_id="patch-004",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_COMBINED_PROOF in rule_ids


def test_missing_role_level_result_fails():
    events: list[dict[str, object]] = [
        _child_output_event(patch_id="patch-005"),
        _merge_gate_event(
            event_type=guard.PATCH_SUBMISSION_EVENT_TYPE,
            patch_id="patch-005",
        ),
        _merge_gate_event(
            event_type=guard.CONFLICT_CHECK_EVENT_TYPE,
            patch_id="patch-005",
        ),
        _merge_gate_event(
            event_type=guard.COMBINED_PROOF_EVENT_TYPE,
            patch_id="patch-005",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_ROLE_LEVEL_RESULT in rule_ids


def test_all_four_artifacts_missing_yields_four_violations():
    events = [_child_output_event(patch_id="patch-006")]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_PATCH_SUBMISSION_RECEIPT in rule_ids
    assert guard.RULE_MISSING_CONFLICT_CHECK in rule_ids
    assert guard.RULE_MISSING_COMBINED_PROOF in rule_ids
    assert guard.RULE_MISSING_ROLE_LEVEL_RESULT in rule_ids


def test_mismatched_parent_coordinator_does_not_satisfy_receipt():
    events: list[dict[str, object]] = [
        _child_output_event(
            patch_id="patch-007",
            parent_role_coordinator_id="claude-parent",
        ),
        _merge_gate_event(
            event_type=guard.PATCH_SUBMISSION_EVENT_TYPE,
            patch_id="patch-007",
            parent_role_coordinator_id="other-parent",
        ),
        _merge_gate_event(
            event_type=guard.CONFLICT_CHECK_EVENT_TYPE,
            patch_id="patch-007",
            parent_role_coordinator_id="other-parent",
        ),
        _merge_gate_event(
            event_type=guard.COMBINED_PROOF_EVENT_TYPE,
            patch_id="patch-007",
            parent_role_coordinator_id="other-parent",
        ),
        _merge_gate_event(
            event_type=guard.ROLE_LEVEL_RESULT_EVENT_TYPE,
            patch_id="patch-007",
            parent_role_coordinator_id="other-parent",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_PATCH_SUBMISSION_RECEIPT in rule_ids
    assert guard.RULE_MISSING_CONFLICT_CHECK in rule_ids
    assert guard.RULE_MISSING_COMBINED_PROOF in rule_ids
    assert guard.RULE_MISSING_ROLE_LEVEL_RESULT in rule_ids


def test_multiple_children_each_get_their_own_merge_gate():
    events: list[dict[str, object]] = [
        _child_output_event(
            child_actor_id="codex-child-A",
            patch_id="patch-A",
        ),
        _child_output_event(
            child_actor_id="codex-child-B",
            patch_id="patch-B",
        ),
        *_full_merge_gate_events(
            child_actor_id="codex-child-A",
            patch_id="patch-A",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    bypassed_children = {
        v["child_actor_id"]
        for v in report["violations"]
    }
    assert "codex-child-B" in bypassed_children
    assert "codex-child-A" not in bypassed_children


def test_row_id_filter_excludes_other_rows():
    events: list[dict[str, object]] = [
        _child_output_event(
            patch_id="patch-other",
            target_ref="plan:OTHER-ROW",
            plan_id="OTHER-ROW",
        ),
    ]
    report = guard.build_report(events=events, row_id_filter="MP-ROW-FILTERED")
    assert report["ok"] is True
    assert report["checked_child_output_count"] == 0


def test_row_id_filter_includes_matching_row():
    events: list[dict[str, object]] = [
        _child_output_event(
            patch_id="patch-filtered",
            target_ref="plan:MP-ROW-FILTERED",
            plan_id="MP-ROW-FILTERED",
        ),
    ]
    report = guard.build_report(
        events=events, row_id_filter="MP-ROW-FILTERED"
    )
    assert report["ok"] is False
    assert report["checked_child_output_count"] == 1


def test_child_actor_id_filter_limits_proof_scope():
    events: list[dict[str, object]] = [
        _child_output_event(
            child_actor_id="codex-child-active",
            patch_id="patch-active",
        ),
        _child_output_event(
            child_actor_id="codex-child-stale",
            patch_id="patch-stale",
        ),
    ]
    report = guard.build_report(
        events=events, child_actor_ids=("codex-child-active",)
    )
    assert report["ok"] is False
    assert report["checked_child_actor_ids"] == ["codex-child-active"]
    assert report["checked_child_output_count"] == 1


def test_child_actor_id_filter_deduplicates_empty_values():
    events = [_child_output_event(child_actor_id="codex-child-X")]
    report = guard.build_report(
        events=events,
        child_actor_ids=("", "codex-child-X", "codex-child-X"),
    )
    assert report["child_actor_ids"] == ["codex-child-X"]


def test_no_child_outputs_passes_with_zero_checks():
    events = [
        _merge_gate_event(
            event_type=guard.PATCH_SUBMISSION_EVENT_TYPE,
            patch_id="patch-orphan",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is True
    assert report["checked_child_output_count"] == 0


def test_render_markdown_includes_violations():
    events = [
        _child_output_event(
            child_actor_id="codex-child-render",
            parent_role_coordinator_id="",
            patch_id="patch-render",
        ),
    ]
    report = guard.build_report(events=events)
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert "codex-child-render" in md
    assert guard.RULE_CHILD_OUTPUT_BYPASSED_PARENT in md


def test_output_schema_matches_spec():
    report = guard.build_report(events=[])
    for field in (
        "ok",
        "contract_id",
        "command",
        "checked_child_output_count",
        "patch_submission_event_count",
        "conflict_check_event_count",
        "combined_proof_event_count",
        "role_level_result_event_count",
        "violation_count",
        "violations",
        "warnings",
    ):
        assert field in report, f"missing required field {field!r}"
    assert report["contract_id"] == "PatchSubmissionMergeGateGuard"
    assert report["command"] == "check_patch_submission_merge_gate"
