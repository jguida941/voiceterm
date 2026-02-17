//! Auto-rearm and post-message finalization helpers for voice drain.

use super::*;
use voiceterm::log_debug;

pub(super) fn should_rearm_after_transcript(
    auto_voice_enabled: bool,
    transcript_mode: VoiceSendMode,
    pending_transcript_count: usize,
    voice_manager_idle: bool,
) -> bool {
    if !auto_voice_enabled || !voice_manager_idle {
        return false;
    }
    match transcript_mode {
        // Insert mode should rearm only when we are fully caught up.
        VoiceSendMode::Insert => pending_transcript_count == 0,
        // Auto-send mode should keep listening while the queue has headroom.
        VoiceSendMode::Auto => {
            pending_transcript_count < crate::transcript::MAX_PENDING_TRANSCRIPTS
        }
    }
}

pub(super) fn should_rearm_after_empty(auto_voice_enabled: bool, voice_manager_idle: bool) -> bool {
    auto_voice_enabled && voice_manager_idle
}

pub(super) struct AutoRearmContext<'a> {
    pub(super) voice_manager: &'a mut VoiceManager,
    pub(super) writer_tx: &'a Sender<WriterMessage>,
    pub(super) status_clear_deadline: &'a mut Option<Instant>,
    pub(super) current_status: &'a mut Option<String>,
    pub(super) status_state: &'a mut StatusLineState,
    pub(super) last_auto_trigger_at: &'a mut Option<Instant>,
    pub(super) recording_started_at: &'a mut Option<Instant>,
    pub(super) preview_clear_deadline: &'a mut Option<Instant>,
    pub(super) last_meter_update: &'a mut Instant,
    pub(super) now: Instant,
}

fn try_rearm_auto_capture(ctx: &mut AutoRearmContext<'_>) {
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

pub(super) fn maybe_rearm_auto_after_transcript<S: TranscriptSession>(
    transcript_mode: VoiceSendMode,
    ctx: &mut super::transcript_delivery::TranscriptDeliveryContext<'_, S>,
) {
    if !should_rearm_after_transcript(
        ctx.auto_voice_enabled,
        transcript_mode,
        ctx.pending_transcripts.len(),
        ctx.voice_manager.is_idle(),
    ) {
        return;
    }

    let mut rearm_ctx = AutoRearmContext {
        voice_manager: ctx.voice_manager,
        writer_tx: ctx.writer_tx,
        status_clear_deadline: ctx.status_clear_deadline,
        current_status: ctx.current_status,
        status_state: ctx.status_state,
        last_auto_trigger_at: ctx.last_auto_trigger_at,
        recording_started_at: ctx.recording_started_at,
        preview_clear_deadline: ctx.preview_clear_deadline,
        last_meter_update: ctx.last_meter_update,
        now: ctx.now,
    };
    try_rearm_auto_capture(&mut rearm_ctx);
}

pub(super) fn maybe_rearm_auto_after_empty(
    ctx: &mut AutoRearmContext<'_>,
    auto_voice_enabled: bool,
) {
    if !should_rearm_after_empty(auto_voice_enabled, ctx.voice_manager.is_idle()) {
        return;
    }
    try_rearm_auto_capture(ctx);
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn should_rearm_after_transcript_insert_requires_empty_queue() {
        assert!(should_rearm_after_transcript(
            true,
            VoiceSendMode::Insert,
            0,
            true
        ));
        assert!(!should_rearm_after_transcript(
            true,
            VoiceSendMode::Insert,
            1,
            true
        ));
    }

    #[test]
    fn should_rearm_after_transcript_auto_allows_queue_headroom() {
        assert!(should_rearm_after_transcript(
            true,
            VoiceSendMode::Auto,
            crate::transcript::MAX_PENDING_TRANSCRIPTS - 1,
            true
        ));
        assert!(!should_rearm_after_transcript(
            true,
            VoiceSendMode::Auto,
            crate::transcript::MAX_PENDING_TRANSCRIPTS,
            true
        ));
    }

    #[test]
    fn should_rearm_after_transcript_requires_auto_voice_and_idle_manager() {
        assert!(!should_rearm_after_transcript(
            false,
            VoiceSendMode::Auto,
            0,
            true
        ));
        assert!(!should_rearm_after_transcript(
            true,
            VoiceSendMode::Auto,
            0,
            false
        ));
    }

    #[test]
    fn should_rearm_after_empty_requires_auto_voice_and_idle_manager() {
        assert!(should_rearm_after_empty(true, true));
        assert!(!should_rearm_after_empty(false, true));
        assert!(!should_rearm_after_empty(true, false));
    }
}
