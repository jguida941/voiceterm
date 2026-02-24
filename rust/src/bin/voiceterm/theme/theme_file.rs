//! TOML theme file parsing, validation, and export.
//!
//! Supports a three-tier token system:
//! - **Palette**: primitive hex colors (e.g. `red = "#ff5555"`)
//! - **Colors**: semantic tokens referencing palette keys or inline hex
//! - **Components**: per-component/state overrides
//!
//! Theme files live in `~/.config/voiceterm/themes/` and can inherit from any
//! built-in theme via `base_theme`.

use std::collections::HashMap;

use serde::{Deserialize, Serialize};

use super::{
    color_value::{palette_to_resolved, ColorValue, ResolvedThemeColors, Rgb},
    BorderSet, GlyphSet, ProgressBarFamily, SpinnerStyle, Theme, VoiceSceneStyle, BORDER_DOUBLE,
    BORDER_HEAVY, BORDER_NONE, BORDER_ROUNDED, BORDER_SINGLE,
};

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

/// Errors encountered while loading or resolving a theme file.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum ThemeFileError {
    Io(String),
    Parse(String),
    InvalidHex(String),
    UnknownPaletteRef(String),
    UnknownBaseTheme(String),
    InvalidBorderStyle(String),
    InvalidGlyphSet(String),
    InvalidSpinnerStyle(String),
    InvalidVoiceSceneStyle(String),
    InvalidProgressBarFamily(String),
}

impl std::fmt::Display for ThemeFileError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(msg) => write!(f, "IO error: {msg}"),
            Self::Parse(msg) => write!(f, "TOML parse error: {msg}"),
            Self::InvalidHex(hex) => write!(f, "invalid hex color: {hex}"),
            Self::UnknownPaletteRef(key) => write!(f, "unknown palette ref: {key}"),
            Self::UnknownBaseTheme(name) => write!(f, "unknown base theme: {name}"),
            Self::InvalidBorderStyle(s) => write!(f, "invalid border style: {s}"),
            Self::InvalidGlyphSet(s) => write!(f, "invalid glyph set: {s}"),
            Self::InvalidSpinnerStyle(s) => write!(f, "invalid spinner style: {s}"),
            Self::InvalidVoiceSceneStyle(s) => write!(f, "invalid voice scene style: {s}"),
            Self::InvalidProgressBarFamily(s) => write!(f, "invalid progress bar family: {s}"),
        }
    }
}

/// Non-fatal warnings from theme file validation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum ThemeFileWarning {
    UnusedPaletteEntry(String),
}

