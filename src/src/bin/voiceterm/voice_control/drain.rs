//! Voice-job drain logic so capture results integrate safely with transcript queues.

mod auto_rearm;
mod message_processing;
mod transcript_delivery;

use crossbeam_channel::Sender;
use std::collections::VecDeque;
use std::time::{Duration, Instant};
use voiceterm::{VoiceCaptureSource, VoiceJobMessage};

use crate::config::{OverlayConfig, VoiceSendMode};
use crate::prompt::PromptTracker;
use crate::session_stats::SessionStats;
use crate::status_line::{RecordingState, StatusLineState};
use crate::transcript::{PendingTranscript, TranscriptSession};
use crate::voice_macros::VoiceMacros;
use crate::writer::WriterMessage;

use super::manager::VoiceManager;
use auto_rearm::{finalize_drain_state, maybe_rearm_auto_after_empty, AutoRearmContext};
use message_processing::{clear_last_latency, handle_voice_message};
use transcript_delivery::{handle_transcript_message, TranscriptDeliveryContext};

pub(crate) fn clear_capture_metrics(status_state: &mut StatusLineState) {
    status_state.recording_duration = None;
    status_state.meter_db = None;
    status_state.meter_levels.clear();
}

pub(crate) struct VoiceMessageContext<'a, S: TranscriptSession> {
    pub config: &'a OverlayConfig,
    pub session: &'a mut S,
    pub writer_tx: &'a Sender<WriterMessage>,
    pub status_clear_deadline: &'a mut Option<Instant>,
    pub current_status: &'a mut Option<String>,
    pub status_state: &'a mut StatusLineState,
    pub session_stats: &'a mut SessionStats,
    pub auto_voice_enabled: bool,
}

pub(crate) struct VoiceDrainContext<'a, S: TranscriptSession> {
    pub voice_manager: &'a mut VoiceManager,
    pub config: &'a OverlayConfig,
    pub voice_macros: &'a VoiceMacros,
    pub session: &'a mut S,
    pub writer_tx: &'a Sender<WriterMessage>,
    pub status_clear_deadline: &'a mut Option<Instant>,
    pub current_status: &'a mut Option<String>,
    pub status_state: &'a mut StatusLineState,
    pub session_stats: &'a mut SessionStats,
    pub pending_transcripts: &'a mut VecDeque<PendingTranscript>,
    pub prompt_tracker: &'a mut PromptTracker,
    pub last_enter_at: &'a mut Option<Instant>,
    pub now: Instant,
    pub transcript_idle_timeout: Duration,
    pub recording_started_at: &'a mut Option<Instant>,
    pub preview_clear_deadline: &'a mut Option<Instant>,
    pub last_meter_update: &'a mut Instant,
    pub last_auto_trigger_at: &'a mut Option<Instant>,
    pub force_send_on_next_transcript: &'a mut bool,
    pub auto_voice_enabled: bool,
    pub sound_on_complete: bool,
    pub sound_on_error: bool,
}

