"""数据模型，字段对齐 PRD §8 与执行计划各 STU 建表任务。"""

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


# ---------- 枚举（存 String，SQLite 友好） ----------


class SourceType(str, enum.Enum):
    text = "text"
    markdown = "markdown"
    file = "file"
    url = "url"
    api = "api"


class ParseStatus(str, enum.Enum):
    pending = "pending"
    parsing = "parsing"
    done = "done"
    failed = "failed"


class FactStatus(str, enum.Enum):
    candidate = "candidate"
    confirmed = "confirmed"
    rejected = "rejected"
    stale = "stale"
    conflict = "conflict"


class FactPackStatus(str, enum.Enum):
    draft = "draft"
    frozen = "frozen"
    archived = "archived"


class Channel(str, enum.Enum):
    douyin = "douyin"
    xiaohongshu = "xiaohongshu"
    wechat = "wechat"
    x_thread = "x_thread"


class EvidenceKind(str, enum.Enum):
    fact = "fact"
    event = "event"
    third_party_quote = "third_party_quote"
    author_opinion = "author_opinion"
    legacy_untyped = "legacy_untyped"


class CandidateReadiness(str, enum.Enum):
    incomplete = "incomplete"
    ready = "ready"
    stale = "stale"


class DraftMediaRole(str, enum.Enum):
    cover = "cover"
    inline = "inline"
    attachment = "attachment"


class DeliveryAction(str, enum.Enum):
    manual_handoff = "manual_handoff"


class DeliveryTargetStatus(str, enum.Enum):
    approved = "approved"
    target_authorized = "target_authorized"
    package_ready = "package_ready"
    awaiting_manual_receipt = "awaiting_manual_receipt"
    human_confirmed = "human_confirmed"
    failed = "failed"
    reconciliation_needed = "reconciliation_needed"
    blocked = "blocked"
    canceled = "canceled"


class ReceiptVerification(str, enum.Enum):
    human_confirmed = "human_confirmed"
    link_checked = "link_checked"
    screenshot_checked = "screenshot_checked"


class FeedbackKind(str, enum.Enum):
    performance = "performance"
    correction = "correction"
    note = "note"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class DraftStatus(str, enum.Enum):
    draft = "draft"
    fact_check_failed = "fact_check_failed"
    ready_for_review = "ready_for_review"
    changes_requested = "changes_requested"
    approved = "approved"
    exported = "exported"
    archived = "archived"


class ClaimCheckStatus(str, enum.Enum):
    pass_ = "pass"
    warning = "warning"
    blocker = "blocker"
    unverified = "unverified"


# ---------- 用户与 RBAC ----------


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="editor")  # admin/editor/reviewer/viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------- Source ----------


class SourceDocument(Base):
    __tablename__ = "source_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    source_type: Mapped[str] = mapped_column(String(20))
    original_uri: Mapped[str | None] = mapped_column(String(1000))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(String(2000))
    as_of: Mapped[str | None] = mapped_column(String(10))  # YYYY-MM-DD
    trust_level: Mapped[float] = mapped_column(Float, default=0.8)
    parse_status: Mapped[str] = mapped_column(String(20), default=ParseStatus.pending.value)
    parse_error: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(String(64))
    # V1 原文存 DB；长文本/二进制走对象存储是文档化的升级路径（执行计划 STU-021 二选一）
    raw_text: Mapped[str | None] = mapped_column(Text)
    parsed_json: Mapped[dict | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    facts: Mapped[list["Fact"]] = relationship(back_populates="source_document", cascade="all, delete-orphan")


# ---------- Fact ----------


class Fact(Base):
    __tablename__ = "fact"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"))
    statement: Mapped[str] = mapped_column(Text)
    fact_type: Mapped[str] = mapped_column(String(30), default="metric")  # metric/event/quote/...
    subject: Mapped[str | None] = mapped_column(String(300))
    predicate: Mapped[str | None] = mapped_column(String(300))
    value_json: Mapped[dict | None] = mapped_column(JSON)
    unit: Mapped[str | None] = mapped_column(String(30))
    as_of: Mapped[str | None] = mapped_column(String(10))
    valid_from: Mapped[str | None] = mapped_column(String(10))
    valid_to: Mapped[str | None] = mapped_column(String(10))
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    status: Mapped[str] = mapped_column(String(20), default=FactStatus.candidate.value)
    source_locator_json: Mapped[dict | None] = mapped_column(JSON)
    note: Mapped[str | None] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[int | None] = mapped_column(String(255))
    updated_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source_document: Mapped["SourceDocument"] = relationship(back_populates="facts")


# ---------- FactPack ----------


class FactPack(Base):
    __tablename__ = "fact_pack"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_fact_pack_name_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default=FactPackStatus.draft.value)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("fact_pack.id"))
    checksum: Mapped[str | None] = mapped_column(String(64))
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    items: Mapped[list["FactPackItem"]] = relationship(
        back_populates="fact_pack", order_by="FactPackItem.sort_order", cascade="all, delete-orphan"
    )


