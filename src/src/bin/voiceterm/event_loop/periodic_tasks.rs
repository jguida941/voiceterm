//! Periodic runtime tasks extracted from the core event loop.

use super::*;

pub(super) fn run_periodic_tasks(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    now: Instant,
) {
    if take_sigwinch_flag() {
        if let Ok((cols, rows)) = read_terminal_size() {
            // JetBrains terminals can emit SIGWINCH without a geometry delta.
            // Skip no-op resize work so we avoid redraw flicker and redundant backend SIGWINCH.
            let size_changed = state.terminal_cols != cols || state.terminal_rows != rows;
            if size_changed {
                state.terminal_cols = cols;
                state.terminal_rows = rows;
                apply_pty_winsize(
                    &mut deps.session,
                    rows,
                    cols,
                    state.overlay_mode,
                    state.status_state.hud_style,
                );
                let _ = deps.writer_tx.send(WriterMessage::Resize { rows, cols });
                refresh_button_registry_if_mouse(state, deps);
                match state.overlay_mode {
                    OverlayMode::Help => render_help_overlay_for_state(state, deps),
                    OverlayMode::ThemePicker => render_theme_picker_overlay_for_state(state, deps),
                    OverlayMode::Settings => render_settings_overlay_for_state(state, deps),
                    OverlayMode::None => {}
                }
            }
        }
    }

    if state.overlay_mode != OverlayMode::ThemePicker {
        reset_theme_picker_digits(state, timers);
    } else if let Some(deadline) = timers.theme_picker_digit_deadline {
        if now >= deadline {
            if let Some(idx) =
                theme_picker_parse_index(&state.theme_picker_digits, THEME_OPTIONS.len())
            {
                if apply_theme_picker_index(
                    idx,
                    &mut state.theme,
                    &mut state.config,
                    &deps.writer_tx,
                    &mut timers.status_clear_deadline,
                    &mut state.current_status,
                    &mut state.status_state,
                    &mut deps.session,
                    &mut state.terminal_rows,
                    &mut state.terminal_cols,
                    &mut state.overlay_mode,
                ) {
                    state.theme_picker_selected = theme_index_from_theme(state.theme);
                }
            }
            reset_theme_picker_digits(state, timers);
        }
    }

    if state.status_state.recording_state == RecordingState::Recording {
        if let Some(start) = timers.recording_started_at {
            if now.duration_since(timers.last_recording_update)
                >= Duration::from_millis(RECORDING_DURATION_UPDATE_MS)
            {
                let duration = now.duration_since(start).as_secs_f32();
                if (duration - state.last_recording_duration).abs() >= 0.1 {
                    state.status_state.recording_duration = Some(duration);
                    state.last_recording_duration = duration;
                    send_enhanced_status_with_buttons(
                        &deps.writer_tx,
                        &deps.button_registry,
                        &state.status_state,
                        state.overlay_mode,
                        state.terminal_cols,
                        state.theme,
                    );
                }
                timers.last_recording_update = now;
            }
        }
    }

    if state.status_state.recording_state == RecordingState::Recording
        && now.duration_since(timers.last_meter_update)
            >= Duration::from_millis(deps.meter_update_ms)
    {
        let level = deps.live_meter.level_db().max(METER_DB_FLOOR);
        state.meter_levels.push_back(level);
        if state.meter_levels.len() > METER_HISTORY_MAX {
            state.meter_levels.pop_front();
        }
        state.status_state.meter_db = Some(level);
        state.status_state.meter_levels.clear();
        state
            .status_state
            .meter_levels
            .extend(state.meter_levels.iter().copied());
        timers.last_meter_update = now;
        send_enhanced_status_with_buttons(
            &deps.writer_tx,
            &deps.button_registry,
            &state.status_state,
            state.overlay_mode,
            state.terminal_cols,
            state.theme,
        );
    }

    if state.status_state.recording_state == RecordingState::Processing
        && now.duration_since(timers.last_processing_tick)
            >= Duration::from_millis(PROCESSING_SPINNER_TICK_MS)
    {
        let spinner = progress::SPINNER_BRAILLE
            [state.processing_spinner_index % progress::SPINNER_BRAILLE.len()];
        state.status_state.message = format!("Processing {spinner}");
        state.processing_spinner_index = state.processing_spinner_index.wrapping_add(1);
        timers.last_processing_tick = now;
        send_enhanced_status_with_buttons(
            &deps.writer_tx,
            &deps.button_registry,
            &state.status_state,
            state.overlay_mode,
            state.terminal_cols,
            state.theme,
        );
    }

    if state.status_state.hud_right_panel == HudRightPanel::Heartbeat {
        let animate = !state.status_state.hud_right_panel_recording_only
            || state.status_state.recording_state == RecordingState::Recording;
        if animate && now.duration_since(timers.last_heartbeat_tick) >= Duration::from_secs(1) {
            timers.last_heartbeat_tick = now;
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
    state.prompt_tracker.on_idle(now, deps.auto_idle_timeout);

    drain_voice_messages_once(state, timers, deps, now);

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

    if state.auto_voice_enabled
        && deps.voice_manager.is_idle()
        && should_auto_trigger(
            &state.prompt_tracker,
            now,
            deps.auto_idle_timeout,
            timers.last_auto_trigger_at,
        )
    {
        if let Err(err) = start_voice_capture_with_hook(
            &mut deps.voice_manager,
            VoiceCaptureTrigger::Auto,
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
        ) {
            log_debug(&format!("auto voice capture failed: {err:#}"));
        } else {
            timers.last_auto_trigger_at = Some(now);
            timers.recording_started_at = Some(now);
            reset_capture_visuals(
                &mut state.status_state,
                &mut timers.preview_clear_deadline,
                &mut timers.last_meter_update,
            );
        }
    }

    if let Some(deadline) = timers.preview_clear_deadline {
        if now >= deadline {
            timers.preview_clear_deadline = None;
            if state.status_state.transcript_preview.is_some() {
                state.status_state.transcript_preview = None;
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
    }

    if let Some(deadline) = timers.status_clear_deadline {
        if now >= deadline {
            timers.status_clear_deadline = None;
            state.current_status = None;
            state.status_state.message.clear();
            if state.status_state.recording_state == RecordingState::Responding {
                state.status_state.recording_state = RecordingState::Idle;
            }
            // Don't repeatedly set "Auto-voice enabled" - the mode indicator shows it
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
}
