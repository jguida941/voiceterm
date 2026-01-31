//! Color themes for the overlay status line.
//!
//! Provides predefined color palettes that can be selected via CLI flags.

/// ANSI color codes for a theme.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThemeColors {
    /// Color for recording/active states
    pub recording: &'static str,
    /// Color for processing/working states
    pub processing: &'static str,
    /// Color for success states
    pub success: &'static str,
    /// Color for warning states
    pub warning: &'static str,
    /// Color for error states
    pub error: &'static str,
    /// Color for info states
    pub info: &'static str,
    /// Reset code
    pub reset: &'static str,
}

/// Available color themes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum Theme {
    /// Default coral/red theme (matches existing TUI)
    #[default]
    Coral,
    /// Catppuccin Mocha - pastel dark theme
    Catppuccin,
    /// Dracula - high contrast dark theme
    Dracula,
    /// Nord - arctic blue-gray theme
    Nord,
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
            "catppuccin" | "mocha" => Some(Self::Catppuccin),
            "dracula" => Some(Self::Dracula),
            "nord" => Some(Self::Nord),
            "ansi" | "ansi16" | "basic" => Some(Self::Ansi),
            "none" | "plain" => Some(Self::None),
            _ => None,
        }
    }

    /// Get the color palette for this theme.
    pub fn colors(&self) -> ThemeColors {
        match self {
            Self::Coral => THEME_CORAL,
            Self::Catppuccin => THEME_CATPPUCCIN,
            Self::Dracula => THEME_DRACULA,
            Self::Nord => THEME_NORD,
            Self::Ansi => THEME_ANSI,
            Self::None => THEME_NONE,
        }
    }

    /// List all available theme names.
    #[allow(dead_code)]
    pub fn available() -> &'static [&'static str] {
        &["coral", "catppuccin", "dracula", "nord", "ansi", "none"]
    }

    /// Check if this theme uses truecolor (24-bit RGB).
    pub fn is_truecolor(&self) -> bool {
        matches!(self, Self::Catppuccin | Self::Dracula | Self::Nord)
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

impl std::fmt::Display for Theme {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Coral => write!(f, "coral"),
            Self::Catppuccin => write!(f, "catppuccin"),
            Self::Dracula => write!(f, "dracula"),
            Self::Nord => write!(f, "nord"),
            Self::Ansi => write!(f, "ansi"),
            Self::None => write!(f, "none"),
        }
    }
}

/// Coral theme - warm red/coral accents (default)
pub const THEME_CORAL: ThemeColors = ThemeColors {
    recording: "\x1b[91m",  // Bright red
    processing: "\x1b[93m", // Bright yellow
    success: "\x1b[92m",    // Bright green
    warning: "\x1b[93m",    // Bright yellow
    error: "\x1b[91m",      // Bright red
    info: "\x1b[94m",       // Bright blue
    reset: "\x1b[0m",
};

/// Catppuccin Mocha theme - pastel colors
/// https://github.com/catppuccin/catppuccin
pub const THEME_CATPPUCCIN: ThemeColors = ThemeColors {
    recording: "\x1b[38;2;243;139;168m",  // Red #f38ba8
    processing: "\x1b[38;2;249;226;175m", // Yellow #f9e2af
    success: "\x1b[38;2;166;227;161m",    // Green #a6e3a1
    warning: "\x1b[38;2;250;179;135m",    // Peach #fab387
    error: "\x1b[38;2;243;139;168m",      // Red #f38ba8
    info: "\x1b[38;2;137;180;250m",       // Blue #89b4fa
    reset: "\x1b[0m",
};

/// Dracula theme - high contrast
/// https://draculatheme.com
pub const THEME_DRACULA: ThemeColors = ThemeColors {
    recording: "\x1b[38;2;255;85;85m",    // Red #ff5555
    processing: "\x1b[38;2;241;250;140m", // Yellow #f1fa8c
    success: "\x1b[38;2;80;250;123m",     // Green #50fa7b
    warning: "\x1b[38;2;255;184;108m",    // Orange #ffb86c
    error: "\x1b[38;2;255;85;85m",        // Red #ff5555
    info: "\x1b[38;2;139;233;253m",       // Cyan #8be9fd
    reset: "\x1b[0m",
};

/// Nord theme - arctic blue-gray
/// https://www.nordtheme.com
pub const THEME_NORD: ThemeColors = ThemeColors {
    recording: "\x1b[38;2;191;97;106m",   // Aurora red #bf616a
    processing: "\x1b[38;2;235;203;139m", // Aurora yellow #ebcb8b
    success: "\x1b[38;2;163;190;140m",    // Aurora green #a3be8c
    warning: "\x1b[38;2;208;135;112m",    // Aurora orange #d08770
    error: "\x1b[38;2;191;97;106m",       // Aurora red #bf616a
    info: "\x1b[38;2;136;192;208m",       // Frost #88c0d0
    reset: "\x1b[0m",
};

/// ANSI 16-color theme - works on all color terminals
/// Uses standard ANSI escape codes (30-37, 90-97)
pub const THEME_ANSI: ThemeColors = ThemeColors {
    recording: "\x1b[31m",  // Red
    processing: "\x1b[33m", // Yellow
    success: "\x1b[32m",    // Green
    warning: "\x1b[33m",    // Yellow
    error: "\x1b[31m",      // Red
    info: "\x1b[36m",       // Cyan
    reset: "\x1b[0m",
};

/// No colors - plain text output
pub const THEME_NONE: ThemeColors = ThemeColors {
    recording: "",
    processing: "",
    success: "",
    warning: "",
    error: "",
    info: "",
    reset: "",
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn theme_from_name_parses_valid() {
        assert_eq!(Theme::from_name("coral"), Some(Theme::Coral));
        assert_eq!(Theme::from_name("CATPPUCCIN"), Some(Theme::Catppuccin));
        assert_eq!(Theme::from_name("Dracula"), Some(Theme::Dracula));
        assert_eq!(Theme::from_name("nord"), Some(Theme::Nord));
        assert_eq!(Theme::from_name("ansi"), Some(Theme::Ansi));
        assert_eq!(Theme::from_name("ansi16"), Some(Theme::Ansi));
        assert_eq!(Theme::from_name("none"), Some(Theme::None));
        assert_eq!(Theme::from_name("default"), Some(Theme::Coral));
    }

    #[test]
    fn theme_is_truecolor() {
        assert!(!Theme::Coral.is_truecolor());
        assert!(Theme::Catppuccin.is_truecolor());
        assert!(Theme::Dracula.is_truecolor());
        assert!(Theme::Nord.is_truecolor());
        assert!(!Theme::Ansi.is_truecolor());
        assert!(!Theme::None.is_truecolor());
    }

    #[test]
    fn theme_fallback_for_ansi() {
        assert_eq!(Theme::Coral.fallback_for_ansi(), Theme::Coral);
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
        assert_eq!(format!("{}", Theme::Catppuccin), "catppuccin");
    }
}
