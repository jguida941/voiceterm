"""Typed attach/auth projection helpers for review-channel state."""

from __future__ import annotations

from typing import TypedDict


class ServiceIdentityState(TypedDict):
    """Typed service identity/discovery payload for one repo/worktree."""

    service_id: str
    project_id: str
    repo_root: str
    worktree_root: str
    bridge_path: str
    review_channel_path: str
    status_root: str
    discovery_fields: list[str]


class ServiceEndpointState(TypedDict):
    """Typed local service endpoint contract."""

    service_id: str
    launch_entrypoints: list[str]
    discovery_fields: list[str]
    health_signals: list[str]
    shutdown_entrypoints: list[str]


class CallerAuthorityState(TypedDict):
    """Typed caller authority bucket set for one caller class."""

    caller_id: str
    allowed_actions: list[str]
    stage_only_actions: list[str]
    approval_required_actions: list[str]
    forbidden_actions: list[str]


class AttachAuthPolicyState(TypedDict):
    """Typed attach/auth policy for the current review-channel backend."""

    attach_scope: str
    local_only: bool
    off_lan_allowed: bool
    transport: str
    auth_mode: str
    token_required: bool
    key_required: bool
    approval_boundary: str
    attach_entrypoints: list[str]
    service_endpoint: ServiceEndpointState
    caller_authority: list[CallerAuthorityState]


def build_service_identity_state(
    service_identity: dict[str, object],
) -> ServiceIdentityState:
    return ServiceIdentityState(
        service_id=str(service_identity.get("service_id") or ""),
        project_id=str(service_identity.get("project_id") or ""),
        repo_root=str(service_identity.get("repo_root") or ""),
        worktree_root=str(service_identity.get("worktree_root") or ""),
        bridge_path=str(service_identity.get("bridge_path") or ""),
        review_channel_path=str(service_identity.get("review_channel_path") or ""),
        status_root=str(service_identity.get("status_root") or ""),
        discovery_fields=[
            str(field)
            for field in list(service_identity.get("discovery_fields") or [])
            if str(field)
        ],
    )


def build_attach_auth_policy_state(
    attach_auth_policy: dict[str, object],
) -> AttachAuthPolicyState:
    service_endpoint = attach_auth_policy.get("service_endpoint")
    caller_authority = attach_auth_policy.get("caller_authority")
    return AttachAuthPolicyState(
        attach_scope=str(attach_auth_policy.get("attach_scope") or ""),
        local_only=bool(attach_auth_policy.get("local_only")),
        off_lan_allowed=bool(attach_auth_policy.get("off_lan_allowed")),
        transport=str(attach_auth_policy.get("transport") or ""),
        auth_mode=str(attach_auth_policy.get("auth_mode") or ""),
        token_required=bool(attach_auth_policy.get("token_required")),
        key_required=bool(attach_auth_policy.get("key_required")),
        approval_boundary=str(attach_auth_policy.get("approval_boundary") or ""),
        attach_entrypoints=[
            str(entry)
            for entry in list(attach_auth_policy.get("attach_entrypoints") or [])
            if str(entry)
        ],
        service_endpoint=ServiceEndpointState(
            service_id=(
                str(service_endpoint.get("service_id") or "")
                if isinstance(service_endpoint, dict)
                else ""
            ),
            launch_entrypoints=_policy_list(service_endpoint, "launch_entrypoints"),
            discovery_fields=_policy_list(service_endpoint, "discovery_fields"),
            health_signals=_policy_list(service_endpoint, "health_signals"),
            shutdown_entrypoints=_policy_list(service_endpoint, "shutdown_entrypoints"),
        ),
        caller_authority=[
            CallerAuthorityState(
                caller_id=str(policy.get("caller_id") or ""),
                allowed_actions=_policy_list(policy, "allowed_actions"),
                stage_only_actions=_policy_list(policy, "stage_only_actions"),
                approval_required_actions=_policy_list(
                    policy,
                    "approval_required_actions",
                ),
                forbidden_actions=_policy_list(policy, "forbidden_actions"),
            )
            for policy in list(caller_authority or [])
            if isinstance(policy, dict)
        ],
    )


def _policy_list(payload: object, key: str) -> list[str]:
    if not isinstance(payload, dict):
        return []
    return [
        str(item)
        for item in list(payload.get(key) or [])
        if str(item)
    ]
