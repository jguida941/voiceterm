"""Scope/sequence helpers for bundle/workflow parity checks."""

from __future__ import annotations

if __package__:
    from .parser import _normalize_command
else:  # pragma: no cover - standalone script fallback
    from parser import _normalize_command


def _is_token_subsequence(command: str, workflow_text: str) -> bool:
    command_tokens = command.split()
    workflow_tokens = workflow_text.split()
    if not command_tokens:
        return True
    command_index = 0
    for token in workflow_tokens:
        if token == command_tokens[command_index]:
            command_index += 1
            if command_index == len(command_tokens):
                return True
    return False


def _command_matches_scope(command: str, scope: str) -> bool:
    return command == scope or command in scope or _is_token_subsequence(command, scope)


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
        scope_index = 0
        for command in sequence:
            match_index = _find_matching_scope_index(
                command,
                scopes,
                start_index=scope_index,
            )
            if match_index is not None:
                scope_index = match_index + 1
                continue
            if _find_matching_scope_index(command, scopes) is None:
                missing_job_sequences.setdefault(job_name, []).append(command)
            else:
                job_sequence_order_errors.setdefault(job_name, []).append(command)
    return missing_job_sequences, job_sequence_order_errors
