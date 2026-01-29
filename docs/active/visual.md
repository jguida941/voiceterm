# Visual Design Audit & Improvement Plan

This document audits the current visual/UI implementation of Codex Voice and proposes improvements to make it look more professional like Claude CLI or Codex CLI.

## Contents

- [Current State Summary](#current-state-summary)
- [File Locations](#file-locations)
- [Current Color Scheme](#current-color-scheme)
- [Current UI Components](#current-ui-components)
- [Issues and Gaps](#issues-and-gaps)
- [Research: Professional CLI Design](#research-professional-cli-design)
- [Research: Popular Color Themes](#research-popular-color-themes)
- [Research: Progress Indicators](#research-progress-indicators)
- [Improvement Ideas](#improvement-ideas)
- [Additional Findings from Deep Audit](#additional-findings-from-deep-audit)
  - [All Status Messages (Catalog for Styling)](#all-status-messages-catalog-for-styling)
  - [Missing: Help System](#missing-help-system)
  - [Missing: Visual Configuration CLI Flags](#missing-visual-configuration-cli-flags)
  - [Missing: Terminal Capability Fallback](#missing-terminal-capability-fallback)
  - [Missing: Error Visual Differentiation](#missing-error-visual-differentiation)
  - [Missing: Mic Meter Visualization](#missing-mic-meter-visualization)
  - [Missing: Real-time Audio Level Display](#missing-real-time-audio-level-display)
  - [Missing: Transcript Preview](#missing-transcript-preview)
  - [Missing: Mode Indicators in Prompt](#missing-mode-indicators-in-prompt)
  - [Missing: Notification Sounds](#missing-notification-sounds-optional)
  - [Additional Widget Ideas](#additional-widget-ideas)
- [Implementation Priorities](#implementation-priorities)
  - [Tier 0 - Quick Wins](#tier-0---quick-wins-high-impact-low-effort)
  - [Tier 1 - Core Visual System](#tier-1---core-visual-system)
  - [Tier 2 - Enhanced Status Line](#tier-2---enhanced-status-line)
  - [Tier 3 - Help and Discoverability](#tier-3---help-and-discoverability)
  - [Tier 4 - Advanced Features](#tier-4---advanced-features)
  - [Tier 5 - Polish](#tier-5---polish)
- [Resources](#resources)
- [Next Steps](#next-steps)

---

## Current State Summary

Codex Voice has **two UI modes**:

| Mode | Framework | Visual Style |
|------|-----------|--------------|
| **Overlay** (`codex-voice`) | Raw ANSI escape codes | Minimal status line at bottom, NO colors |
| **Full TUI** (`rust_tui`) | Ratatui + Crossterm | 3-panel layout, red theme, rounded borders |

**Key Finding:** The overlay mode (primary user-facing) has **zero color styling**. All status messages are plain terminal default text.

---

## File Locations

| File | Purpose | Lines |
|------|---------|-------|
| `rust_tui/src/ui.rs` | Full TUI rendering, colors, layout | 324 |
| `rust_tui/src/app/state.rs` | App state, spinner logic, status text | 777 |
| `rust_tui/src/bin/codex_overlay/writer.rs` | Overlay status line rendering | 284 |
| `rust_tui/src/bin/codex_overlay/main.rs` | Overlay main loop, status messages | 570 |
| `rust_tui/src/codex/mod.rs` | Spinner frame constants | 27 |
| `start.sh` | Startup banner, color definitions | 329 |

---

## Current Color Scheme

### Full TUI (ui.rs lines 208-214)

```rust
let border_color = Color::Rgb(255, 90, 90);      // Vibrant red
let title_color = Color::Rgb(255, 110, 110);     // Bright red
let dim_border = Color::Rgb(130, 70, 70);        // Dim red
let output_text_color = Color::Rgb(210, 205, 200); // Soft white
let input_text_color = Color::Rgb(255, 220, 100);  // Warm yellow
let status_text_color = Color::Rgb(160, 150, 150); // Muted gray
```

### Startup Banner (start.sh lines 13-22)

```bash
CORAL="\033[38;2;255;90;90m"        # RGB(255, 90, 90)
CORAL_BRIGHT="\033[38;2;255;110;110m"
GREEN="\033[0;32m"
GOLD="\033[38;5;214m"
YELLOW="\033[1;33m"
```

### Overlay Mode

**NO COLORS USED** - Status line is plain text with no ANSI color codes.

---

## Current UI Components

### 1. Startup Banner (start.sh)

Large ASCII art banner:
```
   ██████╗ ██████╗ ██████╗ ███████╗██╗  ██╗
  ██╔════╝██╔═══██╗██╔══██╗██╔════╝╚██╗██╔╝
  ██║     ██║   ██║██║  ██║█████╗   ╚███╔╝
  ╚██████╗╚██████╔╝██████╔╝███████╗██╔╝ ██╗
          ██╗   ██╗ ██████╗ ██╗ ██████╗███████╗
          ██║   ██║██╔═══██╗██║██╔════╝██╔════╝
           ╚████╔╝ ╚██████╔╝██║╚██████╗███████╗
```

### 2. Full TUI Layout (ui.rs)

```
┌─────────────────────────────────────┐
│  Codex Output (scrollable)          │
├─────────────────────────────────────┤
│  Prompt (3 lines, cursor visible)   │
├─────────────────────────────────────┤
│  Status (2 lines, spinner)          │
└─────────────────────────────────────┘
```

Features:
- `BorderType::Rounded` on all panels
- Bold titles with red accent
- Keyboard shortcut hints in prompt footer
- Basic spinner: `-`, `\`, `|`, `/` (150ms interval)

### 3. Overlay Status Line (writer.rs)

Position: Last row of terminal
Rendering: Raw ANSI escape sequences
```
\x1b7              # Save cursor
\x1b[{rows};1H     # Move to bottom
\x1b[2K            # Clear line
{status_text}      # Plain text, NO COLOR
\x1b8              # Restore cursor
```

Status messages:
- "Auto-voice enabled"
- "Listening Manual Mode (Rust pipeline)"
- "Processing..."
- "Transcript ready (Rust pipeline)"
- "Mic sensitivity: -35 dB"

---

## Issues and Gaps

### Critical Issues

| Issue | Impact | Location |
|-------|--------|----------|
| **Overlay has no colors** | Looks unprofessional, hard to scan | writer.rs |
| **No theme system** | Can't customize, hardcoded values | ui.rs |
| **Basic spinner** | Dated look compared to modern CLIs | codex/mod.rs |
| **No visual state indicators** | Can't quickly see mode at a glance | main.rs |

### Missing Features

- [ ] No colored status indicators (recording = red, ready = green)
- [ ] No progress bar for long operations
- [ ] No visual distinction between modes (auto vs manual)
- [ ] No syntax highlighting in output
- [ ] No dark/light theme toggle
- [ ] No unicode icons/emoji support
- [ ] No responsive layout for narrow terminals
- [ ] No visual feedback for errors vs success

---

## Research: Professional CLI Design

### Claude CLI Approach

From [Claude Code Internals](https://kotrotsos.medium.com/claude-code-internals-part-11-terminal-ui-542fe17db016):

- Built with **React + Ink** (renders React to terminal)
- Supports **6 theme options**: dark, light, color-vision friendly variants, ANSI-only fallback
- Uses `COLORTERM=truecolor` for 24-bit RGB support
- Declarative component-based architecture
- Automatic light/dark mode detection

### Design Values (from Claude VS Code theme)

- **Warmth**: Rust-orange accents create welcoming environment
- **Professionalism**: Clean design for corporate use
- **Approachability**: Soft edges reduce visual fatigue
- **Intellectual Depth**: Sophisticated academic palette

### Ratatui Best Practices

From [Ratatui documentation](https://ratatui.rs/):

- Use **constraint-based layouts** for responsive design
- Built-in widgets: Block, Paragraph, List, Table, Gauge, Chart, Tabs, Sparkline
- Support for **component-based architecture**
- Templates available: `cargo generate ratatui/templates`
- Extensions: `ratatui-image`, `tui-react`, syntax highlighting via tree-sitter

---

## Research: Popular Color Themes

### Theme Options to Consider

| Theme | Style | Good For |
|-------|-------|----------|
| [Dracula](https://draculatheme.com) | High contrast dark, vibrant | Visibility, 400+ app support |
| [Catppuccin](https://github.com/catppuccin) | Pastel dark, soothing | Eye comfort, consistency |
| [Nord](https://www.nordtheme.com) | Arctic, blue-gray | Minimalist, professional |
| [Gruvbox](https://github.com/morhetz/gruvbox) | Retro warm | Nostalgic, readable |
| [Solarized](https://ethanschoonover.com/solarized/) | Scientific precision | Accessibility |

### Catppuccin Mocha Palette (Recommended)

```
Rosewater  #f5e0dc    Flamingo   #f2cdcd
Pink       #f5c2e7    Mauve      #cba6f7
Red        #f38ba8    Maroon     #eba0ac
Peach      #fab387    Yellow     #f9e2af
Green      #a6e3a1    Teal       #94e2d5
Sky        #89dceb    Sapphire   #74c7ec
Blue       #89b4fa    Lavender   #b4befe
Text       #cdd6f4    Base       #1e1e2e
```

---

## Research: Progress Indicators

### Best Practices

From [Evil Martians CLI UX](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays):

| Duration | Indicator Type |
|----------|----------------|
| < 1 second | None needed |
| 1-3 seconds | Spinner |
| 3-10 seconds | Progress bar |
| 10+ seconds | Progress + time estimate |

### Spinner Recommendations

- **Braille characters** for modern look: `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`
- **Dots** for minimal: `⣾⣽⣻⢿⡿⣟⣯⣷`
- Clear spinner when action completes
- Update on meaningful events, not just time

### Visual Feedback Patterns

- Green checkmark `✓` for success
- Red `✗` for errors
- Yellow `⚠` for warnings
- Blue `ℹ` for info

---

## Improvement Ideas

### Priority 1: Add Colors to Overlay Status Line

**Current (writer.rs):**
```rust
sequence.extend_from_slice(trimmed.as_bytes());
```

**Proposed:**
```rust
// Add ANSI color codes based on status type
let colored = match status_type {
    StatusType::Recording => format!("\x1b[91m● REC\x1b[0m {}", text),  // Red
    StatusType::Ready => format!("\x1b[92m● Ready\x1b[0m {}", text),    // Green
    StatusType::Processing => format!("\x1b[93m◐ {}\x1b[0m", text),     // Yellow
    StatusType::Error => format!("\x1b[91m✗ {}\x1b[0m", text),          // Red
    StatusType::Info => format!("\x1b[94mℹ {}\x1b[0m", text),           // Blue
};
```

### Priority 2: Modern Spinner

**Current (codex/mod.rs):**
```rust
pub const CODEX_SPINNER_FRAMES: &[char] = &['-', '\\', '|', '/'];
```

**Proposed:**
```rust
// Braille spinner (smooth, modern)
pub const SPINNER_BRAILLE: &[&str] = &["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

// Dots spinner (minimal)
pub const SPINNER_DOTS: &[&str] = &["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"];

// Bouncing bar
pub const SPINNER_BOUNCE: &[&str] = &["[    ]", "[=   ]", "[==  ]", "[=== ]", "[ ===]", "[  ==]", "[   =]", "[    ]"];
```

### Priority 3: Theme System

Create `rust_tui/src/theme.rs`:
```rust
pub struct Theme {
    pub name: &'static str,
    pub border: Color,
    pub title: Color,
    pub text: Color,
    pub accent: Color,
    pub success: Color,
    pub error: Color,
    pub warning: Color,
    pub muted: Color,
}

pub const THEME_CORAL: Theme = Theme {
    name: "coral",
    border: Color::Rgb(255, 90, 90),
    title: Color::Rgb(255, 110, 110),
    // ...
};

pub const THEME_CATPPUCCIN: Theme = Theme {
    name: "catppuccin",
    border: Color::Rgb(203, 166, 247),  // Mauve
    title: Color::Rgb(245, 194, 231),   // Pink
    text: Color::Rgb(205, 214, 244),    // Text
    accent: Color::Rgb(137, 180, 250),  // Blue
    success: Color::Rgb(166, 227, 161), // Green
    error: Color::Rgb(243, 139, 168),   // Red
    warning: Color::Rgb(249, 226, 175), // Yellow
    muted: Color::Rgb(108, 112, 134),   // Overlay0
};
```

### Priority 4: Status Line Layout

**Current:**
```
Auto-voice enabled
```

**Proposed:**
```
● AUTO │ ◉ Rust │ -40dB │ Ready                    Ctrl+R rec  Ctrl+V toggle
```

Components:
- Mode indicator (AUTO/MANUAL) with colored dot
- Pipeline indicator (Rust/Python)
- Sensitivity level
- Current status
- Right-aligned shortcuts

### Priority 5: Visual State Indicators

Add unicode indicators to status:

| State | Indicator | Color |
|-------|-----------|-------|
| Recording | `● REC` | Red |
| Processing | `◐` (animated) | Yellow |
| Ready | `○` | Green |
| Error | `✗` | Red |
| Auto-voice on | `◉` | Blue |
| Auto-voice off | `○` | Gray |

### Priority 6: Output Syntax Highlighting

For code blocks in Codex output:
- Use `syntect` or `tree-sitter` for highlighting
- Detect language from markdown fences
- Fall back to plain text

### Priority 7: Progress Bar for Long Operations

```rust
use indicatif::{ProgressBar, ProgressStyle};

let pb = ProgressBar::new(100);
pb.set_style(ProgressStyle::default_bar()
    .template("{spinner:.green} [{bar:40.cyan/blue}] {pos}/{len} ({eta})")
    .progress_chars("#>-"));
```

---

## Additional Findings from Deep Audit

### All Status Messages (Catalog for Styling)

**Voice States** (voice_control.rs, app/state.rs):
| Message | Category | Suggested Color |
|---------|----------|-----------------|
| "Listening Manual Mode (Rust pipeline)" | Recording | Red `● REC` |
| "Listening Auto Mode (Rust pipeline)" | Recording | Red `● AUTO` |
| "Processing..." | Processing | Yellow `◐` |
| "Transcript ready (Rust pipeline)" | Success | Green `✓` |
| "No speech detected" | Warning | Yellow `⚠` |
| "Voice capture failed (see log)" | Error | Red `✗` |
| "Auto-voice enabled" | Info | Blue `◉` |
| "Auto-voice disabled" | Info | Gray `○` |

**Codex States** (app/state.rs):
| Message | Category |
|---------|----------|
| "Waiting for Codex {spinner}" | Processing |
| "Codex failed: {message}" | Error |
| "Codex request canceled" | Info |
| "Codex unavailable: {reason}" | Error |

**Input States** (app/state.rs):
| Message | Category |
|---------|----------|
| "Nothing to send; prompt is empty" | Warning |
| "Input limit reached (max 8000 chars)" | Warning |
| "Codex request already running" | Warning |

### Missing: Help System

**Current state**: No built-in help screen or shortcut reference.

**Shortcuts only documented in**:
- README.md, QUICK_START.md (external docs)
- ui.rs footer hint: `Ctrl+R voice  Ctrl+V toggle` (only 2 shortcuts shown)

**Proposed**: Add `Ctrl+?` or `?` to show help overlay:
```
┌─────────────────────────────────────┐
│  Codex Voice - Keyboard Shortcuts   │
├─────────────────────────────────────┤
│  Ctrl+R   Start voice capture       │
│  Ctrl+V   Toggle auto-voice         │
│  Ctrl+T   Toggle send mode          │
│  Ctrl+]   Increase sensitivity      │
│  Ctrl+\   Decrease sensitivity      │
│  Ctrl+Q   Exit                      │
│  Ctrl+C   Cancel / Forward to Codex │
│  Enter    Send / Stop recording     │
├─────────────────────────────────────┤
│  Press any key to close             │
└─────────────────────────────────────┘
```

### Missing: Visual Configuration CLI Flags

**Current state**: Zero CLI flags for visual settings.

**Proposed flags**:
```
--theme <name>        Color theme (coral, catppuccin, dracula, nord)
--no-color            Disable colors (for pipes/logs)
--color-mode <mode>   Force color mode (truecolor, 256, ansi, none)
--no-unicode          Use ASCII-only characters
--compact             Minimal status line
```

**Proposed env vars**:
```
CODEX_VOICE_THEME=catppuccin
CODEX_VOICE_NO_COLOR=1
NO_COLOR=1              # Standard convention
```

### Missing: Terminal Capability Fallback

**Current state**: Assumes 24-bit truecolor, no fallback.

**Problem**: Some terminals (older SSH sessions, tmux without config) may not support truecolor.

**Proposed detection**:
```rust
fn detect_color_mode() -> ColorMode {
    if env::var("NO_COLOR").is_ok() {
        return ColorMode::None;
    }
    if env::var("COLORTERM").map(|v| v == "truecolor" || v == "24bit").unwrap_or(false) {
        return ColorMode::TrueColor;
    }
    match env::var("TERM").as_deref() {
        Ok(t) if t.contains("256color") => ColorMode::Color256,
        Ok(_) => ColorMode::Ansi16,
        Err(_) => ColorMode::None,
    }
}
```

### Missing: Error Visual Differentiation

**Current state**: Errors shown as plain text, same as info messages.

**Proposed error styling**:
```
✗ Voice capture failed (see log)          # Red prefix + red text
⚠ No speech detected                       # Yellow prefix
ℹ Auto-voice enabled                       # Blue prefix
✓ Transcript ready                         # Green prefix
```

### Missing: Mic Meter Visualization

**Current state** (`mic_meter.rs`): Text-only output:
```
Results (dBFS)
Ambient: RMS -45.2 dB, Peak -38.1 dB
Speech:  RMS -28.3 dB, Peak -15.7 dB

Suggested --voice-vad-threshold-db: -35.0
```

**Proposed visual meter**:
```
Ambient  ████░░░░░░░░░░░░░░░░  -45 dB
Speech   ████████████░░░░░░░░  -28 dB
Threshold         │            -35 dB
         ─────────┴──────────
         -80              -10 dB
```

### Missing: Real-time Audio Level Display

**Proposed**: Show live mic level during recording:
```
● REC │ ▁▂▄▆█▆▄▂▁ │ -32 dB │ 2.3s
```

Components:
- Recording indicator
- Live waveform/level bars
- Current dB level
- Recording duration

### Missing: Transcript Preview

**Current state**: Transcript appears after processing.

**Proposed**: Show partial transcript during processing:
```
◐ Processing... "Hello, can you help me with..."
```

### Missing: Mode Indicators in Prompt

**Current state**: No visual indication of current mode in overlay.

**Proposed persistent status bar**:
```
┌─ codex-voice ───────────────────────────────────────────────┐
│ ◉ AUTO │ Rust │ -40dB │ Ready          Ctrl+R rec  ?=help  │
└─────────────────────────────────────────────────────────────┘
```

### Missing: Notification Sounds (Optional)

**Proposed** (opt-in via `--sounds`):
- Beep on transcript complete
- Different tone for error
- Configurable via `--sound-on-complete`, `--sound-on-error`

### Additional Widget Ideas

**1. Transcript History Panel** (TUI mode):
```
┌─ Recent Transcripts ────────────────┐
│ 1. "Fix the login bug"         12s  │
│ 2. "Add unit tests"            8s   │
│ 3. "Refactor the auth..."      23s  │
└─────────────────────────────────────┘
```

**2. Pipeline Status Indicator**:
```
Pipeline: Rust (native) ✓
Model: ggml-base.en.bin (147MB)
Device: MacBook Pro Microphone
```

**3. Session Stats** (on exit):
```
Session Summary
───────────────
Transcripts: 12
Total speech: 3m 42s
Avg latency: 0.8s
Errors: 1
```

---

## Implementation Priorities

### Tier 0 - Quick Wins (High Impact, Low Effort)

| Task | File(s) | Effort | Impact |
|------|---------|--------|--------|
| Add ANSI colors to overlay status line | writer.rs | Low | **High** |
| Modern Braille spinner | codex/mod.rs | Low | Medium |
| Unicode state indicators (●, ✓, ✗, ⚠) | writer.rs, main.rs | Low | Medium |

### Tier 1 - Core Visual System

| Task | File(s) | Effort | Impact |
|------|---------|--------|--------|
| Create `StatusType` enum for message categories | new status.rs | Medium | **High** |
| Theme struct with coral/catppuccin/dracula | new theme.rs | Medium | Medium |
| `--theme` and `--no-color` CLI flags | config/mod.rs | Low | Medium |
| Color mode detection (truecolor/256/ansi) | new color.rs | Medium | Medium |

### Tier 2 - Enhanced Status Line

| Task | File(s) | Effort | Impact |
|------|---------|--------|--------|
| Redesign status line layout with sections | writer.rs | Medium | **High** |
| Show keyboard shortcuts in overlay | writer.rs | Low | Medium |
| Live recording duration display | voice_control.rs | Low | Medium |
| Pipeline/device indicator | main.rs | Low | Low |

### Tier 3 - Help and Discoverability

| Task | File(s) | Effort | Impact |
|------|---------|--------|--------|
| Help overlay (`Ctrl+?` or `?`) | new help.rs | Medium | Medium |
| Startup banner with version/config | main.rs | Low | Low |
| Session stats on exit | main.rs | Low | Low |

### Tier 4 - Advanced Features

| Task | File(s) | Effort | Impact |
|------|---------|--------|--------|
| Visual mic meter with bars | mic_meter.rs | Medium | Medium |
| Real-time audio level during recording | voice_control.rs, writer.rs | High | Medium |
| Output syntax highlighting | ui.rs + syntect | High | Medium |
| Progress bar for model download | start.sh or new | Medium | Low |
| Transcript preview during processing | voice_control.rs | Medium | Low |

### Tier 5 - Polish

| Task | File(s) | Effort | Impact |
|------|---------|--------|--------|
| Responsive narrow-terminal mode | writer.rs | Medium | Low |
| Transcript history panel (TUI) | ui.rs | High | Low |
| Optional notification sounds | new audio_feedback.rs | Medium | Low |
| ANSI-only fallback mode | theme.rs | Medium | Low |

---

## Resources

### Documentation
- [Ratatui Official Site](https://ratatui.rs/)
- [Ratatui GitHub](https://github.com/ratatui/ratatui)
- [Awesome Ratatui](https://github.com/ratatui/awesome-ratatui)
- [Claude Code Terminal Config](https://code.claude.com/docs/en/terminal-config)

### Color Themes
- [Dracula Theme](https://draculatheme.com)
- [Catppuccin](https://github.com/catppuccin)
- [iTerm2 Color Schemes](https://iterm2colorschemes.com/)
- [Windows Terminal Themes](https://windowsterminalthemes.dev/)

### CLI UX
- [CLI UX Best Practices - Evil Martians](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays)
- [Claude Code Internals: Terminal UI](https://kotrotsos.medium.com/claude-code-internals-part-11-terminal-ui-542fe17db016)

### Libraries
- [indicatif](https://github.com/console-rs/indicatif) - Progress bars for Rust
- [console](https://github.com/console-rs/console) - Terminal styling for Rust
- [syntect](https://github.com/trishume/syntect) - Syntax highlighting

---

## Next Steps

### Phase 1: Immediate Visual Improvements (Tier 0)

1. **Add colors to overlay status** (`writer.rs`):
   - Add ANSI color codes based on message type
   - Recording = red, Processing = yellow, Success = green, Error = red

2. **Replace spinner** (`codex/mod.rs`):
   - Change from `['-', '\\', '|', '/']` to Braille `["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]`

3. **Add unicode prefixes** to status messages:
   - `● REC` for recording
   - `✓` for success
   - `✗` for error
   - `⚠` for warning

### Phase 2: Theme System (Tier 1)

4. Create `rust_tui/src/theme.rs`:
   - Define `Theme` struct with all semantic colors
   - Implement coral (current), catppuccin, dracula, nord presets
   - Add `--theme` CLI flag to config/mod.rs

5. Create `rust_tui/src/color.rs`:
   - Detect terminal color capabilities
   - Provide fallback for non-truecolor terminals
   - Respect `NO_COLOR` environment variable

### Phase 3: Status Line Redesign (Tier 2)

6. Redesign overlay status line format:
   ```
   ● AUTO │ Rust │ -40dB │ Ready            Ctrl+R rec  Ctrl+V toggle
   ```

7. Add recording duration display during capture

### Phase 4: Help System (Tier 3)

8. Add help overlay accessible via `?` key
9. Show all keyboard shortcuts in formatted panel

### Future Phases

- Visual mic meter with ASCII bars
- Real-time audio level indicator
- Syntax highlighting in output
- Session statistics on exit
