use crate::ansi::strip_ansi_preserve_controls;
use crate::prompt::claude_prompt_detect::{
    context_contains_confirmation_prompt_line, context_contains_provider_prompt_markers,
    line_has_confirmation_prompt_prefix, looks_like_numbered_approval_card_with_scan,
    normalize_approval_card_line,
};
use crate::prompt::occlusion_shared::{
    bytes_contains_cursor_up_csi_at_least, bytes_contains_sequence, normalize_signal_text,
};

const LONG_THINK_STATUS_MARKERS: &[&str] = &[
    "baked for ",
    "brewed for ",
    "churned for ",
    "cogitated for ",
    "cooked for ",
    "crunched for ",
    "worked for ",
];

pub(crate) fn chunk_contains_explicit_approval_hint(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let stripped = strip_ansi_preserve_controls(bytes);
    if stripped.is_empty() {
        return false;
    }
    let raw_lower = String::from_utf8_lossy(&stripped).to_ascii_lowercase();
    if raw_lower.contains("this command requires approval")
        || raw_lower.contains("thiscommandrequiresapproval")
    {
        return true;
    }
    let line_starts_with_prompt_question = raw_lower
        .lines()
        .map(normalize_approval_card_line)
        .any(|line| line_has_confirmation_prompt_prefix(&line));
    if line_starts_with_prompt_question {
        return true;
    }
    let normalized = normalize_signal_text(&stripped);
    let compact: String = normalized
        .chars()
        .filter(|ch| !ch.is_ascii_whitespace())
        .collect();
    normalized.contains("this command requires approval")
        || compact.contains("thiscommandrequiresapproval")
        || normalized.starts_with("do you want to proceed")
        || compact.starts_with("doyouwanttoproceed")
        || ((normalized.contains("yes and don t ask again for")
            || compact.contains("yesanddontaskagainfor"))
            && normalized.contains("1")
            && normalized.contains("2"))
}

pub(crate) fn chunk_contains_prompt_context_markers(bytes: &[u8]) -> bool {
    context_contains_provider_prompt_markers(bytes)
}

pub(crate) fn chunk_contains_confirmation_prompt_line(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let stripped = strip_ansi_preserve_controls(bytes);
    if stripped.is_empty() {
        return false;
    }
    let context = String::from_utf8_lossy(&stripped);
    context_contains_confirmation_prompt_line(context.as_ref())
}

pub(crate) fn chunk_contains_numbered_approval_hint(bytes: &[u8], scan_lines: usize) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let text = String::from_utf8_lossy(bytes);
    looks_like_numbered_approval_card_with_scan(text.as_ref(), scan_lines)
}

pub(crate) fn chunk_contains_live_approval_card_hint(bytes: &[u8], scan_lines: usize) -> bool {
    chunk_contains_explicit_approval_hint(bytes)
        && chunk_contains_numbered_approval_hint(bytes, scan_lines)
}

pub(crate) fn chunk_contains_yes_no_approval_hint(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let stripped = strip_ansi_preserve_controls(bytes);
    if stripped.is_empty() {
        return false;
    }
    let lowered = String::from_utf8_lossy(&stripped).to_ascii_lowercase();
    let has_approval_question = chunk_contains_confirmation_prompt_line(&stripped);
    let has_yes_no_choice = lowered.contains("(y/n)")
        || lowered.contains("(yes/no)")
        || lowered.contains(" y/n")
        || lowered.lines().any(|line| {
            let normalized = normalize_approval_card_line(line);
            normalized.starts_with("y/n")
                || normalized.starts_with("yes/no")
                || normalized.starts_with("y or n")
        });
    has_approval_question && has_yes_no_choice
}

pub(crate) fn rolling_high_confidence_approval_hint(
    explicit_approval_hint_chunk: bool,
    numbered_approval_hint_chunk: bool,
    yes_no_approval_hint_chunk: bool,
    confirmation_prompt_line_chunk: bool,
) -> bool {
    numbered_approval_hint_chunk
        || (explicit_approval_hint_chunk
            && yes_no_approval_hint_chunk
            && confirmation_prompt_line_chunk)
}

pub(crate) fn chunk_contains_substantial_non_prompt_activity(
    bytes: &[u8],
    scan_lines: usize,
) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let stripped = strip_ansi_preserve_controls(bytes);
    if stripped.is_empty() {
        return false;
    }
    let text = String::from_utf8_lossy(&stripped);
    let trimmed = text.trim();
    if trimmed.is_empty() {
        return false;
    }
    let compact: String = trimmed
        .chars()
        .filter(|ch| !ch.is_ascii_whitespace())
        .collect();
    if compact.is_empty() {
        return false;
    }
    let compact_lower = compact.to_ascii_lowercase();
    if matches!(
        compact_lower.as_str(),
        "1" | "2" | "3" | "y" | "n" | "yes" | "no" | "enter"
    ) {
        return false;
    }
    if compact_lower.len() < 8 {
        return false;
    }
    if chunk_contains_explicit_approval_hint(&stripped)
        || chunk_contains_numbered_approval_hint(&stripped, scan_lines)
        || chunk_contains_prompt_context_markers(&stripped)
    {
        return false;
    }
    true
}

