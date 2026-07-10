"""Halstead software metrics computation for Python and Rust source files.

Uses Python's stdlib ``tokenize`` for Python files and a regex-based
token scanner for Rust files.  No external dependencies required.

Halstead primitives:
    n1 = distinct operators,  N1 = total operators
    n2 = distinct operands,   N2 = total operands
    vocabulary  n  = n1 + n2
    length      N  = N1 + N2
    volume      V  = N * log2(n)
    difficulty  D  = (n1 / 2) * (N2 / n2)
    effort      E  = D * V
    bugs        B  = V / 3000
    MI = max(0, (171 - 5.2*ln(V) - 0.23*CC - 16.2*ln(LOC)) * 100/171)
"""

from __future__ import annotations

import io
import math
import re
import tokenize as _tokenize
from collections import Counter
from pathlib import Path

from .models import HalsteadFileMetrics, HalsteadSummary

# -- Python token classification ---------------------------------------------
_PYTHON_OPERATORS = frozenset(
    {
        "+", "-", "*", "**", "/", "//", "%", "@",
        "<<", ">>", "&", "|", "^", "~",
        ":=", "<", ">", "<=", ">=", "==", "!=",
        "(", ")", "[", "]", "{", "}",
        ",", ":", ".", ";", "=", "->",
        "+=", "-=", "*=", "@=", "/=", "//=", "%=",
        "&=", "|=", "^=", ">>=", "<<=", "**=",
    }
)

_PYTHON_KEYWORDS_OPERATORS = frozenset(
    {
        "and", "or", "not", "in", "is", "lambda",
        "if", "else", "elif", "for", "while", "with",
        "try", "except", "finally", "raise", "assert",
        "import", "from", "as", "pass", "break", "continue",
        "return", "yield", "del", "global", "nonlocal",
        "class", "def", "async", "await",
    }
)


def _classify_python_tokens(
    source: str,
) -> tuple[Counter[str], Counter[str], int, int]:
    """Classify Python source tokens into operators and operands.

    Returns (operators, operands, loc, cyclomatic_complexity).
    """
    operators: Counter[str] = Counter()
    operands: Counter[str] = Counter()
    loc = 0
    cc = 1  # base path
    seen_lines: set[int] = set()

    cc_keywords = {"if", "elif", "for", "while", "except", "and", "or"}

    try:
        tokens = list(_tokenize.generate_tokens(io.StringIO(source).readline))
    except _tokenize.TokenError:
        return operators, operands, max(1, source.count("\n")), 1

    for tok in tokens:
        if tok.type in (_tokenize.COMMENT, _tokenize.NL, _tokenize.NEWLINE,
                        _tokenize.INDENT, _tokenize.DEDENT, _tokenize.ENCODING,
                        _tokenize.ENDMARKER):
            continue

        seen_lines.add(tok.start[0])

        if tok.type == _tokenize.OP:
            operators[tok.string] += 1
        elif tok.type == _tokenize.NAME:
            if tok.string in _PYTHON_KEYWORDS_OPERATORS:
                operators[tok.string] += 1
                if tok.string in cc_keywords:
                    cc += 1
            else:
                operands[tok.string] += 1
        elif tok.type in (_tokenize.NUMBER, _tokenize.STRING):
            operands[tok.string] += 1

    loc = len(seen_lines) or max(1, source.count("\n"))
    return operators, operands, loc, cc


# -- Rust token classification -----------------------------------------------

