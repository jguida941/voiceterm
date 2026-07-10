//! Runtime style-pack resolver scaffold.
//!
//! This keeps current built-in theme behavior unchanged while introducing a
//! dedicated resolver surface for future Theme Studio packs.

mod apply;
mod state;
#[cfg(test)]
mod tests;

use super::{
    style_schema::{
        parse_style_schema, parse_style_schema_with_fallback, BorderStyleOverride,
        GlyphSetOverride, IndicatorSetOverride, StyleSchemaPack, CURRENT_STYLE_SCHEMA_VERSION,
    },
    BorderSet, Theme, ThemeColors, THEME_ANSI, THEME_CATPPUCCIN, THEME_CHATGPT, THEME_CLAUDE,
    THEME_CODEX, THEME_CORAL, THEME_DRACULA, THEME_GRUVBOX, THEME_NONE, THEME_NORD,
    THEME_TOKYONIGHT,
};
#[cfg(not(test))]
use voiceterm::log_debug;

use apply::{
    apply_border_style_override, apply_glyph_set_override, apply_indicator_set_override,
    apply_progress_bar_family_override, apply_progress_style_override,
    apply_runtime_style_pack_overrides, apply_voice_scene_style_override, resolve_border_set,
};
#[cfg(not(test))]
use state::runtime_color_override;
#[cfg(test)]
pub(crate) use state::RUNTIME_THEME_FILE_OVERRIDE_TEST;
#[cfg(not(test))]
pub(crate) use state::{clear_runtime_color_override, set_runtime_color_override};
pub(crate) use state::{
    runtime_style_pack_overrides, set_runtime_style_pack_overrides, set_runtime_theme_file_override,
};
use state::{runtime_style_pack_payload, runtime_theme_file_override};
#[cfg(test)]
pub(crate) use state::{STYLE_PACK_SCHEMA_ENV, STYLE_PACK_TEST_ENV_OPT_IN};

use super::style_schema::{
    ProgressBarFamily as SchemaProgressBarFamily, ProgressStyleOverride, StartupStyleOverride,
    ToastPositionOverride, ToastSeverityMode,
    VoiceSceneStyleOverride as SchemaVoiceSceneStyleOverride,
};

pub(crate) const STYLE_PACK_RUNTIME_VERSION: u16 = CURRENT_STYLE_SCHEMA_VERSION;

// ---------------------------------------------------------------------------
// Type definitions
// ---------------------------------------------------------------------------

/// Resolved surface-level style overrides exposed to runtime rendering.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub(crate) struct ResolvedSurfaceOverrides {
    pub(crate) toast_position: Option<ToastPositionOverride>,
    pub(crate) startup_style: Option<StartupStyleOverride>,
    pub(crate) progress_style: Option<ProgressStyleOverride>,
    pub(crate) voice_scene_style: Option<SchemaVoiceSceneStyleOverride>,
}

/// Resolved component-level style overrides exposed to runtime rendering.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub(crate) struct ResolvedComponentOverrides {
    pub(crate) overlay_border: Option<BorderStyleOverride>,
    pub(crate) hud_border: Option<BorderStyleOverride>,
    pub(crate) toast_severity_mode: Option<ToastSeverityMode>,
    pub(crate) banner_style: Option<super::style_schema::BannerStyleOverride>,
    pub(crate) progress_bar_family: Option<SchemaProgressBarFamily>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct StylePack {
    pub(crate) schema_version: u16,
    pub(crate) base_theme: Theme,
    pub(crate) border_style_override: Option<BorderStyleOverride>,
    pub(crate) indicator_set_override: Option<IndicatorSetOverride>,
    pub(crate) glyph_set_override: Option<GlyphSetOverride>,
    pub(crate) surface_overrides: ResolvedSurfaceOverrides,
    pub(crate) component_overrides: ResolvedComponentOverrides,
}

impl StylePack {
    #[must_use]
    pub(crate) fn built_in(theme: Theme) -> Self {
        Self {
            schema_version: STYLE_PACK_RUNTIME_VERSION,
            base_theme: theme,
            border_style_override: None,
            indicator_set_override: None,
            glyph_set_override: None,
            surface_overrides: ResolvedSurfaceOverrides::default(),
            component_overrides: ResolvedComponentOverrides::default(),
        }
    }

    #[must_use]
    fn from_schema_pack(pack: StyleSchemaPack) -> Self {
        let StyleSchemaPack {
            version,
            profile: _profile,
            base_theme,
            border_style_override,
            indicator_set_override,
            glyph_set_override,
            surface_overrides,
            component_overrides,
        } = pack;
        Self {
            schema_version: version,
            base_theme,
            border_style_override,
            indicator_set_override,
            glyph_set_override,
            surface_overrides: ResolvedSurfaceOverrides {
                toast_position: surface_overrides.toast_position,
                startup_style: surface_overrides.startup_style,
                progress_style: surface_overrides.progress_style,
                voice_scene_style: surface_overrides.voice_scene_style,
            },
            component_overrides: ResolvedComponentOverrides {
                overlay_border: component_overrides.overlay_border,
                hud_border: component_overrides.hud_border,
                toast_severity_mode: component_overrides.toast_severity_mode,
                banner_style: component_overrides.banner_style,
                progress_bar_family: component_overrides.progress_bar_family,
            },
        }
    }

