//! IPC session lifecycle orchestration for long-lived backend command execution.

use crate::codex::{sanitize_pty_output, CodexCliBackend, CodexEvent, CodexEventKind, CodexJob};
use crate::config::AppConfig;
use crate::pty_session::PtyCliSession;
use crate::voice::VoiceJob;
use crate::{audio, log_debug, log_debug_content, stt};
use anyhow::Result;
use std::sync::mpsc::{self, Receiver};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use super::protocol::{IpcCommand, IpcEvent, Provider};
mod auth_flow;
mod claude_job;
mod event_processing;
mod event_sink;
mod loop_control;
mod loop_runtime;
mod state;
mod stdin_reader;
#[cfg(any(test, feature = "mutants"))]
mod test_support;

// ============================================================================
// PTY toggle for tests/mutants so IPC paths can run without PTY dependencies.
// ============================================================================
#[cfg(any(test, feature = "mutants"))]
const USE_PTY: bool = false;
#[cfg(not(any(test, feature = "mutants")))]
const USE_PTY: bool = true;
const IPC_LOOP_WAIT_MS: u64 = 5;
#[cfg(any(test, feature = "mutants"))]
const AUTH_TIMEOUT: Duration = Duration::from_millis(50);
#[cfg(not(any(test, feature = "mutants")))]
const AUTH_TIMEOUT: Duration = Duration::from_secs(120);

// ============================================================================
// IPC state owned by the event loop.
// ============================================================================

pub(super) struct IpcState {
    pub(super) config: AppConfig,
    pub(super) active_provider: Provider,
    pub(super) codex_cli_backend: Arc<CodexCliBackend>,
    pub(super) claude_cmd: String,
    pub(super) recorder: Option<Arc<Mutex<audio::Recorder>>>,
    pub(super) transcriber: Option<Arc<Mutex<stt::Transcriber>>>,
    pub(super) current_job: Option<ActiveJob>,
    pub(super) current_voice_job: Option<VoiceJob>,
    pub(super) current_auth_job: Option<AuthJob>,
    pub(super) session_id: String,
    pub(super) cancelled: bool,
    pub(super) exit_requested: bool,
}

pub(super) enum ActiveJob {
    Codex(CodexJob),
    Claude(ClaudeJob),
}

pub(super) enum ClaudeJobOutput {
    Piped {
        child: std::process::Child,
        stdout_rx: Receiver<String>,
    },
    Pty {
        session: PtyCliSession,
    },
}

pub(super) struct ClaudeJob {
    pub(super) output: ClaudeJobOutput,
    #[allow(dead_code)]
    pub(super) started_at: Instant,
    pub(super) pending_exit: Option<std::process::ExitStatus>,
}

pub(super) type AuthResult = auth_flow::AuthResult;

pub(super) struct AuthJob {
    pub(super) provider: Provider,
    pub(super) receiver: Receiver<AuthResult>,
    #[allow(dead_code)]
    pub(super) started_at: Instant,
}

// ============================================================================
// Event sending
// ============================================================================

pub(super) fn send_event(event: &IpcEvent) {
    event_sink::send_event(event);
}

