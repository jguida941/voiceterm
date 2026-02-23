//! Wake-word listener runtime with explicit thread lifecycle ownership.
//!
//! The detector runs locally and sends wake events into the event loop so
//! wake-triggered capture reuses the same recording/transcription pipeline as
//! manual hotkeys.

use anyhow::{anyhow, Result};
use crossbeam_channel::{bounded, Receiver, Sender, TrySendError};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
#[cfg(test)]
use std::sync::{Mutex, OnceLock};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};
use voiceterm::{
    audio,
    config::{AppConfig, VadEngineKind},
    log_debug, stt,
};

const WAKE_EVENT_CHANNEL_CAPACITY: usize = 8;
const WAKE_LISTENER_IDLE_SLEEP_MS: u64 = 80;
const WAKE_LISTENER_PAUSE_SLEEP_MS: u64 = 120;
const WAKE_LISTENER_JOIN_POLL_MS: u64 = 5;
const WAKE_LISTENER_JOIN_TIMEOUT_MS: u64 = 1000;
const WAKE_LISTENER_RETRY_BACKOFF_MS: u64 = 1500;
const WAKE_LISTENER_NO_AUDIO_BACKOFF_MS: u64 = 650;

// Keep the wake listener stream open longer to avoid frequent OS-level
// microphone indicator flapping caused by rapid open/close cycles.
const WAKE_CAPTURE_MAX_MS: u64 = 8000;
const WAKE_CAPTURE_SILENCE_TAIL_MS: u64 = 220;
const WAKE_CAPTURE_MIN_SPEECH_MS: u64 = 120;
const WAKE_CAPTURE_LOOKBACK_MS: u64 = 200;
const WAKE_CAPTURE_BUFFER_MS: u64 = 1600;
const WAKE_CAPTURE_CHANNEL_CAPACITY: usize = 8;

const WAKE_MIN_COOLDOWN_MS: u64 = 500;
const WAKE_MAX_COOLDOWN_MS: u64 = 10_000;
const WAKE_MIN_SENSITIVITY: f32 = 0.0;
const WAKE_MAX_SENSITIVITY: f32 = 1.0;

const WAKE_VAD_DB_AT_MIN_SENSITIVITY: f32 = -24.0;
const WAKE_VAD_DB_AT_MAX_SENSITIVITY: f32 = -56.0;

const HOTWORD_PHRASES: &[&str] = &[
    "hey codex",
    "ok codex",
    "okay codex",
    "hey claude",
    "ok claude",
    "okay claude",
    "hey voiceterm",
    "ok voiceterm",
    "okay voiceterm",
    "voiceterm",
];
// Keep detections short and command-like to reduce false positives from
// background conversation that merely mentions a wake phrase.
const WAKE_MAX_TRANSCRIPT_TOKENS: usize = 12;
const WAKE_MAX_PREFIX_TOKENS: usize = 1;
const WAKE_MAX_SUFFIX_TOKENS: usize = 3;
const WAKE_LEADING_PHRASE_MAX_SUFFIX_TOKENS: usize = 8;
const WAKE_LEADING_SINGLE_WORD_MAX_SUFFIX_TOKENS: usize = 6;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum WakeWordEvent {
    Detected,
    SendStagedInput,
}

#[derive(Debug, Clone, Copy, PartialEq)]
struct WakeSettings {
    sensitivity: f32,
    cooldown_ms: u64,
}

impl WakeSettings {
    #[must_use = "wake settings should stay within configured safety bounds"]
    fn clamped(sensitivity: f32, cooldown_ms: u64) -> Self {
        Self {
            sensitivity: sensitivity.clamp(WAKE_MIN_SENSITIVITY, WAKE_MAX_SENSITIVITY),
            cooldown_ms: cooldown_ms.clamp(WAKE_MIN_COOLDOWN_MS, WAKE_MAX_COOLDOWN_MS),
        }
    }
}

#[cfg(test)]
type SpawnListenerHook = fn(
    Sender<WakeWordEvent>,
    Arc<AtomicBool>,
    Arc<AtomicBool>,
    Arc<AtomicBool>,
    WakeSettings,
) -> JoinHandle<()>;

