use super::super::backend::{
    CancelToken, CodexCallError, CodexEvent, CodexEventKind, CodexJobStats, CodexRequest,
    EventSender, JobId, RequestMode, RequestPayload,
};
use super::super::cli::call_codex_cli;
use super::session_call;
use super::{prepare_for_display, sanitize_pty_output};
use crate::{config::AppConfig, log_debug, pty_session::PtyCliSession};
use anyhow::Result;
use std::path::{Path, PathBuf};
use std::time::Instant;

pub(super) struct CodexRunOutcome {
    pub(super) codex_session: Option<PtyCliSession>,
    pub(super) disable_pty: bool,
}

pub(super) struct JobContext {
    pub(super) job_id: JobId,
    pub(super) request: CodexRequest,
    pub(super) mode: RequestMode,
    pub(super) config: AppConfig,
    pub(super) working_dir: PathBuf,
}

fn emit_canceled_event(sender: &EventSender, job_id: JobId, disable_pty: bool) {
    let _ = sender.emit(CodexEvent {
        job_id,
        kind: CodexEventKind::Canceled { disable_pty },
    });
}

fn emit_fatal_event(
    sender: &EventSender,
    job_id: JobId,
    phase: &'static str,
    message: String,
    disable_pty: bool,
) {
    let _ = sender.emit(CodexEvent {
        job_id,
        kind: CodexEventKind::FatalError {
            phase,
            message,
            disable_pty,
        },
    });
}

fn emit_recoverable_event(
    sender: &EventSender,
    job_id: JobId,
    phase: &'static str,
    message: String,
    retry_available: bool,
) {
    let _ = sender.emit(CodexEvent {
        job_id,
        kind: CodexEventKind::RecoverableError {
            phase,
            message,
            retry_available,
        },
    });
}

fn emit_started_event(sender: &EventSender, job_id: JobId, mode: RequestMode) -> bool {
    if sender
        .emit(CodexEvent {
            job_id,
            kind: CodexEventKind::Started { mode },
        })
        .is_err()
    {
        log_debug("CodexJobRunner: failed to emit Started event (queue overflow)");
        return false;
    }
    true
}

fn build_finished_lines(prompt: &str, output_text: &str) -> Vec<String> {
    // Always sanitize output - PTY has control chars, CLI is already clean (sanitize is no-op).
    let sanitized_output = sanitize_pty_output(output_text.as_bytes());
    let sanitized_lines = prepare_for_display(&sanitized_output);
    let mut lines = Vec::with_capacity(sanitized_lines.len() + 4);
    lines.push(format!("> {}", prompt.trim()));
    lines.push(String::new());
    lines.extend(sanitized_lines);
    lines.push(String::new());
    lines
}

fn log_codex_job_timing(
    job_id: JobId,
    stats: &CodexJobStats,
    line_count: usize,
    disable_pty: bool,
    log_timings_enabled: bool,
) {
    if !log_timings_enabled {
        return;
    }
    let total_ms = session_call::duration_ms(stats.finished_at.duration_since(stats.started_at));
    log_debug(&format!(
        "timing|phase=codex_job|job_id={job_id}|pty_attempts={}|cli_fallback={}|disable_pty={}|total_ms={total_ms:.1}|lines={line_count}",
        stats.pty_attempts, stats.cli_fallback_used, disable_pty
    ));
}

fn emit_finished_event(
    sender: &EventSender,
    job_id: JobId,
    prompt: &str,
    output_text: &str,
    mut stats: CodexJobStats,
    disable_pty: bool,
    log_timings_enabled: bool,
) {
    stats.finished_at = Instant::now();
    stats.bytes_transferred = output_text.len();
    stats.disable_pty = disable_pty;

    let lines = build_finished_lines(prompt, output_text);
    let line_count = lines.len();
    log_codex_job_timing(job_id, &stats, line_count, disable_pty, log_timings_enabled);

    let status = format!("Codex returned {line_count} lines.");
    let _ = sender.emit(CodexEvent {
        job_id,
        kind: CodexEventKind::Finished {
            lines,
            status,
            stats,
        },
    });
}

enum PersistentSessionOutput {
    Output(String),
    Canceled,
    FallbackToCli,
}

