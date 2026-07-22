//! Hub-and-spoke daemon for external VoiceTerm clients.
//!
//! Runs VoiceTerm as a background service on a Unix domain socket (and optional
//! WebSocket bridge) so custom clients can share one event stream.

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
