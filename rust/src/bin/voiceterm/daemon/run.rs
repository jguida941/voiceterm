//! Main daemon runtime: binds listeners, processes commands, manages lifecycle.

use std::sync::Arc;
use std::time::Instant;

use tokio::net::{TcpListener, UnixListener};
use tokio::sync::mpsc;

use voiceterm::log_debug;

use super::agent_driver;
use super::event_bus::EventBus;
use super::session_registry::SessionRegistry;
use super::socket_listener::{self, ClientCommand};
use super::types::{DaemonCommand, DaemonConfig, DaemonEvent};
use super::ws_bridge;

/// Run the daemon hub until shutdown is requested or SIGINT/SIGTERM is received.
pub(crate) async fn run_daemon(config: DaemonConfig) -> anyhow::Result<()> {
    let start = Instant::now();
    let event_bus = Arc::new(EventBus::new());
    let (cmd_tx, mut cmd_rx) = mpsc::channel::<ClientCommand>(256);
    let mut registry = SessionRegistry::new();

    let unix_listener = bind_unix_socket(&config)?;
    tokio::spawn(socket_listener::run_socket_listener(
        unix_listener,
        cmd_tx.clone(),
        event_bus.clone(),
    ));

    let ws_port = maybe_bind_ws(&config, &cmd_tx, &event_bus).await;

    event_bus.broadcast(DaemonEvent::DaemonReady {
        version: env!("CARGO_PKG_VERSION").to_string(),
        socket_path: config.socket_path.display().to_string(),
        ws_port,
    });
    print_daemon_banner(&config, ws_port);

    loop {
        tokio::select! {
            Some(client_cmd) = cmd_rx.recv() => {
                let should_shutdown = handle_command(
                    client_cmd.command, &config, &mut registry, &event_bus, start,
                ).await;
                if should_shutdown { break; }
            }
            _ = tokio::signal::ctrl_c() => {
                log_debug("daemon: received SIGINT, shutting down");
                break;
            }
        }
    }

    shutdown_daemon(&mut registry, &event_bus, &config).await;
    Ok(())
}

/// Prepare and bind the Unix domain socket, cleaning up stale files.
fn bind_unix_socket(config: &DaemonConfig) -> anyhow::Result<UnixListener> {
    if let Some(parent) = config.socket_path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    if config.socket_path.exists() {
        std::fs::remove_file(&config.socket_path)?;
    }
    let listener = UnixListener::bind(&config.socket_path)?;
    log_debug(&format!("daemon: listening on {}", config.socket_path.display()));
    Ok(listener)
}

/// Optionally bind the WebSocket bridge if enabled. Returns the bound port.
async fn maybe_bind_ws(
    config: &DaemonConfig,
    cmd_tx: &mpsc::Sender<ClientCommand>,
    event_bus: &Arc<EventBus>,
) -> Option<u16> {
    if !config.ws_enabled {
        return None;
    }
    let addr = format!("0.0.0.0:{}", config.ws_port);
    match TcpListener::bind(&addr).await {
        Ok(tcp_listener) => {
            log_debug(&format!("daemon: WebSocket bridge on {addr}"));
            tokio::spawn(ws_bridge::run_ws_bridge(
                tcp_listener,
                cmd_tx.clone(),
                event_bus.clone(),
            ));
            Some(config.ws_port)
        }
        Err(err) => {
            log_debug(&format!("daemon: WebSocket bind failed on {addr}: {err}"));
            eprintln!("Warning: WebSocket bridge failed to bind on {addr}: {err}");
            None
        }
    }
}

/// Broadcast a session-scoped error event.
fn broadcast_error(event_bus: &EventBus, message: String, session_id: Option<String>) {
    event_bus.broadcast(DaemonEvent::Error {
        message,
        session_id,
    });
}

