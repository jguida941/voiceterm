//! Hotword phrase matching, normalization, and send-intent classification.
//!
//! All matching operates on normalized lowercase text produced by the STT
//! engine. Token canonicalization handles common misrecognitions so the
//! wake-word detector stays resilient across Whisper model variants.

use super::WakeWordEvent;
use voiceterm::{log_debug, log_debug_content};

pub(super) const HOTWORD_PHRASES: &[&str] = &[
    "codex",
    "hey codex",
    "ok codex",
    "okay codex",
    "claude",
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

#[must_use = "hotword matching expects normalized lowercase transcript text"]
pub(super) fn normalize_for_hotword_match(raw: &str) -> String {
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
pub(super) fn transcript_matches_hotword(raw: &str) -> bool {
    detect_wake_event(raw).is_some()
}

#[cfg(test)]
#[must_use = "wake event classification should map transcript intent into runtime action"]
pub(super) fn detect_wake_event(raw: &str) -> Option<WakeWordEvent> {
    let normalized = normalize_for_hotword_match(raw);
    detect_wake_event_from_normalized(&normalized)
}

pub(super) fn detect_wake_event_from_normalized(normalized: &str) -> Option<WakeWordEvent> {
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

pub(super) fn log_wake_transcript_decision(
    raw: &str,
    normalized: &str,
    event: Option<WakeWordEvent>,
) {
    let normalized_tokens: Vec<&str> = normalized.split_whitespace().collect();
    if normalized_tokens.is_empty() {
        return;
    }
    // Keep wake transcript tracing focused on likely intent phrases to avoid
    // flooding logs with unrelated ambient transcripts.
    let interesting_tokens = normalized_tokens.iter().any(|token| {
        matches!(
            *token,
            "hey"
                | "hate"
                | "pay"
                | "codex"
                | "codes"
                | "coach"
                | "coax"
                | "codec"
                | "codecs"
                | "kodak"
                | "kodex"
                | "claude"
                | "cloud"
                | "clog"
                | "voiceterm"
                | "voice"
                | "term"
                | "send"
                | "sent"
                | "sen"
                | "sand"
                | "sending"
                | "submit"
        )
    });
    if !interesting_tokens {
        return;
    }

    let event_label = match event {
        Some(WakeWordEvent::Detected) => "detected",
        Some(WakeWordEvent::SendStagedInput) => "send-intent",
        None => "none",
    };
    let canonical = canonicalize_hotword_tokens(&normalized_tokens);
    log_debug(&format!(
        "wake-word transcript decision: event={event_label}, tokens={}",
        normalized_tokens.len()
    ));
    log_debug_content(&format!(
        "wake-word transcript raw='{raw}' normalized='{normalized}' canonical='{}'",
        canonical.join(" ")
    ));
}

#[cfg(test)]
#[must_use = "hotword check determines whether wake capture should trigger"]
pub(super) fn contains_hotword_phrase(normalized: &str) -> bool {
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
pub(super) fn canonicalize_hotword_tokens(tokens: &[&str]) -> Vec<String> {
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
        let prev = idx
            .checked_sub(1)
            .and_then(|prev_idx| tokens.get(prev_idx))
            .copied()
            .unwrap_or_default();
        let next = tokens.get(idx + 1).copied();
        let token = match tokens[idx] {
            "code"
                if is_wake_prefix_token(prev)
                    && next.map(wake_token_is_send_intent_marker).unwrap_or(true) =>
            {
                "codex"
            }
            "coach" | "coaches" | "coax" if is_wake_prefix_token(prev) => "codex",
            "codec" | "codecs" | "codes" | "kodak" | "kodaks" | "kodex" => "codex",
            "cloud" | "clod" | "clawd" | "clawed" | "claud" | "clog" => "claude",
            "hate" if idx == 0 => "hey",
            "pay" if idx == 0 => "hey",
            other => other,
        };
        canonical.push(token.to_string());
        idx += 1;
    }
    canonical
}

#[inline]
fn is_wake_prefix_token(token: &str) -> bool {
    matches!(token, "hey" | "ok" | "okay")
}

#[inline]
fn wake_token_is_send_intent_marker(token: &str) -> bool {
    matches!(
        token,
        "send" | "sent" | "sen" | "sand" | "son" | "sending" | "submit"
    )
}

#[cfg(test)]
#[must_use = "phrase match result is required for wake-word gating"]
fn contains_hotword_window(haystack_tokens: &[&str], phrase: &str) -> bool {
    let phrase_tokens: Vec<&str> = phrase.split_whitespace().collect();
    find_hotword_window_start(haystack_tokens, &phrase_tokens).is_some()
}

#[must_use = "hotword window search determines phrase location and suffix intent parsing"]
pub(super) fn find_hotword_window_start(
    haystack_tokens: &[&str],
    phrase_tokens: &[&str],
) -> Option<usize> {
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
            | ["sent"]
            | ["sen"]
            | ["sand"]
            | ["son"]
            | ["sending"]
            | ["send", "it"]
            | ["sent", "it"]
            | ["sen", "it"]
            | ["sand", "it"]
            | ["son", "it"]
            | ["send", "this"]
            | ["sent", "this"]
            | ["sen", "this"]
            | ["sand", "this"]
            | ["send", "message"]
            | ["sent", "message"]
            | ["sen", "message"]
            | ["sand", "message"]
            | ["submit"]
            | ["send", "now"]
            | ["sent", "now"]
            | ["sen", "now"]
            | ["sand", "now"]
            | ["son", "now"]
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
