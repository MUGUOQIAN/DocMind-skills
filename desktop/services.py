"""桌面应用业务层：封装 lib 调用。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import httpx

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from lib.config import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    config_file_exists,
    desktop_path,
    downloads_path,
    load_config,
)
from lib.constants import backend_url  # noqa: E402
from lib.file_index import search_index  # noqa: E402
from lib.organizer import organize, undo_last  # noqa: E402
from lib.payment_hint import PaymentRequiredError  # noqa: E402
from lib.archive_location import (  # noqa: E402
    parse_archive_from_config,
    suggest_archive_paths,
    validate_archive_root,
)
from lib.setup_wizard import save_config  # noqa: E402

from .user_id import resolve_desktop_user_id  # noqa: E402

PLATFORM = "desktop"


def repo_root() -> Path:
    return _REPO


def open_path_in_explorer(path: str | Path) -> None:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"路径不存在: {p}")
    system = sys.platform
    if system == "win32":
        os.startfile(p)  # type: ignore[attr-defined]
    elif system == "darwin":
        subprocess.run(["open", str(p)], check=False)
    else:
        subprocess.run(["xdg-open", str(p)], check=False)


class DocMindService:
    def __init__(self) -> None:
        os.environ.setdefault("DOCMIND_PLATFORM", PLATFORM)
        self.user_id = resolve_desktop_user_id()
        os.environ.setdefault("DOCMIND_USER_ID", self.user_id)

    def config_path(self) -> Path:
        return DEFAULT_CONFIG_PATH

    def load_config(self) -> dict[str, Any]:
        return load_config(use_example_fallback=False)

    def has_config(self) -> bool:
        return config_file_exists()

    def init_default_config(self) -> dict[str, Any]:
        from lib.config import default_config

        cfg = default_config()
        desktop = desktop_path()
        cfg["target_folder"] = str(desktop)
        env_archive = os.getenv("DOCMIND_ARCHIVE_ROOT", "").strip()
        if env_archive:
            cfg["archive_root"] = env_archive
        else:
            suggestions = suggest_archive_paths(str(desktop))
            cfg["archive_root"] = suggestions[0] if suggestions else ""
        cfg["dry_run"] = True
        save_config(cfg)
        return cfg

    def archive_root(self) -> str:
        return parse_archive_from_config(self.load_config())

    def save_archive_root(self, archive_root: str) -> dict[str, Any]:
        cfg = self.load_config() if self.has_config() else self.init_default_config()
        resolved = validate_archive_root(archive_root, create=True)
        cfg["archive_root"] = str(resolved)
        save_config(cfg)
        return cfg

    def save_settings(
        self,
        *,
        target_folder: str,
        archive_root: str,
        industry: str = "",
        job_title: str = "",
    ) -> dict[str, Any]:
        cfg = self.load_config() if self.has_config() else self.init_default_config()
        cfg["target_folder"] = target_folder.strip()
        if archive_root.strip():
            cfg["archive_root"] = str(
                validate_archive_root(archive_root.strip(), create=True)
            )
        cfg["industry"] = industry.strip()
        cfg["job_title"] = job_title.strip()
        save_config(cfg)
        return cfg

    def default_source_paths(self) -> dict[str, str]:
        return {
            "desktop": str(desktop_path()),
            "downloads": str(downloads_path()),
        }

    def resolve_source(
        self, choice: str, custom_path: str | None = None
    ) -> tuple[Path, bool]:
        if choice == "desktop":
            return desktop_path(), True
        if choice == "downloads":
            return downloads_path(), False
        path = Path((custom_path or "").strip()).expanduser()
        if not path.is_dir():
            raise FileNotFoundError(f"目录不存在: {path}")
        return path.resolve(), False

    def preview(
        self,
        *,
        source_choice: str = "desktop",
        custom_path: str | None = None,
    ) -> list[dict[str, Any]]:
        cfg = self.load_config()
        if not parse_archive_from_config(cfg):
            raise ValueError("请先在「设置」中选择整理后文件的保存目录")
        source, use_desktop = self.resolve_source(source_choice, custom_path)
        return organize(
            platform_user_id=self.user_id,
            platform=PLATFORM,
            source_dir=str(source),
            use_desktop=use_desktop,
            config=cfg,
            dry_run=True,
        )

    def run_organize(
        self,
        *,
        source_choice: str = "desktop",
        custom_path: str | None = None,
    ) -> list[dict[str, Any]]:
        cfg = self.load_config()
        if not parse_archive_from_config(cfg):
            raise ValueError("请先在「设置」中选择整理后文件的保存目录")
        source, use_desktop = self.resolve_source(source_choice, custom_path)
        return organize(
            platform_user_id=self.user_id,
            platform=PLATFORM,
            source_dir=str(source),
            use_desktop=use_desktop,
            config=cfg,
            dry_run=False,
        )

    def undo(self, source_root: str | Path) -> list[dict[str, Any]]:
        return undo_last(source_root)

    def fetch_quota(self) -> dict[str, Any]:
        url = f"{backend_url()}/api/v1/user/{self.user_id}"
        r = httpx.get(url, timeout=30)
        r.raise_for_status()
        return r.json()

    def search(self, query: str, *, limit: int = 30) -> list[dict[str, Any]]:
        cfg = self.load_config()
        archive = cfg.get("archive_root") or None
        return search_index(query, archive_root=archive, limit=limit)

    def run_in_thread(
        self,
        fn: Callable[[], Any],
        *,
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        import threading

        def worker() -> None:
            try:
                result = fn()
            except Exception as exc:
                on_error(exc)
            else:
                on_success(result)

        threading.Thread(target=worker, daemon=True).start()
