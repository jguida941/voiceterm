//! Terminal-state guards that prevent broken shells after exit or panic paths.

use crossterm::{
    cursor::Show,
    event::DisableMouseCapture,
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use std::{
    io::{self, Write},
    panic,
    sync::{
        atomic::{AtomicBool, Ordering},
        OnceLock,
    },
};

static RAW_MODE_ENABLED: AtomicBool = AtomicBool::new(false);
static ALT_SCREEN_ENABLED: AtomicBool = AtomicBool::new(false);
static MOUSE_CAPTURE_ENABLED: AtomicBool = AtomicBool::new(false);
static PANIC_HOOK_INSTALLED: OnceLock<()> = OnceLock::new();

/// RAII guard to restore terminal state on drop (and on panic via a shared hook).
pub struct TerminalRestoreGuard;

impl TerminalRestoreGuard {
    /// Create a guard and install the shared panic hook (once).
    #[must_use]
    pub fn new() -> Self {
        install_terminal_panic_hook();
        TerminalRestoreGuard
    }

    /// Enable terminal raw mode and track state for guaranteed restoration.
    ///
    /// # Errors
    ///
    /// Returns an error if the terminal cannot enter raw mode.
    pub fn enable_raw_mode(&self) -> io::Result<()> {
        enable_raw_mode()?;
        RAW_MODE_ENABLED.store(true, Ordering::SeqCst);
        Ok(())
    }

    /// Enter alternate screen and track state for guaranteed restoration.
    ///
    /// # Errors
    ///
    /// Returns an error if alternate-screen activation fails.
    pub fn enter_alt_screen(&self, stdout: &mut impl Write) -> io::Result<()> {
        execute!(stdout, EnterAlternateScreen)?;
        ALT_SCREEN_ENABLED.store(true, Ordering::SeqCst);
        Ok(())
    }

    #[allow(dead_code)]
    /// Enable mouse capture and track state for guaranteed restoration.
    ///
    /// # Errors
    ///
    /// Returns an error if mouse capture cannot be enabled.
    pub fn enable_mouse_capture(&self, stdout: &mut impl Write) -> io::Result<()> {
        execute!(stdout, crossterm::event::EnableMouseCapture)?;
        MOUSE_CAPTURE_ENABLED.store(true, Ordering::SeqCst);
        Ok(())
    }

    /// Restore all tracked terminal state immediately.
    pub fn restore(&self) {
        restore_terminal();
    }
}

impl Default for TerminalRestoreGuard {
    fn default() -> Self {
        Self::new()
    }
}

impl Drop for TerminalRestoreGuard {
    fn drop(&mut self) {
        restore_terminal();
    }
}

/// Restore terminal raw mode, mouse capture, alt-screen, and cursor visibility.
pub fn restore_terminal() {
    if RAW_MODE_ENABLED.swap(false, Ordering::SeqCst) {
        let _ = disable_raw_mode();
    }
    let mut stdout = io::stdout();
    if MOUSE_CAPTURE_ENABLED.swap(false, Ordering::SeqCst) {
        let _ = execute!(stdout, DisableMouseCapture);
    }
    if ALT_SCREEN_ENABLED.swap(false, Ordering::SeqCst) {
        let _ = execute!(stdout, LeaveAlternateScreen);
    }
    let _ = execute!(stdout, Show);
    let _ = stdout.flush();
}

/// Install a panic hook that restores terminal state before delegating.
pub fn install_terminal_panic_hook() {
    PANIC_HOOK_INSTALLED.get_or_init(|| {
        let previous = panic::take_hook();
        panic::set_hook(Box::new(move |info| {
            restore_terminal();
            let location = info
                .location()
                .map(|loc| format!("{}:{}", loc.file(), loc.line()))
                .unwrap_or_else(|| "unknown".to_string());
            let payload = if let Some(text) = info.payload().downcast_ref::<&str>() {
                (*text).to_string()
            } else if let Some(text) = info.payload().downcast_ref::<String>() {
                text.clone()
            } else {
                "non-string panic payload".to_string()
            };
            crate::log_panic(&location, &payload);
            crate::log_debug(&format!("panic at {location}"));
            crate::log_debug_content(&format!("panic: {info}"));
            previous(info);
        }));
    });
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    struct FailingWriter;

    impl Write for FailingWriter {
        fn write(&mut self, _buf: &[u8]) -> io::Result<usize> {
            Err(io::Error::other("intentional write failure"))
        }

        fn flush(&mut self) -> io::Result<()> {
            Err(io::Error::other("intentional flush failure"))
        }
    }

    fn test_lock() -> &'static Mutex<()> {
        static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        LOCK.get_or_init(|| Mutex::new(()))
    }

    #[test]
    fn install_terminal_panic_hook_sets_once_flag() {
        let _guard = test_lock().lock().expect("test lock");
        install_terminal_panic_hook();
        assert!(PANIC_HOOK_INSTALLED.get().is_some());
    }

    #[test]
    fn restore_terminal_clears_state_flags() {
        let _guard = test_lock().lock().expect("test lock");
        RAW_MODE_ENABLED.store(true, Ordering::SeqCst);
        ALT_SCREEN_ENABLED.store(true, Ordering::SeqCst);
        MOUSE_CAPTURE_ENABLED.store(true, Ordering::SeqCst);
        restore_terminal();
        assert!(!RAW_MODE_ENABLED.load(Ordering::SeqCst));
        assert!(!ALT_SCREEN_ENABLED.load(Ordering::SeqCst));
        assert!(!MOUSE_CAPTURE_ENABLED.load(Ordering::SeqCst));
    }

    #[test]
    fn guard_restore_delegates_to_restore_terminal() {
        let _guard = test_lock().lock().expect("test lock");
        RAW_MODE_ENABLED.store(true, Ordering::SeqCst);
        let guard = TerminalRestoreGuard::new();
        guard.restore();
        assert!(!RAW_MODE_ENABLED.load(Ordering::SeqCst));
    }

    #[test]
    fn guard_drop_restores_terminal_state() {
        let _guard = test_lock().lock().expect("test lock");
        ALT_SCREEN_ENABLED.store(true, Ordering::SeqCst);
        {
            let _guard = TerminalRestoreGuard::new();
        }
        assert!(!ALT_SCREEN_ENABLED.load(Ordering::SeqCst));
    }

    #[test]
    fn enable_raw_mode_sets_flag_on_success_and_never_sets_it_on_error() {
        let _guard = test_lock().lock().expect("test lock");
        RAW_MODE_ENABLED.store(false, Ordering::SeqCst);
        let guard = TerminalRestoreGuard::new();
        let result = guard.enable_raw_mode();
        if result.is_ok() {
            assert!(RAW_MODE_ENABLED.load(Ordering::SeqCst));
            restore_terminal();
        } else {
            assert!(!RAW_MODE_ENABLED.load(Ordering::SeqCst));
        }
    }

    #[test]
    fn enter_alt_screen_propagates_writer_errors_without_setting_flag() {
        let _guard = test_lock().lock().expect("test lock");
        ALT_SCREEN_ENABLED.store(false, Ordering::SeqCst);
        let guard = TerminalRestoreGuard::new();
        let mut writer = FailingWriter;
        let err = guard
            .enter_alt_screen(&mut writer)
            .expect_err("write error should bubble up");
        assert_eq!(err.kind(), io::ErrorKind::Other);
        assert!(!ALT_SCREEN_ENABLED.load(Ordering::SeqCst));
    }

    #[test]
    fn enable_mouse_capture_propagates_writer_errors_without_setting_flag() {
        let _guard = test_lock().lock().expect("test lock");
        MOUSE_CAPTURE_ENABLED.store(false, Ordering::SeqCst);
        let guard = TerminalRestoreGuard::new();
        let mut writer = FailingWriter;
        let err = guard
            .enable_mouse_capture(&mut writer)
            .expect_err("write error should bubble up");
        assert_eq!(err.kind(), io::ErrorKind::Other);
        assert!(!MOUSE_CAPTURE_ENABLED.load(Ordering::SeqCst));
    }
}
