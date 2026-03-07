//! Audio wake-word detector: microphone capture, VAD gating, and STT-based
//! hotword recognition for a single listen cycle.

use anyhow::{anyhow, Result};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use voiceterm::{audio, config::AppConfig};

use super::matcher::{
    detect_wake_event_from_normalized, log_wake_transcript_decision, normalize_for_hotword_match,
};
use super::WakeWordEvent;

const WAKE_CAPTURE_MAX_MS: u64 = 8000;
const WAKE_CAPTURE_SILENCE_TAIL_MS: u64 = 320;
const WAKE_CAPTURE_MIN_SPEECH_MS: u64 = 80;
const WAKE_CAPTURE_LOOKBACK_MS: u64 = 300;
const WAKE_CAPTURE_BUFFER_MS: u64 = 1600;
const WAKE_CAPTURE_CHANNEL_CAPACITY: usize = 8;

pub(super) const WAKE_VAD_DB_AT_MIN_SENSITIVITY: f32 = -24.0;
pub(super) const WAKE_VAD_DB_AT_MAX_SENSITIVITY: f32 = -56.0;
pub(super) const WAKE_VAD_VOICE_HEADROOM_DB: f32 = 8.0;
pub(super) const WAKE_VAD_THRESHOLD_MIN_DB: f32 = -62.0;
pub(super) const WAKE_VAD_THRESHOLD_MAX_DB: f32 = -20.0;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(super) enum WakeListenOutcome {
    Detected(WakeWordEvent),
    NoDetection,
    NoAudio,
}

pub(super) struct AudioWakeDetector {
    recorder: audio::Recorder,
    transcriber: voiceterm::stt::Transcriber,
    app_config: AppConfig,
    vad_cfg: audio::VadConfig,
    vad_engine: Box<dyn audio::VadEngine + Send>,
}

impl AudioWakeDetector {
    pub(super) fn new(app_config: AppConfig, settings: super::WakeSettings) -> Result<Self> {
        let model_path = app_config
            .whisper_model_path
            .clone()
            .ok_or_else(|| anyhow!("no whisper model path configured for wake-word detector"))?;
        let recorder = audio::Recorder::new(app_config.input_device.as_deref())?;
        let transcriber = voiceterm::stt::Transcriber::new(&model_path)?;

        let mut pipeline_cfg = app_config.voice_pipeline_config();
        pipeline_cfg.max_capture_ms = WAKE_CAPTURE_MAX_MS;
        pipeline_cfg.silence_tail_ms = WAKE_CAPTURE_SILENCE_TAIL_MS;
        pipeline_cfg.min_speech_ms_before_stt_start = WAKE_CAPTURE_MIN_SPEECH_MS;
        pipeline_cfg.lookback_ms = WAKE_CAPTURE_LOOKBACK_MS;
        pipeline_cfg.buffer_ms = WAKE_CAPTURE_BUFFER_MS;
        pipeline_cfg.channel_capacity = WAKE_CAPTURE_CHANNEL_CAPACITY;
        pipeline_cfg.vad_threshold_db = settings.effective_vad_threshold_db;
        let vad_cfg = audio::VadConfig::from(&pipeline_cfg);
        let vad_engine = audio::create_vad_engine(&pipeline_cfg);

        Ok(Self {
            recorder,
            transcriber,
            app_config,
            vad_cfg,
            vad_engine,
        })
    }

    pub(super) fn listen_once(
        &mut self,
        capture_stop_flag: &Arc<AtomicBool>,
    ) -> Result<WakeListenOutcome> {
        capture_stop_flag.store(false, Ordering::Relaxed);
        self.vad_engine.reset();
        let capture = match self.recorder.record_with_vad(
            &self.vad_cfg,
            self.vad_engine.as_mut(),
            Some(capture_stop_flag.clone()),
            None,
        ) {
            Ok(capture) => capture,
            Err(err) => {
                if capture_stop_flag.load(Ordering::Relaxed) {
                    return Ok(WakeListenOutcome::NoDetection);
                }
                if is_expected_no_audio_error(&err) {
                    return Ok(WakeListenOutcome::NoAudio);
                }
                return Err(err);
            }
        };

        if capture_stop_flag.load(Ordering::Relaxed)
            || capture.audio.is_empty()
            || capture.metrics.speech_ms == 0
        {
            return Ok(WakeListenOutcome::NoDetection);
        }

        let transcript = self
            .transcriber
            .transcribe(&capture.audio, &self.app_config)?;
        let normalized = normalize_for_hotword_match(&transcript);
        let wake_event = detect_wake_event_from_normalized(&normalized);
        log_wake_transcript_decision(&transcript, &normalized, wake_event);
        Ok(match wake_event {
            Some(event) => WakeListenOutcome::Detected(event),
            None => WakeListenOutcome::NoDetection,
        })
    }
}

#[must_use = "sensitivity should map to a deterministic dB threshold"]
pub(super) fn sensitivity_to_wake_vad_threshold_db(sensitivity: f32) -> f32 {
    let normalized = sensitivity.clamp(super::WAKE_MIN_SENSITIVITY, super::WAKE_MAX_SENSITIVITY);
    WAKE_VAD_DB_AT_MIN_SENSITIVITY
        + (WAKE_VAD_DB_AT_MAX_SENSITIVITY - WAKE_VAD_DB_AT_MIN_SENSITIVITY) * normalized
}

#[must_use = "wake threshold should stay aligned with mic sensitivity defaults"]
pub(super) fn resolve_wake_vad_threshold_db(sensitivity: f32, voice_vad_threshold_db: f32) -> f32 {
    let mapped = sensitivity_to_wake_vad_threshold_db(sensitivity);
    let voice_aligned = (voice_vad_threshold_db - WAKE_VAD_VOICE_HEADROOM_DB)
        .clamp(WAKE_VAD_THRESHOLD_MIN_DB, WAKE_VAD_THRESHOLD_MAX_DB);
    mapped
        .min(voice_aligned)
        .clamp(WAKE_VAD_THRESHOLD_MIN_DB, WAKE_VAD_THRESHOLD_MAX_DB)
}

#[must_use = "capture error classification avoids noisy logs during silence"]
fn is_expected_no_audio_error(err: &anyhow::Error) -> bool {
    err.to_string().contains("no samples captured")
}
