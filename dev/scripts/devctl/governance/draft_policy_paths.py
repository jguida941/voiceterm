"""Relative-path resolution helpers for governed-markdown policy scans."""

from __future__ import annotations

from pathlib import Path


def coerce_relative_path(value: object) -> str:
    return str(value or "").strip().rstrip("/")


def configured_doc_path(
    repo_root: Path,
    *,
    configured: object,
    fallback: str = "",
    allow_missing_fallback: bool = False,
) -> str:
    candidate = coerce_relative_path(configured)
    if candidate:
        return candidate
    if not fallback:
        return ""
    if allow_missing_fallback or (repo_root / fallback).is_file():
        return fallback
    return ""


def configured_dir(
    repo_root: Path,
    *,
    configured: object,
    fallback: str = "",
) -> str:
    candidate = coerce_relative_path(configured)
    if candidate:
        return candidate
    return fallback if fallback and (repo_root / fallback).is_dir() else ""


__all__ = ["coerce_relative_path", "configured_dir", "configured_doc_path"]
