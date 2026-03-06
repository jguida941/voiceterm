use super::*;

fn chunk_contains_explicit_approval_hint(bytes: &[u8]) -> bool {
    prompt_occlusion_signals::chunk_contains_explicit_approval_hint(bytes)
}

fn chunk_contains_prompt_context_hint(bytes: &[u8]) -> bool {
    prompt_occlusion_signals::chunk_contains_prompt_context_markers(bytes)
}

fn chunk_contains_numbered_approval_hint(bytes: &[u8]) -> bool {
    prompt_occlusion_signals::chunk_contains_numbered_approval_hint(
        bytes,
        NON_ROLLING_APPROVAL_CARD_SCAN_LINES,
    )
}

fn chunk_contains_live_approval_card_hint(bytes: &[u8]) -> bool {
    prompt_occlusion_signals::chunk_contains_live_approval_card_hint(
        bytes,
        NON_ROLLING_APPROVAL_CARD_SCAN_LINES,
    )
}

fn chunk_contains_substantial_non_prompt_activity(bytes: &[u8]) -> bool {
    prompt_occlusion_signals::chunk_contains_substantial_non_prompt_activity(
        bytes,
        NON_ROLLING_APPROVAL_CARD_SCAN_LINES,
    )
}

fn chunk_contains_tool_activity_hint(bytes: &[u8]) -> bool {
    prompt_occlusion_signals::chunk_contains_tool_activity_hint(bytes)
}

fn chunk_contains_synchronized_prompt_activity(bytes: &[u8]) -> bool {
    prompt_occlusion_signals::chunk_contains_synchronized_prompt_activity(bytes)
}

fn chunk_is_probable_prompt_input_echo_rewrite(bytes: &[u8]) -> bool {
    prompt_occlusion_signals::chunk_is_probable_prompt_input_echo_rewrite(bytes)
}

#[test]
fn explicit_approval_hint_detects_cargo_prompt_variant() {
    let bytes = "Bash command\ncargo --version\nShow Cargo version\n\nThis command requires approval\n\nDo you want to proceed?\n› 1. Yes\n2. Yes, and don’t ask again for: cargo:*\n3. No\n"
            .as_bytes();
    assert!(chunk_contains_explicit_approval_hint(bytes));
}

#[test]
fn explicit_approval_hint_detects_compact_spacing_variant() {
    let bytes = b"Doyouwanttoproceed?\n1.Yes\n2.Yes,anddon'taskagainfor:WebSearch:*\n";
    assert!(chunk_contains_explicit_approval_hint(bytes));
}

#[test]
fn explicit_approval_hint_ignores_unrelated_output() {
    assert!(!chunk_contains_explicit_approval_hint(
        b"Web Search(\"rust async await\")\nDid 1 search in 8s\n"
    ));
}

#[test]
fn explicit_approval_hint_ignores_embedded_recap_phrase() {
    assert!(!chunk_contains_explicit_approval_hint(
        b"Recap: earlier output included \"Do you want to proceed?\" before approval.\n"
    ));
}

#[test]
fn explicit_approval_hint_detects_prompt_question_line_start() {
    assert!(chunk_contains_explicit_approval_hint(
        b"  Do you want to proceed?\n"
    ));
}

#[test]
fn explicit_approval_hint_detects_ansi_styled_prompt_question() {
    assert!(chunk_contains_explicit_approval_hint(
        b"\x1b[37mDo you want to proceed?\x1b[39m\n"
    ));
}

#[test]
fn claude_prompt_context_detects_tool_use_card() {
    assert!(chunk_contains_prompt_context_hint(
        b"Tool use\nClaude wants to search the web for rust terminal ui\n"
    ));
}

#[test]
fn numbered_approval_hint_detects_sparse_card() {
    assert!(chunk_contains_numbered_approval_hint(
        b"1. Yes\n2. Yes, and don't ask again for this command\n3. No\n"
    ));
}

#[test]
fn numbered_approval_hint_detects_selected_chevron_card() {
    assert!(chunk_contains_numbered_approval_hint(
        b"\xE2\x80\xBA 1. Yes\n2. Yes, and don't ask again for this command\n"
    ));
}

