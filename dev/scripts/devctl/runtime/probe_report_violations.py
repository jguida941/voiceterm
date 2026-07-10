"""Adapter mapping aggregated probe-report hints into ViolationRecord.

The probe-report aggregate carries its own typed contract
(``PROBE_REPORT_CONTRACT_ID``) and produces enriched risk-hint dicts
shaped by ``dev.scripts.checks.probe_report.contracts.finding_from_probe_hint``.
Separately, the check pipeline already renders through the shared
``CheckResult`` / ``ViolationRecord`` family in ``check_result_models``.

This module is the thin seam between the two: it converts the aggregate's
``risk_hints`` list into a tuple of ``ViolationRecord`` entries so
dashboard, startup summary, and operator surfaces that already consume
``ViolationRecord`` can render probe findings through the same shared
path (``render_check_result_text`` / ``render_check_result_md``) without
duplicating layout logic or inventing a second renderer for probe text.

The mapping is intentionally one-way and non-mutating: probe reports
keep their own JSON/markdown output shape, nothing in the probe pipeline
changes, and the shared contract only gains a new consumer.
"""

from __future__ import annotations

from typing import Any, Mapping

from .check_result_models import ViolationRecord
from .violation_adapter_support import (
    build_bounded_summary,
    coerce_positive_int,
    coerce_stripped_str,
)


def probe_report_to_violations(
    report: Mapping[str, Any],
) -> tuple[ViolationRecord, ...]:
    """Convert one aggregated probe-report payload into ViolationRecord tuples.

    Reads ``report["risk_hints"]`` (the enriched hint list produced by
    ``enrich_probe_hint_contract``) and maps each entry 1:1 into a
    ``ViolationRecord`` so shared-renderer consumers can format probe
    findings through the same path as check violations. Non-dict entries
    are silently skipped so a malformed hint cannot break the mapping.
    """
    hints = report.get("risk_hints") or []
    if not isinstance(hints, list):
        return ()
    return tuple(
        _hint_to_violation(hint)
        for hint in hints
        if isinstance(hint, Mapping)
    )


def _hint_to_violation(hint: Mapping[str, Any]) -> ViolationRecord:
    """Map one enriched probe hint into a ViolationRecord.

    Field map:

    - ``step_name`` <- ``check_id`` (the probe identifier)
    - ``exit_code`` <- ``0`` (probes are advisory, they always exit 0;
      the presence of a ViolationRecord itself is the finding signal)
    - ``summary``   <- first non-empty line of ``ai_instruction`` truncated
      to 120 chars, or a compact ``check_id: risk_type`` / ``check_id:
      review_lens`` fallback when the probe did not supply guidance
    - ``file_path`` <- ``file_path``
    - ``line``      <- ``line`` (or 0 when absent)
    - ``policy``    <- ``review_lens`` (the lens that flagged the finding)
    - ``fix``       <- ``ai_instruction`` (full text; summary holds the
      compact form, fix preserves the guidance paragraph)
    - ``source``    <- ``check_id`` (same as step_name so downstream
      renderers have a stable attribution token)
    - ``severity``  <- ``severity``
    """
    check_id = coerce_stripped_str(hint.get("check_id"))
    ai_instruction = coerce_stripped_str(hint.get("ai_instruction"))
    risk_type = coerce_stripped_str(hint.get("risk_type"))
    review_lens = coerce_stripped_str(hint.get("review_lens"))

    return ViolationRecord(
        step_name=check_id,
        exit_code=0,
        summary=build_bounded_summary(
            primary_text=ai_instruction,
            fallback_labels=(risk_type, review_lens),
            prefix=f"{check_id}: " if check_id else "",
            default=check_id or "probe risk hint",
        ),
        error="",
        failure_output="",
        file_path=coerce_stripped_str(hint.get("file_path")),
        line=coerce_positive_int(hint.get("line")),
        policy=review_lens,
        fix=ai_instruction,
        source=check_id,
        severity=coerce_stripped_str(hint.get("severity")),
    )
