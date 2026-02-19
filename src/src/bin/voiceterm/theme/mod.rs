//! Theme registry so users can switch visual style without changing behavior.
//!
//! Provides predefined color palettes that can be selected via CLI flags.

mod borders;
#[allow(dead_code)]
pub(crate) mod capability_matrix;
mod colors;
#[allow(dead_code)]
pub(crate) mod dependency_baseline;
mod detect;
mod palettes;
#[allow(dead_code)]
pub(crate) mod rule_profile;
mod style_pack;
mod style_schema;
#[allow(dead_code)]
pub(crate) mod texture_profile;
#[allow(dead_code)]
pub(crate) mod widget_pack;

pub use borders::{BorderSet, BORDER_DOUBLE, BORDER_HEAVY, BORDER_ROUNDED, BORDER_SINGLE};
#[allow(unused_imports)]
pub use borders::{BORDER_DOTTED, BORDER_NONE};
pub use colors::{GlyphSet, ThemeColors};
pub use palettes::{
    THEME_ANSI, THEME_CATPPUCCIN, THEME_CHATGPT, THEME_CLAUDE, THEME_CODEX, THEME_CORAL,
    THEME_DRACULA, THEME_GRUVBOX, THEME_NONE, THEME_NORD, THEME_TOKYONIGHT,
};

use self::{
    detect::is_warp_terminal,
    style_pack::{locked_style_pack_theme, resolve_theme_colors},
};

/// Default processing spinner frames used by Theme Studio-resolved surfaces.
pub(crate) const PROCESSING_SPINNER_BRAILLE: &[&str] =
    &["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

/// Waveform bars for HUD sparkline rendering.
pub(crate) const WAVEFORM_BARS_UNICODE: &[char; 8] = &['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
/// ASCII-safe waveform bars for fallback terminals.
pub(crate) const WAVEFORM_BARS_ASCII: &[char; 8] = &['.', ':', '-', '=', '+', '*', '#', '@'];

/// Progress bar partial fill characters (empty -> full).
pub(crate) const PROGRESS_PARTIAL_UNICODE: &[char; 9] =
    &['░', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█'];
/// ASCII-safe partial fill characters.
pub(crate) const PROGRESS_PARTIAL_ASCII: &[char; 9] =
    &['-', '.', ':', '-', '=', '+', '*', '#', '#'];

/// Resolved glyph profile for progress rendering surfaces.
#[derive(Debug, Clone, Copy)]
pub(crate) struct ProgressGlyphProfile {
    pub(crate) bar_filled: char,
    pub(crate) bar_empty: char,
    pub(crate) blocks_filled: char,
    pub(crate) blocks_empty: char,
    pub(crate) partial: &'static [char; 9],
    pub(crate) bouncing_fill: char,
}

/// Available color themes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum Theme {
    /// Default coral/red theme (matches existing TUI)
    #[default]
    Coral,
    /// Claude warm neutral theme (Anthropic-inspired)
    Claude,
    /// Codex cool blue theme (neutral, OpenAI-style)
    Codex,
    /// ChatGPT emerald theme (OpenAI ChatGPT brand)
    ChatGpt,
    /// Catppuccin Mocha - pastel dark theme
    Catppuccin,
    /// Dracula - high contrast dark theme
    Dracula,
    /// Nord - arctic blue-gray theme
    Nord,
    /// Tokyo Night - elegant purple/blue dark theme
    TokyoNight,
    /// Gruvbox - warm retro earthy colors
    Gruvbox,
    /// ANSI 16-color fallback for older terminals
    Ansi,
    /// No colors - plain text
    None,
}

impl Theme {
    /// Parse theme name from string.
    pub fn from_name(name: &str) -> Option<Self> {
        match name.to_lowercase().as_str() {
            "coral" | "default" => Some(Self::Coral),
            "claude" | "anthropic" => Some(Self::Claude),
            "codex" => Some(Self::Codex),
            "chatgpt" | "gpt" | "openai" => Some(Self::ChatGpt),
            "catppuccin" | "mocha" => Some(Self::Catppuccin),
            "dracula" => Some(Self::Dracula),
            "nord" => Some(Self::Nord),
            "tokyonight" | "tokyo-night" | "tokyo" => Some(Self::TokyoNight),
            "gruvbox" | "gruv" => Some(Self::Gruvbox),
            "ansi" | "ansi16" | "basic" => Some(Self::Ansi),
            "none" | "plain" => Some(Self::None),
            _ => None,
        }
    }

    /// Get the color palette for this theme.
    pub fn colors(&self) -> ThemeColors {
        let mut colors = resolve_theme_colors(*self);
        if is_warp_terminal() {
            colors.bg_primary = "";
            colors.bg_secondary = "";
        }
        colors
    }

    /// List all available theme names.
    #[allow(dead_code)]
    pub fn available() -> &'static [&'static str] {
        &[
            "chatgpt",
            "claude",
            "codex",
            "coral",
            "catppuccin",
            "dracula",
            "gruvbox",
            "nord",
            "tokyonight",
            "ansi",
            "none",
        ]
    }

    /// Check if this theme uses truecolor (24-bit RGB).
    pub fn is_truecolor(&self) -> bool {
        matches!(
            self,
            Self::Claude
                | Self::Codex
                | Self::ChatGpt
                | Self::Catppuccin
                | Self::Dracula
                | Self::Nord
                | Self::TokyoNight
                | Self::Gruvbox
        )
    }

    /// Get a fallback theme for terminals without truecolor support.
    pub fn fallback_for_ansi(&self) -> Self {
        if self.is_truecolor() {
            Self::Ansi
        } else {
            *self
        }
    }
}

/// Return the active style-pack base-theme lock, if present.
#[must_use]
pub(crate) fn style_pack_theme_lock() -> Option<Theme> {
    locked_style_pack_theme()
}

/// Convert a theme's base mode indicator into its filled recording variant.
///
/// This keeps recording visuals in the same symbol family instead of switching
/// to an unrelated glyph shape.
#[must_use]
pub fn filled_indicator(symbol: &'static str) -> &'static str {
    match symbol {
        "◎" => "◉",
        "◍" => "◉",
        "◇" => "◆",
        "⊙" => "◉",
        "◈" => "◆",
        "☆" => "★",
        "▢" => "▣",
        "○" => "●",
        "◌" => "●",
        "·" => "•",
        "□" => "■",
        "-" => "•",
        "▸" => "▶",
        "▹" => "▶",
        "▷" => "▶",
        _ => symbol,
    }
}

/// Resolve processing indicator glyph for a frame, honoring theme/style-pack overrides.
///
/// If the active theme keeps the default processing indicator (`◐`), use the
/// animated braille spinner family. If a style-pack override changed the
/// processing indicator glyph, preserve that exact glyph and disable animation.
#[must_use]
pub(crate) fn processing_spinner_symbol(colors: &ThemeColors, frame: usize) -> &'static str {
    if colors.indicator_processing == "◐" {
        let idx = frame % PROCESSING_SPINNER_BRAILLE.len();
        return PROCESSING_SPINNER_BRAILLE[idx];
    }
    colors.indicator_processing
}

/// Resolve HUD queue label glyph by selected icon pack.
#[must_use]
pub(crate) fn hud_queue_icon(glyph_set: GlyphSet) -> &'static str {
    match glyph_set {
        GlyphSet::Unicode => "▤",
        GlyphSet::Ascii => "Q",
    }
}

