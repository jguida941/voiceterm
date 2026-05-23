"""Tests for ``check_multi_actor_merge_conflict`` (G37)."""

from __future__ import annotations

from datetime import datetime, timezone

from dev.scripts.checks import check_multi_actor_merge_conflict as guard


_NOW = datetime(2026, 5, 22, 23, 0, 0, tzinfo=timezone.utc)
_ROW = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"


def _patch(
    *,
    patch_id: str,
    paths: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    packet_targets: tuple[str, ...] = (),
    receipt_targets: tuple[str, ...] = (),
    worktrees: tuple[str, ...] = (),
    branches: tuple[str, ...] = (),
    actor: str = "claude-child-a",
    plan_id: str = _ROW,
    target_ref: str = f"plan:{_ROW}",
) -> dict[str, object]:
    return {
        "patch_id": patch_id,
        "actor": actor,
        "plan_id": plan_id,
        "target_ref": target_ref,
        "paths": list(paths),
        "symbols": list(symbols),
        "packet_targets": list(packet_targets),
        "receipt_targets": list(receipt_targets),
        "worktrees": list(worktrees),
        "branches": list(branches),
    }


def _merge_record(
    *,
    conflict_id: str,
    child_patch_ids: tuple[str, ...],
    conflict_disposition: str = "accept_both_merged",
    merge_coordinator_id: str = "actor-reviewer-claude",
    lease_refs: tuple[str, ...] = ("lease-a", "lease-b"),
    post_merge_proof: str = "receipt-merge-001",
    plan_id: str = _ROW,
    target_ref: str = f"plan:{_ROW}",
) -> dict[str, object]:
    return {
        "conflict_id": conflict_id,
        "child_patch_ids": list(child_patch_ids),
        "conflict_disposition": conflict_disposition,
        "merge_coordinator_id": merge_coordinator_id,
        "lease_refs": list(lease_refs),
        "post_merge_proof": post_merge_proof,
        "plan_id": plan_id,
        "target_ref": target_ref,
    }


# -- Rule 1: overlapping patches with no typed disposition --


