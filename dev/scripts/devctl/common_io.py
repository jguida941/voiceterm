"""Shared devctl path, output, env, and shell helpers."""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .config import REPO_ROOT, SRC_DIR

PIPE_OUTPUT_TIMEOUT_SECONDS = 120.0
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


def normalize_string_field(mapping, key, default=""):
    """Extract a string field from a dict, normalizing None/missing to a stripped default."""
    return str(mapping.get(key) or default).strip()


def add_standard_output_arguments(
    parser,
    *,
    format_choices=("json", "md"),
    default_format="md",
):
    """Add standard --format, --output, --pipe-command, --pipe-args arguments."""
    parser.add_argument("--format", choices=list(format_choices), default=default_format)
    parser.add_argument("--output", help="Write report to a file")
    parser.add_argument("--pipe-command", help="Pipe report output to a command")
    parser.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")


def cmd_str(cmd: list[str]) -> str:
    """Render a command list as a printable string."""
    return shlex.join(cmd)


def display_path(path: Path, *, repo_root: Path = REPO_ROOT) -> str:
    """Render a path relative to the repo root when possible."""
    repo_root_resolved = repo_root.resolve(strict=False)
    try:
        return path.resolve(strict=False).relative_to(repo_root_resolved).as_posix()
    except ValueError:
        return str(path)
    except OSError:
        return str(path)


def resolve_repo_path(
    raw_path: str | Path | None,
    default: Path | None = None,
    *,
    repo_root: Path = REPO_ROOT,
    resolve: bool = False,
) -> Path:
    """Resolve an optional repo-relative path override."""
    if raw_path is None or not str(raw_path).strip():
        if default is None:
            raise ValueError("raw_path is required when no default is provided")
        candidate = Path(default).expanduser()
    else:
        candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve() if resolve else candidate


def resolve_repo_python_command(cmd: list[str], *, cwd: Path | None = None) -> list[str]:
    """Use the active interpreter for repo-owned Python scripts launched as `python3 ...`."""
    if len(cmd) < 2 or cmd[0] != "python3":
        return cmd
    script_arg = cmd[1]
    if not script_arg.endswith(".py"):
        return cmd
    script_path = Path(script_arg).expanduser()
    if not script_path.is_absolute():
        script_path = (cwd or REPO_ROOT) / script_path
    try:
        resolved = script_path.resolve(strict=False)
        resolved.relative_to(REPO_ROOT)
    except (OSError, ValueError):
        return cmd
    return [sys.executable or "python3", *cmd[1:]]


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


def inject_quality_policy_command(
    command: str,
    quality_policy_path: str | None,
) -> str:
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