    #[cfg(test)]
    #[must_use]
    pub(crate) fn with_schema_version(theme: Theme, schema_version: u16) -> Self {
        Self {
            schema_version,
            base_theme: theme,
            border_style_override: None,
            indicator_set_override: None,
            glyph_set_override: None,
            surface_overrides: ResolvedSurfaceOverrides::default(),
            component_overrides: ResolvedComponentOverrides::default(),
        }
    }
}

// ---------------------------------------------------------------------------
// Theme resolution
// ---------------------------------------------------------------------------

#[must_use]
fn base_theme_colors(theme: Theme) -> ThemeColors {
    match theme {
        Theme::Coral => THEME_CORAL,
        Theme::Claude => THEME_CLAUDE,
        Theme::Codex => THEME_CODEX,
        Theme::ChatGpt => THEME_CHATGPT,
        Theme::Catppuccin => THEME_CATPPUCCIN,
        Theme::Dracula => THEME_DRACULA,
        Theme::Nord => THEME_NORD,
        Theme::TokyoNight => THEME_TOKYONIGHT,
        Theme::Gruvbox => THEME_GRUVBOX,
        Theme::Ansi => THEME_ANSI,
        Theme::None => THEME_NONE,
    }
}

#[must_use]
pub(crate) fn resolve_style_pack_colors(pack: StylePack) -> ThemeColors {
    if pack.schema_version != STYLE_PACK_RUNTIME_VERSION {
        // Preserve current startup/theme behavior when a newer schema is seen.
        return base_theme_colors(pack.base_theme);
    }

    let mut colors = base_theme_colors(pack.base_theme);
    apply_border_style_override(&mut colors, pack.border_style_override);
    apply_indicator_set_override(&mut colors, pack.indicator_set_override);
    apply_glyph_set_override(&mut colors, pack.glyph_set_override);
    apply_progress_style_override(&mut colors, pack.surface_overrides.progress_style);
    apply_voice_scene_style_override(&mut colors, pack.surface_overrides.voice_scene_style);
    apply_progress_bar_family_override(&mut colors, pack.component_overrides.progress_bar_family);
    colors
}

#[must_use]
fn style_pack_from_json_payload(theme: Theme, payload: Option<&str>) -> StylePack {
    let Some(payload) = payload else {
        return StylePack::built_in(theme);
    };
    let fallback = StyleSchemaPack::fallback(theme);
    let parsed = parse_style_schema_with_fallback(payload, fallback);
    StylePack::from_schema_pack(parsed)
}

#[must_use]
fn style_pack_theme_override_from_payload(payload: Option<&str>) -> Option<Theme> {
    let payload = payload?;
    let parsed = parse_style_schema(payload).ok()?;
    Some(parsed.base_theme)
}

#[cfg(test)]
#[must_use]
fn resolve_theme_colors_with_payload(theme: Theme, payload: Option<&str>) -> ThemeColors {
    resolve_style_pack_colors(style_pack_from_json_payload(theme, payload))
}

#[cfg(test)]
#[must_use]
fn resolved_overlay_border_set_with_payload(theme: Theme, payload: Option<&str>) -> BorderSet {
    let mut pack = style_pack_from_json_payload(theme, payload);
    apply_runtime_style_pack_overrides(&mut pack, runtime_style_pack_overrides());
    resolve_component_border_set(pack, pack.component_overrides.overlay_border)
}

#[cfg(test)]
#[must_use]
fn resolved_hud_border_set_with_payload(theme: Theme, payload: Option<&str>) -> BorderSet {
    let mut pack = style_pack_from_json_payload(theme, payload);
    apply_runtime_style_pack_overrides(&mut pack, runtime_style_pack_overrides());
    resolve_component_border_set(pack, pack.component_overrides.hud_border)
}

#[must_use]
fn resolved_style_pack(theme: Theme) -> StylePack {
    let payload = runtime_style_pack_payload();
    let mut pack = style_pack_from_json_payload(theme, payload.as_deref());
    apply_runtime_style_pack_overrides(&mut pack, runtime_style_pack_overrides());
    pack
}

#[must_use]
fn resolve_component_border_set(
    pack: StylePack,
    override_value: Option<BorderStyleOverride>,
) -> BorderSet {
    let base_borders = resolve_style_pack_colors(pack).borders;
    resolve_border_set(base_borders, override_value)
}

