from dev.scripts.checks import check_orphan_files as guard


def test_new_scenario_test_without_router_mapping_fails() -> None:
    report = guard.build_report(
        git_status_output="?? dev/scripts/devctl/tests/scenarios/test_half_built.py\n",
        registered_check_paths=frozenset(),
        bundled_check_paths=frozenset(),
        quality_check_paths=frozenset(),
        router_mapped_paths=frozenset(),
    )

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "orphan_test_not_mapped"


def test_new_check_without_catalog_bundle_quality_or_router_fails() -> None:
    path = "dev/scripts/checks/check_new_guard.py"

    report = guard.build_report(
        git_status_output=f"?? {path}\n",
        registered_check_paths=frozenset(),
        bundled_check_paths=frozenset(),
        quality_check_paths=frozenset(),
        router_mapped_paths=frozenset(),
    )

    reasons = {violation["reason"] for violation in report["violations"]}
    assert "orphan_check_not_registered" in reasons
    assert "orphan_check_not_bundled" in reasons
    assert "orphan_check_not_quality_routed" in reasons
    assert "orphan_check_without_focused_test_mapping" in reasons


def test_new_check_with_all_required_wiring_passes() -> None:
    path = "dev/scripts/checks/check_new_guard.py"

    report = guard.build_report(
        git_status_output=f"?? {path}\n",
        registered_check_paths=frozenset({path}),
        bundled_check_paths=frozenset({path}),
        quality_check_paths=frozenset({path}),
        router_mapped_paths=frozenset({path}),
    )

    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_live_bundle_membership_reader_sees_registered_guard() -> None:
    assert "dev/scripts/checks/check_orphan_files.py" in guard._bundled_check_paths()
