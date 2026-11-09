"""图文采用后：平台出图、存成图版，停下等用户验收；验收通过再生成渠道版本、冻结候选，送进审阅与交付。"""

from __future__ import annotations

import hashlib
import io
import logging
from datetime import UTC, datetime

from fastapi import HTTPException
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ChannelVariantRevision, ContentAsset, ContentMasterRevision, MaterialRevision, ProjectMaterialReference, User
from . import article_chain, materials, provider_calls
from .production_modalities import render_input_hash
from .project_events import record_project_event

RENDERER = ("graphic.chromium", "1")
RENDER_FAILURES = {
    "unavailable": "本地出图工具没配好（GRAPHIC_RENDER_*）",
    "failed": "出图失败：检查字体是否覆盖所有文字、字重是否都是常规、同一文字层是否只有一种对齐",
}


def _fail(code: str, message: str, status: int = 409):
    raise HTTPException(status, {"code": code, "message": message})


def _rendered(master: ContentMasterRevision) -> bool:
    return (master.edit_summary_json or {}).get("article_chain") == "rendered" and bool((master.payload_json or {}).get("render_asset_ref"))


def _sources(db: Session, master: ContentMasterRevision) -> list[dict]:
    from .content_masters import _serialize

    sources, seen = [], set()
    for ref in _serialize(db, master)["assets"]:
        if ref["role"] == "render_output" or ref["material_revision_id"] in seen:
            continue
        seen.add(ref["material_revision_id"])
        revision = db.get(MaterialRevision, ref["material_revision_id"])
        placement = ref.get("placement") or {}
        where = f"画布「{placement.get('canvas_id')}」上的图（素材 {revision.id if revision else ref['material_revision_id']}）"
        if revision is None or revision.public_use_allowed is not True or revision.status in {"revoked", "archived"}:
            _fail("graphic_review_source_not_public", f"{where}不能公开使用，成图发不出去；先换图或把素材设为可公开使用", 422)
        try:
            content = materials.read_bytes_checked(db, revision, require_public=True)
        except HTTPException:
            _fail("graphic_review_source_unreadable", f"{where}读不到原文件（素材盘没接上？）")
        sources.append({"revision": revision, "revision_id": revision.id, "content_hash": revision.content_hash,
                        "mime_type": revision.mime_type, "content": content})
    return sources


def _current_context_hash(db: Session, unit, master: ContentMasterRevision) -> str:
    from ..models import ContentProject
    from .content_masters import _context, _hash

    return _hash(_context(db, db.get(ContentProject, unit.project_id), unit, content_form=master.content_form))


