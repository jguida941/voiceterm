"""Provider selection helpers for collaboration profiles."""

from __future__ import annotations

from collections.abc import Sequence

from .provider_registry import is_valid_provider_id, normalize_provider_id


def providers(
    *,
    requested: Sequence[object],
    role_bindings: tuple[object, ...],
    agent_mind_providers: Sequence[object],
    remote_provider: object,
    default_profile_providers: tuple[str, ...],
) -> tuple[str, ...]:
    provider_ids: list[str] = []
    for value in requested:
        append_provider(provider_ids, value)
    for binding in role_bindings:
        append_provider(provider_ids, getattr(binding, "provider", ""))
    for value in agent_mind_providers:
        append_provider(provider_ids, value)
    append_provider(provider_ids, remote_provider)
    if not provider_ids:
        provider_ids.extend(default_profile_providers)
    return tuple(provider_ids)


def agent_mind_providers(
    *,
    requested: Sequence[object],
    providers: tuple[str, ...],
    default_profile_providers: tuple[str, ...],
) -> tuple[str, ...]:
    values: list[str] = []
    for value in requested:
        append_provider(values, value)
    if not values:
        values.extend(provider for provider in providers if provider in default_profile_providers)
    return tuple(values)


def provider_errors(
    providers: tuple[str, ...],
    *,
    label: str = "provider",
) -> tuple[str, ...]:
    return tuple(
        f"{label} `{provider}` is not a valid provider id"
        for provider in providers
        if not is_valid_provider_id(provider)
    )


def validation_warnings(
    *,
    selected_mode_id: str,
    selected_role_preset_id: str,
    role_bindings: tuple[object, ...],
    agent_mind_providers: tuple[str, ...],
) -> tuple[str, ...]:
    warnings: list[str] = []
    if not role_bindings and selected_mode_id != "solo":
        warnings.append("multi-actor mode requested without explicit role bindings")
    if "implementer" in {item.role for item in role_bindings} and "reviewer" in {
        item.role for item in role_bindings
    }:
        implementers = {item.provider for item in role_bindings if item.role == "implementer"}
        reviewers = {item.provider for item in role_bindings if item.role == "reviewer"}
        if implementers & reviewers:
            warnings.append("implementer and reviewer share a provider; self-review is still blocked by authority gates")
    if selected_role_preset_id not in {item.role for item in role_bindings} and role_bindings:
        warnings.append("selected role preset is not explicitly bound in the profile")
    if not agent_mind_providers:
        warnings.append("no agent-mind providers selected; peer polling commands will be omitted")
    return tuple(warnings)


def append_provider(providers: list[str], value: object) -> None:
    provider = normalize_provider_id(value)
    if provider and provider not in providers:
        providers.append(provider)
