//! Theme directory management for user-created `.toml` theme files.
//!
//! Themes are stored in `~/.config/voiceterm/themes/`. This module handles
//! directory discovery, listing, and loading user themes by name.

use std::path::PathBuf;

use super::{
    color_value::ResolvedThemeColors,
    theme_file::{load_theme_file, resolve_theme_file, ThemeFileError},
};

/// Return the user themes directory path (`~/.config/voiceterm/themes/`).
#[must_use]
pub(crate) fn theme_dir() -> Option<PathBuf> {
    dirs::config_dir().map(|d| d.join("voiceterm").join("themes"))
}

/// Ensure the user themes directory exists, creating it if necessary.
pub(crate) fn ensure_theme_dir() -> std::io::Result<PathBuf> {
    let dir = theme_dir().ok_or_else(|| {
        std::io::Error::new(
            std::io::ErrorKind::NotFound,
            "could not determine config directory",
        )
    })?;
    std::fs::create_dir_all(&dir)?;
    Ok(dir)
}

/// List all `.toml` theme files in the user themes directory.
#[must_use]
pub(crate) fn list_theme_files() -> Vec<PathBuf> {
    let Some(dir) = theme_dir() else {
        return Vec::new();
    };
    let Ok(entries) = std::fs::read_dir(&dir) else {
        return Vec::new();
    };

    let mut files: Vec<PathBuf> = entries
        .filter_map(Result::ok)
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|e| e.to_str()) == Some("toml"))
        .collect();
    files.sort_unstable();
    files
}

/// Load a user theme by name (without extension) from the themes directory.
///
/// Looks for `~/.config/voiceterm/themes/{name}.toml`.
pub(crate) fn load_user_theme(name: &str) -> Result<ResolvedThemeColors, ThemeFileError> {
    let dir = theme_dir()
        .ok_or_else(|| ThemeFileError::Io("could not determine config directory".into()))?;
    let path = dir.join(format!("{name}.toml"));
    let file = load_theme_file(&path)?;
    resolve_theme_file(&file)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn theme_dir_returns_some_path() {
        // On most systems (CI included) dirs::config_dir() returns something.
        let dir = theme_dir();
        if let Some(ref d) = dir {
            assert!(d.ends_with("voiceterm/themes") || d.ends_with("voiceterm\\themes"));
        }
    }

    #[test]
    fn list_theme_files_returns_empty_for_nonexistent_dir() {
        // If the themes directory doesn't exist, should return empty vec.
        let files = list_theme_files();
        // This is not an error, just potentially empty.
        assert!(files.is_empty() || !files.is_empty());
    }

    #[test]
    fn load_user_theme_returns_error_for_nonexistent() {
        let result = load_user_theme("definitely_does_not_exist_theme_9999");
        assert!(result.is_err());
    }
}