#[cfg(test)]
fn spawn_listener_hook_cell() -> &'static Mutex<Option<SpawnListenerHook>> {
    static CELL: OnceLock<Mutex<Option<SpawnListenerHook>>> = OnceLock::new();
    CELL.get_or_init(|| Mutex::new(None))
}

#[cfg(test)]
fn set_spawn_listener_hook(hook: Option<SpawnListenerHook>) {
    let mut slot = spawn_listener_hook_cell()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    *slot = hook;
}

struct WakeListener {
    stop_flag: Arc<AtomicBool>,
    pause_flag: Arc<AtomicBool>,
    capture_stop_flag: Arc<AtomicBool>,
    handle: JoinHandle<()>,
}

impl WakeListener {
    fn set_paused(&self, paused: bool) {
        self.pause_flag.store(paused, Ordering::Relaxed);
        if paused {
            self.capture_stop_flag.store(true, Ordering::Relaxed);
        }
    }

    fn request_stop(&self) {
        self.stop_flag.store(true, Ordering::Relaxed);
        self.capture_stop_flag.store(true, Ordering::Relaxed);
    }
}

/// Runtime owner for wake-listening lifecycle and detection event delivery.
pub(crate) struct WakeWordRuntime {
    app_config: AppConfig,
    detection_tx: Sender<WakeWordEvent>,
    detection_rx: Receiver<WakeWordEvent>,
    listener: Option<WakeListener>,
    active_settings: Option<WakeSettings>,
    start_retry_after: Option<Instant>,
    #[cfg(test)]
    listener_active_override: Option<bool>,
}

impl WakeWordRuntime {
    #[must_use = "wake runtime must be retained for detection events to flow"]
    pub(crate) fn new(app_config: AppConfig) -> Self {
        let (detection_tx, detection_rx) = bounded(WAKE_EVENT_CHANNEL_CAPACITY);
        Self {
            app_config,
            detection_tx,
            detection_rx,
            listener: None,
            active_settings: None,
            start_retry_after: None,
            #[cfg(test)]
            listener_active_override: None,
        }
    }

    /// Cloneable receiver used by the event loop to consume wake detections.
    #[must_use = "receiver is required to consume wake detections"]
    pub(crate) fn receiver(&self) -> Receiver<WakeWordEvent> {
        self.detection_rx.clone()
    }

    /// Returns true when a wake listener thread is currently active.
    #[must_use = "callers should use this to keep HUD state aligned with runtime health"]
    pub(crate) fn is_listener_active(&self) -> bool {
        #[cfg(test)]
        if let Some(active) = self.listener_active_override {
            return active;
        }
        self.listener.is_some()
    }

    #[cfg(test)]
    pub(crate) fn set_listener_active_override_for_tests(&mut self, active: Option<bool>) {
        self.listener_active_override = active;
    }

    /// Reconcile listener lifecycle with current settings and capture activity.
    pub(crate) fn sync(
        &mut self,
        enabled: bool,
        sensitivity: f32,
        cooldown_ms: u64,
        capture_active: bool,
    ) {
        self.reap_finished_listener();

        if !enabled {
            self.stop_listener();
            self.active_settings = None;
            return;
        }

        let settings = WakeSettings::clamped(sensitivity, cooldown_ms);
        let restart_required = self.listener.is_none()
            || self.active_settings.is_none()
            || self.active_settings != Some(settings);
        if restart_required {
            self.stop_listener();
            if let Some(retry_after) = self.start_retry_after {
                if Instant::now() < retry_after {
                    return;
                }
            }
            match self.start_listener(settings) {
                Ok(()) => {
                    self.active_settings = Some(settings);
                    self.start_retry_after = None;
                }
                Err(err) => {
                    log_debug(&format!("wake-word listener start failed: {err:#}"));
                    self.start_retry_after = Some(
                        Instant::now() + Duration::from_millis(WAKE_LISTENER_RETRY_BACKOFF_MS),
                    );
                    self.active_settings = None;
                    return;
                }
            }
        }

        if let Some(listener) = &self.listener {
            listener.set_paused(capture_active);
        }
    }

