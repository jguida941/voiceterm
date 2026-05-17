"""Receipt-failure formatting helpers for governed push reports."""

from __future__ import annotations

REVIEW_SNAPSHOT_RECEIPT_FAILURE_DETAIL_LIMIT = 400
REVIEW_SNAPSHOT_RECEIPT_FAILURE_TRUNCATION = (
    " [...truncated; see dev/reports/push/latest_push_report.json]"
)


def review_snapshot_receipt_failure_detail(step: dict[str, object]) -> str:
    """Return a compact, sanitized failure detail for receipt commits."""
    parts = [f"returncode={step.get('returncode', 1)}"]
    stderr = _first_nonempty_line(step.get("stderr"))
    if stderr:
        parts.append(f"stderr={_truncate_receipt_failure_detail(stderr)}")
        return "; ".join(parts)
    error = _first_nonempty_line(step.get("error"))
    if error:
        parts.append(f"error={_truncate_receipt_failure_detail(error)}")
        return "; ".join(parts)
    output = _first_nonempty_line(
        step.get("failure_output")
        or step.get("stdout")
        or step.get("output")
        or step.get("message")
    )
    if output:
        parts.append(f"output={_truncate_receipt_failure_detail(output)}")
    return "; ".join(parts)


def _first_nonempty_line(value: object) -> str:
    for line in str(value or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _truncate_receipt_failure_detail(text: str) -> str:
    if len(text) <= REVIEW_SNAPSHOT_RECEIPT_FAILURE_DETAIL_LIMIT:
        return text
    allowed = (
        REVIEW_SNAPSHOT_RECEIPT_FAILURE_DETAIL_LIMIT
        - len(REVIEW_SNAPSHOT_RECEIPT_FAILURE_TRUNCATION)
    )
    if allowed < 0:
        allowed = 0
    return text[:allowed].rstrip() + REVIEW_SNAPSHOT_RECEIPT_FAILURE_TRUNCATION


__all__ = ["review_snapshot_receipt_failure_detail"]
