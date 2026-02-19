//! Runtime style-pack resolver scaffold.
//!
//! This keeps current built-in theme behavior unchanged while introducing a
//! dedicated resolver surface for future Theme Studio packs.

use super::{
    style_schema::{
        parse_style_schema, parse_style_schema_with_fallback, BorderStyleOverride,
        GlyphSetOverride, IndicatorSetOverride, ProgressStyleOverride, StartupStyleOverride,
        StyleSchemaPack, ToastPositionOverride, VoiceSceneStyleOverride,
        CURRENT_STYLE_SCHEMA_VERSION,
    },
    GlyphSet, Theme, ThemeColors, BORDER_DOUBLE, BORDER_HEAVY, BORDER_NONE, BORDER_ROUNDED,
    BORDER_SINGLE, THEME_ANSI, THEME_CATPPUCCIN, THEME_CHATGPT, THEME_CLAUDE, THEME_CODEX,
    THEME_CORAL, THEME_DRACULA, THEME_GRUVBOX, THEME_NONE, THEME_NORD, THEME_TOKYONIGHT,
};

pub(crate) const STYLE_PACK_RUNTIME_VERSION: u16 = CURRENT_STYLE_SCHEMA_VERSION;
const STYLE_PACK_SCHEMA_ENV: &str = "VOICETERM_STYLE_PACK_JSON";
#[cfg(test)]
const STYLE_PACK_TEST_ENV_OPT_IN: &str = "VOICETERM_TEST_ENABLE_STYLE_PACK_ENV";

/// Resolved surface-level style overrides exposed to runtime rendering.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub(crate) struct ResolvedSurfaceOverrides {
    pub(crate) toast_position: Option<ToastPositionOverride>,
    pub(crate) startup_style: Option<StartupStyleOverride>,
    pub(crate) progress_style: Option<ProgressStyleOverride>,
    pub(crate) voice_scene_style: Option<VoiceSceneStyleOverride>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct StylePack {
    pub(crate) schema_version: u16,
    pub(crate) base_theme: Theme,
    pub(crate) border_style_override: Option<BorderStyleOverride>,
    pub(crate) indicator_set_override: Option<IndicatorSetOverride>,
    pub(crate) glyph_set_override: Option<GlyphSetOverride>,
    pub(crate) surface_overrides: ResolvedSurfaceOverrides,
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

#[must_use]
pub(crate) fn resolve_theme_colors(theme: Theme) -> ThemeColors {
    let payload = runtime_style_pack_payload();
    resolve_theme_colors_with_payload(theme, payload.as_deref())
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
            assert_eq!(resolve_theme_colors(theme), base_theme_colors(theme));
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