    fn reap_finished_listener(&mut self) {
        let finished = self
            .listener
            .as_ref()
            .map(|listener| listener.handle.is_finished())
            .unwrap_or(false);
        if !finished {
            return;
        }
        if let Some(listener) = self.listener.take() {
            join_thread_with_timeout("wake-word", listener.handle);
        }
        self.active_settings = None;
    }

    fn start_listener(&mut self, settings: WakeSettings) -> Result<()> {
        let stop_flag = Arc::new(AtomicBool::new(false));
        let pause_flag = Arc::new(AtomicBool::new(false));
        let capture_stop_flag = Arc::new(AtomicBool::new(false));

        #[cfg(test)]
        if let Some(hook) = *spawn_listener_hook_cell()
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner())
        {
            self.listener = Some(WakeListener {
                stop_flag: stop_flag.clone(),
                pause_flag: pause_flag.clone(),
                capture_stop_flag: capture_stop_flag.clone(),
                handle: hook(
                    self.detection_tx.clone(),
                    stop_flag,
                    pause_flag,
                    capture_stop_flag,
                    settings,
                ),
            });
            return Ok(());
        }

        let detector = AudioWakeDetector::new(self.app_config.clone(), settings.sensitivity)
            .map_err(|err| anyhow!("failed to initialize local wake detector: {err:#}"))?;
        let listener = WakeListener {
            stop_flag: stop_flag.clone(),
            pause_flag: pause_flag.clone(),
            capture_stop_flag: capture_stop_flag.clone(),
            handle: spawn_wake_listener_thread(
                detector,
                settings.cooldown_ms,
                self.detection_tx.clone(),
                stop_flag,
                pause_flag,
                capture_stop_flag,
            ),
        };
        self.listener = Some(listener);
        Ok(())
    }

    fn stop_listener(&mut self) {
        let Some(listener) = self.listener.take() else {
            return;
        };
        listener.request_stop();
        join_thread_with_timeout("wake-word", listener.handle);
        self.active_settings = None;
    }
}

impl Drop for WakeWordRuntime {
    fn drop(&mut self) {
        self.stop_listener();
    }
}

fn spawn_wake_listener_thread(
    mut detector: AudioWakeDetector,
    cooldown_ms: u64,
    detection_tx: Sender<WakeWordEvent>,
    stop_flag: Arc<AtomicBool>,
    pause_flag: Arc<AtomicBool>,
    capture_stop_flag: Arc<AtomicBool>,
) -> JoinHandle<()> {
    thread::spawn(move || {
        let cooldown = Duration::from_millis(cooldown_ms);
        let mut last_detection_at: Option<Instant> = None;
        while !stop_flag.load(Ordering::Relaxed) {
            if pause_flag.load(Ordering::Relaxed) {
                capture_stop_flag.store(true, Ordering::Relaxed);
                thread::sleep(Duration::from_millis(WAKE_LISTENER_PAUSE_SLEEP_MS));
                continue;
            }
            if let Some(last) = last_detection_at {
                let elapsed = last.elapsed();
                if elapsed < cooldown {
                    let remaining = cooldown - elapsed;
                    thread::sleep(
                        remaining.min(Duration::from_millis(WAKE_LISTENER_IDLE_SLEEP_MS)),
                    );
                    continue;
                }
            }
            match detector.listen_once(&capture_stop_flag) {
                Ok(WakeListenOutcome::Detected(event)) => {
                    match detection_tx.try_send(event) {
                        Ok(()) => {
                            // Pause immediately so wake-triggered capture can claim
                            // the microphone without listener overlap races.
                            pause_flag.store(true, Ordering::Relaxed);
                            capture_stop_flag.store(true, Ordering::Relaxed);
                            last_detection_at = Some(Instant::now());
                        }
                        Err(TrySendError::Full(_)) => {
                            log_debug("wake-word detection dropped: queue full");
                        }
                        Err(TrySendError::Disconnected(_)) => break,
                    }
                }
                Ok(WakeListenOutcome::NoDetection) => {}
                Ok(WakeListenOutcome::NoAudio) => {
                    thread::sleep(Duration::from_millis(WAKE_LISTENER_NO_AUDIO_BACKOFF_MS));
                }
                Err(err) => {
                    log_debug(&format!("wake-word listen cycle failed: {err:#}"));
                    thread::sleep(Duration::from_millis(WAKE_LISTENER_RETRY_BACKOFF_MS));
                }
            }
        }
    })
}

