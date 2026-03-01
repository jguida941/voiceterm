//! PTY-backed Codex runner so interactive sessions can stream structured events.

use super::backend::{
    BoundedEventQueue, CancelToken, CodexBackendError, CodexJob, CodexJobRunner, CodexRequest,
    EventSender, JobId, RequestMode, RequestPayload, BACKEND_EVENT_CAPACITY,
};
use crate::{config::AppConfig, lock_or_recover, log_debug, pty_session::PtyCliSession};
use anyhow::{anyhow, Result};
use std::{
    collections::HashMap,
    env,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        mpsc, Arc, Mutex,
    },
    thread,
    time::Duration,
};
mod job_flow;
mod output_sanitize;
mod session_call;
#[cfg(test)]
mod test_support;

#[cfg(test)]
pub(super) use output_sanitize::{
    clamp_line_start, current_line_start, find_csi_sequence, init_guard, normalize_control_bytes,
    pop_last_codepoint, skip_osc_sequence, step_guard,
};
pub use output_sanitize::{prepare_for_display, sanitize_pty_output};
#[cfg(test)]
pub(super) use session_call::{
    call_codex_via_session, compute_deadline, duration_ms, first_output_timed_out,
    should_accept_printable, should_break_overall, should_fail_control_only, CodexSession,
    SanitizedOutputCache,
};
#[cfg(test)]
pub(crate) use test_support::{
    active_backend_threads, reset_session_count, reset_session_count_reset, with_job_hook,
};

// Codex is an AI that takes seconds to respond, not milliseconds
// These timeouts must be realistic for AI response times
const PTY_HEALTHCHECK_TIMEOUT_MS: u64 = 5000; // 5s health check (was 2000ms)

/// Default CLI/PTY backend implementation driving the `codex` binary.
pub struct CodexCliBackend {
    config: AppConfig,
    working_dir: PathBuf,
    next_job_id: AtomicU64,
    pub(super) state: Arc<Mutex<CodexCliBackendState>>,
    pub(super) cancel_tokens: Arc<Mutex<HashMap<JobId, CancelToken>>>,
}

pub(super) struct CodexCliBackendState {
    pub(super) codex_session: Option<PtyCliSession>,
    pub(super) pty_disabled: bool,
}

