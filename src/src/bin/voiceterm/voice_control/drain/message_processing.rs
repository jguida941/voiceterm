//! Message-level helpers extracted from voice drain orchestration.

use super::*;
use crate::status_line::Pipeline;
use crate::transcript::send_transcript;
use crate::voice_control::STATUS_TOAST_SECS;
use crate::writer::set_status;
use voiceterm::log_debug;

pub(super) fn apply_macro_mode(
    text: &str,
    default_mode: VoiceSendMode,
    macros_enabled: bool,
    voice_macros: &VoiceMacros,
) -> (String, VoiceSendMode, Option<String>) {
    if !macros_enabled {
        return (text.to_string(), default_mode, None);
    }
    let expanded = voice_macros.apply(text, default_mode);
    let macro_note = expanded
        .matched_trigger
        .as_ref()
        .map(|trigger| format!("macro '{}'", trigger));
    (expanded.text, expanded.mode, macro_note)
}

pub(super) fn handle_voice_message(
    message: VoiceJobMessage,
    ctx: &mut VoiceMessageContext<'_, impl TranscriptSession>,
) {
    let VoiceMessageContext {
        config,
        session,
        writer_tx,
        status_clear_deadline,
        current_status,
        status_state,
        session_stats,
        auto_voice_enabled,
    } = ctx;
    let auto_voice_enabled = *auto_voice_enabled;
    match message {
        VoiceJobMessage::Transcript {
            text,
            source,
            metrics,
        } => {
            let duration_secs = metrics
                .as_ref()
                .map(|metrics| metrics.speech_ms as f32 / 1000.0)
                .unwrap_or(0.0);
            session_stats.record_transcript(duration_secs);
            status_state.recording_state = RecordingState::Idle;
            clear_capture_metrics(status_state);
            status_state.pipeline = match source {
                VoiceCaptureSource::Native => Pipeline::Rust,
                VoiceCaptureSource::Python => Pipeline::Python,
            };
            let drop_note = metrics
                .as_ref()
                .filter(|metrics| metrics.frames_dropped > 0)
                .map(|metrics| format!("dropped {} frames", metrics.frames_dropped));
            let status = if let Some(note) = drop_note {
                format!("Transcript ready ({note})")
            } else {
                "Transcript ready".to_string()
            };
            set_status(
                writer_tx,
                status_clear_deadline,
                current_status,
                status_state,
                &status,
                Some(Duration::from_secs(STATUS_TOAST_SECS)),
            );
            if let Err(err) = send_transcript(*session, &text, config.voice_send_mode) {
                log_debug(&format!("failed to send transcript: {err:#}"));
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    "Failed to send transcript (see log)",
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
            }
        }
        VoiceJobMessage::Empty { source, metrics } => {
            session_stats.record_empty();
            status_state.recording_state = RecordingState::Idle;
            clear_capture_metrics(status_state);
            status_state.pipeline = match source {
                VoiceCaptureSource::Native => Pipeline::Rust,
                VoiceCaptureSource::Python => Pipeline::Python,
            };
            let drop_note = metrics
                .as_ref()
                .filter(|metrics| metrics.frames_dropped > 0)
                .map(|metrics| format!("dropped {} frames", metrics.frames_dropped));
            if auto_voice_enabled {
                log_debug("auto voice capture detected no speech");
                // Don't show redundant "Auto-voice enabled" - the mode indicator shows it.
                // Only show a note if frames were dropped.
                if let Some(note) = drop_note {
                    set_status(
                        writer_tx,
                        status_clear_deadline,
                        current_status,
                        status_state,
                        &format!("Listening... ({note})"),
                        Some(Duration::from_secs(STATUS_TOAST_SECS)),
                    );
                }
            } else {
                let status = if let Some(note) = drop_note {
                    format!("No speech detected ({note})")
                } else {
                    "No speech detected".to_string()
                };
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    &status,
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
            }
        }
        VoiceJobMessage::Error(message) => {
            session_stats.record_error();
            status_state.recording_state = RecordingState::Idle;
            clear_capture_metrics(status_state);
            set_status(
                writer_tx,
                status_clear_deadline,
                current_status,
                status_state,
                "Voice capture error (see log)",
                Some(Duration::from_secs(STATUS_TOAST_SECS)),
            );
            log_debug(&format!("voice capture error: {message}"));
        }
    }
}

