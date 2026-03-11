"""Concurrency-focused probe remediation practices."""

from __future__ import annotations

from typing import Any

CONCURRENCY_PRACTICES: dict[str, dict[str, Any]] = {
    "nested_locks": {
        "title": "Avoid nested lock acquisitions",
        "explanation": (
            "Acquiring a second lock while holding a first creates deadlock risk. "
            "If thread A holds lock-1 and waits for lock-2, while thread B holds "
            "lock-2 and waits for lock-1, both threads stall forever. This is one "
            "of the most common concurrency bugs in production systems."
        ),
        "fix_pattern": (
            "1. Flatten the locking — acquire one lock, extract the data you need, "
            "drop the lock, then acquire the second.\n"
            "2. If both locks are always acquired together, merge them into a "
            "single lock protecting a combined struct.\n"
            "3. Establish a lock ordering protocol (always acquire lock-A before lock-B)."
        ),
        "example_before": (
            "let guard1 = self.state.read();\n"
            "let guard2 = self.config.read();  // DEADLOCK RISK\n"
            "let result = process(&guard1, &guard2);"
        ),
        "example_after": (
            "let state_snapshot = self.state.read().clone();\n"
            "let config_snapshot = self.config.read().clone();\n"
            "let result = process(&state_snapshot, &config_snapshot);"
        ),
        "references": [
            "Rust Book: Shared-State Concurrency",
            "OWASP: Race Conditions",
        ],
    },
    "arc_mutex_spawn": {
        "title": "Scope Arc<Mutex<>> access around spawned tasks",
        "explanation": (
            "Sharing Arc<Mutex<>> into spawned tasks without clear ownership "
            "boundaries creates hidden coupling. The spawned task can hold the lock "
            "for unpredictable durations, blocking the parent. Worse, if the task "
            "panics while holding the lock, the mutex becomes poisoned."
        ),
        "fix_pattern": (
            "1. Clone the data before spawning (avoid sharing the lock).\n"
            "2. Use message passing (channels) instead of shared mutable state.\n"
            "3. If sharing is required, document the lock scope and use try_lock() "
            "with timeout in the spawned task."
        ),
        "example_before": (
            "let shared = Arc::clone(&self.state);\n"
            "tokio::spawn(async move {\n"
            "    let mut guard = shared.lock().await;  // holds lock across await\n"
            "    do_work(&mut guard).await;\n"
            "});"
        ),
        "example_after": (
            "let snapshot = self.state.lock().await.clone();\n"
            "tokio::spawn(async move {\n"
            "    let result = do_work(&snapshot).await;\n"
            "    // Send result back via channel\n"
            "    tx.send(result).await.ok();\n"
            "});"
        ),
        "references": [
            "Tokio docs: Shared state",
            "Rust async book: Pitfalls of async Mutex",
        ],
    },
    "atomic_relaxed_multi_flag": {
        "title": "Use stronger memory ordering for multi-flag coordination",
        "explanation": (
            "Ordering::Relaxed only guarantees atomicity of individual operations — "
            "it does NOT guarantee that other threads see flag updates in order. "
            "When two AtomicBool flags coordinate behavior (e.g., 'is_running' and "
            "'should_stop'), a thread might see 'should_stop = true' but still read "
            "the old value of 'is_running'. This creates subtle, intermittent bugs "
            "that are nearly impossible to reproduce in testing."
        ),
        "fix_pattern": (
            "1. Use Ordering::SeqCst for flags that must be seen in order.\n"
            "2. Combine related flags into a single AtomicU8 with bit masking.\n"
            "3. Use a Mutex<State> enum instead of multiple booleans.\n"
            "4. If one flag is truly independent, document why Relaxed is safe."
        ),
        "example_before": (
            "static RUNNING: AtomicBool = AtomicBool::new(false);\n"
            "static SHOULD_STOP: AtomicBool = AtomicBool::new(false);\n"
            "// Thread A: RUNNING.store(true, Relaxed); do_work(); SHOULD_STOP.store(true, Relaxed);\n"
            "// Thread B: while !SHOULD_STOP.load(Relaxed) { ... }  // may miss the ordering"
        ),
        "example_after": (
            "enum State { Idle, Running, Stopping, Stopped }\n"
            "let state = Arc::new(Mutex::new(State::Idle));\n"
            "// Or: use a single AtomicU8 with SeqCst ordering"
        ),
        "references": [
            "Rust Nomicon: Atomics and Memory Ordering",
            "Mara Bos: Rust Atomics and Locks (O'Reilly)",
        ],
    },
    "poison_recovery": {
        "title": "Audit lock-poisoning recovery paths",
        "explanation": (
            "When a thread panics while holding a Mutex, the lock becomes poisoned. "
            "Using .into_inner() recovers the data but may leave it in an "
            "inconsistent state — the panic interrupted a mutation mid-way. This is "
            "sometimes acceptable (e.g., a counter that missed an increment) but "
            "dangerous for complex state (e.g., a partially-updated config)."
        ),
        "fix_pattern": (
            "1. Log a warning when recovering from a poisoned lock.\n"
            "2. Validate the recovered state before using it.\n"
            "3. Consider whether the panic path can be eliminated instead."
        ),
        "example_before": (
            "let data = lock.lock().unwrap_or_else(|e| e.into_inner());\n"
            "// Silently uses potentially-corrupt data"
        ),
        "example_after": (
            "let data = match lock.lock() {\n"
            "    Ok(guard) => guard,\n"
            "    Err(poisoned) => {\n"
            "        tracing::warn!(\"lock was poisoned, recovering\");\n"
            "        let recovered = poisoned.into_inner();\n"
            "        // Validate recovered state\n"
            "        recovered\n"
            "    }\n"
            "};"
        ),
        "references": [
            "std::sync::Mutex: Poisoning",
        ],
    },
}
