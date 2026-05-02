"""Argument validation for the `devctl review-channel` command."""

from __future__ import annotations

from ...review_channel.follow_stream import validate_follow_json_format
from ...review_channel.peer_liveness import reviewer_mode_is_active
from .constants import COMMON_NONNEGATIVE_LIMITS
from .constants import COMMON_POSITIVE_LIMITS
from .constants import FOLLOW_JSON_ACTIONS
from .constants import LIMITED_QUERY_ACTIONS
from .constants import PACKET_TRANSITION_ACTIONS
from .constants import POST_REQUIRED_ARGS
from .constants import ReviewChannelAction


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


def _require_provided(args, attr: str, message: str) -> None:
    """Require one CLI attribute to be present, allowing explicit empty values."""
    if getattr(args, attr, None) is None:
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
    checkpoint_payload_file = getattr(args, "checkpoint_payload_file", None)
    if checkpoint_payload_file:
        conflicting_attrs = (
            "verdict",
            "verdict_file",
            "open_findings",
            "open_findings_file",
            "instruction",
            "instruction_file",
            "reviewed_scope_item",
        )
        present_conflicts = [
            attr for attr in conflicting_attrs if getattr(args, attr, None)
        ]
        if present_conflicts:
            raise ValueError(
                "review-channel reviewer-checkpoint does not allow "
                "--checkpoint-payload-file together with inline/file body flags "
                "or --reviewed-scope-item."
            )
        if reviewer_mode_is_active(getattr(args, "reviewer_mode", None)):
            _require_provided(
                args,
                "expected_instruction_revision",
                "review-channel reviewer-checkpoint requires "
                "--expected-instruction-revision in active_dual_agent mode. "
                "Use the live `current_instruction_revision` from bridge-poll/status.",
            )
            _require_present(
                args,
                "expected_implementer_state_hash",
                "review-channel reviewer-checkpoint requires "
                "--expected-implementer-state-hash in active_dual_agent mode. "
                "Use the live `implementer_state_hash` from bridge-poll/status.",
            )
        return

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
        _require_provided(
            args,
            "expected_instruction_revision",
            "review-channel reviewer-checkpoint requires "
            "--expected-instruction-revision in active_dual_agent mode. "
            "Use the live `current_instruction_revision` from bridge-poll/status.",
        )
        _require_present(
            args,
            "expected_implementer_state_hash",
            "review-channel reviewer-checkpoint requires "
            "--expected-implementer-state-hash in active_dual_agent mode. "
            "Use the live `implementer_state_hash` from bridge-poll/status.",
        )


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
    normalized_action = action or ReviewChannelAction(str(getattr(args, "action", None)))
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
    elif normalized_action is ReviewChannelAction.ATTACH_REMOTE_CONTROL:
        attachment_status = str(
            getattr(args, "attachment_status", "attached") or "attached"
        ).strip()
        if attachment_status == "attached" and not (
            getattr(args, "session_url", None)
            or getattr(args, "remote_session_id", None)
        ):
            raise ValueError(
                "review-channel attach-remote-control requires --session-url "
                "or --remote-session-id when --attachment-status=attached."
            )
    elif (
        normalized_action in PACKET_TRANSITION_ACTIONS
        or normalized_action is ReviewChannelAction.SHOW
    ):
        _require_present(
            args,
            "packet_id",
            f"--packet-id is required for review-channel {normalized_action.value}.",
        )
        if normalized_action in PACKET_TRANSITION_ACTIONS:
            _require_present(
                args,
                "actor",
                f"--actor is required for review-channel {normalized_action.value}.",
            )
    elif normalized_action is ReviewChannelAction.REVIEWER_CHECKPOINT:
        _validate_reviewer_checkpoint_args(args)

    if (
        normalized_action in LIMITED_QUERY_ACTIONS
        and getattr(args, "to_agent", None)
    ):
        raise ValueError(
            "--to-agent is only valid for review-channel post. "
            "Use --target for inbox/watch/history filters."
        )

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
    if (
        normalized_action is ReviewChannelAction.STOP
        and float(getattr(args, "stop_grace_seconds", 0.0)) < 0.0
    ):
        raise ValueError("--stop-grace-seconds must be zero or greater.")

    if normalized_action in FOLLOW_JSON_ACTIONS and getattr(args, "follow", False):
        validate_follow_json_format(
            action=normalized_action.value,
            output_format=getattr(args, "format", "json"),
        )
