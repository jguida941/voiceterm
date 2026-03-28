"""Branch-aware helpers for release-bundle user-doc enforcement."""

from __future__ import annotations

import subprocess

from ...config import REPO_ROOT
from ...governance.push_policy import load_push_policy

CLI_SCHEMA_PATHS = frozenset(
    {
        "rust/src/bin/voiceterm/config/cli.rs",
        "rust/src/config/mod.rs",
    }
)
STRICT_RELEASE_USER_DOC_THRESHOLD = 3


def _git_capture_lines(command: list[str]) -> list[str]:
    """Return stripped stdout lines for a git query or an empty list on failure."""
    try:
        output = subprocess.check_output(
            command,
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def branch_matches_release_branch(candidate: str, release_branch: str) -> bool:
    """Return True when a local or remote branch candidate names the release branch."""
    text = str(candidate or "").strip()
    if not text:
        return False
    normalized = text.removeprefix("remotes/")
    return normalized == release_branch or normalized.endswith(f"/{release_branch}")


def head_matches_release_branch(head_ref: str, release_branch: str) -> bool:
    """Return True when the current head resolves to the configured release branch."""
    if branch_matches_release_branch(head_ref, release_branch):
        return True

    current_branch = _git_capture_lines(["git", "branch", "--show-current"])
    if current_branch and branch_matches_release_branch(current_branch[0], release_branch):
        return True

    branch_name = _git_capture_lines(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch_name and branch_matches_release_branch(branch_name[0], release_branch):
        return True

    reference = str(head_ref or "").strip() or "HEAD"
    branch_candidates = _git_capture_lines(
        [
            "git",
            "branch",
            "--all",
            "--contains",
            reference,
            "--format",
            "%(refname:short)",
        ]
    )
    return any(
        branch_matches_release_branch(candidate, release_branch)
        for candidate in branch_candidates
    )


def strict_release_user_docs_signal(
    *,
    changed: set[str],
    user_docs: list[str],
) -> bool:
    """Return True when feature-branch release validation should enforce strict user docs."""
    user_doc_change_count = sum(1 for path in user_docs if path in changed)
    return bool(CLI_SCHEMA_PATHS.intersection(changed)) or (
        user_doc_change_count >= STRICT_RELEASE_USER_DOC_THRESHOLD
    )


def should_run_strict_release_user_docs_gate(
    *,
    changed: set[str],
    user_docs: list[str],
    head_ref: str,
    policy_path: str | None,
) -> bool:
    """Gate strict release-mode user docs on branch posture plus user-facing signal."""
    push_policy = load_push_policy(policy_path=policy_path)
    if head_matches_release_branch(head_ref, push_policy.release_branch):
        return True
    return strict_release_user_docs_signal(changed=changed, user_docs=user_docs)
