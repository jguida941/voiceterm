"""Core scanning logic for IDE/provider isolation guard."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
SOURCE_ROOTS = (
    REPO_ROOT / "rust" / "src" / "bin" / "voiceterm",
    REPO_ROOT / "rust" / "src" / "ipc",
)

HOST_PATTERNS = (
    re.compile(r"\bTerminalHost\b"),
    re.compile(r"\bTerminalFamily\b"),
    re.compile(r"\bJetBrains\b"),
    re.compile(r"\bCursor\b"),
    re.compile(r"\bruntime_compat::detect_terminal_host\b"),
    re.compile(r"\bis_jetbrains_terminal\b"),
    re.compile(r"\bis_cursor_terminal\b"),
)
PROVIDER_LABEL_PATTERN = r"(?:claude|codex|gemini|aider|opencode|custom)"
PROVIDER_PATTERNS = (
    re.compile(r"\bBackendFamily\b"),
    re.compile(r"\bProvider::"),
    re.compile(r"\bProviderId\b"),
    re.compile(
        rf"\b(?:{PROVIDER_LABEL_PATTERN})_backend(?:_label)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bis_(?:{PROVIDER_LABEL_PATTERN})_backend(?:_label)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:provider|backend)(?:_label|_name|_id)?\b[^\n]{{0,80}}(?:==|!=|eq_ignore_ascii_case\(|matches!\()[^\n]{{0,80}}\"{PROVIDER_LABEL_PATTERN}\"",
        re.IGNORECASE,
    ),
)

ALLOWLISTED_MIXED_PATH_PREFIXES = ()
ALLOWLISTED_MIXED_PATHS = (
    "rust/src/bin/voiceterm/runtime_compat.rs",
    "rust/src/bin/voiceterm/writer/state/profile.rs",
    "rust/src/bin/voiceterm/writer/timing.rs",
)
ALLOWLISTED_FILE_SIGNAL_PATHS = (
    "rust/src/bin/voiceterm/runtime_compat.rs",
    "rust/src/bin/voiceterm/writer/state/profile.rs",
    "rust/src/bin/voiceterm/writer/timing.rs",
    "rust/src/bin/voiceterm/event_loop.rs",
    "rust/src/bin/voiceterm/event_loop/periodic_tasks.rs",
    "rust/src/bin/voiceterm/writer/state.rs",
    "rust/src/bin/voiceterm/writer/state/dispatch.rs",
)
USE_STATEMENT_PATTERN = re.compile(r"^(?:pub(?:\([^)]*\))?\s+)?use\s+")
LOCAL_BINDING_PATTERN = re.compile(
    r"\blet\s+(?:mut\s+)?([A-Za-z_][A-Za-z0-9_]*)\b[^=]*=\s*(.+)"
)
CFG_ATTRIBUTE_PATTERN = re.compile(r"^#\s*\[\s*cfg\s*\((?P<expr>.*)\)\s*\]\s*$")


def _is_test_source_path(relative_path: str) -> bool:
    normalized = f"/{relative_path}/"
    name = Path(relative_path).name
    return "/tests/" in normalized or name == "tests.rs" or name.endswith("_test.rs")


def _iter_source_paths() -> list[Path]:
    paths: set[Path] = set()
    for source_root in SOURCE_ROOTS:
        if not source_root.exists():
            continue
        for path in source_root.rglob("*.rs"):
            if "target" in path.parts:
                continue
            paths.add(path)
    return sorted(paths)


def _is_allowlisted_mixed_path(relative_path: str) -> bool:
    return relative_path in ALLOWLISTED_MIXED_PATHS or any(
        relative_path == prefix or relative_path.startswith(prefix)
        for prefix in ALLOWLISTED_MIXED_PATH_PREFIXES
    )


def _is_allowlisted_file_signal_path(relative_path: str) -> bool:
    return relative_path in ALLOWLISTED_FILE_SIGNAL_PATHS or _is_allowlisted_mixed_path(
        relative_path
    )


def _strip_inline_comment(raw_line: str) -> str:
    return raw_line.split("//", 1)[0].strip()


def _contains_any_identifier(raw_line: str, identifiers: set[str]) -> bool:
    if not identifiers:
        return False
    return any(
        re.search(rf"\b{re.escape(identifier)}\b", raw_line)
        for identifier in identifiers
    )


def _is_cfg_test_only_attribute(line: str) -> bool:
    match = CFG_ATTRIBUTE_PATTERN.match(line)
    if not match:
        return False
    expression = match.group("expr")
    if re.search(r"\bnot\s*\(\s*test\s*\)", expression):
        return False
    if re.sub(r"\s+", "", expression).startswith("not("):
        return False
    return re.search(r"\btest\b", expression) is not None


def _statement_ends(line: str) -> bool:
    return line.endswith(";") or line.endswith("{") or line.endswith("}")


def _scan_text(relative_path: str, text: str) -> dict:
    host_hits = 0
    provider_hits = 0
    mixed_line_numbers: list[int] = []
    host_binding_names: set[str] = set()
    provider_binding_names: set[str] = set()
    statement_start: int | None = None
    statement_has_host_signal = False
    statement_has_provider_signal = False
    in_use_statement = False
    pending_cfg_test = False
    skip_cfg_test_depth = 0

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_inline_comment(raw_line)
        if not line:
            continue

        if skip_cfg_test_depth > 0:
            skip_cfg_test_depth += line.count("{") - line.count("}")
            if skip_cfg_test_depth <= 0:
                skip_cfg_test_depth = 0
            continue

        if _is_cfg_test_only_attribute(line):
            pending_cfg_test = True
            continue

        if pending_cfg_test:
            if line.startswith("#["):
                continue
            if "{" in line:
                skip_cfg_test_depth = line.count("{") - line.count("}")
                pending_cfg_test = False
                if skip_cfg_test_depth <= 0:
                    skip_cfg_test_depth = 0
                continue
            if line.endswith(";"):
                pending_cfg_test = False
                continue
            continue

        if in_use_statement:
            if ";" in line:
                in_use_statement = False
            continue
        if USE_STATEMENT_PATTERN.match(line):
            in_use_statement = ";" not in line
            continue

        has_host_signal_direct = any(pattern.search(line) for pattern in HOST_PATTERNS)
        has_provider_signal_direct = any(
            pattern.search(line) for pattern in PROVIDER_PATTERNS
        )
        has_host_signal = has_host_signal_direct or _contains_any_identifier(
            line, host_binding_names
        )
        has_provider_signal = has_provider_signal_direct or _contains_any_identifier(
            line, provider_binding_names
        )
        if has_host_signal:
            host_hits += 1
        if has_provider_signal:
            provider_hits += 1

        if statement_start is None:
            statement_start = lineno
            statement_has_host_signal = False
            statement_has_provider_signal = False
        statement_has_host_signal = statement_has_host_signal or has_host_signal
        statement_has_provider_signal = (
            statement_has_provider_signal or has_provider_signal
        )

        if not _statement_ends(line):
            continue
        if statement_has_host_signal and statement_has_provider_signal:
            mixed_line_numbers.append(statement_start)
        statement_start = None
        statement_has_host_signal = False
        statement_has_provider_signal = False

        binding_match = LOCAL_BINDING_PATTERN.search(line)
        if binding_match:
            binding_name = binding_match.group(1)
            binding_expr = binding_match.group(2)
            binding_has_host_signal = (
                has_host_signal_direct
                or _contains_any_identifier(binding_expr, host_binding_names)
            )
            binding_has_provider_signal = (
                has_provider_signal_direct
                or _contains_any_identifier(binding_expr, provider_binding_names)
            )
            if binding_has_host_signal:
                host_binding_names.add(binding_name)
            if binding_has_provider_signal:
                provider_binding_names.add(binding_name)

    if (
        statement_start is not None
        and statement_has_host_signal
        and statement_has_provider_signal
    ):
        mixed_line_numbers.append(statement_start)

    return {
        "file": relative_path,
        "host_signal_lines": host_hits,
        "provider_signal_lines": provider_hits,
        "mixed_signal_lines": len(mixed_line_numbers),
        "mixed_line_numbers": mixed_line_numbers,
        "file_signal_coupling": host_hits > 0 and provider_hits > 0,
    }
