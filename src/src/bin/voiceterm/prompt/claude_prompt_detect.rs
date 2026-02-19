//! Claude-mode interactive prompt detection so HUD suppression can prevent occlusion.
//!
//! Detects Claude CLI approval prompts, sandbox permission requests, and worktree
//! permission walls that can be obscured by VoiceTerm HUD/overlay rows.

use std::time::Instant;

/// Diagnostic snapshot captured when a prompt-state transition occurs.
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub(crate) struct PromptOcclusionDiagnostic {
    /// Terminal rows at detection time.
    pub(crate) terminal_rows: u16,
    /// Terminal columns at detection time.
    pub(crate) terminal_cols: u16,
    /// Current HUD style name.
    pub(crate) hud_style: String,
    /// Current HUD mode (overlay or banner).
    pub(crate) hud_mode: String,
    /// Detected prompt type.
    pub(crate) prompt_type: PromptType,
    /// Whether absolute worktree paths are present in the prompt context.
    pub(crate) has_worktree_paths: bool,
    /// Estimated command preview wrap depth (lines).
    pub(crate) command_wrap_depth: usize,
    /// Whether a tool-batch summary (`+N more tool uses`) is present.
    pub(crate) has_tool_batch_summary: bool,
}

/// Types of Claude interactive prompts that can cause occlusion.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum PromptType {
    /// Single-command approval prompt (e.g., "Do you want to run this command?")
    SingleCommandApproval,
    /// Local/worktree permission prompt (e.g., cross-worktree read)
    WorktreePermission,
    /// Multi-tool batch approval (e.g., "+N more tool uses")
    MultiToolBatch,
    /// Generic interactive prompt detected by heuristics.
    GenericInteractive,
}

/// State machine for Claude prompt detection and HUD suppression policy.
#[derive(Debug)]
pub(crate) struct ClaudePromptDetector {
    /// Whether Claude is the active backend.
    is_claude_backend: bool,
    /// Current suppression state.
    suppressed: bool,
    /// When suppression was last activated.
    suppressed_at: Option<Instant>,
    /// Rolling line buffer for prompt pattern matching.
    line_buffer: Vec<u8>,
    /// Accumulated lines for multi-line prompt context.
    recent_lines: Vec<String>,
    /// Maximum lines to keep for context.
    max_context_lines: usize,
    /// Last detected prompt type.
    last_prompt_type: Option<PromptType>,
    /// Last diagnostic snapshot.
    last_diagnostic: Option<PromptOcclusionDiagnostic>,
}

/// Claude prompt detection patterns.
const SINGLE_COMMAND_PATTERNS: &[&str] = &[
    "do you want to proceed",
    "do you want to run",
    "allow this command",
    "approve this action",
    "run this command?",
    "execute this?",
    "press enter to continue",
    "press y to confirm",
    "(y/n)",
    "[y/n]",
    "(yes/no)",
    "[yes/no]",
];

const WORKTREE_PERMISSION_PATTERNS: &[&str] = &[
    "do you want to allow",
    "permission to read",
    "permission to write",
    "permission to access",
    "access files outside",
    "outside the project",
    "worktree access",
    "cross-worktree",
    "outside the current directory",
];

const MULTI_TOOL_BATCH_PATTERNS: &[&str] = &[
    "more tool use",
    "more tool calls",
    "additional tool",
    "+1 more tool",
    "+2 more tool",
    "+3 more tool",
    "+4 more tool",
    "+5 more tool",
];

const GENERIC_INTERACTIVE_PATTERNS: &[&str] = &[
    "do you want to",
    "would you like to",
    "shall i proceed",
    "continue?",
    "proceed?",
];

/// Time before prompt suppression auto-expires (seconds).
const PROMPT_SUPPRESSION_TIMEOUT_SECS: u64 = 30;

impl ClaudePromptDetector {
    pub(crate) fn new(is_claude_backend: bool) -> Self {
        Self {
            is_claude_backend,
            suppressed: false,
            suppressed_at: None,
            line_buffer: Vec::with_capacity(512),
            recent_lines: Vec::with_capacity(8),
            max_context_lines: 8,
            last_prompt_type: None,
            last_diagnostic: None,
        }
    }

    /// Feed raw PTY output bytes and detect Claude interactive prompts.
    /// Returns true if a new prompt was just detected (transition to suppressed).
    pub(crate) fn feed_output(&mut self, bytes: &[u8]) -> bool {
        if !self.is_claude_backend {
            return false;
        }

        let mut newly_detected = false;
        for &byte in bytes {
            match byte {
                b'\n' => {
                    let line = String::from_utf8_lossy(&self.line_buffer).to_string();
                    if !line.trim().is_empty() {
                        if self.recent_lines.len() >= self.max_context_lines {
                            self.recent_lines.remove(0);
                        }
                        self.recent_lines.push(line.clone());
                    }
                    self.line_buffer.clear();
                }
                b'\r' => {
                    // CR may precede prompt text; flush current line and check
                    if !self.line_buffer.is_empty() {
                        let line = String::from_utf8_lossy(&self.line_buffer).to_string();
                        if !line.trim().is_empty() {
                            if self.recent_lines.len() >= self.max_context_lines {
                                self.recent_lines.remove(0);
                            }
                            self.recent_lines.push(line);
                        }
                        self.line_buffer.clear();
                    }
                }
                byte if byte.is_ascii_graphic() || byte == b' ' => {
                    self.line_buffer.push(byte);
                }
                _ => {} // Skip ANSI/control bytes for detection
            }
        }

        // Check the current partial line and recent lines for prompt patterns
        let current_line = String::from_utf8_lossy(&self.line_buffer).to_lowercase();
        let combined_context = self.combined_context();
        let lower_context = combined_context.to_ascii_lowercase();

        if let Some(prompt_type) = detect_prompt_type(&current_line, &lower_context) {
            if !self.suppressed {
                self.suppressed = true;
                self.suppressed_at = Some(Instant::now());
                self.last_prompt_type = Some(prompt_type);
                newly_detected = true;
            }
        }

        newly_detected
    }

