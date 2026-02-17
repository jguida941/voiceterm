# Theme + Overlay Studio Plan (No-Code, Full-Surface Customization)

Date: 2026-02-17  
Status: Activated planning track (execution mirrored in `dev/active/MASTER_PLAN.md` MP-148..MP-151)  
Scope: Full in-overlay editor so users can customize nearly every overlay aspect
without writing code

`dev/active/MASTER_PLAN.md` remains the canonical execution tracker.
Implementation starts only through linked MP items and must preserve existing
HUD/theme behavior until non-regression gates pass.

## Product Goal

Users should be able to open a full editor inside VoiceTerm and customize:

- theme colors and token palettes
- borders, glyph/icon packs, and text styles
- layout types and responsive breakpoints
- graphs/widgets and what data they show
- animations and transition behavior
- interaction behavior (hotkeys, mouse, visibility rules)
- accessibility modes and readability controls

No coding should be required for common customization workflows.

## Re-Audit Summary (Codebase + UX Gaps)

### Strong today

- runtime theme switching, picker, and settings wiring exist:
  - `src/src/bin/voiceterm/theme_ops.rs`
  - `src/src/bin/voiceterm/theme_picker.rs`
  - `src/src/bin/voiceterm/settings_handlers.rs`
- color capability fallback already exists:
  - `src/src/bin/voiceterm/config/theme.rs`
  - `src/src/bin/voiceterm/color_mode.rs`
- HUD data modules already have a registry pattern:
  - `src/src/bin/voiceterm/hud/mod.rs`

### Current blockers for full no-code editor

- theme system is enum/static-palette centered:
  - `src/src/bin/voiceterm/theme/mod.rs`
  - `src/src/bin/voiceterm/theme/palettes.rs`
- layout and animation are hardcoded in formatter/util modules:
  - `src/src/bin/voiceterm/status_line/layout.rs`
  - `src/src/bin/voiceterm/status_line/animation.rs`
- settings UI is flat, not a multi-page editor:
  - `src/src/bin/voiceterm/settings/items.rs`
  - `src/src/bin/voiceterm/settings/state.rs`
- active overlay renderer is custom ANSI row redraw, not a structured scene graph:
  - `src/src/bin/voiceterm/writer/state.rs`
  - `src/src/bin/voiceterm/writer/render.rs`

## Is "Full GUI Editor in Overlay" Possible?

Yes, with boundaries:

- possible:
  - full-screen in-terminal editor flows
  - multi-page visual editing with live preview
  - rich controls (lists, sliders, toggles, pickers, reorder)
- not universally possible inside the terminal itself:
  - forcing actual font family changes globally
  - true pixel-canvas drag/drop UIs
  - desktop-window-level chrome effects

We can still make this feel GUI-like by building a full in-overlay Studio with
structured widgets and preview panes.

## Missing User Stories to Add (Delta From Prior Plan)

The prior plan still missed key no-code stories. Add these explicitly:

1. "I want to remap every key/button action without editing files."
2. "I want to choose what HUD modules appear and in what order."
3. "I want different looks for idle, recording, processing, responding."
4. "I want to change graph type, scale, smoothing, and thresholds."
5. "I want to customize startup splash and overlay labels/messages."
6. "I want to save style profiles per backend/project."
7. "I want reduced motion/high contrast/ASCII-safe presets."
8. "I want undo/redo and rollback if I break the style."
9. "I want import/export/share style packs safely."
10. "I want font-like control from inside the editor."

## Font Customization Strategy (Practical, Honest)

Inside terminal constraints:

- provide typography-like controls in overlay:
  - bold/dim/italic/underline policy per component
  - glyph packs (Unicode, ASCII-safe, nerd-font-friendly)
  - spacing/density scale
  - icon density and separators

Host-terminal adapter track (optional):

- WezTerm adapter via runtime config overrides
- Kitty adapter via remote control commands
- iTerm2 adapter via profile-related escape mechanisms
- xterm-compatible font operations only where enabled

This gives users a "fonts" experience where supported, with safe fallback when
not supported.

## Framework Capability Audit (What Rust Stack Enables)

### Ratatui (already in repo)

- supports rich layout composition, constraints, and many widgets (charts,
  sparklines, bars, tables, tabs, scrollbars) and custom widget extensions.
- strong fit for Studio editor surfaces and layout builder previews.
- keep PTY-safe ANSI transport while using Ratatui concepts for composition.

### Crossterm (already in repo)

- supports advanced input events including mouse/focus/paste/resize.
- enables a richer editor interaction model without leaving terminal.

### TachyonFX (candidate, referenced in roadmap)

- supports terminal effect composition and can drive richer state transitions.
- useful for no-code motion presets and channel-level animation controls.

### Ecosystem opportunities

