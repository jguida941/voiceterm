"""Dashboard-side consumers for the shared ViolationRecord adapters.

The MP-381 contract family (``runtime/check_result_models.py``) defines a
single ``ViolationRecord`` shape that every signal source can project into,
plus shared sibling adapters that map domain payloads (probe-report hints,
governance-review rows, startup-context blockers) into that shape:

- ``runtime/probe_report_violations.py``
- ``runtime/governance_review_violations.py``
- ``runtime/startup_summary_violations.py``

The dashboard data layer is the operator-facing **consumer** of those
adapters. Rather than calling each adapter at the section-builder call
site and re-implementing field flattening per panel, this module owns the
one place where ``ViolationRecord`` tuples become dashboard "cell" dicts
(the flat ``{check, status, violation, file_path, line, policy, fix,
source, severity}`` shape that the snapshot panels already consume for
the CHECKS path).

Centralizing this here keeps ``commands/dashboard_data.py`` focused on
the per-section data extraction, removes per-section duplication of the
flattening logic, and gives a single seam where cell shape can evolve
once the dashboard renderer migration to ``CheckResult`` envelopes
(deferred follow-up MP) lands.

The mapping is one-way and additive: source adapters keep their typed
``ViolationRecord`` output, dashboard panels keep their existing data
shape, and consumers see one new ``recent_violations`` field per panel.
Empty / missing source data yields an empty list so renderers can
unconditionally read the field.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..runtime.governance_review_violations import (
    governance_review_recent_to_violations,
)
from ..runtime.probe_report_violations import probe_report_to_violations

# Dashboard panels render at most this many violation rows per section
# so the snapshot stays compact for terminal/markdown surfaces. The
# CHECKS path uses the same cap (see the ``len(details) >= 10`` guard in
# the legacy ``_check_details_from_violations`` body this module replaces).
MAX_DASHBOARD_VIOLATION_ROWS = 10


def violations_to_dashboard_cells(
    violations: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> list[dict[str, str]]:
    """Flatten ViolationRecord-shaped dicts into dashboard "cell" dicts.

    Accepts the dict projection of ``ViolationRecord`` (i.e. what
    ``ViolationRecord.to_dict()`` produces, or any equivalent flat dict
    keyed by the ViolationRecord field names). Returns a list of cell
    dicts in the shape the dashboard snapshot panels already consume:

    - ``check``     <- ``step_name``
    - ``status``    <- always ``"FAIL"`` (the dashboard treats every cell
      in a ``recent_violations`` list as an actionable row regardless of
      whether the source surface considers it advisory; the panel-level
      labeling already disambiguates governance vs probes vs checks)
    - ``violation`` <- ``summary`` prefixed with ``file:line`` location
      when present and not already part of the summary text
    - optional flat fields preserved when present: ``file_path``,
      ``line``, ``policy``, ``fix``, ``source``, ``severity``

    The cap of ``MAX_DASHBOARD_VIOLATION_ROWS`` rows keeps the dashboard
    snapshot compact regardless of how many violations a single source
    surface produces.
    """
    cells: list[dict[str, str]] = []
    for record in violations:
        cells.append(_record_to_cell(record))
        if len(cells) >= MAX_DASHBOARD_VIOLATION_ROWS:
            break
    return cells


def _record_to_cell(record: Mapping[str, Any]) -> dict[str, str]:
    """Map one ViolationRecord-shaped dict into one dashboard cell dict."""
    file_path = str(record.get("file_path") or "")
    line_num = record.get("line") or ""
    location = (
        f"{file_path}:{line_num}" if file_path and line_num else file_path
    )
    violation_text = str(record.get("summary") or "")
    if location and location not in violation_text:
        violation_text = f"{location} {violation_text}".strip()

    cell: dict[str, str] = {
        "check": str(record.get("step_name") or "unknown"),
        "status": "FAIL",
        "violation": violation_text,
    }
    _copy_optional_str(cell, record, "file_path")
    if line_num:
        cell["line"] = str(line_num)
    _copy_optional_str(cell, record, "policy")
    _copy_optional_str(cell, record, "fix")
    _copy_optional_str(cell, record, "source")
    _copy_optional_str(cell, record, "severity")
    return cell


def _copy_optional_str(
    cell: dict[str, str],
    record: Mapping[str, Any],
    key: str,
) -> None:
    """Copy a non-empty string field from *record* into *cell* under *key*."""
    value = str(record.get(key) or "")
    if value:
        cell[key] = value


def audit_recent_violations(
    gov_data: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    """Return dashboard cells for the *recent* governance-review window.

    Reads the same governance-review report dict that
    ``_build_audit_section`` already loads, projects each adjudicated
    ``confirmed_issue`` row in the bounded recent window through
    ``governance_review_recent_to_violations``, and flattens the result
    into dashboard cell dicts. Empty source data yields an empty list so
    renderers can unconditionally read the field.
    """
    if not isinstance(gov_data, Mapping):
        return []
    records = governance_review_recent_to_violations(gov_data)
    return violations_to_dashboard_cells([r.to_dict() for r in records])


def probes_recent_violations(
    probe_data: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    """Return dashboard cells for the probe-report risk hints.

    Reads the same probe-report aggregate dict that
    ``_build_probes_section`` already loads, projects each enriched risk
    hint through ``probe_report_to_violations``, and flattens the result
    into dashboard cell dicts. Empty source data yields an empty list so
    renderers can unconditionally read the field.
    """
    if not isinstance(probe_data, Mapping):
        return []
    records = probe_report_to_violations(probe_data)
    return violations_to_dashboard_cells([r.to_dict() for r in records])


__all__ = [
    "MAX_DASHBOARD_VIOLATION_ROWS",
    "audit_recent_violations",
    "probes_recent_violations",
    "violations_to_dashboard_cells",
]
