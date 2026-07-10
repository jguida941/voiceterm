/// Extract the first non-empty, non-bullet-prefix line for compact display.
pub(crate) fn first_meaningful_line(text: &str) -> String {
    for line in text.lines() {
        let trimmed = line.trim().trim_start_matches('-').trim();
        if !trimmed.is_empty() {
            return trimmed.to_string();
        }
    }
    String::new()
}

/// Push non-empty trimmed lines from `text` into `out`, indented with 2 spaces.
/// Shared by cockpit page rendering and fresh-prompt generation.
pub(crate) fn push_trimmed_lines(out: &mut Vec<String>, text: &str) {
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.is_empty() {
            out.push(format!("  {trimmed}"));
        }
    }
}

/// Parse a bullet-point list section into individual scope items.
pub(crate) fn parse_scope_list(text: &str) -> Vec<String> {
    text.lines()
        .filter_map(|line| {
            let trimmed = line.trim();
            let stripped = trimmed
                .trim_start_matches('-')
                .trim_start_matches('*')
                .trim();
            if stripped.is_empty() || stripped.starts_with('#') {
                None
            } else {
                Some(stripped.to_string())
            }
        })
        .collect()
}

/// Show only the first 12 chars of a worktree hash for compact display.
pub(crate) fn truncate_hash(hash: &str) -> &str {
    if hash.len() > 12 {
        &hash[..12]
    } else {
        hash
    }
}
