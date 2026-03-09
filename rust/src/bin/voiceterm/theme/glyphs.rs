//! Glyph tables and resolver functions for theme-aware symbol rendering.
//!
//! Every visual glyph that adapts between Unicode and ASCII fallback lives here.
//! Consumers import through the parent `theme` module re-exports.

use super::colors::{GlyphSet, ProgressBarFamily, SpinnerStyle, ThemeColors};

// ---------------------------------------------------------------------------
// Spinner frame constants
// ---------------------------------------------------------------------------

/// Default processing spinner frames used by Theme Studio-resolved surfaces.
pub(crate) const PROCESSING_SPINNER_BRAILLE: &[&str] =
    &["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
/// Dot-based processing spinner frames.
pub(crate) const PROCESSING_SPINNER_DOTS: &[&str] = &["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"];
/// Line-based processing spinner frames.
pub(crate) const PROCESSING_SPINNER_LINE: &[&str] = &["-", "\\", "|", "/"];
/// Block-based processing spinner frames.
pub(crate) const PROCESSING_SPINNER_BLOCK: &[&str] = &["▖", "▘", "▝", "▗"];
/// ASCII-safe spinner frames used when explicit animation styles are selected.
pub(crate) const PROCESSING_SPINNER_ASCII: &[&str] = &[".", "o", "O", "o"];

// ---------------------------------------------------------------------------
// Waveform bar constants
// ---------------------------------------------------------------------------

/// Waveform bars for HUD sparkline rendering.
pub(crate) const WAVEFORM_BARS_UNICODE: &[char; 8] = &['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
/// ASCII-safe waveform bars for fallback terminals.
pub(crate) const WAVEFORM_BARS_ASCII: &[char; 8] = &['.', ':', '-', '=', '+', '*', '#', '@'];

// ---------------------------------------------------------------------------
// Progress glyph profile
// ---------------------------------------------------------------------------

/// Resolved glyph profile for progress rendering surfaces.
#[derive(Debug, Clone, Copy)]
pub(crate) struct ProgressGlyphProfile {
    pub(crate) bar_filled: char,
    pub(crate) bar_empty: char,
}

// ---------------------------------------------------------------------------
// GlyphTable generic resolver
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy)]
pub(super) struct GlyphTable<T: Copy> {
    unicode: T,
    ascii: T,
}

impl<T: Copy> GlyphTable<T> {
    const fn new(unicode: T, ascii: T) -> Self {
        Self { unicode, ascii }
    }

    const fn resolve(self, glyph_set: GlyphSet) -> T {
        match glyph_set {
            GlyphSet::Unicode => self.unicode,
            GlyphSet::Ascii => self.ascii,
        }
    }
}

// ---------------------------------------------------------------------------
// Glyph table constants
// ---------------------------------------------------------------------------

const HUD_QUEUE_ICON_TABLE: GlyphTable<&str> = GlyphTable::new("▤", "Q");
const HUD_LATENCY_ICON_TABLE: GlyphTable<&str> = GlyphTable::new("◷", "T");
const WAVEFORM_BARS_TABLE: GlyphTable<&[char; 8]> =
    GlyphTable::new(WAVEFORM_BARS_UNICODE, WAVEFORM_BARS_ASCII);
const OVERLAY_SEPARATOR_TABLE: GlyphTable<&str> = GlyphTable::new("·", "|");
const INLINE_SEPARATOR_TABLE: GlyphTable<&str> = GlyphTable::new("│", "|");
const OVERLAY_CLOSE_SYMBOL_TABLE: GlyphTable<char> = GlyphTable::new('×', 'x');
const OVERLAY_MOVE_HINT_TABLE: GlyphTable<&str> = GlyphTable::new("↑/↓", "up/down");
const OVERLAY_ROW_MARKER_TABLE: GlyphTable<&str> = GlyphTable::new("▸", ">");
const OVERLAY_SLIDER_TRACK_TABLE: GlyphTable<char> = GlyphTable::new('─', '-');
const OVERLAY_SLIDER_KNOB_TABLE: GlyphTable<char> = GlyphTable::new('●', 'o');

// Mode indicator glyphs (HUD voice-mode display).
const MODE_RECORDING_TABLE: GlyphTable<&str> = GlyphTable::new("●", "*");
const MODE_AUTO_TABLE: GlyphTable<&str> = GlyphTable::new("◉", "@");
const MODE_MANUAL_TABLE: GlyphTable<&str> = GlyphTable::new("○", ">");
const MODE_INSERT_TABLE: GlyphTable<&str> = GlyphTable::new("◐", "~");

