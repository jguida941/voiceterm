//! Threshold recommendation logic so mic calibration maps to usable VAD settings.

use anyhow::{anyhow, Result};
use voiceterm::config::{MAX_MIC_METER_SAMPLE_MS, MIN_MIC_METER_SAMPLE_MS};

use super::{RECOMMENDED_CEILING_DB, RECOMMENDED_FLOOR_DB};

pub(super) fn recommend_threshold(ambient_db: f32, speech_db: f32) -> (f32, Option<&'static str>) {
    if speech_db <= ambient_db {
        let suggested = (ambient_db + 1.0).clamp(RECOMMENDED_FLOOR_DB, RECOMMENDED_CEILING_DB);
        return (
            suggested,
            Some("Speech is not louder than ambient noise; results may be unreliable."),
        );
    }

    let margin = speech_db - ambient_db;
    let guard = if margin >= 12.0 {
        6.0
    } else if margin >= 6.0 {
        3.0
    } else {
        1.5
    };

    let mut suggested = ambient_db + guard;
    if suggested > speech_db - 1.0 {
        suggested = (ambient_db + speech_db) / 2.0;
    }

    let warning = if margin < 6.0 {
        Some("Speech is close to ambient noise; consider a quieter room or closer mic.")
    } else {
        None
    };

    (
        suggested.clamp(RECOMMENDED_FLOOR_DB, RECOMMENDED_CEILING_DB),
        warning,
    )
}

pub(super) fn validate_sample_ms(label: &str, value: u64) -> Result<()> {
    if !(MIN_MIC_METER_SAMPLE_MS..=MAX_MIC_METER_SAMPLE_MS).contains(&value) {
        return Err(anyhow!(
            "--mic-meter-{label}-ms must be between {MIN_MIC_METER_SAMPLE_MS} and {MAX_MIC_METER_SAMPLE_MS} ms"
        ));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn recommend_threshold_non_louder_path_warns_and_clamps() {
        let (mid_range, mid_warning) = recommend_threshold(-30.0, -31.0);
        assert!((mid_range - -29.0).abs() < 0.01);
        assert!(mid_warning.is_some());

        let (floor_clamped, floor_warning) = recommend_threshold(-120.0, -130.0);
        assert_eq!(floor_clamped, RECOMMENDED_FLOOR_DB);
        assert!(floor_warning.is_some());

        let (ceiling_clamped, ceiling_warning) = recommend_threshold(4.0, 4.0);
        assert_eq!(ceiling_clamped, RECOMMENDED_CEILING_DB);
        assert!(ceiling_warning.is_some());
    }

    #[test]
    fn recommend_threshold_guard_branches_and_midpoint_fallback() {
        let (hi_margin, hi_warning) = recommend_threshold(-50.0, -38.0);
        assert!((hi_margin - -44.0).abs() < f32::EPSILON);
        assert!(hi_warning.is_none());

        let (mid_margin, mid_warning) = recommend_threshold(-50.0, -44.0);
        assert!((mid_margin - -47.0).abs() < f32::EPSILON);
        assert!(mid_warning.is_none());

        let (low_margin, low_warning) = recommend_threshold(-20.0, -18.0);
        assert!((low_margin - -19.0).abs() < 0.01);
        assert!(low_warning.is_some());

        let (edge, edge_warning) = recommend_threshold(-20.0, -17.5);
        assert!((edge - -18.5).abs() < 0.01);
        assert!(edge_warning.is_some());
    }

    #[test]
    fn validate_sample_ms_accepts_bounds_and_rejects_out_of_range() {
        assert!(validate_sample_ms("ambient", MIN_MIC_METER_SAMPLE_MS).is_ok());
        assert!(validate_sample_ms("speech", MAX_MIC_METER_SAMPLE_MS).is_ok());

        let below = validate_sample_ms("ambient", MIN_MIC_METER_SAMPLE_MS.saturating_sub(1))
            .expect_err("below minimum should fail");
        assert!(below.to_string().contains("--mic-meter-ambient-ms"));

        let above = validate_sample_ms("speech", MAX_MIC_METER_SAMPLE_MS + 1)
            .expect_err("above maximum should fail");
        assert!(above.to_string().contains("--mic-meter-speech-ms"));
    }
}
