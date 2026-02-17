//! IPC loop runtime helpers for command dispatch, event draining, and exit policy.

use super::super::protocol::IpcCommand;
use super::super::router::{
    handle_auth_command, handle_cancel, handle_send_prompt, handle_set_provider, handle_start_voice,
};
use super::{
    process_auth_events, process_claude_events, process_codex_events, process_voice_events,
    ActiveJob, IpcState,
};

pub(super) fn handle_command(state: &mut IpcState, cmd: IpcCommand) {
    state.cancelled = false;

    match cmd {
        IpcCommand::SendPrompt { prompt, provider } => {
            handle_send_prompt(state, &prompt, provider);
        }
        IpcCommand::StartVoice => {
            handle_start_voice(state);
        }
        IpcCommand::Cancel => {
            handle_cancel(state);
        }
        IpcCommand::SetProvider { provider } => {
            handle_set_provider(state, &provider);
        }
        IpcCommand::Auth { provider } => {
            handle_auth_command(state, provider);
        }
        IpcCommand::GetCapabilities => {
            state.emit_capabilities();
        }
    }
}

pub(super) fn drain_active_jobs(state: &mut IpcState) {
    let provider_job_finished = match state.current_job.as_mut() {
        Some(ActiveJob::Codex(codex_job)) => process_codex_events(codex_job, state.cancelled),
        Some(ActiveJob::Claude(claude_job)) => process_claude_events(claude_job, state.cancelled),
        None => false,
    };
    if provider_job_finished {
        state.current_job = None;
    }

    let voice_job_finished = match state.current_voice_job.as_ref() {
        Some(voice_job) => process_voice_events(voice_job, state.cancelled),
        None => false,
    };
    if voice_job_finished {
        state.current_voice_job = None;
    }

    if process_auth_events(state) {
        state.current_auth_job = None;
    }
}

pub(super) fn should_exit(state: &IpcState) -> bool {
    state.exit_requested
        && state.current_job.is_none()
        && state.current_voice_job.is_none()
        && state.current_auth_job.is_none()
}
