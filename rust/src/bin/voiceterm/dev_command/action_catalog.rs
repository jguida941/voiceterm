//! Typed action catalog and execution profile model for the Dev panel.
//!
//! Every button press, review packet, or AI suggestion resolves through
//! this catalog rather than executing raw shell strings. The catalog maps
//! structured action requests to canonical repo handlers with explicit
//! policy outcomes per execution profile.

use super::DevCommandKind;

/// Execution profile controlling how actions are gated before running.
///
/// Default is `Guarded`. Agents may request `UnsafeDirect` but only the
/// human operator can toggle it. The profile is session-scoped and resets
/// to `Guarded` on restart.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub(crate) enum ExecutionProfile {
    /// Always run canonical prechecks, policy gates, and approval flow.
    #[default]
    Guarded,
    /// AI/planner chooses the approved playbook, but guards still run.
    AiAssistedGuarded,
    /// Skip selected non-critical checks for local iteration. Dev-only,
    /// red/noisy, non-default, operator-owned. Emits stronger audit trail.
    UnsafeDirect,
}

impl ExecutionProfile {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Guarded => "Guarded",
            Self::AiAssistedGuarded => "AI-assisted Guarded",
            Self::UnsafeDirect => "!! UNSAFE DIRECT !!",
        }
    }

    #[cfg(test)]
    pub(crate) fn is_unsafe(self) -> bool {
        matches!(self, Self::UnsafeDirect)
    }

    /// Cycle to the next profile in sequence.
    pub(crate) fn cycle(self) -> Self {
        match self {
            Self::Guarded => Self::AiAssistedGuarded,
            Self::AiAssistedGuarded => Self::UnsafeDirect,
            Self::UnsafeDirect => Self::Guarded,
        }
    }
}

/// Classification for actions in the catalog.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ActionCategory {
    /// Safe read-only operation, no side effects.
    ReadOnly,
    /// Mutating operation that requires confirmation.
    Mutating,
    /// Operation requiring explicit operator approval regardless of profile.
    /// Not constructed yet; needed when Git write and push/release actions land.
    OperatorApproval,
}

impl ActionCategory {
    pub(crate) fn marker(self) -> &'static str {
        match self {
            Self::ReadOnly => "R",
            Self::Mutating => "M",
            Self::OperatorApproval => "!",
        }
    }
}

/// Policy outcome after evaluating an action request against the active profile.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum PolicyOutcome {
    /// Action can run without user interaction.
    SafeAutoApply,
    /// Action output should be staged as a draft for review.
    StageDraft,
    /// Action requires explicit operator confirmation before running.
    OperatorApprovalRequired,
    /// Action is blocked under the current profile.
    Blocked,
}

impl PolicyOutcome {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::SafeAutoApply => "auto",
            Self::StageDraft => "draft",
            Self::OperatorApprovalRequired => "approval",
            Self::Blocked => "blocked",
        }
    }
}

/// A single entry in the typed action catalog.
#[derive(Debug, Clone)]
pub(crate) struct ActionEntry {
    id: &'static str,
    label: &'static str,
    category: ActionCategory,
    /// The backing devctl command, if this action routes through the broker.
    dev_command: Option<DevCommandKind>,
}

impl ActionEntry {
    pub(crate) fn label(&self) -> &'static str {
        self.label
    }

    pub(crate) fn category(&self) -> ActionCategory {
        self.category
    }

    pub(crate) fn dev_command(&self) -> Option<DevCommandKind> {
        self.dev_command
    }

    /// Resolve the policy outcome for this action under the given profile.
    pub(crate) fn resolve_policy(&self, profile: ExecutionProfile) -> PolicyOutcome {
        match (self.category, profile) {
            // Read-only actions are always safe regardless of profile.
            (ActionCategory::ReadOnly, _) => PolicyOutcome::SafeAutoApply,

            // Mutating actions under Guarded or AI-assisted require confirmation.
            (ActionCategory::Mutating, ExecutionProfile::Guarded)
            | (ActionCategory::Mutating, ExecutionProfile::AiAssistedGuarded) => {
                PolicyOutcome::OperatorApprovalRequired
            }
            // Mutating under Unsafe Direct gets staged as draft (still not silent).
            (ActionCategory::Mutating, ExecutionProfile::UnsafeDirect) => PolicyOutcome::StageDraft,

            // Operator-approval actions always require approval, even under Unsafe Direct.
            (ActionCategory::OperatorApproval, _) => PolicyOutcome::OperatorApprovalRequired,
        }
    }
}

/// The typed action catalog: a flat registry of all available actions.
///
/// All surfaces (buttons, AI packets, review channel) route through this
/// catalog instead of constructing raw shell commands.
#[derive(Debug, Clone)]
pub(crate) struct ActionCatalog {
    entries: Vec<ActionEntry>,
}

