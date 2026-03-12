"""Constants and regexes shared by process-sweep helpers."""

from __future__ import annotations

import re

from ..config import REPO_ROOT

PROCESS_SWEEP_CMD = ["ps", "-axo", "pid=,ppid=,tty=,etime=,command="]
PROCESS_CWD_LOOKUP_PREFIX = [
    "lsof",
    "-n",
    "-w",
    "-F",
    "pfn0",
    "-a",
    "-d",
    "cwd",
    "-p",
]
DEFAULT_ORPHAN_MIN_AGE_SECONDS = 60
DEFAULT_STALE_MIN_AGE_SECONDS = 600
SECONDS_PER_DAY = 24 * 60 * 60
LSOF_PID_CHUNK_SIZE = 128
BACKGROUND_TTY_VALUES = {"", "?", "??", "-"}
REPO_ROOT_RESOLVED = REPO_ROOT.resolve()

VOICETERM_TEST_BINARY_RE = re.compile(r"(?:^|/|\s)voiceterm-[0-9a-f]{8,}(?:\s|$)")
VOICETERM_CARGO_TEST_RE = re.compile(r"\bcargo\s+test\b[^\n]*(?:^|\s)--bin\s+voiceterm(?:\s|$)")
VOICETERM_STRESS_SCREEN_RE = re.compile(r"(?:^|/|\s)(?:SCREEN|screen)\s+-dmS\s+vt_hud_stress_[0-9]+(?:\s|$)")
REPO_RUNTIME_CARGO_RE = re.compile(r"\bcargo\s+(?:test|run|bench|nextest)\b")
REPO_RUNTIME_TARGET_BINARY_RE = re.compile(
    rf"{re.escape(str(REPO_ROOT_RESOLVED))}/(?:rust/)?target/(?:debug|release)/"
    r"(?:deps/[^\s/]+-[0-9a-f]{8,}|voiceterm)(?:\s|$)"
)
REPO_RUNTIME_RELATIVE_TARGET_BINARY_RE = re.compile(
    r"(?:^|[\s\"'])(?:\./)?(?:rust/)?target/(?:debug|release)/" r"(?:deps/[^\s/]+-[0-9a-f]{8,}|voiceterm)(?:\s|$)"
)
REPO_RUNTIME_COMMAND_RE = re.compile(
    rf"(?:{REPO_RUNTIME_TARGET_BINARY_RE.pattern})|" rf"(?:{REPO_RUNTIME_RELATIVE_TARGET_BINARY_RE.pattern})"
)
VOICETERM_SWEEP_TARGET_RE = re.compile(
    rf"(?:{VOICETERM_TEST_BINARY_RE.pattern})|"
    rf"(?:{VOICETERM_CARGO_TEST_RE.pattern})|"
    rf"(?:{VOICETERM_STRESS_SCREEN_RE.pattern})"
)
REPO_TOOLING_WRAPPER_RE = re.compile(
    r"(?:\bpython(?:3(?:\.\d+)?)?\s+(?:\./)?(?:dev/scripts|scripts)/[^\s\"']+)|"
    r"(?:\b(?:bash|zsh|sh)\s+(?:\./)?(?:dev/scripts|scripts)/[^\s\"']+)|"
    r"(?:\b(?:bash|zsh|sh)\s+-c[^\n]*\b(?:dev/scripts|scripts)/[^\n]+)|"
    r"(?:^|[\s\"'])(?:\./)?(?:dev/scripts|scripts)/[^\s\"']+(?:\s|$)"
)
REVIEW_CHANNEL_CONDUCTOR_SCRIPT_RE = re.compile(
    r"(?:^|[\s\"'])(?:\S+/)?(?:codex|claude)-conductor\.sh" r"(?:\s+__review_channel_inner)?(?:\s|$)"
)
REVIEW_CHANNEL_CONDUCTOR_PROMPT_RE = re.compile(
    r"You are the (?:fresh )?(?:Codex|Claude) conductor for "
    r"(?:a planned VoiceTerm markdown-bridge rollover|the active VoiceTerm "
    r"MP-355 markdown-bridge swarm)\."
)
REPO_TOOLING_CWD_CANDIDATE_RE = re.compile(
    r"(?:^|/|\s)(?:bash|zsh|sh)\s+-[^\s]*c(?:\s|$)|"
    r"(?:^|/|\s)python(?:3(?:\.\d+)?)?(?:\s|$)|"
    r"(?:^|/|\s)(?:node|npm|npx|pnpm|uv|make|just|screen|tmux|"
    r"pytest|py\.test|qemu-system-[^/\s]+)"
    r"(?:\s|$)"
)
REPO_BACKGROUND_COMMAND_RE = re.compile(
    r"^(?:python(?:3(?:\.\d+)?)?|bash|zsh|sh|cargo|rustc|qemu-system-[^/\s]+|cat|"
    r"node|npm|npx|pnpm|uv|make|just|screen|SCREEN|tmux|pytest|py\.test)$"
)
REPO_SHELL_WRAPPER_RE = re.compile(
    r"^\S*(?:bash|zsh|sh)(?:(?:\s+-[A-Za-z-]*c\b|\s+-c\b)|" r"(?:\s+\S*(?:dev/scripts/|scripts/)[^\s]+))"
)
SELF_HYGIENE_COMMAND_RE = re.compile(
    r"^(?:"
    r"(?:\S*python(?:3(?:\.\d+)?)?\s+(?:\./)?dev/scripts/devctl\.py\s+"
    r"(?:check|docs-check|hygiene)\b)|"
    r"(?:\S*(?:bash|zsh|sh)\s+-c[^\n]*\bdev/scripts/devctl\.py\s+"
    r"(?:check|docs-check|hygiene)\b)|"
    r"(?:\S*python(?:3(?:\.\d+)?)?\s+(?:\./)?dev/scripts/checks/[^\s]+\.py(?:\s|$))|"
    r"(?:\S*(?:bash|zsh|sh)\s+(?:\./)?dev/scripts/checks/[^\s]+\.py(?:\s|$))|"
    r"(?:(?:\./)?dev/scripts/checks/[^\s]+\.py(?:\s|$))"
    r")"
)
SCOPE_PRIORITY = {
    "repo_background": 1,
    "repo_tooling": 2,
    "repo_runtime": 3,
    "voiceterm": 4,
    "review_channel_conductor": 5,
}
