//! Runtime style-pack resolver scaffold.
//!
//! This keeps current built-in theme behavior unchanged while introducing a
//! dedicated resolver surface for future Theme Studio packs.

use super::{
    runtime_overrides::{
        RuntimeBannerStyleOverride, RuntimeBorderStyleOverride, RuntimeGlyphSetOverride,
        RuntimeIndicatorSetOverride, RuntimeProgressBarFamilyOverride,
        RuntimeProgressStyleOverride, RuntimeStartupStyleOverride, RuntimeStylePackOverrides,
        RuntimeToastPositionOverride, RuntimeToastSeverityModeOverride,
        RuntimeVoiceSceneStyleOverride,
    },
    style_schema::{
        parse_style_schema, parse_style_schema_with_fallback, BannerStyleOverride,
        BorderStyleOverride, GlyphSetOverride, IndicatorSetOverride,
        ProgressBarFamily as SchemaProgressBarFamily, ProgressStyleOverride, StartupStyleOverride,
        StyleSchemaPack, ToastPositionOverride, ToastSeverityMode,
        VoiceSceneStyleOverride as SchemaVoiceSceneStyleOverride, CURRENT_STYLE_SCHEMA_VERSION,
    },
    BorderSet, GlyphSet, ProgressBarFamily, SpinnerStyle, Theme, ThemeColors, VoiceSceneStyle,
    BORDER_DOUBLE, BORDER_HEAVY, BORDER_NONE, BORDER_ROUNDED, BORDER_SINGLE, THEME_ANSI,
    THEME_CATPPUCCIN, THEME_CHATGPT, THEME_CLAUDE, THEME_CODEX, THEME_CORAL, THEME_DRACULA,
    THEME_GRUVBOX, THEME_NONE, THEME_NORD, THEME_TOKYONIGHT,
};
#[cfg(test)]
use std::cell::Cell;
#[cfg(not(test))]
use std::sync::{Mutex, OnceLock};
#[cfg(not(test))]
use voiceterm::log_debug;

pub(crate) const STYLE_PACK_RUNTIME_VERSION: u16 = CURRENT_STYLE_SCHEMA_VERSION;
const STYLE_PACK_SCHEMA_ENV: &str = "VOICETERM_STYLE_PACK_JSON";
#[cfg(test)]
const STYLE_PACK_TEST_ENV_OPT_IN: &str = "VOICETERM_TEST_ENABLE_STYLE_PACK_ENV";
#[cfg(not(test))]
static RUNTIME_STYLE_PACK_OVERRIDES: OnceLock<Mutex<RuntimeStylePackOverrides>> = OnceLock::new();
#[cfg(test)]
thread_local! {
    static RUNTIME_STYLE_PACK_OVERRIDES: Cell<RuntimeStylePackOverrides> = const {
        Cell::new(RuntimeStylePackOverrides {
            border_style_override: None,
            glyph_set_override: None,
            indicator_set_override: None,
            toast_position_override: None,
            startup_style_override: None,
            progress_style_override: None,
            toast_severity_mode_override: None,
            banner_style_override: None,
            progress_bar_family_override: None,
            voice_scene_style_override: None,
        })
    };
}

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
    pub(crate) banner_style: Option<BannerStyleOverride>,
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

#[cfg(not(test))]
fn runtime_style_pack_overrides_cell() -> &'static Mutex<RuntimeStylePackOverrides> {
    RUNTIME_STYLE_PACK_OVERRIDES.get_or_init(|| Mutex::new(RuntimeStylePackOverrides::default()))
}

#[must_use]
pub(crate) fn runtime_style_pack_overrides() -> RuntimeStylePackOverrides {
    #[cfg(test)]
    {
        return RUNTIME_STYLE_PACK_OVERRIDES.with(Cell::get);
    }
    #[cfg(not(test))]
    match runtime_style_pack_overrides_cell().lock() {
        Ok(guard) => *guard,
        Err(poisoned) => {
            log_debug("runtime style-pack overrides lock poisoned; recovering read");
            *poisoned.into_inner()
        }
    }
}

pub(crate) fn set_runtime_style_pack_overrides(overrides: RuntimeStylePackOverrides) {
    #[cfg(test)]
    {
        RUNTIME_STYLE_PACK_OVERRIDES.with(|slot| slot.set(overrides));
        return;
    }
    #[cfg(not(test))]
    match runtime_style_pack_overrides_cell().lock() {
        Ok(mut guard) => *guard = overrides,
        Err(poisoned) => {
            log_debug("runtime style-pack overrides lock poisoned; recovering write");
            let mut guard = poisoned.into_inner();
            *guard = overrides;
        }
    }
}

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

