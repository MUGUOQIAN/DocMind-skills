#!/usr/bin/env python3
"""Windows 一键安装：写入默认配置并生成稳定用户 ID。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from lib.config import default_config, desktop_path  # noqa: E402
from lib.setup_wizard import save_config  # noqa: E402


def windows_user_id() -> str:
    user = (os.getenv("USERNAME") or os.getenv("USER") or "user").strip()
    computer = (os.getenv("COMPUTERNAME") or "pc").strip()
    safe = lambda s: "".join(c if c.isalnum() or c in "-_" else "-" for c in s)
    return f"win-{safe(user)}-{safe(computer)}".lower()


def main() -> int:
    cfg = default_config()
    desktop = desktop_path()
    cfg["target_folder"] = str(desktop)
    cfg["archive_root"] = str(desktop.parent / "DocMind归档")
    cfg["dry_run"] = True
    path = save_config(cfg)
    payload = {
        "config_path": str(path),
        "user_id": windows_user_id(),
        "target_folder": cfg["target_folder"],
        "archive_root": cfg["archive_root"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
