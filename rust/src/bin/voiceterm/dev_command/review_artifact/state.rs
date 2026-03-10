use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::time::Instant;

use super::artifact::{parse_review_artifact, ReviewArtifact};

fn content_hash(content: &str) -> u64 {
    let mut hasher = DefaultHasher::new();
    content.hash(&mut hasher);
    hasher.finish()
}

/// Which view mode is active inside the Review tab.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub(crate) enum ReviewViewMode {
    #[default]
    Parsed,
    Raw,
}

impl ReviewViewMode {
    pub(crate) fn toggle(self) -> Self {
        match self {
            Self::Parsed => Self::Raw,
            Self::Raw => Self::Parsed,
        }
    }

    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Parsed => "parsed",
            Self::Raw => "raw",
        }
    }
}

/// State for the review artifact surface within the Dev panel.
#[derive(Debug, Clone, Default)]
pub(crate) struct ReviewArtifactState {
    artifact: Option<ReviewArtifact>,
    raw_content: String,
    view_mode: ReviewViewMode,
    loaded_at: Option<Instant>,
    scroll_offset: usize,
    load_error: Option<String>,
    /// Content fingerprint from the last successful load, used by periodic
    /// polling to skip redundant re-parses when the file hasn't changed.
    /// Uses SipHash for fast, collision-resistant comparison that catches
    /// same-length edits (unlike a length-only check).
    last_content_hash: u64,
}

use crate::scrollable::Scrollable;

impl Scrollable for ReviewArtifactState {
    fn scroll_offset(&self) -> usize {
        self.scroll_offset
    }

    fn scroll_offset_mut(&mut self) -> &mut usize {
        &mut self.scroll_offset
    }
}

impl ReviewArtifactState {
    pub(crate) fn artifact(&self) -> Option<&ReviewArtifact> {
        self.artifact.as_ref()
    }

    pub(crate) fn load_error(&self) -> Option<&str> {
        self.load_error.as_deref()
    }

    pub(crate) fn view_mode(&self) -> ReviewViewMode {
        self.view_mode
    }

    /// True when the review surface should render the three-lane column layout
    /// (parsed mode with a loaded artifact). False for raw view, error, or empty.
    pub(crate) fn is_lane_mode(&self) -> bool {
        self.view_mode == ReviewViewMode::Parsed && self.artifact.is_some()
    }

    pub(crate) fn toggle_view_mode(&mut self) {
        self.view_mode = self.view_mode.toggle();
        self.scroll_offset = 0;
    }

    pub(crate) fn raw_content(&self) -> &str {
        &self.raw_content
    }

    #[cfg(test)]
    pub(crate) fn load_from_content(&mut self, content: &str) {
        self.load_from_artifact(content, parse_review_artifact(content));
    }

    pub(crate) fn load_from_artifact(&mut self, raw_content: &str, artifact: ReviewArtifact) {
        self.artifact = Some(artifact);
        self.raw_content = raw_content.to_string();
        self.loaded_at = Some(Instant::now());
        self.load_error = None;
        self.scroll_offset = 0;
        self.last_content_hash = content_hash(raw_content);
    }

    /// Returns true if the content differs from the last load, or if the
    /// previous read failed and a successful reload should clear stale error
    /// state. Uses a content hash so same-length edits are still detected.
    pub(crate) fn content_changed(&self, new_content: &str) -> bool {
        self.artifact.is_none()
            || self.load_error.is_some()
            || content_hash(new_content) != self.last_content_hash
    }

    pub(crate) fn set_load_error(&mut self, error: String) {
        self.load_error = Some(error);
        self.loaded_at = Some(Instant::now());
        // Keep the last successful parse available for read-only handoff and
        // resume surfaces; a transient read failure should not erase bridge state.
        if self.artifact.is_none() {
            self.scroll_offset = 0;
        }
    }

    /// Available for elapsed-time display in the Review footer; not yet wired.
    pub(crate) fn loaded_at(&self) -> Option<Instant> {
        self.loaded_at
    }
}
