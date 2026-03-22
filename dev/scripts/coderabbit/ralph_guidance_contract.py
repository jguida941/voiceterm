"""Guidance-adoption contract helpers for Ralph remediation routes."""

from __future__ import annotations

import json
from dataclasses import dataclass

GUIDANCE_SUMMARY_START = "RALPH_GUIDANCE_SUMMARY_START"
GUIDANCE_SUMMARY_END = "RALPH_GUIDANCE_SUMMARY_END"


@dataclass(frozen=True)
class ClaudeRunResult:
    returncode: int
    output_text: str


def _normalize_claude_result(result: ClaudeRunResult | int) -> ClaudeRunResult:
    """Keep legacy int-only mocks/callers compatible with the richer result contract."""
    if isinstance(result, ClaudeRunResult):
        return result
    return ClaudeRunResult(returncode=int(result), output_text="")


def _extract_guidance_summary(output_text: str) -> dict[str, dict[str, str]]:
    start = output_text.find(GUIDANCE_SUMMARY_START)
    end = output_text.find(GUIDANCE_SUMMARY_END)
    if start < 0 or end < 0 or end <= start:
        return {}
    payload = output_text[start + len(GUIDANCE_SUMMARY_START) : end].strip()
    if not payload:
        return {}
    try:
        rows = json.loads(payload)
    except json.JSONDecodeError:
        return {}
    if not isinstance(rows, list):
        return {}
    parsed: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        summary = str(row.get("summary") or "").strip()
        disposition = str(row.get("guidance_disposition") or "").strip()
        if not summary or not disposition:
            continue
        parsed[summary] = {
            "guidance_disposition": disposition,
            "waiver_reason": str(row.get("waiver_reason") or "").strip(),
        }
    return parsed


def _build_fix_results(
    items: list[dict],
    changes_made: bool,
    checks_passed: bool,
    *,
    guidance_summary: dict[str, dict[str, str]] | None = None,
) -> list[dict]:
    """Build per-finding fix status entries based on outcome."""
    if not changes_made:
        status = "false-positive"
    elif checks_passed:
        status = "fixed"
    else:
        status = "pending"
    guidance_summary = guidance_summary or {}
    results: list[dict] = []
    for item in items:
        summary = str(item.get("summary", ""))
        guidance_entries = item.get("probe_guidance")
        guidance_attached = isinstance(guidance_entries, list) and bool(guidance_entries)
        disposition_row = guidance_summary.get(summary, {})
        disposition = str(disposition_row.get("guidance_disposition") or "").strip()
        if guidance_attached and disposition not in {"used", "waived"}:
            disposition = "unreported"
        elif not guidance_attached:
            disposition = "not_applicable"
        results.append(
            {
                "summary": summary,
                "status": status,
                "fix_skill": "",
                "probe_guidance_attached": guidance_attached,
                "guidance_disposition": disposition,
                "guidance_waiver_reason": (
                    str(disposition_row.get("waiver_reason") or "").strip()
                    if disposition == "waived"
                    else ""
                ),
                "fix_accepted": status == "fixed",
            }
        )
    return results
