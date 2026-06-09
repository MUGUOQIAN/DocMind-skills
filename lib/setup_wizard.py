"""DocMind 首次使用引导配置。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .config import DEFAULT_CONFIG_PATH, default_config, desktop_path, load_config
from .habit_discovery import discover_and_merge, format_discovery_summary
from .presets import (
    apply_industry_preset,
    apply_job_preset,
    apply_preset,
    industry_menu_text,
    job_menu_text,
)

ENV_INDUSTRY = "DOCMIND_INDUSTRY"
ENV_JOB_TITLE = "DOCMIND_JOB_TITLE"
ENV_TARGET = "DOCMIND_TARGET_FOLDER"
ENV_ARCHIVE = "DOCMIND_ARCHIVE_ROOT"
ENV_SKIP = "DOCMIND_SKIP_SETUP"
ENV_PRESET = "DOCMIND_INDUSTRY_PRESET"


def config_exists(path: Path | None = None) -> bool:
    p = path or DEFAULT_CONFIG_PATH
    return p.is_file()


def save_config(cfg: dict[str, Any], path: Path | None = None) -> Path:
    target = path or DEFAULT_CONFIG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def _prompt(text: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    value = input(f"{text}{hint}: ").strip()
    return value or default


def _prompt_yn(text: str, default: bool = True) -> bool:
    default_s = "Y" if default else "N"
    value = _prompt(f"{text} (Y/N)", default_s).upper()
    if not value:
        return default
    return value in ("Y", "YES", "是", "1")


def _config_from_env() -> dict[str, Any] | None:
    if os.getenv(ENV_SKIP, "").lower() in ("1", "true", "yes"):
        return None
    industry = os.getenv(ENV_INDUSTRY)
    job_title = os.getenv(ENV_JOB_TITLE)
    target = os.getenv(ENV_TARGET)
    archive = os.getenv(ENV_ARCHIVE)
    preset = os.getenv(ENV_PRESET)
    if not any([industry, job_title, target, archive, preset]):
        return None

    cfg = default_config()
    base_cats = cfg["categories"]
    if preset:
        ind, cats, job = apply_preset(preset.strip(), base_cats)
        cfg["industry"] = industry or ind
        cfg["job_title"] = job_title or job
        cfg["categories"] = cats
    else:
        if industry:
            cfg["industry"] = industry
        if job_title:
            cfg["job_title"] = job_title

    if target:
        cfg["target_folder"] = target
    if archive:
        cfg["archive_root"] = archive
    cfg["dry_run"] = os.getenv("DOCMIND_DRY_RUN", "true").lower() != "false"
    return cfg


def run_setup_wizard(
    *,
    platform: str = "docmind",
    force: bool = False,
    config_path: Path | None = None,
) -> dict[str, Any]:
    path = config_path or DEFAULT_CONFIG_PATH
    if config_exists(path) and not force:
        return load_config(path)

    print()
    print("=" * 50)
    print(f"  DocMind 首次配置引导 ({platform})")
    print("=" * 50)
    print()
    print("请填写行业与职业，用于辅助 AI 分类；文件具体归类仍以内容为准。")
    print()

    cfg = default_config()

    print(industry_menu_text())
    industry_id = _prompt("请选择行业编号", "1")
    industry, categories, suggested_job_id = apply_industry_preset(
        industry_id, cfg["categories"]
    )
    cfg["industry"] = industry
    cfg["categories"] = categories

    custom_industry = _prompt("自定义行业名称（留空则使用上一项）", industry)
    if custom_industry:
        cfg["industry"] = custom_industry

    print()
    print(job_menu_text(suggested_job_id))
    job_id = _prompt("请选择职业编号", suggested_job_id)
    cfg["job_title"] = apply_job_preset(job_id)

    custom_job = _prompt("自定义职业名称（留空则使用上一项）", cfg["job_title"])
    if custom_job:
        cfg["job_title"] = custom_job

    print()
    print("待整理位置：")
    print(f"  [1] 桌面 ({desktop_path()})")
    print("  [2] 指定文件夹")
    print("  [3] 稍后手动指定")
    loc = _prompt("请选择", "1")
    if loc == "2":
        cfg["target_folder"] = _prompt("请输入待整理文件夹完整路径")
    elif loc == "1":
        cfg["target_folder"] = str(desktop_path())

    default_archive = ""
    if cfg["target_folder"]:
        default_archive = str(Path(cfg["target_folder"]).parent / "DocMind归档")
    cfg["archive_root"] = _prompt("归档根目录（整理后文件放入此处）", default_archive)

    print()
    print("习惯学习（可选）：扫描桌面/文档/待整理目录等，提取您已有的文件夹命名习惯，")
    print("新建归档目录时会优先采用这些名称（仍遵守 生活/工作 分类标准）。")
    if _prompt_yn("是否扫描本地已有文件夹学习整理习惯", True):
        merged, discovery = discover_and_merge(
            cfg["categories"],
            target_folder=cfg.get("target_folder", ""),
            archive_root=cfg.get("archive_root", ""),
        )
        cfg["categories"] = merged
        cfg["habit_discovery_enabled"] = True
        cfg["habit_discovery_at"] = discovery.get("scanned_at", "")
        cfg["discovered_projects"] = discovery.get("detected_projects", [])
        print()
        print(format_discovery_summary(discovery))

    cfg["dry_run"] = _prompt_yn("首次使用建议先开启预览模式（不移动文件）", True)
    cfg["recursive"] = _prompt_yn("是否递归整理子文件夹", True)
    cfg["auto_delete_empty"] = _prompt_yn("整理后删除源目录中的空文件夹", True)

    print()
    print("-" * 50)
    print(f"行业：{cfg['industry'] or '（未指定）'}")
    print(f"职业：{cfg['job_title'] or '（未指定）'}")
    print(f"待整理：{cfg['target_folder'] or '（运行时指定）'}")
    print(f"归档到：{cfg['archive_root'] or '（默认 DocMind归档）'}")
    print(f"预览模式：{'是' if cfg['dry_run'] else '否'}")
    print(f"习惯学习：{'是' if cfg.get('habit_discovery_enabled') else '否'}")
    if cfg.get("discovered_projects"):
        print(f"识别项目：{', '.join(cfg['discovered_projects'][:5])}")
    print(f"配置文件：{path}")
    print("-" * 50)

    if not _prompt_yn("确认保存以上配置", True):
        print("已取消，未写入配置。")
        return cfg

    saved = save_config(cfg, path)
    print(f"\n配置已保存：{saved}")
    return cfg


def ensure_config(
    *,
    platform: str = "docmind",
    interactive: bool | None = None,
    config_path: Path | None = None,
) -> dict[str, Any]:
    path = config_path or DEFAULT_CONFIG_PATH
    if config_exists(path):
        return load_config(path)

    env_cfg = _config_from_env()
    if env_cfg:
        save_config(env_cfg, path)
        print(f"[DocMind] 已根据环境变量生成配置：{path}")
        return env_cfg

    if interactive is False:
        return load_config(path)

    if interactive is None:
        interactive = os.getenv(ENV_SKIP, "").lower() not in ("1", "true", "yes")

    if interactive:
        return run_setup_wizard(platform=platform, config_path=path)

    return load_config(path)
