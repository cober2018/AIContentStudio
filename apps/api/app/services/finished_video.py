"""成片交付候选（schema 6）：视频链里通过的成片、封面和发布文案，作为审阅与交付的待审版本。

The 成片 was cut outside the platform and checked on the review page, so this candidate carries only what is
delivered and checks only those files, not the 导演稿's shot sources (the v4 path re-derives everything from the Master).
"""
import hashlib
import io
import json
import zipfile
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentAsset, ContentProject, ContentUnit, CreativeExecutionOutput, MaterialRevision, User
from .candidates import candidate_hash

SCHEMA = 6
CONTENT_FORM = "short_video"
# Video platforms a finished cut can be delivered to by hand; the channel registry has no video forms yet.
VIDEO_CHANNELS = {"douyin": "抖音", "xiaohongshu": "小红书", "wechat_channels": "视频号", "wechat": "公众号", "kuaishou": "快手",
                  "bilibili": "B站", "baijia": "百家号", "toutiao": "今日头条", "youtube": "YouTube"}
ROLES = ("final", "cover", "cover_43", "cover_vertical")
SUFFIX = {"video/mp4": ".mp4", "video/quicktime": ".mov", "image/png": ".png", "image/jpeg": ".jpg"}


def is_finished(asset: ContentAsset | None) -> bool:
    return bool(asset and (asset.candidate_manifest_json or {}).get("schema_version") == SCHEMA)


def _blocked(code: str, *reasons: str) -> HTTPException:
    return HTTPException(409, {"code": code, "reasons": list(reasons)})


def _accepted(db: Session, execution_id: int, role_id: str) -> CreativeExecutionOutput | None:
    return db.scalar(select(CreativeExecutionOutput).where(
        CreativeExecutionOutput.execution_id == execution_id, CreativeExecutionOutput.role_id == role_id,
        CreativeExecutionOutput.state == "accepted").order_by(CreativeExecutionOutput.attempt_no.desc()).limit(1))


def _file(db: Session, role: str, revision_id: int) -> dict:
    revision = db.get(MaterialRevision, revision_id)
    if revision is None:
        raise _blocked("finished_video_file_missing", f"{role}:{revision_id}")
    return {"role": role, "material_revision_id": revision.id, "content_hash": revision.content_hash, "mime_type": revision.mime_type,
            "width": revision.width, "height": revision.height, "duration_ms": revision.duration_ms}


def build_manifest(db: Session, user: User, unit: ContentUnit, execution_id: int) -> dict:
    from . import video_chain
    from .publish_copy import stored

    final = _accepted(db, execution_id, "final")
    if final is None or final.material_revision_id is None:
        raise _blocked("finished_video_final_missing")
    master = video_chain._latest(db, unit.id)
    cover = ((master.payload_json or {}).get("cover") or {}) if master else {}
    files = [_file(db, "final", final.material_revision_id)]
    # The work's covers are the ones the same approval just wrote onto it.
    for role, key in (("cover", "material_revision_id"), ("cover_43", "four_three_material_revision_id"), ("cover_vertical", "vertical_material_revision_id")):
        if type(cover.get(key)) is int:
            files.append(_file(db, role, cover[key]))
    project = db.get(ContentProject, unit.project_id)
    copy = stored(db, unit.id)
    payload = (master.payload_json or {}) if master else {}
    return {
        "schema_version": SCHEMA, "kind": "finished_video", "artifact_kind": "video", "content_form": CONTENT_FORM,
        "channel": unit.channel_id if unit.channel_id in VIDEO_CHANNELS else None,
        "project": {"id": unit.project_id, "title": project.title if project else "", "unit_id": unit.id, "unit_title": unit.title,
                    "modality": unit.modality, "production_domain": unit.production_domain or "persona"},
        "identity": {"persona_id": unit.persona_id, "identity_snapshot_id": unit.identity_snapshot_id},
        "content_master": {"id": master.id, "revision_no": master.revision_no, "payload_hash": master.payload_hash} if master else None,
        "revision_no": master.revision_no if master else None,
        "execution_id": execution_id, "title": payload.get("title") or unit.title,
        "aspect_ratio": payload.get("aspect_ratio"), "files": files, "publish_copy": copy,
    }


