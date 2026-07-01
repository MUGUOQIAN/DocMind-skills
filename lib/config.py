import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path.home() / ".docmind" / "config.json"
EXAMPLE_IN_REPO = Path(__file__).resolve().parents[1] / "config.example.json"


def default_config() -> dict[str, Any]:
    return {
        "industry": "",
        "job_title": "",
        "target_folder": "",
        "archive_root": "",
        "dry_run": True,
        "max_content_chars": 2000,
        "auto_delete_empty": True,
        "recursive": True,
        "structure_confirmed": False,
        "structure_confirmed_at": "",
        "habit_discovery_enabled": False,
        "habit_discovery_at": "",
        "discovered_projects": [],
        "index_enabled": True,
        "index_snippet_chars": 400,
        "index_watch_debounce_secs": 3,
        "auto_monitor_mode": "preview",
        "auto_monitor_debounce_secs": 10,
        "auto_monitor_folder": "",
        "auto_monitor_targets": ["desktop", "downloads"],
        "auto_monitor_folders": [],
        "auto_monitor_ignore_existing": True,
        "shortcut_path": "应用快捷方式",
        "max_path_depth": 4,
        "project_path_depth": 3,
        "categories": {
            "顶层": ["生活", "工作", "应用快捷方式"],
            "生活": ["财务", "日常"],
            "日常子类": [
                "家庭照片",
                "个人笔记",
                "医疗记录",
                "休闲素材",
                "票证存根",
            ],
            "财务生活子类": [
                "银行账单",
                "税务文件",
                "保险合同",
                "投资理财",
                "收入证明",
            ],
            "工作": ["办公", "项目", "技术资料"],
            "办公子类": ["制度文档", "行政表单", "人事档案", "财务单据", "会议记录"],
            "技术资料子类": [
                "设计规范",
                "技术标准",
                "工艺文件",
                "产品手册",
                "技术方案",
                "图纸说明",
            ],
            "项目子类模板": [
                "图纸",
                "业务往来",
                "进出货单",
                "财务票据",
                "记录照片",
            ],
        },
    }


def config_file_exists(path: str | Path | None = None) -> bool:
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    return p.is_file()


def load_config(path: str | Path | None = None, *, use_example_fallback: bool = True) -> dict[str, Any]:
    env_path = os.getenv("DOCMIND_CONFIG")
    candidates = [Path(path) if path else None, Path(env_path) if env_path else None]
    if not path and not env_path:
        candidates.append(DEFAULT_CONFIG_PATH)
    if use_example_fallback:
        candidates.append(EXAMPLE_IN_REPO)

    cfg = default_config()
    for p in candidates:
        if p and Path(p).exists():
            data = json.loads(Path(p).read_text(encoding="utf-8"))
            cfg.update({k: v for k, v in data.items() if k != "categories"})
            if "categories" in data:
                base = default_config()["categories"]
                cats = data["categories"]
                if "个人" in cats and "生活" not in cats:
                    cats = {**cats, "生活": cats.pop("个人")}
                if "公司" in cats and "工作" not in cats:
                    cats = {**cats, "工作": cats.pop("公司")}
                if "生活子类" in cats and "日常子类" not in cats:
                    cats = {**cats, "日常子类": cats["生活子类"]}
                if "财务个人子类" in cats and "财务生活子类" not in cats:
                    cats = {**cats, "财务生活子类": cats["财务个人子类"]}
                cfg["categories"] = {**base, **cats}
            break
    return cfg


def desktop_path() -> Path:
    home = Path.home()
    for name in ("Desktop", "桌面"):
        p = home / name
        if p.is_dir():
            return p
    return home / "Desktop"


def downloads_path() -> Path:
    home = Path.home()
    for name in ("Downloads", "下载", "下载内容"):
        p = home / name
        if p.is_dir():
            return p
    return home / "Downloads"
