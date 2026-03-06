use crate::prompt::occlusion_shared::normalize_signal_text;

pub(crate) fn context_contains_yes_no_confirmation_controls(context: &str) -> bool {
    context.contains("(y/n)")
        || context.contains("[y/n]")
        || context.contains("(yes/no)")
        || context.contains("[yes/no]")
        || context.contains("press y to confirm")
        || context.contains("press enter to continue")
}

pub(crate) fn line_has_confirmation_prompt_prefix(line: &str) -> bool {
    line.starts_with("do you want to proceed")
        || line.starts_with("do you want to run")
        || line.starts_with("would you like to proceed")
        || line.starts_with("this command requires approval")
        || line.starts_with("requires approval")
        || line.starts_with("allow this command")
        || line.starts_with("approve this action")
        || line.starts_with("run this command?")
        || line.starts_with("execute this?")
        || line.starts_with("press enter to continue")
        || line.starts_with("press y to confirm")
}

pub(crate) fn context_contains_confirmation_prompt_line(context: &str) -> bool {
    context
        .lines()
        .map(normalize_approval_card_line)
        .any(|line| line_has_confirmation_prompt_prefix(&line))
}

pub(crate) fn context_contains_provider_prompt_markers(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let normalized = normalize_signal_text(bytes);
    normalized.contains("claude wants to")
        || normalized.contains("what should claude do instead")
        || normalized.contains("tool use")
        || normalized.contains("claude code")
}

pub(crate) fn looks_like_numbered_approval_card_with_scan(
    context: &str,
    scan_lines: usize,
) -> bool {
    let mut has_option_1 = false;
    let mut has_option_2 = false;
    let mut has_option_3 = false;
    let mut has_yes = false;
    let mut has_no = false;
    let mut has_approval_text = false;
    let mut has_dont_ask_again = false;

    for line in context.lines().rev().take(scan_lines) {
        let lowered = normalize_approval_card_line(line);
        let numbered_payload = numbered_option_payload(&lowered);
        if starts_with_numbered_option(&lowered, b'1') {
            has_option_1 = true;
        }
        if starts_with_numbered_option(&lowered, b'2') {
            has_option_2 = true;
        }
        if starts_with_numbered_option(&lowered, b'3') {
            has_option_3 = true;
        }
        if numbered_payload.is_some_and(|payload| payload.starts_with("yes"))
            || lowered.contains(" yes")
            || lowered.starts_with("yes")
        {
            has_yes = true;
        }
        if numbered_payload.is_some_and(|payload| payload.starts_with("no"))
            || lowered.contains(" no")
            || lowered.starts_with("no")
        {
            has_no = true;
        }
        if lowered.contains("don't ask again") || lowered.contains("dont ask again") {
            has_dont_ask_again = true;
        }
        if lowered.contains("do you want")
            || lowered.contains("requires approval")
            || lowered.contains("allow this command")
            || lowered.contains("approve this action")
        {
            has_approval_text = true;
        }
    }

    let has_numbered_options = has_option_1
        && has_option_2
        && (has_option_3 || has_no || has_approval_text || has_dont_ask_again);
    let has_approval_semantics = (has_yes && has_no) || has_approval_text || has_dont_ask_again;
    has_numbered_options && has_approval_semantics
}

pub(crate) fn normalize_approval_card_line(line: &str) -> String {
    let trimmed = line.trim_start();
    let trimmed = trimmed
        .trim_start_matches(|ch: char| {
            matches!(
                ch,
                '•' | '*'
                    | '-'
                    | '└'
                    | '│'
                    | '⏺'
                    | '›'
                    | '❯'
                    | '>'
                    | '→'
                    | '·'
                    | '▸'
                    | '▶'
                    | '◂'
            )
        })
        .trim_start();
    let trimmed = if let Some(rest) = trimmed.strip_prefix("o ") {
        rest
    } else if let Some(rest) = trimmed.strip_prefix('o') {
        if rest
            .chars()
            .next()
            .is_some_and(|ch| ch.is_ascii_digit() || matches!(ch, '.' | ')' | ':' | ' '))
        {
            rest
        } else {
            trimmed
        }
    } else {
        trimmed
    };
    trimmed.to_ascii_lowercase()
}

pub(crate) fn starts_with_numbered_option(line: &str, option: u8) -> bool {
    if line.len() < 2 {
        return false;
    }
    let first = option as char;
    let bytes = line.as_bytes();
    bytes[0] == first as u8 && matches!(bytes[1], b'.' | b')' | b':' | b' ')
}

fn numbered_option_payload(line: &str) -> Option<&str> {
    if line.len() < 2 {
        return None;
    }
    let bytes = line.as_bytes();
    if !bytes[0].is_ascii_digit() || !matches!(bytes[1], b'.' | b')' | b':' | b' ') {
        return None;
    }
    Some(line[2..].trim_start())
}
