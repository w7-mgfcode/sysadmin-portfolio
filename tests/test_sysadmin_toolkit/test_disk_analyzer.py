"""
Tests for disk analyzer module.

Tesztek a lemez elemző modulhoz.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("/tests/", 1)[0] + "/1-sysadmin-toolkit")

from toolkit.disk_analyzer import (
    analyze_directory,
    find_large_files,
    format_size,
    get_directory_sizes,
    get_filesystem_usage,
)
from toolkit.models import DirectorySize, DiskUsage, LargeFile


class TestGetFilesystemUsage:
    """Tests for get_filesystem_usage function."""

    def test_filesystem_usage_returns_disk_usage(self):
        """Test that function returns DiskUsage object."""
        usage = get_filesystem_usage("/")
        assert isinstance(usage, DiskUsage)

    def test_filesystem_usage_has_valid_percent(self):
        """Test that percent used is valid."""
        usage = get_filesystem_usage("/")
        assert 0 <= usage.percent_used <= 100

    def test_filesystem_usage_sizes_make_sense(self):
        """Test that size values are logical."""
        usage = get_filesystem_usage("/")
        assert usage.total_bytes > 0
        assert usage.used_bytes >= 0
        assert usage.free_bytes >= 0
        assert usage.used_bytes + usage.free_bytes <= usage.total_bytes * 1.1  # Allow small variance


class TestAnalyzeDirectory:
    """Tests for analyze_directory function."""

    def test_analyze_directory_returns_list(self):
        """Test that function returns a list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files and directories
            Path(tmpdir, "subdir1").mkdir()
            Path(tmpdir, "subdir2").mkdir()
            Path(tmpdir, "file1.txt").write_text("hello")

            results = analyze_directory(tmpdir)
            assert isinstance(results, list)

    def test_analyze_directory_finds_subdirs(self):
        """Test that subdirectories are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "subdir1").mkdir()
            Path(tmpdir, "subdir2").mkdir()

            results = analyze_directory(tmpdir)
            paths = [r.path for r in results]
            assert any("subdir1" in p for p in paths)
            assert any("subdir2" in p for p in paths)

    def test_analyze_directory_excludes_hidden(self):
        """Test that hidden directories are excluded by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, ".hidden").mkdir()
            Path(tmpdir, "visible").mkdir()

            results = analyze_directory(tmpdir, exclude_hidden=True)
            paths = [r.path for r in results]
            assert not any(".hidden" in p for p in paths)
            assert any("visible" in p for p in paths)

    def test_analyze_directory_includes_hidden(self):
        """Test that hidden directories can be included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, ".hidden").mkdir()
            Path(tmpdir, "visible").mkdir()

            results = analyze_directory(tmpdir, exclude_hidden=False)
            paths = [r.path for r in results]
            assert any(".hidden" in p for p in paths)

    def test_analyze_directory_not_found(self):
        """Test FileNotFoundError for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            analyze_directory("/nonexistent/directory")

    def test_analyze_directory_not_a_directory(self):
        """Test ValueError when path is not a directory."""
        with tempfile.NamedTemporaryFile() as f:
            with pytest.raises(ValueError):
                analyze_directory(f.name)


class TestFindLargeFiles:
    """Tests for find_large_files function."""

    def test_find_large_files_returns_list(self):
        """Test that function returns a list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = find_large_files(tmpdir, min_size_bytes=1)
            assert isinstance(results, list)

    def test_find_large_files_finds_files(self):
        """Test that large files are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a "large" file (larger than 10 bytes for test)
            large_file = Path(tmpdir, "large.txt")
            large_file.write_text("x" * 100)

            results = find_large_files(tmpdir, min_size_bytes=10)
            assert len(results) > 0
            assert any("large.txt" in r.path for r in results)

    def test_find_large_files_filters_by_size(self):
        """Test that size filter works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create small and large files
            Path(tmpdir, "small.txt").write_text("x")
            Path(tmpdir, "large.txt").write_text("x" * 1000)

            results = find_large_files(tmpdir, min_size_bytes=500)
            paths = [r.path for r in results]
            assert any("large.txt" in p for p in paths)
            assert not any("small.txt" in p for p in paths)

    def test_find_large_files_respects_max_results(self):
        """Test that max_results is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple files
            for i in range(10):
                Path(tmpdir, f"file{i}.txt").write_text("x" * 100)

            results = find_large_files(tmpdir, min_size_bytes=10, max_results=5)
            assert len(results) <= 5

    def test_find_large_files_returns_large_file_objects(self):
        """Test that results are LargeFile objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text("x" * 100)

            results = find_large_files(tmpdir, min_size_bytes=10)
            if results:
                assert isinstance(results[0], LargeFile)

    def test_find_large_files_sorted_by_size(self):
        """Test that results are sorted by size descending."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "small.txt").write_text("x" * 100)
            Path(tmpdir, "medium.txt").write_text("x" * 500)
            Path(tmpdir, "large.txt").write_text("x" * 1000)

            results = find_large_files(tmpdir, min_size_bytes=10)
            if len(results) > 1:
                sizes = [r.size_bytes for r in results]
                assert sizes == sorted(sizes, reverse=True)


class TestGetDirectorySizes:
    """Tests for get_directory_sizes function."""

    def test_directory_sizes_returns_dict(self):
        """Test that function returns a dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sizes = get_directory_sizes(tmpdir)
            assert isinstance(sizes, dict)

    def test_directory_sizes_includes_root(self):
        """Test that root directory is included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sizes = get_directory_sizes(tmpdir)
            assert tmpdir in sizes


class TestFormatSize:
    """Tests for format_size function."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        assert format_size(100) == "100.0 B"
        assert format_size(0) == "0.0 B"

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_size(1024) == "1.0 KB"
        assert format_size(2048) == "2.0 KB"

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        assert format_size(1048576) == "1.0 MB"
        assert format_size(5242880) == "5.0 MB"

    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_size(1073741824) == "1.0 GB"

    def test_format_terabytes(self):
        """Test formatting terabytes."""
        assert format_size(1099511627776) == "1.0 TB"
