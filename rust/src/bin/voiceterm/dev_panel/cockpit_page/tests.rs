use crate::dev_command::{
    DevCommandCompletion, DevCommandKind, DevCommandStatus, DevCommandUpdate, DevPanelState,
    DevPanelTab, DevTerminalPacket, GitStatusSnapshot, HandoffSnapshot, MemoryCockpitSnapshot,
    MemoryPreviewSection, MemoryStatusSnapshot, RuntimeDiagnosticsSnapshot,
};
use crate::dev_panel::dev_panel_height;
use crate::theme::Theme;

use super::*;

#[test]
fn cockpit_control_page_renders_dashboard() {
    let command_state = DevPanelState::default();
    let panel = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    // Chrome and title assertions (always visible in the viewport).
    assert!(panel.contains("Control"), "title shows Control");
    assert_eq!(
        panel.lines().count(),
        dev_panel_height(),
        "control page line count must match dev_panel_height()"
    );

    // Content assertions via line generator (checks all sections, not just
    // the visible viewport — the Control page may need scrolling).
    let lines = control_page_lines(&command_state);
    let joined = lines.join("\n");
    assert!(joined.contains("Guard State"), "has guard state section");
    assert!(joined.contains("Guarded"), "has exec profile");
    assert!(
        joined.contains("Active Command"),
        "has active command section"
    );
    assert!(
        joined.contains("idle"),
        "shows idle when no command running"
    );
    assert!(
        joined.contains("Last Command Result"),
        "has last result section"
    );
    assert!(
        joined.contains("no commands run yet"),
        "shows no-result placeholder"
    );
    assert!(
        joined.contains("Review Bridge"),
        "has review bridge section"
    );
    assert!(
        joined.contains("Git (current shell path)"),
        "has current-shell git section"
    );
    assert!(
        joined.contains("Action Catalog"),
        "has action catalog summary"
    );
    assert!(joined.contains("14 actions"), "shows correct action count");
}

#[test]
fn cockpit_ops_page_renders_process_and_triage_snapshots() {
    let mut command_state = DevPanelState::default();
    command_state.set_ops_snapshot(crate::dev_command::OpsSnapshot {
        process_audit: crate::dev_command::ProcessAuditSnapshot {
            captured_at: "2026-03-09T00:00:00Z".to_string(),
            strict: true,
            total_detected: 3,
            orphaned_count: 1,
            stale_active_count: 1,
            active_recent_count: 1,
            recent_detached_count: 1,
            active_recent_blocking_count: 1,
            active_recent_advisory_count: 0,
            warning_count: 1,
            error_count: 1,
            ok: false,
            headline: "orphaned repo-related host processes detected".to_string(),
            error_message: String::new(),
        },
        triage: crate::dev_command::OpsTriageSnapshot {
            captured_at: "2026-03-09T00:01:00Z".to_string(),
            total_issues: 4,
            high_count: 1,
            medium_count: 2,
            warning_count: 1,
            external_input_count: 2,
            next_action: "Run process-audit to inspect orphaned helpers.".to_string(),
            summary: "next: Run process-audit to inspect orphaned helpers.".to_string(),
            error_message: String::new(),
        },
    });

    let lines = super::ops_page_lines(&command_state);
    let joined = lines.join("\n");
    assert!(joined.contains("Host Process Hygiene"));
    assert!(joined.contains("Detected: 3 total"));
    assert!(joined.contains("orphaned repo-related host processes"));
    assert!(joined.contains("Triage"));
    assert!(joined.contains("Issues: 4 total"));
    assert!(joined.contains("External inputs: 2"));
    assert!(joined.contains("Typed Ops Actions"));
    assert!(joined.contains("process-audit"));
    assert!(joined.contains("process-cleanup"));
}

#[test]
fn cockpit_control_footer_spells_out_refresh_scope() {
    let commands = DevPanelState::default();
    let total = cockpit_content_line_count(&commands, DevPanelTab::Control);
    let footer = cockpit_page_footer(
        &Theme::Coral.colors(),
        &commands,
        DevPanelTab::Control,
        total,
    );
    assert!(
        footer.contains("review/git/memory"),
        "Control footer should say what Enter refreshes"
    );
}