_RUST_OPERATOR_RE = re.compile(
    r"(->|=>|::|&&|\|\||<<|>>|[+\-*/%&|^~!<>=]=?|[(){}\[\],;:.?@#])"
)
_RUST_KEYWORD_OPERATORS = frozenset(
    {
        "as", "async", "await", "break", "continue", "else", "enum",
        "extern", "fn", "for", "if", "impl", "in", "let", "loop",
        "match", "mod", "move", "mut", "pub", "ref", "return",
        "self", "static", "struct", "trait", "type", "unsafe",
        "use", "where", "while", "yield",
    }
)
_RUST_CC_KEYWORDS = frozenset(
    {"if", "else", "for", "while", "loop", "match", "&&", "||", "?"}
)
_RUST_IDENT_RE = re.compile(r"[a-zA-Z_]\w*")
_RUST_NUMBER_RE = re.compile(
    r"0[xXoObB][0-9a-fA-F_]+|[0-9][0-9_]*(?:\.[0-9_]+)?(?:[eE][+-]?[0-9_]+)?(?:f32|f64|u8|u16|u32|u64|u128|usize|i8|i16|i32|i64|i128|isize)?"
)
_RUST_STRING_RE = re.compile(r'b?"(?:[^"\\]|\\.)*"|b?r#*".*?"#*', re.DOTALL)
_RUST_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)


def _classify_rust_tokens(
    source: str,
) -> tuple[Counter[str], Counter[str], int, int]:
    """Classify Rust source tokens into operators and operands."""
    operators: Counter[str] = Counter()
    operands: Counter[str] = Counter()
    cc = 1

    cleaned = _RUST_COMMENT_RE.sub(" ", source)
    cleaned = _RUST_STRING_RE.sub("STR_LIT", cleaned)

    loc = sum(1 for line in cleaned.splitlines() if line.strip())
    loc = max(1, loc)

    pos = 0
    text = cleaned
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue

        op_match = _RUST_OPERATOR_RE.match(text, pos)
        if op_match:
            op = op_match.group(1)
            operators[op] += 1
            if op in _RUST_CC_KEYWORDS:
                cc += 1
            pos = op_match.end()
            continue

        num_match = _RUST_NUMBER_RE.match(text, pos)
        if num_match:
            operands[num_match.group()] += 1
            pos = num_match.end()
            continue

        ident_match = _RUST_IDENT_RE.match(text, pos)
        if ident_match:
            word = ident_match.group()
            if word in _RUST_KEYWORD_OPERATORS:
                operators[word] += 1
                if word in _RUST_CC_KEYWORDS:
                    cc += 1
            elif word != "STR_LIT":
                operands[word] += 1
            else:
                operands[word] += 1
            pos = ident_match.end()
            continue

        pos += 1

    return operators, operands, loc, cc


# -- Halstead formulas -------------------------------------------------------

def _halstead_metrics(
    operators: Counter[str],
    operands: Counter[str],
    loc: int,
    cc: int,
    *,
    path: str,
    language: str,
) -> HalsteadFileMetrics:
    """Compute Halstead metrics from classified token counts."""
    n1 = len(operators)
    n2 = max(1, len(operands))
    big_n1 = sum(operators.values())
    big_n2 = sum(operands.values())
    vocabulary = n1 + n2
    program_length = big_n1 + big_n2

    volume = program_length * math.log2(max(2, vocabulary))
    difficulty = (n1 / 2.0) * (big_n2 / max(1, n2))
    effort = difficulty * volume
    estimated_bugs = volume / 3000.0

    # Classic Maintainability Index (SEI formula, normalized 0-100)
    ln_v = math.log(max(1.0, volume))
    ln_loc = math.log(max(1, loc))
    raw_mi = 171.0 - 5.2 * ln_v - 0.23 * cc - 16.2 * ln_loc
    mi = max(0.0, min(100.0, raw_mi * 100.0 / 171.0))

    return HalsteadFileMetrics(
        path=path,
        language=language,
        loc=loc,
        n1=n1,
        n2=n2,
        big_n1=big_n1,
        big_n2=big_n2,
        vocabulary=vocabulary,
        program_length=program_length,
        volume=round(volume, 2),
        difficulty=round(difficulty, 2),
        effort=round(effort, 2),
        estimated_bugs=round(estimated_bugs, 3),
        maintainability_index=round(mi, 2),
    )


