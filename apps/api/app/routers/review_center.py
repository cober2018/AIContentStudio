"""Review & Publish Center（D26/§7）：Topic-centric 聚合 projection。

不新增 ReviewCenter 表：聚合 Topic/WorkflowRun/Draft/DraftCheckRun/DraftMedia/
DiscoverabilityReport/ContentAsset/DeliveryTarget 组装视图；readiness 是投影。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import (
    ContentAsset,
    ContentJob,
    DeliveryTarget,
    Draft,
    FactPackStatus,
    TopicBrief,
    User,
    WorkflowRun,
)
from ..services import checks as checks_service
from ..services import discoverability as disco
from ..services.content_harness import channel_registry

router = APIRouter(prefix="/api/v1/review-center", tags=["review-center"])


def _readiness_projection(db: Session, draft: Draft | None, asset: ContentAsset | None, targets: list[DeliveryTarget], checks: list, pack_status: str | None) -> dict:
    media_states = []
    if draft:
        from ..services.content_harness.rules import effective_media_rights

        for media in draft.media:
            reason = effective_media_rights(media)
            if reason in {"use_revoked", "revision_revoked"}:
                media_states.append("revoked")
            elif reason is not None:
                media_states.append("warning")
    platform_blockers = [c.check_kind for c in checks if c.status == "blocker"]
    # R4-N2：media readiness 结合 Channel Profile 的 media_requirements——
    # 「小红书缺必需图片」在汇总卡就显示 blocked，而不是等 Approval 才暴露
    media_requirements: dict = {}
    if draft is not None:
        try:
            from ..services.content_harness.rules import media_requirements_for

            media_requirements = media_requirements_for(db, draft)
        except Exception:  # noqa: BLE001 渠道解析失败：按无要求展示
            media_requirements = {}
    requirements_unmet = bool(media_requirements) and not _draft_has_required_media(draft, media_requirements)
    if draft is None:
        media_state = "none"
    elif "revoked" in media_states or requirements_unmet:
        media_state = "blocked"
    elif media_states:
        media_state = "warning"
    else:
        media_state = "ready" if draft.media else "none"
    delivery_states = [t.status for t in targets]
    return {
        "content": "missing" if draft is None else ("ready" if draft.candidate_readiness == "ready" else "in_progress"),
        "evidence": "ready" if pack_status == FactPackStatus.frozen.value else "blocked",
        "media": media_state,
        "platform": "blocked" if platform_blockers else ("ready" if checks else "incomplete"),
        "delivery": (
            "delivered" if "human_confirmed" in delivery_states
            else "blocked" if "blocked" in delivery_states or "reconciliation_needed" in delivery_states
            else "authorized" if delivery_states
            else ("not_authorized" if asset else "awaiting_approval")
        ),
    }


def _draft_has_required_media(draft: Draft | None, requirements: dict) -> bool:
    """media_requirements 满足判定（与 rule.media.required 同语义：真实字节才算）。"""
    if draft is None:
        return False
    from ..services.content_harness.rules import _has_real_bytes

    if requirements.get("cover") == "required":
        covers = [m for m in draft.media if m.role == "cover"]
        if not covers or not any(_has_real_bytes(m) for m in covers):
            return False
    return not (
        requirements.get("inline") == "required"
        and not any(_has_real_bytes(m) for m in draft.media if m.role == "inline")
    )


@router.get("/topics/{topic_id}")
def topic_review_center(topic_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topic = db.get(TopicBrief, topic_id)
    if not topic:
        raise HTTPException(404, "Topic 不存在")
    pack = topic.fact_pack
    targets_spec = topic.targets_json or [{"channel": c, "content_form": None} for c in (topic.channels or [])]
    jobs = []
    for job in db.scalars(select(ContentJob).where(ContentJob.topic_brief_id == topic.id)):
        run = db.get(WorkflowRun, job.workflow_run_id) if job.workflow_run_id else None
        if run is None or run.content_unit_id is None:
            jobs.append(job)

    targets_out = []
    for spec in targets_spec:
        channel = spec.get("channel")
        form = spec.get("content_form")
        try:
            form_spec = channel_registry.resolve_content_form(db, channel, form).to_dict()
        except Exception:  # noqa: BLE001 渠道下线：保留行
            form_spec = {"channel": channel, "content_form": form, "label": form or channel}
        channel_jobs = [
            j for j in jobs
            if j.channel == channel and (j.content_form or None) == (form or None)
        ]
        latest_job = max(channel_jobs, key=lambda j: j.id, default=None)
        draft = (
            db.scalars(select(Draft).where(Draft.content_job_id == latest_job.id).order_by(Draft.revision_no.desc()).limit(1)).first()
            if latest_job
            else None
        )
        run = (
            db.get(WorkflowRun, latest_job.workflow_run_id)
            if latest_job and latest_job.workflow_run_id
            else None
        )
        checks = checks_service.current_checks(db, draft) if draft else []
        report = (
            disco.latest_report(db, draft_id=draft.id, stage="post")
            if draft
            else None
        )
        asset = (
            db.scalars(select(ContentAsset).where(ContentAsset.draft_id == draft.id, ContentAsset.approved_candidate_hash.is_not(None)).order_by(ContentAsset.id.desc()).limit(1)).first()
            if draft
            else None
        )
        delivery_targets = (
            db.scalars(select(DeliveryTarget).where(DeliveryTarget.content_asset_id == asset.id).order_by(DeliveryTarget.id.desc())).all()
            if asset
            else []
        )
        targets_out.append({
            "channel": channel,
            "content_form": form,
            "form_label": form_spec.get("label"),
            "artifact_kind": form_spec.get("artifact_kind"),
            "workflow_run": (
                {
                    "id": run.id, "status": run.status, "workflow_key": run.workflow_key,
                    "workflow_version": run.workflow_version, "error": run.error,
                }
                if run
                else {"id": None, "status": "not_started", "workflow_key": form_spec.get("workflow_key")}
            ),
            "draft": (
                {
                    "id": draft.id, "revision_no": draft.revision_no, "title": draft.title,
                    "status": draft.status, "candidate_readiness": draft.candidate_readiness,
                    "artifact_kind": draft.artifact_kind,
                }
                if draft
                else None
            ),
            "checks": [
                {"kind": c.check_kind, "status": c.status, "input_hash": c.input_hash, "profile": c.profile_key}
                for c in checks
            ],
            "discoverability": disco.serialize(report) if report else None,
            "materials": [
                {
                    "draft_media_id": m.id, "role": m.role, "sort_order": m.sort_order,
                    "material_revision_id": m.material_revision_id, "hash": m.content_hash,
                    "public_use_allowed": m.public_use_allowed,
                    "alt_text": m.alt_text, "caption": m.caption,
                }
                for m in (draft.media if draft else [])
            ],
            "candidate": (
                {
                    "asset_id": asset.id, "approved_candidate_hash": asset.approved_candidate_hash,
                    "manifest_schema": (asset.candidate_manifest_json or {}).get("schema_version"),
                    "approved_revision": asset.approved_revision, "reviewer": asset.reviewer,
                    "capability_unverified": True,
                }
                if asset
                else None
            ),
            "delivery": [
                {
                    "id": t.id, "channel": t.channel, "content_form": t.content_form,
                    "action": t.action, "account_ref": t.account_ref, "status": t.status,
                    "publisher_key": t.publisher_key,
                    "capability": t.capability_snapshot_json,
                }
                for t in delivery_targets
            ],
            "readiness": _readiness_projection(db, draft, asset, delivery_targets, checks, pack.status),
        })

    return {
        "topic": {
            "id": topic.id, "title": topic.title, "status": topic.status,
            "fact_pack": {"id": pack.id, "name": pack.name, "version": pack.version, "status": pack.status, "checksum": pack.checksum},
            "channels": topic.channels or [],
            "targets": targets_spec,
        },
        "content_core": {
            "mother_revisions": [
                {"id": r.id, "revision_no": r.revision_no, "title": r.title, "body_hash": r.body_hash}
                for r in topic.mother_revisions
            ],
        },
        "targets": targets_out,
    }
