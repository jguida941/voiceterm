//! Terminal resize handling so PTY geometry stays aligned with the visible HUD.

use anyhow::{anyhow, Result};
use crossterm::terminal::size as terminal_size;
use std::env;
use std::sync::atomic::{AtomicBool, Ordering};
use voiceterm::log_debug;
use voiceterm::pty_session::PtyOverlaySession;

use crate::config::HudStyle;
use crate::dev_panel::dev_panel_height;
use crate::help::help_overlay_height;
use crate::runtime_compat::{self, BackendFamily};
use crate::settings::settings_overlay_height;
use crate::status_line::status_banner_height_with_policy;
use crate::theme_picker::theme_picker_height;
use crate::theme_studio::theme_studio_height;
use crate::OverlayMode;

/// Flag set by SIGWINCH handler to trigger terminal resize.
static SIGWINCH_RECEIVED: AtomicBool = AtomicBool::new(false);

fn parse_debug_env_flag(raw: &str) -> bool {
    matches!(
        raw.trim().to_ascii_lowercase().as_str(),
        "1" | "true" | "yes" | "on" | "debug"
    )
}

fn claude_hud_debug_enabled() -> bool {
    std::env::var("VOICETERM_DEBUG_CLAUDE_HUD")
        .map(|raw| parse_debug_env_flag(&raw))
        .unwrap_or(cfg!(debug_assertions))
}

/// Signal handler for terminal resize events.
///
/// Sets a flag that the main loop checks to update PTY dimensions.
/// Only uses atomic operations (async-signal-safe).
extern "C" fn handle_sigwinch(_: libc::c_int) {
    SIGWINCH_RECEIVED.store(true, Ordering::SeqCst);
}

pub(crate) fn install_sigwinch_handler() -> Result<()> {
    unsafe {
        // SAFETY: We install an async-signal-safe handler that only sets an atomic flag.
        // `sigemptyset` and `sigaction` are called with initialized pointers and checked
        // for non-zero error returns.
        let mut action: libc::sigaction = std::mem::zeroed();
        action.sa_flags = libc::SA_RESTART;
        action.sa_sigaction = handle_sigwinch as *const () as usize;
        if libc::sigemptyset(&mut action.sa_mask) != 0 {
            log_debug("failed to clear SIGWINCH mask");
            return Err(anyhow!("failed to clear SIGWINCH mask"));
        }
        if libc::sigaction(libc::SIGWINCH, &action, std::ptr::null_mut()) != 0 {
            log_debug("failed to install SIGWINCH handler");
            return Err(anyhow!("failed to install SIGWINCH handler"));
        }
    }
    Ok(())
}

pub(crate) fn take_sigwinch() -> bool {
    SIGWINCH_RECEIVED.swap(false, Ordering::SeqCst)
}

fn parse_env_dimension(key: &str) -> Option<u16> {
    env::var(key)
        .ok()
        .and_then(|value| value.trim().parse::<u16>().ok())
        .filter(|value| *value > 0)
}

fn normalize_dimension(observed: u16, env_fallback: Option<u16>, default_value: u16) -> u16 {
    if observed > 0 {
        observed
    } else {
        env_fallback.unwrap_or(default_value)
    }
}

pub(crate) fn resolved_cols(cached: u16) -> u16 {
    if cached == 0 {
        match terminal_size() {
            Ok((cols, _)) => normalize_dimension(cols, parse_env_dimension("COLUMNS"), 80),
            Err(_) => parse_env_dimension("COLUMNS").unwrap_or(80),
        }
    } else {
        cached
    }
}

pub(crate) fn resolved_rows(cached: u16) -> u16 {
    if cached == 0 {
        match terminal_size() {
            Ok((_, rows)) => normalize_dimension(rows, parse_env_dimension("LINES"), 24),
            Err(_) => parse_env_dimension("LINES").unwrap_or(24),
        }
    } else {
        cached
    }
}

