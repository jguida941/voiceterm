//! Hub-and-spoke daemon so multiple agent PTY sessions broadcast to all surfaces.
//!
//! Runs VoiceTerm as a background service on a Unix domain socket (and optional
//! WebSocket bridge) so PyQt6, iPhone, and TUI clients share one event stream.

mod agent_driver;
mod client_codec;
mod event_bus;
mod memory_bridge;
mod run;
mod session_registry;
mod socket_listener;
mod types;
mod ws_bridge;

#[cfg(test)]
mod tests;

pub(crate) use run::run_daemon;
pub(crate) use types::DaemonConfig;
