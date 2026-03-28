"""Branch-aware helpers for release-bundle user-doc enforcement."""

from __future__ import annotations

from ...governance.branch_matching import head_matches_release_branch
from ...governance.push_policy import load_push_policy

CLI_SCHEMA_PATHS = frozenset(
    {
        "rust/src/bin/voiceterm/config/cli.rs",
        "rust/src/config/mod.rs",
    }
)
STRICT_RELEASE_USER_DOC_THRESHOLD = 3


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
