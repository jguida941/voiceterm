"""Acceptance semantics for reviewer-owned bridge sections."""

from __future__ import annotations

import re

from .handoff_constants import MARKDOWN_ITEM_RE

_ACCEPTED_VERDICT_PREFIX_RE = re.compile(
    r"^(?:reviewer[- ]accepted|accepted|push\s+approved|all\s+green|resolved)\b",
    re.IGNORECASE,
)
_CLEAR_FINDINGS_PREFIX_RE = re.compile(
    r"^(?:\(none\)|none|no\s+blockers|all\s+clear|all\s+green|resolved)\b",
    re.IGNORECASE,
)


def _normalized_bridge_lines(text: str) -> tuple[str, ...]:
    """Return non-empty bridge lines normalized for section-state checks."""
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = MARKDOWN_ITEM_RE.match(stripped)
        candidate = match.group("value").strip() if match is not None else stripped
        if candidate:
            lines.append(candidate.lower())
    return tuple(lines)


def review_acceptance_projection(snapshot) -> tuple[str, str, bool]:
    """Return reviewer verdict/findings plus accepted boolean from bridge state."""
    current_verdict = str(snapshot.sections.get("Current Verdict", "")).strip()
    open_findings = str(snapshot.sections.get("Open Findings", "")).strip()
    verdict_lines = _normalized_bridge_lines(current_verdict)
    if not verdict_lines:
        return current_verdict, open_findings, False
    if _ACCEPTED_VERDICT_PREFIX_RE.match(verdict_lines[0]) is None:
        return current_verdict, open_findings, False

    finding_lines = _normalized_bridge_lines(open_findings)
    return current_verdict, open_findings, not finding_lines or all(
        _CLEAR_FINDINGS_PREFIX_RE.match(line) is not None
        for line in finding_lines
    )


def bridge_review_accepted(source) -> bool:
    """Return reviewer acceptance as a projection over typed runtime state."""
    runtime_acceptance = _runtime_review_accepted(source)
    if runtime_acceptance is not None:
        return runtime_acceptance
    _current_verdict, _open_findings, review_accepted = review_acceptance_projection(
        source
    )
    return review_accepted


def _runtime_review_accepted(source) -> bool | None:
    reviewer_runtime = getattr(source, "reviewer_runtime", None)
    if reviewer_runtime is not None:
        review_acceptance = getattr(reviewer_runtime, "review_acceptance", None)
        if review_acceptance is not None:
            accepted = getattr(review_acceptance, "review_accepted", None)
            if isinstance(accepted, bool):
                return accepted

    review_acceptance = getattr(source, "review_acceptance", None)
    if review_acceptance is not None:
        accepted = getattr(review_acceptance, "review_accepted", None)
        if isinstance(accepted, bool):
            return accepted

    if isinstance(source, dict):
        reviewer_runtime_mapping = source.get("reviewer_runtime")
        if isinstance(reviewer_runtime_mapping, dict):
            review_acceptance_mapping = reviewer_runtime_mapping.get("review_acceptance")
            if isinstance(review_acceptance_mapping, dict):
                accepted = review_acceptance_mapping.get("review_accepted")
                if isinstance(accepted, bool):
                    return accepted
        review_acceptance_mapping = source.get("review_acceptance")
        if isinstance(review_acceptance_mapping, dict):
            accepted = review_acceptance_mapping.get("review_accepted")
            if isinstance(accepted, bool):
                return accepted
    return None