#[test]
fn cockpit_control_page_shows_review_bridge_when_loaded() {
    let mut command_state = DevPanelState::default();
    command_state.review_mut().load_from_content(
        "# Code Audit\n\n\
         - Last Codex poll: `2026-03-08T09:00:00Z`\n\
         - Last non-audit worktree hash: `abc123`\n\n\
         ## Current Verdict\n\n- Slice accepted.\n",
    );
    let panel = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    assert!(
        panel.contains("2026-03-08T09:00:00Z"),
        "shows poll timestamp"
    );
    assert!(panel.contains("abc123"), "shows worktree hash");
    assert!(panel.contains("Slice accepted"), "shows first verdict line");
}

#[test]
fn cockpit_handoff_page_renders_empty_state_without_snapshot() {
    let command_state = DevPanelState::default();
    let panel = format_cockpit_page(Theme::Codex, &command_state, DevPanelTab::Handoff, 96);
    assert!(panel.contains("Handoff"), "title shows Handoff");
    assert!(
        panel.contains("no handoff data"),
        "empty state shows placeholder when no snapshot set"
    );
    assert_eq!(
        panel.lines().count(),
        dev_panel_height(),
        "handoff page line count must match dev_panel_height()"
    );
}

#[test]
fn cockpit_handoff_page_shows_boot_pack_when_snapshot_set() {
    let mut command_state = DevPanelState::default();
    command_state.set_handoff_snapshot(HandoffSnapshot {
        pack_type: "Boot".to_string(),
        summary: "Test project summary".to_string(),
        active_tasks: vec!["Fix the widget".to_string()],
        recent_decisions: vec!["Use Rust".to_string()],
        evidence_count: 7,
        token_used: 1200,
        token_target: 4096,
        token_trimmed: 0,
        ..Default::default()
    });
    let panel = format_cockpit_page(Theme::Codex, &command_state, DevPanelTab::Handoff, 96);
    assert!(panel.contains("Boot Pack"), "shows pack type");
    assert!(panel.contains("Test project summary"), "shows summary");
    assert!(panel.contains("1200/4096"), "shows token usage");
    assert!(panel.contains("Evidence items: 7"), "shows evidence count");
    assert!(panel.contains("Fix the widget"), "shows active tasks");
    assert!(panel.contains("Use Rust"), "shows recent decisions");
    assert_eq!(
        panel.lines().count(),
        dev_panel_height(),
        "handoff page line count must match dev_panel_height()"
    );
}

#[test]
fn cockpit_handoff_page_shows_resume_bundle_with_review_context() {
    let mut command_state = DevPanelState::default();
    // Review-channel data now comes from the loaded artifact (single source of truth).
    command_state.review_mut().load_from_content(
        "# Code Audit\n\n\
         - Last Codex poll: `2026-03-08T13:44:00Z`\n\
         - Last non-audit worktree hash: `2f184248abcd`\n\n\
         ## Current Instruction For Claude\n\nFinish the Handoff page\n\n\
         ## Current Verdict\n\nSession 6 accepted\n",
    );
    command_state.set_handoff_snapshot(HandoffSnapshot {
        pack_type: "Boot".to_string(),
        summary: "project context".to_string(),
        execution_profile: "Guarded".to_string(),
        last_command_result: "status ok (120ms)".to_string(),
        ..Default::default()
    });
    let panel = format_cockpit_page(Theme::Codex, &command_state, DevPanelTab::Handoff, 96);
    assert!(
        panel.contains("Resume Bundle"),
        "shows resume bundle section"
    );
    assert!(
        panel.contains("Finish the Handoff page"),
        "shows current instruction"
    );
    assert!(panel.contains("Session 6 accepted"), "shows verdict");
    assert!(
        panel.contains("poll 2026-03-08T13:44"),
        "shows bridge status"
    );
    assert!(
        panel.contains("Controller State"),
        "shows controller section"
    );
    assert!(panel.contains("Guarded"), "shows execution profile");
    assert!(
        panel.contains("status ok (120ms)"),
        "shows last command result"
    );
    assert_eq!(
        panel.lines().count(),
        dev_panel_height(),
        "handoff page line count must match dev_panel_height()"
    );
}

