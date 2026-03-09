//! Standalone one-shot voice capture for slash-command workflows.

use anyhow::{anyhow, bail, Result};
use std::io::{self, Write};
use std::sync::{Arc, Mutex};
use voiceterm::{audio, log_debug, stt, voice, VoiceJobMessage};

use crate::config::{CaptureOnceFormat, OverlayConfig};

type SharedRecorder = Arc<Mutex<audio::Recorder>>;
type SharedTranscriber = Arc<Mutex<stt::Transcriber>>;
type CaptureComponents = (Option<SharedRecorder>, Option<SharedTranscriber>);

pub(crate) fn run_capture_once(config: &OverlayConfig) -> Result<()> {
    let mut stdout = io::stdout().lock();
    run_capture_once_with(config, &mut stdout, capture_once_message)
}

fn run_capture_once_with<W, F>(config: &OverlayConfig, writer: &mut W, capture: F) -> Result<()>
where
    W: Write,
    F: FnOnce(&voiceterm::config::AppConfig) -> Result<VoiceJobMessage>,
{
    let message = capture(&config.app)?;
    write_capture_once_message(writer, config.capture_once_format, message)
}

fn capture_once_message(config: &voiceterm::config::AppConfig) -> Result<VoiceJobMessage> {
    let (recorder, transcriber) = build_capture_components(config)?;
    let job = voice::start_voice_job(recorder, transcriber, config.clone(), None);
    job.receiver
        .recv()
        .map_err(|_| anyhow!("voice capture worker disconnected before returning a result"))
}

fn build_capture_components(config: &voiceterm::config::AppConfig) -> Result<CaptureComponents> {
    let Some(model_path) = config.whisper_model_path.as_deref() else {
        if config.no_python_fallback {
            bail!("Native Whisper model not configured and --no-python-fallback is set.");
        }
        return Ok((None, None));
    };

    let transcriber = Arc::new(Mutex::new(stt::Transcriber::new(model_path)?));
    let recorder = match audio::Recorder::new(config.input_device.as_deref()) {
        Ok(recorder) => Some(Arc::new(Mutex::new(recorder))),
        Err(err) if config.no_python_fallback => {
            return Err(anyhow!(
                "Audio recorder unavailable and --no-python-fallback is set: {err:#}"
            ));
        }
        Err(err) => {
            log_debug(&format!(
                "standalone capture: audio recorder unavailable ({err:#}); falling back to python pipeline"
            ));
            None
        }
    };

    Ok((recorder, Some(transcriber)))
}

fn write_capture_once_message<W: Write>(
    writer: &mut W,
    format: CaptureOnceFormat,
    message: VoiceJobMessage,
) -> Result<()> {
    match message {
        VoiceJobMessage::Transcript { text, .. } => write_transcript(writer, format, &text),
        VoiceJobMessage::Empty { source, .. } => {
            bail!("voice capture produced no speech ({})", source.label())
        }
        VoiceJobMessage::Error(err) => bail!("voice capture failed: {err}"),
    }
}

fn write_transcript<W: Write>(writer: &mut W, format: CaptureOnceFormat, text: &str) -> Result<()> {
    match format {
        CaptureOnceFormat::Text => writeln!(writer, "{text}")?,
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;
    use voiceterm::{VoiceCaptureSource, VoiceError};

    use crate::config::OverlayConfig;

    #[test]
    fn run_capture_once_writes_text_output() {
        let config = OverlayConfig::parse_from(["test-app", "--capture-once"]);
        let mut output = Vec::new();

        run_capture_once_with(&config, &mut output, |_| {
            Ok(VoiceJobMessage::Transcript {
                text: "captured prompt".to_string(),
                source: VoiceCaptureSource::Python,
                metrics: None,
            })
        })
        .expect("standalone capture should succeed");

        assert_eq!(
            String::from_utf8(output).expect("utf8 output"),
            "captured prompt\n"
        );
    }

    #[test]
    fn run_capture_once_rejects_empty_transcript() {
        let config = OverlayConfig::parse_from(["test-app", "--capture-once"]);
        let mut output = Vec::new();

        let err = run_capture_once_with(&config, &mut output, |_| {
            Ok(VoiceJobMessage::Empty {
                source: VoiceCaptureSource::Native,
                metrics: None,
            })
        })
        .expect_err("empty capture should fail");

        assert!(err.to_string().contains("no speech"));
        assert!(output.is_empty());
    }

    #[test]
    fn run_capture_once_surfaces_voice_errors() {
        let config = OverlayConfig::parse_from(["test-app", "--capture-once"]);
        let mut output = Vec::new();

        let err = run_capture_once_with(&config, &mut output, |_| {
            Ok(VoiceJobMessage::Error(VoiceError::Message(
                "mic unavailable".to_string(),
            )))
        })
        .expect_err("capture error should fail");

        assert!(err.to_string().contains("mic unavailable"));
        assert!(output.is_empty());
    }

    #[test]
    fn capture_once_requires_native_model_when_python_fallback_disabled() {
        let config = voiceterm::config::AppConfig::parse_from(["test-app", "--no-python-fallback"]);

        let err = capture_once_message(&config).expect_err("missing model should fail");
        assert!(
            err.to_string()
                .contains("Native Whisper model not configured"),
            "unexpected error: {err}"
        );
    }
}
