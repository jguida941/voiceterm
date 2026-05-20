"""Git mutation proof support for governed push publication."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ...config import REPO_ROOT
from ...governance.push_state import current_head_commit_sha
from ...runtime.git_mutation_proof_receipt import (
    GitMutationProofReceipt,
    append_git_mutation_proof_receipt,
    build_push_git_mutation_proof_receipt,
)
from .push_findings import append_finding
from .push_report import PushStageTruth


@dataclass(frozen=True, slots=True)
class PushPublicationProofFailure:
    """Failure surfaced after a raw git push returned success."""

    reason: str
    operator_guidance: str
    stages: PushStageTruth
    partial_progress: bool = False


def verify_remote_publication(
    state: object,
    *,
    current_head_sha_fn: Callable[..., str] | None,
    remote_head_sha_fn: Callable[..., str] | None,
) -> PushPublicationProofFailure | None:
    """Verify the remote branch now points at the local HEAD and write proof."""

    if remote_head_sha_fn is None:
        return None
    repo_root = _state_repo_root(state)
    remote_head_after = remote_head_sha_fn(
        _state_remote(state),
        _state_branch(state),
        repo_root=repo_root,
    )
    _set_state_attr(state, "remote_head_after", remote_head_after)
    head_commit = (
        current_head_sha_fn(repo_root=repo_root)
        if current_head_sha_fn is not None
        else current_head_commit_sha(repo_root=repo_root)
    )
    proof = build_push_git_mutation_proof_receipt(
        repo_root=repo_root,
        claim=GitMutationProofReceipt(
            mutation_kind="push",
            remote_name=_state_remote(state),
            branch_name=_state_branch(state),
            expected_sha=head_commit,
            observed_local_sha=head_commit,
            observed_remote_sha=remote_head_after,
            command_returncode=_push_returncode(state),
            operation_returned_success=True,
        ),
    )
    try:
        proof_store = append_git_mutation_proof_receipt(repo_root, proof)
    # broad-except: allow reason=proof receipt store boundary must return typed failure fallback=PushPublicationProofFailure
    except Exception as exc:
        append_finding(
            state,
            "GitMutationProofWriteFailure",
            "Remote publication could not be recorded in GitMutationProofReceipt.",
            evidence=dict(
                branch=_state_branch(state),
                remote=_state_remote(state),
                head_commit=head_commit,
                remote_head_after=remote_head_after,
                error=str(exc),
            ),
        )
        matched = bool(remote_head_after == head_commit)
        return PushPublicationProofFailure(
            reason="push_proof_write_failed",
            operator_guidance=(
                "The governed push proof receipt could not be written after "
                "git push returned. Compare the remote ref with the current "
                "HEAD, then repair the receipt store before treating this push "
                "as fully proven."
            ),
            stages=PushStageTruth(
                validation_ready=True,
                published_remote=matched,
            ),
            partial_progress=matched,
        )

    _set_state_attr(state, "git_mutation_proof_receipt_path", proof_store)
    _set_state_attr(state, "git_mutation_proof_verified", proof.verified)
    if remote_head_after and remote_head_after == head_commit:
        return None
    append_finding(
        state,
        "SilentPushFailure",
        "git push returned success but the remote ref does not match current HEAD.",
        evidence=dict(
            branch=_state_branch(state),
            remote=_state_remote(state),
            head_commit=head_commit,
            remote_head_after=remote_head_after,
        ),
    )
    return PushPublicationProofFailure(
        reason="remote_ref_not_updated",
        operator_guidance=(
            "The governed git push returned success, but the remote ref could not "
            "be proven at the current HEAD. Inspect the remote and retry through "
            "`devctl push --execute`."
        ),
        stages=PushStageTruth(),
    )


def _state_repo_root(state: object) -> Path:
    raw = str(getattr(state, "repo_root", "") or "").strip()
    return Path(raw) if raw else REPO_ROOT


def _state_branch(state: object) -> str:
    return str(getattr(state, "branch", "") or "")


def _state_remote(state: object) -> str:
    return str(getattr(state, "remote", "") or "")


def _push_returncode(state: object) -> int:
    push_step = getattr(state, "push_step", {}) or {}
    if not isinstance(push_step, dict):
        return 0
    try:
        return int(push_step.get("returncode") or 0)
    except (TypeError, ValueError):
        return 0


def _set_state_attr(state: object, name: str, value: object) -> None:
    try:
        setattr(state, name, value)
    except (AttributeError, TypeError):
        pass
