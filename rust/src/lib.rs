//! Shared VoiceTerm library exports that keep binaries aligned on common behavior.

pub mod audio;
pub mod auth;
pub mod backend;
pub mod codex;
pub mod config;
pub mod devtools;
pub mod doctor;
pub mod ipc;
#[doc(hidden)]
pub mod legacy_ui;
mod lock;
pub mod mic_meter;
mod process_signal;
pub mod pty_session;
pub mod stt;
mod telemetry;
pub mod terminal_restore;
pub mod utf8_safe;
#[cfg(feature = "vad_earshot")]
pub mod vad_earshot;
pub mod voice;

mod legacy_tui;

#[doc(hidden)]
pub use legacy_tui::CodexApp;
pub use legacy_tui::{
    crash_log_path, init_logging, log_debug, log_debug_content, log_file_path, log_panic,
};
pub(crate) use legacy_tui::{run_python_transcription, PipelineJsonResult};
#[cfg(test)]
pub(crate) use legacy_tui::{set_logging_for_tests, PipelineMetrics};
pub(crate) use lock::lock_or_recover;
pub use voice::{VoiceCaptureSource, VoiceCaptureTrigger, VoiceError, VoiceJob, VoiceJobMessage};
