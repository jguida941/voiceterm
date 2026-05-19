"""Controller-action matching helpers for control-decision obedience."""

from __future__ import annotations

import shlex
from collections.abc import Mapping, Sequence

from .review_channel_post_actions import required_review_channel_post_action
from .value_coercion import coerce_bool, coerce_string


def action_mutates(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    if allowed_controller_action(action, decision=decision):
        return False
    if coerce_bool(action.get("mutates")) or coerce_bool(action.get("writes_state")):
        return True
    mutation_tokens = (
        "apply_patch",
        "git commit",
        "git push",
        "raw-git",
        "raw_git",
        "devctl.py push",
        " review-channel --action post",
        " review-channel --action apply",
        " review-channel --action dismiss",
        " review-channel --action absorb",
    )
    return any(token in action_text(action) for token in mutation_tokens)


def allowed_controller_action(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    return _allowed_exact_action_kind(
        action,
        decision=decision,
    ) or _allowed_packet_attention_action(
        action,
        decision=decision,
    ) or _allowed_review_channel_post(action, decision=decision)


def action_text(action: Mapping[str, object]) -> str:
    argv = action.get("argv")
    if isinstance(argv, Sequence) and not isinstance(argv, (str, bytes)):
        return " ".join(coerce_string(item) for item in argv).lower()
    return " ".join(
        coerce_string(action.get(key))
        for key in ("action_kind", "command_name", "command", "next_action")
    ).lower()


def _allowed_packet_attention_action(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    text = action_text(action)
    is_show = "review-channel --action show" in text
    is_ingest = "review-channel --action ingest" in text
    is_absorb = "review-channel --action absorb" in text
    if not (is_show or is_ingest or is_absorb):
        return False
    packet_id = _packet_id_from_action(action)
    if is_absorb:
        if not coerce_bool(decision.get("absorption_required")):
            return False
        allowed_packet_ids = {
            coerce_string(decision.get("absorption_packet_id")),
            coerce_string(decision.get("attention_packet_id")),
        }
    elif is_ingest:
        if not coerce_bool(decision.get("semantic_ingestion_required")):
            return False
        allowed_packet_ids = {
            coerce_string(decision.get("semantic_ingestion_packet_id")),
            coerce_string(decision.get("attention_packet_id")),
        }
    else:
        if not coerce_bool(decision.get("body_open_required")):
            return False
        allowed_packet_ids = {
            coerce_string(decision.get("body_open_packet_id")),
            coerce_string(decision.get("active_packet_id")),
            coerce_string(decision.get("attention_packet_id")),
        }
    allowed_packet_ids.discard("")
    return bool(allowed_packet_ids) and packet_id in allowed_packet_ids


def _allowed_exact_action_kind(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    allowed_actions = decision.get("allowed_actions")
    if not isinstance(allowed_actions, Sequence) or isinstance(
        allowed_actions,
        (str, bytes),
    ):
        return False
    normalized_allowed = {
        coerce_string(item).strip().lower() for item in allowed_actions
    }
    candidates = {
        coerce_string(action.get("action_kind")).strip().lower(),
        coerce_string(action.get("command_name")).strip().lower(),
        coerce_string(action.get("next_action")).strip().lower(),
    }
    candidates.discard("")
    return bool(candidates & normalized_allowed)


def _allowed_review_channel_post(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    argv = _action_argv(action)
    if not _argv_is_review_channel_post(argv, action):
        return False
    kind = _argv_option_value(argv, "--kind").strip().lower()
    required_allowed_action = required_review_channel_post_action(argv, kind=kind)
    if not required_allowed_action:
        return False
    allowed_actions = decision.get("allowed_actions")
    if not isinstance(allowed_actions, Sequence) or isinstance(
        allowed_actions,
        (str, bytes),
    ):
        return False
    normalized_allowed = {
        coerce_string(item).strip().lower() for item in allowed_actions
    }
    if required_allowed_action not in normalized_allowed:
        return False
    if kind == "action_request":
        return _allowed_review_channel_action_request_post(argv)
    return True


def _allowed_review_channel_action_request_post(argv: Sequence[str]) -> bool:
    requested_action = _argv_option_value(argv, "--requested-action").strip()
    target_kind = _argv_option_value(argv, "--target-kind").strip()
    target_ref = _argv_option_value(argv, "--target-ref").strip()
    target_revision = _argv_option_value(argv, "--target-revision").strip()
    guard_evidence = _argv_option_value(argv, "--full-guard-bundle-evidence").strip()
    return (
        requested_action == "stage_commit_pipeline"
        and target_kind == "runtime"
        and target_ref.startswith("devctl_commit:")
        and bool(target_revision)
        and bool(guard_evidence)
    )


def _argv_is_review_channel_post(
    argv: Sequence[str],
    action: Mapping[str, object],
) -> bool:
    normalized = tuple(coerce_string(item).strip().lower() for item in argv)
    if "review-channel" not in normalized:
        return False
    if _argv_option_value(normalized, "--action").strip().lower() == "post":
        return True
    return coerce_string(action.get("action_kind")).strip().lower() == "review-channel.post"


def _argv_option_value(argv: Sequence[str], option: str) -> str:
    for index, token in enumerate(argv):
        if coerce_string(token).strip().lower() != option:
            continue
        if index + 1 >= len(argv):
            return ""
        return coerce_string(argv[index + 1])
    return ""


def _action_argv(action: Mapping[str, object]) -> tuple[str, ...]:
    argv = action.get("argv")
    if isinstance(argv, Sequence) and not isinstance(argv, (str, bytes)):
        return tuple(
            coerce_string(item).strip()
            for item in argv
            if coerce_string(item).strip()
        )
    command = coerce_string(action.get("command")).strip()
    if command:
        try:
            return tuple(shlex.split(command))
        except ValueError:
            return tuple(command.split())
    return ()


def _packet_id_from_action(action: Mapping[str, object]) -> str:
    explicit = coerce_string(action.get("packet_id"))
    if explicit:
        return explicit
    text = action_text(action)
    marker = "--packet-id "
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split()[0].strip("'\"")


__all__ = [
    "action_mutates",
    "action_text",
    "allowed_controller_action",
]