#[test]
fn cockpit_handoff_page_shows_fresh_prompt_when_populated() {
    let mut command_state = DevPanelState::default();
    command_state
        .review_mut()
        .load_from_content("## Current Instruction For Claude\n\nDo the next thing\n");
    command_state.set_handoff_snapshot(HandoffSnapshot {
        pack_type: "Boot".to_string(),
        summary: "test".to_string(),
        execution_profile: "Guarded".to_string(),
        fresh_prompt: "Bootstrap this session from the live review channel:\n\nCurrent instruction: Do the next thing\nExecution profile: Guarded\n\nRead CLAUDE.md, AGENTS.md, dev/active/INDEX.md, dev/active/MASTER_PLAN.md, and dev/active/review_channel.md to bootstrap.".to_string(),
        ..Default::default()
    });
    let panel = format_cockpit_page(Theme::Codex, &command_state, DevPanelTab::Handoff, 96);
    assert!(
        panel.contains("Fresh Conversation Prompt"),
        "shows prompt section header"
    );
    assert!(
        panel.contains("Bootstrap this session"),
        "shows prompt opening line"
    );
    assert!(
        panel.contains("Do the next thing"),
        "prompt includes instruction"
    );
    assert!(
        panel.contains("CLAUDE.md"),
        "prompt includes bootstrap files"
    );
}

#[test]
fn cockpit_handoff_page_shows_no_instruction_placeholder_without_review() {
    let mut command_state = DevPanelState::default();
    command_state.set_handoff_snapshot(HandoffSnapshot {
        pack_type: "Boot".to_string(),
        summary: "empty project".to_string(),
        execution_profile: "Guarded".to_string(),
        ..Default::default()
    });
    let panel = format_cockpit_page(Theme::Codex, &command_state, DevPanelTab::Handoff, 96);
    assert!(panel.contains("Resume Bundle"), "shows resume section");
    assert!(
        panel.contains("load Review tab first"),
        "instruction placeholder tells user to load review tab"
    );
}

#[test]
fn cockpit_control_page_shows_memory_snapshot() {
    let mut command_state = DevPanelState::default();
    command_state.set_memory_snapshot(MemoryStatusSnapshot {
        mode_label: "Assist".to_string(),
        capture_allowed: true,
        retrieval_allowed: true,
        events_ingested: 42,
        events_rejected: 3,
        index_size: 39,
        session_id: "abc-123".to_string(),
    });
    // Check content lines directly — memory section may scroll off viewport.
    let lines = control_page_lines(&command_state);
    let joined = lines.join("\n");
    assert!(joined.contains("Assist"), "shows memory mode");
    assert!(joined.contains("Capture: on"), "shows capture enabled");
    assert!(joined.contains("Retrieval: on"), "shows retrieval enabled");
    assert!(joined.contains("42 ingested"), "shows ingested count");
    assert!(joined.contains("3 rejected"), "shows rejected count");
    assert!(joined.contains("39 indexed"), "shows index size");
    assert!(joined.contains("abc-123"), "shows session ID");
}

#[test]
fn cockpit_control_page_no_memory_shows_not_initialized() {
    let command_state = DevPanelState::default();
    let panel = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    assert!(
        panel.contains("not initialized"),
        "shows not-initialized when no memory snapshot"
    );
}

#[test]
fn cockpit_tab_bar_highlights_active_page() {
    let colors = Theme::Coral.colors();
    let bar = cockpit_tab_bar(&colors, DevPanelTab::Review, 80);
    // The active tab (Review) should be styled with info color,
    // while other tabs use dim color. Both should appear in the bar.
    assert!(bar.contains("Control"), "bar shows Control tab");
    assert!(bar.contains("Ops"), "bar shows Ops tab");
    assert!(bar.contains("Review"), "bar shows Review tab");
    assert!(bar.contains("Actions"), "bar shows Actions tab");
    assert!(bar.contains("Handoff"), "bar shows Handoff tab");
    assert!(bar.contains("Memory"), "bar shows Memory tab");
}

/// Helper: feed a DevCommandCompletion into DevPanelState via apply_update.
fn apply_completion(state: &mut DevPanelState, completion: DevCommandCompletion) {
    // First register a launch so apply_update recognizes the request_id.
    state.register_launch(completion.request_id, completion.command);
    state.apply_update(DevCommandUpdate::Completed(completion));
}

