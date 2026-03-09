use super::super::*;
use crate::scrollable::Scrollable;

#[test]
fn control_page_enter_without_memory_keeps_not_initialized_placeholder() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Control);
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(
        state.dev_panel_commands.memory_snapshot().is_none(),
        "Control refresh must leave memory snapshot absent when no ingestor exists"
    );
}

#[test]
fn handoff_page_enter_refreshes_handoff_snapshot() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Handoff);
    let mut running = true;

    // No handoff snapshot yet
    assert!(
        state.dev_panel_commands.handoff_snapshot().is_none(),
        "no snapshot before Enter"
    );

    // Press Enter — should generate a handoff snapshot
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    let snap = state
        .dev_panel_commands
        .handoff_snapshot()
        .expect("Enter on Handoff page should generate handoff snapshot");
    // Without a memory ingestor, refresh_handoff_snapshot still produces a
    // default snapshot with controller metadata populated.
    assert_eq!(
        snap.execution_profile, "Guarded",
        "snapshot should have execution profile from controller state"
    );
}

#[test]
fn memory_page_enter_refreshes_memory_cockpit_snapshot() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Memory);
    let mut running = true;

    state.memory_ingestor = Some(
        crate::memory::MemoryIngestor::new(
            "memory-enter-session".to_string(),
            "memory-enter-project".to_string(),
            None,
            crate::memory::MemoryMode::Assist,
        )
        .unwrap(),
    );
    state
        .memory_ingestor
        .as_mut()
        .expect("memory ingestor should exist")
        .ingest_event_raw(
            crate::memory::types::EventSource::PtyInput,
            crate::memory::types::EventType::Decision,
            crate::memory::types::EventRole::Assistant,
            "Track MP-340 overlay memory cockpit progress.",
            0.8,
            &["memory"],
            &["MP-340"],
            &[],
        );

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    let cockpit = state
        .dev_panel_commands
        .memory_cockpit_snapshot()
        .expect("Memory Enter should build cockpit snapshot");
    assert_eq!(cockpit.task_query_source, "review bridge");
    assert!(cockpit.task_query.starts_with("MP-"));
    assert!(
        cockpit
            .sections
            .iter()
            .any(|section| section.title == "Task Pack"),
        "memory cockpit should include task-pack preview"
    );
}

#[test]
fn memory_page_enter_without_memory_keeps_absent_status() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Memory);
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    let cockpit = state
        .dev_panel_commands
        .memory_cockpit_snapshot()
        .expect("Memory Enter should still build cockpit snapshot");
    assert!(
        cockpit.status.is_none(),
        "memory cockpit must leave status absent when no ingestor exists"
    );
    assert!(
        cockpit
            .sections
            .iter()
            .all(|section| section.summary == "Memory subsystem not initialized."),
        "memory cockpit should still stage not-initialized preview sections"
    );
}

#[test]
fn handoff_direct_entry_loads_review_artifact_without_prior_tab_visits() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    let mut running = true;

    // Pre-condition: no review artifact loaded, no git snapshot cached.
    assert!(
        state.dev_panel_commands.review().artifact().is_none(),
        "review artifact should not be loaded before any tab visit"
    );
    assert!(
        state.dev_panel_commands.git_snapshot().is_none(),
        "git snapshot should not be cached before any tab visit"
    );

    // Go directly to Handoff — the default tab is Actions, so Tab cycles
    // through Actions -> Review -> Control -> Handoff. Set directly for clarity.
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Handoff);

    // Press Enter to trigger the refresh path (same as on_tab_entered).
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    // The Handoff path should have self-loaded the review artifact.
    // code_audit.md exists in this repo, so load_review should succeed.
    assert!(
        state.dev_panel_commands.review().artifact().is_some()
            || state.dev_panel_commands.review().load_error().is_some(),
        "Handoff direct entry should attempt to load review artifact"
    );

    // Git snapshot should also be populated from the self-sufficient path.
    assert!(
        state.dev_panel_commands.git_snapshot().is_some(),
        "Handoff direct entry should populate git snapshot"
    );

    // The handoff snapshot itself should contain review context.
    let snap = state
        .dev_panel_commands
        .handoff_snapshot()
        .expect("Handoff Enter should produce a snapshot");
    assert_eq!(
        snap.execution_profile, "Guarded",
        "controller metadata should be populated"
    );
    // If the artifact loaded successfully, instruction should be non-empty
    // (code_audit.md in this repo has a Current Instruction section).
    // Review data is now read directly from the artifact, not from the snapshot.
    if let Some(artifact) = state.dev_panel_commands.review().artifact() {
        assert!(
            !artifact.instruction.is_empty(),
            "Review artifact should have instruction after direct Handoff entry loads review"
        );
    }
}