/// Try loading a TOML theme file from runtime override or `VOICETERM_THEME_FILE`.
///
/// Returns `None` if the env var is unset, empty, or the file fails to load.
/// On failure, falls through silently to the built-in theme.
#[must_use]
fn toml_theme_file_colors() -> Option<ThemeColors> {
    #[cfg(test)]
    {
        use state::STYLE_PACK_TEST_ENV_OPT_IN;
        std::env::var_os(STYLE_PACK_TEST_ENV_OPT_IN)?;
    }

    let path =
        runtime_theme_file_override().or_else(|| std::env::var("VOICETERM_THEME_FILE").ok())?;
    let path = path.trim();
    if path.is_empty() {
        return None;
    }

    if !path.contains('/')
        && !path.contains('\\')
        && !path.ends_with(".toml")
        && !path.ends_with(".TOML")
    {
        match super::theme_dir::load_user_theme(path) {
            Ok(resolved) => return Some(resolved.to_legacy_theme_colors()),
            Err(load_err) => {
                #[cfg(not(test))]
                {
                    let available = super::theme_dir::list_theme_files();
                    if available.is_empty() {
                        log_debug(&format!(
                            "theme file {path}: named user theme not found ({load_err}); no user themes currently in ~/.config/voiceterm/themes/"
                        ));
                    } else {
                        let names: Vec<String> = available
                            .iter()
                            .filter_map(|file_path| {
                                file_path
                                    .file_stem()
                                    .map(|stem| stem.to_string_lossy().to_string())
                            })
                            .collect();
                        log_debug(&format!(
                            "theme file {path}: named user theme not found ({load_err}); available user themes: {}",
                            names.join(", ")
                        ));
                    }
                }
                #[cfg(test)]
                {
                    let _ = load_err;
                }
            }
        }
    }

    let file = super::theme_file::load_theme_file(std::path::Path::new(path)).ok()?;
    #[cfg(not(test))]
    for warning in super::theme_file::validate_theme_file(&file) {
        match warning {
            super::theme_file::ThemeFileWarning::UnusedPaletteEntry(key) => {
                log_debug(&format!(
                    "theme file {path}: unused palette entry (safe to remove): {key}"
                ));
            }
        }
    }
    let resolved = super::theme_file::resolve_theme_file(&file).ok()?;
    Some(resolved.to_legacy_theme_colors())
}

#[must_use]
pub(crate) fn resolve_theme_colors(theme: Theme) -> ThemeColors {
    // Precedence:
    // 0. Runtime color override from Theme Studio (highest)
    // 1. VOICETERM_STYLE_PACK_JSON
    // 2. Runtime theme-file override (CLI `--theme-file`) / VOICETERM_THEME_FILE
    // 3. Built-in themes (fallback)
    #[cfg(not(test))]
    if let Some(colors) = runtime_color_override() {
        return colors;
    }

    let payload = runtime_style_pack_payload();
    if payload.is_some() {
        return resolve_style_pack_colors(resolved_style_pack(theme));
    }

    if let Some(toml_colors) = toml_theme_file_colors() {
        return toml_colors;
    }

    resolve_style_pack_colors(resolved_style_pack(theme))
}

/// Resolve overlay-border glyphs through style-pack payload/runtime overrides.
#[must_use]
pub(crate) fn resolved_overlay_border_set(theme: Theme) -> BorderSet {
    let pack = resolved_style_pack(theme);
    resolve_component_border_set(pack, pack.component_overrides.overlay_border)
}

/// Resolve HUD-border glyphs through style-pack payload/runtime overrides.
#[must_use]
pub(crate) fn resolved_hud_border_set(theme: Theme) -> BorderSet {
    let pack = resolved_style_pack(theme);
    resolve_component_border_set(pack, pack.component_overrides.hud_border)
}

/// Resolve toast position from persisted payload + runtime overrides.
///
/// Returns `None` when neither the persisted pack nor the runtime override sets
/// an explicit position, meaning the default rendering path applies.
#[must_use]
pub(crate) fn resolved_toast_position(theme: Theme) -> Option<ToastPositionOverride> {
    resolved_style_pack(theme).surface_overrides.toast_position
}

/// Resolve startup style from persisted payload + runtime overrides.
#[must_use]
pub(crate) fn resolved_startup_style(theme: Theme) -> Option<StartupStyleOverride> {
    resolved_style_pack(theme).surface_overrides.startup_style
}

/// Resolve toast severity display mode from persisted payload + runtime overrides.
#[must_use]
pub(crate) fn resolved_toast_severity_mode(theme: Theme) -> Option<ToastSeverityMode> {
    resolved_style_pack(theme)
        .component_overrides
        .toast_severity_mode
}

/// Resolve banner style from persisted payload + runtime overrides.
#[must_use]
pub(crate) fn resolved_banner_style(
    theme: Theme,
) -> Option<super::style_schema::BannerStyleOverride> {
    resolved_style_pack(theme).component_overrides.banner_style
}

/// Return locked base theme when runtime style-pack payload is valid.
///
/// When present, Theme Studio payload owns the base palette and runtime theme
/// cycling should be treated as read-only until the payload is unset.
#[must_use]
pub(crate) fn locked_style_pack_theme() -> Option<Theme> {
    let payload = runtime_style_pack_payload();
    style_pack_theme_override_from_payload(payload.as_deref())
}