#[test]
fn cockpit_control_page_shows_staged_packet_draft() {
    let mut command_state = DevPanelState::default();
    apply_completion(
        &mut command_state,
        DevCommandCompletion {
            request_id: 1,
            command: DevCommandKind::LoopPacket,
            status: DevCommandStatus::Success,
            duration_ms: 42,
            summary: "ok".to_string(),
            stdout_excerpt: None,
            stderr_excerpt: None,
            terminal_packet: Some(DevTerminalPacket {
                packet_id: "pkt-001".to_string(),
                source_command: "loop-packet".to_string(),
                draft_text: "Hello from the staged draft".to_string(),
                auto_send: false,
            }),
        },
    );
    let panel = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    assert!(
        panel.contains("Staged Packet Draft"),
        "shows packet draft section"
    );
    assert!(panel.contains("pkt-001"), "shows packet id");
    assert!(panel.contains("stage only"), "shows stage-only label");
    assert!(
        panel.contains("Hello from the staged draft"),
        "shows draft text"
    );
    assert!(
        panel.contains("read-only preview"),
        "shows read-only indicator"
    );
    assert_eq!(
        panel.lines().count(),
        dev_panel_height(),
        "control page with packet must still match dev_panel_height()"
    );
}

#[test]
fn cockpit_control_page_shows_no_staged_packet_when_empty() {
    let command_state = DevPanelState::default();
    let panel = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    assert!(
        panel.contains("Staged Packet Draft"),
        "section header always shown"
    );
    assert!(
        panel.contains("no staged packet"),
        "shows empty placeholder"
    );
}

#[test]
fn cockpit_control_page_packet_auto_send_label() {
    let mut command_state = DevPanelState::default();
    apply_completion(
        &mut command_state,
        DevCommandCompletion {
            request_id: 2,
            command: DevCommandKind::Triage,
            status: DevCommandStatus::Success,
            duration_ms: 10,
            summary: "done".to_string(),
            stdout_excerpt: None,
            stderr_excerpt: None,
            terminal_packet: Some(DevTerminalPacket {
                packet_id: "pkt-002".to_string(),
                source_command: "triage".to_string(),
                draft_text: "auto content".to_string(),
                auto_send: true,
            }),
        },
    );
    let panel = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    assert!(
        panel.contains("auto-send requested"),
        "shows auto-send label when packet.auto_send is true"
    );
}

#[test]
fn truncate_draft_preview_limits_lines() {
    let draft = "line 1\nline 2\nline 3\nline 4\nline 5";
    let preview = super::truncate_draft_preview(draft, 3);
    assert_eq!(preview.len(), 4, "3 lines + truncation indicator");
    assert_eq!(preview[0], "line 1");
    assert_eq!(preview[2], "line 3");
    assert_eq!(preview[3], "...");
}

#[test]
fn truncate_draft_preview_short_text_no_ellipsis() {
    let draft = "short text";
    let preview = super::truncate_draft_preview(draft, 3);
    assert_eq!(preview.len(), 1);
    assert_eq!(preview[0], "short text");
}

#[test]
fn cockpit_scroll_offset_clamps_and_resets_on_tab_switch() {
    let mut state = DevPanelState::default();
    state.cockpit_scroll_down(5, 10);
    assert_eq!(state.cockpit_scroll_offset(), 5);

    state.cockpit_scroll_up(2);
    assert_eq!(state.cockpit_scroll_offset(), 3);

    // Clamped to max_offset
    state.cockpit_scroll_down(20, 10);
    assert_eq!(state.cockpit_scroll_offset(), 10);

    // Reset on tab switch
    state.toggle_tab();
    assert_eq!(
        state.cockpit_scroll_offset(),
        0,
        "scroll resets on forward tab switch"
    );

    state.cockpit_scroll_down(3, 10);
    state.prev_tab();
    assert_eq!(
        state.cockpit_scroll_offset(),
        0,
        "scroll resets on backward tab switch"
    );
}

