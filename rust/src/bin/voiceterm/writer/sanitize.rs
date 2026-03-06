//! Status-string sanitization so control characters never corrupt terminal output.

use unicode_width::UnicodeWidthChar;

pub(super) fn sanitize_status(text: &str) -> String {
    text.chars()
        .map(|ch| if ch.is_control() { ' ' } else { ch })
        .collect()
}

pub(super) fn status_text_display_width(text: &str) -> usize {
    text.chars()
        .map(|ch| UnicodeWidthChar::width(ch).unwrap_or(0))
        .sum()
}

pub(super) fn truncate_status(text: &str, max_display_width: usize) -> String {
    if max_display_width == 0 {
        return String::new();
    }
    let mut result = String::new();
    let mut width = 0usize;

    for ch in text.chars() {
        let ch_width = UnicodeWidthChar::width(ch).unwrap_or(0);
        if width.saturating_add(ch_width) > max_display_width {
            break;
        }
        result.push(ch);
        width = width.saturating_add(ch_width);
    }

    result
}

/// Truncate a line that may contain ANSI escape sequences to fit within
/// `max_display_width` visible columns.  Escape sequences are passed through
/// without counting toward the width budget.  A reset sequence is appended
/// when the line is actually truncated so colours do not bleed into the
/// trailing erase-to-end-of-line sequence.
pub(super) fn truncate_ansi_line(line: &str, max_display_width: usize) -> String {
    if max_display_width == 0 {
        return String::new();
    }

    let mut result = String::with_capacity(line.len());
    let mut width: usize = 0;
    let bytes = line.as_bytes();
    let mut byte_idx = 0usize;
    let mut truncated = false;
    let mut osc8_link_open = false;

    while byte_idx < bytes.len() {
        let ch = line[byte_idx..].chars().next().unwrap_or('\0');
        // Pass through ANSI escape sequences without counting width.
        if ch == '\x1b' {
            let esc_start = byte_idx;
            byte_idx = byte_idx.saturating_add(1);
            if byte_idx >= bytes.len() {
                result.push('\x1b');
                break;
            }
            match bytes[byte_idx] {
                b'[' => {
                    // CSI sequence: consume until final byte in '@'..='~'.
                    byte_idx = byte_idx.saturating_add(1);
                    while byte_idx < bytes.len() {
                        let byte = bytes[byte_idx];
                        byte_idx = byte_idx.saturating_add(1);
                        if (b'@'..=b'~').contains(&byte) {
                            break;
                        }
                    }
                }
                b']' => {
                    // OSC sequence: consume until BEL or ST (ESC \).
                    byte_idx = byte_idx.saturating_add(1);
                    while byte_idx < bytes.len() {
                        let byte = bytes[byte_idx];
                        if byte == 0x07 {
                            byte_idx = byte_idx.saturating_add(1);
                            break;
                        }
                        if byte == 0x1b
                            && byte_idx + 1 < bytes.len()
                            && bytes[byte_idx + 1] == b'\\'
                        {
                            byte_idx = byte_idx.saturating_add(2);
                            break;
                        }
                        byte_idx = byte_idx.saturating_add(1);
                    }
                }
                _ => {
                    // Single-char non-CSI/non-OSC escape (e.g. ESC 7 / ESC 8).
                    byte_idx = byte_idx.saturating_add(1);
                }
            }
            let sequence = &bytes[esc_start..byte_idx.min(bytes.len())];
            if let Some(link_open) = parse_osc8_state(sequence) {
                osc8_link_open = link_open;
            }
            if let Ok(sequence_text) = std::str::from_utf8(sequence) {
                result.push_str(sequence_text);
            }
            continue;
        }

        let ch_width = UnicodeWidthChar::width(ch).unwrap_or(0);
        if width.saturating_add(ch_width) > max_display_width {
            truncated = true;
            break;
        }
        result.push(ch);
        width = width.saturating_add(ch_width);
        byte_idx = byte_idx.saturating_add(ch.len_utf8());
    }

    if truncated {
        if osc8_link_open {
            // Ensure OSC8 hyperlinks close even when truncation cuts a link label.
            result.push_str("\x1b]8;;\x1b\\");
        }
        // Reset attributes so the erase-to-end-of-line that follows does
        // not inherit colours from the truncated content.
        result.push_str("\x1b[0m");
    }

    result
}

