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
        if state.ui.overlay_mode != OverlayMode::None {
            let overlay_before = state.ui.overlay_mode;
            let replay =
                overlay::handle_overlay_input_event(state, timers, deps, current_event, running);
            pending_event = if replay.is_some() && state.ui.overlay_mode == overlay_before {
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
                let overlay_mode = state.ui.overlay_mode;
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
                let overlay_mode = state.ui.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.cycle_hud_style(1);
                });
                state.status_state.hud_button_focus = None;
                refresh_button_registry_if_mouse(state, deps);
            }
            InputEvent::Bytes(bytes) => {
                voiceterm::log_debug_content(&format!(
                    "[input-debug] bytes_event: len={}, hex={}, hud_focus={:?}",
                    bytes.len(),
                    bytes
                        .iter()
                        .take(24)
                        .map(|b| format!("{b:02x}"))
                        .collect::<Vec<_>>()
                        .join(" "),
                    state.status_state.hud_button_focus
                ));
                if state.ui.suppress_startup_escape_input && is_arrow_escape_noise(&bytes) {
                    log_debug("[input-debug] bytes_event consumed as startup escape noise");
                    return;
                }
                if let Some(keys) = parse_arrow_keys_only(&bytes) {
                    let backend_family = BackendFamily::from_label(&deps.backend_label);
                    // Codex enables kitty keyboard reporting, which emits a
                    // separate release/repeat frame after the press. The arrow
                    // parser intentionally returns an empty list for those
                    // recognized frames. Consume them in Codex mode so they do
                    // not clear HUD focus and reset every next Left/Right press
                    // to the first/last button. Claude keeps its existing path.
                    if backend_family == BackendFamily::Codex && keys.is_empty() {
                        return;
                    }
                    let preserve_caret =
                        should_preserve_terminal_caret_navigation(state, &deps.backend_label);
                    let mut moved = false;
                    let mut consumed = false;
                    for key in keys {
                        let direction = hud_navigation_direction_from_arrow(key, preserve_caret);
                        if direction != 0 {
                            consumed = true;
                            if advance_hud_button_focus(
                                &mut state.status_state,
                                state.ui.overlay_mode,
                                state.ui.terminal_cols,
                                state.theme,
                                direction,
                            ) {
                                moved = true;
                            }
                        }
                    }
                    if moved {
                        send_enhanced_status_with_buttons(
                            &deps.writer_tx,
                            &deps.button_registry,
                            &state.status_state,
                            state.ui.overlay_mode,
                            state.ui.terminal_cols,
                            state.theme,
                        );
                    }
                    if consumed {
                        return;
                    }
                }

                state.status_state.hud_button_focus = None;
                if !bytes.is_empty() {
                    timers.last_user_input_at = Some(Instant::now());
                }
                // Resolve prompt suppression according to prompt type policy.
                register_prompt_resolution_candidate(state, timers, &bytes);
                // Defer HUD re-enable to periodic/output dispatch so we do not redraw the
                // banner on the same keypress frame that backend approval UIs are repainting.
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
            InputEvent::ImageCaptureTrigger => {
                handle_image_capture_trigger(state, timers, deps);
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
                let overlay_mode = state.ui.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.toggle_auto_voice();
                });
                refresh_button_registry_if_mouse(state, deps);
            }
            InputEvent::ToggleSendMode => {
                let overlay_mode = state.ui.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.toggle_send_mode();
                });
                refresh_button_registry_if_mouse(state, deps);
            }
            InputEvent::IncreaseSensitivity => {
                let overlay_mode = state.ui.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.adjust_sensitivity(5.0);
                });
            }
            InputEvent::DecreaseSensitivity => {
                let overlay_mode = state.ui.overlay_mode;
                run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                    settings_ctx.adjust_sensitivity(-5.0);
                });
            }
            InputEvent::EnterKey => {
                log_debug(&format!(
                    "[input-debug] enter_key: hud_focus={:?}, overlay={:?}",
                    state.status_state.hud_button_focus, state.ui.overlay_mode
                ));
                // Treat Enter as prompt-resolution input, but defer HUD re-enable
                // to periodic/output reconciliation to avoid same-frame occlusion
                // over approval options and tool cards.
                register_prompt_resolution_candidate(state, timers, b"\r");
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
                            state.ui.overlay_mode,
                            state.ui.terminal_cols,
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
                        state.ui.overlay_mode,
                        state.ui.terminal_cols,
                        state.theme,
                    );
                }
                log_debug("[input-debug] enter_key: forwarding 0x0d to child pty");
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
                // Hit-test against LIVE state instead of the cached registry:
                // the cache went stale (or empty) across suppression/overlay/
                // recording-state transitions, so clicks died after the first
                // response streamed (field bug: "clicking works at session
                // start, breaks after sending a message").
                let hud_y = state.ui.terminal_rows.saturating_sub(y).saturating_add(1);
                let banner_rows = crate::status_line::status_banner_height_for_state(
                    state.ui.terminal_cols as usize,
                    &state.status_state,
                ) as u16;
                let hit = if (1..=banner_rows).contains(&hud_y) {
                    crate::status_line::get_button_positions(
                        &state.status_state,
                        state.theme,
                        state.ui.terminal_cols as usize,
                    )
                    .into_iter()
                    .find(|pos| pos.row == hud_y && x >= pos.start_x && x <= pos.end_x)
                    .map(|pos| pos.action)
                } else {
                    None
                };
                log_debug(&format!(
                    "[input-debug] mouse_click: x={}, y={}, rows={}, hud_y={}, banner_rows={}, mouse_enabled={}, hit={:?}",
                    x,
                    y,
                    state.ui.terminal_rows,
                    hud_y,
                    banner_rows,
                    state.status_state.mouse_enabled,
                    hit
                ));
                if !state.status_state.mouse_enabled {
                    return;
                }

                if let Some(action) = hit {
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
                        state.ui.overlay_mode,
                        state.ui.terminal_cols,
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
    if !state.config.wake_word || state.ui.overlay_mode != OverlayMode::None {
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

fn handle_image_capture_trigger(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    if state.status_state.recording_state != RecordingState::Idle {
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            "Finish voice capture first",
            Some(Duration::from_secs(2)),
        );
        return;
    }
    trigger_image_capture(state, timers, deps);
}

fn trigger_image_capture(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    let captured_path = match crate::image_mode::capture_image(&state.config) {
        Ok(path) => path,
        Err(err) => {
            let status = crate::status_messages::image_capture_failed(&err);
            set_status(
                &deps.writer_tx,
                &mut timers.status_clear_deadline,
                &mut state.current_status,
                &mut state.status_state,
                &status,
                Some(Duration::from_secs(3)),
            );
            log_debug(&format!("image capture failed: {err:#}"));
            return;
        }
    };
    let voiceterm_cwd = std::env::var("VOICETERM_CWD").unwrap_or_else(|_| "<unset>".to_string());
    log_debug(&format!(
        "image captured path={} voiceterm_cwd={voiceterm_cwd}",
        captured_path.display()
    ));

    let prompt =
        crate::image_mode::build_image_prompt(&captured_path, state.config.voice_send_mode);
    if !write_or_queue_pty_input(state, deps, prompt.text.into_bytes()) {
        return;
    }
    if prompt.auto_sent {
        timers.last_enter_at = Some(Instant::now());
        state.status_state.insert_pending_send = false;
        state.status_state.recording_state = RecordingState::Responding;
    } else {
        state.status_state.insert_pending_send = true;
    }

    let file_name = captured_path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("capture");
    let status = if prompt.auto_sent {
        format!("Image captured and sent ({file_name})")
    } else {
        format!("Image captured and staged ({file_name})")
    };
    set_status(
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
        &status,
        Some(Duration::from_secs(3)),
    );
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

fn hud_navigation_direction_from_arrow(key: ArrowKey, preserve_terminal_caret: bool) -> i32 {
    // Only Left/Right navigate horizontal HUD buttons. Up/Down always pass
    // through to the wrapped terminal so Claude/Cursor keeps input ownership.
    // Vertical overlays (Settings, Review, etc.) handle their own Up/Down
    // through the separate overlay input handler.
    match key {
        ArrowKey::Left if !preserve_terminal_caret => -1,
        ArrowKey::Right if !preserve_terminal_caret => 1,
        _ => 0,
    }
}

fn should_preserve_terminal_caret_navigation(state: &EventLoopState, backend_label: &str) -> bool {
    should_preserve_terminal_caret_navigation_for_input(
        runtime_compat::detect_terminal_host(),
        backend_label,
        state.config.voice_send_mode,
        state.status_state.insert_pending_send,
    )
}

fn should_preserve_terminal_caret_navigation_for_input(
    terminal_host: TerminalHost,
    backend_label: &str,
    send_mode: VoiceSendMode,
    insert_pending_send: bool,
) -> bool {
    let backend_family = BackendFamily::from_label(backend_label);
    (terminal_host == TerminalHost::Cursor && backend_family == BackendFamily::Claude)
        || (backend_family != BackendFamily::Codex
            && send_mode == VoiceSendMode::Insert
            && insert_pending_send)
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
    let can_submit_now = should_send_staged_text_hotkey(state)
        || state.config.voice_send_mode == VoiceSendMode::Auto;
    if can_submit_now {
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

#[cfg(test)]
mod tests {
    use super::*;
    use rstest::rstest;

    #[rstest]
    #[case(TerminalHost::Other, "claude", VoiceSendMode::Insert, true, true)]
    #[case(TerminalHost::Other, "claude", VoiceSendMode::Insert, false, false)]
    #[case(TerminalHost::Other, "claude", VoiceSendMode::Auto, true, false)]
    #[case(TerminalHost::Other, "claude", VoiceSendMode::Auto, false, false)]
    #[case(TerminalHost::Other, "codex", VoiceSendMode::Insert, true, false)]
    #[case(TerminalHost::Cursor, "claude", VoiceSendMode::Auto, false, true)]
    #[case(TerminalHost::Cursor, "codex", VoiceSendMode::Auto, false, false)]
    fn should_preserve_terminal_caret_navigation_matches_send_mode_contract(
        #[case] terminal_host: TerminalHost,
        #[case] backend_label: &str,
        #[case] send_mode: VoiceSendMode,
        #[case] insert_pending_send: bool,
        #[case] expected: bool,
    ) {
        assert_eq!(
            should_preserve_terminal_caret_navigation_for_input(
                terminal_host,
                backend_label,
                send_mode,
                insert_pending_send,
            ),
            expected
        );
    }

    #[rstest]
    #[case(ArrowKey::Left, false, -1)]
    #[case(ArrowKey::Right, false, 1)]
    #[case(ArrowKey::Left, true, 0)]
    #[case(ArrowKey::Right, true, 0)]
    // Up/Down always pass through to the terminal (direction 0), regardless of
    // HUD focus state, so Claude/Cursor keeps vertical input ownership.
    #[case(ArrowKey::Up, false, 0)]
    #[case(ArrowKey::Down, false, 0)]
    #[case(ArrowKey::Up, true, 0)]
    #[case(ArrowKey::Down, true, 0)]
    fn hud_navigation_direction_from_arrow_matches_input_ownership_contract(
        #[case] key: ArrowKey,
        #[case] preserve_terminal_caret: bool,
        #[case] expected_direction: i32,
    ) {
        assert_eq!(
            hud_navigation_direction_from_arrow(key, preserve_terminal_caret),
            expected_direction
        );
    }

    #[rstest]
    #[case("cursor", "claude")]
    #[case("jetbrains", "claude")]
    #[case("other", "claude")]
    fn insert_pending_preserves_caret_for_claude_hosts(#[case] host: &str, #[case] provider: &str) {
        let preserve = should_preserve_terminal_caret_navigation_for_input(
            match host {
                "cursor" => TerminalHost::Cursor,
                "jetbrains" => TerminalHost::JetBrains,
                _ => TerminalHost::Other,
            },
            provider,
            VoiceSendMode::Insert,
            true,
        );
        assert!(preserve, "host={host}, provider={provider}");
        assert_eq!(
            hud_navigation_direction_from_arrow(ArrowKey::Left, preserve),
            0,
            "host={host}, provider={provider}"
        );
        assert_eq!(
            hud_navigation_direction_from_arrow(ArrowKey::Right, preserve),
            0,
            "host={host}, provider={provider}"
        );
    }

    #[rstest]
    #[case("cursor")]
    #[case("jetbrains")]
    #[case("other")]
    fn codex_insert_pending_keeps_horizontal_hud_navigation(#[case] host: &str) {
        let preserve = should_preserve_terminal_caret_navigation_for_input(
            match host {
                "cursor" => TerminalHost::Cursor,
                "jetbrains" => TerminalHost::JetBrains,
                _ => TerminalHost::Other,
            },
            "codex",
            VoiceSendMode::Insert,
            true,
        );
        assert!(!preserve, "host={host}");
        assert_eq!(
            hud_navigation_direction_from_arrow(ArrowKey::Left, preserve),
            -1
        );
        assert_eq!(
            hud_navigation_direction_from_arrow(ArrowKey::Right, preserve),
            1
        );
    }

    #[rstest]
    #[case("cursor", "codex", false)]
    #[case("cursor", "claude", true)]
    #[case("jetbrains", "codex", false)]
    #[case("jetbrains", "claude", false)]
    #[case("other", "codex", false)]
    #[case("other", "claude", false)]
    fn insert_without_pending_routes_horizontal_arrows_to_hud_navigation(
        #[case] host: &str,
        #[case] provider: &str,
        #[case] expected_preserve: bool,
    ) {
        let preserve = should_preserve_terminal_caret_navigation_for_input(
            match host {
                "cursor" => TerminalHost::Cursor,
                "jetbrains" => TerminalHost::JetBrains,
                _ => TerminalHost::Other,
            },
            provider,
            VoiceSendMode::Insert,
            false,
        );
        assert_eq!(
            preserve, expected_preserve,
            "host={host}, provider={provider}"
        );
        assert_eq!(
            hud_navigation_direction_from_arrow(ArrowKey::Left, preserve),
            if expected_preserve { 0 } else { -1 },
            "host={host}, provider={provider}"
        );
        assert_eq!(
            hud_navigation_direction_from_arrow(ArrowKey::Right, preserve),
            if expected_preserve { 0 } else { 1 },
            "host={host}, provider={provider}"
        );
    }
}
