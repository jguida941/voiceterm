#!/usr/bin/env python3
"""Validate registered command-bundle parity against CI workflow run steps."""

from __future__ import annotations

import argparse
import json
import re
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

RUN_STEP_RE = re.compile(r"^(?P<indent>\s*)(?:-\s*)?run:\s*(?P<value>.*)$")

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


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _normalize_command(command: str) -> str:
    tokens = command.strip().split()
    while tokens and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]):
        tokens.pop(0)
    return _normalize_space(" ".join(tokens))


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


def _normalize_workflow_text(raw_text: str) -> str:
    # Normalize escaped multiline shell commands for substring matching.
    normalized = raw_text.replace("\\\n", " ").replace("\\\r\n", " ")
    return _normalize_space(normalized)


def _is_yaml_block_scalar(value: str) -> bool:
    stripped = value.strip()
    return stripped.startswith("|") or stripped.startswith(">")


def _dedent_yaml_block(lines: list[str]) -> str:
    min_indent: int | None = None
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if min_indent is None or indent < min_indent:
            min_indent = indent
    if min_indent is None:
        return ""
    dedented_lines = [line[min_indent:] if line.strip() else "" for line in lines]
    return "\n".join(dedented_lines)


def _extract_workflow_run_scopes(workflow_text: str) -> list[str]:
    lines = workflow_text.splitlines()
    scopes: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = RUN_STEP_RE.match(line)
        if match is None:
            index += 1
            continue
        run_indent = len(match.group("indent"))
        run_value = match.group("value").strip()
        if _is_yaml_block_scalar(run_value):
            index += 1
            block_lines: list[str] = []
            while index < len(lines):
                next_line = lines[index]
                next_stripped = next_line.strip()
                if next_stripped:
                    next_indent = len(next_line) - len(next_line.lstrip(" "))
                    if next_indent <= run_indent:
                        break
                block_lines.append(next_line)
                index += 1
            normalized_scope = _normalize_workflow_text(_dedent_yaml_block(block_lines))
            if normalized_scope:
                scopes.append(normalized_scope)
            continue
        if run_value:
            normalized_scope = _normalize_workflow_text(run_value.strip("'\""))
            if normalized_scope:
                scopes.append(normalized_scope)
        index += 1
    return scopes


def _extract_workflow_job_scopes(workflow_text: str) -> dict[str, list[str]]:
    lines = workflow_text.splitlines()
    job_scopes: dict[str, list[str]] = {}
    index = 0

    while index < len(lines):
        line = lines[index]
        if line.strip() != "jobs:":
            index += 1
            continue
        jobs_indent = len(line) - len(line.lstrip(" "))
        index += 1

        while index < len(lines):
            job_line = lines[index]
            job_stripped = job_line.strip()
            if not job_stripped:
                index += 1
                continue
            job_indent = len(job_line) - len(job_line.lstrip(" "))
            if job_indent <= jobs_indent:
                break
            if job_indent != jobs_indent + 2 or not job_stripped.endswith(":"):
                index += 1
                continue

            job_name = job_stripped[:-1]
            index += 1
            job_lines: list[str] = []
            while index < len(lines):
                nested_line = lines[index]
                nested_stripped = nested_line.strip()
                nested_indent = len(nested_line) - len(nested_line.lstrip(" "))
                if nested_stripped and nested_indent <= job_indent:
                    break
                job_lines.append(nested_line)
                index += 1

            scopes = _extract_workflow_run_scopes("\n".join(job_lines))
            if scopes:
                job_scopes[job_name] = scopes
        break

    return job_scopes


