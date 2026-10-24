"""内置工作流模板：数据源一条线，生成后按渠道分叉（抖音口播 / 小红书 / 公众号各自独立）。

V1 PRD 2.0（§6.27/§9.1）：本文件保留 legacy 模板；标准 Workflow Bundle families 在
Phase 7 注册实现（多平台复用 Workflow，不复制代码），catalog 先占位展示。
"""

from typing import Any

from .content_harness.channel_methods import get as channel_method
from .content_harness.channel_methods import legacy_template_params, legacy_workflow_channels, workflow_meta

# 共享 Workflow Bundle families（Phase 7 实现；key 与平台 profile 的 default_workflow_key 对应）
CATALOG_FAMILIES: list[tuple[str, str]] = [
    ("workflow.article.editorial", "编辑部长文 Bundle"),
    ("workflow.article.feed", "信息流文章 Bundle"),
    ("workflow.qa.answer", "问答 Bundle"),
    ("workflow.image.cards", "图文卡片 Bundle"),
    ("workflow.social.short", "社交短帖 Bundle"),
    ("workflow.social.thread", "社交推串 Bundle"),
    ("workflow.finance.article", "财经文章 Bundle"),
    ("workflow.tech.article", "技术文章 Bundle"),
    ("workflow.script.spoken", "口播脚本 Bundle"),
]

def _node(node_id: str, node_type: str, label: str, params: dict | None = None, x: float = 0, y: float = 0) -> dict:
    return {"id": node_id, "type": node_type, "label": label, "params": params or {}, "layout": {"x": x, "y": y}}


def build_daily_suggest(params: dict | None = None) -> dict:
    """每日舆情 → 荐题：拉取 → 抽取 → 打包冻结 → AI 荐题 →【人工采纳】。"""
    p = params or {}
    return {
        "nodes": [
            _node("pull", "connector_pull", "拉取监测数据", {"endpoint_id": p.get("endpoint_id")}, 0, 0),
            _node("extract", "extract_facts", "抽取候选事实", {"auto_confirm": False}, 260, 0),
            _node("confirm", "confirm_facts", "人工确认事实", {}, 520, 0),
            _node("freeze", "factpack_freeze", "打包并冻结 FactPack", {}, 780, 0),
            _node("suggest", "suggest_topics", "AI 荐题", {"count": p.get("count", 3)}, 1040, 0),
            _node("adopt", "adopt_topic", "人工采纳选题", {}, 1300, 0),
        ],
        "edges": [
            {"from": "pull", "to": "extract"},
            {"from": "extract", "to": "confirm"},
            {"from": "confirm", "to": "freeze"},
            {"from": "freeze", "to": "suggest"},
            {"from": "suggest", "to": "adopt"},
        ],
    }


def build_gen_export(params: dict | None = None) -> dict:
    """生成 → 出库：默认只生成本地交付物；遗留远端草稿需显式开启。"""
    p = params or {}
    channels = p.get("channels") or legacy_workflow_channels()
    nodes: list[dict] = []
    edges: list[dict] = []
    for i, ch in enumerate(channels):
        meta = workflow_meta(ch)
        y = i * 170
        nodes.append(_node(f"gen_{ch}", "generate", f"生成 · {meta['label']}", {"channel": ch}, 0, y))
        nodes.append(_node(f"humanize_{ch}", "humanize_polish", f"去AI味 · {meta['label']}", {"channel": ch}, 230, y))
        nodes.append(_node(f"censor_{ch}", "content_censor", f"合规审查 · {meta['label']}", {"channel": ch}, 460, y))
        nodes.append(_node(f"check_{ch}", "fact_check", f"事实校验 · {meta['label']}", {"channel": ch}, 690, y))
        nodes.append(_node(f"approve_{ch}", "approve", f"人工批准 · {meta['label']}", {"channel": ch}, 920, y))
        nodes.append(
            _node(f"export_{ch}", "export", f"导出 · {meta['label']}", {"channel": ch, "formats": meta["formats"]}, 1150, y)
        )
        edges += [
            {"from": f"gen_{ch}", "to": f"humanize_{ch}"},
            {"from": f"humanize_{ch}", "to": f"censor_{ch}"},
            {"from": f"censor_{ch}", "to": f"check_{ch}"},
            {"from": f"check_{ch}", "to": f"approve_{ch}"},
            {"from": f"approve_{ch}", "to": f"export_{ch}"},
        ]
        plugin = channel_method(ch)
        extension = plugin.legacy_publish_extension(p, y) if plugin and plugin.legacy_publish_extension else None
        if extension:
            nodes.extend(extension["nodes"])
            edges += extension["edges"]
            edges = [edge for edge in edges if edge != extension["drop_edge"]]
    return {"nodes": nodes, "edges": edges}


