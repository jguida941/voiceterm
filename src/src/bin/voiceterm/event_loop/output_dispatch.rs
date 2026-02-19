//! PTY output dispatch extracted from the core event loop.

use super::*;

pub(super) fn handle_output_chunk(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    mut data: Vec<u8>,
    running: &mut bool,
) {
    let mut output_disconnected = false;
    for _ in 0..PTY_OUTPUT_BATCH_CHUNKS {
        match deps.session.output_rx.try_recv() {
            Ok(next) => data.extend_from_slice(&next),
            Err(TryRecvError::Empty) => break,
            Err(TryRecvError::Disconnected) => {
                output_disconnected = true;
                break;
            }
        }
    }
    let now = Instant::now();
    if !data.is_empty() {
        state.suppress_startup_escape_input = false;
        state.transcript_history.ingest_backend_output_bytes(&data);
        if let Some(logger) = state.session_memory_logger.as_mut() {
            logger.record_backend_output_bytes(&data);
        }
        if state.status_state.recording_state == RecordingState::Responding {
            state.status_state.recording_state = RecordingState::Idle;
            send_enhanced_status_with_buttons(
                &deps.writer_tx,
                &deps.button_registry,
                &state.status_state,
                state.overlay_mode,
                state.terminal_cols,
                state.theme,
            );
        }
    }
    state.prompt_tracker.feed_output(&data);
    // Feed PTY output to Claude prompt detector for HUD occlusion prevention.
    if state.claude_prompt_detector.feed_output(&data) {
        // A new interactive prompt was just detected; suppress HUD and free row budget.
        set_claude_prompt_suppression(state, deps, true);
    } else if state.status_state.claude_prompt_suppressed
        && !state.claude_prompt_detector.should_suppress_hud()
    {
        // Suppression expired (timeout); restore HUD and normal row reservation.
        set_claude_prompt_suppression(state, deps, false);
    }
    {
        let mut io = TranscriptIo {
            session: &mut deps.session,
            writer_tx: &deps.writer_tx,
            status_clear_deadline: &mut timers.status_clear_deadline,
            current_status: &mut state.current_status,
            status_state: &mut state.status_state,
        };
        try_flush_pending(
            &mut state.pending_transcripts,
            &state.prompt_tracker,
            &mut timers.last_enter_at,
            &mut io,
            now,
            deps.transcript_idle_timeout,
        );
    }
    match deps.writer_tx.try_send(WriterMessage::PtyOutput(data)) {
        Ok(()) => {}
        Err(TrySendError::Full(WriterMessage::PtyOutput(bytes))) => {
            state.pending_pty_output = Some(bytes);
        }
        Err(TrySendError::Full(_)) => {}
        Err(TrySendError::Disconnected(_)) => {
            *running = false;
        }
    }
    drain_voice_messages_once(state, timers, deps, now);
    if output_disconnected && state.pending_pty_output.is_none() {
        *running = false;
    }
}
