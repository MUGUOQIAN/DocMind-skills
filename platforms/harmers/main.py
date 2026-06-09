"""
Harmers 平台适配：首次引导配置 + 单文件分类 / 批量整理 / 支付占位。
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.config import load_config  # noqa: E402
from lib.content_extract import extract_preview  # noqa: E402
from lib.organizer import (  # noqa: E402
    begin_organize_session_via_api,
    confirm_archive_structure,
    organize,
)
from lib.setup_wizard import ensure_config, run_setup_wizard  # noqa: E402

PLATFORM = "harmers"
BACKEND_URL = os.getenv("DOCMIND_BACKEND_URL", "http://127.0.0.1:8000")


def _classify_file(
    *,
    platform_user_id: str,
    file_path: str,
    preview_only: bool = False,
    config: dict | None = None,
) -> dict[str, Any]:
    cfg = config or load_config()
    preview_text = extract_preview(file_path)[: int(cfg.get("max_content_chars", 2000))]
    session_id = None
    if not preview_only:
        begin = begin_organize_session_via_api(
            platform_user_id=platform_user_id,
            platform=PLATFORM,
        )
        session_id = begin["organize_session_id"]
    payload = {
        "platform_user_id": platform_user_id,
        "platform": PLATFORM,
        "filename": Path(file_path).name,
        "content_preview": preview_text,
        "industry": cfg.get("industry", ""),
        "job_title": cfg.get("job_title", ""),
        "custom_categories": cfg.get("categories", {}),
        "preview_only": preview_only,
    }
    if session_id:
        payload["organize_session_id"] = session_id
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(f"{BACKEND_URL}/api/v1/classify", json=payload)
        resp.raise_for_status()
        return resp.json()


def create_payment_qr(user_id: str, product: str = "credits_1") -> dict:
    return {
        "user_id": user_id,
        "product": product,
        "qr_url": f"https://pay.example.com/qr?user={user_id}&product={product}",
        "hint": "扫码支付 2 元购买 1 次整理额度",
    }


def notify_payment_webhook(
    platform_user_id: str,
    event: str,
    *,
    credits: int = 1,
    subscription_days: int = 0,
    signature: str = "",
) -> dict:
    payload = {
        "platform_user_id": platform_user_id,
        "event": event,
        "credits": credits,
        "subscription_days": subscription_days,
        "signature": signature,
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"{BACKEND_URL}/api/v1/webhook/payment",
            json=payload,
            headers={"X-Signature": signature},
        )
        resp.raise_for_status()
        return resp.json()


def _get_user_quota(platform_user_id: str) -> dict[str, Any]:
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(f"{BACKEND_URL}/api/v1/user/{platform_user_id}")
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DocMind Harmers Skill")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_setup = sub.add_parser("setup", help="运行配置引导")
    p_setup.add_argument("--force", action="store_true", help="覆盖已有配置")

    p_classify = sub.add_parser("classify")
    p_classify.add_argument("--user-id", required=True)
    p_classify.add_argument("--file", required=True)
    p_classify.add_argument("--preview", action="store_true")
    p_classify.add_argument("--no-setup", action="store_true")

    p_org = sub.add_parser("organize")
    p_org.add_argument("--user-id", required=True)
    p_org.add_argument("--source")
    p_org.add_argument("--desktop", action="store_true")
    p_org.add_argument("--preview", action="store_true")
    p_org.add_argument("--run", action="store_true")
    p_org.add_argument("--no-setup", action="store_true")

    p_pay = sub.add_parser("pay-qr")
    p_pay.add_argument("--user-id", required=True)

    p_quota = sub.add_parser("quota")
    p_quota.add_argument("--user-id", required=True)

    p_confirm = sub.add_parser(
        "confirm-structure",
        help="确认首次整理后的归档目录，此后优先归入已有文件夹",
    )

    args = parser.parse_args()

    if args.cmd == "setup":
        cfg = run_setup_wizard(platform=PLATFORM, force=args.force)
        out = {"config": cfg}
    elif args.cmd == "confirm-structure":
        cfg = confirm_archive_structure()
        out = {
            "structure_confirmed": cfg.get("structure_confirmed"),
            "structure_confirmed_at": cfg.get("structure_confirmed_at"),
        }
    else:
        skip = getattr(args, "no_setup", False)
        cfg = (
            load_config()
            if skip
            else ensure_config(platform=PLATFORM, interactive=True)
        )

        if args.cmd == "classify":
            out = _classify_file(
                args.user_id, args.file, preview_only=args.preview, config=cfg
            )
        elif args.cmd == "organize":
            dry_run = True
            if args.run:
                dry_run = False
            elif not args.preview:
                dry_run = None
            out = organize(
                platform_user_id=args.user_id,
                platform=PLATFORM,
                source_dir=args.source,
                use_desktop=args.desktop,
                config=cfg,
                dry_run=dry_run if args.preview or args.run else None,
            )
        elif args.cmd == "pay-qr":
            out = create_payment_qr(args.user_id)
        else:
            out = _get_user_quota(args.user_id)

    print(json.dumps(out, ensure_ascii=False, indent=2))
