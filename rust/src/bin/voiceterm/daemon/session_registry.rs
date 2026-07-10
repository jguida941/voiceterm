//! Agent session registry tracking all active PTY-backed sessions.

use std::collections::HashMap;

use super::agent_driver::AgentHandle;
use super::types::AgentInfo;

/// Manages the set of currently running agent PTY sessions.
pub(super) struct SessionRegistry {
    sessions: HashMap<String, AgentHandle>,
}

impl SessionRegistry {
    pub fn new() -> Self {
        Self {
            sessions: HashMap::new(),
        }
    }

    /// Register a newly spawned agent session.
    pub fn insert(&mut self, handle: AgentHandle) {
        self.sessions.insert(handle.session_id.0.clone(), handle);
    }

    /// Remove a session by ID and return its handle for cleanup.
    pub fn remove(&mut self, session_id: &str) -> Option<AgentHandle> {
        self.sessions.remove(session_id)
    }

    /// Look up a session by ID.
    pub fn get(&self, session_id: &str) -> Option<&AgentHandle> {
        self.sessions.get(session_id)
    }

    /// Remove sessions whose PTY child has already exited.
    pub fn prune_dead(&mut self) -> usize {
        let before = self.sessions.len();
        self.sessions.retain(|_, handle| handle.is_alive());
        before.saturating_sub(self.sessions.len())
    }

    /// Build a snapshot list of all active agents.
    pub fn list(&self) -> Vec<AgentInfo> {
        self.sessions
            .values()
            .map(|h| AgentInfo {
                session_id: h.session_id.0.clone(),
                provider: h.provider.clone(),
                label: h.label.clone(),
                working_dir: h.working_dir.clone(),
                pid: h.child_pid,
                is_alive: h.is_alive(),
            })
            .collect()
    }

    /// Number of active sessions.
    pub fn len(&self) -> usize {
        self.sessions.len()
    }

    /// Drain all sessions for shutdown, returning handles for cleanup.
    pub fn drain_all(&mut self) -> Vec<AgentHandle> {
        self.sessions.drain().map(|(_, h)| h).collect()
    }
}
