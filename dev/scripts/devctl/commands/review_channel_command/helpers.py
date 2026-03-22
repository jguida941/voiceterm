"""Helper functions for the `devctl review-channel` command."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...approval_mode import normalize_approval_mode
from ...review_channel.events import resolve_artifact_paths
from ...review_channel.follow_stream import validate_follow_json_format
from ...review_channel.peer_liveness import reviewer_mode_is_active
from ..review_channel_bridge_handler import _render_bridge_md
from ..review_channel_event_handler import _render_event_md
from .constants import CLI_RUNTIME_PATH_ARGS
from .constants import COMMON_NONNEGATIVE_LIMITS
from .constants import COMMON_POSITIVE_LIMITS
from .constants import EVENT_STATUS_FALLBACK_DETAIL
from .constants import FOLLOW_JSON_ACTIONS
from .constants import LIMITED_QUERY_ACTIONS
from .constants import PACKET_TRANSITION_ACTIONS
from .constants import POST_REQUIRED_ARGS
from .constants import ReviewChannelAction
from .models import ReviewChannelErrorReport
from .models import RuntimePaths


def _coerce_action(action: object) -> ReviewChannelAction:
    """Normalize one CLI action string."""
    try:
        return ReviewChannelAction(str(action))
    except ValueError as exc:
        raise ValueError(f"Unsupported review-channel action: {action}") from exc


def _coerce_runtime_paths(paths: RuntimePaths | Mapping[str, object]) -> RuntimePaths:
    """Accept typed paths or legacy dict inputs."""
    if isinstance(paths, RuntimePaths):
        return paths
    return RuntimePaths.from_mapping(paths)


def _require_positive(flag: str, value: int) -> None:
    """Require a strictly positive CLI numeric value."""
    if value <= 0:
        raise ValueError(f"{flag} must be greater than zero.")


def _require_nonnegative(flag: str, value: int) -> None:
    """Require a zero-or-greater CLI numeric value."""
    if value < 0:
        raise ValueError(f"{flag} must be zero or greater.")


def _require_present(args, attr: str, message: str) -> None:
    """Require one CLI attribute to be truthy."""
    if not getattr(args, attr, None):
        raise ValueError(message)


def _require_percentage(flag: str, value: int) -> None:
    """Require a one-to-one-hundred percentage."""
    if value <= 0 or value > 100:
        raise ValueError(f"{flag} must be between 1 and 100.")


def _validate_required_args(
    args,
    requirements: tuple[tuple[str, str], ...],
) -> None:
    """Validate a tuple of required CLI attributes."""
    for attr, message in requirements:
        _require_present(args, attr, message)


def _require_exactly_one(
    args,
    *,
    attrs: tuple[str, str],
    message: str,
) -> None:
    """Require exactly one of the two related CLI attributes."""
    present = [attr for attr in attrs if getattr(args, attr, None)]
    if len(present) != 1:
        raise ValueError(message)


def _validate_reviewer_checkpoint_args(args) -> None:
    """Validate reviewer-checkpoint inline-vs-file body arguments."""
    _require_exactly_one(
        args,
        attrs=("verdict", "verdict_file"),
        message=(
            "review-channel reviewer-checkpoint requires exactly one of "
            "--verdict or --verdict-file."
        ),
    )
    _require_exactly_one(
        args,
        attrs=("open_findings", "open_findings_file"),
        message=(
            "review-channel reviewer-checkpoint requires exactly one of "
            "--open-findings or --open-findings-file."
        ),
    )
    _require_exactly_one(
        args,
        attrs=("instruction", "instruction_file"),
        message=(
            "review-channel reviewer-checkpoint requires exactly one of "
            "--instruction or --instruction-file."
        ),
    )
    _require_present(
        args,
        "reviewed_scope_item",
        "--reviewed-scope-item is required for review-channel reviewer-checkpoint.",
    )
    if reviewer_mode_is_active(getattr(args, "reviewer_mode", None)):
        _require_present(
            args,
            "expected_instruction_revision",
            "review-channel reviewer-checkpoint requires "
            "--expected-instruction-revision in active_dual_agent mode. "
            "Use the live `current_instruction_revision` from bridge-poll/status.",
        )


def _error_report(args, message: str, *, exit_code: int) -> tuple[dict[str, object], int]:
    """Build a structured failure report."""
    dangerous = bool(getattr(args, "dangerous", False))
    payload = ReviewChannelErrorReport(
        action=getattr(args, "action", None),
        exit_code=exit_code,
        execution_mode=getattr(args, "execution_mode", "auto"),
        terminal=getattr(args, "terminal", "terminal-app"),
        terminal_profile_requested=getattr(args, "terminal_profile", None),
        approval_mode=normalize_approval_mode(
            getattr(args, "approval_mode", None),
            dangerous=dangerous,
        ),
        dangerous=dangerous,
        rollover_threshold_pct=getattr(args, "rollover_threshold_pct", None),
        rollover_trigger=getattr(args, "rollover_trigger", None),
        await_ack_seconds=getattr(args, "await_ack_seconds", None),
        errors=[message],
    )
    return payload.to_report(), exit_code


def _render_report(report: dict[str, object]) -> str:
    """Render one report as markdown."""
    if report.get("report_mode") == "event-backed":
        return _render_event_md(report)
    return _render_bridge_md(report)


def _event_report_error_detail(report: dict[str, object]) -> str:
    """Summarize event report errors."""
    errors = report.get("errors")
    if not isinstance(errors, list):
        return EVENT_STATUS_FALLBACK_DETAIL

    messages = [text for error in errors if (text := str(error).strip())]
    return "; ".join(messages) or EVENT_STATUS_FALLBACK_DETAIL


def _validate_common_limits(args, action: ReviewChannelAction) -> None:
    """Validate shared numeric CLI bounds."""
    _require_percentage(
        "--rollover-threshold-pct",
        getattr(args, "rollover_threshold_pct", 50),
    )

    if action in LIMITED_QUERY_ACTIONS:
        _require_positive("--limit", getattr(args, "limit", 20))

    for flag, attr, default in COMMON_NONNEGATIVE_LIMITS:
        _require_nonnegative(flag, getattr(args, attr, default))

    for flag, attr, default in COMMON_POSITIVE_LIMITS:
        _require_positive(flag, getattr(args, attr, default))


def _validate_args(
    args,
    action: ReviewChannelAction | None = None,
) -> None:
    """Validate review-channel CLI arguments."""
    normalized_action = action or _coerce_action(getattr(args, "action", None))
    _validate_common_limits(args, normalized_action)

    if (
        normalized_action is ReviewChannelAction.ROLLOVER
        and getattr(args, "await_ack_seconds", 0) <= 0
    ):
        raise ValueError(
            "--await-ack-seconds must be greater than zero for rollover so "
            "fresh-session ACK stays fail-closed."
        )

    if normalized_action is ReviewChannelAction.POST:
        _validate_required_args(args, POST_REQUIRED_ARGS)
        if bool(getattr(args, "body", None)) == bool(getattr(args, "body_file", None)):
            raise ValueError("Review-channel post requires exactly one of --body or --body-file.")
    elif normalized_action in PACKET_TRANSITION_ACTIONS:
        _require_present(
            args,
            "packet_id",
            f"--packet-id is required for review-channel {normalized_action.value}.",
        )
        _require_present(
            args,
            "actor",
            f"--actor is required for review-channel {normalized_action.value}.",
        )
    elif normalized_action is ReviewChannelAction.REVIEWER_CHECKPOINT:
        _validate_reviewer_checkpoint_args(args)

    if (
        getattr(args, "start_publisher_if_missing", False)
        and normalized_action is not ReviewChannelAction.ENSURE
    ):
        raise ValueError("--start-publisher-if-missing is only valid for review-channel ensure.")

    if (
        normalized_action is ReviewChannelAction.REVIEWER_CHECKPOINT
        and getattr(args, "follow", False)
    ):
        raise ValueError("review-channel reviewer-checkpoint does not support --follow.")
    if (
        normalized_action is ReviewChannelAction.IMPLEMENTER_WAIT
        and getattr(args, "follow", False)
    ):
        raise ValueError("review-channel implementer-wait does not support --follow.")
    if (
        normalized_action is ReviewChannelAction.REVIEWER_WAIT
        and getattr(args, "follow", False)
    ):
        raise ValueError("review-channel reviewer-wait does not support --follow.")

    if normalized_action in FOLLOW_JSON_ACTIONS and getattr(args, "follow", False):
        validate_follow_json_format(
            action=normalized_action.value,
            output_format=getattr(args, "format", "json"),
        )


def _resolve_runtime_paths(args, repo_root: Path) -> RuntimePaths:
    """Resolve review-channel runtime paths."""
    resolved_paths = {
        name: (repo_root / getattr(args, name)).resolve()
        for name in CLI_RUNTIME_PATH_ARGS
    }
    promotion_plan_rel = getattr(args, "promotion_plan", None)
    script_dir = None
    if getattr(args, "script_dir", None):
        script_dir = (repo_root / args.script_dir).resolve()

    artifact_paths = resolve_artifact_paths(
        repo_root=repo_root,
        artifact_root_rel=getattr(args, "artifact_root", None),
        state_json_rel=getattr(args, "state_json", None),
        projections_dir_rel=getattr(args, "emit_projections", None),
    )
    return RuntimePaths(
        **resolved_paths,
        promotion_plan_path=(
            (repo_root / str(promotion_plan_rel)).resolve()
            if promotion_plan_rel
            else None
        ),
        script_dir=script_dir,
        artifact_paths=artifact_paths,
    )
