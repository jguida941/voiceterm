use super::message_processing::{apply_macro_mode, clear_last_latency, update_last_latency};
use super::*;
use crate::config::VoiceSendMode;
use crate::transcript::TranscriptSession;
use clap::Parser;
use std::fs;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};
use voiceterm::audio::CaptureMetrics;
use voiceterm::config::AppConfig;

#[derive(Default)]
struct StubSession {
    sent: Vec<String>,
    sent_with_newline: Vec<String>,
}

impl TranscriptSession for StubSession {
    fn send_text(&mut self, text: &str) -> anyhow::Result<()> {
        self.sent.push(text.to_string());
        Ok(())
    }

    fn send_text_with_newline(&mut self, text: &str) -> anyhow::Result<()> {
        self.sent_with_newline.push(text.to_string());
        Ok(())
    }
}

fn write_test_macros_file(yaml: &str) -> std::path::PathBuf {
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("clock")
        .as_nanos();
    let mut dir = std::env::temp_dir();
    dir.push(format!(
        "voiceterm-intent-{}-{}",
        now,
        COUNTER.fetch_add(1, Ordering::Relaxed)
    ));
    let macros_dir = dir.join(".voiceterm");
    fs::create_dir_all(&macros_dir).expect("create macro dir");
    fs::write(macros_dir.join("macros.yaml"), yaml).expect("write macro file");
    dir
}

fn test_overlay_config(send_mode: VoiceSendMode) -> OverlayConfig {
    OverlayConfig {
        help: false,
        app: AppConfig::parse_from(["test"]),
        prompt_regex: None,
        prompt_log: None,
        auto_voice: false,
        auto_voice_idle_ms: 1200,
        transcript_idle_ms: 250,
        voice_send_mode: send_mode,
        wake_word: false,
        wake_word_sensitivity: 0.55,
        wake_word_cooldown_ms: 2000,
        theme_name: None,
        no_color: false,
        hud_right_panel: crate::config::HudRightPanel::Ribbon,
        hud_border_style: crate::config::HudBorderStyle::Theme,
        hud_right_panel_recording_only: true,
        hud_style: crate::config::HudStyle::Full,
        latency_display: crate::config::LatencyDisplayMode::Short,
        image_mode: false,
        image_capture_command: None,
        dev_mode: false,
        dev_log: false,
        dev_path: None,
        minimal_hud: false,
        backend: "codex".to_string(),
        codex: false,
        claude: false,
        gemini: false,
        login: false,
    }
}

#[test]
fn apply_macro_mode_applies_macros_when_enabled() {
    let dir = write_test_macros_file(
        r#"
macros:
  run tests: cargo test --all-features
"#,
    );
    let voice_macros = VoiceMacros::load_for_project(&dir);
    let (text, mode, note) =
        apply_macro_mode("run tests", VoiceSendMode::Auto, true, &voice_macros);
    assert_eq!(text, "cargo test --all-features");
    assert_eq!(mode, VoiceSendMode::Auto);
    assert_eq!(note.as_deref(), Some("macro 'run tests'"));
    let _ = fs::remove_dir_all(&dir);
}

#[test]
fn apply_macro_mode_skips_macros_when_disabled() {
    let dir = write_test_macros_file(
        r#"
macros:
  run tests: cargo test --all-features
"#,
    );
    let voice_macros = VoiceMacros::load_for_project(&dir);
    let (text, mode, note) =
        apply_macro_mode("run tests", VoiceSendMode::Insert, false, &voice_macros);
    assert_eq!(text, "run tests");
    assert_eq!(mode, VoiceSendMode::Insert);
    assert!(note.is_none());
    let _ = fs::remove_dir_all(&dir);
}

