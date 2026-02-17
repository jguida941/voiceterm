//! Auto-rearm and post-message finalization helpers for voice drain.

use super::*;
use voiceterm::log_debug;

pub(super) fn maybe_rearm_auto_after_insert<S: TranscriptSession>(
    transcript_mode: VoiceSendMode,
    ctx: &mut super::transcript_delivery::TranscriptDeliveryContext<'_, S>,
) {
    if !ctx.auto_voice_enabled
        || transcript_mode != VoiceSendMode::Insert
        || !ctx.pending_transcripts.is_empty()
        || !ctx.voice_manager.is_idle()
    {
        return;
    }

    if let Err(err) = super::super::manager::start_voice_capture(
        ctx.voice_manager,
        voiceterm::VoiceCaptureTrigger::Auto,
        ctx.writer_tx,
        ctx.status_clear_deadline,
        ctx.current_status,
        ctx.status_state,
    ) {
        log_debug(&format!("auto voice capture failed: {err:#}"));
    } else {
        *ctx.last_auto_trigger_at = Some(ctx.now);
        *ctx.recording_started_at = Some(ctx.now);
        reset_capture_visuals(
            ctx.status_state,
            ctx.preview_clear_deadline,
            ctx.last_meter_update,
        );
    }
}

pub(super) fn finalize_drain_state(
    prompt_tracker: &mut PromptTracker,
    auto_voice_enabled: bool,
    rearm_auto: bool,
    now: Instant,
    status_state: &StatusLineState,
    recording_started_at: &mut Option<Instant>,
) {
    if auto_voice_enabled && rearm_auto {
        prompt_tracker.note_activity(now);
    }
    if status_state.recording_state != RecordingState::Recording {
        *recording_started_at = None;
    }
}
