use crossbeam_channel::{Receiver, Sender};
use crossterm::terminal::size as terminal_size;
use std::io::{self, Write};
use std::thread;
use std::time::{Duration, Instant};

#[derive(Debug)]
pub(crate) enum WriterMessage {
    PtyOutput(Vec<u8>),
    Status { text: String },
    ClearStatus,
    Resize { rows: u16, cols: u16 },
    Shutdown,
}

pub(crate) fn spawn_writer_thread(rx: Receiver<WriterMessage>) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        let mut stdout = io::stdout();
        let mut status: Option<String> = None;
        let mut pending_status: Option<String> = None;
        let mut pending_clear = false;
        let mut needs_redraw = false;
        let mut rows = 0u16;
        let mut cols = 0u16;
        let mut last_output_at = Instant::now();
        let mut last_status_draw_at = Instant::now();

        loop {
            match rx.recv_timeout(Duration::from_millis(25)) {
                Ok(WriterMessage::PtyOutput(bytes)) => {
                    if stdout.write_all(&bytes).is_err() {
                        break;
                    }
                    last_output_at = Instant::now();
                    if status.is_some() {
                        needs_redraw = true;
                    }
                    let _ = stdout.flush();
                }
                Ok(WriterMessage::Status { text }) => {
                    pending_status = Some(text);
                    pending_clear = false;
                    needs_redraw = true;
                    maybe_redraw_status(StatusRedraw {
                        stdout: &mut stdout,
                        rows: &mut rows,
                        cols: &mut cols,
                        status: &mut status,
                        pending_status: &mut pending_status,
                        pending_clear: &mut pending_clear,
                        needs_redraw: &mut needs_redraw,
                        last_output_at,
                        last_status_draw_at: &mut last_status_draw_at,
                    });
                }
                Ok(WriterMessage::ClearStatus) => {
                    pending_status = None;
                    pending_clear = true;
                    needs_redraw = true;
                    maybe_redraw_status(StatusRedraw {
                        stdout: &mut stdout,
                        rows: &mut rows,
                        cols: &mut cols,
                        status: &mut status,
                        pending_status: &mut pending_status,
                        pending_clear: &mut pending_clear,
                        needs_redraw: &mut needs_redraw,
                        last_output_at,
                        last_status_draw_at: &mut last_status_draw_at,
                    });
                }
                Ok(WriterMessage::Resize { rows: r, cols: c }) => {
                    rows = r;
                    cols = c;
                    if status.is_some() || pending_status.is_some() {
                        needs_redraw = true;
                    }
                    maybe_redraw_status(StatusRedraw {
                        stdout: &mut stdout,
                        rows: &mut rows,
                        cols: &mut cols,
                        status: &mut status,
                        pending_status: &mut pending_status,
                        pending_clear: &mut pending_clear,
                        needs_redraw: &mut needs_redraw,
                        last_output_at,
                        last_status_draw_at: &mut last_status_draw_at,
                    });
                }
                Ok(WriterMessage::Shutdown) => break,
                Err(crossbeam_channel::RecvTimeoutError::Timeout) => {
                    maybe_redraw_status(StatusRedraw {
                        stdout: &mut stdout,
                        rows: &mut rows,
                        cols: &mut cols,
                        status: &mut status,
                        pending_status: &mut pending_status,
                        pending_clear: &mut pending_clear,
                        needs_redraw: &mut needs_redraw,
                        last_output_at,
                        last_status_draw_at: &mut last_status_draw_at,
                    });
                }
                Err(crossbeam_channel::RecvTimeoutError::Disconnected) => {
                    break;
                }
            }
        }
    })
}

pub(crate) fn set_status(
    writer_tx: &Sender<WriterMessage>,
    clear_deadline: &mut Option<Instant>,
    current_status: &mut Option<String>,
    text: &str,
    clear_after: Option<Duration>,
) {
    if current_status.as_deref() == Some(text) {
        return;
    }
    let _ = writer_tx.send(WriterMessage::Status {
        text: text.to_string(),
    });
    *current_status = Some(text.to_string());
    *clear_deadline = clear_after.map(|duration| Instant::now() + duration);
}

struct StatusRedraw<'a> {
    stdout: &'a mut io::Stdout,
    rows: &'a mut u16,
    cols: &'a mut u16,
    status: &'a mut Option<String>,
    pending_status: &'a mut Option<String>,
    pending_clear: &'a mut bool,
    needs_redraw: &'a mut bool,
    last_output_at: Instant,
    last_status_draw_at: &'a mut Instant,
}

