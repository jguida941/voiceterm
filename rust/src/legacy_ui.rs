//! Minimal ratatui frontend that keeps legacy Codex UI tests lightweight.
//!
//! This mirrors the logic from the legacy TUI entrypoint so integration tests can drive
//! the UI without pulling in all of the overlay stack. The multi-backend overlay lives
//! under `src/bin/voiceterm/`.

use crate::log_debug;
use crate::terminal_restore::TerminalRestoreGuard;
use crate::utf8_safe::window_by_columns;
use crate::voice::VoiceCaptureTrigger;
use crate::CodexApp;
use anyhow::Result;
use crossterm::event;
use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span, Text},
    widgets::{Block, BorderType, Borders, Paragraph},
    Terminal,
};
use std::io;
use std::time::Duration;
use unicode_width::UnicodeWidthChar;
use unicode_width::UnicodeWidthStr;

const MAX_LINE_WIDTH: usize = 500;

/// Configure the terminal, run the legacy TUI drawing loop, and tear everything down.
///
/// # Errors
///
/// Returns an error if terminal initialization fails, event polling/reading
/// fails, or backend/voice job polling returns an error.
pub fn run_legacy_ui(app: &mut CodexApp) -> Result<()> {
    let terminal_guard = TerminalRestoreGuard::new();
    terminal_guard.enable_raw_mode()?;
    let mut stdout = io::stdout();
    terminal_guard.enter_alt_screen(&mut stdout)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let result = app_loop(&mut terminal, app);

    drop(terminal);
    terminal_guard.restore();

    result
}

/// Core event/render loop for the test-friendly UI entrypoint.
fn app_loop(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    app: &mut CodexApp,
) -> Result<()> {
    // Initial render to show UI immediately on startup
    terminal.draw(|frame| draw(frame, app))?;

    loop {
        app.poll_codex_job()?;
        app.poll_voice_job()?;
        app.drain_persistent_output();

        let has_active_job = app.has_active_jobs();
        if has_active_job {
            app.update_codex_spinner();
        }

        let poll_duration = if has_active_job {
            Duration::from_millis(50)
        } else {
            Duration::from_millis(100)
        };

        // Always draw when there's an active job to show spinner animation
        let mut should_draw = app.take_redraw_request() || has_active_job;
        let mut should_quit = false;

        if event::poll(poll_duration)? {
            match event::read()? {
                Event::Key(key) => {
                    // Handle key BEFORE drawing to avoid input lag
                    should_quit = handle_key_event(app, key)?;
                    should_draw = true;
                }
                Event::Resize(_, _) => {
                    // Terminal resize requires immediate redraw
                    should_draw = true;
                }
                _ => {} // Ignore other events
            }
        }

        if should_draw {
            terminal.draw(|frame| draw(frame, app))?;
        }

        if should_quit {
            break;
        }
    }
    Ok(())
}

/// Interpret keystrokes into modifications to the shared `CodexApp` state.
fn handle_key_event(app: &mut CodexApp, key: KeyEvent) -> Result<bool> {
    log_debug(&format!(
        "Key event: {:?} with modifiers: {:?}",
        key.code, key.modifiers
    ));

    if key.modifiers.contains(KeyModifiers::CONTROL) && key.code == KeyCode::Char('c') {
        if app.cancel_codex_job_if_active() {
            return Ok(false);
        }
        return Ok(true);
    }

    match key.code {
        KeyCode::Char('r') if key.modifiers.contains(KeyModifiers::CONTROL) => {
            log_debug("Ctrl+R pressed, starting voice capture");
            app.start_voice_capture(VoiceCaptureTrigger::Manual)?;
        }
        KeyCode::Char('v') if key.modifiers.contains(KeyModifiers::CONTROL) => {
            app.toggle_voice_mode()?;
        }
        KeyCode::Enter => {
            app.send_current_input()?;
        }
        KeyCode::Backspace => app.backspace_input(),
        KeyCode::Esc => {
            if !app.cancel_codex_job_if_active() {
                app.clear_input();
            }
        }
        KeyCode::Char(c) => {
            if !key.modifiers.contains(KeyModifiers::CONTROL) {
                app.push_input_char(c);
            }
        }
        KeyCode::Delete => app.clear_input(),
        KeyCode::Up => app.scroll_up(),
        KeyCode::Down => app.scroll_down(),
        KeyCode::PageUp => app.page_up(),
        KeyCode::PageDown => app.page_down(),
        KeyCode::Home => app.scroll_to_top(),
        KeyCode::End => app.scroll_to_bottom(),
        _ => {}
    }

    Ok(false)
}

