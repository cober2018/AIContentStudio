"""数据模型，字段对齐 PRD §8 与执行计划各 STU 建表任务。"""

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
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
    """兼容保留：V1 PRD 2.0 起新渠道一律经 ChannelRegistry 注册（profile），禁止在此新增 enum item。"""

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


class ArtifactKind(str, enum.Enum):
    """持久化内容产物形态；未实现的形态仍由服务层能力闸门控制。"""

    text = "text"
    image = "image"
    script = "script"
    video = "video"


class CheckKind(str, enum.Enum):
    fact = "fact"
    platform = "platform"
    safety = "safety"
    rights = "rights"
    seo = "seo"
    domain = "domain"
    media = "media"


class CheckStatus(str, enum.Enum):
    pass_ = "pass"
    warning = "warning"
    blocker = "blocker"
    incomplete = "incomplete"
    stale = "stale"


class DeliveryAction(str, enum.Enum):
    manual_handoff = "manual_handoff"  # legacy alias（M1 人工交付）
    copy_package = "copy_package"
    assisted_draft = "assisted_draft"
    auto_draft = "auto_draft"


class MaterialKind(str, enum.Enum):
    image = "image"
    chart = "chart"
    screenshot = "screenshot"
    video = "video"
    audio = "audio"
    brand = "brand"
    other = "other"


class MaterialRevisionStatus(str, enum.Enum):
    candidate = "candidate"
    usable = "usable"
    revoked = "revoked"
    archived = "archived"


class MaterialSourceKind(str, enum.Enum):
    upload = "upload"
    web_search = "web_search"
    ai_generated = "ai_generated"
    chart = "chart"
    screenshot = "screenshot"
    upstream = "upstream"
    legacy = "legacy"


class DiscoverabilityStage(str, enum.Enum):
    pre = "pre"
    post = "post"


class DiscoverabilityStatus(str, enum.Enum):
    ready = "ready"
    incomplete = "incomplete"
    stale = "stale"
    failed = "failed"


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


