"""Support helpers for policy-backed simple lane commands."""

from __future__ import annotations

import re
import shlex
import sys
from dataclasses import dataclass

from ...collect import collect_git_status
from ..check_router import _extract_bundle_commands
from ..check_router_constants import resolve_check_router_config
from ..check_router_support import (
    classify_lane as _classify_lane,
    detect_risk_addons as _detect_risk_addons,
)

CURRENT_PYTHON = sys.executable
_ENV_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
_POLICY_AWARE_SUBCOMMANDS = frozenset(
    {
        "check",
        "check-router",
        "docs-check",
        "probe-report",
        "quality-policy",
        "render-surfaces",
        "report",
        "status",
        "triage",
    }
)


@dataclass(frozen=True)
class TandemValidateExecution:
    ok: bool
    dry_run: bool
    keep_going: bool
    quality_policy: str | None
    steps: list[dict[str, object]]
    timestamp: str


def split_shell_prefix(command: str) -> tuple[list[str], list[str]] | None:
    """Split a shell command into env assignments and argv tokens."""
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    env_prefix: list[str] = []
    while parts and _ENV_ASSIGNMENT_RE.fullmatch(parts[0]):
        env_prefix.append(parts.pop(0))
    return env_prefix, parts


def inject_quality_policy(command: str, quality_policy_path: str | None) -> str:
    """Append a quality-policy override to policy-aware repo commands."""
    if not quality_policy_path:
        return command
    split = split_shell_prefix(command)
    if split is None:
        return command
    env_prefix, parts = split
    if len(parts) < 2 or parts[1] != "dev/scripts/devctl.py":
        return command
    command_args = parts[2:]
    if not command_args or command_args[0] not in _POLICY_AWARE_SUBCOMMANDS:
        return command
    if "--quality-policy" in command_args:
        return command
    command_args.extend(["--quality-policy", quality_policy_path])
    rebuilt = shlex.join([parts[0], parts[1], *command_args])
    return " ".join([*env_prefix, rebuilt]) if env_prefix else rebuilt


def normalize_repo_python_command(command: str) -> str:
    """Force repo-owned Python commands onto the current interpreter."""
    split = split_shell_prefix(command)
    if split is None:
        return command
    env_prefix, parts = split
    if len(parts) < 2:
        return command
    if parts[0] not in {"python3", "python3.11", CURRENT_PYTHON}:
        return command
    target = parts[1]
    if target != "dev/scripts/devctl.py" and not target.startswith("dev/scripts/checks/"):
        return command
    parts[0] = CURRENT_PYTHON
    rebuilt = shlex.join(parts)
    return " ".join([*env_prefix, rebuilt]) if env_prefix else rebuilt


