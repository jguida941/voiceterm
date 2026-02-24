//! Non-blocking IPC event processors for backend, voice, and auth jobs.

mod auth;
mod claude;
mod codex;
mod voice;

use super::{ClaudeJob, CodexJob, IpcState};
use crate::voice::VoiceJob;

pub(super) fn process_codex_events(job: &mut CodexJob, cancelled: bool) -> bool {
    codex::process_codex_events(job, cancelled)
}

pub(super) fn process_claude_events(job: &mut ClaudeJob, cancelled: bool) -> bool {
    claude::process_claude_events(job, cancelled)
}

pub(super) fn process_voice_events(job: &VoiceJob, cancelled: bool) -> bool {
    voice::process_voice_events(job, cancelled)
}

pub(super) fn process_auth_events(state: &mut IpcState) -> bool {
    auth::process_auth_events(state)
}