#[test]
fn cockpit_control_page_scroll_shows_position_indicator() {
    let mut command_state = DevPanelState::default();
    // Load enough sections to overflow: memory + review + full packet
    command_state.set_memory_snapshot(MemoryStatusSnapshot {
        mode_label: "Assist".to_string(),
        capture_allowed: true,
        retrieval_allowed: true,
        events_ingested: 42,
        events_rejected: 3,
        index_size: 39,
        session_id: "abc-123".to_string(),
    });
    command_state.review_mut().load_from_content(
        "# Code Audit\n\n\
         - Last Codex poll: `2026-03-08T09:00:00Z`\n\
         - Last non-audit worktree hash: `abc123def456`\n\n\
         ## Current Verdict\n\n- Session accepted.\n",
    );
    apply_completion(
        &mut command_state,
        DevCommandCompletion {
            request_id: 1,
            command: DevCommandKind::LoopPacket,
            status: DevCommandStatus::Success,
            duration_ms: 42,
            summary: "ok".to_string(),
            stdout_excerpt: None,
            stderr_excerpt: Some("some stderr output".to_string()),
            terminal_packet: Some(DevTerminalPacket {
                packet_id: "pkt-scroll".to_string(),
                source_command: "loop-packet".to_string(),
                draft_text: "draft line 1\ndraft line 2\ndraft line 3\ndraft line 4".to_string(),
                auto_send: false,
            }),
        },
    );
    // With all sections populated, content should exceed visible rows
    let total = cockpit_content_line_count(&command_state, DevPanelTab::Control);
    let visible = cockpit_visible_rows();
    assert!(
        total > visible,
        "with all sections populated, content ({total}) should exceed visible rows ({visible})"
    );

    // Scrolling down should change which content is visible
    let panel_at_top = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    assert!(
        panel_at_top.contains("Guard State"),
        "top shows first section"
    );

    command_state.cockpit_scroll_down(5, total.saturating_sub(visible));
    let panel_scrolled =
        format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    // After scrolling down 5 rows, Guard State header should be off-screen
    assert!(
        !panel_scrolled.contains("Guard State"),
        "scrolled view should not show first section header"
    );
    // Scroll position indicator should appear in footer
    assert!(panel_scrolled.contains("["), "footer shows scroll position");

    assert_eq!(
        panel_at_top.lines().count(),
        dev_panel_height(),
        "scrolled page line count must still match dev_panel_height()"
    );
    assert_eq!(
        panel_scrolled.lines().count(),
        dev_panel_height(),
        "scrolled page line count must still match dev_panel_height()"
    );
}

#[test]
fn cockpit_control_page_shows_git_snapshot() {
    let mut command_state = DevPanelState::default();
    command_state.set_git_snapshot(GitStatusSnapshot {
        branch: "develop".to_string(),
        dirty_count: 5,
        untracked_count: 12,
        ahead: 3,
        behind: 0,
        last_commit: "abc1234 feat: add git lane".to_string(),
        changed_files: vec![" M src/main.rs".to_string(), "?? new_file.txt".to_string()],
        recent_commits: vec![
            "abc1234 feat: add git lane".to_string(),
            "def5678 fix: resolve merge conflict".to_string(),
        ],
        diff_stat: "3 files changed, 45 insertions(+), 12 deletions(-)".to_string(),
        has_error: false,
        error_message: String::new(),
    });
    // Check content lines directly — git section may scroll off viewport.
    let lines = control_page_lines(&command_state);
    let joined = lines.join("\n");
    assert!(
        joined.contains("Git (current shell path)"),
        "shows current-shell git section header"
    );
    assert!(joined.contains("develop"), "shows branch name");
    assert!(joined.contains("ahead 3"), "shows ahead count");
    assert!(joined.contains("Dirty: 5"), "shows dirty file count");
    assert!(joined.contains("Untracked: 12"), "shows untracked count");
    assert!(joined.contains("abc1234"), "shows HEAD commit");
    assert!(
        joined.contains("Changed files"),
        "shows changed files header"
    );
    assert!(joined.contains("main.rs"), "shows modified file");
    assert!(joined.contains("new_file.txt"), "shows untracked file");
    assert!(
        joined.contains("Diff: 3 files changed"),
        "shows diff stat summary"
    );
    assert!(
        joined.contains("Recent commits"),
        "shows recent commits header"
    );
    assert!(joined.contains("def5678"), "shows older commit");
}

#[test]
fn cockpit_control_page_git_error_shows_message() {
    let mut command_state = DevPanelState::default();
    command_state.set_git_snapshot(GitStatusSnapshot {
        has_error: true,
        error_message: "not a git repository".to_string(),
        ..Default::default()
    });
    let panel = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    assert!(
        panel.contains("not a git repository"),
        "shows error message"
    );
}

