//! User-facing status message helpers so recurring errors stay actionable.

use anyhow::Error;
use voiceterm::log_file_path;

/// Append the active log-file location to an error prefix.
#[must_use]
pub(crate) fn with_log_path(prefix: &str) -> String {
    format!("{prefix} (log: {})", log_file_path().display())
}

/// Render a direct image-capture failure reason for immediate in-HUD debugging.
#[must_use]
pub(crate) fn image_capture_failed(err: &Error) -> String {
    let reason = err.root_cause().to_string();
    if reason.trim().is_empty() {
        with_log_path("Image capture failed")
    } else {
        format!("Image capture failed: {reason}")
    }
}
