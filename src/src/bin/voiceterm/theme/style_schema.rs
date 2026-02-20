//! Versioned Theme Studio style-schema parsing and migration helpers.
//!
//! Phase-0 safety rail: parse/migrate style schema payloads without panics and
//! provide deterministic fallback behavior for invalid inputs.

use super::Theme;
use serde::Deserialize;

pub(super) const CURRENT_STYLE_SCHEMA_VERSION: u16 = 4;
pub(super) const V3_STYLE_SCHEMA_VERSION: u16 = 3;
pub(super) const V2_STYLE_SCHEMA_VERSION: u16 = 2;
pub(super) const LEGACY_STYLE_SCHEMA_VERSION: u16 = 1;
const DEFAULT_PROFILE_NAME: &str = "default";
const LEGACY_PROFILE_NAME: &str = "legacy-v1";

/// Surface-level style-pack overrides for runtime visual surfaces.
///
/// Each field corresponds to a visual surface category that can be independently
/// themed via a style-pack payload, enabling Theme Studio to address every
/// runtime surface without hardcoded constants.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub(super) struct SurfaceOverrides {
    /// Toast notification position policy.
    pub(super) toast_position: Option<ToastPositionOverride>,
    /// Startup splash style policy.
    pub(super) startup_style: Option<StartupStyleOverride>,
    /// Progress spinner style policy.
    pub(super) progress_style: Option<ProgressStyleOverride>,
    /// Voice-state scene animation policy.
    pub(super) voice_scene_style: Option<VoiceSceneStyleOverride>,
}

/// Component-level style-pack overrides for individual renderable control
/// surfaces. Enables Theme Studio to address specific component categories
/// (buttons, overlays, HUD elements, etc.) via style-pack payloads.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub(super) struct ComponentOverrides {
    /// Override for overlay chrome border style.
    pub(super) overlay_border: Option<BorderStyleOverride>,
    /// Override for HUD status line border style.
    pub(super) hud_border: Option<BorderStyleOverride>,
    /// Override for toast notification severity display mode.
    pub(super) toast_severity_mode: Option<ToastSeverityMode>,
    /// Override for startup banner style (compact/full/hidden).
    pub(super) banner_style: Option<BannerStyleOverride>,
    /// Override for progress bar family.
    pub(super) progress_bar_family: Option<ProgressBarFamily>,
}

/// Toast severity display mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum ToastSeverityMode {
    Theme,
    Icon,
    Label,
    IconAndLabel,
}

/// Banner display style.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum BannerStyleOverride {
    Theme,
    Full,
    Compact,
    Minimal,
    Hidden,
}

/// Progress bar rendering family.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum ProgressBarFamily {
    Theme,
    Bar,
    Compact,
    Blocks,
    Braille,
}

/// Toast notification position in the terminal.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum ToastPositionOverride {
    Theme,
    TopRight,
    BottomRight,
    TopCenter,
    BottomCenter,
}

/// Startup splash visual style.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum StartupStyleOverride {
    Theme,
    Full,
    Minimal,
    Hidden,
}

/// Progress indicator family.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum ProgressStyleOverride {
    Theme,
    Braille,
    Dots,
    Line,
    Block,
}

/// Voice-state scene animation policy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum VoiceSceneStyleOverride {
    Theme,
    Pulse,
    Static,
    Minimal,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) struct StyleSchemaPack {
    pub(super) version: u16,
    pub(super) profile: String,
    pub(super) base_theme: Theme,
    pub(super) border_style_override: Option<BorderStyleOverride>,
    pub(super) indicator_set_override: Option<IndicatorSetOverride>,
    pub(super) glyph_set_override: Option<GlyphSetOverride>,
    pub(super) surface_overrides: SurfaceOverrides,
    pub(super) component_overrides: ComponentOverrides,
}