// Toast severity icon glyphs (single-char for width-constrained prefix).
const SEVERITY_INFO_ICON_TABLE: GlyphTable<&str> = GlyphTable::new("ℹ", "i");
const SEVERITY_SUCCESS_ICON_TABLE: GlyphTable<&str> = GlyphTable::new("✓", "+");
const SEVERITY_WARNING_ICON_TABLE: GlyphTable<&str> = GlyphTable::new("⚠", "!");
const SEVERITY_ERROR_ICON_TABLE: GlyphTable<&str> = GlyphTable::new("✗", "x");

// Pulse dot glyphs (right panel level animation).
const PULSE_DOT_ACTIVE_TABLE: GlyphTable<char> = GlyphTable::new('•', '*');
const PULSE_DOT_INACTIVE_TABLE: GlyphTable<char> = GlyphTable::new('·', '.');

// Audio meter marker glyphs (calibration/waveform display).
const METER_PEAK_MARKER_TABLE: GlyphTable<char> = GlyphTable::new('│', '|');
const METER_THRESHOLD_MARKER_TABLE: GlyphTable<char> = GlyphTable::new('▲', '^');

// Heartbeat animation frames (status-line idle/recording pulse).
const HEARTBEAT_FRAMES_UNICODE: &[char] = &['·', '•', '●', '•'];
const HEARTBEAT_FRAMES_ASCII: &[char] = &['.', '*', 'O', '*'];
const HEARTBEAT_FRAMES_TABLE: GlyphTable<&[char]> =
    GlyphTable::new(HEARTBEAT_FRAMES_UNICODE, HEARTBEAT_FRAMES_ASCII);

// Transition pulse markers (state-change visual feedback).
const TRANSITION_PULSE_MARKERS_UNICODE: &[&str] = &["✦", "•"];
const TRANSITION_PULSE_MARKERS_ASCII: &[&str] = &["*", "*"];
const TRANSITION_PULSE_TABLE: GlyphTable<&[&str]> = GlyphTable::new(
    TRANSITION_PULSE_MARKERS_UNICODE,
    TRANSITION_PULSE_MARKERS_ASCII,
);

// ---------------------------------------------------------------------------
// Processing spinner resolver
// ---------------------------------------------------------------------------

/// Resolve processing indicator glyph for a frame, honoring theme/style-pack overrides.
///
/// If the active theme keeps the default processing indicator (`◐`), use the
/// animated braille spinner family. If a style-pack override changed the
/// processing indicator glyph, preserve that exact glyph and disable animation.
#[must_use]
pub(crate) fn processing_spinner_symbol(colors: &ThemeColors, frame: usize) -> &'static str {
    match colors.spinner_style {
        SpinnerStyle::Braille => match colors.glyph_set {
            GlyphSet::Unicode => {
                PROCESSING_SPINNER_BRAILLE[frame % PROCESSING_SPINNER_BRAILLE.len()]
            }
            GlyphSet::Ascii => PROCESSING_SPINNER_ASCII[frame % PROCESSING_SPINNER_ASCII.len()],
        },
        SpinnerStyle::Dots => match colors.glyph_set {
            GlyphSet::Unicode => PROCESSING_SPINNER_DOTS[frame % PROCESSING_SPINNER_DOTS.len()],
            GlyphSet::Ascii => PROCESSING_SPINNER_ASCII[frame % PROCESSING_SPINNER_ASCII.len()],
        },
        SpinnerStyle::Line => PROCESSING_SPINNER_LINE[frame % PROCESSING_SPINNER_LINE.len()],
        SpinnerStyle::Block => match colors.glyph_set {
            GlyphSet::Unicode => PROCESSING_SPINNER_BLOCK[frame % PROCESSING_SPINNER_BLOCK.len()],
            GlyphSet::Ascii => PROCESSING_SPINNER_ASCII[frame % PROCESSING_SPINNER_ASCII.len()],
        },
        SpinnerStyle::Theme => {
            if colors.indicator_processing == "◐" {
                match colors.glyph_set {
                    GlyphSet::Unicode => {
                        PROCESSING_SPINNER_BRAILLE[frame % PROCESSING_SPINNER_BRAILLE.len()]
                    }
                    GlyphSet::Ascii => {
                        PROCESSING_SPINNER_ASCII[frame % PROCESSING_SPINNER_ASCII.len()]
                    }
                }
            } else {
                colors.indicator_processing
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Glyph resolver functions
// ---------------------------------------------------------------------------

/// Resolve HUD queue label glyph by selected icon pack.
#[must_use]
pub(crate) fn hud_queue_icon(glyph_set: GlyphSet) -> &'static str {
    HUD_QUEUE_ICON_TABLE.resolve(glyph_set)
}

/// Resolve HUD latency label glyph by selected icon pack.
#[must_use]
pub(crate) fn hud_latency_icon(glyph_set: GlyphSet) -> &'static str {
    HUD_LATENCY_ICON_TABLE.resolve(glyph_set)
}

/// Resolve sparkline waveform glyph set for meter/latency bars.
#[must_use]
pub(crate) fn waveform_bars(glyph_set: GlyphSet) -> &'static [char; 8] {
    WAVEFORM_BARS_TABLE.resolve(glyph_set)
}

