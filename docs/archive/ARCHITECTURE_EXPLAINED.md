# Architecture Breakdown - Simple Explanation

## The Problem We're Solving

### Current Broken Approach
```
User speaks → New FFmpeg process → New Whisper process → New Codex process → Response → Everything dies
User speaks again → New FFmpeg → New Whisper → New Codex → Response → Everything dies
[Repeat forever, each time losing context and taking 5-6 seconds]
```

**Why this is wrong:**
- Spawning 3 new processes every time = SLOW (5-6 seconds)
- Codex loses all context between messages
- Can't see what Codex is doing (no streaming)
- Terminal gets corrupted by subprocess output
- Enter key breaks because of event queue pollution

## The Correct Solution

### Core Principle
**Codex is the main app. We're just a voice input method.**

Think of it like this:
- Codex = Microsoft Word
- Our tool = Speech-to-text keyboard
- We shouldn't restart Word every time you speak!

### The Right Architecture

```
START ONCE:
1. Launch Codex (keep it running forever)
2. Load Whisper model (keep it in memory)
3. Initialize audio device (keep it ready)

THEN LOOP:
User presses Ctrl+R → Capture audio → Transcribe → Send to SAME Codex → Stream response
User presses Ctrl+R → Capture audio → Transcribe → Send to SAME Codex → Stream response
[Codex remembers everything, instant responses]
```

## Technical Implementation (3 Layers)

### Layer 1: Persistent Codex Session
```rust
// Start Codex ONCE
let codex = CodexSession::start();

// Keep using the SAME session
codex.send("Create a file");     // Codex creates file
codex.send("Edit that file");    // Codex knows which file!
codex.send("Run it");            // Still same context
```

**Benefits:**
- No startup delay
- Maintains context/approvals
- Can see tool usage in real-time

### Layer 2: Voice Service (Always Ready)
```rust
// Load Whisper model ONCE at startup
let voice_service = VoiceService::new("whisper-model.bin");

// Reuse for every capture
let text = voice_service.capture_and_transcribe(); // <100ms
```

**Benefits:**
- Model loaded once (not every time)
- Audio device initialized once
- Near-instant transcription

### Layer 3: Smart TUI
```rust
// The UI just connects the pieces
loop {
    if user_presses_ctrl_r() {
        let text = voice_service.capture();    // Fast (model loaded)
        codex.send(text);                      // Fast (session alive)
        ui.stream(codex.output);               // Real-time display
    }
}
```

## Why Pure Rust?

### Current Stack (Slow)
- Python script → calls FFmpeg binary → calls Whisper binary → calls Codex
- Each step = process spawn, startup time, IPC overhead

### Rust Stack (Fast)
- Single binary with everything compiled in
- Direct audio capture (no FFmpeg)
- Whisper as library (no subprocess)
- Zero-copy buffers
- SIMD optimizations
- One process, multiple threads

**Speed comparison:**
- Current: 5-6 seconds per interaction
- Rust goal: <200ms per interaction
- That's 25-30x faster!

## The Features This Enables

### Immediate (Phase 1)
1. **Persistent sessions** - Codex stays alive
2. **Streaming output** - See responses as they generate
3. **Context preservation** - Multi-turn conversations
4. **Tool access** - Full Codex capabilities

### Advanced (Phase 2)
1. **Wake word** - "Hey Codex" hands-free activation
2. **Voice commands** - "scroll down", "clear input"
3. **Auto-stop** - Stop recording when you stop talking
4. **Real-time transcription** - See text as you speak
5. **Noise cancellation** - Works in noisy environments

### Future (Phase 3)
1. **Multi-language** - Speak in any language
2. **Speaker recognition** - Multiple users
3. **Context awareness** - Project-specific vocabulary
4. **GPU acceleration** - For large models

## Is This The Right Track?

### YES, because:

✅ **Matches Codex's design** - We're working WITH Codex, not against it
✅ **Industry standard** - This is how Siri/Alexa/Assistant work
✅ **Massive speed gain** - 25-30x faster
✅ **Better UX** - Streaming, context, no crashes
✅ **Single binary** - Easy distribution
✅ **Extensible** - Can add features without breaking core

### The Alternative (Current Approach) Fails Because:

❌ **Fighting Codex** - Forcing it to restart constantly
❌ **Architecturally wrong** - Like restarting your browser for each click
❌ **Unfixably slow** - Process spawning overhead can't be optimized away
❌ **Poor UX** - No streaming, lost context, crashes

## Simple Analogy

### Current (Wrong) Approach:
Like hiring a new translator every time you say a sentence, and they have to:
1. Learn your language from scratch
2. Boot up their computer
3. Forget everything after one sentence
4. Get fired and replaced

### Correct Approach:
Like having a dedicated translator who:
1. Stays with you all day
2. Remembers your conversation
3. Gets faster as they learn your patterns
4. Provides real-time translation

## The Ask

**Is this the right architecture?**

Key decisions to validate:
1. Keep Codex alive in a PTY session ✓
2. Use Rust for performance ✓
3. Load models once, reuse forever ✓
4. Stream everything in real-time ✓
5. Single binary distribution ✓

**What we're NOT doing:**
- Not changing Codex itself
- Not creating a Codex alternative
- Not adding unnecessary complexity
- Not requiring special setup

This is a thin, fast voice layer on top of standard Codex.

## Implementation Priority

1. **First:** Get persistent Codex session working (fixes main issues)
2. **Second:** Replace subprocess calls with libraries (massive speedup)
3. **Third:** Add smart features (VAD, wake word, etc.)
4. **Fourth:** Package and distribute (Homebrew, etc.)

Each phase delivers value, but Phase 1 alone fixes 80% of current problems.

## Summary for AI Review

**Current:** Every voice input spawns 3 processes, loses context, takes 5-6 seconds
**Proposed:** One persistent session, instant responses, maintains context
**Technology:** Pure Rust, zero-copy audio, streaming transcription
**Result:** 25-30x speed improvement, proper Codex integration, better UX

The architecture follows standard practices from voice assistants and terminal multiplexers. It's not inventing new patterns, just applying proven ones correctly.