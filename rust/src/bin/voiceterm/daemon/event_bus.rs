//! Fan-out event broadcast to all connected daemon clients.

use std::sync::Mutex;

use super::types::DaemonEvent;
use tokio::sync::broadcast;

const BROADCAST_CAPACITY: usize = 2048;

/// Broadcasts daemon events to all subscribed client connections.
pub(super) struct EventBus {
    tx: broadcast::Sender<DaemonEvent>,
    latest_lifecycle_snapshot: Mutex<Option<DaemonEvent>>,
    latest_agent_list: Mutex<Option<DaemonEvent>>,
}

impl EventBus {
    pub fn new() -> Self {
        let (tx, _rx) = broadcast::channel(BROADCAST_CAPACITY);
        Self {
            tx,
            latest_lifecycle_snapshot: Mutex::new(None),
            latest_agent_list: Mutex::new(None),
        }
    }

    /// Broadcast an event to all subscribers. Slow receivers that fall behind
    /// will see a `Lagged` error on their next recv and skip to the latest.
    pub fn broadcast(&self, event: DaemonEvent) {
        self.update_lifecycle_snapshot(&event);
        self.update_agent_list_snapshot(&event);
        // Zero subscribers is expected during startup and after all clients disconnect.
        if self.tx.receiver_count() > 0 {
            match self.tx.send(event) {
                Ok(_n) => {}
                Err(_no_receivers) => {}
            }
        }
    }

    /// Create a new subscription receiver and replay the latest lifecycle
    /// snapshot plus the latest agent-list snapshot when they exist, so
    /// late-attaching clients learn both daemon status and current agent roster.
    pub fn subscribe_with_snapshot(
        &self,
    ) -> (
        broadcast::Receiver<DaemonEvent>,
        Option<DaemonEvent>,
        Option<DaemonEvent>,
    ) {
        let lifecycle = self
            .latest_lifecycle_snapshot
            .lock()
            .map(|guard| guard.clone())
            .unwrap_or(None);
        let agent_list = self
            .latest_agent_list
            .lock()
            .map(|guard| guard.clone())
            .unwrap_or(None);
        (self.tx.subscribe(), lifecycle, agent_list)
    }

    /// Number of active subscribers (connected clients).
    pub fn subscriber_count(&self) -> usize {
        self.tx.receiver_count()
    }

    fn update_lifecycle_snapshot(&self, event: &DaemonEvent) {
        if !matches!(
            event,
            DaemonEvent::DaemonReady { .. } | DaemonEvent::DaemonStatus { .. }
        ) {
            return;
        }
        if let Ok(mut guard) = self.latest_lifecycle_snapshot.lock() {
            *guard = Some(event.clone());
        }
    }

    fn update_agent_list_snapshot(&self, event: &DaemonEvent) {
        if !matches!(event, DaemonEvent::AgentList { .. }) {
            return;
        }
        if let Ok(mut guard) = self.latest_agent_list.lock() {
            *guard = Some(event.clone());
        }
    }
}
