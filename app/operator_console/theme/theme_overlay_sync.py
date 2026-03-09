"""Shared overlay import/export contract for desktop theme parity."""

from __future__ import annotations

from dataclasses import dataclass

from .overlay_export import (
    OverlayThemeExportPayload,
    build_overlay_style_pack_export,
    build_overlay_theme_file_export,
)
from .overlay_import import (
    OverlayThemeImportResult,
    import_overlay_theme_file,
    import_overlay_theme_text,
    render_overlay_import_summary,
)
from .theme_state import BUILTIN_PRESETS_BY_ID, ThemeState, _match_exact_builtin_theme_id


@dataclass(frozen=True)
class AppliedOverlayImport:
    """Parsed overlay metadata plus the builtin desktop state it maps onto."""

    state: ThemeState
    summary: str


def import_overlay_state_text(
    text: str,
    *,
    source_name: str | None = None,
) -> AppliedOverlayImport | None:
    imported = import_overlay_theme_text(text, source_name=source_name)
    return _applied_overlay_import(imported)


def import_overlay_state_file(path: str) -> AppliedOverlayImport | None:
    imported = import_overlay_theme_file(path)
    return _applied_overlay_import(imported)


def overlay_export_status(state: ThemeState) -> str:
    theme_id = _resolve_overlay_export_theme_id(state)
    if theme_id is None:
        return (
            "Canonical overlay export unavailable: the current desktop theme "
            "includes custom colors or tokens that do not round-trip to shared "
            "VoiceTerm overlay fields yet."
        )
    if state.theme_id == theme_id:
        return (
            f"Ready to export canonical overlay metadata for {state.name}. "
            "Only the shared base_theme contract is written today."
        )
    return (
        f"Ready to export canonical overlay metadata for {state.name} "
        f"using base_theme={theme_id}. Only the shared base_theme contract "
        "is written today."
    )


def overlay_theme_file_preview(state: ThemeState) -> str:
    payload = _overlay_theme_file_export_payload(state)
    if payload is None:
        return (
            "# Canonical overlay export unavailable.\n"
            "# Current desktop-only edits do not map cleanly onto shared\n"
            "# VoiceTerm overlay fields yet.\n"
        )
    return payload.content


def export_overlay_theme_file(state: ThemeState) -> str | None:
    payload = _overlay_theme_file_export_payload(state)
    if payload is None:
        return None
    return payload.content


def export_overlay_style_pack_json(state: ThemeState) -> str | None:
    payload = _overlay_style_pack_export_payload(state)
    if payload is None:
        return None
    return payload.content


def suggested_overlay_theme_file_name(state: ThemeState) -> str:
    payload = _overlay_theme_file_export_payload(state)
    return payload.filename if payload is not None else "voiceterm-theme.toml"


def suggested_overlay_style_pack_file_name(state: ThemeState) -> str:
    payload = _overlay_style_pack_export_payload(state)
    return payload.filename if payload is not None else "style-pack.json"


def _applied_overlay_import(
    imported: OverlayThemeImportResult | None,
) -> AppliedOverlayImport | None:
    if imported is None:
        return None
    preset = BUILTIN_PRESETS_BY_ID.get(imported.theme_id)
    if preset is None:
        return None
    return AppliedOverlayImport(
        state=preset.copy(),
        summary=render_overlay_import_summary(imported),
    )


def _resolve_overlay_export_theme_id(state: ThemeState) -> str | None:
    if state.theme_id in BUILTIN_PRESETS_BY_ID:
        return state.theme_id
    return _match_exact_builtin_theme_id(
        colors=state.colors,
        tokens=state.tokens,
    )


def _overlay_theme_file_export_payload(
    state: ThemeState,
) -> OverlayThemeExportPayload | None:
    theme_id = _resolve_overlay_export_theme_id(state)
    if theme_id is None:
        return None
    return build_overlay_theme_file_export(theme_id, name=state.name)


def _overlay_style_pack_export_payload(
    state: ThemeState,
) -> OverlayThemeExportPayload | None:
    theme_id = _resolve_overlay_export_theme_id(state)
    if theme_id is None:
        return None
    return build_overlay_style_pack_export(theme_id, profile=state.name)
