//! Persistent user config (`~/.config/voiceterm/config.toml`) for core preferences.
//!
//! Loads saved preferences on startup and merges them with CLI flags.
//! CLI flags always take precedence over persisted values. Settings changed via
//! the Settings overlay are persisted back to disk.

use std::env;
use std::fs;
use std::path::PathBuf;

use voiceterm::log_debug;

const CONFIG_FILE: &str = "config.toml";
const CONFIG_DIR_ENV: &str = "VOICETERM_CONFIG_DIR";

/// Persistent user preferences that survive across sessions.
#[derive(Debug, Clone, Default, PartialEq)]
pub(crate) struct UserConfig {
    pub(crate) theme: Option<String>,
    pub(crate) hud_style: Option<String>,
    pub(crate) hud_border_style: Option<String>,
    pub(crate) hud_right_panel: Option<String>,
    pub(crate) hud_right_panel_recording_only: Option<bool>,
    pub(crate) auto_voice: Option<bool>,
    pub(crate) voice_send_mode: Option<String>,
    pub(crate) sensitivity_db: Option<f32>,
    pub(crate) wake_word: Option<bool>,
    pub(crate) wake_word_sensitivity: Option<f32>,
    pub(crate) wake_word_cooldown_ms: Option<u64>,
    pub(crate) latency_display: Option<String>,
    pub(crate) macros_enabled: Option<bool>,
    pub(crate) memory_mode: Option<String>,
}

/// Resolve the config directory path.
fn config_dir() -> Option<PathBuf> {
    if let Ok(dir) = env::var(CONFIG_DIR_ENV) {
        let trimmed = dir.trim();
        if !trimmed.is_empty() {
            return Some(PathBuf::from(trimmed));
        }
    }
    let home = env::var("HOME").ok()?;
    Some(PathBuf::from(home).join(".config").join("voiceterm"))
}

/// Resolve the full config file path.
pub(crate) fn config_file_path() -> Option<PathBuf> {
    config_dir().map(|dir| dir.join(CONFIG_FILE))
}

/// Parse a TOML-like key = value line. Handles quoted and unquoted values.
fn parse_toml_value(line: &str) -> Option<(&str, &str)> {
    let line = line.trim();
    if line.is_empty() || line.starts_with('#') || line.starts_with('[') {
        return None;
    }
    let (key, rest) = line.split_once('=')?;
    let key = key.trim();
    let value = rest.trim().trim_matches('"');
    Some((key, value))
}

fn parse_bool(value: &str) -> Option<bool> {
    match value.to_ascii_lowercase().as_str() {
        "true" | "1" | "yes" => Some(true),
        "false" | "0" | "no" => Some(false),
        _ => None,
    }
}

/// Load user config from `~/.config/voiceterm/config.toml`.
/// Returns a default (all-None) config if the file doesn't exist or can't be read.
pub(crate) fn load_user_config() -> UserConfig {
    let Some(path) = config_file_path() else {
        return UserConfig::default();
    };
    let contents = match fs::read_to_string(&path) {
        Ok(c) => c,
        Err(_) => return UserConfig::default(),
    };
    parse_user_config(&contents)
}

/// Parse config from TOML string content.
fn parse_user_config(contents: &str) -> UserConfig {
    let mut config = UserConfig::default();
    for line in contents.lines() {
        let Some((key, value)) = parse_toml_value(line) else {
            continue;
        };
        match key {
            "theme" => config.theme = Some(value.to_string()),
            "hud_style" => config.hud_style = Some(value.to_string()),
            "hud_border_style" => config.hud_border_style = Some(value.to_string()),
            "hud_right_panel" => config.hud_right_panel = Some(value.to_string()),
            "hud_right_panel_recording_only" => {
                config.hud_right_panel_recording_only = parse_bool(value);
            }
            "auto_voice" => config.auto_voice = parse_bool(value),
            "voice_send_mode" => config.voice_send_mode = Some(value.to_string()),
            "sensitivity_db" => config.sensitivity_db = value.parse().ok(),
            "wake_word" => config.wake_word = parse_bool(value),
            "wake_word_sensitivity" => config.wake_word_sensitivity = value.parse().ok(),
            "wake_word_cooldown_ms" => config.wake_word_cooldown_ms = value.parse().ok(),
            "latency_display" => config.latency_display = Some(value.to_string()),
            "macros_enabled" => config.macros_enabled = parse_bool(value),
            "memory_mode" => config.memory_mode = Some(value.to_string()),
            _ => {} // Ignore unknown keys for forward compatibility
        }
    }
    config
}

