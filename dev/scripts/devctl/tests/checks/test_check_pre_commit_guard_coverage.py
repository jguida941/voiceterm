from pathlib import Path

from dev.scripts.checks import check_pre_commit_guard_coverage as guard


def test_live_pre_commit_hook_contains_role_lane_pre_mutation() -> None:
    hook_path = Path(".git/hooks/pre-commit")

    report = guard.build_report(hook_path=hook_path)
    checks = {
        str(check["guard_id"]): check
        for check in report["checks"]
        if isinstance(check, dict)
    }

    assert report["ok"] is True
    assert checks["check_role_lane_mutation_authority"]["status"] == "ok"
    assert (
        "check_role_lane_mutation_authority.py --mode pre_mutation"
        in checks["check_role_lane_mutation_authority"]["matched_text"]
    )


def test_missing_future_guards_are_expected_pending_until_built(tmp_path: Path) -> None:
    hook_path = tmp_path / "pre-commit"
    hook_path.write_text(
        "#!/bin/sh\n"
        "python3 dev/scripts/checks/check_role_lane_mutation_authority.py "
        "--mode pre_mutation --format md\n",
        encoding="utf-8",
    )

    report = guard.build_report(hook_path=hook_path)
    checks = {
        str(check["guard_id"]): check
        for check in report["checks"]
        if isinstance(check, dict)
    }

    assert report["ok"] is True
    assert checks["check_current_plan_authority"]["status"] == "expected_pending"
    assert checks["check_orphan_files"]["status"] == "expected_pending"