/// Resolve HUD latency label glyph by selected icon pack.
#[must_use]
pub(crate) fn hud_latency_icon(glyph_set: GlyphSet) -> &'static str {
    match glyph_set {
        GlyphSet::Unicode => "◷",
        GlyphSet::Ascii => "T",
    }
}

/// Resolve sparkline waveform glyph set for meter/latency bars.
#[must_use]
pub(crate) fn waveform_bars(glyph_set: GlyphSet) -> &'static [char; 8] {
    match glyph_set {
        GlyphSet::Unicode => WAVEFORM_BARS_UNICODE,
        GlyphSet::Ascii => WAVEFORM_BARS_ASCII,
    }
}

/// Resolve progress-glyph family for bars/spinners.
#[must_use]
pub(crate) fn progress_glyph_profile(glyph_set: GlyphSet) -> ProgressGlyphProfile {
    match glyph_set {
        GlyphSet::Unicode => ProgressGlyphProfile {
            bar_filled: '█',
            bar_empty: '░',
            blocks_filled: '▓',
            blocks_empty: '░',
            partial: PROGRESS_PARTIAL_UNICODE,
            bouncing_fill: '=',
        },
        GlyphSet::Ascii => ProgressGlyphProfile {
            bar_filled: '=',
            bar_empty: '-',
            blocks_filled: '#',
            blocks_empty: '.',
            partial: PROGRESS_PARTIAL_ASCII,
            bouncing_fill: '=',
        },
    }
}