TEMPLATES = {
    "daily_suggest": {
        "name": "每日舆情 → 荐题",
        "description": "拉取监测数据 → 抽取候选 → 人工确认事实 → 打包冻结 → AI 荐题 → 人工采纳",
        "builder": build_daily_suggest,
        "params_schema": [
            {"key": "endpoint_id", "label": "监测数据端点", "type": "endpoint", "required": True},
            {"key": "count", "label": "荐题候选数", "type": "number", "default": 3},
        ],
    },
    "gen_export": {
        "name": "生成 → 出库（按渠道分叉）",
        "description": "共享一个选题，按渠道生成 → 事实校验 → 人工批准 → 本地导出；遗留公众号草稿能力需显式开启",
        "builder": build_gen_export,
        "params_schema": [
            {"key": "channels", "label": "渠道线", "type": "channels", "default": legacy_workflow_channels()},
            *legacy_template_params(),
        ],
    },
}


def build_definition(template_key: str, params: dict | None = None) -> dict[str, Any]:
    template = TEMPLATES.get(template_key)
    if not template:
        raise ValueError(f"未知模板: {template_key}")
    return template["builder"](params or {})


# ---------- V1 共享 Workflow Bundle families（§9.1/§9.2，Phase 7）----------

# 每个 family 的标准节点序列（内置 fallback writer；外部 Skill 在 profile/skill 层接管）
FAMILY_STEPS: dict[str, list[tuple[str, str, str]]] = {
    "workflow.article.editorial": [
        ("gen", "generate", "平台写作"),
        ("humanize", "humanize_polish", "去 AI 味"),
        ("censor", "content_censor", "合规审查"),
        ("check", "fact_check", "事实校验"),
        ("disco", "discoverability", "SEO 审查"),
        ("approve", "approve", "人工批准"),
        ("export", "export", "本地导出"),
    ],
    "workflow.article.feed": [
        ("gen", "generate", "信息流写作"),
        ("censor", "content_censor", "合规审查"),
        ("check", "fact_check", "事实校验"),
        ("disco", "discoverability", "SEO 审查"),
        ("approve", "approve", "人工批准"),
        ("export", "export", "本地导出"),
    ],
    "workflow.qa.answer": [
        ("gen", "generate", "回答写作"),
        ("check", "fact_check", "事实校验"),
        ("disco", "discoverability", "SEO 审查"),
        ("approve", "approve", "人工批准"),
        ("export", "export", "本地导出"),
    ],
    "workflow.image.cards": [
        ("gen", "generate", "图文笔记写作"),
        ("check", "fact_check", "事实校验"),
        ("disco", "discoverability", "SEO 审查"),
        ("approve", "approve", "人工批准"),
        ("export", "export", "本地导出"),
    ],
    "workflow.social.short": [
        ("gen", "generate", "短帖写作"),
        ("censor", "content_censor", "合规审查"),
        ("check", "fact_check", "事实校验"),
        ("disco", "discoverability", "SEO 审查"),
        ("approve", "approve", "人工批准"),
        ("export", "export", "本地导出"),
    ],
    "workflow.social.thread": [
        ("gen", "generate", "推串写作"),
        ("check", "fact_check", "事实校验"),
        ("disco", "discoverability", "SEO 审查"),
        ("approve", "approve", "人工批准"),
        ("export", "export", "本地导出"),
    ],
    "workflow.finance.article": [
        ("gen", "generate", "财经写作"),
        ("censor", "content_censor", "合规审查"),
        ("check", "fact_check", "事实校验"),
        ("disco", "discoverability", "SEO 审查"),
        ("approve", "approve", "人工批准"),
        ("export", "export", "本地导出"),
    ],
    "workflow.tech.article": [
        ("gen", "generate", "技术写作"),
        ("check", "fact_check", "事实校验"),
        ("disco", "discoverability", "SEO 审查"),
        ("approve", "approve", "人工批准"),
        ("export", "export", "本地导出"),
    ],
    "workflow.script.spoken": [
        ("gen", "generate", "口播脚本写作"),
        ("check", "fact_check", "事实校验"),
        ("disco", "discoverability", "SEO 审查"),
        ("approve", "approve", "人工批准"),
        ("export", "export", "本地导出"),
    ],
}


