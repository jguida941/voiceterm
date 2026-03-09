"""Route validation lanes from changed paths and optionally execute them."""

from __future__ import annotations

import json

from ..bundle_registry import BUNDLE_AUTHORITY_PATH, get_bundle_commands
from ..collect import collect_git_status
from ..common import emit_output, pipe_output, run_cmd, write_output
from ..time_utils import utc_timestamp
from ..config import REPO_ROOT
from .check_router_render import render_markdown
from .check_router_support import BUNDLE_BY_LANE
from .check_router_support import classify_lane as _classify_lane
from .check_router_support import dedupe_commands as _dedupe_commands
from .check_router_support import detect_risk_addons as _detect_risk_addons


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


def run(args) -> int:
    """Route and optionally execute the required check lane."""
    since_ref = getattr(args, "since_ref", None)
    head_ref = getattr(args, "head_ref", "HEAD")
    git_info = collect_git_status(since_ref, head_ref)
    if "error" in git_info:
        report = {
            "command": "check-router",
            "timestamp": utc_timestamp(),
            "ok": False,
            "lane": "tooling",
            "bundle": BUNDLE_BY_LANE["tooling"],
            "since_ref": since_ref,
            "head_ref": head_ref,
            "changed_paths": [],
            "reasons": [],
            "risk_addons": [],
            "planned_commands": [],
            "steps": [],
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

    changed_paths = sorted({row["path"] for row in git_info.get("changes", [])})
    classification = _classify_lane(changed_paths)
    lane = classification["lane"]
    bundle_name = BUNDLE_BY_LANE[lane]
    bundle_commands, bundle_error = _extract_bundle_commands(bundle_name)
    risk_addons = _detect_risk_addons(changed_paths)

    planned_rows = [
        {"source": bundle_name, "command": command} for command in bundle_commands
    ]
    for addon in risk_addons:
        planned_rows.extend(
            {"source": addon["id"], "command": command} for command in addon["commands"]
        )
    planned_rows = _dedupe_commands(planned_rows)

    steps: list[dict] = []
    ok = bundle_error is None
    execute = bool(getattr(args, "execute", False))
    if execute and bundle_error is None:
        keep_going = bool(getattr(args, "keep_going", False))
        dry_run = bool(getattr(args, "dry_run", False))
        for index, row in enumerate(planned_rows, start=1):
            result = run_cmd(
                f"router-{index:02d}",
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
        "since_ref": since_ref,
        "head_ref": head_ref,
        "changed_paths": changed_paths,
        "categories": classification["categories"],
        "reasons": classification["reasons"],
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
