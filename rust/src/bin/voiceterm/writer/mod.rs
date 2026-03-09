//! Writer message protocol and bootstrap so terminal output stays serialized.

mod mouse;
mod render;
mod sanitize;
mod state;
mod timing;

use crossbeam_channel::{Receiver, Sender, TrySendError};
use std::thread;
use std::time::{Duration, Instant};

use crate::log_debug;
use crate::status_line::StatusLineState;
use crate::theme::Theme;

const WRITER_RECV_TIMEOUT_MS: u64 = 25;
const STATUS_SEND_TIMEOUT_MS: u64 = 2;

#[derive(Debug, Clone)]
pub(crate) enum WriterMessage {
    PtyOutput(Vec<u8>),
    /// Direct terminal-control bytes that must stay serialized with overlay/HUD output.
    TerminalBytes(Vec<u8>),
    /// Simple status message (legacy format with auto-styled prefix)
    #[allow(
        dead_code,
        reason = "Legacy status payload kept for compatibility while writer-state migration completes."
    )]
    Status {
        text: String,
    },
    /// Enhanced status line with full state
    EnhancedStatus(StatusLineState),
    /// Overlay panel content (multi-line box)
    ShowOverlay {
        content: String,
        height: usize,
    },
    /// Clear overlay panel
    ClearOverlay,
    ClearStatus,
    /// Emit terminal bell sound (optional)
    Bell {
        count: u8,
    },
    Resize {
        rows: u16,
        cols: u16,
    },
    SetTheme(Theme),
    /// Enable mouse tracking for clickable HUD buttons
    EnableMouse,
    /// Disable mouse tracking
    DisableMouse,
    /// User typed into the backend prompt/composer.
    /// Used to temporarily defer non-urgent HUD redraws in Claude Cursor.
    UserInputActivity,
    Shutdown,
}

pub(crate) fn spawn_writer_thread(rx: Receiver<WriterMessage>) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        let mut state = state::WriterState::new();
        loop {
            let message = match rx.recv_timeout(Duration::from_millis(WRITER_RECV_TIMEOUT_MS)) {
                Ok(msg) => msg,
                Err(crossbeam_channel::RecvTimeoutError::Timeout) => {
                    state.maybe_redraw_status();
                    continue;
                }
                Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
            };
            let was_pty_output = matches!(&message, WriterMessage::PtyOutput(_));
            if !state.handle_message(message) {
                break;
            }
            // After PTY output, eagerly drain any immediately pending messages
            // so suppression state transitions (EnhancedStatus) are applied
            // before the next chunk's redraw decision. Without this, status
            // messages can lag behind a burst of PtyOutput messages in the
            // queue, causing stale suppression state during HUD redraws.
            if was_pty_output {
                while let Ok(next) = rx.try_recv() {
                    if !state.handle_message(next) {
                        return;
                    }
                }
            }
        }
    })
}

pub(crate) fn set_status(
    writer_tx: &Sender<WriterMessage>,
    clear_deadline: &mut Option<Instant>,
    current_status: &mut Option<String>,
    status_state: &mut StatusLineState,
    text: &str,
    clear_after: Option<Duration>,
) {
    let same_text = current_status.as_deref() == Some(text);
    status_state.message = text.to_string();
    if !same_text {
        *current_status = Some(status_state.message.clone());
    }
    let _ = try_send_status_message(
        writer_tx,
        WriterMessage::EnhancedStatus(status_state.clone()),
    );
    *clear_deadline = clear_after.map(|duration| Instant::now() + duration);
}

pub(crate) fn send_enhanced_status(
    writer_tx: &Sender<WriterMessage>,
    status_state: &StatusLineState,
) {
    let _ = try_send_status_message(
        writer_tx,
        WriterMessage::EnhancedStatus(status_state.clone()),
    );
}

fn try_send_status_message(writer_tx: &Sender<WriterMessage>, message: WriterMessage) -> bool {
    match writer_tx.try_send(message) {
        Ok(()) => true,
        Err(TrySendError::Full(message)) => {
            match writer_tx.send_timeout(message, Duration::from_millis(STATUS_SEND_TIMEOUT_MS)) {
                Ok(()) => true,
                Err(crossbeam_channel::SendTimeoutError::Timeout(_)) => {
                    log_debug("writer status message dropped: queue remained full after timeout");
                    false
                }
                Err(crossbeam_channel::SendTimeoutError::Disconnected(_)) => {
                    log_debug("writer status message dropped: writer channel disconnected");
                    false
                }
            }
        }
        Err(TrySendError::Disconnected(_)) => false,
    }
}

