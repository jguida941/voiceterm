"""Coverage / violation builders for the control-plane parity guard.

Extracted from ``field_routes_parity.py`` so the parity module fits the
Python soft file-size limit. The contract-closure aggregator only sees
the dict shape produced here; keeping the comparator helpers in their
own module also lets future parity-style guards reuse the same row
schema without taking a dependency on the fixture or extractors.
"""

from __future__ import annotations

from typing import Any, Callable

from dev.scripts.devctl.runtime.control_plane_read_model import ControlPlaneReadModel


def coverage_row(
    *,
    field: str,
    surfaces: tuple[str, ...],
    ok: bool,
    detail: str,
    observed: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Build a contract-closure-shaped coverage row for one parity field."""
    row: dict[str, object] = {
        "kind": "control_plane_parity",
        "contract_id": "ControlPlaneReadModel",
        "field_name": field,
        "surfaces": surfaces,
        "ok": ok,
        "detail": detail,
    }
    if observed is not None:
        row["observed"] = observed
    return row


def violation_row(
    *,
    field: str,
    surfaces: tuple[str, ...],
    detail: str,
    observed: dict[str, Any],
) -> dict[str, object]:
    """Build a contract-closure-shaped violation row for one parity field."""
    return {
        "kind": "control_plane_parity",
        "contract_id": "ControlPlaneReadModel",
        "field_name": field,
        "rule": "control-plane-parity-divergence",
        "surfaces": surfaces,
        "observed": observed,
        "detail": detail,
    }


def compare_parity_field(
    field: str,
    surface_values: dict[str, Any],
) -> tuple[dict[str, object], dict[str, object] | None]:
    """Return (coverage, violation_or_None) for one parity field.

    Only inspects surfaces that actually carry the field; absent surfaces
    are skipped. When two or more surfaces expose the field with
    different values, a violation is raised that names every surface and
    its observed value so an operator can locate the regression.
    """
    if not surface_values:
        return coverage_row(
            field=field,
            surfaces=(),
            ok=True,
            detail=f"No surface carries {field}; nothing to compare.",
        ), None

    surfaces = tuple(sorted(surface_values))
    distinct = {value for value in surface_values.values()}
    if len(distinct) == 1:
        return coverage_row(
            field=field,
            surfaces=surfaces,
            ok=True,
            detail=(
                f"All {len(surfaces)} surface(s) agree on {field}: "
                f"{next(iter(distinct))!r}"
            ),
            observed=dict(surface_values),
        ), None

    detail = (
        f"Surfaces disagree on ControlPlaneReadModel.{field}: "
        + ", ".join(f"{surface}={surface_values[surface]!r}" for surface in surfaces)
    )
    coverage = coverage_row(
        field=field,
        surfaces=surfaces,
        ok=False,
        detail=detail,
        observed=dict(surface_values),
    )
    violation = violation_row(
        field=field,
        surfaces=surfaces,
        detail=detail,
        observed=dict(surface_values),
    )
    return coverage, violation


def run_extractor(
    surface_id: str,
    extractor: Callable[[ControlPlaneReadModel], dict[str, Any]],
    model: ControlPlaneReadModel,
) -> tuple[dict[str, Any] | None, dict[str, object] | None]:
    """Run one extractor and convert any failure into a parity violation.

    A surface that crashes is the strongest possible parity failure: the
    parity guard's job is to keep the surfaces aligned, and an
    unrenderable surface is the most extreme form of disagreement.
    """
    try:
        return extractor(model), None
    # broad-except: allow reason=a crashing surface must become a parity violation, not a closure-aggregator crash fallback=emit control-plane-parity-extractor-error
    except Exception as exc:  # noqa: BLE001
        violation = {
            "kind": "control_plane_parity",
            "contract_id": "ControlPlaneReadModel",
            "field_name": "*",
            "rule": "control-plane-parity-extractor-error",
            "surfaces": (surface_id,),
            "detail": f"surface {surface_id!r} extractor failed: {exc}",
        }
        return None, violation