/// CRITICAL — HUD overlap fix: Returns `(terminal_rows, terminal_cols,
/// pty_rows, pty_cols)` with the PTY rows reduced by the HUD reservation.
/// This MUST be called before `PtyOverlaySession::new()`.  DO NOT remove the
/// reserved-row subtraction or move PTY creation before this call — backends
/// like Claude Code cache `process.stdout.rows` at startup and will lay out
/// their input prompt on the HUD rows, causing persistent overlap that no
/// later SIGWINCH can reliably fix.
pub(crate) fn startup_pty_geometry(hud_style: HudStyle) -> (u16, u16, u16, u16) {
    match terminal_size() {
        Ok((cols, rows)) => {
            let reserved = reserved_rows_for_mode(OverlayMode::None, cols, hud_style, false) as u16;
            (rows, cols, rows.saturating_sub(reserved).max(1), cols)
        }
        Err(_) => (0, 0, 24, 80),
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
            let backend = runtime_compat::backend_family_from_env();
            let base_unsuppressed =
                status_banner_height_with_policy(cols as usize, hud_style, false);
            if backend == BackendFamily::Codex {
                // Keep Codex at the stable v1.0.95 row budget in IDE terminals.
                // Extra guard rows can distort Codex prompt/composer placement.
                base_unsuppressed
            } else {
                // Keep a stable bottom buffer for Claude even while prompt suppression
                // is active so the terminal composer does not jump into HUD rows after
                // suppression transitions.
                let mut reserved =
                    base_unsuppressed + runtime_compat::resolved_hud_safety_gap_rows();
                if backend == BackendFamily::Claude {
                    reserved += runtime_compat::resolved_claude_extra_gap_rows();
                }
                if claude_prompt_suppressed && backend != BackendFamily::Claude {
                    status_banner_height_with_policy(cols as usize, hud_style, true)
                } else {
                    reserved
                }
            }
        }
        OverlayMode::DevPanel => dev_panel_height(),
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
        if claude_hud_debug_enabled() {
            log_debug(&format!(
                "[claude-hud-anomaly] apply_pty_winsize skipped due zero geometry (backend={:?}, mode={:?}, rows={}, cols={}, hud_style={:?}, prompt_suppressed={})",
                runtime_compat::backend_family_from_env(),
                mode,
                rows,
                cols,
                hud_style,
                claude_prompt_suppressed
            ));
        }
        return;
    }
    let reserved = reserved_rows_for_mode(mode, cols, hud_style, claude_prompt_suppressed) as u16;
    let pty_rows = rows.saturating_sub(reserved).max(1);
    if claude_hud_debug_enabled() {
        log_debug(&format!(
            "[claude-hud-debug] apply_pty_winsize (backend={:?}, mode={:?}, rows={}, cols={}, reserved_rows={}, pty_rows={}, hud_style={:?}, prompt_suppressed={})",
            runtime_compat::backend_family_from_env(),
            mode,
            rows,
            cols,
            reserved,
            pty_rows,
            hud_style,
            claude_prompt_suppressed
        ));
        if claude_prompt_suppressed && pty_rows <= 6 {
            log_debug(&format!(
                "[claude-hud-anomaly] prompt overlap risk: suppressed Claude prompt has very low PTY row budget (rows={}, reserved_rows={}, pty_rows={})",
                rows, reserved, pty_rows
            ));
        }
    }
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
    use std::env;
    use std::sync::{Mutex, OnceLock};
    use std::thread;
    use std::time::Duration;

    fn with_backend_env<T>(backend_label: Option<&str>, f: impl FnOnce() -> T) -> T {
        static ENV_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        let lock = ENV_LOCK.get_or_init(|| Mutex::new(()));
        let _guard = lock.lock().expect("env lock poisoned");
        let prev = env::var("VOICETERM_BACKEND_LABEL").ok();
        match backend_label {
            Some(label) => env::set_var("VOICETERM_BACKEND_LABEL", label),
            None => env::remove_var("VOICETERM_BACKEND_LABEL"),
        }
        let out = f();
        match prev {
            Some(value) => env::set_var("VOICETERM_BACKEND_LABEL", value),
            None => env::remove_var("VOICETERM_BACKEND_LABEL"),
        }
        out
    }

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
    fn normalize_dimension_prefers_observed_values() {
        assert_eq!(normalize_dimension(120, Some(90), 80), 120);
        assert_eq!(normalize_dimension(40, None, 80), 40);
    }

    #[test]
    fn normalize_dimension_falls_back_to_env_or_default_for_zero() {
        assert_eq!(normalize_dimension(0, Some(111), 80), 111);
        assert_eq!(normalize_dimension(0, None, 80), 80);
    }

    #[test]
    fn reserved_rows_for_mode_matches_helpers() {
        let cols = 80;
        let none_reserved = reserved_rows_for_mode(OverlayMode::None, cols, HudStyle::Full, false);
        assert!(
            none_reserved >= status_banner_height_with_policy(cols as usize, HudStyle::Full, false)
        );
        assert_eq!(
            reserved_rows_for_mode(OverlayMode::Help, cols, HudStyle::Full, false),
            help_overlay_height()
        );
        assert_eq!(
            reserved_rows_for_mode(OverlayMode::DevPanel, cols, HudStyle::Full, false),
            dev_panel_height()
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
    fn reserved_rows_for_mode_frees_rows_when_prompt_suppressed() {
        with_backend_env(None, || {
            assert_eq!(
                reserved_rows_for_mode(OverlayMode::None, 120, HudStyle::Full, true),
                0
            );
        });
    }

    #[test]
    fn reserved_rows_for_mode_keeps_claude_buffer_when_prompt_suppressed() {
        with_backend_env(Some("claude"), || {
            let unsuppressed =
                reserved_rows_for_mode(OverlayMode::None, 120, HudStyle::Full, false);
            let suppressed = reserved_rows_for_mode(OverlayMode::None, 120, HudStyle::Full, true);
            assert_eq!(suppressed, unsuppressed);
            assert!(suppressed > 0);
        });
    }

    #[cfg(all(unix, feature = "mutants"))]
    #[test]
    fn apply_pty_winsize_updates_session_size() {
        let mut session =
            PtyOverlaySession::new("cat", ".", &[], "xterm-256color", 24, 80).expect("pty session");
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
            PtyOverlaySession::new("cat", ".", &[], "xterm-256color", 24, 80).expect("pty session");
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