pub(crate) fn try_send_message(writer_tx: &Sender<WriterMessage>, message: WriterMessage) -> bool {
    match writer_tx.try_send(message) {
        Ok(()) => true,
        Err(TrySendError::Full(_)) | Err(TrySendError::Disconnected(_)) => false,
    }
}

pub(crate) fn send_message_blocking(
    writer_tx: &Sender<WriterMessage>,
    message: WriterMessage,
    context: &str,
) -> bool {
    match writer_tx.send(message) {
        Ok(()) => true,
        Err(err) => {
            log_debug(&format!(
                "{context}: writer channel disconnected before message delivery: {err}",
            ));
            false
        }
    }
}

pub(crate) fn osc52_copy_bytes(text: &str) -> Vec<u8> {
    let encoded = base64_encode(text.as_bytes());
    format!("\x1b]52;c;{encoded}\x07").into_bytes()
}

fn base64_encode(input: &[u8]) -> String {
    const CHARS: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(input.len().div_ceil(3) * 4);
    for chunk in input.chunks(3) {
        let b0 = chunk[0] as u32;
        let b1 = chunk.get(1).copied().unwrap_or(0) as u32;
        let b2 = chunk.get(2).copied().unwrap_or(0) as u32;
        let triple = (b0 << 16) | (b1 << 8) | b2;
        out.push(CHARS[((triple >> 18) & 0x3F) as usize] as char);
        out.push(CHARS[((triple >> 12) & 0x3F) as usize] as char);
        if chunk.len() > 1 {
            out.push(CHARS[((triple >> 6) & 0x3F) as usize] as char);
        } else {
            out.push('=');
        }
        if chunk.len() > 2 {
            out.push(CHARS[(triple & 0x3F) as usize] as char);
        } else {
            out.push('=');
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;

    #[test]
    fn set_status_updates_deadline() {
        let (tx, rx) = crossbeam_channel::unbounded();
        let mut deadline = None;
        let mut current_status = None;
        let mut status_state = StatusLineState::new();
        let now = Instant::now();
        set_status(
            &tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
            "status",
            Some(Duration::from_millis(50)),
        );
        let msg = rx
            .recv_timeout(Duration::from_millis(200))
            .expect("status message");
        match msg {
            WriterMessage::EnhancedStatus(state) => assert_eq!(state.message, "status"),
            _ => panic!("unexpected writer message"),
        }
        assert!(deadline.expect("deadline set") > now);

        set_status(
            &tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
            "steady",
            None,
        );
        assert!(deadline.is_none());
    }

    #[test]
    fn set_status_does_not_block_when_queue_is_full() {
        let (tx, _rx) = crossbeam_channel::bounded(1);
        tx.try_send(WriterMessage::PtyOutput(vec![1, 2, 3]))
            .expect("queue should accept prefill");

        let mut deadline = None;
        let mut current_status = None;
        let mut status_state = StatusLineState::new();
        set_status(
            &tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
            "status while saturated",
            Some(Duration::from_millis(10)),
        );

        assert_eq!(status_state.message, "status while saturated");
        assert_eq!(current_status.as_deref(), Some("status while saturated"));
        assert!(deadline.is_some());
    }

    #[test]
    fn try_send_message_returns_false_on_full_queue() {
        let (tx, _rx) = crossbeam_channel::bounded(1);
        tx.try_send(WriterMessage::PtyOutput(vec![1]))
            .expect("queue should accept prefill");
        assert!(!try_send_message(&tx, WriterMessage::ClearStatus));
    }

    #[test]
    fn osc52_copy_bytes_encodes_expected_escape() {
        let payload = osc52_copy_bytes("Hello, clipboard!");
        assert_eq!(payload, b"\x1b]52;c;SGVsbG8sIGNsaXBib2FyZCE=\x07");
    }
}