/// Serialize user config to TOML format.
fn serialize_user_config(config: &UserConfig) -> String {
    let mut lines = Vec::new();
    lines.push("# VoiceTerm persistent user config".to_string());
    lines.push("# Managed by Settings overlay; CLI flags override these values.".to_string());
    lines.push(String::new());

    if let Some(ref v) = config.theme {
        lines.push(format!("theme = \"{v}\""));
    }
    if let Some(ref v) = config.hud_style {
        lines.push(format!("hud_style = \"{v}\""));
    }
    if let Some(ref v) = config.hud_border_style {
        lines.push(format!("hud_border_style = \"{v}\""));
    }
    if let Some(ref v) = config.hud_right_panel {
        lines.push(format!("hud_right_panel = \"{v}\""));
    }
    if let Some(v) = config.hud_right_panel_recording_only {
        lines.push(format!("hud_right_panel_recording_only = {v}"));
    }
    if let Some(v) = config.auto_voice {
        lines.push(format!("auto_voice = {v}"));
    }
    if let Some(ref v) = config.voice_send_mode {
        lines.push(format!("voice_send_mode = \"{v}\""));
    }
    if let Some(v) = config.sensitivity_db {
        lines.push(format!("sensitivity_db = {v}"));
    }
    if let Some(v) = config.wake_word {
        lines.push(format!("wake_word = {v}"));
    }
    if let Some(v) = config.wake_word_sensitivity {
        lines.push(format!("wake_word_sensitivity = {v:.2}"));
    }
    if let Some(v) = config.wake_word_cooldown_ms {
        lines.push(format!("wake_word_cooldown_ms = {v}"));
    }
    if let Some(ref v) = config.latency_display {
        lines.push(format!("latency_display = \"{v}\""));
    }
    if let Some(v) = config.macros_enabled {
        lines.push(format!("macros_enabled = {v}"));
    }
    if let Some(ref v) = config.memory_mode {
        lines.push(format!("memory_mode = \"{v}\""));
    }

    lines.push(String::new());
    lines.join("\n")
}

/// Save user config to `~/.config/voiceterm/config.toml`.
pub(crate) fn save_user_config(config: &UserConfig) {
    let Some(path) = config_file_path() else {
        log_debug("persistent config: cannot resolve config file path");
        return;
    };

    if let Some(parent) = path.parent() {
        if let Err(err) = fs::create_dir_all(parent) {
            log_debug(&format!(
                "persistent config: failed to create config directory {}: {err}",
                parent.display()
            ));
            return;
        }
    }

    let body = serialize_user_config(config);
    if let Err(err) = fs::write(&path, body) {
        log_debug(&format!(
            "persistent config: failed to write {}: {err}",
            path.display()
        ));
    }
}

