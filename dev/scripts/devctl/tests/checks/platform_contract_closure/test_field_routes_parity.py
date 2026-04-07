"""Tests for the control-plane parity guard (MP-381 Priority 3).

The parity guard renders one deterministic ``ControlPlaneReadModel``
fixture through every governance surface (dashboard, auto-mode,
session-resume, phone, mobile) and fails if any surface disagrees on the
target parity fields. These tests pin the contract end-to-end:

* the fixture has values for every parity field,
* the live extractors agree on the fixture,
* the comparator actually flags divergence (so the guard would catch a
  silent recomputation regression),
* the phone surface refactor keeps the pure projection equivalent to the
  disk-driven projection.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from dev.scripts.checks.platform_contract_closure.field_routes_parity import (
    PARITY_FIELDS,
    _extract_from_auto_mode,
    _extract_from_dashboard,
    _extract_from_mobile,
    _extract_from_phone,
    _extract_from_session_resume,
    _fixture_read_model,
    run_parity_checks,
)
from dev.scripts.devctl.commands.phone_status import (
    _build_control_plane_section,
    _control_plane_section,
)
from dev.scripts.devctl.runtime.control_plane_read_model import ControlPlaneReadModel


def _model_field_value(model: ControlPlaneReadModel, field: str) -> Any:
    """Return the parity-field value the comparator expects for *field*."""
    return getattr(model, field)


def test_parity_fixture_has_all_target_fields() -> None:
    """Every parity field must have a non-default value on the fixture.

    Guards against forgetting to set a field when extending
    ``PARITY_FIELDS``: the comparator can only catch divergence on
    fields that actually carry distinct fixture values.
    """
    model = _fixture_read_model()
    for field in PARITY_FIELDS:
        assert hasattr(model, field), f"fixture missing parity field {field!r}"
        value = getattr(model, field)
        # Booleans are allowed; the regression test only needs *some*
        # value the extractors can echo back deterministically.
        assert value is not None, f"fixture parity field {field!r} is None"


def test_all_five_surfaces_agree_on_parity_fields() -> None:
    """Running the full parity check on the fixture must yield zero violations."""
    results = run_parity_checks()
    assert results, "parity check returned no rows"

    violations = [violation for _, violation in results if violation is not None]
    assert violations == [], (
        "control-plane parity guard reported violations on the fixture: "
        f"{violations}"
    )

    # Every parity field must show up at least once in the coverage rows so
    # we know the comparator actually evaluated each one.
    covered_fields = {
        row["field_name"]
        for row, _ in results
        if isinstance(row, dict) and row.get("kind") == "control_plane_parity"
    }
    for field in PARITY_FIELDS:
        assert field in covered_fields, (
            f"parity field {field!r} was not exercised by run_parity_checks()"
        )


def test_each_extractor_returns_fixture_values() -> None:
    """Pin each extractor to the fixture: every returned key must echo the model.

    This is the per-surface assertion the cross-surface comparator
    relies on. If any surface starts mutating the value before exposing
    it, the comparator's "all agree" branch can no longer fire.
    """
    model = _fixture_read_model()

    for extractor in (
        _extract_from_dashboard,
        _extract_from_auto_mode,
        _extract_from_session_resume,
        _extract_from_phone,
        _extract_from_mobile,
    ):
        output = extractor(model)
        for field, value in output.items():
            assert value == _model_field_value(model, field), (
                f"{extractor.__name__} surfaced {field}={value!r} "
                f"but the fixture model carries {_model_field_value(model, field)!r}"
            )


def test_parity_guard_detects_divergence() -> None:
    """A perturbed surface must produce a parity violation naming the field.

    Constructs an extractor override that flips ``top_blocker`` for the
    phone surface only. The comparator must surface a violation that
    names both the field and the disagreeing surface so an operator can
    immediately locate the regression.
    """
    model = _fixture_read_model()

    def _perturbed_phone_extractor(_: ControlPlaneReadModel) -> dict[str, Any]:
        # Mirror the live phone extractor but corrupt one field. Using
        # the real extractor as the baseline keeps every other field in
        # parity so the only divergence the comparator can flag is
        # ``top_blocker``.
        baseline = _extract_from_phone(model)
        baseline["top_blocker"] = "perturbed_phone_top_blocker"
        return baseline

    results = run_parity_checks(
        extractor_overrides={"phone": _perturbed_phone_extractor},
    )
    violations = [v for _, v in results if v is not None]
    assert violations, "parity guard did not detect injected top_blocker divergence"

    top_blocker_violations = [
        v for v in violations
        if v.get("field_name") == "top_blocker"
        and v.get("rule") == "control-plane-parity-divergence"
    ]
    assert len(top_blocker_violations) == 1, (
        "expected exactly one top_blocker divergence violation, "
        f"got {top_blocker_violations}"
    )

    violation = top_blocker_violations[0]
    observed = violation["observed"]
    assert "phone" in observed, "violation must name the disagreeing phone surface"
    assert observed["phone"] == "perturbed_phone_top_blocker", (
        "violation must echo the perturbed value so operators can locate the regression"
    )
    # At least one other surface must remain on the fixture value so the
    # comparator's divergence detection is genuine, not a single-surface row.
    other_surfaces = {key: value for key, value in observed.items() if key != "phone"}
    assert other_surfaces, "divergence test needs at least one healthy surface"
    assert any(
        value == "parity_fixture_top_blocker" for value in other_surfaces.values()
    ), "at least one healthy surface must echo the fixture top_blocker"


def test_parity_guard_reports_extractor_crash() -> None:
    """An extractor that raises must become a parity violation, not a crash.

    Pins the broad-except wrapper inside ``_run_extractor`` so a
    surface that fails to render is treated as the strongest possible
    parity failure rather than blowing up the platform-contract-closure
    aggregator.
    """

    def _broken_dashboard(_: ControlPlaneReadModel) -> dict[str, Any]:
        raise RuntimeError("dashboard surface intentionally broken for parity test")

    results = run_parity_checks(
        extractor_overrides={"dashboard": _broken_dashboard},
    )
    violations = [v for _, v in results if v is not None]
    extractor_errors = [
        v for v in violations
        if v.get("rule") == "control-plane-parity-extractor-error"
    ]
    assert len(extractor_errors) == 1
    assert "dashboard" in extractor_errors[0]["surfaces"]
    assert "intentionally broken" in extractor_errors[0]["detail"]


def test_phone_pure_function_matches_disk_function(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The phone refactor must keep the pure projection equivalent to the disk path.

    The disk-based ``_build_control_plane_section`` is now a thin wrapper
    around ``build_control_plane_read_model`` plus the pure
    ``_control_plane_section``. This test patches the loader to return
    the deterministic fixture and proves both layers produce the same
    dict shape and values for the parity-relevant fields.
    """
    fixture = _fixture_read_model()

    monkeypatch.setattr(
        "dev.scripts.devctl.commands.phone_status.build_control_plane_read_model",
        lambda repo_root: fixture,
    )

    pure = _control_plane_section(fixture)
    disk = _build_control_plane_section(tmp_path)

    assert pure == disk, (
        "phone _control_plane_section pure projection diverged from "
        "the disk-driven _build_control_plane_section wrapper"
    )

    # The dict must contain every parity field the guard inspects.
    for field in PARITY_FIELDS:
        if field == "implementation_blocked":
            # phone surface intentionally omits implementation_blocked;
            # the comparator skips absent fields, so this is fine.
            continue
        assert field in pure, (
            f"phone _control_plane_section is missing parity field {field!r}"
        )
