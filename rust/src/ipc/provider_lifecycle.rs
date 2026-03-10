//! IPC provider lifecycle adapter helpers.
//!
//! This module centralizes provider-specific start/cancel/drain behavior so
//! router/session code paths do not duplicate codex/claude lifecycle matches.

use crate::codex::{CodexBackendError, CodexJobRunner, CodexRequest};

use super::protocol::{IpcEvent, Provider, ProviderLifecycle};
use super::session::{
    process_claude_events, process_codex_events, send_event, start_claude_job, ActiveJob, IpcState,
};

pub(super) fn start_provider_job(state: &mut IpcState, provider: Provider, prompt: &str) {
    send_event(&IpcEvent::JobStart {
        provider: provider.as_str().to_string(),
    });

    match provider.lifecycle() {
        ProviderLifecycle::CodexCli => {
            let request = CodexRequest::chat(prompt.to_string());
            match state.codex_cli_backend.start(request) {
                Ok(job) => {
                    state.current_job = Some(ActiveJob::Codex(job));
                }
                Err(err) => {
                    let error = match err {
                        CodexBackendError::InvalidRequest(reason) => reason.to_string(),
                        CodexBackendError::BackendDisabled(reason) => reason,
                    };
                    send_provider_job_error(provider, error);
                }
            }
        }
        ProviderLifecycle::ClaudeCli => match start_claude_job(
            &state.claude_cmd,
            prompt,
            state.config.claude_skip_permissions,
            &state.config.term_value,
        ) {
            Ok(job) => {
                state.current_job = Some(ActiveJob::Claude(job));
            }
            Err(err) => {
                send_provider_job_error(provider, err.to_string());
            }
        },
    }
}

pub(super) fn drain_active_provider_job(state: &mut IpcState, cancelled: bool) {
    let job_finished = match state.current_job.as_mut() {
        Some(ActiveJob::Codex(codex_job)) => process_codex_events(codex_job, cancelled),
        Some(ActiveJob::Claude(claude_job)) => process_claude_events(claude_job, cancelled),
        None => false,
    };

    if job_finished {
        state.current_job = None;
    }
}

pub(super) fn cancel_active_provider_job(state: &mut IpcState) -> Option<Provider> {
    let job = state.current_job.take()?;
    let provider = match job {
        ActiveJob::Codex(job) => {
            state.codex_cli_backend.cancel(job.id);
            Provider::Codex
        }
        ActiveJob::Claude(mut job) => {
            job.cancel();
            Provider::Claude
        }
    };
    Some(provider)
}

fn send_provider_job_error(provider: Provider, error: String) {
    send_event(&IpcEvent::JobEnd {
        provider: provider.as_str().to_string(),
        success: false,
        error: Some(error),
    });
}
