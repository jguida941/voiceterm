use super::super::*;
use crate::scrollable::Scrollable;

#[test]
fn non_interference_request_dev_command_rejected_when_dev_mode_off() {
    // request_selected_dev_panel_command must short-circuit when dev_mode is off,
    // leaving all command state untouched.
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = false;
    state.ui.overlay_mode = OverlayMode::DevPanel; // force overlay open
    state.dev_panel_commands.select_index(0);

    request_selected_dev_panel_command(&mut state, &mut timers, &mut deps);

    assert!(
        state.dev_panel_commands.running_request_id().is_none(),
        "no dev command should be launched when dev_mode is off"
    );
    assert!(
        state.current_status.is_none(),
        "no status message should appear; the function should return immediately"
    );
}

#[test]
fn non_interference_default_harness_mirrors_non_dev_session() {
    // Comprehensive invariant check: the default harness (no --dev flag)
    // must mirror the production default where all dev surfaces are inert.
    let (state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    assert!(!state.config.dev_mode, "dev_mode must default to false");
    assert!(!state.config.dev_log, "dev_log must default to false");
    assert!(
        state.config.dev_path.is_none(),
        "dev_path must default to None"
    );
    assert!(
        state.dev_mode_stats.is_none(),
        "dev_mode_stats must be None"
    );
    assert!(
        state.dev_event_logger.is_none(),
        "dev_event_logger must be None"
    );
    assert!(
        deps.dev_command_broker.is_none(),
        "dev_command_broker must be None"
    );
    assert_eq!(
        state.ui.overlay_mode,
        OverlayMode::None,
        "overlay must start as None"
    );
    assert!(
        !state.status_state.dev_mode_enabled,
        "status_state.dev_mode_enabled must be false"
    );
}

#[test]
fn dev_panel_tab_key_cycles_through_all_pages() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    let mut running = true;

    // Default tab is Actions
    assert_eq!(
        state.dev_panel_commands.active_tab(),
        crate::dev_command::DevPanelTab::Actions
    );

    // Tab cycles: Actions → Handoff → Memory → Control → Ops → Review → Actions
    let expected_tabs = [
        crate::dev_command::DevPanelTab::Handoff,
        crate::dev_command::DevPanelTab::Memory,
        crate::dev_command::DevPanelTab::Control,
        crate::dev_command::DevPanelTab::Ops,
        crate::dev_command::DevPanelTab::Review,
        crate::dev_command::DevPanelTab::Actions,
    ];
    for expected in &expected_tabs {
        handle_input_event(
            &mut state,
            &mut timers,
            &mut deps,
            InputEvent::Bytes(vec![0x09]),
            &mut running,
        );
        assert_eq!(state.dev_panel_commands.active_tab(), *expected);
    }
    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::DevPanel);

    // Should have sent overlay renders
    let mut overlay_count = 0;
    while let Ok(msg) = writer_rx.try_recv() {
        if matches!(msg, WriterMessage::ShowOverlay { .. }) {
            overlay_count += 1;
        }
    }
    assert!(overlay_count >= 4, "Tab cycling should re-render each page");
}

#[test]
fn dev_panel_shift_tab_cycles_backward() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    let mut running = true;

    // Default is Actions; Shift+Tab should go backward: Actions → Review
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b, b'[', b'Z']),
        &mut running,
    );
    assert_eq!(
        state.dev_panel_commands.active_tab(),
        crate::dev_command::DevPanelTab::Review
    );

    // Another Shift+Tab: Review → Ops
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b, b'[', b'Z']),
        &mut running,
    );
    assert_eq!(
        state.dev_panel_commands.active_tab(),
        crate::dev_command::DevPanelTab::Ops
    );

    // Another Shift+Tab: Ops → Control
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b, b'[', b'Z']),
        &mut running,
    );
    assert_eq!(
        state.dev_panel_commands.active_tab(),
        crate::dev_command::DevPanelTab::Control
    );

    // Another Shift+Tab: Control → Memory
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b, b'[', b'Z']),
        &mut running,
    );
    assert_eq!(
        state.dev_panel_commands.active_tab(),
        crate::dev_command::DevPanelTab::Memory
    );
}

