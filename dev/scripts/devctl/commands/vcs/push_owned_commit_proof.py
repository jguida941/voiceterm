"""Git mutation proof rows for push-owned auto-commits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...runtime.git_mutation_proof_receipt import (
    GitMutationProofReceipt,
    append_git_mutation_proof_receipt,
    build_commit_git_mutation_proof_receipt,
)


@dataclass(frozen=True, slots=True)
class PushOwnedCommitProofResult:
    """Result of recording proof for a commit created inside push preflight."""

    ok: bool
    verified: bool
    proof_store: str = ""
    failure_reason: str = ""


def record_push_owned_commit_proof(
    *,
    repo_root: Path,
    commit_sha: str,
    action_id: str = "vcs.push",
    artifact_paths: tuple[str, ...] = (),
) -> PushOwnedCommitProofResult:
    """Record the commit proof required for a push-owned auto-commit."""
    if not commit_sha:
        return PushOwnedCommitProofResult(
            ok=False,
            verified=False,
            failure_reason="missing_commit_sha",
        )
    proof = build_commit_git_mutation_proof_receipt(
        repo_root=repo_root,
        claim=GitMutationProofReceipt(
            mutation_kind="commit",
            action_id=action_id,
            expected_sha=commit_sha,
            command_returncode=0,
            operation_returned_success=True,
            artifact_paths=artifact_paths,
        ),
    )
    try:
        proof_store = append_git_mutation_proof_receipt(repo_root, proof)
    # broad-except: allow reason=push preflight proof store boundary fallback=typed failure result
    except Exception as exc:
        return PushOwnedCommitProofResult(
            ok=False,
            verified=False,
            failure_reason=f"proof_write_failed:{exc}",
        )
    return PushOwnedCommitProofResult(
        ok=proof.verified,
        verified=proof.verified,
        proof_store=proof_store,
        failure_reason=proof.failure_reason,
    )


__all__ = ["PushOwnedCommitProofResult", "record_push_owned_commit_proof"]
