//! Threshold recommendation logic so mic calibration maps to usable VAD settings.

use anyhow::Result;

pub(super) fn recommend_threshold(ambient_db: f32, speech_db: f32) -> (f32, Option<&'static str>) {
    voiceterm::mic_meter::recommend_threshold(ambient_db, speech_db)
}

pub(super) fn validate_sample_ms(label: &str, value: u64) -> Result<()> {
    voiceterm::mic_meter::validate_sample_ms(label, value)
}
