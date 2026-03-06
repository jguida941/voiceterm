//! Prompt subsystem wiring so readiness detection and logging share one policy.

pub(crate) mod claude_prompt_detect;
mod logger;
pub(crate) mod occlusion_shared;
pub(crate) mod occlusion_signals;
mod regex;
mod strip;
mod tracker;

pub(crate) use claude_prompt_detect::ClaudePromptDetector;
pub(crate) use claude_prompt_detect::PromptType;
#[derive(Debug)]
pub(crate) enum PromptOcclusionDetector {
    Claude(ClaudePromptDetector),
}

impl PromptOcclusionDetector {
    #[cfg(test)]
    pub(crate) fn new(prompt_guard_enabled: bool) -> Self {
        Self::Claude(ClaudePromptDetector::new(prompt_guard_enabled))
    }

    pub(crate) fn new_for_backend(backend_label: &str) -> Self {
        Self::Claude(ClaudePromptDetector::new_for_backend(backend_label))
    }

    pub(crate) fn feed_output(&mut self, bytes: &[u8]) -> bool {
        match self {
            Self::Claude(detector) => detector.feed_output(bytes),
        }
    }

    pub(crate) fn activate_startup_guard(&mut self) {
        match self {
            Self::Claude(detector) => detector.activate_startup_guard(),
        }
    }

    pub(crate) fn should_suppress_hud(&self) -> bool {
        match self {
            Self::Claude(detector) => detector.should_suppress_hud(),
        }
    }

    pub(crate) fn on_user_input(&mut self) {
        match self {
            Self::Claude(detector) => detector.on_user_input(),
        }
    }

    pub(crate) fn should_resolve_on_input(&self, bytes: &[u8]) -> bool {
        match self {
            Self::Claude(detector) => detector.should_resolve_on_input(bytes),
        }
    }

    pub(crate) fn take_ready_marker_resolution_kind(&mut self) -> Option<PromptType> {
        match self {
            Self::Claude(detector) => detector.take_ready_marker_resolution_kind(),
        }
    }

    #[cfg(test)]
    pub(crate) fn is_enabled(&self) -> bool {
        match self {
            Self::Claude(detector) => detector.is_enabled(),
        }
    }
}

pub(crate) use logger::{resolve_prompt_log, PromptLogger};
pub(crate) use regex::resolve_prompt_regex;
pub(crate) use tracker::{should_auto_trigger, PromptTracker};
