//! Background worker that runs devctl commands and reports completions.

use std::fs::File;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::thread::{self, JoinHandle};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

use crossbeam_channel::{unbounded, Receiver, Sender};

use super::{DevCommandCompletion, DevCommandKind, DevCommandStatus, DevCommandUpdate};
use completion::{cleanup_temp_files, completion_for_error, completion_for_terminated};

mod completion;
mod path;
mod summary;

pub(crate) use path::{devctl_script_path, find_devctl_root};
#[cfg(test)]
pub(crate) use summary::{excerpt, parse_terminal_packet, summarize_json};

enum Request {
    Run {
        request_id: u64,
        command: DevCommandKind,
    },
    Cancel {
        request_id: u64,
    },
    Shutdown,
}

pub(super) struct RunningProcess {
    pub(super) request_id: u64,
    pub(super) command: DevCommandKind,
    pub(super) started_at: Instant,
    pub(super) child: Child,
    pub(super) stdout_path: PathBuf,
    pub(super) stderr_path: PathBuf,
}

enum TerminationCause {
    Cancelled,
    TimedOut,
    Shutdown,
}

pub(crate) struct DevCommandBroker {
    request_tx: Sender<Request>,
    update_rx: Receiver<DevCommandUpdate>,
    worker: Option<JoinHandle<()>>,
    next_request_id: u64,
}

impl DevCommandBroker {
    pub(crate) fn spawn(working_dir: PathBuf) -> Self {
        let (request_tx, request_rx) = unbounded();
        let (update_tx, update_rx) = unbounded();
        let worker = thread::spawn(move || worker_loop(working_dir, request_rx, update_tx));
        Self {
            request_tx,
            update_rx,
            worker: Some(worker),
            next_request_id: 1,
        }
    }

    pub(crate) fn run_command(&mut self, command: DevCommandKind) -> Result<u64, &'static str> {
        let request_id = self.next_request_id;
        self.next_request_id = self.next_request_id.saturating_add(1);
        self.request_tx
            .send(Request::Run {
                request_id,
                command,
            })
            .map_err(|_| "dev command broker unavailable")?;
        Ok(request_id)
    }

    pub(crate) fn cancel_command(&self, request_id: u64) -> Result<(), &'static str> {
        self.request_tx
            .send(Request::Cancel { request_id })
            .map_err(|_| "dev command broker unavailable")
    }

    pub(crate) fn try_recv_update(&self) -> Option<DevCommandUpdate> {
        self.update_rx.try_recv().ok()
    }
}

impl Drop for DevCommandBroker {
    fn drop(&mut self) {
        if self.request_tx.send(Request::Shutdown).is_err() {
            // Worker may already be gone.
        }
        if let Some(worker) = self.worker.take() {
            if worker.join().is_err() {
                // Test teardown should not panic on a background-thread failure.
            }
        }
    }
}

fn send_update(update_tx: &Sender<DevCommandUpdate>, update: DevCommandUpdate) -> bool {
    update_tx.send(update).is_ok()
}

fn worker_loop(
    working_dir: PathBuf,
    request_rx: Receiver<Request>,
    update_tx: Sender<DevCommandUpdate>,
) {
    let mut running: Option<RunningProcess> = None;

    loop {
        if let Some(process) = running.take() {
            let mut process_slot = Some(process);
            while let Ok(request) = request_rx.try_recv() {
                let active_ref = process_slot.as_ref();
                match request {
                    Request::Run {
                        request_id,
                        command,
                    } => {
                        let busy_label = active_ref
                            .map(|active| active.command.label())
                            .unwrap_or("unknown");
                        let completion = DevCommandCompletion {
                            request_id,
                            command,
                            status: DevCommandStatus::Rejected,
                            duration_ms: 0,
                            summary: format!("busy: '{busy_label}' still running"),
                            stdout_excerpt: None,
                            stderr_excerpt: None,
                            terminal_packet: None,
                        };
                        if !send_update(&update_tx, DevCommandUpdate::Completed(completion)) {
                            return;
                        }
                    }
                    Request::Cancel { request_id } => {
                        if let Some(active) = process_slot.as_mut() {
                            if active.request_id == request_id {
                                terminate_running_process(
                                    &mut process_slot,
                                    &update_tx,
                                    TerminationCause::Cancelled,
                                );
                            }
                        }
                    }
                    Request::Shutdown => {
                        terminate_running_process(
                            &mut process_slot,
                            &update_tx,
                            TerminationCause::Shutdown,
                        );
                        return;
                    }
                }
            }

            if let Some(mut process) = process_slot {
                if process.started_at.elapsed() >= super::DEV_COMMAND_TIMEOUT {
                    process_slot = Some(process);
                    terminate_running_process(
                        &mut process_slot,
                        &update_tx,
                        TerminationCause::TimedOut,
                    );
                } else {
                    match process.child.try_wait() {
                        Ok(Some(status)) => {
                            let completion = completion::completion_from_exit(process, status);
                            if !send_update(&update_tx, DevCommandUpdate::Completed(completion)) {
                                return;
                            }
                        }
                        Ok(None) => {
                            running = Some(process);
                        }
                        Err(err) => {
                            let completion = completion_for_error(process, format!("{err}"));
                            if !send_update(&update_tx, DevCommandUpdate::Completed(completion)) {
                                return;
                            }
                        }
                    }
                }
            }

            thread::sleep(super::DEV_COMMAND_POLL_INTERVAL);
            continue;
        }

        match request_rx.recv() {
            Ok(Request::Run {
                request_id,
                command,
            }) => {
                if !send_update(
                    &update_tx,
                    DevCommandUpdate::Started {
                        request_id,
                        command,
                    },
                ) {
                    return;
                }
                match spawn_process(&working_dir, request_id, command) {
                    Ok(process) => {
                        running = Some(process);
                    }
                    Err(err) => {
                        let completion = DevCommandCompletion {
                            request_id,
                            command,
                            status: DevCommandStatus::SpawnError,
                            duration_ms: 0,
                            summary: format!("spawn failed: {err}"),
                            stdout_excerpt: None,
                            stderr_excerpt: None,
                            terminal_packet: None,
                        };
                        if !send_update(&update_tx, DevCommandUpdate::Completed(completion)) {
                            return;
                        }
                    }
                }
            }
            Ok(Request::Cancel { .. }) => {}
            Ok(Request::Shutdown) | Err(_) => return,
        }
    }
}

