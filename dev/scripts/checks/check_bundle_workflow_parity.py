#!/usr/bin/env python3
"""Validate registered command-bundle parity against CI workflow run steps."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
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


def build_report() -> dict:
    report = {
        "command": "check_bundle_workflow_parity",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "bundle_registry": BUNDLE_AUTHORITY_PATH,
        "ok": True,
        "targets": [],
        "errors": [],
    }

    for target in BUNDLE_WORKFLOW_TARGETS:
        bundle_name = target["bundle"]
        workflow_rel = target["workflow"]
        workflow_path = REPO_ROOT / workflow_rel

        target_report = {
            "bundle": bundle_name,
            "workflow": workflow_rel,
            "command_count": 0,
            "run_scope_count": 0,
            "missing_commands": [],
            "ok": True,
            "error": None,
        }

        commands, command_error = _get_registered_bundle_commands(bundle_name)
        target_report["command_count"] = len(commands)
        if command_error is not None:
            target_report["ok"] = False
            target_report["error"] = command_error
            report["ok"] = False
            report["targets"].append(target_report)
            continue

        if not workflow_path.exists():
            target_report["ok"] = False
            target_report["error"] = f"Missing workflow file: {workflow_rel}"
            report["ok"] = False
            report["targets"].append(target_report)
            continue

        workflow_run_scopes = _extract_workflow_run_scopes(
            workflow_path.read_text(encoding="utf-8")
        )
        target_report["run_scope_count"] = len(workflow_run_scopes)
        if not workflow_run_scopes:
            target_report["ok"] = False
            target_report["error"] = (
                f"Unable to locate `run` steps in workflow: {workflow_rel}"
            )
            report["ok"] = False
            report["targets"].append(target_report)
            continue
        missing: list[str] = []
        for command in commands:
            matched = any(
                command == scope
                or command in scope
                or _is_token_subsequence(command, scope)
                for scope in workflow_run_scopes
            )
            if not matched:
                missing.append(command)

        target_report["missing_commands"] = missing
        target_report["ok"] = not missing
        if missing:
            report["ok"] = False

        report["targets"].append(target_report)

    return report


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
            ]
        )
        error = target.get("error")
        if error:
            lines.append(f"- error: {error}")
        missing_commands = target.get("missing_commands", [])
        lines.append(
            "- missing_commands: "
            + (str(len(missing_commands)) if missing_commands else "0")
        )
        for command in missing_commands:
            lines.append(f"- missing: `{command}`")

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