/// Resolve progress-glyph family for bars/spinners.
#[must_use]
pub(crate) fn progress_glyph_profile(colors: &ThemeColors) -> ProgressGlyphProfile {
    match (colors.progress_bar_family, colors.glyph_set) {
        (ProgressBarFamily::Theme | ProgressBarFamily::Bar, GlyphSet::Unicode) => {
            ProgressGlyphProfile {
                bar_filled: '█',
                bar_empty: '░',
            }
        }
        (ProgressBarFamily::Theme | ProgressBarFamily::Bar, GlyphSet::Ascii) => {
            ProgressGlyphProfile {
                bar_filled: '=',
                bar_empty: '-',
            }
        }
        (ProgressBarFamily::Compact, GlyphSet::Unicode) => ProgressGlyphProfile {
            bar_filled: '■',
            bar_empty: '·',
        },
        (ProgressBarFamily::Compact, GlyphSet::Ascii) => ProgressGlyphProfile {
            bar_filled: '#',
            bar_empty: '.',
        },
        (ProgressBarFamily::Blocks, GlyphSet::Unicode) => ProgressGlyphProfile {
            bar_filled: '▓',
            bar_empty: '░',
        },
        (ProgressBarFamily::Blocks, GlyphSet::Ascii) => ProgressGlyphProfile {
            bar_filled: '#',
            bar_empty: ' ',
        },
        (ProgressBarFamily::Braille, GlyphSet::Unicode) => ProgressGlyphProfile {
            bar_filled: '⣿',
            bar_empty: '⣀',
        },
        (ProgressBarFamily::Braille, GlyphSet::Ascii) => ProgressGlyphProfile {
            bar_filled: '=',
            bar_empty: '.',
        },
    }
}

/// Resolve overlay separator glyph (between footer controls).
#[must_use]
pub(crate) fn overlay_separator(glyph_set: GlyphSet) -> &'static str {
    OVERLAY_SEPARATOR_TABLE.resolve(glyph_set)
}

/// Resolve inline separator glyph (used by startup/banner rows).
#[must_use]
pub(crate) fn inline_separator(glyph_set: GlyphSet) -> &'static str {
    INLINE_SEPARATOR_TABLE.resolve(glyph_set)
}

/// Resolve overlay close button glyph.
#[must_use]
pub(crate) fn overlay_close_symbol(glyph_set: GlyphSet) -> char {
    OVERLAY_CLOSE_SYMBOL_TABLE.resolve(glyph_set)
}

/// Resolve overlay move-hint glyph cluster.
#[must_use]
pub(crate) fn overlay_move_hint(glyph_set: GlyphSet) -> &'static str {
    OVERLAY_MOVE_HINT_TABLE.resolve(glyph_set)
}

/// Resolve selection marker glyph used by overlay menu rows.
#[must_use]
pub(crate) fn overlay_row_marker(glyph_set: GlyphSet) -> &'static str {
    OVERLAY_ROW_MARKER_TABLE.resolve(glyph_set)
}

/// Resolve slider track glyph used by settings rows.
#[must_use]
pub(crate) fn overlay_slider_track(glyph_set: GlyphSet) -> char {
    OVERLAY_SLIDER_TRACK_TABLE.resolve(glyph_set)
}

/// Resolve slider knob glyph used by settings rows.
#[must_use]
pub(crate) fn overlay_slider_knob(glyph_set: GlyphSet) -> char {
    OVERLAY_SLIDER_KNOB_TABLE.resolve(glyph_set)
}

/// Resolve HUD mode indicator glyph for recording state.
#[must_use]
pub(crate) fn mode_recording_icon(glyph_set: GlyphSet) -> &'static str {
    MODE_RECORDING_TABLE.resolve(glyph_set)
}

/// Resolve HUD mode indicator glyph for auto mode.
#[must_use]
pub(crate) fn mode_auto_icon(glyph_set: GlyphSet) -> &'static str {
    MODE_AUTO_TABLE.resolve(glyph_set)
}

