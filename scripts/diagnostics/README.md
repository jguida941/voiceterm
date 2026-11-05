# Diagnostics

Tools for capturing and replaying what VoiceTerm writes to a terminal. They
exist to pin down HUD rendering problems in IDE terminals (JetBrains, VS Code,
Cursor) from evidence instead of screenshots. None of them need a microphone
or a model.

| Tool | Purpose |
|------|---------|
| `rec.sh` | Record a VoiceTerm session with HUD debug logging |
| `ptyrec.py` | The recorder `rec.sh` uses: raw output plus a resize log |
| `replay_capture.py` | Replay a capture through a terminal emulator |
| `region_probe.sh` | Does this terminal honor a scroll region? |
| `region_probe_alt.sh` | The same probe inside the alternate screen |
| `ildl_probe.sh` | Does this terminal honor insert-line and delete-line? |
| `jetbrains_drift_harness.py` | HUD stays put while a child streams past its viewport |
| `utf8_split_harness.py` | No replacement glyphs when a repaint lands mid-character |
| `fake_claude_lines.sh`, `fake_claude_utf8.sh` | Synthetic children for the harnesses |

## Record a session

Run this from the project folder you want the backend to work in, inside the
terminal where the problem shows:

```bash
scripts/diagnostics/rec.sh claude jetbrains-claude
```

Reproduce the problem, resize if the problem involves resizing, then quit
with `Ctrl+Q`. Three files land in `~/voiceterm-captures` (override with
`VOICETERM_CAPTURE_DIR`): `<name>.bytes` is every byte the host received,
`<name>.bytes.events` lists the start size and every resize with the byte
offset it happened at, and `<name>.log` is the writer's debug log.

`ptyrec.py` forwards window resizes to the recorded program. The macOS
`script` command does not, which makes resize bugs vanish under it.

## Replay a capture

```bash
python3 -m venv .venv && .venv/bin/pip install pyte
.venv/bin/python scripts/diagnostics/replay_capture.py replay ~/voiceterm-captures/jetbrains-claude.bytes
.venv/bin/python scripts/diagnostics/replay_capture.py trace ~/voiceterm-captures/jetbrains-claude.bytes
```

`replay` prints the screen just before each resize and at the end. `trace`
prints every point where the rows holding the HUD (`--marker`, default `PTT`)
changed, with the cursor moves and line feeds in that stretch of bytes. A
difference between the replayed screen and the real terminal points at the
terminal's own behavior rather than at the bytes.

## Probe a terminal

Run the probes directly in the terminal under test and read the result line
on screen:

```bash
scripts/diagnostics/region_probe.sh
scripts/diagnostics/region_probe_alt.sh
scripts/diagnostics/ildl_probe.sh
```

JetBrains terminals (JediTerm) fail both region probes: they ignore
`DECSTBM`, which is why the writer fences the child viewport in software
there instead of relying on a scroll region.

## Harnesses

Both harnesses run a release binary against a synthetic child under a
simulated host and print a verdict, no IDE required:

```bash
cd rust && cargo build --release --bin voiceterm && cd ..
.venv/bin/python scripts/diagnostics/jetbrains_drift_harness.py rust/target/release/voiceterm
.venv/bin/python scripts/diagnostics/utf8_split_harness.py rust/target/release/voiceterm
```

The drift harness must report no child rows beyond the viewport and the HUD
on the bottom row. The UTF-8 harness must report zero replacement glyphs.
