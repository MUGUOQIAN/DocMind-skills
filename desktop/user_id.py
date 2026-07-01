"""桌面应用稳定用户 ID（计费）。"""

from __future__ import annotations

import os
import platform as plat


def _safe_token(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in value.strip())


def resolve_desktop_user_id() -> str:
    """显式 DOCMIND_USER_ID > 平台前缀 + 用户名 + 主机名。"""
    explicit = os.getenv("DOCMIND_USER_ID", "").strip()
    if explicit and explicit != "default-user":
        return explicit

    user = (os.getenv("USERNAME") or os.getenv("USER") or "user").strip()
    host = (
        os.getenv("COMPUTERNAME")
        or os.getenv("HOSTNAME")
        or plat.node()
        or "device"
    ).strip()

    system = plat.system()
    if system == "Windows":
        prefix = "win"
    elif system == "Darwin":
        prefix = "mac"
    else:
        prefix = "desk"

    return f"{prefix}-{_safe_token(user)}-{_safe_token(host)}".lower()