/// Apply loaded user config to OverlayConfig, respecting CLI flag precedence.
/// Only applies values that were NOT explicitly set via CLI flags.
pub(crate) fn apply_user_config_to_overlay(
    user_config: &UserConfig,
    overlay_config: &mut crate::config::OverlayConfig,
    cli_explicit: &CliExplicitFlags,
) {
    use crate::config::{
        HudBorderStyle, HudRightPanel, HudStyle, LatencyDisplayMode, VoiceSendMode,
    };

    if !cli_explicit.theme {
        if let Some(ref theme) = user_config.theme {
            overlay_config.theme_name = Some(theme.clone());
        }
    }
    if !cli_explicit.hud_style {
        if let Some(ref style) = user_config.hud_style {
            overlay_config.hud_style = match style.to_ascii_lowercase().as_str() {
                "full" => HudStyle::Full,
                "minimal" => HudStyle::Minimal,
                "hidden" => HudStyle::Hidden,
                _ => overlay_config.hud_style,
            };
        }
    }
    if !cli_explicit.hud_border_style {
        if let Some(ref style) = user_config.hud_border_style {
            overlay_config.hud_border_style = match style.to_ascii_lowercase().as_str() {
                "theme" => HudBorderStyle::Theme,
                "single" => HudBorderStyle::Single,
                "rounded" => HudBorderStyle::Rounded,
                "double" => HudBorderStyle::Double,
                "heavy" => HudBorderStyle::Heavy,
                "none" => HudBorderStyle::None,
                _ => overlay_config.hud_border_style,
            };
        }
    }
    if !cli_explicit.hud_right_panel {
        if let Some(ref panel) = user_config.hud_right_panel {
            overlay_config.hud_right_panel = match panel.to_ascii_lowercase().as_str() {
                "ribbon" => HudRightPanel::Ribbon,
                "dots" => HudRightPanel::Dots,
                "heartbeat" => HudRightPanel::Heartbeat,
                "off" => HudRightPanel::Off,
                _ => overlay_config.hud_right_panel,
            };
        }
    }
    if !cli_explicit.hud_right_panel_recording_only {
        if let Some(v) = user_config.hud_right_panel_recording_only {
            overlay_config.hud_right_panel_recording_only = v;
        }
    }
    if !cli_explicit.auto_voice {
        if let Some(v) = user_config.auto_voice {
            overlay_config.auto_voice = v;
        }
    }
    if !cli_explicit.voice_send_mode {
        if let Some(ref mode) = user_config.voice_send_mode {
            overlay_config.voice_send_mode = match mode.to_ascii_lowercase().as_str() {
                "auto" => VoiceSendMode::Auto,
                "insert" => VoiceSendMode::Insert,
                _ => overlay_config.voice_send_mode,
            };
        }
    }
    if !cli_explicit.sensitivity_db {
        if let Some(db) = user_config.sensitivity_db {
            overlay_config.app.voice_vad_threshold_db = db;
        }
    }
    if !cli_explicit.wake_word {
        if let Some(v) = user_config.wake_word {
            overlay_config.wake_word = v;
        }
    }
    if !cli_explicit.wake_word_sensitivity {
        if let Some(v) = user_config.wake_word_sensitivity {
            overlay_config.wake_word_sensitivity = v.clamp(0.0, 1.0);
        }
    }
    if !cli_explicit.wake_word_cooldown_ms {
        if let Some(v) = user_config.wake_word_cooldown_ms {
            overlay_config.wake_word_cooldown_ms = v.clamp(
                crate::config::MIN_WAKE_WORD_COOLDOWN_MS,
                crate::config::MAX_WAKE_WORD_COOLDOWN_MS,
            );
        }
    }
    if !cli_explicit.latency_display {
        if let Some(ref mode) = user_config.latency_display {
            overlay_config.latency_display = match mode.to_ascii_lowercase().as_str() {
                "off" => LatencyDisplayMode::Off,
                "short" | "nms" => LatencyDisplayMode::Short,
                "label" | "latency: nms" => LatencyDisplayMode::Label,
                _ => overlay_config.latency_display,
            };
        }
    }
}

/// Apply non-CLI runtime state from persistent config.
pub(crate) fn apply_user_config_to_status_state(
    user_config: &UserConfig,
    status_state: &mut crate::status_line::StatusLineState,
) {
    if let Some(v) = user_config.macros_enabled {
        status_state.macros_enabled = v;
    }
}

/// Snapshot the current runtime state into a `UserConfig` for persistence.
pub(crate) fn snapshot_from_runtime(
    config: &crate::config::OverlayConfig,
    status_state: &crate::status_line::StatusLineState,
    theme: crate::theme::Theme,
) -> UserConfig {
    UserConfig {
        theme: Some(theme.to_string().to_ascii_lowercase()),
        hud_style: Some(status_state.hud_style.to_string().to_ascii_lowercase()),
        hud_border_style: Some(
            status_state
                .hud_border_style
                .to_string()
                .to_ascii_lowercase(),
        ),
        hud_right_panel: Some(
            status_state
                .hud_right_panel
                .to_string()
                .to_ascii_lowercase(),
        ),
        hud_right_panel_recording_only: Some(status_state.hud_right_panel_recording_only),
        auto_voice: Some(status_state.auto_voice_enabled),
        voice_send_mode: Some(status_state.send_mode.to_string().to_ascii_lowercase()),
        sensitivity_db: Some(status_state.sensitivity_db),
        wake_word: Some(config.wake_word),
        wake_word_sensitivity: Some(config.wake_word_sensitivity),
        wake_word_cooldown_ms: Some(config.wake_word_cooldown_ms),
        latency_display: Some(
            status_state
                .latency_display
                .to_string()
                .to_ascii_lowercase(),
        ),
        macros_enabled: Some(status_state.macros_enabled),
        memory_mode: None, // Persisted separately when memory mode changes.
    }
}