def dedupe_tandem_validate_rows(command_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Keep stable ordered command rows while preserving forced reruns."""
    seen: set[str] = set()
    deduped: list[dict[str, object]] = []
    for row in command_rows:
        key = " ".join(str(row["command"]).split())
        force_rerun = bool(row.get("force_rerun"))
        if key in seen and not force_rerun:
            continue
        deduped.append(row)
        if not force_rerun:
            seen.add(key)
    return deduped


def build_tandem_validate_plan(
    *,
    quality_policy_path: str | None,
    since_ref: str | None,
    head_ref: str,
) -> dict[str, object]:
    """Resolve the routed tandem-validation plan from changed files."""
    router_config = resolve_check_router_config(policy_path=quality_policy_path)
    git_info = collect_git_status(since_ref, head_ref)
    if "error" in git_info:
        return _error_plan(
            router_config=router_config,
            since_ref=since_ref,
            head_ref=head_ref,
            error=str(git_info["error"]),
        )

    changed_paths = sorted({row["path"] for row in git_info.get("changes", [])})
    classification = _classify_lane(changed_paths, policy_path=quality_policy_path)
    lane = classification["lane"]
    bundle_name = router_config.bundle_by_lane[lane]
    bundle_commands, bundle_error = _extract_bundle_commands(bundle_name)
    risk_addons = _detect_risk_addons(changed_paths, policy_path=quality_policy_path)
    planned_commands = _build_planned_rows(
        bundle_name=bundle_name,
        bundle_commands=bundle_commands,
        risk_addons=risk_addons,
        quality_policy_path=quality_policy_path,
    )
    plan: dict[str, object] = {}
    plan["ok"] = bundle_error is None
    plan["lane"] = lane
    plan["bundle"] = bundle_name
    plan["policy_path"] = router_config.policy_path
    plan["policy_warnings"] = list(router_config.warnings)
    plan["since_ref"] = since_ref
    plan["head_ref"] = head_ref
    plan["changed_paths"] = changed_paths
    plan["categories"] = classification["categories"]
    plan["reasons"] = classification["reasons"]
    plan["risk_addons"] = risk_addons
    plan["planned_commands"] = planned_commands
    plan["error"] = bundle_error
    return plan


def build_tandem_validate_report(
    *,
    plan: dict[str, object],
    execution: TandemValidateExecution,
) -> dict[str, object]:
    """Build the tandem-validation report payload."""
    report: dict[str, object] = {}
    report["command"] = "tandem-validate"
    report["timestamp"] = execution.timestamp
    report["ok"] = execution.ok
    report["lane"] = plan.get("lane")
    report["bundle"] = plan.get("bundle")
    report["policy_warnings"] = plan.get("policy_warnings", [])
    report["since_ref"] = plan.get("since_ref")
    report["head_ref"] = plan.get("head_ref")
    report["changed_paths"] = plan.get("changed_paths", [])
    report["reasons"] = plan.get("reasons", [])
    report["risk_addons"] = plan.get("risk_addons", [])
    report["planned_commands"] = plan.get("planned_commands", [])
    report["dry_run"] = execution.dry_run
    report["keep_going"] = execution.keep_going
    report["quality_policy"] = execution.quality_policy
    report["steps"] = execution.steps
    report["error"] = plan.get("error")
    return report


def render_tandem_validate_markdown(report: dict[str, object]) -> str:
    """Render the tandem-validation report in markdown."""
    lines = ["# devctl tandem-validate", ""]
    lines.append(f"- timestamp: {report['timestamp']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- lane: {report.get('lane')}")
    lines.append(f"- bundle: {report.get('bundle')}")
    lines.append(
        f"- commit_range: {report.get('since_ref') or 'None'}...{report.get('head_ref') or 'HEAD'}"
    )
    lines.append(f"- changed_paths: {len(report.get('changed_paths', []))}")
    lines.append(f"- dry_run: {report['dry_run']}")
    lines.append(f"- keep_going: {report['keep_going']}")
    lines.append(
        f"- quality_policy: {report.get('quality_policy') or '(repo default)'}"
    )
    lines.append("")
    if report.get("policy_warnings"):
        lines.append("## Policy Warnings")
        for warning in report["policy_warnings"]:
            lines.append(f"- {warning}")
        lines.append("")
    if report.get("reasons"):
        lines.append("## Why This Lane")
        for reason in report["reasons"]:
            lines.append(f"- {reason}")
        lines.append("")
    if report.get("risk_addons"):
        lines.append("## Risk Add-ons")
        for addon in report["risk_addons"]:
            lines.append(f"- `{addon['id']}`: {addon['label']}")
            lines.append(
                f"- `{addon['id']}` paths: {', '.join(addon['matched_paths'])}"
            )
        lines.append("")
    lines.append("## Discipline")
    lines.append(
        "- Read the full output from each delegated command; do not validate by grepping for `ok:` or `step failed`."
    )
    lines.append(
        "- This lane derives its core command set from `check-router`, then appends final live-loop guards so bridge/tandem truth is rechecked after the routed bundle finishes."
    )
    lines.append("")
    lines.append("## Planned Commands")
    for row in report.get("planned_commands", []):
        lines.append(f"- `{row['source']}` -> `{row['command']}`")
    if report["steps"]:
        lines.append("")
        lines.append("## Steps")
    for step in report["steps"]:
        status = "ok" if step["returncode"] == 0 else "failed"
        lines.append(
            f"- `{step['name']}`: {status} ({step['duration_s']}s) — `{step['source']}` -> `{step['command']}`"
        )
        if step.get("failure_output"):
            lines.append(f"  failure_output: `{step['failure_output']}`")
    return "\n".join(lines)


def _build_planned_rows(
    *,
    bundle_name: str,
    bundle_commands: list[str],
    risk_addons: list[dict[str, object]],
    quality_policy_path: str | None,
) -> list[dict[str, object]]:
    planned_rows = _build_preflight_rows(quality_policy_path)
    planned_rows.extend(
        _make_command_row(
            source=bundle_name,
            command=normalize_repo_python_command(
                inject_quality_policy(command, quality_policy_path)
            ),
        )
        for command in bundle_commands
    )
    for addon in risk_addons:
        planned_rows.extend(
            _make_command_row(
                source=str(addon["id"]),
                command=normalize_repo_python_command(
                    inject_quality_policy(command, quality_policy_path)
                ),
            )
            for command in addon["commands"]
        )
    planned_rows.extend(_build_postflight_rows())
    return dedupe_tandem_validate_rows(planned_rows)


def _build_preflight_rows(
    quality_policy_path: str | None,
) -> list[dict[str, object]]:
    return [
        _make_command_row(
            source="tandem-preflight",
            command=normalize_repo_python_command(
                inject_quality_policy(
                    "python3 dev/scripts/devctl.py quality-policy --format md",
                    quality_policy_path,
                )
            ),
        ),
        _make_command_row(
            source="tandem-preflight",
            command=normalize_repo_python_command(
                "python3 dev/scripts/devctl.py review-channel --action status "
                "--terminal none --format json"
            ),
        ),
    ]


def _build_postflight_rows() -> list[dict[str, object]]:
    return [
        _make_command_row(
            source="tandem-postflight",
            command=normalize_repo_python_command(
                "python3 dev/scripts/checks/check_review_channel_bridge.py --format md"
            ),
            force_rerun=True,
        ),
        _make_command_row(
            source="tandem-postflight",
            command=normalize_repo_python_command(
                "python3 dev/scripts/checks/check_tandem_consistency.py --format md"
            ),
            force_rerun=True,
        ),
    ]


def _make_command_row(
    *,
    source: str,
    command: str,
    force_rerun: bool = False,
) -> dict[str, object]:
    row = {"source": source, "command": command}
    if force_rerun:
        row["force_rerun"] = True
    return row


def _error_plan(
    *,
    router_config,
    since_ref: str | None,
    head_ref: str,
    error: str,
) -> dict[str, object]:
    plan: dict[str, object] = {}
    plan["ok"] = False
    plan["lane"] = "tooling"
    plan["bundle"] = router_config.bundle_by_lane["tooling"]
    plan["policy_path"] = router_config.policy_path
    plan["policy_warnings"] = list(router_config.warnings)
    plan["since_ref"] = since_ref
    plan["head_ref"] = head_ref
    plan["changed_paths"] = []
    plan["categories"] = {}
    plan["reasons"] = []
    plan["risk_addons"] = []
    plan["planned_commands"] = []
    plan["error"] = error
    return plan
