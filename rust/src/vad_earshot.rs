//! Earshot adapter so VAD engine selection stays behind one stable interface.

use crate::audio::{VadDecision, VadEngine};
use crate::config::VoicePipelineConfig;
use earshot::{VoiceActivityDetector, VoiceActivityProfile};

/// Thin wrapper that adapts `earshot` to the crate's `VadEngine` trait.
pub struct EarshotVad {
    detector: VoiceActivityDetector,
    frame_samples: usize,
    scratch: Vec<i16>,
}

fn float_sample_to_i16(sample: f32) -> i16 {
    let clamped = sample.clamp(-1.0, 1.0);
    if clamped >= 0.0 {
        (clamped * i16::MAX as f32).round() as i16
    } else {
        (clamped * 32_768.0).round() as i16
    }
}

impl EarshotVad {
    /// Build an Earshot-backed VAD using thresholds/frame sizing from pipeline config.
    #[must_use]
    pub fn from_config(cfg: &VoicePipelineConfig) -> Self {
        let profile = match cfg.vad_threshold_db {
            t if t <= -50.0 => VoiceActivityProfile::VERY_AGGRESSIVE,
            t if t <= -40.0 => VoiceActivityProfile::AGGRESSIVE,
            t if t <= -30.0 => VoiceActivityProfile::LBR,
            _ => VoiceActivityProfile::QUALITY,
        };
        let frame_ms = cfg.vad_frame_ms.clamp(10, 30) as usize;
        let frame_samples = ((cfg.sample_rate as usize) * frame_ms) / 1000;
        Self {
            detector: VoiceActivityDetector::new(profile),
            frame_samples: frame_samples.max(160),
            scratch: Vec::new(),
        }
    }
}

impl VadEngine for EarshotVad {
    fn process_frame(&mut self, samples: &[f32]) -> VadDecision {
        if samples.is_empty() {
            return VadDecision::Uncertain;
        }
        self.scratch.clear();
        self.scratch.reserve(self.frame_samples);
        for chunk in samples.iter().copied() {
            self.scratch.push(float_sample_to_i16(chunk));
        }
        if self.scratch.len() < self.frame_samples {
            self.scratch.resize(self.frame_samples, 0);
        } else if self.scratch.len() > self.frame_samples {
            self.scratch.truncate(self.frame_samples);
        }
        match self.detector.predict_16khz(&self.scratch) {
            Ok(true) => VadDecision::Speech,
            Ok(false) => VadDecision::Silence,
            Err(_) => VadDecision::Uncertain,
        }
    }

    fn reset(&mut self) {
        self.detector.reset();
    }

    fn name(&self) -> &'static str {
        "earshot_vad"
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::audio::{VadDecision, VadEngine};
    use crate::config::{VadEngineKind, VoicePipelineConfig};

    fn base_cfg() -> VoicePipelineConfig {
        VoicePipelineConfig {
            sample_rate: 16_000,
            max_capture_ms: 10_000,
            silence_tail_ms: 500,
            min_speech_ms_before_stt_start: 200,
            lookback_ms: 500,
            buffer_ms: 10_000,
            channel_capacity: 64,
            stt_timeout_ms: 2_500,
            vad_threshold_db: -40.0,
            vad_frame_ms: 20,
            vad_smoothing_frames: 3,
            python_fallback_allowed: true,
            vad_engine: VadEngineKind::Earshot,
        }
    }

    #[test]
    fn from_config_clamps_frame_window_and_applies_minimum_sample_floor() {
        let mut cfg = base_cfg();
        cfg.sample_rate = 8_000;
        cfg.vad_frame_ms = 10;
        let vad = EarshotVad::from_config(&cfg);
        assert_eq!(vad.frame_samples, 160);

        cfg.sample_rate = 48_000;
        cfg.vad_frame_ms = 40;
        let vad = EarshotVad::from_config(&cfg);
        assert_eq!(vad.frame_samples, 1_440);
    }

    #[test]
    fn process_frame_empty_input_is_uncertain() {
        let cfg = base_cfg();
        let mut vad = EarshotVad::from_config(&cfg);
        assert_eq!(vad.process_frame(&[]), VadDecision::Uncertain);
        assert!(vad.scratch.is_empty());
    }

    #[test]
    fn process_frame_clamps_samples_and_zero_pads_short_frames() {
        let cfg = base_cfg();
        let mut vad = EarshotVad::from_config(&cfg);
        let decision = vad.process_frame(&[-2.0, -1.0, 0.0, 1.0, 2.0]);
        assert!(matches!(
            decision,
            VadDecision::Speech | VadDecision::Silence | VadDecision::Uncertain
        ));
        assert_eq!(vad.scratch.len(), vad.frame_samples);
        assert_eq!(vad.scratch[0], -32_768);
        assert_eq!(vad.scratch[1], -32_768);
        assert_eq!(vad.scratch[2], 0);
        assert_eq!(vad.scratch[3], 32_767);
        assert_eq!(vad.scratch[4], 32_767);
        assert!(vad.scratch[5..].iter().all(|&s| s == 0));
    }

    #[test]
    fn float_sample_to_i16_saturates_endpoints() {
        assert_eq!(float_sample_to_i16(-2.0), i16::MIN);
        assert_eq!(float_sample_to_i16(-1.0), i16::MIN);
        assert_eq!(float_sample_to_i16(0.0), 0);
        assert_eq!(float_sample_to_i16(1.0), i16::MAX);
        assert_eq!(float_sample_to_i16(2.0), i16::MAX);
    }

    #[test]
    fn process_frame_truncates_long_frames_to_configured_window() {
        let cfg = base_cfg();
        let mut vad = EarshotVad::from_config(&cfg);
        let long_frame = vec![0.5_f32; vad.frame_samples + 23];
        let _ = vad.process_frame(&long_frame);
        assert_eq!(vad.scratch.len(), vad.frame_samples);
        assert!(vad.scratch.iter().all(|&s| s == 16_384));
    }

    #[test]
    fn reset_restores_detector_state_to_match_fresh_instance() {
        let cfg = base_cfg();
        let mut warmed = EarshotVad::from_config(&cfg);
        let mut fresh = EarshotVad::from_config(&cfg);

        let loud = vec![1.0_f32; warmed.frame_samples];
        let silent = vec![0.0_f32; warmed.frame_samples];
        for _ in 0..5 {
            let _ = warmed.process_frame(&loud);
        }
        warmed.reset();

        let after_reset = warmed.process_frame(&silent);
        let from_fresh = fresh.process_frame(&silent);
        assert_eq!(after_reset, from_fresh);
    }

    #[test]
    fn name_reports_stable_identifier() {
        let cfg = base_cfg();
        let vad = EarshotVad::from_config(&cfg);
        assert_eq!(vad.name(), "earshot_vad");
    }
}