/// Tracks which CLI flags were explicitly provided by the user.
/// Persistent config values are only applied when the corresponding flag was NOT provided.
#[derive(Debug, Clone, Default)]
pub(crate) struct CliExplicitFlags {
    pub(crate) theme: bool,
    pub(crate) hud_style: bool,
    pub(crate) hud_border_style: bool,
    pub(crate) hud_right_panel: bool,
    pub(crate) hud_right_panel_recording_only: bool,
    pub(crate) auto_voice: bool,
    pub(crate) voice_send_mode: bool,
    pub(crate) sensitivity_db: bool,
    pub(crate) wake_word: bool,
    pub(crate) wake_word_sensitivity: bool,
    pub(crate) wake_word_cooldown_ms: bool,
    pub(crate) latency_display: bool,
}

fn cli_flag_present(args: &[String], long_name: &str) -> bool {
    let exact = format!("--{long_name}");
    let with_value = format!("{exact}=");
    args.iter()
        .any(|arg| arg == &exact || arg.starts_with(&with_value))
}

fn detect_explicit_flags_with_args(
    config: &crate::config::OverlayConfig,
    args: &[String],
) -> CliExplicitFlags {
    use crate::config::{
        HudBorderStyle, HudRightPanel, HudStyle, LatencyDisplayMode, VoiceSendMode,
    };
    let theme_flag = cli_flag_present(args, "theme");
    let hud_style_flag =
        cli_flag_present(args, "hud-style") || cli_flag_present(args, "minimal-hud");
    let hud_border_style_flag = cli_flag_present(args, "hud-border-style");
    let hud_right_panel_flag = cli_flag_present(args, "hud-right-panel");
    let hud_right_panel_recording_only_flag =
        cli_flag_present(args, "hud-right-panel-recording-only");
    let auto_voice_flag = cli_flag_present(args, "auto-voice");
    let voice_send_mode_flag = cli_flag_present(args, "voice-send-mode");
    let sensitivity_flag = cli_flag_present(args, "voice-vad-threshold-db");
    let wake_word_flag = cli_flag_present(args, "wake-word");
    let wake_word_sensitivity_flag = cli_flag_present(args, "wake-word-sensitivity");
    let wake_word_cooldown_flag = cli_flag_present(args, "wake-word-cooldown-ms");
    let latency_display_flag = cli_flag_present(args, "latency-display");

    CliExplicitFlags {
        // CLI presence wins over fallback heuristics so explicit default values
        // (for example `--voice-send-mode auto`) still take precedence.
        theme: theme_flag || config.theme_name.is_some(),
        hud_style: hud_style_flag || config.hud_style != HudStyle::Full || config.minimal_hud,
        hud_border_style: hud_border_style_flag || config.hud_border_style != HudBorderStyle::Theme,
        hud_right_panel: hud_right_panel_flag || config.hud_right_panel != HudRightPanel::Ribbon,
        hud_right_panel_recording_only: hud_right_panel_recording_only_flag
            || !config.hud_right_panel_recording_only,
        auto_voice: auto_voice_flag || config.auto_voice,
        voice_send_mode: voice_send_mode_flag || config.voice_send_mode != VoiceSendMode::Auto,
        sensitivity_db: sensitivity_flag
            || (config.app.voice_vad_threshold_db - (-35.0)).abs() > 0.01,
        wake_word: wake_word_flag || config.wake_word,
        wake_word_sensitivity: wake_word_sensitivity_flag
            || (config.wake_word_sensitivity - crate::config::DEFAULT_WAKE_WORD_SENSITIVITY).abs()
                > 0.001,
        wake_word_cooldown_ms: wake_word_cooldown_flag
            || config.wake_word_cooldown_ms != crate::config::DEFAULT_WAKE_WORD_COOLDOWN_MS,
        latency_display: latency_display_flag
            || config.latency_display != LatencyDisplayMode::Short,
    }
}