/// Resolve HUD mode indicator glyph for manual mode.
#[must_use]
pub(crate) fn mode_manual_icon(glyph_set: GlyphSet) -> &'static str {
    MODE_MANUAL_TABLE.resolve(glyph_set)
}

/// Resolve HUD mode indicator glyph for insert mode.
#[must_use]
pub(crate) fn mode_insert_icon(glyph_set: GlyphSet) -> &'static str {
    MODE_INSERT_TABLE.resolve(glyph_set)
}

/// Resolve toast severity icon for info level.
#[must_use]
pub(crate) fn severity_info_icon(glyph_set: GlyphSet) -> &'static str {
    SEVERITY_INFO_ICON_TABLE.resolve(glyph_set)
}

/// Resolve toast severity icon for success level.
#[must_use]
pub(crate) fn severity_success_icon(glyph_set: GlyphSet) -> &'static str {
    SEVERITY_SUCCESS_ICON_TABLE.resolve(glyph_set)
}

/// Resolve toast severity icon for warning level.
#[must_use]
pub(crate) fn severity_warning_icon(glyph_set: GlyphSet) -> &'static str {
    SEVERITY_WARNING_ICON_TABLE.resolve(glyph_set)
}

/// Resolve toast severity icon for error level.
#[must_use]
pub(crate) fn severity_error_icon(glyph_set: GlyphSet) -> &'static str {
    SEVERITY_ERROR_ICON_TABLE.resolve(glyph_set)
}

/// Resolve active pulse dot glyph for right panel level display.
#[must_use]
pub(crate) fn pulse_dot_active(glyph_set: GlyphSet) -> char {
    PULSE_DOT_ACTIVE_TABLE.resolve(glyph_set)
}

/// Resolve inactive pulse dot glyph for right panel level display.
#[must_use]
pub(crate) fn pulse_dot_inactive(glyph_set: GlyphSet) -> char {
    PULSE_DOT_INACTIVE_TABLE.resolve(glyph_set)
}

/// Resolve audio meter peak marker glyph.
#[must_use]
pub(crate) fn meter_peak_marker(glyph_set: GlyphSet) -> char {
    METER_PEAK_MARKER_TABLE.resolve(glyph_set)
}

/// Resolve audio meter threshold marker glyph.
#[must_use]
pub(crate) fn meter_threshold_marker(glyph_set: GlyphSet) -> char {
    METER_THRESHOLD_MARKER_TABLE.resolve(glyph_set)
}

/// Resolve heartbeat animation frame sequence by glyph set.
#[must_use]
pub(crate) fn heartbeat_frames(glyph_set: GlyphSet) -> &'static [char] {
    HEARTBEAT_FRAMES_TABLE.resolve(glyph_set)
}

