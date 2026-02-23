//! Canonical memory event schema and shared types for the Memory Studio runtime.
//!
//! All memory ingestion normalizes to the [`MemoryEvent`] envelope.
//! Derived layers (units, cards, packs) reference events by ID.

use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::SystemTime;

/// Schema version for forward-compatible migration checks.
pub(crate) const SCHEMA_VERSION: u32 = 1;

// ---------------------------------------------------------------------------
// Event types
// ---------------------------------------------------------------------------

/// Canonical event type taxonomy (v1).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum EventType {
    ChatTurn,
    VoiceTranscript,
    CommandIntent,
    CommandRun,
    FileChange,
    TestResult,
    Decision,
    Handoff,
    Summary,
}

impl EventType {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::ChatTurn => "chat_turn",
            Self::VoiceTranscript => "voice_transcript",
            Self::CommandIntent => "command_intent",
            Self::CommandRun => "command_run",
            Self::FileChange => "file_change",
            Self::TestResult => "test_result",
            Self::Decision => "decision",
            Self::Handoff => "handoff",
            Self::Summary => "summary",
        }
    }
}

/// Role of the event originator.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum EventRole {
    User,
    Assistant,
    System,
}

impl EventRole {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::User => "user",
            Self::Assistant => "assistant",
            Self::System => "system",
        }
    }
}

/// Source channel that produced the event.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum EventSource {
    VoiceCapture,
    PtyInput,
    PtyOutput,
    DevtoolOutput,
    GitSummary,
    Manual,
}

impl EventSource {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::VoiceCapture => "voice_capture",
            Self::PtyInput => "pty_input",
            Self::PtyOutput => "pty_output",
            Self::DevtoolOutput => "devtool_output",
            Self::GitSummary => "git_summary",
            Self::Manual => "manual",
        }
    }
}

/// Retrieval eligibility state for events, units, and cards.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "snake_case")]
pub(crate) enum RetrievalState {
    #[default]
    Eligible,
    Quarantined,
    Deprecated,
}

impl RetrievalState {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::Eligible => "eligible",
            Self::Quarantined => "quarantined",
            Self::Deprecated => "deprecated",
        }
    }

    pub(crate) fn from_str(s: &str) -> Option<Self> {
        match s {
            "eligible" => Some(Self::Eligible),
            "quarantined" => Some(Self::Quarantined),
            "deprecated" => Some(Self::Deprecated),
            _ => None,
        }
    }
}

// ---------------------------------------------------------------------------
// Artifact reference
// ---------------------------------------------------------------------------

/// A reference to an external artifact linked from an event.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct ArtifactRef {
    pub(crate) kind: String,
    #[serde(rename = "ref")]
    pub(crate) reference: String,
}

// ---------------------------------------------------------------------------
// Canonical event envelope
// ---------------------------------------------------------------------------

/// The canonical memory event envelope. All ingestion normalizes to this schema.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct MemoryEvent {
    pub(crate) event_id: String,
    pub(crate) session_id: String,
    pub(crate) project_id: String,
    pub(crate) ts: String,
    pub(crate) source: EventSource,
    pub(crate) event_type: EventType,
    pub(crate) role: EventRole,
    pub(crate) text: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub(crate) topic_tags: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub(crate) entities: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub(crate) task_refs: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub(crate) artifacts: Vec<ArtifactRef>,
    #[serde(default)]
    pub(crate) importance: f64,
    #[serde(default = "default_confidence")]
    pub(crate) confidence: f64,
    #[serde(default)]
    pub(crate) retrieval_state: RetrievalState,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub(crate) hash: Option<String>,
}

fn default_confidence() -> f64 {
    1.0
}

// ---------------------------------------------------------------------------
// Memory control modes (MP-243)
// ---------------------------------------------------------------------------

/// User memory-control mode governing capture and retrieval behavior.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "snake_case")]
pub(crate) enum MemoryMode {
    /// No capture, no retrieval.
    Off,
    /// Write events/cards, do not inject into prompts.
    CaptureOnly,
    /// Capture + retrieval enabled (default).
    #[default]
    Assist,
    /// Keep store immutable until resumed.
    Paused,
    /// Ephemeral session; no durable writeback.
    Incognito,
}

