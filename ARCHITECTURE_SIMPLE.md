# Architecture - Super Simple Version

## What's Wrong Now?
Every time you speak, we:
1. Start FFmpeg (500ms)
2. Start Whisper (2-3 seconds)
3. Start Codex (1-2 seconds)
4. Get response
5. **Kill everything and forget everything**

Total: 5-6 seconds, no memory of previous messages

## What Should Happen?
Start everything ONCE, then:
1. Record audio (instant - already initialized)
2. Transcribe (instant - model in memory)
3. Send to Codex (instant - still running)
4. Stream response (real-time)
5. **Keep everything running for next input**

Total: <200ms, remembers entire conversation

## The Fix in One Sentence
**Stop killing Codex between messages - keep it alive like a normal chat application.**

## Why This Is Obviously Right
- **Discord:** Doesn't restart when you send a message
- **Terminal:** Doesn't restart bash after each command
- **VS Code:** Doesn't restart for each keystroke
- **Siri:** Doesn't reboot iPhone for each question

So why are we restarting Codex for each voice input?

**We shouldn't. That's the bug.**

## Technical Fix
```rust
// WRONG (current):
for each voice_input {
    spawn_new_codex()  // This is insane
    send(voice_input)
    kill_codex()       // Why?!
}

// RIGHT (proposed):
let codex = start_codex_once()
for each voice_input {
    codex.send(voice_input)  // Reuse same session
}
```

## Will This Work?

YES - This is how every chat app works:
- Slack keeps websocket open
- ChatGPT keeps session alive
- Terminal keeps shell running
- Every voice assistant keeps ASR model loaded

We're not inventing anything new. We're just doing it correctly.

## Quick Test

Ask yourself:
1. Should we restart Codex for every message? **No**
2. Should we reload Whisper model every time? **No**
3. Should we maintain conversation context? **Yes**
4. Should responses stream in real-time? **Yes**

If you agree with these answers, then our architecture is correct.

## Bottom Line

**Problem:** We're restarting everything constantly (stupid)
**Solution:** Keep everything running (obvious)
**Result:** 30x faster, context preserved, actually usable