/// Resolve transition pulse marker sequence by glyph set.
#[must_use]
pub(crate) fn transition_pulse_markers(glyph_set: GlyphSet) -> &'static [&'static str] {
    TRANSITION_PULSE_TABLE.resolve(glyph_set)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::theme::Theme;

    #[test]
    fn hud_icons_follow_glyph_set() {
        assert_eq!(hud_queue_icon(GlyphSet::Unicode), "▤");
        assert_eq!(hud_queue_icon(GlyphSet::Ascii), "Q");
        assert_eq!(hud_latency_icon(GlyphSet::Unicode), "◷");
        assert_eq!(hud_latency_icon(GlyphSet::Ascii), "T");
    }

    #[test]
    fn waveform_and_progress_profiles_follow_glyph_set() {
        let unicode_colors = Theme::Codex.colors();
        let unicode = progress_glyph_profile(&unicode_colors);
        let mut ascii_colors = Theme::Codex.colors();
        ascii_colors.glyph_set = GlyphSet::Ascii;
        let ascii = progress_glyph_profile(&ascii_colors);
        assert_eq!(waveform_bars(GlyphSet::Unicode)[0], '▁');
        assert_eq!(waveform_bars(GlyphSet::Ascii)[0], '.');
        assert_eq!(unicode.bar_filled, '█');
        assert_eq!(ascii.bar_filled, '=');
    }

    #[test]
    fn progress_profile_honors_explicit_family_override() {
        let mut colors = Theme::Codex.colors();
        colors.progress_bar_family = ProgressBarFamily::Compact;
        let compact = progress_glyph_profile(&colors);
        assert_eq!(compact.bar_filled, '■');

        colors.progress_bar_family = ProgressBarFamily::Braille;
        let braille = progress_glyph_profile(&colors);
        assert_eq!(braille.bar_filled, '⣿');
    }

    #[test]
    fn overlay_chrome_glyphs_follow_glyph_set() {
        assert_eq!(inline_separator(GlyphSet::Unicode), "│");
        assert_eq!(inline_separator(GlyphSet::Ascii), "|");
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
    fn mode_indicator_glyphs_follow_glyph_set() {
        assert_eq!(mode_recording_icon(GlyphSet::Unicode), "●");
        assert_eq!(mode_recording_icon(GlyphSet::Ascii), "*");
        assert_eq!(mode_auto_icon(GlyphSet::Unicode), "◉");
        assert_eq!(mode_auto_icon(GlyphSet::Ascii), "@");
        assert_eq!(mode_manual_icon(GlyphSet::Unicode), "○");
        assert_eq!(mode_manual_icon(GlyphSet::Ascii), ">");
        assert_eq!(mode_insert_icon(GlyphSet::Unicode), "◐");
        assert_eq!(mode_insert_icon(GlyphSet::Ascii), "~");
    }

    #[test]
    fn severity_icon_glyphs_follow_glyph_set() {
        assert_eq!(severity_info_icon(GlyphSet::Unicode), "ℹ");
        assert_eq!(severity_info_icon(GlyphSet::Ascii), "i");
        assert_eq!(severity_success_icon(GlyphSet::Unicode), "✓");
        assert_eq!(severity_success_icon(GlyphSet::Ascii), "+");
        assert_eq!(severity_warning_icon(GlyphSet::Unicode), "⚠");
        assert_eq!(severity_warning_icon(GlyphSet::Ascii), "!");
        assert_eq!(severity_error_icon(GlyphSet::Unicode), "✗");
        assert_eq!(severity_error_icon(GlyphSet::Ascii), "x");
    }

    #[test]
    fn pulse_dot_glyphs_follow_glyph_set() {
        assert_eq!(pulse_dot_active(GlyphSet::Unicode), '•');
        assert_eq!(pulse_dot_active(GlyphSet::Ascii), '*');
        assert_eq!(pulse_dot_inactive(GlyphSet::Unicode), '·');
        assert_eq!(pulse_dot_inactive(GlyphSet::Ascii), '.');
    }

    #[test]
    fn meter_marker_glyphs_follow_glyph_set() {
        assert_eq!(meter_peak_marker(GlyphSet::Unicode), '│');
        assert_eq!(meter_peak_marker(GlyphSet::Ascii), '|');
        assert_eq!(meter_threshold_marker(GlyphSet::Unicode), '▲');
        assert_eq!(meter_threshold_marker(GlyphSet::Ascii), '^');
    }

    #[test]
    fn heartbeat_frames_follow_glyph_set() {
        let unicode = heartbeat_frames(GlyphSet::Unicode);
        let ascii = heartbeat_frames(GlyphSet::Ascii);
        assert_eq!(unicode.len(), 4);
        assert_eq!(ascii.len(), 4);
        assert_eq!(unicode[2], '●');
        assert_eq!(ascii[2], 'O');
    }

    #[test]
    fn transition_pulse_markers_follow_glyph_set() {
        let unicode = transition_pulse_markers(GlyphSet::Unicode);
        let ascii = transition_pulse_markers(GlyphSet::Ascii);
        assert_eq!(unicode.len(), 2);
        assert_eq!(ascii.len(), 2);
        assert_eq!(unicode[0], "✦");
        assert_eq!(ascii[0], "*");
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
    fn processing_spinner_symbol_honors_explicit_spinner_style() {
        let mut colors = Theme::Codex.colors();
        colors.spinner_style = SpinnerStyle::Line;
        assert_eq!(processing_spinner_symbol(&colors, 2), "|");

        colors.spinner_style = SpinnerStyle::Dots;
        assert_eq!(processing_spinner_symbol(&colors, 1), "⣽");
    }

    #[test]
    fn processing_spinner_symbol_falls_back_to_ascii_frames_for_ascii_glyph_set() {
        let mut colors = Theme::Codex.colors();
        colors.glyph_set = GlyphSet::Ascii;

        // Theme-default spinner should stay ASCII-safe when the default
        // processing indicator is active.
        assert_eq!(processing_spinner_symbol(&colors, 0), ".");

        colors.spinner_style = SpinnerStyle::Braille;
        assert_eq!(processing_spinner_symbol(&colors, 2), "O");

        colors.spinner_style = SpinnerStyle::Dots;
        assert_eq!(processing_spinner_symbol(&colors, 1), "o");

        colors.spinner_style = SpinnerStyle::Block;
        assert_eq!(processing_spinner_symbol(&colors, 3), "o");
    }
}