impl MemoryMode {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::Off => "off",
            Self::CaptureOnly => "capture_only",
            Self::Assist => "assist",
            Self::Paused => "paused",
            Self::Incognito => "incognito",
        }
    }

    pub(crate) fn from_str(s: &str) -> Option<Self> {
        match s {
            "off" => Some(Self::Off),
            "capture_only" => Some(Self::CaptureOnly),
            "assist" => Some(Self::Assist),
            "paused" => Some(Self::Paused),
            "incognito" => Some(Self::Incognito),
            _ => None,
        }
    }

    /// Whether this mode allows writing events to durable storage.
    pub(crate) fn allows_capture(self) -> bool {
        matches!(self, Self::CaptureOnly | Self::Assist)
    }

    /// Whether this mode allows retrieval/injection into prompts.
    pub(crate) fn allows_retrieval(self) -> bool {
        matches!(self, Self::Assist)
    }

    /// Cycle to the next mode in order.
    pub(crate) fn cycle(self) -> Self {
        match self {
            Self::Off => Self::CaptureOnly,
            Self::CaptureOnly => Self::Assist,
            Self::Assist => Self::Paused,
            Self::Paused => Self::Incognito,
            Self::Incognito => Self::Off,
        }
    }

    pub(crate) fn display_label(self) -> &'static str {
        match self {
            Self::Off => "Off",
            Self::CaptureOnly => "Capture Only",
            Self::Assist => "Assist",
            Self::Paused => "Paused",
            Self::Incognito => "Incognito",
        }
    }
}

// ---------------------------------------------------------------------------
// Retention policy (MP-235)
// ---------------------------------------------------------------------------

/// Retention policy for memory governance.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "snake_case")]
pub(crate) enum RetentionPolicy {
    Days7,
    #[default]
    Days30,
    Days90,
    Forever,
}

impl RetentionPolicy {
    pub(crate) fn as_days(self) -> Option<u32> {
        match self {
            Self::Days7 => Some(7),
            Self::Days30 => Some(30),
            Self::Days90 => Some(90),
            Self::Forever => None,
        }
    }

    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::Days7 => "7d",
            Self::Days30 => "30d",
            Self::Days90 => "90d",
            Self::Forever => "forever",
        }
    }

    pub(crate) fn from_str(s: &str) -> Option<Self> {
        match s {
            "7d" => Some(Self::Days7),
            "30d" => Some(Self::Days30),
            "90d" => Some(Self::Days90),
            "forever" => Some(Self::Forever),
            _ => None,
        }
    }

    pub(crate) fn cycle(self) -> Self {
        match self {
            Self::Days7 => Self::Days30,
            Self::Days30 => Self::Days90,
            Self::Days90 => Self::Forever,
            Self::Forever => Self::Days7,
        }
    }

    pub(crate) fn display_label(self) -> &'static str {
        match self {
            Self::Days7 => "7 days",
            Self::Days30 => "30 days",
            Self::Days90 => "90 days",
            Self::Forever => "Forever",
        }
    }
}

// ---------------------------------------------------------------------------
// Action policy tiers (MP-234)
// ---------------------------------------------------------------------------

/// Command safety tier for the Action Center.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "snake_case")]
pub(crate) enum ActionPolicyTier {
    /// Execute directly (safe, read-only commands).
    ReadOnly,
    /// Preview + explicit user approval required.
    #[default]
    ConfirmRequired,
    /// Cannot execute from overlay.
    Blocked,
}

impl ActionPolicyTier {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::ReadOnly => "read_only",
            Self::ConfirmRequired => "confirm_required",
            Self::Blocked => "blocked",
        }
    }

    pub(crate) fn display_label(self) -> &'static str {
        match self {
            Self::ReadOnly => "Read Only",
            Self::ConfirmRequired => "Confirm Required",
            Self::Blocked => "Blocked",
        }
    }
}

/// A single action template in the Action Center.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct ActionTemplate {
    pub(crate) id: String,
    pub(crate) label: String,
    pub(crate) command: String,
    pub(crate) policy: ActionPolicyTier,
    pub(crate) description: String,
}

/// Result of an action execution, logged as a memory event.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct ActionRunResult {
    pub(crate) action_id: String,
    pub(crate) command: String,
    pub(crate) exit_code: Option<i32>,
    pub(crate) stdout_preview: String,
    pub(crate) stderr_preview: String,
    pub(crate) approved_by: String,
    pub(crate) ts: String,
}

// ---------------------------------------------------------------------------
// ID generation helpers
// ---------------------------------------------------------------------------

static EVENT_ID_COUNTER: AtomicU64 = AtomicU64::new(0);
static SESSION_ID_COUNTER: AtomicU64 = AtomicU64::new(0);

fn unix_epoch_millis() -> u128 {
    SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0)
}

fn next_id_suffix(counter: &AtomicU64) -> u64 {
    let sequence = counter.fetch_add(1, Ordering::Relaxed).wrapping_add(1);
    let now_ns = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_nanos() as u64)
        .unwrap_or(sequence);
    let pid = u64::from(std::process::id());
    splitmix64(now_ns ^ sequence.rotate_left(13) ^ (pid << 32))
}

