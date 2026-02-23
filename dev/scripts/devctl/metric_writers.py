"""JSONL metric append + failure knowledge-base helpers for devctl commands."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

METRICS_DIR = Path("~/.voiceterm/dev/metrics").expanduser()
FAILURE_KB = Path("~/.voiceterm/dev/failure_kb.jsonl").expanduser()
FINGERPRINT_FIELDS = (
    "category",
    "severity",
    "owner",
    "source",
    "summary",
    "component",
    "file",
    "line",
    "type",
    "root_cause",
    "matched_playbook",
)


def _utc_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def append_metric(source: str, record: Any) -> None:
    """Append a timestamped JSONL record to ~/.voiceterm/dev/metrics/{source}.jsonl."""
    path = METRICS_DIR / f"{source}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    # record may be a string (rendered markdown) or a dict (JSON); normalize.
    if isinstance(record, str):
        payload: dict[str, Any] = {"text": record}
    elif isinstance(record, dict):
        payload = dict(record)
    else:
        payload = {"value": str(record)}
    entry = {"ts": _utc_timestamp(), "source": source, **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def issue_fingerprint(issue: Mapping[str, Any]) -> str:
    """Build a deterministic fingerprint for triage issues."""
    fingerprint_fields = {
        key: issue.get(key)
        for key in FINGERPRINT_FIELDS
        if issue.get(key) not in (None, "")
    }
    # Fall back to full issue payload if no canonical fields are present.
    payload = fingerprint_fields if fingerprint_fields else dict(issue)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def append_failure_kb(issue: Mapping[str, Any]) -> None:
    """Append a triage issue to the failure knowledge base."""
    FAILURE_KB.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = issue.get("fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint:
        fingerprint = issue_fingerprint(issue)
    entry = {"ts": _utc_timestamp(), "fingerprint": fingerprint, **dict(issue)}
    with FAILURE_KB.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")
