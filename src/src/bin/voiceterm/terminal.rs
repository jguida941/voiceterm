//! Terminal resize handling so PTY geometry stays aligned with the visible HUD.

use anyhow::{anyhow, Result};
use crossterm::terminal::size as terminal_size;
use std::sync::atomic::{AtomicBool, Ordering};
use voiceterm::log_debug;
use voiceterm::pty_session::PtyOverlaySession;

use crate::config::HudStyle;
use crate::help::help_overlay_height;
use crate::settings::settings_overlay_height;
use crate::status_line::status_banner_height_with_policy;
use crate::theme_picker::theme_picker_height;
use crate::theme_studio::theme_studio_height;
use crate::OverlayMode;

/// Flag set by SIGWINCH handler to trigger terminal resize.
static SIGWINCH_RECEIVED: AtomicBool = AtomicBool::new(false);

/// Signal handler for terminal resize events.
///
/// Sets a flag that the main loop checks to update PTY dimensions.
/// Only uses atomic operations (async-signal-safe).
extern "C" fn handle_sigwinch(_: libc::c_int) {
    SIGWINCH_RECEIVED.store(true, Ordering::SeqCst);
}

pub(crate) fn install_sigwinch_handler() -> Result<()> {
    unsafe {
        // SAFETY: handle_sigwinch is an extern "C" signal handler with no side effects
        // beyond flipping an atomic flag, which is async-signal-safe.
        let handler = handle_sigwinch as *const () as libc::sighandler_t;
        if libc::signal(libc::SIGWINCH, handler) == libc::SIG_ERR {
            log_debug("failed to install SIGWINCH handler");
            return Err(anyhow!("failed to install SIGWINCH handler"));
        }
    }
    Ok(())
}

pub(crate) fn take_sigwinch() -> bool {
    SIGWINCH_RECEIVED.swap(false, Ordering::SeqCst)
}

pub(crate) fn resolved_cols(cached: u16) -> u16 {
    if cached == 0 {
        terminal_size().map(|(c, _)| c).unwrap_or(80)
    } else {
        cached
    }
}

pub(crate) fn resolved_rows(cached: u16) -> u16 {
    if cached == 0 {
        terminal_size().map(|(_, r)| r).unwrap_or(24)
    } else {
        cached
    }
}

pub(crate) fn reserved_rows_for_mode(
    mode: OverlayMode,
    cols: u16,
    hud_style: HudStyle,
    claude_prompt_suppressed: bool,
) -> usize {
    match mode {
        OverlayMode::None => {
            status_banner_height_with_policy(cols as usize, hud_style, claude_prompt_suppressed)
        }
        OverlayMode::Help => help_overlay_height(),
        OverlayMode::ThemeStudio => theme_studio_height(),
        OverlayMode::ThemePicker => theme_picker_height(),
        OverlayMode::Settings => settings_overlay_height(),
        OverlayMode::TranscriptHistory => {
            crate::transcript_history::transcript_history_overlay_height()
        }
        // Toast history uses a fixed default height estimate since the actual
        // height depends on runtime state; 10 rows is a safe conservative value.
        OverlayMode::ToastHistory => 10,
        // Memory Browser and Action Center use the same height as transcript history
        // for the initial iteration (placeholder until dedicated overlays are built).
        OverlayMode::MemoryBrowser | OverlayMode::ActionCenter => {
            crate::transcript_history::transcript_history_overlay_height()
        }
    }
}

pub(crate) fn apply_pty_winsize(
    session: &mut PtyOverlaySession,
    rows: u16,
    cols: u16,
    mode: OverlayMode,
    hud_style: HudStyle,
    claude_prompt_suppressed: bool,
) {
    if rows == 0 || cols == 0 {
        return;
    }
    let reserved = reserved_rows_for_mode(mode, cols, hud_style, claude_prompt_suppressed) as u16;
    let pty_rows = rows.saturating_sub(reserved).max(1);
    let _ = session.set_winsize(pty_rows, cols);
}