fn apply_runtime_style_pack_overrides(pack: &mut StylePack, overrides: RuntimeStylePackOverrides) {
    if let Some(border_override) = overrides.border_style_override {
        pack.border_style_override = Some(match border_override {
            RuntimeBorderStyleOverride::Single => BorderStyleOverride::Single,
            RuntimeBorderStyleOverride::Rounded => BorderStyleOverride::Rounded,
            RuntimeBorderStyleOverride::Double => BorderStyleOverride::Double,
            RuntimeBorderStyleOverride::Heavy => BorderStyleOverride::Heavy,
            RuntimeBorderStyleOverride::None => BorderStyleOverride::None,
        });
    }
    if let Some(glyph_override) = overrides.glyph_set_override {
        pack.glyph_set_override = Some(match glyph_override {
            RuntimeGlyphSetOverride::Unicode => GlyphSetOverride::Unicode,
            RuntimeGlyphSetOverride::Ascii => GlyphSetOverride::Ascii,
        });
    }
    if let Some(indicator_override) = overrides.indicator_set_override {
        pack.indicator_set_override = Some(match indicator_override {
            RuntimeIndicatorSetOverride::Ascii => IndicatorSetOverride::Ascii,
            RuntimeIndicatorSetOverride::Dot => IndicatorSetOverride::Dot,
            RuntimeIndicatorSetOverride::Diamond => IndicatorSetOverride::Diamond,
        });
    }
    if let Some(position_override) = overrides.toast_position_override {
        pack.surface_overrides.toast_position = Some(match position_override {
            RuntimeToastPositionOverride::TopRight => ToastPositionOverride::TopRight,
            RuntimeToastPositionOverride::BottomRight => ToastPositionOverride::BottomRight,
            RuntimeToastPositionOverride::TopCenter => ToastPositionOverride::TopCenter,
            RuntimeToastPositionOverride::BottomCenter => ToastPositionOverride::BottomCenter,
        });
    }
    if let Some(startup_override) = overrides.startup_style_override {
        pack.surface_overrides.startup_style = Some(match startup_override {
            RuntimeStartupStyleOverride::Full => StartupStyleOverride::Full,
            RuntimeStartupStyleOverride::Minimal => StartupStyleOverride::Minimal,
            RuntimeStartupStyleOverride::Hidden => StartupStyleOverride::Hidden,
        });
    }
    if let Some(progress_override) = overrides.progress_style_override {
        pack.surface_overrides.progress_style = Some(match progress_override {
            RuntimeProgressStyleOverride::Braille => ProgressStyleOverride::Braille,
            RuntimeProgressStyleOverride::Dots => ProgressStyleOverride::Dots,
            RuntimeProgressStyleOverride::Line => ProgressStyleOverride::Line,
            RuntimeProgressStyleOverride::Block => ProgressStyleOverride::Block,
        });
    }
    if let Some(toast_severity_override) = overrides.toast_severity_mode_override {
        pack.component_overrides.toast_severity_mode = Some(match toast_severity_override {
            RuntimeToastSeverityModeOverride::Icon => ToastSeverityMode::Icon,
            RuntimeToastSeverityModeOverride::Label => ToastSeverityMode::Label,
            RuntimeToastSeverityModeOverride::IconAndLabel => ToastSeverityMode::IconAndLabel,
        });
    }
    if let Some(banner_override) = overrides.banner_style_override {
        pack.component_overrides.banner_style = Some(match banner_override {
            RuntimeBannerStyleOverride::Full => BannerStyleOverride::Full,
            RuntimeBannerStyleOverride::Compact => BannerStyleOverride::Compact,
            RuntimeBannerStyleOverride::Minimal => BannerStyleOverride::Minimal,
            RuntimeBannerStyleOverride::Hidden => BannerStyleOverride::Hidden,
        });
    }
    if let Some(progress_bar_override) = overrides.progress_bar_family_override {
        pack.component_overrides.progress_bar_family = Some(match progress_bar_override {
            RuntimeProgressBarFamilyOverride::Bar => SchemaProgressBarFamily::Bar,
            RuntimeProgressBarFamilyOverride::Compact => SchemaProgressBarFamily::Compact,
            RuntimeProgressBarFamilyOverride::Blocks => SchemaProgressBarFamily::Blocks,
            RuntimeProgressBarFamilyOverride::Braille => SchemaProgressBarFamily::Braille,
        });
    }
    if let Some(scene_override) = overrides.voice_scene_style_override {
        pack.surface_overrides.voice_scene_style = Some(match scene_override {
            RuntimeVoiceSceneStyleOverride::Pulse => SchemaVoiceSceneStyleOverride::Pulse,
            RuntimeVoiceSceneStyleOverride::Static => SchemaVoiceSceneStyleOverride::Static,
            RuntimeVoiceSceneStyleOverride::Minimal => SchemaVoiceSceneStyleOverride::Minimal,
        });
    }
}