pub(super) fn utf8_prefix(text: &str, max_chars: usize) -> String {
    text.chars().take(max_chars).collect()
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn init_event_sink() {
    event_sink::init_event_sink();
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn ipc_loop_count_set(count: u64) {
    event_sink::ipc_loop_count_set(count);
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn ipc_loop_count_reset() {
    event_sink::ipc_loop_count_reset();
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn ipc_loop_count() -> u64 {
    event_sink::ipc_loop_count()
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn event_snapshot() -> usize {
    event_sink::event_snapshot()
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn events_since(start: usize) -> Vec<IpcEvent> {
    event_sink::events_since(start)
}

impl ClaudeJob {
    pub(super) fn cancel(&mut self) {
        match &mut self.output {
            ClaudeJobOutput::Piped { child, .. } => {
                terminate_piped_child(child);
            }
            ClaudeJobOutput::Pty { session } => {
                // Send graceful Ctrl+C first; PtyCliSession::drop will escalate to
                // SIGTERM → SIGKILL if the process ignores the interrupt.
                let _ = session.send("\u{3}");
            }
        }
    }
}

impl Drop for ClaudeJob {
    fn drop(&mut self) {
        // std::process::Child does NOT kill on drop; ensure the piped child is
        // always reaped so it cannot outlive the IPC session.
        // The PTY path is covered by PtyCliSession::drop → shutdown_pty_child.
        if let ClaudeJobOutput::Piped { child, .. } = &mut self.output {
            terminate_piped_child(child);
        }
    }
}

// ============================================================================
// Stdin Reader Thread
// ============================================================================

pub(super) fn terminate_piped_child(child: &mut std::process::Child) {
    claude_job::terminate_piped_child(child);
}

pub(super) fn start_claude_job(
    claude_cmd: &str,
    prompt: &str,
    skip_permissions: bool,
    term_value: &str,
) -> Result<ClaudeJob, String> {
    claude_job::start_claude_job(claude_cmd, prompt, skip_permissions, term_value, USE_PTY)
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn start_claude_job_with_pty(
    claude_cmd: &str,
    prompt: &str,
    skip_permissions: bool,
    term_value: &str,
) -> Result<ClaudeJob, String> {
    claude_job::start_claude_job(claude_cmd, prompt, skip_permissions, term_value, true)
}

// ============================================================================
// Auth Backend
// ============================================================================

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) type AuthFlowHook = auth_flow::AuthFlowHook;

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn set_auth_flow_hook(hook: Option<AuthFlowHook>) {
    auth_flow::set_auth_flow_hook(hook);
}

pub(super) fn run_auth_flow(provider: Provider, codex_cmd: &str, claude_cmd: &str) -> AuthResult {
    auth_flow::run_auth_flow(provider, codex_cmd, claude_cmd)
}

// ============================================================================
// Main Event Loop
// ============================================================================

/// Run newline-delimited JSON IPC mode until stdin closes or loop exits.
///
/// # Errors
///
/// Returns an error if IPC loop setup fails or any processing step in the main
/// loop returns a fatal error.
pub fn run_ipc_mode(config: AppConfig) -> Result<()> {
    log_debug("Starting JSON IPC mode (non-blocking)");

    let mut state = IpcState::new(config);

    // Emit capabilities on startup
    state.emit_capabilities();

    // Start stdin reader thread
    let (cmd_tx, cmd_rx) = mpsc::channel();
    #[cfg(any(test, feature = "mutants"))]
    {
        drop(cmd_tx);
        run_ipc_loop(&mut state, &cmd_rx, Some(10))
    }
    #[cfg(not(any(test, feature = "mutants")))]
    {
        let _stdin_handle = stdin_reader::spawn_stdin_reader(cmd_tx);
        run_ipc_loop(&mut state, &cmd_rx, None)
    }
}

#[cfg(any(test, feature = "mutants"))]
pub(super) fn ipc_guard_tripped(elapsed: Duration) -> bool {
    elapsed > Duration::from_secs(2)
}

pub(super) fn run_ipc_loop(
    state: &mut IpcState,
    cmd_rx: &Receiver<IpcCommand>,
    max_loops: Option<u64>,
) -> Result<()> {
    loop_control::run_ipc_loop(state, cmd_rx, max_loops)
}

pub(super) fn process_codex_events(job: &mut CodexJob, cancelled: bool) -> bool {
    event_processing::process_codex_events(job, cancelled)
}

pub(super) fn process_claude_events(job: &mut ClaudeJob, cancelled: bool) -> bool {
    event_processing::process_claude_events(job, cancelled)
}

pub(super) fn process_voice_events(job: &VoiceJob, cancelled: bool) -> bool {
    event_processing::process_voice_events(job, cancelled)
}

pub(super) fn process_auth_events(state: &mut IpcState) -> bool {
    event_processing::process_auth_events(state)
}
