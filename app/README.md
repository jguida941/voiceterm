# macOS Launcher

`app/macos/VoiceTerm.app` is a lightweight Finder launcher for VoiceTerm. It
asks for a project directory and opens VoiceTerm in Terminal with that folder
as the working directory.

## Use it

1. Install VoiceTerm with Homebrew, PyPI, or `./scripts/install.sh`.
2. Double-click `app/macos/VoiceTerm.app`.
3. Choose the project folder you want Codex or Claude Code to use.

The launcher contains no separate VoiceTerm runtime; it invokes the installed
`voiceterm` command. If the app cannot find that command, verify the install
with:

```bash
command -v voiceterm
voiceterm --doctor
```

The launch script is at `app/macos/VoiceTerm.app/Contents/MacOS/launch`, and
bundle metadata is in `app/macos/VoiceTerm.app/Contents/Info.plist`.
