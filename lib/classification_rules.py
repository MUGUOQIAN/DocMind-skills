"""DocMind 文档整理分类规则与默认配置。"""

import json
from typing import Any

FALLBACK_PATH = "其他/未分类"
UNNAMED_PROJECT = "未命名项目"
MAX_PATH_DEPTH = 4
PROJECT_PATH_DEPTH = 3

TOP_LIFE = "生活"
TOP_WORK = "工作"
TOP_SHORTCUT = "应用快捷方式"

# 兼容旧版 AI / 配置返回的路径
_LEGACY_TOP = {"个人": TOP_LIFE, "公司": TOP_WORK}

DEFAULT_CATEGORIES: dict[str, Any] = {
    "顶层": [TOP_LIFE, TOP_WORK, TOP_SHORTCUT],
    "生活": ["财务", "日常"],
    "日常子类": ["家庭照片", "个人笔记", "医疗记录", "休闲素材", "票证存根"],
    "财务生活子类": ["银行账单", "税务文件", "保险合同", "投资理财", "收入证明"],
    "工作": ["办公", "项目", "技术资料"],
    "办公子类": ["制度文档", "行政表单", "人事档案", "财务单据", "会议记录"],
    "技术资料子类": ["设计规范", "技术标准", "工艺文件", "产品手册", "技术方案", "图纸说明"],
    "项目子类模板": ["图纸", "业务往来", "进出货单", "财务票据", "记录照片"],
}

RULES_TEXT = f"""
## 顶层：{TOP_LIFE} / {TOP_WORK} / {TOP_SHORTCUT}
先判断文件属于哪一大类（三者互斥）：
- {TOP_LIFE}：与工作无关的私人文件（家庭照片、笔记、医疗、个人银行账单等）
- {TOP_WORK}：与工作/职业相关（合同、项目文档、会议纪要、单位财务等）
- {TOP_SHORTCUT}：程序/网页快捷方式（.lnk、.url），不是快捷方式指向的文档

## {TOP_WORK}层
### 办公（不绑定具体项目）
路径：{TOP_WORK}/办公/{{子类}}

### 技术资料（不绑定具体项目）
路径：{TOP_WORK}/技术资料/{{子类}}
子类：设计规范、技术标准、工艺文件、产品手册、技术方案、图纸说明等

### 项目（优先三级）
路径：{TOP_WORK}/{{项目名称}}/{{子类}}（不要用 {TOP_WORK}/项目/…/… 四级）

## {TOP_LIFE}层
### 财务
路径：{TOP_LIFE}/财务/{{子类}}

### 日常（原私人生活类，勿写成 {TOP_LIFE}/{TOP_LIFE}/…）
路径：{TOP_LIFE}/日常/{{子类}}

### {TOP_SHORTCUT}
路径：{TOP_SHORTCUT}（仅 1 级）

## 目录深度
- 最多 4 级；{TOP_LIFE}、{TOP_WORK} 办公一般为 3 级；{TOP_WORK} 项目为 3 级 {TOP_WORK}/项目名/子类

## 优先级
0. 快捷方式 → {TOP_SHORTCUT}
1. 内容优先于文件名
2. 无法判断 → {FALLBACK_PATH}
"""


