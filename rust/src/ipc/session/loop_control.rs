use anyhow::Result;
use std::sync::mpsc::{Receiver, RecvTimeoutError};
use std::time::Duration;
#[cfg(any(test, feature = "mutants"))]
use std::time::Instant;

use super::super::protocol::IpcCommand;
use super::{log_debug, log_debug_content, loop_runtime, IpcState, IPC_LOOP_WAIT_MS};

pub(super) fn run_ipc_loop(
    state: &mut IpcState,
    cmd_rx: &Receiver<IpcCommand>,
    max_loops: Option<u64>,
) -> Result<()> {
    #[cfg(any(test, feature = "mutants"))]
    let guard_start = Instant::now();
    let mut loop_count: u64 = 0;
    loop {
        #[cfg(any(test, feature = "mutants"))]
        if super::ipc_guard_tripped(guard_start.elapsed()) {
            panic!("IPC loop guard exceeded");
        }
        loop_count += 1;
        #[cfg(any(test, feature = "mutants"))]
        super::ipc_loop_count_set(loop_count);
        if loop_count.is_multiple_of(1000) {
            log_debug(&format!(
                "IPC loop iteration {}, job active: {}",
                loop_count,
                state.current_job.is_some()
            ));
        }

        if let Some(limit) = max_loops {
            if loop_count >= limit {
                log_debug("IPC loop reached test limit, exiting");
                break;
            }
        }

        // Wait briefly for commands so idle IPC loops don't spin.
        match cmd_rx.recv_timeout(Duration::from_millis(IPC_LOOP_WAIT_MS)) {
            Ok(cmd) => {
                log_debug_content(&format!("IPC command received: {cmd:?}"));
                loop_runtime::handle_command(state, cmd);
            }
            Err(RecvTimeoutError::Timeout) => {}
            Err(RecvTimeoutError::Disconnected) => {
                log_debug("Command channel disconnected, exiting");
                break;
            }
        }

        loop_runtime::drain_active_jobs(state);

        if loop_runtime::should_exit(state) {
            log_debug("IPC graceful exit requested; no active work remains");
            break;
        }
    }

    log_debug("IPC mode exiting");
    Ok(())
}
