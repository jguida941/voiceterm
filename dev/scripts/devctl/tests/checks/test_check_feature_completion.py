from dev.scripts.checks import check_feature_completion as guard


def test_new_cataloged_guard_without_completion_wiring_fails() -> None:
    path = "dev/scripts/checks/check_new_guard.py"

    report = guard.build_report(
        git_status_output=f"?? {path}\n",
        registered_check_paths=frozenset({path}),
        bundled_check_paths=frozenset(),
        quality_check_paths=frozenset(),
        router_mapped_paths=frozenset(),
        existing_paths=frozenset({path}),
        source_text_by_path={path: "print('no machine reasons here')"},
    )

    reasons = {violation["reason"] for violation in report["violations"]}
    assert "feature_guard_missing_focused_test" in reasons
    assert "feature_guard_missing_router_mapping" in reasons
    assert "feature_guard_missing_quality_step" in reasons
    assert "feature_guard_missing_execution_path" in reasons
    assert "feature_guard_missing_failure_reason" in reasons


def test_new_uncataloged_guard_is_still_a_completion_failure() -> None:
    path = "dev/scripts/checks/check_unregistered_guard.py"

    report = guard.build_report(
        git_status_output=f"?? {path}\n",
        registered_check_paths=frozenset(),
        bundled_check_paths=frozenset({path}),
        quality_check_paths=frozenset({path}),
        router_mapped_paths=frozenset({path}),
        existing_paths=frozenset(
            {
                path,
                "dev/scripts/devctl/tests/checks/test_check_unregistered_guard.py",
            }
        ),
        source_text_by_path={path: 'reason="machine_readable_reason"'},
    )

    reasons = {violation["reason"] for violation in report["violations"]}
    assert "feature_guard_not_cataloged" in reasons


def test_new_guard_with_complete_wiring_passes() -> None:
    path = "dev/scripts/checks/check_new_guard.py"

    report = guard.build_report(
        git_status_output=f"?? {path}\n",
        registered_check_paths=frozenset({path}),
        bundled_check_paths=frozenset({path}),
        quality_check_paths=frozenset({path}),
        router_mapped_paths=frozenset(
            {
                path,
                "dev/scripts/devctl/tests/checks/test_check_new_guard.py",
            }
        ),
        existing_paths=frozenset(
            {
                path,
                "dev/scripts/devctl/tests/checks/test_check_new_guard.py",
            }
        ),
        source_text_by_path={path: 'reason="machine_readable_reason"'},
    )

    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_shim_guard_can_delegate_failure_reason_to_target_source() -> None:
    path = "dev/scripts/checks/check_shim_guard.py"
    target = "dev/scripts/checks/shim_guard/command.py"

    report = guard.build_report(
        git_status_output=f"?? {path}\n",
        registered_check_paths=frozenset({path}),
        bundled_check_paths=frozenset({path}),
        quality_check_paths=frozenset({path}),
        router_mapped_paths=frozenset(
            {
                path,
                "dev/scripts/devctl/tests/checks/test_check_shim_guard.py",
            }
        ),
        existing_paths=frozenset(
            {
                path,
                "dev/scripts/devctl/tests/checks/test_check_shim_guard.py",
            }
        ),
        source_text_by_path={
            path: f"# shim-target: {target}\n",
            target: 'reason="delegated_machine_reason"',
        },
    )

    assert report["ok"] is True


def test_live_bundle_membership_reader_sees_registered_guard() -> None:
    assert "dev/scripts/checks/check_feature_completion.py" in guard._bundled_check_paths()
