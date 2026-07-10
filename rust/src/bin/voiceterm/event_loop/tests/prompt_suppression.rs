use super::*;

#[test]
fn handle_output_chunk_empty_data_keeps_responding_state_and_suppress_flag() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    state.ui.suppress_startup_escape_input = true;
    state.status_state.recording_state = RecordingState::Responding;
    let mut running = true;

    handle_output_chunk(&mut state, &mut timers, &mut deps, Vec::new(), &mut running);

    assert!(running);
    assert!(state.ui.suppress_startup_escape_input);
    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Responding
    );
}

#[test]
fn handle_output_chunk_non_empty_idle_emits_only_pty_output() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    state.ui.suppress_startup_escape_input = true;
    state.status_state.recording_state = RecordingState::Idle;
    let mut running = true;

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"ok".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(!state.ui.suppress_startup_escape_input);
    assert_eq!(state.status_state.recording_state, RecordingState::Idle);
    let messages: Vec<_> = writer_rx.try_iter().collect();
    assert_eq!(
        messages.len(),
        1,
        "idle non-empty output should not emit an extra status redraw"
    );
    match &messages[0] {
        WriterMessage::PtyOutput(bytes) => assert_eq!(bytes, b"ok"),
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn handle_output_chunk_bash_approval_card_suppresses_hud() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Bash command\nThis command requires approval\nDo you want to proceed?\n1. Yes\n".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.prompt_suppressed);
    let (rows, _) = deps.session.current_winsize();
    let expected_suppressed_rows = state
        .ui
        .terminal_rows
        .saturating_sub(crate::terminal::reserved_rows_for_mode(
            OverlayMode::None,
            state.ui.terminal_cols,
            state.status_state.hud_style,
            true,
        ) as u16)
        .max(1);
    assert_eq!(rows, expected_suppressed_rows);
}

#[test]
fn nonrolling_explicit_approval_card_suppresses_without_backend_label() {
    let _rolling_override = install_prompt_rolling_override(false);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "test".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"This command requires approval\nDo you want to proceed?\n1. Yes\n2. Yes, and don't ask again for this command\n".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(
        state.status_state.prompt_suppressed,
        "explicit approval card must suppress HUD even if backend label guard is unavailable"
    );
}

// Field bug (Cursor+codex): codex's routine approval cards tripped the
// non-rolling latch on ordinary output, driving a suppress→release oscillation
// (HUD box flipping full/collapsed every few seconds). Codex is excluded from
// the latch — suppression buys it nothing (its PTY row budget is unchanged
// while suppressed) and the flip-flop is pure visual churn.
#[test]
fn nonrolling_approval_card_does_not_suppress_for_codex_backend() {
    let _rolling_override = install_prompt_rolling_override(false);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "codex".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"This command requires approval\nDo you want to proceed?\n1. Yes\n2. Yes, and don't ask again for this command\n".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(
        !state.status_state.prompt_suppressed,
        "codex approval cards must not suppress the HUD (oscillation fix)"
    );
}

#[test]
fn nonrolling_long_wrapped_approval_card_still_suppresses() {
    let _rolling_override = install_prompt_rolling_override(false);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "test".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut payload = String::from("This command requires approval\nDo you want to proceed?\n");
    payload.push_str("1. Yes\n");
    for _ in 0..40 {
        payload.push_str("/Users/jguida941/testing_upgrade/codex-voice/rust\n");
    }
    payload.push_str("2. Yes, and don't ask again for Web Search commands in this directory\n");
    payload.push_str("3. No\n");

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        payload.into_bytes(),
        &mut running,
    );

    assert!(running);
    assert!(
        state.status_state.prompt_suppressed,
        "wrapped approval cards must still suppress HUD on non-rolling hosts"
    );
}

#[test]
fn nonrolling_prompt_question_line_suppresses_before_numbered_options() {
    let _rolling_override = install_prompt_rolling_override(false);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "test".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Tool use\nDo you want to proceed?\n".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(
        state.status_state.prompt_suppressed,
        "prompt question line should suppress immediately before numbered options land"
    );
}

