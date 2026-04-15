"""Safe reviewer-heartbeat refresh helpers for the markdown bridge."""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..common import display_path
from .bridge_file import rewrite_bridge_markdown
from .handoff import extract_bridge_snapshot, summarize_bridge_liveness
from .heartbeat_launch_contract import (
    validate_refreshable_launch_contract as _validate_refreshable_launch_contract,
)
from .heartbeat_metadata import (
    CURRENT_INSTRUCTION_REVISION_RE,
    HEAD_AT_PUSH_TIME_RE,
    HeartbeatMetadataInputs,
    LAST_CHECKPOINT_ACTION_RE,
    LAST_CODEX_POLL_LOCAL_RE,
    LAST_CODEX_POLL_RE,
    LAST_WORKTREE_HASH_RE,
    format_local_timestamp as _format_local_timestamp,
    replace_or_insert_metadata_line as _replace_or_insert_metadata_line,
    rewrite_heartbeat_metadata as _rewrite_heartbeat_metadata,
    should_strip_poll_status_line as _should_strip_poll_status_line,
)
_BASE_NON_AUDIT_HASH_EXCLUDED_PREFIXES = (
    "dev/reports/",
    "dev/audits/",
    "rust/target/",
)


def non_audit_hash_excluded_prefixes() -> tuple[str, ...]:
    """Return hash-excluded prefixes including the repo-pack local state dir."""
    from ..repo_packs import active_path_config

    config = active_path_config()
    prefix = config.local_state_prefix_rel
    if prefix and prefix not in _BASE_NON_AUDIT_HASH_EXCLUDED_PREFIXES:
        return _BASE_NON_AUDIT_HASH_EXCLUDED_PREFIXES + (prefix,)
    return _BASE_NON_AUDIT_HASH_EXCLUDED_PREFIXES


# Backward-compatible alias — callers should migrate to the function form.
NON_AUDIT_HASH_EXCLUDED_PREFIXES = _BASE_NON_AUDIT_HASH_EXCLUDED_PREFIXES
NON_AUDIT_HASH_EXCLUDED_BASENAMES = (
    "convo.md",
)
NON_AUDIT_HASH_EXCLUDED_DIR_NAMES = (
    ".pytest_cache",
    "__pycache__",
)


@dataclass(frozen=True)
class BridgeHeartbeatRefresh:
    """One repo-owned heartbeat refresh applied to `bridge.md`."""

    bridge_path: str
    reason: str
    last_codex_poll_utc: str
    last_codex_poll_local: str
    last_worktree_hash: str


@dataclass(frozen=True)
class _HeartbeatHashes:
    observed_hash: str
    reviewed_hash: str


def bridge_heartbeat_refresh_to_dict(
    refresh: BridgeHeartbeatRefresh | None,
) -> dict[str, object] | None:
    """Convert a heartbeat refresh payload into JSON-friendly data."""
    if refresh is None:
        return None
    return asdict(refresh)


def bridge_excluded_rel_paths(
    *,
    repo_root: Path,
    bridge_path: Path,
) -> tuple[str, ...]:
    """Return repo-relative bridge paths that should not affect code hashes."""
    try:
        return (bridge_path.relative_to(repo_root).as_posix(),)
    except ValueError:
        return ()


