"""
Unit tests for bot/utils/file_ops.py.
"""

from pathlib import Path
from bot.utils.file_ops import (
    get_disk_usage,
    get_unique_filepath,
    human_readable_size,
    is_path_safe,
    list_directory_files,
    sanitize_filename,
)


def test_sanitize_filename() -> None:
    assert sanitize_filename("safe_file.txt") == "safe_file.txt"
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("file:name?.mp4") == "file_name?.mp4"
    assert sanitize_filename("   spaced_file.pdf   ") == "spaced_file.pdf"
    assert sanitize_filename("...dots...") == "dots"
    # Empty string should fallback to generated name
    assert sanitize_filename("").startswith("file_")


def test_get_unique_filepath(tmp_path: Path) -> None:
    # First file
    f1 = get_unique_filepath(tmp_path, "sample.txt")
    assert f1.name == "sample.txt"
    f1.write_text("first")

    # Second file with same name
    f2 = get_unique_filepath(tmp_path, "sample.txt")
    assert f2.name == "sample (1).txt"
    f2.write_text("second")

    # Third file
    f3 = get_unique_filepath(tmp_path, "sample.txt")
    assert f3.name == "sample (2).txt"


def test_human_readable_size() -> None:
    assert human_readable_size(0) == "0 B"
    assert human_readable_size(512) == "512 B"
    assert human_readable_size(1024) == "1.00 KB"
    assert human_readable_size(1024 * 1024) == "1.00 MB"
    assert human_readable_size(1572864) == "1.50 MB"
    assert human_readable_size(1024 * 1024 * 1024) == "1.00 GB"


def test_get_disk_usage(tmp_path: Path) -> None:
    usage = get_disk_usage(tmp_path)
    assert "total" in usage
    assert "used" in usage
    assert "free" in usage
    assert "percent" in usage
    assert isinstance(usage["percent"], (int, float))


def test_list_directory_files(tmp_path: Path) -> None:
    # Initially empty
    files, total = list_directory_files(tmp_path)
    assert files == []
    assert total == 0

    # Add 2 files
    (tmp_path / "a.txt").write_text("aaa")
    (tmp_path / "b.txt").write_text("bbbbbb")

    files, total = list_directory_files(tmp_path)
    assert total == 2
    assert len(files) == 2
    names = [f["name"] for f in files]
    assert "a.txt" in names
    assert "b.txt" in names


def test_is_path_safe(tmp_path: Path) -> None:
    sub = tmp_path / "subdir"
    sub.mkdir()
    child = sub / "test.txt"

    assert is_path_safe(tmp_path, child) is True
    assert is_path_safe(tmp_path, tmp_path) is True
    assert is_path_safe(sub, tmp_path) is False
    assert is_path_safe(sub, Path("/etc/passwd")) is False