/// Detect which CLI flags were explicitly provided.
pub(crate) fn detect_explicit_flags(config: &crate::config::OverlayConfig) -> CliExplicitFlags {
    let args: Vec<String> = env::args().skip(1).collect();
    detect_explicit_flags_with_args(config, &args)
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    #[test]
    fn parse_empty_config() {
        let config = parse_user_config("");
        assert_eq!(config, UserConfig::default());
    }

    #[test]
    fn parse_full_config() {
        let content = r#"
# VoiceTerm persistent user config
theme = "coral"
hud_style = "minimal"
hud_border_style = "rounded"
hud_right_panel = "dots"
hud_right_panel_recording_only = true
auto_voice = false
voice_send_mode = "insert"
sensitivity_db = -40.0
wake_word = true
wake_word_sensitivity = 0.70
wake_word_cooldown_ms = 3000
latency_display = "off"
macros_enabled = true
"#;
        let config = parse_user_config(content);
        assert_eq!(config.theme.as_deref(), Some("coral"));
        assert_eq!(config.hud_style.as_deref(), Some("minimal"));
        assert_eq!(config.hud_border_style.as_deref(), Some("rounded"));
        assert_eq!(config.hud_right_panel.as_deref(), Some("dots"));
        assert_eq!(config.hud_right_panel_recording_only, Some(true));
        assert_eq!(config.auto_voice, Some(false));
        assert_eq!(config.voice_send_mode.as_deref(), Some("insert"));
        assert_eq!(config.sensitivity_db, Some(-40.0));
        assert_eq!(config.wake_word, Some(true));
        assert_eq!(config.wake_word_sensitivity, Some(0.70));
        assert_eq!(config.wake_word_cooldown_ms, Some(3000));
        assert_eq!(config.latency_display.as_deref(), Some("off"));
        assert_eq!(config.macros_enabled, Some(true));
    }

    #[test]
    fn parse_ignores_comments_and_unknown_keys() {
        let content = "# comment\nunknown_key = \"value\"\ntheme = \"nord\"\n";
        let config = parse_user_config(content);
        assert_eq!(config.theme.as_deref(), Some("nord"));
    }

    #[test]
    fn serialize_roundtrips() {
        let config = UserConfig {
            theme: Some("catppuccin".to_string()),
            hud_style: Some("full".to_string()),
            hud_border_style: Some("double".to_string()),
            hud_right_panel: Some("heartbeat".to_string()),
            hud_right_panel_recording_only: Some(false),
            auto_voice: Some(true),
            voice_send_mode: Some("auto".to_string()),
            sensitivity_db: Some(-35.0),
            wake_word: Some(false),
            wake_word_sensitivity: Some(0.55),
            wake_word_cooldown_ms: Some(2000),
            latency_display: Some("short".to_string()),
            macros_enabled: Some(false),
            memory_mode: Some("assist".to_string()),
        };
        let serialized = serialize_user_config(&config);
        let reparsed = parse_user_config(&serialized);
        assert_eq!(config.theme, reparsed.theme);
        assert_eq!(config.hud_style, reparsed.hud_style);
        assert_eq!(config.hud_border_style, reparsed.hud_border_style);
        assert_eq!(config.hud_right_panel, reparsed.hud_right_panel);
        assert_eq!(
            config.hud_right_panel_recording_only,
            reparsed.hud_right_panel_recording_only
        );
        assert_eq!(config.auto_voice, reparsed.auto_voice);
        assert_eq!(config.voice_send_mode, reparsed.voice_send_mode);
        assert_eq!(config.wake_word, reparsed.wake_word);
        assert_eq!(config.latency_display, reparsed.latency_display);
        assert_eq!(config.macros_enabled, reparsed.macros_enabled);
    }

    #[test]
    fn parse_bool_values() {
        assert_eq!(parse_bool("true"), Some(true));
        assert_eq!(parse_bool("True"), Some(true));
        assert_eq!(parse_bool("TRUE"), Some(true));
        assert_eq!(parse_bool("1"), Some(true));
        assert_eq!(parse_bool("yes"), Some(true));
        assert_eq!(parse_bool("false"), Some(false));
        assert_eq!(parse_bool("0"), Some(false));
        assert_eq!(parse_bool("no"), Some(false));
        assert_eq!(parse_bool("maybe"), None);
    }

    #[test]
    fn serialize_only_set_fields() {
        let config = UserConfig {
            theme: Some("coral".to_string()),
            ..Default::default()
        };
        let serialized = serialize_user_config(&config);
        assert!(serialized.contains("theme = \"coral\""));
        assert!(!serialized.contains("hud_style"));
        assert!(!serialized.contains("auto_voice"));
    }

    #[test]
    fn save_and_load_roundtrip_via_env() {
        use std::sync::{Mutex, OnceLock};
        use std::time::{SystemTime, UNIX_EPOCH};

        static ENV_GUARD: OnceLock<Mutex<()>> = OnceLock::new();
        let _guard = ENV_GUARD
            .get_or_init(|| Mutex::new(()))
            .lock()
            .unwrap_or_else(|e| e.into_inner());

        let millis = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_millis())
            .unwrap_or(0);
        let dir = env::temp_dir().join(format!("voiceterm_config_test_{millis}"));
        env::set_var(CONFIG_DIR_ENV, &dir);

        let config = UserConfig {
            theme: Some("dracula".to_string()),
            auto_voice: Some(true),
            sensitivity_db: Some(-42.5),
            ..Default::default()
        };
        save_user_config(&config);

        let loaded = load_user_config();
        assert_eq!(loaded.theme.as_deref(), Some("dracula"));
        assert_eq!(loaded.auto_voice, Some(true));
        assert_eq!(loaded.sensitivity_db, Some(-42.5));

        env::remove_var(CONFIG_DIR_ENV);
        let _ = fs::remove_dir_all(dir);
    }

    #[test]
    fn default_config_is_all_none() {
        let config = UserConfig::default();
        assert!(config.theme.is_none());
        assert!(config.hud_style.is_none());
        assert!(config.auto_voice.is_none());
        assert!(config.sensitivity_db.is_none());
        assert!(config.wake_word.is_none());
        assert!(config.macros_enabled.is_none());
    }

    #[test]
    fn parse_toml_value_handles_edge_cases() {
        assert!(parse_toml_value("").is_none());
        assert!(parse_toml_value("# comment").is_none());
        assert!(parse_toml_value("[section]").is_none());
        let (key, value) = parse_toml_value("key = value").unwrap();
        assert_eq!(key, "key");
        assert_eq!(value, "value");
        let (key, value) = parse_toml_value("  key  =  \"value\"  ").unwrap();
        assert_eq!(key, "key");
        assert_eq!(value, "value");
    }

    #[test]
    fn detect_explicit_flags_marks_default_value_flags_as_explicit() {
        let cfg = crate::config::OverlayConfig::parse_from([
            "voiceterm",
            "--voice-send-mode",
            "auto",
            "--latency-display",
            "short",
            "--hud-style",
            "full",
        ]);
        let args = vec![
            "--voice-send-mode".to_string(),
            "auto".to_string(),
            "--latency-display".to_string(),
            "short".to_string(),
            "--hud-style".to_string(),
            "full".to_string(),
        ];
        let explicit = detect_explicit_flags_with_args(&cfg, &args);
        assert!(explicit.voice_send_mode);
        assert!(explicit.latency_display);
        assert!(explicit.hud_style);
    }

    #[test]
    fn apply_user_config_to_status_state_restores_macros_flag() {
        let mut status = crate::status_line::StatusLineState::new();
        status.macros_enabled = false;
        let cfg = UserConfig {
            macros_enabled: Some(true),
            ..Default::default()
        };
        apply_user_config_to_status_state(&cfg, &mut status);
        assert!(status.macros_enabled);
    }
}
