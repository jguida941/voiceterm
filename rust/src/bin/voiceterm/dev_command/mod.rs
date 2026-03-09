//! Dev-only command broker and panel state for control-plane actions.

use std::time::Duration;

mod action_catalog;
mod broker;
mod command_state;
mod review_artifact;

pub(crate) use action_catalog::*;
pub(crate) use broker::DevCommandBroker;
pub(crate) use broker::{devctl_script_path, find_devctl_root};
pub(crate) use command_state::{
    DevPanelState, GitStatusSnapshot, HandoffSnapshot, MemoryCockpitSnapshot, MemoryPreviewSection,
    MemoryStatusSnapshot, OpsSnapshot, OpsTriageSnapshot, ProcessAuditSnapshot,
    RuntimeDiagnosticsSnapshot,
};
pub(crate) use review_artifact::*;

// Private re-imports so `tests.rs` can reach broker helpers via `use super::*;`.
#[cfg(test)]
use broker::{excerpt, parse_terminal_packet, summarize_json};

const DEV_COMMAND_POLL_INTERVAL: Duration = Duration::from_millis(25);
const DEV_COMMAND_TIMEOUT: Duration = Duration::from_secs(90);
const OUTPUT_EXCERPT_MAX_CHARS: usize = 180;
const TERMINAL_PACKET_ID_MAX_CHARS: usize = 64;
const TERMINAL_PACKET_DRAFT_MAX_CHARS: usize = 1600;

/// Truncate a string to at most `max_chars` Unicode characters, appending "..."
/// if the input was longer. Shared by broker and command_state.
fn truncate_chars(value: &str, max_chars: usize) -> String {
    let mut chars = value.chars();
    let truncated: String = chars.by_ref().take(max_chars).collect();
    if chars.next().is_some() {
        format!("{truncated}...")
    } else {
        truncated
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum DevCommandKind {
    Status,
    Report,
    Triage,
    ProcessAudit,
    ProcessWatch,
    LoopPacket,
    Security,
    ReviewLaunchDryRun,
    ReviewLaunchLive,
    ReviewRollover,
    PauseLoop,
    ResumeLoop,
    ProcessCleanup,
    Sync,
}

impl DevCommandKind {
    #[cfg(test)]
    pub(crate) const ALL: [Self; 14] = [
        Self::Status,
        Self::Report,
        Self::Triage,
        Self::ProcessAudit,
        Self::ProcessWatch,
        Self::LoopPacket,
        Self::Security,
        Self::ReviewLaunchDryRun,
        Self::ReviewLaunchLive,
        Self::ReviewRollover,
        Self::PauseLoop,
        Self::ResumeLoop,
        Self::ProcessCleanup,
        Self::Sync,
    ];

    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Status => "status",
            Self::Report => "report",
            Self::Triage => "triage",
            Self::ProcessAudit => "process-audit",
            Self::ProcessWatch => "process-watch",
            Self::LoopPacket => "loop-packet",
            Self::Security => "security",
            Self::ReviewLaunchDryRun => "swarm-dry-run",
            Self::ReviewLaunchLive => "start-swarm",
            Self::ReviewRollover => "swarm-rollover",
            Self::PauseLoop => "pause-loop",
            Self::ResumeLoop => "resume-loop",
            Self::ProcessCleanup => "process-cleanup",
            Self::Sync => "sync",
        }
    }

    #[cfg(test)]
    pub(crate) fn is_mutating(self) -> bool {
        matches!(
            self,
            Self::ReviewLaunchLive
                | Self::ReviewRollover
                | Self::PauseLoop
                | Self::ResumeLoop
                | Self::ProcessCleanup
                | Self::Sync
        )
    }

    fn devctl_args(self) -> &'static [&'static str] {
        match self {
            Self::Status => &["status", "--ci", "--format", "json"],
            Self::Report => &["report", "--ci", "--format", "json"],
            Self::Triage => &["triage", "--ci", "--format", "json", "--no-cihub"],
            Self::ProcessAudit => &["process-audit", "--strict", "--format", "json"],
            Self::ProcessWatch => &[
                "process-watch",
                "--strict",
                "--iterations",
                "3",
                "--interval-seconds",
                "5",
                "--stop-on-clean",
                "--format",
                "json",
            ],
            Self::LoopPacket => &["loop-packet", "--format", "json"],
            Self::Security => &["security", "--format", "json", "--offline"],
            Self::ReviewLaunchDryRun => &[
                "review-channel",
                "--action",
                "launch",
                "--terminal",
                "none",
                "--dry-run",
                "--format",
                "json",
            ],
            Self::ReviewLaunchLive => &["review-channel", "--action", "launch", "--format", "json"],
            Self::ReviewRollover => &[
                "review-channel",
                "--action",
                "rollover",
                "--rollover-threshold-pct",
                "50",
                "--await-ack-seconds",
                "60",
                "--format",
                "json",
            ],
            Self::PauseLoop => &[
                "controller-action",
                "--action",
                "pause-loop",
                "--format",
                "json",
            ],
            Self::ResumeLoop => &[
                "controller-action",
                "--action",
                "resume-loop",
                "--format",
                "json",
            ],
            Self::ProcessCleanup => &["process-cleanup", "--verify", "--format", "json"],
            Self::Sync => &["sync", "--format", "json"],
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum DevCommandStatus {
    Success,
    Failed,
    Cancelled,
    TimedOut,
    JsonError,
    SpawnError,
    Rejected,
}

impl DevCommandStatus {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Success => "ok",
            Self::Failed => "failed",
            Self::Cancelled => "cancelled",
            Self::TimedOut => "timeout",
            Self::JsonError => "json-error",
            Self::SpawnError => "spawn-error",
            Self::Rejected => "rejected",
        }
    }
}

#[derive(Debug, Clone)]
pub(crate) struct DevCommandCompletion {
    pub(crate) request_id: u64,
    pub(crate) command: DevCommandKind,
    pub(crate) status: DevCommandStatus,
    pub(crate) duration_ms: u64,
    pub(crate) summary: String,
    pub(crate) stdout_excerpt: Option<String>,
    pub(crate) stderr_excerpt: Option<String>,
    pub(crate) terminal_packet: Option<DevTerminalPacket>,
}

#[derive(Debug, Clone)]
pub(crate) struct DevTerminalPacket {
    pub(crate) packet_id: String,
    pub(crate) source_command: String,
    pub(crate) draft_text: String,
    pub(crate) auto_send: bool,
}

#[derive(Debug, Clone)]
pub(crate) enum DevCommandUpdate {
    Started {
        request_id: u64,
        command: DevCommandKind,
    },
    Completed(DevCommandCompletion),
}

#[cfg(test)]
mod tests;
