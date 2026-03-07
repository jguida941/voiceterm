use super::profile::RuntimeProfile;
use crate::runtime_compat::{RuntimeVariant, TerminalHost};
use std::mem;
use std::time::Instant;

#[derive(Debug, Clone)]
pub(super) enum WriterAdapterState {
    JetBrainsClaude(JetBrainsClaudeWriterState),
    JetBrainsCodex(JetBrainsCodexWriterState),
    CursorClaude(CursorClaudeWriterState),
    Generic(GenericWriterState),
}

#[derive(Debug, Clone, Default)]
pub(super) struct JetBrainsClaudeWriterState {
    pub(super) dec_cursor_saved_active: bool,
    pub(super) ansi_cursor_saved_active: bool,
    pub(super) cursor_restore_settle_until: Option<Instant>,
    pub(super) cursor_escape_carry: Vec<u8>,
    pub(super) composer_repair_due: Option<Instant>,
    pub(super) repair_skip_quiet_window: bool,
    pub(super) resize_repair_until: Option<Instant>,
    pub(super) startup_screen_clear_pending: bool,
    pub(super) last_destructive_clear_repaint_at: Option<Instant>,
}

#[derive(Debug, Clone, Default)]
pub(super) struct JetBrainsCodexWriterState;

#[derive(Debug, Clone)]
pub(super) struct CursorClaudeWriterState {
    pub(super) input_repair_due: Option<Instant>,
    pub(super) startup_screen_clear_pending: bool,
    pub(super) startup_scroll_preclear_pending: bool,
}

impl Default for CursorClaudeWriterState {
    fn default() -> Self {
        Self {
            input_repair_due: None,
            startup_screen_clear_pending: true,
            startup_scroll_preclear_pending: true,
        }
    }
}

#[derive(Debug, Clone, Default)]
pub(super) struct GenericWriterState {
    pub(super) cursor_startup_screen_clear_pending: bool,
}

impl WriterAdapterState {
    pub(super) fn for_runtime_profile(profile: RuntimeProfile) -> Self {
        match profile.runtime_variant {
            RuntimeVariant::JetBrainsClaude => Self::JetBrainsClaude(JetBrainsClaudeWriterState {
                startup_screen_clear_pending: true,
                ..JetBrainsClaudeWriterState::default()
            }),
            RuntimeVariant::JetBrainsCodex => Self::JetBrainsCodex(JetBrainsCodexWriterState),
            RuntimeVariant::CursorClaude => Self::CursorClaude(CursorClaudeWriterState::default()),
            RuntimeVariant::Generic => Self::Generic(GenericWriterState {
                cursor_startup_screen_clear_pending: profile.terminal_family
                    == TerminalHost::Cursor,
            }),
        }
    }

    #[cfg(test)]
    pub(super) fn cursor_startup_screen_clear_pending(&self) -> bool {
        match self {
            Self::CursorClaude(state) => state.startup_screen_clear_pending,
            Self::Generic(state) => state.cursor_startup_screen_clear_pending,
            Self::JetBrainsClaude(_) | Self::JetBrainsCodex(_) => false,
        }
    }

    pub(super) fn take_cursor_startup_screen_clear_pending(&mut self) -> bool {
        match self {
            Self::CursorClaude(state) => mem::take(&mut state.startup_screen_clear_pending),
            Self::Generic(state) => mem::take(&mut state.cursor_startup_screen_clear_pending),
            Self::JetBrainsClaude(_) | Self::JetBrainsCodex(_) => false,
        }
    }

    pub(super) fn cursor_startup_scroll_preclear_pending(&self) -> bool {
        match self {
            Self::CursorClaude(state) => state.startup_scroll_preclear_pending,
            Self::JetBrainsClaude(_) | Self::JetBrainsCodex(_) | Self::Generic(_) => false,
        }
    }

    pub(super) fn set_cursor_startup_scroll_preclear_pending(&mut self, pending: bool) {
        if let Self::CursorClaude(state) = self {
            state.startup_scroll_preclear_pending = pending;
        }
    }

    pub(super) fn cursor_claude_input_repair_due(&self) -> Option<Instant> {
        match self {
            Self::CursorClaude(state) => state.input_repair_due,
            Self::JetBrainsClaude(_) | Self::JetBrainsCodex(_) | Self::Generic(_) => None,
        }
    }

    pub(super) fn set_cursor_claude_input_repair_due(&mut self, due: Option<Instant>) {
        if let Self::CursorClaude(state) = self {
            state.input_repair_due = due;
        }
    }

