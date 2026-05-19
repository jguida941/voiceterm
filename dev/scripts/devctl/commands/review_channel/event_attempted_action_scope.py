"""Scope helpers for review-channel attempted-action receipts."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ...runtime.control_decision_obedience import _proxy_execution as proxy_execution
from ...runtime.value_coercion import coerce_string


@dataclass(frozen=True, slots=True)
class ProxyAuthorityRoute:
    executor_actor: str
    executor_role: str
    executor_session_id: str
    subject_actor: str
    subject_role: str
    subject_session_id: str


@dataclass(frozen=True, slots=True)
class ProxyAuthoritySource:
    decision_id: str
    snapshot_id: str
    latest_event_id: str


def action_actor(args) -> str:
    return coerce_string(
        getattr(args, "actor", "")
        or getattr(args, "from_agent", "")
        or getattr(args, "to_agent", "")
    ).strip()


def action_role(args) -> str:
    actor_role = coerce_string(getattr(args, "actor_role", "")).strip()
    if actor_role:
        return actor_role
    if coerce_string(getattr(args, "action", "")).strip() == "post":
        return coerce_string(getattr(args, "role", "")).strip()
    return coerce_string(
        getattr(args, "role", "") or getattr(args, "target_role", "")
    ).strip()


def action_session_id(args) -> str:
    if coerce_string(getattr(args, "action", "")).strip() == "post":
        return coerce_string(getattr(args, "session_id", "")).strip()
    return coerce_string(
        (
            getattr(args, "session_id", "") or getattr(args, "target_session_id", "")
        )
        if coerce_string(getattr(args, "actor_role", "")).strip()
        else (getattr(args, "target_session_id", "") or getattr(args, "session_id", ""))
    ).strip()


def executor_actor(args, *, fallback_actor: str) -> str:
    explicit = coerce_string(getattr(args, "executor_actor", "")).strip()
    if explicit:
        return explicit
    env_actor = coerce_string(os.environ.get("DEVCTL_EXECUTOR_ACTOR")).strip()
    if env_actor:
        return env_actor
    if coerce_string(os.environ.get("CODEX_THREAD_ID")).strip():
        return "codex"
    return fallback_actor


def executor_role(
    args,
    *,
    fallback_role: str,
    executor_actor: str,
    subject_actor: str,
) -> str:
    explicit = coerce_string(getattr(args, "executor_role", "")).strip()
    if explicit:
        return explicit
    env_role = coerce_string(os.environ.get("DEVCTL_EXECUTOR_ROLE")).strip()
    if env_role:
        return env_role
    return fallback_role if executor_actor == subject_actor else ""


def executor_session_id(
    args,
    *,
    fallback_session_id: str,
    executor_actor: str,
    subject_actor: str,
) -> str:
    explicit = coerce_string(getattr(args, "executor_session_id", "")).strip()
    if explicit:
        return explicit
    env_session = coerce_string(os.environ.get("DEVCTL_EXECUTOR_SESSION_ID")).strip()
    if env_session:
        return env_session
    if executor_actor != subject_actor:
        return coerce_string(os.environ.get("CODEX_THREAD_ID")).strip()
    return fallback_session_id


def proxy_authority_ref(
    args,
    *,
    route: ProxyAuthorityRoute,
    source: ProxyAuthoritySource,
) -> str:
    explicit = coerce_string(getattr(args, "proxy_authority_ref", "")).strip()
    if explicit:
        return explicit
    if not proxy_execution(
        executor_actor=route.executor_actor,
        executor_role=route.executor_role,
        executor_session_id=route.executor_session_id,
        subject_actor=route.subject_actor,
        subject_role=route.subject_role,
        subject_session_id=route.subject_session_id,
    ):
        return ""
    return source.decision_id or source.snapshot_id or source.latest_event_id


def review_channel_attempted_argv(args, *, packet_id: str = "") -> tuple[str, ...]:
    argv = ["review-channel", "--action", coerce_string(getattr(args, "action", ""))]
    packet_kind = coerce_string(getattr(args, "kind", "")).strip()
    if packet_kind:
        argv.extend(("--kind", packet_kind))
    if packet_id:
        argv.extend(("--packet-id", packet_id))
    for option, attr in (
        ("--requested-action", "requested_action"),
        ("--target-kind", "target_kind"),
        ("--target-ref", "target_ref"),
        ("--target-revision", "target_revision"),
        ("--target-role", "target_role"),
        ("--target-session-id", "target_session_id"),
        ("--full-guard-bundle-evidence", "full_guard_bundle_evidence"),
    ):
        value = coerce_string(getattr(args, attr, "")).strip()
        if value:
            argv.extend((option, value))
    actor = action_actor(args)
    if actor:
        argv.extend(("--actor", actor))
    actor_role = coerce_string(getattr(args, "actor_role", "")).strip()
    if actor_role:
        argv.extend(("--actor-role", actor_role))
    session_id = coerce_string(getattr(args, "session_id", "")).strip()
    if session_id:
        argv.extend(("--session-id", session_id))
    return tuple(item for item in argv if item)


def review_channel_attempted_command(args, *, packet_id: str = "") -> str:
    return " ".join(
        (
            "python3",
            "dev/scripts/devctl.py",
            *review_channel_attempted_argv(args, packet_id=packet_id),
        )
    )


__all__ = [
    "ProxyAuthorityRoute",
    "ProxyAuthoritySource",
    "action_actor",
    "action_role",
    "action_session_id",
    "executor_actor",
    "executor_role",
    "executor_session_id",
    "proxy_authority_ref",
    "review_channel_attempted_argv",
    "review_channel_attempted_command",
]