#[must_use]
fn resolve_border_set(base: BorderSet, override_value: Option<BorderStyleOverride>) -> BorderSet {
    match override_value {
        None | Some(BorderStyleOverride::Theme) => base,
        Some(BorderStyleOverride::Single) => BORDER_SINGLE,
        Some(BorderStyleOverride::Rounded) => BORDER_ROUNDED,
        Some(BorderStyleOverride::Double) => BORDER_DOUBLE,
        Some(BorderStyleOverride::Heavy) => BORDER_HEAVY,
        Some(BorderStyleOverride::None) => BORDER_NONE,
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
fn runtime_style_pack_payload() -> Option<String> {
    #[cfg(test)]
    if std::env::var_os(STYLE_PACK_TEST_ENV_OPT_IN).is_none() {
        // Keep unit tests deterministic even when a developer exported
        // VOICETERM_STYLE_PACK_JSON in their interactive shell.
        return None;
    }

    std::env::var(STYLE_PACK_SCHEMA_ENV)
        .ok()
        .filter(|payload| !payload.trim().is_empty())
}

fn apply_border_style_override(
    colors: &mut ThemeColors,
    override_value: Option<BorderStyleOverride>,
) {
    colors.borders = resolve_border_set(colors.borders, override_value);
}

fn apply_indicator_set_override(
    colors: &mut ThemeColors,
    override_value: Option<IndicatorSetOverride>,
) {
    let Some(override_value) = override_value else {
        return;
    };
    let (rec, auto, manual, idle, processing, responding) = match override_value {
        IndicatorSetOverride::Theme => (
            colors.indicator_rec,
            colors.indicator_auto,
            colors.indicator_manual,
            colors.indicator_idle,
            colors.indicator_processing,
            colors.indicator_responding,
        ),
        IndicatorSetOverride::Ascii => ("*", "@", ">", "-", "~", ">"),
        IndicatorSetOverride::Dot => ("●", "◎", "▶", "○", "◐", "↺"),
        IndicatorSetOverride::Diamond => ("◆", "◇", "▸", "·", "◈", "▸"),
    };
    colors.indicator_rec = rec;
    colors.indicator_auto = auto;
    colors.indicator_manual = manual;
    colors.indicator_idle = idle;
    colors.indicator_processing = processing;
    colors.indicator_responding = responding;
}

fn apply_glyph_set_override(colors: &mut ThemeColors, override_value: Option<GlyphSetOverride>) {
    let Some(override_value) = override_value else {
        return;
    };
    colors.glyph_set = match override_value {
        GlyphSetOverride::Theme => colors.glyph_set,
        GlyphSetOverride::Unicode => GlyphSet::Unicode,
        GlyphSetOverride::Ascii => GlyphSet::Ascii,
    };
}

fn apply_progress_style_override(
    colors: &mut ThemeColors,
    override_value: Option<ProgressStyleOverride>,
) {
    let Some(override_value) = override_value else {
        return;
    };
    colors.spinner_style = match override_value {
        ProgressStyleOverride::Theme => colors.spinner_style,
        ProgressStyleOverride::Braille => SpinnerStyle::Braille,
        ProgressStyleOverride::Dots => SpinnerStyle::Dots,
        ProgressStyleOverride::Line => SpinnerStyle::Line,
        ProgressStyleOverride::Block => SpinnerStyle::Block,
    };
}

fn apply_progress_bar_family_override(
    colors: &mut ThemeColors,
    override_value: Option<SchemaProgressBarFamily>,
) {
    let Some(override_value) = override_value else {
        return;
    };
    colors.progress_bar_family = match override_value {
        SchemaProgressBarFamily::Theme => colors.progress_bar_family,
        SchemaProgressBarFamily::Bar => ProgressBarFamily::Bar,
        SchemaProgressBarFamily::Compact => ProgressBarFamily::Compact,
        SchemaProgressBarFamily::Blocks => ProgressBarFamily::Blocks,
        SchemaProgressBarFamily::Braille => ProgressBarFamily::Braille,
    };
}

fn apply_voice_scene_style_override(
    colors: &mut ThemeColors,
    override_value: Option<SchemaVoiceSceneStyleOverride>,
) {
    let Some(override_value) = override_value else {
        return;
    };
    colors.voice_scene_style = match override_value {
        SchemaVoiceSceneStyleOverride::Theme => colors.voice_scene_style,
        SchemaVoiceSceneStyleOverride::Pulse => VoiceSceneStyle::Pulse,
        SchemaVoiceSceneStyleOverride::Static => VoiceSceneStyle::Static,
        SchemaVoiceSceneStyleOverride::Minimal => VoiceSceneStyle::Minimal,
    };
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

#[must_use]
pub(crate) fn resolve_theme_colors(theme: Theme) -> ThemeColors {
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

/// Return locked base theme when runtime style-pack payload is valid.
///
/// When present, Theme Studio payload owns the base palette and runtime theme
/// cycling should be treated as read-only until the payload is unset.
#[must_use]
pub(crate) fn locked_style_pack_theme() -> Option<Theme> {
    let payload = runtime_style_pack_payload();
    style_pack_theme_override_from_payload(payload.as_deref())
}

#[cfg(test)]
mod tests;