fn normalize_tool_activity_line(line: &str) -> String {
    line.trim_start()
        .trim_start_matches(|ch: char| {
            matches!(
                ch,
                '•' | '*' | '-' | '└' | '│' | '⏺' | '›' | '❯' | '>' | '→' | '·'
            )
        })
        .trim_start()
        .to_ascii_lowercase()
}

pub(crate) fn chunk_contains_synchronized_prompt_activity(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let synchronized_packet = bytes_contains_sequence(bytes, b"\x1b[?2026h")
        && bytes_contains_sequence(bytes, b"\x1b[?2026l");
    if !synchronized_packet {
        return false;
    }
    let has_rewrite_structure = bytes_contains_sequence(bytes, b"\r\r\n")
        || bytes_contains_sequence(bytes, b"\x1b[2K")
        || bytes_contains_sequence(bytes, b"\x1b[7m")
        || bytes_contains_sequence(bytes, b"\x1b[G");
    let has_large_cursor_up = bytes_contains_cursor_up_csi_at_least(bytes, 4);
    let has_medium_cursor_up = bytes_contains_cursor_up_csi_at_least(bytes, 2);
    let has_any_cursor_up = bytes_contains_cursor_up_csi_at_least(bytes, 1);
    let stripped = strip_ansi_preserve_controls(bytes);
    let lowered = String::from_utf8_lossy(&stripped).to_ascii_lowercase();
    let has_status_marker = lowered.contains("(thinking)")
        || lowered.contains("for shortcuts")
        || LONG_THINK_STATUS_MARKERS
            .iter()
            .any(|marker| lowered.contains(marker));
    has_large_cursor_up
        || (has_medium_cursor_up && has_rewrite_structure)
        || (has_any_cursor_up && has_status_marker && has_rewrite_structure)
}

pub(crate) fn chunk_is_probable_prompt_input_echo_rewrite(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let synchronized_packet = bytes_contains_sequence(bytes, b"\x1b[?2026h")
        && bytes_contains_sequence(bytes, b"\x1b[?2026l");
    if !synchronized_packet {
        return false;
    }
    let has_inverse_video_caret =
        bytes_contains_sequence(bytes, b"\x1b[7m") && bytes_contains_sequence(bytes, b"\x1b[27m");
    if !has_inverse_video_caret {
        return false;
    }
    let has_medium_cursor_up = bytes_contains_cursor_up_csi_at_least(bytes, 2);
    let has_large_cursor_up = bytes_contains_cursor_up_csi_at_least(bytes, 4);
    if !has_medium_cursor_up || has_large_cursor_up {
        return false;
    }
    let stripped = strip_ansi_preserve_controls(bytes);
    let lowered = String::from_utf8_lossy(&stripped).to_ascii_lowercase();
    let has_long_think_marker = lowered.contains("(thinking)")
        || LONG_THINK_STATUS_MARKERS
            .iter()
            .any(|marker| lowered.contains(marker));
    if has_long_think_marker {
        return false;
    }
    bytes.len() <= 256
}

pub(crate) fn chunk_contains_tool_activity_hint(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let text = String::from_utf8_lossy(bytes);
    for line in text.lines().rev().take(12) {
        let lowered = normalize_tool_activity_line(line);
        if lowered.starts_with("bash(")
            || lowered == "bash command"
            || lowered.starts_with("web search(")
            || lowered.starts_with("google search(")
            || lowered.contains("running tools")
            || lowered.contains("+1 more tool use")
            || lowered.contains("+2 more tool use")
            || lowered.contains("+3 more tool use")
            || lowered.contains("+4 more tool use")
            || lowered.contains("+5 more tool use")
            || lowered.contains("+1 more tool call")
            || lowered.contains("+2 more tool call")
            || lowered.contains("+3 more tool call")
            || lowered.contains("+4 more tool call")
            || lowered.contains("+5 more tool call")
        {
            return true;
        }
    }
    false
}

pub(crate) fn should_resolve_prompt_suppression_on_input_without_detector(bytes: &[u8]) -> bool {
    matches!(
        bytes,
        [b'\r']
            | [b'\n']
            | [b'y']
            | [b'Y']
            | [b'n']
            | [b'N']
            | [b'1']
            | [b'2']
            | [b'3']
            | [0x03]
            | [0x04]
            | [0x1b]
    )
}
