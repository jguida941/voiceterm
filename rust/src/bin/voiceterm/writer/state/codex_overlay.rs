use super::*;
use crate::runtime_compat::BackendFamily;
use voiceterm::terminal_restore::{enter_alt_screen_tracked, leave_alt_screen_tracked};

const CLEAR_ISOLATED_SCREEN: &[u8] = b"\x1b[0m\x1b[2J\x1b[H";

/// Codex repaints large portions of its conversation while a turn is running.
/// Keep those bytes away from VoiceTerm overlays so the two renderers never
/// fight over the same rows. The primary terminal buffer is restored exactly
/// when the overlay closes, then accumulated Codex output is applied once.
#[derive(Debug, Default)]
pub(super) struct CodexOverlayIsolation {
    active: bool,
    buffered_pty: Vec<u8>,
}

impl CodexOverlayIsolation {
    pub(super) fn is_active(&self) -> bool {
        self.active
    }

    pub(super) fn buffer_pty_output(&mut self, bytes: Vec<u8>) -> Result<(), Vec<u8>> {
        if !self.active {
            return Err(bytes);
        }
        self.buffered_pty.extend_from_slice(&bytes);
        Ok(())
    }

    fn activate(&mut self) {
        self.active = true;
        self.buffered_pty.clear();
    }

    fn deactivate_and_take_output(&mut self) -> Vec<u8> {
        self.active = false;
        std::mem::take(&mut self.buffered_pty)
    }
}

pub(super) fn should_isolate_overlay(backend_family: BackendFamily) -> bool {
    backend_family == BackendFamily::Codex
}

impl WriterState {
    /// Start a Codex-only alternate-screen overlay. Claude intentionally keeps
    /// the existing in-place overlay and resize behavior unchanged.
    pub(super) fn begin_codex_overlay_isolation(&mut self) -> bool {
        if !should_isolate_overlay(self.runtime_profile.backend_family) {
            return false;
        }
        if self.codex_overlay_isolation.is_active() {
            return true;
        }
        if let Err(err) = enter_alt_screen_tracked(&mut self.stdout) {
            log_debug(&format!(
                "codex overlay isolation unavailable; using in-place overlay: {err}"
            ));
            return false;
        }
        self.codex_overlay_isolation.activate();
        if let Err(err) = self.stdout.write_all(CLEAR_ISOLATED_SCREEN) {
            log_debug(&format!(
                "codex overlay isolated-screen clear failed: {err}"
            ));
        }
        if let Err(err) = self.stdout.flush() {
            log_debug(&format!(
                "codex overlay isolated-screen flush failed: {err}"
            ));
        }
        true
    }

    /// Restore Codex's primary conversation screen and return all output that
    /// arrived while the overlay was active. The caller replays it only after
    /// overlay display state has been cleared.
    pub(super) fn end_codex_overlay_isolation(&mut self) -> Option<Vec<u8>> {
        if !self.codex_overlay_isolation.is_active() {
            return None;
        }
        let buffered = self.codex_overlay_isolation.deactivate_and_take_output();
        if let Err(err) = leave_alt_screen_tracked(&mut self.stdout) {
            log_debug(&format!(
                "codex overlay primary-screen restore failed: {err}"
            ));
        }
        Some(buffered)
    }

    pub(super) fn buffer_codex_overlay_output(&mut self, bytes: Vec<u8>) -> Result<(), Vec<u8>> {
        self.codex_overlay_isolation.buffer_pty_output(bytes)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn isolation_is_codex_only() {
        assert!(should_isolate_overlay(BackendFamily::Codex));
        assert!(!should_isolate_overlay(BackendFamily::Claude));
        assert!(!should_isolate_overlay(BackendFamily::Other));
    }

    #[test]
    fn active_isolation_buffers_and_releases_pty_bytes_in_order() {
        let mut isolation = CodexOverlayIsolation::default();
        assert_eq!(
            isolation.buffer_pty_output(b"before".to_vec()),
            Err(b"before".to_vec())
        );

        isolation.activate();
        assert_eq!(isolation.buffer_pty_output(b"first".to_vec()), Ok(()));
        assert_eq!(isolation.buffer_pty_output(b"-second".to_vec()), Ok(()));
        assert_eq!(isolation.deactivate_and_take_output(), b"first-second");
        assert!(!isolation.is_active());
        assert_eq!(
            isolation.buffer_pty_output(b"after".to_vec()),
            Err(b"after".to_vec())
        );
    }
}