pub(crate) fn drain_voice_messages<S: TranscriptSession>(ctx: &mut VoiceDrainContext<'_, S>) {
    let voice_manager = &mut *ctx.voice_manager;
    let config = ctx.config;
    let voice_macros = ctx.voice_macros;
    let session = &mut *ctx.session;
    let writer_tx = ctx.writer_tx;
    let status_clear_deadline = &mut *ctx.status_clear_deadline;
    let current_status = &mut *ctx.current_status;
    let status_state = &mut *ctx.status_state;
    let session_stats = &mut *ctx.session_stats;
    let pending_transcripts = &mut *ctx.pending_transcripts;
    let prompt_tracker = &mut *ctx.prompt_tracker;
    let last_enter_at = &mut *ctx.last_enter_at;
    let now = ctx.now;
    let transcript_idle_timeout = ctx.transcript_idle_timeout;
    let recording_started_at = &mut *ctx.recording_started_at;
    let preview_clear_deadline = &mut *ctx.preview_clear_deadline;
    let last_meter_update = &mut *ctx.last_meter_update;
    let last_auto_trigger_at = &mut *ctx.last_auto_trigger_at;
    let force_send_on_next_transcript = &mut *ctx.force_send_on_next_transcript;
    let auto_voice_enabled = ctx.auto_voice_enabled;
    let sound_on_complete = ctx.sound_on_complete;
    let sound_on_error = ctx.sound_on_error;

    let Some(message) = voice_manager.poll_message() else {
        return;
    };
    let rearm_auto = matches!(
        message,
        VoiceJobMessage::Empty { .. } | VoiceJobMessage::Error(_)
    );
    match message {
        VoiceJobMessage::Transcript {
            text,
            source,
            metrics,
        } => {
            let mut transcript_ctx = TranscriptDeliveryContext {
                text,
                source,
                metrics,
                voice_manager,
                config,
                voice_macros,
                session,
                writer_tx,
                status_clear_deadline,
                current_status,
                status_state,
                session_stats,
                pending_transcripts,
                prompt_tracker,
                last_enter_at,
                now,
                transcript_idle_timeout,
                recording_started_at,
                preview_clear_deadline,
                last_meter_update,
                last_auto_trigger_at,
                force_send_on_next_transcript,
                auto_voice_enabled,
                sound_on_complete,
            };
            handle_transcript_message(&mut transcript_ctx);
        }
        VoiceJobMessage::Empty { source, metrics } => {
            *force_send_on_next_transcript = false;
            clear_last_latency(status_state);
            let mut non_transcript_ctx = NonTranscriptDispatchContext {
                config,
                session,
                writer_tx,
                status_clear_deadline,
                current_status,
                status_state,
                session_stats,
                auto_voice_enabled,
            };
            dispatch_voice_message(
                VoiceJobMessage::Empty { source, metrics },
                &mut non_transcript_ctx,
            );
            let mut rearm_ctx = AutoRearmContext {
                voice_manager,
                writer_tx,
                status_clear_deadline,
                current_status,
                status_state,
                last_auto_trigger_at,
                recording_started_at,
                preview_clear_deadline,
                last_meter_update,
                now,
            };
            maybe_rearm_auto_after_empty(&mut rearm_ctx, auto_voice_enabled);
        }
        other => {
            *force_send_on_next_transcript = false;
            clear_last_latency(status_state);
            if sound_on_error && matches!(other, VoiceJobMessage::Error(_)) {
                let _ = writer_tx.send(WriterMessage::Bell { count: 2 });
            }
            let mut non_transcript_ctx = NonTranscriptDispatchContext {
                config,
                session,
                writer_tx,
                status_clear_deadline,
                current_status,
                status_state,
                session_stats,
                auto_voice_enabled,
            };
            dispatch_voice_message(other, &mut non_transcript_ctx);
        }
    }
    finalize_drain_state(
        prompt_tracker,
        auto_voice_enabled,
        rearm_auto,
        now,
        status_state,
        recording_started_at,
    );
}

pub(crate) fn reset_capture_visuals(
    status_state: &mut StatusLineState,
    preview_clear_deadline: &mut Option<Instant>,
    last_meter_update: &mut Instant,
) {
    status_state.transcript_preview = None;
    *preview_clear_deadline = None;
    *last_meter_update = Instant::now();
}

fn dispatch_voice_message<S: TranscriptSession>(
    message: VoiceJobMessage,
    ctx: &mut NonTranscriptDispatchContext<'_, S>,
) {
    let mut ctx = VoiceMessageContext {
        config: ctx.config,
        session: ctx.session,
        writer_tx: ctx.writer_tx,
        status_clear_deadline: ctx.status_clear_deadline,
        current_status: ctx.current_status,
        status_state: ctx.status_state,
        session_stats: ctx.session_stats,
        auto_voice_enabled: ctx.auto_voice_enabled,
    };
    handle_voice_message(message, &mut ctx);
}

struct NonTranscriptDispatchContext<'a, S: TranscriptSession> {
    config: &'a OverlayConfig,
    session: &'a mut S,
    writer_tx: &'a Sender<WriterMessage>,
    status_clear_deadline: &'a mut Option<Instant>,
    current_status: &'a mut Option<String>,
    status_state: &'a mut StatusLineState,
    session_stats: &'a mut SessionStats,
    auto_voice_enabled: bool,
}

#[cfg(test)]
mod tests;
