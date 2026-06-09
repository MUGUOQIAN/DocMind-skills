"""Skill 端调用 DocMind 计费 API。"""

from __future__ import annotations

import os

import httpx

BACKEND_URL = os.getenv("DOCMIND_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


def consume_search_quota(
    platform_user_id: str,
    *,
    platform: str = "docmind",
) -> dict:
    """每次 search 前扣减 1 次查找额度。"""
    r = httpx.post(
        f"{BACKEND_URL}/api/v1/search/consume",
        json={"platform_user_id": platform_user_id, "platform": platform},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()