#[test]
fn handle_voice_message_sends_status_and_transcript() {
    let config = test_overlay_config(VoiceSendMode::Auto);
    let mut session = StubSession::default();
    let (writer_tx, writer_rx) = crossbeam_channel::unbounded();
    let mut deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut session_stats = SessionStats::new();
    let mut ctx = VoiceMessageContext {
        config: &config,
        session: &mut session,
        writer_tx: &writer_tx,
        status_clear_deadline: &mut deadline,
        current_status: &mut current_status,
        status_state: &mut status_state,
        session_stats: &mut session_stats,
        auto_voice_enabled: false,
    };

    handle_voice_message(
        VoiceJobMessage::Transcript {
            text: " hello ".to_string(),
            source: VoiceCaptureSource::Native,
            metrics: None,
        },
        &mut ctx,
    );

    let msg = writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message");
    match msg {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Transcript ready"));
        }
        _ => panic!("unexpected writer message"),
    }
    assert_eq!(session.sent_with_newline, vec!["hello"]);
}

#[test]
fn handle_voice_message_no_speech_omits_pipeline_label() {
    let config = test_overlay_config(VoiceSendMode::Insert);
    let mut session = StubSession::default();
    let (writer_tx, writer_rx) = crossbeam_channel::unbounded();
    let mut deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut session_stats = SessionStats::new();
    let mut ctx = VoiceMessageContext {
        config: &config,
        session: &mut session,
        writer_tx: &writer_tx,
        status_clear_deadline: &mut deadline,
        current_status: &mut current_status,
        status_state: &mut status_state,
        session_stats: &mut session_stats,
        auto_voice_enabled: false,
    };

    handle_voice_message(
        VoiceJobMessage::Empty {
            source: VoiceCaptureSource::Native,
            metrics: None,
        },
        &mut ctx,
    );

    let msg = writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message");
    match msg {
        WriterMessage::EnhancedStatus(state) => {
            assert_eq!(state.message, "No speech detected");
            assert!(!state.message.contains("Rust"));
            assert!(!state.message.contains("Python"));
        }
        _ => panic!("unexpected writer message"),
    }
}

#[test]
fn update_last_latency_prefers_stt_metrics_when_available() {
    let mut status_state = StatusLineState::new();
    let now = Instant::now();
    let started_at = now - Duration::from_millis(1800);
    let metrics = CaptureMetrics {
        capture_ms: 1450,
        transcribe_ms: 220,
        speech_ms: 1100,
        ..Default::default()
    };

    update_last_latency(&mut status_state, Some(started_at), Some(&metrics), now);

    assert_eq!(status_state.last_latency_ms, Some(220));
    assert_eq!(status_state.last_latency_speech_ms, Some(1100));
    assert_eq!(status_state.last_latency_rtf_x1000, Some(200));
    assert_eq!(status_state.last_latency_updated_at, Some(now));
    assert_eq!(status_state.latency_history_ms, vec![220]);
}

#[test]
fn update_last_latency_keeps_empty_state_when_stt_missing_and_no_prior_sample() {
    let mut status_state = StatusLineState::new();
    let now = Instant::now();
    let started_at = now - Duration::from_millis(2000);
    let metrics = CaptureMetrics {
        capture_ms: 1500,
        transcribe_ms: 0,
        speech_ms: 1200,
        ..Default::default()
    };

    update_last_latency(&mut status_state, Some(started_at), Some(&metrics), now);

    assert_eq!(status_state.last_latency_ms, None);
    assert!(status_state.last_latency_speech_ms.is_none());
    assert!(status_state.last_latency_rtf_x1000.is_none());
    assert!(status_state.last_latency_updated_at.is_none());
    assert!(status_state.latency_history_ms.is_empty());
}

#[test]
fn update_last_latency_hides_previous_badge_when_stt_missing() {
    let mut status_state = StatusLineState::new();
    status_state.last_latency_ms = Some(412);
    status_state.last_latency_speech_ms = Some(1600);
    status_state.last_latency_rtf_x1000 = Some(257);
    let prior_updated_at = Instant::now() - Duration::from_secs(4);
    status_state.last_latency_updated_at = Some(prior_updated_at);
    status_state.push_latency_sample(412);
    let now = Instant::now();
    let started_at = now - Duration::from_millis(2000);
    let metrics = CaptureMetrics {
        capture_ms: 1500,
        transcribe_ms: 0,
        speech_ms: 1100,
        ..Default::default()
    };

    update_last_latency(&mut status_state, Some(started_at), Some(&metrics), now);

    assert_eq!(status_state.last_latency_ms, None);
    assert!(status_state.last_latency_speech_ms.is_none());
    assert!(status_state.last_latency_rtf_x1000.is_none());
    assert!(status_state.last_latency_updated_at.is_none());
    assert_eq!(status_state.latency_history_ms, vec![412]);
}