impl CodexCliBackend {
    /// Build a backend instance using the provided validated app config.
    #[must_use]
    pub fn new(config: AppConfig) -> Self {
        let working_dir = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        let state = CodexCliBackendState {
            codex_session: None,
            pty_disabled: !config.persistent_codex,
        };
        Self {
            config,
            working_dir,
            next_job_id: AtomicU64::new(0),
            state: Arc::new(Mutex::new(state)),
            cancel_tokens: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub(super) fn take_codex_session_for_job(&self) -> Option<PtyCliSession> {
        if !self.config.persistent_codex {
            return None;
        }
        let mut state = lock_or_recover(&self.state, "CodexCliBackend::take_codex_session_for_job");
        if state.pty_disabled {
            return None;
        }
        if state.codex_session.is_none() {
            if let Err(err) = self.ensure_codex_session(&mut state) {
                log_debug(&format!(
                    "CodexCliBackend: persistent Codex unavailable: {err:#}"
                ));
                state.pty_disabled = true;
                return None;
            }
        }
        state.codex_session.take()
    }

    pub(super) fn ensure_codex_session(&self, state: &mut CodexCliBackendState) -> Result<()> {
        let working_dir = self.working_dir.clone();
        let wd_str = working_dir.to_str().unwrap_or(".");
        log_debug(&format!(
            "Attempting to create PTY session with codex_cmd={}, working_dir={}",
            self.config.codex_cmd, wd_str
        ));

        let pty_args = build_persistent_session_args(wd_str, &self.config.codex_args);

        match PtyCliSession::new(
            &self.config.codex_cmd,
            wd_str,
            &pty_args,
            &self.config.term_value,
            24,
            80,
        ) {
            Ok(mut session) => {
                log_debug("PTY session created, checking responsiveness...");
                let timeout = Duration::from_millis(PTY_HEALTHCHECK_TIMEOUT_MS);
                if session.is_responsive(timeout) {
                    state.codex_session = Some(session);
                    log_debug("CodexCliBackend: persistent PTY session ready and responsive");
                    Ok(())
                } else {
                    log_debug("PTY health check failed - session unresponsive");
                    Err(anyhow!("persistent Codex unresponsive"))
                }
            }
            Err(err) => {
                log_debug(&format!("Failed to create PTY session: {err:#}"));
                Err(err.context("failed to start Codex PTY"))
            }
        }
    }
}

impl CodexJobRunner for CodexCliBackend {
    fn start(&self, request: CodexRequest) -> Result<CodexJob, CodexBackendError> {
        let mode = match &request.payload {
            RequestPayload::Chat { prompt } => {
                if prompt.trim().is_empty() {
                    return Err(CodexBackendError::InvalidRequest("Prompt is empty"));
                }
                RequestMode::Chat
            }
        };

        let job_id = self.next_job_id.fetch_add(1, Ordering::Relaxed) + 1;
        let queue = Arc::new(BoundedEventQueue::new(BACKEND_EVENT_CAPACITY));
        let queue_for_worker = Arc::clone(&queue);
        let (signal_tx, signal_rx) = mpsc::channel();
        let cancel_token = CancelToken::new();
        let cancel_for_worker = cancel_token.clone();
        let mut session_for_job = self.take_codex_session_for_job();
        let config = self.config.clone();
        let working_dir = self.working_dir.clone();
        let state = Arc::clone(&self.state);
        let cancel_registry = Arc::clone(&self.cancel_tokens);

        {
            let mut registry = lock_or_recover(&cancel_registry, "CodexCliBackend::start");
            registry.insert(job_id, cancel_token.clone());
        }

        let context = job_flow::JobContext {
            job_id,
            request,
            mode,
            config,
            working_dir,
        };
        let handle = thread::spawn(move || {
            #[cfg(test)]
            let _thread_guard = test_support::backend_thread_guard();
            let sender = EventSender::new(queue_for_worker, signal_tx);
            let outcome = job_flow::run_codex_job(
                context,
                session_for_job.take(),
                cancel_for_worker,
                &sender,
            );
            CodexCliBackend::cleanup_job(cancel_registry, job_id);
            CodexCliBackend::restore_static_state(
                state,
                outcome.codex_session,
                outcome.disable_pty,
            );
        });

        Ok(CodexJob::new(
            job_id,
            queue,
            signal_rx,
            handle,
            cancel_token,
        ))
    }

    fn cancel(&self, job_id: JobId) {
        let maybe_token = {
            let registry = lock_or_recover(&self.cancel_tokens, "CodexCliBackend::cancel");
            registry.get(&job_id).cloned()
        };
        if let Some(token) = maybe_token {
            token.cancel();
        }
    }

    fn working_dir(&self) -> &Path {
        &self.working_dir
    }
}

impl CodexCliBackend {
    pub(super) fn cleanup_job(registry: Arc<Mutex<HashMap<JobId, CancelToken>>>, job_id: JobId) {
        let mut registry = lock_or_recover(&registry, "CodexCliBackend::cleanup_job");
        registry.remove(&job_id);
    }

    /// Drop the cached PTY session so the next request can re-establish state.
    pub fn reset_session(&self) {
        #[cfg(test)]
        test_support::record_reset_session();
        let mut state = lock_or_recover(&self.state, "CodexCliBackend::reset_session");
        state.codex_session = None;
    }

    pub(super) fn restore_static_state(
        state: Arc<Mutex<CodexCliBackendState>>,
        session: Option<PtyCliSession>,
        disable_pty: bool,
    ) {
        let mut state = lock_or_recover(&state, "CodexCliBackend::restore_static_state");
        if disable_pty {
            state.pty_disabled = true;
            state.codex_session = None;
            return;
        }
        if let Some(session) = session {
            state.codex_session = Some(session);
        }
    }
}

fn build_persistent_session_args(working_dir: &str, codex_args: &[String]) -> Vec<String> {
    let mut args = Vec::with_capacity(codex_args.len() + 2);
    args.push("-C".to_string());
    args.push(working_dir.to_string());
    args.extend(codex_args.iter().cloned());
    args
}
