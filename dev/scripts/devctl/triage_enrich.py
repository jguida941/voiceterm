"""Issue enrichment helpers for `devctl triage`.

This module normalizes issue records and maps cihub artifact payloads into
stable issue objects (`category`, `severity`, `owner`, `summary`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_OWNER_MAP = {
    "ci": "platform",
    "infra": "platform",
    "security": "security",
    "release": "release",
    "quality": "runtime",
    "performance": "runtime",
    "docs": "docs",
    "governance": "maintainers",
    "general": "maintainers",
}

SEVERITY_MAP = {
    "critical": "critical",
    "sev0": "critical",
    "p0": "critical",
    "blocker": "critical",
    "high": "high",
    "sev1": "high",
    "p1": "high",
    "urgent": "high",
    "medium": "medium",
    "moderate": "medium",
    "sev2": "medium",
    "p2": "medium",
    "warning": "medium",
    "warn": "medium",
    "low": "low",
    "minor": "low",
    "sev3": "low",
    "p3": "low",
    "info": "info",
    "informational": "info",
    "p4": "info",
}

CATEGORY_MAP = {
    "ci": "ci",
    "workflow": "ci",
    "infra": "infra",
    "infrastructure": "infra",
    "security": "security",
    "sec": "security",
    "release": "release",
    "quality": "quality",
    "mutation": "quality",
    "test": "quality",
    "perf": "performance",
    "performance": "performance",
    "docs": "docs",
    "documentation": "docs",
    "governance": "governance",
}


def _clean_key(value: Any) -> str:
    text = str(value or "").strip().lower()
    return "".join(ch for ch in text if ch.isalnum())


def normalize_severity(value: Any) -> str:
    key = _clean_key(value)
    if not key:
        return "medium"
    return SEVERITY_MAP.get(key, "medium")


def normalize_category(value: Any) -> str:
    key = _clean_key(value)
    if not key:
        return "general"
    return CATEGORY_MAP.get(key, key if key.isalpha() else "general")


def normalize_summary(value: Any) -> str:
    text = str(value or "").strip()
    return text


def load_owner_map(owner_map_file: str | None) -> Tuple[dict, List[str]]:
    """Load optional category->owner map; fall back to defaults with warnings."""
    owner_map = dict(DEFAULT_OWNER_MAP)
    warnings: List[str] = []
    if not owner_map_file:
        return owner_map, warnings
    path = Path(owner_map_file).expanduser()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        warnings.append(f"owner map file unavailable ({exc})")
        return owner_map, warnings
    except json.JSONDecodeError as exc:
        warnings.append(f"owner map JSON invalid ({exc})")
        return owner_map, warnings

    if not isinstance(payload, dict):
        warnings.append("owner map ignored: expected JSON object")
        return owner_map, warnings

    applied = 0
    for raw_key, raw_owner in payload.items():
        category = normalize_category(raw_key)
        owner = str(raw_owner or "").strip()
        if not owner:
            continue
        owner_map[category] = owner
        applied += 1
    warnings.append(f"owner map loaded ({applied} category overrides)")
    return owner_map, warnings


def _extract_record_fields(record: dict, source: str, owner_map: dict) -> dict | None:
    summary = normalize_summary(
        record.get("summary")
        or record.get("title")
        or record.get("name")
        or record.get("description")
        or record.get("message")
    )
    if not summary:
        return None
    category = normalize_category(
        record.get("category")
        or record.get("domain")
        or record.get("group")
        or record.get("type")
    )
    severity = normalize_severity(
        record.get("severity")
        or record.get("priority")
        or record.get("level")
        or record.get("rank")
    )
    owner = str(record.get("owner") or "").strip() or owner_map.get(category) or owner_map.get(
        "general", "maintainers"
    )
    return {
        "category": category,
        "severity": severity,
        "owner": owner,
        "source": source,
        "summary": summary,
    }


def _iter_issue_like_records(payload: Any):
    if isinstance(payload, str):
        text = payload.strip()
        if text:
            yield {"summary": text}
        return
    if isinstance(payload, list):
        for item in payload:
            yield from _iter_issue_like_records(item)
        return
    if not isinstance(payload, dict):
        return

    known_issue_keys = {
        "summary",
        "title",
        "name",
        "description",
        "message",
        "severity",
        "priority",
        "level",
        "rank",
        "category",
        "domain",
        "group",
        "type",
        "owner",
    }
    if any(key in payload for key in known_issue_keys):
        yield payload
    for value in payload.values():
        if isinstance(value, (dict, list)):
            yield from _iter_issue_like_records(value)


def extract_cihub_issues(cihub_payload: dict, owner_map: dict) -> List[dict]:
    """Extract normalized issues from cihub triage artifact payloads."""
    artifacts = cihub_payload.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return []

    issues: List[dict] = []
    sources = [
        ("cihub.triage_json", artifacts.get("triage_json")),
        ("cihub.priority_json", artifacts.get("priority_json")),
    ]
    for source, payload in sources:
        for record in _iter_issue_like_records(payload):
            if not isinstance(record, dict):
                continue
            issue = _extract_record_fields(record, source=source, owner_map=owner_map)
            if issue:
                issues.append(issue)

    deduped: List[dict] = []
    seen = set()
    for issue in issues:
        key = (
            issue.get("source"),
            issue.get("category"),
            issue.get("severity"),
            issue.get("owner"),
            issue.get("summary"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped


def apply_defaults_to_issues(issues: List[dict], owner_map: dict) -> List[dict]:
    """Normalize existing issue records and add default owners."""
    normalized: List[dict] = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        category = normalize_category(issue.get("category"))
        severity = normalize_severity(issue.get("severity"))
        summary = normalize_summary(issue.get("summary"))
        if not summary:
            continue
        owner = str(issue.get("owner") or "").strip() or owner_map.get(category) or owner_map.get(
            "general", "maintainers"
        )
        normalized.append(
            {
                "category": category,
                "severity": severity,
                "owner": owner,
                "source": issue.get("source", "devctl.triage"),
                "summary": summary,
            }
        )
    return normalized


def build_issue_rollup(issues: List[dict]) -> dict:
    """Build aggregate counts by severity, category, and owner."""
    by_severity: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    by_owner: Dict[str, int] = {}
    for issue in issues:
        severity = str(issue.get("severity", "unknown"))
        category = str(issue.get("category", "unknown"))
        owner = str(issue.get("owner", "unknown"))
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1
        by_owner[owner] = by_owner.get(owner, 0) + 1
    return {
        "total": len(issues),
        "by_severity": dict(sorted(by_severity.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_owner": dict(sorted(by_owner.items())),
    }
