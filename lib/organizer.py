import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from .archive_structure import resolve_path_with_existing, scan_archive_dirs
from .config import desktop_path, load_config
from .content_extract import extract_preview
from .file_index import (
    archive_root_from_destination,
    index_paths_for_agent,
    remove_index_entries,
    update_index_from_operations,
)
from .classification_rules import normalize_archive_path
from .setup_wizard import save_config
from .shortcuts import is_shortcut, shortcut_target_path

BACKEND_URL = os.getenv("DOCMIND_BACKEND_URL", "http://127.0.0.1:8000")
SKIP_NAMES = {".docmind", "desktop.ini", "thumbs.db", ".ds_store"}
LOG_DIR_NAME = ".docmind/logs"


def resolve_unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    parent = dest.parent
    n = 1
    while True:
        candidate = parent / f"{stem}_{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def _iter_files(root: Path, recursive: bool) -> list[Path]:
    files: list[Path] = []
    if recursive:
        for p in root.rglob("*"):
            if p.is_file() and not any(part in SKIP_NAMES for part in p.parts):
                files.append(p)
    else:
        for p in root.iterdir():
            if p.is_file() and p.name.lower() not in SKIP_NAMES:
                files.append(p)
    return files


def _log_path(source_root: Path) -> Path:
    return source_root / LOG_DIR_NAME


def _write_session_log(
    source_root: Path,
    operations: list[dict],
    dry_run: bool,
    *,
    organize_session_id: str | None = None,
    session_billing_type: str | None = None,
) -> Path:
    log_dir = _log_path(source_root)
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"session_{ts}.json"
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "operations": operations,
    }
    if organize_session_id:
        payload["organize_session_id"] = organize_session_id
    if session_billing_type:
        payload["session_billing_type"] = session_billing_type
    log_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = log_dir / "latest.json"
    latest.write_text(json.dumps({"session": log_file.name}, ensure_ascii=False), encoding="utf-8")
    return log_file


def undo_last(source_root: str | Path) -> list[dict]:
    root = Path(source_root)
    log_dir = _log_path(root)
    latest = log_dir / "latest.json"
    if not latest.exists():
        raise FileNotFoundError("没有可撤销的整理记录")
    meta = json.loads(latest.read_text(encoding="utf-8"))
    session = log_dir / meta["session"]
    data = json.loads(session.read_text(encoding="utf-8"))
    if data.get("dry_run"):
        raise RuntimeError("该次为预览模式，未实际移动文件")
    undone = []
    removed_paths: list[str] = []
    for op in reversed(data["operations"]):
        src = Path(op["destination"])
        dst = Path(op["source"])
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            undone.append(op)
            removed_paths.append(str(src))
    if removed_paths and undone:
        try:
            op0 = undone[0]
            ar = archive_root_from_destination(
                op0["destination"], op0.get("target_path", "")
            )
            remove_index_entries(ar, removed_paths)
        except Exception:
            pass
    return undone


def _prune_empty_dirs(root: Path) -> None:
    for dirpath in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if LOG_DIR_NAME in dirpath.parts:
            continue
        try:
            if dirpath.is_dir() and not any(dirpath.iterdir()):
                dirpath.rmdir()
        except OSError:
            pass


