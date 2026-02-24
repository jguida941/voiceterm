use std::process::ExitStatus;
use std::sync::mpsc::{RecvTimeoutError, TryRecvError};
use std::time::Duration;

use super::super::{
    log_debug, log_debug_content, sanitize_pty_output, send_event, terminate_piped_child,
    utf8_prefix, ClaudeJob, ClaudeJobOutput, IpcEvent,
};

pub(super) fn process_claude_events(job: &mut ClaudeJob, cancelled: bool) -> bool {
    if cancelled {
        log_debug("Claude job: cancelled");
        job.cancel();
        return true;
    }

    match &mut job.output {
        ClaudeJobOutput::Piped { child, stdout_rx } => match stdout_rx.try_recv() {
            Ok(line) => {
                emit_claude_line(&line);
                false
            }
            Err(TryRecvError::Empty) => {
                if job.pending_exit.is_none() {
                    match child.try_wait() {
                        Ok(Some(status)) => {
                            log_debug(&format!(
                                "Claude job: process exited with status {status:?}"
                            ));
                            // Reader threads may still flush buffered stdout/stderr after the child exits.
                            // Delay JobEnd briefly so we do not drop final token lines.
                            job.pending_exit = Some(status);
                        }
                        Ok(None) => return false,
                        Err(e) => {
                            send_claude_job_end(false, Some(format!("Process error: {e}")));
                            return true;
                        }
                    }
                }

                let mut drained_any = false;
                while let Ok(line) = stdout_rx.try_recv() {
                    drained_any = true;
                    emit_claude_line(&line);
                }
                if drained_any {
                    return false;
                }

                // Use a short timeout (5ms) when draining trailing output after
                // child exit to avoid blocking the event loop unnecessarily.
                let drain_ms = if job.pending_exit.is_some() { 5 } else { 25 };
                match stdout_rx.recv_timeout(Duration::from_millis(drain_ms)) {
                    Ok(line) => {
                        emit_claude_line(&line);
                        false
                    }
                    Err(RecvTimeoutError::Timeout) | Err(RecvTimeoutError::Disconnected) => {
                        let Some(status) = job.pending_exit.take() else {
                            return false;
                        };
                        let (success, error) = claude_status_outcome(status);
                        send_claude_job_end(success, error);
                        true
                    }
                }
            }
            Err(TryRecvError::Disconnected) => {
                log_debug("Claude job: stdout disconnected");
                match child.try_wait() {
                    Ok(Some(status)) => {
                        log_debug(&format!(
                            "Claude job: process already exited with {status:?}"
                        ));
                        send_claude_job_end(status.success(), None);
                        true
                    }
                    Ok(None) => {
                        log_debug("Claude job: process still running, killing it");
                        terminate_piped_child(child);
                        send_claude_job_end(true, None);
                        true
                    }
                    Err(e) => {
                        // try_wait failed; kill the child to avoid leaving it running.
                        log_debug(&format!(
                            "Claude job: try_wait error ({e}), terminating child"
                        ));
                        terminate_piped_child(child);
                        send_claude_job_end(false, Some(format!("Wait error: {e}")));
                        true
                    }
                }
            }
        },
        ClaudeJobOutput::Pty { session } => {
            for chunk in session.read_output() {
                let text = sanitize_pty_output(&chunk);
                if !text.is_empty() {
                    send_event(&IpcEvent::Token { text });
                }
            }
            if let Some(status) = job.pending_exit.take() {
                let (success, error) = claude_status_outcome(status);
                send_claude_job_end(success, error);
                return true;
            }
            if let Some(status) = session.try_wait() {
                let trailing = session.read_output_timeout(Duration::from_millis(50));
                if !trailing.is_empty() {
                    for chunk in trailing {
                        let text = sanitize_pty_output(&chunk);
                        if !text.is_empty() {
                            send_event(&IpcEvent::Token { text });
                        }
                    }
                    job.pending_exit = Some(status);
                    return false;
                }
                let (success, error) = claude_status_outcome(status);
                send_claude_job_end(success, error);
                return true;
            }
            false
        }
    }
}

fn emit_claude_line(line: &str) {
    log_debug_content(&format!("Claude job: got line: {}", utf8_prefix(line, 50)));
    send_event(&IpcEvent::Token {
        text: format!("{line}\n"),
    });
}

fn claude_status_outcome(status: ExitStatus) -> (bool, Option<String>) {
    if status.success() {
        (true, None)
    } else {
        let message = status
            .code()
            .map(|code| format!("Exit code: {code}"))
            .unwrap_or_else(|| "Exited by signal".to_string());
        (false, Some(message))
    }
}

fn send_claude_job_end(success: bool, error: Option<String>) {
    send_event(&IpcEvent::JobEnd {
        provider: "claude".to_string(),
        success,
        error,
    });
}