pub(super) fn update_last_latency(
    status_state: &mut StatusLineState,
    recording_started_at: Option<Instant>,
    metrics: Option<&voiceterm::audio::CaptureMetrics>,
    now: Instant,
) {
    #[inline]
    fn clamp_u64_to_u32(value: u64) -> u32 {
        value.min(u64::from(u32::MAX)) as u32
    }

    let elapsed_ms = recording_started_at
        .and_then(|started_at| now.checked_duration_since(started_at))
        .map(|elapsed| elapsed.as_millis().min(u128::from(u32::MAX)) as u32);

    let capture_ms = metrics
        .filter(|m| m.capture_ms > 0)
        .map(|m| clamp_u64_to_u32(m.capture_ms));
    let stt_ms = metrics
        .filter(|m| m.transcribe_ms > 0)
        .map(|m| clamp_u64_to_u32(m.transcribe_ms));
    let speech_ms = metrics
        .filter(|m| m.speech_ms > 0)
        .map(|m| clamp_u64_to_u32(m.speech_ms));

    // Trust mode: display only direct STT timing, never derived estimates.
    let latency_ms = stt_ms;
    let rtf_x1000 = match (stt_ms, speech_ms) {
        (Some(stt), Some(speech)) if speech > 0 => Some(
            (u64::from(stt) * 1000)
                .saturating_div(u64::from(speech))
                .min(u64::from(u32::MAX)) as u32,
        ),
        _ => None,
    };
    let speech_for_display = latency_ms.and(speech_ms);
    let rtf_for_display = latency_ms.and(rtf_x1000);
    status_state.last_latency_ms = latency_ms;
    status_state.last_latency_speech_ms = speech_for_display;
    status_state.last_latency_rtf_x1000 = rtf_for_display;
    status_state.last_latency_updated_at = latency_ms.map(|_| now);
    if let Some(sample) = latency_ms {
        status_state.push_latency_sample(sample);
    }

    let display_field = latency_ms
        .map(|v| v.to_string())
        .unwrap_or_else(|| "na".to_string());
    let capture_field = capture_ms
        .map(|v| v.to_string())
        .unwrap_or_else(|| "na".to_string());
    let stt_field = stt_ms
        .map(|v| v.to_string())
        .unwrap_or_else(|| "na".to_string());
    let speech_field = speech_ms
        .map(|v| v.to_string())
        .unwrap_or_else(|| "na".to_string());
    let rtf_field = rtf_x1000
        .map(|v| format!("{:.3}", v as f32 / 1000.0))
        .unwrap_or_else(|| "na".to_string());
    let elapsed_field = elapsed_ms
        .map(|v| v.to_string())
        .unwrap_or_else(|| "na".to_string());
    log_debug(&format!(
        "latency_audit|display_ms={display_field}|elapsed_ms={elapsed_field}|capture_ms={capture_field}|speech_ms={speech_field}|stt_ms={stt_field}|rtf={rtf_field}"
    ));
}

pub(super) fn clear_last_latency(status_state: &mut StatusLineState) {
    status_state.last_latency_ms = None;
    status_state.last_latency_speech_ms = None;
    status_state.last_latency_rtf_x1000 = None;
    status_state.last_latency_updated_at = None;
}

pub(super) fn format_transcript_preview(text: &str, max_len: usize) -> String {
    let trimmed = text.trim();
    if trimmed.is_empty() {
        return String::new();
    }
    let mut collapsed = String::new();
    let mut last_space = false;
    for ch in trimmed.chars() {
        if ch.is_whitespace() || ch.is_ascii_control() {
            if !last_space {
                collapsed.push(' ');
                last_space = true;
            }
        } else {
            collapsed.push(ch);
            last_space = false;
        }
    }
    let cleaned = collapsed.trim();
    let max_len = max_len.max(4);
    if cleaned.chars().count() > max_len {
        let keep = max_len.saturating_sub(3);
        let prefix: String = cleaned.chars().take(keep).collect();
        format!("{prefix}...")
    } else {
        cleaned.to_string()
    }
}
