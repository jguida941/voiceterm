//! Bounded in-memory Dev Mode session aggregation for guarded runtime usage.

use std::collections::VecDeque;

use crate::devtools::events::{DevEvent, DevEventKind};
use crate::VoiceJobMessage;

pub const DEFAULT_DEV_EVENT_RING_CAPACITY: usize = 256;

#[derive(Debug, Clone)]
pub struct DevModeStats {
    events: VecDeque<DevEvent>,
    max_events: usize,
    next_event_id: u64,
    transcript_count: u32,
    empty_count: u32,
    error_count: u32,
    total_words: u64,
    latency_sum_ms: u64,
    latency_samples: u64,
}

impl DevModeStats {
    pub fn with_capacity(max_events: usize) -> Self {
        let max_events = max_events.max(1);
        Self {
            events: VecDeque::with_capacity(max_events),
            max_events,
            next_event_id: 1,
            transcript_count: 0,
            empty_count: 0,
            error_count: 0,
            total_words: 0,
            latency_sum_ms: 0,
            latency_samples: 0,
        }
    }

    pub fn record_voice_message(&mut self, message: &VoiceJobMessage) -> DevEvent {
        let event_id = self.next_event_id;
        self.next_event_id = self.next_event_id.saturating_add(1);

        let event = match message {
            VoiceJobMessage::Transcript {
                text,
                source,
                metrics,
            } => DevEvent::transcript(event_id, *source, text, metrics.as_ref()),
            VoiceJobMessage::Empty { source, metrics } => {
                DevEvent::empty(event_id, *source, metrics.as_ref())
            }
            VoiceJobMessage::Error(message) => DevEvent::error(event_id, message),
        };

        self.update_counters(&event);
        self.push_event(event.clone());
        event
    }

    pub fn snapshot(&self) -> DevModeSnapshot {
        DevModeSnapshot {
            transcript_count: self.transcript_count,
            empty_count: self.empty_count,
            error_count: self.error_count,
            total_words: self.total_words,
            avg_latency_ms: self.average_latency_ms(),
            buffered_events: self.events.len(),
        }
    }

    pub fn recent_events(&self) -> &VecDeque<DevEvent> {
        &self.events
    }

    fn update_counters(&mut self, event: &DevEvent) {
        match event.kind {
            DevEventKind::Transcript => {
                self.transcript_count = self.transcript_count.saturating_add(1);
            }
            DevEventKind::Empty => {
                self.empty_count = self.empty_count.saturating_add(1);
            }
            DevEventKind::Error => {
                self.error_count = self.error_count.saturating_add(1);
            }
        }
        self.total_words = self
            .total_words
            .saturating_add(u64::from(event.transcript_words));
        if let Some(latency_ms) = event.latency_ms {
            self.latency_sum_ms = self.latency_sum_ms.saturating_add(u64::from(latency_ms));
            self.latency_samples = self.latency_samples.saturating_add(1);
        }
    }

    fn push_event(&mut self, event: DevEvent) {
        if self.events.len() >= self.max_events {
            self.events.pop_front();
        }
        self.events.push_back(event);
    }

    fn average_latency_ms(&self) -> Option<u32> {
        (self.latency_samples > 0).then(|| {
            self.latency_sum_ms
                .saturating_div(self.latency_samples)
                .min(u64::from(u32::MAX)) as u32
        })
    }
}

impl Default for DevModeStats {
    fn default() -> Self {
        Self::with_capacity(DEFAULT_DEV_EVENT_RING_CAPACITY)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DevModeSnapshot {
    pub transcript_count: u32,
    pub empty_count: u32,
    pub error_count: u32,
    pub total_words: u64,
    pub avg_latency_ms: Option<u32>,
    pub buffered_events: usize,
}

#[cfg(test)]
mod tests {
    use crate::audio::CaptureMetrics;
    use crate::VoiceCaptureSource;

    use super::*;

    #[test]
    fn transcript_events_update_word_and_latency_counters() {
        let mut stats = DevModeStats::with_capacity(8);
        let metrics = CaptureMetrics {
            transcribe_ms: 240,
            speech_ms: 1200,
            ..Default::default()
        };
        stats.record_voice_message(&VoiceJobMessage::Transcript {
            text: "hello from dev mode".to_string(),
            source: VoiceCaptureSource::Native,
            metrics: Some(metrics),
        });

        let snapshot = stats.snapshot();
        assert_eq!(snapshot.transcript_count, 1);
        assert_eq!(snapshot.empty_count, 0);
        assert_eq!(snapshot.error_count, 0);
        assert_eq!(snapshot.total_words, 4);
        assert_eq!(snapshot.avg_latency_ms, Some(240));
        assert_eq!(snapshot.buffered_events, 1);
    }

    #[test]
    fn ring_buffer_keeps_most_recent_events_only() {
        let mut stats = DevModeStats::with_capacity(2);
        stats.record_voice_message(&VoiceJobMessage::Error("first".to_string()));
        stats.record_voice_message(&VoiceJobMessage::Error("second".to_string()));
        stats.record_voice_message(&VoiceJobMessage::Error("third".to_string()));

        let ids: Vec<u64> = stats
            .recent_events()
            .iter()
            .map(|event| event.event_id)
            .collect();
        assert_eq!(ids, vec![2, 3]);
        assert_eq!(stats.snapshot().error_count, 3);
    }

    #[test]
    fn avg_latency_none_when_no_latency_samples_exist() {
        let mut stats = DevModeStats::default();
        stats.record_voice_message(&VoiceJobMessage::Error("boom".to_string()));
        assert_eq!(stats.snapshot().avg_latency_ms, None);
    }

    #[test]
    fn empty_events_capture_drop_count_when_present() {
        let mut stats = DevModeStats::default();
        let metrics = CaptureMetrics {
            frames_dropped: 7,
            ..Default::default()
        };
        stats.record_voice_message(&VoiceJobMessage::Empty {
            source: VoiceCaptureSource::Python,
            metrics: Some(metrics),
        });

        let event = stats.recent_events().back();
        assert!(event.is_some());
        let event = match event {
            Some(event) => event,
            None => unreachable!("event asserted as present"),
        };
        assert_eq!(event.dropped_frames, 7);
        assert_eq!(event.transcript_words, 0);
        assert_eq!(event.latency_ms, None);
    }
}