#[test]
fn handoff_direct_entry_populates_git_context_in_fresh_prompt() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Handoff);
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    let snap = state
        .dev_panel_commands
        .handoff_snapshot()
        .expect("should produce handoff snapshot");

    // The fresh prompt should contain git context from the self-loaded snapshot.
    // The exact label can evolve as the snapshot source gets more precise, but
    // the prompt must keep an explicit git-context line.
    assert!(
        snap.fresh_prompt.contains("Git (") || snap.fresh_prompt.contains("Git:"),
        "fresh prompt should include git context even on direct Handoff entry: got '{}'",
        &snap.fresh_prompt[..snap.fresh_prompt.len().min(200)],
    );
}

#[test]
fn review_footer_close_click_handles_raw_view_with_scroll_suffix() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.terminal_rows = 40; // overlay is 30 rows; terminal must be tall enough
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Review);
    state.dev_panel_commands.review_mut().load_from_content(
        "# Code Audit\n\n## Current Verdict\n\n- line 1\n- line 2\n- line 3\n- line 4\n- line 5\n- line 6\n- line 7\n- line 8\n- line 9\n- line 10\n- line 11\n- line 12\n- line 13\n- line 14\n- line 15\n- line 16\n- line 17\n- line 18\n- line 19\n- line 20\n- line 21\n- line 22\n- line 23\n- line 24\n- line 25\n",
    );
    state.dev_panel_commands.review_mut().toggle_view_mode();
    let visible = crate::dev_panel::review_visible_rows(false);
    let total = crate::dev_panel::review_content_line_count(
        &state.dev_panel_commands,
        state.ui.terminal_cols as usize,
    );
    state
        .dev_panel_commands
        .review_mut()
        .scroll_down(3, total.saturating_sub(visible));

    let (x, y) = dev_panel_footer_close_click(&state);
    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
}

#[test]
fn handoff_footer_close_click_handles_scroll_suffix() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.terminal_rows = 40; // overlay is 30 rows; terminal must be tall enough
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Handoff);
    state
        .dev_panel_commands
        .set_handoff_snapshot(crate::dev_command::HandoffSnapshot {
            pack_type: "Boot".to_string(),
            summary: "project summary".to_string(),
            active_tasks: (0..24).map(|idx| format!("task {idx}")).collect(),
            recent_decisions: (0..16).map(|idx| format!("decision {idx}")).collect(),
            evidence_count: 8,
            token_used: 512,
            token_target: 4096,
            execution_profile: "Guarded".to_string(),
            fresh_prompt: "prompt".to_string(),
            ..Default::default()
        });
    // Load a review artifact so handoff page has review-channel context.
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content("## Current Instruction For Claude\n\ntest instruction\n");
    let visible = crate::dev_panel::cockpit_visible_rows();
    let total = crate::dev_panel::cockpit_content_line_count(
        &state.dev_panel_commands,
        crate::dev_command::DevPanelTab::Handoff,
    );
    state
        .dev_panel_commands
        .cockpit_scroll_down(3, total.saturating_sub(visible));

    let (x, y) = dev_panel_footer_close_click(&state);
    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
}

