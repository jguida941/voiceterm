"""Mutation hotspot plotting helpers."""

import math
import os
from collections import Counter
from pathlib import Path
from typing import Optional


def normalize_top_pct(value: float) -> float:
    """Normalize a percentage (0-1 or 0-100) into a 0-1 float."""
    if value <= 0:
        return 0.0
    if value > 1:
        return value / 100.0
    return min(value, 1.0)


def top_items(counter: Counter, top_pct: float) -> list[tuple[str, int]]:
    """Return the top N items based on a percentage of the list length."""
    items = counter.most_common()
    if not items:
        return []
    pct = normalize_top_pct(top_pct)
    if pct <= 0:
        return []
    count = max(1, int(math.ceil(len(items) * pct)))
    return items[:count]


def plot_hotspots(
    results, scope: str, top_pct: float, output_path: Optional[str], show: bool
) -> None:
    """Plot survived mutant hotspots (file or dir) using matplotlib."""
    if results is None:
        return
    counter = (
        results["survived_by_file"] if scope == "file" else results["survived_by_dir"]
    )
    items = top_items(counter, top_pct)
    if not items:
        print("No survived mutants to plot.")
        return

    try:
        import matplotlib

        if not os.environ.get("DISPLAY") and not os.environ.get("MPLBACKEND"):
            # Headless-friendly default for CI/sandboxed runs.
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. Install with: pip install matplotlib")
        return

    labels = [path for path, _ in items]
    values = [count for _, count in items]
    y_pos = list(range(len(labels)))

    fig_height = max(3.0, 0.4 * len(labels))
    fig, ax = plt.subplots(figsize=(10, fig_height))
    ax.barh(y_pos, values, color="#3b82f6")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Survived mutants")
    ax.set_title(f"Top {scope} hotspots (top {normalize_top_pct(top_pct) * 100:.0f}%)")
    fig.tight_layout()

    results_dir = Path(results["results_dir"])
    if output_path:
        output_file = Path(output_path)
    else:
        output_file = results_dir / f"mutants-top-{scope}.png"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    print(f"Plot saved to: {output_file}")
    if show:
        plt.show()
    plt.close(fig)
