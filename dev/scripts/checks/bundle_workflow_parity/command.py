#!/usr/bin/env python3
"""Validate registered command-bundle parity against CI workflow run steps."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.bundle_registry import (
    BUNDLE_AUTHORITY_PATH,
    get_bundle_commands,
)
if __package__:
    from .parser import (
        _extract_workflow_job_scopes,
        _extract_workflow_run_scopes,
        _normalize_command,
    )
    from .paths import (
        _collect_missing_path_filters,
        _extract_workflow_trigger_paths,
    )
    from .sequences import (
        _collect_job_sequence_issues,
        _missing_scope_commands,
        _normalized_target_commands,
        _resolve_required_job_sequences,
    )
else:  # pragma: no cover - standalone script fallback
    from parser import (
        _extract_workflow_job_scopes,
        _extract_workflow_run_scopes,
        _normalize_command,
    )
    from paths import (
        _collect_missing_path_filters,
        _extract_workflow_trigger_paths,
    )
    from sequences import (
        _collect_job_sequence_issues,
        _missing_scope_commands,
        _normalized_target_commands,
        _resolve_required_job_sequences,
    )

BUNDLE_WORKFLOW_TARGETS = (
    {
        "bundle": "bundle.tooling",
        "workflow": ".github/workflows/tooling_control_plane.yml",
        "required_extra_commands": (
            "python3 dev/scripts/checks/check_publication_sync.py",
        ),
        "required_path_filters": (
            "dev/config/publication_sync_registry.json",
            "scripts/operator_console.sh",
        ),
        "required_trigger_events": ("push", "pull_request"),
        "required_job_sequences": {
            "docs-policy": {
                "bundle_commands": "all",
                "exclude_commands": (
                    "python3 -m pytest app/operator_console/tests/ -q --tb=short",
                ),
            },
            "operator-console-tests": {
                "commands": (
                    "python3 -m pytest app/operator_console/tests/ -q --tb=short",
                ),
            },
        },
    },
    {
        "bundle": "bundle.release",
        "workflow": ".github/workflows/release_preflight.yml",
    },
)


def _get_registered_bundle_commands(bundle_name: str) -> tuple[list[str], str | None]:
    try:
        commands = get_bundle_commands(bundle_name)
    except KeyError:
        return (
            [],
            f"bundle `{bundle_name}` is not registered in {BUNDLE_AUTHORITY_PATH}",
        )

    normalized: list[str] = []
    for command in commands:
        normalized_command = _normalize_command(command)
        if normalized_command:
            normalized.append(normalized_command)
    if not normalized:
        return (
            [],
            f"bundle `{bundle_name}` has no executable commands in {BUNDLE_AUTHORITY_PATH}",
        )
    return normalized, None


def _new_target_report(bundle_name: str, workflow_rel: str) -> dict:
    return {
        "bundle": bundle_name,
        "workflow": workflow_rel,
        "command_count": 0,
        "run_scope_count": 0,
        "configured_trigger_paths": {},
        "missing_commands": [],
        "required_extra_command_count": 0,
        "missing_extra_commands": [],
        "required_path_filter_count": 0,
        "missing_path_filters": [],
        "missing_trigger_path_filters": {},
        "ok": True,
        "error": None,
    }


def _finalize_target_error(target_report: dict, error: str) -> dict:
    target_report["ok"] = False
    target_report["error"] = error
    return target_report


def _evaluate_target(target: dict) -> dict:
    bundle_name = target["bundle"]
    workflow_rel = target["workflow"]
    workflow_path = REPO_ROOT / workflow_rel
    target_report = _new_target_report(bundle_name, workflow_rel)

    commands, command_error = _get_registered_bundle_commands(bundle_name)
    target_report["command_count"] = len(commands)
    if command_error is not None:
        return _finalize_target_error(target_report, command_error)
    if not workflow_path.exists():
        return _finalize_target_error(
            target_report,
            f"Missing workflow file: {workflow_rel}",
        )

    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow_run_scopes = _extract_workflow_run_scopes(workflow_text)
    workflow_job_scopes = _extract_workflow_job_scopes(workflow_text)
    workflow_trigger_paths = _extract_workflow_trigger_paths(workflow_text)
    target_report["run_scope_count"] = len(workflow_run_scopes)
    target_report["job_scope_counts"] = {
        job_name: len(scopes)
        for job_name, scopes in sorted(workflow_job_scopes.items())
    }
    target_report["configured_trigger_paths"] = workflow_trigger_paths
    if not workflow_run_scopes:
        return _finalize_target_error(
            target_report,
            f"Unable to locate `run` steps in workflow: {workflow_rel}",
        )

    missing_commands = _missing_scope_commands(commands, workflow_run_scopes)
    extra_commands = _normalized_target_commands(target, "required_extra_commands")
    missing_extra_commands = _missing_scope_commands(extra_commands, workflow_run_scopes)
    missing_path_filters, missing_trigger_path_filters = _collect_missing_path_filters(
        target=target,
        workflow_text=workflow_text,
        workflow_trigger_paths=workflow_trigger_paths,
    )
    missing_job_sequences, job_sequence_order_errors = _collect_job_sequence_issues(
        target=target,
        commands=commands,
        workflow_job_scopes=workflow_job_scopes,
    )

    target_report["missing_commands"] = missing_commands
    target_report["required_extra_command_count"] = len(extra_commands)
    target_report["missing_extra_commands"] = missing_extra_commands
    target_report["required_path_filter_count"] = len(
        target.get("required_path_filters", ())
    )
    target_report["missing_path_filters"] = missing_path_filters
    target_report["missing_trigger_path_filters"] = missing_trigger_path_filters
    target_report["required_job_sequence_count"] = len(
        _resolve_required_job_sequences(target, bundle_commands=commands)
    )
    target_report["missing_job_sequences"] = missing_job_sequences
    target_report["job_sequence_order_errors"] = job_sequence_order_errors
    target_report["ok"] = not any(
        (
            missing_commands,
            missing_extra_commands,
            missing_path_filters,
            missing_trigger_path_filters,
            missing_job_sequences,
            job_sequence_order_errors,
        )
    )
    return target_report


def build_report() -> dict:
    targets = [_evaluate_target(target) for target in BUNDLE_WORKFLOW_TARGETS]
    return {
        "command": "check_bundle_workflow_parity",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "bundle_registry": BUNDLE_AUTHORITY_PATH,
        "ok": all(target["ok"] for target in targets),
        "targets": targets,
        "errors": [],
    }


def render_markdown(report: dict) -> str:
    lines = ["# check_bundle_workflow_parity", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- bundle_registry: {report.get('bundle_registry')}")
    targets = report.get("targets", [])
    lines.append(f"- targets: {len(targets)}")

    errors = report.get("errors", [])
    if errors:
        lines.append(f"- errors: {' | '.join(errors)}")

    for target in targets:
        lines.extend(
            [
                "",
                f"## {target.get('bundle')} -> {target.get('workflow')}",
                f"- ok: {target.get('ok')}",
                f"- command_count: {target.get('command_count')}",
                f"- run_scope_count: {target.get('run_scope_count')}",
                f"- required_extra_command_count: {target.get('required_extra_command_count')}",
                f"- required_path_filter_count: {target.get('required_path_filter_count')}",
                f"- required_job_sequence_count: {target.get('required_job_sequence_count', 0)}",
            ]
        )
        error = target.get("error")
        if error:
            lines.append(f"- error: {error}")
        configured_trigger_paths = target.get("configured_trigger_paths", {})
        if configured_trigger_paths:
            lines.append(
                "- trigger_events: " + ", ".join(sorted(configured_trigger_paths))
            )
        job_scope_counts = target.get("job_scope_counts", {})
        if job_scope_counts:
            lines.append(
                "- job_scope_counts: "
                + ", ".join(
                    f"{job_name}={job_scope_counts[job_name]}"
                    for job_name in sorted(job_scope_counts)
                )
            )
        missing_commands = target.get("missing_commands", [])
        lines.append(
            "- missing_commands: "
            + (str(len(missing_commands)) if missing_commands else "0")
        )
        for command in missing_commands:
            lines.append(f"- missing: `{command}`")
        missing_extra_commands = target.get("missing_extra_commands", [])
        lines.append(
            "- missing_extra_commands: "
            + (str(len(missing_extra_commands)) if missing_extra_commands else "0")
        )
        for command in missing_extra_commands:
            lines.append(f"- missing_extra_command: `{command}`")
        missing_path_filters = target.get("missing_path_filters", [])
        lines.append(
            "- missing_path_filters: "
            + (str(len(missing_path_filters)) if missing_path_filters else "0")
        )
        for path_filter in missing_path_filters:
            lines.append(f"- missing_path_filter: `{path_filter}`")
        missing_trigger_path_filters = target.get("missing_trigger_path_filters", {})
        missing_trigger_total = sum(
            len(paths) for paths in missing_trigger_path_filters.values()
        )
        lines.append(
            "- missing_trigger_path_filters: "
            + (str(missing_trigger_total) if missing_trigger_total else "0")
        )
        for event_name in sorted(missing_trigger_path_filters):
            for path_filter in missing_trigger_path_filters[event_name]:
                lines.append(
                    f"- missing_trigger_path_filter[{event_name}]: `{path_filter}`"
                )
        missing_job_sequences = target.get("missing_job_sequences", {})
        missing_job_total = sum(
            len(commands) for commands in missing_job_sequences.values()
        )
        lines.append(
            "- missing_job_sequences: "
            + (str(missing_job_total) if missing_job_total else "0")
        )
        for job_name in sorted(missing_job_sequences):
            for command in missing_job_sequences[job_name]:
                lines.append(
                    f"- missing_job_sequence[{job_name}]: `{command}`"
                )
        job_sequence_order_errors = target.get("job_sequence_order_errors", {})
        order_error_total = sum(
            len(commands) for commands in job_sequence_order_errors.values()
        )
        lines.append(
            "- job_sequence_order_errors: "
            + (str(order_error_total) if order_error_total else "0")
        )
        for job_name in sorted(job_sequence_order_errors):
            for command in job_sequence_order_errors[job_name]:
                lines.append(
                    f"- job_sequence_order_error[{job_name}]: `{command}`"
                )

    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