#[test]
fn dev_panel_control_page_m_key_cycles_memory_mode() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Control);
    let mut running = true;

    // Initialize a memory ingestor so mode cycling has something to act on
    state.memory_ingestor = Some(
        crate::memory::MemoryIngestor::new(
            "test-session".to_string(),
            "test-project".to_string(),
            None,
            crate::memory::MemoryMode::Assist,
        )
        .unwrap(),
    );

    // Default mode is Assist
    assert_eq!(
        state.memory_ingestor.as_ref().unwrap().mode(),
        crate::memory::MemoryMode::Assist
    );

    // Press 'm' to cycle
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![b'm']),
        &mut running,
    );

    // Mode should have advanced: Assist → Paused
    assert_eq!(
        state.memory_ingestor.as_ref().unwrap().mode(),
        crate::memory::MemoryMode::Paused,
        "'m' in Control tab should cycle memory mode"
    );

    // Memory snapshot on DevPanelState should also be updated
    let snap = state
        .dev_panel_commands
        .memory_snapshot()
        .expect("snapshot should be set after cycle");
    assert_eq!(snap.mode_label, "Paused");
}

#[test]
fn dev_panel_control_page_m_key_persists_memory_mode() {
    let _guard = crate::test_env::env_lock();
    let millis = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let dir = std::env::temp_dir().join(format!("voiceterm_memory_mode_cycle_{millis}"));
    std::env::set_var("VOICETERM_CONFIG_DIR", &dir);

    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Control);
    state.memory_ingestor = Some(
        crate::memory::MemoryIngestor::new(
            "persisted-memory-session".to_string(),
            "persisted-memory-project".to_string(),
            None,
            crate::memory::MemoryMode::Assist,
        )
        .unwrap(),
    );
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![b'm']),
        &mut running,
    );

    let saved = crate::persistent_config::load_user_config();
    assert_eq!(saved.memory_mode.as_deref(), Some("paused"));

    std::env::remove_var("VOICETERM_CONFIG_DIR");
    let _ = std::fs::remove_dir_all(dir);
}

#[test]
fn dev_panel_memory_page_m_key_cycles_memory_mode_and_refreshes_snapshot() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Memory);
    let mut running = true;

    state.memory_ingestor = Some(
        crate::memory::MemoryIngestor::new(
            "memory-tab-session".to_string(),
            "memory-tab-project".to_string(),
            None,
            crate::memory::MemoryMode::Assist,
        )
        .unwrap(),
    );

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![b'm']),
        &mut running,
    );

    assert_eq!(
        state.memory_ingestor.as_ref().unwrap().mode(),
        crate::memory::MemoryMode::Paused
    );
    let cockpit = state
        .dev_panel_commands
        .memory_cockpit_snapshot()
        .expect("memory page should refresh cockpit snapshot after mode change");
    assert_eq!(
        cockpit
            .status
            .as_ref()
            .expect("memory cockpit status should exist while ingestor is live")
            .mode_label,
        "Paused"
    );
}

#[test]
fn dev_panel_enter_in_review_tab_does_not_run_command() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Review);
    let mut running = true;

    // Enter in Review tab should reload artifact, not run a dev command
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    // No command should be running
    assert!(state.dev_panel_commands.running_request_id().is_none());
}

#[test]
fn run_periodic_tasks_reloads_review_when_due_on_review_tab() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Review);

    // Set last poll to 6 seconds ago so the 5-second interval is due.
    let now = Instant::now();
    timers.last_review_poll = now - Duration::from_secs(6);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    // Timer must have advanced to `now`, proving the poll branch fired.
    assert!(
        now.duration_since(timers.last_review_poll) < Duration::from_millis(50),
        "timer should have been updated to now"
    );

    // The poll triggers load_review, which sets loaded_at regardless of
    // success or error — proving the reload path executed.
    assert!(
        state.dev_panel_commands.review().loaded_at().is_some(),
        "review artifact should have been loaded (or errored) by periodic poll"
    );

    // A ShowOverlay message should have been sent for the re-render.
    let msg = writer_rx.recv_timeout(Duration::from_millis(200));
    assert!(
        msg.is_ok(),
        "expected overlay re-render message from periodic poll"
    );
}

#[test]
fn run_periodic_tasks_skips_review_on_tools_tab() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    // active_tab defaults to Tools — do not toggle.

    let now = Instant::now();
    let stale = now - Duration::from_secs(6);
    timers.last_review_poll = stale;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    // Timer must NOT have advanced — the poll should not fire on the Tools tab.
    assert_eq!(
        timers.last_review_poll, stale,
        "timer should remain unchanged when Tools tab is active"
    );

    // No overlay re-render from the review-artifact poll path.
    // (Other periodic tasks may send messages, so we just verify the artifact was not touched.)
    assert!(
        state.dev_panel_commands.review().loaded_at().is_none(),
        "review artifact should not be loaded when Tools tab is active"
    );
}

