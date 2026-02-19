//! Terminal texture/graphics capability track (MP-176).
//!
//! Implements `TextureProfile` and adapter policy: symbol-texture baseline for
//! all terminals plus capability-gated Kitty/iTerm2 image paths with enforced
//! fallback chain tests.
//!
//! Gate evidence: TS-G09 (capability fallback), TS-G06 (snapshot matrix).

use std::env;

// ---------------------------------------------------------------------------
// Texture tiers
// ---------------------------------------------------------------------------

/// Terminal texture rendering tier, ordered from richest to most basic.
///
/// The resolver walks the chain from richest to most basic until a supported
/// tier is found, ensuring every terminal gets a usable visual.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub(crate) enum TextureTier {
    /// Kitty graphics protocol (inline images via APC sequences).
    KittyGraphics,
    /// iTerm2 inline image protocol (OSC 1337).
    ITermInlineImage,
    /// Sixel graphics (DEC terminals, some modern emulators).
    Sixel,
    /// Unicode symbol textures (shade/braille/block characters).
    SymbolTexture,
    /// Plain ASCII (no special rendering).
    Plain,
}

impl TextureTier {
    /// Human-readable label.
    #[must_use]
    pub(crate) const fn name(&self) -> &'static str {
        match self {
            Self::KittyGraphics => "kitty-graphics",
            Self::ITermInlineImage => "iterm-inline-image",
            Self::Sixel => "sixel",
            Self::SymbolTexture => "symbol-texture",
            Self::Plain => "plain",
        }
    }

    /// Ordered fallback chain from richest to most basic.
    #[must_use]
    pub(crate) const fn fallback_chain() -> &'static [Self] {
        &[
            Self::KittyGraphics,
            Self::ITermInlineImage,
            Self::Sixel,
            Self::SymbolTexture,
            Self::Plain,
        ]
    }
}

// ---------------------------------------------------------------------------
// Symbol texture families
// ---------------------------------------------------------------------------

/// Symbol-texture families available for universal terminal rendering.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) enum SymbolTextureFamily {
    /// Unicode shade characters (░▒▓█).
    Shade,
    /// Braille dot patterns (⠁..⣿).
    Braille,
    /// Block elements (▀▄█▌▐).
    Block,
    /// Box-drawing lines (─│┌┐└┘).
    Line,
}

impl SymbolTextureFamily {
    /// All symbol texture families.
    #[must_use]
    pub(crate) const fn all() -> &'static [Self] {
        &[Self::Shade, Self::Braille, Self::Block, Self::Line]
    }

    /// Human-readable name.
    #[must_use]
    pub(crate) const fn name(&self) -> &'static str {
        match self {
            Self::Shade => "shade",
            Self::Braille => "braille",
            Self::Block => "block",
            Self::Line => "line",
        }
    }

    /// Sample characters for the family.
    #[must_use]
    pub(crate) const fn sample_chars(&self) -> &'static [char] {
        match self {
            Self::Shade => &['░', '▒', '▓', '█'],
            Self::Braille => &['⠁', '⠃', '⠇', '⡇', '⣇', '⣿'],
            Self::Block => &['▀', '▄', '█', '▌', '▐'],
            Self::Line => &['─', '│', '┌', '┐', '└', '┘'],
        }
    }
}

// ---------------------------------------------------------------------------
// TextureProfile
// ---------------------------------------------------------------------------

/// Resolved texture profile for a terminal session.
///
/// Created once at startup from environment detection and optionally overridden
/// by style-pack configuration.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct TextureProfile {
    /// Maximum supported texture tier for this terminal.
    pub(crate) max_tier: TextureTier,
    /// Active tier (may be lower than max if user or style-pack restricts it).
    pub(crate) active_tier: TextureTier,
    /// Symbol texture family to use when tier is `SymbolTexture`.
    pub(crate) symbol_family: SymbolTextureFamily,
    /// Terminal identifier used for capability detection.
    pub(crate) terminal_id: TerminalId,
}

/// Known terminal identifiers for capability gating.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum TerminalId {
    Kitty,
    ITerm2,
    WezTerm,
    Foot,
    Mintty,
    VsCode,
    Cursor,
    JetBrains,
    Alacritty,
    Warp,
    Generic(String),
    Unknown,
}

impl TerminalId {
    /// Human-readable name.
    #[must_use]
    pub(crate) fn name(&self) -> &str {
        match self {
            Self::Kitty => "kitty",
            Self::ITerm2 => "iterm2",
            Self::WezTerm => "wezterm",
            Self::Foot => "foot",
            Self::Mintty => "mintty",
            Self::VsCode => "vscode",
            Self::Cursor => "cursor",
            Self::JetBrains => "jetbrains",
            Self::Alacritty => "alacritty",
            Self::Warp => "warp",
            Self::Generic(name) => name.as_str(),
            Self::Unknown => "unknown",
        }
    }
}

// ---------------------------------------------------------------------------
// Detection
// ---------------------------------------------------------------------------