impl StyleSchemaPack {
    #[must_use]
    pub(super) fn fallback(theme: Theme) -> Self {
        Self {
            version: CURRENT_STYLE_SCHEMA_VERSION,
            profile: DEFAULT_PROFILE_NAME.to_string(),
            base_theme: theme,
            border_style_override: None,
            indicator_set_override: None,
            glyph_set_override: None,
            surface_overrides: SurfaceOverrides::default(),
            component_overrides: ComponentOverrides::default(),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum BorderStyleOverride {
    Theme,
    Single,
    Rounded,
    Double,
    Heavy,
    None,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum IndicatorSetOverride {
    Theme,
    Ascii,
    Dot,
    Diamond,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(super) enum GlyphSetOverride {
    Theme,
    Unicode,
    Ascii,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) enum StyleSchemaError {
    InvalidJson(String),
    MissingVersion,
    UnsupportedVersion(u16),
    InvalidTheme(String),
}

impl std::fmt::Display for StyleSchemaError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidJson(err) => write!(f, "invalid style schema json: {err}"),
            Self::MissingVersion => write!(f, "style schema missing version"),
            Self::UnsupportedVersion(version) => {
                write!(f, "unsupported style schema version: {version}")
            }
            Self::InvalidTheme(theme) => write!(f, "invalid style schema theme: {theme}"),
        }
    }
}

impl std::error::Error for StyleSchemaError {}

#[derive(Debug, Deserialize)]
struct StyleSchemaEnvelope {
    version: Option<u16>,
}

#[derive(Debug, Deserialize)]
struct StyleSchemaV1 {
    theme: String,
}

#[derive(Debug, Deserialize)]
struct StyleSchemaV2 {
    #[serde(default = "default_profile")]
    profile: String,
    base_theme: String,
    #[serde(default)]
    overrides: StyleSchemaOverrides,
}

#[derive(Debug, Clone, Default, Deserialize)]
struct StyleSchemaOverrides {
    #[serde(default)]
    border_style: Option<BorderStyleOverride>,
    #[serde(default)]
    indicators: Option<IndicatorSetOverride>,
    #[serde(default)]
    glyphs: Option<GlyphSetOverride>,
}

/// V3 schema adds surface-level overrides for toast, startup, progress, and
/// voice-state surfaces while remaining backward-compatible with V2 core
/// overrides.
#[derive(Debug, Deserialize)]
struct StyleSchemaV3 {
    #[serde(default = "default_profile")]
    profile: String,
    base_theme: String,
    #[serde(default)]
    overrides: StyleSchemaOverrides,
    #[serde(default)]
    surfaces: StyleSchemaSurfaces,
}

#[derive(Debug, Clone, Default, Deserialize)]
struct StyleSchemaSurfaces {
    #[serde(default)]
    toast_position: Option<ToastPositionOverride>,
    #[serde(default)]
    startup_style: Option<StartupStyleOverride>,
    #[serde(default)]
    progress_style: Option<ProgressStyleOverride>,
    #[serde(default)]
    voice_scene_style: Option<VoiceSceneStyleOverride>,
}

/// V4 schema adds component-level overrides for per-surface style-pack
/// addressing while remaining backward-compatible with V3 surface overrides.
#[derive(Debug, Deserialize)]
struct StyleSchemaV4 {
    #[serde(default = "default_profile")]
    profile: String,
    base_theme: String,
    #[serde(default)]
    overrides: StyleSchemaOverrides,
    #[serde(default)]
    surfaces: StyleSchemaSurfaces,
    #[serde(default)]
    components: StyleSchemaComponents,
}

#[derive(Debug, Clone, Default, Deserialize)]
struct StyleSchemaComponents {
    #[serde(default)]
    overlay_border: Option<BorderStyleOverride>,
    #[serde(default)]
    hud_border: Option<BorderStyleOverride>,
    #[serde(default)]
    toast_severity_mode: Option<ToastSeverityMode>,
    #[serde(default)]
    banner_style: Option<BannerStyleOverride>,
    #[serde(default)]
    progress_bar_family: Option<ProgressBarFamily>,
}

fn default_profile() -> String {
    DEFAULT_PROFILE_NAME.to_string()
}

fn parse_theme(theme_name: &str) -> Result<Theme, StyleSchemaError> {
    Theme::from_name(theme_name).ok_or_else(|| StyleSchemaError::InvalidTheme(theme_name.into()))
}

fn normalize_border_override(value: Option<BorderStyleOverride>) -> Option<BorderStyleOverride> {
    match value {
        Some(BorderStyleOverride::Theme) | None => None,
        other => other,
    }
}

fn normalize_indicator_override(
    value: Option<IndicatorSetOverride>,
) -> Option<IndicatorSetOverride> {
    match value {
        Some(IndicatorSetOverride::Theme) | None => None,
        other => other,
    }
}

fn normalize_glyph_override(value: Option<GlyphSetOverride>) -> Option<GlyphSetOverride> {
    match value {
        Some(GlyphSetOverride::Theme) | None => None,
        other => other,
    }
}

fn normalize_toast_position(value: Option<ToastPositionOverride>) -> Option<ToastPositionOverride> {
    match value {
        Some(ToastPositionOverride::Theme) | None => None,
        other => other,
    }
}

fn normalize_startup_style(value: Option<StartupStyleOverride>) -> Option<StartupStyleOverride> {
    match value {
        Some(StartupStyleOverride::Theme) | None => None,
        other => other,
    }
}

fn normalize_progress_style(value: Option<ProgressStyleOverride>) -> Option<ProgressStyleOverride> {
    match value {
        Some(ProgressStyleOverride::Theme) | None => None,
        other => other,
    }
}

fn normalize_voice_scene_style(
    value: Option<VoiceSceneStyleOverride>,
) -> Option<VoiceSceneStyleOverride> {
    match value {
        Some(VoiceSceneStyleOverride::Theme) | None => None,
        other => other,
    }
}

fn normalize_toast_severity_mode(value: Option<ToastSeverityMode>) -> Option<ToastSeverityMode> {
    match value {
        Some(ToastSeverityMode::Theme) | None => None,
        other => other,
    }
}

fn normalize_banner_style(value: Option<BannerStyleOverride>) -> Option<BannerStyleOverride> {
    match value {
        Some(BannerStyleOverride::Theme) | None => None,
        other => other,
    }
}

fn normalize_progress_bar_family(value: Option<ProgressBarFamily>) -> Option<ProgressBarFamily> {
    match value {
        Some(ProgressBarFamily::Theme) | None => None,
        other => other,
    }
}

pub(super) fn parse_style_schema(payload: &str) -> Result<StyleSchemaPack, StyleSchemaError> {
    let envelope: StyleSchemaEnvelope = serde_json::from_str(payload)
        .map_err(|err| StyleSchemaError::InvalidJson(err.to_string()))?;
    let version = envelope.version.ok_or(StyleSchemaError::MissingVersion)?;

    match version {
        LEGACY_STYLE_SCHEMA_VERSION => {
            let legacy: StyleSchemaV1 = serde_json::from_str(payload)
                .map_err(|err| StyleSchemaError::InvalidJson(err.to_string()))?;
            let base_theme = parse_theme(&legacy.theme)?;
            Ok(StyleSchemaPack {
                version: CURRENT_STYLE_SCHEMA_VERSION,
                profile: LEGACY_PROFILE_NAME.to_string(),
                base_theme,
                border_style_override: None,
                indicator_set_override: None,
                glyph_set_override: None,
                surface_overrides: SurfaceOverrides::default(),
                component_overrides: ComponentOverrides::default(),
            })
        }
        V2_STYLE_SCHEMA_VERSION => {
            let current: StyleSchemaV2 = serde_json::from_str(payload)
                .map_err(|err| StyleSchemaError::InvalidJson(err.to_string()))?;
            let base_theme = parse_theme(&current.base_theme)?;
            let profile = if current.profile.trim().is_empty() {
                DEFAULT_PROFILE_NAME.to_string()
            } else {
                current.profile
            };
            Ok(StyleSchemaPack {
                version: CURRENT_STYLE_SCHEMA_VERSION,
                profile,
                base_theme,
                border_style_override: normalize_border_override(current.overrides.border_style),
                indicator_set_override: normalize_indicator_override(current.overrides.indicators),
                glyph_set_override: normalize_glyph_override(current.overrides.glyphs),
                surface_overrides: SurfaceOverrides::default(),
                component_overrides: ComponentOverrides::default(),
            })
        }
        V3_STYLE_SCHEMA_VERSION => {
            let current: StyleSchemaV3 = serde_json::from_str(payload)
                .map_err(|err| StyleSchemaError::InvalidJson(err.to_string()))?;
            let base_theme = parse_theme(&current.base_theme)?;
            let profile = if current.profile.trim().is_empty() {
                DEFAULT_PROFILE_NAME.to_string()
            } else {
                current.profile
            };
            Ok(StyleSchemaPack {
                version: CURRENT_STYLE_SCHEMA_VERSION,
                profile,
                base_theme,
                border_style_override: normalize_border_override(current.overrides.border_style),
                indicator_set_override: normalize_indicator_override(current.overrides.indicators),
                glyph_set_override: normalize_glyph_override(current.overrides.glyphs),
                surface_overrides: SurfaceOverrides {
                    toast_position: normalize_toast_position(current.surfaces.toast_position),
                    startup_style: normalize_startup_style(current.surfaces.startup_style),
                    progress_style: normalize_progress_style(current.surfaces.progress_style),
                    voice_scene_style: normalize_voice_scene_style(
                        current.surfaces.voice_scene_style,
                    ),
                },
                component_overrides: ComponentOverrides::default(),
            })
        }
        CURRENT_STYLE_SCHEMA_VERSION => {
            let current: StyleSchemaV4 = serde_json::from_str(payload)
                .map_err(|err| StyleSchemaError::InvalidJson(err.to_string()))?;
            let base_theme = parse_theme(&current.base_theme)?;
            let profile = if current.profile.trim().is_empty() {
                DEFAULT_PROFILE_NAME.to_string()
            } else {
                current.profile
            };
            Ok(StyleSchemaPack {
                version: CURRENT_STYLE_SCHEMA_VERSION,
                profile,
                base_theme,
                border_style_override: normalize_border_override(current.overrides.border_style),
                indicator_set_override: normalize_indicator_override(current.overrides.indicators),
                glyph_set_override: normalize_glyph_override(current.overrides.glyphs),
                surface_overrides: SurfaceOverrides {
                    toast_position: normalize_toast_position(current.surfaces.toast_position),
                    startup_style: normalize_startup_style(current.surfaces.startup_style),
                    progress_style: normalize_progress_style(current.surfaces.progress_style),
                    voice_scene_style: normalize_voice_scene_style(
                        current.surfaces.voice_scene_style,
                    ),
                },
                component_overrides: ComponentOverrides {
                    overlay_border: normalize_border_override(current.components.overlay_border),
                    hud_border: normalize_border_override(current.components.hud_border),
                    toast_severity_mode: normalize_toast_severity_mode(
                        current.components.toast_severity_mode,
                    ),
                    banner_style: normalize_banner_style(current.components.banner_style),
                    progress_bar_family: normalize_progress_bar_family(
                        current.components.progress_bar_family,
                    ),
                },
            })
        }
        other => Err(StyleSchemaError::UnsupportedVersion(other)),
    }
}

#[must_use]
pub(super) fn parse_style_schema_with_fallback(
    payload: &str,
    fallback: StyleSchemaPack,
) -> StyleSchemaPack {
    parse_style_schema(payload).unwrap_or(fallback)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_style_schema_reads_current_version_payload() {
        let payload = r#"{"version":4,"profile":"ops","base_theme":"codex"}"#;
        let parsed = parse_style_schema(payload).expect("v4 payload should parse");

        assert_eq!(parsed.version, CURRENT_STYLE_SCHEMA_VERSION);
        assert_eq!(parsed.profile, "ops");
        assert_eq!(parsed.base_theme, Theme::Codex);
        assert_eq!(parsed.border_style_override, None);
        assert_eq!(parsed.indicator_set_override, None);
        assert_eq!(parsed.glyph_set_override, None);
        assert_eq!(parsed.surface_overrides, SurfaceOverrides::default());
    }

    #[test]
    fn parse_style_schema_migrates_v2_payload_to_current_version() {
        let payload = r#"{"version":2,"profile":"ops","base_theme":"codex"}"#;
        let parsed = parse_style_schema(payload).expect("v2 payload should migrate");

        assert_eq!(parsed.version, CURRENT_STYLE_SCHEMA_VERSION);
        assert_eq!(parsed.profile, "ops");
        assert_eq!(parsed.base_theme, Theme::Codex);
        assert_eq!(parsed.surface_overrides, SurfaceOverrides::default());
    }

    #[test]
    fn parse_style_schema_migrates_v1_payload_to_current_version() {
        let payload = r#"{"version":1,"theme":"claude"}"#;
        let parsed = parse_style_schema(payload).expect("v1 payload should migrate");

        assert_eq!(parsed.version, CURRENT_STYLE_SCHEMA_VERSION);
        assert_eq!(parsed.profile, "legacy-v1");
        assert_eq!(parsed.base_theme, Theme::Claude);
        assert_eq!(parsed.border_style_override, None);
        assert_eq!(parsed.indicator_set_override, None);
        assert_eq!(parsed.glyph_set_override, None);
        assert_eq!(parsed.surface_overrides, SurfaceOverrides::default());
    }

    #[test]
    fn parse_style_schema_rejects_unsupported_versions() {
        let payload = r#"{"version":99,"theme":"coral"}"#;
        assert_eq!(
            parse_style_schema(payload),
            Err(StyleSchemaError::UnsupportedVersion(99))
        );
    }

    #[test]
    fn parse_style_schema_rejects_invalid_theme_names() {
        let payload = r#"{"version":4,"profile":"qa","base_theme":"unknown-theme"}"#;
        assert_eq!(
            parse_style_schema(payload),
            Err(StyleSchemaError::InvalidTheme("unknown-theme".to_string()))
        );
    }

    #[test]
    fn parse_style_schema_with_fallback_returns_default_on_parse_error() {
        let fallback = StyleSchemaPack::fallback(Theme::Coral);
        let payload = r#"{"version":"bad","base_theme":"codex"}"#;
        let resolved = parse_style_schema_with_fallback(payload, fallback.clone());

        assert_eq!(resolved, fallback);
    }

    #[test]
    fn parse_style_schema_defaults_blank_profile_to_default_name() {
        let payload = r#"{"version":2,"profile":" ","base_theme":"chatgpt"}"#;
        let parsed = parse_style_schema(payload).expect("v2 payload should parse");

        assert_eq!(parsed.profile, "default");
        assert_eq!(parsed.base_theme, Theme::ChatGpt);
    }

    #[test]
    fn parse_style_schema_reads_runtime_visual_overrides() {
        let payload = r#"{
            "version":2,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"border_style":"rounded","indicators":"ascii","glyphs":"ascii"}
        }"#;
        let parsed = parse_style_schema(payload).expect("v2 payload should parse");

        assert_eq!(
            parsed.border_style_override,
            Some(BorderStyleOverride::Rounded)
        );
        assert_eq!(
            parsed.indicator_set_override,
            Some(IndicatorSetOverride::Ascii)
        );
        assert_eq!(parsed.glyph_set_override, Some(GlyphSetOverride::Ascii));
    }