def _migrate_category_keys(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    if "个人" in out and "生活" not in out:
        out["生活"] = out.pop("个人")
    if "公司" in out and "工作" not in out:
        out["工作"] = out.pop("公司")
    if "生活子类" in out and "日常子类" not in out:
        out["日常子类"] = out.pop("生活子类")
    if "财务个人子类" in out and "财务生活子类" not in out:
        out["财务生活子类"] = out.pop("财务个人子类")
    if "顶层" in out:
        out["顶层"] = [
            _LEGACY_TOP.get(x, x) for x in out["顶层"]
        ]
    return out


def merge_categories(custom: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(DEFAULT_CATEGORIES)
    if not custom:
        return merged
    data = _migrate_category_keys(custom)
    for key, val in data.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = {**merged[key], **val}
        elif key in merged or key.endswith("子类") or key.endswith("模板") or key == "用户项目名":
            merged[key] = val
    return merged


def build_classification_prompt(
    *,
    filename: str,
    content_preview: str,
    industry: str = "",
    job_title: str = "",
    custom_categories: dict[str, Any] | None = None,
    existing_archive_paths: list[str] | None = None,
) -> str:
    categories = merge_categories(custom_categories)
    profile_lines = []
    if industry:
        profile_lines.append(f"用户行业：{industry}")
    if job_title:
        profile_lines.append(f"用户职业：{job_title}")
    profile_block = "\n".join(profile_lines) + "\n" if profile_lines else ""
    cats_json = json.dumps(categories, ensure_ascii=False, indent=2)

    habit_block = ""
    user_projects = categories.get("用户项目名") if categories else None
    if user_projects:
        names = "、".join(user_projects[:15])
        habit_block = f"""
## 用户已有项目/文件夹命名习惯（来自本机扫描）
整理工作类项目文件时，若内容与下列名称相符，优先使用相同文件夹名，不要擅自改名：
{names}
"""

    existing_block = ""
    if existing_archive_paths:
        lines = "\n".join(f"- {p}" for p in existing_archive_paths[:80])
        if len(existing_archive_paths) > 80:
            lines += f"\n- …（另有 {len(existing_archive_paths) - 80} 个）"
        existing_block = f"""
## 已有归档目录（用户已确认结构）
下列目录已存在，请**优先**选用其中与文件内容最匹配的路径（路径字面尽量与已有目录一致）。
仅当没有任何已有目录能合理容纳该文件时，再按分类标准新建同级目录，或在合适的已有目录下增加子文件夹。

{lines}
"""

    return f"""你是 DocMind 智能文件整理助手。根据文件内容与文件名，返回唯一的目标相对路径。
{profile_block}（行业/职业仅供辅助，分类仍以文件内容为主；若内容与职业不符，以内容为准。）
{habit_block}
{existing_block}
{RULES_TEXT}

用户自定义分类配置（JSON）：
{cats_json}

## 输出要求
- 只输出一行路径，用 / 分隔
- 办公：{TOP_WORK}/办公/会议记录
- 技术资料：{TOP_WORK}/技术资料/技术标准
- 项目：{TOP_WORK}/东方广场改造/图纸
- 财务：{TOP_LIFE}/财务/银行账单
- 日常：{TOP_LIFE}/日常/家庭照片
- 快捷方式：{TOP_SHORTCUT}
- 禁止使用过时的「个人」「公司」作为顶层
- 无法分类：{FALLBACK_PATH}

文件名：{filename}
文件内容预览：
{content_preview or "（无文本内容）"}
"""


def _migrate_legacy_parts(parts: list[str]) -> list[str]:
    if parts and parts[0] in _LEGACY_TOP:
        parts[0] = _LEGACY_TOP[parts[0]]
    if len(parts) >= 3 and parts[0] == TOP_LIFE and parts[1] == TOP_LIFE:
        parts[1] = "日常"
    if len(parts) >= 3 and parts[0] == TOP_LIFE and parts[1] == "生活":
        parts[1] = "日常"
    return parts


def normalize_archive_path(path: str, *, max_depth: int = MAX_PATH_DEPTH) -> str:
    parts = [p.strip() for p in path.replace("\\", "/").split("/") if p.strip()]
    if not parts:
        return FALLBACK_PATH

    parts = _migrate_legacy_parts(parts)

    if parts[0] == "其他" and len(parts) == 1:
        return FALLBACK_PATH

    if parts[0] == TOP_SHORTCUT:
        return TOP_SHORTCUT

    if len(parts) >= 4 and parts[0] == TOP_WORK and parts[1] == "项目":
        parts = [parts[0], parts[2], parts[3], *parts[4:]]

    if len(parts) >= 3 and parts[0] == TOP_WORK and parts[1] in ("办公", "技术资料"):
        parts = parts[:3]

    if parts[0] in (TOP_LIFE, TOP_WORK) and len(parts) > 3:
        if parts[1] in ("办公", "技术资料", "财务", "日常"):
            parts = parts[:3]
        elif parts[0] == TOP_WORK:
            parts = parts[:4]

    if len(parts) > max_depth:
        parts = parts[:max_depth]

    return "/".join(parts)