#[test]
fn handoff_copy_sends_osc52_through_writer_channel() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Handoff);
    state
        .dev_panel_commands
        .set_handoff_snapshot(crate::dev_command::HandoffSnapshot {
            fresh_prompt: "copy me".to_string(),
            ..Default::default()
        });
    while writer_rx.try_recv().is_ok() {}

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![b'c']),
        &mut running,
    );

    let writer_messages: Vec<_> = writer_rx.try_iter().collect();
    assert!(
        writer_messages.iter().any(|message| match message {
            WriterMessage::TerminalBytes(bytes) =>
                bytes == &crate::writer::osc52_copy_bytes("copy me"),
            _ => false,
        }),
        "copy action should send OSC 52 through the writer channel"
    );
    assert_eq!(
        state.current_status.as_deref(),
        Some("Prompt copied to clipboard (OSC 52)")
    );
}

#[test]
fn control_enter_refresh_rebuilds_runtime_snapshot() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Control);
    assert!(
        state.dev_panel_commands.runtime_diagnostics().is_none(),
        "runtime snapshot should start empty before explicit refresh"
    );

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    let runtime = state
        .dev_panel_commands
        .runtime_diagnostics()
        .expect("Control refresh should rebuild runtime diagnostics");
    assert_eq!(runtime.backend_label, deps.backend_label);
}

#[test]
fn handoff_enter_refresh_force_reloads_review_and_git() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    let mut running = true;

    // Pre-load the review artifact by visiting the Review tab first.
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Review);
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    assert!(
        state.dev_panel_commands.review().artifact().is_some(),
        "Review tab should load artifact"
    );

    // Pre-load git by visiting Control.
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Control);
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    assert!(
        state.dev_panel_commands.git_snapshot().is_some(),
        "Control tab should load git snapshot"
    );

    // Switch to Handoff and press Enter — should force-reload both sources
    // (not skip because caches already exist).
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Handoff);
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    // Artifact should still be loaded after force-reload.
    assert!(
        state.dev_panel_commands.review().artifact().is_some(),
        "Enter refresh should reload (not clear) the artifact"
    );
    // Git snapshot should still be populated after force-reload.
    assert!(
        state.dev_panel_commands.git_snapshot().is_some(),
        "Enter refresh should reload (not clear) the git snapshot"
    );
    // Handoff snapshot should reflect the force-reloaded data.
    let snap = state
        .dev_panel_commands
        .handoff_snapshot()
        .expect("Enter refresh should produce a fresh handoff snapshot");
    assert_eq!(snap.execution_profile, "Guarded");
}

#[test]
fn handoff_tab_switch_lazy_loads_missing_caches_only() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;

    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Review);
    let mut running = true;
    let review_lines = (1..=80)
        .map(|idx| format!("- line {idx}"))
        .collect::<Vec<_>>()
        .join("\n");
    let review_content = format!("# Code Audit\n\n## Current Verdict\n\n{review_lines}\n");
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content(&review_content);
    state.dev_panel_commands.review_mut().toggle_view_mode();
    let visible = crate::dev_panel::review_visible_rows(false);
    let total = crate::dev_panel::review_content_line_count(
        &state.dev_panel_commands,
        state.ui.terminal_cols as usize,
    );
    state
        .dev_panel_commands
        .review_mut()
        .scroll_down(3, total.saturating_sub(visible));
    let scroll_before = state.dev_panel_commands.review().scroll_offset();
    assert!(
        state.dev_panel_commands.review().artifact().is_some(),
        "precondition: review artifact must be loaded"
    );
    assert!(
        scroll_before > 0,
        "precondition: review tab must be scrolled"
    );

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x09]),
        &mut running,
    );
    assert_eq!(
        state.dev_panel_commands.active_tab(),
        crate::dev_command::DevPanelTab::Actions,
        "Tab should advance to Actions"
    );

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b, b'[', b'Z']),
        &mut running,
    );
    assert_eq!(
        state.dev_panel_commands.active_tab(),
        crate::dev_command::DevPanelTab::Review,
        "Shift+Tab should return to Review"
    );
    assert_eq!(
        state.dev_panel_commands.review().scroll_offset(),
        scroll_before,
        "lazy tab return should preserve review scroll instead of reloading"
    );
}