// ---------------------------------------------------------------------------
// TOML schema types (deserialization)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize, Serialize)]
pub(crate) struct ThemeFile {
    #[serde(default)]
    pub(crate) meta: ThemeFileMeta,
    #[serde(default)]
    pub(crate) palette: HashMap<String, String>,
    #[serde(default)]
    pub(crate) colors: ThemeFileColors,
    #[serde(default)]
    pub(crate) borders: ThemeFileBorders,
    #[serde(default)]
    pub(crate) indicators: ThemeFileIndicators,
    #[serde(default)]
    pub(crate) glyphs: ThemeFileGlyphs,
    #[serde(default)]
    pub(crate) spinner: ThemeFileSpinner,
    #[serde(default)]
    pub(crate) voice_scene: ThemeFileVoiceScene,
    #[serde(default)]
    pub(crate) progress: ThemeFileProgress,
    #[serde(default)]
    pub(crate) components: HashMap<String, HashMap<String, ThemeFileComponentStyle>>,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub(crate) struct ThemeFileMeta {
    #[serde(default)]
    pub(crate) name: Option<String>,
    #[serde(default = "default_version")]
    pub(crate) version: u32,
    #[serde(default)]
    pub(crate) base_theme: Option<String>,
}

fn default_version() -> u32 {
    1
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub(crate) struct ThemeFileColors {
    pub(crate) recording: Option<String>,
    pub(crate) processing: Option<String>,
    pub(crate) success: Option<String>,
    pub(crate) warning: Option<String>,
    pub(crate) error: Option<String>,
    pub(crate) info: Option<String>,
    pub(crate) dim: Option<String>,
    pub(crate) bg_primary: Option<String>,
    pub(crate) bg_secondary: Option<String>,
    pub(crate) border: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub(crate) struct ThemeFileBorders {
    pub(crate) style: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub(crate) struct ThemeFileIndicators {
    pub(crate) rec: Option<String>,
    pub(crate) auto: Option<String>,
    pub(crate) manual: Option<String>,
    pub(crate) idle: Option<String>,
    pub(crate) processing: Option<String>,
    pub(crate) responding: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub(crate) struct ThemeFileGlyphs {
    pub(crate) set: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub(crate) struct ThemeFileSpinner {
    pub(crate) style: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub(crate) struct ThemeFileVoiceScene {
    pub(crate) style: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub(crate) struct ThemeFileProgress {
    pub(crate) bar_family: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub(crate) struct ThemeFileComponentStyle {
    pub(crate) fg: Option<String>,
    pub(crate) bg: Option<String>,
    #[serde(default)]
    pub(crate) bold: bool,
    #[serde(default)]
    pub(crate) dim: bool,
}

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

/// Load a theme file from disk and parse it as TOML.
pub(crate) fn load_theme_file(path: &std::path::Path) -> Result<ThemeFile, ThemeFileError> {
    let content = std::fs::read_to_string(path).map_err(|e| ThemeFileError::Io(e.to_string()))?;
    toml::from_str::<ThemeFile>(&content).map_err(|e| ThemeFileError::Parse(e.to_string()))
}

// ---------------------------------------------------------------------------
// Color resolution helpers
// ---------------------------------------------------------------------------

/// Resolve a color token: either a palette reference or an inline `#hex` value.
fn resolve_color_token(
    token: &str,
    palette: &HashMap<String, String>,
) -> Result<ColorValue, ThemeFileError> {
    // If it looks like a hex literal, parse directly.
    if token.starts_with('#') {
        let rgb = Rgb::from_hex(token).ok_or_else(|| ThemeFileError::InvalidHex(token.into()))?;
        return Ok(ColorValue::Rgb(rgb));
    }
    // Otherwise treat as palette reference.
    let hex = palette
        .get(token)
        .ok_or_else(|| ThemeFileError::UnknownPaletteRef(token.into()))?;
    let rgb = Rgb::from_hex(hex).ok_or_else(|| ThemeFileError::InvalidHex(hex.clone()))?;
    Ok(ColorValue::Rgb(rgb))
}

fn resolve_border_style(style: &str) -> Result<BorderSet, ThemeFileError> {
    match style.to_lowercase().as_str() {
        "single" => Ok(BORDER_SINGLE),
        "rounded" => Ok(BORDER_ROUNDED),
        "double" => Ok(BORDER_DOUBLE),
        "heavy" => Ok(BORDER_HEAVY),
        "none" => Ok(BORDER_NONE),
        other => Err(ThemeFileError::InvalidBorderStyle(other.into())),
    }
}

fn resolve_glyph_set(set: &str) -> Result<GlyphSet, ThemeFileError> {
    match set.to_lowercase().as_str() {
        "unicode" => Ok(GlyphSet::Unicode),
        "ascii" => Ok(GlyphSet::Ascii),
        other => Err(ThemeFileError::InvalidGlyphSet(other.into())),
    }
}

fn resolve_spinner_style(style: &str) -> Result<SpinnerStyle, ThemeFileError> {
    match style.to_lowercase().as_str() {
        "theme" => Ok(SpinnerStyle::Theme),
        "braille" => Ok(SpinnerStyle::Braille),
        "dots" => Ok(SpinnerStyle::Dots),
        "line" => Ok(SpinnerStyle::Line),
        "block" => Ok(SpinnerStyle::Block),
        other => Err(ThemeFileError::InvalidSpinnerStyle(other.into())),
    }
}

fn resolve_voice_scene_style(style: &str) -> Result<VoiceSceneStyle, ThemeFileError> {
    match style.to_lowercase().as_str() {
        "theme" => Ok(VoiceSceneStyle::Theme),
        "pulse" => Ok(VoiceSceneStyle::Pulse),
        "static" => Ok(VoiceSceneStyle::Static),
        "minimal" => Ok(VoiceSceneStyle::Minimal),
        other => Err(ThemeFileError::InvalidVoiceSceneStyle(other.into())),
    }
}

fn resolve_progress_bar_family(family: &str) -> Result<ProgressBarFamily, ThemeFileError> {
    match family.to_lowercase().as_str() {
        "theme" => Ok(ProgressBarFamily::Theme),
        "bar" => Ok(ProgressBarFamily::Bar),
        "compact" => Ok(ProgressBarFamily::Compact),
        "blocks" => Ok(ProgressBarFamily::Blocks),
        "braille" => Ok(ProgressBarFamily::Braille),
        other => Err(ThemeFileError::InvalidProgressBarFamily(other.into())),
    }
}

// ---------------------------------------------------------------------------
// Theme file resolution
// ---------------------------------------------------------------------------

/// Resolve a `ThemeFile` into runtime-editable `ResolvedThemeColors`.
///
/// Applies base-theme inheritance: any unset field inherits from the built-in
/// theme specified in `meta.base_theme` (defaults to "codex").
pub(crate) fn resolve_theme_file(file: &ThemeFile) -> Result<ResolvedThemeColors, ThemeFileError> {
    // Resolve base theme for inheritance.
    let base_name = file.meta.base_theme.as_deref().unwrap_or("codex");
    let base_theme = Theme::from_name(base_name)
        .ok_or_else(|| ThemeFileError::UnknownBaseTheme(base_name.into()))?;
    let base_colors = base_theme.colors();
    let mut resolved = palette_to_resolved(&base_colors);

    // Apply color overrides.
    let palette = &file.palette;
    if let Some(ref token) = file.colors.recording {
        resolved.recording = resolve_color_token(token, palette)?;
    }
    if let Some(ref token) = file.colors.processing {
        resolved.processing = resolve_color_token(token, palette)?;
    }
    if let Some(ref token) = file.colors.success {
        resolved.success = resolve_color_token(token, palette)?;
    }
    if let Some(ref token) = file.colors.warning {
        resolved.warning = resolve_color_token(token, palette)?;
    }
    if let Some(ref token) = file.colors.error {
        resolved.error = resolve_color_token(token, palette)?;
    }
    if let Some(ref token) = file.colors.info {
        resolved.info = resolve_color_token(token, palette)?;
    }
    if let Some(ref token) = file.colors.dim {
        resolved.dim = resolve_color_token(token, palette)?;
    }
    if let Some(ref token) = file.colors.bg_primary {
        resolved.bg_primary = resolve_color_token(token, palette)?;
    }
    if let Some(ref token) = file.colors.bg_secondary {
        resolved.bg_secondary = resolve_color_token(token, palette)?;
    }
    if let Some(ref token) = file.colors.border {
        resolved.border = resolve_color_token(token, palette)?;
    }

    // Border style.
    if let Some(ref style) = file.borders.style {
        resolved.borders = resolve_border_style(style)?;
    }

    // Indicators.
    if let Some(ref v) = file.indicators.rec {
        resolved.indicator_rec = v.clone();
    }
    if let Some(ref v) = file.indicators.auto {
        resolved.indicator_auto = v.clone();
    }
    if let Some(ref v) = file.indicators.manual {
        resolved.indicator_manual = v.clone();
    }
    if let Some(ref v) = file.indicators.idle {
        resolved.indicator_idle = v.clone();
    }
    if let Some(ref v) = file.indicators.processing {
        resolved.indicator_processing = v.clone();
    }
    if let Some(ref v) = file.indicators.responding {
        resolved.indicator_responding = v.clone();
    }

    // Glyph set.
    if let Some(ref set) = file.glyphs.set {
        resolved.glyph_set = resolve_glyph_set(set)?;
    }

    // Spinner style.
    if let Some(ref style) = file.spinner.style {
        resolved.spinner_style = resolve_spinner_style(style)?;
    }

    // Voice scene style.
    if let Some(ref style) = file.voice_scene.style {
        resolved.voice_scene_style = resolve_voice_scene_style(style)?;
    }

    // Progress bar family.
    if let Some(ref family) = file.progress.bar_family {
        resolved.progress_bar_family = resolve_progress_bar_family(family)?;
    }

    Ok(resolved)
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

/// Export `ResolvedThemeColors` (and optional metadata) as a TOML string.
pub(crate) fn export_theme_file(
    colors: &ResolvedThemeColors,
    name: Option<&str>,
    base_theme: Option<&str>,
) -> String {
    let mut out = String::with_capacity(512);

    // [meta]
    out.push_str("[meta]\n");
    if let Some(name) = name {
        out.push_str(&format!("name = \"{name}\"\n"));
    }
    out.push_str("version = 1\n");
    if let Some(base) = base_theme {
        out.push_str(&format!("base_theme = \"{base}\"\n"));
    }
    out.push('\n');

    // [colors]
    out.push_str("[colors]\n");
    write_color_field(&mut out, "recording", &colors.recording);
    write_color_field(&mut out, "processing", &colors.processing);
    write_color_field(&mut out, "success", &colors.success);
    write_color_field(&mut out, "warning", &colors.warning);
    write_color_field(&mut out, "error", &colors.error);
    write_color_field(&mut out, "info", &colors.info);
    write_color_field(&mut out, "dim", &colors.dim);
    write_color_field(&mut out, "bg_primary", &colors.bg_primary);
    write_color_field(&mut out, "bg_secondary", &colors.bg_secondary);
    write_color_field(&mut out, "border", &colors.border);
    out.push('\n');

    // [borders]
    out.push_str("[borders]\n");
    out.push_str(&format!(
        "style = \"{}\"\n",
        border_set_name(&colors.borders)
    ));
    out.push('\n');

    // [indicators]
    out.push_str("[indicators]\n");
    out.push_str(&format!("rec = \"{}\"\n", colors.indicator_rec));
    out.push_str(&format!("auto = \"{}\"\n", colors.indicator_auto));
    out.push_str(&format!("manual = \"{}\"\n", colors.indicator_manual));
    out.push_str(&format!("idle = \"{}\"\n", colors.indicator_idle));
    out.push_str(&format!(
        "processing = \"{}\"\n",
        colors.indicator_processing
    ));
    out.push_str(&format!(
        "responding = \"{}\"\n",
        colors.indicator_responding
    ));
    out.push('\n');

    // [glyphs]
    out.push_str("[glyphs]\n");
    out.push_str(&format!(
        "set = \"{}\"\n",
        match colors.glyph_set {
            GlyphSet::Unicode => "unicode",
            GlyphSet::Ascii => "ascii",
        }
    ));
    out.push('\n');

    // [spinner]
    out.push_str("[spinner]\n");
    out.push_str(&format!(
        "style = \"{}\"\n",
        match colors.spinner_style {
            SpinnerStyle::Theme => "theme",
            SpinnerStyle::Braille => "braille",
            SpinnerStyle::Dots => "dots",
            SpinnerStyle::Line => "line",
            SpinnerStyle::Block => "block",
        }
    ));
    out.push('\n');

    // [voice_scene]
    out.push_str("[voice_scene]\n");
    out.push_str(&format!(
        "style = \"{}\"\n",
        match colors.voice_scene_style {
            VoiceSceneStyle::Theme => "theme",
            VoiceSceneStyle::Pulse => "pulse",
            VoiceSceneStyle::Static => "static",
            VoiceSceneStyle::Minimal => "minimal",
        }
    ));
    out.push('\n');

    // [progress]
    out.push_str("[progress]\n");
    out.push_str(&format!(
        "bar_family = \"{}\"\n",
        match colors.progress_bar_family {
            ProgressBarFamily::Theme => "theme",
            ProgressBarFamily::Bar => "bar",
            ProgressBarFamily::Compact => "compact",
            ProgressBarFamily::Blocks => "blocks",
            ProgressBarFamily::Braille => "braille",
        }
    ));

    out
}

fn write_color_field(out: &mut String, name: &str, color: &ColorValue) {
    match color {
        ColorValue::Rgb(rgb) => {
            out.push_str(&format!("{name} = \"{}\"\n", rgb.to_hex()));
        }
        ColorValue::Empty => {
            // Omit empty colors.
        }
        ColorValue::Reset | ColorValue::Ansi16(_) => {
            // ANSI16 colors cannot be represented as hex; omit.
        }
    }
}

fn border_set_name(borders: &BorderSet) -> &'static str {
    if *borders == BORDER_SINGLE {
        "single"
    } else if *borders == BORDER_ROUNDED {
        "rounded"
    } else if *borders == BORDER_DOUBLE {
        "double"
    } else if *borders == BORDER_HEAVY {
        "heavy"
    } else if *borders == BORDER_NONE {
        "none"
    } else {
        "single"
    }
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

/// Validate a theme file and return non-fatal warnings.
#[must_use]
pub(crate) fn validate_theme_file(file: &ThemeFile) -> Vec<ThemeFileWarning> {
    let mut warnings = Vec::new();

    // Check for unused palette entries.
    let color_fields = [
        &file.colors.recording,
        &file.colors.processing,
        &file.colors.success,
        &file.colors.warning,
        &file.colors.error,
        &file.colors.info,
        &file.colors.dim,
        &file.colors.bg_primary,
        &file.colors.bg_secondary,
        &file.colors.border,
    ];

    for key in file.palette.keys() {
        let is_referenced = color_fields
            .iter()
            .any(|field| field.as_ref().is_some_and(|v| v == key));
        if !is_referenced {
            warnings.push(ThemeFileWarning::UnusedPaletteEntry(key.clone()));
        }
    }

    warnings
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::theme::color_value::palette_to_resolved;

    fn parse_theme_file_or_panic(toml_str: &str) -> ThemeFile {
        match toml::from_str(toml_str) {
            Ok(file) => file,
            Err(err) => panic!("failed to parse theme file for test: {err}"),
        }
    }

    fn resolve_theme_file_or_panic(file: &ThemeFile) -> ResolvedThemeColors {
        match resolve_theme_file(file) {
            Ok(resolved) => resolved,
            Err(err) => panic!("failed to resolve theme file for test: {err}"),
        }
    }

    fn resolve_theme_file_err_or_panic(file: &ThemeFile) -> ThemeFileError {
        match resolve_theme_file(file) {
            Ok(_) => panic!("expected resolve_theme_file to fail"),
            Err(err) => err,
        }
    }

    #[test]
    fn parse_minimal_theme_file() {
        let toml_str = r##"
[meta]
name = "Test"
version = 1
base_theme = "codex"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        assert_eq!(file.meta.name.as_deref(), Some("Test"));
        assert_eq!(file.meta.base_theme.as_deref(), Some("codex"));
    }

    #[test]
    fn resolve_theme_file_inherits_from_base() {
        let toml_str = r##"
[meta]
name = "Custom"
base_theme = "claude"

[colors]
recording = "#ff0000"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        let resolved = resolve_theme_file_or_panic(&file);

        // Recording should be our custom color.
        assert_eq!(
            resolved.recording,
            ColorValue::Rgb(Rgb { r: 255, g: 0, b: 0 })
        );

        // Processing should inherit from Claude.
        let claude_resolved = palette_to_resolved(&Theme::Claude.colors());
        assert_eq!(resolved.processing, claude_resolved.processing);
    }

    #[test]
    fn resolve_theme_file_with_palette_refs() {
        let toml_str = r##"
[meta]
base_theme = "codex"

[palette]
red = "#ff5555"
blue = "#6fb1ff"

[colors]
recording = "red"
processing = "blue"
success = "#7ad4a8"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        let resolved = resolve_theme_file_or_panic(&file);

        assert_eq!(
            resolved.recording,
            ColorValue::Rgb(Rgb {
                r: 255,
                g: 85,
                b: 85
            })
        );
        assert_eq!(
            resolved.processing,
            ColorValue::Rgb(Rgb {
                r: 111,
                g: 177,
                b: 255
            })
        );
        assert_eq!(
            resolved.success,
            ColorValue::Rgb(Rgb {
                r: 122,
                g: 212,
                b: 168
            })
        );
    }

    #[test]
    fn resolve_theme_file_unknown_palette_ref() {
        let toml_str = r##"
[meta]
base_theme = "codex"

[colors]
recording = "nonexistent"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        let err = resolve_theme_file_err_or_panic(&file);
        assert_eq!(err, ThemeFileError::UnknownPaletteRef("nonexistent".into()));
    }

    #[test]
    fn resolve_theme_file_invalid_hex() {
        let toml_str = r##"
[meta]
base_theme = "codex"

[colors]
recording = "#ZZZZZZ"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        let err = resolve_theme_file_err_or_panic(&file);
        assert_eq!(err, ThemeFileError::InvalidHex("#ZZZZZZ".into()));
    }

    #[test]
    fn resolve_theme_file_unknown_base_theme() {
        let toml_str = r##"
[meta]
base_theme = "nosuchtheme"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        let err = resolve_theme_file_err_or_panic(&file);
        assert_eq!(err, ThemeFileError::UnknownBaseTheme("nosuchtheme".into()));
    }

    #[test]
    fn resolve_theme_file_border_style() {
        let toml_str = r##"
[meta]
base_theme = "codex"

[borders]
style = "heavy"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        let resolved = resolve_theme_file_or_panic(&file);
        assert_eq!(resolved.borders, BORDER_HEAVY);
    }

    #[test]
    fn resolve_theme_file_indicators() {
        let toml_str = r##"
[meta]
base_theme = "codex"

[indicators]
rec = "X"
auto = "Y"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        let resolved = resolve_theme_file_or_panic(&file);
        assert_eq!(resolved.indicator_rec, "X");
        assert_eq!(resolved.indicator_auto, "Y");
    }

    #[test]
    fn export_roundtrip() {
        let codex_resolved = palette_to_resolved(&Theme::Codex.colors());
        let toml_str = export_theme_file(&codex_resolved, Some("Codex Export"), Some("codex"));

        // Parse back.
        let file = parse_theme_file_or_panic(&toml_str);
        let re_resolved = resolve_theme_file_or_panic(&file);

        // Color values should match (for Rgb-representable fields).
        assert_eq!(re_resolved.recording, codex_resolved.recording);
        assert_eq!(re_resolved.processing, codex_resolved.processing);
        assert_eq!(re_resolved.success, codex_resolved.success);
        assert_eq!(re_resolved.borders, codex_resolved.borders);
        assert_eq!(re_resolved.indicator_rec, codex_resolved.indicator_rec);
        assert_eq!(re_resolved.glyph_set, codex_resolved.glyph_set);
    }

    #[test]
    fn validate_warns_on_unused_palette() {
        let toml_str = r##"
[meta]
base_theme = "codex"

[palette]
red = "#ff0000"
unused_blue = "#0000ff"

[colors]
recording = "red"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        let warnings = validate_theme_file(&file);
        assert!(warnings.iter().any(|w| matches!(
            w,
            ThemeFileWarning::UnusedPaletteEntry(key) if key == "unused_blue"
        )));
    }

    #[test]
    fn parse_malformed_toml() {
        let bad = "this is not valid toml [[[";
        let result = toml::from_str::<ThemeFile>(bad);
        assert!(result.is_err());
    }

    #[test]
    fn resolve_theme_file_glyphs_and_spinner() {
        let toml_str = r##"
[meta]
base_theme = "codex"

[glyphs]
set = "ascii"

[spinner]
style = "dots"

[voice_scene]
style = "pulse"

[progress]
bar_family = "compact"
"##;
        let file = parse_theme_file_or_panic(toml_str);
        let resolved = resolve_theme_file_or_panic(&file);
        assert_eq!(resolved.glyph_set, GlyphSet::Ascii);
        assert_eq!(resolved.spinner_style, SpinnerStyle::Dots);
        assert_eq!(resolved.voice_scene_style, VoiceSceneStyle::Pulse);
        assert_eq!(resolved.progress_bar_family, ProgressBarFamily::Compact);
    }
}