fn join_thread_with_timeout(name: &str, handle: JoinHandle<()>) {
    let timeout = Duration::from_millis(WAKE_LISTENER_JOIN_TIMEOUT_MS);
    let deadline = Instant::now() + timeout;
    while !handle.is_finished() && Instant::now() < deadline {
        thread::sleep(Duration::from_millis(WAKE_LISTENER_JOIN_POLL_MS));
    }
    if handle.is_finished() {
        if let Err(err) = handle.join() {
            log_debug(&format!(
                "{name} listener thread panicked during shutdown: {err:?}"
            ));
        }
    } else {
        log_debug(&format!(
            "{name} listener thread did not exit within {}ms; detaching",
            timeout.as_millis()
        ));
    }
}

struct AudioWakeDetector {
    recorder: audio::Recorder,
    transcriber: stt::Transcriber,
    app_config: AppConfig,
    vad_cfg: audio::VadConfig,
    vad_engine: Box<dyn audio::VadEngine + Send>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum WakeListenOutcome {
    Detected(WakeWordEvent),
    NoDetection,
    NoAudio,
}

impl AudioWakeDetector {
    fn new(app_config: AppConfig, sensitivity: f32) -> Result<Self> {
        let model_path = app_config
            .whisper_model_path
            .clone()
            .ok_or_else(|| anyhow!("no whisper model path configured for wake-word detector"))?;
        let recorder = audio::Recorder::new(app_config.input_device.as_deref())?;
        let transcriber = stt::Transcriber::new(&model_path)?;

        let mut pipeline_cfg = app_config.voice_pipeline_config();
        pipeline_cfg.max_capture_ms = WAKE_CAPTURE_MAX_MS;
        pipeline_cfg.silence_tail_ms = WAKE_CAPTURE_SILENCE_TAIL_MS;
        pipeline_cfg.min_speech_ms_before_stt_start = WAKE_CAPTURE_MIN_SPEECH_MS;
        pipeline_cfg.lookback_ms = WAKE_CAPTURE_LOOKBACK_MS;
        pipeline_cfg.buffer_ms = WAKE_CAPTURE_BUFFER_MS;
        pipeline_cfg.channel_capacity = WAKE_CAPTURE_CHANNEL_CAPACITY;
        pipeline_cfg.vad_threshold_db = sensitivity_to_wake_vad_threshold_db(sensitivity);
        let vad_cfg = audio::VadConfig::from(&pipeline_cfg);
        let vad_engine = create_vad_engine(&pipeline_cfg);

        Ok(Self {
            recorder,
            transcriber,
            app_config,
            vad_cfg,
            vad_engine,
        })
    }