fn spawn_process(
    working_dir: &Path,
    request_id: u64,
    command: DevCommandKind,
) -> std::io::Result<RunningProcess> {
    let stdout_path = temp_output_path(request_id, "stdout");
    let stderr_path = temp_output_path(request_id, "stderr");
    let stdout_file = File::create(&stdout_path)?;
    let stderr_file = File::create(&stderr_path)?;

    let repo_root = path::find_devctl_root(working_dir);
    let script = path::devctl_script_path(&repo_root);
    let mut process = Command::new("python3");
    process
        .current_dir(&repo_root)
        .arg(script)
        .args(command.devctl_args())
        .stdin(Stdio::null())
        .stdout(Stdio::from(stdout_file))
        .stderr(Stdio::from(stderr_file));

    let child = match process.spawn() {
        Ok(child) => child,
        Err(err) => {
            cleanup_temp_files(&stdout_path, &stderr_path);
            return Err(err);
        }
    };

    Ok(RunningProcess {
        request_id,
        command,
        started_at: Instant::now(),
        child,
        stdout_path,
        stderr_path,
    })
}

fn terminate_child(child: &mut Child) {
    let _ = child.kill();
    let _ = child.wait();
}

fn terminate_running_process(
    process_slot: &mut Option<RunningProcess>,
    update_tx: &Sender<DevCommandUpdate>,
    cause: TerminationCause,
) {
    let Some(mut process) = process_slot.take() else {
        return;
    };
    terminate_child(&mut process.child);
    let (status, summary) = match cause {
        TerminationCause::Cancelled => (DevCommandStatus::Cancelled, "cancelled by user"),
        TerminationCause::TimedOut => (DevCommandStatus::TimedOut, "timed out"),
        TerminationCause::Shutdown => (DevCommandStatus::Cancelled, "cancelled during shutdown"),
    };
    let completion = completion_for_terminated(process, status, summary);
    if !send_update(update_tx, DevCommandUpdate::Completed(completion)) {
        // Receiver already dropped while the worker was tearing down.
    }
}

fn temp_output_path(request_id: u64, stream: &str) -> PathBuf {
    let now_nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    std::env::temp_dir().join(format!(
        "voiceterm-devctl-{stream}-{}-{request_id}-{now_nanos}.log",
        std::process::id()
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shutdown_termination_emits_completion_and_cleans_temp_files() {
        let stdout_path = temp_output_path(41, "stdout");
        let stderr_path = temp_output_path(41, "stderr");
        File::create(&stdout_path).expect("create stdout file");
        File::create(&stderr_path).expect("create stderr file");

        let child = Command::new("python3")
            .args(["-c", "import time; time.sleep(10)"])
            .stdout(Stdio::from(
                File::options()
                    .append(true)
                    .open(&stdout_path)
                    .expect("open stdout path"),
            ))
            .stderr(Stdio::from(
                File::options()
                    .append(true)
                    .open(&stderr_path)
                    .expect("open stderr path"),
            ))
            .spawn()
            .expect("spawn child");

        let process = RunningProcess {
            request_id: 41,
            command: DevCommandKind::Status,
            started_at: Instant::now(),
            child,
            stdout_path: stdout_path.clone(),
            stderr_path: stderr_path.clone(),
        };
        let (update_tx, update_rx) = unbounded();
        let mut process_slot = Some(process);

        terminate_running_process(&mut process_slot, &update_tx, TerminationCause::Shutdown);

        let DevCommandUpdate::Completed(completion) =
            update_rx.recv().expect("shutdown completion update")
        else {
            panic!("expected completed update");
        };
        assert_eq!(completion.request_id, 41);
        assert_eq!(completion.status, DevCommandStatus::Cancelled);
        assert_eq!(completion.summary, "cancelled during shutdown");
        assert!(process_slot.is_none(), "process slot should be cleared");
        assert!(
            !stdout_path.exists() && !stderr_path.exists(),
            "shutdown path should clean temp files"
        );
    }
}
