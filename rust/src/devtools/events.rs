//! Stable dev-event schema used by runtime capture and future offline analysis.

use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::audio::CaptureMetrics;
use crate::VoiceCaptureSource;

pub const DEV_EVENT_SCHEMA_VERSION: u16 = 1;
pub const DEV_EVENT_SOURCE_UNKNOWN: DevCaptureSource = DevCaptureSource::Unknown;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DevCaptureSource {
    Native,
    Python,
    Unknown,
}

impl From<VoiceCaptureSource> for DevCaptureSource {
    fn from(source: VoiceCaptureSource) -> Self {
        match source {
            VoiceCaptureSource::Native => Self::Native,
            VoiceCaptureSource::Python => Self::Python,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DevEventKind {
    Transcript,
    Empty,
    Error,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DevEvent {
    pub schema_version: u16,
    pub event_id: u64,
    pub timestamp_unix_ms: u64,
    pub kind: DevEventKind,
    pub source: DevCaptureSource,
    pub transcript_chars: usize,
    pub transcript_words: u32,
    pub latency_ms: Option<u32>,
    pub speech_ms: Option<u32>,
    pub dropped_frames: u32,
    pub error_message: Option<String>,
}

impl DevEvent {
    pub fn transcript(
        event_id: u64,
        source: VoiceCaptureSource,
        text: &str,
        metrics: Option<&CaptureMetrics>,
    ) -> Self {
        Self {
            schema_version: DEV_EVENT_SCHEMA_VERSION,
            event_id,
            timestamp_unix_ms: now_unix_ms(),
            kind: DevEventKind::Transcript,
            source: source.into(),
            transcript_chars: text.chars().count(),
            transcript_words: text.split_whitespace().count() as u32,
            latency_ms: capture_latency_ms(metrics),
            speech_ms: capture_speech_ms(metrics),
            dropped_frames: capture_dropped_frames(metrics),
            error_message: None,
        }
    }

    pub fn empty(
        event_id: u64,
        source: VoiceCaptureSource,
        metrics: Option<&CaptureMetrics>,
    ) -> Self {
        Self {
            schema_version: DEV_EVENT_SCHEMA_VERSION,
            event_id,
            timestamp_unix_ms: now_unix_ms(),
            kind: DevEventKind::Empty,
            source: source.into(),
            transcript_chars: 0,
            transcript_words: 0,
            latency_ms: capture_latency_ms(metrics),
            speech_ms: capture_speech_ms(metrics),
            dropped_frames: capture_dropped_frames(metrics),
            error_message: None,
        }
    }

    pub fn error(event_id: u64, message: &str) -> Self {
        Self {
            schema_version: DEV_EVENT_SCHEMA_VERSION,
            event_id,
            timestamp_unix_ms: now_unix_ms(),
            kind: DevEventKind::Error,
            source: DEV_EVENT_SOURCE_UNKNOWN,
            transcript_chars: 0,
            transcript_words: 0,
            latency_ms: None,
            speech_ms: None,
            dropped_frames: 0,
            error_message: Some(message.to_string()),
        }
    }
}

fn now_unix_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis().min(u128::from(u64::MAX)) as u64)
        .unwrap_or(0)
}

fn capture_latency_ms(metrics: Option<&CaptureMetrics>) -> Option<u32> {
    metrics
        .and_then(|value| (value.transcribe_ms > 0).then_some(value.transcribe_ms))
        .map(clamp_u64_to_u32)
}

fn capture_speech_ms(metrics: Option<&CaptureMetrics>) -> Option<u32> {
    metrics
        .and_then(|value| (value.speech_ms > 0).then_some(value.speech_ms))
        .map(clamp_u64_to_u32)
}

fn capture_dropped_frames(metrics: Option<&CaptureMetrics>) -> u32 {
    metrics
        .map(|value| value.frames_dropped.min(u32::MAX as usize) as u32)
        .unwrap_or(0)
}

fn clamp_u64_to_u32(value: u64) -> u32 {
    value.min(u64::from(u32::MAX)) as u32
}