class FactPackItem(Base):
    __tablename__ = "fact_pack_item"
    __table_args__ = (
        UniqueConstraint("fact_pack_id", "fact_id", name="uq_pack_item"),
        CheckConstraint(
            "evidence_kind IN ('fact', 'event', 'third_party_quote', 'author_opinion', 'legacy_untyped')",
            name="ck_fact_pack_item_evidence_kind",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fact_pack_id: Mapped[int] = mapped_column(ForeignKey("fact_pack.id"))
    fact_id: Mapped[int | None] = mapped_column(ForeignKey("fact.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str | None] = mapped_column(Text)
    evidence_kind: Mapped[str] = mapped_column(String(30), default=EvidenceKind.legacy_untyped.value)
    snapshot_version: Mapped[int | None] = mapped_column(Integer)
    snapshot_json: Mapped[dict | None] = mapped_column(JSON)
    snapshot_checksum: Mapped[str | None] = mapped_column(String(64))
    public_use_allowed: Mapped[bool | None] = mapped_column(Boolean)
    model_use_allowed: Mapped[bool | None] = mapped_column(Boolean)
    public_use_revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    public_use_revocation_note: Mapped[str | None] = mapped_column(Text)

    fact_pack: Mapped["FactPack"] = relationship(back_populates="items")
    fact: Mapped["Fact"] = relationship()


# ---------- Brand Voice / Template / Prompt ----------


class BrandVoiceVersion(Base):
    __tablename__ = "brand_voice_version"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_brand_voice_name_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str | None] = mapped_column(Text)
    tone_rules: Mapped[list | None] = mapped_column(JSON)
    preferred_words: Mapped[list | None] = mapped_column(JSON)
    forbidden_words: Mapped[list | None] = mapped_column(JSON)
    examples: Mapped[list | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/published/archived
    checksum: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChannelTemplateVersion(Base):
    __tablename__ = "channel_template_version"
    __table_args__ = (UniqueConstraint("channel", "version", name="uq_template_channel_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(200))
    structure: Mapped[list | None] = mapped_column(JSON)  # 必备模块
    length_guidance: Mapped[dict | None] = mapped_column(JSON)
    forbidden_patterns: Mapped[list | None] = mapped_column(JSON)
    output_schema: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    checksum: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PromptVersion(Base):
    __tablename__ = "prompt_version"
    __table_args__ = (UniqueConstraint("channel", "version", name="uq_prompt_channel_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(200))
    template_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    checksum: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------- Topic ----------


class TopicBrief(Base):
    __tablename__ = "topic_brief"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    audience: Mapped[str | None] = mapped_column(String(300))
    goal: Mapped[str | None] = mapped_column(Text)
    angle: Mapped[str | None] = mapped_column(Text)
    core_thesis: Mapped[str | None] = mapped_column(Text)
    must_include_json: Mapped[list | None] = mapped_column(JSON)
    forbidden_json: Mapped[list | None] = mapped_column(JSON)
    cta: Mapped[str | None] = mapped_column(Text)
    brand_voice_version_id: Mapped[int | None] = mapped_column(ForeignKey("brand_voice_version.id"))
    fact_pack_id: Mapped[int] = mapped_column(ForeignKey("fact_pack.id"))
    fact_pack_version: Mapped[int] = mapped_column(Integer)
    channels: Mapped[list | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/archived
    tags: Mapped[list | None] = mapped_column(JSON)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    fact_pack: Mapped["FactPack"] = relationship()
    content_jobs: Mapped[list["ContentJob"]] = relationship(back_populates="topic_brief")
    mother_revisions: Mapped[list["MotherRevision"]] = relationship(
        back_populates="topic_brief", order_by="MotherRevision.revision_no", cascade="all, delete-orphan"
    )


# ---------- Generation ----------


class ContentJob(Base):
    __tablename__ = "content_job"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_brief_id: Mapped[int] = mapped_column(ForeignKey("topic_brief.id"))
    channel: Mapped[str] = mapped_column(String(30))
    template_version_id: Mapped[int | None] = mapped_column(ForeignKey("channel_template_version.id"))
    model_provider: Mapped[str | None] = mapped_column(String(50))
    model_name: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[int | None] = mapped_column(String(30))
    fact_pack_snapshot: Mapped[dict | None] = mapped_column(JSON)  # id/version/checksum
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.queued.value)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    topic_brief: Mapped["TopicBrief"] = relationship(back_populates="content_jobs")
    drafts: Mapped[list["Draft"]] = relationship(back_populates="content_job", order_by="Draft.revision_no")


class Draft(Base):
    __tablename__ = "draft"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_job_id: Mapped[int] = mapped_column(ForeignKey("content_job.id"))
    revision_no: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)  # 渲染后的 Markdown 正文
    structured_json: Mapped[dict | None] = mapped_column(JSON)  # 模型结构化输出（含 fact_ids）
    fact_check_json: Mapped[dict | None] = mapped_column(JSON)  # 最近一次 FactCheck 结果
    mother_revision_id: Mapped[int | None] = mapped_column(ForeignKey("mother_revision.id"))
    evidence_checksum: Mapped[str | None] = mapped_column(String(64))
    input_hash: Mapped[str | None] = mapped_column(String(64))
    thread_posts_json: Mapped[list | None] = mapped_column(JSON)
    candidate_readiness: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default=DraftStatus.draft.value)
    created_by_type: Mapped[str] = mapped_column(String(10), default="ai")  # ai/user
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    content_job: Mapped["ContentJob"] = relationship(back_populates="drafts")
    mother_revision: Mapped["MotherRevision | None"] = relationship(back_populates="drafts")
    claims: Mapped[list["DraftClaim"]] = relationship(back_populates="draft", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="draft")
    media: Mapped[list["DraftMedia"]] = relationship(
        back_populates="draft", order_by="DraftMedia.sort_order", cascade="all, delete-orphan"
    )


class MotherRevision(Base):
    __tablename__ = "mother_revision"
    __table_args__ = (UniqueConstraint("topic_brief_id", "revision_no", name="uq_mother_revision_topic_no"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_brief_id: Mapped[int] = mapped_column(ForeignKey("topic_brief.id"))
    revision_no: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str | None] = mapped_column(String(500))
    body_markdown: Mapped[str] = mapped_column(Text)
    parent_revision_id: Mapped[int | None] = mapped_column(ForeignKey("mother_revision.id"))
    evidence_checksum: Mapped[str | None] = mapped_column(String(64))
    body_hash: Mapped[str] = mapped_column(String(64))
    import_metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    topic_brief: Mapped["TopicBrief"] = relationship(back_populates="mother_revisions")
    parent_revision: Mapped["MotherRevision | None"] = relationship(remote_side=[id])
    drafts: Mapped[list["Draft"]] = relationship(back_populates="mother_revision")


class DraftMedia(Base):
    __tablename__ = "draft_media"
    __table_args__ = (
        UniqueConstraint("draft_id", "content_hash", name="uq_draft_media_hash"),
        CheckConstraint("role IN ('cover', 'inline', 'attachment')", name="ck_draft_media_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("draft.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(20), default=DraftMediaRole.inline.value)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    file_path: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    rights_status: Mapped[str | None] = mapped_column(String(30))
    public_use_allowed: Mapped[bool | None] = mapped_column(Boolean)
    public_use_revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    public_use_revocation_note: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped["Draft"] = relationship(back_populates="media")


class DraftClaim(Base):
    __tablename__ = "draft_claim"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("draft.id"))
    text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String(20), default="fact")  # fact/opinion/quote/transition
    start_offset: Mapped[int | None] = mapped_column(Integer)
    end_offset: Mapped[int | None] = mapped_column(Integer)
    check_status: Mapped[str] = mapped_column(String(20), default=ClaimCheckStatus.unverified.value)
    fact_ids_json: Mapped[list | None] = mapped_column(JSON)

    draft: Mapped["Draft"] = relationship(back_populates="claims")


# ---------- Review ----------


class Review(Base):
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("draft.id"))
    revision_no: Mapped[int] = mapped_column(Integer)  # 打开审核时的 revision，approve 时校验未被编辑
    reviewer_id: Mapped[int | None] = mapped_column(String(255))
    decision: Mapped[str] = mapped_column(String(30))  # changes_requested/approved
    comment: Mapped[str | None] = mapped_column(Text)
    candidate_hash: Mapped[str | None] = mapped_column(String(64))
    candidate_readiness: Mapped[str | None] = mapped_column(String(20))
    warning_dispositions_json: Mapped[dict | None] = mapped_column(JSON)
    checked_input_hash: Mapped[str | None] = mapped_column(String(64))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped["Draft"] = relationship(back_populates="reviews")


# ---------- Asset / Export ----------


class ContentAsset(Base):
    __tablename__ = "content_asset"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("draft.id"))
    topic_brief_id: Mapped[int] = mapped_column(ForeignKey("topic_brief.id"))
    channel: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(500))
    final_body: Mapped[str] = mapped_column(Text)
    structured_json: Mapped[dict | None] = mapped_column(JSON)
    fact_pack_id: Mapped[int] = mapped_column(Integer)
    fact_pack_version: Mapped[int] = mapped_column(Integer)
    fact_pack_checksum: Mapped[str | None] = mapped_column(String(64))
    brand_voice_version_id: Mapped[int | None] = mapped_column(Integer)
    template_version_id: Mapped[int | None] = mapped_column(Integer)
    model_provider: Mapped[str | None] = mapped_column(String(50))
    model_name: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(30))
    reviewer: Mapped[str | None] = mapped_column(String(255))
    approved_revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="approved")
    approved_candidate_hash: Mapped[str | None] = mapped_column(String(64))
    candidate_manifest_json: Mapped[dict | None] = mapped_column(JSON)
    mother_revision_id: Mapped[int | None] = mapped_column(ForeignKey("mother_revision.id"))
    tags: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DeliveryTarget(Base):
    __tablename__ = "delivery_target"
    __table_args__ = (
        UniqueConstraint(
            "content_asset_id", "approved_candidate_hash", "channel", "content_form", "account_ref", "action", "authorization_version",
            name="uq_delivery_target_authorization",
        ),
        CheckConstraint("channel IN ('wechat', 'x_thread')", name="ck_delivery_target_channel"),
        CheckConstraint("action = 'manual_handoff'", name="ck_delivery_target_action"),
        CheckConstraint(
            "status IN ('approved', 'target_authorized', 'package_ready', 'awaiting_manual_receipt', 'human_confirmed', 'failed', 'reconciliation_needed', 'blocked', 'canceled')",
            name="ck_delivery_target_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    content_asset_id: Mapped[int] = mapped_column(ForeignKey("content_asset.id"))
    channel: Mapped[str] = mapped_column(String(30))
    content_form: Mapped[str] = mapped_column(String(30))
    account_ref: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(30), default=DeliveryAction.manual_handoff.value)
    authorization_version: Mapped[str] = mapped_column(String(64))
    approved_candidate_hash: Mapped[str] = mapped_column(String(64))
    authorized_by: Mapped[str | None] = mapped_column(String(255))
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default=DeliveryTargetStatus.target_authorized.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    receipts: Mapped[list["DeliveryReceipt"]] = relationship(
        back_populates="target", order_by="DeliveryReceipt.created_at", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["DeliveryFeedback"]] = relationship(
        back_populates="target", order_by="DeliveryFeedback.created_at", cascade="all, delete-orphan"
    )


class DeliveryReceipt(Base):
    __tablename__ = "delivery_receipt"
    __table_args__ = (UniqueConstraint("target_id", "idempotency_key", name="uq_delivery_receipt_idempotency"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("delivery_target.id"))
    approved_candidate_hash: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(30), default=DeliveryAction.manual_handoff.value)
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30))
    operator: Mapped[str | None] = mapped_column(String(255))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_ref: Mapped[str | None] = mapped_column(String(1000))
    verification_method: Mapped[str | None] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    target: Mapped["DeliveryTarget"] = relationship(back_populates="receipts")


