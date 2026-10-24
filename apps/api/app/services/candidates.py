"""Canonical candidate manifest for approval and manual handoff.

V1 PRD 2.0（D18）：schema v2 覆盖最终 Document、真实素材、检查、SEO、Render、
Workflow/Plugin 版本快照；candidate hash 对整个 canonical JSON 计算。
schema v1 builder 保留供 legacy M1 读取。
"""

import hashlib
import json

from sqlalchemy.orm import Session

from ..models import ContentAsset, Draft, WorkflowRun
from . import checks as checks_service
from .content_harness.renderers import bootstrap_renderers, render_for


def build_manifest(draft: Draft) -> dict:
    media = [
        {
            "id": row.id,
            "hash": row.content_hash,
            "role": row.role,
            "sort_order": row.sort_order,
            "public_use_allowed": row.public_use_allowed,
            "rights_status": row.rights_status,
        }
        for row in draft.media
    ]
    return {
        "schema_version": 1,
        "draft_id": draft.id,
        "revision_no": draft.revision_no,
        "title": draft.title,
        "body_markdown": draft.body,
        "structured": draft.structured_json,
        "thread_posts": draft.thread_posts_json,
        "media": media,
        "citations": (draft.structured_json or {}).get("citations") or (draft.structured_json or {}).get("claim_fact_map") or [],
        "declarations": (draft.structured_json or {}).get("declarations") or [],
        "fact_check": draft.fact_check_json,
        "mother_revision_id": draft.mother_revision_id,
        "input_hash": draft.input_hash,
    }


def readiness_reasons(draft: Draft) -> list[str]:
    reasons: list[str] = []
    fact_check = draft.fact_check_json or {}
    if not fact_check:
        reasons.append("missing_fact_check")
    elif fact_check.get("result") == "blocker":
        reasons.append("blocking_fact_check")
    if draft.input_hash and fact_check.get("input_hash") not in {None, draft.input_hash}:
        reasons.append("stale_fact_check")
    for media in draft.media:
        if media.public_use_allowed is not True or not media.rights_status or media.public_use_revoked_at:
            reasons.append(f"media_rights_incomplete:{media.id}")
    from .content_harness.channel_methods import readiness_gaps

    reasons.extend(readiness_gaps(
        draft.content_job.channel,
        has_cover=any(media.role == "cover" for media in draft.media),
        has_thread_posts=bool(draft.thread_posts_json),
    ))
    return reasons


def candidate_hash(manifest: dict) -> str:
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def draft_input_hash(title: str, body: str, thread_posts: list | None, media: list | None = None) -> str:
    payload = {"title": title, "body": body, "thread_posts": thread_posts or [], "media": media or []}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------- schema v2（D18）----------


def _media_v2(draft: Draft) -> list[dict]:
    media = []
    for row in draft.media:
        media.append(
            {
                "draft_media_id": row.id,
                "material_revision_id": row.material_revision_id,
                "hash": row.content_hash,
                "role": row.role,
                "sort_order": row.sort_order,
                "placement": row.placement_json or {},
                "alt_text": row.alt_text,
                "caption": row.caption,
                "rights": {
                    "rights_status": row.rights_status,
                    "public_use_allowed": row.public_use_allowed is True,
                    "revoked": row.public_use_revoked_at is not None,
                },
            }
        )
    return media


