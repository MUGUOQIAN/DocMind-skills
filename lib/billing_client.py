"""Skill 端调用 DocMind 计费 API。"""

from __future__ import annotations

import httpx

from .constants import backend_url, platform_name

BACKEND_URL = backend_url()


def consume_search_quota(
    platform_user_id: str,
    *,
    platform: str | None = None,
) -> dict:
    platform = platform or platform_name()
    """每次 search 前扣减 1 次查找额度。"""
    r = httpx.post(
        f"{BACKEND_URL}/api/v1/search/consume",
        json={"platform_user_id": platform_user_id, "platform": platform},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()
