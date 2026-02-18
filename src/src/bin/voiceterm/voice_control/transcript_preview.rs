//! Shared transcript-preview formatter to keep navigation and drain paths consistent.

pub(super) fn format_transcript_preview(text: &str, max_len: usize) -> String {
    let trimmed = text.trim();
    if trimmed.is_empty() {
        return String::new();
    }
    let mut collapsed = String::new();
    let mut last_space = false;
    for ch in trimmed.chars() {
        if ch.is_whitespace() || ch.is_ascii_control() {
            if !last_space {
                collapsed.push(' ');
                last_space = true;
            }
        } else {
            collapsed.push(ch);
            last_space = false;
        }
    }
    let cleaned = collapsed.trim();
    let max_len = max_len.max(4);
    if cleaned.chars().count() > max_len {
        let keep = max_len.saturating_sub(3);
        let prefix: String = cleaned.chars().take(keep).collect();
        format!("{prefix}...")
    } else {
        cleaned.to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::format_transcript_preview;

    #[test]
    fn format_transcript_preview_cleans_and_collapses_whitespace() {
        assert_eq!(
            format_transcript_preview("  hello\t\nworld  ", 32),
            "hello world"
        );
    }

    #[test]
    fn format_transcript_preview_truncates_and_appends_ellipsis() {
        assert_eq!(format_transcript_preview("alpha beta gamma", 8), "alpha...");
    }

    #[test]
    fn format_transcript_preview_enforces_minimum_length_floor() {
        assert_eq!(format_transcript_preview("abcdef", 2), "a...");
    }

    #[test]
    fn format_transcript_preview_empty_input_returns_empty() {
        assert!(format_transcript_preview(" \n\t ", 12).is_empty());
    }
}
