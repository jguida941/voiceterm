"""Shared devctl path, output, env, and shell helpers."""

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from .config import REPO_ROOT, SRC_DIR

PIPE_OUTPUT_TIMEOUT_SECONDS = 120.0


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


def read_json_object(
    path: Path,
    *,
    missing_message: str = "artifact missing: {path}",
    invalid_message: str = "invalid JSON ({error})",
    object_message: str = "expected top-level JSON object",
) -> tuple[dict[str, Any] | None, str | None]:
    """Load one JSON object with caller-tunable error wording."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, missing_message.format(path=path)
    except OSError as exc:
        return None, str(exc)
    except json.JSONDecodeError as exc:
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
    return env


def write_output(content: str, output_path: Optional[str]) -> None:
    """Write report output to a file, or print it to stdout."""
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Report saved to: {path}")
    else:
        print(content)


def pipe_output(
    content: str, pipe_command: Optional[str], pipe_args: Optional[list[str]]
) -> int:
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
        print(
            f"Pipe command timed out after {PIPE_OUTPUT_TIMEOUT_SECONDS:.0f}s: {cmd_str(cmd)}"
        )
        return 124
    except OSError as exc:
        print(f"Pipe command failed to start ({cmd_str(cmd)}): {exc}")
        return 127
    return result.returncode


def emit_output(
    content: str,
    *,
    output_path: Optional[str],
    pipe_command: Optional[str],
    pipe_args: Optional[list[str]],
    additional_outputs: Optional[Sequence[tuple[str, Optional[str]]]] = None,
    writer: Callable[[str, Optional[str]], None] = write_output,
    piper: Callable[[str, Optional[str], Optional[list[str]]], int] = pipe_output,
) -> int:
    """Write output and optionally pipe it, returning the pipe exit code."""
    writer(content, output_path)
    for extra_content, extra_output_path in additional_outputs or ():
        writer(extra_content, extra_output_path)
    if not pipe_command:
        return 0
    return piper(content, pipe_command, pipe_args)


def should_emit_output(args) -> bool:
    """Return True when the caller asked for formatted/output report text."""
    return (
        args.format != "text"
        or bool(args.output)
        or bool(getattr(args, "pipe_command", None))
    )


def confirm_or_abort(message: str, assume_yes: bool) -> None:
    """Ask for yes/no confirmation unless `--yes` was provided."""
    if assume_yes:
        return
    try:
        reply = input(f"{message} [y/N] ").strip().lower()
    except EOFError:
        print(f"{message} [y/N] <non-interactive input unavailable>")
        print("Aborted. Re-run with --yes for non-interactive usage.")
        raise SystemExit(1)
    if reply not in ("y", "yes"):
        print("Aborted.")
        raise SystemExit(1)


def find_latest_outcomes_file(*, src_dir: Path = SRC_DIR) -> Optional[Path]:
    """Find the newest mutation `outcomes.json` file under `rust/mutants.out`."""
    output_dir = src_dir / "mutants.out"
    primary = output_dir / "outcomes.json"
    if primary.exists():
        return primary
    candidates = list(output_dir.rglob("outcomes.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)
