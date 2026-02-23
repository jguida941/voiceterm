//! Input event handling extracted from the core event loop.

use super::*;
use crate::wake_word::WakeWordEvent;

mod overlay;
pub(super) fn handle_input_event(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    evt: InputEvent,
    running: &mut bool,
) {
    let mut pending_event = Some(evt);
    while let Some(current_event) = pending_event.take() {
        if state.overlay_mode != OverlayMode::None {
            let overlay_before = state.overlay_mode;
            let replay =
                overlay::handle_overlay_input_event(state, timers, deps, current_event, running);
            pending_event = if replay.is_some() && state.overlay_mode == overlay_before {
                // Prevent replay loops if an overlay handler returns an event
                // without actually transitioning out of overlay mode.
                None
            } else {
                replay
            };
            continue;
        }

        match current_event {
            InputEvent::HelpToggle => {
                state.status_state.hud_button_focus = None;
                open_help_overlay(state, deps);
            }
            InputEvent::ThemePicker => {
                state.status_state.hud_button_focus = None;
                open_theme_studio_overlay(state, deps);
            }
            InputEvent::QuickThemeCycle => {
                let overlay_mode = state.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.cycle_theme(1);
                });
                state.status_state.hud_button_focus = None;
                refresh_button_registry_if_mouse(state, deps);
            }
            InputEvent::SettingsToggle => {
                state.status_state.hud_button_focus = None;
                open_settings_overlay(state, deps);
            }
            InputEvent::TranscriptHistoryToggle => {
                state.status_state.hud_button_focus = None;
                open_transcript_history_overlay(state, deps);
            }
            InputEvent::ToastHistoryToggle => {
                state.status_state.hud_button_focus = None;
                open_toast_history_overlay(state, deps);
            }
            InputEvent::ToggleHudStyle => {
                let overlay_mode = state.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.cycle_hud_style(1);
                });
                state.status_state.hud_button_focus = None;
                refresh_button_registry_if_mouse(state, deps);
            }
            InputEvent::CollapseHiddenLauncher => {
                if state.status_state.hud_style == crate::config::HudStyle::Hidden {
                    state.status_state.hidden_launcher_collapsed = true;
                    state.status_state.hud_button_focus = None;
                    send_enhanced_status_with_buttons(
                        &deps.writer_tx,
                        &deps.button_registry,
                        &state.status_state,
                        state.overlay_mode,
                        state.terminal_cols,
                        state.theme,
                    );
                }
                refresh_button_registry_if_mouse(state, deps);
            }
            InputEvent::Bytes(bytes) => {
                if state.suppress_startup_escape_input && is_arrow_escape_noise(&bytes) {
                    return;
                }
                if let Some(keys) = parse_arrow_keys_only(&bytes) {
                    let mut moved = false;
                    for key in keys {
                        let direction = match key {
                            ArrowKey::Left => -1,
                            ArrowKey::Right => 1,
                            _ => 0,
                        };
                        if direction != 0
                            && advance_hud_button_focus(
                                &mut state.status_state,
                                state.overlay_mode,
                                state.terminal_cols,
                                state.theme,
                                direction,
                            )
                        {
                            moved = true;
                        }
                    }
                    if moved {
                        send_enhanced_status_with_buttons(
                            &deps.writer_tx,
                            &deps.button_registry,
                            &state.status_state,
                            state.overlay_mode,
                            state.terminal_cols,
                            state.theme,
                        );
                        return;
                    }
                }

                state.status_state.hud_button_focus = None;
                // Clear Claude prompt suppression when user sends any input to PTY.
                if state.status_state.claude_prompt_suppressed && !bytes.is_empty() {
                    state.claude_prompt_detector.on_user_input();
                    set_claude_prompt_suppression(state, deps, false);
                }
                let mark_insert_pending =
                    state.config.voice_send_mode == VoiceSendMode::Insert && !bytes.is_empty();
                if !write_or_queue_pty_input(state, deps, bytes) {
                    *running = false;
                } else if mark_insert_pending {
                    state.status_state.insert_pending_send = true;
                }
            }
            InputEvent::VoiceTrigger => {
                handle_voice_trigger(state, timers, deps, VoiceTriggerOrigin::ManualHotkey);
            }
            InputEvent::SendStagedText => {
                if should_finalize_insert_capture_hotkey(state) {
                    let _ = request_early_finalize_capture(state, timers, deps);
                    return;
                }
                if should_consume_insert_send_hotkey(state) {
                    if state.status_state.recording_state == RecordingState::Idle {
                        let msg = if state.status_state.insert_pending_send {
                            "Text staged; press Enter to send"
                        } else {
                            "Nothing to finalize"
                        };
                        set_status(
                            &deps.writer_tx,
                            &mut timers.status_clear_deadline,
                            &mut state.current_status,
                            &mut state.status_state,
                            msg,
                            Some(Duration::from_secs(2)),
                        );
                    }
                    return;
                }
                if !write_or_queue_pty_input(state, deps, vec![0x05]) {
                    *running = false;
                }
            }
            InputEvent::ToggleAutoVoice => {
                let overlay_mode = state.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.toggle_auto_voice();
                });
                refresh_button_registry_if_mouse(state, deps);
            }
            InputEvent::ToggleSendMode => {
                let overlay_mode = state.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.toggle_send_mode();
                });
                refresh_button_registry_if_mouse(state, deps);
            }
            InputEvent::IncreaseSensitivity => {
                let overlay_mode = state.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.adjust_sensitivity(5.0);
                });
            }
            InputEvent::DecreaseSensitivity => {
                let overlay_mode = state.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.adjust_sensitivity(-5.0);
                });
            }
            InputEvent::EnterKey => {
                // User responded to a potential Claude prompt; clear HUD suppression.
                if state.status_state.claude_prompt_suppressed {
                    state.claude_prompt_detector.on_user_input();
                    set_claude_prompt_suppression(state, deps, false);
                }
                if let Some(action) = state.status_state.hud_button_focus {
                    state.status_state.hud_button_focus = None;
                    if action != ButtonAction::ToggleAutoVoice {
                        if action == ButtonAction::ThemePicker {
                            reset_theme_studio_selection(state);
                        }
                        {
                            let mut button_ctx = button_action_context(state, timers, deps);
                            button_ctx.handle_action(action);
                        }
                        send_enhanced_status_with_buttons(
                            &deps.writer_tx,
                            &deps.button_registry,
                            &state.status_state,
                            state.overlay_mode,
                            state.terminal_cols,
                            state.theme,
                        );
                        return;
                    }
                    // Enter should submit terminal input even if a stale HUD focus highlight
                    // is sitting on the auto-voice button.
                    send_enhanced_status_with_buttons(
                        &deps.writer_tx,
                        &deps.button_registry,
                        &state.status_state,
                        state.overlay_mode,
                        state.terminal_cols,
                        state.theme,
                    );
                }
                if !write_or_queue_pty_input(state, deps, vec![0x0d]) {
                    *running = false;
                } else {
                    timers.last_enter_at = Some(Instant::now());
                    state.status_state.insert_pending_send = false;
                }
            }
            InputEvent::Exit => {
                *running = false;
            }
            InputEvent::MouseClick { x, y } => {
                if !state.status_state.mouse_enabled {
                    return;
                }

                if let Some(action) = deps.button_registry.find_at(x, y, state.terminal_rows) {
                    if action == ButtonAction::ThemePicker {
                        reset_theme_studio_selection(state);
                    }
                    {
                        let mut button_ctx = button_action_context(state, timers, deps);
                        button_ctx.handle_action(action);
                    }
                    state.status_state.hud_button_focus = None;
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
    }
}

