"""Route validation lanes from changed paths and optionally execute them."""

from __future__ import annotations

from ...bundle_registry import BUNDLE_AUTHORITY_PATH, get_bundle_commands
from ...collect import collect_git_status
from ...time_utils import utc_timestamp
from .router_constants import BUNDLE_BY_LANE, resolve_check_router_config
from .router_coverage import (
    build_guard_coverage_receipt,
    build_remediation_actions,
)
from .router_execution import (
    build_planned_rows,
    emit_router_report,
    execute_planned_rows,
)
from .router_render import render_markdown
from .router_support import classify_lane as _classify_lane
from .router_support import dedupe_commands as _dedupe_commands
from .router_support import detect_python_test_addons as _detect_python_test_addons
from .router_support import detect_risk_addons as _detect_risk_addons


def _extract_bundle_commands(bundle_name: str) -> tuple[list[str], str | None]:
    try:
        return get_bundle_commands(bundle_name), None
    except KeyError:
        return (
            [],
            "bundle `{}` is not registered in {}".format(
                bundle_name, BUNDLE_AUTHORITY_PATH
            ),
        )


def _render_md(report: dict) -> str:
    return render_markdown(report)


def _changed_paths(git_info: dict[str, object]) -> list[str]:
    changes = git_info.get("changes")
    if not isinstance(changes, list):
        return []
    return sorted(
        {
            str(row.get("path") or "")
            for row in changes
            if isinstance(row, dict) and str(row.get("path") or "")
        }
    )


def _resolve_router_git_scope(
    *,
    since_ref: str | None,
    head_ref: str,
) -> tuple[dict[str, object], dict[str, object]]:
    range_info = collect_git_status(since_ref, head_ref)
    scope = {
        "source": str(range_info.get("mode") or ""),
        "requested_since_ref": since_ref,
        "requested_head_ref": head_ref,
        "range_changed_paths_count": len(_changed_paths(range_info)),
        "used_worktree_dirty_paths": False,
    }
    if not since_ref or "error" in range_info:
        return range_info, scope

    worktree_info = collect_git_status(None, head_ref)
    worktree_paths = _changed_paths(worktree_info)
    if "error" not in worktree_info and worktree_paths:
        scope["source"] = "working-tree-dirty-over-since-ref"
        scope["used_worktree_dirty_paths"] = True
        scope["worktree_changed_paths_count"] = len(worktree_paths)
        return worktree_info, scope
    return range_info, scope


def run(args) -> int:
    """Route and optionally execute the required check lane."""
    since_ref = getattr(args, "since_ref", None)
    head_ref = getattr(args, "head_ref", "HEAD")
    policy_path = getattr(args, "quality_policy", None)
    router_config = resolve_check_router_config(policy_path=policy_path)
    bundle_by_lane = router_config.bundle_by_lane
    git_info, change_scope = _resolve_router_git_scope(
        since_ref=since_ref,
        head_ref=head_ref,
    )
    if "error" in git_info:
        report = {
            "command": "check-router",
            "timestamp": utc_timestamp(),
            "ok": False,
            "lane": "tooling",
            "bundle": bundle_by_lane["tooling"],
            "policy_path": router_config.policy_path,
            "policy_warnings": list(router_config.warnings),
            "since_ref": since_ref,
            "head_ref": head_ref,
            "change_scope": change_scope,
            "changed_paths": [],
            "reasons": [],
            "risk_addons": [],
            "planned_commands": [],
            "steps": [],
            "rule_summary": "",
            "match_evidence": [],
            "rejected_rule_traces": [],
            "execute": bool(getattr(args, "execute", False)),
            "error": git_info["error"],
        }
        return emit_router_report(args, report, render_md=_render_md)

    changed_paths = _changed_paths(git_info)
    classification = _classify_lane(changed_paths, policy_path=policy_path)
    lane = classification["lane"]
    bundle_name = bundle_by_lane[lane]
    bundle_commands, bundle_error = _extract_bundle_commands(bundle_name)
    risk_addons = [
        *_detect_risk_addons(changed_paths, policy_path=policy_path),
        *_detect_python_test_addons(changed_paths),
    ]

    planned_rows = _dedupe_commands(
        build_planned_rows(
            bundle_name=bundle_name,
            bundle_commands=bundle_commands,
            risk_addons=risk_addons,
            policy_path=policy_path,
            since_ref=since_ref,
            head_ref=head_ref,
        )
    )
    steps, ok = execute_planned_rows(
        planned_rows=planned_rows,
        args=args,
        bundle_error=bundle_error,
    )
    execute = bool(getattr(args, "execute", False))
    keep_going = bool(getattr(args, "keep_going", False))
    parallel_workers = max(1, int(getattr(args, "parallel_workers", 4)))
    parallel_enabled = (
        execute
        and keep_going
        and not bool(getattr(args, "no_parallel", False))
        and parallel_workers > 1
    )

    report = {
        "command": "check-router",
        "timestamp": utc_timestamp(),
        "ok": ok,
        "lane": lane,
        "bundle": bundle_name,
        "policy_path": router_config.policy_path,
        "policy_warnings": list(router_config.warnings),
        "since_ref": since_ref,
        "head_ref": head_ref,
        "change_scope": change_scope,
        "changed_paths": changed_paths,
        "categories": classification["categories"],
        "reasons": classification["reasons"],
        "rule_summary": classification.get("rule_summary", ""),
        "match_evidence": classification.get("match_evidence", []),
        "rejected_rule_traces": classification.get("rejected_rule_traces", []),
        "risk_addons": risk_addons,
        "planned_commands": planned_rows,
        "steps": steps,
        "execute": execute,
        "keep_going": keep_going,
        "parallel_enabled": parallel_enabled,
        "parallel_workers": parallel_workers,
        "error": bundle_error,
    }
    report["guard_coverage"] = build_guard_coverage_receipt(
        planned_rows=planned_rows,
        steps=steps,
        execute=execute,
        dry_run=bool(getattr(args, "dry_run", False)),
        bundle_name=bundle_name,
        risk_addons=risk_addons,
    )
    report["remediation_actions"] = build_remediation_actions(steps)

    return emit_router_report(args, report, render_md=_render_md)
