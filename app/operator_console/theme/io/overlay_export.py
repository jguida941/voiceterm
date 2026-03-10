"""Write-path helpers for canonical VoiceTerm overlay theme metadata."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ..colors import resolve_theme

THEME_FILE_VERSION = 1
STYLE_PACK_SCHEMA_VERSION = 4


@dataclass(frozen=True)
class OverlayThemeExportPayload:
    """Canonical overlay export artifact produced by the desktop editor."""

    kind: str
    filename: str
    content: str


def build_overlay_theme_file_export(
    theme_id: str,
    *,
    name: str | None = None,
) -> OverlayThemeExportPayload:
    """Render a minimal canonical TOML theme file for a shared base theme."""

    display_name = resolve_theme(theme_id).display_name
    rendered_name = _clean_name(name) or display_name
    escaped_name = _escape_toml_string(rendered_name)
    content = (
        "[meta]\n"
        f'name = "{escaped_name}"\n'
        f"version = {THEME_FILE_VERSION}\n"
        f'base_theme = "{theme_id}"\n'
    )
    return OverlayThemeExportPayload(
        kind="theme-file-toml",
        filename=f"voiceterm-{_slugify(rendered_name) or theme_id}.toml",
        content=content,
    )


def build_overlay_style_pack_export(
    theme_id: str,
    *,
    profile: str | None = None,
) -> OverlayThemeExportPayload:
    """Render a minimal canonical style-pack JSON payload for a base theme."""

    display_name = resolve_theme(theme_id).display_name
    profile_name = _slugify(profile or display_name) or theme_id
    content = json.dumps(
        {
            "version": STYLE_PACK_SCHEMA_VERSION,
            "profile": profile_name,
            "base_theme": theme_id,
        },
        indent=2,
    )
    return OverlayThemeExportPayload(
        kind="style-pack-json",
        filename=f"style-pack-{profile_name}.json",
        content=content,
    )


def _clean_name(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def _escape_toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    if not lowered:
        return ""
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-")
