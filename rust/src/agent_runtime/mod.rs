//! Agent CLI runtime used by benchmarks and provider-neutral output sanitization.

mod backend;
mod cli;
mod pty_backend;
#[cfg(test)]
mod tests;

/// Spinner frames used by the UI when a Codex request is inflight.
/// Uses Braille pattern characters for a smooth, modern animation.
pub const CODEX_SPINNER_FRAMES: &[&str] = &["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

pub use backend::{
    CodexBackendError, CodexEvent, CodexEventKind, CodexJob, CodexJobRunner, CodexJobStats,
    CodexRequest, JobId, RequestMode, RequestPayload,
};

pub use pty_backend::{prepare_for_display, sanitize_pty_output, CodexCliBackend};

#[cfg(test)]
pub(crate) use pty_backend::{active_backend_threads, with_job_hook};