    fn listen_once(&mut self, capture_stop_flag: &Arc<AtomicBool>) -> Result<WakeListenOutcome> {
        capture_stop_flag.store(false, Ordering::Relaxed);
        self.vad_engine.reset();
        let capture = match self.recorder.record_with_vad(
            &self.vad_cfg,
            self.vad_engine.as_mut(),
            Some(capture_stop_flag.clone()),
            None,
        ) {
            Ok(capture) => capture,
            Err(err) => {
                if capture_stop_flag.load(Ordering::Relaxed) {
                    return Ok(WakeListenOutcome::NoDetection);
                }
                if is_expected_no_audio_error(&err) {
                    return Ok(WakeListenOutcome::NoAudio);
                }
                return Err(err);
            }
        };

        if capture_stop_flag.load(Ordering::Relaxed)
            || capture.audio.is_empty()
            || capture.metrics.speech_ms == 0
        {
            return Ok(WakeListenOutcome::NoDetection);
        }

        let transcript = self
            .transcriber
            .transcribe(&capture.audio, &self.app_config)?;
        Ok(match detect_wake_event(&transcript) {
            Some(event) => WakeListenOutcome::Detected(event),
            None => WakeListenOutcome::NoDetection,
        })
    }
}

fn create_vad_engine(
    cfg: &voiceterm::config::VoicePipelineConfig,
) -> Box<dyn audio::VadEngine + Send> {
    match cfg.vad_engine {
        VadEngineKind::Simple => Box::new(audio::SimpleThresholdVad::new(cfg.vad_threshold_db)),
        VadEngineKind::Earshot => {
            #[cfg(feature = "vad_earshot")]
            {
                Box::new(voiceterm::vad_earshot::EarshotVad::from_config(cfg))
            }
            #[cfg(not(feature = "vad_earshot"))]
            {
                unreachable!("earshot VAD requested without 'vad_earshot' feature")
            }
        }
    }
}

#[must_use = "sensitivity should map to a deterministic dB threshold"]
fn sensitivity_to_wake_vad_threshold_db(sensitivity: f32) -> f32 {
    let normalized = sensitivity.clamp(WAKE_MIN_SENSITIVITY, WAKE_MAX_SENSITIVITY);
    WAKE_VAD_DB_AT_MIN_SENSITIVITY
        + (WAKE_VAD_DB_AT_MAX_SENSITIVITY - WAKE_VAD_DB_AT_MIN_SENSITIVITY) * normalized
}

#[must_use = "hotword matching expects normalized lowercase transcript text"]
fn normalize_for_hotword_match(raw: &str) -> String {
    let mut normalized = String::with_capacity(raw.len());
    let mut previous_was_space = true;
    for ch in raw.chars() {
        if ch.is_ascii_alphanumeric() {
            normalized.push(ch.to_ascii_lowercase());
            previous_was_space = false;
            continue;
        }
        if previous_was_space {
            continue;
        }
        if ch.is_ascii_whitespace() || matches!(ch, '-' | '_' | '\'') {
            normalized.push(' ');
            previous_was_space = true;
        }
    }
    normalized.trim().to_string()
}

#[cfg(test)]
#[must_use = "wake detection should evaluate normalized transcript and phrase policy"]
fn transcript_matches_hotword(raw: &str) -> bool {
    detect_wake_event(raw).is_some()
}

#[must_use = "wake event classification should map transcript intent into runtime action"]
fn detect_wake_event(raw: &str) -> Option<WakeWordEvent> {
    let normalized = normalize_for_hotword_match(raw);
    if normalized.is_empty() {
        return None;
    }
    let raw_tokens: Vec<&str> = normalized.split_whitespace().collect();
    if raw_tokens.is_empty() {
        return None;
    }
    let canonical_tokens = canonicalize_hotword_tokens(&raw_tokens);
    if canonical_tokens.len() > WAKE_MAX_TRANSCRIPT_TOKENS {
        return None;
    }
    let haystack_tokens: Vec<&str> = canonical_tokens.iter().map(String::as_str).collect();
    let has_wake_phrase = HOTWORD_PHRASES.iter().any(|phrase| {
        let phrase_tokens: Vec<&str> = phrase.split_whitespace().collect();
        find_hotword_window_start(&haystack_tokens, &phrase_tokens).is_some()
    });
    if !has_wake_phrase {
        return None;
    }

    let token_count = haystack_tokens.len();
    let last_token_is_send_intent = wake_suffix_is_send_intent(&haystack_tokens[token_count - 1..]);
    let last_two_tokens_are_send_intent =
        token_count >= 2 && wake_suffix_is_send_intent(&haystack_tokens[token_count - 2..]);
    if last_token_is_send_intent || last_two_tokens_are_send_intent {
        return Some(WakeWordEvent::SendStagedInput);
    }
    Some(WakeWordEvent::Detected)
}

#[cfg(test)]
#[must_use = "hotword check determines whether wake capture should trigger"]
fn contains_hotword_phrase(normalized: &str) -> bool {
    if normalized.is_empty() {
        return false;
    }
    let raw_tokens: Vec<&str> = normalized.split_whitespace().collect();
    if raw_tokens.is_empty() {
        return false;
    }
    let canonical_tokens = canonicalize_hotword_tokens(&raw_tokens);
    if canonical_tokens.len() > WAKE_MAX_TRANSCRIPT_TOKENS {
        return false;
    }
    let haystack_tokens: Vec<&str> = canonical_tokens.iter().map(String::as_str).collect();
    HOTWORD_PHRASES
        .iter()
        .any(|phrase| contains_hotword_window(&haystack_tokens, phrase))
}

#[must_use = "token canonicalization keeps wake matching resilient to common STT splits"]
fn canonicalize_hotword_tokens(tokens: &[&str]) -> Vec<String> {
    let mut canonical = Vec::with_capacity(tokens.len());
    let mut idx = 0;
    while idx < tokens.len() {
        if idx + 1 < tokens.len() {
            if tokens[idx] == "code" && tokens[idx + 1] == "x" {
                canonical.push("codex".to_string());
                idx += 2;
                continue;
            }
            if tokens[idx] == "voice" && tokens[idx + 1] == "term" {
                canonical.push("voiceterm".to_string());
                idx += 2;
                continue;
            }
        }
        let token = match tokens[idx] {
            "codec" | "codecs" | "kodak" | "kodaks" | "kodex" => "codex",
            other => other,
        };
        canonical.push(token.to_string());
        idx += 1;
    }
    canonical
}

#[cfg(test)]
#[must_use = "phrase match result is required for wake-word gating"]
fn contains_hotword_window(haystack_tokens: &[&str], phrase: &str) -> bool {
    let phrase_tokens: Vec<&str> = phrase.split_whitespace().collect();
    find_hotword_window_start(haystack_tokens, &phrase_tokens).is_some()
}

#[must_use = "hotword window search determines phrase location and suffix intent parsing"]
fn find_hotword_window_start(haystack_tokens: &[&str], phrase_tokens: &[&str]) -> Option<usize> {
    if phrase_tokens.is_empty() || haystack_tokens.len() < phrase_tokens.len() {
        return None;
    }
    haystack_tokens
        .windows(phrase_tokens.len())
        .enumerate()
        .find_map(|(start_idx, window)| {
            (window == phrase_tokens
                && hotword_window_is_actionable(
                    start_idx,
                    phrase_tokens.len(),
                    haystack_tokens.len(),
                ))
            .then_some(start_idx)
        })
}

#[must_use = "wake suffix matcher maps concise send phrases into submit action"]
fn wake_suffix_is_send_intent(suffix_tokens: &[&str]) -> bool {
    matches!(
        suffix_tokens,
        ["send"]
            | ["sen"]
            | ["send", "message"]
            | ["sen", "message"]
            | ["submit"]
            | ["send", "now"]
            | ["sen", "now"]
            | ["submit", "now"]
    )
}

#[must_use = "wake phrase window position determines intent confidence"]
fn hotword_window_is_actionable(start_idx: usize, phrase_len: usize, token_count: usize) -> bool {
    let prefix_tokens = start_idx;
    let suffix_tokens = token_count.saturating_sub(start_idx + phrase_len);
    if phrase_len == 1 {
        if prefix_tokens != 0 {
            return false;
        }
        return suffix_tokens <= WAKE_LEADING_SINGLE_WORD_MAX_SUFFIX_TOKENS;
    }
    if prefix_tokens == 0 {
        return suffix_tokens <= WAKE_LEADING_PHRASE_MAX_SUFFIX_TOKENS;
    }
    prefix_tokens <= WAKE_MAX_PREFIX_TOKENS && suffix_tokens <= WAKE_MAX_SUFFIX_TOKENS
}

#[must_use = "capture error classification avoids noisy logs during silence"]
fn is_expected_no_audio_error(err: &anyhow::Error) -> bool {
    err.to_string().contains("no samples captured")
}

#[cfg(test)]
mod tests;
