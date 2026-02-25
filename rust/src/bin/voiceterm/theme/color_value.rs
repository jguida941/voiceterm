//! Runtime color model so themes can be edited without recompilation.
//!
//! Introduces `Rgb`, `ColorValue`, and `ResolvedThemeColors` that can produce
//! ANSI escape sequences on demand, bridging to the existing `&'static str`
//! rendering pipeline via string interning (`Box::leak`).

use super::{BorderSet, GlyphSet, ProgressBarFamily, SpinnerStyle, ThemeColors, VoiceSceneStyle};

// ---------------------------------------------------------------------------
// Rgb
// ---------------------------------------------------------------------------

/// 24-bit RGB color.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) struct Rgb {
    pub(crate) r: u8,
    pub(crate) g: u8,
    pub(crate) b: u8,
}

impl Rgb {
    /// Parse `#RRGGBB` (case-insensitive, leading `#` required).
    #[must_use]
    pub(crate) fn from_hex(hex: &str) -> Option<Self> {
        let hex = hex.strip_prefix('#')?;
        if hex.len() != 6 {
            return None;
        }
        let r = u8::from_str_radix(&hex[0..2], 16).ok()?;
        let g = u8::from_str_radix(&hex[2..4], 16).ok()?;
        let b = u8::from_str_radix(&hex[4..6], 16).ok()?;
        Some(Self { r, g, b })
    }

    /// Serialize to `#rrggbb` (lowercase).
    #[must_use]
    pub(crate) fn to_hex(self) -> String {
        format!("#{:02x}{:02x}{:02x}", self.r, self.g, self.b)
    }

    /// ANSI 24-bit foreground escape: `\x1b[38;2;R;G;Bm`.
    #[must_use]
    pub(crate) fn to_fg_escape(self) -> String {
        format!("\x1b[38;2;{};{};{}m", self.r, self.g, self.b)
    }

    /// ANSI 24-bit background escape: `\x1b[48;2;R;G;Bm`.
    #[must_use]
    #[cfg(test)]
    pub(crate) fn to_bg_escape(self) -> String {
        format!("\x1b[48;2;{};{};{}m", self.r, self.g, self.b)
    }
}

// ---------------------------------------------------------------------------
// ColorValue
// ---------------------------------------------------------------------------

/// A color that can be resolved to an ANSI escape sequence at runtime.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) enum ColorValue {
    /// 24-bit true color.
    Rgb(Rgb),
    /// Standard ANSI 16-color code (e.g. 31 for red, 91 for bright red).
    Ansi16(u8),
    /// Reset sequence `\x1b[0m`.
    Reset,
    /// Empty string — no color applied.
    Empty,
}

impl ColorValue {
    /// Produce the ANSI escape sequence for this color value.
    #[must_use]
    pub(crate) fn to_escape(self) -> String {
        match self {
            Self::Rgb(rgb) => rgb.to_fg_escape(),
            Self::Ansi16(code) => format!("\x1b[{code}m"),
            Self::Reset => "\x1b[0m".to_string(),
            Self::Empty => String::new(),
        }
    }
}

// ---------------------------------------------------------------------------
// ANSI escape parsing
// ---------------------------------------------------------------------------

/// Parse an existing ANSI escape string back into a `ColorValue`.
///
/// Handles:
/// - `""` → `Empty`
/// - `\x1b[0m` → `Reset`
/// - `\x1b[38;2;R;G;Bm` → `Rgb`
/// - `\x1b[48;2;R;G;Bm` → `Rgb` (background, stored as Rgb for editing)
/// - `\x1b[Nm` → `Ansi16(N)`
#[must_use]
pub(crate) fn parse_ansi_escape_to_color_value(escape: &str) -> Option<ColorValue> {
    if escape.is_empty() {
        return Some(ColorValue::Empty);
    }
    if escape == "\x1b[0m" {
        return Some(ColorValue::Reset);
    }

    // Strip ESC[ prefix and trailing 'm'
    let inner = escape.strip_prefix("\x1b[")?.strip_suffix('m')?;

    let parts: Vec<&str> = inner.split(';').collect();
    match parts.as_slice() {
        // 24-bit: 38;2;R;G;B or 48;2;R;G;B
        [mode, "2", r, g, b] if *mode == "38" || *mode == "48" => {
            let r = r.parse::<u8>().ok()?;
            let g = g.parse::<u8>().ok()?;
            let b = b.parse::<u8>().ok()?;
            Some(ColorValue::Rgb(Rgb { r, g, b }))
        }
        // ANSI 16-color: single number
        [code] => {
            let code = code.parse::<u8>().ok()?;
            Some(ColorValue::Ansi16(code))
        }
        _ => None,
    }
}

