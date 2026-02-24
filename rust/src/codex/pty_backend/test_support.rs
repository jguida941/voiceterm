use super::super::backend::{CancelToken, CodexEventKind};
use std::cell::Cell;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Mutex, MutexGuard, OnceLock};

thread_local! {
    static RESET_SESSION_COUNT: Cell<usize> = const { Cell::new(0) };
}

pub(super) fn record_reset_session() {
    RESET_SESSION_COUNT.with(|count| count.set(count.get().saturating_add(1)));
}

pub(crate) fn reset_session_count() -> usize {
    RESET_SESSION_COUNT.with(|count| count.get())
}

pub(crate) fn reset_session_count_reset() {
    RESET_SESSION_COUNT.with(|count| count.set(0));
}

#[derive(Clone)]
pub(crate) struct CancelProbe(CancelToken);

impl CancelProbe {
    pub fn is_cancelled(&self) -> bool {
        self.0.is_cancelled()
    }
}

pub(crate) type CodexJobHook =
    Box<dyn Fn(&str, CancelProbe) -> Vec<CodexEventKind> + Send + Sync + 'static>;

static CODEX_JOB_HOOK: OnceLock<Mutex<Option<CodexJobHook>>> = OnceLock::new();
static JOB_HOOK_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
static ACTIVE_BACKEND_THREADS: AtomicUsize = AtomicUsize::new(0);

pub(crate) fn active_backend_threads() -> usize {
    ACTIVE_BACKEND_THREADS.load(Ordering::SeqCst)
}

pub(super) struct BackendThreadGuard;

impl BackendThreadGuard {
    fn new() -> Self {
        ACTIVE_BACKEND_THREADS.fetch_add(1, Ordering::SeqCst);
        Self
    }
}

impl Drop for BackendThreadGuard {
    fn drop(&mut self) {
        ACTIVE_BACKEND_THREADS.fetch_sub(1, Ordering::SeqCst);
    }
}

pub(super) fn backend_thread_guard() -> BackendThreadGuard {
    BackendThreadGuard::new()
}

pub(super) fn try_job_hook(prompt: &str, cancel: &CancelToken) -> Option<Vec<CodexEventKind>> {
    let storage = CODEX_JOB_HOOK.get_or_init(|| Mutex::new(None));
    let guard = storage.lock().unwrap_or_else(|e| e.into_inner());
    guard
        .as_ref()
        .map(|hook| hook(prompt, CancelProbe(cancel.clone())))
}

pub(crate) struct JobHookGuard {
    lock: Option<MutexGuard<'static, ()>>,
}

impl Drop for JobHookGuard {
    fn drop(&mut self) {
        if let Some(storage) = CODEX_JOB_HOOK.get() {
            *storage.lock().unwrap_or_else(|e| e.into_inner()) = None;
        }
        self.lock.take();
    }
}

pub(crate) fn with_job_hook<R>(hook: CodexJobHook, f: impl FnOnce() -> R) -> (R, JobHookGuard) {
    let storage = CODEX_JOB_HOOK.get_or_init(|| Mutex::new(None));
    let lock = JOB_HOOK_LOCK
        .get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(|e| e.into_inner());
    *storage.lock().unwrap_or_else(|e| e.into_inner()) = Some(hook);
    let result = f();
    (result, JobHookGuard { lock: Some(lock) })
}