/// Resolve overlay separator glyph (between footer controls).
#[must_use]
pub(crate) fn overlay_separator(glyph_set: GlyphSet) -> &'static str {
    match glyph_set {
        GlyphSet::Unicode => "·",
        GlyphSet::Ascii => "|",
    }
}

/// Resolve overlay close button glyph.
#[must_use]
pub(crate) fn overlay_close_symbol(glyph_set: GlyphSet) -> char {
    match glyph_set {
        GlyphSet::Unicode => '×',
        GlyphSet::Ascii => 'x',
    }
}

/// Resolve overlay move-hint glyph cluster.
#[must_use]
pub(crate) fn overlay_move_hint(glyph_set: GlyphSet) -> &'static str {
    match glyph_set {
        GlyphSet::Unicode => "↑/↓",
        GlyphSet::Ascii => "up/down",
    }
}

/// Resolve selection marker glyph used by overlay menu rows.
#[must_use]
pub(crate) fn overlay_row_marker(glyph_set: GlyphSet) -> &'static str {
    match glyph_set {
        GlyphSet::Unicode => "▸",
        GlyphSet::Ascii => ">",
    }
}

/// Resolve slider track glyph used by settings rows.
#[must_use]
pub(crate) fn overlay_slider_track(glyph_set: GlyphSet) -> char {
    match glyph_set {
        GlyphSet::Unicode => '─',
        GlyphSet::Ascii => '-',
    }
}

/// Resolve slider knob glyph used by settings rows.
#[must_use]
pub(crate) fn overlay_slider_knob(glyph_set: GlyphSet) -> char {
    match glyph_set {
        GlyphSet::Unicode => '●',
        GlyphSet::Ascii => 'o',
    }
}

