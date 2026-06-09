"""在用户确认归档结构后，将分类路径贴合已有目录，仅在必要时扩展。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

WORK_TOP = "工作"
LIFE_TOP = "生活"
SHORTCUT_TOP = "应用快捷方式"
WORK_BRANCHES = frozenset({"办公", "技术资料"})
LIFE_BRANCHES = frozenset({"财务", "日常"})

def scan_archive_dirs(archive_root: Path) -> set[str]:
    """扫描归档根下已有目录（含各级前缀路径）。"""
    dirs: set[str] = set()
    if not archive_root.is_dir():
        return dirs
    for p in archive_root.rglob("*"):
        if not p.is_dir():
            continue
        rel = p.relative_to(archive_root).as_posix()
        if not rel or rel.startswith("."):
            continue
        parts = rel.split("/")
        for i in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:i]))
    return dirs


def _child_names(existing_dirs: set[str], parent: str) -> list[str]:
    prefix = f"{parent}/" if parent else ""
    names: set[str] = set()
    for p in existing_dirs:
        if parent:
            if not p.startswith(prefix):
                continue
            rest = p[len(prefix) :]
        else:
            rest = p
        if not rest:
            continue
        name = rest.split("/")[0]
        if name:
            names.add(name)
    return sorted(names)


def _pick_existing_child(suggested: str, children: list[str]) -> str | None:
    if suggested in children:
        return suggested
    return None


def resolve_path_with_existing(
    suggested: str,
    existing_dirs: set[str],
    categories: dict[str, Any] | None = None,
    *,
    max_depth: int = 4,
) -> tuple[str, bool]:
    """
    将 AI 建议路径贴合已有目录树（按路径段精确匹配已有文件夹名）。
    返回 (最终相对路径, 是否包含新建目录段)。
    """
    _ = categories
    parts = [p for p in suggested.replace("\\", "/").split("/") if p]
    if not parts:
        return suggested, True
    if parts[0] == SHORTCUT_TOP:
        return SHORTCUT_TOP, SHORTCUT_TOP not in existing_dirs

    resolved: list[str] = []
    used_new = False

    for i, part in enumerate(parts):
        parent = "/".join(resolved)
        candidate = f"{parent}/{part}" if parent else part

        if candidate in existing_dirs:
            resolved.append(part)
            continue

        children = _child_names(existing_dirs, parent)
        picked = _pick_existing_child(part, children)
        if picked:
            resolved.append(picked)
            continue

        resolved.extend(parts[i:])
        used_new = True
        break

    final = "/".join(resolved[:max_depth])
    return final, used_new


def format_existing_paths_for_prompt(
    existing_dirs: set[str],
    *,
    max_lines: int = 80,
) -> str:
    if not existing_dirs:
        return ""
    ordered = sorted(existing_dirs, key=lambda p: (p.count("/"), p))
    lines = ordered[:max_lines]
    text = "\n".join(f"- {p}" for p in lines)
    if len(ordered) > max_lines:
        text += f"\n- …（另有 {len(ordered) - max_lines} 个目录）"
    return text
