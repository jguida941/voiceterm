use super::*;

mod ascii;
mod basic;
mod full_banner;
mod layout_and_messages;
mod panels_and_snapshots;

fn expected_recording_indicator(mode: VoiceMode, colors: &ThemeColors) -> &'static str {
    let base = match mode {
        VoiceMode::Auto => colors.indicator_auto,
        VoiceMode::Manual => colors.indicator_manual,
        VoiceMode::Idle => colors.indicator_idle,
    };
    crate::theme::filled_indicator(base)
}

fn has_pulse_color_prefix(rendered: &str, indicator: &str, colors: &ThemeColors) -> bool {
    colors.recording.is_empty()
        || rendered.contains(&format!("{}{}", colors.recording, indicator))
        || rendered.contains(&format!("{}{}", colors.dim, indicator))
}

fn separator_columns(row: &str) -> Vec<usize> {
    let mut cols = Vec::new();
    let mut display_col = 0usize;
    let mut chars = row.chars();

    while let Some(ch) = chars.next() {
        if ch == '\u{1b}' {
            // Skip ANSI escape sequences.
            for next in chars.by_ref() {
                if ('@'..='~').contains(&next) {
                    break;
                }
            }
            continue;
        }

        display_col += 1;
        if ch == '│' {
            cols.push(display_col);
        }
    }

    cols
}

fn strip_ansi(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    let mut in_escape = false;
    for ch in input.chars() {
        if ch == '\x1b' {
            in_escape = true;
            continue;
        }
        if in_escape {
            if ch == 'm' {
                in_escape = false;
            }
            continue;
        }
        out.push(ch);
    }
    out
}

fn fnv1a64(input: &str) -> u64 {
    let mut hash: u64 = 0xcbf29ce484222325;
    for byte in input.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

fn internal_separator_columns(row: &str) -> Vec<usize> {
    let mut cols = separator_columns(row);
    if cols.len() >= 2 {
        cols.remove(0);
        cols.pop();
    }
    cols
}

fn button_start_col(banner: &StatusBanner, action: crate::buttons::ButtonAction) -> usize {
    usize::from(
        banner
            .buttons
            .iter()
            .find(|button| button.row == 2 && button.action == action)
            .expect("button position should exist on shortcuts row")
            .start_x,
    )
}