def confirm_archive_structure(
    *,
    config: dict[str, Any] | None = None,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """用户确认首次整理后的目录结构，此后整理优先归入已有文件夹。"""
    cfg = dict(config or load_config(config_path))
    cfg["structure_confirmed"] = True
    cfg["structure_confirmed_at"] = datetime.now(timezone.utc).isoformat()
    save_config(cfg, Path(config_path) if config_path else None)
    return cfg


def begin_organize_session_via_api(
    *,
    platform_user_id: str,
    platform: str,
) -> dict[str, Any]:
    """开启整理会话；整轮 run 只扣 1 次额度。"""
    payload = {
        "platform_user_id": platform_user_id,
        "platform": platform,
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(f"{BACKEND_URL}/api/v1/organize/begin", json=payload)
        resp.raise_for_status()
        return resp.json()


def classify_via_api(
    *,
    platform_user_id: str,
    platform: str,
    filename: str,
    content_preview: str,
    industry: str,
    job_title: str,
    custom_categories: dict,
    preview_only: bool,
    existing_archive_paths: list[str] | None = None,
    organize_session_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "platform_user_id": platform_user_id,
        "platform": platform,
        "file_path": filename,
        "filename": filename,
        "content_preview": content_preview,
        "industry": industry,
        "job_title": job_title,
        "custom_categories": custom_categories,
        "preview_only": preview_only,
    }
    if existing_archive_paths:
        payload["existing_archive_paths"] = existing_archive_paths
    if organize_session_id:
        payload["organize_session_id"] = organize_session_id
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(f"{BACKEND_URL}/api/v1/classify", json=payload)
        resp.raise_for_status()
        return resp.json()


def organize(
    *,
    platform_user_id: str,
    platform: str,
    source_dir: str | Path | None = None,
    archive_root: str | Path | None = None,
    use_desktop: bool = False,
    config: dict[str, Any] | None = None,
    dry_run: bool | None = None,
) -> list[dict]:
    cfg = config or load_config()
    source = Path(source_dir or cfg.get("target_folder") or "")
    if use_desktop or not source:
        source = desktop_path()
    if not source.is_dir():
        raise FileNotFoundError(f"源目录不存在: {source}")

    target_root = Path(archive_root or cfg.get("archive_root") or source.parent / "DocMind归档")
    is_preview = cfg.get("dry_run", True) if dry_run is None else dry_run
    recursive = cfg.get("recursive", True)
    max_chars = int(cfg.get("max_content_chars", 2000))
    auto_empty = cfg.get("auto_delete_empty", True)
    industry = cfg.get("industry", "")
    job_title = cfg.get("job_title", "")
    categories = cfg.get("categories", {})
    structure_confirmed = bool(cfg.get("structure_confirmed"))
    max_depth = int(cfg.get("max_path_depth", 4))

    existing_dirs: set[str] = set()
    existing_list: list[str] | None = None
    if structure_confirmed and target_root.is_dir():
        existing_dirs = scan_archive_dirs(target_root)
        existing_list = sorted(existing_dirs) if existing_dirs else None

    session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    index_enabled = cfg.get("index_enabled", True)
    index_snippet = int(cfg.get("index_snippet_chars", 400))

    file_list = _iter_files(source, recursive)
    organize_session_id: str | None = None
    session_billing: str | None = None
    if not is_preview and file_list:
        try:
            begin = begin_organize_session_via_api(
                platform_user_id=platform_user_id,
                platform=platform,
            )
            organize_session_id = begin["organize_session_id"]
            session_billing = begin.get("billing_type")
            print(
                f"[DocMind] 已开启整理会话（计费: {session_billing}），"
                f"本轮最多 {begin.get('max_files', 500)} 个文件"
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 402:
                detail = exc.response.json().get("detail", {})
                raise RuntimeError(detail.get("message", "需要付费")) from exc
            raise

    operations: list[dict] = []
    for file_path in file_list:
        preview_text = ""
        if is_shortcut(file_path):
            rel = normalize_archive_path(shortcut_target_path(cfg))
            result = {"target_path": rel, "billing_type": None}
        else:
            preview_text = extract_preview(str(file_path))[:max_chars]
            try:
                result = classify_via_api(
                    platform_user_id=platform_user_id,
                    platform=platform,
                    filename=file_path.name,
                    content_preview=preview_text,
                    industry=industry,
                    job_title=job_title,
                    custom_categories=categories,
                    preview_only=is_preview,
                    existing_archive_paths=existing_list,
                    organize_session_id=organize_session_id,
                )
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 402:
                    detail = exc.response.json().get("detail", {})
                    raise RuntimeError(detail.get("message", "需要付费")) from exc
                raise
            suggested = normalize_archive_path(result["target_path"].replace("\\", "/"))
            rel = suggested
            path_created = False
            if structure_confirmed and existing_dirs:
                rel, path_created = resolve_path_with_existing(
                    suggested,
                    existing_dirs,
                    categories,
                    max_depth=max_depth,
                )
                rel = normalize_archive_path(rel, max_depth=max_depth)
                existing_dirs.add(rel)
                for i in range(1, len(rel.split("/")) + 1):
                    existing_dirs.add("/".join(rel.split("/")[:i]))
        dest = resolve_unique_path(target_root / rel / file_path.name)
        op = {
            "source": str(file_path),
            "destination": str(dest),
            "target_path": rel,
            "billing_type": result.get("billing_type"),
            "content_snippet": preview_text[:index_snippet] if preview_text else "",
        }
        if structure_confirmed and not is_shortcut(file_path):
            op["target_path_suggested"] = suggested
            op["path_created"] = path_created
        operations.append(op)

        if not is_preview:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(dest))

    _write_session_log(
        source,
        operations,
        dry_run=is_preview,
        organize_session_id=organize_session_id,
        session_billing_type=session_billing,
    )
    if index_enabled and operations:
        update_index_from_operations(
            target_root,
            operations,
            session_id=session_id,
            dry_run=is_preview,
        )
        paths = index_paths_for_agent(target_root)
        label = "预览" if is_preview else "归档"
        print(f"[DocMind] 文件索引已更新（{label}）：{paths['markdown']}")

    if not is_preview and auto_empty:
        _prune_empty_dirs(source)

    if not is_preview and operations and not structure_confirmed:
        print(
            "[DocMind] 首次整理已完成。若目录结构满意，请执行确认命令以启用「优先归入已有文件夹」：\n"
            "  python setup.py confirm-structure\n"
            "  或 python scripts/docmind.py confirm-structure"
        )

    return operations
