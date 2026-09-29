"""Local v4 packages never infer content from Draft or legacy asset fields."""

import hashlib
import io
import json
import zipfile
from copy import deepcopy

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ContentAsset, ContentMasterRevision, DeliveryTarget, MaterialRevision
from .materials import read_bytes_checked
from .production_modalities import adapter_for
from .production_validation import validate_live_v4_candidate


def build_v4_package(db: Session, target: DeliveryTarget, asset: ContentAsset) -> dict:
    manifest = validate_live_v4_candidate(db, asset, require_current=False, require_approved=True, lock_live=True)
    if target.action not in {"copy_package", "manual_handoff"} or target.channel != manifest["channel"] or target.content_form != manifest["content_form"] or target.approved_candidate_hash != asset.candidate_hash:
        raise HTTPException(409, "v4交付授权与准确候选/渠道/形态不一致")
    master = db.get(ContentMasterRevision, asset.content_master_revision_id)
    projection = adapter_for(master.modality, master.payload_schema).build_package_projection(db, master)
    media = []
    for ref in manifest["assets"]:
        revision = db.get(MaterialRevision, ref["material_revision_id"])
        data = read_bytes_checked(db, revision, require_public=True)
        if hashlib.sha256(data).hexdigest() != ref["content_hash"]:
            raise HTTPException(409, "冻结媒体字节哈希不一致")
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif", "video/mp4": ".mp4", "audio/mpeg": ".mp3", "application/pdf": ".pdf"}.get(revision.mime_type, ".bin")
        media.append({**deepcopy(ref), "name": f"media/{len(media):02d}-{revision.id}{suffix}"})
    package_manifest = {**deepcopy(manifest), "target_id": target.id, "asset_id": asset.id, "candidate": {"id": asset.id, "hash": asset.candidate_hash}, "approved_candidate_hash": target.approved_candidate_hash, "account_ref": target.account_ref, "action": target.action, "authorization_version": target.authorization_version, "media": media, "remote_call": False}
    return {"manifest": package_manifest, "content": {"title": manifest["content"].get("title"), "markdown": manifest["render"].get("body_markdown")}, "projection": projection}


def v4_zip_bytes(db: Session, target: DeliveryTarget, package: dict) -> tuple[bytes, str]:
    manifest = package["manifest"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        for file in package["projection"]["text_files"]:
            if file["name"] != "content.md" or file["content"] != manifest["render"].get("body_markdown"):
                raise HTTPException(409, "渲染投影与冻结内容不一致")
            archive.writestr(file["name"], file["content"])
        frozen_media_bytes: dict[int, bytes] = {}
        for media in manifest["media"]:
            revision = db.get(MaterialRevision, media["material_revision_id"])
            data = read_bytes_checked(db, revision, require_public=True)
            if hashlib.sha256(data).hexdigest() != media["content_hash"]:
                raise HTTPException(409, "冻结媒体字节校验失败")
            archive.writestr(media["name"], data)
            frozen_media_bytes[revision.id] = data
        for output in package["projection"]["material_outputs"]:
            data = frozen_media_bytes.get(output["material_revision_id"])
            if data is None or hashlib.sha256(data).hexdigest() != output["content_hash"]:
                raise HTTPException(409, "最终渲染与冻结媒体不一致")
            archive.writestr(output["name"], data)
        archive.writestr("publish-guide.md", f"# 交付说明\n\n- 渠道：{target.channel} / {target.content_form}\n- 账号：{target.account_ref}\n- 候选哈希：{target.approved_candidate_hash}\n- 动作：{target.action}\n\n按 manifest.media 中的 role、sort_order 和 placement 使用精确媒体版本；人工发布后回填回执。本包没有调用远端发布。\n")
    # Recheck live DB state before returning bytes; frozen content is never retargeted.
    db.expire_all()
    validate_live_v4_candidate(db, db.get(ContentAsset, target.content_asset_id), require_current=False, require_approved=True)
    return buffer.getvalue(), f"delivery-target-{target.id}.zip"