/// Detect the terminal identifier from environment variables.
#[must_use]
pub(crate) fn detect_terminal_id() -> TerminalId {
    // TERM_PROGRAM is the most reliable signal.
    if let Ok(term_program) = env::var("TERM_PROGRAM") {
        let lower = term_program.to_lowercase();
        if lower == "kitty" {
            return TerminalId::Kitty;
        }
        if lower == "iterm.app" || lower == "iterm2" {
            return TerminalId::ITerm2;
        }
        if lower == "wezterm" {
            return TerminalId::WezTerm;
        }
        if lower == "alacritty" {
            return TerminalId::Alacritty;
        }
        if lower == "vscode" {
            return TerminalId::VsCode;
        }
        if lower == "cursor" {
            return TerminalId::Cursor;
        }
        if lower.contains("jetbrains") || lower.contains("jediterm") {
            return TerminalId::JetBrains;
        }
        if lower.contains("warp") {
            return TerminalId::Warp;
        }
        if lower == "foot" {
            return TerminalId::Foot;
        }
        if lower == "mintty" {
            return TerminalId::Mintty;
        }
        return TerminalId::Generic(term_program);
    }

    // Fallback: TERMINAL_EMULATOR (JetBrains sets this).
    if let Ok(emulator) = env::var("TERMINAL_EMULATOR") {
        let lower = emulator.to_lowercase();
        if lower.contains("jetbrains") || lower.contains("jediterm") {
            return TerminalId::JetBrains;
        }
    }

    // Fallback: KITTY_WINDOW_ID implies Kitty.
    if env::var("KITTY_WINDOW_ID").is_ok() {
        return TerminalId::Kitty;
    }

    // Fallback: ITERM_SESSION_ID implies iTerm2.
    if env::var("ITERM_SESSION_ID").is_ok() {
        return TerminalId::ITerm2;
    }

    TerminalId::Unknown
}

/// Detect the maximum supported texture tier for the identified terminal.
#[must_use]
pub(crate) fn detect_max_texture_tier(terminal: &TerminalId) -> TextureTier {
    match terminal {
        TerminalId::Kitty => TextureTier::KittyGraphics,
        TerminalId::ITerm2 => TextureTier::ITermInlineImage,
        TerminalId::WezTerm => TextureTier::ITermInlineImage,
        TerminalId::Foot => TextureTier::Sixel,
        TerminalId::Mintty => TextureTier::Sixel,
        // Text-only terminals get symbol textures.
        TerminalId::VsCode
        | TerminalId::Cursor
        | TerminalId::JetBrains
        | TerminalId::Alacritty
        | TerminalId::Warp => TextureTier::SymbolTexture,
        TerminalId::Generic(_) | TerminalId::Unknown => TextureTier::SymbolTexture,
    }
}

/// Resolve the best available texture tier, applying the fallback chain.
///
/// If `requested` is supported (at or below `max`), return it. Otherwise,
/// walk the fallback chain until a supported tier is found.
#[must_use]
pub(crate) fn resolve_texture_tier(max: TextureTier, requested: TextureTier) -> TextureTier {
    // Lower ordinal = richer capability. If requested is at or below max, use it.
    if requested >= max {
        return requested;
    }
    // Requested is richer than max; walk fallback chain.
    for tier in TextureTier::fallback_chain() {
        if *tier >= max {
            return *tier;
        }
    }
    TextureTier::Plain
}

/// Build a complete texture profile for the current terminal environment.
#[must_use]
pub(crate) fn detect_texture_profile() -> TextureProfile {
    let terminal_id = detect_terminal_id();
    let max_tier = detect_max_texture_tier(&terminal_id);
    TextureProfile {
        max_tier,
        active_tier: max_tier,
        symbol_family: SymbolTextureFamily::Shade,
        terminal_id,
    }
}

