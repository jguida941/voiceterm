#!/usr/bin/env python3
"""Stable entrypoint for checked extraction-plan artifact claims."""

from guardir_extraction_plan_artifacts.command import build_report, main


if __name__ == "__main__":
    raise SystemExit(main())
