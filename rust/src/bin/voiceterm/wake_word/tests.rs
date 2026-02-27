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

    let code_alias = canonicalize_hotword_tokens(&["hey", "code"]);
    let code_alias_tokens: Vec<&str> = code_alias.iter().map(String::as_str).collect();
    assert_eq!(code_alias_tokens, vec!["hey", "codex"]);

    let code_send_alias = canonicalize_hotword_tokens(&["hey", "code", "send"]);
    let code_send_alias_tokens: Vec<&str> = code_send_alias.iter().map(String::as_str).collect();
    assert_eq!(code_send_alias_tokens, vec!["hey", "codex", "send"]);

    let coach_alias = canonicalize_hotword_tokens(&["hey", "coach"]);
    let coach_alias_tokens: Vec<&str> = coach_alias.iter().map(String::as_str).collect();
    assert_eq!(coach_alias_tokens, vec!["hey", "codex"]);

    let code_non_wake_alias = canonicalize_hotword_tokens(&["review", "code"]);
    let code_non_wake_alias_tokens: Vec<&str> =
        code_non_wake_alias.iter().map(String::as_str).collect();
    assert_eq!(code_non_wake_alias_tokens, vec!["review", "code"]);

    let codec_alias = canonicalize_hotword_tokens(&["codec", "send"]);
    let codec_alias_tokens: Vec<&str> = codec_alias.iter().map(String::as_str).collect();
    assert_eq!(codec_alias_tokens, vec!["codex", "send"]);

    let voiceterm = canonicalize_hotword_tokens(&["ok", "voice", "term", "start"]);
    let voiceterm_tokens: Vec<&str> = voiceterm.iter().map(String::as_str).collect();
    assert_eq!(voiceterm_tokens, vec!["ok", "voiceterm", "start"]);

    let hate_alias = canonicalize_hotword_tokens(&["hate", "codex"]);
    let hate_alias_tokens: Vec<&str> = hate_alias.iter().map(String::as_str).collect();
    assert_eq!(hate_alias_tokens, vec!["hey", "codex"]);

    let pay_clog_alias = canonicalize_hotword_tokens(&["pay", "clog"]);
    let pay_clog_alias_tokens: Vec<&str> = pay_clog_alias.iter().map(String::as_str).collect();
    assert_eq!(pay_clog_alias_tokens, vec!["hey", "claude"]);

    let cloud_alias = canonicalize_hotword_tokens(&["okay", "cloud", "send"]);
    let cloud_alias_tokens: Vec<&str> = cloud_alias.iter().map(String::as_str).collect();
    assert_eq!(cloud_alias_tokens, vec!["okay", "claude", "send"]);

    let claud_alias = canonicalize_hotword_tokens(&["hey", "claud", "send"]);
    let claud_alias_tokens: Vec<&str> = claud_alias.iter().map(String::as_str).collect();
    assert_eq!(claud_alias_tokens, vec!["hey", "claude", "send"]);

    let clawed_alias = canonicalize_hotword_tokens(&["hey", "clawed", "send"]);
    let clawed_alias_tokens: Vec<&str> = clawed_alias.iter().map(String::as_str).collect();
    assert_eq!(clawed_alias_tokens, vec!["hey", "claude", "send"]);
}