def test_red_overlapping_patches_with_no_merge_record_fails():
    # Two child patches touch the same file but no merge record exists.
    patches = [
        _patch(patch_id="p-a", paths=("dev/foo.py",)),
        _patch(patch_id="p-b", paths=("dev/foo.py", "dev/bar.py"), actor="claude-child-b"),
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=[], current_row_id=_ROW
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CONFLICTING_PATCHES_NO_DISPOSITION in rule_ids
    assert report["overlap_count"] == 1
    assert report["checked_patch_count"] == 2


def test_red_overlapping_patches_with_invalid_disposition_fails():
    patches = [
        _patch(patch_id="p-a", symbols=("foo_func",)),
        _patch(patch_id="p-b", symbols=("foo_func",), actor="claude-child-b"),
    ]
    records = [
        _merge_record(
            conflict_id="c-1",
            child_patch_ids=("p-a", "p-b"),
            conflict_disposition="ad_hoc_chat_decision",  # not in vocabulary
        )
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=records, current_row_id=_ROW
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CONFLICTING_PATCHES_NO_DISPOSITION in rule_ids


def test_green_overlapping_patches_with_supported_disposition_passes():
    patches = [
        _patch(patch_id="p-a", paths=("dev/foo.py",)),
        _patch(patch_id="p-b", paths=("dev/foo.py",), actor="claude-child-b"),
    ]
    records = [
        _merge_record(
            conflict_id="c-1",
            child_patch_ids=("p-a", "p-b"),
            conflict_disposition="accept_a_reject_b",
        )
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=records, current_row_id=_ROW
    )
    assert report["ok"] is True
    assert report["violations"] == []
    assert report["overlap_count"] == 1


def test_green_non_overlapping_patches_need_no_record():
    patches = [
        _patch(patch_id="p-a", paths=("dev/foo.py",)),
        _patch(patch_id="p-b", paths=("dev/bar.py",), actor="claude-child-b"),
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=[], current_row_id=_ROW
    )
    assert report["ok"] is True
    assert report["overlap_count"] == 0


# -- Rule 2: missing merge_coordinator_id on a typed record --


def test_red_record_without_merge_coordinator_id_fails():
    patches = [
        _patch(patch_id="p-a", receipt_targets=("rec-1",)),
        _patch(patch_id="p-b", receipt_targets=("rec-1",), actor="claude-child-b"),
    ]
    records = [
        _merge_record(
            conflict_id="c-2",
            child_patch_ids=("p-a", "p-b"),
            merge_coordinator_id="",
        )
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=records, current_row_id=_ROW
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_MERGE_COORDINATOR_ID in rule_ids


# -- Rule 3: missing lease_refs --


def test_red_record_without_lease_refs_fails():
    patches = [
        _patch(patch_id="p-a", packet_targets=("pkt-1",)),
        _patch(patch_id="p-b", packet_targets=("pkt-1",), actor="claude-child-b"),
    ]
    records = [
        _merge_record(
            conflict_id="c-3",
            child_patch_ids=("p-a", "p-b"),
            lease_refs=(),
        )
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=records, current_row_id=_ROW
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_LEASE_REFS in rule_ids


# -- Rule 4: missing post_merge_proof --


def test_red_record_without_post_merge_proof_fails():
    patches = [
        _patch(patch_id="p-a", branches=("feat/x",)),
        _patch(patch_id="p-b", branches=("feat/x",), actor="claude-child-b"),
    ]
    records = [
        _merge_record(
            conflict_id="c-4",
            child_patch_ids=("p-a", "p-b"),
            post_merge_proof="",
        )
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=records, current_row_id=_ROW
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_POST_MERGE_PROOF in rule_ids


def test_red_record_missing_all_three_typed_fields_reports_each():
    # A record with a supported disposition but everything else blank must
    # surface all three downstream rule violations.
    patches = [
        _patch(patch_id="p-a", worktrees=("wt-1",)),
        _patch(patch_id="p-b", worktrees=("wt-1",), actor="claude-child-b"),
    ]
    records = [
        _merge_record(
            conflict_id="c-5",
            child_patch_ids=("p-a", "p-b"),
            merge_coordinator_id="",
            lease_refs=(),
            post_merge_proof="",
        )
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=records, current_row_id=_ROW
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_MERGE_COORDINATOR_ID in rule_ids
    assert guard.RULE_MISSING_LEASE_REFS in rule_ids
    assert guard.RULE_MISSING_POST_MERGE_PROOF in rule_ids
    # And the typed disposition is supported so Rule 1 must NOT also fire.
    assert guard.RULE_CONFLICTING_PATCHES_NO_DISPOSITION not in rule_ids


# -- Scope / matching --


def test_row_filter_skips_other_rows():
    other_row = "MP-OTHER-ROW-S1"
    patches = [
        _patch(
            patch_id="p-a",
            paths=("dev/foo.py",),
            plan_id=other_row,
            target_ref=f"plan:{other_row}",
        ),
        _patch(
            patch_id="p-b",
            paths=("dev/foo.py",),
            actor="claude-child-b",
            plan_id=other_row,
            target_ref=f"plan:{other_row}",
        ),
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=[], current_row_id=_ROW
    )
    assert report["ok"] is True
    assert report["checked_patch_count"] == 0
    assert report["overlap_count"] == 0


def test_record_matching_by_subset_of_child_patch_ids():
    # The record's child_patch_ids may include a third superseding patch;
    # the overlap pair {p-a, p-b} should still resolve to this record.
    patches = [
        _patch(patch_id="p-a", paths=("dev/foo.py",)),
        _patch(patch_id="p-b", paths=("dev/foo.py",), actor="claude-child-b"),
    ]
    records = [
        _merge_record(
            conflict_id="c-6",
            child_patch_ids=("p-a", "p-b", "p-c-supersede"),
            conflict_disposition="supersede_by_third_patch",
        )
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=records, current_row_id=_ROW
    )
    assert report["ok"] is True
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CONFLICTING_PATCHES_NO_DISPOSITION not in rule_ids


def test_overlap_fields_record_each_distinct_field():
    patches = [
        _patch(
            patch_id="p-a",
            paths=("dev/foo.py",),
            symbols=("foo_func",),
        ),
        _patch(
            patch_id="p-b",
            paths=("dev/foo.py",),
            symbols=("foo_func",),
            actor="claude-child-b",
        ),
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=[], current_row_id=_ROW
    )
    assert report["ok"] is False
    violations = report["violations"]
    overlap_fields = set(violations[0]["overlap_fields"])
    assert "paths" in overlap_fields
    assert "symbols" in overlap_fields


# -- Rendering / boundary --


def test_render_markdown_includes_violations():
    patches = [
        _patch(patch_id="p-a", paths=("dev/foo.py",)),
        _patch(patch_id="p-b", paths=("dev/foo.py",), actor="claude-child-b"),
    ]
    report = guard.build_report(
        child_patches=patches, merge_records=[], current_row_id=_ROW
    )
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert guard.RULE_CONFLICTING_PATCHES_NO_DISPOSITION in md
    assert guard.DISPLAY_TEXT in md
    assert "violation_count" in md


def test_unknown_merge_state_path_emits_warning():
    from pathlib import Path

    missing = Path("/tmp/nonexistent-multi-actor-merge-state.json")
    report = guard.build_report(merge_state_path=missing, current_row_id=_ROW)
    assert report["ok"] is True
    assert any(
        "merge state missing" in str(w).lower() for w in report["warnings"]
    )


def test_clean_empty_inputs_passes():
    report = guard.build_report(
        child_patches=[], merge_records=[], current_row_id=_ROW
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["overlap_count"] == 0