# -- Public API --------------------------------------------------------------

def analyze_file(
    path: Path,
    *,
    relative_to: Path | None = None,
) -> HalsteadFileMetrics | None:
    """Compute Halstead metrics for a single Python or Rust source file.

    When *relative_to* is given, ``path`` is stored as a repo-relative
    POSIX string so that artifact JSON stays portable across machines.
    """
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    suffix = path.suffix.lower()
    if suffix == ".py":
        operators, operands, loc, cc = _classify_python_tokens(source)
        language = "python"
    elif suffix == ".rs":
        operators, operands, loc, cc = _classify_rust_tokens(source)
        language = "rust"
    else:
        return None

    if not operators and not operands:
        return None

    display_path = str(path)
    if relative_to is not None:
        try:
            display_path = path.resolve().relative_to(
                relative_to.resolve()
            ).as_posix()
        except ValueError:
            pass

    return _halstead_metrics(
        operators, operands, loc, cc,
        path=display_path, language=language,
    )


def analyze_directory(
    root: Path,
    *,
    extensions: tuple[str, ...] = (".py", ".rs"),
    exclude_patterns: tuple[str, ...] = ("__pycache__", ".git", "target", "node_modules"),
    max_files: int = 5000,
) -> list[HalsteadFileMetrics]:
    """Scan a directory tree and return Halstead metrics for each source file."""
    results: list[HalsteadFileMetrics] = []
    count = 0
    for ext in extensions:
        for path in sorted(root.rglob(f"*{ext}")):
            if count >= max_files:
                break
            if any(part in exclude_patterns for part in path.parts):
                continue
            metrics = analyze_file(path, relative_to=root)
            if metrics is not None:
                results.append(metrics)
                count += 1
    return results


def summarize_halstead(file_metrics: list[HalsteadFileMetrics]) -> HalsteadSummary:
    """Aggregate per-file Halstead metrics into a repo-level summary."""
    if not file_metrics:
        return HalsteadSummary(
            files_scanned=0,
            total_loc=0,
            avg_volume=0.0,
            avg_difficulty=0.0,
            avg_effort=0.0,
            avg_maintainability_index=0.0,
            estimated_total_bugs=0.0,
            by_language={},
        )

    total_loc = sum(m.loc for m in file_metrics)
    avg_volume = sum(m.volume for m in file_metrics) / len(file_metrics)
    avg_difficulty = sum(m.difficulty for m in file_metrics) / len(file_metrics)
    avg_effort = sum(m.effort for m in file_metrics) / len(file_metrics)
    avg_mi = sum(m.maintainability_index for m in file_metrics) / len(file_metrics)
    total_bugs = sum(m.estimated_bugs for m in file_metrics)

    by_language: dict[str, list[HalsteadFileMetrics]] = {}
    for m in file_metrics:
        by_language.setdefault(m.language, []).append(m)

    lang_summary: dict[str, dict[str, float]] = {}
    for lang, files in sorted(by_language.items()):
        lang_summary[lang] = dict((
            ("files_scanned", float(len(files))),
            ("total_loc", float(sum(f.loc for f in files))),
            ("avg_volume", round(sum(f.volume for f in files) / len(files), 2)),
            ("avg_difficulty", round(sum(f.difficulty for f in files) / len(files), 2)),
            ("avg_maintainability_index", round(
                sum(f.maintainability_index for f in files) / len(files), 2,
            )),
            ("estimated_bugs", round(sum(f.estimated_bugs for f in files), 3)),
        ))

    return HalsteadSummary(
        files_scanned=len(file_metrics),
        total_loc=total_loc,
        avg_volume=round(avg_volume, 2),
        avg_difficulty=round(avg_difficulty, 2),
        avg_effort=round(avg_effort, 2),
        avg_maintainability_index=round(avg_mi, 2),
        estimated_total_bugs=round(total_bugs, 3),
        by_language=lang_summary,
    )
