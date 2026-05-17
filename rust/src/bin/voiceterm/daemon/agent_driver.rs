//! Per-agent PTY lifecycle: spawn, output drain, command relay, and shutdown.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::sync::Condvar;
use std::sync::Mutex;
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
    pub(super) alive: Arc<AtomicBool>,
    /// Startup gate keeps the driver quiescent until the registry/event bus are ready.
    pub(super) startup_gate: Arc<StartupGate>,
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

    /// Allow the driver thread to begin emitting runtime events.
    pub fn activate(&self) {
        self.startup_gate.open();
    }
    /// Request graceful shutdown. Returns false if already dead.
    pub async fn request_kill(&self) -> bool {
        self.startup_gate.cancel();
        self.cmd_tx.send(AgentCmd::Kill).await.is_ok()
    }
}

/// Synchronizes driver startup so spawn metadata is observable before runtime events.
pub(super) struct StartupGate {
    state: Mutex<StartupGateState>,
    ready_cv: Condvar,
}

#[derive(Clone, Copy, Eq, PartialEq)]
enum StartupGateState {
    Waiting,
    Open,
    Canceled,
}

impl StartupGate {
    pub fn new() -> Arc<Self> {
        Arc::new(Self {
            state: Mutex::new(StartupGateState::Waiting),
            ready_cv: Condvar::new(),
        })
    }

    #[cfg(test)]
    pub fn opened() -> Arc<Self> {
        let gate = Self::new();
        gate.open();
        gate
    }

    fn wait_until_ready(&self) -> bool {
        let mut state = lock_gate(&self.state);
        while *state == StartupGateState::Waiting {
            state = wait_for_gate(&self.ready_cv, state);
        }
        *state == StartupGateState::Open
    }

    fn open(&self) {
        let mut state = lock_gate(&self.state);
        *state = StartupGateState::Open;
        self.ready_cv.notify_all();
    }

    fn cancel(&self) {
        let mut state = lock_gate(&self.state);
        if *state == StartupGateState::Waiting {
            *state = StartupGateState::Canceled;
        }
        self.ready_cv.notify_all();
    }

    fn is_open(&self) -> bool {
        *lock_gate(&self.state) == StartupGateState::Open
    }
}

impl Drop for AgentHandle {
    fn drop(&mut self) {
        if !self.startup_gate.is_open() {
            self.startup_gate.cancel();
        }
    }
}

fn lock_gate(state: &Mutex<StartupGateState>) -> std::sync::MutexGuard<'_, StartupGateState> {
    match state.lock() {
        Ok(guard) => guard,
        Err(poisoned) => poisoned.into_inner(),
    }
}

fn wait_for_gate<'a>(
    ready_cv: &Condvar,
    state: std::sync::MutexGuard<'a, StartupGateState>,
) -> std::sync::MutexGuard<'a, StartupGateState> {
    match ready_cv.wait(state) {
        Ok(guard) => guard,
        Err(poisoned) => poisoned.into_inner(),
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
    let startup_gate = StartupGate::new();
    let (cmd_tx, cmd_rx) = mpsc::channel::<AgentCmd>(64);

    // The spawned task needs its own copies of session_id (as String) and
    // working_dir. Extract the task's copies first, then move the originals
    // into the handle — avoids an extra SessionId::clone().
    let sid = session_id.0.clone();
    let project_id = working_dir.to_string();

    let handle = AgentHandle {
        session_id,
        provider: provider_cmd.to_string(),
        label: label.to_string(),
        working_dir: working_dir.to_string(),
        child_pid,
        cmd_tx,
        alive: alive.clone(),
        startup_gate: startup_gate.clone(),
    };

    tokio::task::spawn_blocking(move || {
        let memory = SessionMemoryBridge::new(&sid, &project_id, memory_mode);
        run_agent_driver(pty, cmd_rx, event_bus, sid, alive, memory, startup_gate);
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
    startup_gate: Arc<StartupGate>,
) {
    if !startup_gate.wait_until_ready() {
        alive.store(false, Ordering::Relaxed);
        log_debug(&format!(
            "agent {session_id}: startup canceled before activation"
        ));
        return;
    }
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
            alive.store(false, Ordering::Relaxed);
            log_debug(&format!(
                "agent {session_id}: exited with code {exit_code:?}"
            ));
            // Move session_id into the event instead of cloning — this is
            // the last use of session_id before return.
            event_bus.broadcast(DaemonEvent::AgentExited {
                session_id,
                exit_code,
            });
            return;
        }

        std::thread::sleep(Duration::from_millis(50));
    }

    // Shutdown: PtyCliSession::drop handles SIGTERM → SIGKILL.
    // Memory bridge flushed on drop via its Drop impl.
    alive.store(false, Ordering::Relaxed);
    log_debug(&format!("agent {session_id}: driver stopped"));
    // Move session_id into the event — last use before function exit.
    event_bus.broadcast(DaemonEvent::AgentKilled { session_id });
}

#[cfg(test)]
mod tests {
    use std::sync::mpsc;
    use std::thread;
    use std::time::Duration;

    use super::StartupGate;

    #[test]
    fn startup_gate_blocks_until_opened() {
        let gate = StartupGate::new();
        let gate_for_thread = gate.clone();
        let (tx, rx) = mpsc::channel();
        thread::spawn(move || {
            assert!(gate_for_thread.wait_until_ready());
            assert!(tx.send("opened").is_ok());
        });

        assert!(rx.recv_timeout(Duration::from_millis(25)).is_err());
        gate.open();
        assert_eq!(rx.recv_timeout(Duration::from_millis(250)), Ok("opened"));
    }

    #[test]
    fn startup_gate_cancel_unblocks_waiters() {
        let gate = StartupGate::new();
        let gate_for_thread = gate.clone();
        let (tx, rx) = mpsc::channel();
        thread::spawn(move || {
            assert!(!gate_for_thread.wait_until_ready());
            assert!(tx.send("canceled").is_ok());
        });

        assert!(rx.recv_timeout(Duration::from_millis(25)).is_err());
        gate.cancel();
        assert_eq!(rx.recv_timeout(Duration::from_millis(250)), Ok("canceled"));
    }
}
