//! Action Center audit and policy enforcement (MP-234).
//!
//! Provides the action template catalog, policy classification,
//! and audit logging for overlay command execution.

use super::types::*;

/// Built-in action templates for the Action Center.
pub(crate) fn builtin_actions() -> Vec<ActionTemplate> {
    vec![
        ActionTemplate {
            id: "git_status".to_string(),
            label: "Git Status".to_string(),
            command: "git status --short".to_string(),
            policy: ActionPolicyTier::ReadOnly,
            description: "Show working tree status".to_string(),
        },
        ActionTemplate {
            id: "git_log".to_string(),
            label: "Git Log".to_string(),
            command: "git log --oneline -n 10".to_string(),
            policy: ActionPolicyTier::ReadOnly,
            description: "Show recent commits".to_string(),
        },
        ActionTemplate {
            id: "git_diff".to_string(),
            label: "Git Diff".to_string(),
            command: "git diff --stat".to_string(),
            policy: ActionPolicyTier::ReadOnly,
            description: "Show changed files summary".to_string(),
        },
        ActionTemplate {
            id: "cargo_test".to_string(),
            label: "Cargo Test".to_string(),
            command: "cargo test --bin voiceterm".to_string(),
            policy: ActionPolicyTier::ConfirmRequired,
            description: "Run project tests".to_string(),
        },
        ActionTemplate {
            id: "cargo_check".to_string(),
            label: "Cargo Check".to_string(),
            command: "cargo check".to_string(),
            policy: ActionPolicyTier::ReadOnly,
            description: "Type-check the project".to_string(),
        },
        ActionTemplate {
            id: "devctl_check".to_string(),
            label: "DevCtl Check".to_string(),
            command: "python3 dev/scripts/devctl.py check --profile ci".to_string(),
            policy: ActionPolicyTier::ConfirmRequired,
            description: "Run CI verification checks".to_string(),
        },
        ActionTemplate {
            id: "devctl_docs".to_string(),
            label: "Docs Check".to_string(),
            command: "python3 dev/scripts/devctl.py docs-check --user-facing".to_string(),
            policy: ActionPolicyTier::ReadOnly,
            description: "Verify documentation coverage".to_string(),
        },
        ActionTemplate {
            id: "devctl_hygiene".to_string(),
            label: "Hygiene Check".to_string(),
            command: "python3 dev/scripts/devctl.py hygiene".to_string(),
            policy: ActionPolicyTier::ReadOnly,
            description: "Run governance hygiene checks".to_string(),
        },
    ]
}

/// Classify a command string into a policy tier.
/// Default: all non-read actions are `ConfirmRequired`.
pub(crate) fn classify_command_policy(command: &str) -> ActionPolicyTier {
    let cmd_lower = command.to_ascii_lowercase();

    // Blocked commands (dangerous/destructive).
    let blocked_patterns = [
        "rm -rf",
        "rm -r /",
        "sudo rm",
        "mkfs",
        "dd if=",
        "> /dev/",
        ":(){ :|:",
        "chmod -R 777",
        "git push --force",
        "git reset --hard",
    ];
    for pattern in &blocked_patterns {
        if cmd_lower.contains(pattern) {
            return ActionPolicyTier::Blocked;
        }
    }

    // Read-only commands.
    let read_only_prefixes = [
        "git status",
        "git log",
        "git diff",
        "git branch",
        "git remote",
        "git show",
        "ls ",
        "cat ",
        "head ",
        "tail ",
        "wc ",
        "find ",
        "grep ",
        "rg ",
        "cargo check",
        "cargo clippy",
        "python3 dev/scripts/devctl.py docs-check",
        "python3 dev/scripts/devctl.py hygiene",
        "python3 dev/scripts/devctl.py status",
        "python3 dev/scripts/devctl.py report",
        "python3 dev/scripts/devctl.py list",
    ];
    for prefix in &read_only_prefixes {
        if cmd_lower.starts_with(prefix) {
            return ActionPolicyTier::ReadOnly;
        }
    }

    // Everything else requires confirmation.
    ActionPolicyTier::ConfirmRequired
}

/// Action Center state for the overlay.
#[derive(Debug)]
pub(crate) struct ActionCenterState {
    pub(crate) actions: Vec<ActionTemplate>,
    pub(crate) selected: usize,
    pub(crate) scroll_offset: usize,
    pub(crate) pending_approval: Option<usize>,
    pub(crate) last_result: Option<ActionRunSummary>,
}

/// Summary of the last action run for display.
#[derive(Debug, Clone)]
pub(crate) struct ActionRunSummary {
    pub(crate) label: String,
    pub(crate) exit_code: Option<i32>,
    pub(crate) output_preview: String,
}

impl ActionCenterState {
    pub(crate) fn new() -> Self {
        Self {
            actions: builtin_actions(),
            selected: 0,
            scroll_offset: 0,
            pending_approval: None,
            last_result: None,
        }
    }

    pub(crate) fn move_up(&mut self) {
        if self.selected > 0 {
            self.selected -= 1;
            if self.selected < self.scroll_offset {
                self.scroll_offset = self.selected;
            }
        }
    }

