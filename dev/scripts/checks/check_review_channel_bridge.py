#!/usr/bin/env python3
"""Validate the temporary markdown review-channel bridge contract."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_review_channel_handoff = importlib.import_module("dev.scripts.devctl.review_channel.handoff")

DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS = _review_channel_handoff.DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS
extract_bridge_snapshot = _review_channel_handoff.extract_bridge_snapshot
validate_live_bridge_contract = _review_channel_handoff.validate_live_bridge_contract

CODE_AUDIT_PATH = REPO_ROOT / "code_audit.md"
REVIEW_CHANNEL_PATH = REPO_ROOT / "dev/active/review_channel.md"

REQUIRED_CODE_AUDIT_H2 = [
    "Start-Of-Conversation Rules",
    "Protocol",
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Claude Status",
    "Claude Questions",
    "Claude Ack",
    "Current Instruction For Claude",
    "Last Reviewed Scope",
]

REQUIRED_CODE_AUDIT_MARKERS = [
    "Codex is the reviewer. Claude is the coder.",
    "`AGENTS.md`",
    "`dev/active/INDEX.md`",
    "`dev/active/MASTER_PLAN.md`",
    "`dev/active/review_channel.md`",
    "Codex must poll non-`code_audit.md` worktree changes every 2-3 minutes",
    "Codex must exclude `code_audit.md` itself when computing the reviewed",
    "operator-visible chat update",
    "Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
    "Claude should start from `Current Verdict`, `Open Findings`, and `Current Instruction For Claude`",
    "When the current slice is accepted and scoped plan work remains, Codex must",
    "Only the Codex conductor may update the Codex-owned sections",
    "Only the Claude conductor may update the Claude-owned sections",
    "Specialist workers should wake on owned-path changes",
    "Codex must emit an operator-visible heartbeat every 5 minutes",
    "- Last Codex poll:",
    "- Last Codex poll (Local America/New_York):",
    "- Last non-audit worktree hash:",
]

REQUIRED_REVIEW_CHANNEL_MARKERS = [
    "## Transitional Markdown Bridge (Current Operating Mode)",
    "`code_audit.md`",
    "each meaningful Codex reviewer write to\n   `code_audit.md` must also emit a concise operator-visible chat update",
    "`MASTER_PLAN.md` remains the canonical tracker and\n   `INDEX.md` remains the router",
    "`last_poll_local`",
    "`check_review_channel_bridge.py`",
    "`devctl swarm_run --continuous`",
    "only one Codex conductor updates the Codex-owned bridge",
    "heartbeat every five minutes even when the blocker set is unchanged",
    "Default multi-agent wakeups should be change-routed instead of brute-force",
    "Completion stall",
]

UTC_TIMESTAMP_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
LOCAL_POLL_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{3,4}$")
WORKTREE_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MAX_POLL_AGE_MINUTES = DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS // 60


def _extract_h2(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE)]


def _missing_markers(text: str, required_markers: list[str]) -> list[str]:
    return [marker for marker in required_markers if marker not in text]


def _review_bridge_is_active(text: str) -> bool:
    return "## Transitional Markdown Bridge (Current Operating Mode)" in text


def _strip_backticks(text: str) -> str:
    return text.strip().strip("`").strip()


def _extract_code_audit_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        trimmed = line.strip().lstrip("-").strip()
        if trimmed.startswith("Last Codex poll (Local America/New_York):"):
            metadata["last_codex_poll_local"] = _strip_backticks(trimmed.split(":", 1)[1])
        elif trimmed.startswith("Last Codex poll:"):
            metadata["last_codex_poll"] = _strip_backticks(trimmed.split(":", 1)[1])
        elif trimmed.startswith("Last non-audit worktree hash:"):
            metadata["last_worktree_hash"] = _strip_backticks(trimmed.split(":", 1)[1])
    return metadata


def _current_utc() -> datetime:
    return datetime.now(UTC)


def _enforce_live_poll_freshness() -> bool:
    """GitHub-hosted CI cannot act as the live Codex reviewer heartbeat owner."""
    return os.getenv("GITHUB_ACTIONS", "").strip().lower() != "true"


def _validate_code_audit_metadata(text: str) -> list[str]:
    metadata = _extract_code_audit_metadata(text)
    errors: list[str] = []

    last_codex_poll = metadata.get("last_codex_poll", "")
    if not UTC_TIMESTAMP_PATTERN.fullmatch(last_codex_poll):
        errors.append("Invalid `Last Codex poll` timestamp; expected ISO-8601 UTC like " "`2026-03-08T19:08:45Z`.")
    else:
        poll_time = datetime.strptime(last_codex_poll, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        max_age = timedelta(minutes=MAX_POLL_AGE_MINUTES)
        poll_age = _current_utc() - poll_time
        if poll_age < timedelta(0):
            errors.append("`Last Codex poll` is in the future.")
        elif poll_age > max_age and _enforce_live_poll_freshness():
            errors.append(
                "`Last Codex poll` is stale; bridge-active reviews must refresh "
                f"within {MAX_POLL_AGE_MINUTES} minutes."
            )

    if not LOCAL_POLL_PATTERN.fullmatch(metadata.get("last_codex_poll_local", "")):
        errors.append(
            "Invalid `Last Codex poll (Local America/New_York)` value; expected "
            "local timestamp text like `2026-03-08 15:08:45 EDT`."
        )

    if not WORKTREE_HASH_PATTERN.fullmatch(metadata.get("last_worktree_hash", "")):
        errors.append(
            "Invalid `Last non-audit worktree hash`; expected a 64-character " "lowercase SHA-256 hex digest."
        )

    return errors


def _validate_code_audit_live_state(text: str) -> list[str]:
    return validate_live_bridge_contract(extract_bridge_snapshot(text))


def _is_tracked_by_git(path: Path) -> bool:
    """Return True if the file is tracked by git (committed or staged)."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # If git is unavailable or times out, skip the tracking check
        return True


