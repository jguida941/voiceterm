"""Shared parsing helpers for check_architecture_surface_sync."""

from __future__ import annotations

import ast
import re
import subprocess
from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path


def workflow_files(repo_root: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in (".github/workflows/*.yml", ".github/workflows/*.yaml"):
        paths.update(repo_root.glob(pattern))
    return sorted(paths)


def run_git(repo_root: Path, cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def normalize_path(repo_root: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.relative_to(repo_root)
    return path


def discover_new_paths(
    repo_root: Path,
    *,
    since_ref: str | None,
    head_ref: str,
) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    candidates: set[Path] = set()

    diff_cmd = ["git", "diff", "--name-only", "--diff-filter=A"]
    if since_ref:
        diff_cmd.extend([since_ref, head_ref])
    else:
        diff_cmd.append("HEAD")
    diff_result = run_git(repo_root, diff_cmd)
    if diff_result.returncode != 0:
        errors.append(diff_result.stderr.strip() or "git diff failed")
    else:
        for line in diff_result.stdout.splitlines():
            stripped = line.strip()
            if stripped:
                candidates.add(Path(stripped))

    untracked_result = run_git(
        repo_root,
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    if untracked_result.returncode != 0:
        errors.append(untracked_result.stderr.strip() or "git ls-files failed")
    else:
        for line in untracked_result.stdout.splitlines():
            stripped = line.strip()
            if stripped:
                candidates.add(Path(stripped))

    return sorted(candidates), errors


def path_matches(path: Path, patterns: tuple[str, ...]) -> bool:
    path_text = path.as_posix()
    return any(fnmatch(path_text, pattern) for pattern in patterns)


def is_allowlisted(
    path: Path,
    zone_id: str,
    allowlist: dict[str, tuple[str, ...]],
) -> bool:
    return path_matches(path, allowlist.get(zone_id, ()))


def reference_tokens(path: Path) -> tuple[str, ...]:
    filename = path.name
    return (path.as_posix(), f"active/{filename}", filename)


def contains_any_token(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def collect_devctl_commands(command_pattern: re.Pattern[str], text: str) -> set[str]:
    return {match.group("command") for match in command_pattern.finditer(text)}


def command_module_key(path: Path) -> str:
    module_path = path.relative_to("dev/scripts/devctl").with_suffix("")
    return ".".join(module_path.parts)


def extract_cli_command_bindings(cli_text: str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    aliases: dict[str, list[str]] = defaultdict(list)
    handlers: dict[str, list[str]] = defaultdict(list)
    try:
        module = ast.parse(cli_text)
    except SyntaxError:
        pattern = re.compile(r'["\']([^"\']+)["\']\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\.run')
        for command_name, module_name in pattern.findall(cli_text):
            handlers[module_name].append(command_name)
        return {}, dict(handlers)

    for node in ast.walk(module):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level != 1 or node.module is None or (
            node.module != "commands" and not node.module.startswith("commands.")
        ):
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            module_key = f"{node.module}.{alias.name}"
            local_name = alias.asname or alias.name
            if local_name not in aliases[module_key]:
                aliases[module_key].append(local_name)

    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Dict) or not any(
            isinstance(target, ast.Name) and target.id == "COMMAND_HANDLERS"
            for target in node.targets
        ):
            continue
        for key_node, value_node in zip(node.value.keys, node.value.values):
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                continue
            if not isinstance(value_node, ast.Attribute) or value_node.attr != "run":
                continue
            if not isinstance(value_node.value, ast.Name):
                continue
            handlers[value_node.value.id].append(key_node.value)
    return dict(aliases), dict(handlers)


def has_run_entrypoint(source_text: str) -> bool:
    return re.search(r"^def\s+run\s*\(", source_text, re.MULTILINE) is not None


def app_reference_tokens(path: Path) -> tuple[str, ...]:
    parts = path.parts
    tokens: list[str] = [path.as_posix()]
    for index in range(len(parts) - 1, 1, -1):
        prefix = "/".join(parts[:index])
        if prefix != "app":
            tokens.append(prefix)
    return tuple(tokens)