def _execution_snapshot(db: Session, draft: Draft) -> dict:
    """从 content_job.workflow_run_id 还原 Workflow/定义身份（D5 冻结信息的读取）。

    R2-B4：plugins 快照取自 run 的 WorkflowStep 钉死记录（node plugin key@version 去重），
    skills 取自冻结 definition 的引用——candidate hash 由此绑定实际执行过的插件与技能版本。
    """
    from sqlalchemy import select

    from ..models import Workflow, WorkflowStep

    job = draft.content_job
    snapshot: dict = {"workflow_key": None, "workflow_version": None, "workflow_checksum": None, "plugins": [], "skills": []}
    if job.workflow_run_id:
        run = db.get(WorkflowRun, job.workflow_run_id)
        if run:
            snapshot.update(
                {
                    "workflow_key": run.workflow_key,
                    "workflow_version": run.workflow_version,
                    "workflow_checksum": run.definition_checksum,
                    "workflow_run_id": run.id,
                }
            )
            steps = db.scalars(select(WorkflowStep).where(WorkflowStep.run_id == run.id)).all()
            pairs = sorted({(s.plugin_key, s.plugin_version) for s in steps if s.plugin_key})
            snapshot["plugins"] = [{"key": key, "version": version} for key, version in pairs]
            workflow = db.get(Workflow, run.workflow_id)
            if workflow:
                from .content_harness.skill_runtime import _referenced_skills

                snapshot["skills"] = [
                    {"skill": r["skill"], "skill_version": r["skill_version"]}
                    for r in _referenced_skills(workflow.definition_json or {})
                ]
    return snapshot


def _discoverability_freeze(db: Session, draft: Draft) -> tuple[dict | None, bool]:
    """R2-B4：冻结当前有效的 post 阶段 DiscoverabilityReport + profile 是否声明 SEO 必需。"""
    from . import discoverability as disco
    from .content_harness.channel_registry import resolve_content_form

    job = draft.content_job
    content_form = getattr(draft, "content_form", None) or job.content_form
    required = False
    try:
        spec = resolve_content_form(db, job.channel, content_form)
        required = bool(spec.discoverability_profile)
    except Exception:  # noqa: BLE001 渠道解析失败：不强制
        required = False
    report = disco.latest_report(db, draft_id=draft.id, stage="post")
    frozen = None
    if report is not None:
        frozen = {
            "report_id": report.id,
            "stage": report.stage,
            "profile_version_id": report.profile_version_id,
            "input_hash": report.input_hash,
            "status": report.status,
            "report": report.report_json,
            "model_provider": report.model_provider,
            "model_name": report.model_name,
        }
    return frozen, required


def build_manifest_v2(db: Session, draft: Draft) -> dict:
    """schema v2 manifest：批准前调用（含 render 冻结）。"""
    bootstrap_renderers()
    checks = checks_service.current_checks(db, draft)

    media_v2 = _media_v2(draft)
    render_result = render_for(db, draft, media=media_v2)
    job = draft.content_job
    topic = job.topic_brief
    discoverability, discoverability_required = _discoverability_freeze(db, draft)

    manifest = {
        "schema_version": 2,
        "artifact_kind": draft.artifact_kind or "text",
        "content_form": getattr(draft, "content_form", None) or job.content_form,
        "channel": job.channel,
        "source": {
            "topic_id": topic.id,
            "mother_revision_id": draft.mother_revision_id,
            "evidence_checksum": draft.evidence_checksum,
            "fact_pack_id": topic.fact_pack_id,
            "fact_pack_version": topic.fact_pack_version,
            "fact_pack_checksum": topic.fact_pack.checksum,
        },
        "content": {
            "title": draft.title,
            "body_markdown": draft.body,
            "document": draft.document_json,
            "structured": draft.structured_json,
            "thread_posts": draft.thread_posts_json,
        },
        "media": media_v2,
        "checks": [
            {"id": row.id, "kind": row.check_kind, "input_hash": row.input_hash, "status": row.status}
            for row in checks
        ],
        "discoverability": discoverability,  # R2-B4：冻结当前有效 post 报告（进入 candidate hash）
        "discoverability_required": discoverability_required,  # profile 声明了 SEO 才是批准前置
        "render": {
            "renderer_key": render_result.renderer_key,
            "renderer_version": render_result.version,
            "content_hash": render_result.content_hash,
            "payload": render_result.payload,
            "warnings": render_result.warnings,
        },
        "execution": _execution_snapshot(db, draft),
        "declarations": (draft.structured_json or {}).get("declarations") or [],
        "citations": (draft.structured_json or {}).get("citations") or [],
        "input_hash": draft.input_hash,
        "revision_no": draft.revision_no,
    }
    return manifest


