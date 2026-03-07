//! Wake-word listener runtime with explicit thread lifecycle ownership.
//!
//! The detector runs locally and sends wake events into the event loop so
//! wake-triggered capture reuses the same recording/transcription pipeline as
//! manual hotkeys.

mod detector;
mod matcher;
#[cfg(test)]
mod tests;

use anyhow::{anyhow, Result};
use crossbeam_channel::{bounded, Receiver, Sender, TrySendError};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
#[cfg(test)]
use std::sync::{Mutex, OnceLock};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};
use voiceterm::{config::AppConfig, log_debug};

use detector::{resolve_wake_vad_threshold_db, AudioWakeDetector, WakeListenOutcome};

// Re-export matcher and detector items used by tests (via `use super::*`).
#[cfg(test)]
pub(self) use detector::sensitivity_to_wake_vad_threshold_db;
#[cfg(test)]
pub(self) use matcher::{
    canonicalize_hotword_tokens, contains_hotword_phrase, detect_wake_event,
    normalize_for_hotword_match, transcript_matches_hotword,
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
const WAKE_MIN_COOLDOWN_MS: u64 = 500;
const WAKE_MAX_COOLDOWN_MS: u64 = 10_000;
const WAKE_MIN_SENSITIVITY: f32 = 0.0;
const WAKE_MAX_SENSITIVITY: f32 = 1.0;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum WakeWordEvent {
    Detected,
    SendStagedInput,
}

#[derive(Debug, Clone, Copy, PartialEq)]
struct WakeSettings {
    sensitivity: f32,
    cooldown_ms: u64,
    voice_vad_threshold_db: f32,
    effective_vad_threshold_db: f32,
}

impl WakeSettings {
    #[must_use = "wake settings should stay within configured safety bounds"]
    fn clamped(sensitivity: f32, cooldown_ms: u64, voice_vad_threshold_db: f32) -> Self {
        let clamped_sensitivity = sensitivity.clamp(WAKE_MIN_SENSITIVITY, WAKE_MAX_SENSITIVITY);
        let clamped_cooldown = cooldown_ms.clamp(WAKE_MIN_COOLDOWN_MS, WAKE_MAX_COOLDOWN_MS);
        let clamped_voice_vad_threshold = voice_vad_threshold_db.clamp(
            detector::WAKE_VAD_THRESHOLD_MIN_DB,
            detector::WAKE_VAD_THRESHOLD_MAX_DB,
        );
        let effective_vad_threshold_db =
            resolve_wake_vad_threshold_db(clamped_sensitivity, clamped_voice_vad_threshold);
        if (clamped_sensitivity - sensitivity).abs() > f32::EPSILON
            || clamped_cooldown != cooldown_ms
            || (clamped_voice_vad_threshold - voice_vad_threshold_db).abs() > f32::EPSILON
        {
            log_debug(&format!(
                "wake-word settings clamped: sensitivity {sensitivity:.3} -> {clamped_sensitivity:.3}, cooldown {cooldown_ms} -> {clamped_cooldown}ms, voice_vad {voice_vad_threshold_db:.1} -> {clamped_voice_vad_threshold:.1}"
            ));
        }
        Self {
            sensitivity: clamped_sensitivity,
            cooldown_ms: clamped_cooldown,
            voice_vad_threshold_db: clamped_voice_vad_threshold,
            effective_vad_threshold_db,
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
    prioritize_send_flag: Arc<AtomicBool>,
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

    fn set_prioritize_send_window(&self, enabled: bool) {
        self.prioritize_send_flag.store(enabled, Ordering::Relaxed);
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
        voice_vad_threshold_db: f32,
        prioritize_send_intent_window: bool,
        capture_active: bool,
    ) {
        self.reap_finished_listener();

        if !enabled {
            let _ = self.stop_listener();
            if self.listener.is_none() {
                self.active_settings = None;
            }
            return;
        }

        let settings = WakeSettings::clamped(sensitivity, cooldown_ms, voice_vad_threshold_db);
        let restart_required = self.listener.is_none()
            || self.active_settings.is_none()
            || self.active_settings != Some(settings);
        if restart_required {
            if !self.stop_listener() {
                return;
            }
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
            listener.set_prioritize_send_window(prioritize_send_intent_window && !capture_active);
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
            let WakeListener {
                stop_flag,
                pause_flag,
                capture_stop_flag,
                prioritize_send_flag,
                handle,
            } = listener;
            if let Err(handle) = join_thread_with_timeout("wake-word", handle) {
                self.listener = Some(WakeListener {
                    stop_flag,
                    pause_flag,
                    capture_stop_flag,
                    prioritize_send_flag,
                    handle,
                });
                return;
            }
        }
        self.active_settings = None;
    }

    fn start_listener(&mut self, settings: WakeSettings) -> Result<()> {
        let stop_flag = Arc::new(AtomicBool::new(false));
        let pause_flag = Arc::new(AtomicBool::new(false));
        let capture_stop_flag = Arc::new(AtomicBool::new(false));
        let prioritize_send_flag = Arc::new(AtomicBool::new(false));

        #[cfg(test)]
        if let Some(hook) = *spawn_listener_hook_cell()
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner())
        {
            self.listener = Some(WakeListener {
                stop_flag: stop_flag.clone(),
                pause_flag: pause_flag.clone(),
                capture_stop_flag: capture_stop_flag.clone(),
                prioritize_send_flag: prioritize_send_flag.clone(),
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

        let detector = AudioWakeDetector::new(self.app_config.clone(), settings)
            .map_err(|err| anyhow!("failed to initialize local wake detector: {err:#}"))?;
        let listener = WakeListener {
            stop_flag: stop_flag.clone(),
            pause_flag: pause_flag.clone(),
            capture_stop_flag: capture_stop_flag.clone(),
            prioritize_send_flag: prioritize_send_flag.clone(),
            handle: spawn_wake_listener_thread(
                detector,
                settings.cooldown_ms,
                self.detection_tx.clone(),
                stop_flag,
                pause_flag,
                capture_stop_flag,
                prioritize_send_flag,
            ),
        };
        self.listener = Some(listener);
        Ok(())
    }

    fn stop_listener(&mut self) -> bool {
        let Some(listener) = self.listener.take() else {
            self.active_settings = None;
            return true;
        };
        listener.request_stop();
        let WakeListener {
            stop_flag,
            pause_flag,
            capture_stop_flag,
            prioritize_send_flag,
            handle,
        } = listener;
        match join_thread_with_timeout("wake-word", handle) {
            Ok(()) => {
                self.active_settings = None;
                true
            }
            Err(handle) => {
                self.listener = Some(WakeListener {
                    stop_flag,
                    pause_flag,
                    capture_stop_flag,
                    prioritize_send_flag,
                    handle,
                });
                self.start_retry_after =
                    Some(Instant::now() + Duration::from_millis(WAKE_LISTENER_RETRY_BACKOFF_MS));
                log_debug(
                    "wake-word listener still running after stop request; deferring restart/disable",
                );
                false
            }
        }
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
    prioritize_send_flag: Arc<AtomicBool>,
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
            let prioritize_send_window = prioritize_send_flag.load(Ordering::Relaxed);
            let mut within_cooldown = false;
            if let Some(last) = last_detection_at {
                let elapsed = last.elapsed();
                if elapsed < cooldown {
                    within_cooldown = true;
                    if !prioritize_send_window {
                        let remaining = cooldown - elapsed;
                        thread::sleep(
                            remaining.min(Duration::from_millis(WAKE_LISTENER_IDLE_SLEEP_MS)),
                        );
                        continue;
                    }
                }
            }
            match detector.listen_once(&capture_stop_flag) {
                Ok(WakeListenOutcome::Detected(event)) => {
                    if within_cooldown
                        && !allow_cooldown_bypass_for_event(event, prioritize_send_window)
                    {
                        continue;
                    }
                    match detection_tx.try_send(event) {
                        Ok(()) => {
                            if matches!(event, WakeWordEvent::Detected) {
                                // Pause immediately so wake-triggered capture can claim
                                // the microphone without listener overlap races.
                                pause_flag.store(true, Ordering::Relaxed);
                                capture_stop_flag.store(true, Ordering::Relaxed);
                            }
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

#[inline]
fn allow_cooldown_bypass_for_event(event: WakeWordEvent, prioritize_send_window: bool) -> bool {
    prioritize_send_window && matches!(event, WakeWordEvent::SendStagedInput)
}

fn join_thread_with_timeout(name: &str, handle: JoinHandle<()>) -> Result<(), JoinHandle<()>> {
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
        return Ok(());
    }
    log_debug(&format!(
        "{name} listener thread did not exit within {}ms",
        timeout.as_millis()
    ));
    Err(handle)
}