def normalize_repo_python_shell_command(command: str) -> str:
    """Force repo-owned Python shell commands onto the current interpreter."""
    split = split_shell_prefix(command)
    if split is None:
        return command
    env_prefix, parts = split
    if len(parts) < 2:
        return command
    if parts[0] not in {"python3", "python3.11", sys.executable}:
        return command
    target = parts[1]
    if target != "dev/scripts/devctl.py" and not target.startswith("dev/scripts/checks/"):
        return command
    parts[0] = sys.executable or "python3"
    rebuilt = shlex.join(parts)
    return " ".join([*env_prefix, rebuilt]) if env_prefix else rebuilt


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build one JSON object while rejecting duplicate keys."""
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError(f"duplicate JSON key `{key}`")
        payload[key] = value
    return payload


def read_json_object(
    path: Path,
    *,
    missing_message: str = "artifact missing: {path}",
    invalid_message: str = "invalid JSON ({error})",
    object_message: str = "expected top-level JSON object",
    reject_duplicate_keys: bool = False,
) -> tuple[dict[str, Any] | None, str | None]:
    """Load one JSON object with caller-tunable error wording."""
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, missing_message.format(path=path)
    except OSError as exc:
        return None, str(exc)
    try:
        if reject_duplicate_keys:
            payload = json.loads(
                raw_text,
                object_pairs_hook=_reject_duplicate_json_keys,
            )
        else:
            payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return None, invalid_message.format(path=path, error=exc)
    except ValueError as exc:
        return None, invalid_message.format(path=path, error=exc)
    if not isinstance(payload, dict):
        return None, object_message.format(path=path)
    return payload, None


def build_env(args) -> dict:
    """Build env vars from common CLI flags (offline/cargo cache options)."""
    env = os.environ.copy()
    if getattr(args, "offline", False):
        env["CARGO_NET_OFFLINE"] = "true"
    if getattr(args, "cargo_home", None):
        env["CARGO_HOME"] = os.path.expanduser(args.cargo_home)
    if getattr(args, "cargo_target_dir", None):
        env["CARGO_TARGET_DIR"] = os.path.expanduser(args.cargo_target_dir)
    if getattr(args, "quality_policy", None):
        env["DEVCTL_QUALITY_POLICY"] = os.path.expanduser(args.quality_policy)
    if getattr(args, "repo_path", None):
        env["DEVCTL_REPO_ROOT"] = str(Path(args.repo_path).resolve())
    return env


def write_output(
    content: str,
    output_path: str | None,
    *,
    announce_output_path: bool = True,
    stdout_content: str | None = None,
) -> None:
    """Write report output to a file, or print it to stdout."""
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if stdout_content is not None:
            print(stdout_content)
        elif announce_output_path:
            print(f"Report saved to: {path}")
    else:
        print(stdout_content if stdout_content is not None else content)


def pipe_output(content: str, pipe_command: str | None, pipe_args: list[str] | None) -> int:
    """Send report output to another command through stdin."""
    if not pipe_command:
        return 0
    cmd = [pipe_command] + (pipe_args or [])
    if not shutil.which(cmd[0]):
        print(f"Pipe command not found: {cmd[0]}")
        return 2
    try:
        result = subprocess.run(
            cmd,
            input=content,
            text=True,
            timeout=PIPE_OUTPUT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"Pipe command timed out after {PIPE_OUTPUT_TIMEOUT_SECONDS:.0f}s: {cmd_str(cmd)}")
        return 124
    except OSError as exc:
        print(f"Pipe command failed to start ({cmd_str(cmd)}): {exc}")
        return 127
    return result.returncode


def emit_output(
    content: str,
    *,
    output_path: str | None,
    pipe_command: str | None,
    pipe_args: list[str] | None,
    additional_outputs: Sequence[tuple[str, str | None]] | None = None,
    announce_output_path: bool = True,
    stdout_content: str | None = None,
    writer: Callable[[str, str | None], None] = write_output,
    piper: Callable[[str, str | None, list[str] | None], int] = pipe_output,
) -> int:
    """Write output and optionally pipe it, returning the pipe exit code."""
    if announce_output_path and stdout_content is None:
        writer(content, output_path)
    else:
        try:
            writer(
                content,
                output_path,
                announce_output_path=announce_output_path,
                stdout_content=stdout_content,
            )
        except TypeError:
            writer(content, output_path)
            if output_path and stdout_content is not None:
                print(stdout_content)
    for extra_content, extra_output_path in additional_outputs or ():
        writer(extra_content, extra_output_path)
    if not pipe_command:
        return 0
    return piper(content, pipe_command, pipe_args)


def should_emit_output(args) -> bool:
    """Return True when the caller asked for formatted/output report text."""
    return args.format != "text" or bool(args.output) or bool(getattr(args, "pipe_command", None))


def confirm_or_abort(message: str, assume_yes: bool) -> None:
    """Ask for yes/no confirmation unless `--yes` was provided."""
    if assume_yes:
        return
    try:
        reply = input(f"{message} [y/N] ").strip().lower()
    except EOFError as err:
        print(f"{message} [y/N] <non-interactive input unavailable>")
        print("Aborted. Re-run with --yes for non-interactive usage.")
        raise SystemExit(1) from err
    if reply not in ("y", "yes"):
        print("Aborted.")
        raise SystemExit(1)


def find_latest_outcomes_file(*, src_dir: Path = SRC_DIR) -> Path | None:
    """Find the newest mutation `outcomes.json` file under `rust/mutants.out`."""
    output_dir = src_dir / "mutants.out"
    primary = output_dir / "outcomes.json"
    if primary.exists():
        return primary
    candidates = list(output_dir.rglob("outcomes.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)
