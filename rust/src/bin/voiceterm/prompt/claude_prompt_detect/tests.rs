use super::*;

#[test]
fn detector_ignores_non_claude_backend() {
    let mut detector = ClaudePromptDetector::new(false);
    let detected = detector.feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn detector_detects_single_command_approval() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(b"Do you want to run this command? (y/n)\n");
    assert!(detected);
    assert!(detector.should_suppress_hud());
    assert_eq!(
        detector.last_prompt_type,
        Some(PromptType::SingleCommandApproval)
    );
}

#[test]
fn detector_detects_bash_command_approval_card() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(
        b"Bash command\nThis command requires approval\nDo you want to proceed?\n1. Yes\n",
    );
    assert!(detected);
    assert!(detector.should_suppress_hud());
    assert_eq!(
        detector.last_prompt_type,
        Some(PromptType::SingleCommandApproval)
    );
}

#[test]
fn detector_ignores_bash_command_prompt_without_choice_controls() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector
        .feed_output(b"Bash command\nThis command requires approval\nDo you want to proceed?\n");
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn detector_detects_numbered_approval_card_without_header_text() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected =
        detector.feed_output(b"1. Yes\n2. Yes, and don't ask again for this command\n3. No\n");
    assert!(detected);
    assert!(detector.should_suppress_hud());
    assert_eq!(
        detector.last_prompt_type,
        Some(PromptType::SingleCommandApproval)
    );
}

#[test]
fn detector_detects_numbered_approval_card_with_selected_chevron() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector
        .feed_output(b"\xE2\x80\xBA 1. Yes\n2. Yes, and don't ask again for this command\n");
    assert!(detected);
    assert!(detector.should_suppress_hud());
    assert_eq!(
        detector.last_prompt_type,
        Some(PromptType::SingleCommandApproval)
    );
}

#[test]
fn detector_detects_cargo_approval_card_variant() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(
            "Bash command\ncargo --version\nShow Cargo version\n\nThis command requires approval\n\nDo you want to proceed?\n› 1. Yes\n2. Yes, and don’t ask again for: cargo:*\n3. No\n"
                .as_bytes(),
        );
    assert!(detected);
    assert!(detector.should_suppress_hud());
    assert_eq!(
        detector.last_prompt_type,
        Some(PromptType::SingleCommandApproval)
    );
}

#[test]
fn detector_ignores_non_approval_numbered_lists() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(b"1. alpha\n2. beta\n3. gamma\n");
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn detector_ignores_tool_activity_lines() {
    // ToolExecution suppression was removed to prevent SIGWINCH flicker.
    // Tool-activity lines (Bash, Web Search, etc.) should NOT suppress HUD.
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(b"Bash(echo $SHELL)\n");
    assert!(!detected);
    assert!(!detector.should_suppress_hud());

    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(b"Web Search(\"safe query\")\n");
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn startup_guard_suppresses_then_expires() {
    let mut detector = ClaudePromptDetector::new(true);
    detector.activate_startup_guard();
    assert!(detector.should_suppress_hud());
    detector.suppressed_at =
        Some(Instant::now() - std::time::Duration::from_secs(STARTUP_GUARD_TIMEOUT_SECS + 1));
    assert!(!detector.should_suppress_hud());
}

#[test]
fn startup_guard_releases_early_when_prompt_is_ready() {
    let mut detector = ClaudePromptDetector::new(true);
    detector.activate_startup_guard();
    assert!(detector.should_suppress_hud());

    detector.feed_output("❯ Try \"fix typecheck errors\"\n? for shortcuts\n".as_bytes());
    assert!(!detector.should_suppress_hud());
}

#[test]
fn detector_detects_worktree_permission() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected =
        detector.feed_output(b"Do you want to allow permission to read outside the project?\n");
    assert!(detected);
    assert!(detector.should_suppress_hud());
    assert_eq!(
        detector.last_prompt_type,
        Some(PromptType::WorktreePermission)
    );
}

#[test]
fn detector_detects_multi_tool_batch() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(b"Running tools... +3 more tool uses\n");
    assert!(detected);
    assert_eq!(detector.last_prompt_type, Some(PromptType::MultiToolBatch));
}

