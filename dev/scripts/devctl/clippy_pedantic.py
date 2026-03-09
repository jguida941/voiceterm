"""Helpers for advisory `clippy::pedantic` artifact classification."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

from .common import normalize_string_field, read_json_object, resolve_repo_path
from .config import REPO_ROOT

DEFAULT_SUMMARY_PATH = REPO_ROOT / "dev/reports/check/clippy-pedantic-summary.json"
DEFAULT_LINTS_PATH = REPO_ROOT / "dev/reports/check/clippy-pedantic-lints.json"
DEFAULT_POLICY_PATH = REPO_ROOT / "dev/config/clippy/pedantic_policy.json"

ACTION_ORDER = {
    "promote": 0,
    "review": 1,
    "defer": 2,
    "ignore": 3,
}
LEVEL_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
}
def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    return read_json_object(path)


def load_policy(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Load the pedantic policy file or return a minimal fallback policy."""
    payload, error = _read_json(path)
    if error or payload is None:
        return (
            {
                "schema_version": 1,
                "default_action": "review",
                "rules": [],
            },
            [f"pedantic policy unavailable ({error})"],
        )

    rules = payload.get("rules")
    if not isinstance(rules, list):
        return (
            {
                "schema_version": 1,
                "default_action": "review",
                "rules": [],
            },
            [f"pedantic policy invalid ({path} missing list field `rules`)"],
        )

    default_action = normalize_string_field(payload, "default_action", "review").lower()
    if default_action not in ACTION_ORDER:
        default_action = "review"

    return (
        {
            "schema_version": int(payload.get("schema_version") or 1),
            "default_action": default_action,
            "rules": rules,
            "owner": payload.get("owner"),
            "description": payload.get("description"),
        },
        [],
    )


