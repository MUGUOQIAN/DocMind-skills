"""桌面/系统快捷方式识别（不调用 AI）。"""

from pathlib import Path

# Windows 常见快捷方式；macOS 可为 .webloc 等，按需扩展
SHORTCUT_SUFFIXES = {".lnk", ".url", ".website"}

DEFAULT_SHORTCUT_PATH = "应用快捷方式"


def is_shortcut(file_path: str | Path) -> bool:
    return Path(file_path).suffix.lower() in SHORTCUT_SUFFIXES


def shortcut_target_path(config: dict | None = None) -> str:
    if config:
        custom = config.get("shortcut_path") or config.get("categories", {}).get(
            "shortcut_path"
        )
        if custom:
            return str(custom).replace("\\", "/")
    return DEFAULT_SHORTCUT_PATH
