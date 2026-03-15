//! First-run onboarding hint persistence so setup guidance can be dismissed permanently.

use std::env;
use std::fs;
use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use voiceterm::log_debug;

use crate::persistence_io::write_text_atomically;

const ONBOARDING_STATE_ENV: &str = "VOICETERM_ONBOARDING_STATE";
const ONBOARDING_STATE_FILE: &str = "onboarding_state.toml";

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default)]
struct OnboardingState {
    completed_first_capture: bool,
}

fn onboarding_state_path() -> Option<PathBuf> {
    if let Ok(path) = env::var(ONBOARDING_STATE_ENV) {
        let trimmed = path.trim();
        if !trimmed.is_empty() {
            return Some(PathBuf::from(trimmed));
        }
    }
    let home = env::var("HOME").ok()?;
    Some(
        PathBuf::from(home)
            .join(".config")
            .join("voiceterm")
            .join(ONBOARDING_STATE_FILE),
    )
}

fn parse_state(contents: &str) -> OnboardingState {
    toml::from_str(contents).unwrap_or_default()
}

fn load_state() -> OnboardingState {
    let Some(path) = onboarding_state_path() else {
        return OnboardingState::default();
    };
    match fs::read_to_string(&path) {
        Ok(contents) => parse_state(&contents),
        Err(_) => OnboardingState::default(),
    }
}

fn save_state(state: OnboardingState) {
    let Some(path) = onboarding_state_path() else {
        return;
    };

    let body = match toml::to_string(&state) {
        Ok(body) => body,
        Err(err) => {
            log_debug(&format!("failed to serialize onboarding state: {err}"));
            return;
        }
    };
    if let Err(err) = write_text_atomically(&path, &body) {
        log_debug(&format!(
            "failed to write onboarding state {}: {err}",
            path.display()
        ));
    }
}

/// Return whether the first-run guidance hint should be shown.
#[must_use]
pub(crate) fn should_show_hint() -> bool {
    !load_state().completed_first_capture
}

/// Mark first successful capture as complete.
pub(crate) fn mark_first_capture_complete() {
    let state = load_state();
    if state.completed_first_capture {
        return;
    }
    save_state(OnboardingState {
        completed_first_capture: true,
    });
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_env::with_env_overrides;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn unique_path() -> PathBuf {
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0);
        let pid = std::process::id();
        env::temp_dir().join(format!("voiceterm_onboarding_{pid}_{nanos}.toml"))
    }

    #[test]
    fn should_show_hint_when_state_file_missing() {
        let path = unique_path();
        let _ = fs::remove_file(&path);
        let path_string = path.display().to_string();
        with_env_overrides(
            &[ONBOARDING_STATE_ENV],
            &[(ONBOARDING_STATE_ENV, Some(path_string.as_str()))],
            || {
                assert!(should_show_hint());
            },
        );
        let _ = fs::remove_file(path);
    }

    #[test]
    fn mark_first_capture_complete_persists_state() {
        let path = unique_path();
        let _ = fs::remove_file(&path);
        let path_string = path.display().to_string();
        with_env_overrides(
            &[ONBOARDING_STATE_ENV],
            &[(ONBOARDING_STATE_ENV, Some(path_string.as_str()))],
            || {
                assert!(should_show_hint());
                mark_first_capture_complete();
                assert!(!should_show_hint());
            },
        );

        let written = fs::read_to_string(&path).expect("state should be written");
        let parsed = parse_state(&written);
        assert!(parsed.completed_first_capture);
        let _ = fs::remove_file(path);
    }
}
