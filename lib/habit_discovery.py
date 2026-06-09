"""扫描用户已有目录，提取文件夹命名习惯并合并到分类配置。"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import desktop_path

# 目录名命中即跳过该目录及其子树（不区分大小写）
SKIP_DIR_NAMES = frozenset(
    {
        # 系统 / 隐藏
        "appdata",
        "application data",
        "program files",
        "program files (x86)",
        "programdata",
        "windows",
        "system32",
        "syswow64",
        "$recycle.bin",
        "recycler",
        "system volume information",
        "recovery",
        "perflogs",
        "msocache",
        "config.msi",
        # 开发依赖与缓存（非用户整理习惯）
        ".git",
        ".svn",
        ".hg",
        ".docmind",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".virtualenv",
        "site-packages",
        "dist",
        "build",
        "target",
        "vendor",
        ".gradle",
        ".m2",
        ".npm",
        ".cargo",
        ".rustup",
        # 常见软件安装/运行目录名
        "microsoft",
        "windowsapps",
        "packages",
        "cache",
        "caches",
        "temp",
        "tmp",
        "logs",
        "log",
    }
)

# 作为扫描根目录时直接拒绝（绝对路径前缀）
BLOCKED_ROOT_PREFIXES = (
    "c:/windows",
    "c:/program files",
    "c:/program files (x86)",
    "c:/programdata",
    "/system",
    "/library",
    "/applications",
    "/usr",
    "/var",
    "/opt",
    "/etc",
    "/bin",
    "/sbin",
)

CATEGORY_HINTS: dict[str, list[str]] = {
    "财务生活子类": [
        "账单",
        "银行",
        "税务",
        "保险",
        "理财",
        "财务",
        "发票",
        "报销",
        "工资",
        "信用卡",
    ],
    "日常子类": [
        "照片",
        "图片",
        "家庭",
        "医疗",
        "笔记",
        "日记",
        "旅行",
        "证件",
        "票证",
        "休闲",
    ],
    "办公子类": [
        "办公",
        "行政",
        "人事",
        "制度",
        "会议",
        "合同",
        "表单",
        "档案",
    ],
    "技术资料子类": [
        "技术",
        "规范",
        "标准",
        "工艺",
        "手册",
        "方案",
        "图纸",
        "设计",
    ],
    "项目子类模板": [
        "图纸",
        "合同",
        "往来",
        "出货",
        "进货",
        "票据",
        "照片",
        "记录",
        "报告",
        "方案",
        "代码",
        "测试",
    ],
}

PROJECT_PARENT_HINTS = ("项目", "工程", "客户", "合同", "case", "project")
PROJECT_CHILD_MIN = 2


def _is_blocked_root(path: Path) -> bool:
    resolved = str(path.resolve()).replace("\\", "/").lower()
    return any(resolved.startswith(prefix) for prefix in BLOCKED_ROOT_PREFIXES)


def _path_has_skipped_segment(path: Path) -> bool:
    for part in path.parts:
        low = part.lower()
        if low in SKIP_DIR_NAMES:
            return True
        if part.startswith(".") and low not in {".docmind"}:
            return True
    return False


def common_scan_roots(target_folder: str = "", archive_root: str = "") -> list[Path]:
    """首次安装建议扫描的根目录（不扫全盘、不扫系统盘根）。"""
    home = Path.home()
    roots: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        if _is_blocked_root(p):
            return
        key = str(p.resolve()).lower()
        if key not in seen and p.is_dir():
            seen.add(key)
            roots.append(p)

    if target_folder:
        add(Path(target_folder))
    if archive_root:
        add(Path(archive_root))
    add(desktop_path())
    for name in ("Documents", "文档", "Downloads", "下载"):
        add(home / name)
    return roots


def _should_skip_dir(path: Path) -> bool:
    return _path_has_skipped_segment(path)


def _match_category_key(folder_name: str) -> str | None:
    for key, hints in CATEGORY_HINTS.items():
        if any(h in folder_name for h in hints):
            return key
    return None


def _is_project_folder(name: str, child_names: list[str]) -> bool:
    if any(h in name for h in PROJECT_PARENT_HINTS):
        return True
    if len(child_names) < PROJECT_CHILD_MIN:
        return False
    hits = sum(1 for c in child_names if _match_category_key(c) == "项目子类模板")
    return hits >= 1


def _unique_append(items: list[str], name: str) -> None:
    if name and name not in items:
        items.append(name)


def scan_folder_habits(
    roots: list[Path],
    *,
    max_depth: int = 4,
    max_dirs: int = 800,
) -> dict[str, Any]:
    """遍历目录树，统计文件夹命名习惯。"""
    dir_counter: Counter[str] = Counter()
    rel_paths: list[str] = []
    project_names: list[str] = []
    category_hits: dict[str, list[str]] = {k: [] for k in CATEGORY_HINTS}
    scanned_roots: list[str] = []
    dir_count = 0

    for root in roots:
        if not root.is_dir():
            continue
        scanned_roots.append(str(root))
        # 手动遍历以便遇到系统/安装目录时剪枝，不进入子树
        stack: list[Path] = [root]
        while stack:
            dirpath = stack.pop()
            if not dirpath.is_dir():
                continue
            if dirpath != root and _should_skip_dir(dirpath):
                continue

            try:
                rel_parts = dirpath.relative_to(root).parts
            except ValueError:
                continue

            if dirpath != root and len(rel_parts) <= max_depth:
                dir_count += 1
                if dir_count > max_dirs:
                    break

                name = dirpath.name.strip()
                if name and len(name) <= 40:
                    dir_counter[name] += 1
                    rel_paths.append(dirpath.relative_to(root).as_posix())
                    key = _match_category_key(name)
                    if key:
                        _unique_append(category_hits[key], name)
                    children = [
                        p.name
                        for p in dirpath.iterdir()
                        if p.is_dir() and not _should_skip_dir(p)
                    ]
                    if _is_project_folder(name, children):
                        _unique_append(project_names, name)

            if dirpath == root or len(rel_parts) < max_depth:
                try:
                    for child in dirpath.iterdir():
                        if child.is_dir() and not _should_skip_dir(child):
                            stack.append(child)
                except OSError:
                    pass

            if dir_count > max_dirs:
                break

        if dir_count > max_dirs:
            break

    frequent = [name for name, _ in dir_counter.most_common(30)]
    return {
        "scanned_roots": scanned_roots,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "dir_count": dir_count,
        "frequent_folder_names": frequent,
        "rel_paths_sample": sorted(set(rel_paths))[:120],
        "detected_projects": project_names[:20],
        "category_folder_names": category_hits,
    }


def merge_habits_into_categories(
    categories: dict[str, Any],
    discovery: dict[str, Any],
) -> dict[str, Any]:
    """把扫描到的文件夹名并入分类配置（保留默认项，追加用户习惯）。"""
    merged = {k: list(v) if isinstance(v, list) else v for k, v in categories.items()}
    for key, names in discovery.get("category_folder_names", {}).items():
        if key not in merged or not isinstance(merged[key], list):
            continue
        for name in names:
            _unique_append(merged[key], name)
    for name in discovery.get("frequent_folder_names", []):
        key = _match_category_key(name)
        if key and key in merged and isinstance(merged[key], list):
            _unique_append(merged[key], name)
    if discovery.get("detected_projects"):
        merged["用户项目名"] = list(discovery["detected_projects"])
    return merged


def discover_and_merge(
    categories: dict[str, Any],
    *,
    target_folder: str = "",
    archive_root: str = "",
    extra_roots: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    roots = common_scan_roots(target_folder, archive_root)
    if extra_roots:
        for r in extra_roots:
            p = Path(r)
            if p.is_dir() and p not in roots:
                roots.append(p)
    discovery = scan_folder_habits(roots)
    merged = merge_habits_into_categories(categories, discovery)
    return merged, discovery


def format_discovery_summary(discovery: dict[str, Any]) -> str:
    lines = [
        f"已扫描 {discovery.get('dir_count', 0)} 个文件夹，来源：",
        *[f"  - {r}" for r in discovery.get("scanned_roots", [])],
    ]
    projects = discovery.get("detected_projects") or []
    if projects:
        lines.append("推测的项目文件夹：")
        lines.extend(f"  - {p}" for p in projects[:10])
    hits = discovery.get("category_folder_names") or {}
    custom = [(k, v) for k, v in hits.items() if v]
    if custom:
        lines.append("已识别的习惯子类名：")
        for key, names in custom:
            lines.append(f"  - {key}: {', '.join(names[:8])}")
    frequent = discovery.get("frequent_folder_names") or []
    if frequent:
        lines.append(f"高频文件夹名：{', '.join(frequent[:12])}")
    return "\n".join(lines)