fn parse_osc8_state(sequence: &[u8]) -> Option<bool> {
    if !sequence.starts_with(b"\x1b]") {
        return None;
    }
    let payload = if sequence.ends_with(b"\x07") && sequence.len() >= 3 {
        &sequence[2..sequence.len() - 1]
    } else if sequence.ends_with(b"\x1b\\") && sequence.len() >= 4 {
        &sequence[2..sequence.len() - 2]
    } else {
        return None;
    };
    if !payload.starts_with(b"8;") {
        return None;
    }
    let rest = &payload[2..];
    let uri_start = rest.iter().position(|&byte| byte == b';')?;
    let uri = &rest[uri_start + 1..];
    Some(!uri.is_empty())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn status_helpers_sanitize_and_truncate() {
        let sanitized = sanitize_status("ok\t界bad\n");
        assert_eq!(sanitized, "ok 界bad ");
        assert_eq!(sanitize_status("ok界🙂"), "ok界🙂");
        assert_eq!(status_text_display_width("abc"), 3);
        assert_eq!(status_text_display_width("界"), 2);
        assert_eq!(truncate_status("hello", 0), "");
        assert_eq!(truncate_status("hello", 2), "he");
        assert_eq!(truncate_status("A界B", 2), "A");
        assert_eq!(truncate_status("A界B", 3), "A界");
    }

    #[test]
    fn truncate_ansi_line_plain_text() {
        assert_eq!(truncate_ansi_line("hello world", 5), "hello\x1b[0m");
        assert_eq!(truncate_ansi_line("hello", 10), "hello");
        assert_eq!(truncate_ansi_line("hello", 0), "");
    }

    #[test]
    fn truncate_ansi_line_preserves_escape_sequences() {
        // Color code should not count toward width.
        let colored = "\x1b[91mRed text\x1b[0m";
        let result = truncate_ansi_line(colored, 3);
        assert!(result.starts_with("\x1b[91mRed"));
        assert!(result.ends_with("\x1b[0m"));
    }

    #[test]
    fn truncate_ansi_line_no_truncation_keeps_original() {
        let line = "\x1b[92mOK\x1b[0m";
        // "OK" is 2 visible chars, fits in width 10.
        assert_eq!(truncate_ansi_line(line, 10), line);
    }

    #[test]
    fn truncate_ansi_line_unicode_width() {
        let line = "A界B";
        // 界 is 2 columns wide. A(1) + 界(2) = 3, B would be 4.
        assert_eq!(truncate_ansi_line(line, 3), "A界\x1b[0m");
    }

    #[test]
    fn truncate_ansi_line_osc8_escapes_do_not_count_toward_width() {
        let line = "\x1b]8;;https://example.com/docs\x1b\\[README]\x1b]8;;\x1b\\";
        // Visible width of "[README]" is 8.
        assert_eq!(truncate_ansi_line(line, 8), line);
    }

    #[test]
    fn truncate_ansi_line_closes_osc8_when_truncated_inside_link_label() {
        let line = "\x1b]8;;https://example.com/docs\x1b\\[README]\x1b]8;;\x1b\\";
        let out = truncate_ansi_line(line, 4);
        assert!(out.contains("\x1b]8;;https://example.com/docs\x1b\\"));
        assert!(out.contains("[REA"));
        assert!(out.contains("\x1b]8;;\x1b\\\x1b[0m"));
    }

    #[test]
    fn truncate_ansi_line_osc_with_bel_terminator_is_ignored_for_width() {
        let line = "\x1b]0;Window title\x07OK";
        assert_eq!(truncate_ansi_line(line, 2), line);
    }
}
