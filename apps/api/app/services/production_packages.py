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
from .production_validation import validate_live_v4_candidate, validate_live_v5_candidate


def _write_stable_entry(archive: zipfile.ZipFile, name: str, content: bytes | str) -> None:
    # ZIP member timestamps must not change the bytes of the same approved package.
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = 0o600 << 16
    archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED)


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
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif", "video/mp4": ".mp4", "audio/mpeg": ".mp3", "audio/wav": ".wav", "application/pdf": ".pdf"}.get(revision.mime_type, ".bin")
        media.append({**deepcopy(ref), "name": f"media/{len(media):02d}-{revision.id}{suffix}"})
    package_manifest = {**deepcopy(manifest), "target_id": target.id, "asset_id": asset.id, "candidate": {"id": asset.id, "hash": asset.candidate_hash}, "approved_candidate_hash": target.approved_candidate_hash, "account_ref": target.account_ref, "action": target.action, "authorization_version": target.authorization_version, "media": media, "remote_call": False}
    return {"manifest": package_manifest, "content": {"title": manifest["content"].get("title"), "markdown": manifest["render"].get("body_markdown")}, "projection": projection}


def v4_zip_bytes(db: Session, target: DeliveryTarget, package: dict) -> tuple[bytes, str]:
    manifest = package["manifest"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        _write_stable_entry(archive, "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        for file in package["projection"]["text_files"]:
            if file["name"] != "content.md" or file["content"] != manifest["render"].get("body_markdown"):
                raise HTTPException(409, "渲染投影与冻结内容不一致")
            _write_stable_entry(archive, file["name"], file["content"])
        frozen_media_bytes: dict[int, bytes] = {}
        for media in manifest["media"]:
            revision = db.get(MaterialRevision, media["material_revision_id"])
            data = read_bytes_checked(db, revision, require_public=True)
            if hashlib.sha256(data).hexdigest() != media["content_hash"]:
                raise HTTPException(409, "冻结媒体字节校验失败")
            _write_stable_entry(archive, media["name"], data)
            frozen_media_bytes[revision.id] = data
        for output in package["projection"]["material_outputs"]:
            data = frozen_media_bytes.get(output["material_revision_id"])
            if data is None or hashlib.sha256(data).hexdigest() != output["content_hash"]:
                raise HTTPException(409, "最终渲染与冻结媒体不一致")
            _write_stable_entry(archive, output["name"], data)
        _write_stable_entry(archive, "publish-guide.md", f"# 交付说明\n\n- 渠道：{target.channel} / {target.content_form}\n- 账号：{target.account_ref}\n- 候选哈希：{target.approved_candidate_hash}\n- 动作：{target.action}\n\n按 manifest.media 中的 role、sort_order 和 placement 使用精确媒体版本；人工发布后回填回执。本包没有调用远端发布。\n")
    # Recheck live DB state before returning bytes; frozen content is never retargeted.
    db.expire_all()
    validate_live_v4_candidate(db, db.get(ContentAsset, target.content_asset_id), require_current=False, require_approved=True)
    return buffer.getvalue(), f"delivery-target-{target.id}.zip"


def build_v5_package(db: Session, target: DeliveryTarget, asset: ContentAsset) -> dict:
    """Project only the approved frozen Variant and exact local media into a manual package."""
    manifest = validate_live_v5_candidate(db, asset, require_current=False, require_approved=True, lock_live=True)
    target_form = manifest["target"]
    if (target.action not in {"copy_package", "manual_handoff"} or target.channel != target_form["channel"]
            or target.content_form != target_form["content_form"] or target.approved_candidate_hash != asset.candidate_hash):
        raise HTTPException(409, "v5交付授权与准确候选/渠道/形态不一致")
    media = []
    for ref in manifest["assets"]:
        revision = db.get(MaterialRevision, ref["material_revision_id"])
        data = read_bytes_checked(db, revision, require_public=True)
        if hashlib.sha256(data).hexdigest() != ref["content_hash_snapshot"]:
            raise HTTPException(409, "v5冻结媒体字节哈希不一致")
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif",
                  "video/mp4": ".mp4", "audio/mpeg": ".mp3", "audio/wav": ".wav", "application/pdf": ".pdf"}.get(revision.mime_type, ".bin")
        media.append({**deepcopy(ref), "name": f"media/{ref['sort_order']:02d}-{revision.id}{suffix}"})
    package_manifest = {**deepcopy(manifest), "target_id": target.id, "asset_id": asset.id,
                        "candidate": {"id": asset.id, "hash": asset.candidate_hash},
                        "approved_candidate_hash": target.approved_candidate_hash,
                        "account_ref": target.account_ref, "content_account_id": target.content_account_id,
                        "action": target.action, "authorization_version": target.authorization_version,
                        "media": media, "remote_call": False, "manual_handoff": True}
    render = manifest["render"]
    files = []
    if target_form["artifact_kind"] == "text":
        files.append({"name": "content.md", "content": render["text"]})
        if target_form["content_form"] == "thread":
            files.append({"name": "thread.json", "content": json.dumps(manifest["content"]["posts"], ensure_ascii=False, sort_keys=True)})
    elif target_form["artifact_kind"] == "image":
        files.append({"name": "content.md", "content": render["title"] + "\n\n" + "\n\n".join(card["caption"] for card in render["cards"])})
        files.append({"name": "cards.json", "content": json.dumps(render["cards"], ensure_ascii=False, sort_keys=True)})
    elif target_form["artifact_kind"] == "script":
        files.append({"name": "content.md", "content": "\n\n".join(scene["script"] for scene in render["scenes"])})
        files.append({"name": "scenes.json", "content": json.dumps(render["scenes"], ensure_ascii=False, sort_keys=True)})
        if render.get("estimated_srt"):
            files.append({"name": "estimated.srt", "content": render["estimated_srt"]["text"]})
    else:
        raise HTTPException(409, "v5目标成品类型不可用")
    return {"manifest": package_manifest, "content": {"title": manifest["content"].get("title"),
                                                        "markdown": files[0]["content"]}, "files": files}


def v5_zip_bytes(db: Session, target: DeliveryTarget, package: dict) -> tuple[bytes, str]:
    manifest = package["manifest"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        _write_stable_entry(archive, "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        for file in package["files"]:
            _write_stable_entry(archive, file["name"], file["content"])
        for media in manifest["media"]:
            revision = db.get(MaterialRevision, media["material_revision_id"])
            data = read_bytes_checked(db, revision, require_public=True)
            if hashlib.sha256(data).hexdigest() != media["content_hash_snapshot"]:
                raise HTTPException(409, "v5冻结媒体字节校验失败")
            _write_stable_entry(archive, media["name"], data)
        _write_stable_entry(archive, "publish-guide.md", f"# 人工交付说明\n\n- 渠道：{target.channel} / {target.content_form}\n- 账号：{target.account_ref}\n- 候选哈希：{target.approved_candidate_hash}\n- 动作：{target.action}\n\n本包未调用远端发布。请按 manifest.media 的顺序和位置使用精确媒体版本；完成发布后人工回填真实回执。\n")
    db.expire_all()
    validate_live_v5_candidate(db, db.get(ContentAsset, target.content_asset_id), require_current=False, require_approved=True)
    return buffer.getvalue(), f"delivery-target-{target.id}.zip"
