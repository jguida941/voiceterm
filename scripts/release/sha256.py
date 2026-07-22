#!/usr/bin/env python3
"""Write a sha256 checksum sidecar file for a release artifact."""

import argparse
import hashlib
from pathlib import Path


def compute_sha256(path: Path) -> str:
    """Compute sha256 digest for one file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checksum_file(input_path: Path, output_path: Path) -> None:
    """Write '<hex>  <filename>' checksum file."""
    digest = compute_sha256(input_path)
    output_path.write_text(f"{digest}  {input_path.name}\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Artifact path")
    parser.add_argument("--output", default="", help="Checksum output path (default: <input>.sha256)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else Path(f"{args.input}.sha256")
    write_checksum_file(input_path, output_path)
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
