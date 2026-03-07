# Phase 2: Terminal Companion Platform

> Transform VoiceTerm from a voice-only overlay into a full terminal companion
> that complements AI sessions, shell workflows, and any interactive terminal use.

---

## Current Architecture Audit

### What We Already Have

VoiceTerm is a **PTY-wrapping overlay** written in Rust. It spawns the user's
shell (or an AI CLI like Claude) inside a pseudo-terminal, intercepts all I/O
through the PTY master fd, and renders a multi-row HUD using ratatui on top of
the native terminal output.

**Existing data capture points:**

| Capability | File | Status |
|---|---|---|
| All PTY raw output (ANSI-intact) | `pty_session/io.rs` (spawn_reader_thread) | Active |
| User input bytes | `session_memory.rs` (record_user_input_bytes) | Active |
| Backend output bytes | `session_memory.rs` (record_backend_output_bytes) | Active |
| Shell prompt detection | `prompt.rs` (PromptTracker) | Active |
| Claude prompt suppression | `event_state.rs` (claude_prompt_detector) | Active |
| Audio levels (real-time meter) | `voice_control/manager.rs` (live_meter) | Active |
| Transcript history | `transcript_history.rs` | Active |
| Session memory (markdown log) | `session_memory.rs` | Active |
| Dev event stream (JSONL) | `--dev-log` flag | Active |
| Process exit status | `pty.rs` (try_wait) | Available but unused |
| VTE escape sequence parsing | `vte` crate in deps | Available |
| Window resize events | `terminal.rs` (SIGWINCH) | Active |
| Memory/ingestor schema | `memory/mod.rs` | Wired but empty |

**Architecture strengths:**

- Multi-threaded message-passing design (input, output, writer, voice threads)
- Bounded crossbeam channels prevent backpressure issues
- Event loop already multiplexes PTY output, input, voice, and wake-word channels
- Row-budget system dynamically reserves HUD space
- VTE crate already in dependencies for escape sequence parsing
- Session memory and transcript history provide working data capture pipelines

**Architecture gaps for Phase 2:**

- No structured command boundary detection (relies on regex prompt heuristics)
- No exit code capture from commands
- No working directory tracking beyond session start
- No command duration measurement
- No structured analytics storage
- No AI context packaging pipeline
- No plugin/extension system
- Memory module exists but has no active data flow

---

## Research Findings

### 1. Shell Integration Protocols (OSC 133)

The industry standard for detecting command boundaries in a terminal is the
**FinalTerm / OSC 133 protocol**, now adopted by iTerm2, VS Code, Kitty,
Windows Terminal, and Warp.

**Sequence definitions:**

| Sequence | Meaning |
|---|---|
| `ESC ] 133 ; A BEL` | Prompt start |
| `ESC ] 133 ; B BEL` | Prompt end / command input start |
| `ESC ] 133 ; C BEL` | Command executed (output begins) |
| `ESC ] 133 ; D [; exitcode] BEL` | Command finished with optional exit code |

**State machine:**

```
IDLE ──(A)──> PROMPT ──(B)──> COMMAND_INPUT ──(C)──> COMMAND_OUTPUT ──(D)──> IDLE
                                    │
                                    └──(Ctrl-C)──> synthesize C, then D
```

This gives us everything: command text (between B and C), output (between C and
D), exit codes (from D parameter), and command duration (timestamp C vs D).

**VS Code extends this with OSC 633:**

| Sequence | Purpose |
|---|---|
| `ESC ] 633 ; E <cmdline> [; nonce] ST` | Explicit command line text |
| `ESC ] 633 ; P Cwd=<path> ST` | Set working directory property |

**Implementation:** We ship a small shell hook script (bash/zsh/fish) that users
source in their rc file. The hook emits OSC 133 sequences at precmd/preexec
boundaries. Our VTE parser picks them up from the PTY output stream.

### 2. Working Directory & Environment Tracking

**OSC 7** reports the current working directory:

```
ESC ] 7 ; file://<hostname>/<path> BEL
```

**OSC 1337** (iTerm2 extensions) provides additional metadata:

| Sequence | Data |
|---|---|
| `ESC ] 1337 ; RemoteHost=<user>@<host> ST` | User and hostname |
| `ESC ] 1337 ; CurrentDir=<path> ST` | Absolute working directory |
| `ESC ] 1337 ; SetUserVar=<key>=<b64val> ST` | Custom variables |

**Fallback (no shell hooks):** On macOS, `proc_pidinfo()` with
`PROC_PIDVNODEPATHINFO` can retrieve the child process's CWD directly. The
`libproc` crate provides safe Rust bindings. On Linux, read
`/proc/<pid>/cwd`.

### 3. Process Monitoring from PTY Parent

Since we own the child PID, we can inspect it:

| Metric | macOS | Linux |
|---|---|---|
| Working directory | `proc_pidinfo(PROC_PIDVNODEPATHINFO)` | `/proc/pid/cwd` |
| Open files | `proc_pidinfo(PROC_PIDLISTFDS)` | `/proc/pid/fd/` |
| CPU usage | `sysinfo` crate | `sysinfo` or `/proc/pid/stat` |
| Memory usage | `sysinfo` crate | `/proc/pid/status` |
| Network connections | `lsof -p <pid>` | `/proc/pid/net/tcp` |
| Child processes | `sysctl(KERN_PROC)` | `/proc/pid/children` |
| Process state | `sysinfo` crate | `/proc/pid/status` |

**Relevant crates:**

- `libproc` -- macOS process info via libproc.h
- `procfs` -- Linux /proc filesystem bindings
- `sysinfo` -- Cross-platform CPU/memory/disk/network per process

### 4. Terminal Clipboard (OSC 52)

```
ESC ] 52 ; c ; <base64-data> BEL     -- write to clipboard
ESC ] 52 ; c ; ? BEL                  -- query clipboard
```

Since we sit between the child and the real terminal, we can intercept and
inject clipboard operations. The `arboard` crate provides direct OS clipboard
access as a fallback. Maximum payload: 74,994 bytes of decoded data.

### 5. Notifications (OSC 9, OSC 99)

**Simple notifications:** `ESC ] 9 ; <message> BEL`

**Kitty rich notifications (OSC 99):**

| Key | Purpose | Values |
|---|---|---|
| `p` | Payload type | title, body, close, icon, buttons |
| `u` | Urgency | 0=low, 1=normal, 2=critical |
| `o` | When to show | always, unfocused, invisible |
| `w` | Expiry (ms) | -1=OS default, 0=never, N=ms |

**Progress bars (OSC 9;4):**

```
ESC ] 9 ; 4 ; 1 ; <0-100> BEL     -- normal progress
ESC ] 9 ; 4 ; 3 ; 0 BEL           -- indeterminate spinner
ESC ] 9 ; 4 ; 0 ; 0 BEL           -- clear progress
```

