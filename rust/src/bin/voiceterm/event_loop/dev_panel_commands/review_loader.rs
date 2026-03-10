//! Review artifact loading and polling for the Review tab.

use super::super::*;
use super::git_snapshot::resolve_session_working_dir;
use std::path::Path;

fn find_review_artifact_path(
    state: &EventLoopState,
    session: &voiceterm::pty_session::PtyOverlaySession,
) -> Option<std::path::PathBuf> {
    let session_dir = resolve_session_working_dir(session.child_pid());
    crate::dev_command::find_review_artifact_path(
        session_dir.as_deref(),
        Some(Path::new(&state.working_dir)),
    )
}

pub(in super::super) fn load_review(
    state: &mut EventLoopState,
    session: &voiceterm::pty_session::PtyOverlaySession,
) {
    let Some(path) = find_review_artifact_path(state, session) else {
        state
            .dev_panel_commands
            .review_mut()
            .set_load_error("review artifact not found in repo".to_string());
        return;
    };
    match crate::dev_command::load_review_artifact_document(&path) {
        Ok(document) => {
            state
                .dev_panel_commands
                .review_mut()
                .load_from_artifact(&document.raw_content, document.artifact);
        }
        Err(err) => {
            state
                .dev_panel_commands
                .review_mut()
                .set_load_error(format!("Failed to read review artifact: {err}"));
        }
    }
}

/// Periodic-poll variant: reads the file but skips re-parse + scroll reset
/// when the content hash is unchanged. Returns true if content was refreshed.
pub(in super::super) fn poll_review(
    state: &mut EventLoopState,
    session: &voiceterm::pty_session::PtyOverlaySession,
) -> bool {
    let Some(path) = find_review_artifact_path(state, session) else {
        state
            .dev_panel_commands
            .review_mut()
            .set_load_error("review artifact not found in repo".to_string());
        return true;
    };
    match crate::dev_command::load_review_artifact_document(&path) {
        Ok(document) => {
            if state
                .dev_panel_commands
                .review()
                .content_changed(&document.raw_content)
            {
                state
                    .dev_panel_commands
                    .review_mut()
                    .load_from_artifact(&document.raw_content, document.artifact);
                true
            } else {
                false
            }
        }
        Err(err) => {
            state
                .dev_panel_commands
                .review_mut()
                .set_load_error(format!("Failed to read review artifact: {err}"));
            true
        }
    }
}