    #[test]
    fn parse_style_schema_normalizes_theme_overrides_to_none() {
        let payload = r#"{
            "version":2,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"border_style":"theme","indicators":"theme","glyphs":"theme"}
        }"#;
        let parsed = parse_style_schema(payload).expect("v2 payload should parse");

        assert_eq!(parsed.border_style_override, None);
        assert_eq!(parsed.indicator_set_override, None);
        assert_eq!(parsed.glyph_set_override, None);
    }

    #[test]
    fn parse_style_schema_v3_reads_surface_overrides() {
        let payload = r#"{
            "version":3,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"border_style":"heavy"},
            "surfaces":{
                "toast_position":"top-right",
                "startup_style":"minimal",
                "progress_style":"dots",
                "voice_scene_style":"pulse"
            }
        }"#;
        let parsed = parse_style_schema(payload).expect("v3 payload should parse");

        assert_eq!(parsed.version, CURRENT_STYLE_SCHEMA_VERSION);
        assert_eq!(
            parsed.border_style_override,
            Some(BorderStyleOverride::Heavy)
        );
        assert_eq!(
            parsed.surface_overrides.toast_position,
            Some(ToastPositionOverride::TopRight)
        );
        assert_eq!(
            parsed.surface_overrides.startup_style,
            Some(StartupStyleOverride::Minimal)
        );
        assert_eq!(
            parsed.surface_overrides.progress_style,
            Some(ProgressStyleOverride::Dots)
        );
        assert_eq!(
            parsed.surface_overrides.voice_scene_style,
            Some(VoiceSceneStyleOverride::Pulse)
        );
    }

    #[test]
    fn parse_style_schema_v3_normalizes_theme_surface_overrides() {
        let payload = r#"{
            "version":3,
            "profile":"ops",
            "base_theme":"codex",
            "surfaces":{
                "toast_position":"theme",
                "startup_style":"theme",
                "progress_style":"theme",
                "voice_scene_style":"theme"
            }
        }"#;
        let parsed = parse_style_schema(payload).expect("v3 payload should parse");

        assert_eq!(parsed.surface_overrides.toast_position, None);
        assert_eq!(parsed.surface_overrides.startup_style, None);
        assert_eq!(parsed.surface_overrides.progress_style, None);
        assert_eq!(parsed.surface_overrides.voice_scene_style, None);
    }

    #[test]
    fn parse_style_schema_v3_with_empty_surfaces_section() {
        let payload = r#"{"version":3,"profile":"ops","base_theme":"codex","surfaces":{}}"#;
        let parsed = parse_style_schema(payload).expect("v3 payload should parse");

        assert_eq!(parsed.surface_overrides, SurfaceOverrides::default());
    }

    #[test]
    fn parse_style_schema_v2_migrated_has_no_surface_overrides() {
        let payload = r#"{
            "version":2,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"border_style":"rounded"}
        }"#;
        let parsed = parse_style_schema(payload).expect("v2 payload should migrate");

        assert_eq!(
            parsed.border_style_override,
            Some(BorderStyleOverride::Rounded)
        );
        assert_eq!(parsed.surface_overrides, SurfaceOverrides::default());
        assert_eq!(parsed.component_overrides, ComponentOverrides::default());
    }

    #[test]
    fn parse_style_schema_v3_migrated_has_no_component_overrides() {
        let payload = r#"{
            "version":3,
            "profile":"ops",
            "base_theme":"codex",
            "surfaces":{"toast_position":"top-right"}
        }"#;
        let parsed = parse_style_schema(payload).expect("v3 payload should migrate");

        assert_eq!(
            parsed.surface_overrides.toast_position,
            Some(ToastPositionOverride::TopRight)
        );
        assert_eq!(parsed.component_overrides, ComponentOverrides::default());
    }

    #[test]
    fn parse_style_schema_v4_reads_component_overrides() {
        let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "components":{
                "overlay_border":"rounded",
                "hud_border":"heavy",
                "toast_severity_mode":"icon-and-label",
                "banner_style":"compact",
                "progress_bar_family":"blocks"
            }
        }"#;
        let parsed = parse_style_schema(payload).expect("v4 payload should parse");

        assert_eq!(parsed.version, CURRENT_STYLE_SCHEMA_VERSION);
        assert_eq!(
            parsed.component_overrides.overlay_border,
            Some(BorderStyleOverride::Rounded)
        );
        assert_eq!(
            parsed.component_overrides.hud_border,
            Some(BorderStyleOverride::Heavy)
        );
        assert_eq!(
            parsed.component_overrides.toast_severity_mode,
            Some(ToastSeverityMode::IconAndLabel)
        );
        assert_eq!(
            parsed.component_overrides.banner_style,
            Some(BannerStyleOverride::Compact)
        );
        assert_eq!(
            parsed.component_overrides.progress_bar_family,
            Some(ProgressBarFamily::Blocks)
        );
    }

    #[test]
    fn parse_style_schema_v4_normalizes_theme_component_overrides() {
        let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "components":{
                "overlay_border":"theme",
                "hud_border":"theme",
                "toast_severity_mode":"theme",
                "banner_style":"theme",
                "progress_bar_family":"theme"
            }
        }"#;
        let parsed = parse_style_schema(payload).expect("v4 payload should parse");

        assert_eq!(parsed.component_overrides.overlay_border, None);
        assert_eq!(parsed.component_overrides.hud_border, None);
        assert_eq!(parsed.component_overrides.toast_severity_mode, None);
        assert_eq!(parsed.component_overrides.banner_style, None);
        assert_eq!(parsed.component_overrides.progress_bar_family, None);
    }

    #[test]
    fn parse_style_schema_v4_with_empty_components_section() {
        let payload = r#"{"version":4,"profile":"ops","base_theme":"codex","components":{}}"#;
        let parsed = parse_style_schema(payload).expect("v4 payload should parse");

        assert_eq!(parsed.component_overrides, ComponentOverrides::default());
    }
}