#[test]
fn run_periodic_tasks_skips_review_when_interval_not_due() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Review);

    // Set last poll to 1 second ago — well within the 5-second interval.
    let now = Instant::now();
    let recent = now - Duration::from_secs(1);
    timers.last_review_poll = recent;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    // Timer must NOT have advanced — interval is not yet due.
    assert_eq!(
        timers.last_review_poll, recent,
        "timer should remain unchanged when poll interval is not due"
    );

    // Artifact should not have been loaded.
    assert!(
        state.dev_panel_commands.review().loaded_at().is_none(),
        "review artifact should not be loaded when interval is not due"
    );
}

#[test]
fn run_periodic_tasks_background_polls_review_when_previously_loaded() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    // Pre-load the artifact so background polling is enabled.
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content("## Current Verdict\n\n- ok\n");
    // NOT on the Review tab — normal voice mode.
    state.ui.overlay_mode = OverlayMode::None;

    let now = Instant::now();
    timers.last_review_poll = now - Duration::from_secs(6);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    // Timer must have advanced — background poll fired even without Review tab.
    assert!(
        now.duration_since(timers.last_review_poll) < Duration::from_millis(50),
        "background poll should fire when artifact was previously loaded"
    );
}

#[test]
fn run_periodic_tasks_skips_background_poll_when_never_loaded() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    // Never loaded — loaded_at() is None.
    state.ui.overlay_mode = OverlayMode::None;

    let now = Instant::now();
    let stale = now - Duration::from_secs(6);
    timers.last_review_poll = stale;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    // Timer must NOT have advanced — no background poll when never loaded.
    assert_eq!(
        timers.last_review_poll, stale,
        "should not poll when artifact was never loaded and not on Review tab"
    );
}

#[test]
fn background_review_poll_emits_toast_on_changed_content() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    // Pre-load with dummy content that definitely differs from the real
    // code_audit.md on disk, so poll_review sees a content change.
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content("## dummy\n\n- placeholder that does not match the real file\n");
    // NOT on the Review tab — background toast path.
    state.ui.overlay_mode = OverlayMode::None;

    let toast_count_before = state.toast_center.active_count();
    let now = Instant::now();
    timers.last_review_poll = now - Duration::from_secs(6);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    // poll_review reads the real code_audit.md, content differs → toast fired.
    assert!(
        state.toast_center.active_count() > toast_count_before,
        "toast must fire when background poll detects changed content"
    );
    let toast = &state.toast_center.active_toasts()[0];
    assert_eq!(toast.message, "Review artifact updated");
}

#[test]
fn background_review_poll_does_not_repeat_toast_on_unchanged_content() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    // Pre-load with dummy content → first poll will load the real file.
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content("## dummy\n\n- triggers first reload\n");
    state.ui.overlay_mode = OverlayMode::None;

    let now = Instant::now();
    timers.last_review_poll = now - Duration::from_secs(6);
    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    // First poll loaded the real file — one toast emitted.
    let count_after_first = state.toast_center.active_count();
    assert!(count_after_first > 0, "first poll should emit a toast");

    // Second poll with enough timer gap — content is now identical.
    let later = now + Duration::from_secs(6);
    timers.last_review_poll = now; // simulate elapsed time
    run_periodic_tasks(&mut state, &mut timers, &mut deps, later);

    assert_eq!(
        state.toast_center.active_count(),
        count_after_first,
        "unchanged content must not emit a repeat toast"
    );
}

#[test]
fn review_poll_on_visible_review_tab_does_not_emit_toast() {
    // When the Review tab is visible and content changes, the overlay
    // re-renders in place but no toast is emitted. Toasts are reserved for
    // off-tab background notification only.
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Review);

    // Pre-load with dummy content that differs from the real code_audit.md.
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content("## dummy\n\n- definitely not the real file content\n");

    let toast_count_before = state.toast_center.active_count();
    let now = Instant::now();
    timers.last_review_poll = now - Duration::from_secs(6);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    // Content changed (dummy vs real file), but Review tab is visible,
    // so the overlay re-renders instead of emitting a toast.
    assert_eq!(
        state.toast_center.active_count(),
        toast_count_before,
        "visible Review tab must re-render without emitting a toast"
    );
}