    pub(super) fn jetbrains_dec_cursor_saved_active(&self) -> bool {
        match self {
            Self::JetBrainsClaude(state) => state.dec_cursor_saved_active,
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => false,
        }
    }

    pub(super) fn set_jetbrains_dec_cursor_saved_active(&mut self, active: bool) {
        if let Self::JetBrainsClaude(state) = self {
            state.dec_cursor_saved_active = active;
        }
    }

    pub(super) fn jetbrains_ansi_cursor_saved_active(&self) -> bool {
        match self {
            Self::JetBrainsClaude(state) => state.ansi_cursor_saved_active,
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => false,
        }
    }

    pub(super) fn set_jetbrains_ansi_cursor_saved_active(&mut self, active: bool) {
        if let Self::JetBrainsClaude(state) = self {
            state.ansi_cursor_saved_active = active;
        }
    }

    pub(super) fn jetbrains_cursor_restore_settle_until(&self) -> Option<Instant> {
        match self {
            Self::JetBrainsClaude(state) => state.cursor_restore_settle_until,
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => None,
        }
    }

    pub(super) fn set_jetbrains_cursor_restore_settle_until(&mut self, until: Option<Instant>) {
        if let Self::JetBrainsClaude(state) = self {
            state.cursor_restore_settle_until = until;
        }
    }

    pub(super) fn jetbrains_cursor_escape_carry(&self) -> &[u8] {
        match self {
            Self::JetBrainsClaude(state) => state.cursor_escape_carry.as_slice(),
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => &[],
        }
    }

    pub(super) fn set_jetbrains_cursor_escape_carry(&mut self, carry: Vec<u8>) {
        if let Self::JetBrainsClaude(state) = self {
            state.cursor_escape_carry = carry;
        }
    }

    pub(super) fn clear_jetbrains_cursor_escape_carry(&mut self) {
        if let Self::JetBrainsClaude(state) = self {
            state.cursor_escape_carry.clear();
        }
    }

    pub(super) fn jetbrains_claude_composer_repair_due(&self) -> Option<Instant> {
        match self {
            Self::JetBrainsClaude(state) => state.composer_repair_due,
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => None,
        }
    }

    pub(super) fn set_jetbrains_claude_composer_repair_due(&mut self, due: Option<Instant>) {
        if let Self::JetBrainsClaude(state) = self {
            state.composer_repair_due = due;
        }
    }

    pub(super) fn jetbrains_claude_repair_skip_quiet_window(&self) -> bool {
        match self {
            Self::JetBrainsClaude(state) => state.repair_skip_quiet_window,
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => false,
        }
    }

    pub(super) fn set_jetbrains_claude_repair_skip_quiet_window(&mut self, skip_quiet: bool) {
        if let Self::JetBrainsClaude(state) = self {
            state.repair_skip_quiet_window = skip_quiet;
        }
    }

    pub(super) fn jetbrains_claude_resize_repair_until(&self) -> Option<Instant> {
        match self {
            Self::JetBrainsClaude(state) => state.resize_repair_until,
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => None,
        }
    }

    pub(super) fn set_jetbrains_claude_resize_repair_until(&mut self, until: Option<Instant>) {
        if let Self::JetBrainsClaude(state) = self {
            state.resize_repair_until = until;
        }
    }

    #[cfg(test)]
    pub(super) fn jetbrains_claude_startup_screen_clear_pending(&self) -> bool {
        match self {
            Self::JetBrainsClaude(state) => state.startup_screen_clear_pending,
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => false,
        }
    }

    pub(super) fn take_jetbrains_claude_startup_screen_clear_pending(&mut self) -> bool {
        match self {
            Self::JetBrainsClaude(state) => mem::take(&mut state.startup_screen_clear_pending),
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => false,
        }
    }

    pub(super) fn jetbrains_claude_last_destructive_clear_repaint_at(&self) -> Option<Instant> {
        match self {
            Self::JetBrainsClaude(state) => state.last_destructive_clear_repaint_at,
            Self::JetBrainsCodex(_) | Self::CursorClaude(_) | Self::Generic(_) => None,
        }
    }

    pub(super) fn set_jetbrains_claude_last_destructive_clear_repaint_at(
        &mut self,
        at: Option<Instant>,
    ) {
        if let Self::JetBrainsClaude(state) = self {
            state.last_destructive_clear_repaint_at = at;
        }
    }
}
