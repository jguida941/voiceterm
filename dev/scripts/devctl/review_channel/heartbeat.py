"""Safe reviewer-heartbeat refresh helpers for the markdown bridge."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ..common import display_path
from .handoff import (
    extract_bridge_snapshot,
    summarize_bridge_liveness,
    validate_launch_bridge_state,
)

LAST_CODEX_POLL_RE = re.compile(r"(?m)^- Last Codex poll:\s*`.*?`\s*$")
LAST_CODEX_POLL_LOCAL_RE = re.compile(
    r"(?m)^- Last Codex poll \(Local America/New_York\):\s*`.*?`\s*$"
)
LAST_WORKTREE_HASH_RE = re.compile(
    r"(?m)^- Last non-audit worktree hash:\s*`.*?`\s*$"
)
POLL_STATUS_SECTION_RE = re.compile(
    r"(^## Poll Status\s*$\n)(.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
AUTO_REFRESH_PREFIX = "- Auto-refreshed reviewer heartbeat:"
REFRESHABLE_LAUNCH_ERRORS = (
    "Missing `Last Codex poll`;",
    "Missing `Last Codex poll`",
    "`Last Codex poll` is stale;",
    "`Last Codex poll` is stale",
)


@dataclass(frozen=True)
class BridgeHeartbeatRefresh:
    """One repo-owned heartbeat refresh applied to `code_audit.md`."""

    bridge_path: str
    reason: str
    last_codex_poll_utc: str
    last_codex_poll_local: str
    last_worktree_hash: str


def bridge_heartbeat_refresh_to_dict(
    refresh: BridgeHeartbeatRefresh | None,
) -> dict[str, object] | None:
    """Convert a heartbeat refresh payload into JSON-friendly data."""
    if refresh is None:
        return None
    return asdict(refresh)


def refresh_bridge_heartbeat(
    *,
    repo_root: Path,
    bridge_path: Path,
    reason: str,
) -> BridgeHeartbeatRefresh:
    """Refresh the reviewer heartbeat metadata when launch is otherwise valid."""
    bridge_text = bridge_path.read_text(encoding="utf-8")
    snapshot = extract_bridge_snapshot(bridge_text)
    liveness = summarize_bridge_liveness(snapshot)
    launch_errors = validate_launch_bridge_state(snapshot, liveness=liveness)
    non_refreshable = [
        error for error in launch_errors if not _is_refreshable_launch_error(error)
    ]
    if non_refreshable:
        raise ValueError(
            "Bridge heartbeat refresh refused because the launch contract has "
            "other blockers: " + "; ".join(non_refreshable)
        )

    now_utc = datetime.now(timezone.utc)
    last_codex_poll_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    last_codex_poll_local = _format_new_york_timestamp(now_utc)
    last_worktree_hash = _compute_non_audit_worktree_hash(
        repo_root=repo_root,
        excluded_rel_paths=("code_audit.md",),
    )

    updated_text = bridge_text
    updated_text = _replace_or_insert_metadata_line(
        updated_text,
        pattern=LAST_CODEX_POLL_RE,
        replacement=f"- Last Codex poll: `{last_codex_poll_utc}`",
    )
    updated_text = _replace_or_insert_metadata_line(
        updated_text,
        pattern=LAST_CODEX_POLL_LOCAL_RE,
        replacement=(
            "- Last Codex poll (Local America/New_York): "
            f"`{last_codex_poll_local}`"
        ),
    )
    updated_text = _replace_or_insert_metadata_line(
        updated_text,
        pattern=LAST_WORKTREE_HASH_RE,
        replacement=f"- Last non-audit worktree hash: `{last_worktree_hash}`",
    )
    updated_text = _rewrite_poll_status(
        updated_text,
        note=(
            f"{AUTO_REFRESH_PREFIX} `{last_codex_poll_utc}` "
            f"(reason: {reason}; tree: {last_worktree_hash[:12]})."
        ),
    )
    bridge_path.write_text(updated_text, encoding="utf-8")
    return BridgeHeartbeatRefresh(
        bridge_path=display_path(bridge_path, repo_root=repo_root),
        reason=reason,
        last_codex_poll_utc=last_codex_poll_utc,
        last_codex_poll_local=last_codex_poll_local,
        last_worktree_hash=last_worktree_hash,
    )


def _is_refreshable_launch_error(error: str) -> bool:
    stripped = error.strip()
    return any(stripped.startswith(prefix) for prefix in REFRESHABLE_LAUNCH_ERRORS)


def _replace_or_insert_metadata_line(
    text: str,
    *,
    pattern: re.Pattern[str],
    replacement: str,
) -> str:
    updated, count = pattern.subn(replacement, text, count=1)
    if count == 1:
        return updated
    marker = "\n## Protocol\n"
    if marker not in text:
        raise ValueError("Unable to locate the markdown-bridge metadata block.")
    return text.replace(marker, f"{replacement}\n{marker}", 1)


def _rewrite_poll_status(text: str, *, note: str) -> str:
    def replace_section(match: re.Match[str]) -> str:
        body_lines = [line.rstrip() for line in match.group(2).splitlines()]
        filtered_lines = [
            line
            for line in body_lines
            if line.strip() and not line.strip().startswith(AUTO_REFRESH_PREFIX)
        ]
        new_body_lines = [note, *filtered_lines]
        body = "\n".join(new_body_lines).strip()
        return f"{match.group(1)}\n{body}\n\n"

    rewritten, count = POLL_STATUS_SECTION_RE.subn(replace_section, text, count=1)
    if count != 1:
        raise ValueError("Unable to locate the `Poll Status` section in the bridge.")
    return rewritten


def _format_new_york_timestamp(timestamp_utc: datetime) -> str:
    local = timestamp_utc.astimezone(ZoneInfo("America/New_York"))
    return local.strftime("%Y-%m-%d %H:%M:%S %Z")


def _compute_non_audit_worktree_hash(
    *,
    repo_root: Path,
    excluded_rel_paths: tuple[str, ...],
) -> str:
    excluded = {path.strip() for path in excluded_rel_paths if path.strip()}
    if (repo_root / ".git").exists():
        completed = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).decode(
                "utf-8",
                errors="replace",
            )
            raise ValueError(
                detail.strip()
                or "git ls-files failed while refreshing bridge heartbeat."
            )
        entries = sorted(
            {
                raw.decode("utf-8", errors="surrogateescape")
                for raw in completed.stdout.split(b"\0")
                if raw
            }
        )
    else:
        entries = sorted(_walk_repo_paths(repo_root))
    digest = hashlib.sha256()
    for relative_path in entries:
        if relative_path in excluded:
            continue
        target = repo_root / relative_path
        digest.update(relative_path.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        if target.is_symlink():
            digest.update(b"symlink\0")
            digest.update(os.readlink(target).encode("utf-8", errors="surrogateescape"))
            digest.update(b"\0")
            continue
        if target.is_file():
            digest.update(target.read_bytes())
            digest.update(b"\0")
            continue
        if target.exists():
            digest.update(b"non-file\0")
        else:
            digest.update(b"missing\0")
    return digest.hexdigest()


def _walk_repo_paths(repo_root: Path) -> list[str]:
    entries: list[str] = []
    for path in repo_root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_dir():
            continue
        entries.append(path.relative_to(repo_root).as_posix())
    return entries