#[test]
fn contains_hotword_phrase_detects_supported_aliases() {
    assert!(contains_hotword_phrase("please hey codex start"));
    assert!(contains_hotword_phrase("okay code x"));
    assert!(contains_hotword_phrase("hey codecs start"));
    assert!(contains_hotword_phrase("hey codes start"));
    assert!(contains_hotword_phrase("hey code"));
    assert!(contains_hotword_phrase("hey coach"));
    assert!(contains_hotword_phrase("hey kodak start"));
    assert!(contains_hotword_phrase("hate codex start"));
    assert!(contains_hotword_phrase("okay claude"));
    assert!(contains_hotword_phrase("okay cloud"));
    assert!(contains_hotword_phrase("pay clog"));
    assert!(contains_hotword_phrase("codex send"));
    assert!(contains_hotword_phrase("claude send"));
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
    assert!(!contains_hotword_phrase("hey code review"));
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
        detect_wake_event("hey codes sent"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("hey coach send"),
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
    assert_eq!(
        detect_wake_event("hey codex send it"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("hey codex sand"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("hey claude sand"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("pay clog sand"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("codex son"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("claude son now"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("hate cloud send this"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("okay cloud sending"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("hey claud send"),
        Some(WakeWordEvent::SendStagedInput)
    );
    assert_eq!(
        detect_wake_event("hey clawed send"),
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
        detect_wake_event("claude explain this"),
        Some(WakeWordEvent::Detected)
    );
    assert_eq!(detect_wake_event("hey code"), Some(WakeWordEvent::Detected));
    assert_eq!(
        detect_wake_event("please hey codex start"),
        Some(WakeWordEvent::Detected)
    );
    assert_eq!(detect_wake_event("i hate codex"), None);
    assert_eq!(detect_wake_event("random words"), None);
}

#[test]
fn wake_runtime_sync_starts_stops_and_pauses_listener() {
    let _lock = wake_runtime_test_lock()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let _guard = install_spawn_listener_hook(hook_spawn_listener);
    let mut runtime = WakeWordRuntime::new(AppConfig::parse_from(["voiceterm"]));

    runtime.sync(true, 0.55, 2000, -35.0, false, false);
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

    runtime.sync(true, 0.55, 2000, -35.0, false, true);
    let paused = runtime
        .listener
        .as_ref()
        .map(|listener| listener.pause_flag.load(Ordering::Relaxed))
        .unwrap_or(false);
    assert!(
        paused,
        "expected listener pause flag to track capture-active"
    );

    runtime.sync(false, 0.55, 2000, -35.0, false, false);
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

    runtime.sync(true, 0.40, 2000, -35.0, false, false);
    runtime.sync(true, 0.40, 2000, -35.0, false, false);
    runtime.sync(true, 0.70, 2000, -35.0, false, false);
    runtime.sync(true, 0.70, 3000, -35.0, false, false);

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
fn wake_runtime_sync_updates_prioritize_send_window_without_unpausing_capture() {
    let _lock = wake_runtime_test_lock()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let _guard = install_spawn_listener_hook(hook_spawn_listener);
    let mut runtime = WakeWordRuntime::new(AppConfig::parse_from(["voiceterm"]));

    runtime.sync(true, 0.55, 2000, -35.0, true, false);
    let prioritized = runtime
        .listener
        .as_ref()
        .map(|listener| listener.prioritize_send_flag.load(Ordering::Relaxed))
        .unwrap_or(false);
    assert!(
        prioritized,
        "expected prioritize-send flag to be enabled when staged send window is active"
    );

    runtime.sync(true, 0.55, 2000, -35.0, true, true);
    let prioritized_while_capture_active = runtime
        .listener
        .as_ref()
        .map(|listener| listener.prioritize_send_flag.load(Ordering::Relaxed))
        .unwrap_or(true);
    assert!(
        !prioritized_while_capture_active,
        "expected prioritize-send flag to stay disabled while capture is active"
    );

    runtime.sync(true, 0.55, 2000, -35.0, false, false);
    let prioritized_after_clear = runtime
        .listener
        .as_ref()
        .map(|listener| listener.prioritize_send_flag.load(Ordering::Relaxed))
        .unwrap_or(true);
    assert!(
        !prioritized_after_clear,
        "expected prioritize-send flag to clear when staged send window ends"
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

#[test]
fn resolve_wake_threshold_tracks_voice_threshold_headroom() {
    let base = resolve_wake_vad_threshold_db(0.55, -35.0);
    let stricter_voice = resolve_wake_vad_threshold_db(0.55, -45.0);
    let less_sensitive_voice = resolve_wake_vad_threshold_db(0.55, -20.0);

    assert!(stricter_voice < base);
    assert!(less_sensitive_voice <= -24.0);
    assert!(less_sensitive_voice >= -62.0);
}
