use std::process::ExitStatus;
use std::sync::mpsc::TryRecvError;
use std::time::Duration;

use super::super::{
    log_debug, log_debug_content, sanitize_pty_output, send_event, terminate_piped_child,
    ClaudeJob, ClaudeJobOutput, IpcEvent,
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
                log_debug_content(&format!(
                    "Claude job: got line: {}",
                    &line[..line.len().min(50)]
                ));
                send_event(&IpcEvent::Token {
                    text: format!("{line}\n"),
                });
                false
            }
            Err(TryRecvError::Empty) => match child.try_wait() {
                Ok(Some(status)) => {
                    log_debug(&format!(
                        "Claude job: process exited with status {status:?}"
                    ));
                    let (success, error) = claude_status_outcome(status);
                    send_claude_job_end(success, error);
                    true
                }
                Ok(None) => false,
                Err(e) => {
                    send_claude_job_end(false, Some(format!("Process error: {e}")));
                    true
                }
            },
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