#[test]
fn detector_ignores_low_confidence_generic_interactive_text() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(b"Would you like to proceed?\n");
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn detector_ignores_reply_composer_marker() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output("❯ ".as_bytes());
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn detector_ignores_codex_generate_command_hint() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output("⌘K to generate command".as_bytes());
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn detector_resolves_on_user_input() {
    let mut detector = ClaudePromptDetector::new(true);
    detector.feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(detector.should_suppress_hud());
    detector.on_user_input();
    assert!(!detector.should_suppress_hud());
}

#[test]
fn detector_does_not_re_suppress_from_stale_line_after_enter_resolution() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(detected);
    assert!(detector.should_suppress_hud());

    detector.on_user_input();
    assert!(!detector.should_suppress_hud());

    // Empty/no-op output should not resurrect suppression from stale line-buffer text.
    let re_detected = detector.feed_output(b"");
    assert!(!re_detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn approval_prompt_resolves_only_on_confirmation_or_cancel_keys() {
    let mut detector = ClaudePromptDetector::new(true);
    detector.feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(detector.should_suppress_hud());
    assert!(!detector.should_resolve_on_input(b" "));
    assert!(!detector.should_resolve_on_input(b"a"));
    assert!(!detector.should_resolve_on_input(b"d"));
    assert!(!detector.should_resolve_on_input(b"q"));
    assert!(!detector.should_resolve_on_input(b"hello"));
    assert!(detector.should_resolve_on_input(b"y"));
    assert!(detector.should_resolve_on_input(b"\x03"));
}

#[test]
fn reply_composer_prompt_resolves_on_submit_or_cancel_only() {
    let mut detector = ClaudePromptDetector::new_with_policy(true, true);
    let detected = detector.feed_output("Type your message".as_bytes());
    assert!(detected);
    assert!(detector.should_suppress_hud());
    assert!(!detector.should_resolve_on_input(b"x"));
    assert!(detector.should_resolve_on_input(b"\r"));
    assert!(detector.should_resolve_on_input(b"\x1b"));
}

#[test]
fn claude_backend_ignores_reply_composer_marker() {
    let mut detector = ClaudePromptDetector::new_for_backend("claude");
    let detected = detector.feed_output("❯ ".as_bytes());
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn claude_backend_ignores_codex_generate_command_hint() {
    let mut detector = ClaudePromptDetector::new_for_backend("claude");
    let detected = detector.feed_output("⌘K to generate command".as_bytes());
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn codex_backend_ignores_reply_composer_marker() {
    let mut detector = ClaudePromptDetector::new_for_backend("codex");
    let detected = detector.feed_output("❯ ".as_bytes());
    assert!(!detected);
    assert!(!detector.should_suppress_hud());
}

#[test]
fn detector_does_not_re_suppress_same_prompt() {
    let mut detector = ClaudePromptDetector::new(true);
    let first = detector.feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(first);
    let second = detector.feed_output(b"still waiting...\n");
    assert!(!second);
    assert!(detector.should_suppress_hud());
}

#[test]
fn detector_refreshes_suppression_deadline_when_prompt_reappears() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(detected);
    detector.suppressed_at =
        Some(Instant::now() - std::time::Duration::from_secs(PROMPT_SUPPRESSION_TIMEOUT_SECS + 1));
    assert!(!detector.should_suppress_hud());
    let re_detected = detector.feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(
        re_detected,
        "expired suppression should re-enter on a fresh matching prompt"
    );
    assert!(detector.should_suppress_hud());
    assert_eq!(
        detector.last_prompt_type,
        Some(PromptType::SingleCommandApproval)
    );
}

#[test]
fn detector_captures_diagnostic() {
    let mut detector = ClaudePromptDetector::new(true);
    detector.feed_output(b"Do you want to allow access files outside the project?\n");
    let diag = detector.capture_diagnostic(40, 120, "Full", "banner");
    assert!(diag.is_some());
    let diag = diag.unwrap();
    assert_eq!(diag.terminal_rows, 40);
    assert_eq!(diag.terminal_cols, 120);
    assert_eq!(diag.hud_style, "Full");
    assert_eq!(diag.hud_mode, "banner");
    assert_eq!(diag.prompt_type, PromptType::WorktreePermission);
    assert!(!diag.has_worktree_paths);
    assert!(diag.command_wrap_depth >= 1);
    assert!(!diag.has_tool_batch_summary);
    assert_eq!(
        detector
            .last_diagnostic()
            .map(|snapshot| snapshot.prompt_type),
        Some(PromptType::WorktreePermission)
    );
}

#[test]
fn estimate_command_wrap_depth_basic() {
    let context = "short\nmedium length line here";
    assert!(estimate_command_wrap_depth(context, 80) >= 2);
}

#[test]
fn estimate_command_wrap_depth_long_line() {
    let long_line = "a".repeat(200);
    assert_eq!(estimate_command_wrap_depth(&long_line, 80), 3);
}

#[test]
fn estimate_command_wrap_depth_zero_cols() {
    assert_eq!(estimate_command_wrap_depth("any text", 0), 0);
}

#[test]
fn detector_handles_cr_line_split() {
    let mut detector = ClaudePromptDetector::new(true);
    let detected = detector.feed_output(b"Do you want to proceed?\r(y/n)\n");
    assert!(detected);
}

#[test]
fn detect_prompt_type_prioritizes_worktree_over_generic() {
    let prompt_type = detect_prompt_type(
        "do you want to allow permission to read outside the project?",
        "",
        false,
    );
    assert_eq!(prompt_type, Some(PromptType::WorktreePermission));
}

#[test]
fn detect_prompt_type_prioritizes_single_command_over_tool_activity() {
    let prompt_type = detect_prompt_type(
            "do you want to proceed? (y/n)",
            "web search(\"rust\")\nclaude wants to search the web for: rust\ndo you want to proceed? (y/n)",
            false,
        );
    assert_eq!(prompt_type, Some(PromptType::SingleCommandApproval));
}

#[test]
fn detect_prompt_type_ignores_plain_proceed_phrase_without_choices() {
    let prompt_type = detect_prompt_type("do you want to proceed?", "", false);
    assert_eq!(prompt_type, None);
}

#[test]
fn detect_prompt_type_ignores_inline_quoted_confirmation_phrase() {
    let prompt_type = detect_prompt_type(
        "recap: we previously saw \"do you want to proceed? (y/n)\" in logs",
        "recap: we previously saw \"do you want to proceed? (y/n)\" in logs",
        false,
    );
    assert_eq!(prompt_type, None);
}

#[test]
fn shared_approval_parser_accepts_colon_and_space_numbering() {
    let context = "› 1: Yes\n2 Yes, and don't ask again for: cargo:*\nNo\n";
    assert!(looks_like_numbered_approval_card_with_scan(context, 64));
}

#[test]
fn shared_approval_parser_accepts_compact_dot_numbering() {
    let context = "❯1.Yes\n2.No\n";
    assert!(looks_like_numbered_approval_card_with_scan(context, 64));
}

#[test]
fn shared_line_normalizer_trims_cursor_markers_and_o_prefix() {
    assert_eq!(normalize_approval_card_line("  ▸ o 2: Yes"), "2: yes");
    assert_eq!(
        normalize_approval_card_line("  › Do you want to proceed?"),
        "do you want to proceed?"
    );
}

#[test]
fn shared_confirmation_line_parser_matches_prefixed_prompt_lines() {
    assert!(context_contains_confirmation_prompt_line(
        "› Do you want to proceed?\n1. Yes\n"
    ));
}

#[test]
fn detector_enabled_flag() {
    let detector = ClaudePromptDetector::new(true);
    assert!(detector.is_enabled());
    let detector = ClaudePromptDetector::new(false);
    assert!(!detector.is_enabled());
}

#[test]
fn backend_supports_prompt_guard_for_claude_only() {
    assert!(backend_supports_prompt_occlusion_guard("claude"));
    assert!(!backend_supports_prompt_occlusion_guard("codex"));
    assert!(backend_supports_prompt_occlusion_guard("Claude Code"));
    assert!(!backend_supports_prompt_occlusion_guard("gemini"));
}
