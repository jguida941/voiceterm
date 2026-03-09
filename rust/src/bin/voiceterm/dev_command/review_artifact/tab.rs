/// Which tab is active inside the Dev panel overlay.
///
/// The cockpit pages form the operator cockpit (Phase 3.7.1):
///   Control  — read-only loop state, controller projections
///   Ops      — process hygiene and triage telemetry
///   Review   — code_audit.md lane view (parsed + raw)
///   Actions  — typed devctl action catalog and execution
///   Handoff  — fresh-conversation prompts and resume bundles
///   Memory   — structured memory/query/export previews
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub(crate) enum DevPanelTab {
    /// Read-only controller state / loop status.
    Control,
    /// Process hygiene and triage telemetry.
    Ops,
    /// Review artifact lane view.
    Review,
    /// Typed devctl action catalog.
    #[default]
    Actions,
    /// Cross-agent handoff prompts and resume bundles.
    Handoff,
    /// Memory status plus pack/query/export previews.
    Memory,
}

impl DevPanelTab {
    /// All tabs in display order, used for tab-bar rendering.
    pub(crate) const ALL: [Self; 6] = [
        Self::Control,
        Self::Ops,
        Self::Review,
        Self::Actions,
        Self::Handoff,
        Self::Memory,
    ];

    /// Cycle forward to the next tab (wraps around).
    pub(crate) fn next(self) -> Self {
        match self {
            Self::Control => Self::Ops,
            Self::Ops => Self::Review,
            Self::Review => Self::Actions,
            Self::Actions => Self::Handoff,
            Self::Handoff => Self::Memory,
            Self::Memory => Self::Control,
        }
    }

    /// Cycle backward to the previous tab (wraps around).
    pub(crate) fn prev(self) -> Self {
        match self {
            Self::Control => Self::Memory,
            Self::Ops => Self::Control,
            Self::Review => Self::Ops,
            Self::Actions => Self::Review,
            Self::Handoff => Self::Actions,
            Self::Memory => Self::Handoff,
        }
    }

    /// Short label for the tab bar and status messages.
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Control => "Control",
            Self::Ops => "Ops",
            Self::Review => "Review",
            Self::Actions => "Actions",
            Self::Handoff => "Handoff",
            Self::Memory => "Memory",
        }
    }
}
