//! Provider adapter contracts used by MP-346 extraction slices.
//!
//! Phase 3a wires prompt detector strategy through provider adapters.

use crate::prompt::PromptOcclusionDetector;
use crate::runtime_compat::BackendFamily;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ProviderId {
    Claude,
    Codex,
    Gemini,
    Other,
}

pub(crate) trait PromptDetectionStrategy {
    fn build_detector(&self, backend_label: &str) -> PromptOcclusionDetector;
}

pub(crate) trait ProviderAdapter {
    fn provider(&self) -> ProviderId;
    fn supports_prompt_occlusion(&self) -> bool;
    fn prompt_detection_strategy(&self) -> Option<&'static dyn PromptDetectionStrategy>;
}

struct ClaudePromptDetectionStrategy;
struct ClaudeProviderAdapter;
struct CodexProviderAdapter;
struct GeminiProviderAdapter;
struct OtherProviderAdapter;

static CLAUDE_PROMPT_DETECTION_STRATEGY: ClaudePromptDetectionStrategy =
    ClaudePromptDetectionStrategy;
static CLAUDE_PROVIDER_ADAPTER: ClaudeProviderAdapter = ClaudeProviderAdapter;
static CODEX_PROVIDER_ADAPTER: CodexProviderAdapter = CodexProviderAdapter;
static GEMINI_PROVIDER_ADAPTER: GeminiProviderAdapter = GeminiProviderAdapter;
static OTHER_PROVIDER_ADAPTER: OtherProviderAdapter = OtherProviderAdapter;

impl PromptDetectionStrategy for ClaudePromptDetectionStrategy {
    fn build_detector(&self, backend_label: &str) -> PromptOcclusionDetector {
        // Strategy-owned detector policy: Claude adapter controls detector wiring.
        PromptOcclusionDetector::new_for_backend(backend_label)
    }
}

impl ProviderAdapter for ClaudeProviderAdapter {
    fn provider(&self) -> ProviderId {
        ProviderId::Claude
    }

    fn supports_prompt_occlusion(&self) -> bool {
        true
    }

    fn prompt_detection_strategy(&self) -> Option<&'static dyn PromptDetectionStrategy> {
        Some(&CLAUDE_PROMPT_DETECTION_STRATEGY)
    }
}

impl ProviderAdapter for CodexProviderAdapter {
    fn provider(&self) -> ProviderId {
        ProviderId::Codex
    }

    fn supports_prompt_occlusion(&self) -> bool {
        false
    }

    fn prompt_detection_strategy(&self) -> Option<&'static dyn PromptDetectionStrategy> {
        None
    }
}

impl ProviderAdapter for GeminiProviderAdapter {
    fn provider(&self) -> ProviderId {
        ProviderId::Gemini
    }

    fn supports_prompt_occlusion(&self) -> bool {
        false
    }

    fn prompt_detection_strategy(&self) -> Option<&'static dyn PromptDetectionStrategy> {
        None
    }
}

impl ProviderAdapter for OtherProviderAdapter {
    fn provider(&self) -> ProviderId {
        ProviderId::Other
    }

    fn supports_prompt_occlusion(&self) -> bool {
        false
    }

    fn prompt_detection_strategy(&self) -> Option<&'static dyn PromptDetectionStrategy> {
        None
    }
}

pub(crate) fn provider_id_from_backend_label(backend_label: &str) -> ProviderId {
    match BackendFamily::from_label(backend_label) {
        BackendFamily::Claude => ProviderId::Claude,
        BackendFamily::Codex => ProviderId::Codex,
        BackendFamily::Gemini => ProviderId::Gemini,
        BackendFamily::Other => ProviderId::Other,
    }
}

pub(crate) fn resolve_provider_adapter(backend_label: &str) -> &'static dyn ProviderAdapter {
    match provider_id_from_backend_label(backend_label) {
        ProviderId::Claude => &CLAUDE_PROVIDER_ADAPTER,
        ProviderId::Codex => &CODEX_PROVIDER_ADAPTER,
        ProviderId::Gemini => &GEMINI_PROVIDER_ADAPTER,
        ProviderId::Other => &OTHER_PROVIDER_ADAPTER,
    }
}

pub(crate) fn build_prompt_occlusion_detector(backend_label: &str) -> PromptOcclusionDetector {
    let adapter = resolve_provider_adapter(backend_label);
    debug_assert_eq!(
        adapter.provider(),
        provider_id_from_backend_label(backend_label)
    );
    if !adapter.supports_prompt_occlusion() {
        return PromptOcclusionDetector::new_for_backend(backend_label);
    }

    if let Some(strategy) = adapter.prompt_detection_strategy() {
        return strategy.build_detector(backend_label);
    }

    PromptOcclusionDetector::new_for_backend(backend_label)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn provider_contract_enum_variants_are_exhaustive() {
        let providers = [
            ProviderId::Codex,
            ProviderId::Claude,
            ProviderId::Gemini,
            ProviderId::Other,
        ];
        assert_eq!(providers.len(), 4);
    }

    #[test]
    fn resolve_provider_adapter_maps_backend_label() {
        assert_eq!(
            resolve_provider_adapter("claude").provider(),
            ProviderId::Claude
        );
        assert_eq!(
            resolve_provider_adapter("codex").provider(),
            ProviderId::Codex
        );
        assert_eq!(
            resolve_provider_adapter("gemini").provider(),
            ProviderId::Gemini
        );
        assert_eq!(
            resolve_provider_adapter("custom").provider(),
            ProviderId::Other
        );
    }

    #[test]
    fn provider_id_mapping_stays_aligned_with_backend_family_labels() {
        assert_eq!(
            provider_id_from_backend_label("Claude Code"),
            ProviderId::Claude
        );
        assert_eq!(
            provider_id_from_backend_label("codex-cli"),
            ProviderId::Codex
        );
        assert_eq!(provider_id_from_backend_label("Gemini"), ProviderId::Gemini);
        assert_eq!(
            provider_id_from_backend_label("custom-provider"),
            ProviderId::Other
        );
    }

    #[test]
    fn provider_ids_match_backend_contract() {
        assert_eq!(provider_id_from_backend_label("claude"), ProviderId::Claude);
        assert_eq!(provider_id_from_backend_label("codex"), ProviderId::Codex);
    }

    #[test]
    fn claude_adapter_exposes_prompt_detection_strategy() {
        let adapter = resolve_provider_adapter("claude");
        assert_eq!(adapter.provider(), ProviderId::Claude);
        assert!(adapter.supports_prompt_occlusion());
        assert!(adapter.prompt_detection_strategy().is_some());
    }

    #[test]
    fn prompt_detector_defaults_to_provider_strategy() {
        let mut detector = build_prompt_occlusion_detector("claude");
        assert!(detector.is_enabled());
        let detected = detector.feed_output(b"Do you want to run this command? (y/n)\n");
        assert!(detected);
        assert!(detector.should_suppress_hud());
    }

    #[test]
    fn prompt_detector_fallback_remains_for_non_claude_providers() {
        let detector = build_prompt_occlusion_detector("codex");
        assert!(!detector.is_enabled());
    }

    #[test]
    fn claude_strategy_forwards_backend_label_policy() {
        let strategy = ClaudePromptDetectionStrategy;
        let detector = strategy.build_detector("codex");
        assert!(!detector.is_enabled());
        let detector = strategy.build_detector("claude");
        assert!(detector.is_enabled());
    }
}