def send_to_review(db: Session, user: User, project_id: int, unit_id: int, execution_id: int) -> ContentAsset:
    """Called when the 成片 is approved: the work is finalized and its delivery candidate is frozen."""
    unit = db.get(ContentUnit, unit_id)
    manifest = build_manifest(db, user, unit, execution_id)
    frozen = candidate_hash(manifest)
    asset = db.scalar(select(ContentAsset).where(ContentAsset.project_id == project_id, ContentAsset.content_unit_id == unit_id,
                                                 ContentAsset.candidate_hash == frozen).limit(1))
    if asset is None:
        asset = ContentAsset(project_id=project_id, content_unit_id=unit_id, identity_snapshot_id=unit.identity_snapshot_id,
                             channel=manifest["channel"] or "unassigned", title=manifest["title"][:500], structured_json=None,
                             status="frozen", candidate_hash=frozen, approved_candidate_hash=None, candidate_manifest_json=manifest,
                             artifact_kind="video", content_form=CONTENT_FORM)
        db.add(asset)
        db.flush()
        from .project_events import record_project_event

        record_project_event(db, project_id=project_id, event_type="candidate.frozen", actor=user.email, entity_type="content_asset",
                             entity_id=asset.id, payload={"unit_id": unit_id, "candidate_hash": frozen, "schema_version": SCHEMA,
                                                          "execution_id": execution_id})
    if unit.status not in {"published", "archived"}:
        unit.status = "finalized"
    db.commit()
    db.refresh(asset)
    return asset


def validate_live(db: Session, asset: ContentAsset, *, require_current: bool = True, require_approved: bool = False) -> dict:
    """The candidate's own files must still be there, public and byte-identical; the work's later edits do not matter."""
    from .materials import verify_bytes_checked
    from .production_validation import latest_unit_candidate_id

    manifest = asset.candidate_manifest_json or {}
    if manifest.get("schema_version") != SCHEMA or candidate_hash(manifest) != asset.candidate_hash:
        raise _blocked("candidate_mismatch", "冻结候选哈希不一致")
    if require_current and latest_unit_candidate_id(db, asset.content_unit_id) != asset.id:
        raise _blocked("historical_candidate", "历史候选只可查看")
    if require_approved and (asset.status not in {"approved", "exported"} or asset.approved_candidate_hash != asset.candidate_hash):
        raise _blocked("candidate_unapproved", "候选尚未批准")
    reasons = []
    for item in manifest["files"]:
        revision = db.get(MaterialRevision, item["material_revision_id"])
        if (revision is None or revision.status in {"revoked", "archived"} or revision.public_use_allowed is not True
                or revision.content_hash != item["content_hash"]):
            reasons.append(f"asset_unready:{item['material_revision_id']}")
            continue
        try:
            verify_bytes_checked(db, revision, require_public=True)
        except HTTPException:
            reasons.append(f"asset_bytes_unready:{item['material_revision_id']}")
    if reasons:
        raise _blocked("readiness_blocked", *reasons)
    return manifest


def check_target(asset: ContentAsset, payload) -> SimpleNamespace:
    """Channels are chosen at authorization, one delivery target each; the candidate itself is not tied to one."""
    if payload.channel not in VIDEO_CHANNELS:
        raise HTTPException(422, f"成片只能交付到视频平台：{'、'.join(VIDEO_CHANNELS.values())}")
    if payload.content_form != CONTENT_FORM:
        raise HTTPException(409, "成片的内容形态固定为 short_video")
    if payload.action not in {"copy_package", "manual_handoff"}:
        raise HTTPException(422, "capability_unavailable: 成片当前只支持本地成品包 / 人工交付")
    return SimpleNamespace(channel=payload.channel, content_form=CONTENT_FORM)


def publish_url(channel: str) -> str | None:
    """The platform page a video is uploaded on: its video entry first, else its general one."""
    from .content_identity import creator_links

    links = [link for link in creator_links(channel) if link["label"] != "去数据页"]
    return next((link["url"] for link in links if "视频" in link["label"]), links[0]["url"] if links else None)


