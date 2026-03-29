"""Markdown helpers for review-channel attach/auth sections."""

from __future__ import annotations


def append_attach_auth_policy_markdown(
    lines: list[str],
    attach_auth_policy: object,
) -> None:
    """Append a concise attach/auth section when the payload is present."""
    if not isinstance(attach_auth_policy, dict):
        return
    service_endpoint = attach_auth_policy.get("service_endpoint")
    caller_authority = attach_auth_policy.get("caller_authority")
    lines.append("")
    lines.append("## Attach/Auth Policy")
    lines.append(f"- attach_scope: {attach_auth_policy.get('attach_scope') or 'n/a'}")
    lines.append(f"- transport: {attach_auth_policy.get('transport') or 'n/a'}")
    lines.append(f"- auth_mode: {attach_auth_policy.get('auth_mode') or 'n/a'}")
    lines.append(f"- local_only: {attach_auth_policy.get('local_only')}")
    lines.append(f"- off_lan_allowed: {attach_auth_policy.get('off_lan_allowed')}")
    lines.append(f"- token_required: {attach_auth_policy.get('token_required')}")
    lines.append(f"- key_required: {attach_auth_policy.get('key_required')}")
    lines.append(
        f"- approval_boundary: {attach_auth_policy.get('approval_boundary') or 'n/a'}"
    )
    lines.append(
        "- attach_entrypoints: "
        + ", ".join(
            str(entry)
            for entry in list(attach_auth_policy.get("attach_entrypoints") or [])
            if str(entry)
        )
    )
    if isinstance(service_endpoint, dict):
        lines.append(
            "- service_health_signals: "
            + ", ".join(
                str(signal)
                for signal in list(service_endpoint.get("health_signals") or [])
                if str(signal)
            )
        )
    if isinstance(caller_authority, list):
        lines.append(
            "- caller_authority: "
            + ", ".join(
                str(policy.get("caller_id") or "")
                for policy in caller_authority
                if isinstance(policy, dict) and str(policy.get("caller_id") or "")
            )
        )