fn splitmix64(mut x: u64) -> u64 {
    x = x.wrapping_add(0x9E37_79B9_7F4A_7C15);
    x = (x ^ (x >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    x = (x ^ (x >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    x ^ (x >> 31)
}

/// Generate a unique event ID using timestamp + non-deterministic suffix.
pub(crate) fn generate_event_id() -> String {
    let ts = unix_epoch_millis();
    let suffix = next_id_suffix(&EVENT_ID_COUNTER);
    format!("evt_{ts:013}_{suffix:016x}")
}

/// Generate a unique session ID.
pub(crate) fn generate_session_id() -> String {
    let ts = unix_epoch_millis();
    let suffix = next_id_suffix(&SESSION_ID_COUNTER);
    format!("sess_{ts:013}_{suffix:016x}")
}

/// Generate an ISO 8601 timestamp string.
pub(crate) fn iso_timestamp() -> String {
    let ts = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    // Simple ISO format: seconds-level precision is sufficient for event logging.
    let secs = ts / 1000;
    let millis = ts % 1000;
    format_epoch_millis(secs, millis)
}

fn format_epoch_millis(epoch_secs: u128, millis: u128) -> String {
    // Compute date/time from epoch seconds (simplified UTC calendar).
    let total_secs = epoch_secs as u64;
    let days = total_secs / 86400;
    let day_secs = total_secs % 86400;
    let hours = day_secs / 3600;
    let minutes = (day_secs % 3600) / 60;
    let seconds = day_secs % 60;

    // Compute year/month/day from days since epoch (simplified Gregorian).
    let (year, month, day) = days_to_ymd(days);

    format!("{year:04}-{month:02}-{day:02}T{hours:02}:{minutes:02}:{seconds:02}.{millis:03}Z")
}

fn days_to_ymd(mut days: u64) -> (u64, u64, u64) {
    // Civil date from days since 1970-01-01 (simplified algorithm).
    let mut year = 1970u64;
    loop {
        let year_days = if is_leap(year) { 366 } else { 365 };
        if days < year_days {
            break;
        }
        days -= year_days;
        year += 1;
    }
    let leap = is_leap(year);
    let month_days: [u64; 12] = [
        31,
        if leap { 29 } else { 28 },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    let mut month = 0u64;
    for (i, &md) in month_days.iter().enumerate() {
        if days < md {
            month = i as u64 + 1;
            break;
        }
        days -= md;
    }
    if month == 0 {
        month = 12;
    }
    (year, month, days + 1)
}

fn is_leap(year: u64) -> bool {
    (year % 4 == 0 && year % 100 != 0) || year % 400 == 0
}

// ---------------------------------------------------------------------------
// Context pack types (MP-232)
// ---------------------------------------------------------------------------

/// Type of context pack.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum ContextPackType {
    Boot,
    Task,
}

/// A scored evidence item inside a context pack.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct PackEvidence {
    pub(crate) event_id: String,
    pub(crate) score: f64,
    pub(crate) text_preview: String,
    pub(crate) source: String,
}

/// Token budget tracking for context pack generation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct TokenBudget {
    pub(crate) target: usize,
    pub(crate) used: usize,
    pub(crate) trimmed: usize,
}

/// A generated context pack for AI boot or task handoff workflows.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct ContextPack {
    pub(crate) query: String,
    pub(crate) generated_at: String,
    pub(crate) pack_type: ContextPackType,
    pub(crate) summary: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub(crate) active_tasks: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub(crate) recent_decisions: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub(crate) changed_files: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub(crate) open_questions: Vec<String>,
    pub(crate) token_budget: TokenBudget,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub(crate) evidence: Vec<PackEvidence>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn event_id_is_unique_across_calls() {
        let id1 = generate_event_id();
        let id2 = generate_event_id();
        assert!(id1.starts_with("evt_"));
        assert!(id2.starts_with("evt_"));
        assert_ne!(id1, id2);
    }

    #[test]
    fn session_id_format() {
        let id1 = generate_session_id();
        let id2 = generate_session_id();
        assert!(id1.starts_with("sess_"));
        assert!(id2.starts_with("sess_"));
        assert_ne!(id1, id2);
    }

    #[test]
    fn iso_timestamp_is_valid_format() {
        let ts = iso_timestamp();
        assert!(ts.ends_with('Z'));
        assert!(ts.contains('T'));
        assert_eq!(ts.len(), 24); // YYYY-MM-DDTHH:MM:SS.mmmZ
    }

    #[test]
    fn memory_mode_cycle_is_complete() {
        let start = MemoryMode::Off;
        let mut mode = start;
        let mut seen = vec![mode];
        for _ in 0..10 {
            mode = mode.cycle();
            seen.push(mode);
        }
        // After 5 cycles we should be back to Off.
        assert_eq!(seen[5], MemoryMode::Off);
    }

    #[test]
    fn memory_mode_capture_retrieval_semantics() {
        assert!(!MemoryMode::Off.allows_capture());
        assert!(!MemoryMode::Off.allows_retrieval());

        assert!(MemoryMode::CaptureOnly.allows_capture());
        assert!(!MemoryMode::CaptureOnly.allows_retrieval());

        assert!(MemoryMode::Assist.allows_capture());
        assert!(MemoryMode::Assist.allows_retrieval());

        assert!(!MemoryMode::Paused.allows_capture());
        assert!(!MemoryMode::Paused.allows_retrieval());

        assert!(!MemoryMode::Incognito.allows_capture());
        assert!(!MemoryMode::Incognito.allows_retrieval());
    }

    #[test]
    fn memory_mode_roundtrip_str() {
        for mode in [
            MemoryMode::Off,
            MemoryMode::CaptureOnly,
            MemoryMode::Assist,
            MemoryMode::Paused,
            MemoryMode::Incognito,
        ] {
            let s = mode.as_str();
            let parsed = MemoryMode::from_str(s);
            assert_eq!(parsed, Some(mode), "roundtrip failed for {s}");
        }
    }

    #[test]
    fn retention_policy_cycle() {
        let start = RetentionPolicy::Days7;
        assert_eq!(start.cycle(), RetentionPolicy::Days30);
        assert_eq!(RetentionPolicy::Forever.cycle(), RetentionPolicy::Days7);
    }

    #[test]
    fn retention_policy_days() {
        assert_eq!(RetentionPolicy::Days7.as_days(), Some(7));
        assert_eq!(RetentionPolicy::Days30.as_days(), Some(30));
        assert_eq!(RetentionPolicy::Days90.as_days(), Some(90));
        assert_eq!(RetentionPolicy::Forever.as_days(), None);
    }

    #[test]
    fn retention_policy_roundtrip_str() {
        for policy in [
            RetentionPolicy::Days7,
            RetentionPolicy::Days30,
            RetentionPolicy::Days90,
            RetentionPolicy::Forever,
        ] {
            let s = policy.as_str();
            let parsed = RetentionPolicy::from_str(s);
            assert_eq!(parsed, Some(policy), "roundtrip failed for {s}");
        }
    }

    #[test]
    fn action_policy_tier_labels() {
        assert_eq!(ActionPolicyTier::ReadOnly.as_str(), "read_only");
        assert_eq!(
            ActionPolicyTier::ConfirmRequired.as_str(),
            "confirm_required"
        );
        assert_eq!(ActionPolicyTier::Blocked.as_str(), "blocked");
    }

    #[test]
    fn retrieval_state_roundtrip() {
        for state in [
            RetrievalState::Eligible,
            RetrievalState::Quarantined,
            RetrievalState::Deprecated,
        ] {
            let s = state.as_str();
            let parsed = RetrievalState::from_str(s);
            assert_eq!(parsed, Some(state));
        }
    }

    #[test]
    fn event_serialization_roundtrip() {
        let event = MemoryEvent {
            event_id: "evt_test_001".to_string(),
            session_id: "sess_test_001".to_string(),
            project_id: "test_project".to_string(),
            ts: "2026-02-19T12:00:00.000Z".to_string(),
            source: EventSource::PtyInput,
            event_type: EventType::ChatTurn,
            role: EventRole::User,
            text: "hello world".to_string(),
            topic_tags: vec!["test".to_string()],
            entities: vec![],
            task_refs: vec![],
            artifacts: vec![],
            importance: 0.5,
            confidence: 0.9,
            retrieval_state: RetrievalState::Eligible,
            hash: None,
        };
        let json = serde_json::to_string(&event).expect("serialize");
        let parsed: MemoryEvent = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(parsed.event_id, event.event_id);
        assert_eq!(parsed.text, event.text);
        assert_eq!(parsed.source, event.source);
        assert_eq!(parsed.retrieval_state, event.retrieval_state);
    }

    #[test]
    fn days_to_ymd_epoch() {
        let (y, m, d) = days_to_ymd(0);
        assert_eq!((y, m, d), (1970, 1, 1));
    }

    #[test]
    fn days_to_ymd_known_date() {
        // 2026-02-19 = 20503 days since epoch
        let (y, m, d) = days_to_ymd(20503);
        assert_eq!((y, m, d), (2026, 2, 19));
    }

    #[test]
    fn context_pack_type_serialization() {
        let boot = serde_json::to_string(&ContextPackType::Boot).expect("serialize");
        assert_eq!(boot, "\"boot\"");
        let task = serde_json::to_string(&ContextPackType::Task).expect("serialize");
        assert_eq!(task, "\"task\"");
    }
}
