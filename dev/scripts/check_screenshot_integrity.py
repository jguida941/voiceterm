"""Validate markdown image references and report stale screenshot age."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOC_GLOBS = (
    "README.md",
    "QUICK_START.md",
    "DEV_INDEX.md",
    "guides/*.md",
    "dev/README.md",
    "scripts/README.md",
    "pypi/README.md",
    "app/README.md",
)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
HTML_IMAGE_RE = re.compile(r"""<img\s+[^>]*src=["']([^"']+)["']""", re.IGNORECASE)


def _resolve_doc_paths(patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        for candidate in REPO_ROOT.glob(pattern):
            if candidate.is_file():
                paths.add(candidate)
    return sorted(paths)


def _normalize_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target:
        target = target.split(" ", 1)[0]
    return target.strip()


def _is_remote_or_ignored(target: str) -> bool:
    lowered = target.lower()
    return (
        lowered.startswith(("http://", "https://", "data:", "mailto:"))
        or target.startswith("#")
        or not target
    )


def _collect_image_targets(doc_path: Path) -> list[str]:
    text = doc_path.read_text(encoding="utf-8")
    raw_targets = MD_IMAGE_RE.findall(text) + HTML_IMAGE_RE.findall(text)
    return [_normalize_target(target) for target in raw_targets]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check markdown image references and optional screenshot staleness."
    )
    parser.add_argument(
        "--docs",
        nargs="*",
        default=list(DEFAULT_DOC_GLOBS),
        help="Markdown glob patterns to scan (repo-relative).",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=0,
        help="Report referenced image files older than this many days (0 disables).",
    )
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit non-zero when stale image references are detected.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    docs = _resolve_doc_paths(args.docs)
    if not docs:
        print("error: no markdown files matched requested --docs patterns", file=sys.stderr)
        return 2

    missing_refs: list[dict[str, str]] = []
    image_to_docs: dict[Path, set[Path]] = defaultdict(set)
    refs_checked = 0

    for doc_path in docs:
        try:
            targets = _collect_image_targets(doc_path)
        except OSError as error:
            print(f"error reading {doc_path}: {error}", file=sys.stderr)
            return 2

        for raw_target in targets:
            if _is_remote_or_ignored(raw_target):
                continue
            refs_checked += 1
            resolved = (doc_path.parent / raw_target).resolve()
            if not resolved.exists():
                missing_refs.append(
                    {
                        "doc": str(doc_path.relative_to(REPO_ROOT)),
                        "target": raw_target,
                    }
                )
                continue
            if resolved.suffix.lower() in IMAGE_EXTENSIONS and resolved.is_file():
                image_to_docs[resolved].add(doc_path)

    stale_refs: list[dict[str, object]] = []
    if args.stale_days > 0:
        now = datetime.now(timezone.utc).timestamp()
        for image_path in sorted(image_to_docs):
            age_days = int((now - image_path.stat().st_mtime) // 86400)
            if age_days >= args.stale_days:
                stale_refs.append(
                    {
                        "image": str(image_path.relative_to(REPO_ROOT)),
                        "age_days": age_days,
                        "referenced_by": sorted(
                            str(path.relative_to(REPO_ROOT)) for path in image_to_docs[image_path]
                        ),
                    }
                )

    ok = not missing_refs and (not args.fail_on_stale or not stale_refs)
    report = {
        "ok": ok,
        "docs_scanned": [str(path.relative_to(REPO_ROOT)) for path in docs],
        "docs_scanned_count": len(docs),
        "references_checked": refs_checked,
        "missing_references": missing_refs,
        "stale_days_threshold": args.stale_days,
        "stale_references": stale_refs,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print("# check_screenshot_integrity")
        print(f"- ok: {ok}")
        print(f"- docs_scanned: {len(docs)}")
        print(f"- references_checked: {refs_checked}")
        print(f"- missing_references: {len(missing_refs)}")
        if missing_refs:
            for item in missing_refs:
                print(f"  - {item['doc']} -> {item['target']}")
        if args.stale_days > 0:
            print(f"- stale_days_threshold: {args.stale_days}")
            print(f"- stale_references: {len(stale_refs)}")
            for item in stale_refs:
                print(
                    "  - "
                    + f"{item['image']} ({item['age_days']} days) referenced_by="
                    + ", ".join(item["referenced_by"])
                )
        else:
            print("- stale_days_threshold: disabled")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
