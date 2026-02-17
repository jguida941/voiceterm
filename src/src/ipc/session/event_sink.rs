use super::super::protocol::IpcEvent;
#[cfg(any(test, feature = "mutants"))]
use super::test_support;
use std::io::{self, Write};

pub(super) fn send_event(event: &IpcEvent) {
    #[cfg(any(test, feature = "mutants"))]
    if test_support::capture_test_event(event) {
        return;
    }
    if let Ok(json) = serde_json::to_string(event) {
        let mut stdout = io::stdout().lock();
        let _ = writeln!(stdout, "{json}");
        let _ = stdout.flush();
    }
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn init_event_sink() {
    test_support::init_event_sink();
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn ipc_loop_count_set(count: u64) {
    test_support::set_ipc_loop_count(count);
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn ipc_loop_count_reset() {
    test_support::ipc_loop_count_reset();
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn ipc_loop_count() -> u64 {
    test_support::ipc_loop_count()
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn event_snapshot() -> usize {
    test_support::event_snapshot()
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn events_since(start: usize) -> Vec<IpcEvent> {
    test_support::events_since(start)
}
