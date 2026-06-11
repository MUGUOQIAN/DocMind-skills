#!/usr/bin/env python3
"""DocMind 配置引导入口：python setup.py"""

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from lib.config import DEFAULT_CONFIG_PATH, load_config  # noqa: E402
from lib.habit_discovery import discover_and_merge, format_discovery_summary  # noqa: E402
from lib.organizer import confirm_archive_structure  # noqa: E402
from lib.setup_wizard import config_exists, ensure_config, run_setup_wizard, save_config  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="DocMind 配置引导")
    parser.add_argument(
        "--platform",
        default="workbuddy",
        help="平台标识：workbuddy / openclaw / harmers",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="即使已有配置也重新引导",
    )
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument(
        "--show",
        action="store_true",
        help="显示当前有效配置",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("confirm-structure", "discover-habits"),
        help="confirm-structure / discover-habits",
    )
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH

    if args.command == "confirm-structure":
        cfg = confirm_archive_structure(config_path=config_path)
        print(
            json.dumps(
                {
                    "structure_confirmed": cfg.get("structure_confirmed"),
                    "structure_confirmed_at": cfg.get("structure_confirmed_at"),
                    "config_path": str(config_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "discover-habits":
        cfg = load_config(config_path)
        merged, discovery = discover_and_merge(
            cfg["categories"],
            target_folder=cfg.get("target_folder", ""),
            archive_root=cfg.get("archive_root", ""),
        )
        cfg["categories"] = merged
        cfg["habit_discovery_enabled"] = True
        cfg["habit_discovery_at"] = discovery.get("scanned_at", "")
        cfg["discovered_projects"] = discovery.get("detected_projects", [])
        save_config(cfg, config_path)
        print(format_discovery_summary(discovery))
        print(f"\n配置已更新：{config_path}")
        return

    if args.show:
        print(json.dumps(load_config(config_path), ensure_ascii=False, indent=2))
        return

    if args.force or not config_exists(config_path):
        cfg = run_setup_wizard(
            platform=args.platform,
            force=args.force,
            config_path=config_path,
        )
    else:
        cfg = ensure_config(platform=args.platform, config_path=config_path)

    print(json.dumps({"config_path": str(config_path), "config": cfg}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