def build_catalog_workflow(family_key: str, params: dict | None = None) -> dict[str, Any]:
    """实例化共享 Workflow Bundle（schema v2 节点：plugin/plugin_version）。

    R2-B1：params 不带 channel 时构建「target 无关」的共享定义——channel/content_form
    由 WorkflowRun.params 承载（同一 Bundle 多平台复用，不复制定义）；带 channel 的
    构建（catalog 页面实例化）保持旧行为，参数烘焙进节点。
    """
    steps = FAMILY_STEPS.get(family_key)
    if not steps:
        raise ValueError(f"未知 Workflow Bundle: {family_key}")
    p = params or {}
    channel = p.get("channel")
    content_form = p.get("content_form")
    tag = f"{channel}.{content_form}" if channel and content_form else (channel or "")
    target_params: dict[str, Any] = {}
    if channel:
        target_params["channel"] = channel
    if content_form:
        target_params["content_form"] = content_form
    nodes = []
    for index, (suffix, plugin_type, label) in enumerate(steps):
        node: dict[str, Any] = {
            "id": f"{suffix}_{tag}" if tag else suffix,
            "plugin": f"builtin.{ {'generate':'generate','humanize_polish':'humanize','content_censor':'content_censor','fact_check':'fact_check','discoverability':'discoverability_post','approve':'approve','export':'export'}[plugin_type] }",
            "plugin_version": "1",
            "label": f"{label} · {channel}" if channel else label,
            "config": dict(target_params),
            "layout": {"x": index * 230, "y": 0},
        }
        if target_params:
            node["params"] = dict(target_params)
        nodes.append(node)
    edges = [{"from": nodes[i]["id"], "to": nodes[i + 1]["id"]} for i in range(len(nodes) - 1)]
    return {"nodes": nodes, "edges": edges}


def _is_target_agnostic(definition: dict | None) -> bool:
    """定义中所有节点都不携带 channel 参数（共享 Bundle 的判据）。

    R4.1：与执行同用 node_config_of 语义（config 优先合并），params 里藏 channel 也逃不掉。
    """
    from .content_harness.contracts import node_config_of

    for node in (definition or {}).get("nodes", []):
        if node_config_of(node).get("channel"):
            return False
    return True


def ensure_bundle_workflow(db, family_key: str | None):
    """R2-B1：主生产入口按 family 解析/创建共享 Bundle Workflow（幂等）。

    只复用「target 无关」的 published 版本（channel 由 run 参数承载）；找不到则按标准
    序列构建 v1 并发布。返回 None 表示 family 缺失（legacy 渠道走直连生成兼容路径）。
    """
    from sqlalchemy import select

    from ..models import Workflow
    from .workflow_engine import definition_checksum

    if not family_key:
        return None
    rows = db.scalars(
        select(Workflow)
        .where(Workflow.workflow_key == family_key, Workflow.status == "published")
        .order_by(Workflow.version.desc())
    ).all()
    for row in rows:
        if _is_target_agnostic(row.definition_json):
            return row
    definition = build_catalog_workflow(family_key, {})
    max_version = db.scalars(
        select(Workflow.version).where(Workflow.workflow_key == family_key).order_by(Workflow.version.desc()).limit(1)
    ).first() or 0
    workflow = Workflow(
        name=f"{family_key}（共享 Bundle）",
        description=f"V1 共享 Workflow Bundle · {family_key} · target 由 run 参数承载",
        template_key=None,
        workflow_key=family_key,
        version=max_version + 1,
        schema_version=2,
        status="published",
        checksum=definition_checksum(definition),
        definition_json=definition,
        created_by="system",
    )
    db.add(workflow)
    db.commit()
    return workflow

def ensure_product_workflow(db, modality, user):
    from sqlalchemy import select
    from ..models import Workflow
    from .starter_personas import _definition
    from .project_workflows import new_workflow_version, validate_definition

    key = f"product.{user.id}.{modality}"
    row = db.scalar(select(Workflow).where(Workflow.workflow_key == key,
        Workflow.owner_user_id == user.id, Workflow.scope == "product_default",
        Workflow.status == "published", Workflow.enabled.is_(True)).order_by(Workflow.version.desc()).limit(1))
    # Product defaults are system-owned, so older video recipes (script/shots or prepare stages) move to the storyboard stage.
    if row and not any(node["id"] in {"shots", "prepare"} for node in row.definition_json.get("nodes", [])):
        return row
    definition = _definition(modality, "product")
    for node in definition["nodes"]:
        config = node["config"]
        if node["id"] == "master":
            config["method"] = {"source_kind": "studio_builtin", "skill_ref": "studio.video.product-script@1"}
            config["instruction"] += (" 仅依据SKU资料和本条目标：针对具体买家场景讲一个购买理由，区分AI情境与真实证据，回答主要顾虑并给一个下一步；不得虚构性能、价格、体验或评价。"
                                      " 商品外观一致；每镜一个动作，画面写清机位、景别、人与商品接触、首尾状态和接镜关系；区分实拍证据与AI示意。")
    return new_workflow_version(db, key=key, name="商品视频制作", definition=validate_definition(definition),
        owner_user_id=user.id, scope="product_default", created_by=user.email)