pub(super) fn handle_wake_word_detection(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    wake_event: WakeWordEvent,
) {
    // Auto-voice pause is a guard for idle auto-triggering only; explicit wake
    // phrases should still arm capture.
    if !state.config.wake_word || state.overlay_mode != OverlayMode::None {
        return;
    }
    match wake_event {
        WakeWordEvent::Detected => {
            resume_auto_voice_if_wake_triggered(state);
            handle_voice_trigger(state, timers, deps, VoiceTriggerOrigin::WakeWord);
        }
        WakeWordEvent::SendStagedInput => {
            handle_wake_word_send_intent(state, timers, deps);
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum VoiceTriggerOrigin {
    ManualHotkey,
    WakeWord,
}

fn handle_voice_trigger(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    origin: VoiceTriggerOrigin,
) {
    if state.status_state.recording_state == RecordingState::Recording {
        if origin == VoiceTriggerOrigin::ManualHotkey {
            let _ = stop_active_capture(state, timers, deps);
        }
        return;
    }
    start_capture_for_trigger(state, timers, deps, origin);
}

fn start_capture_for_trigger(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    origin: VoiceTriggerOrigin,
) {
    let trigger = match origin {
        VoiceTriggerOrigin::WakeWord => VoiceCaptureTrigger::WakeWord,
        VoiceTriggerOrigin::ManualHotkey => {
            if state.auto_voice_enabled {
                VoiceCaptureTrigger::Auto
            } else {
                VoiceCaptureTrigger::Manual
            }
        }
    };
    if let Err(err) = start_voice_capture_with_hook(
        &mut deps.voice_manager,
        trigger,
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
    ) {
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            &crate::status_messages::with_log_path("Voice capture failed"),
            Some(Duration::from_secs(2)),
        );
        log_debug(&format!("voice capture failed: {err:#}"));
        return;
    }
    if origin == VoiceTriggerOrigin::WakeWord {
        log_wake_capture_started();
    }
    if origin == VoiceTriggerOrigin::ManualHotkey {
        state.auto_voice_paused_by_user = false;
    }
    timers.recording_started_at = Some(Instant::now());
    state.force_send_on_next_transcript = false;
    reset_capture_visuals(
        &mut state.status_state,
        &mut timers.preview_clear_deadline,
        &mut timers.last_meter_update,
    );
}

fn should_send_staged_text_hotkey(state: &EventLoopState) -> bool {
    state.config.voice_send_mode == VoiceSendMode::Insert && state.status_state.insert_pending_send
}

fn resume_auto_voice_if_wake_triggered(state: &mut EventLoopState) {
    if state.auto_voice_enabled && state.auto_voice_paused_by_user {
        state.auto_voice_paused_by_user = false;
    }
}

fn handle_wake_word_send_intent(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    if should_send_staged_text_hotkey(state) {
        if write_or_queue_pty_input(state, deps, vec![0x0d]) {
            timers.last_enter_at = Some(Instant::now());
            state.status_state.insert_pending_send = false;
        }
        return;
    }
    set_status(
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
        "Nothing to send",
        Some(Duration::from_secs(2)),
    );
}

fn should_finalize_insert_capture_hotkey(state: &EventLoopState) -> bool {
    state.config.voice_send_mode == VoiceSendMode::Insert
        && state.status_state.recording_state == RecordingState::Recording
}

fn should_consume_insert_send_hotkey(state: &EventLoopState) -> bool {
    state.config.voice_send_mode == VoiceSendMode::Insert
}

fn request_early_finalize_capture(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) -> bool {
    if !request_early_stop_with_hook(&mut deps.voice_manager) {
        return false;
    }
    state.force_send_on_next_transcript = false;
    state.status_state.recording_state = RecordingState::Processing;
    set_status(
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
        "Finalizing capture...",
        Some(Duration::from_secs(2)),
    );
    true
}

fn stop_active_capture(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) -> bool {
    if !cancel_capture_with_hook(&mut deps.voice_manager) {
        return false;
    }
    if state.auto_voice_enabled {
        state.auto_voice_paused_by_user = true;
    }
    state.force_send_on_next_transcript = false;
    state.status_state.recording_state = RecordingState::Idle;
    clear_capture_metrics(&mut state.status_state);
    timers.recording_started_at = None;
    set_status(
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
        "Capture stopped",
        Some(Duration::from_secs(2)),
    );
    true
}

fn run_settings_action(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    overlay_mode: OverlayMode,
    apply: impl FnOnce(&mut SettingsActionContext<'_>),
) {
    let mut settings_ctx = settings_action_context(state, timers, deps, overlay_mode);
    apply(&mut settings_ctx);
    // Persist changed settings to ~/.config/voiceterm/config.toml
    save_persistent_config(state);
}

fn save_persistent_config(state: &EventLoopState) {
    let snapshot = crate::persistent_config::snapshot_from_runtime(
        &state.config,
        &state.status_state,
        state.theme,
    );
    crate::persistent_config::save_user_config(&snapshot);
}
