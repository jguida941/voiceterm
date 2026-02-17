use super::super::protocol::IpcEvent;
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, OnceLock};

#[derive(Default)]
struct EventSink {
    per_thread: HashMap<std::thread::ThreadId, Vec<IpcEvent>>,
}

static EVENT_SINK: OnceLock<Mutex<EventSink>> = OnceLock::new();
static IPC_LOOP_COUNT: AtomicU64 = AtomicU64::new(0);

pub(super) fn capture_test_event(event: &IpcEvent) -> bool {
    if let Some(sink) = EVENT_SINK.get() {
        if let Ok(mut events) = sink.lock() {
            events
                .per_thread
                .entry(std::thread::current().id())
                .or_default()
                .push(event.clone());
            return true;
        }
    }
    false
}

pub(super) fn init_event_sink() {
    let _ = EVENT_SINK.get_or_init(|| Mutex::new(EventSink::default()));
}

pub(super) fn set_ipc_loop_count(count: u64) {
    IPC_LOOP_COUNT.store(count, Ordering::SeqCst);
}

pub(super) fn ipc_loop_count_reset() {
    IPC_LOOP_COUNT.store(0, Ordering::SeqCst);
}

pub(super) fn ipc_loop_count() -> u64 {
    IPC_LOOP_COUNT.load(Ordering::SeqCst)
}

pub(super) fn event_snapshot() -> usize {
    init_event_sink();
    let current = std::thread::current().id();
    EVENT_SINK
        .get()
        .and_then(|sink| {
            sink.lock()
                .ok()
                .and_then(|events| events.per_thread.get(&current).map(Vec::len))
        })
        .unwrap_or(0)
}

pub(super) fn events_since(start: usize) -> Vec<IpcEvent> {
    let current = std::thread::current().id();
    EVENT_SINK
        .get()
        .and_then(|sink| {
            sink.lock().ok().and_then(|events| {
                events
                    .per_thread
                    .get(&current)
                    .map(|thread_events| thread_events.iter().skip(start).cloned().collect())
            })
        })
        .unwrap_or_default()
}
