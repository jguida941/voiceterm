//! Transcript-specific delivery/queue handling extracted from voice drain orchestration.

use super::*;

pub(super) struct TranscriptDeliveryContext<'a, S: TranscriptSession> {
    pub(super) text: String,
    pub(super) source: VoiceCaptureSource,
    pub(super) metrics: Option<voiceterm::audio::CaptureMetrics>,
    pub(super) voice_manager: &'a mut VoiceManager,
    pub(super) config: &'a OverlayConfig,
    pub(super) voice_macros: &'a VoiceMacros,
    pub(super) session: &'a mut S,
    pub(super) writer_tx: &'a Sender<WriterMessage>,
    pub(super) status_clear_deadline: &'a mut Option<Instant>,
    pub(super) current_status: &'a mut Option<String>,
    pub(super) status_state: &'a mut StatusLineState,
    pub(super) session_stats: &'a mut SessionStats,
    pub(super) pending_transcripts: &'a mut VecDeque<PendingTranscript>,
    pub(super) prompt_tracker: &'a mut PromptTracker,
    pub(super) last_enter_at: &'a mut Option<Instant>,
    pub(super) now: Instant,
    pub(super) transcript_idle_timeout: Duration,
    pub(super) recording_started_at: &'a mut Option<Instant>,
    pub(super) preview_clear_deadline: &'a mut Option<Instant>,
    pub(super) last_meter_update: &'a mut Instant,
    pub(super) last_auto_trigger_at: &'a mut Option<Instant>,
    pub(super) auto_voice_enabled: bool,
    pub(super) sound_on_complete: bool,
}

pub(super) fn handle_transcript_message<S: TranscriptSession>(
    ctx: &mut TranscriptDeliveryContext<'_, S>,
) {
    super::message_processing::update_last_latency(
        ctx.status_state,
        *ctx.recording_started_at,
        ctx.metrics.as_ref(),
        ctx.now,
    );
    let ready = crate::transcript::transcript_ready(
        ctx.prompt_tracker,
        *ctx.last_enter_at,
        ctx.now,
        ctx.transcript_idle_timeout,
    );
    if ctx.auto_voice_enabled {
        ctx.prompt_tracker.note_activity(ctx.now);
    }
    ctx.status_state.recording_state = RecordingState::Idle;
    clear_capture_metrics(ctx.status_state);
    ctx.status_state.pipeline = match ctx.source {
        VoiceCaptureSource::Native => crate::status_line::Pipeline::Rust,
        VoiceCaptureSource::Python => crate::status_line::Pipeline::Python,
    };
    let preview = super::message_processing::format_transcript_preview(
        &ctx.text,
        super::super::TRANSCRIPT_PREVIEW_MAX,
    );
    if preview.is_empty() {
        ctx.status_state.transcript_preview = None;
        *ctx.preview_clear_deadline = None;
    } else {
        ctx.status_state.transcript_preview = Some(preview);
        *ctx.preview_clear_deadline =
            Some(ctx.now + Duration::from_millis(super::super::PREVIEW_CLEAR_MS));
    }
    let duration_secs = ctx
        .metrics
        .as_ref()
        .map(|metrics| metrics.speech_ms as f32 / 1000.0)
        .unwrap_or(0.0);
    ctx.session_stats.record_transcript(duration_secs);

    let (text, transcript_mode, macro_note) = super::message_processing::apply_macro_mode(
        &ctx.text,
        ctx.config.voice_send_mode,
        ctx.status_state.macros_enabled,
        ctx.voice_macros,
    );
    if let Some(action) =
        super::super::navigation::resolve_voice_navigation_action(&text, macro_note.is_some())
    {
        let sent_newline = super::super::navigation::execute_voice_navigation_action(
            action,
            ctx.prompt_tracker,
            ctx.session,
            ctx.writer_tx,
            ctx.status_clear_deadline,
            ctx.current_status,
            ctx.status_state,
        );
        if sent_newline {
            *ctx.last_enter_at = Some(ctx.now);
        }
    } else {
        queue_or_deliver_transcript(text, transcript_mode, macro_note, ready, ctx);
    }

    super::auto_rearm::maybe_rearm_auto_after_transcript(transcript_mode, ctx);

    if ctx.sound_on_complete {
        let _ = ctx.writer_tx.send(WriterMessage::Bell { count: 1 });
    }
}

fn queue_or_deliver_transcript<S: TranscriptSession>(
    text: String,
    transcript_mode: VoiceSendMode,
    macro_note: Option<String>,
    ready: bool,
    ctx: &mut TranscriptDeliveryContext<'_, S>,
) {
    let drop_note = ctx
        .metrics
        .as_ref()
        .filter(|metrics| metrics.frames_dropped > 0)
        .map(|metrics| format!("dropped {} frames", metrics.frames_dropped));
    let mut notes = Vec::with_capacity(2);
    if let Some(note) = drop_note {
        notes.push(note);
    }
    if let Some(note) = macro_note {
        notes.push(note);
    }
    let delivery_note = if notes.is_empty() {
        None
    } else {
        Some(notes.join(", "))
    };
    let queued_suffix = delivery_note
        .as_ref()
        .map(|note| format!(", {note}"))
        .unwrap_or_default();

    if ready && ctx.pending_transcripts.is_empty() {
        let mut io = crate::transcript::TranscriptIo {
            session: ctx.session,
            writer_tx: ctx.writer_tx,
            status_clear_deadline: ctx.status_clear_deadline,
            current_status: ctx.current_status,
            status_state: ctx.status_state,
        };
        let sent_newline = crate::transcript::deliver_transcript(
            &text,
            transcript_mode,
            &mut io,
            0,
            delivery_note.as_deref(),
        );
        if sent_newline {
            *ctx.last_enter_at = Some(ctx.now);
        }
        return;
    }

    let dropped = crate::transcript::push_pending_transcript(
        ctx.pending_transcripts,
        PendingTranscript {
            text,
            mode: transcript_mode,
        },
    );
    ctx.status_state.queue_depth = ctx.pending_transcripts.len();
    if dropped {
        crate::writer::set_status(
            ctx.writer_tx,
            ctx.status_clear_deadline,
            ctx.current_status,
            ctx.status_state,
            "Transcript queue full (oldest dropped)",
            Some(Duration::from_secs(2)),
        );
    }
    if ready {
        let mut io = crate::transcript::TranscriptIo {
            session: ctx.session,
            writer_tx: ctx.writer_tx,
            status_clear_deadline: ctx.status_clear_deadline,
            current_status: ctx.current_status,
            status_state: ctx.status_state,
        };
        crate::transcript::try_flush_pending(
            ctx.pending_transcripts,
            ctx.prompt_tracker,
            ctx.last_enter_at,
            &mut io,
            ctx.now,
            ctx.transcript_idle_timeout,
        );
    } else if !dropped {
        let status = format!(
            "Transcript queued ({}{})",
            ctx.pending_transcripts.len(),
            queued_suffix
        );
        crate::writer::set_status(
            ctx.writer_tx,
            ctx.status_clear_deadline,
            ctx.current_status,
            ctx.status_state,
            &status,
            None,
        );
    }
}