    pub(crate) fn move_down(&mut self) {
        let max = self.actions.len().saturating_sub(1);
        if self.selected < max {
            self.selected += 1;
        }
    }

    pub(crate) fn selected_action(&self) -> Option<&ActionTemplate> {
        self.actions.get(self.selected)
    }

    /// Request execution of the selected action.
    /// Returns the action if it can proceed (ReadOnly or ConfirmRequired with approval).
    pub(crate) fn request_execute(&mut self) -> Option<&ActionTemplate> {
        let action = self.actions.get(self.selected)?;
        match action.policy {
            ActionPolicyTier::ReadOnly => Some(action),
            ActionPolicyTier::ConfirmRequired => {
                if self.pending_approval == Some(self.selected) {
                    // Already pending, this is the confirmation.
                    self.pending_approval = None;
                    Some(action)
                } else {
                    // First press: request approval.
                    self.pending_approval = Some(self.selected);
                    None
                }
            }
            ActionPolicyTier::Blocked => None,
        }
    }

    /// Cancel any pending approval.
    pub(crate) fn cancel_approval(&mut self) {
        self.pending_approval = None;
    }

    /// Ensure scroll offset keeps the selected item visible.
    pub(crate) fn clamp_scroll(&mut self, visible_rows: usize) {
        if visible_rows == 0 {
            return;
        }
        if self.selected >= self.scroll_offset + visible_rows {
            self.scroll_offset = self.selected.saturating_sub(visible_rows.saturating_sub(1));
        }
        if self.selected < self.scroll_offset {
            self.scroll_offset = self.selected;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn builtin_actions_are_not_empty() {
        let actions = builtin_actions();
        assert!(!actions.is_empty());
        // All should have non-empty fields.
        for a in &actions {
            assert!(!a.id.is_empty());
            assert!(!a.label.is_empty());
            assert!(!a.command.is_empty());
        }
    }

    #[test]
    fn classify_command_read_only() {
        assert_eq!(
            classify_command_policy("git status --short"),
            ActionPolicyTier::ReadOnly
        );
        assert_eq!(
            classify_command_policy("git log --oneline"),
            ActionPolicyTier::ReadOnly
        );
        assert_eq!(
            classify_command_policy("cargo check"),
            ActionPolicyTier::ReadOnly
        );
    }

    #[test]
    fn classify_command_blocked() {
        assert_eq!(
            classify_command_policy("rm -rf /"),
            ActionPolicyTier::Blocked
        );
        assert_eq!(
            classify_command_policy("sudo rm -rf /tmp"),
            ActionPolicyTier::Blocked
        );
        assert_eq!(
            classify_command_policy("git push --force origin main"),
            ActionPolicyTier::Blocked
        );
    }

    #[test]
    fn classify_command_confirm_required() {
        assert_eq!(
            classify_command_policy("cargo test --bin voiceterm"),
            ActionPolicyTier::ConfirmRequired
        );
        assert_eq!(
            classify_command_policy("make build"),
            ActionPolicyTier::ConfirmRequired
        );
    }

    #[test]
    fn action_center_navigation() {
        let mut state = ActionCenterState::new();
        assert_eq!(state.selected, 0);

        state.move_down();
        assert_eq!(state.selected, 1);

        state.move_up();
        assert_eq!(state.selected, 0);

        // Cannot go below 0.
        state.move_up();
        assert_eq!(state.selected, 0);
    }

    #[test]
    fn action_center_read_only_executes_immediately() {
        let mut state = ActionCenterState::new();
        // First action is git_status (ReadOnly).
        let action = state.request_execute();
        assert!(action.is_some());
        assert_eq!(action.unwrap().id, "git_status");
    }

    #[test]
    fn action_center_confirm_required_needs_two_presses() {
        let mut state = ActionCenterState::new();
        // Select cargo_test (index 3, ConfirmRequired).
        state.selected = 3;

        // First press: starts approval.
        let first = state.request_execute();
        assert!(first.is_none());
        assert_eq!(state.pending_approval, Some(3));

        // Second press: confirms.
        let second = state.request_execute();
        assert!(second.is_some());
        assert_eq!(second.unwrap().id, "cargo_test");
        assert!(state.pending_approval.is_none());
    }

    #[test]
    fn action_center_cancel_approval() {
        let mut state = ActionCenterState::new();
        state.selected = 3;
        let _ = state.request_execute(); // Start approval.
        assert!(state.pending_approval.is_some());

        state.cancel_approval();
        assert!(state.pending_approval.is_none());
    }

    #[test]
    fn action_center_clamp_scroll() {
        let mut state = ActionCenterState::new();
        state.selected = 5;
        state.scroll_offset = 0;
        state.clamp_scroll(3);
        assert!(state.scroll_offset > 0);
    }

    #[test]
    fn selected_action_returns_correct_template() {
        let state = ActionCenterState::new();
        let action = state.selected_action();
        assert!(action.is_some());
        assert_eq!(action.unwrap().id, "git_status");
    }
}
