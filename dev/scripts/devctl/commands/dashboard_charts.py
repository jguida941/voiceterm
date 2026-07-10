"""Zero-dependency ASCII chart rendering for governance dashboard."""

from __future__ import annotations

_BLOCKS = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float], width: int | None = None) -> str:
    """Render a list of numeric values as a single-line Unicode sparkline.

    Each value maps to one of 8 block characters (▁..█) scaled to the
    min/max range.  If *width* is given and smaller than ``len(values)``,
    the series is down-sampled by picking evenly spaced entries.
    """
    if not values:
        return ""
    if width and len(values) > width:
        ratio = len(values) / width
        values = [values[int(i * ratio)] for i in range(width)]
    min_v, max_v = min(values), max(values)
    if max_v == min_v:
        return _BLOCKS[4] * len(values)
    scale = 7.99 / (max_v - min_v)
    return "".join(_BLOCKS[int((v - min_v) * scale)] for v in values)


def bar_chart(
    items: list[tuple[str, float]],
    max_width: int = 30,
    label_width: int = 20,
) -> str:
    """Render a horizontal bar chart with left-aligned labels.

    Each bar is scaled relative to the largest value in *items*.
    Returns a multi-line string ready for terminal or markdown output.
    """
    if not items:
        return ""
    max_val = max(v for _, v in items) or 1
    lines: list[str] = []
    for label, value in items:
        bar_len = int((value / max_val) * max_width)
        bar = "█" * bar_len
        lines.append(f"  {label:<{label_width}} {bar} {value:.0f}")
    return "\n".join(lines)


def progress_bar(fraction: float, width: int = 20) -> str:
    """Render a bracketed progress bar with percentage label.

    *fraction* should be in the 0.0..1.0 range.  Values outside that
    range are clamped.
    """
    clamped = max(0.0, min(1.0, fraction))
    filled = int(clamped * width)
    return f"[{'█' * filled}{'░' * (width - filled)}] {clamped * 100:.1f}%"