Supported by Windows Terminal, Ghostty, Konsole, mintty.

### 6. What Existing AI Terminal Tools Do

| Tool | Approach | Key Features |
|---|---|---|
| **Warp** | Full terminal replacement (Rust + Metal) | Blocks architecture, AI command gen via `#`, agent mode, error explanation, DCS+JSON metadata |
| **Fig / Amazon Q** | Overlay on existing terminal | Autocomplete, contextual suggestions, AWS-aware |
| **GitHub Copilot CLI** | Plugin | NL-to-command translation, GitHub integration |
| **Aider** | In-terminal AI pair programmer | Repo map (function signatures), auto-git-commits, architect mode |
| **Butterfish** | PTY wrapper (Go) | Shell history IS the context window, capital-letter AI trigger, goal mode |
| **llmsh** | PTY wrapper + daemon | `:` prefix for AI, daemon maintains session context |

**Key insight from Butterfish:** "Your shell history maps directly to ChatGPT's
alternating user/assistant message format. Commands and output become 'user'
messages, LLM responses become 'assistant' messages."

**Key insight from Warp:** Uses hex-encoded DCS sequences containing JSON
metadata from shell hooks. Each command+output is a discrete "block" with
structured metadata (cwd, git branch, timing, exit code).

**Key insight from Aider:** Maintains a "repository map" -- function signatures
and file structures -- as persistent context. Compressed git graph representation
survives context restarts.

### 7. Context Packaging for AI

**Structured context format:**

```json
{
  "cwd": "/home/user/project",
  "git": {
    "branch": "feature/xyz",
    "dirty_files": ["src/main.rs"],
    "last_commit": "abc123 fix: resolve build error"
  },
  "recent_commands": [
    {
      "cmd": "cargo build",
      "exit_code": 1,
      "duration_ms": 3200,
      "output_tail": "error[E0308]: mismatched types..."
    }
  ],
  "environment": {
    "shell": "zsh",
    "rust_version": "1.75.0"
  }
}
```

**Context window management strategies:**

1. **Head/tail preservation** -- keep first and last N lines of large outputs
2. **Hierarchical summarization** -- recent commands verbatim, older ones summarized
3. **File-based overflow** -- write large outputs to temp files, pass reference only
4. **Structured packaging** -- JSON over raw text, 70-90% token reduction

**Relevant crates:** `git2` (libgit2 bindings), `tiktoken-rs` (token counting),
`reqwest` (LLM API calls).

### 8. Plugin / Extension Architecture

**Zellij's WASM plugin system (gold standard):**

- Plugins compile from Rust to WebAssembly via `zellij-tile` SDK
- Sandboxed execution in `wasmi` interpreter
- 9-permission model (ReadApplicationState, RunCommand, WriteToStdin, etc.)
- Event subscription: plugins register for events in `load()`, handle in `update()`
- Render by writing ANSI to stdout from within the WASM sandbox
- Background workers for resource-intensive tasks
- Inter-plugin communication via pipe messages

**tmux control mode (`tmux -CC`):**

- External apps interact via stdin/stdout text protocol
- `%output <pane_id> <data>` for pane output events
- `%subscription-changed` for state change notifications
- All tmux commands available programmatically

**Recommended pattern for VoiceTerm:**

```rust
trait CompanionPlugin {
    fn name(&self) -> &str;
    fn on_command_start(&mut self, cmd: &str, cwd: &Path);
    fn on_command_finish(&mut self, cmd: &str, exit_code: i32, output: &str, duration: Duration);
    fn on_directory_change(&mut self, old: &Path, new: &Path);
    fn on_prompt(&mut self, prompt_text: &str);
    fn render(&self, area: Rect, buf: &mut Buffer); // ratatui widget
    fn subscriptions(&self) -> Vec<EventKind>;
}
```

**Crates:** `wasmi` or `wasmtime` for sandboxed plugins, `libloading` for
native .so/.dylib dynamic loading.

### 9. Session Analytics

**What Atuin captures (Rust, SQLite-backed):**

- Command text, exit code, CWD, hostname, session ID, duration
- Searchable history with stats subcommand
- E2E encrypted sync between machines

**Derivable metrics from our PTY position:**

- Command frequency / most-used commands
- Exit code distribution (success/failure rate)
- Command execution duration
- Output volume per command
- Error patterns (non-zero exit, "error:", "fatal:", "permission denied")
- Directory navigation patterns (most-visited, traversal graph)
- Idle time vs active time
- Edit-compile-run cycle detection
- Time-of-day usage patterns

**Storage:** SQLite via `rusqlite` with tables for commands, sessions,
directories.

---

## Phase 2 Feature Roadmap

### Tier 1: Foundation (Enable Everything Else)

#### 1.1 Shell Integration Hook Script

Ship `voiceterm-shell-integration.{bash,zsh,fish}` that users source in their
rc file. The script installs precmd/preexec hooks that emit:

- `OSC 133;A` at prompt start
- `OSC 133;B` at prompt end
- `OSC 133;C` at preexec (command about to run)
- `OSC 133;D;<exit_code>` at precmd (previous command finished)
- `OSC 7` with current working directory
- Optional: `OSC 1337;CurrentDir=<path>` and `OSC 1337;RemoteHost=<user>@<host>`

**Auto-injection option:** If the user's backend is bash/zsh/fish, inject the
hook script automatically by prepending it to the shell's init sequence via the
PTY. This requires no user rc file modification.

**Fallback:** For shells without hooks, use `PromptTracker` regex detection
(already exists) plus `proc_pidinfo` / `/proc` CWD polling.

#### 1.2 OSC 133 Parser in Event Loop

Extend the existing VTE-based output pipeline to detect and parse OSC 133/633
sequences:

- New `ShellIntegrationTracker` struct in the event loop
- State machine: Idle -> Prompt -> CommandInput -> CommandOutput -> Idle
- On each transition, emit a typed `ShellEvent` to a new channel
- Strip the OSC sequences from output before forwarding to the terminal (they're
  metadata, not display content)

```rust
enum ShellEvent {
    PromptStart,
    CommandStart { command_text: String },
    CommandOutput { chunk: Vec<u8> },
    CommandFinish { exit_code: Option<i32>, duration: Duration },
    DirectoryChange { path: PathBuf },
}
```

#### 1.3 Command History Database

SQLite database at `~/.voiceterm/history.db`:

```sql
CREATE TABLE commands (
    id          INTEGER PRIMARY KEY,
    session_id  TEXT NOT NULL,
    command     TEXT NOT NULL,
    exit_code   INTEGER,
    duration_ms INTEGER,
    cwd         TEXT,
    output_head TEXT,    -- first 500 chars
    output_tail TEXT,    -- last 500 chars
    output_bytes INTEGER,
    timestamp   INTEGER NOT NULL,
    backend     TEXT     -- "bash", "zsh", "claude", etc.
);

CREATE TABLE sessions (
    id         TEXT PRIMARY KEY,
    start_time INTEGER NOT NULL,
    end_time   INTEGER,
    shell      TEXT,
    hostname   TEXT,
    cwd_start  TEXT
);
```

Crate: `rusqlite` with bundled SQLite.

---

### Tier 2: Terminal Intelligence

#### 2.1 Smart Status HUD Modules

New HUD modules that display live terminal context in the status bar:

| Module | Data Source | Display |
|---|---|---|
| **CWD** | OSC 7 / proc_pidinfo | Truncated path in status bar |
| **Git Branch** | `git2` crate on CWD change | Branch name + dirty indicator |
| **Last Exit** | OSC 133;D exit code | Green checkmark or red X |
| **Cmd Duration** | OSC 133 C-to-D timing | "2.3s" for commands >1s |
| **Error Count** | Session error accumulator | Red badge when >0 |

These plug into the existing `HudModule` trait and row-budget system.

#### 2.2 Error Detection & Explanation

When a command finishes with non-zero exit code:

1. Capture the last N lines of output
2. Pattern-match against common error types:
   - Compiler errors (`error[E`, `SyntaxError`, `TypeError`)
   - Permission errors (`Permission denied`, `EACCES`)
   - Not-found errors (`command not found`, `No such file`)
   - Network errors (`Connection refused`, `timeout`)
3. Display a brief error summary in the HUD
4. Offer to send the error context to an AI for explanation (hotkey)

#### 2.3 Long-Running Command Notifications

- Track command duration via OSC 133 C/D timestamps
- If duration exceeds configurable threshold (default 10s) AND terminal is in
  background, emit `OSC 99` (Kitty) or `OSC 9` (iTerm2) desktop notification
- Show progress bar in HUD for commands that emit recognizable progress patterns
- Emit `OSC 9;4` for taskbar/tab progress on supported terminals

#### 2.4 Session Analytics Dashboard

New overlay (Ctrl+A or similar hotkey):

- Most-used commands (bar chart, ratatui widgets)
- Success/failure rate
- Average command duration
- Most-visited directories
- Session timeline
- Error frequency over time

Data sourced from the SQLite history database.

---

### Tier 3: AI Companion Features

#### 3.1 Context-Aware AI Assist

Hotkey-triggered AI assistance that packages terminal context:

1. Gather context:
   - Last N commands with exit codes and output tails
   - Current working directory
   - Git status (branch, dirty files, recent commits) via `git2`
   - Detected project type (Cargo.toml -> Rust, package.json -> Node, etc.)
   - Current error state if any
2. Package as structured JSON
3. Send to configured LLM endpoint (Claude API, OpenAI, local Ollama)
4. Display response in a scrollable overlay pane

**Trigger modes:**
- Manual: hotkey (e.g., Ctrl+?) opens AI assist
- Auto-suggest: on error, show "AI can help" indicator in HUD
- Voice: "hey, what went wrong?" triggers context gather + AI query

#### 3.2 Command Suggestion Engine

When the user pauses at a prompt (detected via OSC 133 B -> idle timer):

- Analyze recent command history for patterns
- Detect common sequences (e.g., after `git add`, suggest `git commit`)
- Show ghost text suggestion in the HUD (not injected into terminal)
- Accept with Tab or dismiss with any other key
- Can be backed by local heuristics or LLM API

#### 3.3 AI Session Memory

Extend the existing `memory/` module:

- Feed `ShellEvent`s into `MemoryIngestor` (already wired but empty)
- Build per-project memory: common workflows, preferred commands, error patterns
- Persist across sessions in `~/.voiceterm/memory/`
- Feed into AI context for personalized assistance
- Retention/redaction policies (already specced in memory module)

#### 3.4 Transcript-to-Command Pipeline

For AI CLI sessions (Claude, ChatGPT, etc.):

- Detect when the AI backend suggests a command (pattern matching on code blocks)
- Offer one-click execution in a sandboxed sub-PTY
- Capture output and feed back to the AI session
- Track which AI suggestions succeeded/failed

---

### Tier 4: Platform Features

#### 4.1 Clipboard Ring

- Intercept OSC 52 sequences from child processes
- Maintain a clipboard history ring (last 20 entries)
- Hotkey to open clipboard picker overlay
- Search within clipboard history
- Paste selected entry via PTY input injection

#### 4.2 Plugin System (v1 -- Native Rust)

Start with a trait-based native plugin architecture:

```rust
pub trait CompanionPlugin: Send + Sync {
    fn name(&self) -> &str;
    fn version(&self) -> &str;
    fn subscriptions(&self) -> Vec<EventKind>;

    fn on_event(&mut self, event: &CompanionEvent) -> PluginAction;
    fn render_hud(&self, area: Rect, buf: &mut Buffer) {}
    fn render_overlay(&self, area: Rect, buf: &mut Buffer) {}
}

pub enum CompanionEvent {
    CommandStart { cmd: String, cwd: PathBuf },
    CommandFinish { cmd: String, exit_code: i32, duration: Duration, output: String },
    DirectoryChange { path: PathBuf },
    Prompt { text: String },
    Transcript { text: String, source: VoiceCaptureSource },
    Tick { elapsed: Duration },
}

pub enum PluginAction {
    None,
    InjectInput(String),
    ShowNotification { title: String, body: String, urgency: u8 },
    UpdateHud,
}
```

Built-in plugins: analytics, git status, error detector, AI assist.

Future v2: WASM sandboxed plugins via `wasmi` for third-party extensions.

#### 4.3 Multiplexed Companion Panes

Split the terminal view to show companion content alongside the main PTY:

- Side panel for AI chat / context
- Bottom panel for live analytics / logs
- Floating panel for quick actions
- Uses ratatui layout system (already the rendering backend)
- Row/column budget extends the existing row reservation system

#### 4.4 Remote Session Awareness

Detect SSH sessions and adapt:

- Parse `OSC 1337;RemoteHost` for remote context
- Use OSC 52 for clipboard (works over SSH)
- Adjust process monitoring (can't use proc_pidinfo on remote host)
- Track local vs remote directory context

---

## Implementation Priority

```
Phase 2a (Foundation)         Phase 2b (Intelligence)
├── Shell integration hooks   ├── Smart HUD modules
├── OSC 133 parser            ├── Error detection
├── Command history DB        ├── Long-running notifications
└── CWD tracking              └── Session analytics overlay

Phase 2c (AI Companion)       Phase 2d (Platform)
├── Context-aware AI assist   ├── Clipboard ring
├── Command suggestions       ├── Plugin system v1
├── AI session memory         ├── Companion panes
└── Transcript-to-command     └── Remote awareness
```

Each tier builds on the previous. Tier 1 (Foundation) is the prerequisite for
everything else -- once we can detect command boundaries and track state, every
other feature becomes straightforward.

---

## New Dependencies

| Crate | Purpose | Phase |
|---|---|---|
| `rusqlite` | Command history + analytics storage | 2a |
| `git2` | Git status in HUD + AI context | 2b |
| `libproc` | macOS process CWD/resource monitoring | 2a |
| `sysinfo` | Cross-platform process metrics | 2b |
| `arboard` | Direct OS clipboard access (OSC 52 fallback) | 2d |
| `reqwest` | LLM API calls for AI assist | 2c |
| `base64` | OSC 52/99 payload encoding | 2d |

---

## Key Technical Decisions

### Shell hook injection: Auto vs Manual

**Auto-injection** (prepend to shell init via PTY): Zero setup, works
immediately. Risk: may conflict with user's existing shell integration
(e.g., iTerm2 hooks).

**Manual sourcing** (user adds `source voiceterm-integration.sh` to rc): More
reliable, user is in control. Downside: requires setup step.

**Recommendation:** Auto-inject by default with `--no-shell-integration` flag to
disable. Detect existing integrations (iTerm2, VS Code) and defer to them,
parsing their sequences instead.

### Analytics storage: SQLite vs Flat file

SQLite gives us indexed queries for the analytics dashboard without
reimplementing a query engine. The `rusqlite` crate with bundled SQLite adds
~1.5MB to the binary but eliminates external dependencies.

**Recommendation:** SQLite with `rusqlite` (bundled feature).

### AI backend: Built-in vs Pluggable

Start with a simple HTTP client (`reqwest`) that calls the Claude API. Make the
endpoint, model, and system prompt configurable. The plugin system (Tier 4) will
allow community-built backends for OpenAI, Ollama, etc.

### Plugin execution: Native vs WASM

Native Rust plugins (v1) for built-in functionality and trusted extensions.
WASM sandboxing (v2) for third-party plugins -- follows Zellij's proven model
with the `wasmi` crate.

---

## Competitive Positioning

| Feature | Warp | Fig/Q | Copilot CLI | VoiceTerm Phase 2 |
|---|---|---|---|---|
| Voice control | No | No | No | Yes (core) |
| Works with any terminal | No (is the terminal) | Yes (overlay) | Yes (plugin) | Yes (PTY wrapper) |
| Command suggestions | Yes | Yes | Yes | Planned (2c) |
| Error explanation | Yes | No | No | Planned (2b) |
| Session analytics | No | No | No | Planned (2b) |
| AI context packaging | Yes | Limited | Limited | Planned (2c) |
| Plugin system | No | No | No | Planned (2d) |
| Desktop notifications | No | No | No | Planned (2b) |
| Clipboard management | Basic | No | No | Planned (2d) |
| Open source | No | No | No | Yes |

**Our differentiators:**
1. Voice-first -- no other terminal tool has native voice control
2. Overlay model -- works with ANY terminal, doesn't replace it
3. Open source + extensible -- plugin system for community features
4. AI-agnostic -- works with Claude, ChatGPT, local models, or no AI at all
5. Analytics -- no terminal tool currently offers session analytics

---

## Swiss Army Knife: Expanded Use-Case Catalog

Everything below maps back to our existing architecture. We own the PTY master
fd, we have a ratatui HUD, we have voice control, bounded channels, and a
plugin-ready event loop. Each idea notes what existing module it hooks into.

---

### A. White-Hat Security & Pentesting

**Why we're uniquely positioned:** A PTY overlay sees every byte of every tool's
output before it hits the screen. No other security tool has this vantage point
without requiring the user to change their workflow.

#### A.1 Engagement Auto-Logger

Auto-detect when security tools are running and switch to structured evidence
capture:

- **Tool detection:** Pattern-match executed commands against a known tool list
  (nmap, burpsuite, metasploit, ffuf, gobuster, sqlmap, nikto, nuclei, recon-ng,
  theHarvester, hydra, john, hashcat, wireshark/tshark, responder, crackmapexec)
- **Structured capture:** For each tool invocation, log: timestamp, command,
  raw output, parsed findings (IPs, ports, CVEs, hostnames, credentials found)
- **Evidence snippets:** Auto-extract output sections that constitute evidence
  (first/last 2000 chars per finding, linked to tool+timestamp)
- **Report generation:** Export session as Markdown/HTML pentest report with
  executive summary, tool-by-tool findings, evidence trail, and timeline
- **Hooks into:** `session_memory.rs` (already captures I/O), `ShellEvent`
  pipeline (command detection), new `SecurityAuditPlugin`

**Existing art:**
- tmux-logger (auto pipe-pane logging for pentest sessions)
- Guardian AI pentest framework (Markdown/HTML/JSON reports)
- Dradis framework (structured pentest reporting)

#### A.2 Nmap / Security Tool Output Parser

Real-time structured parsing of security tool output:

- **Nmap:** Parse text output for hosts, open ports, service versions, OS
  fingerprints. Cross-reference against NVD API for CVE lookups
- **Gobuster/ffuf:** Aggregate discovered paths, status codes, sizes into
  a structured table in a sidebar overlay
- **Hydra/john:** Track credential testing progress, found passwords
- **recon-ng/theHarvester:** Collect emails, subdomains, IPs into a
  deduplicated OSINT target list

Display parsed results in a dedicated overlay panel (new `OverlayMode::SecurityDashboard`).

**Crates:** `regex` (already in deps), `flawz` (ratatui CVE browser),
`netscanner` (ratatui network scanner)

#### A.3 CTF Helper Toolkit

Quick-access utilities in overlay popups:

- **Encoding/decoding:** Base64, hex, ROT13, URL-encode, binary, octal -- all
  accessible via hotkey or voice ("decode base64")
- **Hash identification:** Detect hash types in output (MD5, SHA-1, SHA-256,
  bcrypt, NTLM) and suggest cracking tools
- **Crypto helpers:** XOR brute-force, Caesar cipher sweep, frequency analysis
- **Binary analysis hints:** When `gdb`, `objdump`, `radare2`, or pwntools
  commands are detected, show relevant cheatsheets
- **Flag detection:** Regex for common CTF flag formats (`flag{...}`,
  `CTF{...}`, `picoCTF{...}`) -- highlight and auto-copy to clipboard

**Hooks into:** Voice macros (say "decode base64" to trigger), clipboard ring
(auto-copy flags), HUD modules (hash type indicator)

#### A.4 Network Reconnaissance HUD

Real-time network context in the status bar during security engagements:

- **Active host count:** Track discovered hosts across tool runs
- **Port summary:** Most common open ports found this session
- **Vulnerability counter:** CVEs identified, categorized by severity
- **Scope tracker:** Warn if a command targets an IP outside the defined scope

---

### B. Network & Internet Tools

#### B.1 Embedded Network Diagnostics

Leverage the Rust network tool ecosystem directly in overlay panels:

| Tool | Crate | Integration |
|---|---|---|
| Traceroute + ping graph | `trippy-tui` / `trippy-packet` | Overlay panel |
| Bandwidth per-process | `bandwhich` | HUD sparkline widget |
| Connection viewer | `rustnet` | Process-attributed connections |
| Packet sniffing | `pcap` / `pnet` | Filtered capture summaries |
| DNS lookups | `hickory-dns` (trust-dns) | Inline resolution of domains in output |
| HTTP load testing | `oha` | Request rate / latency graphs |

#### B.2 Inline Domain Intelligence

When the overlay detects a domain name or IP in PTY output:

- Offer inline DNS resolution (A, AAAA, MX, TXT records)
- WHOIS lookup summary
- GeoIP location (via `maxminddb` crate)
- Reverse DNS
- HTTP header preview (for URLs)

Trigger via hotkey while hovering over text, or voice ("look up that domain").

#### B.3 API Testing Companion

When `curl`, `wget`, `httpie`, or API client commands are detected:

- Pretty-print JSON/XML responses in the HUD
- Show HTTP status code with color-coded badge
- Parse and display response headers
- Offer to save response to file
- Measure and display response latency

**Crates:** `jsonxf` (JSON pretty-print), `serde_json` (already in deps)

#### B.4 MQTT / IoT Dashboard

For IoT development sessions:

- Subscribe to MQTT topics via `rumqttc` crate
- Display live sensor values in sparkline widgets
- Threshold alerting (value > X triggers HUD warning)
- Publish commands to devices from overlay panel
- Serial port monitoring via `serialport-rs` for embedded work

---

### C. Developer Productivity Swiss Army Knife

#### C.1 Quick-Access Utility Palette

Hotkey-triggered popup (like VS Code's command palette) with:

| Utility | Description | Voice Trigger |
|---|---|---|
| JSON prettify | Format clipboard/selection as JSON | "pretty print json" |
| Base64 encode/decode | Encode/decode selection | "encode base64" |
| JWT decode | Parse and display JWT claims | "decode jwt" |
| Timestamp convert | Unix epoch to human-readable and back | "convert timestamp" |
| UUID generate | Generate v4 UUID, copy to clipboard | "generate uuid" |
| Hash compute | MD5/SHA-1/SHA-256 of selection | "hash this" |
| URL encode/decode | Percent-encoding utilities | "url encode" |
| Color picker | Preview and convert color values (hex/rgb/hsl) | "pick color" |
| Regex tester | Test regex against sample text | "test regex" |
| Diff viewer | Side-by-side diff of two selections | "show diff" |

**Crates:** `base64`, `jsonxf`, `jwt-ui`, `pastel`, `uuid`, `sha2`/`md5`

#### C.2 Smart Output Formatting

Auto-detect structured data in command output and offer enhanced views:

- **JSON output:** Detect `{...}` in output, offer collapsible tree view
- **CSV/TSV output:** Detect delimited data, offer table view via `tabiew` patterns
- **Log output:** Detect log patterns, offer severity-filtered view
- **Diff output:** Detect unified diff format, offer syntax-highlighted side-by-side
- **Markdown output:** Render markdown in output with `termimad`

#### C.3 File Preview in Overlay

When `ls`, `find`, or file paths appear in output:

- Preview file contents on hover/hotkey (syntax-highlighted via `syntect`)
- Image preview via `ratatui-image` (sixel/kitty/iterm2 protocols)
- Markdown rendering for `.md` files
- Hex view for binary files

**Crates:** `syntect`, `ratatui-image`, `termimad`, `hexhog`

#### C.4 Git Companion Panel

Always-visible or hotkey-toggled git context:

- Current branch + ahead/behind count
- Staged/unstaged/untracked file counts
- Recent commit log (last 5)
- Diff preview for staged changes
- One-key shortcuts: stage all, commit, push, pull, stash
- Merge conflict helper (detect conflict markers, show both sides)

**Crates:** `git2` (libgit2 bindings)

#### C.5 Project Context Detector

Auto-detect project type from working directory and adapt HUD:

| File | Project Type | Adapted Features |
|---|---|---|
| `Cargo.toml` | Rust | Clippy warnings count, test results, build time |
| `package.json` | Node/JS | npm script shortcuts, dependency audit |
| `pyproject.toml` / `setup.py` | Python | venv status, pytest results |
| `Makefile` | C/C++ | Build target list, compile error count |
| `docker-compose.yml` | Docker | Container status panel |
| `Gemfile` | Ruby | Bundle status |
| `go.mod` | Go | Build/test shortcuts |

---

### D. Advanced AI Integration

#### D.1 Semantic Error Analysis

Go beyond pattern matching -- use LLM to understand errors:

- Capture full error output + surrounding context (file paths, versions, config)
- Package with project type, dependency versions, recent changes
- Query AI for: root cause analysis, fix suggestions, similar issues
- Display in scrollable overlay with copy-pasteable fix commands
- Track which AI suggestions the user applied (feedback loop)

#### D.2 Natural Language Terminal

Voice or text natural language that maps to commands:

- "show me all files changed in the last hour" -> `find . -mmin -60 -type f`
- "what's using port 3000" -> `lsof -i :3000`
- "compress this directory" -> `tar -czf archive.tar.gz ./`
- "show disk usage sorted by size" -> `du -sh * | sort -rh`

The overlay intercepts NL input (via voice or prefix like `?`), translates to
a shell command, shows preview, and executes on confirmation.

#### D.3 Auto-Documentation Generator

When the user runs a sequence of commands that forms a workflow:

- Detect workflow boundaries (same directory, related commands, short intervals)
- Generate step-by-step documentation with explanations
- Save as runbook/playbook in Markdown
- Voice trigger: "document what I just did"

#### D.4 AI Log Analyst

When `tail -f`, `kubectl logs`, `docker logs`, or `journalctl` are running:

- Maintain a rolling buffer of log lines
- Detect anomalies (error spikes, unusual patterns, latency jumps)
- Summarize log patterns in HUD ("3 connection timeouts in last 5 min")
- Voice trigger: "what's happening in the logs?"

#### D.5 AI-Powered Test Generation

After file edits detected (via `inotify`/`kqueue` or git status polling):

- Identify changed functions/methods
- Generate test stubs for new/modified code
- Display in overlay for review
- Inject into test file on approval

#### D.6 Database Query Assistant

When `psql`, `mysql`, `sqlite3`, or `mongosh` are detected:

- Accept natural language queries in the overlay
- Translate to SQL/query syntax
- Show query plan preview
- Execute on confirmation
- Display results in table format

---

### E. DevOps & System Administration

#### E.1 Container Dashboard

When Docker/Podman commands are detected, show live container panel:

- Container list with status (running/stopped/exited)
- CPU/memory per container (via `sysinfo` or Docker API)
- Log tail per container
- One-key actions: stop, restart, remove, exec shell
- Compose stack overview

**Inspiration:** lazydocker, dockyard, oxker (all ratatui-based)

#### E.2 Kubernetes Context Panel

When `kubectl` commands are detected:

- Current context/namespace in HUD
- Pod status summary (running/pending/failed counts)
- Recent events
- Log streaming for selected pod
- Port-forward management

**Inspiration:** k9s, kdash, kubetui

#### E.3 Service Health Monitor

Configurable service endpoints to poll:

- HTTP health checks with response time sparklines
- TCP port checks
- Process status (via `sysinfo`)
- Alert in HUD when service goes down
- Historical uptime percentage

#### E.4 SSH Session Manager

Overlay panel for managing SSH connections:

- Parse `~/.ssh/config` for known hosts
- Quick-connect list
- Session bookmarks (host + directory + last commands)
- Multi-host command broadcast
- SFTP file browser in overlay

**Crates:** `ssh_ui` (ratatui SSH terminal over SSH)

#### E.5 Environment Variable Manager

Interactive panel for environment management:

- View/search/filter current env vars
- Edit in overlay (inject via `export` to PTY)
- Profile switching (dev/staging/prod)
- Secret masking (detect sensitive values)
- Import/export (JSON, YAML, .env)

**Inspiration:** envx (TUI env manager)

#### E.6 Process Monitor Widget

HUD module showing child process tree stats:

- CPU and memory usage of shell and its children
- Open file descriptor count (detect leaks)
- Network connection count
- Disk I/O rate

**Crates:** `sysinfo` (cross-platform), `libproc` (macOS)

---

### F. Data & Analysis

#### F.1 Inline Data Explorer

When command output contains structured data:

- Auto-detect CSV, JSON, YAML, TOML in output
- Offer tabular view with sorting/filtering
- Column statistics (min, max, avg, count, unique)
- SQL queries against output data (via in-memory SQLite)

**Crates:** `rusqlite`, `csv`, `serde_json`, `serde_yaml`

#### F.2 Terminal Charts

Visualize data directly in the overlay:

- Sparklines for time-series data (already have ratatui `Sparkline` widget)
- Bar charts for categorical data (ratatui `BarChart`)
- Line charts for trends (ratatui `Chart`)
- Pie charts for distributions (`tui-piechart` crate)
- Histogram for frequency analysis
- Mermaid/D2 diagrams via `graphs-tui` crate

#### F.3 Pipeline Monitor

For data pipeline sessions:

- Track stages: input -> transform -> output
- Show row counts and byte sizes at each stage
- Error rate per stage
- Duration per stage
- Visual pipeline flow in overlay

---

### G. Education & Safety

#### G.1 Command Explainer

Before or after execution, explain what a command does:

- Parse command and flags using `shell-words` (already in deps)
- Look up flag meanings from embedded tldr data or man page summaries
- Display explanation in HUD: "This will recursively delete all files in /tmp"
- Voice trigger: "what does this command do?"

**Crates:** `tealdeer` (Rust tldr client), `shell-words` (already in deps)

#### G.2 Dangerous Command Guard

Intercept and warn before executing risky commands:

| Pattern | Risk Level | Action |
|---|---|---|
| `rm -rf /` or `rm -rf ~` | CRITICAL | Block + explain |
| `chmod -R 777` | HIGH | Warn + require confirmation |
| `dd if=/dev/zero of=/dev/sd*` | CRITICAL | Block |
| `:(){ :\|:& };:` (fork bomb) | CRITICAL | Block |
| `git push --force` to main | HIGH | Warn + require confirmation |
| `DROP TABLE` / `DROP DATABASE` | HIGH | Warn + require confirmation |
| `curl ... \| bash` | MEDIUM | Warn about piping to shell |
| `mkfs.*` | CRITICAL | Block unless confirmed twice |
| `kill -9 1` | CRITICAL | Block |

**Hooks into:** Existing `classify_command_policy()` in `action_audit.rs` --
already has ReadOnly/ConfirmRequired/Blocked tiers. Extend the pattern list.

#### G.3 Typo Corrector

When "command not found" is detected in output:

- Compute Levenshtein distance to known commands
- Suggest corrections: "Did you mean `docker` instead of `docekr`?"
- Offer package install: "Install with `brew install foo`?"
- Learn from user's command history for better suggestions

**Crate:** `strsim` (string similarity algorithms)

#### G.4 Interactive Learning Mode

Toggle-able learning mode that annotates everything:

- Show brief explanation of each command as it's typed
- Highlight dangerous flags in red
- Suggest more efficient alternatives ("tip: use `rg` instead of `grep -r`")
- Track commands learned vs commands looked up
- Progressive difficulty (stop annotating commands the user has used 10+ times)

---

### H. Security Hardening & Privacy

#### H.1 Secret Detection in Real-Time

Scan PTY output for leaked secrets before display:

- API keys (AWS, GCP, Azure, GitHub, Stripe patterns)
- Private keys (RSA, ECDSA headers)
- Passwords in URLs (`https://user:pass@host`)
- Connection strings with embedded credentials
- JWTs in headers or output

When detected:
- Replace with `[REDACTED-API-KEY]` in display and logs
- Flash warning in HUD
- Option to reveal with hotkey

**Pattern source:** Gitleaks rule set (400+ patterns)

#### H.2 Encrypted Session Logs

For sensitive work (pentesting, production access):

- AES-256-GCM encryption of session memory files
- Per-session encryption keys derived from user passphrase
- Tamper-evident hash chain (each entry includes hash of previous)
- Configurable retention (auto-delete after N days)

**Crates:** `aes-gcm`, `sha2`

#### H.3 Audit Trail Generation

Compliance-friendly audit logging:

- Hash-chained log entries (tamper-evident)
- Timestamp, user, command, exit code, duration
- Session correlation IDs
- Export as CSV/JSON for compliance systems
- Integration with syslog via `syslog` crate

#### H.4 Environment Leak Prevention

Before executing commands that would expose environment:

- Warn on `env`, `printenv`, `set` in shared terminals
- Detect `echo $SECRET_VAR` patterns
- Warn when `curl` headers contain hardcoded tokens
- Detect `git push` to public repos with secrets in recent commits

---

### I. Automation & Macros

#### I.1 Session Recording (asciinema Integration)

Record terminal sessions with enhanced metadata:

- Start/stop recording via hotkey or voice ("start recording")
- Embed OSC 133 command boundaries as chapters
- Add voice annotations as timestamped bookmarks
- Export as `.cast` (asciinema v3 format) for web playback
- Generate animated GIF via `agg` (Rust asciinema-to-GIF)

**Crate:** `asciinema` (Rust, rewritten in v3)

#### I.2 Workflow Macro Recorder

Record command sequences as replayable macros:

- Voice trigger: "record macro" / "stop recording" / "play macro deploy"
- Parameterize: replace specific values with `$1`, `$2` variables
- Conditional logic: retry on failure, skip on success
- Export as shell script or VoiceTerm macro format
- Store in `.voiceterm/workflows/`

**Hooks into:** Existing voice macro system (`.voiceterm/macros.yaml`) --
extend with recorded workflow macros.

#### I.3 Watch Mode

Monitor file changes and auto-execute:

- "Watch src/ and run cargo test on change"
- Uses `kqueue` (macOS) / `inotify` (Linux) via `notify` crate
- Show change summary in HUD before executing
- Debounce rapid changes
- Display test results inline

**Crate:** `notify` (cross-platform file watcher)

#### I.4 Smart Retry

When a command fails:

- Offer immediate retry
- Retry with `sudo` prefix
- Retry with modified arguments (e.g., different port)
- Exponential backoff retry for flaky commands
- Configurable retry policies per command pattern

---

### J. Collaboration

#### J.1 Shared Terminal Sessions

Expose the overlay-wrapped session for remote access:

- SSH-based sharing via `ssh_ui` crate pattern
- Read-only observer mode for mentoring/demos
- Full collaborative mode for pair programming
- Session link generation (like tmate)

#### J.2 Annotated Session Recordings

Enhanced asciinema recordings for async collaboration:

- Timestamped voice/text annotations
- Chapter markers at command boundaries
- Error highlights with explanation annotations
- Searchable transcript of all voice commands
- Export as documentation

#### J.3 Team Command Library

Shared macro/workflow library for teams:

- Git-synced `.voiceterm/team-macros/` directory
- Role-based access (dev macros, ops macros, security macros)
- Version-controlled with change history
- Voice-accessible: "run team macro deploy-staging"

---

### K. Hardware & IoT

#### K.1 Serial Port Monitor Panel

For embedded development:

- Auto-detect serial ports on USB device connect
- Live serial output in overlay panel
- Baud rate switching
- Hex/ASCII view toggle
- Log to file with timestamps

**Crates:** `serialport-rs`, `tokio-serial`

#### K.2 Firmware Flash Progress

Detect embedded tooling and show progress:

- `cargo-embed` / `probe-rs`: Show flash progress bar
- `espflash`: ESP32 flash + verify progress
- RTT (Real Time Transfer) output in dedicated panel
- Build + flash + monitor in single workflow

#### K.3 BLE/Bluetooth Scanner

For IoT development:

- Scan for nearby BLE devices
- Display GATT services and characteristics
- Subscribe to characteristic notifications
- Show data in sparkline graphs

**Crates:** `btleplug` (cross-platform BLE), `blendr` (ratatui BLE browser)

---

### L. Accessibility

#### L.1 Voice-to-Command Enhancement

Build on existing voice control for motor impairment support:

- Expanded voice macro library for common operations
- Sticky modifier key emulation ("press control" persists until "release")
- Voice-driven history navigation ("previous", "next", "run again")
- Spelling mode for precise input ("spell alpha bravo charlie")
- Voice-driven overlay navigation ("open help", "go to settings")

#### L.2 Audio Feedback System

Complement visual HUD with audio cues:

- Command success: short pleasant tone
- Command failure: distinct error tone
- Long-running command complete: notification chime
- Dangerous command warning: alert tone
- Progress indication: pitch increases with completion percentage

**Implementation:** System notification sounds via `notify-rust`, terminal bell
(`\a`) as fallback. On macOS, `NSSpeech` for spoken feedback.

#### L.3 High-Contrast & Large Text Modes

- Built-in high-contrast theme preset (our theme system supports this)
- Large text mode via `tui-big-text` (font8x8 rendering)
- Screen reader integration: expose semantic screen model via accessibility APIs
- Configurable minimum contrast ratio enforcement

---

## What We Already Have That Enables All This

Mapping back to the codebase:

| Existing Module | Enables |
|---|---|
| PTY master fd ownership (`pty_session/`) | All I/O interception, output parsing, input injection |
| VTE crate + `osc.rs` | OSC 133/633/7/52 sequence parsing |
| Event loop multiplexer (`event_loop.rs`) | Plugin event distribution, new data channels |
| ratatui HUD + row budget (`writer/`, `hud/`, `status_line/`) | All overlay panels, widgets, dashboards |
| Voice macros (`voice_macros.rs`) | Voice-triggered utilities, NL commands |
| Session memory (`session_memory.rs`) | Audit trails, engagement logs, recording |
| Memory ingestor (`memory/`) | AI context, session analytics, structured events |
| Transcript history (`transcript_history.rs`) | AI context window, session review |
| OverlayMode enum (`overlays.rs`) | New overlay panels (security, analytics, git, etc.) |
| Theme + StylePack system (`theme/`) | Accessibility themes, high-contrast modes |
| Action audit + policy tiers (`memory/action_audit.rs`) | Dangerous command guard, secret detection |
| Persistent config (`persistent_config.rs`) | New feature toggles, per-feature settings |
| `process.rs` + child PID | Process monitoring, CWD tracking |
| Crossbeam bounded channels | New data pipelines without architectural changes |
| MemoryBrowser + ActionCenter overlays | Deferred but infrastructure ready to activate |

---

## Expanded Dependency Table

| Crate | Purpose | Phase | Category |
|---|---|---|---|
| `rusqlite` | Command history + analytics | 2a | Foundation |
| `git2` | Git status, branch, diff | 2b | Dev productivity |
| `libproc` | macOS process monitoring | 2a | Foundation |
| `sysinfo` | Cross-platform process metrics | 2b | DevOps |
| `arboard` | OS clipboard access | 2d | Platform |
| `reqwest` | LLM API calls | 2c | AI |
| `base64` | OSC 52/99 + encoding utils | 2d | Platform |
| `syntect` | Syntax highlighting for previews | 2c | Dev productivity |
| `termimad` | Markdown rendering in overlay | 2c | Dev productivity |
| `strsim` | Fuzzy string matching (typo correction) | 2b | Education |
| `tealdeer` | tldr page lookups | 2b | Education |
| `notify` | File watching for auto-execute | 2d | Automation |
| `aes-gcm` | Encrypted session logs | 2d | Security |
| `sha2` | Hash computation utilities | 2c | Swiss army knife |
| `uuid` | UUID generation utility | 2c | Swiss army knife |
| `hickory-dns` | DNS resolution | 2d | Network |
| `maxminddb` | GeoIP lookups | 2d | Network |
| `serialport-rs` | Serial port monitoring | 2d | Hardware/IoT |
| `rumqttc` | MQTT client for IoT dashboard | 2d | Hardware/IoT |
| `pcap` | Packet capture for security | 2d | Security |
| `asciinema` | Session recording | 2d | Collaboration |
| `ratatui-image` | Image preview in terminal | 2d | Dev productivity |
| `graphs-tui` | Mermaid/D2 diagram rendering | 2d | Data/Analysis |
| `tui-big-text` | Large text for accessibility | 2d | Accessibility |
| `btleplug` | BLE scanning for IoT | 2d | Hardware/IoT |

---

## Revised Competitive Positioning

| Feature | Warp | Fig/Q | Copilot CLI | tmux | Zellij | VoiceTerm Phase 2 |
|---|---|---|---|---|---|---|
| Voice control | No | No | No | No | No | **Yes (core)** |
| Works with any terminal | No | Yes | Yes | Yes | Yes | **Yes** |
| PTY I/O interception | Yes | No | No | Yes | Yes | **Yes** |
| Command suggestions | Yes | Yes | Yes | No | No | Planned |
| Error explanation | Yes | No | No | No | No | Planned |
| Session analytics | No | No | No | No | No | **Planned** |
| AI context packaging | Yes | Limited | Limited | No | No | Planned |
| Plugin system | No | No | No | Shell | WASM | **Planned (Native+WASM)** |
| Desktop notifications | No | No | No | No | No | Planned |
| Clipboard ring | Basic | No | No | Yes | No | Planned |
| Security tool integration | No | No | No | No | No | **Planned** |
| CTF/pentest helpers | No | No | No | No | No | **Planned** |
| Secret detection | No | No | No | No | No | **Planned** |
| Session recording | No | No | No | No | No | Planned |
| IoT/serial monitor | No | No | No | No | No | **Planned** |
| Dangerous command guard | No | No | No | No | No | **Planned** |
| Accessibility (voice+audio) | No | No | No | No | No | **Planned** |
| Open source | No | No | No | Yes | Yes | **Yes** |

**The pitch:** VoiceTerm is the only tool that combines voice control, full PTY
interception, security tooling, AI integration, and extensibility in a single
overlay that works with any terminal. It's not replacing your terminal -- it's
making every terminal session smarter.

---

## References

**Shell Integration & Terminal Protocols:**
- [iTerm2 Shell Integration Protocol](https://gist.github.com/tep/e3f3d384de40dbda932577c7da576ec3)
- [VS Code Terminal Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration)
- [OSC 8 Hyperlinks Spec](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda)
- [Kitty Desktop Notifications](https://sw.kovidgoyal.net/kitty/desktop-notifications/)
- [Kitty Keyboard Protocol](https://sw.kovidgoyal.net/kitty/keyboard-protocol/)
- [OSC 52 Clipboard](https://sunaku.github.io/tmux-yank-osc52.html)
- [OSC 9;4 Progress Bars](https://learn.microsoft.com/en-us/windows/terminal/tutorials/progress-bar-sequences)
- [bash-preexec](https://github.com/rcaloras/bash-preexec)

**AI Terminal Tools:**
- [How Warp Works](https://www.warp.dev/blog/how-warp-works)
- [Warp Agent Mode](https://www.warp.dev/blog/agent-mode)
- [Butterfish Architecture](https://pbbakkum.com/blog/20230927/)
- [Aider Documentation](https://aider.chat/docs/)
- [2026 Guide to Coding CLI Tools](https://www.tembo.io/blog/coding-cli-tools-comparison)
- [AI Coding Tools - Agentic CLI Era](https://thenewstack.io/ai-coding-tools-in-2025-welcome-to-the-agentic-cli-era/)
- [grepai Semantic Code Search](https://yoanbernabeu.github.io/grepai/)

**Terminal Multiplexers & Plugins:**
- [Zellij Plugin System](https://zellij.dev/news/new-plugin-system/)
- [Zellij Plugin API](https://zellij.dev/documentation/plugin-api.html)
- [tmux Control Mode](https://github.com/tmux/tmux/wiki/Control-Mode)
- [Libghostty Architecture](https://mitchellh.com/writing/libghostty-is-coming)

**Security & Privacy:**
- [Gitleaks](https://github.com/gitleaks/gitleaks)
- [detect-secrets](https://github.com/Yelp/detect-secrets)
- [Guardian AI Pentest Framework](https://cybersecuritynews.com/guardian-ai-penetration-testing-tool/)
- [tmux-logger for Pentesting](https://github.com/dptsec/tmux-logger)
- [TrustedSec Workflow Improvements](https://trustedsec.com/blog/workflow-improvements-for-pentesters)

**Rust Terminal Ecosystem:**
- [Awesome Ratatui](https://github.com/ratatui/awesome-ratatui)
- [Ratatui App Showcase](https://ratatui.rs/showcase/apps/)
- [Atuin (Rust shell history)](https://github.com/atuinsh/atuin)
- [Alacritty VTE Parser](https://github.com/alacritty/vte)
- [vt100 Crate](https://docs.rs/vt100)
- [Trippy Network Diagnostic](https://crates.io/crates/trippy-tui)
- [Bandwhich Bandwidth Monitor](https://github.com/imsnif/bandwhich)
- [Tabiew Data Explorer](https://www.blog.brightcoding.dev/2025/08/12/tabiew-the-terminal-swiss-army-knife-for-csv-tsv-and-parquet-files/)
- [Asciinema v3 (Rust rewrite)](https://github.com/asciinema/asciinema)

**Process Monitoring:**
- [libproc-rs (macOS)](https://github.com/andrewdavidmackenzie/libproc-rs)
- [sysinfo Crate](https://docs.rs/sysinfo)
- [procfs Crate (Linux)](https://crates.io/crates/procfs)

**Developer Tools:**
- [navi Cheatsheet Tool](https://github.com/denisidoro/navi)
- [tldr-pages](https://github.com/tldr-pages/tldr)
- [pastel Color Tool](https://github.com/sharkdp/pastel)
- [Watchexec File Watcher](https://watchexec.github.io/)
- [probe-rs Embedded Toolset](https://probe.rs/)
- [serialport-rs](https://github.com/serialport/serialport-rs)

**Collaboration:**
- [tmate Terminal Sharing](https://tmate.io/)
- [ssh_ui (Ratatui over SSH)](https://github.com/ellenhp/ssh_ui)
- [Nex Terminal Recorder](https://nex-terminal.netlify.app/)

**Accessibility:**
- [Turbo Whisper Voice Dictation](https://github.com/knowall-ai/turbo-whisper)
- [Warp Terminal Accessibility](https://docs.warp.dev/terminal/more-features/accessibility)
