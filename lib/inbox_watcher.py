"""监视待整理目录（桌面/下载/指定目录），有新文件时自动触发整理。"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .config import DEFAULT_CONFIG_PATH, desktop_path, downloads_path, load_config
from .index_watcher import _should_skip_path
from .organizer import organize

MONITOR_STATE_FILE = "monitor_state.json"
GLOBAL_MONITOR_STATE = DEFAULT_CONFIG_PATH.parent / "auto_monitor_state.json"
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


def write_global_monitor_state(state: dict[str, Any]) -> None:
    GLOBAL_MONITOR_STATE.parent.mkdir(parents=True, exist_ok=True)
    GLOBAL_MONITOR_STATE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def read_global_monitor_state() -> dict[str, Any] | None:
    if not GLOBAL_MONITOR_STATE.is_file():
        return None
    return json.loads(GLOBAL_MONITOR_STATE.read_text(encoding="utf-8"))


def clear_global_monitor_state() -> None:
    if GLOBAL_MONITOR_STATE.is_file():
        GLOBAL_MONITOR_STATE.unlink()


def _snapshot_files(root: Path, *, recursive: bool) -> set[str]:
    files: set[str] = set()
    if not root.is_dir():
        return files
    if recursive:
        for p in root.rglob("*"):
            if p.is_file() and META_DIR not in p.parts and not _should_skip_path(p):
                files.add(str(p.resolve()))
    else:
        for p in root.iterdir():
            if p.is_file() and not _should_skip_path(p):
                files.add(str(p.resolve()))
    return files


def resolve_monitor_targets(
    *,
    use_desktop: bool = False,
    use_downloads: bool = False,
    use_all: bool = False,
    folders: list[str] | None = None,
    source_dir: str | Path | None = None,
    config: dict[str, Any] | None = None,
) -> list[Path]:
    """解析要监视的一个或多个目录（去重、仅保留存在的路径）。"""
    cfg = config or load_config()
    paths: list[Path] = []

    def add(path: str | Path | None) -> None:
        if not path:
            return
        p = Path(path).expanduser().resolve()
        if p.is_dir() and p not in paths:
            paths.append(p)

    if source_dir:
        add(source_dir)
        return paths

    if folders:
        for f in folders:
            add(f)
        if paths:
            return paths

    if use_all:
        for key in cfg.get("auto_monitor_targets") or ["desktop", "downloads"]:
            k = str(key).strip().lower()
            if k == "desktop":
                add(desktop_path())
            elif k == "downloads":
                add(downloads_path())
            else:
                add(key)
        for f in cfg.get("auto_monitor_folders") or []:
            add(f)
        if paths:
            return paths

    if use_desktop:
        add(desktop_path())
    if use_downloads:
        add(downloads_path())

    for f in cfg.get("auto_monitor_folders") or []:
        add(f)

    if not paths:
        legacy = (cfg.get("auto_monitor_folder") or cfg.get("target_folder") or "").strip()
        if legacy:
            add(legacy)
        else:
            add(desktop_path())

    return paths


def resolve_monitor_source(
    *,
    source_dir: str | Path | None = None,
    use_desktop: bool = False,
    use_downloads: bool = False,
    config: dict[str, Any] | None = None,
) -> Path:
    """单目录解析（兼容旧 CLI）。"""
    targets = resolve_monitor_targets(
        use_desktop=use_desktop,
        use_downloads=use_downloads,
        source_dir=source_dir,
        config=config,
    )
    if not targets:
        raise FileNotFoundError("未找到可监视的目录")
    return targets[0]


def collect_monitor_status(
    *,
    targets: list[Path] | None = None,
    config: dict[str, Any] | None = None,
    use_all: bool = False,
) -> dict[str, Any]:
    cfg = config or load_config()
    dirs = targets or resolve_monitor_targets(use_all=True, config=cfg)
    entries = []
    for p in dirs:
        state = read_monitor_state(p)
        entries.append(
            {
                "source_root": str(p),
                "label": _folder_label(p),
                "watching": state is not None,
                "state": state,
            }
        )
    global_state = read_global_monitor_state()
    return {
        "watching_any": any(e["watching"] for e in entries),
        "global_state": global_state,
        "folders": entries,
        "configured_targets": cfg.get("auto_monitor_targets", ["desktop", "downloads"]),
        "configured_folders": cfg.get("auto_monitor_folders", []),
    }


def _folder_label(path: Path) -> str:
    try:
        if path.resolve() == desktop_path().resolve():
            return "desktop"
    except OSError:
        pass
    try:
        if path.resolve() == downloads_path().resolve():
            return "downloads"
    except OSError:
        pass
    return path.name or str(path)


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
        ignore_existing: bool = True,
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
        self._baseline: set[str] = set()
        if ignore_existing:
            self._baseline = _snapshot_files(
                self.source_root,
                recursive=bool(self.config.get("recursive", True)),
            )

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
                "source_root": str(self.source_root),
                "label": _folder_label(self.source_root),
                "reason": reason,
                "path": str(path),
                "debounce_sec": self.debounce_sec,
                "mode": self.mode,
            }
        )

    def _run_organize(self, reason: str, path: Path) -> None:
        if not self._organize_lock.acquire(blocking=False):
            self._emit(
                {
                    "event": "monitor_skipped",
                    "source_root": str(self.source_root),
                    "reason": "organize_in_progress",
                }
            )
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
            for op in ops:
                self._baseline.discard(str(Path(op["source"]).resolve()))
            self._emit(
                {
                    "event": "monitor_organized",
                    "source_root": str(self.source_root),
                    "label": _folder_label(self.source_root),
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
                "source_root": str(self.source_root),
                "label": _folder_label(self.source_root),
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
        key = str(path.resolve())
        if action == "delete":
            self._baseline.discard(key)
            return
        if key in self._baseline:
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
    use_downloads: bool = False,
    use_all: bool = False,
    folders: list[str] | None = None,
    mode: str | None = None,
    debounce_sec: float | None = None,
    config: dict[str, Any] | None = None,
    log_events: bool = True,
) -> int:
    """阻塞监视一个或多个待整理目录，有新文件时自动 preview 或 run。"""
    from watchdog.observers import Observer

    cfg = config or load_config()
    targets = resolve_monitor_targets(
        use_desktop=use_desktop,
        use_downloads=use_downloads,
        use_all=use_all,
        folders=folders,
        source_dir=source_dir,
        config=cfg,
    )
    if not targets:
        raise FileNotFoundError("未找到可监视的目录，请检查 --desktop / --downloads / --folder")

    effective_mode = mode or cfg.get("auto_monitor_mode", "preview")
    effective_debounce = debounce_sec
    if effective_debounce is None:
        effective_debounce = float(cfg.get("auto_monitor_debounce_secs", 10))
    ignore_existing = bool(cfg.get("auto_monitor_ignore_existing", True))

    def on_result(payload: dict[str, Any]) -> None:
        if log_events:
            print(json.dumps(payload, ensure_ascii=False), flush=True)

    monitors: list[InboxMonitor] = []
    observers: list[Any] = []
    recursive = bool(cfg.get("recursive", True))

    for root in targets:
        monitor = InboxMonitor(
            root,
            platform_user_id=platform_user_id,
            platform=platform,
            mode=effective_mode,
            debounce_sec=effective_debounce,
            config=cfg,
            on_result=on_result,
            ignore_existing=ignore_existing,
        )
        handler = _make_inbox_handler(monitor)
        observer = Observer()
        observer.schedule(handler, str(root), recursive=recursive)
        observer.start()
        monitors.append(monitor)
        observers.append(observer)
        write_monitor_state(
            root,
            {
                "source_root": str(root),
                "label": _folder_label(root),
                "mode": effective_mode,
                "started_at": _now_iso(),
                "last_trigger_at": "",
                "runs": 0,
                "debounce_sec": effective_debounce,
                "ignore_existing": ignore_existing,
                "pid": __import__("os").getpid(),
            },
        )

    global_state = {
        "started_at": _now_iso(),
        "mode": effective_mode,
        "debounce_sec": effective_debounce,
        "ignore_existing": ignore_existing,
        "pid": __import__("os").getpid(),
        "folders": [
            {
                "source_root": str(m.source_root),
                "label": _folder_label(m.source_root),
                "baseline_files": len(m._baseline),
            }
            for m in monitors
        ],
    }
    write_global_monitor_state(global_state)

    if log_events:
        print(
            json.dumps(
                {
                    "event": "monitor_started",
                    "mode": effective_mode,
                    "debounce_sec": effective_debounce,
                    "ignore_existing": ignore_existing,
                    "folders": global_state["folders"],
                    "hint": "仅整理监视启动后新增的文件；run 模式每次触发扣 1 次整理会话",
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    try:
        while True:
            time.sleep(2)
            folder_states = []
            for monitor, root in zip(monitors, targets):
                state = {
                    "source_root": str(root),
                    "label": _folder_label(root),
                    "last_trigger_at": monitor.last_trigger_at,
                    "runs": monitor.runs,
                    "last_error": monitor.last_error,
                }
                folder_states.append(state)
                write_monitor_state(
                    root,
                    {
                        **state,
                        "mode": effective_mode,
                        "started_at": global_state["started_at"],
                        "debounce_sec": effective_debounce,
                        "ignore_existing": ignore_existing,
                        "pid": global_state["pid"],
                    },
                )
            global_state["folders"] = folder_states
            global_state["updated_at"] = _now_iso()
            write_global_monitor_state(global_state)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join(timeout=5)
        for root in targets:
            clear_monitor_state(root)
        clear_global_monitor_state()
        if log_events:
            print(
                json.dumps(
                    {
                        "event": "monitor_stopped",
                        "folders": [str(p) for p in targets],
                        "total_runs": sum(m.runs for m in monitors),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        return 0
