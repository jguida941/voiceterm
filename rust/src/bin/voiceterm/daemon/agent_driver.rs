//! Per-agent PTY lifecycle: spawn, output drain, command relay, and shutdown.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

use tokio::sync::mpsc;
use voiceterm::log_debug;
use voiceterm::pty_session::PtyCliSession;

use super::event_bus::EventBus;
use super::memory_bridge::SessionMemoryBridge;
use super::types::{DaemonEvent, SessionId};
use crate::memory::MemoryMode;

/// Command sent from the daemon hub to a specific agent's driver thread.
pub(super) enum AgentCmd {
    /// Write text to the agent's PTY stdin.
    Send(String),
    /// Gracefully shut down the agent session.
    Kill,
}

/// Handle held by the registry to interact with a running agent.
pub(super) struct AgentHandle {
    pub session_id: SessionId,
    pub provider: String,
    pub label: String,
    pub working_dir: String,
    pub child_pid: i32,
    /// Send commands to the agent's blocking driver thread.
    pub cmd_tx: mpsc::Sender<AgentCmd>,
    /// Flag set to false when the PTY child exits.
    alive: Arc<AtomicBool>,
}

impl AgentHandle {
    /// Check whether the agent's PTY child is still running.
    pub fn is_alive(&self) -> bool {
        self.alive.load(Ordering::Relaxed)
    }

    /// Send text to the agent's PTY. Returns false if the channel is closed.
    pub async fn send_text(&self, text: String) -> bool {
        self.cmd_tx.send(AgentCmd::Send(text)).await.is_ok()
    }

    /// Request graceful shutdown. Returns false if already dead.
    pub async fn request_kill(&self) -> bool {
        self.cmd_tx.send(AgentCmd::Kill).await.is_ok()
    }
}

/// Spawn an agent in a headless PTY and return a handle for interaction.
///
/// The PTY output is drained in a blocking thread and broadcast via the event bus.
/// Commands are received via the returned handle's `cmd_tx`. When `memory_mode`
/// allows capture, a [`SessionMemoryBridge`] is created to persist all I/O
/// through the Memory Studio pipeline.
pub(super) fn spawn_agent(
    provider_cmd: &str,
    working_dir: &str,
    args: &[String],
    label: &str,
    event_bus: Arc<EventBus>,
    memory_mode: MemoryMode,
) -> anyhow::Result<AgentHandle> {
    let session_id = SessionId::new();
    let pty = PtyCliSession::new(provider_cmd, working_dir, args, "xterm-256color", 40, 120)?;
    let child_pid = pty.child_pid();
    let alive = Arc::new(AtomicBool::new(true));
    let (cmd_tx, cmd_rx) = mpsc::channel::<AgentCmd>(64);

    let handle = AgentHandle {
        session_id: session_id.clone(),
        provider: provider_cmd.to_string(),
        label: label.to_string(),
        working_dir: working_dir.to_string(),
        child_pid,
        cmd_tx,
        alive: alive.clone(),
    };

    let sid = session_id.0.clone();
    let project_id = working_dir.to_string();
    tokio::task::spawn_blocking(move || {
        let memory = SessionMemoryBridge::new(&sid, &project_id, memory_mode);
        run_agent_driver(pty, cmd_rx, event_bus, sid, alive, memory);
    });

    Ok(handle)
}

/// Drain all waiting PTY output chunks, broadcast each as an AgentOutput event,
/// and capture into the memory bridge if present.
fn drain_and_broadcast(
    pty: &PtyCliSession,
    event_bus: &EventBus,
    session_id: &str,
    memory: &mut Option<SessionMemoryBridge>,
) {
    for chunk in &pty.read_output() {
        let text = String::from_utf8_lossy(chunk);
        if !text.is_empty() {
            let owned = text.into_owned();
            if let Some(ref mut bridge) = memory {
                bridge.capture_output(&owned);
            }
            event_bus.broadcast(DaemonEvent::AgentOutput {
                session_id: session_id.to_string(),
                text: owned,
            });
        }
    }
}

/// Blocking driver loop: drains PTY output and processes commands.
/// The optional memory bridge captures all I/O for the Memory Studio pipeline.
fn run_agent_driver(
    mut pty: PtyCliSession,
    mut cmd_rx: mpsc::Receiver<AgentCmd>,
    event_bus: Arc<EventBus>,
    session_id: String,
    alive: Arc<AtomicBool>,
    mut memory: Option<SessionMemoryBridge>,
) {
    loop {
        drain_and_broadcast(&pty, &event_bus, &session_id, &mut memory);

        match cmd_rx.try_recv() {
            Ok(AgentCmd::Send(text)) => {
                if let Some(ref mut bridge) = memory {
                    bridge.capture_input(&text);
                }
                if let Err(err) = pty.send(&text) {
                    log_debug(&format!("agent {session_id}: send failed: {err}"));
                }
            }
            Ok(AgentCmd::Kill) => {
                log_debug(&format!("agent {session_id}: kill requested"));
                break;
            }
            Err(mpsc::error::TryRecvError::Empty) => {}
            Err(mpsc::error::TryRecvError::Disconnected) => {
                log_debug(&format!("agent {session_id}: command channel closed"));
                break;
            }
        }

        if !pty.is_alive() {
            drain_and_broadcast(&pty, &event_bus, &session_id, &mut memory);
            let exit_code = pty.try_wait().and_then(|s| s.code());
            event_bus.broadcast(DaemonEvent::AgentExited {
                session_id: session_id.clone(),
                exit_code,
            });
            alive.store(false, Ordering::Relaxed);
            log_debug(&format!("agent {session_id}: exited with code {exit_code:?}"));
            return;
        }

        std::thread::sleep(Duration::from_millis(50));
    }

    // Shutdown: PtyCliSession::drop handles SIGTERM → SIGKILL.
    // Memory bridge flushed on drop via its Drop impl.
    alive.store(false, Ordering::Relaxed);
    event_bus.broadcast(DaemonEvent::AgentKilled {
        session_id: session_id.clone(),
    });
    log_debug(&format!("agent {session_id}: driver stopped"));
}
