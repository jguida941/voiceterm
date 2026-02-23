//! Periodic runtime tasks extracted from the core event loop.

use super::*;

const LATENCY_BADGE_MAX_AGE_SECS: u64 = 8;
const TOAST_TICK_INTERVAL_MS: u64 = 250;

pub(super) fn run_periodic_tasks(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    now: Instant,
) {
    if state.status_state.claude_prompt_suppressed
        && !state.claude_prompt_detector.should_suppress_hud()
    {
        // Timeout-based clear path, even when no new PTY output arrives.
        set_claude_prompt_suppression(state, deps, false);
    }

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
                    state.status_state.claude_prompt_suppressed,
                );
                let _ = deps.writer_tx.send(WriterMessage::Resize { rows, cols });
                refresh_button_registry_if_mouse(state, deps);
                match state.overlay_mode {
                    OverlayMode::Help => render_help_overlay_for_state(state, deps),
                    OverlayMode::ThemeStudio => render_theme_studio_overlay_for_state(state, deps),
                    OverlayMode::ThemePicker => render_theme_picker_overlay_for_state(state, deps),
                    OverlayMode::Settings => render_settings_overlay_for_state(state, deps),
                    OverlayMode::TranscriptHistory => {
                        render_transcript_history_overlay_for_state(state, deps)
                    }
                    OverlayMode::ToastHistory => {
                        render_toast_history_overlay_for_state(state, deps)
                    }
                    OverlayMode::MemoryBrowser | OverlayMode::ActionCenter => {
                        // Placeholder: re-render on resize when dedicated overlays ship.
                    }
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

    if state.status_state.recording_state != RecordingState::Recording {
        state.meter_floor_started_at = None;
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
        let is_floor_level = level <= METER_DB_FLOOR + METER_FLOOR_EPSILON_DB;
        if is_floor_level {
            let floor_started_at = state.meter_floor_started_at.get_or_insert(now);
            let quiet_for = now.saturating_duration_since(*floor_started_at);
            if quiet_for >= Duration::from_millis(METER_NO_SIGNAL_PLACEHOLDER_MS) {
                // Keep the last rendered value visible instead of collapsing to "--dB"/empty.
                // If nothing has ever been rendered this capture, seed with the floor level.
                state.status_state.meter_db = state.status_state.meter_db.or(Some(level));
            } else {
                state.status_state.meter_db = Some(level);
            }
        } else {
            state.meter_floor_started_at = None;
            state.status_state.meter_db = Some(level);
        }
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
        let colors = state.theme.colors();
        let spinner =
            crate::theme::processing_spinner_symbol(&colors, state.processing_spinner_index);
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

    let capture_active = !deps.voice_manager.is_idle();
    deps.wake_word_runtime.sync(
        state.config.wake_word,
        state.config.wake_word_sensitivity,
        state.config.wake_word_cooldown_ms,
        capture_active,
    );
    let wake_listener_active = deps.wake_word_runtime.is_listener_active();
    let wake_paused = wake_listener_active && capture_active;
    update_wake_word_hud_state(state, timers, deps, wake_listener_active, wake_paused, now);

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
    maybe_expire_stale_latency(state, deps, now);
    maybe_capture_status_toast(state, deps);

    if state.auto_voice_enabled
        && !state.auto_voice_paused_by_user
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
            state.meter_floor_started_at = None;
            reset_capture_visuals(
                &mut state.status_state,
                &mut timers.preview_clear_deadline,
                &mut timers.last_meter_update,
            );
        }
    }

    // Tick toast center to dismiss expired notifications.
    if now.duration_since(timers.last_toast_tick) >= Duration::from_millis(TOAST_TICK_INTERVAL_MS) {
        timers.last_toast_tick = now;
        if state.toast_center.tick() {
            if state.overlay_mode == OverlayMode::ToastHistory {
                render_toast_history_overlay_for_state(state, deps);
            }
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
            state.last_toast_status = None;
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

fn maybe_capture_status_toast(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    let Some(status) = state.current_status.clone() else {
        return;
    };
    if state.last_toast_status.as_deref() == Some(status.as_str()) {
        return;
    }
    let severity = match crate::status_style::StatusType::from_message(&status) {
        crate::status_style::StatusType::Success => crate::toast::ToastSeverity::Success,
        crate::status_style::StatusType::Warning => crate::toast::ToastSeverity::Warning,
        crate::status_style::StatusType::Error => crate::toast::ToastSeverity::Error,
        crate::status_style::StatusType::Recording
        | crate::status_style::StatusType::Processing
        | crate::status_style::StatusType::Info => crate::toast::ToastSeverity::Info,
    };
    state.toast_center.push(severity, status.clone());
    state.last_toast_status = Some(status);
    if state.overlay_mode == OverlayMode::ToastHistory {
        render_toast_history_overlay_for_state(state, deps);
    }
}

fn maybe_expire_stale_latency(state: &mut EventLoopState, deps: &EventLoopDeps, now: Instant) {
    if state.status_state.recording_state != RecordingState::Idle {
        return;
    }
    let Some(updated_at) = state.status_state.last_latency_updated_at else {
        return;
    };
    if now.duration_since(updated_at) < Duration::from_secs(LATENCY_BADGE_MAX_AGE_SECS) {
        return;
    }
    state.status_state.last_latency_ms = None;
    state.status_state.last_latency_speech_ms = None;
    state.status_state.last_latency_rtf_x1000 = None;
    state.status_state.last_latency_updated_at = None;
    send_enhanced_status_with_buttons(
        &deps.writer_tx,
        &deps.button_registry,
        &state.status_state,
        state.overlay_mode,
        state.terminal_cols,
        state.theme,
    );
}

fn update_wake_word_hud_state(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &EventLoopDeps,
    wake_listener_active: bool,
    wake_paused: bool,
    now: Instant,
) {
    use crate::status_line::WakeWordHudState;

    let next_state = if !state.config.wake_word {
        WakeWordHudState::Off
    } else if !wake_listener_active {
        WakeWordHudState::Unavailable
    } else if wake_paused {
        WakeWordHudState::Paused
    } else {
        WakeWordHudState::Listening
    };
    if state.status_state.wake_word_state == next_state {
        return;
    }
    let previous_state = state.status_state.wake_word_state;
    state.status_state.wake_word_state = next_state;
    if previous_state != WakeWordHudState::Unavailable
        && next_state == WakeWordHudState::Unavailable
    {
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            &crate::status_messages::with_log_path("Wake listener unavailable"),
            Some(Duration::from_secs(3)),
        );
    }
    timers.last_wake_hud_tick = now;
    send_enhanced_status_with_buttons(
        &deps.writer_tx,
        &deps.button_registry,
        &state.status_state,
        state.overlay_mode,
        state.terminal_cols,
        state.theme,
    );
}