#[test]
fn nonrolling_tool_activity_hint_does_not_suppress_without_approval_card() {
    let _rolling_override = install_prompt_rolling_override(false);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Web Search(\"best terminal emulators\")\n".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(
        !state.status_state.prompt_suppressed,
        "tool activity text alone must not hide HUD on non-rolling hosts"
    );
}

#[test]
fn nonrolling_stale_explicit_text_does_not_retrigger_suppression() {
    let _rolling_override = install_prompt_rolling_override(false);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "test".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"This command requires approval\nDo you want to proceed?\n1. Yes\n2. Yes, and don't ask again for this command\n".to_vec(),
        &mut running,
    );
    assert!(running);
    assert!(
        state.status_state.prompt_suppressed,
        "approval card should suppress HUD in non-rolling mode"
    );

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"1".to_vec()),
        &mut running,
    );
    assert!(running);

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Approval accepted. Continuing execution...\n".to_vec(),
        &mut running,
    );
    assert!(running);

    let now = Instant::now();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(20),
    );
    assert!(
        state.status_state.prompt_suppressed,
        "sticky hold should keep HUD suppressed for rapid back-to-back approval cards"
    );

    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(1200),
    );
    assert!(
        !state.status_state.prompt_suppressed,
        "HUD should unsuppress after sticky hold elapses and approval window remains drained"
    );

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Recap: earlier output included \"Do you want to proceed?\" before approval.\n".to_vec(),
        &mut running,
    );
    assert!(running);
    assert!(
        !state.status_state.prompt_suppressed,
        "stale explicit phrase without numbered approval options must not resuppress HUD"
    );
}

#[test]
fn nonrolling_release_arm_defers_on_echo_chunk_until_substantial_output() {
    let _rolling_override = install_prompt_rolling_override(false);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "test".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"This command requires approval\nDo you want to proceed?\n1. Yes\n2. No\n".to_vec(),
        &mut running,
    );
    assert!(running);
    assert!(state.status_state.prompt_suppressed);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"1".to_vec()),
        &mut running,
    );
    assert!(running);

    // A tiny post-input echo should not clear the approval window immediately.
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"1\n".to_vec(),
        &mut running,
    );
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        Instant::now() + Duration::from_millis(25),
    );
    assert!(
        state.status_state.prompt_suppressed,
        "HUD should stay suppressed until substantial post-input output confirms prompt exit"
    );

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Approval accepted. Continuing execution...\n".to_vec(),
        &mut running,
    );
    let now = Instant::now();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(50),
    );
    assert!(
        state.status_state.prompt_suppressed,
        "sticky hold should prevent early unsuppress after substantial output"
    );

    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(1200),
    );
    assert!(
        !state.status_state.prompt_suppressed,
        "HUD should unsuppress after sticky hold elapses and no approval card remains"
    );
}

#[test]
fn nonrolling_sticky_hold_covers_rapid_consecutive_approvals() {
    let _rolling_override = install_prompt_rolling_override(false);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "test".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"This command requires approval\nDo you want to proceed?\n1. Yes\n2. No\n".to_vec(),
        &mut running,
    );
    assert!(running);
    assert!(state.status_state.prompt_suppressed);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"1".to_vec()),
        &mut running,
    );
    assert!(running);

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Approval accepted. Continuing execution...\n".to_vec(),
        &mut running,
    );
    let first_now = Instant::now();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        first_now + Duration::from_millis(100),
    );
    assert!(
        state.status_state.prompt_suppressed,
        "first sticky hold should prevent unsuppress while next approval card may arrive"
    );

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"This command requires approval\nDo you want to proceed?\n1. Yes\n2. No\n".to_vec(),
        &mut running,
    );
    assert!(running);
    assert!(
        state.status_state.prompt_suppressed,
        "second approval card should stay in suppressed state without an unsuppress gap"
    );

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"1".to_vec()),
        &mut running,
    );
    assert!(running);

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Approval accepted. Final step complete.\n".to_vec(),
        &mut running,
    );

    let second_now = Instant::now();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        second_now + Duration::from_millis(100),
    );
    assert!(state.status_state.prompt_suppressed);

    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        second_now + Duration::from_millis(1200),
    );
    assert!(
        !state.status_state.prompt_suppressed,
        "HUD should restore once final sticky hold elapses"
    );
}

