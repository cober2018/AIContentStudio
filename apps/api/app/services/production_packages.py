"""Local v4 packages never infer content from Draft or legacy asset fields."""

import hashlib
import io
import json
import zipfile
from copy import deepcopy
from html import escape
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ContentAsset, ContentMasterRevision, DeliveryTarget, FactPackItem, MaterialRevision
from .materials import read_bytes_checked
from .production_modalities import adapter_for
from .production_validation import validate_live_v4_candidate, validate_live_v5_candidate


def _write_stable_entry(archive: zipfile.ZipFile, name: str, content: bytes | str) -> None:
    # ZIP member timestamps must not change the bytes of the same approved package.
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = 0o600 << 16
    archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED)


def _public_metadata_text(value: object, *, url: bool = False) -> str:
    from .creative_intents import contains_secret_text

    if not isinstance(value, str) or len(value) > 4000 or contains_secret_text(value):
        raise HTTPException(409, {"code": "export_disclosure_unavailable"})
    if any(marker in value for marker in ("/Users/", "/home/", "file://", "Bearer ")):
        raise HTTPException(409, {"code": "export_disclosure_unavailable"})
    if url:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise HTTPException(409, {"code": "export_disclosure_unavailable"})
    return value


def public_export_metadata(db: Session, assets: list[dict], evidence: list[dict]) -> dict:
    sources, media = [], []
    for ref in evidence:
        item = db.get(FactPackItem, ref["fact_pack_item_id"])
        if item is None or item.public_use_allowed is not True or item.public_use_revoked_at is not None:
            raise HTTPException(409, {"code": "export_source_unavailable"})
        snapshot = item.snapshot_json or {}
        source = snapshot.get("source", {})
        source = source if isinstance(source, dict) else {}
        required = bool(snapshot.get("attribution_required") or source.get("attribution_required"))
        if required and (snapshot.get("public_disclosure_allowed") is False or source.get("public_disclosure_allowed") is False):
            raise HTTPException(409, {"code": "export_disclosure_unavailable"})
        projected = {"fact_pack_item_id": item.id, "snapshot_checksum": ref["snapshot_checksum"]}
        if snapshot.get("public_disclosure_allowed") is False or source.get("public_disclosure_allowed") is False:
            sources.append(projected)
            continue
        for field in ("title", "source_url", "author", "license", "attribution", "published_at"):
            value = source.get(field, snapshot.get(field))
            if value:
                projected[field] = _public_metadata_text(value, url=field == "source_url")
        if required and not projected.get("attribution"):
            raise HTTPException(409, {"code": "export_required_attribution_missing"})
        sources.append(projected)
    for ref in assets:
        revision = db.get(MaterialRevision, ref["material_revision_id"])
        if revision is None:
            raise HTTPException(409, {"code": "export_media_unavailable"})
        metadata = revision.source_metadata_json or {}
        required = bool(metadata.get("attribution_required"))
        if required and (metadata.get("public_disclosure_allowed") is False or not revision.attribution_text):
            raise HTTPException(409, {"code": "export_disclosure_unavailable"})
        item = {"material_revision_id": revision.id}
        if metadata.get("public_disclosure_allowed") is False:
            media.append(item)
            continue
        if revision.attribution_text:
            item["attribution"] = _public_metadata_text(revision.attribution_text)
        if revision.source_url:
            # Local/private source locations are provenance, not publishable attribution.
            if revision.source_url.startswith(("http://", "https://")):
                item["source_url"] = _public_metadata_text(revision.source_url, url=True)
            elif required:
                raise HTTPException(409, {"code": "export_disclosure_unavailable"})
        if metadata.get("license"):
            item["license"] = _public_metadata_text(metadata["license"])
        media.append(item)
    return {"sources": sources, "media": media}


