//! Daemon protocol types shared across socket, WebSocket, and agent layers.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

static ID_COUNTER: AtomicU64 = AtomicU64::new(1);

fn next_id(prefix: &str) -> String {
    let seq = ID_COUNTER.fetch_add(1, Ordering::Relaxed);
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    format!("{prefix}_{ts:x}_{seq}")
}

/// Unique identifier for a spawned agent session.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub(crate) struct SessionId(pub String);

impl SessionId {
    pub fn new() -> Self {
        Self(next_id("agent"))
    }
}

/// Unique identifier for a connected client.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub(crate) struct ClientId(pub String);

impl ClientId {
    pub fn new(transport: &str) -> Self {
        Self(next_id(transport))
    }
}

/// Configuration for the daemon runtime.
#[derive(Debug, Clone)]
pub(crate) struct DaemonConfig {
    pub socket_path: PathBuf,
    pub ws_port: u16,
    pub ws_enabled: bool,
    pub working_dir: String,
    /// Memory capture mode for agent sessions.
    pub memory_mode: crate::memory::MemoryMode,
}

impl DaemonConfig {
    pub fn default_socket_path() -> PathBuf {
        dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join(".voiceterm")
            .join("control.sock")
    }
}

/// Lifecycle stage for the local daemon process.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum DaemonLifecycleState {
    Running,
}

/// Canonical local attach transport clients should prefer first.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum DaemonAttachTransport {
    UnixSocket,
    WebSocket,
}

// ============================================================================
// Commands (client → daemon)
// ============================================================================

/// Commands from connected clients to the daemon hub.
#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "cmd")]
pub(crate) enum DaemonCommand {
    /// Spawn a new agent PTY session.
    #[serde(rename = "spawn_agent")]
    SpawnAgent {
        /// CLI provider: "claude" or "codex".
        provider: String,
        /// Working directory for the session.
        #[serde(default)]
        working_dir: Option<String>,
        /// Human-readable label (e.g. "reviewer-1").
        #[serde(default)]
        label: Option<String>,
        /// Initial prompt to send after spawn.
        #[serde(default)]
        initial_prompt: Option<String>,
    },

    /// Send text to a specific agent session's PTY.
    #[serde(rename = "send_to_agent")]
    SendToAgent { session_id: String, text: String },

    /// Gracefully kill a specific agent session.
    #[serde(rename = "kill_agent")]
    KillAgent { session_id: String },

    /// List all active agent sessions.
    #[serde(rename = "list_agents")]
    ListAgents,

    /// Request daemon status.
    #[serde(rename = "get_status")]
    GetStatus,

    /// Graceful daemon shutdown.
    #[serde(rename = "shutdown")]
    Shutdown,

    /// Forward-compatible fallback for commands added in newer protocol versions.
    #[serde(other)]
    Unknown,
}

// ============================================================================
// Events (daemon → clients)
// ============================================================================

/// Events broadcast from the daemon to all connected clients.
#[derive(Debug, Clone, Serialize)]
#[serde(tag = "event")]
pub(crate) enum DaemonEvent {
    /// Daemon is ready and listening.
    #[serde(rename = "daemon_ready")]
    DaemonReady {
        version: String,
        socket_path: String,
        ws_port: Option<u16>,
        #[serde(skip_serializing_if = "Option::is_none")]
        ws_url: Option<String>,
        lifecycle: DaemonLifecycleState,
        primary_attach: DaemonAttachTransport,
        pid: u32,
        started_at_unix_ms: u64,
        working_dir: String,
        memory_mode: String,
    },

    /// A new agent session was created.
    #[serde(rename = "agent_spawned")]
    AgentSpawned {
        session_id: String,
        provider: String,
        label: String,
        working_dir: String,
        pid: i32,
    },

    /// Output from an agent's PTY stream.
    #[serde(rename = "agent_output")]
    AgentOutput { session_id: String, text: String },

    /// An agent session has exited.
    #[serde(rename = "agent_exited")]
    AgentExited {
        session_id: String,
        exit_code: Option<i32>,
    },

    /// An agent session was killed by request.
    #[serde(rename = "agent_killed")]
    AgentKilled { session_id: String },

    /// List of all active agents.
    #[serde(rename = "agent_list")]
    AgentList { agents: Vec<AgentInfo> },

    /// Daemon status snapshot.
    #[serde(rename = "daemon_status")]
    DaemonStatus {
        version: String,
        active_agents: usize,
        connected_clients: usize,
        uptime_secs: f64,
        socket_path: String,
        ws_port: Option<u16>,
        #[serde(skip_serializing_if = "Option::is_none")]
        ws_url: Option<String>,
        lifecycle: DaemonLifecycleState,
        primary_attach: DaemonAttachTransport,
        pid: u32,
        started_at_unix_ms: u64,
        working_dir: String,
        memory_mode: String,
    },

    /// Error response.
    #[serde(rename = "error")]
    Error {
        message: String,
        #[serde(skip_serializing_if = "Option::is_none")]
        session_id: Option<String>,
    },

    /// Daemon is shutting down.
    #[serde(rename = "daemon_shutdown")]
    DaemonShutdown,
}

/// Summary info for a single agent session.
#[derive(Debug, Clone, Serialize)]
pub(crate) struct AgentInfo {
    pub session_id: String,
    pub provider: String,
    pub label: String,
    pub working_dir: String,
    pub pid: i32,
    pub is_alive: bool,
}

#[cfg(test)]
mod type_tests {
    use super::*;

    #[test]
    fn session_id_uniqueness() {
        let a = SessionId::new();
        let b = SessionId::new();
        assert_ne!(a, b);
    }

    #[test]
    fn daemon_command_deserializes() {
        let json = r#"{"cmd":"spawn_agent","provider":"claude"}"#;
        let cmd: DaemonCommand = serde_json::from_str(json).unwrap();
        assert!(matches!(cmd, DaemonCommand::SpawnAgent { .. }));
    }

    #[test]
    fn daemon_event_serializes() {
        let event = DaemonEvent::AgentOutput {
            session_id: "test".to_string(),
            text: "hello".to_string(),
        };
        let json = serde_json::to_string(&event).unwrap();
        assert!(json.contains("agent_output"));
        assert!(json.contains("hello"));
    }

    #[test]
    fn send_to_agent_roundtrip() {
        let json = r#"{"cmd":"send_to_agent","session_id":"a1","text":"fix the bug"}"#;
        let cmd: DaemonCommand = serde_json::from_str(json).unwrap();
        match cmd {
            DaemonCommand::SendToAgent { session_id, text } => {
                assert_eq!(session_id, "a1");
                assert_eq!(text, "fix the bug");
            }
            _ => panic!("wrong variant"),
        }
    }
}