#[test]
fn cockpit_handoff_page_shows_git_context() {
    let mut command_state = DevPanelState::default();
    command_state.set_git_snapshot(GitStatusSnapshot {
        branch: "develop".to_string(),
        dirty_count: 3,
        untracked_count: 2,
        ahead: 1,
        last_commit: "abc1234 feat: git lane".to_string(),
        ..Default::default()
    });
    command_state.set_handoff_snapshot(HandoffSnapshot {
        pack_type: "Boot".to_string(),
        summary: "test".to_string(),
        execution_profile: "Guarded".to_string(),
        ..Default::default()
    });
    let lines = handoff_page_lines(&command_state);
    let joined = lines.join("\n");
    assert!(
        joined.contains("Git Context (current shell path)"),
        "shows current-shell git context section"
    );
    assert!(joined.contains("develop"), "shows branch name");
    assert!(joined.contains("5 changed"), "shows total change count");
    assert!(joined.contains("abc1234"), "shows HEAD commit");
}

#[test]
fn cockpit_control_page_no_git_shows_not_loaded() {
    let command_state = DevPanelState::default();
    let panel = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Control, 96);
    assert!(
        panel.contains("not loaded"),
        "shows not-loaded when no git snapshot"
    );
}

#[test]
fn cockpit_visible_rows_and_content_count_are_consistent() {
    let visible = cockpit_visible_rows();
    // Visible rows should be dev_panel_height minus 8 chrome lines
    assert_eq!(visible, dev_panel_height() - 8);

    // Empty state should have content within visible bounds
    let state = DevPanelState::default();
    let control_count = cockpit_content_line_count(&state, DevPanelTab::Control);
    assert!(control_count > 0, "Control page always has content");

    let ops_count = cockpit_content_line_count(&state, DevPanelTab::Ops);
    assert!(ops_count > 0, "Ops page always has content");

    let handoff_count = cockpit_content_line_count(&state, DevPanelTab::Handoff);
    assert!(handoff_count > 0, "Handoff page always has content");

    let memory_count = cockpit_content_line_count(&state, DevPanelTab::Memory);
    assert!(memory_count > 0, "Memory page always has content");
}

#[test]
fn cockpit_memory_footer_spells_out_refresh_scope() {
    let commands = DevPanelState::default();
    let total = cockpit_content_line_count(&commands, DevPanelTab::Memory);
    let footer = cockpit_page_footer(
        &Theme::Coral.colors(),
        &commands,
        DevPanelTab::Memory,
        total,
    );
    assert!(footer.contains("refresh packs"));
    assert!(footer.contains("m memory mode"));
}

#[test]
fn cockpit_memory_page_renders_preview_sections() {
    let mut command_state = DevPanelState::default();
    command_state.set_memory_cockpit_snapshot(MemoryCockpitSnapshot {
        status: Some(MemoryStatusSnapshot {
            mode_label: "Assist".to_string(),
            capture_allowed: true,
            retrieval_allowed: true,
            events_ingested: 12,
            events_rejected: 1,
            index_size: 11,
            session_id: "sess-memory".to_string(),
        }),
        task_query: "MP-340".to_string(),
        task_query_source: "review bridge".to_string(),
        sections: vec![
            MemoryPreviewSection {
                title: "Boot Pack".to_string(),
                summary: "Boot context pack with 3 evidence items.".to_string(),
                lines: vec!["Query: boot".to_string(), "Evidence items: 3".to_string()],
                json_ref: ".voiceterm/memory/exports/boot_pack.json".to_string(),
                markdown_ref: ".voiceterm/memory/exports/boot_pack.md".to_string(),
            },
            MemoryPreviewSection {
                title: "Session Handoff".to_string(),
                summary: "Fresh-conversation handoff preview.".to_string(),
                lines: vec!["Instruction: Finish the cockpit.".to_string()],
                json_ref: ".voiceterm/memory/exports/session_handoff.json".to_string(),
                markdown_ref: ".voiceterm/memory/exports/session_handoff.md".to_string(),
            },
        ],
        context_pack_refs: vec![
            ".voiceterm/memory/exports/boot_pack.json".to_string(),
            ".voiceterm/memory/exports/session_handoff.json".to_string(),
        ],
    });

    let panel = format_cockpit_page(Theme::Coral, &command_state, DevPanelTab::Memory, 96);
    assert!(panel.contains("Memory"), "title shows Memory");

    let lines = memory_page_lines(&command_state);
    let joined = lines.join("\n");
    assert!(joined.contains("Memory Status"));
    assert!(joined.contains("Task Focus"));
    assert!(joined.contains("MP-340"));
    assert!(joined.contains("Boot Pack"));
    assert!(joined.contains("Session Handoff"));
    assert!(joined.contains("JSON:"));
    assert!(joined.contains("Export Index"));
}

