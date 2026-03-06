use std::sync::OnceLock;

const CLAUDE_HUD_DEBUG_ENV: &str = "VOICETERM_DEBUG_CLAUDE_HUD";

pub(crate) fn parse_debug_env_flag(raw: &str) -> bool {
    matches!(
        raw.trim().to_ascii_lowercase().as_str(),
        "1" | "true" | "yes" | "on" | "debug"
    )
}

pub(crate) fn claude_hud_debug_enabled() -> bool {
    static ENABLED: OnceLock<bool> = OnceLock::new();
    *ENABLED.get_or_init(|| {
        std::env::var(CLAUDE_HUD_DEBUG_ENV)
            .map(|raw| parse_debug_env_flag(&raw))
            // Keep debug traces on by default in debug/dev binaries so field
            // regressions are diagnosable without env-var misses.
            .unwrap_or(cfg!(debug_assertions))
    })
}

pub(crate) fn debug_bytes_preview(bytes: &[u8], max_chars: usize) -> String {
    let text = String::from_utf8_lossy(bytes);
    let mut out = String::new();
    for (count, ch) in text.chars().enumerate() {
        if count >= max_chars {
            out.push_str("...");
            break;
        }
        for escaped in ch.escape_default() {
            out.push(escaped);
        }
    }
    out
}