/// Process a single daemon command. Returns true if daemon should shut down.
async fn handle_command(
    command: DaemonCommand,
    config: &DaemonConfig,
    registry: &mut SessionRegistry,
    event_bus: &Arc<EventBus>,
    start: Instant,
) -> bool {
    match command {
        DaemonCommand::SpawnAgent { provider, working_dir, label, initial_prompt } => {
            handle_spawn(provider, working_dir, label, initial_prompt, config, registry, event_bus).await;
        }
        DaemonCommand::SendToAgent { session_id, text } => {
            if let Some(handle) = registry.get(&session_id) {
                if !handle.send_text(text).await {
                    broadcast_error(event_bus, "agent channel closed".into(), Some(session_id));
                }
            } else {
                broadcast_error(event_bus, format!("unknown session: {session_id}"), Some(session_id));
            }
        }
        DaemonCommand::KillAgent { session_id } => {
            if let Some(handle) = registry.remove(&session_id) {
                let _best_effort = handle.request_kill().await;
            } else {
                broadcast_error(event_bus, format!("unknown session: {session_id}"), Some(session_id));
            }
        }
        DaemonCommand::ListAgents => {
            event_bus.broadcast(DaemonEvent::AgentList { agents: registry.list() });
        }
        DaemonCommand::GetStatus => {
            event_bus.broadcast(DaemonEvent::DaemonStatus {
                version: env!("CARGO_PKG_VERSION").to_string(),
                active_agents: registry.len(),
                connected_clients: event_bus.subscriber_count(),
                uptime_secs: start.elapsed().as_secs_f64(),
            });
        }
        DaemonCommand::Shutdown => {
            log_debug("daemon: shutdown requested by client");
            return true;
        }
        DaemonCommand::Unknown => {
            broadcast_error(event_bus, "unknown command (protocol version mismatch?)".into(), None);
        }
    }
    false
}

/// Handle the SpawnAgent command with its multi-step lifecycle.
async fn handle_spawn(
    provider: String,
    working_dir: Option<String>,
    label: Option<String>,
    initial_prompt: Option<String>,
    config: &DaemonConfig,
    registry: &mut SessionRegistry,
    event_bus: &Arc<EventBus>,
) {
    let wd = working_dir.as_deref().unwrap_or(&config.working_dir);
    let lbl = label.as_deref().unwrap_or(&provider);
    let args: Vec<String> = Vec::new();
    match agent_driver::spawn_agent(&provider, wd, &args, lbl, event_bus.clone(), config.memory_mode) {
        Ok(handle) => {
            let spawned = DaemonEvent::AgentSpawned {
                session_id: handle.session_id.0.clone(),
                provider: handle.provider.clone(),
                label: handle.label.clone(),
                working_dir: handle.working_dir.clone(),
                pid: handle.child_pid,
            };
            if let Some(prompt) = initial_prompt {
                let _best_effort = handle.send_text(prompt).await;
            }
            registry.insert(handle);
            event_bus.broadcast(spawned);
        }
        Err(err) => {
            broadcast_error(event_bus, format!("failed to spawn agent: {err}"), None);
        }
    }
}

/// Clean up all sessions and notify clients before exit.
async fn shutdown_daemon(
    registry: &mut SessionRegistry,
    event_bus: &Arc<EventBus>,
    config: &DaemonConfig,
) {
    log_debug("daemon: shutting down all agent sessions");
    for handle in registry.drain_all() {
        let _best_effort = handle.request_kill().await;
    }
    event_bus.broadcast(DaemonEvent::DaemonShutdown);
    let _cleanup = std::fs::remove_file(&config.socket_path);
    log_debug("daemon: shutdown complete");
}

fn print_daemon_banner(config: &DaemonConfig, ws_port: Option<u16>) {
    eprintln!("VoiceTerm Daemon v{}", env!("CARGO_PKG_VERSION"));
    eprintln!("  Socket: {}", config.socket_path.display());
    if let Some(port) = ws_port {
        eprintln!("  WebSocket: ws://0.0.0.0:{port}");
    }
    eprintln!("  Working dir: {}", config.working_dir);
    eprintln!("  Press Ctrl+C to stop");
}