// ---------------------------------------------------------------------------
// ResolvedThemeColors
// ---------------------------------------------------------------------------

/// Same semantic fields as `ThemeColors` but with runtime-editable `ColorValue`
/// and owned `String` for indicator fields.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct ResolvedThemeColors {
    pub(crate) recording: ColorValue,
    pub(crate) processing: ColorValue,
    pub(crate) success: ColorValue,
    pub(crate) warning: ColorValue,
    pub(crate) error: ColorValue,
    pub(crate) info: ColorValue,
    pub(crate) reset: ColorValue,
    pub(crate) dim: ColorValue,
    pub(crate) bg_primary: ColorValue,
    pub(crate) bg_secondary: ColorValue,
    pub(crate) border: ColorValue,
    pub(crate) borders: BorderSet,
    pub(crate) indicator_rec: String,
    pub(crate) indicator_auto: String,
    pub(crate) indicator_manual: String,
    pub(crate) indicator_idle: String,
    pub(crate) indicator_processing: String,
    pub(crate) indicator_responding: String,
    pub(crate) glyph_set: GlyphSet,
    pub(crate) spinner_style: SpinnerStyle,
    pub(crate) voice_scene_style: VoiceSceneStyle,
    pub(crate) progress_bar_family: ProgressBarFamily,
}

impl ResolvedThemeColors {
    /// Convert to the legacy `ThemeColors` using string interning (`Box::leak`).
    ///
    /// Each leaked string is ~20-60 bytes. With ~16 color fields this costs
    /// roughly 200-400 bytes per theme conversion — negligible for the rare
    /// event of applying a user theme.
    #[must_use]
    pub(crate) fn to_legacy_theme_colors(&self) -> ThemeColors {
        ThemeColors {
            recording: intern_string(&self.recording.to_escape()),
            processing: intern_string(&self.processing.to_escape()),
            success: intern_string(&self.success.to_escape()),
            warning: intern_string(&self.warning.to_escape()),
            error: intern_string(&self.error.to_escape()),
            info: intern_string(&self.info.to_escape()),
            reset: intern_string(&self.reset.to_escape()),
            dim: intern_string(&self.dim.to_escape()),
            bg_primary: intern_string(&self.bg_primary.to_escape()),
            bg_secondary: intern_string(&self.bg_secondary.to_escape()),
            border: intern_string(&self.border.to_escape()),
            borders: self.borders,
            indicator_rec: intern_string(&self.indicator_rec),
            indicator_auto: intern_string(&self.indicator_auto),
            indicator_manual: intern_string(&self.indicator_manual),
            indicator_idle: intern_string(&self.indicator_idle),
            indicator_processing: intern_string(&self.indicator_processing),
            indicator_responding: intern_string(&self.indicator_responding),
            glyph_set: self.glyph_set,
            spinner_style: self.spinner_style,
            voice_scene_style: self.voice_scene_style,
            progress_bar_family: self.progress_bar_family,
        }
    }
}

/// Intern a string to `&'static str` via `Box::leak`.
///
/// This is intentionally leaked memory — each call allocates a small heap
/// buffer that lives for the remainder of the process. Only used when
/// converting user-edited themes to the legacy `ThemeColors` representation.
fn intern_string(s: &str) -> &'static str {
    if s.is_empty() {
        return "";
    }
    // Common constant — avoid allocation.
    if s == "\x1b[0m" {
        return "\x1b[0m";
    }
    Box::leak(s.to_string().into_boxed_str())
}

// ---------------------------------------------------------------------------
// Palette conversion
// ---------------------------------------------------------------------------

