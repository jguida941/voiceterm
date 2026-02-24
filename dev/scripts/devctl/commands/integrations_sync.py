"""`devctl integrations-sync` command implementation."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ..common import pipe_output, run_cmd, write_output
from ..config import REPO_ROOT
from ..integration_federation_policy import (
    federation_audit_log_path,
    federation_sources,
    load_federation_policy,
    source_repo_path,
)


def _run_git_capture(args: list[str], *, cwd: Path = REPO_ROOT) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, (completed.stdout or "").strip(), (completed.stderr or "").strip()


def _append_audit_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


def _selected_sources(
    all_sources: dict[str, dict[str, Any]],
    requested: list[str] | None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if requested:
        selected = []
        seen: set[str] = set()
        for item in requested:
            name = str(item).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            selected.append(name)
    else:
        selected = sorted(all_sources.keys())

    for name in selected:
        if name not in all_sources:
            errors.append(f"Unknown integration source: {name}")
    return selected, errors


def _source_status(
    source_name: str,
    source_cfg: dict[str, Any],
    *,
    policy_audit_log: Path,
) -> dict[str, Any]:
    source_path = source_repo_path(REPO_ROOT, source_cfg)
    url = str(source_cfg.get("url") or "").strip() or None
    row: dict[str, Any] = {
        "source": source_name,
        "path": str(source_path.relative_to(REPO_ROOT)) if source_path else None,
        "url": url,
        "exists": False,
        "sha": None,
        "branch": None,
        "dirty": None,
        "submodule_status": None,
        "errors": [],
    }
    if source_path is None:
        row["errors"].append("Policy source is missing required `path`.")
        return row
    if not source_path.exists():
        row["errors"].append("Source path does not exist.")
        return row
    row["exists"] = True

    code, sha_out, sha_err = _run_git_capture(["rev-parse", "HEAD"], cwd=source_path)
    if code == 0:
        row["sha"] = sha_out
    else:
        row["errors"].append(sha_err or "Unable to read source SHA.")

    code, branch_out, _ = _run_git_capture(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        cwd=source_path,
    )
    if code == 0:
        row["branch"] = branch_out

    code, status_out, status_err = _run_git_capture(
        ["status", "--porcelain"],
        cwd=source_path,
    )
    if code == 0:
        row["dirty"] = bool(status_out)
    else:
        row["errors"].append(status_err or "Unable to read source dirty state.")

    if not row["url"]:
        code, remote_out, _ = _run_git_capture(
            ["config", "--get", "remote.origin.url"],
            cwd=source_path,
        )
        if code == 0 and remote_out:
            row["url"] = remote_out

    rel_path = str(source_path.relative_to(REPO_ROOT))
    code, submodule_out, submodule_err = _run_git_capture(
        ["submodule", "status", "--", rel_path]
    )
    if code == 0:
        row["submodule_status"] = submodule_out
    else:
        row["errors"].append(submodule_err or "Unable to read submodule status.")

    row["policy_audit_log"] = str(policy_audit_log.relative_to(REPO_ROOT))
    return row


def _render_md(report: dict[str, Any]) -> str:
    lines = ["# devctl integrations-sync", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- remote_update: {report['remote_update']}")
    lines.append(f"- dry_run: {report['dry_run']}")
    lines.append(f"- selected_sources: {', '.join(report['selected_sources']) or 'none'}")
    lines.append(f"- audit_log: `{report['audit_log']}`")
    lines.append(f"- errors: {len(report['errors'])}")
    lines.append("")
    lines.append("| Source | Path | SHA | Branch | Dirty | Status |")
    lines.append("|---|---|---|---|---|---|")
    for row in report["sources"]:
        sha = row.get("sha") or "-"
        branch = row.get("branch") or "-"
        dirty = "-" if row.get("dirty") is None else str(bool(row.get("dirty")))
        status = "ok" if not row.get("errors") else "error"
        lines.append(
            f"| `{row.get('source')}` | `{row.get('path')}` | `{sha}` | `{branch}` | `{dirty}` | {status} |"
        )
    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {item}" for item in report["errors"])
    return "\n".join(lines)


def run(args) -> int:
    """Sync pinned integration sources with policy and audit controls."""
    warnings: list[str] = []
    errors: list[str] = []
    steps: list[dict[str, Any]] = []

    policy_section = load_federation_policy(REPO_ROOT)
    sources_cfg = federation_sources(policy_section)
    if not sources_cfg:
        errors.append("No integration_federation.sources configured in policy.")

    selected, source_errors = _selected_sources(sources_cfg, args.source)
    errors.extend(source_errors)
    selected_paths: list[str] = []
    for name in selected:
        cfg = sources_cfg.get(name)
        if not isinstance(cfg, dict):
            continue
        source_path = source_repo_path(REPO_ROOT, cfg)
        if source_path is None:
            errors.append(f"Policy source {name} is missing required `path`.")
            continue
        selected_paths.append(str(source_path.relative_to(REPO_ROOT)))

    if not args.status_only and not errors and selected_paths:
        sync_step = run_cmd(
            "git-submodule-sync",
            ["git", "submodule", "sync", "--", *selected_paths],
            cwd=REPO_ROOT,
            dry_run=args.dry_run,
        )
        steps.append(sync_step)
        if sync_step.get("returncode") != 0:
            errors.append("git submodule sync failed.")

        update_cmd = ["git", "submodule", "update", "--init"]
        if args.remote:
            update_cmd.append("--remote")
        update_cmd.extend(["--", *selected_paths])
        update_step = run_cmd(
            "git-submodule-update",
            update_cmd,
            cwd=REPO_ROOT,
            dry_run=args.dry_run,
        )
        steps.append(update_step)
        if update_step.get("returncode") != 0:
            errors.append("git submodule update failed.")

    audit_log_path = federation_audit_log_path(REPO_ROOT, policy_section)
    sources = []
    for name in selected:
        cfg = sources_cfg.get(name)
        if not isinstance(cfg, dict):
            continue
        row = _source_status(name, cfg, policy_audit_log=audit_log_path)
        if row.get("errors"):
            errors.extend(
                [f"{name}: {message}" for message in row.get("errors", [])]
            )
        sources.append(row)

    report = {
        "command": "integrations-sync",
        "timestamp": datetime.now().isoformat(),
        "ok": len(errors) == 0,
        "mode": "status-only" if args.status_only else "sync",
        "remote_update": bool(args.remote),
        "dry_run": bool(args.dry_run),
        "selected_sources": selected,
        "sources": sources,
        "steps": steps,
        "warnings": warnings,
        "errors": errors,
        "audit_log": str(audit_log_path.relative_to(REPO_ROOT)),
    }
    _append_audit_log(
        audit_log_path,
        {
            "timestamp": report["timestamp"],
            "command": report["command"],
            "mode": report["mode"],
            "remote_update": report["remote_update"],
            "dry_run": report["dry_run"],
            "selected_sources": report["selected_sources"],
            "ok": report["ok"],
            "error_count": len(report["errors"]),
        },
    )

    output = json.dumps(report, indent=2) if args.format == "json" else _render_md(report)
    write_output(output, args.output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 0 if report["ok"] else 1