def refresh_bridge_heartbeat(
    *,
    repo_root: Path,
    bridge_path: Path,
    reason: str,
    allow_non_refreshable_launch_errors: bool = False,
) -> BridgeHeartbeatRefresh:
    """Refresh the reviewer heartbeat metadata when launch is otherwise valid."""
    refresh: BridgeHeartbeatRefresh | None = None

    def transform(bridge_text: str) -> str:
        nonlocal refresh
        from ..repo_packs import active_path_config

        snapshot = extract_bridge_snapshot(bridge_text)
        liveness = summarize_bridge_liveness(snapshot)
        _validate_refreshable_launch_contract(
            snapshot=snapshot,
            liveness=liveness,
            allow_non_refreshable_launch_errors=allow_non_refreshable_launch_errors,
        )

        now_utc = datetime.now(timezone.utc)
        last_codex_poll_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        last_codex_poll_local = _format_local_timestamp(now_utc)
        hashes = _compute_heartbeat_hashes(
            repo_root=repo_root,
            bridge_path=bridge_path,
            reviewed_hash=str(snapshot.metadata.get("last_non_audit_worktree_hash") or ""),
        )
        tz_label = active_path_config().display_timezone
        updated_text = _rewrite_heartbeat_metadata(
            inputs=HeartbeatMetadataInputs(
                bridge_text=bridge_text,
                last_codex_poll_utc=last_codex_poll_utc,
                last_codex_poll_local=last_codex_poll_local,
                tz_label=tz_label,
                reason=reason,
                observed_hash=hashes.observed_hash,
                reviewed_hash=hashes.reviewed_hash,
            ),
        )
        refresh = BridgeHeartbeatRefresh(
            bridge_path=display_path(bridge_path, repo_root=repo_root),
            reason=reason,
            last_codex_poll_utc=last_codex_poll_utc,
            last_codex_poll_local=last_codex_poll_local,
            last_worktree_hash=hashes.reviewed_hash,
        )
        return updated_text

    rewrite_bridge_markdown(bridge_path, transform=transform)
    assert refresh is not None
    return refresh


def _compute_heartbeat_hashes(
    *,
    repo_root: Path,
    bridge_path: Path,
    reviewed_hash: str,
) -> _HeartbeatHashes:
    # Refresh the heartbeat timestamp without advancing the reviewed hash.
    # Heartbeat/ensure flows are liveness-only; they must not claim that the
    # current tree has been semantically reviewed.
    try:
        observed_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=bridge_excluded_rel_paths(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    except (ValueError, OSError):
        observed_hash = reviewed_hash
    return _HeartbeatHashes(
        observed_hash=observed_hash,
        reviewed_hash=reviewed_hash or observed_hash,
    )


def compute_non_audit_worktree_hash(
    *,
    repo_root: Path,
    excluded_rel_paths: tuple[str, ...],
    excluded_prefixes: tuple[str, ...] | None = None,
) -> str:
    if excluded_prefixes is None:
        excluded_prefixes = non_audit_hash_excluded_prefixes()
    excluded = {path.strip() for path in excluded_rel_paths if path.strip()}
    entries = _repo_entries_for_hash(repo_root)
    digest = hashlib.sha256()
    for relative_path in entries:
        if _is_non_audit_hash_excluded(
            relative_path,
            excluded=excluded,
            excluded_prefixes=excluded_prefixes,
        ):
            continue
        _update_digest_for_path(
            digest=digest,
            repo_root=repo_root,
            relative_path=relative_path,
        )
    return digest.hexdigest()


def _repo_entries_for_hash(repo_root: Path) -> list[str]:
    if not (repo_root / ".git").exists():
        return sorted(_walk_repo_paths(repo_root))

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

    return sorted(
        {
            raw.decode("utf-8", errors="surrogateescape")
            for raw in completed.stdout.split(b"\0")
            if raw
        }
    )


def _update_digest_for_path(
    *,
    digest: object,
    repo_root: Path,
    relative_path: str,
) -> None:
    target = repo_root / relative_path
    digest.update(relative_path.encode("utf-8", errors="surrogateescape"))
    digest.update(b"\0")

    if target.is_symlink():
        digest.update(b"symlink\0")
        digest.update(os.readlink(target).encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        return

    if target.is_file():
        digest.update(target.read_bytes())
        digest.update(b"\0")
        return

    digest.update(b"non-file\0" if target.exists() else b"missing\0")


def _is_non_audit_hash_excluded(
    relative_path: str,
    *,
    excluded: set[str],
    excluded_prefixes: tuple[str, ...],
) -> bool:
    path = Path(relative_path)
    if relative_path in excluded:
        return True
    if excluded_prefixes and any(relative_path.startswith(p) for p in excluded_prefixes):
        return True
    if path.name in NON_AUDIT_HASH_EXCLUDED_BASENAMES:
        return True
    return any(
        part in NON_AUDIT_HASH_EXCLUDED_DIR_NAMES
        for part in path.parts[:-1]
    )


def _walk_repo_paths(repo_root: Path) -> list[str]:
    entries: list[str] = []
    for path in repo_root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_dir():
            continue
        entries.append(path.relative_to(repo_root).as_posix())
    return entries