#[test]
fn cockpit_memory_page_shows_not_initialized_status_when_snapshot_has_no_ingestor() {
    let mut command_state = DevPanelState::default();
    command_state.set_memory_cockpit_snapshot(MemoryCockpitSnapshot {
        status: None,
        task_query: "memory".to_string(),
        task_query_source: "fallback".to_string(),
        sections: vec![MemoryPreviewSection {
            title: "Boot Pack".to_string(),
            summary: "Memory subsystem not initialized.".to_string(),
            lines: vec!["Initialize memory capture to build preview packs.".to_string()],
            json_ref: String::new(),
            markdown_ref: String::new(),
        }],
        context_pack_refs: Vec::new(),
    });

    let lines = memory_page_lines(&command_state);
    let joined = lines.join("\n");
    assert!(joined.contains("Memory Status"));
    assert!(joined.contains("memory subsystem not initialized"));
    assert!(!joined.contains("Mode: "));
}

#[test]
fn cockpit_control_page_shows_runtime_diagnostics() {
    let mut state = DevPanelState::default();
    state.set_runtime_diagnostics(RuntimeDiagnosticsSnapshot {
        terminal_host: "Cursor".to_string(),
        terminal_rows: 42,
        terminal_cols: 120,
        backend_label: "codex".to_string(),
        theme_name: "Coral".to_string(),
        auto_voice: "Active".to_string(),
        overlay_mode: "DevPanel".to_string(),
        voice_mode: "Manual".to_string(),
        recording_state: "Idle".to_string(),
        dev_mode: true,
        dev_log: true,
        session_uptime_secs: 3725.0,
        transcripts: 15,
        errors: 2,
    });
    let lines = control_page_lines(&state);
    let joined = lines.join("\n");
    assert!(
        joined.contains("Runtime Snapshot"),
        "has Runtime Snapshot section header"
    );
    assert!(joined.contains("Cursor"), "shows terminal host");
    assert!(joined.contains("codex"), "shows backend label");
    assert!(joined.contains("120x42"), "shows terminal dimensions");
    assert!(joined.contains("Coral"), "shows theme name");
    assert!(joined.contains("Active"), "shows auto-voice state");
    assert!(joined.contains("Voice: Manual"), "shows voice mode");
    assert!(joined.contains("Recording: Idle"), "shows recording state");
    assert!(joined.contains("Dev: on"), "shows dev-mode flag");
    assert!(joined.contains("(logging)"), "shows dev-log flag");
    assert!(joined.contains("1h 2m"), "shows session uptime");
    assert!(joined.contains("Transcripts: 15"), "shows transcript count");
    assert!(joined.contains("Errors: 2"), "shows error count");
}

#[test]
fn format_uptime_formats_seconds_minutes_hours() {
    assert_eq!(format_uptime(30.5), "30s");
    assert_eq!(format_uptime(125.0), "2m 5s");
    assert_eq!(format_uptime(3725.0), "1h 2m");
    assert_eq!(format_uptime(0.0), "0s");
    assert_eq!(format_uptime(60.0), "1m 0s");
    assert_eq!(format_uptime(3600.0), "1h 0m");
}

#[test]
fn cockpit_control_page_no_diagnostics_shows_placeholder() {
    let state = DevPanelState::default();
    let lines = control_page_lines(&state);
    let joined = lines.join("\n");
    assert!(
        joined.contains("Runtime Snapshot"),
        "has Runtime Snapshot section header"
    );
    assert!(
        joined.contains("diagnostics not loaded"),
        "shows placeholder when no diagnostics"
    );
}

