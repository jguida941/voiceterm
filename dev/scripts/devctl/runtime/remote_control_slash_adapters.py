"""Provider-neutral slash adapter catalog for remote-control lifecycle."""

from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_REMOTE_CONTROL_PROVIDERS = ("claude",)


@dataclass(frozen=True, slots=True)
class RemoteControlSlashAdapterSpec:
    provider_id: str
    slash_command: str
    backend_command: str
    compatibility_alias: bool = False


def build_remote_control_slash_adapter_catalog(
    *,
    providers: tuple[str, ...] = SUPPORTED_REMOTE_CONTROL_PROVIDERS,
) -> tuple[RemoteControlSlashAdapterSpec, ...]:
    rows: list[RemoteControlSlashAdapterSpec] = []
    for provider in providers:
        # The only project-facing recovery slash. Claude's unqualified
        # `/remote-control` and `/rc` remain provider-owned built-ins.
        rows.append(
            RemoteControlSlashAdapterSpec(
                provider_id=provider,
                slash_command="/project:typed-remote-control",
                backend_command=(
                    "python3 dev/scripts/devctl.py remote-control enter "
                    f"--provider {provider} "
                    "--entrypoint /project:typed-remote-control"
                ),
            )
        )
    return tuple(rows)


def render_remote_control_slash_adapter_catalog_markdown() -> str:
    lines = [
        "# Remote-Control Slash Adapter Catalog",
        "",
        "Provider slash files are thin adapters over `devctl remote-control`.",
        "They do not own lifecycle policy, role maps, launch authority, or approval rules.",
        "",
        "| Provider | Slash command | Backend command | Alias |",
        "|---|---|---|---|",
    ]
    for row in build_remote_control_slash_adapter_catalog():
        lines.append(
            "| {provider} | `{slash}` | `{backend}` | {alias} |".format(
                provider=row.provider_id,
                slash=row.slash_command,
                backend=row.backend_command,
                alias="yes" if row.compatibility_alias else "no",
            )
        )
    return "\n".join(lines) + "\n"


__all__ = [
    "RemoteControlSlashAdapterSpec",
    "build_remote_control_slash_adapter_catalog",
    "render_remote_control_slash_adapter_catalog_markdown",
]