def _article_html(content: dict, media: list[dict]) -> str:
    paths = {ref["slot_key"]: ref["name"] for ref in media}
    parts = ["<!doctype html><html lang=\"zh\"><meta charset=\"utf-8\"><title>" + escape(content.get("title", "")) + "</title><body>",
             "<h1>" + escape(content.get("title", "")) + "</h1>"]
    if content.get("question"):
        parts.append("<h2>" + escape(content["question"]["text"]) + "</h2>")
    if content.get("summary"):
        parts.append("<p>" + escape(content["summary"]) + "</p>")
    for ref in media:
        if ref["role"] == "cover":
            parts.append('<figure><img src="' + escape(ref["name"], quote=True) + '" alt="封面"></figure>')
    for block in content.get("blocks", []):
        kind = block["kind"]
        text = escape(block.get("text", ""))
        if kind == "image":
            path = paths.get(block["image_ref_key"])
            if path is None:
                raise HTTPException(409, {"code": "export_image_mapping_missing"})
            parts.append('<figure><img src="' + escape(path, quote=True) + '" alt="' + escape(block.get("alt_text", ""), quote=True) + '"><figcaption>' + text + '</figcaption></figure>')
        elif kind == "divider":
            parts.append("<hr>")
        elif kind == "list" and "items" in block:
            tag = "ol" if block.get("ordered") else "ul"
            parts.append("<" + tag + ">" + "".join("<li>" + escape(item["text"]) + "</li>" for item in block["items"]) + "</" + tag + ">")
        else:
            tag = {"heading": "h2", "quote": "blockquote", "code": "pre", "callout": "aside"}.get(kind, "p")
            parts.append("<" + tag + ">" + text + "</" + tag + ">")
    parts.append("</body></html>")
    return "\n".join(parts)


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
    if target_form.get("account") is not None and target.content_account_id != target_form["account"]["content_account_id"]:
        raise HTTPException(409, {"code": "candidate_target_account_mismatch"})
    media = []
    for ref in manifest["assets"]:
        revision = db.get(MaterialRevision, ref["material_revision_id"])
        data = read_bytes_checked(db, revision, require_public=True)
        if hashlib.sha256(data).hexdigest() != ref["content_hash_snapshot"]:
            raise HTTPException(409, "v5冻结媒体字节哈希不一致")
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif",
                  "video/mp4": ".mp4", "audio/mpeg": ".mp3", "audio/wav": ".wav", "application/pdf": ".pdf"}.get(revision.mime_type, ".bin")
        media.append({**deepcopy(ref), "name": f"media/{ref['sort_order']:02d}-{revision.id}{suffix}"})
    export_metadata = manifest.get("export_metadata")
    if export_metadata is None:
        export_metadata = public_export_metadata(db, manifest["assets"], manifest["evidence_refs"])
        if any(len(item) > (2 if "snapshot_checksum" in item else 1)
               for item in export_metadata["sources"] + export_metadata["media"]):
            raise HTTPException(409, {"code": "historical_export_attribution_not_frozen"})
    package_manifest = {"export_schema": "studio.channel-export.v1", "schema_version": 5,
                        "target_id": target.id, "asset_id": asset.id,
                        "candidate": {"id": asset.id, "hash": asset.candidate_hash},
                        "approved_candidate_hash": target.approved_candidate_hash,
                        "content_account_id": target.content_account_id,
                        "target": {key: deepcopy(target_form[key]) for key in ("channel", "content_form", "artifact_kind", "profile", "adapter", "rule_hash")},
                        "payload_schema": manifest["variant"]["payload_schema"],
                        "payload_hash": manifest["variant"]["payload_hash"],
                        "action": target.action, "authorization_version": target.authorization_version,
                        "media": media, "remote_call": False, "manual_handoff": True,
                        "sources": export_metadata["sources"], "media_attribution": export_metadata["media"],
                        "declarations": deepcopy(manifest["declarations"]),
                        "citations": deepcopy(manifest["citations"]),
                        "evidence_refs": deepcopy(manifest["evidence_refs"]),
                        "candidate_hash_semantics": "reference_to_internal_frozen_candidate"}
    if target_form["artifact_kind"] == "script":
        package_manifest["render"] = {"artifact_kind": "script", "finished_video": False,
                                      "estimated_subtitles": bool(manifest["render"].get("estimated_srt"))}
    if target_form.get("account") is not None:
        package_manifest["target"]["account"] = {key: target_form["account"][key] for key in
            ("content_account_id", "platform_channel", "platform_account_id", "account_revision_id", "account_profile_checksum")}
    render = manifest["render"]
    files = []
    if target_form["artifact_kind"] == "text":
        files.append({"name": "content.md", "content": render["text"]})
        if target_form["content_form"] == "thread":
            files.append({"name": "thread.json", "content": json.dumps(manifest["content"]["posts"], ensure_ascii=False, sort_keys=True)})
        elif "blocks" in manifest["content"]:
            form = target_form["content_form"]
            public_content = {key: value for key, value in manifest["content"].items() if key not in {"html_template"}}
            files.append({"name": f"{form}.json", "content": json.dumps(public_content, ensure_ascii=False, sort_keys=True)})
            files.append({"name": "content.html", "content": _article_html(public_content, media)})
            if form == "answer":
                files.append({"name": "question.json", "content": json.dumps(public_content["question"], ensure_ascii=False, sort_keys=True)})
        else:
            files.append({"name": "post.json", "content": json.dumps(manifest["content"], ensure_ascii=False, sort_keys=True)})
    elif target_form["artifact_kind"] == "image":
        files.append({"name": "content.md", "content": render["title"] + "\n\n" + (render.get("description", "") + "\n\n" if render.get("description") else "") + "\n\n".join(card["caption"] for card in render["cards"]) + ("\n\n" + " ".join("#" + tag for tag in render["tags"]) if render.get("tags") else "")})
        files.append({"name": "cards.json", "content": json.dumps(render["cards"], ensure_ascii=False, sort_keys=True)})
        files.append({"name": "image-note.json", "content": json.dumps(manifest["content"], ensure_ascii=False, sort_keys=True)})
    elif target_form["artifact_kind"] == "script":
        files.append({"name": "content.md", "content": "\n\n".join(scene["script"] for scene in render["scenes"])})
        files.append({"name": "scenes.json", "content": json.dumps(render["scenes"], ensure_ascii=False, sort_keys=True)})
        if render.get("estimated_srt"):
            files.append({"name": "estimated.srt", "content": render["estimated_srt"]["text"]})
    else:
        raise HTTPException(409, "v5目标成品类型不可用")
    files.extend([
        {"name": "sources.json", "content": json.dumps(export_metadata["sources"], ensure_ascii=False, sort_keys=True)},
        {"name": "declarations.json", "content": json.dumps(manifest["declarations"], ensure_ascii=False, sort_keys=True)},
        {"name": "publish-guide.md", "content": f"# 人工交付说明\n\n- 渠道：{target.channel} / {target.content_form}\n- 候选哈希：{target.approved_candidate_hash}\n- 动作：{target.action}\n\n本地包就绪不等于公开发布；公众号草稿也不等于公开发布。按 manifest.media 的顺序和位置使用精确素材，并保留 sources.json 和 declarations.json 的来源、署名与声明。HTML 为本产品的安全排版，平台编辑器可能改变样式。X 长帖/Articles 账号资格未验证，不影响本地交付。抖音内容为脚本，字幕为估算，不是成片或音频对齐字幕。本包没有调用远端；发布后人工回填真实回执。\n"},
    ])
    package_manifest["files"] = [{"name": file["name"], "sha256": hashlib.sha256(file["content"].encode()).hexdigest()} for file in files]
    package_manifest["files"].extend({"name": ref["name"], "sha256": ref["content_hash_snapshot"]} for ref in media)
    package_manifest["export_hash"] = hashlib.sha256(json.dumps(package_manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
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
    db.expire_all()
    validate_live_v5_candidate(db, db.get(ContentAsset, target.content_asset_id), require_current=False, require_approved=True)
    return buffer.getvalue(), f"delivery-target-{target.id}.zip"
