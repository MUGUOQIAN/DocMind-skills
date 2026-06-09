"""常见工作型行业与职业预设（按使用频率排序）。"""

from typing import Any

# 常见工作型行业（优先级从高到低）
INDUSTRY_PRESETS: dict[str, dict[str, Any]] = {
    "1": {
        "label": "信息传输、软件和信息技术服务业",
        "industry": "信息传输、软件和信息技术服务业",
        "suggested_job": "1",
        "categories": {
            "项目子类模板": [
                "代码仓库",
                "设计文档",
                "测试报告",
                "部署脚本",
                "会议记录",
            ],
        },
    },
    "2": {
        "label": "制造业",
        "industry": "制造业",
        "suggested_job": "5",
        "categories": {
            "项目子类模板": [
                "图纸",
                "工艺文件",
                "质检报告",
                "进出货单",
                "生产记录",
            ],
        },
    },
    "3": {
        "label": "建筑业",
        "industry": "建筑业",
        "suggested_job": "1",
        "categories": {
            "项目子类模板": [
                "图纸",
                "业务往来",
                "进出货单",
                "财务票据",
                "记录照片",
            ],
        },
    },
    "4": {
        "label": "金融业",
        "industry": "金融业",
        "suggested_job": "3",
        "categories": {
            "办公子类": [
                "制度文档",
                "合规文件",
                "客户资料",
                "财务单据",
                "会议记录",
            ],
        },
    },
    "5": {
        "label": "科学研究和技术服务业",
        "industry": "科学研究和技术服务业",
        "suggested_job": "1",
        "categories": {
            "技术资料子类": [
                "设计规范",
                "技术标准",
                "实验数据",
                "技术方案",
                "论文草稿",
            ],
        },
    },
    "6": {
        "label": "教育",
        "industry": "教育",
        "suggested_job": "1",
        "categories": {
            "办公子类": [
                "教学大纲",
                "教案",
                "试卷",
                "学生名单",
                "教研活动",
            ],
            "项目子类模板": [
                "课题资料",
                "论文草稿",
                "课件PPT",
                "实验数据",
                "会议记录",
            ],
        },
    },
    "7": {
        "label": "卫生和社会工作",
        "industry": "卫生和社会工作",
        "suggested_job": "1",
        "categories": {
            "办公子类": [
                "病历档案",
                "诊疗记录",
                "体检报告",
                "公共卫生",
                "会议记录",
            ],
        },
    },
    "8": {
        "label": "批发和零售业",
        "industry": "批发和零售业",
        "suggested_job": "4",
        "categories": {
            "项目子类模板": [
                "进出货单",
                "业务往来",
                "报价合同",
                "库存记录",
                "销售数据",
            ],
        },
    },
    "9": {
        "label": "其他行业（稍后自定义）",
        "industry": "",
        "suggested_job": "6",
        "categories": {},
    },
}

# 常见职业（优先级从高到低）
JOB_PRESETS: dict[str, dict[str, Any]] = {
    "1": {
        "label": "专业技术人员（工程师、医生、教师、律师、IT从业人员等）",
        "job_title": "专业技术人员",
    },
    "2": {
        "label": "企业负责人/管理者",
        "job_title": "企业负责人",
    },
    "3": {
        "label": "办事人员（行政、文员等）",
        "job_title": "办事人员",
    },
    "4": {
        "label": "商业服务业人员（销售、运营、采购等）",
        "job_title": "商业服务业人员",
    },
    "5": {
        "label": "生产制造人员",
        "job_title": "生产制造人员",
    },
    "6": {
        "label": "其他职业（稍后自定义）",
        "job_title": "",
    },
}


def industry_menu_text() -> str:
    lines = ["【常见工作型行业】请选编号：", ""]
    for key in sorted(INDUSTRY_PRESETS, key=int):
        lines.append(f"  [{key}] {INDUSTRY_PRESETS[key]['label']}")
    lines.append("")
    return "\n".join(lines)


def job_menu_text(suggested_id: str = "1") -> str:
    lines = ["【常见职业】请选编号：", ""]
    for key in sorted(JOB_PRESETS, key=int):
        mark = " ← 推荐" if key == suggested_id else ""
        lines.append(f"  [{key}] {JOB_PRESETS[key]['label']}{mark}")
    lines.append("")
    return "\n".join(lines)


def apply_industry_preset(
    preset_id: str, base_categories: dict[str, Any]
) -> tuple[str, dict[str, Any], str]:
    """返回：行业名称、分类树、推荐职业编号。"""
    preset = INDUSTRY_PRESETS.get(preset_id, INDUSTRY_PRESETS["9"])
    cats = dict(base_categories)
    for key, val in preset.get("categories", {}).items():
        cats[key] = val
    return (
        preset.get("industry", ""),
        cats,
        preset.get("suggested_job", "1"),
    )


def apply_job_preset(preset_id: str) -> str:
    preset = JOB_PRESETS.get(preset_id, JOB_PRESETS["6"])
    return preset.get("job_title", "")


def apply_preset(
    preset_id: str, base_categories: dict[str, Any]
) -> tuple[str, dict[str, Any], str]:
    """兼容旧接口：仅按行业预设，返回行业、分类树、职业名称。"""
    industry, cats, job_id = apply_industry_preset(preset_id, base_categories)
    job_title = apply_job_preset(job_id)
    return industry, cats, job_title


def preset_menu_text() -> str:
    return industry_menu_text()
