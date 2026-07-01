#!/usr/bin/env python3
"""DocMind Skill 统一 CLI（DocMind-skills 独立客户端）。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _monitor_selection(args) -> dict:
    """根据 CLI 参数解析 monitor / monitor-status 的目录选择。"""
    folders = getattr(args, "folders", None) or None
    use_desktop = bool(getattr(args, "desktop", False))
    use_downloads = bool(getattr(args, "downloads", False))
    use_all = bool(getattr(args, "all", False))
    source_dir = folders[0] if folders and len(folders) == 1 and not (
        use_desktop or use_downloads or use_all
    ) else None
    if folders and len(folders) > 1:
        source_dir = None
    if not (use_desktop or use_downloads or use_all or folders or source_dir):
        use_all = True
    return {
        "use_desktop": use_desktop,
        "use_downloads": use_downloads,
        "use_all": use_all,
        "folders": folders if folders and not source_dir else None,
        "source_dir": source_dir,
    }


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
    parser.add_argument("--user-id", default=None)
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
    p_rebuild.add_argument("--archive", help="归档根目录（默认读配置）")

    p_watch = sub.add_parser("watch", help="监视归档目录变动并增量更新索引")
    p_watch.add_argument("--archive", help="归档根目录（默认读配置 archive_root）")
    p_watch.add_argument(
        "--debounce",
        type=float,
        default=None,
        help="防抖秒数（默认 3，或配置 index_watch_debounce_secs）",
    )
    p_watch.add_argument(
        "--sync-on-start",
        action="store_true",
        help="启动时先增量同步现有文件到索引",
    )

    sub.add_parser("watch-status", help="查看归档目录索引监视状态")

    p_monitor = sub.add_parser("monitor", help="监视待整理目录，有新文件时自动整理")
    p_monitor.add_argument("--desktop", action="store_true", help="监视桌面")
    p_monitor.add_argument("--downloads", action="store_true", help="监视下载文件夹")
    p_monitor.add_argument(
        "--all",
        action="store_true",
        help="监视配置中的 desktop+downloads+auto_monitor_folders（无参数时默认）",
    )
    p_monitor.add_argument(
        "--folder",
        action="append",
        dest="folders",
        metavar="PATH",
        help="指定待整理目录，可多次使用",
    )
    p_monitor.add_argument(
        "--mode",
        choices=("preview", "run"),
        help="preview 不移动；run 自动归档（每次触发扣 1 次整理会话）",
    )
    p_monitor.add_argument(
        "--debounce",
        type=float,
        default=None,
        help="防抖秒数（默认 10 或配置 auto_monitor_debounce_secs）",
    )

    p_ms = sub.add_parser("monitor-status", help="查看待整理目录自动监视状态")
    p_ms.add_argument("--desktop", action="store_true")
    p_ms.add_argument("--downloads", action="store_true")
    p_ms.add_argument("--all", action="store_true")
    p_ms.add_argument("--folder", action="append", dest="folders", metavar="PATH")
    sub.add_parser("products", help="查询可购 SKU（402 时展示）")
    sub.add_parser("gui", help="启动桌面图形应用（macOS / Windows）")

    args = parser.parse_args()
    if args.repo:
        os.environ["DOCMIND_REPO_ROOT"] = args.repo
    repo = find_client_root()
    sys.path.insert(0, str(repo))
    from lib.constants import platform_name, resolve_user_id  # noqa: E402

    py = sys.executable
    uid = resolve_user_id(args.user_id)
    platform = platform_name()
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

        from lib.constants import backend_url  # noqa: E402

        r = httpx.get(f"{backend_url()}/api/v1/user/{uid}", timeout=30)
        r.raise_for_status()
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "products":
        from lib.payment_hint import fetch_products  # noqa: E402

        print(json.dumps({"products": fetch_products()}, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "gui":
        return _run(repo, [py, str(repo / "desktop" / "main.py")])

    if args.cmd in ("search", "rebuild-index", "watch", "watch-status", "monitor", "monitor-status"):
        sys.path.insert(0, str(repo))
        from lib.config import load_config  # noqa: E402
        from lib.file_index import (  # noqa: E402
            index_paths_for_agent,
            rebuild_index_from_archive,
            search_index,
        )

        cfg = load_config()
        archive = getattr(args, "archive", None) or cfg.get("archive_root") or None

        if args.cmd == "monitor-status":
            from lib.inbox_watcher import collect_monitor_status, resolve_monitor_targets  # noqa: E402

            sel = _monitor_selection(args)
            if sel["use_all"] and not (
                sel["use_desktop"] or sel["use_downloads"] or sel["folders"] or sel["source_dir"]
            ):
                status = collect_monitor_status(use_all=True, config=cfg)
            else:
                targets = resolve_monitor_targets(**sel, config=cfg)
                status = collect_monitor_status(targets=targets, config=cfg)
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return 0

        if args.cmd == "monitor":
            from lib.inbox_watcher import run_monitor  # noqa: E402

            sel = _monitor_selection(args)
            try:
                return run_monitor(
                    platform_user_id=uid,
                    platform=platform,
                    mode=getattr(args, "mode", None),
                    debounce_sec=getattr(args, "debounce", None),
                    config=cfg,
                    **sel,
                )
            except ImportError:
                print(
                    "缺少 watchdog 依赖，请执行: pip install watchdog",
                    file=sys.stderr,
                )
                return 1

        if args.cmd == "watch-status":
            from lib.index_watcher import read_watch_state  # noqa: E402

            if not archive:
                raise SystemExit("请指定 --archive 或在配置中设置 archive_root")
            state = read_watch_state(archive)
            out = {
                "archive_root": str(Path(archive).resolve()),
                "watching": state is not None,
                "state": state,
                "index_paths": index_paths_for_agent(archive),
            }
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0

        if args.cmd == "watch":
            from lib.index_watcher import run_watch  # noqa: E402

            if not archive:
                raise SystemExit("请指定 --archive 或在配置中设置 archive_root")
            debounce = args.debounce
            if debounce is None:
                debounce = float(cfg.get("index_watch_debounce_secs", 3))
            max_chars = int(cfg.get("index_snippet_chars", 400))
            try:
                return run_watch(
                    archive,
                    debounce_sec=debounce,
                    max_chars=max_chars,
                    sync_on_start=args.sync_on_start,
                )
            except ImportError:
                print(
                    "缺少 watchdog 依赖，请执行: pip install watchdog",
                    file=sys.stderr,
                )
                return 1

        if args.cmd == "rebuild-index" and not archive:
            raise SystemExit("rebuild-index 需要 --archive 或在配置中设置 archive_root")
        if args.cmd == "search":
            import httpx

            from lib.billing_client import consume_search_quota  # noqa: E402

            from lib.payment_hint import payment_required_payload  # noqa: E402

            try:
                billing = consume_search_quota(uid, platform=platform)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 402:
                    detail = exc.response.json().get("detail", {})
                    msg = detail.get("message", "查找额度不足，请充值或订阅。")
                    print(
                        json.dumps(
                            payment_required_payload(msg),
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

    os.environ.setdefault("DOCMIND_PLATFORM", "workbuddy")
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
