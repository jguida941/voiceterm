//! Voice-pipeline capability logic so UI labels match the active capture path.

pub(super) fn using_native_pipeline(has_transcriber: bool, has_recorder: bool) -> bool {
    has_transcriber && has_recorder
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn using_native_pipeline_requires_both_components() {
        assert!(!using_native_pipeline(false, false));
        assert!(!using_native_pipeline(true, false));
        assert!(!using_native_pipeline(false, true));
        assert!(using_native_pipeline(true, true));
    }

    #[test]
    fn native_pipeline_matches_voice_source() {
        use voiceterm::VoiceCaptureSource;
        let native = VoiceCaptureSource::Native;
        let python = VoiceCaptureSource::Python;
        assert_ne!(native, python);
    }
}
