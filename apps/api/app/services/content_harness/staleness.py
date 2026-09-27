"""Staleness 服务（D28 基础版）：派生状态失效的唯一入口。

Phase 2 落 draft/media 相关失效；Phase 6 扩展 workflow downstream 标记与 rerun 联动。
现有散落的 `candidate_readiness = "stale"` / `fact_check_json = None` 逐步统一到这里。
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import ContentAsset, Draft, DraftMedia


def mark_draft_changed(db: Session, draft: Draft, reason: str = "draft_changed") -> None:
    """正文/结构/标题等输入变化：候选失效，旧事实检查不再代表当前输入。"""
    from ...services import checks as checks_service

    draft.candidate_readiness = "stale"
    if draft.fact_check_json is not None:
        draft.fact_check_json = None
    checks_service.mark_all_stale(db, draft, reason)


def mark_media_changed(db: Session, draft: Draft, reason: str = "media_changed") -> None:
    """素材集合/顺序/placement 变化：候选失效（media 属于 candidate 输入）。

    R2-M8：只换图不重跑正文 FactCheck——fact_check_json 保留（正文输入未变），
    仅 media/rights 相关 check runs 标 stale（下次批准前重算）。
    """
    from ...services import checks as checks_service

    draft.candidate_readiness = "stale"
    checks_service.mark_kinds_stale(db, draft, {"media", "rights"}, reason or "media_changed")


def invalidate_candidate(db: Session, draft_id: int, reason: str = "invalidated") -> int:
    """记录「历史批准候选事后失效」事件（R3-6：Immutable Candidate——绝不修改历史 manifest）。

    ContentAsset.candidate_manifest_json 与 approved_candidate_hash 永不改写；
    失效语义由承载方表达：素材撤权（rights status）、交付目标 blocked、审计记录。
    返回受影响 asset 数。
    """
    from ...models import AuditLog

    assets = db.scalars(select(ContentAsset).where(ContentAsset.draft_id == draft_id)).all()
    count = 0
    for asset in assets:
        db.add(
            AuditLog(
                event="candidate.invalidated",
                actor="system",
                entity_type="content_asset",
                entity_id=str(asset.id),
                detail_json={"reason": reason, "approved_candidate_hash": asset.approved_candidate_hash},
            )
        )
        count += 1
    return count


def mark_material_rights_revoked(db: Session, material_revision_id: int, note: str) -> list[int]:
    """素材撤权：所有引用该 revision 的 draft 候选失效。返回受影响 draft ids。"""
    uses = db.scalars(select(DraftMedia).where(DraftMedia.material_revision_id == material_revision_id)).all()
    draft_ids: list[int] = []
    for use in uses:
        draft = db.get(Draft, use.draft_id)
        if draft and draft.id not in draft_ids:
            draft_ids.append(draft.id)
        if draft:
            mark_media_changed(db, draft, reason=f"material_rights_revoked: {note}"[:200])
    return draft_ids


def mark_workflow_downstream_stale(db: Session, run, node_id: str, reason: str) -> int:
    """D28：workflow 下游节点标 stale（Phase 6）。engine 的 rerun 变更检测统一走这里。"""
    from ...services.workflow_engine import _definition_of, _downstream, _steps

    downstream = set(_downstream(_definition_of(db, run), node_id))
    count = 0
    for step in _steps(db, run):
        if step.node_id in downstream and step.status in {"succeeded", "failed", "skipped"}:
            step.status = "stale"
            step.stale_reason = reason
            count += 1
    return count
