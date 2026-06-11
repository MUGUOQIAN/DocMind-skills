"""DocMind Skill 共享常量。"""

from __future__ import annotations

import os

DEFAULT_BACKEND_URL = "https://api.blt3d.cn"
DEFAULT_PLATFORM = "workbuddy"


def backend_url() -> str:
    return os.getenv("DOCMIND_BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")


def platform_name(*, default: str | None = None) -> str:
    env = os.getenv("DOCMIND_PLATFORM", "").strip()
    if env:
        return env
    return default or DEFAULT_PLATFORM


def resolve_user_id(explicit: str | None = None) -> str:
    """平台用户 ID：显式参数 > DOCMIND_USER_ID > CodeBuddy/Claude 会话 ID。"""
    if explicit and explicit.strip() and explicit.strip() != "default-user":
        return explicit.strip()
    for key in (
        "DOCMIND_USER_ID",
        "CODEBUDDY_SESSION_ID",
        "CLAUDE_SESSION_ID",
    ):
        value = os.getenv(key, "").strip()
        if value:
            return value
    if explicit and explicit.strip():
        return explicit.strip()
    return "default-user"
