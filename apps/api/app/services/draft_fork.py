"""Draft Revision Fork（R3-5）：人工编辑 / SEO apply 等所有「产生新 revision」入口的统一实现。

旧 revision 永不覆盖（PRD 验收 13）；fork 时：
- 克隆 DraftMedia use（新 use 行指向同一 MaterialRevision——素材字节内容寻址，不复制文件）；
- 重建 document（build_document_from_body 基于 fork 后的 use 重建，杜绝引用旧稿 draft_media_id）；
- 新 revision 依赖按 stale 起步（fact check 不继承，须对新输入重跑）。
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Draft, DraftMedia
from .candidates import draft_input_hash
from .content_harness import staleness
from .document_composition import sync_document


def fork_draft_revision(
    db: Session,
    draft: Draft,
    *,
    title: str | None = None,
    body: str | None = None,
    created_by: str | None = None,
    status: str | None = None,
    reason: str = "draft_forked",
) -> Draft:
    """以 draft 为基产生新 revision：字段继承 + media use 克隆 + document 处理 + 依赖 stale。

    R4-H4 派生数据策略：
    - title-only fork（正文未变）：继承 structured_json / thread_posts_json；
      document 克隆并映射旧 use id（保留手工编排的图片位置，不重排）；
    - body-changing fork：structured_json / thread_posts_json 是旧正文的派生物，
      一律清空待重建（旧 update_draft 语义）；document 按新正文 + media 重建。
    - media use 克隆同时继承撤权字段（public_use_revoked_at/note）——
      「对当前稿件撤权过的图」fork 后不得洗白。
    """
    if draft.status == "approved":
        raise ValueError("已批准的 Draft 不可 fork（修订请基于历史 revision 重新发起）")
    job = draft.content_job
    new_title = title if title is not None else draft.title
    new_body = body if body is not None else draft.body
    body_changed = new_body != draft.body
    new_draft = Draft(
        content_job_id=draft.content_job_id,
        revision_no=max(d.revision_no for d in job.drafts) + 1,
        title=new_title,
        body=new_body,
        # 正文派生数据：body 变更即 stale（清空重建）；title-only 继承
        structured_json=None if body_changed else draft.structured_json,
        thread_posts_json=None if body_changed else draft.thread_posts_json,
        fact_check_json=None,  # 正文输入变化（或待重算）：fact check 不继承
        mother_revision_id=draft.mother_revision_id,
        evidence_checksum=draft.evidence_checksum,
        input_hash=draft_input_hash(new_title, new_body, None if body_changed else draft.thread_posts_json),
        artifact_kind=draft.artifact_kind,
        content_form=draft.content_form,
        candidate_readiness="stale",
        status=status or "draft",
        created_by_type="user",
        created_by=created_by,
    )
    db.add(new_draft)
    db.flush()

    # 克隆 media use（同 MaterialRevision 新 use 行；relationship append 保证同事务可见）
    id_map: dict[int, int] = {}
    for m in sorted(draft.media, key=lambda x: (x.sort_order or 0, x.id)):
        row = DraftMedia(
            draft_id=new_draft.id,
            content_hash=m.content_hash,
            role=m.role,
            sort_order=m.sort_order,
            material_revision_id=m.material_revision_id,
            mime_type=m.mime_type,
            rights_status=m.rights_status,
            public_use_allowed=m.public_use_allowed,
            public_use_revoked_at=m.public_use_revoked_at,  # R4-H4：撤权状态随 use 迁移，不洗白
            public_use_revocation_note=m.public_use_revocation_note,
            alt_text=m.alt_text,
            caption=m.caption,
            placement_json=m.placement_json,
            metadata_json={**(m.metadata_json or {}), "forked_from_draft_media_id": m.id},
        )
        new_draft.media.append(row)
        db.add(row)
        db.flush()
        id_map[m.id] = row.id
    db.flush()

    # document：title-only（正文未变）克隆手工编排并映射 use id；body 变更才按默认规则重建
    if draft.document_json and not body_changed:
        new_draft.document_json = _remap_document(draft.document_json, id_map)
        new_draft.document_schema_version = draft.document_schema_version or 1
    else:
        sync_document(db, new_draft)

    staleness.mark_draft_changed(db, new_draft, reason=reason)
    new_draft.candidate_readiness = "stale"
    db.flush()
    return new_draft


def _remap_document(document: dict, id_map: dict[int, int]) -> dict:
    """克隆 document，image 块的 draft_media_id 映射为 fork 后的新 use id。

    旧 id 无法映射（数据不一致）时丢弃该块引用字段——后续 set_document 归属校验会兜底，
    绝不保留指向旧稿的引用。
    """
    blocks = []
    for block in document.get("blocks", []):
        item = dict(block)
        if item.get("type") == "image":
            old_id = item.get("draft_media_id")
            item["draft_media_id"] = id_map.get(old_id)
            if item["draft_media_id"] is None:
                continue  # 引用不明的块不带入新稿
        blocks.append(item)
    return {"schema_version": document.get("schema_version") or 1, "blocks": blocks}
