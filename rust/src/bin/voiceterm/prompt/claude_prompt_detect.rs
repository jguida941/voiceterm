//! Interactive prompt detection so HUD suppression can prevent occlusion.
//!
//! Detects interactive approval prompts that can be obscured by VoiceTerm HUD/overlay rows.

use std::collections::VecDeque;
use std::time::Instant;

use crate::runtime_compat;

use super::strip::strip_ansi_preserve_controls;

/// Diagnostic snapshot captured when a prompt-state transition occurs.
#[cfg(test)]
#[derive(Debug, Clone)]
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

/// Types of interactive prompts that can cause occlusion.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum PromptType {
    /// Single-command approval prompt (e.g., "Do you want to run this command?")
    SingleCommandApproval,
    /// Local/worktree permission prompt (e.g., cross-worktree read)
    WorktreePermission,
    /// Multi-tool batch approval (e.g., "+N more tool uses")
    MultiToolBatch,
    /// Startup grace window used to avoid first-frame HUD collisions on IDE terminals.
    StartupGuard,
    /// Composer/input prompt (for example Claude reply box markers).
    ReplyComposer,
}

/// State machine for prompt detection and HUD suppression policy.
#[derive(Debug)]
pub(crate) struct ClaudePromptDetector {
    /// Whether prompt suppression heuristics are enabled for this backend.
    prompt_guard_enabled: bool,
    /// Whether reply-composer marker detection is enabled.
    detect_reply_composer: bool,
    /// Current suppression state.
    suppressed: bool,
    /// When suppression was last activated.
    suppressed_at: Option<Instant>,
    /// Rolling line buffer for prompt pattern matching.
    line_buffer: Vec<u8>,
    /// Accumulated lines for multi-line prompt context.
    recent_lines: VecDeque<String>,
    /// Maximum lines to keep for context.
    max_context_lines: usize,
    /// Last detected prompt type.
    last_prompt_type: Option<PromptType>,
    /// One-shot flag set when output contains explicit prompt-ready markers.
    resolved_on_ready_marker: bool,
    /// Tracks whether the one-shot ready marker came from startup guard release.
    ready_marker_from_startup_guard: bool,
    /// Last diagnostic snapshot.
    #[cfg(test)]
    last_diagnostic: Option<PromptOcclusionDiagnostic>,
}

