"""Git index-lock classification for governed VCS actions."""

from __future__ import annotations

from ...runtime.vcs import (
    classify_git_index_error,
    git_index_lock_busy,
    git_index_write_blocked,
)


def git_index_failure_reason(error: str, *, default: str) -> str:
    return classify_git_index_error(error, default=default)


def git_index_failure_guidance() -> str:
    return (
        "The current execution sandbox cannot create `.git/index.lock`. "
        "Rerun the governed command with repo-approved filesystem access or "
        "from the implementer-owned local terminal lane, then retry `vcs.stage`."
    )


def git_index_busy_guidance() -> str:
    return (
        "The git index stayed locked after bounded backoff. Rerun the governed "
        "command after the concurrent git operation finishes."
    )


def git_index_result_kwargs(
    *,
    error: str,
    reason: str,
    default_reason: str,
) -> dict[str, object]:
    if reason not in {"git_index_write_blocked", "git_index_lock_busy"}:
        return {}
    error_fields = _git_index_error_fields(
        error=error,
        reason=reason,
        default_reason=default_reason,
    )
    return {
        "errors": (error_fields,),
        "reason_chain": tuple(error_fields["reason_chain"]),
        "remediation": str(error_fields["remediation"]),
        "auto_executable": bool(error_fields["auto_executable"]),
        "retryable": bool(error_fields["retryable"]),
    }


def review_snapshot_index_failure_warning(warnings: list[str]) -> str:
    for warning in warnings:
        text = str(warning or "")
        if "review_snapshot_stage_failed" in text and "index.lock" in text:
            return text
    return ""


def _git_index_error_fields(
    *,
    error: str,
    reason: str,
    default_reason: str,
) -> dict[str, object]:
    reason_chain = [default_reason]
    remediation = ""
    auto_executable = False
    if reason == "git_index_write_blocked":
        reason_chain.extend(["git_index_write_blocked", "sandbox_index_lock_denied"])
        remediation = "stage_commit_pipeline"
        retryable = True
    elif reason == "git_index_lock_busy":
        reason_chain.extend(["git_index_lock_busy", "bounded_backoff_exhausted"])
        remediation = "retry_git_index_write_after_backoff"
        auto_executable = True
        retryable = True
    else:
        retryable = False
    return {
        "reason": reason,
        "reason_chain": reason_chain,
        "message": error,
        "remediation": remediation,
        "auto_executable": auto_executable,
        "retryable": retryable,
    }
