"""Shared helpers for `devctl ship`.

Why this exists:
- ship steps share the same result format
- ship output (text/md) should stay consistent
- command failures (like missing binaries) should be handled the same way
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from ..common import build_env
from ..config import REPO_ROOT

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    tomllib = None  # type: ignore[assignment]

VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def make_step(
    name: str,
    ok: bool,
    returncode: int = 0,
    *,
    skipped: bool = False,
    details: Dict | None = None,
) -> Dict:
    """Create one standard result object for a ship step."""
    return {
        "name": name,
        "ok": ok,
        "status": "skipped" if skipped else ("ok" if ok else "failed"),
        "returncode": returncode,
        "skipped": skipped,
        "details": details or {},
    }


def run_checked(args: List[str], cwd: Path = REPO_ROOT) -> Tuple[int, str]:
    """Run a command and always return `(exit_code, output_text)`."""
    try:
        output = subprocess.check_output(args, cwd=cwd, text=True).strip()
        return 0, output
    except FileNotFoundError as exc:
        return 127, str(exc)
    except subprocess.CalledProcessError as exc:
        return exc.returncode, (exc.output or "").strip()


def tag_exists(tag: str) -> bool:
    """Return `True` if a local git tag exists."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", tag],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def read_version(path: Path) -> str:
    """Read version from known TOML roots (`[package]`/`[project]`)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""

    if tomllib is None:
        return _read_version_fallback(text)

    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return ""
    if not isinstance(parsed, dict):
        return ""

    for section_name in ("package", "project"):
        section = parsed.get(section_name)
        if isinstance(section, dict):
            value = section.get("version")
            if isinstance(value, str):
                return value.strip()
    return ""


def _read_version_fallback(text: str) -> str:
    """Fallback parser for Python runtimes without `tomllib`."""
    active_section = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            active_section = line.strip("[]").strip().split(".", 1)[0]
            continue
        if active_section not in {"package", "project"}:
            continue
        if not line.startswith("version"):
            continue
        key, _, value = line.partition("=")
        if key.strip() != "version":
            continue
        return value.strip().strip('"').strip("'")
    return ""


def changelog_has_version(version: str) -> bool:
    """Check whether `dev/CHANGELOG.md` has a heading for this version."""
    changelog = REPO_ROOT / "dev/CHANGELOG.md"
    if not changelog.exists():
        return False
    text = changelog.read_text(encoding="utf-8")
    return f"## [{version}]" in text or f"## {version}" in text


def render_md(report: Dict) -> str:
    """Format ship report as markdown."""
    lines = ["# devctl ship", ""]
    lines.append(f"- version: {report['version']}")
    lines.append(f"- tag: {report['tag']}")
    lines.append(f"- notes_file: {report['notes_file']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- exit_code: {report['exit_code']}")
    lines.append("")
    lines.append("| Step | Status | Exit | Details |")
    lines.append("|---|---|---:|---|")
    for step in report["steps"]:
        details = ", ".join(f"{k}={v}" for k, v in step.get("details", {}).items()) or "-"
        lines.append(
            f"| `{step['name']}` | {step['status']} | {step['returncode']} | {details} |"
        )
    return "\n".join(lines)


def render_text(report: Dict) -> str:
    """Format ship report as compact plain text."""
    lines = [
        f"devctl ship version={report['version']} tag={report['tag']}",
        f"notes_file={report['notes_file']}",
        "",
    ]
    for step in report["steps"]:
        lines.append(f"[{step['status']}] {step['name']} (exit={step['returncode']})")
    lines.append("")
    lines.append(f"overall={report['ok']} exit_code={report['exit_code']}")
    return "\n".join(lines)


def internal_env(args) -> Dict:
    """Set env vars used by internal publish wrapper scripts."""
    env = build_env(args)
    env["VOICETERM_DEVCTL_INTERNAL"] = "1"
    if args.yes or args.dry_run:
        env["VOICETERM_DEVCTL_ASSUME_YES"] = "1"
    return env
