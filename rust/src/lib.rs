//! Shared VoiceTerm library exports that keep binaries aligned on common behavior.

pub mod agent_runtime;
pub mod audio;
pub mod auth;
pub mod backend;
pub mod config;
pub mod doctor;
mod lock;
pub mod mic_meter;
mod process_signal;
pub mod pty_session;
mod runtime_support;
pub mod stt;
mod telemetry;
pub mod terminal_restore;
pub mod utf8_safe;
#[cfg(feature = "vad_earshot")]
pub mod vad_earshot;
pub mod voice;

pub(crate) use lock::lock_or_recover;
pub use runtime_support::{
    crash_log_path, init_logging, log_debug, log_debug_content, log_file_path, log_panic,
};
pub(crate) use runtime_support::{run_python_transcription, PipelineJsonResult};
#[cfg(test)]
pub(crate) use runtime_support::{set_logging_for_tests, PipelineMetrics};
pub use voice::{VoiceCaptureSource, VoiceCaptureTrigger, VoiceError, VoiceJob, VoiceJobMessage};
