pub const TARGET_RATE: u32 = 16_000;
pub const TARGET_CHANNELS: u32 = 1;

mod capture;
mod dispatch;
mod recorder;
mod resample;
#[cfg(test)]
mod tests;
mod vad;

pub use capture::{offline_capture_from_pcm, CaptureMetrics, CaptureResult, StopReason};
pub use recorder::Recorder;
pub use vad::{SimpleThresholdVad, VadConfig, VadDecision, VadEngine};
