"""Read-path import helpers for canonical VoiceTerm overlay theme metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    tomllib = None  # type: ignore[assignment]

try:  # Optional fallback package
    import tomli  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - tomli is optional
    tomli = None  # type: ignore[assignment]

from .colors import resolve_theme

_RUST_THEME_ALIASES = {
    "ansi": "ansi",
    "ansi16": "ansi",
    "anthropic": "claude",
    "basic": "ansi",
    "catppuccin": "catppuccin",
    "chat-gpt": "chatgpt",
    "chat_gpt": "chatgpt",
    "chatgpt": "chatgpt",
    "claude": "claude",
    "codex": "codex",
    "coral": "coral",
    "default": "coral",
    "dracula": "dracula",
    "gruv": "gruvbox",
    "gruvbox": "gruvbox",
    "gpt": "chatgpt",
    "none": "none",
    "nord": "nord",
    "openai": "chatgpt",
    "plain": "none",
    "tokyo": "tokyonight",
    "tokyo-night": "tokyonight",
    "tokyo_night": "tokyonight",
    "tokyonight": "tokyonight",
}


@dataclass(frozen=True)
class OverlayThemeImportResult:
    """Read-only overlay metadata import result for the desktop theme editor."""

    theme_id: str
    source_kind: str
    applied_fields: tuple[str, ...]
    ignored_fields: tuple[str, ...]
    provenance: tuple[tuple[str, str], ...]


def import_overlay_theme_text(
    text: str,
    *,
    source_name: str | None = None,
) -> OverlayThemeImportResult | None:
    """Parse canonical overlay metadata and return the mapped desktop base theme."""

    stripped = text.lstrip()
    if not stripped:
        return None
    if stripped.startswith("{"):
        return _import_style_pack_json(stripped, source_name=source_name)
    return _import_theme_file_toml(stripped, source_name=source_name)


def import_overlay_theme_file(path: str) -> OverlayThemeImportResult | None:
    """Load overlay metadata from a JSON or TOML file path."""

    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    return import_overlay_theme_text(text, source_name=Path(path).name)


def render_overlay_import_summary(result: OverlayThemeImportResult) -> str:
    """Render a compact operator-facing summary for the import page."""

    display_name = resolve_theme(result.theme_id).display_name
    parts = [f"Imported {result.source_kind} -> {display_name} base theme."]
    if result.provenance:
        details = ", ".join(f"{key}={value}" for key, value in result.provenance)
        parts.append(details)
    parts.append(f"Applied: {', '.join(result.applied_fields)}.")
    if result.ignored_fields:
        ignored = ", ".join(result.ignored_fields)
        parts.append(f"Not yet mapped: {ignored}.")
    else:
        parts.append("No additional Rust-only fields were present.")
    return " ".join(parts)


def _import_style_pack_json(
    text: str,
    *,
    source_name: str | None,
) -> OverlayThemeImportResult | None:
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None

    theme_key = "base_theme" if "base_theme" in payload else "theme"
    theme_id = _normalize_theme_id(payload.get(theme_key))
    if theme_id is None:
        return None

    ignored = _flatten_ignored_fields(
        payload,
        sections=("overrides", "surfaces", "components"),
    )
    provenance = _build_provenance(
        source_name=source_name,
        version=payload.get("version"),
        profile=payload.get("profile"),
    )
    return OverlayThemeImportResult(
        theme_id=theme_id,
        source_kind="style-pack-json",
        applied_fields=(theme_key,),
        ignored_fields=ignored,
        provenance=provenance,
    )


def _import_theme_file_toml(
    text: str,
    *,
    source_name: str | None,
) -> OverlayThemeImportResult | None:
    payload = _load_toml_mapping(text)
    if not isinstance(payload, dict):
        return None

    meta = payload.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    theme_id = _normalize_theme_id(meta.get("base_theme", "codex"))
    if theme_id is None:
        return None

    ignored = tuple(
        sorted(section for section in payload if section != "meta")
    )
    provenance = _build_provenance(
        source_name=source_name,
        version=meta.get("version"),
        profile=meta.get("name"),
    )
    return OverlayThemeImportResult(
        theme_id=theme_id,
        source_kind="theme-file-toml",
        applied_fields=("meta.base_theme",),
        ignored_fields=ignored,
        provenance=provenance,
    )


def _normalize_theme_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace(" ", "-")
    if not normalized:
        return None
    return _RUST_THEME_ALIASES.get(normalized)


def _flatten_ignored_fields(
    payload: dict[str, Any],
    *,
    sections: tuple[str, ...],
) -> tuple[str, ...]:
    ignored: list[str] = []
    for section_name in sections:
        section = payload.get(section_name)
        if isinstance(section, dict):
            ignored.extend(
                f"{section_name}.{key}" for key in sorted(section) if isinstance(key, str)
            )
        elif section is not None:
            ignored.append(section_name)
    return tuple(ignored)


def _build_provenance(
    *,
    source_name: str | None,
    version: object,
    profile: object,
) -> tuple[tuple[str, str], ...]:
    items: list[tuple[str, str]] = []
    if source_name:
        items.append(("source", source_name))
    if version is not None:
        items.append(("version", str(version)))
    if isinstance(profile, str) and profile.strip():
        items.append(("profile", profile.strip()))
    return tuple(items)


def _load_toml_mapping(text: str) -> dict[str, Any] | None:
    if tomllib is not None:
        try:
            parsed = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    if tomli is not None:
        try:
            parsed = tomli.loads(text)
        except tomli.TOMLDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    return _parse_simple_toml(text)


def _parse_simple_toml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current: dict[str, Any] = root
    for raw_line in text.splitlines():
        line = _strip_inline_comment(raw_line).strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = _toml_section(root, line[1:-1].strip())
            continue
        key, separator, value = line.partition("=")
        if separator != "=":
            continue
        current[key.strip()] = _parse_toml_scalar(value.strip())
    return root


def _toml_section(root: dict[str, Any], section_path: str) -> dict[str, Any]:
    current = root
    for part in section_path.split("."):
        name = part.strip()
        if not name:
            continue
        child = current.get(name)
        if not isinstance(child, dict):
            child = {}
            current[name] = child
        current = child
    return current


def _parse_toml_scalar(value: str) -> object:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    if value.isdigit():
        return int(value)
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def _strip_inline_comment(line: str) -> str:
    in_quote = False
    quote_char = ""
    for index, char in enumerate(line):
        if char in {'"', "'"}:
            if not in_quote:
                in_quote = True
                quote_char = char
            elif quote_char == char:
                in_quote = False
                quote_char = ""
        elif char == "#" and not in_quote:
            return line[:index]
    return line
