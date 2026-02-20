//! Theme color tokens so rendering code references semantic colors, not raw escapes.

/// Glyph family selection for icon/progress rendering.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum GlyphSet {
    /// Unicode-rich glyph rendering.
    #[default]
    Unicode,
    /// ASCII-safe glyph rendering.
    Ascii,
}

/// Processing spinner animation family.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum SpinnerStyle {
    /// Theme-default processing behavior.
    #[default]
    Theme,
    /// Braille spinner frames.
    Braille,
    /// Dots spinner frames.
    Dots,
    /// Line spinner frames.
    Line,
    /// Block spinner frames.
    Block,
}

/// Voice-scene animation profile.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum VoiceSceneStyle {
    /// Theme-default scene behavior.
    #[default]
    Theme,
    /// Emphasize animated scene behavior.
    Pulse,
    /// Reduce dynamic scene animation.
    Static,
    /// Minimal scene ornamentation.
    Minimal,
}

/// Progress bar glyph family.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ProgressBarFamily {
    /// Theme-default progress bar behavior.
    #[default]
    Theme,
    /// Classic bar-family glyphs.
    Bar,
    /// Compact glyph-heavy bar family.
    Compact,
    /// Block-oriented bar family.
    Blocks,
    /// Braille-style bar family.
    Braille,
}

/// ANSI color codes for a theme.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ThemeColors {
    /// Color for recording/active states
    pub recording: &'static str,
    /// Color for processing/working states
    pub processing: &'static str,
    /// Color for success states
    pub success: &'static str,
    /// Color for warning states
    pub warning: &'static str,
    /// Color for error states
    pub error: &'static str,
    /// Color for info states
    pub info: &'static str,
    /// Reset code
    pub reset: &'static str,
    /// Dim/muted text for secondary info
    pub dim: &'static str,
    /// Primary background color (for main status area)
    pub bg_primary: &'static str,
    /// Secondary background color (for shortcuts row)
    pub bg_secondary: &'static str,
    /// Border/frame color
    pub border: &'static str,
    /// Border character set
    pub borders: super::BorderSet,
    /// Mode indicator symbol
    pub indicator_rec: &'static str,
    pub indicator_auto: &'static str,
    pub indicator_manual: &'static str,
    pub indicator_idle: &'static str,
    pub indicator_processing: &'static str,
    pub indicator_responding: &'static str,
    /// Icon/progress glyph profile.
    pub glyph_set: GlyphSet,
    /// Processing spinner animation profile.
    pub spinner_style: SpinnerStyle,
    /// Voice-scene animation profile.
    pub voice_scene_style: VoiceSceneStyle,
    /// Progress bar glyph profile.
    pub progress_bar_family: ProgressBarFamily,
}