- third-party Ratatui widgets (tree, editors, popups, etc.) can accelerate Studio.
- style packs can mirror proven patterns from Helix/Zellij/VS Code ecosystems.

## Full Customization Surface (Target)

### A) Visual tokens

- full semantic palette per state and component
- border sets per section
- icon/glyph packs and fallback packs
- text style policy (bold/dim/italic/underline per token)
- background styles (solid, gradient-like stepped palettes where supported)

### B) Layout editor

- choose layout template (classic, compact, pro, split, minimal)
- container tree editing (`row`, `column`, `grid`, `stack`)
- module reorder and docking
- responsive breakpoints and per-width variants
- spacing scale, padding scale, density presets

### C) Widget editor

- enable/disable widget modules
- choose widget types for metrics:
  - sparkline, bar, line, gauge, dots, heartbeat, compact text
- configure each widget:
  - color mapping
  - scale mode
  - history window length
  - smoothing policy

### D) Motion editor

- animation channel toggles (pulse/spinner/heartbeat/transitions)
- speed, easing, and frame-set selection
- per-state animation policy
- reduced-motion one-click policy

### E) Behavior editor

- auto-hide and collapse rules
- update cadence and refresh policy
- message verbosity and dwell durations
- panel show/hide triggers by state

### F) Input + interaction editor

- full keybind remapping
- mouse click zones and behavior policies
- focus order and navigation style

### G) Accessibility editor

- high-contrast and color-blind safe modes
- reduced motion mode
- ASCII-safe glyph mode
- large-spacing mode
- readability warnings/contrast checker

### H) Profile editor

- per-backend style profile
- per-project style profile
- time-based or context-based profile switching (later phase)

## Studio UX Architecture (No-Code)

Add `Settings -> Studio` with pages:

1. Home
2. Colors
3. Typography + Glyphs
4. Borders + Frames
5. Layout Builder
6. Widgets
7. Motion
8. Behavior
9. Keybinds
10. Accessibility
11. Profiles
12. Preview + Save/Export

Interaction model:

- keyboard-first with mouse enhancement
- persistent draft state
- instant preview
- undo/redo stack
- apply vs save distinction
- rollback to last-known-good

## Data Model Upgrade

Move from theme-only to style-pack model:

- `ThemeTokens`: colors/borders/glyph/text styles
- `LayoutProfile`: structure + responsive rules
- `WidgetProfile`: module composition + chart configs
- `MotionProfile`: animation channels + timings
- `BehaviorProfile`: visibility/update/interaction rules
- `AccessibilityProfile`: readability and fallback policies
- `TerminalAdapterProfile`: optional host-terminal integration settings

Persist as versioned `StylePack` with inheritance and partial overrides.

## File/Module Plan

### New modules (proposed)

- `src/src/bin/voiceterm/theme/spec.rs`
- `src/src/bin/voiceterm/theme/runtime.rs`
- `src/src/bin/voiceterm/theme/registry.rs`
- `src/src/bin/voiceterm/theme/resolver.rs`
- `src/src/bin/voiceterm/theme/io.rs`
- `src/src/bin/voiceterm/theme/migrate.rs`
- `src/src/bin/voiceterm/studio/` (editor pages/state/actions)
- `src/src/bin/voiceterm/render_model/` (scene/layout/widget composition)
- `src/src/bin/voiceterm/keymap/` (runtime-editable keybinding profiles)
- `src/src/bin/voiceterm/profiles/` (backend/project profile resolution)

### Existing modules to refactor

- `src/src/bin/voiceterm/theme/mod.rs`
- `src/src/bin/voiceterm/theme/palettes.rs`
- `src/src/bin/voiceterm/config/theme.rs`
- `src/src/bin/voiceterm/settings/*`
- `src/src/bin/voiceterm/event_loop.rs`
- `src/src/bin/voiceterm/status_line/layout.rs`
- `src/src/bin/voiceterm/status_line/animation.rs`
- `src/src/bin/voiceterm/status_line/format.rs`
- `src/src/bin/voiceterm/writer/state.rs`

## Safe Rollout Plan (Do Not Break Overlay)

### Phase 0: Safety rails before expansion

- add golden snapshots for existing HUD layouts/themes
- add compatibility matrix tests for terminals/modes
- add migration test harness for style schema versions

Acceptance:

- baseline output parity protected by tests before new editor work

### Phase 1: Style engine foundation

- implement `StylePack` schema and runtime resolver
- convert built-ins to style packs internally
- keep UI behavior unchanged

Acceptance:

- all existing theme behavior remains intact

### Phase 2: Persistence and precedence

- preferences + style packs on disk
- project overrides + CLI precedence
- atomic writes + fallback on invalid specs

Acceptance:

- stable cross-restart behavior with tested precedence

### Phase 3: Studio v1 (visual tokens only)

- colors, borders, glyphs, text-style controls
- live preview + save/duplicate/export

Acceptance:

- non-coder can fully restyle visuals end-to-end

### Phase 4: Studio v2 (layout + widgets)

- layout builder
- widget composer
- graph configuration panel

Acceptance:

- user can create distinct structural layouts and graph styles without code

### Phase 5: Studio v3 (motion + behavior + accessibility)

- motion channel editor
- behavior rules editor
- accessibility profiles

Acceptance:

- user can control animation intensity and behavior per state

### Phase 6: Keybinds and profile routing

- no-code keymap editor
- backend/project profile selection

Acceptance:

- user can remap interactions and apply context-specific styles

### Phase 7: Terminal adapter layer (fonts and host-specific extras)

- optional adapters for WezTerm/Kitty/iTerm2/xterm-compatible flows
- explicit capability checks and opt-in guardrails

Acceptance:

- supported terminals can apply host-level extras from Studio
- unsupported terminals degrade cleanly

### Phase 8: Optional render-backend hardening

- evaluate Ratatui-buffer path for Studio overlays/widgets
- keep ANSI writer transport and PTY integrity

Acceptance:

- no PTY regressions, reduced render complexity where adopted

## "No-Code Promise" Rules

To keep this truly no-code:

1. Every persisted field in `StylePack` must have a Studio control.
2. Importing a pack must never require manual edits.
3. Every validation error must be shown with a guided fix action.
4. Every destructive action must have undo/rollback.
5. Studio must support keyboard-only workflows.

## Robustness and Guardrails

- strict schema validation and bounded numeric ranges
- capability-aware fallback for color/glyph/animation features
- last-known-good runtime fallback on invalid updates
- safe-mode startup flag if style loading fails repeatedly
- profile sanity checks before activation

## Quality Gates

Unit tests:

- schema parse/validate
- inheritance merge
- precedence rules
- migration steps
- fallback transforms

Integration tests:

- startup with preferences + overrides
- import/export roundtrip
- studio apply/save/rollback flows
- keymap/profile activation behavior

Snapshot tests:

- narrow/medium/wide renders
- all built-ins + sample custom packs
- per-state visual variants

Performance checks:

- bounded render-time allocations
- bounded animation tick rates
- no unbounded buffers in hot paths

Repo gates:

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py docs-check --user-facing`
- `python3 dev/scripts/devctl.py hygiene`

## Risks and Mitigations

- Risk: Feature scope explosion slows delivery.
  - Mitigation: strict phased delivery with frozen acceptance per phase.
- Risk: Editor complexity harms reliability.
  - Mitigation: snapshot baselines, kill-switches, and staged flags.
- Risk: Terminal differences break "font-like" behavior.
  - Mitigation: adapter capability detection + explicit unsupported fallback.
- Risk: Too many options overwhelm users.
  - Mitigation: presets first, advanced mode toggle, guided templates.

## Documentation Updates Required

When implemented, update:

- `dev/active/MASTER_PLAN.md`
- `dev/CHANGELOG.md`
- `guides/USAGE.md`
- `guides/CLI_FLAGS.md`
- `guides/TROUBLESHOOTING.md`
- `dev/ARCHITECTURE.md`

## References (Framework and Pattern Research)

- Ratatui layout concepts: <https://ratatui.rs/concepts/layout/>
- Ratatui widgets and custom widgets:
  <https://ratatui.rs/concepts/widgets/>
- Ratatui crate docs and markers/styles:
  <https://docs.rs/ratatui/latest/ratatui/>
- Crossterm event model:
  <https://docs.rs/crossterm/latest/crossterm/event/index.html>
- Crossterm key event kinds:
  <https://docs.rs/crossterm/latest/crossterm/event/enum.KeyEventKind.html>
- TachyonFX docs:
  <https://docs.rs/tachyonfx/latest/tachyonfx/>
- Ratatui third-party widgets list:
  <https://ratatui.rs/community/third-party-widgets/>
- Helix theme model:
  <https://docs.helix-editor.com/themes.html>
- Zellij themes:
  <https://zellij.dev/documentation/themes>
- VS Code theme customization:
  <https://code.visualstudio.com/docs/configure/themes>
- xterm control sequences (`allowFontOps`, OSC 50 context):
  <https://invisible-island.net/xterm/ctlseqs/ctlseqs.html>
- iTerm2 escape codes and profile notes:
  <https://iterm2.com/documentation-escape-codes.html>
- Kitty remote control protocol:
  <https://sw.kovidgoyal.net/kitty/rc_protocol/>
- WezTerm runtime config overrides:
  <https://wezterm.org/config/lua/window/set_config_overrides.html>