#[test]
fn review_tab_arrow_scroll_reaches_stale_lane_tail() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Review);

    let verdict_lines = (1..=40)
        .map(|idx| format!("- verdict-row-{idx:03}"))
        .collect::<Vec<_>>()
        .join("\n");
    let review_content =
        format!("## Current Verdict\n\n{verdict_lines}\n\n## Claude Status\n\n- synced\n");
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content(&review_content);
    state
        .dev_panel_commands
        .review_mut()
        .set_load_error("permission denied".to_string());

    let visible = crate::dev_panel::review_scroll_visible_rows(&state.dev_panel_commands);
    let total = crate::dev_panel::review_content_line_count(
        &state.dev_panel_commands,
        state.ui.terminal_cols as usize,
    );
    let expected_max_offset = total.saturating_sub(visible);
    assert!(
        expected_max_offset > 0,
        "fixture must exceed the stale-banner viewport"
    );

    let mut running = true;
    for _ in 0..expected_max_offset {
        handle_input_event(
            &mut state,
            &mut timers,
            &mut deps,
            InputEvent::Bytes(vec![0x1b, b'[', b'B']),
            &mut running,
        );
    }

    assert_eq!(
        state.dev_panel_commands.review().scroll_offset(),
        expected_max_offset,
        "Review arrow scrolling should use the stale-banner-adjusted max offset"
    );
}

#[test]
fn background_review_poll_refreshes_handoff_when_handoff_tab_visible() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Handoff);

    // Pre-load with dummy content that differs from the real code_audit.md,
    // so the next poll_review sees a content change.
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content("## dummy\n\n- placeholder that does not match the real file\n");

    // No handoff snapshot yet.
    assert!(
        state.dev_panel_commands.handoff_snapshot().is_none(),
        "no handoff snapshot before poll"
    );

    let toast_count_before = state.toast_center.active_count();
    let now = Instant::now();
    timers.last_review_poll = now - Duration::from_secs(6);
    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    // Since Handoff tab is visible, the poll should refresh the snapshot
    // instead of emitting a toast.
    assert_eq!(
        state.toast_center.active_count(),
        toast_count_before,
        "no toast when Handoff tab is visible — re-render instead"
    );
    assert!(
        state.dev_panel_commands.handoff_snapshot().is_some(),
        "background poll should refresh handoff snapshot when Handoff tab is visible"
    );
}

#[test]
fn background_review_poll_refreshes_memory_when_memory_tab_visible() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .set_tab(crate::dev_command::DevPanelTab::Memory);
    state.memory_ingestor = Some(
        crate::memory::MemoryIngestor::new(
            "memory-poll-session".to_string(),
            "memory-poll-project".to_string(),
            None,
            crate::memory::MemoryMode::Assist,
        )
        .unwrap(),
    );
    state
        .dev_panel_commands
        .review_mut()
        .load_from_content("## dummy\n\n- placeholder that does not match the real file\n");

    assert!(
        state.dev_panel_commands.memory_cockpit_snapshot().is_none(),
        "no memory cockpit snapshot before poll"
    );

    let toast_count_before = state.toast_center.active_count();
    let now = Instant::now();
    timers.last_review_poll = now - Duration::from_secs(6);
    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    assert_eq!(
        state.toast_center.active_count(),
        toast_count_before,
        "no toast when Memory tab is visible — re-render instead"
    );
    assert!(
        state.dev_panel_commands.memory_cockpit_snapshot().is_some(),
        "background poll should refresh memory cockpit when Memory tab is visible"
    );
}
