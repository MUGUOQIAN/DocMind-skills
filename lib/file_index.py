"""整理后文件索引：供 Agent 快速检索已归档文件。"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .content_extract import extract_preview

INDEX_VERSION = 1
INDEX_JSON = "file_index.json"
INDEX_MD = "file_index.md"
META_DIR = ".docmind"
GLOBAL_INDEX_PATH = Path.home() / ".docmind" / "file_index.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    parts = re.findall(r"[\w\u4e00-\u9fff]+", text)
    return [p for p in parts if len(p) >= 2]


def archive_root_from_destination(destination: str | Path, target_path: str) -> Path:
    """从归档后完整路径与 target_path 反推 archive_root。"""
    p = Path(destination)
    parts = [x for x in target_path.replace("\\", "/").split("/") if x]
    return p.parents[len(parts)]


def archive_index_dir(archive_root: str | Path) -> Path:
    return Path(archive_root) / META_DIR


def archive_index_json(archive_root: str | Path) -> Path:
    return archive_index_dir(archive_root) / INDEX_JSON


def _empty_archive_index(archive_root: str) -> dict[str, Any]:
    return {
        "version": INDEX_VERSION,
        "archive_root": archive_root,
        "updated_at": _now_iso(),
        "entry_count": 0,
        "entries": [],
    }


def load_archive_index(archive_root: str | Path) -> dict[str, Any]:
    path = archive_index_json(archive_root)
    root = str(Path(archive_root).resolve())
    if not path.is_file():
        return _empty_archive_index(root)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("entries", [])
    data["archive_root"] = root
    return data


def save_archive_index(archive_root: str | Path, data: dict[str, Any]) -> Path:
    d = archive_index_dir(archive_root)
    d.mkdir(parents=True, exist_ok=True)
    data["version"] = INDEX_VERSION
    data["updated_at"] = _now_iso()
    data["entry_count"] = len(data.get("entries", []))
    path = d / INDEX_JSON
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_index_markdown(archive_root, data)
    _sync_global_index(archive_root, data)
    return path


def write_index_markdown(archive_root: str | Path, data: dict[str, Any]) -> Path:
    d = archive_index_dir(archive_root)
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DocMind 文件索引",
        "",
        f"- 归档根目录：`{data.get('archive_root', '')}`",
        f"- 更新时间：{data.get('updated_at', '')}",
        f"- 文件数：{data.get('entry_count', 0)}",
        "",
        "Agent 可用 `docmind.py search --query \"关键词\"` 检索，或直接阅读本文件。",
        "",
        "| 文件名 | 分类路径 | 完整路径 | 内容摘要 |",
        "|--------|----------|----------|----------|",
    ]
    for e in data.get("entries", [])[-500:]:
        if not e.get("exists", True):
            continue
        name = e.get("filename", "").replace("|", "\\|")
        tp = e.get("target_path", "").replace("|", "\\|")
        fp = e.get("path", "").replace("|", "\\|")
        snip = (e.get("content_snippet") or "").replace("\n", " ").replace("|", "\\|")[:120]
        lines.append(f"| {name} | {tp} | {fp} | {snip} |")
    md_path = d / INDEX_MD
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def _entry_from_operation(
    op: dict[str, Any],
    *,
    archive_root: str,
    session_id: str,
    dry_run: bool,
) -> dict[str, Any]:
    dest = op.get("destination", "")
    return {
        "filename": Path(dest).name if dest else Path(op.get("source", "")).name,
        "path": dest if not dry_run else op.get("destination", ""),
        "source": op.get("source", ""),
        "target_path": op.get("target_path", ""),
        "archive_root": archive_root,
        "content_snippet": (op.get("content_snippet") or "")[:500],
        "indexed_at": _now_iso(),
        "session_id": session_id,
        "exists": not dry_run,
        "preview_only": dry_run,
    }


def _dedupe_key(entry: dict[str, Any]) -> str:
    return (entry.get("path") or entry.get("source") or entry.get("filename", "")).lower()


def update_index_from_operations(
    archive_root: str | Path,
    operations: list[dict],
    *,
    session_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """整理/预览结束后，将本次操作写入归档索引。"""
    root = str(Path(archive_root).resolve())
    data = load_archive_index(root)
    by_key = {_dedupe_key(e): e for e in data["entries"]}

    for op in operations:
        entry = _entry_from_operation(op, archive_root=root, session_id=session_id, dry_run=dry_run)
        key = _dedupe_key(entry)
        by_key[key] = entry

    data["entries"] = list(by_key.values())
    save_archive_index(root, data)
    return data


def _should_skip_index_path(path: Path) -> bool:
    if META_DIR in path.parts:
        return True
    name = path.name.lower()
    if name in {"desktop.ini", "thumbs.db", ".ds_store"}:
        return True
    if name.startswith("~$") or name.startswith(".~"):
        return True
    if path.suffix.lower() in {".tmp", ".temp", ".swp", ".partial"}:
        return True
    return False


def entry_from_archive_file(
    file_path: Path,
    archive_root: Path,
    *,
    max_chars: int = 400,
    session_id: str = "watch",
) -> dict[str, Any]:
    """从归档目录中的单个文件构建索引条目。"""
    f = file_path.resolve()
    root = archive_root.resolve()
    rel = f.relative_to(root)
    parts = rel.parts
    target_path = "/".join(parts[:-1]) if len(parts) > 1 else ""
    snippet = ""
    try:
        snippet = extract_preview(str(f))[:max_chars]
    except Exception:
        snippet = ""
    return {
        "filename": f.name,
        "path": str(f),
        "source": "",
        "target_path": target_path.replace("\\", "/"),
        "archive_root": str(root),
        "content_snippet": snippet,
        "indexed_at": _now_iso(),
        "session_id": session_id,
        "exists": True,
        "preview_only": False,
    }


def upsert_index_file(
    archive_root: str | Path,
    file_path: str | Path,
    *,
    max_chars: int = 400,
    session_id: str = "watch",
) -> dict[str, Any] | None:
    """新增或更新单个文件的索引条目。"""
    root = Path(archive_root).resolve()
    f = Path(file_path).resolve()
    if not f.is_file() or _should_skip_index_path(f):
        return None
    try:
        f.relative_to(root)
    except ValueError:
        return None
    entry = entry_from_archive_file(f, root, max_chars=max_chars, session_id=session_id)
    data = load_archive_index(root)
    by_key = {_dedupe_key(e): e for e in data["entries"]}
    by_key[_dedupe_key(entry)] = entry
    data["entries"] = list(by_key.values())
    save_archive_index(root, data)
    return entry


def sync_archive_to_index(
    archive_root: str | Path,
    *,
    max_chars: int = 400,
    max_files: int = 2000,
    session_id: str = "watch-bootstrap",
) -> dict[str, int]:
    """增量同步：为归档目录中现有文件 upsert 索引（不删除多余条目）。"""
    root = Path(archive_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"归档目录不存在: {root}")
    upserted = 0
    skipped = 0
    for f in root.rglob("*"):
        if not f.is_file() or _should_skip_index_path(f):
            skipped += 1
            continue
        if upserted >= max_files:
            break
        if upsert_index_file(root, f, max_chars=max_chars, session_id=session_id):
            upserted += 1
    return {"upserted": upserted, "skipped": skipped}


def remove_index_entries(
    archive_root: str | Path,
    paths: list[str],
) -> dict[str, Any]:
    """撤销整理时，按归档路径移除索引项。"""
    root = str(Path(archive_root).resolve())
    data = load_archive_index(root)
    remove_set = {p.lower() for p in paths}
    data["entries"] = [
        e for e in data["entries"] if (e.get("path") or "").lower() not in remove_set
    ]
    save_archive_index(root, data)
    return data


def _score_entry(entry: dict[str, Any], query: str, tokens: list[str]) -> int:
    if not entry.get("exists", True) and not entry.get("preview_only"):
        return 0
    hay = " ".join(
        [
            entry.get("filename", ""),
            entry.get("target_path", ""),
            entry.get("path", ""),
            entry.get("content_snippet", ""),
        ]
    ).lower()
    score = 0
    q = query.lower().strip()
    if q and q in hay:
        score += 30
    for t in tokens:
        if t in hay:
            score += 10
    return score


def search_index(
    query: str,
    *,
    archive_root: str | Path | None = None,
    limit: int = 20,
    include_preview: bool = True,
) -> list[dict[str, Any]]:
    """在索引中搜索文件（文件名、分类路径、内容摘要）。"""
    query = query.strip()
    if not query:
        return []
    tokens = _tokenize(query)
    results: list[tuple[int, dict[str, Any]]] = []

    def scan_data(data: dict[str, Any]) -> None:
        for entry in data.get("entries", []):
            if not include_preview and entry.get("preview_only"):
                continue
            if not entry.get("exists", True) and not entry.get("preview_only"):
                continue
            s = _score_entry(entry, query, tokens)
            if s > 0:
                results.append((s, dict(entry)))

    if archive_root:
        scan_data(load_archive_index(archive_root))
    else:
        global_data = load_global_index()
        for _root, data in global_data.get("archives", {}).items():
            scan_data(data)

    results.sort(key=lambda x: (-x[0], x[1].get("indexed_at", "")))
    out = []
    for score, entry in results[:limit]:
        entry = dict(entry)
        entry["score"] = score
        out.append(entry)
    return out


def load_global_index() -> dict[str, Any]:
    if not GLOBAL_INDEX_PATH.is_file():
        return {"version": INDEX_VERSION, "updated_at": _now_iso(), "archives": {}}
    return json.loads(GLOBAL_INDEX_PATH.read_text(encoding="utf-8"))


def _sync_global_index(archive_root: str | Path, data: dict[str, Any]) -> None:
    root = str(Path(archive_root).resolve())
    global_data = load_global_index()
    global_data.setdefault("archives", {})
    global_data["archives"][root] = {
        "updated_at": data.get("updated_at"),
        "entry_count": data.get("entry_count"),
        "entries": data.get("entries", []),
    }
    global_data["updated_at"] = _now_iso()
    GLOBAL_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    GLOBAL_INDEX_PATH.write_text(
        json.dumps(global_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def rebuild_index_from_archive(
    archive_root: str | Path,
    *,
    max_chars: int = 400,
    max_files: int = 2000,
) -> dict[str, Any]:
    """扫描归档目录重建索引（较慢，用于修复或补全）。"""
    root = Path(archive_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"归档目录不存在: {root}")
    entries: list[dict[str, Any]] = []
    count = 0
    for f in root.rglob("*"):
        if not f.is_file() or _should_skip_index_path(f):
            continue
        count += 1
        if count > max_files:
            break
        entries.append(
            entry_from_archive_file(f, root, max_chars=max_chars, session_id="rebuild")
        )
    data = _empty_archive_index(str(root))
    data["entries"] = entries
    save_archive_index(root, data)
    return data


def index_paths_for_agent(archive_root: str | Path) -> dict[str, str]:
    """返回 Agent 可读取的索引文件路径。"""
    d = archive_index_dir(archive_root)
    return {
        "json": str(d / INDEX_JSON),
        "markdown": str(d / INDEX_MD),
        "global_json": str(GLOBAL_INDEX_PATH),
    }
