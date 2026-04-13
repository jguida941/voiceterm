"""Caller-lane enforcement for governed commit."""

from __future__ import annotations

import os

from .governed_executor_actions import _build_report

_CALLER_ROLE_ENV_VARS = ("DEVCTL_CALLER_ROLE", "REVIEW_CHANNEL_CALLER_ROLE")
_MUTATION_BLOCKED_CALLER_ROLES = frozenset({"dashboard", "observer", "reviewer"})


def caller_role_report(args) -> dict[str, object] | None:
    """Block governed mutation when the current lane is findings-only."""
    caller_role, source = _resolve_caller_role(args)
    if caller_role not in _MUTATION_BLOCKED_CALLER_ROLES:
        return None

    guidance = (
        "Dashboard/observer lanes are read/findings-only. Post a typed "
        "`action_request` or `finding` packet and let the implementer lane "
        "run `devctl commit`."
    )
    allowed_outputs: list[str] = ["finding_packet", "action_request_packet"]
    if caller_role == "reviewer":
        guidance = (
            "Reviewer lane is review-only by default. Use the implementer "
            "lane for `devctl commit`, or rerun the reviewer lane with an "
            "explicit implementation takeover before mutating the repo."
        )
        allowed_outputs = ["finding_packet", "review_checkpoint"]

    return _build_report(
        status="blocked",
        reason="caller_role_blocked",
        caller_role=caller_role,
        caller_role_source=source,
        blocked_actions=["vcs.stage", "vcs.commit", "vcs.push"],
        allowed_outputs=allowed_outputs,
        operator_guidance=guidance,
    )


def _resolve_caller_role(args) -> tuple[str, str]:
    explicit_role = _normalize_caller_role(getattr(args, "role", None))
    if explicit_role:
        return explicit_role, "arg:role"
    for env_name in _CALLER_ROLE_ENV_VARS:
        env_role = _normalize_caller_role(os.environ.get(env_name))
        if env_role:
            return env_role, f"env:{env_name}"
    return "", ""


def _normalize_caller_role(value: object) -> str:
    role = str(value or "").strip().lower()
    if role in {"dashboard", "implementer", "observer", "reviewer"}:
        return role
    return ""
