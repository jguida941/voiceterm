# Codex Voice 🎤

Voice interface for Anthropic's Codex CLI. Speak naturally to code.

## Quick Start

```bash
# Install and run
git clone https://github.com/jguida941/codex-voice.git
cd codex-voice
./voice

# Custom recording duration
./voice -s 15  # 15 seconds
```

## How It Works

1. Press `Ctrl+R` to start recording
2. Speak your command
3. Press `Enter` to send to Codex
4. Get response

## Documentation

See **[MASTER_DOC.md](MASTER_DOC.md)** for:
- Installation instructions
- Architecture details
- Testing guide
- Troubleshooting
- Development roadmap

## Current Status

- ✅ Voice capture working
- ✅ Codex integration working
- 🚧 Persistent sessions (implemented, needs testing)
- 📋 Performance optimizations (planned)

## Requirements

- macOS (Linux/Windows coming)
- FFmpeg
- OpenAI Whisper
- Codex CLI
- Rust (for building)
