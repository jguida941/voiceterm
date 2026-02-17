use std::sync::mpsc::TryRecvError;

use super::super::{send_event, CodexEvent, CodexEventKind, CodexJob, IpcEvent};

pub(super) fn process_codex_events(job: &mut CodexJob, cancelled: bool) -> bool {
    if cancelled {
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
                send_event(&IpcEvent::JobEnd {
                    provider: "codex".to_string(),
                    success: true,
                    error: None,
                });
                true
            }
            CodexEventKind::FatalError { message, .. } => {
                send_event(&IpcEvent::JobEnd {
                    provider: "codex".to_string(),
                    success: false,
                    error: Some(message),
                });
                true
            }
            CodexEventKind::RecoverableError { message, .. } => {
                send_event(&IpcEvent::Status {
                    message: format!("Retrying: {message}"),
                });
                false
            }
            CodexEventKind::Canceled { .. } => {
                send_event(&IpcEvent::JobEnd {
                    provider: "codex".to_string(),
                    success: false,
                    error: Some("Cancelled".to_string()),
                });
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
                send_event(&IpcEvent::JobEnd {
                    provider: "codex".to_string(),
                    success: true,
                    error: None,
                });
            }
            true
        }
    }
}
