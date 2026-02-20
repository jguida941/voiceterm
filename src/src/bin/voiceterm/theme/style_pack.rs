//! Runtime style-pack resolver scaffold.
//!
//! This keeps current built-in theme behavior unchanged while introducing a
//! dedicated resolver surface for future Theme Studio packs.

use super::{
    style_schema::{
        parse_style_schema, parse_style_schema_with_fallback, BannerStyleOverride,
        BorderStyleOverride, GlyphSetOverride, IndicatorSetOverride,
        ProgressBarFamily as SchemaProgressBarFamily, ProgressStyleOverride, StartupStyleOverride,
        StyleSchemaPack, ToastPositionOverride, ToastSeverityMode,
        VoiceSceneStyleOverride as SchemaVoiceSceneStyleOverride, CURRENT_STYLE_SCHEMA_VERSION,
    },
    GlyphSet, ProgressBarFamily, SpinnerStyle, Theme, ThemeColors, VoiceSceneStyle, BORDER_DOUBLE,
    BORDER_HEAVY, BORDER_NONE, BORDER_ROUNDED, BORDER_SINGLE, THEME_ANSI, THEME_CATPPUCCIN,
    THEME_CHATGPT, THEME_CLAUDE, THEME_CODEX, THEME_CORAL, THEME_DRACULA, THEME_GRUVBOX,
    THEME_NONE, THEME_NORD, THEME_TOKYONIGHT,
};
#[cfg(test)]
use std::cell::Cell;
#[cfg(not(test))]
use std::sync::{Mutex, OnceLock};

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
            progress_style_override: None,
            progress_bar_family_override: None,
            voice_scene_style_override: None,
        })
    };
}

/// Runtime glyph-profile override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeGlyphSetOverride {
    Unicode,
    Ascii,
}

/// Runtime indicator-profile override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeIndicatorSetOverride {
    Ascii,
    Dot,
    Diamond,
}

/// Runtime progress-spinner override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeProgressStyleOverride {
    Braille,
    Dots,
    Line,
    Block,
}

/// Runtime progress-bar-family override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeProgressBarFamilyOverride {
    Bar,
    Compact,
    Blocks,
    Braille,
}

/// Runtime voice-scene override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeVoiceSceneStyleOverride {
    Pulse,
    Static,
    Minimal,
}

/// Runtime border-style override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeBorderStyleOverride {
    Single,
    Rounded,
    Double,
    Heavy,
    None,
}