/// Render scrollback, prompt, and status bars.
pub fn draw(frame: &mut ratatui::Frame<'_>, app: &CodexApp) {
    // Split the screen into output, input, and status regions.
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(5),
            Constraint::Length(3),
            Constraint::Length(2),
        ])
        .split(frame.size());

    let output_text = if app.output_lines().is_empty() {
        Text::from("No Codex output yet. Press Ctrl+R to capture voice or type and press Enter.")
    } else {
        let lines: Vec<Line> = app
            .output_lines()
            .iter()
            .map(|s| Line::from(sanitize_output_line(s)))
            .collect();
        Text::from(lines)
    };

    // Theme colors - Vibrant red
    let border_color = Color::Rgb(255, 90, 90); // Vibrant red accent
    let title_color = Color::Rgb(255, 110, 110); // Bright red for titles
    let dim_border = Color::Rgb(130, 70, 70); // Dimmer border for less important areas
    let output_text_color = Color::Rgb(210, 205, 200); // Soft white for output
    let input_text_color = Color::Rgb(255, 220, 100); // Warm yellow for input
    let status_text_color = Color::Rgb(160, 150, 150); // Dimmer for status

    // CRITICAL: Disable text wrapping entirely to avoid ratatui's underflow bug
    // The bug in tui/src/wrapping.rs:21 causes integer underflow when calculating
    // slice positions, leading to "byte index 18446... out of bounds" panics.
    // Until ratatui fixes this, we must avoid text wrapping completely.
    let output_block = Paragraph::new(output_text)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_type(BorderType::Rounded)
                .border_style(Style::default().fg(border_color))
                .title(Span::styled(
                    " Codex Output ",
                    Style::default()
                        .fg(title_color)
                        .add_modifier(Modifier::BOLD),
                )),
        )
        .style(Style::default().fg(output_text_color))
        .scroll((app.get_scroll_offset(), 0));
    frame.render_widget(output_block, chunks[0]);

    // CRITICAL FIX: Sanitize the input text before rendering to prevent crashes
    // from terminal control sequences like "0;0;0u" that can appear in the input buffer
    let sanitized_input = app.sanitized_input_text();
    let input_block = Paragraph::new(sanitized_input.as_str())
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_type(BorderType::Rounded)
                .border_style(Style::default().fg(border_color))
                .title(Span::styled(
                    " Prompt ",
                    Style::default()
                        .fg(title_color)
                        .add_modifier(Modifier::BOLD),
                ))
                .title_bottom(Line::from(vec![
                    Span::styled(
                        " Ctrl+R ",
                        Style::default()
                            .fg(input_text_color)
                            .add_modifier(Modifier::BOLD),
                    ),
                    Span::styled("voice  ", Style::default().fg(dim_border)),
                    Span::styled(
                        "Ctrl+V ",
                        Style::default()
                            .fg(input_text_color)
                            .add_modifier(Modifier::BOLD),
                    ),
                    Span::styled("toggle ", Style::default().fg(dim_border)),
                ])),
        )
        .style(Style::default().fg(input_text_color));
    frame.render_widget(input_block, chunks[1]);

    let status_block = Paragraph::new(app.status_text())
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_type(BorderType::Rounded)
                .border_style(Style::default().fg(dim_border))
                .title(Span::styled(
                    " Status ",
                    Style::default().fg(status_text_color),
                )),
        )
        .style(Style::default().fg(status_text_color));
    frame.render_widget(status_block, chunks[2]);

    let inner_width = chunks[1].width.saturating_sub(2);
    let input_width =
        UnicodeWidthStr::width(sanitized_input.as_str()).min(u16::MAX as usize) as u16;
    let cursor_offset = input_width.min(inner_width);
    let cursor_x = chunks[1].x.saturating_add(1).saturating_add(cursor_offset);
    let cursor_y = chunks[1].y + 1;
    frame.set_cursor(cursor_x, cursor_y);
}

