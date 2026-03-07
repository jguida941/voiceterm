"""devctl release-gates command implementation."""

from __future__ import annotations

import json

from ..common import pipe_output, run_cmd, write_output
from ..time_utils import utc_timestamp
from ..config import REPO_ROOT
from ..script_catalog import check_script_cmd

DEFAULT_WAIT_SECONDS = 1800
DEFAULT_POLL_SECONDS = 20
DEFAULT_RELEASE_PREFLIGHT_WORKFLOW = "release_preflight.yml"


def _build_gate_cmd(
    *,
    script_id: str,
    branch: str,
    sha: str,
    wait_seconds: int,
    poll_seconds: int,
    allow_branch_fallback: bool,
    repo: str | None = None,
    workflow: str | None = None,
) -> list[str]:
    cmd = check_script_cmd(
        script_id,
        "--branch",
        branch,
        "--sha",
        sha,
        "--wait-seconds",
        str(wait_seconds),
        "--poll-seconds",
        str(poll_seconds),
        "--format",
        "md",
    )
    if repo:
        cmd.extend(["--repo", repo])
    if workflow:
        cmd.extend(["--workflow", workflow])
    if allow_branch_fallback:
        cmd.append("--allow-branch-fallback")
    return cmd


def _render_md(report: dict) -> str:
    lines = ["# devctl release-gates", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- branch: {report['branch']}")
    lines.append(f"- sha: {report['sha']}")
    lines.append(f"- wait_seconds: {report['wait_seconds']}")
    lines.append(f"- poll_seconds: {report['poll_seconds']}")
    lines.append(f"- allow_branch_fallback: {report['allow_branch_fallback']}")
    lines.append(f"- require_preflight: {report['require_preflight']}")
    lines.append("")
    lines.append("| Step | Status | Exit | Duration (s) |")
    lines.append("|---|---|---:|---:|")
    for step in report["steps"]:
        status = "ok" if step["returncode"] == 0 else "failed"
        lines.append(
            f"| `{step['name']}` | {status} | {step['returncode']} | {step['duration_s']} |"
        )
        failure_output = step.get("failure_output")
        if failure_output:
            escaped_failure_output = failure_output.replace("`", "\\`")
            lines.append(f"| `{step['name']} output` | excerpt | - | - |")
            lines.append(f"|  | `{escaped_failure_output}` | - | - |")
    if report.get("failure_reason"):
        lines.append("")
        lines.append(f"- failure_reason: {report['failure_reason']}")
    return "\n".join(lines)


def run(args) -> int:
    """Run release commit gates used by publish/release workflows."""
    steps: list[dict] = []
    wait_seconds = int(getattr(args, "wait_seconds", DEFAULT_WAIT_SECONDS) or 0)
    poll_seconds = int(getattr(args, "poll_seconds", DEFAULT_POLL_SECONDS) or 1)
    allow_branch_fallback = bool(getattr(args, "allow_branch_fallback", False))
    require_preflight = not bool(getattr(args, "skip_preflight", False))

    planned_steps: list[tuple[str, list[str]]] = [
        (
            "coderabbit-gate",
            _build_gate_cmd(
                script_id="coderabbit_gate",
                branch=args.branch,
                sha=args.sha,
                wait_seconds=wait_seconds,
                poll_seconds=poll_seconds,
                allow_branch_fallback=allow_branch_fallback,
                repo=args.repo,
            ),
        ),
    ]
    if require_preflight:
        planned_steps.append(
            (
                "release-preflight-gate",
                _build_gate_cmd(
                    script_id="coderabbit_gate",
                    workflow=args.preflight_workflow,
                    branch=args.branch,
                    sha=args.sha,
                    wait_seconds=wait_seconds,
                    poll_seconds=poll_seconds,
                    allow_branch_fallback=allow_branch_fallback,
                    repo=args.repo,
                ),
            )
        )
    planned_steps.append(
        (
            "coderabbit-ralph-gate",
            _build_gate_cmd(
                script_id="coderabbit_ralph_gate",
                branch=args.branch,
                sha=args.sha,
                wait_seconds=wait_seconds,
                poll_seconds=poll_seconds,
                allow_branch_fallback=allow_branch_fallback,
                repo=args.repo,
            ),
        )
    )

    failure_reason = ""
    for name, cmd in planned_steps:
        result = run_cmd(name, cmd, cwd=REPO_ROOT, dry_run=args.dry_run)
        steps.append(result)
        if result["returncode"] != 0:
            failure_reason = f"{name} failed"
            break

    ok = bool(steps) and all(step["returncode"] == 0 for step in steps)
    report = {
        "command": "release-gates",
        "timestamp": utc_timestamp(),
        "ok": ok,
        "branch": args.branch,
        "sha": args.sha,
        "repo": args.repo,
        "allow_branch_fallback": allow_branch_fallback,
        "require_preflight": require_preflight,
        "preflight_workflow": args.preflight_workflow,
        "wait_seconds": wait_seconds,
        "poll_seconds": poll_seconds,
        "steps": steps,
        "failure_reason": failure_reason,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)

    write_output(output, args.output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc
    return 0 if ok else 1