#[test]
fn handle_output_chunk_tool_activity_without_approval_hints_does_not_suppress_hud() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Bash(echo $SHELL)\n".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(!state.status_state.prompt_suppressed);

    let now = Instant::now();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(1200),
    );
    assert!(!state.status_state.prompt_suppressed);

    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_secs(4),
    );
    assert!(!state.status_state.prompt_suppressed);
}

#[test]
fn handle_output_chunk_synchronized_cursor_activity_without_approval_hints_does_not_suppress_hud() {
    let _rolling_override = install_prompt_rolling_override(true);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"\x1b[?2026h\r\x1b[6A* Crunched for 47s\r\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(!state.status_state.prompt_suppressed);

    let now = Instant::now();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(1200),
    );
    assert!(!state.status_state.prompt_suppressed);

    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_secs(4),
    );
    assert!(!state.status_state.prompt_suppressed);
}

#[test]
fn handle_output_chunk_synchronized_rewrite_with_historical_approval_phrase_does_not_suppress_hud()
{
    let _rolling_override = install_prompt_rolling_override(true);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"\x1b[?2026h\r\x1b[7ARecap: earlier output included \"Do you want to proceed?\" before approval.\r\r\n\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(
        !state.status_state.prompt_suppressed,
        "quoted approval text in normal transcript output must not hide HUD"
    );
}

#[test]
fn handle_output_chunk_synchronized_rewrite_with_inline_quote_and_yes_no_does_not_suppress_hud() {
    let _rolling_override = install_prompt_rolling_override(true);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"\x1b[?2026h\r\x1b[7ARecap: we previously saw \"Do you want to proceed? (y/n)\" in an earlier step.\r\r\n\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(
        !state.status_state.prompt_suppressed,
        "inline quoted prompt text with y/n markers must not be treated as a live approval card"
    );
}

#[test]
fn handle_output_chunk_synchronized_yes_no_approval_prompt_suppresses_hud() {
    let _rolling_override = install_prompt_rolling_override(true);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"\x1b[?2026h\r\x1b[6AThis command requires approval\r\nDo you want to proceed? (y/n)\r\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(
        state.status_state.prompt_suppressed,
        "live y/n approval prompts in synchronized rewrites must still suppress HUD"
    );
}

#[test]
fn handle_output_chunk_recent_input_echo_rewrite_does_not_re_suppress_hud() {
    let _rolling_override = install_prompt_rolling_override(true);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;
    timers.last_user_input_at = Some(Instant::now());

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"\x1b[?2026h\x1b[2K\x1b[G\x1b[1A\r\x1b[2C\x1b[2Ab\x1b[7m \r\x1b[2B\x1b[27m                                              \x1b[?2026l".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(
        !state.status_state.prompt_suppressed,
        "recent local keystrokes should prevent prompt-input repaint packets from hiding the HUD"
    );
}

#[test]
fn handle_output_chunk_input_echo_rewrite_does_not_suppress_without_recent_input_timestamp() {
    let _rolling_override = install_prompt_rolling_override(true);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"\x1b[?2026h\x1b[2K\x1b[G\x1b[1A\r\x1b[2C\x1b[2Ab\x1b[7m \r\x1b[2B\x1b[27m                                              \x1b[?2026l".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(
        !state.status_state.prompt_suppressed,
        "input-echo rewrites should not hide HUD even when input/output ordering races"
    );
}

#[test]
fn handle_output_chunk_non_empty_responding_stays_responding_until_prompt_ready() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    state.status_state.recording_state = RecordingState::Responding;
    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"done".to_vec(),
        &mut running,
    );

    assert!(running);
    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Responding
    );
    let has_output = writer_rx
        .try_iter()
        .any(|message| matches!(message, WriterMessage::PtyOutput(_)));
    assert!(has_output, "PTY output should always be forwarded");
}

#[test]
fn handle_output_chunk_non_empty_responding_transitions_to_idle_when_prompt_is_ready() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    state.prompt.tracker = PromptTracker::new(
        Some(Regex::new(r"^codex> ?$").expect("prompt regex")),
        true,
        PromptLogger::new(None),
    );
    timers.last_enter_at = Some(Instant::now() - Duration::from_millis(50));
    state.status_state.recording_state = RecordingState::Responding;

    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"codex> \n".to_vec(),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.status_state.recording_state, RecordingState::Idle);
}
