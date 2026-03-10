//! Fan-out event broadcast to all connected daemon clients.

use super::types::DaemonEvent;
use tokio::sync::broadcast;

const BROADCAST_CAPACITY: usize = 2048;

/// Broadcasts daemon events to all subscribed client connections.
pub(super) struct EventBus {
    tx: broadcast::Sender<DaemonEvent>,
}

impl EventBus {
    pub fn new() -> Self {
        let (tx, _rx) = broadcast::channel(BROADCAST_CAPACITY);
        Self { tx }
    }

    /// Broadcast an event to all subscribers. Slow receivers that fall behind
    /// will see a `Lagged` error on their next recv and skip to the latest.
    pub fn broadcast(&self, event: DaemonEvent) {
        // Zero subscribers is expected during startup and after all clients disconnect.
        if self.tx.receiver_count() > 0 {
            match self.tx.send(event) {
                Ok(_n) => {}
                Err(_no_receivers) => {}
            }
        }
    }

    /// Create a new subscription receiver for a client connection.
    pub fn subscribe(&self) -> broadcast::Receiver<DaemonEvent> {
        self.tx.subscribe()
    }

    /// Number of active subscribers (connected clients).
    pub fn subscriber_count(&self) -> usize {
        self.tx.receiver_count()
    }
}