fn attempt_persistent_codex_output(
    outcome: &mut CodexRunOutcome,
    stats: &mut CodexJobStats,
    prompt: &str,
    cancel: &CancelToken,
    sender: &EventSender,
    job_id: JobId,
    persistent_enabled: bool,
) -> PersistentSessionOutput {
    if !persistent_enabled {
        return PersistentSessionOutput::FallbackToCli;
    }
    let Some(mut session) = outcome.codex_session.take() else {
        return PersistentSessionOutput::FallbackToCli;
    };

    stats.pty_attempts = 1;
    log_debug("CodexJobRunner: attempting persistent Codex session");
    match session_call::call_codex_via_session(&mut session, prompt, cancel) {
        Ok(text) => {
            outcome.codex_session = Some(session);
            PersistentSessionOutput::Output(text)
        }
        Err(CodexCallError::Cancelled) => {
            emit_canceled_event(sender, job_id, false);
            outcome.codex_session = Some(session);
            PersistentSessionOutput::Canceled
        }
        Err(err) => {
            outcome.disable_pty = true;
            emit_recoverable_event(
                sender,
                job_id,
                "pty_session",
                format!("Persistent Codex failed: {err:?}"),
                true,
            );
            PersistentSessionOutput::FallbackToCli
        }
    }
}

fn resolve_output_text(
    codex_output: Option<String>,
    config: &AppConfig,
    prompt: &str,
    working_dir: &Path,
    cancel: &CancelToken,
    stats: &mut CodexJobStats,
) -> Result<String, CodexCallError> {
    match codex_output {
        Some(text) => Ok(text),
        None => match call_codex_cli(config, prompt, working_dir, cancel) {
            Ok(text) => {
                stats.cli_fallback_used = true;
                Ok(text)
            }
            Err(err) => Err(err),
        },
    }
}

pub(super) fn run_codex_job(
    context: JobContext,
    codex_session: Option<PtyCliSession>,
    cancel: CancelToken,
    sender: &EventSender,
) -> CodexRunOutcome {
    let JobContext {
        job_id,
        request,
        mode,
        config,
        working_dir,
    } = context;
    let mut outcome = CodexRunOutcome {
        codex_session,
        disable_pty: false,
    };

    if !emit_started_event(sender, job_id, mode) {
        return outcome;
    }

    let prompt = match request.payload {
        RequestPayload::Chat { prompt } => prompt,
    };

    #[cfg(test)]
    if let Some(events) = super::test_support::try_job_hook(&prompt, &cancel) {
        for kind in events {
            let _ = sender.emit(CodexEvent { job_id, kind });
        }
        return outcome;
    }

    if prompt.trim().is_empty() {
        emit_fatal_event(
            sender,
            job_id,
            "input_validation",
            "Prompt is empty.".into(),
            false,
        );
        return outcome;
    }

    let started_at = Instant::now();
    let mut stats = CodexJobStats::new(started_at);
    let codex_output = match attempt_persistent_codex_output(
        &mut outcome,
        &mut stats,
        &prompt,
        &cancel,
        sender,
        job_id,
        config.persistent_codex,
    ) {
        PersistentSessionOutput::Output(text) => Some(text),
        PersistentSessionOutput::Canceled => return outcome,
        PersistentSessionOutput::FallbackToCli => None,
    };

    if cancel.is_cancelled() {
        emit_canceled_event(sender, job_id, outcome.disable_pty);
        return outcome;
    }

    let output_text = match resolve_output_text(
        codex_output,
        &config,
        &prompt,
        &working_dir,
        &cancel,
        &mut stats,
    ) {
        Ok(text) => text,
        Err(CodexCallError::Cancelled) => {
            emit_canceled_event(sender, job_id, outcome.disable_pty);
            return outcome;
        }
        Err(CodexCallError::Failure(err)) => {
            emit_fatal_event(
                sender,
                job_id,
                "cli",
                format!("{err:#}"),
                outcome.disable_pty,
            );
            return outcome;
        }
    };

    emit_finished_event(
        sender,
        job_id,
        &prompt,
        &output_text,
        stats,
        outcome.disable_pty,
        config.log_timings,
    );
    outcome
}
