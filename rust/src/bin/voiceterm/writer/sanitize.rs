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
    let mut chars = line.chars().peekable();
    let mut truncated = false;

    while let Some(ch) = chars.next() {
        // Pass through ANSI escape sequences without counting width.
        if ch == '\x1b' {
            result.push(ch);
            // Consume the rest of the escape sequence.
            if let Some(&next) = chars.peek() {
                if next == '[' {
                    if let Some(next_char) = chars.next() {
                        result.push(next_char);
                    } else {
                        break;
                    }
                    // CSI sequence: consume until a letter in '@'..='~'.
                    while let Some(&param) = chars.peek() {
                        if let Some(next_char) = chars.next() {
                            result.push(next_char);
                        } else {
                            break;
                        }
                        if param.is_ascii_alphabetic() || ('@'..='~').contains(&param) {
                            break;
                        }
                    }
                } else {
                    // Non-CSI (e.g. ESC 7 / ESC 8): consume the single char.
                    if let Some(next_char) = chars.next() {
                        result.push(next_char);
                    } else {
                        break;
                    }
                }
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
    }

    if truncated {
        // Reset attributes so the erase-to-end-of-line that follows does
        // not inherit colours from the truncated content.
        result.push_str("\x1b[0m");
    }

    result
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
}
