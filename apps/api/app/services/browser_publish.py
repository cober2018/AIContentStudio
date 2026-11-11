"""Publish packages for a third-party model that publishes them, or saves them as drafts, in the user's logged-in browser.

Only targets the user authorized on the delivery page are reachable; a publish is recorded as that target's receipt.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AuditLog, ContentAsset, DeliveryTarget, MaterialRevision, User
from .project_authorization import authorize_project_target

OPEN = ("target_authorized", "package_ready", "awaiting_manual_receipt")
DRAFT_EVENT = "delivery_target.browser_draft"
CHANNEL_NAMES = {"wechat_channels": "视频号", "wechat": "公众号", "douyin": "抖音", "xiaohongshu": "小红书", "bilibili": "B站",
                 "toutiao": "头条", "baijia": "百家号", "kuaishou": "快手", "zhihu": "知乎"}
RULE = ("按用户说的做：说发布就点「发表」，发表后截图并用 report_publish_result 记回执；说存草稿就停在「发表」之前截图，用 report_publish_draft 记一笔并停下。"
        "登录、扫码、验证码、短信、风控都停下请用户处理。一次只发一个。发布包的文件只读，不复制、不改；文案照 publish_copy 填，平台字数不够时只截短、不改意思。"
        "先读 get_craft_skill(skill=\"craft-publish\") 的总则，再读这个平台那一份（entry 见 skill_entry）。")


def _fail(status: int, code: str, message: str):
    raise HTTPException(status, {"code": code, "message": message})


def _target(db: Session, user: User, target_id: int) -> DeliveryTarget:
    target = db.get(DeliveryTarget, target_id)
    if target is None:
        _fail(404, "publish_target_not_found", "交付目标不存在")
    authorize_project_target(db, target, user)
    if target.authorized_by and target.authorized_by != user.email:
        _fail(403, "publish_target_forbidden", "这个交付目标没授权给当前用户")
    if target.action != "copy_package":
        _fail(409, "publish_target_not_copy_package", "这个目标走平台自动推送，不用浏览器上传")
    return target


def latest_drafts(db: Session, target_ids: list[int]) -> dict[int, dict]:
    if not target_ids:
        return {}
    rows = db.scalars(select(AuditLog).where(AuditLog.event == DRAFT_EVENT, AuditLog.entity_type == "delivery_target",
                                             AuditLog.entity_id.in_([str(item) for item in target_ids])).order_by(AuditLog.id)).all()
    # Later rows overwrite earlier ones, so each target keeps its newest draft record.
    return {int(row.entity_id): {**(row.detail_json or {}), "at": row.created_at.isoformat(), "by": row.actor} for row in rows}


def _manifest(db: Session, target: DeliveryTarget) -> dict:
    asset = db.get(ContentAsset, target.content_asset_id)
    return (asset.candidate_manifest_json or {}) if asset else {}


def pending(db: Session, user: User) -> dict:
    rows = db.scalars(select(DeliveryTarget).where(DeliveryTarget.authorized_by == user.email, DeliveryTarget.action == "copy_package",
                                                   DeliveryTarget.status.in_(OPEN)).order_by(DeliveryTarget.id.desc()).limit(100)).all()
    drafts = latest_drafts(db, [row.id for row in rows])
    items = []
    for target in rows:
        try:
            authorize_project_target(db, target, user)
        except HTTPException:
            continue
        manifest = _manifest(db, target)
        project = manifest.get("project") or {}
        items.append({"target_id": target.id, "channel": target.channel, "platform": CHANNEL_NAMES.get(target.channel, target.channel),
                      "content_form": target.content_form, "account": target.account_ref, "status": target.status,
                      "project_id": project.get("id"), "unit_id": project.get("unit_id"), "title": manifest.get("title") or project.get("unit_title"),
                      "draft": drafts.get(target.id)})
    return {"items": items, "rule": RULE}


def package(db: Session, user: User, target_id: int) -> dict:
    from .delivery import build_copy_package
    from .materials import file_location

    target = _target(db, user, target_id)
    built = build_copy_package(db, target)
    manifest = built.get("manifest") if isinstance(built.get("manifest"), dict) else None
    head = {"target_id": target.id, "channel": target.channel, "platform": CHANNEL_NAMES.get(target.channel, target.channel),
            "account": target.account_ref, "status": target.status, "rule": RULE,
            "skill_entry": f"{target.channel}.md", "draft": latest_drafts(db, [target.id]).get(target.id)}
    if manifest is None or manifest.get("schema_version") != 6:
        # Text packages carry their body in the package itself; no media files to upload.
        return {**head, "package": built}
    files = []
    for item in manifest.get("files") or []:
        revision = db.get(MaterialRevision, item.get("material_revision_id"))
        path = file_location(db, revision) if revision is not None else None
        found = path is not None and Path(path).is_file()
        files.append({"role": item.get("role"), "path": str(path) if found else None, "missing": not found,
                      **{key: item.get(key) for key in ("mime_type", "width", "height", "duration_ms")}})
    project = manifest.get("project") or {}
    shots = None
    if project.get("id"):
        from .project_folders import export_dir

        try:
            shots = str(export_dir(db, project["id"], "final").parent / "发布截图")
        except Exception:  # noqa: BLE001 Without the material drive the model falls back to the system temp folder.
            shots = None
    return {**head, "project_id": project.get("id"), "unit_id": project.get("unit_id"), "title": manifest.get("title"),
            "screenshot_dir": shots,
            "aspect_ratio": manifest.get("aspect_ratio"), "files": files, "publish_copy": manifest.get("publish_copy") or {}}


def _open_target(db: Session, user: User, target_id: int, screenshot_path: str) -> tuple[DeliveryTarget, Path]:
    target = _target(db, user, target_id)
    if target.status not in OPEN:
        _fail(409, "publish_target_closed", "这个交付目标已经回填或关闭，不用再上传")
    path = Path(screenshot_path)
    if not path.is_absolute() or not path.is_file():
        _fail(422, "publish_screenshot_missing", "截图要给本机绝对路径，并且文件要存在")
    return target, path


def record_draft(db: Session, user: User, target_id: int, screenshot_path: str, note: str, model: str) -> dict:
    target, path = _open_target(db, user, target_id, screenshot_path)
    db.add(AuditLog(event=DRAFT_EVENT, actor=user.email, entity_type="delivery_target", entity_id=str(target.id),
                    detail_json={"channel": target.channel, "screenshot": str(path), "note": note.strip()[:500], "model": model.strip()[:120]}))
    db.commit()
    return {"target_id": target.id, "status": target.status, "draft": latest_drafts(db, [target.id]).get(target.id),
            "next": "停下：告诉用户草稿已存好，等用户说要不要发表"}


def record_published(db: Session, user: User, target_id: int, screenshot_path: str, link: str, note: str, model: str) -> dict:
    from ..routers.delivery import ReceiptIn, add_receipt

    target, path = _open_target(db, user, target_id, screenshot_path)
    # 视频号这类网页上拿不到作品链接的平台，用发表后的截图当回执依据。
    evidence = link.strip() or str(path)
    detail = f"第三方模型发表（{model.strip()[:120]}）；截图 {path}" + (f"；{note.strip()[:300]}" if note.strip() else "")
    add_receipt(target.id, ReceiptIn(status="human_confirmed", evidence_ref=evidence, verification_method="third_party_model_browser",
                                     note=detail), db, user)
    db.refresh(target)
    return {"target_id": target.id, "status": target.status, "evidence_ref": evidence,
            "next": "告诉用户已发表，回执已记在交付页"}
