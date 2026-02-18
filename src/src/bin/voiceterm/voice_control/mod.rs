//! Voice-capture subsystem wiring so start/stop/drain share consistent policy.

mod drain;
mod manager;
mod navigation;
mod pipeline;
mod transcript_preview;

const STATUS_TOAST_SECS: u64 = 2;
const PREVIEW_CLEAR_MS: u64 = 3000;
const TRANSCRIPT_PREVIEW_MAX: usize = 60;

pub(crate) use drain::{
    clear_capture_metrics, drain_voice_messages, reset_capture_visuals, VoiceDrainContext,
};
pub(crate) use manager::{start_voice_capture, VoiceManager};
