use super::*;
use clap::Parser;
use std::sync::atomic::AtomicUsize;

static SPAWN_LISTENER_CALLS: AtomicUsize = AtomicUsize::new(0);

fn wake_runtime_test_lock() -> &'static Mutex<()> {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    LOCK.get_or_init(|| Mutex::new(()))
}

struct SpawnHookGuard;

impl Drop for SpawnHookGuard {
    fn drop(&mut self) {
        set_spawn_listener_hook(None);
        SPAWN_LISTENER_CALLS.store(0, Ordering::Relaxed);
    }
}

fn install_spawn_listener_hook(hook: SpawnListenerHook) -> SpawnHookGuard {
    set_spawn_listener_hook(Some(hook));
    SPAWN_LISTENER_CALLS.store(0, Ordering::Relaxed);
    SpawnHookGuard
}

fn hook_spawn_listener(
    _detection_tx: Sender<WakeWordEvent>,
    stop_flag: Arc<AtomicBool>,
    pause_flag: Arc<AtomicBool>,
    capture_stop_flag: Arc<AtomicBool>,
    _settings: WakeSettings,
) -> JoinHandle<()> {
    SPAWN_LISTENER_CALLS.fetch_add(1, Ordering::Relaxed);
    thread::spawn(move || {
        while !stop_flag.load(Ordering::Relaxed) {
            if pause_flag.load(Ordering::Relaxed) {
                capture_stop_flag.store(true, Ordering::Relaxed);
            }
            thread::sleep(Duration::from_millis(2));
        }
    })
}

#[test]
fn normalize_for_hotword_match_collapses_punctuation_and_case() {
    assert_eq!(
        normalize_for_hotword_match("  Hey, CODEX!!!  "),
        "hey codex"
    );
    assert_eq!(
        normalize_for_hotword_match("ok___voiceterm\nplease"),
        "ok voiceterm please"
    );
}

#[test]
fn canonicalize_hotword_tokens_merges_common_split_aliases() {
    let codex = canonicalize_hotword_tokens(&["hey", "code", "x", "now"]);
    let codex_tokens: Vec<&str> = codex.iter().map(String::as_str).collect();
    assert_eq!(codex_tokens, vec!["hey", "codex", "now"]);

    let codex_alias = canonicalize_hotword_tokens(&["hey", "codecs", "please"]);
    let codex_alias_tokens: Vec<&str> = codex_alias.iter().map(String::as_str).collect();
    assert_eq!(codex_alias_tokens, vec!["hey", "codex", "please"]);

    let voiceterm = canonicalize_hotword_tokens(&["ok", "voice", "term", "start"]);
    let voiceterm_tokens: Vec<&str> = voiceterm.iter().map(String::as_str).collect();
    assert_eq!(voiceterm_tokens, vec!["ok", "voiceterm", "start"]);
}

#[test]
fn contains_hotword_phrase_detects_supported_aliases() {
    assert!(contains_hotword_phrase("please hey codex start"));
    assert!(contains_hotword_phrase("okay code x"));
    assert!(contains_hotword_phrase("hey codecs start"));
    assert!(contains_hotword_phrase("hey kodak start"));
    assert!(contains_hotword_phrase("okay claude"));
    assert!(contains_hotword_phrase("voiceterm"));
    assert!(contains_hotword_phrase("hey voice term"));
    assert!(contains_hotword_phrase("voice term start recording"));
    assert!(contains_hotword_phrase("voiceterm start recording"));
    assert!(contains_hotword_phrase(
        "hey codex run this command right now quickly"
    ));
    assert!(contains_hotword_phrase(
        "voiceterm please compile and run tests now"
    ));
    assert!(!contains_hotword_phrase("hello codec"));
    assert!(!contains_hotword_phrase("random noise words"));
    assert!(!contains_hotword_phrase(
        "we should review the code x integration details"
    ));
    assert!(!contains_hotword_phrase(
        "we should maybe hey codex after this meeting"
    ));
    assert!(!contains_hotword_phrase(
        "the team discussed voiceterm integration details"
    ));
    assert!(!contains_hotword_phrase(
        "please hey codex run this command right now quickly"
    ));
}