#[test]
fn update_last_latency_uses_stt_even_without_recording_start_time() {
    let mut status_state = StatusLineState::new();
    let now = Instant::now();
    let metrics = CaptureMetrics {
        capture_ms: 1000,
        transcribe_ms: 310,
        speech_ms: 1240,
        ..Default::default()
    };

    update_last_latency(&mut status_state, None, Some(&metrics), now);

    assert_eq!(status_state.last_latency_ms, Some(310));
    assert_eq!(status_state.last_latency_speech_ms, Some(1240));
    assert_eq!(status_state.last_latency_rtf_x1000, Some(250));
    assert_eq!(status_state.last_latency_updated_at, Some(now));
    assert_eq!(status_state.latency_history_ms, vec![310]);
}

#[test]
fn update_last_latency_hides_previous_badge_when_metrics_missing() {
    let mut status_state = StatusLineState::new();
    status_state.last_latency_ms = Some(777);
    status_state.last_latency_speech_ms = Some(2000);
    status_state.last_latency_rtf_x1000 = Some(388);
    status_state.last_latency_updated_at = Some(Instant::now() - Duration::from_secs(3));
    status_state.push_latency_sample(777);
    let now = Instant::now();
    let started_at = now - Duration::from_millis(1400);

    update_last_latency(&mut status_state, Some(started_at), None, now);

    assert_eq!(status_state.last_latency_ms, None);
    assert!(status_state.last_latency_speech_ms.is_none());
    assert!(status_state.last_latency_rtf_x1000.is_none());
    assert!(status_state.last_latency_updated_at.is_none());
    assert_eq!(status_state.latency_history_ms, vec![777]);
}

#[test]
fn should_clear_latency_for_empty_depends_on_auto_mode() {
    let empty = VoiceJobMessage::Empty {
        source: VoiceCaptureSource::Native,
        metrics: None,
    };

    assert!(should_clear_latency_for_message(&empty, false));
    assert!(!should_clear_latency_for_message(&empty, true));
}

#[test]
fn should_clear_latency_for_error_is_always_true() {
    let error = VoiceJobMessage::Error("mic unavailable".to_string());
    assert!(should_clear_latency_for_message(&error, false));
    assert!(should_clear_latency_for_message(&error, true));
}

#[test]
fn clear_last_latency_hides_badge_without_erasing_history() {
    let mut status_state = StatusLineState::new();
    status_state.last_latency_ms = Some(420);
    status_state.last_latency_speech_ms = Some(2100);
    status_state.last_latency_rtf_x1000 = Some(200);
    status_state.last_latency_updated_at = Some(Instant::now() - Duration::from_secs(1));
    status_state.push_latency_sample(420);

    clear_last_latency(&mut status_state);

    assert!(status_state.last_latency_ms.is_none());
    assert!(status_state.last_latency_speech_ms.is_none());
    assert!(status_state.last_latency_rtf_x1000.is_none());
    assert!(status_state.last_latency_updated_at.is_none());
    assert_eq!(status_state.latency_history_ms, vec![420]);
}

#[test]
fn clear_capture_metrics_resets_recording_artifacts() {
    let mut status_state = StatusLineState::new();
    status_state.recording_duration = Some(3.2);
    status_state.meter_db = Some(-12.0);
    status_state.meter_levels.extend_from_slice(&[-40.0, -20.0]);

    clear_capture_metrics(&mut status_state);

    assert!(status_state.recording_duration.is_none());
    assert!(status_state.meter_db.is_none());
    assert!(status_state.meter_levels.is_empty());
}