fn maybe_redraw_status(ctx: StatusRedraw<'_>) {
    const STATUS_IDLE_MS: u64 = 50;
    const STATUS_MAX_WAIT_MS: u64 = 500;
    if !*ctx.needs_redraw {
        return;
    }
    let since_output = ctx.last_output_at.elapsed();
    let since_draw = ctx.last_status_draw_at.elapsed();
    if since_output < Duration::from_millis(STATUS_IDLE_MS)
        && since_draw < Duration::from_millis(STATUS_MAX_WAIT_MS)
    {
        return;
    }
    if *ctx.rows == 0 || *ctx.cols == 0 {
        if let Ok((c, r)) = terminal_size() {
            *ctx.rows = r;
            *ctx.cols = c;
        }
    }
    if *ctx.pending_clear {
        let _ = clear_status_line(ctx.stdout, *ctx.rows, *ctx.cols);
        *ctx.status = None;
        *ctx.pending_clear = false;
    }
    if let Some(text) = ctx.pending_status.take() {
        *ctx.status = Some(text);
    }
    if let Some(text) = ctx.status.as_deref() {
        let _ = write_status_line(ctx.stdout, text, *ctx.rows, *ctx.cols);
    }
    *ctx.needs_redraw = false;
    *ctx.last_status_draw_at = Instant::now();
    let _ = ctx.stdout.flush();
}

fn write_status_line(stdout: &mut dyn Write, text: &str, rows: u16, cols: u16) -> io::Result<()> {
    if rows == 0 || cols == 0 {
        return Ok(());
    }
    let sanitized = sanitize_status(text);
    let trimmed = truncate_status(&sanitized, cols as usize);
    let mut sequence = Vec::new();
    sequence.extend_from_slice(b"\x1b7");
    sequence.extend_from_slice(format!("\x1b[{rows};1H").as_bytes());
    sequence.extend_from_slice(b"\x1b[2K");
    sequence.extend_from_slice(trimmed.as_bytes());
    sequence.extend_from_slice(b"\x1b8");
    stdout.write_all(&sequence)
}

fn clear_status_line(stdout: &mut dyn Write, rows: u16, cols: u16) -> io::Result<()> {
    if rows == 0 || cols == 0 {
        return Ok(());
    }
    let mut sequence = Vec::new();
    sequence.extend_from_slice(b"\x1b7");
    sequence.extend_from_slice(format!("\x1b[{rows};1H").as_bytes());
    sequence.extend_from_slice(b"\x1b[2K");
    sequence.extend_from_slice(b"\x1b8");
    stdout.write_all(&sequence)
}

fn sanitize_status(text: &str) -> String {
    text.chars()
        .map(|ch| {
            if ch.is_ascii_graphic() || ch == ' ' {
                ch
            } else {
                ' '
            }
        })
        .collect()
}

fn truncate_status(text: &str, max: usize) -> String {
    if max == 0 {
        return String::new();
    }
    text.chars().take(max).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;

    #[test]
    fn status_helpers_sanitize_and_truncate() {
        let sanitized = sanitize_status("ok\tbad\n");
        assert_eq!(sanitized, "ok bad ");
        assert_eq!(truncate_status("hello", 0), "");
        assert_eq!(truncate_status("hello", 2), "he");
    }

    #[test]
    fn write_and_clear_status_line_respect_dimensions() {
        let mut buf = Vec::new();
        write_status_line(&mut buf, "hi", 0, 10).unwrap();
        assert!(buf.is_empty());

        write_status_line(&mut buf, "hi", 2, 0).unwrap();
        assert!(buf.is_empty());

        write_status_line(&mut buf, "hi", 2, 10).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert!(output.contains("\u{1b}[2;1H"));
        assert!(output.contains("hi"));

        buf.clear();
        clear_status_line(&mut buf, 2, 10).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert!(output.contains("\u{1b}[2;1H"));

        buf.clear();
        clear_status_line(&mut buf, 2, 0).unwrap();
        assert!(buf.is_empty());
    }

    #[test]
    fn set_status_updates_deadline() {
        let (tx, rx) = crossbeam_channel::unbounded();
        let mut deadline = None;
        let mut current_status = None;
        let now = Instant::now();
        set_status(
            &tx,
            &mut deadline,
            &mut current_status,
            "status",
            Some(Duration::from_millis(50)),
        );
        let msg = rx
            .recv_timeout(Duration::from_millis(200))
            .expect("status message");
        match msg {
            WriterMessage::Status { text } => assert_eq!(text, "status"),
            _ => panic!("unexpected writer message"),
        }
        assert!(deadline.expect("deadline set") > now);

        set_status(&tx, &mut deadline, &mut current_status, "steady", None);
        assert!(deadline.is_none());
    }
}