    /// Check if HUD should currently be suppressed for prompt safety.
    pub(crate) fn should_suppress_hud(&self) -> bool {
        if !self.suppressed {
            return false;
        }
        // Auto-expire after timeout
        if let Some(at) = self.suppressed_at {
            if at.elapsed().as_secs() >= PROMPT_SUPPRESSION_TIMEOUT_SECS {
                return false;
            }
        }
        true
    }

    /// Notify that user input was sent (Enter/y/n/etc), resolving the prompt.
    pub(crate) fn on_user_input(&mut self) {
        if self.suppressed {
            self.suppressed = false;
            self.suppressed_at = None;
            self.recent_lines.clear();
        }
    }

    /// Capture a diagnostic snapshot for the current prompt state.
    #[allow(dead_code)]
    pub(crate) fn capture_diagnostic(
        &mut self,
        terminal_rows: u16,
        terminal_cols: u16,
        hud_style: &str,
        hud_mode: &str,
    ) -> Option<&PromptOcclusionDiagnostic> {
        let prompt_type = self.last_prompt_type?;
        let context = self.combined_context();
        let lower_context = context.to_ascii_lowercase();
        let has_worktree_paths =
            context.contains("/Users/") || context.contains("/home/") || context.contains("/tmp/");
        let command_wrap_depth = estimate_command_wrap_depth(&context, terminal_cols as usize);
        let has_tool_batch_summary = MULTI_TOOL_BATCH_PATTERNS
            .iter()
            .any(|p| lower_context.contains(p));

        self.last_diagnostic = Some(PromptOcclusionDiagnostic {
            terminal_rows,
            terminal_cols,
            hud_style: hud_style.to_string(),
            hud_mode: hud_mode.to_string(),
            prompt_type,
            has_worktree_paths,
            command_wrap_depth,
            has_tool_batch_summary,
        });
        self.last_diagnostic.as_ref()
    }

    /// Return the last captured diagnostic, if any.
    #[allow(dead_code)]
    pub(crate) fn last_diagnostic(&self) -> Option<&PromptOcclusionDiagnostic> {
        self.last_diagnostic.as_ref()
    }

    /// Whether the detector is tracking Claude backend.
    #[allow(dead_code)]
    pub(crate) fn is_claude(&self) -> bool {
        self.is_claude_backend
    }

    fn combined_context(&self) -> String {
        let mut parts: Vec<&str> = self.recent_lines.iter().map(String::as_str).collect();
        let current = String::from_utf8_lossy(&self.line_buffer);
        let current_str = current.as_ref();
        if !current_str.trim().is_empty() {
            parts.push(current_str);
        }
        parts.join("\n")
    }
}

fn detect_prompt_type(current_line: &str, context: &str) -> Option<PromptType> {
    // Check in priority order: most specific first
    if WORKTREE_PERMISSION_PATTERNS
        .iter()
        .any(|p| context.contains(p) || current_line.contains(p))
    {
        return Some(PromptType::WorktreePermission);
    }
    if MULTI_TOOL_BATCH_PATTERNS
        .iter()
        .any(|p| context.contains(p) || current_line.contains(p))
    {
        return Some(PromptType::MultiToolBatch);
    }
    if SINGLE_COMMAND_PATTERNS
        .iter()
        .any(|p| context.contains(p) || current_line.contains(p))
    {
        return Some(PromptType::SingleCommandApproval);
    }
    if GENERIC_INTERACTIVE_PATTERNS
        .iter()
        .any(|p| context.contains(p) || current_line.contains(p))
    {
        return Some(PromptType::GenericInteractive);
    }
    None
}

#[allow(dead_code)]
fn estimate_command_wrap_depth(context: &str, terminal_cols: usize) -> usize {
    if terminal_cols == 0 {
        return 0;
    }
    context
        .lines()
        .map(|line| {
            let len = line.len();
            if len == 0 {
                1
            } else {
                len.div_ceil(terminal_cols)
            }
        })
        .sum()
}

#[cfg(test)]
mod tests {
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
    fn detector_detects_generic_interactive() {
        let mut detector = ClaudePromptDetector::new(true);
        let detected = detector.feed_output(b"Would you like to proceed?\n");
        assert!(detected);
        assert_eq!(
            detector.last_prompt_type,
            Some(PromptType::GenericInteractive)
        );
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
    fn detector_does_not_re_suppress_same_prompt() {
        let mut detector = ClaudePromptDetector::new(true);
        let first = detector.feed_output(b"Do you want to proceed? (y/n)\n");
        assert!(first);
        let second = detector.feed_output(b"still waiting...\n");
        assert!(!second);
        assert!(detector.should_suppress_hud());
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
        assert_eq!(diag.prompt_type, PromptType::WorktreePermission);
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
        );
        assert_eq!(prompt_type, Some(PromptType::WorktreePermission));
    }

    #[test]
    fn is_claude_flag() {
        let detector = ClaudePromptDetector::new(true);
        assert!(detector.is_claude());
        let detector = ClaudePromptDetector::new(false);
        assert!(!detector.is_claude());
    }
}
