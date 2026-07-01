"""归档目录选择：磁盘列表、空间检测与路径校验。"""

from __future__ import annotations

import os
import shutil
import string
import sys
from pathlib import Path
from typing import Any


DEFAULT_ARCHIVE_FOLDER_NAME = "DocMind归档"


def format_free_space(free_bytes: int) -> str:
    if free_bytes < 0:
        return "未知"
    gb = free_bytes / (1024**3)
    if gb >= 1:
        return f"{gb:.1f} GB 可用"
    mb = free_bytes / (1024**2)
    return f"{mb:.0f} MB 可用"


def _disk_usage(path: Path) -> int | None:
    try:
        return shutil.disk_usage(path).free
    except OSError:
        return None


def _root_entry(path: Path, *, label: str | None = None) -> dict[str, Any]:
    free = _disk_usage(path)
    display = label or str(path)
    if free is not None:
        display = f"{display}（{format_free_space(free)}）"
    return {
        "path": str(path.resolve()),
        "label": label or str(path),
        "free_bytes": free,
        "free_gb": round(free / (1024**3), 2) if free is not None else None,
        "display": display,
    }


def list_storage_roots() -> list[dict[str, Any]]:
    """列出可选存储根路径（系统盘、其他磁盘/卷、用户目录）。"""
    seen: set[str] = set()
    roots: list[dict[str, Any]] = []

    def add(path: Path, label: str | None = None) -> None:
        try:
            resolved = path.resolve()
        except OSError:
            return
        key = str(resolved).lower() if sys.platform == "win32" else str(resolved)
        if not resolved.exists() or key in seen:
            return
        seen.add(key)
        roots.append(_root_entry(resolved, label=label))

    home = Path.home()
    add(home, label=f"用户目录 ({home})")

    if sys.platform == "win32":
        try:
            import ctypes

            bitmask = ctypes.windll.kernel32.GetLogicalDrives()  # type: ignore[attr-defined]
            for i, letter in enumerate(string.ascii_uppercase):
                if bitmask & (1 << i):
                    add(Path(f"{letter}:\\"), label=f"本地磁盘 ({letter}:)")
        except Exception:
            for letter in string.ascii_uppercase:
                p = Path(f"{letter}:\\")
                if p.exists():
                    add(p, label=f"本地磁盘 ({letter}:)")
    elif sys.platform == "darwin":
        add(Path("/"), label="系统磁盘 (/)")
        volumes = Path("/Volumes")
        if volumes.is_dir():
            for vol in sorted(volumes.iterdir()):
                if vol.is_dir() and not vol.name.startswith("."):
                    add(vol, label=f"卷 {vol.name}")
    else:
        add(Path("/"), label="根目录 (/)")
        for mount in (Path("/mnt"), Path("/media")):
            if mount.is_dir():
                for vol in sorted(mount.iterdir()):
                    if vol.is_dir():
                        add(vol, label=str(vol))

    return roots


def join_archive_path(storage_root: str | Path, folder_name: str) -> Path:
    root = Path(storage_root).expanduser()
    name = (folder_name or DEFAULT_ARCHIVE_FOLDER_NAME).strip().strip("\\/")
    if not name:
        name = DEFAULT_ARCHIVE_FOLDER_NAME
    return (root / name).resolve()


def suggest_archive_paths(target_folder: str | Path | None = None) -> list[str]:
    """常用归档路径建议（优先非系统盘的大容量磁盘）。"""
    suggestions: list[str] = []
    home = Path.home()
    target_parent = Path(target_folder).parent if target_folder else home

    roots = list_storage_roots()
    ranked: list[tuple[int, str]] = []
    for item in roots:
        path = item["path"]
        free = item.get("free_bytes") or 0
        score = free
        if sys.platform == "win32" and len(path) >= 2 and path[1] == ":":
            if path[0].upper() != "C":
                score += 10**12
        if path == str(home.resolve()):
            score -= 10**10
        ranked.append((score, path))

    ranked.sort(reverse=True)
    for _, root in ranked[:4]:
        candidate = str(join_archive_path(root, DEFAULT_ARCHIVE_FOLDER_NAME))
        if candidate not in suggestions:
            suggestions.append(candidate)

    fallback = str(target_parent / DEFAULT_ARCHIVE_FOLDER_NAME)
    if fallback not in suggestions:
        suggestions.append(fallback)
    return suggestions


def validate_archive_root(
    path: str | Path,
    *,
    create: bool = True,
) -> Path:
    """校验归档目录可写；必要时创建。"""
    if not str(path).strip():
        raise ValueError("请指定整理后文件的保存目录")

    target = Path(path).expanduser()
    if not target.is_absolute():
        target = target.resolve()

    if target.exists():
        if not target.is_dir():
            raise ValueError(f"归档路径不是文件夹: {target}")
        if not os.access(target, os.W_OK):
            raise ValueError(f"归档目录无写入权限: {target}")
        return target

    if not create:
        raise FileNotFoundError(f"归档目录不存在: {target}")

    parent = target.parent
    if parent.exists() and not os.access(parent, os.W_OK):
        raise ValueError(f"无法在「{parent}」下创建文件夹，请检查磁盘权限")

    target.mkdir(parents=True, exist_ok=True)
    if not os.access(target, os.W_OK):
        raise ValueError(f"归档目录无写入权限: {target}")
    return target


def parse_archive_from_config(cfg: dict[str, Any]) -> str:
    return str(cfg.get("archive_root") or "").strip()