def _render(db: Session, user: User, project_id: int, unit, master: ContentMasterRevision) -> ContentMasterRevision:
    from types import SimpleNamespace

    from .content_masters import save_revision
    from .content_harness.providers import bootstrap_media_providers
    from .media_renderers import resolve_renderer

    bootstrap_media_providers()
    renderer, fingerprint = resolve_renderer(*RENDERER)
    if (master.channel_id, master.content_form) not in renderer.supported_forms:
        _fail("graphic_review_form_unsupported", "这篇的渠道形式不能用本地出图工具出图（只支持小红书图文、公众号图片消息）", 422)
    sources = _sources(db, master)
    # The rendered revision is saved under the current context (e.g. facts frozen after approval), so its input hash is computed for that.
    input_hash = render_input_hash(db, SimpleNamespace(id=master.id, project_id=master.project_id, content_unit_id=master.content_unit_id,
                                                       payload_schema=master.payload_schema, payload_json=master.payload_json,
                                                       context_hash=_current_context_hash(db, unit, master),
                                                       channel_id=master.channel_id, content_form=master.content_form))
    payload = {key: value for key, value in master.payload_json.items() if key != "render_asset_ref"}
    outputs = []
    for canvas in payload["canvases"]:
        request = {"payload": payload, "payload_schema": master.payload_schema, "render_input_hash": input_hash,
                   "canvas_id": canvas["id"], "timeout_seconds": 30, "channel": master.channel_id, "content_form": master.content_form,
                   "max_output_bytes": 30 * 1024 * 1024,
                   "source_assets": [{key: item[key] for key in ("revision_id", "content_hash", "mime_type", "content")} for item in sources]}
        output = provider_calls.call(renderer.render_master, request)
        if getattr(output, "status", None) != "succeeded" or output.canvas_id != canvas["id"] or output.render_input_hash != input_hash:
            _fail("graphic_review_render_failed", f"第 {canvas['order'] + 1} 张（{canvas['id']}）{RENDER_FAILURES.get(getattr(output, 'status', None), '出图失败')}")
        with Image.open(io.BytesIO(output.content)) as image:
            if image.size != (canvas["width"], canvas["height"]):
                _fail("graphic_review_render_size", f"第 {canvas['order'] + 1} 张出图尺寸和画布不一致")
        outputs.append((canvas, output.content))
    revisions = [item["revision"] for item in sources]
    rights = {"model_use_allowed": all(item.model_use_allowed is True for item in revisions),
              "commercial_use_allowed": all(item.commercial_use_allowed is True for item in revisions)}
    render_refs, declarations = [], []
    base_refs = article_chain._asset_refs(db, "graphic", payload)
    for canvas, content in outputs:
        material = materials.create_material(db, kind="image", title=f"{unit.title} · 成图 {canvas['order'] + 1}"[:200], created_by=user.email)
        revision = materials.create_revision(
            db, material, content=content, suffix=".png", declared_mime="image/png", source_kind="upstream",
            source_metadata={"renderer_origin": {"renderer_key": renderer.key, "renderer_version": renderer.version, "runtime_hash": fingerprint,
                                                 "master_id": master.id, "canvas_id": canvas["id"], "render_input_hash": input_hash},
                             "source_refs": [{"revision_id": item["revision_id"], "content_hash": item["content_hash"]} for item in sources]},
            provider_key=renderer.key, provider_version=renderer.version, public_use_allowed=True,
            width=canvas["width"], height=canvas["height"], created_by=user.email, **rights)
        revision.status = "usable"
        db.add(ProjectMaterialReference(project_id=project_id, material_revision_id=revision.id, origin="system_reference",
                                        status="active", attached_by=user.email))
        db.flush()
        record_project_event(db, project_id=project_id, event_type="asset.attached", actor=user.email, entity_type="material_revision",
                             entity_id=revision.id, payload={"content_hash": revision.content_hash, "graphic_render": canvas["id"]})
        render_refs.append({"material_revision_id": revision.id, "content_hash": revision.content_hash, "role": "render_output",
                            "slot_key": canvas["id"], "sort_order": canvas["order"], "placement": {"canvas_id": canvas["id"]}})
        declarations.append({"canvas_id": canvas["id"], "material_revision_id": revision.id})
    db.flush()
    token = article_chain.finalizing.set(unit.id)
    try:
        saved = save_revision(db, project_id=project_id, unit_id=unit.id, user=user, payload={
            "expected_revision": master.revision_no, "parent_revision_id": master.id, "content_form": master.content_form,
            "idempotency_key": f"graphic-render:{master.id}:{hashlib.sha256(input_hash.encode()).hexdigest()[:16]}",
            "payload_schema": master.payload_schema, "payload": {**payload, "render_asset_ref": declarations}, "source_kind": "user_edit",
            "edit_summary": {"article_chain": "rendered", "rendered_from": master.id},
            "asset_refs": base_refs + render_refs, "evidence_refs": article_chain._evidence_refs("graphic", payload),
            "render_attestation": {"confirmed": True, "render_input_hash": input_hash}})
    finally:
        article_chain.finalizing.reset(token)
    rendered = db.get(ContentMasterRevision, saved["id"])
    # The images wait for the user's check (成图待你验收) before the piece is final.
    record = article_chain._record(db, unit.id)
    record["decisions"].append({"target_id": rendered.id, "decision": "rendered", "notes": [], "by": user.email,
                                "rendered_from": master.id, "at": datetime.now(UTC).isoformat()})
    article_chain._put(db, unit.id, record)
    db.commit()
    return rendered


def _variant(db: Session, user: User, project_id: int, unit_id: int, master: ContentMasterRevision) -> ChannelVariantRevision:
    from . import channel_variants

    key = f"{master.channel_id}.{master.content_form}"
    preview = channel_variants.adapt_preview(db, project_id=project_id, unit_id=unit_id, user=user, payload={
        "source_master_revision_id": master.id, "expected_source_payload_hash": master.payload_hash,
        "expected_source_context_hash": master.context_hash, "channel_id": master.channel_id, "content_form": master.content_form})
    head = db.scalar(select(ChannelVariantRevision).where(ChannelVariantRevision.content_unit_id == unit_id,
                                                          ChannelVariantRevision.variant_key == key)
                     .order_by(ChannelVariantRevision.revision_no.desc()).limit(1))
    if head is not None and head.source_master_revision_id == master.id:
        return head
    saved = channel_variants.save_revision(db, project_id=project_id, unit_id=unit_id, user=user, payload={
        "source_master_revision_id": master.id, "expected_source_payload_hash": master.payload_hash,
        "expected_source_context_hash": master.context_hash, "channel_id": master.channel_id, "content_form": master.content_form,
        "variant_key": key, "expected_revision": head.revision_no if head else 0, "idempotency_key": f"graphic-review:{master.id}",
        "source_kind": "deterministic_adapt", "expected_profile_hash": preview["profile_hash"], "payload": preview["payload"],
        "asset_refs": preview["asset_refs"], "evidence_refs": preview["evidence_refs"]})
    return db.get(ChannelVariantRevision, saved["id"])


