//! Border glyph sets so HUD framing can vary by theme without layout changes.

/// Border character set for drawing boxes.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BorderSet {
    pub top_left: char,
    pub top_right: char,
    pub bottom_left: char,
    pub bottom_right: char,
    pub horizontal: char,
    pub vertical: char,
    pub t_left: char,   // ├
    pub t_right: char,  // ┤
    pub t_top: char,    // ┬
    pub t_bottom: char, // ┴
    pub cross: char,    // ┼
}

/// Standard single-line borders
pub const BORDER_SINGLE: BorderSet = BorderSet {
    top_left: '┌',
    top_right: '┐',
    bottom_left: '└',
    bottom_right: '┘',
    horizontal: '─',
    vertical: '│',
    t_left: '├',
    t_right: '┤',
    t_top: '┬',
    t_bottom: '┴',
    cross: '┼',
};

/// Double-line borders (elegant)
pub const BORDER_DOUBLE: BorderSet = BorderSet {
    top_left: '╔',
    top_right: '╗',
    bottom_left: '╚',
    bottom_right: '╝',
    horizontal: '═',
    vertical: '║',
    t_left: '╠',
    t_right: '╣',
    t_top: '╦',
    t_bottom: '╩',
    cross: '╬',
};

/// Heavy/bold borders
pub const BORDER_HEAVY: BorderSet = BorderSet {
    top_left: '┏',
    top_right: '┓',
    bottom_left: '┗',
    bottom_right: '┛',
    horizontal: '━',
    vertical: '┃',
    t_left: '┣',
    t_right: '┫',
    t_top: '┳',
    t_bottom: '┻',
    cross: '╋',
};

/// Rounded corners (modern)
pub const BORDER_ROUNDED: BorderSet = BorderSet {
    top_left: '╭',
    top_right: '╮',
    bottom_left: '╰',
    bottom_right: '╯',
    horizontal: '─',
    vertical: '│',
    t_left: '├',
    t_right: '┤',
    t_top: '┬',
    t_bottom: '┴',
    cross: '┼',
};

/// Minimal dotted borders (reserved for future themes)
#[allow(
    dead_code,
    reason = "Reserved border presets for staged Theme Studio surface expansion."
)]
pub const BORDER_DOTTED: BorderSet = BorderSet {
    top_left: '·',
    top_right: '·',
    bottom_left: '·',
    bottom_right: '·',
    horizontal: '·',
    vertical: '·',
    t_left: '·',
    t_right: '·',
    t_top: '·',
    t_bottom: '·',
    cross: '·',
};

/// No borders (spaces) (reserved for future themes)
#[allow(
    dead_code,
    reason = "Reserved border presets for staged Theme Studio surface expansion."
)]
pub const BORDER_NONE: BorderSet = BorderSet {
    top_left: ' ',
    top_right: ' ',
    bottom_left: ' ',
    bottom_right: ' ',
    horizontal: ' ',
    vertical: ' ',
    t_left: ' ',
    t_right: ' ',
    t_top: ' ',
    t_bottom: ' ',
    cross: ' ',
};
