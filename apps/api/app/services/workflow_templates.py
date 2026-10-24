"""Built-in workflow helpers: the node shape starter pipelines use, and the product video default."""


def _node(node_id: str, node_type: str, label: str, params: dict | None = None, x: float = 0, y: float = 0) -> dict:
    return {"id": node_id, "type": node_type, "label": label, "params": params or {}, "layout": {"x": x, "y": y}}


def _is_target_agnostic(definition: dict | None) -> bool:
    """定义中所有节点都不携带 channel 参数（共享 Bundle 的判据）。

    R4.1：与执行同用 node_config_of 语义（config 优先合并），params 里藏 channel 也逃不掉。
    """
    from .content_harness.contracts import node_config_of

    for node in (definition or {}).get("nodes", []):
        if node_config_of(node).get("channel"):
            return False
    return True


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
