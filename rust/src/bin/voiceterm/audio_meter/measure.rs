//! Audio-level sampling so mic calibration reflects real ambient/speech levels.

use anyhow::Result;
use std::time::Duration;
use voiceterm::audio::Recorder;

use super::{AudioLevel, RECOMMENDED_FLOOR_DB};

#[inline]
fn rms_db(samples: &[f32]) -> f32 {
    if samples.is_empty() {
        return RECOMMENDED_FLOOR_DB;
    }
    let energy: f32 = samples.iter().map(|s| s * s).sum::<f32>() / samples.len() as f32;
    let rms = energy.sqrt().max(1e-6);
    20.0 * rms.log10()
}

#[inline]
fn peak_db(samples: &[f32]) -> f32 {
    if samples.is_empty() {
        return RECOMMENDED_FLOOR_DB;
    }
    let peak = samples
        .iter()
        .map(|s| s.abs())
        .fold(0.0_f32, f32::max)
        .max(1e-6);
    20.0 * peak.log10()
}

pub(super) fn measure(recorder: &Recorder, duration: Duration) -> Result<AudioLevel> {
    let samples = recorder.record_for(duration)?;
    Ok(AudioLevel {
        rms_db: rms_db(&samples),
        peak_db: peak_db(&samples),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rms_db_empty_returns_floor() {
        assert_eq!(rms_db(&[]), RECOMMENDED_FLOOR_DB);
    }

    #[test]
    fn rms_db_matches_known_amplitude() {
        let samples = vec![0.5_f32; 64];
        let rms = rms_db(&samples);
        let expected = 20.0 * 0.5_f32.log10();
        assert!(
            (rms - expected).abs() < 0.01,
            "rms={rms}, expected={expected}"
        );
    }

    #[test]
    fn peak_db_empty_returns_floor() {
        assert_eq!(peak_db(&[]), RECOMMENDED_FLOOR_DB);
    }

    #[test]
    fn peak_db_tracks_absolute_max_amplitude() {
        let samples = vec![-0.25_f32, 0.75_f32, -0.5_f32];
        let peak = peak_db(&samples);
        let expected = 20.0 * 0.75_f32.log10();
        assert!(
            (peak - expected).abs() < 0.01,
            "peak={peak}, expected={expected}"
        );
    }
}
