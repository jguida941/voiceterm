"""Route validation lanes from changed paths and optionally execute them."""

from __future__ import annotations

import json

from ...bundle_registry import BUNDLE_AUTHORITY_PATH, get_bundle_commands
from ...collect import collect_git_status
from ...common import (
    emit_output,
    inject_quality_policy_command,
    normalize_repo_python_shell_command,
    pipe_output,
    run_cmd,
    write_output,
)
from ...time_utils import utc_timestamp
from ...config import REPO_ROOT
from .router_constants import resolve_check_router_config
from .router_render import render_markdown
from .router_support import BUNDLE_BY_LANE
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


def _normalize_router_command(command: str, policy_path: str | None) -> str:
    return normalize_repo_python_shell_command(
        inject_quality_policy_command(command, policy_path)
    )


def _dry_run_step_result(name: str, row: dict[str, str]) -> dict[str, object]:
    return dict(
        name=name,
        cmd=["bash", "-lc", row["command"]],
        cwd=str(REPO_ROOT),
        returncode=0,
        duration_s=0.0,
        skipped=True,
        source=row["source"],
        router_command=row["command"],
    )


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
        output = (
            json.dumps(report, indent=2)
            if args.format == "json"
            else _render_md(report)
        )
        pipe_rc = emit_output(
            output,
            output_path=args.output,
            pipe_command=args.pipe_command,
            pipe_args=args.pipe_args,
            writer=write_output,
            piper=pipe_output,
        )
        if pipe_rc != 0:
            return pipe_rc
        return 1

    changed_paths = _changed_paths(git_info)
    classification = _classify_lane(changed_paths, policy_path=policy_path)
    lane = classification["lane"]
    bundle_name = bundle_by_lane[lane]
    bundle_commands, bundle_error = _extract_bundle_commands(bundle_name)
    risk_addons = [
        *_detect_risk_addons(changed_paths, policy_path=policy_path),
        *_detect_python_test_addons(changed_paths),
    ]

    planned_rows = [
        {
            "source": bundle_name,
            "command": _normalize_router_command(command, policy_path),
        }
        for command in bundle_commands
    ]
    for addon in risk_addons:
        planned_rows.extend(
            {
                "source": addon["id"],
                "command": _normalize_router_command(command, policy_path),
            }
            for command in addon["commands"]
        )
    planned_rows = _dedupe_commands(planned_rows)

    steps: list[dict] = []
    ok = bundle_error is None
    execute = bool(getattr(args, "execute", False))
    if execute and bundle_error is None:
        keep_going = bool(getattr(args, "keep_going", False))
        dry_run = bool(getattr(args, "dry_run", False))
        for index, row in enumerate(planned_rows, start=1):
            step_name = f"router-{index:02d}"
            if dry_run and args.format == "json":
                result = _dry_run_step_result(step_name, row)
            else:
                result = run_cmd(
                    step_name,
                    ["bash", "-lc", row["command"]],
                    cwd=REPO_ROOT,
                    dry_run=dry_run,
                )
                result["source"] = row["source"]
                result["router_command"] = row["command"]
            steps.append(result)
            if result["returncode"] != 0:
                ok = False
                if not keep_going:
                    break
    elif execute and bundle_error is not None:
        ok = False

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
        "error": bundle_error,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if ok else 1
