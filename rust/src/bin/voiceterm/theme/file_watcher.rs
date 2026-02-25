//! Polling-based file watcher for live theme hot-reload.
//!
//! Checks the mtime of a theme file on a configurable interval and returns
//! new content when the file has changed. No additional crate dependencies
//! required — uses `std::fs::metadata` for mtime.

use std::fs;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

/// Polls a single file for changes based on modification time.
#[derive(Debug)]
pub(crate) struct ThemeFileWatcher {
    path: PathBuf,
    last_modified: Option<SystemTime>,
    last_hash: u64,
}

impl ThemeFileWatcher {
    /// Create a new watcher for the given file path.
    ///
    /// Reads the file immediately to establish a baseline so the first
    /// call to `poll()` does not spuriously report a change.
    #[must_use]
    pub(crate) fn new(path: PathBuf) -> Self {
        let (mtime, hash) = Self::read_mtime_and_hash(&path);
        Self {
            path,
            last_modified: mtime,
            last_hash: hash,
        }
    }

    /// Check whether the file has changed since the last poll.
    ///
    /// Returns `Some(content)` if the file was modified (different mtime
    /// AND different content hash), `None` otherwise.
    pub(crate) fn poll(&mut self) -> Option<String> {
        let current_mtime = fs::metadata(&self.path).and_then(|m| m.modified()).ok();

        // Fast path: mtime unchanged.
        if current_mtime == self.last_modified {
            return None;
        }

        // Mtime changed — read file and compare content hash.
        let content = fs::read_to_string(&self.path).ok()?;
        let hash = Self::hash_content(&content);

        self.last_modified = current_mtime;

        if hash == self.last_hash {
            return None;
        }

        self.last_hash = hash;
        Some(content)
    }

    /// Get the watched file path.
    #[must_use]
    pub(crate) fn path(&self) -> &Path {
        &self.path
    }

    fn read_mtime_and_hash(path: &Path) -> (Option<SystemTime>, u64) {
        let mtime = fs::metadata(path).and_then(|m| m.modified()).ok();
        let hash = fs::read_to_string(path)
            .map(|c| Self::hash_content(&c))
            .unwrap_or(0);
        (mtime, hash)
    }

    /// Simple FNV-1a hash — good enough for change detection, no crypto needed.
    fn hash_content(content: &str) -> u64 {
        let mut hash: u64 = 0xcbf2_9ce4_8422_2325;
        for byte in content.bytes() {
            hash ^= u64::from(byte);
            hash = hash.wrapping_mul(0x0100_0000_01b3);
        }
        hash
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn watcher_returns_none_when_file_unchanged() {
        let dir = std::env::temp_dir().join("voiceterm_watcher_test_unchanged");
        let _ = fs::create_dir_all(&dir);
        let path = dir.join("test_theme.toml");
        assert!(fs::write(&path, "[meta]\nname = \"test\"\n").is_ok());

        let mut watcher = ThemeFileWatcher::new(path.clone());

        // First poll should return None since baseline was established in new().
        assert!(watcher.poll().is_none());

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn watcher_detects_content_change() {
        let dir = std::env::temp_dir().join("voiceterm_watcher_test_change");
        let _ = fs::create_dir_all(&dir);
        let path = dir.join("test_theme2.toml");
        assert!(fs::write(&path, "[meta]\nname = \"v1\"\n").is_ok());

        let mut watcher = ThemeFileWatcher::new(path.clone());
        assert!(watcher.poll().is_none());

        // Modify the file.
        // Sleep briefly to ensure mtime changes on filesystems with coarse resolution.
        std::thread::sleep(std::time::Duration::from_millis(50));
        let mut file = match fs::OpenOptions::new()
            .write(true)
            .truncate(true)
            .open(&path)
        {
            Ok(file) => file,
            Err(err) => panic!("failed to open theme file for rewrite: {err}"),
        };
        assert!(file.write_all(b"[meta]\nname = \"v2\"\n").is_ok());
        drop(file);

        let result = watcher.poll();
        assert!(result.is_some());
        let changed = match result {
            Some(changed) => changed,
            None => panic!("watcher did not return changed content"),
        };
        assert!(changed.contains("v2"));

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn watcher_ignores_mtime_only_change() {
        let dir = std::env::temp_dir().join("voiceterm_watcher_test_mtime");
        let _ = fs::create_dir_all(&dir);
        let path = dir.join("test_theme3.toml");
        let content = "[meta]\nname = \"same\"\n";
        assert!(fs::write(&path, content).is_ok());

        let mut watcher = ThemeFileWatcher::new(path.clone());
        assert!(watcher.poll().is_none());

        // Rewrite same content (changes mtime but not hash).
        std::thread::sleep(std::time::Duration::from_millis(50));
        assert!(fs::write(&path, content).is_ok());

        assert!(watcher.poll().is_none());

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn hash_is_deterministic() {
        let h1 = ThemeFileWatcher::hash_content("hello world");
        let h2 = ThemeFileWatcher::hash_content("hello world");
        assert_eq!(h1, h2);

        let h3 = ThemeFileWatcher::hash_content("hello world!");
        assert_ne!(h1, h3);
    }
}
