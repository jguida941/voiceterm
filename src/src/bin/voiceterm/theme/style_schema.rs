//! Versioned Theme Studio style-schema parsing and migration helpers.
//!
//! Phase-0 safety rail: parse/migrate style schema payloads without panics and
//! provide deterministic fallback behavior for invalid inputs.

use super::Theme;
use serde::Deserialize;

pub(super) const CURRENT_STYLE_SCHEMA_VERSION: u16 = 2;
pub(super) const LEGACY_STYLE_SCHEMA_VERSION: u16 = 1;
const DEFAULT_PROFILE_NAME: &str = "default";
const LEGACY_PROFILE_NAME: &str = "legacy-v1";

#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) struct StyleSchemaPack {
    pub(super) version: u16,
    pub(super) profile: String,
    pub(super) base_theme: Theme,
    pub(super) border_style_override: Option<BorderStyleOverride>,
    pub(super) indicator_set_override: Option<IndicatorSetOverride>,
    pub(super) glyph_set_override: Option<GlyphSetOverride>,
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
            })
        }
        CURRENT_STYLE_SCHEMA_VERSION => {
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
        let payload = r#"{"version":2,"profile":"ops","base_theme":"codex"}"#;
        let parsed = parse_style_schema(payload).expect("v2 payload should parse");

        assert_eq!(parsed.version, CURRENT_STYLE_SCHEMA_VERSION);
        assert_eq!(parsed.profile, "ops");
        assert_eq!(parsed.base_theme, Theme::Codex);
        assert_eq!(parsed.border_style_override, None);
        assert_eq!(parsed.indicator_set_override, None);
        assert_eq!(parsed.glyph_set_override, None);
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
        let payload = r#"{"version":2,"profile":"qa","base_theme":"unknown-theme"}"#;
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
}
