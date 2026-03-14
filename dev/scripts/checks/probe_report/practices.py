"""Best-practice guidance catalog for probe report rendering."""

from __future__ import annotations

from typing import Any

from .practices_concurrency import CONCURRENCY_PRACTICES
from .practices_rust import RUST_PRACTICES

BEST_PRACTICE_LIBRARY: dict[str, dict[str, Any]] = {
    "nested_locks": {
        "title": "Avoid nested lock acquisitions",
        "explanation": "Locking one shared value while acquiring another creates deadlock risk and hides ownership boundaries between concurrent tasks.",
        "fix_pattern": "Flatten the lock sequence, snapshot one value before taking the next lock, or enforce one global lock-ordering rule.",
        "example_before": "let guard1 = self.state.read();\nlet guard2 = self.config.read();\nlet result = process(&guard1, &guard2);",
        "example_after": "let state_snapshot = self.state.read().clone();\nlet config_snapshot = self.config.read().clone();\nlet result = process(&state_snapshot, &config_snapshot);",
        "references": ["Rust Book: Shared-State Concurrency", "OWASP: Race Conditions"],
    },
    "arc_mutex_spawn": {
        "title": "Scope Arc<Mutex<...>> access around spawned work",
        "explanation": "Passing shared locks into spawned work can stretch lock lifetimes and couple parent and child tasks in surprising ways.",
        "fix_pattern": "Clone only the data you need before spawning, or switch to message passing when the worker only needs a snapshot/result channel.",
        "example_before": "let shared = Arc::clone(&self.state);\ntokio::spawn(async move {\n    let mut guard = shared.lock().await;\n    do_work(&mut guard).await;\n});",
        "example_after": "let snapshot = self.state.lock().await.clone();\ntokio::spawn(async move {\n    let result = do_work(&snapshot).await;\n    tx.send(result).await.ok();\n});",
        "references": ["Tokio docs: Shared state", "Rust async book: async Mutex pitfalls"],
    },
    "atomic_relaxed_multi_flag": {
        "title": "Use stronger ordering for multi-flag coordination",
        "explanation": "Relaxed atomics only guarantee single-operation atomicity, not ordering between related flags read by different threads.",
        "fix_pattern": "Use SeqCst for coordinated flags, combine related flags into one atomic state value, or replace them with a mutex-backed enum.",
        "example_before": "RUNNING.store(true, Relaxed);\nSHOULD_STOP.store(true, Relaxed);",
        "example_after": "enum State { Idle, Running, Stopping, Stopped }\nlet state = Arc::new(Mutex::new(State::Idle));",
        "references": ["Rust Nomicon: Atomics and Memory Ordering"],
    },
    "poison_recovery": {
        "title": "Audit lock-poisoning recovery paths",
        "explanation": "Recovering a poisoned lock may be valid, but it should be explicit because the guarded state may be only partially updated.",
        "fix_pattern": "Log the recovery, validate the recovered state, and prefer removing the panic path when the state is not trivially repairable.",
        "example_before": "let data = lock.lock().unwrap_or_else(|err| err.into_inner());",
        "example_after": 'let data = match lock.lock() {\n    Ok(guard) => guard,\n    Err(poisoned) => {\n        tracing::warn!("lock was poisoned, recovering");\n        poisoned.into_inner()\n    }\n};',
        "references": ["std::sync::Mutex: Poisoning"],
    },
    "getattr_density": {
        "title": "Replace getattr() chains with typed access",
        "explanation": "Heavy getattr() usage usually means the code is treating structured data as an untyped attribute bag, which weakens refactors and type checks.",
        "fix_pattern": "Introduce a dataclass, Protocol, or TypedDict and replace getattr(obj, 'field') with direct typed access.",
        "example_before": "status = getattr(result, 'status', 'unknown')\nname = getattr(result, 'name', '')",
        "example_after": "@dataclass\nclass Result:\n    status: str = 'unknown'\n    name: str = ''\n\nstatus = result.status\nname = result.name",
        "references": ["Python docs: dataclasses", "PEP 544: Protocols"],
    },
    "untyped_object_param": {
        "title": "Replace `object` parameters with a real interface",
        "explanation": "An `object` parameter followed by attribute access hides the real contract and defeats editor/type-checker help.",
        "fix_pattern": "Define a Protocol or concrete type for the required fields and use that in the signature.",
        "example_before": "def process(data: object) -> str:\n    return f\"{getattr(data, 'name', '')}: {getattr(data, 'value', 0)}\"",
        "example_after": 'class HasNameValue(Protocol):\n    name: str\n    value: int\n\ndef process(data: HasNameValue) -> str:\n    return f"{data.name}: {data.value}"',
        "references": ["PEP 544: Structural Subtyping"],
    },
    "format_helper_sprawl": {
        "title": "Consolidate format-helper sprawl",
        "explanation": "Many tiny private format helpers usually signal presentation logic that should live in one shared presenter instead of drifting across files.",
        "fix_pattern": "Extract the shared formatting rules into a presenter/formatter module and keep file-local helpers only for truly unique output.",
        "example_before": "def _fmt_status(...): ...\ndef _fmt_duration(...): ...\ndef _format_summary(...): ...",
        "example_after": "def format_status(...): ...\ndef format_duration(...): ...\ndef format_summary(...): ...",
        "references": ["Clean Code: DRY principle"],
    },
    "stringly_typed_python": {
        "title": "Replace string dispatch with StrEnum",
        "explanation": "String-literal branching hides the valid state space and turns typos into silent control-flow bugs.",
        "fix_pattern": "Parse incoming strings once at the boundary and dispatch internally on a StrEnum.",
        "example_before": "if action == 'create': ...\nelif action == 'update': ...\nelif action == 'delet': ...",
        "example_after": "class Action(StrEnum):\n    CREATE = 'create'\n    UPDATE = 'update'\n    DELETE = 'delete'",
        "references": ["Python docs: enum.StrEnum", "PEP 435: Enum"],
    },
    "stringly_typed_rust": {
        "title": "Replace string match arms with an enum",
        "explanation": "Matching on strings bypasses exhaustiveness checking, which is one of Rust's strongest safety properties.",
        "fix_pattern": "Parse once into an enum and match on enum variants everywhere else.",
        "example_before": 'match action.as_str() {\n    "create" => do_create(),\n    _ => {}\n}',
        "example_after": "enum Action { Create, Update, Delete }\nmatch action {\n    Action::Create => do_create(),\n    Action::Update => do_update(),\n    Action::Delete => do_delete(),\n}",
        "references": ["Rust Book: Defining an Enum", "Rust Book: match"],
    },
    "boolean_params_python": {
        "title": "Bundle boolean parameters into an options dataclass",
        "explanation": "Call sites with several positional booleans are unreadable because the meaning of each flag is hidden.",
        "fix_pattern": "Replace multiple bool parameters with a dataclass or options object using named fields.",
        "example_before": "deploy(True, False, True, False)",
        "example_after": "deploy(DeployOptions(verbose=True, force=True))",
        "references": ["Python docs: dataclasses"],
    },
    "boolean_params_rust": {
        "title": "Bundle boolean parameters into an options struct",
        "explanation": "Rust call sites with 3+ booleans are hard to review because intent disappears behind positional values.",
        "fix_pattern": "Use a named-field options struct, ideally with Default for ergonomic updates.",
        "example_before": "deploy(true, false, true, false);",
        "example_after": "deploy(DeployOptions { verbose: true, force: true, ..Default::default() });",
        "references": ["Rust API Guidelines: builder/options patterns"],
    },
    "unwrap_chains": {
        "title": "Replace unwrap/expect chains with `?`",
        "explanation": "Repeated unwrap/expect calls create multiple crash points instead of one recoverable error path.",
        "fix_pattern": "Return Result, propagate failures with `?`, and add context where the caller needs more runtime detail.",
        "example_before": "let text = fs::read_to_string(path).unwrap();\nlet parsed = serde_json::from_str(&text).unwrap();",
        "example_after": "let text = fs::read_to_string(path)?;\nlet parsed = serde_json::from_str(&text)?;",
        "references": ["Rust Book: Recoverable Errors with Result", "Rust Book: The ? Operator"],
    },
    "type_conversions": {
        "title": "Eliminate redundant conversion chains",
        "explanation": "Conversions like String -> &str -> String add noise and allocation without changing the value.",
        "fix_pattern": "Keep values borrowed when only reading, or clone/move once at the actual ownership boundary.",
        "example_before": "let name = config.name.as_str().to_string();",
        "example_after": "let name = config.name.clone();",
        "references": ["Rust Book: Ownership", "Rust Book: References and Borrowing"],
    },
    "magic_numbers": {
        "title": "Name slice-related magic numbers",
        "explanation": "Raw numbers in slice limits hide whether the value is a preview limit, page size, or truncation rule.",
        "fix_pattern": "Lift the number into a named constant and reuse that constant at every related call site.",
        "example_before": "for item in results[:10]:\n    ...",
        "example_after": "MAX_DISPLAY_ROWS = 10\nfor item in results[:MAX_DISPLAY_ROWS]:\n    ...",
        "references": ["PEP 8: Constants", "Clean Code: Meaningful Names"],
    },
    "clone_density": {
        "title": "Reduce clone density with clearer ownership",
        "explanation": "Frequent cloning often means the code is working around unclear ownership instead of modeling data flow directly.",
        "fix_pattern": "Prefer references for read-only access, clone only the specific fields needed, and move values when ownership really changes.",
        "example_before": "let name = config.name.clone();\nlet items = data.items.clone();",
        "example_after": "do_work(&config.name, &data.items);",
        "references": ["Rust Book: References and Borrowing"],
    },
    "dict_as_struct": {
        "title": "Replace large returned dicts with typed data",
        "explanation": "Large returned dicts create invisible schemas that editors and type checkers cannot validate.",
        "fix_pattern": "Use a dataclass, TypedDict, or named object for the returned shape and update callers to use typed fields.",
        "example_before": "return {'name': job.name, 'status': job.state, 'progress': job.pct, 'started': job.t0, 'elapsed': elapsed}",
        "example_after": "@dataclass\nclass JobStatus:\n    name: str\n    status: str\n    progress: float",
        "references": ["Python docs: dataclasses", "PEP 589: TypedDict"],
    },
    "unnecessary_intermediates": {
        "title": "Return expressions directly when the temp name adds nothing",
        "explanation": "Assign-then-return with names like `result` or `output` adds indirection without adding meaning.",
        "fix_pattern": "Return the expression directly unless the temporary variable documents a real intermediate concept.",
        "example_before": "result = compute_items()\nreturn result",
        "example_after": "return compute_items()",
        "references": ["PEP 20: Simple is better than complex"],
    },
    "vague_errors": {
        "title": "Include runtime context in error messages",
        "explanation": "An error without the path, id, or input that triggered it forces the next reviewer to reproduce the problem just to understand it.",
        "fix_pattern": "Add the relevant runtime variables to the error message or use contextual error helpers like `with_context`.",
        "example_before": '.context("failed to parse config")?',
        "example_after": '.with_context(|| format!("failed to parse config at {path:?}"))?',
        "references": ["anyhow crate: Error context"],
    },
    "defensive_overchecking": {
        "title": "Consolidate repeated isinstance checks",
        "explanation": "Long chains of isinstance checks act like a manual dispatch table and are harder to review than one combined check or pattern match.",
        "fix_pattern": "Use isinstance(value, (...)), match/case, or a Protocol/ABC instead of repeating the same variable in many branches.",
        "example_before": "if isinstance(value, str): ...\nelif isinstance(value, int): ...\nelif isinstance(value, float): ...",
        "example_after": "match value:\n    case str(): ...\n    case int(): ...\n    case float(): ...",
        "references": ["PEP 634: Structural Pattern Matching"],
    },
    "single_use_helpers": {
        "title": "Inline single-use private helpers when they add no abstraction",
        "explanation": "Tiny helpers called once often fragment the control flow without creating real reuse or conceptual boundaries.",
        "fix_pattern": "Inline trivial one-off helpers unless they encapsulate a meaningful concept, testing seam, or shared abstraction boundary.",
        "example_before": "def _format_name(name: str) -> str:\n    return name.strip().title()",
        "example_after": "name = data['name'].strip().title()",
        "references": ["Refactoring: Inline Function"],
    },
    "suppressive_broad_handler": {
        "title": "Make fail-soft broad handlers observable",
        "explanation": "A broad handler that silently returns a sentinel or passes onward hides the original failure and makes incident review much harder.",
        "fix_pattern": "Narrow the exception type, emit runtime context before falling back, or return a typed result that makes the degraded path explicit.",
        "example_before": "except Exception:\n    return None",
        "example_after": 'except Exception as exc:\n    logger.warning("cache refresh failed for %s: %s", key, exc)\n    return CacheResult.missed(reason="refresh_failed")',
        "references": ["Python docs: logging", "Effective Python: Prefer explicit error handling"],
    },
    "weak_exception_translation": {
        "title": "Translate exceptions with runtime context",
        "explanation": "Re-raising a generic message like 'failed to load config' forces the next reviewer to reproduce the error just to find the failing input.",
        "fix_pattern": "Include the path/id/input that failed, or attach structured context before wrapping the exception.",
        "example_before": 'except OSError as exc:\n    raise RuntimeError("failed to read config") from exc',
        "example_after": 'except OSError as exc:\n    raise RuntimeError(f"failed to read config at {path}") from exc',
        "references": ["Python docs: Exception chaining", "Effective Python: Raise exceptions with context"],
    },
}
BEST_PRACTICE_LIBRARY.update(CONCURRENCY_PRACTICES)
BEST_PRACTICE_LIBRARY.update(RUST_PRACTICES)