class KnowledgeCollection(Base):
    __tablename__ = "knowledge_collection"
    __table_args__ = (
        CheckConstraint("status IN ('active','archived')", name="ck_knowledge_collection_status"),
        CheckConstraint("revision > 0", name="ck_knowledge_collection_revision"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class KnowledgeCollectionItem(Base):
    __tablename__ = "knowledge_collection_item"
    __table_args__ = (
        CheckConstraint(
            "(item_type = 'source_document' AND source_document_id IS NOT NULL AND fact_pack_id IS NULL) OR "
            "(item_type = 'fact_pack' AND fact_pack_id IS NOT NULL AND source_document_id IS NULL)",
            name="ck_knowledge_item_resource",
        ),
        CheckConstraint("status IN ('active','detached')", name="ck_knowledge_item_status"),
        CheckConstraint("sort_order >= 0", name="ck_knowledge_item_sort_order"),
        UniqueConstraint("collection_id", "source_document_id", name="uq_knowledge_item_source"),
        UniqueConstraint("collection_id", "fact_pack_id", name="uq_knowledge_item_pack"),
        Index("ix_knowledge_item_collection_status_order", "collection_id", "status", "sort_order", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_id: Mapped[int] = mapped_column(ForeignKey("knowledge_collection.id"))
    item_type: Mapped[str] = mapped_column(String(30))
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("source_document.id"))
    fact_pack_id: Mapped[int | None] = mapped_column(ForeignKey("fact_pack.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    added_by: Mapped[str | None] = mapped_column(String(255))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    detached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


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
    # V1 PRD 2.0：本表提升为 Channel Profile Version 载体（content_forms → workflow/renderer/rules/seo/publishers）
    profile_schema_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    profile_json: Mapped[dict | None] = mapped_column(JSON)
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
    channels: Mapped[list | None] = mapped_column(JSON)  # 兼容字段：targets_json 去重后的 channel 列表
    # V1 PRD 2.0：交付目标真源 [{channel, content_form}]
    targets_json: Mapped[list | None] = mapped_column(JSON)
    product_ref: Mapped[str | None] = mapped_column(String(100))
    business_line: Mapped[str | None] = mapped_column(String(100))
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
    content_form: Mapped[str | None] = mapped_column(String(50))
    artifact_kind: Mapped[str | None] = mapped_column(String(20))
    workflow_run_id: Mapped[int | None] = mapped_column(Integer)
    channel_profile_version_id: Mapped[int | None] = mapped_column(Integer)
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
    # V1 PRD 2.0：平台 Artifact 形态与图文 composition（Markdown 仍是文本真源）
    artifact_kind: Mapped[str] = mapped_column(String(20), default=ArtifactKind.text.value, server_default="text")
    content_form: Mapped[str | None] = mapped_column(String(50))
    document_schema_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    document_json: Mapped[dict | None] = mapped_column(JSON)
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
    check_runs: Mapped[list["DraftCheckRun"]] = relationship(
        back_populates="draft", order_by="DraftCheckRun.created_at", cascade="all, delete-orphan"
    )


class DraftCheckRun(Base):
    """通用检查记录（V1 PRD 2.0 D12）：统一 fact/platform/safety/rights/seo/domain/media 检查语义。

    兼容期：`Draft.fact_check_json` 继续写，同时镜像一条 check_kind='fact' 的记录；
    新 Review Gate 只读本表。incomplete 不等于 pass，input_hash 变化后标 stale。
    """

    __tablename__ = "draft_check_run"
    __table_args__ = (
        Index("ix_draft_check_run_draft_kind_time", "draft_id", "check_kind", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("draft.id"))
    check_kind: Mapped[str] = mapped_column(String(30))
    profile_key: Mapped[str | None] = mapped_column(String(150))
    profile_version: Mapped[str | None] = mapped_column(String(50))
    input_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20))  # pass/warning/blocker/incomplete/stale
    report_json: Mapped[dict | None] = mapped_column(JSON)
    provider_key: Mapped[str | None] = mapped_column(String(100))
    provider_version: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped["Draft"] = relationship(back_populates="check_runs")


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
    # V1 PRD 2.0（D9）：DraftMedia 降为 Use/Placement；旧行 material_revision_id 为空仍可读
    material_revision_id: Mapped[int | None] = mapped_column(ForeignKey("material_revision.id"))
    placement_json: Mapped[dict | None] = mapped_column(JSON)
    alt_text: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped["Draft"] = relationship(back_populates="media")
    material_revision: Mapped["MaterialRevision | None"] = relationship(back_populates="draft_uses")


# ---------- Material Library（D9）----------


class Material(Base):
    """全局素材：跨稿件复用的逻辑实体，字节不可变体现在 MaterialRevision。"""

    __tablename__ = "material"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), default=MaterialKind.image.value)
    title: Mapped[str] = mapped_column(String(500))
    tags_json: Mapped[list | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/archived
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    revisions: Mapped[list["MaterialRevision"]] = relationship(
        back_populates="material", order_by="MaterialRevision.revision_no", cascade="all, delete-orphan"
    )


class MaterialRevision(Base):
    """素材版本：content_hash 寻址的字节快照 + 来源/权利元数据。

    被 approved Candidate 引用后不可变（替换=新 Revision）；web_search 来源在
    public_use_allowed != true 前不满足 Candidate media readiness。
    """

    __tablename__ = "material_revision"
    __table_args__ = (
        UniqueConstraint("material_id", "revision_no", name="uq_material_revision_no"),
        Index("ix_material_revision_content_hash", "content_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("material.id"))
    revision_no: Mapped[int] = mapped_column(Integer, default=1)
    parent_revision_id: Mapped[int | None] = mapped_column(ForeignKey("material_revision.id"))
    status: Mapped[str] = mapped_column(String(20), default=MaterialRevisionStatus.candidate.value)
    source_kind: Mapped[str] = mapped_column(String(30), default=MaterialSourceKind.upload.value)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    source_metadata_json: Mapped[dict | None] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    file_path: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    rights_status: Mapped[str | None] = mapped_column(String(30))
    public_use_allowed: Mapped[bool | None] = mapped_column(Boolean)
    model_use_allowed: Mapped[bool | None] = mapped_column(Boolean)
    commercial_use_allowed: Mapped[bool | None] = mapped_column(Boolean)
    attribution_text: Mapped[str | None] = mapped_column(Text)
    provider_key: Mapped[str | None] = mapped_column(String(100))
    provider_version: Mapped[str | None] = mapped_column(String(50))
    prompt_text: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    material: Mapped["Material"] = relationship(back_populates="revisions")
    draft_uses: Mapped[list["DraftMedia"]] = relationship(back_populates="material_revision")


# ---------- Discoverability（D14）----------


class DiscoverabilityProfileVersion(Base):
    """SEO Profile 版本：config_json 定义该渠道×形态的 discoverability 检查项。"""

    __tablename__ = "discoverability_profile_version"
    __table_args__ = (UniqueConstraint("profile_key", "version", name="uq_discoverability_profile_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_key: Mapped[str] = mapped_column(String(150))
    version: Mapped[int] = mapped_column(Integer, default=1)
    channel: Mapped[str] = mapped_column(String(30))
    content_form: Mapped[str | None] = mapped_column(String(50))
    config_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    checksum: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DiscoverabilityReport(Base):
    """Pre/Post SEO 报告：不自动改稿；apply 建议走 Draft 新 revision。"""

    __tablename__ = "discoverability_report"
    __table_args__ = (
        Index("ix_discoverability_report_stage", "stage", "channel", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int | None] = mapped_column(Integer)
    mother_revision_id: Mapped[int | None] = mapped_column(Integer)
    draft_id: Mapped[int | None] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(String(10))  # pre / post
    channel: Mapped[str] = mapped_column(String(30))
    content_form: Mapped[str | None] = mapped_column(String(50))
    profile_version_id: Mapped[int | None] = mapped_column(Integer)
    input_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default=DiscoverabilityStatus.incomplete.value)
    report_json: Mapped[dict | None] = mapped_column(JSON)
    model_provider: Mapped[str | None] = mapped_column(String(50))
    model_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


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
    draft_id: Mapped[int | None] = mapped_column(ForeignKey("draft.id"))
    revision_no: Mapped[int | None] = mapped_column(Integer)  # 打开审核时的 revision，approve 时校验未被编辑
    content_asset_id: Mapped[int | None] = mapped_column(ForeignKey("content_asset.id"), index=True)
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
    __table_args__ = (UniqueConstraint("project_id", "content_unit_id", "candidate_hash", name="uq_project_candidate_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int | None] = mapped_column(ForeignKey("draft.id"))
    topic_brief_id: Mapped[int | None] = mapped_column(ForeignKey("topic_brief.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("content_project.id"), index=True)
    content_unit_id: Mapped[int | None] = mapped_column(ForeignKey("content_unit.id"), index=True)
    identity_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("identity_snapshot.id"), index=True)
    workflow_run_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_run.id"), index=True)
    candidate_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    channel: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(500))
    final_body: Mapped[str | None] = mapped_column(Text)
    structured_json: Mapped[dict | None] = mapped_column(JSON)
    fact_pack_id: Mapped[int | None] = mapped_column(Integer)
    fact_pack_version: Mapped[int | None] = mapped_column(Integer)
    fact_pack_checksum: Mapped[str | None] = mapped_column(String(64))
    brand_voice_version_id: Mapped[int | None] = mapped_column(Integer)
    template_version_id: Mapped[int | None] = mapped_column(Integer)
    model_provider: Mapped[str | None] = mapped_column(String(50))
    model_name: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(30))
    reviewer: Mapped[str | None] = mapped_column(String(255))
    approved_revision: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="approved")
    approved_candidate_hash: Mapped[str | None] = mapped_column(String(64))
    candidate_manifest_json: Mapped[dict | None] = mapped_column(JSON)
    mother_revision_id: Mapped[int | None] = mapped_column(ForeignKey("mother_revision.id"))
    # V1 PRD 2.0（§6.23）：查询性能列（真源在 candidate_manifest_json）
    artifact_kind: Mapped[str | None] = mapped_column(String(20))
    content_form: Mapped[str | None] = mapped_column(String(50))
    workflow_key: Mapped[str | None] = mapped_column(String(120))
    workflow_version: Mapped[int | None] = mapped_column(Integer)
    tags: Mapped[list | None] = mapped_column(JSON)
    content_master_revision_id: Mapped[int | None] = mapped_column(ForeignKey("content_master_revision.id"), index=True)
    channel_variant_revision_id: Mapped[int | None] = mapped_column(ForeignKey("channel_variant_revision.id", ondelete="RESTRICT"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentMasterRevision(Base):
    """Immutable, unit-scoped production content revision."""

    __tablename__ = "content_master_revision"
    __table_args__ = (
        UniqueConstraint("content_unit_id", "revision_no", name="uq_master_unit_revision"),
        UniqueConstraint("content_unit_id", "idempotency_key", name="uq_master_unit_idempotency"),
        Index("ix_master_project_unit_created", "project_id", "content_unit_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id"), index=True)
    content_unit_id: Mapped[int] = mapped_column(ForeignKey("content_unit.id"), index=True)
    revision_no: Mapped[int] = mapped_column(Integer)
    parent_revision_id: Mapped[int | None] = mapped_column(ForeignKey("content_master_revision.id"))
    modality: Mapped[str] = mapped_column(String(20))
    channel_id: Mapped[str | None] = mapped_column(String(100))
    content_form: Mapped[str | None] = mapped_column(String(100))
    payload_schema: Mapped[str] = mapped_column(String(100))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    payload_hash: Mapped[str] = mapped_column(String(64), index=True)
    context_hash: Mapped[str] = mapped_column(String(64), index=True)
    identity_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("identity_snapshot.id"))
    creative_brief_revision_id: Mapped[int | None] = mapped_column(ForeignKey("creative_brief_revision.id"))
    fact_boundary_revision_id: Mapped[int | None] = mapped_column(ForeignKey("project_fact_boundary_revision.id"))
    origin_workflow_run_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_run.id"))
    origin_project_output_id: Mapped[int | None] = mapped_column(ForeignKey("project_workflow_output.id"))
    source_kind: Mapped[str] = mapped_column(String(30))
    edit_summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(150))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentMasterAssetRef(Base):
    __tablename__ = "content_master_asset_ref"
    __table_args__ = (Index("ix_master_asset_ref_master_order", "master_revision_id", "sort_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    master_revision_id: Mapped[int] = mapped_column(ForeignKey("content_master_revision.id"), index=True)
    material_revision_id: Mapped[int] = mapped_column(ForeignKey("material_revision.id"))
    role: Mapped[str] = mapped_column(String(40))
    slot_key: Mapped[str | None] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    placement_json: Mapped[dict] = mapped_column(JSON, default=dict)
    rights_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash_snapshot: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentMasterEvidenceRef(Base):
    __tablename__ = "content_master_evidence_ref"
    __table_args__ = (Index("ix_master_evidence_ref_master_order", "master_revision_id", "sort_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    master_revision_id: Mapped[int] = mapped_column(ForeignKey("content_master_revision.id"), index=True)
    fact_pack_item_id: Mapped[int] = mapped_column(ForeignKey("fact_pack_item.id"))
    role: Mapped[str] = mapped_column(String(40))
    content_locator_json: Mapped[dict] = mapped_column(JSON, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    snapshot_checksum: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentMasterCheckRun(Base):
    __tablename__ = "content_master_check_run"
    __table_args__ = (Index("ix_master_check_master_kind_created", "master_revision_id", "check_kind", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    master_revision_id: Mapped[int] = mapped_column(ForeignKey("content_master_revision.id"), index=True)
    check_kind: Mapped[str] = mapped_column(String(40))
    profile_key: Mapped[str | None] = mapped_column(String(100))
    profile_version: Mapped[str | None] = mapped_column(String(50))
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20))
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provider_key: Mapped[str | None] = mapped_column(String(100))
    provider_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChannelVariantRevision(Base):
    __tablename__ = "channel_variant_revision"
    __table_args__ = (
        UniqueConstraint("content_unit_id", "variant_key", "revision_no", name="uq_variant_series_revision"),
        UniqueConstraint("content_unit_id", "variant_key", "idempotency_key", name="uq_variant_series_idempotency"),
        CheckConstraint("revision_no > 0", name="ck_variant_revision_positive"),
        CheckConstraint("length(variant_key) BETWEEN 1 AND 120", name="ck_variant_key_length"),
        CheckConstraint("artifact_kind IN ('text', 'image', 'script')", name="ck_variant_artifact_kind"),
        CheckConstraint("source_kind IN ('manual_edit', 'deterministic_adapt', 'model_assisted')", name="ck_variant_source_kind"),
        CheckConstraint("length(payload_hash) = 64 AND length(context_hash) = 64", name="ck_variant_hash_lengths"),
        Index("ix_variant_project_unit_target", "project_id", "content_unit_id", "channel_id", "content_form"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id", ondelete="RESTRICT"), index=True)
    content_unit_id: Mapped[int] = mapped_column(ForeignKey("content_unit.id", ondelete="RESTRICT"), index=True)
    variant_key: Mapped[str] = mapped_column(String(120))
    revision_no: Mapped[int] = mapped_column(Integer)
    parent_revision_id: Mapped[int | None] = mapped_column(ForeignKey("channel_variant_revision.id", ondelete="RESTRICT"))
    source_master_revision_id: Mapped[int] = mapped_column(ForeignKey("content_master_revision.id", ondelete="RESTRICT"), index=True)
    source_master_payload_hash: Mapped[str] = mapped_column(String(64))
    source_master_context_hash: Mapped[str] = mapped_column(String(64))
    source_channel_id: Mapped[str | None] = mapped_column(String(100))
    source_content_form: Mapped[str | None] = mapped_column(String(100))
    identity_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("identity_snapshot.id", ondelete="RESTRICT"))
    channel_id: Mapped[str] = mapped_column(String(100))
    content_form: Mapped[str] = mapped_column(String(100))
    artifact_kind: Mapped[str] = mapped_column(String(20))
    profile_template_version_id: Mapped[int] = mapped_column(ForeignKey("channel_template_version.id", ondelete="RESTRICT"))
    profile_key: Mapped[str] = mapped_column(String(150))
    profile_version: Mapped[str] = mapped_column(String(50))
    profile_hash: Mapped[str] = mapped_column(String(64))
    adapter_key: Mapped[str] = mapped_column(String(150))
    adapter_version: Mapped[str] = mapped_column(String(50))
    rule_hash: Mapped[str] = mapped_column(String(64))
    payload_schema: Mapped[str] = mapped_column(String(100))
    payload_json: Mapped[dict] = mapped_column(JSON)
    payload_hash: Mapped[str] = mapped_column(String(64), index=True)
    context_hash: Mapped[str] = mapped_column(String(64), index=True)
    source_kind: Mapped[str] = mapped_column(String(40))
    edit_summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    llm_provenance_json: Mapped[dict | None] = mapped_column(JSON)
    idempotency_key: Mapped[str] = mapped_column(String(150))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChannelVariantAssetRef(Base):
    __tablename__ = "channel_variant_asset_ref"
    __table_args__ = (Index("ix_variant_asset_ref_order", "variant_revision_id", "sort_order"),
                      CheckConstraint("sort_order >= 0", name="ck_variant_asset_order_nonnegative"))

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_revision_id: Mapped[int] = mapped_column(ForeignKey("channel_variant_revision.id", ondelete="RESTRICT"), index=True)
    material_revision_id: Mapped[int] = mapped_column(ForeignKey("material_revision.id", ondelete="RESTRICT"))
    role: Mapped[str] = mapped_column(String(40))
    slot_key: Mapped[str | None] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    placement_json: Mapped[dict] = mapped_column(JSON, default=dict)
    rights_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash_snapshot: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChannelVariantEvidenceRef(Base):
    __tablename__ = "channel_variant_evidence_ref"
    __table_args__ = (Index("ix_variant_evidence_ref_order", "variant_revision_id", "sort_order"),
                      CheckConstraint("sort_order >= 0", name="ck_variant_evidence_order_nonnegative"))

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_revision_id: Mapped[int] = mapped_column(ForeignKey("channel_variant_revision.id", ondelete="RESTRICT"), index=True)
    fact_pack_item_id: Mapped[int] = mapped_column(ForeignKey("fact_pack_item.id", ondelete="RESTRICT"))
    role: Mapped[str] = mapped_column(String(40))
    content_locator_json: Mapped[dict] = mapped_column(JSON, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    snapshot_checksum: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChannelVariantCheckRun(Base):
    __tablename__ = "channel_variant_check_run"
    __table_args__ = (Index("ix_variant_check_kind_created", "variant_revision_id", "check_kind", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_revision_id: Mapped[int] = mapped_column(ForeignKey("channel_variant_revision.id", ondelete="RESTRICT"), index=True)
    check_kind: Mapped[str] = mapped_column(String(40))
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    profile_hash: Mapped[str] = mapped_column(String(64))
    adapter_hash: Mapped[str] = mapped_column(String(64))
    rule_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20))
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DeliveryTarget(Base):
    """交付目标（D20/D21）：action 四值；渠道/形态合法性由 ChannelRegistry+PublisherRegistry 服务层验证。

    DB 约束不再锁渠道枚举（新增渠道不得要求改 migration）。
    """

    __tablename__ = "delivery_target"
    __table_args__ = (
        UniqueConstraint(
            "content_asset_id", "approved_candidate_hash", "channel", "content_form", "authorization_account_key", "action", "authorization_version",
            name="uq_delivery_target_authorization",
        ),
        CheckConstraint(
            "action IN ('manual_handoff', 'copy_package', 'assisted_draft', 'auto_draft')",
            name="ck_delivery_target_action",
        ),
        CheckConstraint(
            "status IN ('approved', 'target_authorized', 'package_ready', 'awaiting_manual_receipt', 'human_confirmed', 'failed', 'reconciliation_needed', 'blocked', 'canceled')",
            name="ck_delivery_target_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    content_asset_id: Mapped[int] = mapped_column(ForeignKey("content_asset.id"))
    content_account_id: Mapped[int | None] = mapped_column(ForeignKey("content_account.id"), index=True)
    channel: Mapped[str] = mapped_column(String(30))
    content_form: Mapped[str] = mapped_column(String(30))
    account_ref: Mapped[str] = mapped_column(String(255))
    authorization_account_key: Mapped[str] = mapped_column(
        String(300),
        default=lambda context: (
            f"content-account:{context.get_current_parameters()['content_account_id']}"
            if context.get_current_parameters().get("content_account_id") is not None
            else f"legacy-ref:{context.get_current_parameters()['account_ref']}"
        ),
    )
    action: Mapped[str] = mapped_column(String(30), default=DeliveryAction.manual_handoff.value)
    authorization_version: Mapped[str] = mapped_column(String(64))
    approved_candidate_hash: Mapped[str] = mapped_column(String(64))
    authorized_by: Mapped[str | None] = mapped_column(String(255))
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default=DeliveryTargetStatus.target_authorized.value)
    # V1 PRD 2.0（D22/D23）：执行 publisher 与能力快照
    publisher_key: Mapped[str | None] = mapped_column(String(150))
    publisher_version: Mapped[str | None] = mapped_column(String(50))
    capability_snapshot_json: Mapped[dict | None] = mapped_column(JSON)
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    receipts: Mapped[list["DeliveryReceipt"]] = relationship(
        back_populates="target", order_by="DeliveryReceipt.created_at", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["DeliveryFeedback"]] = relationship(
        back_populates="target", order_by="DeliveryFeedback.created_at", cascade="all, delete-orphan"
    )
    attempts: Mapped[list["DeliveryAttempt"]] = relationship(
        back_populates="target", order_by="DeliveryAttempt.attempt_no", cascade="all, delete-orphan"
    )


class DeliveryAttempt(Base):
    """一次远端交付尝试（D22）：prepared 必须先 COMMIT 再调远端；超时=unknown，不自动重发。"""

    __tablename__ = "delivery_attempt"
    __table_args__ = (
        UniqueConstraint("target_id", "attempt_no", name="uq_delivery_attempt_no"),
        UniqueConstraint("idempotency_key", name="uq_delivery_attempt_idempotency"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("delivery_target.id"))
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)
    idempotency_key: Mapped[str] = mapped_column(String(64))
    publisher_key: Mapped[str | None] = mapped_column(String(150))
    publisher_version: Mapped[str | None] = mapped_column(String(50))
    request_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="prepared")  # prepared/running/succeeded/failed/unknown
    remote_id: Mapped[str | None] = mapped_column(String(200))
    response_metadata_json: Mapped[dict | None] = mapped_column(JSON)  # 只存安全 metadata（禁止 token/cookie）
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    target: Mapped["DeliveryTarget"] = relationship(back_populates="attempts")


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


class CapabilityRegistration(Base):
    __tablename__ = "capability_registration"
    __table_args__ = (
        UniqueConstraint("kind", "key", "version", name="uq_capability_registration_identity"),
        CheckConstraint("kind IN ('node','rule','renderer','publisher','asset_provider','material_search','skill_runtime',"
                        "'model_provider','tool_provider','data_connector','search_provider','image_provider',"
                        "'video_provider','tts_provider','asr_provider','channel_adapter','browser_automation')",
                        name="ck_capability_registration_kind"),
        CheckConstraint("length(kind) > 0 AND length(key) > 0 AND length(version) > 0", name="ck_capability_registration_identity_nonempty"),
        CheckConstraint("status IN ('configured', 'disabled')", name="ck_capability_registration_status"),
        CheckConstraint("length(config_fingerprint) = 64", name="ck_capability_registration_fingerprint"),
        CheckConstraint(
            "(kind = 'data_connector' AND data_source_plugin_key IS NOT NULL AND endpoint_id IS NOT NULL) "
            "OR (kind != 'data_connector' AND data_source_plugin_key IS NULL AND endpoint_id IS NULL)",
            name="ck_capability_registration_data_mapping",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(150), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="configured")
    config_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    data_source_plugin_key: Mapped[str | None] = mapped_column(String(100))
    endpoint_id: Mapped[int | None] = mapped_column(ForeignKey("connector_endpoint.id", ondelete="RESTRICT"))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CapabilityVerification(Base):
    __tablename__ = "capability_verification"
    __table_args__ = (
        Index("ix_capability_verification_registration_scope_id", "registration_id", "scope_kind", "id"),
        CheckConstraint("result IN ('verified', 'failed', 'revoked')", name="ck_capability_verification_result"),
        CheckConstraint("scope_kind IN ('publisher_action', 'data_source_endpoint', 'renderer_output')", name="ck_capability_verification_scope_kind"),
        CheckConstraint("length(config_fingerprint) = 64", name="ck_capability_verification_fingerprint"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("capability_registration.id", ondelete="RESTRICT"), nullable=False, index=True)
    config_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    scope_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String(255))
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_json: Mapped[dict] = mapped_column(JSON, nullable=False)


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
    """工作流画布定义（仿扣子）：节点=已有能力的编排壳，结果沉淀回既有实体。

    V1 PRD 2.0（D4）：本表升级为版本化 Definition——workflow_key+version 唯一，
    publish 后 immutable（修改须 clone 新版本），历史行回填 schema_version=1。
    """

    __tablename__ = "workflow"
    __table_args__ = (UniqueConstraint("workflow_key", "version", name="uq_workflow_key_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    template_key: Mapped[str | None] = mapped_column(String(50))  # daily_suggest / gen_export / null=自定义
    workflow_key: Mapped[str | None] = mapped_column(String(120))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("workflow.id"))
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/published/archived
    schema_version: Mapped[int] = mapped_column(Integer, default=2, server_default="1")  # 历史行=1，新定义=2
    checksum: Mapped[str | None] = mapped_column(String(64))
    definition_json: Mapped[dict] = mapped_column(JSON)  # {nodes:[{id,type,label,params,layout}], edges:[{from,to}]}
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(255))
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), index=True)
    scope: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkflowRun(Base):
    """一次画布执行。status: running / waiting_input / succeeded / failed / canceled。

    V1 PRD 2.0（D5）：新平台生产按 Platform×ContentForm 一 Run，启动时冻结
    topic/channel/content_form/workflow_key/workflow_version/definition_checksum。
    """

    __tablename__ = "workflow_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow.id"))
    content_unit_id: Mapped[int | None] = mapped_column(ForeignKey("content_unit.id"), index=True)
    identity_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("identity_snapshot.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    context_json: Mapped[dict] = mapped_column(JSON, default=dict)  # 节点间数据总线（实体 ID 等）
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)  # 启动参数（topic_id 等）
    topic_id: Mapped[int | None] = mapped_column(Integer)
    channel: Mapped[str | None] = mapped_column(String(30))
    content_form: Mapped[str | None] = mapped_column(String(50))
    workflow_key: Mapped[str | None] = mapped_column(String(120))
    workflow_version: Mapped[int | None] = mapped_column(Integer)
    definition_checksum: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkflowStep(Base):
    """画布上单个节点的一次执行记录（input=params，output=产物摘要 + 实体 ID）。

    V1 PRD 2.0（D8）：记录 plugin key/version 与 input/output hash，支持 stale 与 rerun 审计。
    """

    __tablename__ = "workflow_step"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("workflow_run.id"))
    node_id: Mapped[str] = mapped_column(String(50))
    node_type: Mapped[str] = mapped_column(String(30))
    label: Mapped[str | None] = mapped_column(String(200))
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/running/waiting_input/succeeded/failed/skipped/stale
    output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    plugin_key: Mapped[str | None] = mapped_column(String(150))
    plugin_version: Mapped[str | None] = mapped_column(String(50))
    input_hash: Mapped[str | None] = mapped_column(String(64))
    output_hash: Mapped[str | None] = mapped_column(String(64))
    stale_reason: Mapped[str | None] = mapped_column(Text)
    attempt_no: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkflowStepAttempt(Base):
    """节点每次执行的不可变审计行（R2-H7：新旧 output 均可审计）。

    WorkflowStep 只保存「当前」输出；rerun 覆盖前，旧 output/hash 已沉淀为本表历史行。
    """

    __tablename__ = "workflow_step_attempt"
    __table_args__ = (
        Index("ix_workflow_step_attempt_step", "step_id", "attempt_no"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("workflow_step.id"))
    run_id: Mapped[int] = mapped_column(ForeignKey("workflow_run.id"))
    node_id: Mapped[str] = mapped_column(String(50))
    plugin_key: Mapped[str | None] = mapped_column(String(150))
    plugin_version: Mapped[str | None] = mapped_column(String(50))
    attempt_no: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    status: Mapped[str] = mapped_column(String(20))  # succeeded/failed
    output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_hash: Mapped[str | None] = mapped_column(String(64))
    input_hash: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentBrand(Base):
    __tablename__ = "content_brand"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentBrandRevision(Base):
    __tablename__ = "content_brand_revision"
    __table_args__ = (UniqueConstraint("brand_id", "revision_no", name="uq_content_brand_revision"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("content_brand.id"), index=True)
    revision_no: Mapped[int] = mapped_column(Integer)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    checksum: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentPersona(Base):
    __tablename__ = "content_persona"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("content_brand.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentPersonaRevision(Base):
    __tablename__ = "content_persona_revision"
    __table_args__ = (UniqueConstraint("persona_id", "revision_no", name="uq_content_persona_revision"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("content_persona.id"), index=True)
    revision_no: Mapped[int] = mapped_column(Integer)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    checksum: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentAccount(Base):
    __tablename__ = "content_account"
    __table_args__ = (
        CheckConstraint("(platform_channel IS NULL AND platform_account_id IS NULL) OR (platform_channel IS NOT NULL AND platform_account_id IS NOT NULL)", name="ck_content_account_platform_pair"),
        UniqueConstraint("platform_channel", "platform_account_id", name="uq_content_account_platform_identity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("content_persona.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    platform_channel: Mapped[str | None] = mapped_column(String(50))
    platform_account_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentAccountRevision(Base):
    __tablename__ = "content_account_revision"
    __table_args__ = (UniqueConstraint("account_id", "revision_no", name="uq_content_account_revision"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("content_account.id"), index=True)
    revision_no: Mapped[int] = mapped_column(Integer)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    checksum: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentSeries(Base):
    __tablename__ = "content_series"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("content_account.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentSeriesRevision(Base):
    __tablename__ = "content_series_revision"
    __table_args__ = (UniqueConstraint("series_id", "revision_no", name="uq_content_series_revision"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("content_series.id"), index=True)
    revision_no: Mapped[int] = mapped_column(Integer)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    checksum: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IdentitySnapshot(Base):
    __tablename__ = "identity_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("content_brand.id"))
    brand_revision_id: Mapped[int | None] = mapped_column(ForeignKey("content_brand_revision.id"))
    persona_id: Mapped[int] = mapped_column(ForeignKey("content_persona.id"), index=True)
    persona_revision_id: Mapped[int | None] = mapped_column(ForeignKey("content_persona_revision.id"))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("content_account.id"))
    account_revision_id: Mapped[int | None] = mapped_column(ForeignKey("content_account_revision.id"))
    series_id: Mapped[int | None] = mapped_column(ForeignKey("content_series.id"))
    series_revision_id: Mapped[int | None] = mapped_column(ForeignKey("content_series_revision.id"))
    brand_voice_version_id: Mapped[int | None] = mapped_column(ForeignKey("brand_voice_version.id"))
    effective_profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    field_origins_json: Mapped[dict] = mapped_column(JSON, default=dict)
    checksum: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentProject(Base):
    __tablename__ = "content_project"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    objective: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ContentOpportunity(Base):
    __tablename__ = "content_opportunity"
    __table_args__ = (
        CheckConstraint("status IN ('new','watching','qualified','dismissed','converted','archived')", name="ck_content_opportunity_status"),
        CheckConstraint("priority IN ('low','normal','high')", name="ck_content_opportunity_priority"),
        Index("ix_content_opportunity_owner_status_priority", "owner_user_id", "status", "priority", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="new")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    relevant_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ContentOpportunitySignal(Base):
    __tablename__ = "content_opportunity_signal"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "signal_type", "source_entity_id", name="uq_opportunity_signal_resource"),
        Index("ix_opportunity_signal_type_status", "opportunity_id", "signal_type", "status"),
        CheckConstraint("status IN ('active','detached')", name="ck_opportunity_signal_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("content_opportunity.id"), index=True)
    signal_type: Mapped[str] = mapped_column(String(30))
    source_entity_id: Mapped[int | None] = mapped_column(Integer)
    external_ref: Mapped[str | None] = mapped_column(String(1000))
    label: Mapped[str] = mapped_column(String(300))
    annotation_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_checksum: Mapped[str | None] = mapped_column(String(64))
    source_version: Mapped[str | None] = mapped_column(String(100))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")
    attached_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    detached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ContentOpportunityAssessmentRevision(Base):
    __tablename__ = "content_opportunity_assessment_revision"
    __table_args__ = (UniqueConstraint("opportunity_id", "revision_no", name="uq_opportunity_assessment_revision"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("content_opportunity.id"), index=True)
    revision_no: Mapped[int] = mapped_column(Integer)
    parent_revision_id: Mapped[int | None] = mapped_column(ForeignKey("content_opportunity_assessment_revision.id"))
    assessment_json: Mapped[dict] = mapped_column(JSON, default=dict)
    checksum: Mapped[str] = mapped_column(String(64))
    analysis_source: Mapped[str] = mapped_column(String(30), default="manual")
    analysis_provider_key: Mapped[str | None] = mapped_column(String(100))
    analysis_provider_version: Mapped[str | None] = mapped_column(String(100))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OpportunityProjectConversion(Base):
    __tablename__ = "opportunity_project_conversion"
    __table_args__ = (
        UniqueConstraint("opportunity_id", name="uq_opportunity_conversion_opportunity"),
        UniqueConstraint("project_id", name="uq_opportunity_conversion_project"),
        UniqueConstraint("idempotency_key", name="uq_opportunity_conversion_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("content_opportunity.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id"), index=True)
    assessment_revision_id: Mapped[int] = mapped_column(ForeignKey("content_opportunity_assessment_revision.id"))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    conversion_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentUnit(Base):
    __tablename__ = "content_unit"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id"), index=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("content_persona.id"))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("content_account.id"), index=True)
    series_id: Mapped[int | None] = mapped_column(ForeignKey("content_series.id"), index=True)
    identity_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("identity_snapshot.id"), index=True)
    modality: Mapped[str] = mapped_column(String(20))
    channel_id: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    pinned_workflow_id: Mapped[int | None] = mapped_column(ForeignKey("workflow.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PersonaWorkflowDefault(Base):
    __tablename__ = "persona_workflow_default"
    __table_args__ = (UniqueConstraint("persona_id", "modality", name="uq_persona_workflow_default"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("content_persona.id"))
    modality: Mapped[str] = mapped_column(String(20))
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow.id"))
    revision: Mapped[int] = mapped_column(Integer, default=1)


class AccountWorkflowDefault(Base):
    __tablename__ = "account_workflow_default"
    __table_args__ = (UniqueConstraint("account_id", "modality", name="uq_account_workflow_default"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("content_account.id"), index=True)
    modality: Mapped[str] = mapped_column(String(20))
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow.id"))
    revision: Mapped[int] = mapped_column(Integer, default=1)


class SeriesWorkflowDefault(Base):
    __tablename__ = "series_workflow_default"
    __table_args__ = (UniqueConstraint("series_id", "modality", name="uq_series_workflow_default"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("content_series.id"), index=True)
    modality: Mapped[str] = mapped_column(String(20))
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow.id"))
    revision: Mapped[int] = mapped_column(Integer, default=1)


class ProjectWorkflowBinding(Base):
    __tablename__ = "project_workflow_binding"
    __table_args__ = (UniqueConstraint("unit_id", name="uq_project_workflow_binding_unit"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("content_unit.id"))
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow.id"))
    revision: Mapped[int] = mapped_column(Integer, default=1)


class DataSnapshot(Base):
    __tablename__ = "data_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("content_unit.id"), index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_run.id"))
    node_id: Mapped[str] = mapped_column(String(50))
    plugin_key: Mapped[str] = mapped_column(String(150))
    source_ref: Mapped[str] = mapped_column(String(255))
    source_version: Mapped[str | None] = mapped_column(String(100))
    checksum: Mapped[str] = mapped_column(String(64))
    normalized_output: Mapped[dict] = mapped_column(JSON, default=dict)
    lineage_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProjectWorkflowOutput(Base):
    __tablename__ = "project_workflow_output"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id"), index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("content_unit.id"))
    run_id: Mapped[int] = mapped_column(ForeignKey("workflow_run.id"))
    node_id: Mapped[str] = mapped_column(String(50))
    attempt_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_step_attempt.id"))
    output_kind: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[int] = mapped_column(Integer)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CreativeBriefRevision(Base):
    __tablename__ = "creative_brief_revision"
    __table_args__ = (
        UniqueConstraint("project_id", "revision_no", name="uq_creative_brief_project_revision"),
        Index("ix_creative_brief_project_created", "project_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id"))
    revision_no: Mapped[int] = mapped_column(Integer)
    parent_revision_id: Mapped[int | None] = mapped_column(ForeignKey("creative_brief_revision.id"))
    objective: Mapped[str] = mapped_column(Text)
    primary_audience: Mapped[str | None] = mapped_column(Text)
    core_message: Mapped[str | None] = mapped_column(Text)
    angle: Mapped[str | None] = mapped_column(Text)
    required_evidence_json: Mapped[list] = mapped_column(JSON, default=list)
    content_constraints_json: Mapped[list] = mapped_column(JSON, default=list)
    identity_scope_json: Mapped[list] = mapped_column(JSON, default=list)
    modality_scope_json: Mapped[list] = mapped_column(JSON, default=list)
    channel_scope_json: Mapped[list] = mapped_column(JSON, default=list)
    cta: Mapped[str | None] = mapped_column(Text)
    references_json: Mapped[list] = mapped_column(JSON, default=list)
    checksum: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProjectSourceBinding(Base):
    __tablename__ = "project_source_binding"
    __table_args__ = (
        UniqueConstraint("project_id", "source_document_id", name="uq_project_source"),
        Index("ix_project_source_project_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id"))
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")
    note: Mapped[str | None] = mapped_column(Text)
    attached_by: Mapped[str | None] = mapped_column(String(255))
    attached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    detached_by: Mapped[str | None] = mapped_column(String(255))
    detached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProjectFactBoundaryRevision(Base):
    __tablename__ = "project_fact_boundary_revision"
    __table_args__ = (
        UniqueConstraint("project_id", "revision_no", name="uq_project_fact_boundary_revision"),
        Index("ix_project_fact_boundary_project_created", "project_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id"))
    revision_no: Mapped[int] = mapped_column(Integer)
    parent_revision_id: Mapped[int | None] = mapped_column(ForeignKey("project_fact_boundary_revision.id"))
    fact_pack_id: Mapped[int] = mapped_column(ForeignKey("fact_pack.id"))
    fact_pack_version: Mapped[int] = mapped_column(Integer)
    fact_pack_checksum: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProjectMaterialReference(Base):
    __tablename__ = "project_material_reference"
    __table_args__ = (
        UniqueConstraint("project_id", "material_revision_id", name="uq_project_material_revision"),
        Index("ix_project_material_project_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id"))
    material_revision_id: Mapped[int] = mapped_column(ForeignKey("material_revision.id"))
    origin: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="active")
    note: Mapped[str | None] = mapped_column(Text)
    attached_by: Mapped[str | None] = mapped_column(String(255))
    attached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    detached_by: Mapped[str | None] = mapped_column(String(255))
    detached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProjectEvent(Base):
    __tablename__ = "project_event"
    __table_args__ = (
        Index("ix_project_event_project_id_id", "project_id", "id"),
        Index("ix_project_event_project_created", "project_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("content_project.id"))
    event_type: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(80))
    actor: Mapped[str | None] = mapped_column(String(255))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PublishedContentRecord(Base):
    __tablename__ = "published_content_record"
    __table_args__ = (
        UniqueConstraint('delivery_receipt_id', name='uq_published_receipt'),
        UniqueConstraint('owner_user_id', 'channel', 'external_key', name='uq_published_external'),
        CheckConstraint("origin IN ('studio','external_import')", name='ck_published_origin'),
        CheckConstraint("status IN ('active','archived')", name='ck_published_status'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    origin: Mapped[str] = mapped_column(String(30))
    external_key: Mapped[str | None] = mapped_column(String(300))
    content_asset_id: Mapped[int | None] = mapped_column(ForeignKey('content_asset.id'))
    delivery_target_id: Mapped[int | None] = mapped_column(ForeignKey('delivery_target.id'))
    delivery_receipt_id: Mapped[int | None] = mapped_column(ForeignKey('delivery_receipt.id'))
    content_account_id: Mapped[int | None] = mapped_column(ForeignKey('content_account.id'))
    identity_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey('identity_snapshot.id'))
    channel: Mapped[str] = mapped_column(String(30), index=True)
    content_form: Mapped[str | None] = mapped_column(String(50))
    account_ref_snapshot: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(500))
    canonical_url: Mapped[str | None] = mapped_column(String(2000))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    content_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    coverage_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default='active')
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PerformanceObservation(Base):
    __tablename__ = "performance_observation"
    __table_args__ = (
        UniqueConstraint('supersedes_id', name='uq_observation_correction_tip'),
        CheckConstraint("observation_kind IN ('metric','feedback','editorial','correction')", name='ck_observation_kind'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    published_content_id: Mapped[int] = mapped_column(ForeignKey('published_content_record.id'), index=True)
    observation_kind: Mapped[str] = mapped_column(String(30))
    metric_namespace: Mapped[str | None] = mapped_column(String(100))
    metric_key: Mapped[str | None] = mapped_column(String(100))
    numeric_value: Mapped[float | None] = mapped_column(Float)
    text_value: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(50))
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(30), default='manual')
    source_ref: Mapped[str | None] = mapped_column(String(300))
    source_checksum: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float | None] = mapped_column(Float)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    supersedes_id: Mapped[int | None] = mapped_column(ForeignKey('performance_observation.id'))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentInsight(Base):
    __tablename__ = "content_insight"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    insight_type: Mapped[str] = mapped_column(String(30), default='general')
    statement: Mapped[str] = mapped_column(Text)
    scope_json: Mapped[dict] = mapped_column(JSON, default=dict)
    cohort_json: Mapped[dict] = mapped_column(JSON, default=dict)
    coverage_json: Mapped[dict] = mapped_column(JSON, default=dict)
    supporting_refs_json: Mapped[list] = mapped_column(JSON, default=list)
    contradicting_refs_json: Mapped[list] = mapped_column(JSON, default=list)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float | None] = mapped_column(Float)
    analysis_source: Mapped[str] = mapped_column(String(30), default='manual')
    provider_key: Mapped[str | None] = mapped_column(String(150))
    provider_version: Mapped[str | None] = mapped_column(String(50))
    checksum: Mapped[str] = mapped_column(String(64))
    supersedes_id: Mapped[int | None] = mapped_column(ForeignKey('content_insight.id'))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LearningCandidate(Base):
    __tablename__ = "learning_candidate"
    __table_args__ = (
        CheckConstraint("status IN ('collecting','ready_for_review','accepted','rejected','archived')", name='ck_learning_candidate_status'),
        CheckConstraint("category IN ('identity','audience','channel','format','topic','workflow')", name='ck_learning_candidate_category'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    category: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(500))
    proposition: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, default='')
    scope_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default='collecting', index=True)
    revision_no: Mapped[int] = mapped_column(Integer, default=1)
    confidence: Mapped[float | None] = mapped_column(Float)
    validation_method: Mapped[str | None] = mapped_column(String(30))
    validation_summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_from_insight_id: Mapped[int | None] = mapped_column(ForeignKey('content_insight.id'))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_by: Mapped[str | None] = mapped_column(String(255))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LearningCandidateEvidence(Base):
    __tablename__ = "learning_candidate_evidence"
    __table_args__ = (
        UniqueConstraint('learning_candidate_id', 'evidence_type', 'entity_id', 'role', name='uq_learning_evidence'),
        CheckConstraint("role IN ('support','contradict','context')", name='ck_learning_evidence_role'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learning_candidate_id: Mapped[int] = mapped_column(ForeignKey('learning_candidate.id'), index=True)
    evidence_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(20))
    snapshot_checksum: Mapped[str | None] = mapped_column(String(64))
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentMemoryEntry(Base):
    __tablename__ = "content_memory_entry"
    __table_args__ = (
        UniqueConstraint('source_learning_candidate_id', name='uq_memory_promoted_candidate'),
        UniqueConstraint('owner_user_id','promotion_idempotency_key', name='uq_memory_promotion_key'),
        CheckConstraint("scope_type IN ('owner','brand','persona','account','series')", name='ck_memory_scope'),
        CheckConstraint("status IN ('active','archived')", name='ck_memory_status'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    scope_type: Mapped[str] = mapped_column(String(30))
    brand_id: Mapped[int | None] = mapped_column(ForeignKey('content_brand.id'))
    persona_id: Mapped[int | None] = mapped_column(ForeignKey('content_persona.id'))
    account_id: Mapped[int | None] = mapped_column(ForeignKey('content_account.id'))
    series_id: Mapped[int | None] = mapped_column(ForeignKey('content_series.id'))
    memory_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default='active')
    source_learning_candidate_id: Mapped[int] = mapped_column(ForeignKey('learning_candidate.id'))
    promotion_idempotency_key: Mapped[str] = mapped_column(String(100))
    promotion_checksum: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProviderGenerationTask(Base):
    __tablename__ = "provider_generation_task"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "idempotency_key", name="uq_generation_owner_key"),
        CheckConstraint("state IN ('prepared','submitting','running','unknown','result_ready','accepted','failed','cancelled')", name="ck_generation_state"),
        CheckConstraint("revision > 0", name="ck_generation_revision"),
        CheckConstraint("query_count >= 0 AND query_count <= 120", name="ck_generation_queries"),
        CheckConstraint("result_size IS NULL OR (result_size > 0 AND result_size <= 31457280)", name="ck_generation_size"),
        CheckConstraint("state != 'accepted' OR accepted_material_revision_id IS NOT NULL", name="ck_generation_accepted_ref"),
        Index("ix_generation_owner_state", "owner_user_id", "state"),
        Index("ix_generation_project_state", "project_id", "state"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("content_project.id"))
    workflow_step_attempt_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_step_attempt.id"))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    request_hash: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(20), default="prepared")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    request_json: Mapped[dict] = mapped_column(JSON)
    plan_json: Mapped[dict] = mapped_column(JSON)
    plan_hash: Mapped[str] = mapped_column(String(64))
    provider_kind: Mapped[str] = mapped_column(String(30))
    provider_key: Mapped[str] = mapped_column(String(150))
    provider_version: Mapped[str] = mapped_column(String(50))
    model_id: Mapped[str] = mapped_column(String(100))
    protocol_version: Mapped[str] = mapped_column(String(50))
    runtime_hash: Mapped[str] = mapped_column(String(64))
    credential_epoch: Mapped[str] = mapped_column(String(64))
    input_hash: Mapped[str] = mapped_column(String(64))
    source_refs_json: Mapped[list] = mapped_column(JSON, default=list)
    receipt_key_id: Mapped[str] = mapped_column(String(100))
    receipt_signature: Mapped[str] = mapped_column(String(64))
    provider_job_id: Mapped[str | None] = mapped_column(String(200))
    provider_file_id: Mapped[str | None] = mapped_column(String(200))
    result_storage_key: Mapped[str | None] = mapped_column(String(300))
    result_mime: Mapped[str | None] = mapped_column(String(100))
    result_hash: Mapped[str | None] = mapped_column(String(64))
    result_size: Mapped[int | None] = mapped_column(Integer)
    result_signature: Mapped[str | None] = mapped_column(String(64))
    accepted_material_revision_id: Mapped[int | None] = mapped_column(ForeignKey("material_revision.id"))
    acceptance_hash: Mapped[str | None] = mapped_column(String(64))
    lease_token: Mapped[str | None] = mapped_column(String(32))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason_code: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentMemoryRevision(Base):
    __tablename__ = "content_memory_revision"
    __table_args__ = (
        UniqueConstraint('memory_entry_id','revision_no',name='uq_memory_revision'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    memory_entry_id: Mapped[int] = mapped_column(ForeignKey('content_memory_entry.id'), index=True)
    revision_no: Mapped[int] = mapped_column(Integer)
    parent_revision_id: Mapped[int | None] = mapped_column(ForeignKey('content_memory_revision.id'))
    statement: Mapped[str] = mapped_column(Text)
    applicability_json: Mapped[dict] = mapped_column(JSON, default=dict)
    limitations_json: Mapped[list] = mapped_column(JSON, default=list)
    source_learning_candidate_id: Mapped[int] = mapped_column(ForeignKey('learning_candidate.id'))
    evidence_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    checksum: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