def _match_rule(lint: str, rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        match = rule.get("match")
        if not isinstance(match, dict):
            continue

        exact_lint = match.get("lint")
        prefix = match.get("prefix")
        pattern = match.get("pattern")
        if isinstance(exact_lint, str) and lint == exact_lint:
            return rule
        if isinstance(prefix, str) and lint.startswith(prefix):
            return rule
        if isinstance(pattern, str) and fnmatch.fnmatch(lint, pattern):
            return rule
    return None


def _normalize_level(value: Any, default: str) -> str:
    text = str(value or "").strip().lower()
    if text in LEVEL_ORDER:
        return text
    return default


def classify_lints(
    lint_counts: dict[str, int],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    """Attach policy metadata to each observed lint."""
    ranked: list[dict[str, Any]] = []
    default_action = normalize_string_field(policy, "default_action", "review").lower()
    rules = policy.get("rules")
    if not isinstance(rules, list):
        rules = []

    for lint, count in lint_counts.items():
        if not isinstance(lint, str) or not lint:
            continue
        if not isinstance(count, int) or count <= 0:
            continue

        rule = _match_rule(lint, rules)
        action = default_action
        reason = "No pedantic policy decision recorded yet."
        bug_risk = "medium"
        noise = "medium"
        fix_cost = "medium"
        rule_id = "unreviewed"
        matched = False
        if isinstance(rule, dict):
            matched = True
            action = normalize_string_field(rule, "action", default_action).lower()
            if action not in ACTION_ORDER:
                action = default_action
            reason = normalize_string_field(rule, "reason", reason)
            bug_risk = _normalize_level(rule.get("bug_risk"), "medium")
            noise = _normalize_level(rule.get("noise"), "medium")
            fix_cost = _normalize_level(rule.get("fix_cost"), "medium")
            rule_id = normalize_string_field(rule, "id", lint) or lint

        ranked.append(
            {
                "lint": lint,
                "count": count,
                "action": action,
                "bug_risk": bug_risk,
                "noise": noise,
                "fix_cost": fix_cost,
                "reason": reason,
                "policy_rule_id": rule_id,
                "policy_matched": matched,
            }
        )

    ranked.sort(
        key=lambda row: (
            ACTION_ORDER.get(str(row.get("action")), 99),
            -int(row.get("count") or 0),
            -LEVEL_ORDER.get(str(row.get("bug_risk")), 0),
            LEVEL_ORDER.get(str(row.get("noise")), 99),
            LEVEL_ORDER.get(str(row.get("fix_cost")), 99),
            str(row.get("lint")),
        )
    )
    return ranked


def build_rule_rollup(ranked_lints: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Aggregate observed counts by matched policy rule."""
    rollup: dict[str, dict[str, Any]] = {}
    for item in ranked_lints:
        rule_id = str(item.get("policy_rule_id") or "unreviewed")
        row = rollup.setdefault(
            rule_id,
            {
                "action": item.get("action", "review"),
                "observations": 0,
                "lints": [],
            },
        )
        row["observations"] += int(item.get("count") or 0)
        row["lints"].append(
            {
                "lint": item.get("lint"),
                "count": item.get("count"),
            }
        )
    for row in rollup.values():
        row["lints"].sort(
            key=lambda item: (-int(item.get("count") or 0), str(item.get("lint")))
        )
    return dict(sorted(rollup.items()))


def build_issues(
    ranked_lints: list[dict[str, Any]],
    *,
    artifact_found: bool,
    warning: str | None,
    exit_code: int,
    status: str,
) -> list[dict[str, Any]]:
    """Convert pedantic observations into normalized triage issues."""
    issues: list[dict[str, Any]] = []
    if not artifact_found:
        if warning:
            issues.append(
                {
                    "category": "governance",
                    "severity": "low",
                    "source": "devctl.pedantic",
                    "summary": f"Pedantic advisory requested but artifacts are unavailable: {warning}",
                }
            )
        return issues

    if exit_code != 0 or status != "success":
        issues.append(
            {
                "category": "quality",
                "severity": "medium",
                "source": "devctl.pedantic",
                "summary": (
                    f"Pedantic advisory run failed (status={status}, exit={exit_code}); "
                    "inspect the saved clippy command/result before trusting zero-warning output."
                ),
            }
        )

    promote_candidates = [
        row for row in ranked_lints if row.get("action") == "promote"
    ]
    for row in promote_candidates[:3]:
        issues.append(
            {
                "category": "quality",
                "severity": "medium",
                "source": "devctl.pedantic",
                "summary": (
                    f"Pedantic promote candidate `{row['lint']}` observed "
                    f"{row['count']} time(s); consider graduating it into "
                    "`maintainer-lint` after cleanup."
                ),
            }
        )

    unreviewed = [row for row in ranked_lints if not row.get("policy_matched", False)]
    if unreviewed:
        issues.append(
            {
                "category": "governance",
                "severity": "medium",
                "source": "devctl.pedantic",
                "summary": (
                    f"Pedantic sweep found {len(unreviewed)} unreviewed lint ids; "
                    "classify them in `dev/config/clippy/pedantic_policy.json` "
                    "before promoting new strict lanes."
                ),
            }
        )

    return issues


def build_snapshot(
    *,
    summary_path: str | None = None,
    lints_path: str | None = None,
    policy_path: str | None = None,
) -> Dict[str, Any]:
    """Build a structured pedantic advisory snapshot from existing artifacts."""
    resolved_summary_path = resolve_repo_path(summary_path, DEFAULT_SUMMARY_PATH)
    resolved_lints_path = resolve_repo_path(lints_path, DEFAULT_LINTS_PATH)
    resolved_policy_path = resolve_repo_path(policy_path, DEFAULT_POLICY_PATH)

    summary_payload, summary_error = _read_json(resolved_summary_path)
    lints_payload, lints_error = _read_json(resolved_lints_path)
    policy, policy_warnings = load_policy(resolved_policy_path)

    warning_parts = [part for part in (summary_error, lints_error) if part]
    warning_text = "; ".join(warning_parts) if warning_parts else None
    artifact_found = summary_payload is not None and lints_payload is not None
    exit_code = int((summary_payload or {}).get("exit_code") or 0)
    status = str((summary_payload or {}).get("status") or "unknown")

    lint_counts: dict[str, int] = {}
    if isinstance(lints_payload, dict):
        raw_lints = lints_payload.get("lints")
        if isinstance(raw_lints, dict):
            lint_counts = {
                str(lint): int(count)
                for lint, count in raw_lints.items()
                if isinstance(lint, str) and isinstance(count, int) and count > 0
            }

    ranked_lints = classify_lints(lint_counts, policy) if artifact_found else []
    issues = build_issues(
        ranked_lints,
        artifact_found=artifact_found,
        warning=warning_text,
        exit_code=exit_code,
        status=status,
    )

    observations_by_action = {action: 0 for action in ACTION_ORDER}
    lints_by_action = {action: 0 for action in ACTION_ORDER}
    for item in ranked_lints:
        action = str(item.get("action") or "review")
        observations_by_action[action] = observations_by_action.get(action, 0) + int(
            item.get("count") or 0
        )
        lints_by_action[action] = lints_by_action.get(action, 0) + 1

    top_promote = [
        item for item in ranked_lints if item.get("action") == "promote"
    ][:5]
    top_review = [
        item for item in ranked_lints if item.get("action") == "review"
    ][:5]

    summary_payload = summary_payload or {}
    return {
        "enabled": True,
        "artifact_found": artifact_found,
        "summary_path": str(resolved_summary_path),
        "lints_path": str(resolved_lints_path),
        "policy_path": str(resolved_policy_path),
        "warning": warning_text,
        "warnings": int(summary_payload.get("warnings") or 0),
        "exit_code": exit_code,
        "status": status,
        "generated_at": summary_payload.get("generated_at")
        or (lints_payload or {}).get("generated_at"),
        "policy_warnings": policy_warnings,
        "policy_owner": policy.get("owner"),
        "observed_lints": len(ranked_lints),
        "reviewed_lints": sum(1 for item in ranked_lints if item.get("policy_matched")),
        "unreviewed_lints": sum(
            1 for item in ranked_lints if not item.get("policy_matched")
        ),
        "rollup": {
            "lints_by_action": dict(sorted(lints_by_action.items())),
            "observations_by_action": dict(sorted(observations_by_action.items())),
            "rule_rollup": build_rule_rollup(ranked_lints),
        },
        "top_lints": ranked_lints[:10],
        "top_promote_candidates": top_promote,
        "top_review_candidates": top_review,
        "ranked_lints": ranked_lints,
        "issues": issues,
    }