def readiness_reasons_v2(db: Session, draft: Draft, manifest: dict | None = None, *, required: list[str] | None = None) -> list[str]:
    """schema v2 readiness Gate：检查绑定当前输入 + 媒体真实权利 + render 冻结。"""
    reasons: list[str] = []
    manifest = manifest or build_manifest_v2(db, draft)

    # 1) mandatory checks 必须存在且 current（incomplete 不是 pass）
    missing = checks_service.missing_mandatory_kinds(db, draft, required=required)
    if missing:
        reasons.append(f"missing_or_failed_checks:{missing}")

    # 1b) 已运行的 media/rights 检查出现 blocker（有素材但非真实/无权利）→ 阻止
    for row in checks_service.current_checks(db, draft):
        if row.check_kind in {"media", "rights"} and row.status == "blocker":
            reasons.append(f"check_blocker:{row.check_kind}")

    # 2) fact check blocker / 绑定
    fc = draft.fact_check_json or {}
    if not fc:
        reasons.append("missing_fact_check")
    elif fc.get("result") == "blocker":
        reasons.append("blocking_fact_check")
    elif fc.get("input_hash") not in {None, draft.input_hash}:
        reasons.append("fact_check_not_bound_to_candidate")

    # 3) 媒体：真实字节 + 统一权利判定（R4-B3：use 行 + MaterialRevision 全局撤权同时检查，
    #    复核 manifest，防止 checks 与 manifest 漂移）
    from .content_harness.rules import _has_real_bytes, effective_media_rights

    for m, row in zip(manifest["media"], draft.media):
        if (reason := effective_media_rights(row)) is not None:
            reasons.append(f"media_rights_incomplete:{m['draft_media_id']}:{reason}")
        if not _has_real_bytes(row):
            reasons.append(f"media_not_actual:{m['draft_media_id']}")

    # 3b) R2-B2：Channel Profile media_requirements 直接强制——零图/占位图的小红书必须 blocker，
    # 不依赖 check run 是否已运行（Prompt 不算成品，实际素材必须参与审批）
    requirements = _media_requirements(db, draft)
    if requirements.get("cover") == "required":
        covers = [m for m in draft.media if m.role == "cover"]
        if not covers or not any(_has_real_bytes(m) for m in covers):
            reasons.append("missing_required_cover")
    if requirements.get("inline") == "required" and not any(
        _has_real_bytes(m) for m in draft.media if m.role == "inline"
    ):
        reasons.append("missing_required_inline_media")

    # 4) render 必须已冻结且非空
    render = manifest.get("render") or {}
    if not render.get("content_hash"):
        reasons.append("render_not_frozen")

    # 5) profile 声明的 discoverability（声明了才必需；R2-B4 起报告冻进 candidate hash）。
    #    只要求「存在并冻结」——报告 status（ready/incomplete）是 Review Center 的展示信息，
    #    不作为批准硬闸（incomplete 会被如实冻结，批准者据此人工判断）。
    if manifest.get("discoverability_required") and not manifest.get("discoverability"):
        reasons.append("missing_discoverability_report")

    return sorted(set(reasons))


def _media_requirements(db: Session, draft: Draft) -> dict:
    try:
        from .content_harness.rules import media_requirements_for

        return media_requirements_for(db, draft)
    except Exception:  # noqa: BLE001
        return {}


def asset_v2_columns(manifest: dict) -> dict:
    """ContentAsset 实体列提取（§6.23：为查询性能落列）。"""
    execution = manifest.get("execution") or {}
    return {
        "artifact_kind": manifest.get("artifact_kind"),
        "content_form": manifest.get("content_form"),
        "workflow_key": execution.get("workflow_key"),
        "workflow_version": execution.get("workflow_version"),
    }


def referenced_material_revisions(db: Session, asset: ContentAsset) -> set[int]:
    ids: set[int] = set()
    for media in (asset.candidate_manifest_json or {}).get("media", []):
        rid = media.get("material_revision_id")
        if isinstance(rid, int):
            ids.add(rid)
    return ids
