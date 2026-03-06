//! Terminal color-capability detection so theme fallbacks match host support.
//!
//! Detects what color modes the terminal supports and provides fallbacks.

use crate::runtime_compat::{detect_terminal_host, TerminalHost};
use std::env;

/// Color mode capabilities of the terminal.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ColorMode {
    /// 24-bit true color (16 million colors)
    #[default]
    TrueColor,
    /// 256 color mode
    Color256,
    /// Basic 16 ANSI colors
    Ansi16,
    /// No color support
    None,
}

impl ColorMode {
    /// Detect the terminal's color capabilities from environment variables.
    pub fn detect() -> Self {
        // Check NO_COLOR first (standard convention)
        // https://no-color.org/
        if env::var("NO_COLOR").is_ok() {
            return Self::None;
        }

        // Check COLORTERM for truecolor support
        if let Ok(colorterm) = env::var("COLORTERM") {
            if colorterm == "truecolor" || colorterm == "24bit" {
                return Self::TrueColor;
            }
        }

        // Some terminals support truecolor but do not set COLORTERM.
        if env_supports_truecolor_without_colorterm() {
            return Self::TrueColor;
        }

        // Check TERM for color capabilities
        if let Ok(term) = env::var("TERM") {
            if term.contains("256color") || term.contains("256-color") {
                return Self::Color256;
            }
            if term == "dumb" {
                return Self::None;
            }
        }

        // Default to ANSI 16 colors as a safe fallback
        Self::Ansi16
    }

    /// Check if colors are supported at all.
    pub fn supports_color(&self) -> bool {
        !matches!(self, Self::None)
    }

    /// Check if 256 colors are supported.
    #[cfg(test)]
    pub fn supports_256(&self) -> bool {
        matches!(self, Self::TrueColor | Self::Color256)
    }

    /// Check if true color (24-bit) is supported.
    #[cfg(test)]
    pub fn supports_truecolor(&self) -> bool {
        matches!(self, Self::TrueColor)
    }
}

fn env_supports_truecolor_without_colorterm() -> bool {
    if matches!(
        detect_terminal_host(),
        TerminalHost::Cursor | TerminalHost::JetBrains
    ) {
        return true;
    }

    if let Ok(term_program) = env::var("TERM_PROGRAM") {
        let program = term_program.to_ascii_lowercase();
        if matches!(program.as_str(), "vscode" | "wezterm" | "iterm.app")
            || program.contains("warp")
        {
            return true;
        }
    }

    false
}

impl std::fmt::Display for ColorMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::TrueColor => write!(f, "truecolor"),
            Self::Color256 => write!(f, "256"),
            Self::Ansi16 => write!(f, "ansi"),
            Self::None => write!(f, "none"),
        }
    }
}

/// Convert a 24-bit RGB color to the closest ANSI 256 color.
#[cfg(test)]
pub fn rgb_to_256(r: u8, g: u8, b: u8) -> u8 {
    // Check for grayscale
    if r == g && g == b {
        if r < 8 {
            return 16;
        }
        // The xterm grayscale ramp tops out at 231; avoid overflow at the upper edge.
        if r >= 248 {
            return 231;
        }
        return ((r as u16 - 8) / 10 + 232) as u8;
    }

    // Convert to 6x6x6 color cube
    let r_idx = (r as u16 * 5 / 255) as u8;
    let g_idx = (g as u16 * 5 / 255) as u8;
    let b_idx = (b as u16 * 5 / 255) as u8;

    16 + 36 * r_idx + 6 * g_idx + b_idx
}