/// Runtime Theme Studio overrides applied after style-pack payload resolution.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub(crate) struct RuntimeStylePackOverrides {
    pub(crate) border_style_override: Option<RuntimeBorderStyleOverride>,
    pub(crate) glyph_set_override: Option<RuntimeGlyphSetOverride>,
    pub(crate) indicator_set_override: Option<RuntimeIndicatorSetOverride>,
    pub(crate) progress_style_override: Option<RuntimeProgressStyleOverride>,
    pub(crate) progress_bar_family_override: Option<RuntimeProgressBarFamilyOverride>,
    pub(crate) voice_scene_style_override: Option<RuntimeVoiceSceneStyleOverride>,
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
        Err(poisoned) => *poisoned.into_inner(),
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
    if let Some(progress_override) = overrides.progress_style_override {
        pack.surface_overrides.progress_style = Some(match progress_override {
            RuntimeProgressStyleOverride::Braille => ProgressStyleOverride::Braille,
            RuntimeProgressStyleOverride::Dots => ProgressStyleOverride::Dots,
            RuntimeProgressStyleOverride::Line => ProgressStyleOverride::Line,
            RuntimeProgressStyleOverride::Block => ProgressStyleOverride::Block,
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
    let Some(override_value) = override_value else {
        return;
    };
    colors.borders = match override_value {
        BorderStyleOverride::Theme => colors.borders,
        BorderStyleOverride::Single => BORDER_SINGLE,
        BorderStyleOverride::Rounded => BORDER_ROUNDED,
        BorderStyleOverride::Double => BORDER_DOUBLE,
        BorderStyleOverride::Heavy => BORDER_HEAVY,
        BorderStyleOverride::None => BORDER_NONE,
    };
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
pub(crate) fn resolve_theme_colors(theme: Theme) -> ThemeColors {
    let payload = runtime_style_pack_payload();
    let mut pack = style_pack_from_json_payload(theme, payload.as_deref());
    apply_runtime_style_pack_overrides(&mut pack, runtime_style_pack_overrides());
    resolve_style_pack_colors(pack)
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
mod tests {
    use super::*;
    use std::sync::{Mutex, OnceLock};

    static ENV_GUARD: OnceLock<Mutex<()>> = OnceLock::new();

    struct RuntimeOverridesGuard {
        previous: RuntimeStylePackOverrides,
    }

    impl Drop for RuntimeOverridesGuard {
        fn drop(&mut self) {
            set_runtime_style_pack_overrides(self.previous);
        }
    }

    fn install_runtime_overrides(overrides: RuntimeStylePackOverrides) -> RuntimeOverridesGuard {
        let previous = runtime_style_pack_overrides();
        set_runtime_style_pack_overrides(overrides);
        RuntimeOverridesGuard { previous }
    }

    #[test]
    fn style_pack_built_in_uses_current_schema_version() {
        let pack = StylePack::built_in(Theme::Codex);
        assert_eq!(pack.schema_version, STYLE_PACK_RUNTIME_VERSION);
        assert_eq!(pack.base_theme, Theme::Codex);
        assert_eq!(pack.border_style_override, None);
        assert_eq!(pack.indicator_set_override, None);
        assert_eq!(pack.glyph_set_override, None);
    }

    #[test]
    fn resolve_theme_colors_matches_legacy_palette_map() {
        let themes = [
            Theme::Coral,
            Theme::Claude,
            Theme::Codex,
            Theme::ChatGpt,
            Theme::Catppuccin,
            Theme::Dracula,
            Theme::Nord,
            Theme::TokyoNight,
            Theme::Gruvbox,
            Theme::Ansi,
            Theme::None,
        ];

        for theme in themes {
            assert_eq!(
                resolve_theme_colors_with_payload(theme, None),
                base_theme_colors(theme)
            );
        }
    }

    #[test]
    fn resolve_theme_colors_with_payload_uses_schema_base_theme() {
        let payload = r#"{"version":3,"profile":"ops","base_theme":"dracula"}"#;
        assert_eq!(
            resolve_theme_colors_with_payload(Theme::Codex, Some(payload)),
            THEME_DRACULA
        );
    }

    #[test]
    fn resolve_theme_colors_with_payload_migrates_legacy_schema() {
        let payload = r#"{"version":1,"theme":"nord"}"#;
        assert_eq!(
            resolve_theme_colors_with_payload(Theme::Coral, Some(payload)),
            THEME_NORD
        );
    }

    #[test]
    fn resolve_theme_colors_with_payload_falls_back_to_requested_theme_when_invalid() {
        let payload = r#"{"version":"bad","base_theme":"dracula"}"#;
        assert_eq!(
            resolve_theme_colors_with_payload(Theme::Coral, Some(payload)),
            THEME_CORAL
        );
    }

    #[test]
    fn resolve_style_pack_colors_falls_back_to_base_theme_for_unsupported_schema_version() {
        let unsupported = StylePack::with_schema_version(Theme::Codex, u16::MAX);
        assert_eq!(resolve_style_pack_colors(unsupported), THEME_CODEX);
    }

    #[test]
    fn resolve_theme_colors_with_payload_applies_border_style_override() {
        let payload = r#"{
            "version":3,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"border_style":"none"}
        }"#;
        let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
        assert_eq!(colors.borders, BORDER_NONE);
    }

    #[test]
    fn resolve_theme_colors_with_payload_applies_indicator_override() {
        let payload = r#"{
            "version":3,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"indicators":"ascii"}
        }"#;
        let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
        assert_eq!(colors.indicator_rec, "*");
        assert_eq!(colors.indicator_auto, "@");
        assert_eq!(colors.indicator_manual, ">");
        assert_eq!(colors.indicator_idle, "-");
        assert_eq!(colors.indicator_processing, "~");
        assert_eq!(colors.indicator_responding, ">");
    }

    #[test]
    fn resolve_theme_colors_with_payload_applies_glyph_override() {
        let payload = r#"{
            "version":3,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"glyphs":"ascii"}
        }"#;
        let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
        assert_eq!(colors.glyph_set, GlyphSet::Ascii);
    }

    #[test]
    fn resolve_theme_colors_with_payload_applies_progress_style_override() {
        let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "surfaces":{"progress_style":"dots"}
        }"#;
        let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
        assert_eq!(colors.spinner_style, SpinnerStyle::Dots);
    }

    #[test]
    fn resolve_theme_colors_with_payload_applies_progress_bar_family_override() {
        let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "components":{"progress_bar_family":"blocks"}
        }"#;
        let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
        assert_eq!(colors.progress_bar_family, ProgressBarFamily::Blocks);
    }

    #[test]
    fn resolve_theme_colors_with_payload_applies_voice_scene_style_override() {
        let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "surfaces":{"voice_scene_style":"minimal"}
        }"#;
        let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
        assert_eq!(colors.voice_scene_style, VoiceSceneStyle::Minimal);
    }

    #[test]
    fn resolve_theme_colors_applies_runtime_glyph_override() {
        let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
            border_style_override: None,
            glyph_set_override: Some(RuntimeGlyphSetOverride::Ascii),
            indicator_set_override: None,
            progress_style_override: None,
            progress_bar_family_override: None,
            voice_scene_style_override: None,
        });
        let colors = resolve_theme_colors(Theme::Codex);
        assert_eq!(colors.glyph_set, GlyphSet::Ascii);
    }

    #[test]
    fn resolve_theme_colors_applies_runtime_indicator_override() {
        let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
            border_style_override: None,
            glyph_set_override: None,
            indicator_set_override: Some(RuntimeIndicatorSetOverride::Diamond),
            progress_style_override: None,
            progress_bar_family_override: None,
            voice_scene_style_override: None,
        });
        let colors = resolve_theme_colors(Theme::Codex);
        assert_eq!(colors.indicator_rec, "◆");
        assert_eq!(colors.indicator_processing, "◈");
    }

    #[test]
    fn resolve_theme_colors_applies_runtime_border_override() {
        let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
            border_style_override: Some(RuntimeBorderStyleOverride::None),
            glyph_set_override: None,
            indicator_set_override: None,
            progress_style_override: None,
            progress_bar_family_override: None,
            voice_scene_style_override: None,
        });
        let colors = resolve_theme_colors(Theme::Codex);
        assert_eq!(colors.borders, BORDER_NONE);
    }

    #[test]
    fn resolve_theme_colors_applies_runtime_progress_style_override() {
        let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
            border_style_override: None,
            glyph_set_override: None,
            indicator_set_override: None,
            progress_style_override: Some(RuntimeProgressStyleOverride::Line),
            progress_bar_family_override: None,
            voice_scene_style_override: None,
        });
        let colors = resolve_theme_colors(Theme::Codex);
        assert_eq!(colors.spinner_style, SpinnerStyle::Line);
    }

    #[test]
    fn resolve_theme_colors_applies_runtime_progress_bar_family_override() {
        let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
            border_style_override: None,
            glyph_set_override: None,
            indicator_set_override: None,
            progress_style_override: None,
            progress_bar_family_override: Some(RuntimeProgressBarFamilyOverride::Braille),
            voice_scene_style_override: None,
        });
        let colors = resolve_theme_colors(Theme::Codex);
        assert_eq!(colors.progress_bar_family, ProgressBarFamily::Braille);
    }

    #[test]
    fn resolve_theme_colors_applies_runtime_voice_scene_style_override() {
        let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
            border_style_override: None,
            glyph_set_override: None,
            indicator_set_override: None,
            progress_style_override: None,
            progress_bar_family_override: None,
            voice_scene_style_override: Some(RuntimeVoiceSceneStyleOverride::Pulse),
        });
        let colors = resolve_theme_colors(Theme::Codex);
        assert_eq!(colors.voice_scene_style, VoiceSceneStyle::Pulse);
    }

    #[test]
    fn style_pack_theme_override_from_payload_reads_valid_base_theme() {
        let payload = r#"{"version":3,"profile":"ops","base_theme":"dracula"}"#;
        assert_eq!(
            style_pack_theme_override_from_payload(Some(payload)),
            Some(Theme::Dracula)
        );
    }

    #[test]
    fn style_pack_theme_override_from_payload_ignores_invalid_payload() {
        let payload = r#"{"version":"bad","base_theme":"dracula"}"#;
        assert_eq!(style_pack_theme_override_from_payload(Some(payload)), None);
    }

    #[test]
    fn resolve_theme_colors_ignores_style_pack_env_without_test_opt_in() {
        let _guard = ENV_GUARD
            .get_or_init(|| Mutex::new(()))
            .lock()
            .unwrap_or_else(|e| e.into_inner());
        let prev_style_pack = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
        let prev_opt_in = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

        std::env::set_var(
            STYLE_PACK_SCHEMA_ENV,
            r#"{"version":3,"profile":"ops","base_theme":"codex"}"#,
        );
        std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN);

        assert_eq!(resolve_theme_colors(Theme::Coral), THEME_CORAL);
        assert_eq!(locked_style_pack_theme(), None);

        match prev_style_pack {
            Some(value) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, value),
            None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
        }
        match prev_opt_in {
            Some(value) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, value),
            None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
        }
    }

    #[test]
    fn resolve_theme_colors_reads_style_pack_env_when_test_opted_in() {
        let _guard = ENV_GUARD
            .get_or_init(|| Mutex::new(()))
            .lock()
            .unwrap_or_else(|e| e.into_inner());
        let prev_style_pack = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
        let prev_opt_in = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

        std::env::set_var(
            STYLE_PACK_SCHEMA_ENV,
            r#"{"version":3,"profile":"ops","base_theme":"codex"}"#,
        );
        std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

        assert_eq!(resolve_theme_colors(Theme::Coral), THEME_CODEX);
        assert_eq!(locked_style_pack_theme(), Some(Theme::Codex));

        match prev_style_pack {
            Some(value) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, value),
            None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
        }
        match prev_opt_in {
            Some(value) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, value),
            None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
        }
    }
}