pub(crate) fn update_pty_winsize(
    session: &mut PtyOverlaySession,
    terminal_rows: &mut u16,
    terminal_cols: &mut u16,
    mode: OverlayMode,
    hud_style: HudStyle,
    claude_prompt_suppressed: bool,
) {
    let rows = resolved_rows(*terminal_rows);
    let cols = resolved_cols(*terminal_cols);
    *terminal_rows = rows;
    *terminal_cols = cols;
    apply_pty_winsize(
        session,
        rows,
        cols,
        mode,
        hud_style,
        claude_prompt_suppressed,
    );
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;
    use std::time::Duration;

    #[test]
    fn sigwinch_handler_sets_flag() {
        SIGWINCH_RECEIVED.store(false, Ordering::SeqCst);
        handle_sigwinch(0);
        assert!(SIGWINCH_RECEIVED.swap(false, Ordering::SeqCst));
    }

    #[test]
    fn take_sigwinch_returns_true_once_and_clears_flag() {
        SIGWINCH_RECEIVED.store(true, Ordering::SeqCst);
        assert!(take_sigwinch());
        assert!(!take_sigwinch());
    }

    #[test]
    fn take_sigwinch_returns_false_when_unset() {
        SIGWINCH_RECEIVED.store(false, Ordering::SeqCst);
        assert!(!take_sigwinch());
    }

    #[test]
    fn install_sigwinch_handler_installs_handler() {
        SIGWINCH_RECEIVED.store(false, Ordering::SeqCst);
        install_sigwinch_handler().expect("install sigwinch handler");
        unsafe {
            // SAFETY: raising SIGWINCH in-process is used for test validation only.
            libc::raise(libc::SIGWINCH);
        }
        for _ in 0..20 {
            if SIGWINCH_RECEIVED.swap(false, Ordering::SeqCst) {
                return;
            }
            thread::sleep(Duration::from_millis(5));
        }
        panic!("SIGWINCH was not received");
    }

    #[test]
    fn resolved_cols_rows_use_cache() {
        assert_eq!(resolved_cols(123), 123);
        assert_eq!(resolved_rows(45), 45);
    }

    #[test]
    fn reserved_rows_for_mode_matches_helpers() {
        let cols = 80;
        assert_eq!(
            reserved_rows_for_mode(OverlayMode::None, cols, HudStyle::Full, false),
            status_banner_height_with_policy(cols as usize, HudStyle::Full, false)
        );
        assert_eq!(
            reserved_rows_for_mode(OverlayMode::Help, cols, HudStyle::Full, false),
            help_overlay_height()
        );
        assert_eq!(
            reserved_rows_for_mode(OverlayMode::ThemePicker, cols, HudStyle::Full, false),
            theme_picker_height()
        );
        assert_eq!(
            reserved_rows_for_mode(OverlayMode::Settings, cols, HudStyle::Full, false),
            settings_overlay_height()
        );
    }

    #[test]
    fn reserved_rows_for_mode_drops_banner_rows_when_prompt_suppressed() {
        assert_eq!(
            reserved_rows_for_mode(OverlayMode::None, 120, HudStyle::Full, true),
            0
        );
    }

    #[cfg(all(unix, feature = "mutants"))]
    #[test]
    fn apply_pty_winsize_updates_session_size() {
        let mut session =
            PtyOverlaySession::new("cat", ".", &[], "xterm-256color").expect("pty session");
        let rows = 30;
        let cols = 100;
        apply_pty_winsize(
            &mut session,
            rows,
            cols,
            OverlayMode::None,
            HudStyle::Full,
            false,
        );
        let reserved =
            reserved_rows_for_mode(OverlayMode::None, cols, HudStyle::Full, false) as u16;
        let expected_rows = rows.saturating_sub(reserved).max(1);
        let (set_rows, set_cols) = session.current_winsize();
        assert_eq!(set_cols, cols);
        assert_eq!(set_rows, expected_rows);

        let before = session.current_winsize();
        apply_pty_winsize(
            &mut session,
            0,
            cols,
            OverlayMode::None,
            HudStyle::Full,
            false,
        );
        assert_eq!(session.current_winsize(), before);
    }

    #[cfg(unix)]
    #[test]
    fn update_pty_winsize_updates_cached_dimensions() {
        let mut session =
            PtyOverlaySession::new("cat", ".", &[], "xterm-256color").expect("pty session");
        let mut rows = 0;
        let mut cols = 0;
        update_pty_winsize(
            &mut session,
            &mut rows,
            &mut cols,
            OverlayMode::None,
            HudStyle::Full,
            false,
        );
        assert!(rows > 0);
        assert!(cols > 0);
    }
}
