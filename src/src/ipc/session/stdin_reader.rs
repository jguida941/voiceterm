use std::io::{self, BufRead};
use std::sync::mpsc::Sender;
use std::thread;

use crate::log_debug;

use super::super::protocol::IpcCommand;
use super::{send_event, IpcEvent};

#[cfg_attr(any(test, feature = "mutants"), allow(dead_code))]
pub(super) fn spawn_stdin_reader(tx: Sender<IpcCommand>) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        let stdin = io::stdin();
        let stdin_lock = stdin.lock();

        for line in stdin_lock.lines() {
            let line = match line {
                Ok(l) => l,
                Err(_) => break,
            };

            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }

            match serde_json::from_str::<IpcCommand>(trimmed) {
                Ok(cmd) => {
                    if tx.send(cmd).is_err() {
                        break; // Main thread has exited
                    }
                }
                Err(e) => {
                    send_event(&IpcEvent::Error {
                        message: format!("Invalid command: {e}"),
                        recoverable: true,
                    });
                }
            }
        }

        log_debug("Stdin reader thread exiting");
    })
}