def _strip_yaml_quotes(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        return stripped[1:-1]
    return stripped


def _extract_workflow_trigger_paths(workflow_text: str) -> dict[str, list[str]]:
    lines = workflow_text.splitlines()
    trigger_paths: dict[str, list[str]] = {}
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped != "on:":
            index += 1
            continue
        on_indent = len(line) - len(line.lstrip(" "))
        index += 1

        while index < len(lines):
            event_line = lines[index]
            event_stripped = event_line.strip()
            if not event_stripped:
                index += 1
                continue
            event_indent = len(event_line) - len(event_line.lstrip(" "))
            if event_indent <= on_indent:
                break
            if not event_stripped.endswith(":"):
                index += 1
                continue
            event_name = event_stripped[:-1]
            index += 1

            while index < len(lines):
                nested_line = lines[index]
                nested_stripped = nested_line.strip()
                if not nested_stripped:
                    index += 1
                    continue
                nested_indent = len(nested_line) - len(nested_line.lstrip(" "))
                if nested_indent <= event_indent:
                    break
                if event_name not in {"push", "pull_request"}:
                    index += 1
                    continue
                if nested_stripped != "paths:":
                    index += 1
                    continue
                paths_indent = nested_indent
                index += 1
                paths: list[str] = []
                while index < len(lines):
                    path_line = lines[index]
                    path_stripped = path_line.strip()
                    if not path_stripped:
                        index += 1
                        continue
                    path_indent = len(path_line) - len(path_line.lstrip(" "))
                    if path_indent <= paths_indent:
                        break
                    if path_stripped.startswith("- "):
                        path_value = _strip_yaml_quotes(path_stripped[2:])
                        if path_value:
                            paths.append(path_value)
                    index += 1
                trigger_paths[event_name] = paths
                continue
        break

    return trigger_paths


def _command_matches_scope(command: str, scope: str) -> bool:
    return (
        command == scope
        or command in scope
        or _is_token_subsequence(command, scope)
    )


def _find_matching_scope_index(
    command: str,
    scopes: list[str],
    *,
    start_index: int = 0,
) -> int | None:
    for index, scope in enumerate(scopes[start_index:], start=start_index):
        if _command_matches_scope(command, scope):
            return index
    return None


def _resolve_required_job_sequences(
    target: dict,
    *,
    bundle_commands: list[str],
) -> dict[str, list[str]]:
    resolved: dict[str, list[str]] = {}
    for job_name, spec in target.get("required_job_sequences", {}).items():
        if isinstance(spec, dict):
            if spec.get("bundle_commands") == "all":
                excluded = {
                    _normalize_command(command)
                    for command in spec.get("exclude_commands", ())
                    if _normalize_command(command)
                }
                commands = [
                    command
                    for command in bundle_commands
                    if _normalize_command(command) not in excluded
                ]
            else:
                commands = []
            explicit_commands = [
                _normalize_command(command)
                for command in spec.get("commands", ())
                if _normalize_command(command)
            ]
            if explicit_commands:
                commands.extend(explicit_commands)
        else:
            commands = [
                _normalize_command(command)
                for command in spec
                if _normalize_command(command)
            ]
        if commands:
            resolved[job_name] = commands
    return resolved


def _is_token_subsequence(command: str, workflow_text: str) -> bool:
    command_tokens = command.split()
    workflow_tokens = workflow_text.split()
    if not command_tokens:
        return True
    cursor = 0
    for token in workflow_tokens:
        if token == command_tokens[cursor]:
            cursor += 1
            if cursor == len(command_tokens):
                return True
    return False


def _has_workflow_path_filter(workflow_text: str, path_filter: str) -> bool:
    pattern = re.compile(
        rf"^\s*-\s*[\"']?{re.escape(path_filter)}[\"']?\s*$",
        re.MULTILINE,
    )
    return pattern.search(workflow_text) is not None


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


def _missing_scope_commands(commands: list[str], scopes: list[str]) -> list[str]:
    return [
        command
        for command in commands
        if not any(_command_matches_scope(command, scope) for scope in scopes)
    ]


def _normalized_target_commands(target: dict, field_name: str) -> list[str]:
    return [
        _normalize_command(command)
        for command in target.get(field_name, ())
        if _normalize_command(command)
    ]


def _collect_missing_path_filters(
    *,
    target: dict,
    workflow_text: str,
    workflow_trigger_paths: dict[str, list[str]],
) -> tuple[list[str], dict[str, list[str]]]:
    required_path_filters = list(target.get("required_path_filters", ()))
    required_trigger_events = tuple(target.get("required_trigger_events", ()))
    missing_trigger_path_filters: dict[str, list[str]] = {}
    if required_trigger_events:
        for event_name in required_trigger_events:
            configured_paths = workflow_trigger_paths.get(event_name, [])
            missing_paths = [
                path_filter
                for path_filter in required_path_filters
                if path_filter not in configured_paths
            ]
            if missing_paths:
                missing_trigger_path_filters[event_name] = missing_paths
        return [], missing_trigger_path_filters
    missing_path_filters = [
        path_filter
        for path_filter in required_path_filters
        if not _has_workflow_path_filter(workflow_text, path_filter)
    ]
    return missing_path_filters, missing_trigger_path_filters


def _collect_job_sequence_issues(
    *,
    target: dict,
    commands: list[str],
    workflow_job_scopes: dict[str, list[str]],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    required_job_sequences = _resolve_required_job_sequences(
        target,
        bundle_commands=commands,
    )
    missing_job_sequences: dict[str, list[str]] = {}
    job_sequence_order_errors: dict[str, list[str]] = {}
    for job_name, sequence in required_job_sequences.items():
        scopes = workflow_job_scopes.get(job_name, [])
        if not scopes:
            missing_job_sequences[job_name] = list(sequence)
            continue
        cursor = 0
        for command in sequence:
            match_index = _find_matching_scope_index(
                command,
                scopes,
                start_index=cursor,
            )
            if match_index is not None:
                cursor = match_index + 1
                continue
            if _find_matching_scope_index(command, scopes) is None:
                missing_job_sequences.setdefault(job_name, []).append(command)
            else:
                job_sequence_order_errors.setdefault(job_name, []).append(command)
    return missing_job_sequences, job_sequence_order_errors


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