/// Convert a 24-bit RGB color to the closest ANSI 16 color.
#[cfg(test)]
pub fn rgb_to_ansi16(r: u8, g: u8, b: u8) -> u8 {
    // Simple brightness-based conversion
    let brightness = (r as u16 + g as u16 + b as u16) / 3;
    let is_bright = brightness > 127;

    // Determine primary color component
    let max = r.max(g).max(b);
    let base = if max == 0 {
        0 // Black
    } else if r == max && g == max && b == max {
        7 // White/gray
    } else if r == max && g >= b {
        if g > r / 2 {
            3 // Yellow
        } else {
            1 // Red
        }
    } else if g == max {
        if b > g / 2 {
            6 // Cyan
        } else {
            2 // Green
        }
    } else if r > b / 2 {
        5 // Magenta
    } else {
        4 // Blue
    };

    if is_bright {
        base + 8 // Bright variant
    } else {
        base
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_env::with_env_lock;

    fn detect_with_env(
        colorterm: Option<&str>,
        term: Option<&str>,
        term_program: Option<&str>,
        terminal_emulator: Option<&str>,
        no_color: Option<&str>,
    ) -> ColorMode {
        detect_with_env_overrides(
            colorterm,
            term,
            term_program,
            terminal_emulator,
            no_color,
            &[],
        )
    }

    fn detect_with_env_overrides(
        colorterm: Option<&str>,
        term: Option<&str>,
        term_program: Option<&str>,
        terminal_emulator: Option<&str>,
        no_color: Option<&str>,
        overrides: &[(&str, Option<&str>)],
    ) -> ColorMode {
        with_env_lock(|| {
            const KEYS: &[&str] = &[
                "COLORTERM",
                "TERM",
                "TERM_PROGRAM",
                "TERMINAL_EMULATOR",
                "NO_COLOR",
                "PYCHARM_HOSTED",
                "JETBRAINS_IDE",
                "IDEA_INITIAL_DIRECTORY",
                "IDEA_INITIAL_PROJECT",
                "CLION_IDE",
                "WEBSTORM_IDE",
                "CURSOR_TRACE_ID",
                "CURSOR_APP_VERSION",
                "CURSOR_VERSION",
                "CURSOR_BUILD_VERSION",
            ];
            let mut keys = KEYS.to_vec();
            for (key, _) in overrides {
                if !keys.contains(key) {
                    keys.push(key);
                }
            }
            let previous: Vec<(String, Option<String>)> = keys
                .iter()
                .map(|key| ((*key).to_string(), std::env::var(key).ok()))
                .collect();

            for key in &keys {
                std::env::remove_var(key);
            }

            match colorterm {
                Some(v) => std::env::set_var("COLORTERM", v),
                None => std::env::remove_var("COLORTERM"),
            }
            match term {
                Some(v) => std::env::set_var("TERM", v),
                None => std::env::remove_var("TERM"),
            }
            match term_program {
                Some(v) => std::env::set_var("TERM_PROGRAM", v),
                None => std::env::remove_var("TERM_PROGRAM"),
            }
            match terminal_emulator {
                Some(v) => std::env::set_var("TERMINAL_EMULATOR", v),
                None => std::env::remove_var("TERMINAL_EMULATOR"),
            }
            match no_color {
                Some(v) => std::env::set_var("NO_COLOR", v),
                None => std::env::remove_var("NO_COLOR"),
            }
            for (key, value) in overrides {
                match value {
                    Some(v) => std::env::set_var(key, v),
                    None => std::env::remove_var(key),
                }
            }

            let detected = ColorMode::detect();

            for (key, value) in previous {
                match value {
                    Some(v) => std::env::set_var(key, v),
                    None => std::env::remove_var(key),
                }
            }

            detected
        })
    }

    #[test]
    fn color_mode_supports_color() {
        assert!(ColorMode::TrueColor.supports_color());
        assert!(ColorMode::Color256.supports_color());
        assert!(ColorMode::Ansi16.supports_color());
        assert!(!ColorMode::None.supports_color());
    }

    #[test]
    fn color_mode_supports_256() {
        assert!(ColorMode::TrueColor.supports_256());
        assert!(ColorMode::Color256.supports_256());
        assert!(!ColorMode::Ansi16.supports_256());
        assert!(!ColorMode::None.supports_256());
    }

    #[test]
    fn color_mode_supports_truecolor() {
        assert!(ColorMode::TrueColor.supports_truecolor());
        assert!(!ColorMode::Color256.supports_truecolor());
        assert!(!ColorMode::Ansi16.supports_truecolor());
        assert!(!ColorMode::None.supports_truecolor());
    }

    #[test]
    fn color_mode_display() {
        assert_eq!(format!("{}", ColorMode::TrueColor), "truecolor");
        assert_eq!(format!("{}", ColorMode::None), "none");
    }

    #[test]
    fn rgb_to_256_grayscale() {
        assert_eq!(rgb_to_256(0, 0, 0), 16);
        assert_eq!(rgb_to_256(255, 255, 255), 231);
    }

    #[test]
    fn rgb_to_256_colors() {
        // Pure red should map to color cube
        let red = rgb_to_256(255, 0, 0);
        assert!(red >= 16 && red < 232);
    }

    #[test]
    fn rgb_to_ansi16_basic() {
        // Black
        assert_eq!(rgb_to_ansi16(0, 0, 0), 0);
        // Bright white
        assert_eq!(rgb_to_ansi16(255, 255, 255), 15);
    }

    #[test]
    fn rgb_to_256_exact_cube_samples() {
        assert_eq!(rgb_to_256(255, 0, 0), 196);
        assert_eq!(rgb_to_256(0, 255, 0), 46);
        assert_eq!(rgb_to_256(0, 0, 255), 21);
        assert_eq!(rgb_to_256(255, 255, 0), 226);
        assert_eq!(rgb_to_256(10, 20, 30), 16);
    }

    #[test]
    fn rgb_to_256_grayscale_ramp_samples() {
        assert_eq!(rgb_to_256(8, 8, 8), 232);
        assert_eq!(rgb_to_256(18, 18, 18), 233);
        assert_eq!(rgb_to_256(128, 128, 128), 244);
        assert_eq!(rgb_to_256(248, 248, 248), 231);
    }

    #[test]
    fn rgb_to_ansi16_branch_samples() {
        // red branch
        assert_eq!(rgb_to_ansi16(200, 20, 20), 1);
        // yellow branch
        assert_eq!(rgb_to_ansi16(200, 120, 10), 3);
        // green branch
        assert_eq!(rgb_to_ansi16(10, 200, 90), 2);
        // cyan branch
        assert_eq!(rgb_to_ansi16(10, 200, 130), 6);
        // magenta branch
        assert_eq!(rgb_to_ansi16(120, 10, 200), 5);
        // blue branch
        assert_eq!(rgb_to_ansi16(80, 10, 200), 4);
        // gray branch
        assert_eq!(rgb_to_ansi16(100, 100, 100), 7);
        // bright variant
        assert_eq!(rgb_to_ansi16(250, 250, 10), 11);
    }

    #[test]
    fn rgb_to_ansi16_boundary_samples() {
        // brightness threshold (exactly 127 is not bright)
        assert_eq!(rgb_to_ansi16(127, 127, 127), 7);
        // g == r/2 stays in the red branch
        assert_eq!(rgb_to_ansi16(200, 100, 50), 1);
        // b == g/2 stays in the green branch
        assert_eq!(rgb_to_ansi16(50, 200, 100), 2);
        // r == b/2 stays in the blue branch
        assert_eq!(rgb_to_ansi16(100, 50, 200), 4);
    }

    #[test]
    fn detect_truecolor_from_colorterm_24bit() {
        assert_eq!(
            detect_with_env(Some("24bit"), Some("xterm-256color"), None, None, None),
            ColorMode::TrueColor
        );
    }

    #[test]
    fn detect_color256_when_term_program_unrecognized() {
        assert_eq!(
            detect_with_env(None, Some("xterm-256color"), Some("acme-term"), None, None),
            ColorMode::Color256
        );
    }

    #[test]
    fn detect_ansi16_when_term_is_xterm_without_256_hint() {
        assert_eq!(
            detect_with_env(None, Some("xterm"), None, None, None),
            ColorMode::Ansi16
        );
    }

    #[test]
    fn detect_colorterm_non_truecolor_does_not_force_truecolor() {
        assert_eq!(
            detect_with_env(Some("ansi"), Some("xterm-256color"), None, None, None),
            ColorMode::Color256
        );
    }

    #[test]
    fn detect_dumb_term_without_color_hints_is_none() {
        assert_eq!(
            detect_with_env(None, Some("dumb"), None, None, None),
            ColorMode::None
        );
    }

    #[test]
    fn detect_truecolor_when_term_program_contains_jetbrains() {
        assert_eq!(
            detect_with_env(
                None,
                Some("xterm-256color"),
                Some("my-jetbrains-shell"),
                None,
                None
            ),
            ColorMode::TrueColor
        );
    }

    #[test]
    fn detect_truecolor_when_terminal_emulator_contains_jediterm_only() {
        assert_eq!(
            detect_with_env(
                None,
                Some("xterm-256color"),
                None,
                Some("jediterm-shell"),
                None
            ),
            ColorMode::TrueColor
        );
    }

    #[test]
    fn detect_truecolor_for_jetbrains_terminal_env() {
        assert_eq!(
            detect_with_env(
                None,
                Some("xterm-256color"),
                None,
                Some("JetBrains-JediTerm"),
                None
            ),
            ColorMode::TrueColor
        );
    }

    #[test]
    fn detect_truecolor_for_vscode_term_program_env() {
        assert_eq!(
            detect_with_env(None, Some("xterm-256color"), Some("vscode"), None, None),
            ColorMode::TrueColor
        );
    }

    #[test]
    fn detect_truecolor_for_warp_term_program_env() {
        assert_eq!(
            detect_with_env(
                None,
                Some("xterm-256color"),
                Some("WarpTerminal"),
                None,
                None
            ),
            ColorMode::TrueColor
        );
    }

    #[test]
    fn detect_truecolor_for_jetbrains_term_program_env() {
        assert_eq!(
            detect_with_env(
                None,
                Some("xterm-256color"),
                Some("JetBrains-JediTerm"),
                None,
                None
            ),
            ColorMode::TrueColor
        );
    }

    #[test]
    fn detect_truecolor_for_jetbrains_ide_env_marker_without_term_hints() {
        assert_eq!(
            detect_with_env_overrides(
                None,
                Some("xterm-256color"),
                None,
                None,
                None,
                &[("IDEA_INITIAL_DIRECTORY", Some("/tmp/project"))]
            ),
            ColorMode::TrueColor
        );
    }

    #[test]
    fn detect_truecolor_for_cursor_env_marker_without_term_program() {
        assert_eq!(
            detect_with_env_overrides(
                None,
                Some("xterm-256color"),
                None,
                None,
                None,
                &[("CURSOR_TRACE_ID", Some("trace-id"))]
            ),
            ColorMode::TrueColor
        );
    }

    #[test]
    fn detect_terminal_capability_matrix_cases() {
        let cases = [
            (
                "no-color override",
                None,
                Some("xterm-256color"),
                None,
                None,
                Some("1"),
                ColorMode::None,
            ),
            (
                "explicit truecolor",
                Some("truecolor"),
                Some("xterm-256color"),
                None,
                None,
                None,
                ColorMode::TrueColor,
            ),
            (
                "cursor/term_program truecolor inference",
                None,
                Some("xterm-256color"),
                Some("cursor"),
                None,
                None,
                ColorMode::TrueColor,
            ),
            (
                "256-color term",
                None,
                Some("xterm-256color"),
                Some("acme-term"),
                None,
                None,
                ColorMode::Color256,
            ),
            (
                "ansi fallback",
                None,
                Some("xterm"),
                None,
                None,
                None,
                ColorMode::Ansi16,
            ),
            (
                "dumb terminal",
                None,
                Some("dumb"),
                None,
                None,
                None,
                ColorMode::None,
            ),
        ];

        for (name, colorterm, term, term_program, terminal_emulator, no_color, expected) in cases {
            let detected =
                detect_with_env(colorterm, term, term_program, terminal_emulator, no_color);
            assert_eq!(detected, expected, "matrix case failed: {name}");
        }
    }
}