impl ActionCatalog {
    /// Expected number of entries in the default catalog. Used by height
    /// calculations that cannot access catalog state directly.
    pub(crate) const DEFAULT_LEN: usize = 14;

    fn default_entries() -> Vec<ActionEntry> {
        vec![
            ActionEntry {
                id: "devctl_status",
                label: "status",
                category: ActionCategory::ReadOnly,
                dev_command: Some(DevCommandKind::Status),
            },
            ActionEntry {
                id: "devctl_report",
                label: "report",
                category: ActionCategory::ReadOnly,
                dev_command: Some(DevCommandKind::Report),
            },
            ActionEntry {
                id: "devctl_triage",
                label: "triage",
                category: ActionCategory::ReadOnly,
                dev_command: Some(DevCommandKind::Triage),
            },
            ActionEntry {
                id: "devctl_loop_packet",
                label: "loop-packet",
                category: ActionCategory::ReadOnly,
                dev_command: Some(DevCommandKind::LoopPacket),
            },
            ActionEntry {
                id: "devctl_security",
                label: "security",
                category: ActionCategory::ReadOnly,
                dev_command: Some(DevCommandKind::Security),
            },
            ActionEntry {
                id: "devctl_review_channel_dry_run",
                label: "swarm-dry-run",
                category: ActionCategory::ReadOnly,
                dev_command: Some(DevCommandKind::ReviewLaunchDryRun),
            },
            ActionEntry {
                id: "devctl_review_channel_launch",
                label: "start-swarm",
                category: ActionCategory::Mutating,
                dev_command: Some(DevCommandKind::ReviewLaunchLive),
            },
            ActionEntry {
                id: "devctl_review_channel_rollover",
                label: "swarm-rollover",
                category: ActionCategory::Mutating,
                dev_command: Some(DevCommandKind::ReviewRollover),
            },
            ActionEntry {
                id: "devctl_controller_pause",
                label: "pause-loop",
                category: ActionCategory::Mutating,
                dev_command: Some(DevCommandKind::PauseLoop),
            },
            ActionEntry {
                id: "devctl_controller_resume",
                label: "resume-loop",
                category: ActionCategory::Mutating,
                dev_command: Some(DevCommandKind::ResumeLoop),
            },
            ActionEntry {
                id: "devctl_sync",
                label: "sync",
                category: ActionCategory::Mutating,
                dev_command: Some(DevCommandKind::Sync),
            },
            ActionEntry {
                id: "devctl_process_audit",
                label: "process-audit",
                category: ActionCategory::ReadOnly,
                dev_command: Some(DevCommandKind::ProcessAudit),
            },
            ActionEntry {
                id: "devctl_process_watch",
                label: "process-watch",
                category: ActionCategory::ReadOnly,
                dev_command: Some(DevCommandKind::ProcessWatch),
            },
            ActionEntry {
                id: "devctl_process_cleanup",
                label: "process-cleanup",
                category: ActionCategory::Mutating,
                dev_command: Some(DevCommandKind::ProcessCleanup),
            },
        ]
    }

    /// Build the default catalog with the current devctl command set.
    pub(crate) fn default_catalog() -> Self {
        // Keep the stricter approval category compiled until a real
        // operator-owned write action lands in the catalog.
        let _reserved_operator_approval_category = ActionCategory::OperatorApproval;
        let entries = Self::default_entries();
        debug_assert_eq!(entries.len(), Self::DEFAULT_LEN);
        debug_assert_eq!(
            entries
                .iter()
                .map(|entry| entry.id)
                .collect::<std::collections::BTreeSet<_>>()
                .len(),
            entries.len(),
            "action ids should remain unique"
        );
        Self { entries }
    }

    pub(crate) fn entries(&self) -> &[ActionEntry] {
        &self.entries
    }

    pub(crate) fn len(&self) -> usize {
        self.entries.len()
    }

    pub(crate) fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    pub(crate) fn get(&self, index: usize) -> Option<&ActionEntry> {
        self.entries.get(index)
    }

    #[cfg(test)]
    pub(crate) fn find_by_id(&self, id: &str) -> Option<(usize, &ActionEntry)> {
        self.entries.iter().enumerate().find(|(_, e)| e.id == id)
    }

    #[cfg(test)]
    pub(crate) fn find_by_dev_command(
        &self,
        kind: DevCommandKind,
    ) -> Option<(usize, &ActionEntry)> {
        self.entries
            .iter()
            .enumerate()
            .find(|(_, e)| e.dev_command == Some(kind))
    }
}
