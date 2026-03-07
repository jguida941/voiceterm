//! Runtime override state storage for style-pack, theme-file, and color overrides.
//!
//! Production builds use `OnceLock<Mutex<_>>` for thread-safe shared state.
//! Test builds use thread-local `Cell`/`RefCell` for deterministic isolation.

use super::super::runtime_overrides::RuntimeStylePackOverrides;
#[cfg(not(test))]
use super::super::ThemeColors;
#[cfg(test)]
use std::cell::{Cell, RefCell};
#[cfg(not(test))]
use std::sync::{Mutex, OnceLock};
#[cfg(not(test))]
use voiceterm::log_debug;

pub(crate) const STYLE_PACK_SCHEMA_ENV: &str = "VOICETERM_STYLE_PACK_JSON";
#[cfg(test)]
pub(crate) const STYLE_PACK_TEST_ENV_OPT_IN: &str = "VOICETERM_TEST_ENABLE_STYLE_PACK_ENV";

#[cfg(not(test))]
static RUNTIME_STYLE_PACK_OVERRIDES: OnceLock<Mutex<RuntimeStylePackOverrides>> = OnceLock::new();
#[cfg(not(test))]
static RUNTIME_COLOR_OVERRIDE: OnceLock<Mutex<Option<ThemeColors>>> = OnceLock::new();
#[cfg(not(test))]
static RUNTIME_THEME_FILE_OVERRIDE: OnceLock<Mutex<Option<String>>> = OnceLock::new();

#[cfg(test)]
thread_local! {
    static RUNTIME_STYLE_PACK_OVERRIDES: Cell<RuntimeStylePackOverrides> = const {
        Cell::new(RuntimeStylePackOverrides {
            border_style_override: None,
            glyph_set_override: None,
            indicator_set_override: None,
            toast_position_override: None,
            startup_style_override: None,
            progress_style_override: None,
            toast_severity_mode_override: None,
            banner_style_override: None,
            progress_bar_family_override: None,
            voice_scene_style_override: None,
        })
    };
    pub(crate) static RUNTIME_THEME_FILE_OVERRIDE_TEST: RefCell<Option<String>> = const { RefCell::new(None) };
}

#[cfg(not(test))]
fn runtime_style_pack_overrides_cell() -> &'static Mutex<RuntimeStylePackOverrides> {
    RUNTIME_STYLE_PACK_OVERRIDES.get_or_init(|| Mutex::new(RuntimeStylePackOverrides::default()))
}

#[must_use]
pub(crate) fn runtime_style_pack_overrides() -> RuntimeStylePackOverrides {
    #[cfg(test)]
    {
        RUNTIME_STYLE_PACK_OVERRIDES.with(Cell::get)
    }
    #[cfg(not(test))]
    match runtime_style_pack_overrides_cell().lock() {
        Ok(guard) => *guard,
        Err(poisoned) => {
            log_debug("runtime style-pack overrides lock poisoned; recovering read");
            *poisoned.into_inner()
        }
    }
}

pub(crate) fn set_runtime_style_pack_overrides(overrides: RuntimeStylePackOverrides) {
    #[cfg(test)]
    {
        RUNTIME_STYLE_PACK_OVERRIDES.with(|slot| slot.set(overrides));
    }
    #[cfg(not(test))]
    match runtime_style_pack_overrides_cell().lock() {
        Ok(mut guard) => *guard = overrides,
        Err(poisoned) => {
            log_debug("runtime style-pack overrides lock poisoned; recovering write");
            let mut guard = poisoned.into_inner();
            *guard = overrides;
        }
    }
}

pub(crate) fn set_runtime_theme_file_override(path: Option<String>) {
    #[cfg(test)]
    {
        RUNTIME_THEME_FILE_OVERRIDE_TEST.with(|slot| *slot.borrow_mut() = path);
    }
    #[cfg(not(test))]
    {
        let cell = RUNTIME_THEME_FILE_OVERRIDE.get_or_init(|| Mutex::new(None));
        match cell.lock() {
            Ok(mut guard) => *guard = path,
            Err(poisoned) => {
                log_debug("runtime theme-file override lock poisoned; recovering write");
                let mut guard = poisoned.into_inner();
                *guard = path;
            }
        }
    }
}

#[must_use]
pub(crate) fn runtime_theme_file_override() -> Option<String> {
    #[cfg(test)]
    {
        RUNTIME_THEME_FILE_OVERRIDE_TEST.with(|slot| slot.borrow().clone())
    }
    #[cfg(not(test))]
    {
        let cell = RUNTIME_THEME_FILE_OVERRIDE.get_or_init(|| Mutex::new(None));
        match cell.lock() {
            Ok(guard) => guard.clone(),
            Err(poisoned) => {
                log_debug("runtime theme-file override lock poisoned; recovering read");
                poisoned.into_inner().clone()
            }
        }
    }
}

/// Set a full runtime color palette override from the Theme Studio Colors page.
///
/// Takes highest precedence when set — `resolve_theme_colors()` checks this
/// before style-pack JSON, TOML files, or built-in themes.
#[cfg(not(test))]
pub(crate) fn set_runtime_color_override(colors: ThemeColors) {
    let cell = RUNTIME_COLOR_OVERRIDE.get_or_init(|| Mutex::new(None));
    match cell.lock() {
        Ok(mut guard) => *guard = Some(colors),
        Err(poisoned) => {
            let mut guard = poisoned.into_inner();
            *guard = Some(colors);
        }
    }
}

/// Clear the runtime color palette override (e.g. when studio closes).
#[cfg(not(test))]
pub(crate) fn clear_runtime_color_override() {
    let cell = RUNTIME_COLOR_OVERRIDE.get_or_init(|| Mutex::new(None));
    match cell.lock() {
        Ok(mut guard) => *guard = None,
        Err(poisoned) => {
            poisoned.into_inner().take();
        }
    }
}

/// Get the current runtime color override, if any.
#[cfg(not(test))]
pub(crate) fn runtime_color_override() -> Option<ThemeColors> {
    let cell = RUNTIME_COLOR_OVERRIDE.get_or_init(|| Mutex::new(None));
    match cell.lock() {
        Ok(guard) => *guard,
        Err(poisoned) => *poisoned.into_inner(),
    }
}

/// Retrieve the environment payload, gated by test opt-in in test builds.
#[must_use]
pub(crate) fn runtime_style_pack_payload() -> Option<String> {
    #[cfg(test)]
    {
        std::env::var_os(STYLE_PACK_TEST_ENV_OPT_IN)?;
    }

    std::env::var(STYLE_PACK_SCHEMA_ENV)
        .ok()
        .filter(|payload| !payload.trim().is_empty())
}
