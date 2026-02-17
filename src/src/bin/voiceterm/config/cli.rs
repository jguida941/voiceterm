//! CLI flag schema so overlay startup behavior is explicit and discoverable.

use clap::{ArgAction, Parser, ValueEnum};
use std::path::PathBuf;
use voiceterm::config::AppConfig;

pub(crate) const DEFAULT_WAKE_WORD_SENSITIVITY: f32 = 0.55;
pub(crate) const DEFAULT_WAKE_WORD_COOLDOWN_MS: u64 = 2000;
pub(crate) const MIN_WAKE_WORD_COOLDOWN_MS: u64 = 500;
pub(crate) const MAX_WAKE_WORD_COOLDOWN_MS: u64 = 10_000;

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum, Default)]
pub(crate) enum VoiceSendMode {
    #[default]
    Auto,
    Insert,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum, Default)]
pub(crate) enum HudRightPanel {
    #[default]
    Ribbon,
    Dots,
    Heartbeat,
    Off,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum, Default)]
pub(crate) enum HudBorderStyle {
    #[default]
    Theme,
    Single,
    Rounded,
    Double,
    Heavy,
    None,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum, Default)]
pub(crate) enum LatencyDisplayMode {
    Off,
    #[default]
    Short,
    Label,
}

/// HUD display style - controls overall banner visibility.
#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum, Default)]
pub(crate) enum HudStyle {
    /// Full 4-row banner with borders and shortcuts (default)
    #[default]
    Full,
    /// Single-line minimal indicator (just colored text, no borders)
    Minimal,
    /// Hidden unless recording
    Hidden,
}

impl std::fmt::Display for HudStyle {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let label = match self {
            HudStyle::Full => "Full",
            HudStyle::Minimal => "Minimal",
            HudStyle::Hidden => "Hidden",
        };
        write!(f, "{label}")
    }
}

impl std::fmt::Display for HudRightPanel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let label = match self {
            HudRightPanel::Off => "Off",
            HudRightPanel::Ribbon => "Ribbon",
            HudRightPanel::Dots => "Dots",
            HudRightPanel::Heartbeat => "Heartbeat",
        };
        write!(f, "{label}")
    }
}

impl std::fmt::Display for HudBorderStyle {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let label = match self {
            HudBorderStyle::Theme => "Theme",
            HudBorderStyle::Single => "Single",
            HudBorderStyle::Rounded => "Rounded",
            HudBorderStyle::Double => "Double",
            HudBorderStyle::Heavy => "Heavy",
            HudBorderStyle::None => "None",
        };
        write!(f, "{label}")
    }
}

impl std::fmt::Display for LatencyDisplayMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let label = match self {
            LatencyDisplayMode::Off => "Off",
            LatencyDisplayMode::Short => "Nms",
            LatencyDisplayMode::Label => "Latency: Nms",
        };
        write!(f, "{label}")
    }
}

#[derive(Debug, Parser, Clone)]
#[command(about = "VoiceTerm", author, version, disable_help_flag = true)]
pub(crate) struct OverlayConfig {
    /// Show themed, grouped help and exit
    #[arg(long = "help", short = 'h', action = ArgAction::SetTrue)]
    pub(crate) help: bool,

    #[command(flatten)]
    pub(crate) app: AppConfig,

    /// Regex used to detect the AI prompt line (overrides auto-detection)
    #[arg(long = "prompt-regex")]
    pub(crate) prompt_regex: Option<String>,

    /// Log file path for prompt detection diagnostics
    #[arg(long = "prompt-log")]
    pub(crate) prompt_log: Option<PathBuf>,

    /// Start in auto-voice mode
    #[arg(long = "auto-voice", default_value_t = false)]
    pub(crate) auto_voice: bool,

    /// Idle time before auto-voice triggers when prompt detection is unknown (ms)
    #[arg(long = "auto-voice-idle-ms", default_value_t = 1200)]
    pub(crate) auto_voice_idle_ms: u64,

    /// Idle time before transcripts auto-send when a prompt has not been detected (ms)
    #[arg(long = "transcript-idle-ms", default_value_t = 250)]
    pub(crate) transcript_idle_ms: u64,

    /// Voice transcript handling (auto = send newline, insert = leave for editing)
    #[arg(long = "voice-send-mode", value_enum, default_value_t = VoiceSendMode::Auto)]
    pub(crate) voice_send_mode: VoiceSendMode,

    /// Enable local wake-word listening (default OFF until fully hardened).
    #[arg(long = "wake-word", default_value_t = false)]
    pub(crate) wake_word: bool,