def preview(db: Session, asset: ContentAsset) -> dict:
    manifest = asset.candidate_manifest_json or {}
    # The page plays the 成片 through the library's own signed stream, which needs the material id.
    files = [{**item, "material_id": getattr(db.get(MaterialRevision, item["material_revision_id"]), "material_id", None)} for item in manifest["files"]]
    return {"modality": "video", "finished_video": True, "title": asset.title,
            "target": {"channel": None if asset.channel == "unassigned" else asset.channel, "content_form": CONTENT_FORM, "artifact_kind": "video"},
            "channels": VIDEO_CHANNELS, "publish_urls": {key: publish_url(key) for key in VIDEO_CHANNELS}, "aspect_ratio": manifest.get("aspect_ratio"), "files": files,
            "publish_copy": manifest.get("publish_copy"), "checks": [],
            "delivery_notice": "本地包供人工发布；下载和回填凭证都不会替你发到平台。"}


def zip_bytes(db: Session, target, asset: ContentAsset) -> tuple[bytes, str]:
    from .materials import local_file_checked, read_bytes_checked
    from .publish_copy import text

    manifest = validate_live(db, asset, require_current=False, require_approved=True)
    if (target.action not in {"copy_package", "manual_handoff"} or target.content_form != CONTENT_FORM or target.channel not in VIDEO_CHANNELS
            or target.approved_candidate_hash != asset.candidate_hash):
        raise HTTPException(409, "成片交付授权与准确候选 / 渠道不一致")
    covers = [item for item in manifest["files"] if item["role"] != "final"]
    # Every platform package carries every cover the work has; the person picks the one the platform asks for.
    chosen = [item for item in manifest["files"] if item["role"] == "final"] + covers
    names = {"final": "成片", "cover": "封面" if len(covers) < 2 else "横封面-16x9", "cover_43": "横封面-4x3", "cover_vertical": "竖封面-3x4"}
    package = {"export_schema": "studio.finished-video.v1", "schema_version": SCHEMA, "target_id": target.id, "asset_id": asset.id,
               "candidate": {"id": asset.id, "hash": asset.candidate_hash}, "channel": target.channel, "content_form": CONTENT_FORM,
               "account_ref": target.account_ref, "action": target.action, "authorization_version": target.authorization_version,
               "title": manifest["title"], "files": [], "publish_copy": manifest.get("publish_copy"), "remote_call": False}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in chosen:
            revision = db.get(MaterialRevision, item["material_revision_id"])
            if revision.public_use_allowed is not True or revision.content_hash != item["content_hash"]:
                raise HTTPException(409, "冻结媒体字节校验失败")
            name = names[item["role"]] + SUFFIX.get(revision.mime_type, ".bin")
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            # Video is already compressed; storing it keeps a large 成片 from costing a second compression pass.
            info.compress_type = zipfile.ZIP_STORED if revision.mime_type.startswith("video/") else zipfile.ZIP_DEFLATED
            # A 成片 is far over the in-memory read limit, so it is streamed from its hash-checked local file.
            path = local_file_checked(db, revision)
            if path is None:
                data = read_bytes_checked(db, revision, require_public=True)
                if hashlib.sha256(data).hexdigest() != item["content_hash"]:
                    raise HTTPException(409, "冻结媒体字节校验失败")
                archive.writestr(info, data)
            else:
                with path.open("rb") as source, archive.open(info, "w", force_zip64=True) as sink:
                    while chunk := source.read(1024 * 1024):
                        sink.write(chunk)
            package["files"].append({**item, "name": name})
        copy = text(manifest.get("publish_copy"))
        if copy:
            archive.writestr(zipfile.ZipInfo("发布文案.txt", date_time=(2020, 1, 1, 0, 0, 0)), copy)
        archive.writestr(zipfile.ZipInfo("manifest.json", date_time=(2020, 1, 1, 0, 0, 0)),
                         json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True))
        archive.writestr(zipfile.ZipInfo("发布说明.md", date_time=(2020, 1, 1, 0, 0, 0)),
                         f"# 发布说明\n\n- 平台：{VIDEO_CHANNELS.get(target.channel, target.channel)}\n- 账号：{target.account_ref}\n- 候选哈希：{target.approved_candidate_hash}\n\n"
                         "在平台上手动上传成片和封面、填好发布文案；发布后回到审阅与交付回填发布凭证。本包没有调用任何平台接口。\n")
    db.expire_all()
    validate_live(db, db.get(ContentAsset, target.content_asset_id), require_current=False, require_approved=True)
    return buffer.getvalue(), f"delivery-target-{target.id}.zip"