SIGNAL_TO_PRACTICE: tuple[tuple[str, str, str], ...] = (
    ("concurrency_risk", "nested", "nested_locks"),
    ("concurrency_risk", "Arc<Mutex", "arc_mutex_spawn"),
    ("concurrency_risk", "AtomicBool", "atomic_relaxed_multi_flag"),
    ("concurrency_risk", "Relaxed", "atomic_relaxed_multi_flag"),
    ("concurrency_risk", "poison", "poison_recovery"),
    ("race_condition", "nested", "nested_locks"),
    ("race_condition", "Arc<Mutex", "arc_mutex_spawn"),
    ("race_condition", "Relaxed", "atomic_relaxed_multi_flag"),
    ("race_condition", "poison", "poison_recovery"),
    ("design_smell", "getattr", "getattr_density"),
    ("design_smell", "object", "untyped_object_param"),
    ("design_smell", "format helper", "format_helper_sprawl"),
    ("design_smell", "bool parameters", "boolean_params_python"),
    ("design_smell", "string literals", "stringly_typed_python"),
    ("design_smell", "string-literal arms", "stringly_typed_rust"),
    ("error_handling", ".unwrap()", "unwrap_chains"),
    ("error_handling", ".expect()", "unwrap_chains"),
    ("ownership_smell", ".clone()", "clone_density"),
    ("ownership_smell", "ownership-copying", "clone_density"),
    ("ownership_smell", "round-trip", "type_conversions"),
    ("ownership_smell", ".as_str()", "type_conversions"),
    ("ownership_smell", ".as_ref()", "type_conversions"),
    ("design_smell", "magic-number slice", "magic_numbers"),
    ("design_smell", "returns dict with", "dict_as_struct"),
    ("design_smell", "assign-then-return", "unnecessary_intermediates"),
    ("error_handling", "error messages without runtime context", "vague_errors"),
    ("design_smell", "isinstance()", "defensive_overchecking"),
    ("design_smell", "private functions called only once", "single_use_helpers"),
    ("error_handling", "suppressive broad handler", "suppressive_broad_handler"),
    (
        "error_handling",
        "translated exception without runtime context",
        "weak_exception_translation",
    ),
)


def match_best_practice(hint: dict[str, Any]) -> dict[str, Any] | None:
    """Return the best-practice entry matching a probe finding."""
    risk_type = str(hint.get("risk_type", ""))
    signals_text = " ".join(str(signal) for signal in hint.get("signals", []))
    file_path = str(hint.get("file", ""))
    is_rust = file_path.endswith(".rs")

    for entry_risk_type, keyword, practice_key in SIGNAL_TO_PRACTICE:
        if entry_risk_type != risk_type or keyword not in signals_text:
            continue
        if practice_key == "boolean_params_python" and is_rust:
            return BEST_PRACTICE_LIBRARY.get("boolean_params_rust")
        if practice_key == "stringly_typed_python" and is_rust:
            return BEST_PRACTICE_LIBRARY.get("stringly_typed_rust")
        return BEST_PRACTICE_LIBRARY.get(practice_key)
    return None