    /// Wake-word detector sensitivity in normalized range [0.0, 1.0].
    #[arg(
        long = "wake-word-sensitivity",
        default_value_t = DEFAULT_WAKE_WORD_SENSITIVITY,
        value_parser = parse_wake_word_sensitivity
    )]
    pub(crate) wake_word_sensitivity: f32,

    /// Cooldown applied after wake detection to suppress immediate retriggers (ms).
    #[arg(
        long = "wake-word-cooldown-ms",
        default_value_t = DEFAULT_WAKE_WORD_COOLDOWN_MS,
        value_parser = parse_wake_word_cooldown_ms
    )]
    pub(crate) wake_word_cooldown_ms: u64,

    /// Color theme for status line (chatgpt, claude, codex, coral, catppuccin, dracula, gruvbox, nord, tokyonight, ansi, none)
    /// Defaults to the backend-specific theme if not provided.
    #[arg(long = "theme")]
    pub(crate) theme_name: Option<String>,

    /// Disable colors in status line output
    #[arg(long = "no-color", default_value_t = false)]
    pub(crate) no_color: bool,

    /// Right-side HUD panel (off, ribbon, dots, heartbeat)
    #[arg(long = "hud-right-panel", value_enum, default_value_t = HudRightPanel::Ribbon)]
    pub(crate) hud_right_panel: HudRightPanel,

    /// Full HUD border style (theme, single, rounded, double, heavy, none)
    #[arg(
        long = "hud-border-style",
        value_enum,
        default_value_t = HudBorderStyle::Theme
    )]
    pub(crate) hud_border_style: HudBorderStyle,

    /// Only animate the right-side panel while recording
    #[arg(long = "hud-right-panel-recording-only", default_value_t = true)]
    pub(crate) hud_right_panel_recording_only: bool,

    /// HUD display style (full, minimal, hidden)
    #[arg(long = "hud-style", value_enum, default_value_t = HudStyle::Full)]
    pub(crate) hud_style: HudStyle,

    /// Latency badge style in shortcuts row (`off`, `short` = `123ms`, `label` = `Latency: 123ms`)
    #[arg(
        long = "latency-display",
        value_enum,
        default_value_t = LatencyDisplayMode::Short
    )]
    pub(crate) latency_display: LatencyDisplayMode,

    /// Shorthand for --hud-style minimal
    #[arg(long = "minimal-hud", default_value_t = false)]
    pub(crate) minimal_hud: bool,

    /// Backend CLI to run (codex, claude, gemini, or custom command)
    ///
    /// Use a preset name or provide a custom command string.
    /// Examples:
    ///   --backend codex
    ///   --backend claude
    ///   --backend "my-tool --flag"
    #[arg(long = "backend", default_value = "codex")]
    pub(crate) backend: String,

    /// Shorthand for --backend codex
    #[arg(long = "codex", default_value_t = false)]
    pub(crate) codex: bool,

    /// Shorthand for --backend claude
    #[arg(long = "claude", default_value_t = false)]
    pub(crate) claude: bool,

    /// Shorthand for --backend gemini
    #[arg(long = "gemini", default_value_t = false)]
    pub(crate) gemini: bool,

    /// Run backend login before starting the overlay
    #[arg(long = "login", default_value_t = false)]
    pub(crate) login: bool,
}

fn parse_wake_word_sensitivity(raw: &str) -> Result<f32, String> {
    let value: f32 = raw
        .parse()
        .map_err(|_| format!("invalid wake-word sensitivity '{raw}'"))?;
    if !(0.0..=1.0).contains(&value) {
        return Err("wake-word sensitivity must be between 0.0 and 1.0".to_string());
    }
    Ok(value)
}

fn parse_wake_word_cooldown_ms(raw: &str) -> Result<u64, String> {
    let value: u64 = raw
        .parse()
        .map_err(|_| format!("invalid wake-word cooldown '{raw}'"))?;
    if !(MIN_WAKE_WORD_COOLDOWN_MS..=MAX_WAKE_WORD_COOLDOWN_MS).contains(&value) {
        return Err(format!(
            "wake-word cooldown must be between {MIN_WAKE_WORD_COOLDOWN_MS} and {MAX_WAKE_WORD_COOLDOWN_MS} ms"
        ));
    }
    Ok(value)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wake_word_defaults_are_safe() {
        let cfg = OverlayConfig::parse_from(["test-app"]);
        assert!(!cfg.wake_word);
        assert!((cfg.wake_word_sensitivity - DEFAULT_WAKE_WORD_SENSITIVITY).abs() < f32::EPSILON);
        assert_eq!(cfg.wake_word_cooldown_ms, DEFAULT_WAKE_WORD_COOLDOWN_MS);
    }

    #[test]
    fn wake_word_parser_accepts_bounds() {
        let cfg = OverlayConfig::parse_from([
            "test-app",
            "--wake-word",
            "--wake-word-sensitivity",
            "1.0",
            "--wake-word-cooldown-ms",
            "500",
        ]);
        assert!(cfg.wake_word);
        assert!((cfg.wake_word_sensitivity - 1.0).abs() < f32::EPSILON);
        assert_eq!(cfg.wake_word_cooldown_ms, 500);
    }

    #[test]
    fn wake_word_parser_rejects_out_of_bounds_values() {
        assert!(
            OverlayConfig::try_parse_from(["test-app", "--wake-word-sensitivity", "1.5",]).is_err()
        );
        assert!(
            OverlayConfig::try_parse_from(["test-app", "--wake-word-cooldown-ms", "200",]).is_err()
        );
    }

    #[test]
    fn manual_help_flags_parse_without_clap_auto_exit() {
        let long = OverlayConfig::parse_from(["test-app", "--help"]);
        assert!(long.help);

        let short = OverlayConfig::parse_from(["test-app", "-h"]);
        assert!(short.help);
    }
}
