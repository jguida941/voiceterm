"""Runtime helpers for governed commit attention and handoff behavior."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Callable

from ...common import run_cmd
from ...review_channel.event_reducer import load_or_refresh_event_bundle
from ...review_channel.events import post_packet, resolve_artifact_paths
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.review_state_models import ReviewState
from ...runtime.review_state_parser import review_state_from_payload
from ...runtime.startup_receipt import load_startup_receipt
from .governed_executor_commit_attention import (
    _held_lease_active,
    _target_agent_has_actionable_packet_attention,
)
from .governed_executor_commit_targets import (
    resolve_commit_execution_target,
    resolve_commit_stage_target,
)
from .governed_executor_git import head_commit
from .governed_executor_packets import (
    CommitStageRequestFields,
    build_commit_execution_request,
    build_commit_stage_request,
    matching_commit_stage_request_packet,
)
from .startup_context_refresh import startup_context_advisory_from_step


CommandRunner = Callable[[str, list[str], Path], dict[str, object]]


@dataclass(frozen=True, slots=True)
class StartupContextRefreshResult:
    """Outcome of the startup-context receipt refresh preflight step."""

    ok: bool
    warnings: tuple[str, ...] = ()
    advisory_action: str = ""
    advisory_reason: str = ""


@dataclass(frozen=True, slots=True)
class AttentionRevisionRefreshDecision:
    """Decision after refreshing startup receipt and rechecking attention."""

    status: str
    warnings: tuple[str, ...] = ()


def refresh_startup_context_receipt_before_vcs_preflight(
    *,
    repo_root: Path,
    next_step_label: str,
    command_runner: CommandRunner | None = None,
) -> StartupContextRefreshResult:
    """Run the existing startup-context command so its receipt matches live attention."""
    entrypoint = repo_root / "dev/scripts/devctl.py"
    if not entrypoint.is_file():
        return StartupContextRefreshResult(ok=True)
    runner = command_runner or _run_startup_context_command
    step = runner(
        "commit-refresh-startup-context",
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "startup-context",
            "--format",
            "summary",
        ],
        repo_root,
    )
    returncode_value = step.get("returncode", 1)
    returncode = int(returncode_value) if returncode_value is not None else 1
    if returncode == 0:
        return StartupContextRefreshResult(
            ok=True,
            warnings=(
                f"Refreshed startup-context receipt before {next_step_label}.",
            ),
        )
    advisory_action, advisory_reason = startup_context_advisory_from_step(step)
    if advisory_action:
        advisory_detail = f"action={advisory_action}"
        if advisory_reason:
            advisory_detail = f"{advisory_detail}, reason={advisory_reason}"
        return StartupContextRefreshResult(
            ok=True,
            warnings=(
                "Refreshed startup-context receipt before "
                f"{next_step_label}; startup-context returned advisory "
                f"{advisory_detail} (exit {returncode}).",
            ),
            advisory_action=advisory_action,
            advisory_reason=advisory_reason,
        )
    detail = str(step.get("failure_output") or step.get("error") or "").strip()
    warning = (
        f"startup-context refresh failed before {next_step_label}"
        f" (exit {returncode})"
    )
    if detail:
        warning = f"{warning}: {detail}"
    return StartupContextRefreshResult(ok=False, warnings=(warning,))


def refresh_and_recheck_attention_revision(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
    held_lease: str,
    next_step_label: str,
    stale_check_fn: Callable[..., bool] | None = None,
    command_runner: CommandRunner | None = None,
) -> AttentionRevisionRefreshDecision:
    """Refresh startup receipt once, then rerun the stale-attention check."""
    refresh_result = refresh_startup_context_receipt_before_vcs_preflight(
        repo_root=repo_root,
        next_step_label=next_step_label,
        command_runner=command_runner,
    )
    if not refresh_result.ok:
        return AttentionRevisionRefreshDecision(
            status="refresh_failed",
            warnings=refresh_result.warnings,
        )
    check_fn = stale_check_fn or attention_revision_stale
    if check_fn(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        held_lease=held_lease,
    ):
        return AttentionRevisionRefreshDecision(
            status="stale",
            warnings=refresh_result.warnings,
        )
    return AttentionRevisionRefreshDecision(
        status="fresh",
        warnings=refresh_result.warnings,
    )


def _run_startup_context_command(
    name: str,
    command: list[str],
    cwd: Path,
) -> dict[str, object]:
    return run_cmd(name, command, cwd=cwd, live_output=False)


def attention_revision_stale(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
    held_lease: str = "",
) -> bool:
    """Return true when packet attention changed since the latest startup receipt.

    When `held_lease` is a non-empty revision string, treat it as authoritative:
    the caller (e.g., the commit-pipeline post-approval window) has pinned the
    attention revision and subsequent typed-state writes must not re-trigger the
    stale gate. This is the Q100 attention-revision-lease pattern. Callers that
    still want the pre-lease, receipt-comparison semantics pass an empty lease.
    """
    if _held_lease_active(held_lease):
        return False
    review_state = load_live_review_state(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
    )
    if review_state is None:
        return False
    packet_inbox = getattr(review_state, "packet_inbox", None)
    if packet_inbox is None:
        return False
    current_attention_revision = str(
        getattr(packet_inbox, "attention_revision", "") or ""
    ).strip()
    if not current_attention_revision:
        return False
    target_agent = resolve_commit_execution_target(review_state)
    if not _target_agent_has_actionable_packet_attention(
        packet_inbox=packet_inbox,
        target_agent=target_agent,
    ):
        return False
    receipt = load_startup_receipt(repo_root=repo_root)
    if receipt is None:
        return True
    return receipt.attention_revision != current_attention_revision

def live_attention_revision(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
) -> str:
    """Return the current live packet-inbox attention revision, or empty string."""
    review_state = load_live_review_state(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
    )
    if review_state is None:
        return ""
    packet_inbox = getattr(review_state, "packet_inbox", None)
    if packet_inbox is None:
        return ""
    return str(getattr(packet_inbox, "attention_revision", "") or "").strip()

def post_commit_execution_handoff(
    *,
    pipeline: RemoteCommitPipelineContract,
    repo_root: Path,
    review_channel_path: Path | None,
) -> tuple[str, str, str]:
    """Post one typed commit handoff when the local lane cannot write `.git`."""
    review_state = load_live_review_state(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
    )
    target_agent = resolve_commit_execution_target(review_state)
    if review_channel_path is None:
        return "", "", "commit_execution_request_review_channel_missing"
    if not target_agent:
        return "", "", "commit_execution_target_unavailable"
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    try:
        _, event = post_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            request=build_commit_execution_request(
                pipeline,
                to_agent=target_agent,
                body=(
                    "The current lane hit `.git/index.lock` permission denial "
                    "while running the already-approved governed commit. "
                    "Resume the same runtime-bound pipeline from the writable "
                    "lane without restaging."
                ),
            ),
        )
    except (OSError, ValueError) as exc:
        return target_agent, "", f"commit_execution_request_failed: {exc}"
    return target_agent, str(event.get("packet_id") or "").strip(), ""


def post_commit_stage_handoff(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
    commit_message_draft: str,
    stage_reason: str,
    stage_warnings: list[str] | tuple[str, ...] = (),
) -> tuple[str, str, str]:
    """Post one typed stage handoff when local sandbox policy blocks `.git`."""
    review_state = load_live_review_state(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
    )
    target_agent = resolve_commit_stage_target(review_state)
    if review_channel_path is None:
        return "", "", "commit_stage_request_review_channel_missing"
    if not target_agent:
        return "", "", "commit_stage_target_unavailable"
    head_sha = head_commit(repo_root)
    existing_packet = matching_commit_stage_request_packet(
        getattr(review_state, "packets", ()),
        to_agent=target_agent,
        head_sha=head_sha,
    )
    if existing_packet is not None:
        packet_id = (
            existing_packet.get("packet_id")
            if isinstance(existing_packet, dict)
            else getattr(existing_packet, "packet_id", "")
        )
        return target_agent, str(packet_id or "").strip(), ""
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    try:
        _, event = post_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            request=build_commit_stage_request(
                CommitStageRequestFields(
                    to_agent=target_agent,
                    head_sha=head_sha,
                    commit_message_draft=commit_message_draft,
                    stage_reason=stage_reason,
                    stage_warnings=tuple(stage_warnings),
                )
            ),
        )
    except (OSError, ValueError) as exc:
        return target_agent, "", f"commit_stage_request_failed: {exc}"
    return target_agent, str(event.get("packet_id") or "").strip(), ""


def load_live_review_state(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
) -> ReviewState | None:
    """Return the latest typed review state when event-backed projections exist."""
    if review_channel_path is None or not review_channel_path.exists():
        return None
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    try:
        bundle = load_or_refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
    except ValueError:
        return None
    return review_state_from_payload(bundle.review_state)
