//! User-facing status message helpers so recurring errors stay actionable.

use voiceterm::log_file_path;

/// Append the active log-file location to an error prefix.
#[must_use]
pub(crate) fn with_log_path(prefix: &str) -> String {
    format!("{prefix} (log: {})", log_file_path().display())
}