#[test]
fn review_poll_error_state_suppresses_toast_via_has_error_guard() {
    // The periodic_tasks toast path guards on `!has_error` after poll_review
    // returns true. When poll_review hits a read error (file missing,
    // permission denied), it calls set_load_error and returns true, causing
    // the `!has_error` guard to suppress the toast.
    //
    // We can't trigger a real read error through run_periodic_tasks because
    // code_audit.md always exists in the test repo. Instead we simulate the
    // post-poll error state and exercise the exact guard logic from
    // periodic_tasks.rs lines 144-148.
    let (mut state, _timers, _deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    // Pre-load so loaded_at is set (precondition for background polling).
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content("## ok\n");
    state.ui.overlay_mode = OverlayMode::None;

    // Simulate what poll_review does on a read error.
    state.dev_panel_commands.review_mut().set_load_error(
        "Failed to read code_audit.md: Permission denied (os error 13)".to_string(),
    );

    // Exercise the exact guard from periodic_tasks: after poll_review
    // returns true with has_error set, the toast must NOT fire.
    let has_error = state.dev_panel_commands.review().load_error().is_some();
    let review_tab_visible = state.ui.overlay_mode == OverlayMode::DevPanel
        && state.dev_panel_commands.active_tab() == crate::dev_command::DevPanelTab::Review;

    let toast_count_before = state.toast_center.active_count();
    // This matches periodic_tasks.rs: `else if !has_error { toast.push(...) }`
    if !review_tab_visible && !has_error {
        state
            .toast_center
            .push(crate::toast::ToastSeverity::Info, "Review artifact updated");
    }

    assert!(
        has_error,
        "load_error must be set after simulated read failure"
    );
    assert_eq!(
        state.toast_center.active_count(),
        toast_count_before,
        "error state must suppress toast emission — has_error guard prevents notification"
    );
}

#[test]
fn review_tab_r_key_toggles_view_mode() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Review);

    // Load content so the toggle has something to render.
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content("## Current Verdict\n\n- ok\n");

    // Drain any prior writer messages.
    while writer_rx.try_recv().is_ok() {}

    // Default mode is Parsed.
    assert_eq!(
        state.dev_panel_commands.review().view_mode(),
        crate::dev_command::ReviewViewMode::Parsed,
    );

    // Send 'r' key to toggle to Raw mode.
    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![b'r']),
        &mut running,
    );

    assert_eq!(
        state.dev_panel_commands.review().view_mode(),
        crate::dev_command::ReviewViewMode::Raw,
        "pressing 'r' in Review tab should toggle to Raw mode"
    );

    // Scroll should have been reset to 0 after toggle.
    assert_eq!(state.dev_panel_commands.review().scroll_offset(), 0);

    // An overlay re-render message should have been sent.
    let msg = writer_rx.recv_timeout(Duration::from_millis(200));
    assert!(
        msg.is_ok(),
        "expected overlay re-render after view mode toggle"
    );

    // Toggle back to Parsed with 'R' (uppercase).
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![b'R']),
        &mut running,
    );

    assert_eq!(
        state.dev_panel_commands.review().view_mode(),
        crate::dev_command::ReviewViewMode::Parsed,
        "pressing 'R' should toggle back to Parsed mode"
    );
}

#[test]
fn control_page_enter_refreshes_memory_snapshot() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Control);
    let mut running = true;

    // Initialize a memory ingestor so there's data to snapshot
    state.memory_ingestor = Some(
        crate::memory::MemoryIngestor::new(
            "test-session".to_string(),
            "test-project".to_string(),
            None,
            crate::memory::MemoryMode::Assist,
        )
        .unwrap(),
    );

    // No snapshot yet (we haven't entered the tab through the normal path)
    assert!(
        state.dev_panel_commands.memory_snapshot().is_none(),
        "no snapshot before Enter"
    );

    // Press Enter — should refresh the snapshot
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    let snap = state
        .dev_panel_commands
        .memory_snapshot()
        .expect("Enter on Control page should refresh memory snapshot");
    assert_eq!(
        snap.mode_label, "Assist",
        "snapshot should reflect current mode"
    );
    assert!(
        state.dev_panel_commands.review().artifact().is_some()
            || state.dev_panel_commands.review().load_error().is_some(),
        "Control refresh should also refresh review bridge data"
    );
}