#[test]
fn detect_wake_event_maps_send_suffix_intent() {
    assert_eq!(
        detect_wake_event("hey codex send"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("hey codecs send"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("hey kodak sen"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("ok claude send message"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("voiceterm submit now"),
        Some(WakeWordEvent::SendStagedInput)
    );
}

#[test]
fn detect_wake_event_defaults_to_detection_for_non_send_suffix() {
    assert_eq!(
        detect_wake_event("hey codex run tests"),
        Some(WakeWordEvent::Detected)
    );
    assert_eq!(
        detect_wake_event("please hey codex start"),
        Some(WakeWordEvent::Detected)
    );
    assert_eq!(detect_wake_event("random words"), None);
}

#[test]
fn wake_runtime_sync_starts_stops_and_pauses_listener() {
    let _lock = wake_runtime_test_lock()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let _guard = install_spawn_listener_hook(hook_spawn_listener);
    let mut runtime = WakeWordRuntime::new(AppConfig::parse_from(["voiceterm"]));

    runtime.sync(true, 0.55, 2000, false);
    assert!(
        runtime.listener.is_some(),
        "expected wake listener to start when enabled"
    );
    assert!(
        runtime.is_listener_active(),
        "listener activity helper should report running listener"
    );
    assert_eq!(
        SPAWN_LISTENER_CALLS.load(Ordering::Relaxed),
        1,
        "expected exactly one listener spawn"
    );

    runtime.sync(true, 0.55, 2000, true);
    let paused = runtime
        .listener
        .as_ref()
        .map(|listener| listener.pause_flag.load(Ordering::Relaxed))
        .unwrap_or(false);
    assert!(
        paused,
        "expected listener pause flag to track capture-active"
    );

    runtime.sync(false, 0.55, 2000, false);
    assert!(
        runtime.listener.is_none(),
        "expected wake listener to stop when disabled"
    );
    assert!(
        !runtime.is_listener_active(),
        "listener activity helper should report no listener after stop"
    );
}

#[test]
fn wake_runtime_sync_restarts_listener_when_settings_change() {
    let _lock = wake_runtime_test_lock()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let _guard = install_spawn_listener_hook(hook_spawn_listener);
    let mut runtime = WakeWordRuntime::new(AppConfig::parse_from(["voiceterm"]));

    runtime.sync(true, 0.40, 2000, false);
    runtime.sync(true, 0.40, 2000, false);
    runtime.sync(true, 0.70, 2000, false);
    runtime.sync(true, 0.70, 3000, false);

    assert_eq!(
        SPAWN_LISTENER_CALLS.load(Ordering::Relaxed),
        3,
        "expected listener restart only when wake settings change"
    );
}

#[test]
fn hotword_guardrail_soak_false_positive_and_latency() {
    const SOAK_ROUNDS: usize = 5000;
    const P95_LATENCY_BUDGET_US: u128 = 15_000;
    let positives = [
        "hey codex",
        "hey codex please start",
        "ok codex open settings",
        "okay claude",
        "voiceterm",
        "voiceterm start recording",
        "hey voiceterm explain this error",
    ];
    let negatives = [
        "we should maybe hey codex after this meeting",
        "the team discussed voiceterm integration details",
        "please hey codex run this command right now quickly",
        "hello codec",
        "this is only a random conversation",
        "we said okay and moved on",
    ];
    let eval_count = (positives.len() + negatives.len()) * SOAK_ROUNDS;
    let mut latencies_us = Vec::with_capacity(eval_count);
    let mut misses = 0usize;
    let mut false_positives = 0usize;

    for _ in 0..SOAK_ROUNDS {
        for sample in positives {
            let started_at = Instant::now();
            if !transcript_matches_hotword(sample) {
                misses += 1;
            }
            latencies_us.push(started_at.elapsed().as_micros());
        }
        for sample in negatives {
            let started_at = Instant::now();
            if transcript_matches_hotword(sample) {
                false_positives += 1;
            }
            latencies_us.push(started_at.elapsed().as_micros());
        }
    }

    assert_eq!(misses, 0, "expected no misses in curated positive corpus");
    assert_eq!(
        false_positives, 0,
        "expected no false positives in curated negative corpus"
    );
    latencies_us.sort_unstable();
    let p95_idx = ((latencies_us.len() - 1) * 95) / 100;
    let p95_us = latencies_us[p95_idx];
    assert!(
        p95_us <= P95_LATENCY_BUDGET_US,
        "wake matcher p95 latency {p95_us}us exceeded budget {P95_LATENCY_BUDGET_US}us"
    );
}

#[test]
fn sensitivity_mapping_is_monotonic_and_clamped() {
    let low = sensitivity_to_wake_vad_threshold_db(0.0);
    let mid = sensitivity_to_wake_vad_threshold_db(0.5);
    let high = sensitivity_to_wake_vad_threshold_db(1.0);
    let below = sensitivity_to_wake_vad_threshold_db(-5.0);
    let above = sensitivity_to_wake_vad_threshold_db(5.0);

    assert!(
        low > mid,
        "expected lower sensitivity to use stricter dB gate"
    );
    assert!(mid > high, "expected higher sensitivity to lower dB gate");
    assert_eq!(low, below);
    assert_eq!(high, above);
}
