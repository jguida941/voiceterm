"""Typed review-candidate builder for dirty-tree and commit-range handoff."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Mapping
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from ..runtime.review_state_models import (
    ReviewCandidateRecord,
    ReviewCurrentSessionState,
    review_candidate_from_mapping,
)
from ..runtime.review_state_semantics import is_pending_implementer_state
from ..time_utils import utc_timestamp
from .reviewer_head_tracking import current_head_sha

_BACKTICK_RE = re.compile(r"`([^`]+)`")
_PATH_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./-]+\.(?:py|rs|md|json|ya?ml|toml|txt|tsx?|jsx?|sh))"
)
_COMMAND_PREFIXES = (
    "python3 ",
    "python -m ",
    "pytest",
    "cargo test",
    "cargo clippy",
    "cargo fmt",
    "make ",
    "uv run ",
)
_COMPLETION_MARKERS = (
    "ready for review",
    "awaiting review",
    "review pending",
    "tests passed",
    "checks passed",
    "guard bundle passed",
    "all green",
    "completed the slice",
    "implemented the requested",
    "implemented the exact",
    "landed the requested",
)


def build_review_candidate(
    *,
    repo_root: Path,
    current_session: ReviewCurrentSessionState,
    bridge_liveness: Mapping[str, object],
    prior_review_state: Mapping[str, object] | None,
) -> ReviewCandidateRecord | None:
    """Build the current frozen review target, invalidating stale prior targets."""
    prior_candidate = _prior_candidate(prior_review_state)
    artifact_kind, changed_paths = _resolve_changed_paths(
        repo_root=repo_root,
        base_sha=str(bridge_liveness.get("head_at_push_time") or "").strip(),
    )
    head_sha = current_head_sha(repo_root)
    worktree_hash = str(bridge_liveness.get("last_worktree_hash") or "").strip()
    implementer_status_written = _implementer_status_written(current_session)
    tests_run, guards_run = _extract_execution_commands(current_session)
    completion_claimed = _completion_claimed(
        current_session=current_session,
        tests_run=tests_run,
        guards_run=guards_run,
    )
    scope_paths = _extract_scope_paths(
        current_session.current_instruction,
        current_session.last_reviewed_scope,
    )
    missing_scope_paths = tuple(
        path for path in scope_paths if path not in set(changed_paths)
    )

    if prior_candidate is not None and _same_candidate_state(
        prior_candidate,
        current_session=current_session,
    ):
        if _target_drifted(
            prior_candidate,
            head_sha=head_sha,
            worktree_hash=worktree_hash,
            changed_paths=changed_paths,
        ):
            return replace(
                prior_candidate,
                ready_for_review=False,
                valid=False,
                invalidation_reason="worktree_drift_after_candidate",
                missing_scope_paths=missing_scope_paths,
            )
        return replace(
            prior_candidate,
            scope_paths=scope_paths,
            missing_scope_paths=missing_scope_paths,
        )

    if not completion_claimed:
        return None

    base_sha = str(bridge_liveness.get("head_at_push_time") or "").strip()
    candidate_id = _candidate_id(
        instruction_revision=current_session.current_instruction_revision,
        artifact_kind=artifact_kind,
        base_sha=base_sha,
        head_sha=head_sha,
        worktree_hash=worktree_hash,
        changed_paths=changed_paths,
        implementer_state_hash=current_session.implementer_state_hash,
    )
    valid, invalidation_reason = _validate_candidate(
        artifact_kind=artifact_kind,
        changed_paths=changed_paths,
        worktree_hash=worktree_hash,
        missing_scope_paths=missing_scope_paths,
    )
    return ReviewCandidateRecord(
        candidate_id=candidate_id,
        instruction_revision=current_session.current_instruction_revision,
        artifact_kind=artifact_kind,
        base_sha=base_sha,
        head_sha=head_sha,
        worktree_hash=worktree_hash,
        changed_paths=changed_paths,
        tests_run=tests_run,
        guards_run=guards_run,
        implementer_status_written=implementer_status_written,
        ready_for_review=valid,
        valid=valid,
        invalidation_reason=invalidation_reason,
        implementer_state_hash=current_session.implementer_state_hash,
        emitted_at_utc=utc_timestamp(),
        scope_paths=scope_paths,
        missing_scope_paths=missing_scope_paths,
    )


def review_candidate_error(
    *,
    current_session: ReviewCurrentSessionState,
    candidate: ReviewCandidateRecord | None,
) -> str | None:
    """Return a fail-closed bridge/runtime error for missing or stale review targets."""
    tests_run, guards_run = _extract_execution_commands(current_session)
    if not _completion_claimed(
        current_session=current_session,
        tests_run=tests_run,
        guards_run=guards_run,
    ):
        return None
    if candidate is None:
        return (
            "Claude Status/Ack claim a completed review-ready slice, but no typed "
            "`ReviewCandidateRecord` exists yet. Emit one frozen review target "
            "through the repo-owned status/session-resume path before reviewer "
            "bootstrap continues."
        )
    if candidate.valid:
        return None
    detail = candidate.invalidation_reason or "candidate_invalid"
    if candidate.missing_scope_paths:
        missing = ", ".join(f"`{path}`" for path in candidate.missing_scope_paths)
        return (
            "Current reviewer target is stale or wrong: the instruction names "
            f"scoped paths missing from the candidate diff ({missing})."
        )
    return (
        "Claude Status/Ack claim a completed review-ready slice, but the typed "
        f"`ReviewCandidateRecord` is invalid (`{detail}`)."
    )


def _prior_candidate(
    prior_review_state: Mapping[str, object] | None,
) -> ReviewCandidateRecord | None:
    if not isinstance(prior_review_state, Mapping):
        return None
    return review_candidate_from_mapping(prior_review_state.get("review_candidate"))


def _same_candidate_state(
    prior_candidate: ReviewCandidateRecord,
    *,
    current_session: ReviewCurrentSessionState,
) -> bool:
    return (
        prior_candidate.instruction_revision == current_session.current_instruction_revision
        and prior_candidate.implementer_state_hash
        == current_session.implementer_state_hash
    )


def _target_drifted(
    prior_candidate: ReviewCandidateRecord,
    *,
    head_sha: str,
    worktree_hash: str,
    changed_paths: tuple[str, ...],
) -> bool:
    if head_sha and prior_candidate.head_sha and head_sha != prior_candidate.head_sha:
        return True
    if worktree_hash and prior_candidate.worktree_hash and worktree_hash != prior_candidate.worktree_hash:
        return True
    return changed_paths != prior_candidate.changed_paths


def _completion_claimed(
    *,
    current_session: ReviewCurrentSessionState,
    tests_run: tuple[str, ...],
    guards_run: tuple[str, ...],
) -> bool:
    if is_pending_implementer_state(
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_state=current_session.implementer_ack_state,
    ):
        return False
    if current_session.implementer_ack_state != "current":
        return False
    combined = (
        f"{current_session.implementer_status}\n{current_session.implementer_ack}"
    ).lower()
    return bool(
        tests_run
        or guards_run
        or any(marker in combined for marker in _COMPLETION_MARKERS)
    )


def _implementer_status_written(current_session: ReviewCurrentSessionState) -> bool:
    if is_pending_implementer_state(
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_state=current_session.implementer_ack_state,
    ):
        return False
    return bool(current_session.implementer_status.strip())


def _extract_execution_commands(
    current_session: ReviewCurrentSessionState,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    commands = _candidate_commands(
        f"{current_session.implementer_status}\n{current_session.implementer_ack}"
    )
    tests: list[str] = []
    guards: list[str] = []
    for command in commands:
        lowered = command.lower()
        if _is_test_command(lowered):
            tests.append(command)
        elif _is_guard_command(lowered):
            guards.append(command)
    return tuple(tests), tuple(guards)


def _candidate_commands(text: str) -> tuple[str, ...]:
    commands: list[str] = []
    for match in _BACKTICK_RE.finditer(text):
        _append_command(commands, match.group(1))
    for raw_line in text.splitlines():
        stripped = raw_line.strip().lstrip("-").strip()
        _append_command(commands, stripped)
    return tuple(commands)


def _append_command(commands: list[str], candidate: str) -> None:
    normalized = candidate.strip()
    lowered = normalized.lower()
    if not normalized:
        return
    if not any(lowered.startswith(prefix) for prefix in _COMMAND_PREFIXES):
        return
    if normalized not in commands:
        commands.append(normalized)


def _is_test_command(command: str) -> bool:
    return (
        "pytest" in command
        or "cargo test" in command
        or "unittest" in command
        or re.search(r"\btest\b", command) is not None
    )


def _is_guard_command(command: str) -> bool:
    return (
        "devctl.py check" in command
        or "docs-check" in command
        or "render-surfaces" in command
        or "check_" in command
    )


def _extract_scope_paths(*texts: str) -> tuple[str, ...]:
    scope_paths: list[str] = []
    for text in texts:
        for match in _PATH_RE.finditer(text):
            path = match.group("path").strip().lstrip("./")
            if path and path not in scope_paths:
                scope_paths.append(path)
    return tuple(scope_paths)


def _resolve_changed_paths(
    *,
    repo_root: Path,
    base_sha: str,
) -> tuple[str, tuple[str, ...]]:
    worktree_paths = _git_worktree_paths(repo_root)
    if worktree_paths:
        return "dirty_tree", worktree_paths
    head_sha = current_head_sha(repo_root)
    if base_sha and head_sha and base_sha != head_sha:
        commit_paths = _git_commit_range_paths(repo_root, base_sha, head_sha)
        if commit_paths:
            return "commit_range", commit_paths
    return "", ()


def _git_worktree_paths(repo_root: Path) -> tuple[str, ...]:
    try:
        tracked = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout.splitlines()
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout.splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return ()
    paths: list[str] = []
    for raw_path in (*tracked, *untracked):
        path = raw_path.strip()
        if path and path not in paths:
            paths.append(path)
    return tuple(paths)


def _git_commit_range_paths(
    repo_root: Path,
    base_sha: str,
    head_sha: str,
) -> tuple[str, ...]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_sha}..{head_sha}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ()
    return tuple(path.strip() for path in result.stdout.splitlines() if path.strip())


def _validate_candidate(
    *,
    artifact_kind: str,
    changed_paths: tuple[str, ...],
    worktree_hash: str,
    missing_scope_paths: tuple[str, ...],
) -> tuple[bool, str]:
    if not changed_paths:
        return False, "missing_changed_paths"
    if artifact_kind == "dirty_tree" and not worktree_hash:
        return False, "missing_worktree_hash"
    if missing_scope_paths:
        return False, "scope_mismatch"
    return True, ""


def _candidate_id(
    *,
    instruction_revision: str,
    artifact_kind: str,
    base_sha: str,
    head_sha: str,
    worktree_hash: str,
    changed_paths: tuple[str, ...],
    implementer_state_hash: str,
) -> str:
    payload = "\0".join(
        (
            instruction_revision,
            artifact_kind,
            base_sha,
            head_sha,
            worktree_hash,
            "\n".join(changed_paths),
            implementer_state_hash,
        )
    )
    return f"review-candidate-{sha256(payload.encode('utf-8')).hexdigest()[:12]}"