/// Prompt detection patterns.
const SINGLE_COMMAND_PATTERNS: &[&str] = &[
    "do you want to proceed",
    "do you want to run",
    "this command requires approval",
    "requires approval",
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
    "yes, and don't ask again for",
    "yes, and dont ask again for",
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

const REPLY_COMPOSER_PATTERNS: &[&str] = &[
    "to generate command",
    "generate command",
    "type a message",
    "type your message",
];

/// Time before prompt suppression auto-expires (seconds).
///
/// Approval/worktree prompts should stay suppressed long enough for deliberate
/// user review so option rows do not get occluded mid-prompt.
const PROMPT_SUPPRESSION_TIMEOUT_SECS: u64 = 180;
const STARTUP_GUARD_TIMEOUT_SECS: u64 = 2;
const STARTUP_READY_PATTERNS: &[&str] = &["for shortcuts", "try \"", "try '"];

fn suppression_timeout_secs(prompt_type: Option<PromptType>) -> u64 {
    match prompt_type {
        Some(PromptType::StartupGuard) => STARTUP_GUARD_TIMEOUT_SECS,
        _ => PROMPT_SUPPRESSION_TIMEOUT_SECS,
    }
}

pub(crate) fn backend_supports_prompt_occlusion_guard(backend_label: &str) -> bool {
    runtime_compat::backend_supports_prompt_occlusion_guard(backend_label)
}

impl ClaudePromptDetector {
    #[cfg(test)]
    pub(crate) fn new(prompt_guard_enabled: bool) -> Self {
        Self::new_with_policy(prompt_guard_enabled, false)
    }

    pub(crate) fn new_for_backend(backend_label: &str) -> Self {
        Self::new_with_policy(
            backend_supports_prompt_occlusion_guard(backend_label),
            false,
        )
    }

    fn new_with_policy(prompt_guard_enabled: bool, detect_reply_composer: bool) -> Self {
        Self {
            prompt_guard_enabled,
            detect_reply_composer,
            suppressed: false,
            suppressed_at: None,
            line_buffer: Vec::with_capacity(512),
            recent_lines: VecDeque::with_capacity(8),
            max_context_lines: 8,
            last_prompt_type: None,
            resolved_on_ready_marker: false,
            ready_marker_from_startup_guard: false,
            #[cfg(test)]
            last_diagnostic: None,
        }
    }

    /// Feed raw PTY output bytes and detect interactive prompts.
    /// Returns true if a new prompt was just detected (transition to suppressed).
    pub(crate) fn feed_output(&mut self, bytes: &[u8]) -> bool {
        if !self.prompt_guard_enabled {
            return false;
        }

        // Expired suppression should not be revived by stale context lines.
        if self.suppressed
            && self.suppressed_at.is_some_and(|at| {
                at.elapsed().as_secs() >= suppression_timeout_secs(self.last_prompt_type)
            })
        {
            self.suppressed = false;
            self.suppressed_at = None;
            self.last_prompt_type = None;
            self.resolved_on_ready_marker = false;
            self.ready_marker_from_startup_guard = false;
            self.recent_lines.clear();
            self.line_buffer.clear();
        }

        let cleaned = strip_ansi_preserve_controls(bytes);
        let mut newly_detected = false;
        let was_suppressed_at_entry = self.suppressed;
        for &byte in &cleaned {
            match byte {
                b'\n' => {
                    let line = String::from_utf8_lossy(&self.line_buffer).to_string();
                    if !line.trim().is_empty() {
                        self.push_context_line(line.clone());
                    }
                    self.line_buffer.clear();
                }
                b'\r' => {
                    // CR may precede prompt text; flush current line and check
                    if !self.line_buffer.is_empty() {
                        let line = String::from_utf8_lossy(&self.line_buffer).to_string();
                        if !line.trim().is_empty() {
                            self.push_context_line(line);
                        }
                        self.line_buffer.clear();
                    }
                }
                b'\t' => {
                    self.line_buffer.push(b' ');
                }
                byte if !byte.is_ascii_control() => {
                    self.line_buffer.push(byte);
                }
                _ => {} // Skip ANSI/control bytes for detection
            }
        }

        // Check the current partial line and recent lines for prompt patterns
        let current_line = String::from_utf8_lossy(&self.line_buffer).to_lowercase();
        let combined_context = self.combined_context();
        let lower_context = combined_context.to_ascii_lowercase();

        // Startup suppression is only a first-frame guard. As soon as we see
        // stable prompt-ready markers, release it early instead of waiting for
        // the full timeout.
        let startup_ready_candidate = self.suppressed
            && self.last_prompt_type == Some(PromptType::StartupGuard)
            && startup_guard_ready(&current_line, &lower_context);
        if startup_ready_candidate {
            self.suppressed = false;
            self.suppressed_at = None;
            self.last_prompt_type = None;
            self.resolved_on_ready_marker = true;
            self.ready_marker_from_startup_guard = true;
        }

        let prompt_type =
            detect_prompt_type(&current_line, &lower_context, self.detect_reply_composer);

        if let Some(prompt_type) = prompt_type {
            if !self.suppressed {
                self.suppressed = true;
                if !was_suppressed_at_entry {
                    newly_detected = true;
                }
            }
            // Refresh suppression timeout whenever prompt context is still present.
            self.suppressed_at = Some(Instant::now());
            self.last_prompt_type = Some(prompt_type);
            // Same-chunk prompt detection wins over a ready-marker release.
            self.resolved_on_ready_marker = false;
            self.ready_marker_from_startup_guard = false;
        }

        newly_detected
    }

    /// Activate a short startup suppression window.
    pub(crate) fn activate_startup_guard(&mut self) {
        if !self.prompt_guard_enabled {
            return;
        }
        self.suppressed = true;
        self.suppressed_at = Some(Instant::now());
        self.last_prompt_type = Some(PromptType::StartupGuard);
    }

    /// Check if HUD should currently be suppressed for prompt safety.
    pub(crate) fn should_suppress_hud(&self) -> bool {
        if !self.suppressed {
            return false;
        }
        // Auto-expire after timeout
        if let Some(at) = self.suppressed_at {
            let timeout_secs = suppression_timeout_secs(self.last_prompt_type);
            if at.elapsed().as_secs() >= timeout_secs {
                return false;
            }
        }
        true
    }

    /// Notify that prompt-submit or prompt-abort input was sent, resolving the prompt.
    pub(crate) fn on_user_input(&mut self) {
        if self.suppressed {
            self.suppressed = false;
            self.suppressed_at = None;
            self.last_prompt_type = None;
            self.recent_lines.clear();
            self.line_buffer.clear();
        }
    }

    /// Consume a one-shot explicit-ready transition signal.
    #[cfg(test)]
    pub(crate) fn take_ready_marker_resolution(&mut self) -> bool {
        self.take_ready_marker_resolution_kind().is_some()
    }

    /// Consume a one-shot explicit-ready transition source marker.
    pub(crate) fn take_ready_marker_resolution_kind(&mut self) -> Option<PromptType> {
        if !self.resolved_on_ready_marker {
            return None;
        }
        self.resolved_on_ready_marker = false;
        self.ready_marker_from_startup_guard = false;
        Some(PromptType::StartupGuard)
    }

    /// Return true when this input should resolve the active suppression.
    pub(crate) fn should_resolve_on_input(&self, bytes: &[u8]) -> bool {
        if !self.suppressed || bytes.is_empty() {
            return false;
        }
        match self.last_prompt_type {
            Some(PromptType::ReplyComposer) => bytes.iter().any(|byte| {
                matches!(
                    byte,
                    b'\r'   // Enter
                        | b'\n' // LF submit path
                        | 0x03  // Ctrl+C cancel
                        | 0x04  // Ctrl+D exit
                        | 0x1b // Escape cancel
                )
            }),
            Some(PromptType::StartupGuard) => false,
            _ => matches!(
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
            ),
        }
    }

    /// Capture a diagnostic snapshot for the current prompt state.
    #[cfg(test)]
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
    #[cfg(test)]
    pub(crate) fn last_diagnostic(&self) -> Option<&PromptOcclusionDiagnostic> {
        self.last_diagnostic.as_ref()
    }

    /// Whether prompt-occlusion guardrails are enabled for this backend.
    #[cfg(test)]
    pub(crate) fn is_enabled(&self) -> bool {
        self.prompt_guard_enabled
    }

    fn push_context_line(&mut self, line: String) {
        if self.recent_lines.len() >= self.max_context_lines {
            self.recent_lines.pop_front();
        }
        self.recent_lines.push_back(line);
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

fn context_matches_patterns(current_line: &str, context: &str, patterns: &[&str]) -> bool {
    patterns
        .iter()
        .any(|pattern| context.contains(pattern) || current_line.contains(pattern))
}

fn detect_prompt_type(
    current_line: &str,
    context: &str,
    detect_reply_composer: bool,
) -> Option<PromptType> {
    if detect_reply_composer
        && (looks_like_reply_composer(current_line)
            || context_matches_patterns(current_line, context, REPLY_COMPOSER_PATTERNS))
    {
        return Some(PromptType::ReplyComposer);
    }
    // Claude/Codex approval cards often emit a "Bash command" section header, followed by
    // approval text in later rows. Treat that combo as a single-command approval prompt.
    let has_bash_header = current_line.contains("bash command") || context.contains("bash command");
    let has_approval_text = current_line.contains("do you want to proceed")
        || context.contains("do you want to proceed")
        || current_line.contains("this command requires approval")
        || context.contains("this command requires approval")
        || current_line.contains("requires approval")
        || context.contains("requires approval");
    if has_bash_header && has_approval_text {
        return Some(PromptType::SingleCommandApproval);
    }
    // Approval cards can arrive as numbered options with minimal prose. If we
    // only look for full question text, suppression can miss option rows and
    // let HUD reappear over choice lines (for example option 3).
    if looks_like_numbered_approval_card(context) {
        return Some(PromptType::SingleCommandApproval);
    }
    // Check in priority order: most specific first
    if context_matches_patterns(current_line, context, WORKTREE_PERMISSION_PATTERNS) {
        return Some(PromptType::WorktreePermission);
    }
    if context_matches_patterns(current_line, context, MULTI_TOOL_BATCH_PATTERNS) {
        return Some(PromptType::MultiToolBatch);
    }
    if context_matches_patterns(current_line, context, SINGLE_COMMAND_PATTERNS) {
        return Some(PromptType::SingleCommandApproval);
    }
    // Generic phrase matches are intentionally not used because they are noisy
    // in normal assistant output and can hide HUD unexpectedly.
    None
}

fn looks_like_numbered_approval_card(context: &str) -> bool {
    let mut has_option_1 = false;
    let mut has_option_2 = false;
    let mut has_option_3 = false;
    let mut has_yes = false;
    let mut has_no = false;
    let mut has_approval_text = false;
    let mut has_dont_ask_again = false;

    for line in context.lines().rev().take(12) {
        let lowered = normalize_approval_card_line(line);
        if starts_with_numbered_option(&lowered, b'1') {
            has_option_1 = true;
        }
        if starts_with_numbered_option(&lowered, b'2') {
            has_option_2 = true;
        }
        if starts_with_numbered_option(&lowered, b'3') {
            has_option_3 = true;
        }
        if lowered.contains(" yes") || lowered.starts_with("yes") {
            has_yes = true;
        }
        if lowered.contains(" no") || lowered.starts_with("no") {
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

    let has_numbered_options =
        has_option_1 && has_option_2 && (has_option_3 || has_approval_text || has_dont_ask_again);
    let has_approval_semantics = (has_yes && has_no) || has_approval_text || has_dont_ask_again;
    has_numbered_options && has_approval_semantics
}

fn normalize_approval_card_line(line: &str) -> String {
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

fn starts_with_numbered_option(line: &str, option: u8) -> bool {
    if line.len() < 2 {
        return false;
    }
    let first = option as char;
    let bytes = line.as_bytes();
    bytes[0] == first as u8 && matches!(bytes[1], b'.' | b')')
}

fn looks_like_reply_composer(current_line: &str) -> bool {
    let trimmed = current_line.trim();
    if trimmed.is_empty() || trimmed.len() > 240 {
        return false;
    }
    trimmed.starts_with('❯') || trimmed.starts_with('›') || trimmed.starts_with('〉')
}

fn startup_guard_ready(current_line: &str, context: &str) -> bool {
    if STARTUP_READY_PATTERNS
        .iter()
        .any(|pattern| context.contains(pattern) || current_line.contains(pattern))
    {
        return true;
    }
    context.lines().rev().take(4).any(|line| {
        let trimmed = line.trim_start();
        trimmed.starts_with('❯')
            || trimmed.starts_with('›')
            || trimmed.starts_with('〉')
            || (trimmed.starts_with('>') && trimmed.len() > 1)
    })
}

#[cfg(test)]
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
                len / terminal_cols + usize::from(len % terminal_cols != 0)
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
        let detected = detector.feed_output(b"Done. Press Enter to continue to Bash command 4/10.");
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
        detector.suppressed_at = Some(
            Instant::now() - std::time::Duration::from_secs(PROMPT_SUPPRESSION_TIMEOUT_SECS + 1),
        );
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
            "do you want to proceed?",
            "web search(\"rust\")\nclaude wants to search the web for: rust\ndo you want to proceed?",
            false,
        );
        assert_eq!(prompt_type, Some(PromptType::SingleCommandApproval));
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
}