#[test]
fn numbered_approval_hint_detects_two_option_yes_no_card() {
    assert!(chunk_contains_numbered_approval_hint(b"1. Yes\n2. No\n"));
}

#[test]
fn numbered_approval_hint_detects_selected_o_prefix_variant() {
    assert!(chunk_contains_numbered_approval_hint(b"o 1. Yes\n2. No\n"));
}

#[test]
fn numbered_approval_hint_detects_compact_prefix_variant() {
    assert!(chunk_contains_numbered_approval_hint(
        b"\xE2\x9D\xAF1.Yes\n2.No\n"
    ));
}

#[test]
fn numbered_approval_hint_detects_space_separator_variant() {
    assert!(chunk_contains_numbered_approval_hint(b"1 Yes\n2 No\n"));
}

#[test]
fn numbered_approval_hint_detects_wrapped_long_option_cards() {
    let mut card =
        String::from("This command requires approval\nDo you want to proceed?\n1. Yes\n");
    for _ in 0..40 {
        card.push_str("/Users/jguida941/testing_upgrade/codex-voice/rust\n");
    }
    card.push_str("2. Yes, and don't ask again for Web Search commands in this directory\n");
    card.push_str("3. No\n");
    assert!(chunk_contains_numbered_approval_hint(card.as_bytes()));
}

#[test]
fn numbered_approval_hint_ignores_plain_numbered_list() {
    assert!(!chunk_contains_numbered_approval_hint(
        b"1. alpha\n2. beta\n3. gamma\n"
    ));
}

#[test]
fn live_approval_card_hint_requires_explicit_and_numbered_signals() {
    assert!(chunk_contains_live_approval_card_hint(
        b"This command requires approval\nDo you want to proceed?\n1. Yes\n2. No\n"
    ));
    assert!(!chunk_contains_live_approval_card_hint(
        b"Recap: Do you want to proceed with this plan later?\n"
    ));
    assert!(!chunk_contains_live_approval_card_hint(
        b"1. alpha\n2. beta\n3. gamma\n"
    ));
}

#[test]
fn substantial_non_prompt_activity_ignores_choice_echo() {
    assert!(!chunk_contains_substantial_non_prompt_activity(b"1\n"));
    assert!(!chunk_contains_substantial_non_prompt_activity(b"yes\n"));
    assert!(!chunk_contains_substantial_non_prompt_activity(
        b"\x1b[2K\r\n"
    ));
}

#[test]
fn substantial_non_prompt_activity_detects_post_approval_output() {
    assert!(chunk_contains_substantial_non_prompt_activity(
        b"Approval accepted. Continuing execution...\n"
    ));
}

#[test]
fn approval_hint_detects_split_card_when_chunks_are_merged() {
    let chunk_a = b"This command requires approval\nDo you want to proceed?\n";
    let chunk_b = b"1. Yes\n2. Yes, and don't ask again for this command\n";
    assert!(chunk_contains_explicit_approval_hint(chunk_a));
    assert!(!chunk_contains_numbered_approval_hint(chunk_a));
    assert!(chunk_contains_numbered_approval_hint(chunk_b));
    let mut merged = Vec::new();
    merged.extend_from_slice(chunk_a);
    merged.extend_from_slice(chunk_b);
    assert!(chunk_contains_explicit_approval_hint(&merged));
    assert!(chunk_contains_numbered_approval_hint(&merged));
}

#[test]
fn tool_activity_hint_detects_bash_tool_line() {
    assert!(chunk_contains_tool_activity_hint(
        b"Bash(echo $SHELL)\nDid 1 run in 0.1s\n"
    ));
}

#[test]
fn tool_activity_hint_detects_web_search_line() {
    assert!(chunk_contains_tool_activity_hint(
        b"Web Search(\"rust async await\")\nDid 1 search in 8s\n"
    ));
}

#[test]
fn tool_activity_hint_ignores_plain_bash_commands_heading() {
    assert!(!chunk_contains_tool_activity_hint(
        b"Bash Commands:\n1. Echo -- printed hello\n"
    ));
}

