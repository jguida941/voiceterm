//! First-run onboarding hint persistence so setup guidance can be dismissed permanently.

use std::env;
use std::fs;
use std::path::PathBuf;

use voiceterm::log_debug;

const ONBOARDING_STATE_ENV: &str = "VOICETERM_ONBOARDING_STATE";
const ONBOARDING_STATE_FILE: &str = "onboarding_state.toml";

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
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
    // Intentional minimal parser: a single boolean key keeps startup overhead low
    // and avoids a full TOML dependency for this one-file state marker.
    for line in contents.lines() {
        let line = line.trim();
        if let Some(value) = line.strip_prefix("completed_first_capture") {
            if let Some(value) = value.split('=').nth(1) {
                let normalized = value.trim().trim_matches('"').to_ascii_lowercase();
                return OnboardingState {
                    completed_first_capture: matches!(normalized.as_str(), "true" | "1" | "yes"),
                };
            }
        }
    }
    OnboardingState::default()
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

    if let Some(parent) = path.parent() {
        if let Err(err) = fs::create_dir_all(parent) {
            log_debug(&format!(
                "failed to create onboarding state directory {}: {err}",
                parent.display()
            ));
            return;
        }
    }

    let body = format!(
        "completed_first_capture = {}\n",
        if state.completed_first_capture {
            "true"
        } else {
            "false"
        }
    );
    if let Err(err) = fs::write(&path, body) {
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
    use std::sync::{Mutex, OnceLock};
    use std::time::{SystemTime, UNIX_EPOCH};

    fn env_lock() -> std::sync::MutexGuard<'static, ()> {
        static ENV_GUARD: OnceLock<Mutex<()>> = OnceLock::new();
        ENV_GUARD
            .get_or_init(|| Mutex::new(()))
            .lock()
            .unwrap_or_else(|e| e.into_inner())
    }

    fn unique_path() -> PathBuf {
        let millis = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_millis())
            .unwrap_or(0);
        env::temp_dir().join(format!("voiceterm_onboarding_{millis}.toml"))
    }

    #[test]
    fn should_show_hint_when_state_file_missing() {
        let _guard = env_lock();
        let path = unique_path();
        let _ = fs::remove_file(&path);
        env::set_var(ONBOARDING_STATE_ENV, &path);

        assert!(should_show_hint());

        env::remove_var(ONBOARDING_STATE_ENV);
        let _ = fs::remove_file(path);
    }

    #[test]
    fn mark_first_capture_complete_persists_state() {
        let _guard = env_lock();
        let path = unique_path();
        let _ = fs::remove_file(&path);
        env::set_var(ONBOARDING_STATE_ENV, &path);

        assert!(should_show_hint());
        mark_first_capture_complete();
        assert!(!should_show_hint());

        let written = fs::read_to_string(&path).expect("state should be written");
        assert!(written.contains("completed_first_capture = true"));

        env::remove_var(ONBOARDING_STATE_ENV);
        let _ = fs::remove_file(path);
    }
}