/// Convert a built-in `ThemeColors` palette into editable `ResolvedThemeColors`.
#[must_use]
pub(crate) fn palette_to_resolved(palette: &ThemeColors) -> ResolvedThemeColors {
    let parse = |s: &str| -> ColorValue {
        parse_ansi_escape_to_color_value(s).unwrap_or(ColorValue::Empty)
    };

    ResolvedThemeColors {
        recording: parse(palette.recording),
        processing: parse(palette.processing),
        success: parse(palette.success),
        warning: parse(palette.warning),
        error: parse(palette.error),
        info: parse(palette.info),
        reset: parse(palette.reset),
        dim: parse(palette.dim),
        bg_primary: parse(palette.bg_primary),
        bg_secondary: parse(palette.bg_secondary),
        border: parse(palette.border),
        borders: palette.borders,
        indicator_rec: palette.indicator_rec.to_string(),
        indicator_auto: palette.indicator_auto.to_string(),
        indicator_manual: palette.indicator_manual.to_string(),
        indicator_idle: palette.indicator_idle.to_string(),
        indicator_processing: palette.indicator_processing.to_string(),
        indicator_responding: palette.indicator_responding.to_string(),
        glyph_set: palette.glyph_set,
        spinner_style: palette.spinner_style,
        voice_scene_style: palette.voice_scene_style,
        progress_bar_family: palette.progress_bar_family,
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::theme::{
        THEME_ANSI, THEME_CATPPUCCIN, THEME_CHATGPT, THEME_CLAUDE, THEME_CODEX, THEME_CORAL,
        THEME_DRACULA, THEME_GRUVBOX, THEME_NONE, THEME_NORD, THEME_TOKYONIGHT,
    };

    fn rgb_from_hex_or_panic(hex: &str) -> Rgb {
        match Rgb::from_hex(hex) {
            Some(rgb) => rgb,
            None => panic!("failed to parse rgb hex {hex}"),
        }
    }

    fn parse_escape_or_panic(escape: &str) -> ColorValue {
        match parse_ansi_escape_to_color_value(escape) {
            Some(value) => value,
            None => panic!("failed to parse ansi escape {escape}"),
        }
    }

    #[test]
    fn rgb_from_hex_valid() {
        let rgb = rgb_from_hex_or_panic("#d97757");
        assert_eq!(
            rgb,
            Rgb {
                r: 217,
                g: 119,
                b: 87
            }
        );
    }

    #[test]
    fn rgb_from_hex_uppercase() {
        let rgb = rgb_from_hex_or_panic("#FF00AA");
        assert_eq!(
            rgb,
            Rgb {
                r: 255,
                g: 0,
                b: 170
            }
        );
    }

    #[test]
    fn rgb_from_hex_rejects_invalid() {
        assert!(Rgb::from_hex("d97757").is_none()); // missing #
        assert!(Rgb::from_hex("#d9775").is_none()); // too short
        assert!(Rgb::from_hex("#d97757ff").is_none()); // too long
        assert!(Rgb::from_hex("#ZZZZZZ").is_none()); // not hex
        assert!(Rgb::from_hex("").is_none());
    }

    #[test]
    fn rgb_hex_roundtrip() {
        let rgb = Rgb {
            r: 111,
            g: 177,
            b: 255,
        };
        assert_eq!(rgb.to_hex(), "#6fb1ff");
        assert_eq!(Rgb::from_hex(&rgb.to_hex()), Some(rgb));
    }

    #[test]
    fn rgb_to_fg_escape_matches_codex_recording() {
        let rgb = rgb_from_hex_or_panic("#6fb1ff");
        assert_eq!(rgb.to_fg_escape(), "\x1b[38;2;111;177;255m");
        assert_eq!(rgb.to_fg_escape(), THEME_CODEX.recording);
    }

    #[test]
    fn rgb_to_bg_escape() {
        let rgb = Rgb {
            r: 10,
            g: 20,
            b: 30,
        };
        assert_eq!(rgb.to_bg_escape(), "\x1b[48;2;10;20;30m");
    }

    #[test]
    fn rgb_claude_recording_roundtrip() {
        // THEME_CLAUDE.recording == "\x1b[38;2;217;119;87m" == #d97757
        let parsed = parse_escape_or_panic(THEME_CLAUDE.recording);
        let ColorValue::Rgb(rgb) = parsed else {
            panic!("expected Rgb, got {parsed:?}");
        };
        assert_eq!(rgb.to_hex(), "#d97757");
        assert_eq!(rgb.to_fg_escape(), THEME_CLAUDE.recording);
    }

    #[test]
    fn color_value_escape_roundtrips() {
        let cases: &[(ColorValue, &str)] = &[
            (
                ColorValue::Rgb(Rgb {
                    r: 255,
                    g: 0,
                    b: 128,
                }),
                "\x1b[38;2;255;0;128m",
            ),
            (ColorValue::Ansi16(91), "\x1b[91m"),
            (ColorValue::Reset, "\x1b[0m"),
            (ColorValue::Empty, ""),
        ];
        for (cv, expected) in cases {
            assert_eq!(cv.to_escape(), *expected, "for {cv:?}");
        }
    }

    #[test]
    fn parse_ansi_escape_empty() {
        assert_eq!(
            parse_ansi_escape_to_color_value(""),
            Some(ColorValue::Empty)
        );
    }

    #[test]
    fn parse_ansi_escape_reset() {
        assert_eq!(
            parse_ansi_escape_to_color_value("\x1b[0m"),
            Some(ColorValue::Reset)
        );
    }

    #[test]
    fn parse_ansi_escape_ansi16() {
        assert_eq!(
            parse_ansi_escape_to_color_value("\x1b[91m"),
            Some(ColorValue::Ansi16(91))
        );
        assert_eq!(
            parse_ansi_escape_to_color_value("\x1b[33m"),
            Some(ColorValue::Ansi16(33))
        );
    }

    #[test]
    fn parse_ansi_escape_truecolor_fg() {
        assert_eq!(
            parse_ansi_escape_to_color_value("\x1b[38;2;111;177;255m"),
            Some(ColorValue::Rgb(Rgb {
                r: 111,
                g: 177,
                b: 255
            }))
        );
    }

    #[test]
    fn parse_ansi_escape_truecolor_bg() {
        assert_eq!(
            parse_ansi_escape_to_color_value("\x1b[48;2;10;20;30m"),
            Some(ColorValue::Rgb(Rgb {
                r: 10,
                g: 20,
                b: 30
            }))
        );
    }

    #[test]
    fn parse_ansi_escape_rejects_garbage() {
        assert!(parse_ansi_escape_to_color_value("hello").is_none());
        assert!(parse_ansi_escape_to_color_value("\x1b[m").is_none());
        assert!(parse_ansi_escape_to_color_value("\x1b[38;2;999;0;0m").is_none());
    }

    #[test]
    fn all_palettes_parse_via_palette_to_resolved() {
        let palettes: &[(&str, &ThemeColors)] = &[
            ("coral", &THEME_CORAL),
            ("claude", &THEME_CLAUDE),
            ("codex", &THEME_CODEX),
            ("chatgpt", &THEME_CHATGPT),
            ("catppuccin", &THEME_CATPPUCCIN),
            ("dracula", &THEME_DRACULA),
            ("nord", &THEME_NORD),
            ("tokyonight", &THEME_TOKYONIGHT),
            ("gruvbox", &THEME_GRUVBOX),
            ("ansi", &THEME_ANSI),
            ("none", &THEME_NONE),
        ];

        for (name, palette) in palettes {
            let resolved = palette_to_resolved(palette);
            // Verify no field ended up as a spurious Empty where the original had content.
            if !palette.recording.is_empty() {
                assert_ne!(
                    resolved.recording,
                    ColorValue::Empty,
                    "{name}: recording should not be Empty"
                );
            }
            if !palette.reset.is_empty() {
                assert_eq!(
                    resolved.reset,
                    ColorValue::Reset,
                    "{name}: reset should be Reset"
                );
            }
        }
    }

    #[test]
    fn resolved_to_legacy_roundtrip() {
        let resolved = palette_to_resolved(&THEME_CODEX);
        let legacy = resolved.to_legacy_theme_colors();

        // Color escapes should match exactly.
        assert_eq!(legacy.recording, THEME_CODEX.recording);
        assert_eq!(legacy.processing, THEME_CODEX.processing);
        assert_eq!(legacy.success, THEME_CODEX.success);
        assert_eq!(legacy.warning, THEME_CODEX.warning);
        assert_eq!(legacy.error, THEME_CODEX.error);
        assert_eq!(legacy.info, THEME_CODEX.info);
        assert_eq!(legacy.reset, THEME_CODEX.reset);
        assert_eq!(legacy.dim, THEME_CODEX.dim);
        assert_eq!(legacy.border, THEME_CODEX.border);
        assert_eq!(legacy.borders, THEME_CODEX.borders);
        assert_eq!(legacy.indicator_rec, THEME_CODEX.indicator_rec);
        assert_eq!(legacy.indicator_auto, THEME_CODEX.indicator_auto);
        assert_eq!(legacy.glyph_set, THEME_CODEX.glyph_set);
        assert_eq!(legacy.spinner_style, THEME_CODEX.spinner_style);
    }

    #[test]
    fn resolved_to_legacy_roundtrip_all_palettes() {
        let palettes: &[(&str, &ThemeColors)] = &[
            ("coral", &THEME_CORAL),
            ("claude", &THEME_CLAUDE),
            ("codex", &THEME_CODEX),
            ("chatgpt", &THEME_CHATGPT),
            ("catppuccin", &THEME_CATPPUCCIN),
            ("dracula", &THEME_DRACULA),
            ("nord", &THEME_NORD),
            ("tokyonight", &THEME_TOKYONIGHT),
            ("gruvbox", &THEME_GRUVBOX),
            ("ansi", &THEME_ANSI),
            ("none", &THEME_NONE),
        ];

        for (name, palette) in palettes {
            let resolved = palette_to_resolved(palette);
            let legacy = resolved.to_legacy_theme_colors();
            assert_eq!(
                legacy.recording, palette.recording,
                "{name}: recording mismatch"
            );
            assert_eq!(
                legacy.processing, palette.processing,
                "{name}: processing mismatch"
            );
            assert_eq!(legacy.success, palette.success, "{name}: success mismatch");
            assert_eq!(legacy.reset, palette.reset, "{name}: reset mismatch");
            assert_eq!(legacy.dim, palette.dim, "{name}: dim mismatch");
            assert_eq!(legacy.border, palette.border, "{name}: border mismatch");
            assert_eq!(legacy.borders, palette.borders, "{name}: borders mismatch");
            assert_eq!(
                legacy.indicator_rec, palette.indicator_rec,
                "{name}: indicator_rec mismatch"
            );
            assert_eq!(
                legacy.glyph_set, palette.glyph_set,
                "{name}: glyph_set mismatch"
            );
        }
    }

    #[test]
    fn intern_string_common_cases() {
        // Empty string returns static empty
        let empty = intern_string("");
        assert_eq!(empty, "");
        assert!(std::ptr::eq(empty, ""));

        // Reset returns known constant
        let reset = intern_string("\x1b[0m");
        assert_eq!(reset, "\x1b[0m");
    }

    #[test]
    fn rgb_arbitrary_hex_roundtrip() {
        // Property-like: several arbitrary values round-trip through hex and escape.
        let test_colors = [
            (0u8, 0u8, 0u8),
            (255, 255, 255),
            (128, 64, 32),
            (1, 2, 3),
            (254, 253, 252),
        ];
        for (r, g, b) in test_colors {
            let rgb = Rgb { r, g, b };
            let hex = rgb.to_hex();
            let back = rgb_from_hex_or_panic(&hex);
            assert_eq!(rgb, back, "hex roundtrip failed for ({r},{g},{b})");

            let escape = rgb.to_fg_escape();
            let parsed = parse_escape_or_panic(&escape);
            assert_eq!(
                parsed,
                ColorValue::Rgb(rgb),
                "escape roundtrip failed for ({r},{g},{b})"
            );
        }
    }
}
