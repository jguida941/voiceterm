from dataclasses import asdict

from dev.scripts.devctl.runtime.master_plan_contract import PlanRow


def _row(**overrides: object) -> PlanRow:
    values = {
        "row_id": "MP-NEW-P220-PHASE-0C-COMMIT-ANCHOR-REF-S1",
        "title": "Add commit_anchor_ref",
        "status": "queued",
        "sdlc_stage": "impl",
    }
    values.update(overrides)
    return PlanRow(**values)


def test_plan_row_with_empty_commit_anchor_ref_is_valid_for_backward_compat() -> None:
    row = _row(commit_anchor_ref="")

    assert row.commit_anchor_ref == ""


def test_applied_status_without_commit_anchor_ref_fails_new_validator() -> None:
    from dev.scripts.devctl.runtime.master_plan_contract import (
        validate_plan_row_commit_anchor_ref,
    )

    row = _row(status="applied")
    report = validate_plan_row_commit_anchor_ref(row)

    assert report.ok is False
    assert report.violations[0].reason == "applied_row_missing_commit_anchor_ref"


def test_plan_row_to_dict_round_trips_commit_anchor_ref_field() -> None:
    row = _row(commit_anchor_ref="commit:52f7c49f")
    payload = row.to_dict()

    assert payload["commit_anchor_ref"] == "commit:52f7c49f"
    assert asdict(row)["commit_anchor_ref"] == "commit:52f7c49f"


def test_hydrate_commit_anchor_ref_called_on_status_applied_transition() -> None:
    from dev.scripts.devctl.commands.development.plan_intake import (
        hydrate_commit_anchor_ref_for_applied_row,
    )

    row = _row(status="applied", anchor_refs=("commit:52f7c49f",))
    hydrated = hydrate_commit_anchor_ref_for_applied_row(row)

    assert hydrated.commit_anchor_ref == "commit:52f7c49f"
