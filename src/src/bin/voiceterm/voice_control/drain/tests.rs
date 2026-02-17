use super::message_processing::apply_macro_mode;
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
        app: AppConfig::parse_from(["test"]),
        prompt_regex: None,
        prompt_log: None,
        auto_voice: false,
        auto_voice_idle_ms: 1200,
        transcript_idle_ms: 250,
        voice_send_mode: send_mode,
        theme_name: None,
        no_color: false,
        hud_right_panel: crate::config::HudRightPanel::Ribbon,
        hud_border_style: crate::config::HudBorderStyle::Theme,
        hud_right_panel_recording_only: true,
        hud_style: crate::config::HudStyle::Full,
        latency_display: crate::config::LatencyDisplayMode::Short,
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
        ..Default::default()
    };

    update_last_latency(&mut status_state, Some(started_at), Some(&metrics), now);

    assert_eq!(status_state.last_latency_ms, Some(220));
    assert_eq!(status_state.latency_history_ms, vec![220]);
}

#[test]
fn update_last_latency_uses_elapsed_minus_capture_when_stt_missing() {
    let mut status_state = StatusLineState::new();
    let now = Instant::now();
    let started_at = now - Duration::from_millis(2000);
    let metrics = CaptureMetrics {
        capture_ms: 1500,
        transcribe_ms: 0,
        ..Default::default()
    };

    update_last_latency(&mut status_state, Some(started_at), Some(&metrics), now);

    assert_eq!(status_state.last_latency_ms, Some(500));
    assert_eq!(status_state.latency_history_ms, vec![500]);
}

#[test]
fn update_last_latency_hides_badge_when_metrics_missing() {
    let mut status_state = StatusLineState::new();
    status_state.last_latency_ms = Some(777);
    status_state.push_latency_sample(777);
    let now = Instant::now();
    let started_at = now - Duration::from_millis(1400);

    update_last_latency(&mut status_state, Some(started_at), None, now);

    assert_eq!(status_state.last_latency_ms, None);
    assert_eq!(status_state.latency_history_ms, vec![777]);
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
