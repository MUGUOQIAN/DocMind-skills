"""监视归档目录变动，增量更新文件索引。"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .file_index import (
    META_DIR,
    index_paths_for_agent,
    remove_index_entries,
    sync_archive_to_index,
    upsert_index_file,
)

logger = logging.getLogger(__name__)

WATCH_STATE_FILE = "watch_state.json"
SKIP_NAMES = {"desktop.ini", "thumbs.db", ".ds_store"}
SKIP_SUFFIXES = {".tmp", ".temp", ".swp", ".partial", ".crdownload", ".download"}
SKIP_PREFIXES = ("~$", ".~")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _should_skip_path(path: Path) -> bool:
    if META_DIR in path.parts:
        return True
    name = path.name.lower()
    if name in SKIP_NAMES:
        return True
    for prefix in SKIP_PREFIXES:
        if name.startswith(prefix):
            return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def watch_state_path(archive_root: str | Path) -> Path:
    return Path(archive_root).resolve() / META_DIR / WATCH_STATE_FILE


def write_watch_state(archive_root: str | Path, state: dict[str, Any]) -> None:
    path = watch_state_path(archive_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def read_watch_state(archive_root: str | Path) -> dict[str, Any] | None:
    path = watch_state_path(archive_root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clear_watch_state(archive_root: str | Path) -> None:
    path = watch_state_path(archive_root)
    if path.is_file():
        path.unlink()


class DebouncedIndexHandler:
    """将文件系统事件防抖后写入索引。"""

    def __init__(
        self,
        archive_root: str | Path,
        *,
        debounce_sec: float = 3.0,
        max_chars: int = 400,
        on_update: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.archive_root = Path(archive_root).resolve()
        self.debounce_sec = debounce_sec
        self.max_chars = max_chars
        self.on_update = on_update
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        self.events_processed = 0
        self.last_event_at = ""

    def _emit(self, payload: dict[str, Any]) -> None:
        self.events_processed += 1
        self.last_event_at = _now_iso()
        if self.on_update:
            self.on_update(payload)

    def _cancel_timer(self, key: str) -> None:
        with self._lock:
            timer = self._timers.pop(key, None)
        if timer:
            timer.cancel()

    def _schedule(self, key: str, action: str, path: Path, src: Path | None = None) -> None:
        def work() -> None:
            try:
                self._apply(action, path, src)
            finally:
                with self._lock:
                    self._timers.pop(key, None)

        self._cancel_timer(key)
        timer = threading.Timer(self.debounce_sec, work)
        with self._lock:
            self._timers[key] = timer
        timer.daemon = True
        timer.start()

    def _apply(self, action: str, path: Path, src: Path | None) -> None:
        root = self.archive_root
        if action == "delete":
            remove_index_entries(root, [str(path)])
            self._emit({"action": "delete", "path": str(path)})
            return
        if action == "move" and src:
            remove_index_entries(root, [str(src)])
            path = path
        if not path.is_file() or _should_skip_path(path):
            return
        try:
            path.resolve().relative_to(root)
        except ValueError:
            return
        entry = upsert_index_file(
            root,
            path,
            max_chars=self.max_chars,
            session_id="watch",
        )
        if entry:
            self._emit({"action": action, "path": str(path), "entry": entry})

    def on_created(self, path: Path) -> None:
        if _should_skip_path(path):
            return
        self._schedule(str(path), "create", path)

    def on_modified(self, path: Path) -> None:
        if _should_skip_path(path) or not path.is_file():
            return
        self._schedule(str(path), "modify", path)

    def on_deleted(self, path: Path) -> None:
        if _should_skip_path(path):
            return
        self._schedule(str(path), "delete", path)

    def on_moved(self, src: Path, dest: Path) -> None:
        if not _should_skip_path(src):
            self._schedule(str(src), "delete", src)
        if dest.is_file() and not _should_skip_path(dest):
            self._schedule(str(dest), "move", dest, src)


def _make_watchdog_handler(delegate: DebouncedIndexHandler):
    from watchdog.events import FileSystemEventHandler

    class Handler(FileSystemEventHandler):
        def on_created(self, event) -> None:
            if not event.is_directory:
                delegate.on_created(Path(event.src_path))

        def on_modified(self, event) -> None:
            if not event.is_directory:
                delegate.on_modified(Path(event.src_path))

        def on_deleted(self, event) -> None:
            if not event.is_directory:
                delegate.on_deleted(Path(event.src_path))

        def on_moved(self, event) -> None:
            if not event.is_directory:
                delegate.on_moved(Path(event.src_path), Path(event.dest_path))

    return Handler()


def run_watch(
    archive_root: str | Path,
    *,
    debounce_sec: float = 3.0,
    max_chars: int = 400,
    sync_on_start: bool = False,
    log_events: bool = True,
) -> int:
    """阻塞运行监视，直到 KeyboardInterrupt。"""
    from watchdog.observers import Observer

    root = Path(archive_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"归档目录不存在: {root}")

    if sync_on_start:
        stats = sync_archive_to_index(root, max_chars=max_chars, session_id="watch-bootstrap")
        if log_events:
            print(
                json.dumps(
                    {"event": "bootstrap", "archive_root": str(root), **stats},
                    ensure_ascii=False,
                ),
                flush=True,
            )

    def on_update(payload: dict[str, Any]) -> None:
        if log_events:
            print(json.dumps({"event": "index_update", **payload}, ensure_ascii=False), flush=True)

    delegate = DebouncedIndexHandler(
        root,
        debounce_sec=debounce_sec,
        max_chars=max_chars,
        on_update=on_update,
    )
    handler = _make_watchdog_handler(delegate)
    observer = Observer()
    observer.schedule(handler, str(root), recursive=True)
    observer.start()

    state = {
        "archive_root": str(root),
        "started_at": _now_iso(),
        "last_event_at": "",
        "events_processed": 0,
        "debounce_sec": debounce_sec,
        "pid": __import__("os").getpid(),
        "index_paths": index_paths_for_agent(root),
    }
    write_watch_state(root, state)

    if log_events:
        print(
            json.dumps(
                {
                    "event": "watch_started",
                    "archive_root": str(root),
                    "debounce_sec": debounce_sec,
                    "index_paths": state["index_paths"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    try:
        while True:
            time.sleep(2)
            state["last_event_at"] = delegate.last_event_at
            state["events_processed"] = delegate.events_processed
            write_watch_state(root, state)
    except KeyboardInterrupt:
        observer.stop()
        observer.join(timeout=5)
        clear_watch_state(root)
        if log_events:
            print(
                json.dumps(
                    {
                        "event": "watch_stopped",
                        "archive_root": str(root),
                        "events_processed": delegate.events_processed,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        return 0
