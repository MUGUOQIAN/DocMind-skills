#!/usr/bin/env python3
"""DocMind Skill 统一 CLI（DocMind-skills 独立客户端）。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def find_client_root() -> Path:
    """定位 DocMind-skills 仓库根目录（含 lib/organizer.py）。"""
    env = os.getenv("DOCMIND_REPO_ROOT", "").strip()
    if env:
        root = Path(env).expanduser().resolve()
        if (root / "lib" / "organizer.py").is_file():
            return root
        raise SystemExit(
            f"DOCMIND_REPO_ROOT 无效（缺少 lib/organizer.py）: {root}"
        )

    here = Path(__file__).resolve()
    candidates = [here.parent.parent, *here.parents]
    for root in candidates:
        if (root / "lib" / "organizer.py").is_file():
            return root
    raise SystemExit(
        "未找到 DocMind-skills 根目录。请克隆 "
        "https://github.com/MUGUOQIAN/DocMind-skills 并设置 DOCMIND_REPO_ROOT。"
    )


def _run(repo: Path, args: list[str]) -> int:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    proc = subprocess.run(args, cwd=str(repo), env=env)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="DocMind Skill CLI")
    parser.add_argument("--user-id", default=os.getenv("DOCMIND_USER_ID", "default-user"))
    parser.add_argument("--repo", help="DocMind-skills 根目录（覆盖 DOCMIND_REPO_ROOT）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("setup", help="首次配置引导")
    sub.add_parser("discover-habits", help="扫描本机文件夹习惯")
    sub.add_parser("confirm-structure", help="确认归档目录结构")

    p_preview = sub.add_parser("preview", help="预览整理（不移动文件）")
    p_preview.add_argument("--desktop", action="store_true")
    p_preview.add_argument("--folder")

    p_run = sub.add_parser("run", help="执行整理")
    p_run.add_argument("--desktop", action="store_true")
    p_run.add_argument("--folder")

    p_undo = sub.add_parser("undo", help="撤销上次整理")
    p_undo.add_argument("--desktop", action="store_true")
    p_undo.add_argument("--folder")

    sub.add_parser("quota", help="查询后端额度")

    p_search = sub.add_parser("search", help="在文件索引中搜索已整理文件")
    p_search.add_argument("--query", "-q", required=True, help="搜索关键词，如：东方广场 合同")
    p_search.add_argument("--archive", help="限定归档根目录（默认搜索全部已索引归档）")
    p_search.add_argument("--limit", type=int, default=20)

    p_rebuild = sub.add_parser("rebuild-index", help="扫描归档目录重建文件索引")
    p_rebuild.add_argument("--archive", required=True, help="归档根目录")

    args = parser.parse_args()
    if args.repo:
        os.environ["DOCMIND_REPO_ROOT"] = args.repo
    repo = find_client_root()
    py = sys.executable
    uid = args.user_id
    wb = repo / "platforms" / "workbuddy" / "main.py"
    setup = repo / "setup.py"

    if args.cmd == "setup":
        return _run(repo, [py, str(setup), "--platform", "docmind"])
    if args.cmd == "discover-habits":
        return _run(repo, [py, str(setup), "discover-habits"])
    if args.cmd == "confirm-structure":
        return _run(repo, [py, str(setup), "confirm-structure"])

    if args.cmd == "quota":
        import httpx

        base = os.getenv("DOCMIND_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
        r = httpx.get(f"{base}/api/v1/user/{uid}", timeout=30)
        r.raise_for_status()
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
        return 0

    if args.cmd in ("search", "rebuild-index"):
        sys.path.insert(0, str(repo))
        from lib.config import load_config  # noqa: E402
        from lib.file_index import (  # noqa: E402
            index_paths_for_agent,
            rebuild_index_from_archive,
            search_index,
        )

        cfg = load_config()
        archive = args.archive or cfg.get("archive_root") or None
        if args.cmd == "search":
            import httpx

            from lib.billing_client import consume_search_quota  # noqa: E402

            try:
                billing = consume_search_quota(uid, platform="docmind")
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 402:
                    detail = exc.response.json().get("detail", {})
                    print(
                        json.dumps(
                            {
                                "error": "payment_required",
                                "message": detail.get(
                                    "message", "查找额度不足，请充值或订阅。"
                                ),
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                raise
            hits = search_index(args.query, archive_root=archive, limit=args.limit)
            out = {
                "query": args.query,
                "count": len(hits),
                "results": hits,
                "billing": billing,
                "index_paths": index_paths_for_agent(archive) if archive else {},
            }
            if archive:
                out["index_paths"] = index_paths_for_agent(archive)
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        data = rebuild_index_from_archive(archive)
        paths = index_paths_for_agent(archive)
        print(
            json.dumps(
                {
                    "entry_count": data.get("entry_count"),
                    "archive_root": data.get("archive_root"),
                    "index_paths": paths,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    cmd = [py, str(wb), "--user-id", uid, "--no-setup"]
    if args.cmd == "preview":
        cmd.append("--preview")
    elif args.cmd == "run":
        cmd.append("--run")
    elif args.cmd == "undo":
        cmd.append("--undo")

    if getattr(args, "desktop", False):
        cmd.append("--desktop")
    if getattr(args, "folder", None):
        cmd.extend(["--source", args.folder])

    return _run(repo, cmd)


if __name__ == "__main__":
    raise SystemExit(main())