def _build_path_report(
    *,
    path: Path,
    required_h2: list[str] | None = None,
    required_markers: list[str],
    optional: bool = False,
    require_tracked: bool = False,
) -> dict:
    relative_path = str(path.relative_to(REPO_ROOT))
    if not path.exists():
        if optional:
            return {
                "path": relative_path,
                "ok": True,
                "active": False,
                "missing_h2": [],
                "missing_markers": [],
            }
        return {
            "path": relative_path,
            "ok": False,
            "active": False,
            "error": f"Missing file: {relative_path}",
            "missing_h2": required_h2 or [],
            "missing_markers": required_markers,
        }

    untracked = require_tracked and not _is_tracked_by_git(path)

    text = path.read_text(encoding="utf-8")
    headings = _extract_h2(text)
    missing_h2 = [heading for heading in required_h2 if heading not in headings] if required_h2 is not None else []
    missing_markers = _missing_markers(text, required_markers)
    report: dict = {
        "path": relative_path,
        "ok": not (missing_h2 or missing_markers or untracked),
        "active": True,
        "missing_h2": missing_h2,
        "missing_markers": missing_markers,
    }
    if untracked:
        report["untracked"] = True
        report["error"] = f"Bridge-active file is untracked by git: {relative_path}"
    return report


def build_report() -> dict:
    review_channel_text = REVIEW_CHANNEL_PATH.read_text(encoding="utf-8") if REVIEW_CHANNEL_PATH.exists() else ""
    review_bridge_active = _review_bridge_is_active(review_channel_text)
    code_audit = _build_path_report(
        path=CODE_AUDIT_PATH,
        required_h2=REQUIRED_CODE_AUDIT_H2,
        required_markers=REQUIRED_CODE_AUDIT_MARKERS,
        optional=not review_bridge_active,
        require_tracked=review_bridge_active,
    )
    if review_bridge_active and code_audit.get("ok", False):
        code_audit_text = CODE_AUDIT_PATH.read_text(encoding="utf-8")
        metadata_errors = _validate_code_audit_metadata(code_audit_text)
        if metadata_errors:
            code_audit["ok"] = False
            code_audit["metadata_errors"] = metadata_errors
        state_errors = _validate_code_audit_live_state(code_audit_text)
        if state_errors:
            code_audit["ok"] = False
            code_audit["state_errors"] = state_errors
    review_channel = _build_path_report(
        path=REVIEW_CHANNEL_PATH,
        required_markers=(REQUIRED_REVIEW_CHANNEL_MARKERS if review_bridge_active else []),
        require_tracked=review_bridge_active,
    )
    return {
        "command": "check_review_channel_bridge",
        "review_bridge_active": review_bridge_active,
        "ok": code_audit["ok"] and review_channel["ok"],
        "code_audit": code_audit,
        "review_channel": review_channel,
    }


def render_md(report: dict) -> str:
    lines = ["# check_review_channel_bridge", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- review_bridge_active: {report.get('review_bridge_active', False)}")
    for key in ("code_audit", "review_channel"):
        section = report[key]
        lines.append(f"- {key}_path: {section['path']}")
        lines.append(f"- {key}_ok: {section.get('ok', False)}")
        if key == "code_audit":
            lines.append(f"- {key}_active: {section.get('active', False)}")
        if section.get("untracked"):
            lines.append(f"- {key}_untracked: True")
        error = section.get("error")
        if error:
            lines.append(f"- {key}_error: {error}")
            if section.get("untracked"):
                continue
        missing_h2 = section.get("missing_h2", [])
        lines.append(f"- {key}_missing_h2: {', '.join(missing_h2) if missing_h2 else 'none'}")
        missing_markers = section.get("missing_markers", [])
        lines.append("- " f"{key}_missing_markers: " f"{', '.join(missing_markers) if missing_markers else 'none'}")
        metadata_errors = section.get("metadata_errors", [])
        if metadata_errors:
            lines.append("- " f"{key}_metadata_errors: " f"{', '.join(metadata_errors) if metadata_errors else 'none'}")
        state_errors = section.get("state_errors", [])
        if state_errors:
            lines.append("- " f"{key}_state_errors: " f"{', '.join(state_errors) if state_errors else 'none'}")
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
        print(render_md(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