#[test]
fn cockpit_control_page_shows_command_history_tail() {
    let mut state = DevPanelState::default();

    // Feed 3 completions — the Control page should show the latest under
    // "Last Command Result" and the older two under "Command History".
    for i in 1..=3u64 {
        apply_completion(
            &mut state,
            DevCommandCompletion {
                request_id: i,
                command: DevCommandKind::Status,
                status: DevCommandStatus::Success,
                duration_ms: i * 100,
                summary: format!("run-{i}"),
                stdout_excerpt: None,
                stderr_excerpt: None,
                terminal_packet: None,
            },
        );
    }

    let lines = control_page_lines(&state);
    let joined = lines.join("\n");

    // Latest completion (run-3) appears in "Last Command Result"
    assert!(
        joined.contains("Last Command Result"),
        "has last-result section"
    );
    assert!(joined.contains("run-3"), "latest run shown in last-result");

    // Older completions appear in "Command History" section
    assert!(
        joined.contains("Command History"),
        "has command history section"
    );
    assert!(joined.contains("run-2"), "second-to-last in history");
    assert!(joined.contains("run-1"), "oldest in history");
}

#[test]
fn cockpit_control_page_no_command_history_when_single_completion() {
    let mut state = DevPanelState::default();
    apply_completion(
        &mut state,
        DevCommandCompletion {
            request_id: 1,
            command: DevCommandKind::Status,
            status: DevCommandStatus::Success,
            duration_ms: 50,
            summary: "only-run".to_string(),
            stdout_excerpt: None,
            stderr_excerpt: None,
            terminal_packet: None,
        },
    );
    let lines = control_page_lines(&state);
    let joined = lines.join("\n");

    // With only one completion, "Command History" section should not appear.
    assert!(
        !joined.contains("Command History"),
        "no history section with single completion"
    );
    assert!(
        joined.contains("only-run"),
        "single run still shown in last-result"
    );
}

#[test]
fn command_history_ring_buffer_caps_at_max() {
    let mut state = DevPanelState::default();

    // Feed 12 completions — should cap at MAX_RECENT_COMPLETIONS (8)
    for i in 1..=12u64 {
        apply_completion(
            &mut state,
            DevCommandCompletion {
                request_id: i,
                command: DevCommandKind::Status,
                status: DevCommandStatus::Success,
                duration_ms: i * 10,
                summary: format!("cmd-{i}"),
                stdout_excerpt: None,
                stderr_excerpt: None,
                terminal_packet: None,
            },
        );
    }

    let recent = state.recent_completions();
    assert_eq!(recent.len(), 8, "ring buffer capped at 8 entries");
    assert_eq!(
        recent.first().unwrap().summary,
        "cmd-5",
        "oldest retained is cmd-5 (1-4 evicted)"
    );
    assert_eq!(recent.last().unwrap().summary, "cmd-12", "newest is cmd-12");
}

#[test]
fn cockpit_handoff_page_shows_findings_scope_and_questions() {
    let mut command_state = DevPanelState::default();
    // Review-channel data now comes from the loaded artifact.
    command_state.review_mut().load_from_content(
        "## Current Instruction For Claude\n\nconverge reducer\n\n\
         ## Current Verdict\n\nYellow\n\n\
         ## Open Findings\n\n- gutter click false hit\n- bridge guard stale hash\n\n\
         ## Last Reviewed Scope\n\n- `overlay_mouse.rs`\n- `snapshots.rs`\n\n\
         ## Claude Questions\n\n- Should we migrate to async git?\n",
    );
    command_state.set_handoff_snapshot(HandoffSnapshot::default());

    let lines = handoff_page_lines(&command_state);
    let joined = lines.join("\n");

    assert!(
        joined.contains("Open Findings"),
        "renders Open Findings section"
    );
    assert!(
        joined.contains("gutter click false hit"),
        "shows finding detail"
    );
    assert!(
        joined.contains("bridge guard stale hash"),
        "shows second finding"
    );
    assert!(
        joined.contains("Last Reviewed Scope"),
        "renders scope section"
    );
    assert!(joined.contains("`overlay_mouse.rs`"), "shows scope item");
    assert!(joined.contains("`snapshots.rs`"), "shows second scope item");
    assert!(
        joined.contains("Claude Questions"),
        "renders questions section"
    );
    assert!(
        joined.contains("migrate to async git"),
        "shows question detail"
    );
}
