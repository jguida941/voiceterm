"""Report assembly and rendering for the tandem-consistency guard."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.governance.draft import scan_repo_governance
from dev.scripts.devctl.runtime.review_state_locator import load_review_state_payload

try:
    from .checks import (
        check_implementer_ack_freshness,
        check_implementer_completion_stall,
        check_launch_truth,
        check_plan_alignment,
        check_promotion_state,
        check_reviewed_hash_honesty,
        check_reviewer_freshness,
    )
except ImportError:
    from tandem_consistency.checks import (
        check_implementer_ack_freshness,
        check_implementer_completion_stall,
        check_launch_truth,
        check_plan_alignment,
        check_promotion_state,
        check_reviewed_hash_honesty,
        check_reviewer_freshness,
    )


def _load_typed_review_state(repo_root: Path | None) -> dict[str, object] | None:
    """Try to load typed review_state.json for checks that can use it."""
    if repo_root is None:
        return None
    governance = scan_repo_governance(repo_root)
    payload = load_review_state_payload(repo_root, governance=governance)
    if payload is None:
        return None
    return dict(payload)


def build_report(
    *,
    bridge_text: str | None,
    repo_root: Path | None = None,
    ci_bundle: bool = False,
) -> dict[str, object]:
    """Run all tandem-consistency checks and return a structured report.

    When typed review_state.json is available, checks that can read typed
    current_session state will prefer it over parsing bridge prose. The bridge
    text is still passed for backward compatibility and for checks that have
    not yet been migrated.
    """
    if bridge_text is None:
        return {
            "command": "check_tandem_consistency",
            "ok": True,
            "bridge_present": False,
            "checks": [],
            "detail": "No bridge file — tandem checks are not applicable.",
        }

    typed_state = _load_typed_review_state(repo_root)

    checks = [
        check_reviewer_freshness(bridge_text, typed_state=typed_state),
        check_implementer_ack_freshness(bridge_text, typed_state=typed_state),
        check_implementer_completion_stall(bridge_text, typed_state=typed_state),
        check_reviewed_hash_honesty(bridge_text, repo_root=repo_root, ci_bundle=ci_bundle, typed_state=typed_state),
        check_plan_alignment(bridge_text, repo_root=repo_root, typed_state=typed_state),
        check_promotion_state(bridge_text, typed_state=typed_state),
        check_launch_truth(bridge_text, typed_state=typed_state),
    ]
    all_ok = all(check["ok"] for check in checks)
    failed = [check for check in checks if not check["ok"]]
    return {
        "command": "check_tandem_consistency",
        "ok": all_ok,
        "bridge_present": True,
        "typed_review_state_available": typed_state is not None,
        "total_checks": len(checks),
        "passed": len(checks) - len(failed),
        "failed": len(failed),
        "checks": checks,
        "role_summary": _role_summary(checks),
    }


def _role_summary(checks: list[dict[str, object]]) -> dict[str, str]:
    roles: dict[str, list[bool]] = {}
    for check in checks:
        role = str(check.get("role", "system"))
        roles.setdefault(role, []).append(bool(check.get("ok", False)))
    return {
        role: "healthy" if all(results) else "degraded"
        for role, results in sorted(roles.items())
    }


def render_md(report: dict[str, object]) -> str:
    lines = ["# check_tandem_consistency", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- bridge_present: {report.get('bridge_present', False)}")
    if not report.get("bridge_present"):
        lines.append(f"- detail: {report.get('detail', '')}")
        return "\n".join(lines)
    lines.append(f"- total_checks: {report.get('total_checks', 0)}")
    lines.append(f"- passed: {report.get('passed', 0)}")
    lines.append(f"- failed: {report.get('failed', 0)}")
    role_summary = report.get("role_summary", {})
    if isinstance(role_summary, dict):
        for role, status in sorted(role_summary.items()):
            lines.append(f"- {role}: {status}")
    checks = report.get("checks", [])
    if isinstance(checks, list):
        lines.append("")
        for check in checks:
            if not isinstance(check, dict):
                continue
            ok = check.get("ok", False)
            marker = "PASS" if ok else "FAIL"
            name = check.get("check", "unknown")
            role = check.get("role", "system")
            detail = check.get("detail", "")
            lines.append(f"- [{marker}] {name} (role={role}): {detail}")
    return "\n".join(lines)