impl std::fmt::Display for Theme {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Coral => write!(f, "coral"),
            Self::Claude => write!(f, "claude"),
            Self::Codex => write!(f, "codex"),
            Self::ChatGpt => write!(f, "chatgpt"),
            Self::Catppuccin => write!(f, "catppuccin"),
            Self::Dracula => write!(f, "dracula"),
            Self::Nord => write!(f, "nord"),
            Self::TokyoNight => write!(f, "tokyonight"),
            Self::Gruvbox => write!(f, "gruvbox"),
            Self::Ansi => write!(f, "ansi"),
            Self::None => write!(f, "none"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{
        fs,
        path::{Path, PathBuf},
    };

    #[test]
    fn theme_from_name_parses_valid() {
        assert_eq!(Theme::from_name("coral"), Some(Theme::Coral));
        assert_eq!(Theme::from_name("claude"), Some(Theme::Claude));
        assert_eq!(Theme::from_name("anthropic"), Some(Theme::Claude));
        assert_eq!(Theme::from_name("codex"), Some(Theme::Codex));
        assert_eq!(Theme::from_name("chatgpt"), Some(Theme::ChatGpt));
        assert_eq!(Theme::from_name("gpt"), Some(Theme::ChatGpt));
        assert_eq!(Theme::from_name("openai"), Some(Theme::ChatGpt));
        assert_eq!(Theme::from_name("CATPPUCCIN"), Some(Theme::Catppuccin));
        assert_eq!(Theme::from_name("Dracula"), Some(Theme::Dracula));
        assert_eq!(Theme::from_name("nord"), Some(Theme::Nord));
        assert_eq!(Theme::from_name("ansi"), Some(Theme::Ansi));
        assert_eq!(Theme::from_name("ansi16"), Some(Theme::Ansi));
        assert_eq!(Theme::from_name("none"), Some(Theme::None));
        assert_eq!(Theme::from_name("default"), Some(Theme::Coral));
    }

    #[test]
    fn theme_from_name_supports_tokyo_and_gruv_aliases() {
        assert_eq!(Theme::from_name("tokyonight"), Some(Theme::TokyoNight));
        assert_eq!(Theme::from_name("tokyo-night"), Some(Theme::TokyoNight));
        assert_eq!(Theme::from_name("tokyo"), Some(Theme::TokyoNight));
        assert_eq!(Theme::from_name("gruvbox"), Some(Theme::Gruvbox));
        assert_eq!(Theme::from_name("gruv"), Some(Theme::Gruvbox));
    }

    #[test]
    fn theme_available_reports_full_theme_list() {
        assert_eq!(
            Theme::available(),
            &[
                "chatgpt",
                "claude",
                "codex",
                "coral",
                "catppuccin",
                "dracula",
                "gruvbox",
                "nord",
                "tokyonight",
                "ansi",
                "none",
            ]
        );
    }

    #[test]
    fn theme_is_truecolor() {
        assert!(!Theme::Coral.is_truecolor());
        assert!(Theme::Claude.is_truecolor());
        assert!(Theme::Codex.is_truecolor());
        assert!(Theme::ChatGpt.is_truecolor());
        assert!(Theme::Catppuccin.is_truecolor());
        assert!(Theme::Dracula.is_truecolor());
        assert!(Theme::Nord.is_truecolor());
        assert!(!Theme::Ansi.is_truecolor());
        assert!(!Theme::None.is_truecolor());
    }

    #[test]
    fn theme_fallback_for_ansi() {
        assert_eq!(Theme::Coral.fallback_for_ansi(), Theme::Coral);
        assert_eq!(Theme::Claude.fallback_for_ansi(), Theme::Ansi);
        assert_eq!(Theme::Codex.fallback_for_ansi(), Theme::Ansi);
        assert_eq!(Theme::ChatGpt.fallback_for_ansi(), Theme::Ansi);
        assert_eq!(Theme::Catppuccin.fallback_for_ansi(), Theme::Ansi);
        assert_eq!(Theme::Dracula.fallback_for_ansi(), Theme::Ansi);
        assert_eq!(Theme::None.fallback_for_ansi(), Theme::None);
    }

    #[test]
    fn theme_from_name_rejects_invalid() {
        assert_eq!(Theme::from_name("invalid"), None);
        assert_eq!(Theme::from_name(""), None);
    }

    #[test]
    fn theme_colors_returns_palette() {
        let colors = Theme::Coral.colors();
        assert!(colors.recording.contains("\x1b["));
        assert!(colors.reset.contains("\x1b[0m"));

        let none_colors = Theme::None.colors();
        assert!(none_colors.recording.is_empty());
    }

    #[test]
    fn theme_display_matches_name() {
        assert_eq!(format!("{}", Theme::Coral), "coral");
        assert_eq!(format!("{}", Theme::Claude), "claude");
        assert_eq!(format!("{}", Theme::Codex), "codex");
        assert_eq!(format!("{}", Theme::ChatGpt), "chatgpt");
        assert_eq!(format!("{}", Theme::Catppuccin), "catppuccin");
    }

    #[test]
    fn theme_has_expected_borders() {
        // Spot-check representative border styles for a few themes.
        assert_eq!(Theme::Coral.colors().borders.horizontal, '─'); // Single
        assert_eq!(Theme::Catppuccin.colors().borders.horizontal, '═'); // Double
        assert_eq!(Theme::Codex.colors().borders.horizontal, '═'); // Double
        assert_eq!(Theme::Dracula.colors().borders.horizontal, '━'); // Heavy
        assert_eq!(Theme::TokyoNight.colors().borders.horizontal, '━'); // Heavy
        assert_eq!(Theme::Nord.colors().borders.top_left, '╭'); // Rounded
        assert_eq!(Theme::Claude.colors().borders.top_left, '╭'); // Rounded
        assert_eq!(Theme::ChatGpt.colors().borders.top_left, '╭'); // Rounded
    }

    #[test]
    fn theme_has_indicators() {
        let colors = Theme::Coral.colors();
        assert!(!colors.indicator_rec.is_empty());
        assert!(!colors.indicator_auto.is_empty());
    }

    #[test]
    fn filled_indicator_keeps_symbol_family() {
        assert_eq!(filled_indicator("☆"), "★");
        assert_eq!(filled_indicator("▢"), "▣");
        assert_eq!(filled_indicator("◇"), "◆");
        assert_eq!(filled_indicator("◎"), "◉");
        assert_eq!(filled_indicator("▶"), "▶");
    }

    #[test]
    fn processing_spinner_symbol_uses_braille_for_default_processing_indicator() {
        let colors = Theme::Codex.colors();
        let indicator = processing_spinner_symbol(&colors, 3);
        assert_eq!(indicator, PROCESSING_SPINNER_BRAILLE[3]);
    }

    #[test]
    fn processing_spinner_symbol_preserves_theme_override_indicator() {
        let mut colors = Theme::Codex.colors();
        colors.indicator_processing = "~";
        assert_eq!(processing_spinner_symbol(&colors, 5), "~");
    }

    #[test]
    fn hud_icons_follow_glyph_set() {
        assert_eq!(hud_queue_icon(GlyphSet::Unicode), "▤");
        assert_eq!(hud_queue_icon(GlyphSet::Ascii), "Q");
        assert_eq!(hud_latency_icon(GlyphSet::Unicode), "◷");
        assert_eq!(hud_latency_icon(GlyphSet::Ascii), "T");
    }

    #[test]
    fn waveform_and_progress_profiles_follow_glyph_set() {
        let unicode = progress_glyph_profile(GlyphSet::Unicode);
        let ascii = progress_glyph_profile(GlyphSet::Ascii);
        assert_eq!(waveform_bars(GlyphSet::Unicode)[0], '▁');
        assert_eq!(waveform_bars(GlyphSet::Ascii)[0], '.');
        assert_eq!(unicode.bar_filled, '█');
        assert_eq!(ascii.bar_filled, '=');
    }

    #[test]
    fn overlay_chrome_glyphs_follow_glyph_set() {
        assert_eq!(overlay_separator(GlyphSet::Unicode), "·");
        assert_eq!(overlay_separator(GlyphSet::Ascii), "|");
        assert_eq!(overlay_close_symbol(GlyphSet::Unicode), '×');
        assert_eq!(overlay_close_symbol(GlyphSet::Ascii), 'x');
        assert_eq!(overlay_move_hint(GlyphSet::Unicode), "↑/↓");
        assert_eq!(overlay_move_hint(GlyphSet::Ascii), "up/down");
        assert_eq!(overlay_row_marker(GlyphSet::Unicode), "▸");
        assert_eq!(overlay_row_marker(GlyphSet::Ascii), ">");
        assert_eq!(overlay_slider_track(GlyphSet::Unicode), '─');
        assert_eq!(overlay_slider_track(GlyphSet::Ascii), '-');
        assert_eq!(overlay_slider_knob(GlyphSet::Unicode), '●');
        assert_eq!(overlay_slider_knob(GlyphSet::Ascii), 'o');
    }

    #[test]
    fn runtime_sources_do_not_bypass_theme_resolver_with_palette_constants() {
        const STYLE_CONSTANTS: &[&str] = &[
            "THEME_CORAL",
            "THEME_CLAUDE",
            "THEME_CODEX",
            "THEME_CHATGPT",
            "THEME_CATPPUCCIN",
            "THEME_DRACULA",
            "THEME_NORD",
            "THEME_TOKYONIGHT",
            "THEME_GRUVBOX",
            "THEME_ANSI",
            "THEME_NONE",
            "BORDER_SINGLE",
            "BORDER_ROUNDED",
            "BORDER_DOUBLE",
            "BORDER_HEAVY",
            "BORDER_NONE",
        ];
        const ALLOWED_FILES: &[&str] = &[
            "src/bin/voiceterm/theme/mod.rs",
            "src/bin/voiceterm/theme/borders.rs",
            "src/bin/voiceterm/theme/palettes.rs",
            "src/bin/voiceterm/theme/style_pack.rs",
            "src/bin/voiceterm/status_line/format.rs",
        ];

        let source_root = Path::new(env!("CARGO_MANIFEST_DIR")).join("src/bin/voiceterm");
        let mut violations = Vec::new();

        for path in collect_rust_files(&source_root) {
            let relative = normalize_relative_path(&path);
            if ALLOWED_FILES.contains(&relative.as_str()) {
                continue;
            }
            let source = fs::read_to_string(&path)
                .unwrap_or_else(|err| panic!("failed to read {relative}: {err}"));
            let offenders: Vec<&str> = STYLE_CONSTANTS
                .iter()
                .copied()
                .filter(|name| source.contains(name))
                .collect();
            if !offenders.is_empty() {
                violations.push(format!("{relative}: {}", offenders.join(", ")));
            }
        }

        assert!(
            violations.is_empty(),
            "style constants must stay behind theme resolver or explicit style-ownership surfaces:\n{}",
            violations.join("\n")
        );
    }

    fn collect_rust_files(root: &Path) -> Vec<PathBuf> {
        let mut files = Vec::new();
        let entries = fs::read_dir(root)
            .unwrap_or_else(|err| panic!("failed to scan {}: {err}", root.display()));
        for entry in entries {
            let entry = entry.unwrap_or_else(|err| {
                panic!("failed to read dir entry in {}: {err}", root.display())
            });
            let path = entry.path();
            if path.is_dir() {
                files.extend(collect_rust_files(&path));
            } else if path.extension().and_then(|ext| ext.to_str()) == Some("rs") {
                files.push(path);
            }
        }
        files.sort_unstable();
        files
    }

    fn normalize_relative_path(path: &Path) -> String {
        let root = Path::new(env!("CARGO_MANIFEST_DIR"));
        path.strip_prefix(root)
            .unwrap_or(path)
            .to_string_lossy()
            .replace('\\', "/")
    }
}