fn sanitize_output_line(s: &str) -> String {
    if s.trim().is_empty() && !s.is_empty() {
        return String::new();
    }

    let cleaned = s
        .chars()
        .filter(|c| !c.is_control() || *c == '\n' || *c == '\t')
        .collect::<String>();
    let mut final_text = cleaned
        .trim_matches(|c: char| {
            c.is_control() || (c as u32) < 32 || c == '\u{200B}' || c == '\u{FEFF}'
        })
        .to_string();
    if final_text.is_empty() {
        final_text = " ".to_string();
    }

    let safe_text = final_text
        .chars()
        .map(|c| {
            if c.width().unwrap_or(0) == 0 && c != '\n' && c != '\t' {
                ' '
            } else {
                c
            }
        })
        .collect::<String>();
    let safe_text = safe_text.replace('`', "'");

    let trimmed = window_by_columns(&safe_text, 0, MAX_LINE_WIDTH);
    let mut final_safe_text = trimmed.to_string();
    if UnicodeWidthStr::width(safe_text.as_str()) > UnicodeWidthStr::width(trimmed) {
        final_safe_text.push('…');
    }
    final_safe_text
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::codex::{self, CodexEventKind, CodexJobStats};
    use crate::config::AppConfig;
    use clap::Parser;
    use ratatui::backend::{Backend, TestBackend};
    use ratatui::Terminal;
    use std::thread;
    use std::time::{Duration, Instant};

    fn test_app() -> CodexApp {
        let mut config = AppConfig::parse_from(["test-app"]);
        config.persistent_codex = false;
        CodexApp::new(config)
    }

    #[test]
    fn handle_key_event_appends_and_backspaces() {
        let mut app = test_app();
        handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Char('a'), KeyModifiers::empty()),
        )
        .expect("key event");
        assert_eq!(app.sanitized_input_text(), "a");

        handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Backspace, KeyModifiers::empty()),
        )
        .expect("key event");
        assert_eq!(app.sanitized_input_text(), "");
    }

    fn test_stats() -> CodexJobStats {
        let now = Instant::now();
        CodexJobStats {
            backend_type: "cli",
            started_at: now,
            first_token_at: None,
            finished_at: now,
            tokens_received: 0,
            bytes_transferred: 0,
            pty_attempts: 0,
            cli_fallback_used: false,
            disable_pty: false,
        }
    }

    fn app_with_output_line(line: String) -> CodexApp {
        app_with_output_lines(vec![line])
    }

    fn app_with_output_lines(lines: Vec<String>) -> CodexApp {
        let mut app = test_app();
        app.push_input_char('x');
        let (_result, hook_guard) = codex::with_job_hook(
            Box::new(move |_, _| {
                vec![CodexEventKind::Finished {
                    lines: lines.clone(),
                    status: "ok".into(),
                    stats: test_stats(),
                }]
            }),
            || {
                app.send_current_input().expect("send input");
                for _ in 0..100 {
                    if !app.has_active_jobs() {
                        break;
                    }
                    app.poll_codex_job().expect("poll codex job");
                    thread::sleep(Duration::from_millis(1));
                }
            },
        );
        drop(hook_guard);
        app
    }

    fn draw_into_test_backend(app: &CodexApp, width: u16, height: u16) -> (String, (u16, u16)) {
        let backend = TestBackend::new(width, height);
        let mut terminal = Terminal::new(backend).expect("test terminal");
        terminal
            .draw(|frame| draw(frame, app))
            .expect("legacy ui draw");
        let symbols = terminal
            .backend()
            .buffer()
            .content()
            .iter()
            .map(|cell| cell.symbol())
            .collect::<String>();
        let cursor = terminal
            .backend_mut()
            .get_cursor()
            .expect("cursor position");
        (symbols, cursor)
    }

    #[test]
    fn draw_appends_ellipsis_only_for_truncated_output_lines() {
        let long_line = "x".repeat(600);
        let app_long = app_with_output_line(long_line);
        let (symbols_long, _) = draw_into_test_backend(&app_long, 700, 20);
        assert!(
            symbols_long.contains('…'),
            "expected ellipsis when output line exceeds trim width"
        );

        let exact_line = "x".repeat(500);
        let app_exact = app_with_output_line(exact_line);
        let (symbols_exact, _) = draw_into_test_backend(&app_exact, 700, 20);
        assert!(
            !symbols_exact.contains('…'),
            "did not expect ellipsis when output line matches trim width"
        );
    }

    #[test]
    fn draw_sets_cursor_on_prompt_row_plus_one() {
        let mut app = test_app();
        app.push_input_char('a');
        let (_symbols, cursor) = draw_into_test_backend(&app, 80, 24);
        assert_eq!(cursor, (2, 20));
    }

    #[test]
    fn handle_key_event_plain_r_and_v_append_chars() {
        let mut app = test_app();
        handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Char('r'), KeyModifiers::empty()),
        )
        .expect("plain r should append");
        handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Char('v'), KeyModifiers::empty()),
        )
        .expect("plain v should append");
        assert_eq!(app.sanitized_input_text(), "rv");
    }

    #[test]
    fn handle_key_event_enter_sends_prompt_and_appends_output() {
        let mut app = test_app();
        app.push_input_char('x');
        let (_result, hook_guard) = codex::with_job_hook(
            Box::new(|_, _| {
                vec![CodexEventKind::Finished {
                    lines: vec!["enter-ok".into()],
                    status: "ok".into(),
                    stats: test_stats(),
                }]
            }),
            || {
                handle_key_event(
                    &mut app,
                    KeyEvent::new(KeyCode::Enter, KeyModifiers::empty()),
                )
                .expect("enter key should dispatch input");
                for _ in 0..100 {
                    if !app.has_active_jobs() {
                        break;
                    }
                    app.poll_codex_job().expect("poll codex");
                    thread::sleep(Duration::from_millis(1));
                }
            },
        );
        drop(hook_guard);
        assert!(app.output_lines().iter().any(|line| line == "enter-ok"));
    }

    #[test]
    fn handle_key_event_esc_and_delete_clear_input() {
        let mut app = test_app();
        app.push_input_char('a');
        app.push_input_char('b');
        handle_key_event(&mut app, KeyEvent::new(KeyCode::Esc, KeyModifiers::empty()))
            .expect("esc should clear input");
        assert!(app.sanitized_input_text().is_empty());

        app.push_input_char('z');
        handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Delete, KeyModifiers::empty()),
        )
        .expect("delete should clear input");
        assert!(app.sanitized_input_text().is_empty());
    }

    #[test]
    fn handle_key_event_navigation_keys_adjust_scroll_offset() {
        let mut app = app_with_output_lines((0..30).map(|i| format!("line-{i}")).collect());

        handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Home, KeyModifiers::empty()),
        )
        .expect("home should move to top");
        assert_eq!(app.get_scroll_offset(), 0);

        handle_key_event(&mut app, KeyEvent::new(KeyCode::End, KeyModifiers::empty()))
            .expect("end should move to bottom");
        assert_eq!(app.get_scroll_offset(), 20);

        handle_key_event(&mut app, KeyEvent::new(KeyCode::Up, KeyModifiers::empty()))
            .expect("up should scroll up");
        assert_eq!(app.get_scroll_offset(), 19);

        handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Down, KeyModifiers::empty()),
        )
        .expect("down should scroll down");
        assert_eq!(app.get_scroll_offset(), 20);

        handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::PageUp, KeyModifiers::empty()),
        )
        .expect("page up should scroll up");
        assert_eq!(app.get_scroll_offset(), 10);

        handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::PageDown, KeyModifiers::empty()),
        )
        .expect("page down should scroll down");
        assert_eq!(app.get_scroll_offset(), 20);
    }

    #[test]
    fn handle_key_event_ctrl_c_quits_without_active_job() {
        let mut app = test_app();
        let should_quit = handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL),
        )
        .expect("ctrl+c should be handled");
        assert!(should_quit);
    }

    #[test]
    fn handle_key_event_ctrl_c_cancels_active_job_and_keeps_loop_running() {
        let mut app = test_app();
        app.push_input_char('x');
        let (_result, hook_guard) = codex::with_job_hook(
            Box::new(|_, cancel| {
                let start = Instant::now();
                while !cancel.is_cancelled() {
                    if start.elapsed() > Duration::from_millis(500) {
                        break;
                    }
                    thread::sleep(Duration::from_millis(1));
                }
                vec![CodexEventKind::Canceled { disable_pty: false }]
            }),
            || {
                app.send_current_input().expect("start codex job");
                let should_quit = handle_key_event(
                    &mut app,
                    KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL),
                )
                .expect("ctrl+c should cancel active job");
                assert!(!should_quit);
                for _ in 0..100 {
                    if !app.has_active_jobs() {
                        break;
                    }
                    app.poll_codex_job().expect("poll codex");
                    thread::sleep(Duration::from_millis(1));
                }
            },
        );
        drop(hook_guard);
        assert_eq!(app.status_text(), "Codex request canceled.");
    }

    #[test]
    fn handle_key_event_plain_c_without_control_does_not_quit() {
        let mut app = test_app();
        let should_quit = handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Char('c'), KeyModifiers::empty()),
        )
        .expect("plain c should be handled as input");
        assert!(!should_quit);
        assert_eq!(app.sanitized_input_text(), "c");
    }

    #[test]
    fn handle_key_event_ctrl_shortcuts_trigger_control_paths() {
        let mut cfg = AppConfig::parse_from(["test-app"]);
        cfg.persistent_codex = false;
        cfg.no_python_fallback = true;
        let mut app = CodexApp::new(cfg);

        let ctrl_r = handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Char('r'), KeyModifiers::CONTROL),
        );
        assert!(ctrl_r.is_err(), "ctrl+r should invoke voice path and error");
        assert!(app.sanitized_input_text().is_empty());

        let ctrl_v = handle_key_event(
            &mut app,
            KeyEvent::new(KeyCode::Char('v'), KeyModifiers::CONTROL),
        );
        assert!(
            ctrl_v.is_err(),
            "ctrl+v should invoke voice-mode path and error"
        );
        assert!(app.sanitized_input_text().is_empty());
    }

    #[test]
    fn sanitize_output_line_covers_control_and_width_edge_cases() {
        assert_eq!(sanitize_output_line("   "), "");
        assert_eq!(sanitize_output_line("a\u{0007}b"), "ab");
        assert_eq!(sanitize_output_line("\u{0007}abc"), "abc");
        assert_eq!(sanitize_output_line("\u{001f}abc"), "abc");
        assert_eq!(sanitize_output_line("\u{200b}abc\u{200b}"), "abc");
        assert_eq!(sanitize_output_line("\u{feff}abc\u{feff}"), "abc");
        assert_eq!(sanitize_output_line(" abc"), " abc");
        assert_eq!(sanitize_output_line("a\tb"), "a\tb");
        assert_eq!(sanitize_output_line("a\nb"), "a\nb");
        assert_eq!(sanitize_output_line("A\u{200B}B"), "A B");
        assert_eq!(sanitize_output_line("`cmd`"), "'cmd'");
        assert!(sanitize_output_line(&"x".repeat(600)).ends_with('…'));
        assert!(!sanitize_output_line(&"x".repeat(500)).ends_with('…'));
    }
}
