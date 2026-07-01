"""402 付费提示与产品目录。"""

from __future__ import annotations

from typing import Any

import httpx

from .constants import backend_url


def fetch_products() -> list[dict[str, Any]]:
    r = httpx.get(f"{backend_url()}/api/v1/products", timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("products", []) if isinstance(data, dict) else []


def payment_required_payload(
    message: str,
    *,
    include_products: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": "payment_required",
        "message": message,
    }
    if include_products:
        try:
            payload["products"] = fetch_products()
        except Exception as exc:
            payload["products"] = []
            payload["products_error"] = str(exc)
    return payload


class PaymentRequiredError(RuntimeError):
    """额度不足；payload 含 products 供 Agent/CLI 展示。"""

    def __init__(self, message: str, *, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.payload = payload or payment_required_payload(message)
