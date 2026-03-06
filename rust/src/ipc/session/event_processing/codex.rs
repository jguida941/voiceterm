use std::sync::mpsc::TryRecvError;

use super::super::{send_event, CodexEvent, CodexEventKind, CodexJob, IpcEvent, Provider};

fn send_codex_job_end(success: bool, error: Option<String>) {
    send_event(&IpcEvent::JobEnd {
        provider: Provider::Codex.as_str().to_string(),
        success,
        error,
    });
}

pub(super) fn process_codex_events(job: &mut CodexJob, cancelled: bool) -> bool {
    if cancelled {
        // Fire the cancel token so the worker thread terminates its subprocess.
        job.cancel();
        return true;
    }

    let handle_event = |event: CodexEvent| -> bool {
        match event.kind {
            CodexEventKind::Token { text } => {
                send_event(&IpcEvent::Token { text });
                false
            }
            CodexEventKind::Status { message } => {
                send_event(&IpcEvent::Status { message });
                false
            }
            CodexEventKind::Started { .. } => {
                send_event(&IpcEvent::Status {
                    message: "Processing...".to_string(),
                });
                false
            }
            CodexEventKind::Finished { lines, .. } => {
                for line in lines {
                    send_event(&IpcEvent::Token {
                        text: format!("{line}\n"),
                    });
                }
                send_codex_job_end(true, None);
                true
            }
            CodexEventKind::FatalError { message, .. } => {
                send_codex_job_end(false, Some(message));
                true
            }
            CodexEventKind::RecoverableError { message, .. } => {
                send_event(&IpcEvent::Status {
                    message: format!("Retrying: {message}"),
                });
                false
            }
            CodexEventKind::Canceled { .. } => {
                send_codex_job_end(false, Some("Cancelled".to_string()));
                true
            }
        }
    };

    match job.try_recv_signal() {
        Ok(()) => {
            for event in job.drain_events() {
                if handle_event(event) {
                    return true;
                }
            }
            false
        }
        Err(TryRecvError::Empty) => false,
        Err(TryRecvError::Disconnected) => {
            let mut completed = false;
            for event in job.drain_events() {
                if handle_event(event) {
                    completed = true;
                    break;
                }
            }
            if !completed {
                send_codex_job_end(true, None);
            }
            true
        }
    }
}
