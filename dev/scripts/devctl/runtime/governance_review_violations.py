"""Adapter mapping *recent* governance-review findings into ViolationRecord.

``devctl governance-review`` emits a typed report whose
``recent_findings`` list carries a *bounded* window of adjudicated
finding rows built by
``dev.scripts.devctl.governance_review_log.build_governance_review_row``.
That window is explicitly recent-only: ``build_governance_review_report``
slices ``recent_findings`` to the last ``recent_limit`` rows (default
10) out of the full review log, so this adapter projects the **recent**
governance window into ViolationRecord, not the full set of currently
open governance findings.

That distinction matters. Downstream shared-renderer consumers should
treat this output as "recent governance activity" rather than a
canonical live-governance feed; unresolved ``confirmed_issue`` rows
older than the recent window are intentionally NOT in the source
payload and will not appear in the ViolationRecord tuple. If a
consumer needs an all-open view of governance findings, it must either
call this adapter with a larger ``recent_limit`` upstream or wire a
separate all-open governance data source (out of scope for this
helper).

Field semantics and filtering are the same regardless of how large the
recent window is: each row carries a ``verdict`` from the closed set
``{confirmed_issue, false_positive, fixed, waived, deferred, unknown}``,
and the default include set is ``("confirmed_issue",)`` because only
those rows represent a currently tracked violation the operator should
see. Callers that want a historical recent-window view across more
verdicts can pass their own include tuple.

The mapping is one-way and non-mutating: governance-review keeps its
own JSON/markdown output shape, nothing in the governance-review write
path changes, and the shared contract only gains a new consumer.
"""

from __future__ import annotations

from typing import Any, Mapping

from .check_result_models import ViolationRecord
from .violation_adapter_support import (
    build_bounded_summary,
    coerce_positive_int,
    coerce_stripped_str,
)

DEFAULT_INCLUDE_VERDICTS: tuple[str, ...] = ("confirmed_issue",)


def governance_review_recent_to_violations(
    report: Mapping[str, Any],
    *,
    include_verdicts: tuple[str, ...] = DEFAULT_INCLUDE_VERDICTS,
) -> tuple[ViolationRecord, ...]:
    """Convert the *recent* governance-review window into ViolationRecord tuples.

    Reads ``report["recent_findings"]`` (the bounded recent window
    produced by ``build_governance_review_report``, sliced to the last
    ``recent_limit`` adjudicated rows) and maps each row whose
    ``verdict`` is in *include_verdicts* into a ``ViolationRecord``.
    Non-dict entries and rows with an unaccepted verdict are silently
    skipped so a malformed or resolved row cannot break the mapping.

    This helper is explicitly scoped to the **recent** window. It is
    not a live-governance feed: ``confirmed_issue`` rows older than
    the recent window are not in the source payload and will not
    appear here. Consumers that need the full open set must widen the
    source upstream or use a different governance data source.
    """
    findings = report.get("recent_findings") or []
    if not isinstance(findings, list):
        return ()
    accepted = frozenset(include_verdicts)
    return tuple(
        _row_to_violation(row)
        for row in findings
        if isinstance(row, Mapping)
        and coerce_stripped_str(row.get("verdict")) in accepted
    )


def _row_to_violation(row: Mapping[str, Any]) -> ViolationRecord:
    """Map one adjudicated governance-review row into a ViolationRecord.

    Field map:

    - ``step_name`` <- ``check_id`` (the check that flagged the finding)
    - ``exit_code`` <- ``0`` (adjudicated rows are not subprocess exit
      codes; the presence of a ViolationRecord is the finding signal)
    - ``summary``   <- first non-empty line of ``notes`` truncated to
      120 chars, or a compact ``check_id: finding_class`` /
      ``check_id: signal_type`` fallback when the reviewer did not
      write free-form notes
    - ``file_path`` <- ``file_path``
    - ``line``      <- ``line`` (or 0 when absent)
    - ``policy``    <- ``prevention_surface`` (the guardrail category
      the reviewer assigned to the finding)
    - ``fix``       <- ``notes`` (full reviewer commentary; summary
      holds the compact form, fix preserves the paragraph)
    - ``source``    <- ``source_command`` if present, otherwise
      ``signal_type``, otherwise the literal ``governance-review``
    - ``severity``  <- ``severity``
    """
    check_id = coerce_stripped_str(row.get("check_id"))
    notes = coerce_stripped_str(row.get("notes"))
    finding_class = coerce_stripped_str(row.get("finding_class"))
    signal_type = coerce_stripped_str(row.get("signal_type"))

    return ViolationRecord(
        step_name=check_id,
        exit_code=0,
        summary=build_bounded_summary(
            primary_text=notes,
            fallback_labels=(finding_class, signal_type),
            prefix=f"{check_id}: " if check_id else "",
            default=check_id or "governance finding",
        ),
        error="",
        failure_output="",
        file_path=coerce_stripped_str(row.get("file_path")),
        line=coerce_positive_int(row.get("line")),
        policy=coerce_stripped_str(row.get("prevention_surface")),
        fix=notes,
        source=_resolve_source(row, signal_type=signal_type),
        severity=coerce_stripped_str(row.get("severity")),
    )


def _resolve_source(
    row: Mapping[str, Any],
    *,
    signal_type: str,
) -> str:
    """Return the most specific source attribution the row carries."""
    source_command = coerce_stripped_str(row.get("source_command"))
    if source_command:
        return source_command
    if signal_type:
        return signal_type
    return "governance-review"
