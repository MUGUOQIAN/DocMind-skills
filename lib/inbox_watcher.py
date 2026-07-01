"""监视待整理目录（桌面/下载等），有新文件时自动触发整理。"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .config import desktop_path, load_config
from .index_watcher import _should_skip_path
from .organizer import organize

MONITOR_STATE_FILE = "monitor_state.json"
META_DIR = ".docmind"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def monitor_state_path(source_root: str | Path) -> Path:
    return Path(source_root).resolve() / META_DIR / MONITOR_STATE_FILE


def write_monitor_state(source_root: str | Path, state: dict[str, Any]) -> None:
    path = monitor_state_path(source_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def read_monitor_state(source_root: str | Path) -> dict[str, Any] | None:
    path = monitor_state_path(source_root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clear_monitor_state(source_root: str | Path) -> None:
    path = monitor_state_path(source_root)
    if path.is_file():
        path.unlink()


def resolve_monitor_source(
    *,
    source_dir: str | Path | None = None,
    use_desktop: bool = False,
    config: dict[str, Any] | None = None,
) -> Path:
    cfg = config or load_config()
    if use_desktop:
        return desktop_path()
    if source_dir:
        return Path(source_dir).expanduser().resolve()
    folder = (cfg.get("auto_monitor_folder") or cfg.get("target_folder") or "").strip()
    if folder:
        return Path(folder).expanduser().resolve()
    return desktop_path()


class InboxMonitor:
    """防抖后对待整理目录执行 organize。"""

    def __init__(
        self,
        source_root: Path,
        *,
        platform_user_id: str,
        platform: str,
        mode: str = "preview",
        debounce_sec: float = 10.0,
        config: dict[str, Any] | None = None,
        on_result: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.source_root = source_root.resolve()
        self.platform_user_id = platform_user_id
        self.platform = platform
        self.mode = mode if mode in ("preview", "run") else "preview"
        self.debounce_sec = debounce_sec
        self.config = config or load_config()
        self.on_result = on_result
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._organize_lock = threading.Lock()
        self.runs = 0
        self.last_trigger_at = ""
        self.last_error = ""

    def _emit(self, payload: dict[str, Any]) -> None:
        if self.on_result:
            self.on_result(payload)

    def _cancel_timer(self) -> None:
        with self._lock:
            timer = self._timer
            self._timer = None
        if timer:
            timer.cancel()

    def _schedule_organize(self, reason: str, path: Path) -> None:
        def work() -> None:
            with self._lock:
                self._timer = None
            self._run_organize(reason, path)

        self._cancel_timer()
        timer = threading.Timer(self.debounce_sec, work)
        timer.daemon = True
        with self._lock:
            self._timer = timer
        timer.start()
        self._emit(
            {
                "event": "monitor_scheduled",
                "reason": reason,
                "path": str(path),
                "debounce_sec": self.debounce_sec,
                "mode": self.mode,
            }
        )

    def _run_organize(self, reason: str, path: Path) -> None:
        if not self._organize_lock.acquire(blocking=False):
            self._emit({"event": "monitor_skipped", "reason": "organize_in_progress"})
            return
        try:
            dry_run = self.mode == "preview"
            ops = organize(
                platform_user_id=self.platform_user_id,
                platform=self.platform,
                source_dir=self.source_root,
                config=self.config,
                dry_run=dry_run,
            )
            self.runs += 1
            self.last_trigger_at = _now_iso()
            self.last_error = ""
            self._emit(
                {
                    "event": "monitor_organized",
                    "reason": reason,
                    "trigger_path": str(path),
                    "mode": self.mode,
                    "file_count": len(ops),
                    "operations": ops,
                }
            )
        except Exception as exc:
            self.last_error = str(exc)
            payload: dict[str, Any] = {
                "event": "monitor_error",
                "reason": reason,
                "message": str(exc),
            }
            if hasattr(exc, "payload"):
                payload["billing"] = getattr(exc, "payload")
            self._emit(payload)
        finally:
            self._organize_lock.release()

    def on_file_event(self, action: str, path: Path) -> None:
        if _should_skip_path(path) or META_DIR in path.parts:
            return
        if not path.is_file():
            return
        try:
            path.resolve().relative_to(self.source_root)
        except ValueError:
            return
        self._schedule_organize(action, path)


def _make_inbox_handler(monitor: InboxMonitor):
    from watchdog.events import FileSystemEventHandler

    class Handler(FileSystemEventHandler):
        def on_created(self, event) -> None:
            if not event.is_directory:
                monitor.on_file_event("create", Path(event.src_path))

        def on_modified(self, event) -> None:
            if not event.is_directory:
                monitor.on_file_event("modify", Path(event.src_path))

        def on_moved(self, event) -> None:
            if event.is_directory:
                return
            dest = Path(event.dest_path)
            if dest.is_file():
                monitor.on_file_event("move", dest)

    return Handler()


def run_monitor(
    *,
    platform_user_id: str,
    platform: str,
    source_dir: str | Path | None = None,
    use_desktop: bool = False,
    mode: str | None = None,
    debounce_sec: float | None = None,
    config: dict[str, Any] | None = None,
    log_events: bool = True,
) -> int:
    """阻塞监视待整理目录，有新文件时自动 preview 或 run。"""
    from watchdog.observers import Observer

    cfg = config or load_config()
    root = resolve_monitor_source(
        source_dir=source_dir,
        use_desktop=use_desktop,
        config=cfg,
    )
    if not root.is_dir():
        raise FileNotFoundError(f"待监视目录不存在: {root}")

    effective_mode = mode or cfg.get("auto_monitor_mode", "preview")
    effective_debounce = debounce_sec
    if effective_debounce is None:
        effective_debounce = float(cfg.get("auto_monitor_debounce_secs", 10))

    def on_result(payload: dict[str, Any]) -> None:
        if log_events:
            print(json.dumps(payload, ensure_ascii=False), flush=True)

    monitor = InboxMonitor(
        root,
        platform_user_id=platform_user_id,
        platform=platform,
        mode=effective_mode,
        debounce_sec=effective_debounce,
        config=cfg,
        on_result=on_result,
    )
    handler = _make_inbox_handler(monitor)
    observer = Observer()
    observer.schedule(handler, str(root), recursive=bool(cfg.get("recursive", True)))
    observer.start()

    state = {
        "source_root": str(root),
        "mode": effective_mode,
        "started_at": _now_iso(),
        "last_trigger_at": "",
        "runs": 0,
        "debounce_sec": effective_debounce,
        "pid": __import__("os").getpid(),
    }
    write_monitor_state(root, state)

    if log_events:
        print(
            json.dumps(
                {
                    "event": "monitor_started",
                    "source_root": str(root),
                    "mode": effective_mode,
                    "debounce_sec": effective_debounce,
                    "hint": "preview 模式不移动文件；run 模式每次触发扣 1 次整理会话",
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    try:
        while True:
            time.sleep(2)
            state["last_trigger_at"] = monitor.last_trigger_at
            state["runs"] = monitor.runs
            state["last_error"] = monitor.last_error
            write_monitor_state(root, state)
    except KeyboardInterrupt:
        observer.stop()
        observer.join(timeout=5)
        clear_monitor_state(root)
        if log_events:
            print(
                json.dumps(
                    {
                        "event": "monitor_stopped",
                        "source_root": str(root),
                        "runs": monitor.runs,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        return 0
