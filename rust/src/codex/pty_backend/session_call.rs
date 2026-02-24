use super::super::backend::{CancelToken, CodexCallError};
use super::output_sanitize::sanitize_pty_output;
use crate::{log_debug, pty_session::PtyCliSession};
use anyhow::{anyhow, Context, Result};
use std::time::{Duration, Instant};

// Codex is an AI that takes seconds to respond, not milliseconds.
// These timeouts must stay realistic for AI response times.
#[cfg(test)]
const PTY_FIRST_BYTE_TIMEOUT_MS: u64 = 500;
#[cfg(not(test))]
const PTY_FIRST_BYTE_TIMEOUT_MS: u64 = 3000; // 3s for first byte - fail fast if PTY not working.
#[cfg(test)]
const PTY_OVERALL_TIMEOUT_MS: u64 = 5000;
#[cfg(not(test))]
const PTY_OVERALL_TIMEOUT_MS: u64 = 60000; // 60s overall for long responses.
#[cfg(test)]
const PTY_QUIET_GRACE_MS: u64 = 200;
#[cfg(not(test))]
const PTY_QUIET_GRACE_MS: u64 = 2000; // 2s quiet period.
const PTY_POLL_INTERVAL_MS: u64 = 50;
const PTY_CONTROL_ONLY_TIMEOUT_MS: u64 = 5000;
const PTY_MAX_OUTPUT_BYTES: usize = 2 * 1024 * 1024;

pub(in crate::codex) fn duration_ms(duration: Duration) -> f64 {
    duration.as_secs_f64() * 1000.0
}

pub(in crate::codex) fn compute_deadline(start: Instant, timeout: Duration) -> Instant {
    start + timeout
}

pub(in crate::codex) fn should_accept_printable(
    has_printable: bool,
    idle_since_raw: Duration,
    quiet_grace: Duration,
) -> bool {
    has_printable && idle_since_raw >= quiet_grace
}

pub(in crate::codex) fn should_fail_control_only(
    has_printable: bool,
    idle_since_printable: Duration,
    control_only_timeout: Duration,
) -> bool {
    !has_printable && idle_since_printable >= control_only_timeout
}

pub(in crate::codex) fn should_break_overall(elapsed: Duration, overall_timeout: Duration) -> bool {
    elapsed >= overall_timeout
}

pub(in crate::codex) fn first_output_timed_out(now: Instant, deadline: Instant) -> bool {
    now >= deadline
}

#[derive(Default)]
pub(in crate::codex) struct SanitizedOutputCache {
    text: String,
    dirty: bool,
    #[cfg(test)]
    refresh_count: usize,
}

impl SanitizedOutputCache {
    pub(in crate::codex) fn mark_dirty(&mut self) {
        self.dirty = true;
    }

    pub(in crate::codex) fn sanitized<'a>(&'a mut self, raw: &[u8]) -> &'a str {
        if self.dirty {
            self.text = sanitize_pty_output(raw);
            self.dirty = false;
            #[cfg(test)]
            {
                self.refresh_count += 1;
            }
        }
        &self.text
    }

    #[cfg(test)]
    pub(in crate::codex) fn refresh_count(&self) -> usize {
        self.refresh_count
    }
}

pub(in crate::codex) trait CodexSession {
    fn send(&mut self, text: &str) -> Result<()>;
    fn read_output_timeout(&self, timeout: Duration) -> Vec<Vec<u8>>;
}

impl CodexSession for PtyCliSession {
    fn send(&mut self, text: &str) -> Result<()> {
        PtyCliSession::send(self, text)
    }

    fn read_output_timeout(&self, timeout: Duration) -> Vec<Vec<u8>> {
        PtyCliSession::read_output_timeout(self, timeout)
    }
}

pub(in crate::codex) fn call_codex_via_session<S: CodexSession>(
    session: &mut S,
    prompt: &str,
    cancel: &CancelToken,
) -> Result<String, CodexCallError> {
    session
        .send(prompt)
        .context("failed to write prompt to persistent Codex session")?;

    let mut combined_raw = Vec::new();
    let mut sanitized_cache = SanitizedOutputCache::default();
    let mut truncated_output = false;
    let start_time = Instant::now();
    let overall_timeout = Duration::from_millis(PTY_OVERALL_TIMEOUT_MS);
    let first_output_deadline =
        compute_deadline(start_time, Duration::from_millis(PTY_FIRST_BYTE_TIMEOUT_MS));
    let quiet_grace = Duration::from_millis(PTY_QUIET_GRACE_MS);
    let control_only_timeout = Duration::from_millis(PTY_CONTROL_ONLY_TIMEOUT_MS);
    let mut last_printable_output = start_time;
    let mut last_raw_output = start_time;

    loop {
        if cancel.is_cancelled() {
            return Err(CodexCallError::Cancelled);
        }

        let output_chunks =
            session.read_output_timeout(Duration::from_millis(PTY_POLL_INTERVAL_MS));
        for chunk in output_chunks {
            if chunk.is_empty() {
                continue;
            }
            combined_raw.extend_from_slice(&chunk);
            if combined_raw.len() > PTY_MAX_OUTPUT_BYTES {
                let excess = combined_raw.len() - PTY_MAX_OUTPUT_BYTES;
                combined_raw = combined_raw.split_off(excess);
                if !truncated_output {
                    log_debug("Persistent Codex session output exceeded cap; truncating");
                    truncated_output = true;
                }
            }
            sanitized_cache.mark_dirty();
            last_raw_output = Instant::now();
        }

        let now = Instant::now();

        if !combined_raw.is_empty() {
            let sanitized = sanitized_cache.sanitized(&combined_raw);
            let has_printable = !sanitized.trim().is_empty();

            if has_printable {
                last_printable_output = now;
            }

            let idle_since_raw = now.duration_since(last_raw_output);
            let idle_since_printable = now.duration_since(last_printable_output);

            // Success: got printable output and no new data for quiet_grace period.
            if should_accept_printable(has_printable, idle_since_raw, quiet_grace) {
                return Ok(sanitized.to_owned());
            }

            // Fail fast: raw output but no printable content for control_only_timeout.
            if should_fail_control_only(has_printable, idle_since_printable, control_only_timeout) {
                log_debug("Persistent Codex session produced only control sequences; falling back");
                return Err(CodexCallError::Failure(anyhow!(
                    "persistent Codex session produced no printable output"
                )));
            }

            // Overall timeout with output.
            if should_break_overall(now.duration_since(start_time), overall_timeout) {
                if has_printable {
                    return Ok(sanitized.to_owned());
                }
                break;
            }
        } else {
            // No output yet - check first byte timeout.
            if first_output_timed_out(now, first_output_deadline) {
                log_debug(&format!(
                    "Persistent Codex session produced no output within {PTY_FIRST_BYTE_TIMEOUT_MS}ms; falling back"
                ));
                return Err(CodexCallError::Failure(anyhow!(
                    "persistent Codex session timed out before producing output"
                )));
            }
            if should_break_overall(now.duration_since(start_time), overall_timeout) {
                break;
            }
        }
    }

    log_debug("Persistent Codex session yielded no printable output; falling back");
    Err(CodexCallError::Failure(anyhow!(
        "persistent Codex session returned no text"
    )))
}
