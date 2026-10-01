"""
File operations and path utility helpers for Orion Bot.
"""

from __future__ import annotations

import os
import re
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and remove unsafe characters.
    """
    # Extract base name to strip any preceding path traversal like ../
    base = Path(filename).name
    # Remove directory separators and null bytes
    clean = re.sub(r'[/\\:\0]', '_', base)
    # Strip leading/trailing whitespaces and dots
    clean = clean.strip(". ")
    if not clean:
        clean = f"file_{int(time.time())}"
    return clean



def get_unique_filepath(directory: Path, filename: str) -> Path:
    """
    Generate a non-conflicting filepath in directory.
    If 'report.pdf' exists, tries 'report (1).pdf', 'report (2).pdf', etc.
    """
    safe_name = sanitize_filename(filename)
    target = directory / safe_name
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        candidate = directory / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def human_readable_size(size_bytes: int | float) -> str:
    """Convert raw bytes to human readable format (e.g. 12.4 MB)."""
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(size_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} PB"


def get_disk_usage(path: Path | str) -> Dict[str, str | int | float]:
    """Return total, used, free space, and usage percentage for the given filesystem path."""
    try:
        usage = shutil.disk_usage(str(path))
        used_pct = (usage.used / usage.total) * 100 if usage.total > 0 else 0
        return {
            "total": human_readable_size(usage.total),
            "used": human_readable_size(usage.used),
            "free": human_readable_size(usage.free),
            "percent": round(used_pct, 1),
            "raw_free": usage.free,
        }
    except Exception:
        return {
            "total": "Unknown",
            "used": "Unknown",
            "free": "Unknown",
            "percent": 0.0,
            "raw_free": 0,
        }


def list_directory_files(
    directory: Path,
    limit: int = 50,
) -> Tuple[List[Dict[str, str | int]], int]:
    """
    List files in directory with metadata sorted by modification time (newest first).
    Returns (list of file info dicts, total file count).
    """
    if not directory.exists() or not directory.is_dir():
        return [], 0

    entries: List[Dict[str, str | int]] = []
    total_count = 0

    try:
        all_items = sorted(
            [p for p in directory.iterdir() if p.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
        total_count = len(all_items)

        for p in all_items[:limit]:
            stat = p.stat()
            entries.append(
                {
                    "name": p.name,
                    "path": str(p),
                    "size": human_readable_size(stat.st_size),
                    "raw_size": stat.st_size,
                    "mtime": time.strftime(
                        "%Y-%m-%d %H:%M", time.localtime(stat.st_mtime)
                    ),
                }
            )
    except Exception:
        pass

    return entries, total_count


def is_path_safe(base_dir: Path, target_path: Path) -> bool:
    """
    Check if target_path is within base_dir (prevents directory traversal).
    """
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        return resolved_base in resolved_target.parents or resolved_base == resolved_target
    except Exception:
        return False