def _graphic_unit(db: Session, user: User, project_id: int, unit_id: int):
    unit = article_chain._unit(db, user, project_id, unit_id, mutate=True)
    if unit.modality != "graphic":
        _fail("graphic_review_modality", "只有图文作品走这一步", 422)
    master = article_chain._latest(db, unit_id)
    if not master.channel_id or not master.content_form:
        _fail("graphic_review_channel_missing", "这篇还没选渠道和形式", 422)
    return unit, master


def render_for_check(db: Session, user: User, project_id: int, unit_id: int) -> ContentMasterRevision:
    """After 采用: draw every canvas and stop at 成图待你验收."""
    unit, master = _graphic_unit(db, user, project_id, unit_id)
    if article_chain._state(db, unit_id)["state"] != "rendering":
        _fail("graphic_review_not_final", "这篇还没采用")
    return _render(db, user, project_id, unit, master)


def send_to_review(db: Session, user: User, project_id: int, unit_id: int) -> ContentAsset | None:
    """After 验收通过: build, check and freeze the channel variant. Facts changed since then mean new images to check (None)."""
    from . import channel_variants, content_masters
    from .project_review import freeze_variant_candidate

    unit, master = _graphic_unit(db, user, project_id, unit_id)
    if not article_chain.locked(db, unit_id):
        _fail("graphic_review_not_final", "成图还没验收")
    if not _rendered(master) or master.context_hash != _current_context_hash(db, unit, master):
        _render(db, user, project_id, unit, master)
        return None
    sent = db.scalar(select(ContentAsset).join(ChannelVariantRevision, ContentAsset.channel_variant_revision_id == ChannelVariantRevision.id)
                     .where(ContentAsset.content_unit_id == unit_id, ChannelVariantRevision.source_master_revision_id == master.id)
                     .order_by(ContentAsset.id.desc()).limit(1))
    if sent is not None:
        return sent
    content_masters.run_checks(db, project_id, unit_id, master.id, user)
    variant = _variant(db, user, project_id, unit_id, master)
    checks = channel_variants.run_variant_checks(db, project_id, unit_id, variant.id, user)
    if not checks.get("ready"):
        blocked = [f"{item['check_kind']}（{'、'.join(map(str, (item.get('report') or {}).get('reasons') or [])) or item['status']}）"
                   for item in checks["items"] if item["status"] != "pass"]
        if checks["source_gate"].get("status") != "pass":
            blocked.append("稿件检查")
        _fail("graphic_review_checks_blocked", f"渠道版本检查没过：{'、'.join(blocked + checks.get('drift_reasons', [])) or '见渠道版本检查'}")
    asset = freeze_variant_candidate(db, project_id, unit_id, variant.id, user, expected_payload_hash=variant.payload_hash)
    if unit.status not in {"published", "archived"}:
        unit.status = "finalized"
    db.commit()
    db.refresh(asset)
    return asset


def run(db: Session, user: User, project_id: int, unit_id: int) -> dict:
    """Records how sending went on the work, so the page can show the reason and a retry."""
    try:
        if article_chain._state(db, unit_id)["state"] == "done":
            asset = send_to_review(db, user, project_id, unit_id)
            outcome = {"state": "sent", "candidate_id": asset.id} if asset else {"state": "rendered"}
        else:
            render_for_check(db, user, project_id, unit_id)
            outcome = {"state": "rendered"}
    except HTTPException as exc:
        db.rollback()
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        if detail.get("code") in {"graphic_review_modality", "graphic_review_not_final", "article_chain_modality"} or exc.status_code in {403, 404}:
            raise
        reasons = detail.get("reasons")
        outcome = {"state": "failed", "message": detail.get("message") or (f"{detail.get('code')}：{'、'.join(map(str, reasons))}" if reasons else str(detail.get("code") or "送审失败"))}
    except Exception:  # noqa: BLE001 The approval stands; the page shows the failure and offers a retry.
        db.rollback()
        logging.getLogger(__name__).warning("graphic review failed: unit=%s", unit_id, exc_info=True)
        outcome = {"state": "failed", "message": "出图或送审时出错，稍后点「重试」再试"}
    record = article_chain._record(db, unit_id)
    record["review"] = {**outcome, "at": datetime.now(UTC).isoformat()}
    article_chain._put(db, unit_id, record)
    db.commit()
    return record["review"]
