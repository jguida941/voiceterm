use clap::{Parser, ValueEnum};
use rust_tui::config::AppConfig;
use std::path::PathBuf;

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum)]
pub(crate) enum VoiceSendMode {
    Auto,
    Insert,
}

#[derive(Debug, Parser, Clone)]
#[command(about = "Codex Voice", author, version)]
pub(crate) struct OverlayConfig {
    #[command(flatten)]
    pub(crate) app: AppConfig,

    /// Regex used to detect the Codex prompt line (overrides auto-detection)
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
}