#[test]
fn tool_activity_hint_ignores_plain_web_searches_heading() {
    assert!(!chunk_contains_tool_activity_hint(
        b"Web Searches:\n1. Rust TUI rendering -- Ratatui dominates\n"
    ));
}

#[test]
fn tool_activity_hint_ignores_unrelated_output() {
    assert!(!chunk_contains_tool_activity_hint(
        b"transcript ready\nall checks passed\n"
    ));
}

#[test]
fn synchronized_cursor_activity_detects_thinking_packets() {
    let packet = b"\x1b[?2026h\r\x1b[14C\x1b[6A\x1b[38;5;246m(thinking)\x1b[39m\r\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l";
    assert!(chunk_contains_synchronized_prompt_activity(packet));
}

#[test]
fn synchronized_cursor_activity_detects_long_think_status_packets() {
    let packet = b"\x1b[?2026h\r\x1b[6A\x1b[37m* Crunched for 47s\x1b[39m\r\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l";
    assert!(chunk_contains_synchronized_prompt_activity(packet));
}

#[test]
fn synchronized_cursor_activity_detects_spinner_only_packets() {
    let packet = b"\x1b[?2026h\r\x1b[26A*\r\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l";
    assert!(chunk_contains_synchronized_prompt_activity(packet));
}

#[test]
fn synchronized_cursor_activity_detects_shortcut_marker_packets() {
    let packet =
            b"\x1b[?2026h\r\x1b[2A\x1b[7m \x1b[27m \r\r\n\r\n\x1b[2C\x1b[37m? for shortcuts\x1b[39m\r\r\n\x1b[?2026l";
    assert!(chunk_contains_synchronized_prompt_activity(packet));
}

#[test]
fn synchronized_cursor_activity_detects_early_prompt_rewrite_packets() {
    let packet = b"\x1b[?2026h\x1b[2K\x1b[G\x1b[1A\r\x1b[2C\x1b[2A\xb4\x1b[7m \r\x1b[2B\x1b[27m                                              \x1b[?2026l";
    assert!(chunk_contains_synchronized_prompt_activity(packet));
}

#[test]
fn synchronized_cursor_activity_detects_three_row_status_hop_packets() {
    let packet = b"\x1b[?2026h\r\x1b[3A\x1b[91m* Swooping...\x1b[39m\r\r\n\r\n\r\n\x1b[?2026l";
    assert!(chunk_contains_synchronized_prompt_activity(packet));
}

#[test]
fn synchronized_cursor_activity_identifies_prompt_input_echo_rewrites() {
    let packet = b"\x1b[?2026h\x1b[2K\x1b[G\x1b[1A\r\x1b[2C\x1b[2Ab\x1b[7m \r\x1b[2B\x1b[27m                                              \x1b[?2026l";
    assert!(chunk_is_probable_prompt_input_echo_rewrite(packet));
}

#[test]
fn synchronized_cursor_activity_identifies_three_row_input_echo_rewrites() {
    let packet = b"\x1b[?2026h\r\x1b[2C\x1b[3Ad\x1b[7m \x1b[27m\r\r\n\r\n\r\n\x1b[?2026l";
    assert!(chunk_is_probable_prompt_input_echo_rewrite(packet));
}

#[test]
fn synchronized_cursor_activity_input_echo_guard_ignores_long_think_packets() {
    let packet = b"\x1b[?2026h\r\x1b[6A\x1b[37m* Crunched for 47s\x1b[39m\r\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l";
    assert!(!chunk_is_probable_prompt_input_echo_rewrite(packet));
}

#[test]
fn synchronized_cursor_activity_ignores_non_rewrite_packets() {
    assert!(!chunk_contains_synchronized_prompt_activity(
        b"\x1b[?2026hplain text only\x1b[?2026l"
    ));
    assert!(!chunk_contains_synchronized_prompt_activity(
        b"\x1b[?2026h\r\x1b[2A(thinking)\x1b[?2026l"
    ));
    assert!(!chunk_contains_synchronized_prompt_activity(
        b"\x1b[?2026hfor shortcuts only\x1b[?2026l"
    ));
}
