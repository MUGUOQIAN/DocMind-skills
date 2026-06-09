"""
腾讯 WorkBuddy Skill：按 DocMind 整理规则整理指定文件夹或桌面。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.config import load_config  # noqa: E402
from lib.organizer import confirm_archive_structure, organize, undo_last  # noqa: E402
from lib.setup_wizard import ensure_config, run_setup_wizard  # noqa: E402

PLATFORM = "workbuddy"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="DocMind WorkBuddy 文件整理")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--source", help="待整理文件夹（默认读配置或桌面）")
    parser.add_argument("--target", help="归档根目录（默认配置 archive_root）")
    parser.add_argument("--desktop", action="store_true", help="整理当前用户桌面")
    parser.add_argument("--preview", action="store_true", help="预览，不移动文件")
    parser.add_argument("--run", action="store_true", help="执行整理（覆盖配置 dry_run）")
    parser.add_argument("--undo", action="store_true", help="撤销上一次整理")
    parser.add_argument("--setup", action="store_true", help="运行配置引导")
    parser.add_argument("--force-setup", action="store_true", help="强制重新引导")
    parser.add_argument("--no-setup", action="store_true", help="跳过首次引导")
    parser.add_argument("--config", help="配置文件路径，默认 ~/.docmind/config.json")
    parser.add_argument(
        "--confirm-structure",
        action="store_true",
        help="确认归档目录结构，此后整理优先归入已有文件夹",
    )
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None

    if args.setup or args.force_setup:
        run_setup_wizard(
            platform=PLATFORM,
            force=args.force_setup,
            config_path=config_path,
        )
        return

    if args.confirm_structure:
        cfg = confirm_archive_structure(config_path=config_path)
        print(
            json.dumps(
                {
                    "structure_confirmed": cfg.get("structure_confirmed"),
                    "structure_confirmed_at": cfg.get("structure_confirmed_at"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.undo:
        cfg = load_config(config_path, use_example_fallback=False)
        root = args.source or cfg.get("target_folder") or ""
        if not root and args.desktop:
            from lib.config import desktop_path

            root = str(desktop_path())
        if not root:
            raise SystemExit("撤销需指定 --source 或配置 target_folder")
        undone = undo_last(root)
        print(json.dumps({"undone": len(undone), "operations": undone}, ensure_ascii=False, indent=2))
        return

    if not args.no_setup:
        cfg = ensure_config(
            platform=PLATFORM,
            interactive=not args.no_setup,
            config_path=config_path,
        )
    else:
        cfg = load_config(config_path)

    dry_run = None
    if args.preview:
        dry_run = True
    elif args.run:
        dry_run = False

    ops = organize(
        platform_user_id=args.user_id,
        platform=PLATFORM,
        source_dir=args.source,
        archive_root=args.target,
        use_desktop=args.desktop,
        config=cfg,
        dry_run=dry_run,
    )
    print(json.dumps(ops, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