class DeliveryFeedback(Base):
    __tablename__ = "delivery_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("delivery_target.id"))
    kind: Mapped[str] = mapped_column(String(30), default=FeedbackKind.note.value)
    body: Mapped[str] = mapped_column(Text)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    target: Mapped["DeliveryTarget"] = relationship(back_populates="feedback")


class AssetMedia(Base):
    """资产配图素材：底层统一素材池（本表全量），前端按 asset 归属随文展示。

    kind: cover（封面）/ inline（文章内配图位）；
    source: generated（占位位，prompt=配图说明，来自 structured_json 的 image_prompts/
    image_suggestions）/ upload（用户上传的实体图片，落本地 media 目录）。
    PRD §6.7：V1 素材=说明/Prompt，不依赖具体生图平台。
    """

    __tablename__ = "asset_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("content_asset.id"))
    kind: Mapped[str] = mapped_column(String(10), default="inline")  # cover / inline
    source: Mapped[str] = mapped_column(String(10), default="generated")  # generated / upload
    prompt: Mapped[str | None] = mapped_column(Text)  # 配图说明（生图 Prompt / 建议）
    file_path: Mapped[str | None] = mapped_column(String(300))  # 上传文件相对 media 根的路径
    mime_type: Mapped[str | None] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ExternalContent(Base):
    """外部 agent（dsh/Antigravity skills）产出内容的入库载体。

    与 ContentAsset（内部生成链路产物，强绑定 draft/topic）分离，
    只走简化状态机：draft → published / archived。
    (origin, origin_ref) 唯一，保证同一外部产物重复上报幂等。
    """

    __tablename__ = "external_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(30))
    origin: Mapped[str] = mapped_column(String(50), default="dsh")  # dsh / antigravity / manual
    origin_ref: Mapped[str | None] = mapped_column(String(500))  # 外部唯一引用（run id / url / 文件路径）
    status: Mapped[str] = mapped_column(String(20), default="draft")
    tags: Mapped[list | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ExportRecord(Base):
    __tablename__ = "export_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("content_asset.id"))
    fmt: Mapped[str] = mapped_column(String(10))  # md/txt/json/srt
    exported_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------- LLM Run 与审计 ----------


class LLMRun(Base):
    __tablename__ = "llm_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(30))
    purpose: Mapped[str] = mapped_column(String(50))  # generate/fact_review/rewrite
    input_hash: Mapped[str | None] = mapped_column(String(64))
    raw_output: Mapped[str | None] = mapped_column(Text)
    parsed_output_json: Mapped[dict | None] = mapped_column(JSON)
    usage_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------- External Connector（EPIC-18：量化平台等外部 API 拉数据）----------


class Connector(Base):
    __tablename__ = "connector"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    connector_type: Mapped[str] = mapped_column(String(30), default="generic_rest")
    base_url: Mapped[str] = mapped_column(String(500))
    # 鉴权凭据只存环境变量名，值不进 DB（PRD：Secret 只走环境变量）
    api_key_env: Mapped[str | None] = mapped_column(String(100))
    auth_style: Mapped[str] = mapped_column(String(20), default="bearer")  # bearer / header / none
    auth_header_name: Mapped[str | None] = mapped_column(String(100))  # auth_style=header 时的 header 名
    default_headers_json: Mapped[dict | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    endpoints: Mapped[list["ConnectorEndpoint"]] = relationship(
        back_populates="connector", cascade="all, delete-orphan"
    )


class ConnectorEndpoint(Base):
    __tablename__ = "connector_endpoint"

    id: Mapped[int] = mapped_column(primary_key=True)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connector.id"))
    name: Mapped[str] = mapped_column(String(200))
    path: Mapped[str] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(10), default="GET")  # GET / POST
    body_template_json: Mapped[dict | None] = mapped_column(JSON)  # POST body，值支持 {today} 占位符
    params_json: Mapped[dict | None] = mapped_column(JSON)  # 查询参数，值支持 {today} 占位符
    title_template: Mapped[str] = mapped_column(String(300))  # Source 标题模板
    as_of_path: Mapped[str | None] = mapped_column(String(200))  # 从响应 JSON 取 as_of 的路径
    trust_level: Mapped[float] = mapped_column(Float, default=0.9)  # 量化平台结构化数据默认高可信
    # JSON → Fact 映射协议：items_path 定位数组，fields 指定字段来源，statement 为模板
    fact_mapping_json: Mapped[dict | None] = mapped_column(JSON)
    # 分页配置：{type: page, page_param, page_start, max_pages} 或 {type: cursor, cursor_param, cursor_path, max_pages}
    pagination_json: Mapped[dict | None] = mapped_column(JSON)
    # 定时拉取间隔（分钟）；null/0 = 不定时，仅手动触发
    interval_minutes: Mapped[int | None] = mapped_column(Integer)
    last_pull_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_pull_status: Mapped[str | None] = mapped_column(String(20))  # ok / failed
    last_pull_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    connector: Mapped["Connector"] = relationship(back_populates="endpoints")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    event: Mapped[str] = mapped_column(String(100))
    actor: Mapped[str | None] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(50))
    detail_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SystemSetting(Base):
    """运行时配置覆盖（前端设置页写入），值优先于环境变量。

    Secret（如 LLM API Key）允许存本表以支持前端配置，但所有 API 读取一律脱敏回显；
    「恢复默认」删除覆盖行后回落环境变量。生产建议仍走环境变量/secret manager。
    """

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)  # 如 llm
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    updated_by: Mapped[str | None] = mapped_column(String(255))


class Workflow(Base):
    """工作流画布定义（仿扣子）：节点=已有能力的编排壳，结果沉淀回既有实体。"""

    __tablename__ = "workflow"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    template_key: Mapped[str | None] = mapped_column(String(50))  # daily_suggest / gen_export / null=自定义
    definition_json: Mapped[dict] = mapped_column(JSON)  # {nodes:[{id,type,label,params,layout}], edges:[{from,to}]}
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkflowRun(Base):
    """一次画布执行。status: running / waiting_input / succeeded / failed / canceled。"""

    __tablename__ = "workflow_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow.id"))
    status: Mapped[str] = mapped_column(String(20), default="running")
    context_json: Mapped[dict] = mapped_column(JSON, default=dict)  # 节点间数据总线（实体 ID 等）
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)  # 启动参数（topic_id 等）
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkflowStep(Base):
    """画布上单个节点的一次执行记录（input=params，output=产物摘要 + 实体 ID）。"""

    __tablename__ = "workflow_step"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("workflow_run.id"))
    node_id: Mapped[str] = mapped_column(String(50))
    node_type: Mapped[str] = mapped_column(String(30))
    label: Mapped[str | None] = mapped_column(String(200))
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/running/waiting_input/succeeded/failed/skipped
    output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
