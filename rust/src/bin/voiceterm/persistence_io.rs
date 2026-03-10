//! Shared file persistence helpers for atomic text writes under the VoiceTerm config tree.

use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

static TEMP_FILE_SEQUENCE: AtomicU64 = AtomicU64::new(0);

fn atomic_temp_path(path: &Path) -> PathBuf {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    let stem = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("voiceterm");
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or(0);
    let seq = TEMP_FILE_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    parent.join(format!(".{stem}.{stamp}.{seq}.tmp"))
}

/// Write UTF-8 text to `path` via a same-directory temp file and atomic rename.
///
/// Creates the parent directory if needed.
pub(crate) fn write_text_atomically(path: &Path, body: &str) -> io::Result<()> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent)?;

    let temp_path = atomic_temp_path(path);
    let write_result = (|| -> io::Result<()> {
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temp_path)?;
        file.write_all(body.as_bytes())?;
        file.sync_all()?;
        Ok(())
    })();

    if let Err(err) = write_result {
        let _ = fs::remove_file(&temp_path);
        return Err(err);
    }

    if let Err(err) = fs::rename(&temp_path, path) {
        let _ = fs::remove_file(&temp_path);
        return Err(err);
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::write_text_atomically;
    use std::fs;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn unique_path(label: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|duration| duration.as_nanos())
            .unwrap_or(0);
        std::env::temp_dir().join(format!("voiceterm-persistence-io-{label}-{stamp}.toml"))
    }

    #[test]
    fn write_text_atomically_creates_parent_dirs_and_writes_body() {
        let path = std::env::temp_dir()
            .join(format!(
                "voiceterm-persistence-io-dir-{}",
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .map(|duration| duration.as_nanos())
                    .unwrap_or(0)
            ))
            .join("config.toml");
        if let Some(parent) = path.parent() {
            let _ = fs::remove_dir_all(parent);
        }

        write_text_atomically(&path, "theme = \"coral\"\n").expect("write config");

        let written = fs::read_to_string(&path).expect("read config");
        assert_eq!(written, "theme = \"coral\"\n");

        if let Some(parent) = path.parent() {
            let _ = fs::remove_dir_all(parent);
        }
    }

    #[test]
    fn write_text_atomically_replaces_existing_file_contents() {
        let path = unique_path("overwrite");
        let _ = fs::remove_file(&path);
        fs::write(&path, "old = true\n").expect("seed file");

        write_text_atomically(&path, "old = false\n").expect("overwrite config");

        let written = fs::read_to_string(&path).expect("read config");
        assert_eq!(written, "old = false\n");

        let _ = fs::remove_file(path);
    }
}