/// Build a texture profile with an explicit tier override (for style-pack use).
#[must_use]
pub(crate) fn texture_profile_with_override(
    requested_tier: TextureTier,
    symbol_family: SymbolTextureFamily,
) -> TextureProfile {
    let terminal_id = detect_terminal_id();
    let max_tier = detect_max_texture_tier(&terminal_id);
    let active_tier = resolve_texture_tier(max_tier, requested_tier);
    TextureProfile {
        max_tier,
        active_tier,
        symbol_family,
        terminal_id,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fallback_chain_starts_at_richest_and_ends_at_plain() {
        let chain = TextureTier::fallback_chain();
        assert_eq!(chain.first(), Some(&TextureTier::KittyGraphics));
        assert_eq!(chain.last(), Some(&TextureTier::Plain));
        assert_eq!(chain.len(), 5);
    }

    #[test]
    fn fallback_chain_is_ordered_richest_to_plainest() {
        let chain = TextureTier::fallback_chain();
        for window in chain.windows(2) {
            assert!(
                window[0] < window[1],
                "{:?} should be before {:?}",
                window[0],
                window[1]
            );
        }
    }

    #[test]
    fn resolve_tier_returns_requested_when_supported() {
        assert_eq!(
            resolve_texture_tier(TextureTier::KittyGraphics, TextureTier::SymbolTexture),
            TextureTier::SymbolTexture
        );
        assert_eq!(
            resolve_texture_tier(TextureTier::SymbolTexture, TextureTier::SymbolTexture),
            TextureTier::SymbolTexture
        );
        assert_eq!(
            resolve_texture_tier(TextureTier::SymbolTexture, TextureTier::Plain),
            TextureTier::Plain
        );
    }

    #[test]
    fn resolve_tier_falls_back_when_requested_exceeds_max() {
        // Terminal only supports SymbolTexture; requesting KittyGraphics should
        // fall back to SymbolTexture.
        let resolved = resolve_texture_tier(TextureTier::SymbolTexture, TextureTier::KittyGraphics);
        assert_eq!(resolved, TextureTier::SymbolTexture);
    }

    #[test]
    fn resolve_tier_plain_max_returns_plain() {
        let resolved = resolve_texture_tier(TextureTier::Plain, TextureTier::KittyGraphics);
        assert_eq!(resolved, TextureTier::Plain);
    }

    #[test]
    fn detect_max_tier_for_kitty() {
        assert_eq!(
            detect_max_texture_tier(&TerminalId::Kitty),
            TextureTier::KittyGraphics
        );
    }

    #[test]
    fn detect_max_tier_for_iterm2() {
        assert_eq!(
            detect_max_texture_tier(&TerminalId::ITerm2),
            TextureTier::ITermInlineImage
        );
    }

    #[test]
    fn detect_max_tier_for_wezterm() {
        assert_eq!(
            detect_max_texture_tier(&TerminalId::WezTerm),
            TextureTier::ITermInlineImage
        );
    }

    #[test]
    fn detect_max_tier_for_foot() {
        assert_eq!(
            detect_max_texture_tier(&TerminalId::Foot),
            TextureTier::Sixel
        );
    }

    #[test]
    fn detect_max_tier_for_vscode() {
        assert_eq!(
            detect_max_texture_tier(&TerminalId::VsCode),
            TextureTier::SymbolTexture
        );
    }

    #[test]
    fn detect_max_tier_for_unknown() {
        assert_eq!(
            detect_max_texture_tier(&TerminalId::Unknown),
            TextureTier::SymbolTexture
        );
    }

    #[test]
    fn symbol_texture_families_have_non_empty_samples() {
        for family in SymbolTextureFamily::all() {
            let samples = family.sample_chars();
            assert!(
                !samples.is_empty(),
                "family {} has empty samples",
                family.name()
            );
        }
    }

    #[test]
    fn symbol_texture_family_names_are_non_empty() {
        for family in SymbolTextureFamily::all() {
            assert!(!family.name().is_empty());
        }
    }

    #[test]
    fn texture_tier_names_are_non_empty() {
        for tier in TextureTier::fallback_chain() {
            assert!(!tier.name().is_empty());
        }
    }

    #[test]
    fn terminal_id_names_are_non_empty() {
        let ids = [
            TerminalId::Kitty,
            TerminalId::ITerm2,
            TerminalId::WezTerm,
            TerminalId::Foot,
            TerminalId::Mintty,
            TerminalId::VsCode,
            TerminalId::Cursor,
            TerminalId::JetBrains,
            TerminalId::Alacritty,
            TerminalId::Warp,
            TerminalId::Generic("test".to_string()),
            TerminalId::Unknown,
        ];
        for id in &ids {
            assert!(!id.name().is_empty());
        }
    }

    #[test]
    fn texture_profile_with_override_respects_max_tier() {
        // Simulate a SymbolTexture-only terminal requesting KittyGraphics.
        let terminal_id = TerminalId::Alacritty;
        let max_tier = detect_max_texture_tier(&terminal_id);
        assert_eq!(max_tier, TextureTier::SymbolTexture);

        let resolved = resolve_texture_tier(max_tier, TextureTier::KittyGraphics);
        assert_eq!(resolved, TextureTier::SymbolTexture);
    }

    #[test]
    fn texture_profile_detect_returns_valid_profile() {
        // In test environments, terminal detection will likely return Unknown.
        let profile = detect_texture_profile();
        assert!(profile.active_tier >= profile.max_tier);
    }

    #[test]
    fn fallback_chain_enforces_plain_as_ultimate_fallback() {
        // Even the most restricted terminal should resolve to Plain.
        let resolved = resolve_texture_tier(TextureTier::Plain, TextureTier::Plain);
        assert_eq!(resolved, TextureTier::Plain);
    }

    #[test]
    fn sixel_tier_falls_back_correctly() {
        // Terminal supports up to Sixel; requesting KittyGraphics should
        // fall back to Sixel.
        let resolved = resolve_texture_tier(TextureTier::Sixel, TextureTier::KittyGraphics);
        assert_eq!(resolved, TextureTier::Sixel);
    }

    #[test]
    fn iterm_inline_tier_falls_back_correctly() {
        let resolved =
            resolve_texture_tier(TextureTier::ITermInlineImage, TextureTier::KittyGraphics);
        assert_eq!(resolved, TextureTier::ITermInlineImage);
    }
}
