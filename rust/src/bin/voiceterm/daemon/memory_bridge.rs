//! Memory integration bridge for daemon agent sessions.
//!
//! Each agent driver thread creates a [`SessionMemoryBridge`] to capture PTY
//! output and user input into the Memory Studio pipeline. The bridge wraps
//! [`MemoryIngestor`] and provides a daemon-friendly API that aligns with
//! the agent driver's blocking loop.

use std::path::{Path, PathBuf};

use voiceterm::log_debug;

use crate::memory::ingest::MemoryIngestor;
use crate::memory::types::MemoryMode;

/// Memory capture bridge for a single daemon agent session.
///
/// Created on the `spawn_blocking` thread so the `MemoryIngestor` (which
/// contains an in-memory SQLite index and is `!Send`) stays on one thread.
pub(super) struct SessionMemoryBridge {
    ingestor: MemoryIngestor,
    session_id: String,
}

impl SessionMemoryBridge {
    /// Create a new memory bridge for an agent session.
    ///
    /// The JSONL log file is placed under `~/.voiceterm/memory/daemon/{session_id}.jsonl`.
    /// Returns `None` if memory capture is disabled or the storage path can't be created.
    pub fn new(session_id: &str, project_id: &str, mode: MemoryMode) -> Option<Self> {
        if !mode.allows_capture() {
            return None;
        }
        let jsonl_path = memory_log_path(session_id);
        if let Some(parent) = jsonl_path.parent() {
            if std::fs::create_dir_all(parent).is_err() {
                log_debug(&format!(
                    "daemon memory: failed to create log dir for {session_id}"
                ));
                return None;
            }
        }
        match MemoryIngestor::new(
            session_id.to_string(),
            project_id.to_string(),
            Some(&jsonl_path),
            mode,
        ) {
            Ok(ingestor) => Some(Self {
                ingestor,
                session_id: session_id.to_string(),
            }),
            Err(err) => {
                log_debug(&format!(
                    "daemon memory: failed to init ingestor for {session_id}: {err}"
                ));
                None
            }
        }
    }

    /// Capture assistant output from the agent's PTY stream.
    pub fn capture_output(&mut self, text: &str) {
        self.ingestor.ingest_assistant_output(text);
    }

    /// Capture user input sent to the agent.
    pub fn capture_input(&mut self, text: &str) {
        self.ingestor.ingest_user_input(text);
    }

    /// Flush buffered events to disk. Call on shutdown or idle.
    pub fn flush(&mut self) {
        self.ingestor.flush();
    }

    /// Number of events captured during this session.
    pub fn events_ingested(&self) -> u64 {
        self.ingestor.events_ingested()
    }

    /// The session ID this bridge is capturing for.
    #[allow(dead_code, reason = "API surface for upcoming per-session memory queries")]
    pub fn session_id(&self) -> &str {
        &self.session_id
    }
}

impl Drop for SessionMemoryBridge {
    fn drop(&mut self) {
        self.flush();
        log_debug(&format!(
            "daemon memory: session {} flushed {} events on drop",
            self.session_id,
            self.events_ingested(),
        ));
    }
}

/// Build the JSONL log path for a daemon agent session.
fn memory_log_path(session_id: &str) -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| Path::new(".").to_path_buf())
        .join(".voiceterm")
        .join("memory")
        .join("daemon")
        .join(format!("{session_id}.jsonl"))
}
