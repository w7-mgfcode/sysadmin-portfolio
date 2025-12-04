"""
Disk Analyzer - Lemezterület elemző.

Tools for analyzing disk usage, finding large files, and directory sizes.

Eszközök lemezterület elemzéshez, nagy fájlok kereséséhez és
könyvtár méretek meghatározásához.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil

from .models import DirectorySize, DiskUsage, LargeFile


def get_filesystem_usage(path: str = "/") -> DiskUsage:
    """
    Fájlrendszer használat lekérdezése adott útvonalon.

    Args:
        path: Az ellenőrizendő útvonal.

    Returns:
        DiskUsage objektum a használati adatokkal.
    """
    usage = psutil.disk_usage(path)

    # Eszköz keresése a mountpoint alapján
    device = "unknown"
    fstype = "unknown"
    for partition in psutil.disk_partitions(all=False):
        if partition.mountpoint == path:
            device = partition.device
            fstype = partition.fstype
            break

    return DiskUsage(
        device=device,
        mountpoint=path,
        fstype=fstype,
        total_bytes=usage.total,
        used_bytes=usage.used,
        free_bytes=usage.free,
        percent_used=usage.percent,
    )


def analyze_directory(
    path: Path | str,
    max_depth: int = 1,
    exclude_hidden: bool = True,
) -> list[DirectorySize]:
    """
    Könyvtár méret elemzése.

    Args:
        path: Az elemzendő könyvtár útvonala.
        max_depth: Maximum mélység (1 = csak közvetlen alkönyvtárak).
        exclude_hidden: Rejtett könyvtárak kizárása.

    Returns:
        DirectorySize objektumok listája méret szerint rendezve.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Könyvtár nem található: {path}")

    if not path.is_dir():
        raise ValueError(f"Nem könyvtár: {path}")

    results = []

    # Közvetlen alkönyvtárak bejárása
    try:
        entries = list(path.iterdir())
    except PermissionError:
        return results

    for entry in entries:
        if exclude_hidden and entry.name.startswith("."):
            continue

        if entry.is_dir():
            try:
                dir_size = _calculate_dir_size(entry)
                results.append(dir_size)
            except PermissionError:
                # Reason: Nincs jogosultság a könyvtárhoz
                results.append(
                    DirectorySize(
                        path=str(entry),
                        size_bytes=0,
                        file_count=0,
                        dir_count=0,
                    )
                )
        elif entry.is_file():
            try:
                stat = entry.stat()
                results.append(
                    DirectorySize(
                        path=str(entry),
                        size_bytes=stat.st_size,
                        file_count=1,
                        dir_count=0,
                    )
                )
            except (PermissionError, OSError):
                continue

    # Rendezés méret szerint (csökkenő)
    results.sort(key=lambda x: x.size_bytes, reverse=True)
    return results


def _calculate_dir_size(path: Path) -> DirectorySize:
    """
    Könyvtár méretének kiszámítása rekurzívan.

    Args:
        path: A könyvtár útvonala.

    Returns:
        DirectorySize objektum.
    """
    total_size = 0
    file_count = 0
    dir_count = 0

    for entry in path.rglob("*"):
        try:
            if entry.is_file():
                total_size += entry.stat().st_size
                file_count += 1
            elif entry.is_dir():
                dir_count += 1
        except (PermissionError, OSError):
            continue

    return DirectorySize(
        path=str(path),
        size_bytes=total_size,
        file_count=file_count,
        dir_count=dir_count,
    )


def find_large_files(
    path: Path | str,
    min_size_bytes: int = 100 * 1024 * 1024,  # 100 MB
    max_results: int = 50,
    exclude_patterns: Optional[list[str]] = None,
) -> list[LargeFile]:
    """
    Nagy fájlok keresése könyvtárban.

    Args:
        path: A keresési könyvtár útvonala.
        min_size_bytes: Minimum fájlméret (alapértelmezett: 100 MB).
        max_results: Maximum visszaadandó eredmények száma.
        exclude_patterns: Kizárandó mintázatok listája (pl. ["*.log", "*.tmp"]).

    Returns:
        LargeFile objektumok listája méret szerint rendezve.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Könyvtár nem található: {path}")

    exclude_patterns = exclude_patterns or []
    large_files = []

    for entry in path.rglob("*"):
        try:
            if not entry.is_file():
                continue

            # Kizárási minták ellenőrzése
            if any(entry.match(pattern) for pattern in exclude_patterns):
                continue

            stat = entry.stat()
            if stat.st_size >= min_size_bytes:
                # Tulajdonos lekérdezése
                try:
                    import pwd
                    owner = pwd.getpwuid(stat.st_uid).pw_name
                except (ImportError, KeyError):
                    owner = str(stat.st_uid)

                large_files.append(
                    LargeFile(
                        path=str(entry),
                        size_bytes=stat.st_size,
                        modified_time=datetime.fromtimestamp(stat.st_mtime),
                        owner=owner,
                    )
                )
        except (PermissionError, OSError):
            continue

    # Rendezés méret szerint (csökkenő)
    large_files.sort(key=lambda x: x.size_bytes, reverse=True)
    return large_files[:max_results]


def get_directory_sizes(
    path: Path | str,
    depth: int = 1,
) -> dict[str, int]:
    """
    Könyvtár méretek lekérdezése adott mélységig.

    Args:
        path: A kiindulási könyvtár útvonala.
        depth: Maximum mélység.

    Returns:
        Dict ahol a kulcs a könyvtár útvonala, az érték a méret bájtban.
    """
    path = Path(path)
    sizes: dict[str, int] = {}

    def _get_size(current_path: Path, current_depth: int) -> int:
        """Rekurzív méret számítás."""
        total = 0

        try:
            entries = list(current_path.iterdir())
        except PermissionError:
            return 0

        for entry in entries:
            try:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    if current_depth < depth:
                        subdir_size = _get_size(entry, current_depth + 1)
                        sizes[str(entry)] = subdir_size
                        total += subdir_size
                    else:
                        # Mélység elérve, teljes méret számítás
                        dir_size = sum(
                            f.stat().st_size
                            for f in entry.rglob("*")
                            if f.is_file()
                        )
                        sizes[str(entry)] = dir_size
                        total += dir_size
            except (PermissionError, OSError):
                continue

        return total

    total_size = _get_size(path, 0)
    sizes[str(path)] = total_size

    return sizes


def format_size(size_bytes: int) -> str:
    """
    Fájlméret formázása ember-olvasható formátumba.

    Args:
        size_bytes: Méret bájtban.

    Returns:
        Formázott méret string (pl. "1.5 GB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} EB"
