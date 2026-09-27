# OpenSpec — add-v2-video-content-harness

> Change ID: `add-v2-video-content-harness`  
> Product: AIContentStudio  
> Scope: V2 Video & Multimodal Production  
> Type: Major additive architecture change  
> Baseline: V1 PRD 2.0 Content Harness 已实施  
> Date: 2026-09-24  
> Source PRD: `AIContentStudio_V2_视频生产版_PRD_代码级_2026-09-24.md`  
> North Star: 图 / 文 / 视一体化 Content Harness  
> Implementation principle: **新增 Video Domain，复用 V1 Control Plane；不创建第二套 Material / Review / Delivery / Workflow 系统。**

---

# 0. OpenSpec 使用方式

本文件是 V2 视频版本的代码级 OpenSpec 总投影。

实际落入仓库时建议拆成：

```text
openspec/changes/add-v2-video-content-harness/
├── proposal.md
├── design.md
├── tasks.md
└── specs/
    ├── video-domain-model/
    │   └── spec.md
    ├── video-composition-timeline/
    │   └── spec.md
    ├── video-material-derivation/
    │   └── spec.md
    ├── video-provider-runtime/
    │   └── spec.md
    ├── video-rendering/
    │   └── spec.md
    ├── video-tts-voice/
    │   └── spec.md
    ├── video-digital-human/
    │   └── spec.md
    ├── video-checks-rights/
    │   └── spec.md
    ├── video-candidate-approval/
    │   └── spec.md
    ├── video-discoverability/
    │   └── spec.md
    ├── video-review-publish-center/
    │   └── spec.md
    └── video-delivery/
        └── spec.md
```

本文件已经包含上述四类内容：

```text
Proposal
Design
Capability Specs
Tasks / Acceptance
```

实施前由 Codex 按上述目录投影，不应改动本文件表达的产品语义。

---

# PART I — PROPOSAL

# 1. Why

V1 Content Harness 已经建立以下稳定核心：

```text
Source / FactPack
Topic / MotherRevision
Channel Registry
Workflow / WorkflowRun / WorkflowStep
Node Plugin Registry
Material / MaterialRevision
Draft / DraftMedia
DraftCheckRun
Discoverability
Candidate Manifest v2
ContentAsset
DeliveryTarget / DeliveryAttempt / Receipt
Review & Publish Center
```

这套架构已经能够支持：

```text
TextArtifact
ImageArtifact
```

并且已经形成：

```text
Content Control Plane
+
Execution Plugin Runtime
```

的基本边界。

如果 V2 视频采用另一套：

```text
VideoProject
VideoMaterialCenter
VideoReview
VideoPublishJob
VideoWorkflowEngine
```

将会产生以下严重问题：

1. 同一个 Topic 出现文章事实与视频事实两套真源；
2. 图片素材与视频素材不能复用；
3. 视频审核与文章审核状态冲突；
4. 视频 Publisher 重复建设 Delivery 幂等与 Unknown 处理；
5. 视频 Workflow 无法复用现有 Plugin Registry / Rerun / Staleness；
6. SEO / Discoverability 再建一套；
7. 后续数字人、TTS、AI Video Provider 被写死在视频业务代码；
8. Review Center 无法形成统一内容控制面；
9. V3 再增加新模态时继续复制系统；
10. 无法回答“最终视频到底使用了哪一版事实、声音、数字人、素材、Timeline 和 Provider”。

因此 V2 必须坚持：

> **Video 是 Content Harness 中新增的一级 Artifact，而不是独立产品。**

---

# 2. What Changes

V2 新增以下核心能力：

1. 新增 `VideoProject`，作为 Topic 下的视频 Artifact 生产实例。
2. 新增版本化 `VideoScriptRevision`。
3. 新增版本化 `StoryboardRevision`。
4. 新增稳定 `VideoScene` 标识，支持 Scene 级重跑。
5. 新增版本化 `TimelineRevision`，作为最终视频 Composition 真源。
6. 扩展 `Material / MaterialRevision` 支持 video/audio/music/sfx/avatar/subtitle 等。
7. 新增 `MaterialDerivation`，记录素材派生图。
8. 新增 `VoiceProfileVersion` 与 `TTSProvider`。
9. 新增 `AvatarProfileVersion` 与 `DigitalHumanProvider`。
10. 新增 `VideoGenerationProvider`。
11. 新增 `VideoRenderProvider`。
12. 新增 `ProviderJob`，统一高成本/远端生成任务的 prepared/running/succeeded/failed/unknown 状态。
13. 新增 `VideoRender`，记录 preview/final/segment render。
14. 新增 `SubtitleTrackRevision`。
15. 扩展 Discoverability，支持 Video SEO。
16. 扩展 Rule Registry，支持 Video QC / Rights / Voice / Avatar / Subtitle / Render 检查。
17. Candidate Manifest 升级到 schema v3，冻结最终视频 bytes、thumbnail、subtitle、SEO、Timeline provenance 和 Provider 版本。
18. Review & Publish Center 增加 Video Review projection，不创建第二套审核中心。
19. Delivery Router 支持 video package / assisted upload / auto draft，不创建 VideoDeliveryTarget。
20. Celery 增加 media/render/publisher queue。
21. 引入 BlobStore abstraction，为大文件和对象存储做好生产准备。
22. 增加 `VideoWorkspace.tsx`，用于 Storyboard / Timeline / Material / Render 生产。
23. `ReviewPublish.tsx` 增加视频批准视图。
24. V1 Text/Image 全链路必须保持兼容。

---

# 3. New Capabilities

- `video-domain-model`
- `video-composition-timeline`
- `video-material-derivation`
- `video-provider-runtime`
- `video-rendering`
- `video-tts-voice`
- `video-digital-human`
- `video-checks-rights`
- `video-candidate-approval`
- `video-discoverability`
- `video-review-publish-center`
- `video-delivery`

---

# 4. Modified Capabilities

以下 V1 capability 被扩展，不被替换：

- `content-harness-registry`
- `versioned-channel-workflow`
- `material-library-v1`
- `unified-check-runs`
- `discoverability-optimization`
- `workflow-rerun-staleness`
- `unified-review-publish-center`
- `delivery-router-v1`
- `versioned-article-candidate`

Candidate 能力在 V2 后应逐步改称通用：

```text
versioned-content-candidate
```

但 V2 实施中不要求立即重命名历史 capability。

---

# 5. Non-goals

本 change 不建设：

- Premiere / Final Cut 级 NLE；
- 高级关键帧动画；
- 多人实时协作；
- 自研 TTS 模型；
- 自研 Digital Human 模型；
- 自研视频 Diffusion 模型；
- 自动购买素材版权；
- 自动法律判断；
- 无人审批自动公开发布；
- 独立视频素材库；
- 独立视频审核中心；
- 独立视频发布系统；
- 独立视频 Workflow Engine；
- 第二套 SEO 系统。

---

# 6. Impact

## Backend

主要涉及：

```text
apps/api/app/models.py
apps/api/app/services/content_harness/
apps/api/app/services/video/
apps/api/app/services/materials.py
apps/api/app/services/discoverability.py
apps/api/app/services/candidates.py
apps/api/app/services/delivery.py
apps/api/app/services/workflow_engine.py
apps/api/app/tasks/celery_app.py
apps/api/app/tasks/worker_tasks.py
apps/api/app/routers/review_center.py
apps/api/app/routers/materials.py
apps/api/app/routers/workflows.py
apps/api/app/routers/delivery.py
apps/api/app/routers/video_projects.py          # new
apps/api/app/routers/video_composition.py       # new
apps/api/app/routers/video_providers.py         # new
apps/api/app/seed.py
```

## Frontend

```text
apps/web/src/pages/VideoWorkspace.tsx           # new
apps/web/src/pages/ReviewPublish.tsx
apps/web/src/pages/Materials.tsx
apps/web/src/pages/Workflows.tsx
apps/web/src/pages/Settings.tsx

apps/web/src/components/video/
  VideoPreview.tsx
  VideoTimeline.tsx
  SceneList.tsx
  SceneEditor.tsx
  StoryboardPanel.tsx
  SubtitleEditor.tsx
  AudioPanel.tsx
  AvatarPanel.tsx
  VideoChecksPanel.tsx
  VideoSeoPanel.tsx
  VideoRenderPanel.tsx

apps/web/src/api/video.ts                       # new
```

## Persistence

Additive Alembic migrations：

```text
V2-A video core
V2-B media/profiles
V2-C render/provider jobs
V2-D check/candidate generalization if required
```

## Infrastructure

新增：

```text
BlobStore
Celery media queue
Celery render queue
Celery publisher queue（若本批次迁移）
FFmpeg / equivalent render runtime
```

---

# PART II — DESIGN

# 7. Overall Architecture

```text
Source / FactPack
      ↓
Topic / MotherRevision
      ↓
VideoProject
      ↓
Video Strategy
      ↓
VideoScriptRevision
      ↓
StoryboardRevision
      ↓
VideoScene
      ↓
Material Planning
      ↓
Material Library
  ├─ Image
  ├─ Video
  ├─ Audio
  ├─ Chart
  ├─ Screenshot
  ├─ Music
  ├─ Avatar
  └─ Subtitle
      ↓
TTS / Digital Human / VideoGen
      ↓
TimelineRevision
      ↓
SubtitleTrackRevision
      ↓
Preview Render
      ↓
Human Review
      ↓
Final Render
      ↓
Video QC + Rights + SEO
      ↓
Candidate Manifest v3
      ↓
Approval
      ↓
Existing DeliveryTarget
      ↓
Auto / Assisted / Copy Package
      ↓
Receipt / Feedback
```

---

# 8. Key Design Decisions

## D1 — Video 是一级 Artifact，不是 Draft 附件

`VideoProject` 表达视频生产实例。

最终批准仍然落入：

```text
ContentAsset
candidate_manifest_json
approved_candidate_hash
```

不新增第二套 approved asset。

---

## D2 — 不新建 Video Material Library

所有媒体统一进入：

```text
Material
MaterialRevision
```

V2 只扩展：

```text
kind
technical metadata
derivation
blob storage
```

---

## D3 — Script / Storyboard / Timeline 三层必须分离

### Script

表达：

```text
说什么
```

### Storyboard

表达：

```text
每一段应该呈现什么
```

### Timeline

表达：

```text
最终在时间轴上实际摆了什么素材
```

禁止将三者压成一个大 JSON 后无法局部重跑。

---

## D4 — TimelineRevision 是视频 Composition 真源

最终 Render 必须绑定：

```text
timeline_revision_id
timeline_hash
```

不能用当前 mutable editor state 直接产生 approved candidate。

---

## D5 — Scene 使用稳定 scene_key

同一个 Storyboard Revision 内：

```text
scene_key
```

必须稳定。

用于：

- Scene rerun；
- Material attach；
- Clip provenance；
- QC 报告定位；
- UI selection；
- stale propagation。

---

## D6 — V2 继续使用 Revision-only Editing

以下对象不可原地修改历史版本：

```text
VideoScriptRevision
StoryboardRevision
TimelineRevision
SubtitleTrackRevision
VoiceProfileVersion
AvatarProfileVersion
MaterialRevision
```

用户 Save = 新 Revision。

---

## D7 — Video Provider 全部插件化

Provider kinds：

```text
tts
digital_human
video_generation
video_render
blob_store
```

不允许业务层：

```python
if provider == "xxx":
```

散落实现。

---

## D8 — ProviderJob 统一远端生产副作用

任何可能：

- 收费；
- 长时间运行；
- timeout 但远端仍继续；
- 无法安全自动重复；

的远端生成操作使用：

```text
ProviderJob
```

状态：

```text
prepared
running
succeeded
failed
unknown
```

---

## D9 — ProviderJob 与 DeliveryAttempt 分离

两者语义不同。

### ProviderJob

生产内容：

```text
TTS
Avatar
AI Video
External Render
```

### DeliveryAttempt

把已批准内容送到平台。

不能混成一个表。

---

## D10 — BlobStore 统一大文件存储

MaterialRevision 增加：

```text
storage_provider
storage_key
```

保留：

```text
file_path
```

作为 V1 local compatibility。

---

## D11 — Binary 不进入 DB / Workflow Context / Celery Message

禁止：

```text
video bytes
audio bytes
large base64
```

进入：

```text
JSON
Celery payload
Workflow context
Candidate manifest
```

只传 ID / hash / storage key。

---

## D12 — FFmpeg / Renderer 是 Provider，不是 VideoProject 内部函数

推荐首个实现：

```text
render.ffmpeg@1
```

未来允许：

```text
render.remotion
render.cloud_x
```

---

## D13 — Preview Render 与 Final Render 分离

Preview：

- 快；
- 低成本；
- 可低码率；
- 用于审核生产过程。

Final：

- 平台目标规格；
- 最终 bytes；
- 参与 Candidate Hash。

---

## D14 — Segment Render 一等能力

长视频局部调整时允许：

```text
start_ms
end_ms
```

Render。

避免每次改 5 秒都重渲整片。

---

## D15 — TTS 输出必须成为 MaterialRevision

不能只返回：

```text
/tmp/voice.wav
```

必须保存：

```text
MaterialRevision(kind=audio)
```

并建立 provenance。

---

## D16 — Digital Human 输出必须成为 MaterialRevision

输入：

```text
AvatarProfileVersion
Audio MaterialRevision
```

输出：

```text
MaterialRevision(kind=video)
```

同时创建 `MaterialDerivation`。

---

## D17 — Digital Human 不是 Video Workflow 必选节点

普通视频：

```text
不需要 avatar
```

没有 Digital Human Provider 时不能阻塞：

```text
short_video
long_video
demo_video
```

只阻塞：

```text
content_form requiring avatar
```

---

## D18 — Avatar / Voice 权利是硬 Gate

Avatar：

```text
consent_ref
public_use_allowed
commercial_use_allowed
allowed_channels
```

Voice：

```text
rights_status
consent_ref
allowed_channels
```

缺失时：

```text
blocker
```

---

## D19 — 字幕是版本化成品组成部分

字幕不是 Render 临时副产品。

SubtitleTrackRevision：

```text
cues
language
source
hash
```

Candidate 冻结其 revision/hash。

---

## D20 — Discoverability 继续复用 V1 Report

不新增：

```text
VideoSEOReport
```

只增加：

```text
video discoverability profile
```

和 report schema 字段。

---

## D21 — Video QC 进入统一 Rule / Check 体系

如果 V1 `DraftCheckRun` 无法自然绑定 VideoProject：

V2 允许新增通用：

```text
ArtifactCheckRun
```

推荐最终模型：

```text
target_type
target_id
check_kind
profile
input_hash
status
report_json
```

V1 DraftCheckRun 保持可读。

---

## D22 — Candidate Manifest 升级 schema v3

v3 必须覆盖：

```text
final video hash
timeline revision
script revision
storyboard revision
subtitle revision
thumbnail
voice profile
avatar profile
materials
rights
discoverability
checks
workflow/plugin versions
```

---

## D23 — Approval 绑定最终 Video Candidate

Reviewer 批准前必须看到：

```text
final render
thumbnail
title
description
tags
subtitle
chapters
rights
QC
SEO
```

不能批准只有 Script / Timeline 的半成品。

---

## D24 — Platform Transcode 必须发生在 Approval 前

如果：

```text
Bilibili
XHS
Douyin
```

需要不同视频 bytes：

应形成各自 Platform Candidate。

Publisher 禁止批准后重新编码并静默改变 bytes。

---

## D25 — Review Center 继续是 Projection

`ReviewPublish.tsx` 增加 Video Panel。

后端 `review_center.py` 聚合视频实体。

禁止新建：

```text
VideoReviewState
```

作为第二真源。

---

## D26 — Delivery 继续复用 V1

继续：

```text
DeliveryTarget
DeliveryAttempt
DeliveryReceipt
```

只增加 video content form / renderer / package。

---

## D27 — Unknown 安全哲学统一

远端：

```text
TTS
Avatar
VideoGen
Publisher
```

如果请求结果未知：

```text
unknown
```

禁止 blind retry。

---

## D28 — Queue 按负载拆分

推荐：

```text
default
llm
media
render
publisher
```

长 Render 不占满 LLM worker。

---

## D29 — Provider Capability 在 Workflow Preflight 检查

运行 Workflow 前检查：

```text
required capability exists?
configured?
enabled?
rights compatible?
platform compatible?
```

缺失：

```text
BLOCKED before execution
```

---

## D30 — V2 第一版 Timeline 不做专业 NLE

支持：

```text
clip
start/end
track
replace material
subtitle
overlay
avatar selection
scene order
preview
```

不支持高级：

```text
keyframe curve
mask animation
complex compositing
color grading
```

---

# 9. Database Design

# 9.1 VideoProject

```python
class VideoProject(Base):
    __tablename__ = "video_project"

    id: Mapped[int] = mapped_column(primary_key=True)

    topic_brief_id: Mapped[int] = mapped_column(
        ForeignKey("topic_brief.id"), index=True
    )

    mother_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("mother_revision.id"), index=True
    )

    channel: Mapped[str] = mapped_column(String(30), index=True)
    content_form: Mapped[str] = mapped_column(String(50))

    aspect_ratio: Mapped[str] = mapped_column(String(20))
    target_duration_ms: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(30), default="draft")

    workflow_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("workflow_run.id")
    )

    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

Status：

```text
draft
producing
needs_review
ready
archived
```

---

# 9.2 VideoScriptRevision

```python
class VideoScriptRevision(Base):
    __tablename__ = "video_script_revision"
    __table_args__ = (
        UniqueConstraint(
            "video_project_id",
            "revision_no",
            name="uq_video_script_revision_no",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"), index=True
    )

    revision_no: Mapped[int] = mapped_column(Integer)
    parent_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("video_script_revision.id")
    )

    title: Mapped[str | None] = mapped_column(String(500))
    hook_text: Mapped[str | None] = mapped_column(Text)
    script_text: Mapped[str] = mapped_column(Text)
    structured_json: Mapped[dict | None] = mapped_column(JSON)

    duration_estimate_ms: Mapped[int | None] = mapped_column(Integer)

    input_hash: Mapped[str] = mapped_column(String(64))
    body_hash: Mapped[str] = mapped_column(String(64))

    skill_key: Mapped[str | None] = mapped_column(String(150))
    skill_version: Mapped[str | None] = mapped_column(String(50))
    model_provider: Mapped[str | None] = mapped_column(String(50))
    model_name: Mapped[str | None] = mapped_column(String(100))

    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

---

# 9.3 StoryboardRevision

```python
class StoryboardRevision(Base):
    __tablename__ = "storyboard_revision"
    __table_args__ = (
        UniqueConstraint(
            "video_project_id",
            "revision_no",
            name="uq_storyboard_revision_no",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"), index=True
    )

    script_revision_id: Mapped[int] = mapped_column(
        ForeignKey("video_script_revision.id")
    )

    revision_no: Mapped[int] = mapped_column(Integer)
    parent_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("storyboard_revision.id")
    )

    storyboard_json: Mapped[dict] = mapped_column(JSON)

    input_hash: Mapped[str] = mapped_column(String(64))

    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

---

# 9.4 VideoScene

```python
class VideoScene(Base):
    __tablename__ = "video_scene"
    __table_args__ = (
        UniqueConstraint(
            "video_project_id",
            "storyboard_revision_id",
            "scene_key",
            name="uq_video_scene_revision_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"), index=True
    )

    storyboard_revision_id: Mapped[int] = mapped_column(
        ForeignKey("storyboard_revision.id")
    )

    scene_key: Mapped[str] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(Integer)

    start_ms: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    narration_text: Mapped[str | None] = mapped_column(Text)
    on_screen_text: Mapped[str | None] = mapped_column(Text)
    visual_intent: Mapped[str | None] = mapped_column(String(50))

    config_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="planned")
```

---

# 9.5 TimelineRevision

```python
class TimelineRevision(Base):
    __tablename__ = "timeline_revision"
    __table_args__ = (
        UniqueConstraint(
            "video_project_id",
            "revision_no",
            name="uq_timeline_revision_no",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"), index=True
    )

    storyboard_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("storyboard_revision.id")
    )

    revision_no: Mapped[int] = mapped_column(Integer)
    parent_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("timeline_revision.id")
    )

    duration_ms: Mapped[int] = mapped_column(Integer)
    fps: Mapped[float] = mapped_column(Float, default=30.0)

    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)

    composition_json: Mapped[dict] = mapped_column(JSON)

    input_hash: Mapped[str] = mapped_column(String(64))
    timeline_hash: Mapped[str] = mapped_column(String(64))

    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

---

# 9.6 SubtitleTrackRevision

```python
class SubtitleTrackRevision(Base):
    __tablename__ = "subtitle_track_revision"
    __table_args__ = (
        UniqueConstraint(
            "video_project_id",
            "language",
            "revision_no",
            name="uq_subtitle_track_revision",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"), index=True
    )

    revision_no: Mapped[int] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(20))
    format: Mapped[str] = mapped_column(String(20))

    cues_json: Mapped[list] = mapped_column(JSON)

    text_hash: Mapped[str] = mapped_column(String(64))
    source_kind: Mapped[str] = mapped_column(String(30))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

---

# 9.7 MaterialDerivation

```python
class MaterialDerivation(Base):
    __tablename__ = "material_derivation"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_revision_id: Mapped[int] = mapped_column(
        ForeignKey("material_revision.id"), index=True
    )

    output_revision_id: Mapped[int] = mapped_column(
        ForeignKey("material_revision.id"), index=True
    )

    operation: Mapped[str] = mapped_column(String(50))

    provider_key: Mapped[str | None] = mapped_column(String(150))
    provider_version: Mapped[str | None] = mapped_column(String(50))

    config_json: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

---

# 9.8 VoiceProfileVersion

```python
class VoiceProfileVersion(Base):
    __tablename__ = "voice_profile_version"
    __table_args__ = (
        UniqueConstraint(
            "profile_key",
            "version",
            name="uq_voice_profile_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    profile_key: Mapped[str] = mapped_column(String(150))
    version: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))

    provider_key: Mapped[str | None] = mapped_column(String(150))
    provider_voice_ref: Mapped[str | None] = mapped_column(String(255))

    language: Mapped[str | None] = mapped_column(String(30))

    config_json: Mapped[dict | None] = mapped_column(JSON)

    rights_status: Mapped[str | None] = mapped_column(String(30))
    consent_ref: Mapped[str | None] = mapped_column(String(500))

    allowed_channels_json: Mapped[list | None] = mapped_column(JSON)

    status: Mapped[str] = mapped_column(String(20))
    checksum: Mapped[str] = mapped_column(String(64))
```

---

# 9.9 AvatarProfileVersion

```python
class AvatarProfileVersion(Base):
    __tablename__ = "avatar_profile_version"
    __table_args__ = (
        UniqueConstraint(
            "profile_key",
            "version",
            name="uq_avatar_profile_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    profile_key: Mapped[str] = mapped_column(String(150))
    version: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))

    avatar_kind: Mapped[str] = mapped_column(String(30))

    provider_key: Mapped[str | None] = mapped_column(String(150))
    provider_avatar_ref: Mapped[str | None] = mapped_column(String(255))

    source_material_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("material_revision.id")
    )

    owner: Mapped[str | None] = mapped_column(String(255))
    consent_ref: Mapped[str | None] = mapped_column(String(500))

    public_use_allowed: Mapped[bool | None] = mapped_column(Boolean)
    commercial_use_allowed: Mapped[bool | None] = mapped_column(Boolean)

    allowed_channels_json: Mapped[list | None] = mapped_column(JSON)

    config_json: Mapped[dict | None] = mapped_column(JSON)

    status: Mapped[str] = mapped_column(String(20))
    checksum: Mapped[str] = mapped_column(String(64))
```

---

# 9.10 ProviderJob

```python
class ProviderJob(Base):
    __tablename__ = "provider_job"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_provider_job_idempotency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    provider_key: Mapped[str] = mapped_column(String(150))
    provider_version: Mapped[str | None] = mapped_column(String(50))

    operation: Mapped[str] = mapped_column(String(50))

    local_entity_type: Mapped[str] = mapped_column(String(50))
    local_entity_id: Mapped[str] = mapped_column(String(100))

    idempotency_key: Mapped[str] = mapped_column(String(64))
    request_hash: Mapped[str] = mapped_column(String(64))

    remote_job_id: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(
        String(20), default="prepared"
    )

    response_metadata_json: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

---

# 9.11 VideoRender

```python
class VideoRender(Base):
    __tablename__ = "video_render"

    id: Mapped[int] = mapped_column(primary_key=True)

    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"), index=True
    )

    timeline_revision_id: Mapped[int] = mapped_column(
        ForeignKey("timeline_revision.id")
    )

    render_kind: Mapped[str] = mapped_column(String(30))

    segment_start_ms: Mapped[int | None] = mapped_column(Integer)
    segment_end_ms: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(
        String(30), default="queued"
    )

    provider_key: Mapped[str] = mapped_column(String(150))
    provider_version: Mapped[str | None] = mapped_column(String(50))

    input_hash: Mapped[str] = mapped_column(String(64))

    output_material_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("material_revision.id")
    )

    progress_pct: Mapped[int | None] = mapped_column(Integer)
    stage: Mapped[str | None] = mapped_column(String(100))

    error: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

---

# 9.12 ExecutionUsage

```python
class ExecutionUsage(Base):
    __tablename__ = "execution_usage"

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("workflow_run.id")
    )

    workflow_step_id: Mapped[int | None] = mapped_column(
        ForeignKey("workflow_step.id")
    )

    provider_key: Mapped[str] = mapped_column(String(150))
    operation: Mapped[str] = mapped_column(String(50))

    usage_json: Mapped[dict] = mapped_column(JSON)

    currency: Mapped[str | None] = mapped_column(String(10))
    cost_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))

    metadata_json: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

无可信价格时：

```text
cost_amount = null
```

---

# 10. MaterialRevision Additive Fields

建议：

```python
storage_provider: Mapped[str | None]
storage_key: Mapped[str | None]

technical_metadata_json: Mapped[dict | None]

transcript_text: Mapped[str | None]
```

技术字段优先放：

```text
technical_metadata_json
```

例如：

```json
{
  "codec": "h264",
  "fps": 30,
  "bitrate": 5000000,
  "sample_rate": 48000,
  "audio_channels": 2
}
```

避免第一版拆过多数据库列。

---

# 11. Timeline Schema v1

```json
{
  "schema_version": 1,
  "canvas": {
    "width": 1080,
    "height": 1920,
    "fps": 30
  },
  "duration_ms": 60000,
  "tracks": [
    {
      "track_id": "main_video",
      "kind": "video",
      "clips": [
        {
          "clip_id": "clip_001",
          "scene_key": "scene_001",
          "start_ms": 0,
          "duration_ms": 5000,
          "material_revision_id": 100,
          "source_in_ms": 0,
          "source_out_ms": 5000,
          "transform": {
            "x": 0,
            "y": 0,
            "scale": 1.0,
            "crop": null
          }
        }
      ]
    }
  ]
}
```

---

# 12. Storyboard Schema v1

```json
{
  "schema_version": 1,
  "scenes": [
    {
      "scene_key": "scene_001",
      "order": 1,
      "duration_ms": 6000,
      "narration": "过去一年……",
      "visual_intent": "market_chart",
      "on_screen_text": "沪深300",
      "material_brief": {
        "kind": "chart",
        "subject": "沪深300一年走势",
        "rights_requirement": "owned_or_generated"
      },
      "transition": "cut"
    }
  ]
}
```

---

# 13. Subtitle Schema v1

```json
[
  {
    "start_ms": 0,
    "end_ms": 2200,
    "text": "AI Agent 真正改变的不是写作。",
    "speaker": "host",
    "style": "default"
  }
]
```

---

# 14. Provider Contracts

建议新增：

```text
apps/api/app/services/content_harness/video/contracts.py
apps/api/app/services/content_harness/video/providers.py
apps/api/app/services/content_harness/video/tts.py
apps/api/app/services/content_harness/video/avatar.py
apps/api/app/services/content_harness/video/generation.py
apps/api/app/services/content_harness/video/render.py
apps/api/app/services/content_harness/video/rules.py
apps/api/app/services/content_harness/video/nodes.py
```

---

# 14.1 TTSProvider

```python
class TTSProvider(Protocol):
    key: str
    version: str

    def capability(self) -> ProviderCapability:
        ...

    def synthesize(
        self,
        *,
        text: str,
        voice_profile: VoiceProfileVersion,
        request: TTSRequest,
    ) -> MaterialRevision:
        ...
```

---

# 14.2 DigitalHumanProvider

```python
class DigitalHumanProvider(Protocol):
    key: str
    version: str

    def capability(self) -> ProviderCapability:
        ...

    def generate(
        self,
        *,
        avatar: AvatarProfileVersion,
        audio_material: MaterialRevision,
        request: AvatarRenderRequest,
    ) -> MaterialRevision:
        ...
```

---

# 14.3 VideoGenerationProvider

```python
class VideoGenerationProvider(Protocol):
    key: str
    version: str

    def capability(self) -> ProviderCapability:
        ...

    def generate(
        self,
        brief: VideoGenerationBrief,
    ) -> MaterialRevision:
        ...
```

---

# 14.4 VideoRenderProvider

```python
class VideoRenderProvider(Protocol):
    key: str
    version: str

    def render(
        self,
        *,
        timeline: TimelineRevision,
        resolved_materials: list[MaterialRevision],
        output: RenderSpec,
    ) -> VideoRenderResult:
        ...
```

---

# 14.5 BlobStore

```python
class BlobStore(Protocol):
    key: str

    def put(
        self,
        *,
        source_path: Path,
        content_hash: str,
        mime_type: str,
    ) -> BlobRef:
        ...

    def open(self, ref: BlobRef) -> BinaryIO:
        ...

    def stat(self, ref: BlobRef) -> BlobStat:
        ...

    def delete(self, ref: BlobRef) -> None:
        ...

    def signed_url(self, ref: BlobRef, ttl_seconds: int) -> str | None:
        ...
```

Provider：

```text
blob.local@1
blob.s3@1
blob.s3_compatible@1
```

---

# 15. Provider Descriptor

```python
@dataclass(frozen=True)
class ProviderDescriptor:
    key: str
    version: str
    kind: str

    capabilities: frozenset[str]
    side_effects: frozenset[str]

    config_schema: dict
```

Capability 示例：

```json
{
  "key": "avatar.example",
  "version": "1",
  "capabilities": [
    "digital_human.talking_head"
  ],
  "max_duration_ms": 300000,
  "supported_aspect_ratios": ["9:16", "16:9"],
  "supports_idempotency": false,
  "supports_status_poll": true
}
```

---

# 16. Workflow Node Plugins

注册：

```text
node.video.strategy@1
node.video.script@1
node.video.storyboard@1
node.video.material_plan@1
node.video.material_resolve@1
node.video.tts@1
node.video.avatar@1
node.video.timeline@1
node.video.subtitle@1
node.video.render@1
node.video.qc@1
node.video.thumbnail@1
node.video.discoverability@1
```

这些 Node 使用现有：

```text
Node Registry
WorkflowRun
WorkflowStep
WorkflowStepAttempt
```

禁止单独建设 VideoWorkflowRun。

---

# 17. NodeResult 扩展

建议：

```python
@dataclass
class EntityRef:
    entity_type: str
    entity_id: int | str
    revision_id: int | None = None
    content_hash: str | None = None


@dataclass
class NodeResult:
    status: str
    output_refs: list[EntityRef]
    context_patch: dict
    usage: dict | None = None
    warnings: list[dict] | None = None
```

Node 之间主要传：

```text
EntityRef
```

不传 binary。

---

# 18. Workflow Context V2

```json
{
  "video": {
    "project_id": 12,
    "script_revision_id": 20,
    "storyboard_revision_id": 25,
    "timeline_revision_id": 30,
    "subtitle_revision_id": 31,
    "preview_render_id": 40,
    "final_render_id": 41
  }
}
```

---

# 19. Short Video Workflow

```text
content_core
→ video_strategy
→ short_script
→ script_fact_check
→ storyboard
→ material_plan
→ material_resolve
→ tts
→ avatar(optional)
→ timeline_compose
→ subtitle
→ preview_render
→ video_rules
→ thumbnail
→ discoverability_post
→ human_review
→ final_render
→ final_qc
→ candidate
```

---

# 20. Long Video Workflow

```text
content_core
→ research_gap_check
→ video_strategy
→ outline
→ script
→ script_fact_check
→ chapters
→ storyboard
→ material_plan
→ material_resolve
→ voice
→ screen/demo_material
→ timeline
→ subtitle
→ preview
→ human_review
→ final_render
→ qc
→ thumbnail
→ video_seo
→ final_review
→ candidate
```

---

# 21. Digital Human Workflow

```text
content_core
→ script
→ fact_check
→ tts
→ avatar_render
→ supporting_material
→ timeline
→ subtitle
→ preview
→ qc
→ human_review
→ final_render
```

---

# 22. Staleness Graph

## Script Changed

```text
Storyboard stale
Material Plan stale
TTS stale
Timeline stale
Subtitle stale
Render stale
QC stale
Candidate invalid
```

## B-roll Replaced

```text
Script valid
Storyboard valid
TTS valid
Timeline stale
Render stale
QC stale
Candidate invalid
```

## Voice Changed

```text
TTS stale
Avatar clip stale if dependent
Timeline stale
Render stale
QC stale
Candidate invalid
```

## Subtitle Text Changed

```text
Timeline maybe valid
Subtitle revision new
Burned-in render stale
QC stale
Candidate invalid
```

## Description/Tags Changed

```text
Video bytes valid
Discoverability updated
Candidate invalid
```

---

# 23. Scene Rerun

Existing Workflow rerun APIs extend scope：

```http
POST /api/v1/workflow-runs/{run_id}/steps/{step_id}/rerun
```

Payload：

```json
{
  "scope": {
    "scene_key": "scene_004"
  }
}
```

支持 scene scope 的 Node 执行局部逻辑。

不支持的 Node：

```text
422 scope_not_supported
```

---

# 24. Render Idempotency

Render request hash：

```text
timeline_hash
+
render_profile_hash
+
provider_key
+
provider_version
+
segment range
```

相同 successful render：

```text
允许复用
```

记录：

```text
cache_hit=true
```

---

# 25. Provider Job Safety

远端操作流程：

```text
create ProviderJob(status=prepared)
COMMIT
↓
call remote provider
↓
running / remote_job_id
↓
poll
↓
succeeded / failed / unknown
```

timeout：

```text
unknown
```

没有 idempotency/status query 时禁止自动重发。

---

# 26. Celery Queues

修改：

```text
apps/api/app/tasks/celery_app.py
```

目标：

```text
default
llm
media
render
publisher
```

示意：

```python
task_routes = {
    "app.tasks.video_tasks.generate_video_script": {"queue": "llm"},
    "app.tasks.video_tasks.generate_storyboard": {"queue": "llm"},

    "app.tasks.video_tasks.generate_tts": {"queue": "media"},
    "app.tasks.video_tasks.generate_avatar_clip": {"queue": "media"},
    "app.tasks.video_tasks.generate_video_material": {"queue": "media"},

    "app.tasks.video_tasks.render_video": {"queue": "render"},

    "app.tasks.delivery_tasks.execute_delivery": {"queue": "publisher"},
}
```

开发环境允许一个 worker 消费多 queue。

---

# 27. Task Modules

推荐从现有：

```text
worker_tasks.py
```

逐步拆：

```text
tasks/
  celery_app.py
  worker_tasks.py          # compatibility / generic
  video_tasks.py
  provider_tasks.py
  delivery_tasks.py
```

Celery task name 必须稳定。

---

# 28. API Surface

# 28.1 Video Project

```http
POST /api/v1/topics/{topic_id}/video-projects
GET  /api/v1/topics/{topic_id}/video-projects
GET  /api/v1/video-projects/{project_id}
PATCH /api/v1/video-projects/{project_id}
```

Create：

```json
{
  "channel": "bilibili",
  "content_form": "long_video",
  "aspect_ratio": "16:9",
  "target_duration_ms": 600000,
  "workflow_key": "workflow.bilibili.long_video"
}
```

---

# 28.2 Script

```http
POST /api/v1/video-projects/{id}/scripts
GET  /api/v1/video-projects/{id}/scripts
POST /api/v1/video-projects/{id}/scripts/{revision_id}/clone
```

禁止更新历史 revision。

---

# 28.3 Storyboard

```http
POST /api/v1/video-projects/{id}/storyboards/generate
POST /api/v1/video-projects/{id}/storyboards
GET  /api/v1/video-projects/{id}/storyboards
GET  /api/v1/storyboards/{id}
```

---

# 28.4 Scene

```http
GET  /api/v1/video-projects/{id}/scenes
POST /api/v1/video-projects/{id}/scenes/{scene_key}/rerun
POST /api/v1/video-projects/{id}/scenes/{scene_key}/materials
```

---

# 28.5 Timeline

```http
POST /api/v1/video-projects/{id}/timelines
GET  /api/v1/video-projects/{id}/timelines
GET  /api/v1/timelines/{timeline_id}
POST /api/v1/timelines/{timeline_id}/clone
```

V2 第一版前端本地编辑整份：

```text
composition_json
```

Save 时创建新 TimelineRevision。

---

# 28.6 Render

```http
POST /api/v1/video-projects/{id}/renders
GET  /api/v1/video-projects/{id}/renders
GET  /api/v1/video-renders/{render_id}
POST /api/v1/video-renders/{render_id}/cancel
```

Payload：

```json
{
  "kind": "segment",
  "timeline_revision_id": 10,
  "start_ms": 12000,
  "end_ms": 26000
}
```

---

# 28.7 Subtitle

```http
GET  /api/v1/video-projects/{id}/subtitles
POST /api/v1/video-projects/{id}/subtitles
POST /api/v1/video-projects/{id}/subtitles/generate
```

---

# 28.8 Provider

```http
GET /api/v1/video-providers
GET /api/v1/video-providers/capabilities
```

不得返回 Secret。

---

# 28.9 Voice Profiles

```http
GET  /api/v1/voice-profiles
POST /api/v1/voice-profiles
POST /api/v1/voice-profiles/{profile_key}/versions
GET  /api/v1/voice-profiles/{profile_key}/versions
```

---

# 28.10 Avatar Profiles

```http
GET  /api/v1/avatar-profiles
POST /api/v1/avatar-profiles
POST /api/v1/avatar-profiles/{profile_key}/versions
GET  /api/v1/avatar-profiles/{profile_key}/versions
```

---

# 29. Review Center V2 Projection

`routers/review_center.py` 扩展 target：

```json
{
  "artifact_kind": "video",
  "video": {
    "project": {},
    "script": {},
    "storyboard": {},
    "timeline": {},
    "subtitle": {},
    "preview_render": {},
    "final_render": {},
    "thumbnail": {}
  },
  "checks": [],
  "discoverability": {},
  "candidate": {},
  "delivery": []
}
```

不创建 ReviewCenter 表。

---

# 30. Video Candidate Manifest v3

```json
{
  "schema_version": 3,
  "artifact_kind": "video",
  "content_form": "short_video",

  "source": {
    "topic_id": 1,
    "mother_revision_id": 3,
    "fact_pack_id": 9,
    "fact_pack_checksum": "..."
  },

  "video": {
    "project_id": 8,
    "script_revision_id": 12,
    "storyboard_revision_id": 14,
    "timeline_revision_id": 20,

    "final_render_id": 31,
    "video_material_revision_id": 900,

    "content_hash": "...",
    "duration_ms": 58400,
    "width": 1080,
    "height": 1920,
    "fps": 30
  },

  "audio": {
    "voice_profile_key": "voice.main",
    "voice_profile_version": 2,
    "material_revision_ids": [801]
  },

  "avatar": {
    "profile_key": "avatar.main",
    "profile_version": 1
  },

  "subtitle": {
    "revision_id": 66,
    "text_hash": "...",
    "burned_in": true
  },

  "thumbnail": {
    "material_revision_id": 903,
    "hash": "..."
  },

  "discoverability": {
    "report_id": 50,
    "title": "...",
    "description": "...",
    "tags": [],
    "chapters": []
  },

  "materials": [],

  "checks": [],

  "execution": {
    "workflow_key": "...",
    "workflow_version": 1,
    "plugins": []
  },

  "rights": {}
}
```

---

# 31. Candidate Hash

Hash 必须覆盖：

```text
final video content hash
thumbnail hash
title
description
tags
chapters
subtitle hash/payload
public declarations
rights snapshot
platform/content form
workflow/plugin versions
```

Publisher 获得的 package 必须能反推出同一批准 Candidate。

---

# 32. Video Rules

至少注册：

```text
rule.video.render_exists
rule.video.duration_valid
rule.video.resolution_valid
rule.video.aspect_ratio
rule.video.no_missing_material
rule.video.no_stale_clip
rule.video.subtitle_present
rule.video.subtitle_timing
rule.video.subtitle_safe_area
rule.video.audio_present
rule.video.audio_quality
rule.video.thumbnail_present
rule.video.description_present
rule.video.rights_ready
rule.video.avatar_authorized
rule.video.voice_authorized
rule.video.fact_consistency
rule.video.seo_ready
```

---

# 33. Video Ready Gate

## Content Ready

- Script current；
- 必填字段完整；
- 无内容 blocker。

## Evidence Ready

- Fact checks current；
- 关键事实与 FactPack 一致。

## Material Ready

- 所有必要素材存在；
- 无 placeholder；
- Rights 通过。

## Composition Ready

- Timeline current；
- 所有 clip material 可解析；
- 无 stale Scene。

## Audio Ready

- 需要音频时实际 audio material 存在。

## Avatar Ready

若 Workflow 要求：

- profile current；
- consent valid；
- channel allowed。

## Render Ready

- Final Render succeeded；
- output material exists；
- hash verified。

## QC Ready

- 无 blocker。

## SEO Ready

如果 profile required：

- Discoverability report current。

## Delivery Ready

- Platform renderer 可以生成完整发布包。

---

# 34. Video Discoverability

继续：

```text
DiscoverabilityProfileVersion
DiscoverabilityReport
```

Video Post Report：

```json
{
  "title_candidates": [],
  "description": "",
  "primary_queries": [],
  "entities": [],
  "tags": [],
  "thumbnail_copy": [],
  "chapters": [],
  "transcript_keywords": [],
  "issues": []
}
```

SEO 修改后：

```text
Candidate invalid
```

---

# 35. Delivery V2

继续使用：

```text
DeliveryTarget
DeliveryAttempt
DeliveryReceipt
```

Video Copy Package：

```text
video.mp4
thumbnail.jpg
title.txt
description.txt
tags.txt
chapters.txt
subtitle.srt
manifest.json
publish-guide.md
```

---

# 36. Assisted Video Delivery

自动化可执行：

```text
upload video
upload thumbnail
fill title
fill description
fill tags
save draft
```

默认停在草稿/提交确认前。

公开发布需要独立 verified capability。

---

# 37. Platform Video Profiles

Channel Profile 增加：

```json
{
  "channel": "bilibili",
  "content_forms": {
    "long_video": {
      "artifact_kind": "video",
      "workflow_key": "workflow.bilibili.long_video",
      "renderer": "renderer.video.bilibili",
      "discoverability_profile": "seo.bilibili.video",
      "rule_sets": [
        "rules.video.base",
        "rules.bilibili.video"
      ],
      "publisher_candidates": []
    }
  }
}
```

首批推荐：

```text
bilibili.long_video
xiaohongshu.short_video
douyin.short_video
```

---

# 38. Frontend Architecture

新增：

```text
VideoWorkspace.tsx
```

布局：

```text
┌──────────────┬───────────────────────────┬───────────────┐
│ Scenes       │ Player / Canvas           │ Inspector     │
│ Storyboard   │                           │ Material      │
│              │                           │ Voice         │
│              │                           │ Avatar        │
│              │                           │ Subtitle      │
├──────────────┴───────────────────────────┴───────────────┤
│ Timeline                                                   │
└────────────────────────────────────────────────────────────┘
```

审批仍进入：

```text
ReviewPublish.tsx
```

---

# 39. Frontend Components

```text
components/video/
  VideoPreview.tsx
  VideoTimeline.tsx
  TimelineTrack.tsx
  TimelineClip.tsx
  SceneList.tsx
  SceneEditor.tsx
  StoryboardPanel.tsx
  SubtitleEditor.tsx
  AudioPanel.tsx
  AvatarPanel.tsx
  MaterialPicker.tsx
  VideoChecksPanel.tsx
  VideoSeoPanel.tsx
  VideoRenderPanel.tsx
```

---

# 40. Timeline Editor V2 Scope

必须支持：

- Scene list；
- Track view；
- Clip start/end；
- Material replace；
- Reorder；
- Subtitle editing；
- Avatar selection；
- Text overlay basic editing；
- Preview；
- Save Timeline Revision。

不要求：

- Keyframe curves；
- Mask editor；
- Professional transition graph；
- Color grading suite。

---

# 41. Materials UI V2

`Materials.tsx` 增加：

```text
image
video
audio
music
sfx
avatar_asset
subtitle
thumbnail
```

Detail 增加：

```text
duration
technical metadata
transcript
derived_from
used_by timeline
rights
```

---

# 42. Settings V2

新增：

```text
Video Providers
TTS Providers
Digital Human Providers
Render Providers
Blob Storage
Voice Profiles
Avatar Profiles
```

前端只显示：

```text
configured / unconfigured
capabilities
status
```

不显示 Secret。

---

# 43. Security

## Upload

必须：

- MIME sniff；
- max size；
- content hash；
- 禁止只信扩展名。

## Remote Material

必须：

- SSRF 防护；
- scheme allowlist；
- timeout；
- size limit；
- content type 校验；
- 下载后落 BlobStore。

## FFmpeg

必须：

```python
subprocess.run(args, shell=False)
```

禁止用户输入直接进入 shell command。

## Secrets

禁止写入：

```text
Candidate
ProviderJob metadata
Workflow definition
Frontend response
```

---

# 44. Rights

视频 Candidate 中所有外部媒体必须检查：

```text
public_use_allowed
```

商业账号配置要求时：

```text
commercial_use_allowed
```

Avatar：

```text
consent_ref
```

Voice：

```text
rights_status
```

任一 required right 缺失：

```text
blocker
```

---

# 45. Backward Compatibility

V2 必须保证：

- V1 Text/Image 全部正常；
- Candidate Manifest v2 可读；
- Candidate Manifest v3 可读；
- V1 Material file_path 可继续读取；
- V1 Workflow schema 可继续解析；
- V1 ReviewPublish 继续工作；
- V1 DeliveryTarget / Receipt 不迁移伪造新字段；
- 不把抖音 script package 自动迁移成 VideoProject；
- 不给旧 Material 自动补 rights=true。

Candidate reader：

```python
if schema_version == 2:
    read_v2_text_image_candidate()
elif schema_version == 3:
    read_multimodal_candidate()
```

---

# 46. Alembic Plan

## Migration V2-A — `add_video_core_domain`

新增：

```text
video_project
video_script_revision
storyboard_revision
video_scene
timeline_revision
subtitle_track_revision
```

---

## Migration V2-B — `add_video_media_profiles`

新增：

```text
material_derivation
voice_profile_version
avatar_profile_version
```

扩：

```text
material_revision.storage_provider
material_revision.storage_key
material_revision.technical_metadata_json
material_revision.transcript_text
```

---

## Migration V2-C — `add_video_runtime_jobs`

新增：

```text
provider_job
video_render
execution_usage
```

---

## Migration V2-D — `generalize_artifact_checks`

只有确定 V1 DraftCheckRun 无法复用时才执行。

目标：

```text
ArtifactCheckRun
```

或 additive 泛化字段。

禁止为了形式统一而破坏 V1 已运行检查。

---

# PART III — CAPABILITY SPECS

# 47. Capability: video-domain-model

## ADDED Requirements

### Requirement: VideoProject reuses existing content root

系统 SHALL 在 Topic / MotherRevision 下创建 VideoProject，MUST NOT 创建独立的视频 Topic / FactPack 真源。

#### Scenario: 从现有 Topic 创建 B站长视频

- **WHEN** editor 从 Topic 创建 `bilibili.long_video`
- **THEN** VideoProject 记录原 topic_id 与 mother_revision_id
- **AND** FactPack 继续来自原 Topic
- **AND** 不创建第二份事实集合

---

### Requirement: Video script is immutable by revision

系统 MUST 通过 VideoScriptRevision 保存脚本历史，MUST NOT 原地覆盖被历史 Workflow 或 Candidate 引用的脚本。

#### Scenario: 用户修改脚本

- **WHEN** 用户保存修改后的脚本
- **THEN** 创建新的 `revision_no`
- **AND** 旧 revision 保持不变
- **AND** downstream 根据依赖标 stale

---

### Requirement: Storyboard and Timeline are distinct revisions

系统 SHALL 分离 StoryboardRevision 与 TimelineRevision。

#### Scenario: 用户只替换视频素材

- **WHEN** Storyboard 语义不变但 Timeline 中替换一个素材
- **THEN** StoryboardRevision 保持 current
- **AND** 创建新的 TimelineRevision
- **AND** Render / Candidate 失效

---

# 48. Capability: video-composition-timeline

## ADDED Requirements

### Requirement: Timeline is the render source of truth

Video render MUST 绑定明确 TimelineRevision 与 timeline_hash。

#### Scenario: 请求 final render

- **WHEN** 用户对 timeline revision 12 请求 final render
- **THEN** VideoRender 保存 timeline_revision_id=12
- **AND** input_hash 包含 timeline_hash 与 render profile
- **AND** 后续 TimelineRevision 13 不改变该 Render 的 provenance

---

### Requirement: Scene supports scoped rerun

系统 SHALL 支持对声明 scene-scope capability 的 Node 仅重跑指定 scene_key。

#### Scenario: 重做 scene_004 的 AI B-roll

- **WHEN** 用户对 scene_004 选择 Rerun Scene
- **THEN** 不重新执行无关 Scene
- **AND** 新素材保存为新 MaterialRevision
- **AND** 新 TimelineRevision 引用新素材
- **AND** Preview/Final Render stale
- **AND** Candidate invalid

---

### Requirement: Segment rendering is supported

Render Provider SHALL 支持 segment render 或明确声明 capability unavailable。

#### Scenario: 长视频只预览 12s–26s

- **WHEN** 用户提交 start_ms=12000/end_ms=26000
- **THEN** 系统创建 render_kind=segment
- **AND** 不要求生成 full final render

---

# 49. Capability: video-material-derivation

## ADDED Requirements

### Requirement: All generated video assets enter Material Library

TTS、AI Video、Digital Human、Render 输出 MUST 以 MaterialRevision 持久化。

#### Scenario: TTS 成功

- **WHEN** TTS Provider 返回音频
- **THEN** 系统计算 content hash
- **AND** 存入 BlobStore
- **AND** 创建 `MaterialRevision(kind=audio)`
- **AND** 不只保存临时文件路径

---

### Requirement: Material derivation is traceable

系统 SHALL 保存关键媒体派生关系。

#### Scenario: 数字人视频由音频生成

- **WHEN** Avatar Provider 以 audio revision 80 生成 video revision 90
- **THEN** MaterialDerivation 保存 source=80/output=90/operation=avatar_render
- **AND** 记录 provider key/version

---

# 50. Capability: video-provider-runtime

## ADDED Requirements

### Requirement: Provider resolution is registry based

Video workflow MUST 通过 Provider Registry 解析 TTS/Avatar/VideoGen/Render Provider。

#### Scenario: 替换 TTS Provider

- **WHEN** Workflow 新版本从 `tts.a@1` 切换到 `tts.b@2`
- **THEN** 历史 WorkflowRun 仍保留 `tts.a@1`
- **AND** 新 Run 才使用 `tts.b@2`

---

### Requirement: Missing required capability blocks preflight

缺失 Required Provider MUST 在 Workflow 开始前阻断。

#### Scenario: Digital Human workflow 未配置 Avatar Provider

- **WHEN** 用户启动必须使用 Avatar 的 Workflow
- **THEN** preflight 返回 blocked/capability_unavailable
- **AND** 不运行到一半才失败

---

### Requirement: Remote provider unknown is not blind-retried

#### Scenario: AI Video Provider timeout

- **WHEN** 请求已提交但远端结果不可确认
- **THEN** ProviderJob status=unknown
- **AND** 系统不自动创建第二个远端任务
- **AND** 用户通过 reconcile/status query 后再决定 retry

---

# 51. Capability: video-rendering

## ADDED Requirements

### Requirement: Preview and final renders are distinct

#### Scenario: 用户在审核前生成 Preview

- **WHEN** 请求 preview
- **THEN** 创建 `VideoRender(render_kind=preview)`
- **AND** preview bytes 不自动成为 final Candidate video

---

### Requirement: Final render bytes are immutable candidate input

#### Scenario: Final Render 成功

- **WHEN** render_kind=final succeeded
- **THEN** 输出创建 MaterialRevision
- **AND** candidate manifest 冻结该 content_hash
- **AND** Approval 后不得替换该 bytes 而保留原 Candidate Hash

---

### Requirement: Identical render request can reuse successful render

#### Scenario: 同 Timeline 再次点击 Final Render

- **WHEN** timeline_hash/render_profile/provider/version 完全一致
- **THEN** 系统可以复用已成功 Render
- **AND** 必须标记 cache/reuse provenance

---

# 52. Capability: video-tts-voice

## ADDED Requirements

### Requirement: Voice Profile is versioned

#### Scenario: 修改语速和声音

- **WHEN** admin 修改 Voice Profile 配置
- **THEN** 创建新 Version
- **AND** 历史视频继续绑定旧 Version

---

### Requirement: Voice rights gate candidate readiness

#### Scenario: 克隆声音缺少授权

- **WHEN** Video Candidate 使用 rights_status 不满足要求的 Voice Profile
- **THEN** `rule.video.voice_authorized` 返回 blocker
- **AND** Candidate 不得 Ready

---

# 53. Capability: video-digital-human

## ADDED Requirements

### Requirement: Avatar Profile stores authorization

Avatar profile MUST 保存 owner / consent / channel restrictions。

#### Scenario: Avatar 不允许用于抖音

- **WHEN** allowed_channels 不含 douyin 且目标是 douyin
- **THEN** Avatar rule blocker
- **AND** 不调用远端 Avatar Provider

---

### Requirement: Digital human is optional for ordinary video

#### Scenario: 没有 Avatar Provider

- **WHEN** 用户创建普通 B站技术视频
- **THEN** Workflow 可以正常完成
- **AND** 只有 requires_avatar 的 Workflow 被阻断

---

# 54. Capability: video-checks-rights

## ADDED Requirements

### Requirement: Video candidate must contain no stale required dependency

#### Scenario: 替换一段 B-roll 后未重渲

- **WHEN** TimelineRevision 已更新而 final render 仍来自旧 Timeline
- **THEN** video render/check status stale
- **AND** Candidate Ready 被阻断

---

### Requirement: Public rights are mandatory for published materials

#### Scenario: Web 搜索素材 rights 未确认

- **WHEN** Timeline 引用 public_use_allowed != true 的 MaterialRevision
- **THEN** rights check blocker
- **AND** Final Candidate 不可批准

---

### Requirement: Video QC is deterministic where possible

尺寸、时长、缺文件、字幕 timing、rights、render existence MUST 优先由确定性 Rule 检查，不以 LLM Review 作为唯一判断。

---

# 55. Capability: video-candidate-approval

## ADDED Requirements

### Requirement: Candidate schema v3 freezes complete video payload

#### Scenario: reviewer approves video

- **WHEN** reviewer approves
- **THEN** manifest 包含 final video hash、thumbnail、subtitle、SEO、timeline/script/storyboard provenance、rights、checks、plugins
- **AND** Candidate Hash 对 canonical manifest 计算

---

### Requirement: Candidate approval is invalidated by public payload changes

#### Scenario: 改了 description

- **WHEN** approved 前/后 title、description、tags、thumbnail、subtitle 或 final video bytes 任一变化
- **THEN** 生成新 Candidate
- **AND** 旧 Approval 不得复用于新 Candidate

---

# 56. Capability: video-discoverability

## ADDED Requirements

### Requirement: Video SEO uses existing Discoverability system

系统 MUST 复用 DiscoverabilityProfileVersion / DiscoverabilityReport，不创建第二个 SEO 状态系统。

#### Scenario: B站长视频生成 Post SEO

- **WHEN** final video metadata 已准备
- **THEN** 生成 DiscoverabilityReport
- **AND** 报告可含 title/description/tags/thumbnail_copy/chapters/transcript_keywords
- **AND** report 与 input hash 绑定

---

# 57. Capability: video-review-publish-center

## ADDED Requirements

### Requirement: Video review is a projection of existing entities

#### Scenario: 打开 Video Target

- **WHEN** 用户从 Review & Publish Center 打开一个 video target
- **THEN** 页面聚合 project/script/storyboard/timeline/render/subtitle/thumbnail/checks/SEO/candidate/delivery
- **AND** 不创建第二套 approval/delivery state

---

### Requirement: Reviewer sees final video payload

#### Scenario: reviewer 准备批准

- **WHEN** Candidate Ready
- **THEN** reviewer 可以看到 final render、thumbnail、title、description、tags、subtitle、chapters、rights、checks
- **AND** Approval 对应的就是之后 Delivery 使用的 payload

---

# 58. Capability: video-delivery

## ADDED Requirements

### Requirement: Video uses existing DeliveryTarget

#### Scenario: 创建 B站视频交付

- **WHEN** approved Video Candidate 创建 delivery target
- **THEN** 使用现有 DeliveryTarget/Attempt/Receipt
- **AND** 不创建 VideoPublishJob 作为第二套发布状态

---

### Requirement: Copy Package preserves full approved payload

#### Scenario: 平台无自动上传能力

- **WHEN** action=copy_package
- **THEN** package 至少包含 video、thumbnail、title、description、tags、chapters、subtitle、manifest、guide
- **AND** 文件 hashes 与 approved candidate 一致

---

### Requirement: Publisher cannot mutate approved media

#### Scenario: 平台要求不同编码

- **WHEN** 当前 approved video bytes 不符合平台要求
- **THEN** Publisher MUST reject
- **AND** 系统回到 Platform Render → New Candidate → Re-approve
- **AND** Publisher 不得在交付时偷偷转码后沿用旧 Candidate Hash

---

# PART IV — IMPLEMENTATION TASKS

# 59. Phase 0 — Baseline & Change Scaffold

- [ ] 0.1 读取当前 `git status` / `git diff`，不 reset 用户改动。
- [ ] 0.2 确认 V1 `align-v1-prd2-content-harness` 状态、当前 migration head、现有测试基线。
- [ ] 0.3 创建 `openspec/changes/add-v2-video-content-harness/`。
- [ ] 0.4 投影 proposal/design/specs/tasks。
- [ ] 0.5 `openspec validate add-v2-video-content-harness --strict`。
- [ ] 0.6 运行 backend full baseline。
- [ ] 0.7 运行 `ruff check app/ tests/`。
- [ ] 0.8 运行 web build。
- [ ] 0.9 记录命令级 baseline evidence 到 `tasks.md`。

---

# 60. Phase 1 — Video Core Domain

- [ ] 1.1 `models.py` 新增 VideoProject。
- [ ] 1.2 新增 VideoScriptRevision。
- [ ] 1.3 新增 StoryboardRevision。
- [ ] 1.4 新增 VideoScene。
- [ ] 1.5 新增 TimelineRevision。
- [ ] 1.6 新增 SubtitleTrackRevision。
- [ ] 1.7 Migration V2-A。
- [ ] 1.8 新建 `services/video/projects.py`。
- [ ] 1.9 新建 `services/video/scripts.py`。
- [ ] 1.10 新建 `services/video/storyboard.py`。
- [ ] 1.11 新建 `services/video/composition.py`。
- [ ] 1.12 新建 `services/video/subtitles.py`。
- [ ] 1.13 新建 `routers/video_projects.py`。
- [ ] 1.14 新建 `routers/video_composition.py`。
- [ ] 1.15 `main.py` 注册 routers。
- [ ] 1.16 新增 unit tests。
- [ ] 1.17 fresh SQLite migration。
- [ ] 1.18 V1 DB → V2-A stepwise migration。

验收：

```text
Topic
→ VideoProject
→ Script Revision
→ Storyboard Revision
→ Timeline Revision
```

可完全用 Mock / 手工 JSON 跑通。

---

# 61. Phase 2 — Material V2 + BlobStore

- [ ] 2.1 `Material.kind` 支持 video/audio/music/sfx/avatar_asset/subtitle/thumbnail。
- [ ] 2.2 MaterialRevision 增 storage_provider/storage_key/technical_metadata/transcript。
- [ ] 2.3 新增 MaterialDerivation。
- [ ] 2.4 新增 VoiceProfileVersion。
- [ ] 2.5 新增 AvatarProfileVersion。
- [ ] 2.6 Migration V2-B。
- [ ] 2.7 新建 `services/blob_store.py` protocol。
- [ ] 2.8 实现 `blob.local@1`。
- [ ] 2.9 预留 S3 provider contract。
- [ ] 2.10 materials service 支持 audio/video bytes。
- [ ] 2.11 raw/download path 同时兼容 file_path 和 storage_key。
- [ ] 2.12 `Materials.tsx` 增 video/audio filter 和 detail。
- [ ] 2.13 测试 content hash / derivation / rights / local BlobStore。

验收：

```text
上传 mp4/wav
→ MaterialRevision
→ content hash
→ BlobStore
→ UI 可查看 metadata
```

---

# 62. Phase 3 — Video Provider Runtime

- [ ] 3.1 新建 video provider contracts。
- [ ] 3.2 Provider Registry 支持 tts/avatar/video_gen/render/blob。
- [ ] 3.3 新增 ProviderJob。
- [ ] 3.4 新增 ExecutionUsage。
- [ ] 3.5 Migration V2-C（部分）。
- [ ] 3.6 实现 MockTTSProvider。
- [ ] 3.7 实现 MockAvatarProvider。
- [ ] 3.8 实现 MockVideoGenerationProvider。
- [ ] 3.9 实现 MockVideoRenderProvider。
- [ ] 3.10 preflight capability resolve。
- [ ] 3.11 unknown/reconcile contract。
- [ ] 3.12 Provider secrets 不出 API。
- [ ] 3.13 provider registry tests。
- [ ] 3.14 provider job idempotency tests。

验收：

```text
Provider missing → start 前 blocker
Provider timeout → unknown
unknown → no blind retry
```

---

# 63. Phase 4 — Workflow Video Nodes

- [ ] 4.1 注册 node.video.strategy@1。
- [ ] 4.2 注册 node.video.script@1。
- [ ] 4.3 注册 node.video.storyboard@1。
- [ ] 4.4 注册 node.video.material_plan@1。
- [ ] 4.5 注册 node.video.material_resolve@1。
- [ ] 4.6 注册 node.video.tts@1。
- [ ] 4.7 注册 node.video.avatar@1。
- [ ] 4.8 注册 node.video.timeline@1。
- [ ] 4.9 注册 node.video.subtitle@1。
- [ ] 4.10 注册 node.video.render@1。
- [ ] 4.11 注册 node.video.qc@1。
- [ ] 4.12 注册 node.video.thumbnail@1。
- [ ] 4.13 注册 node.video.discoverability@1。
- [ ] 4.14 NodeResult 支持 output_refs/usage。
- [ ] 4.15 Workflow context 保存 video IDs。
- [ ] 4.16 Short Video default workflow。
- [ ] 4.17 Long Video default workflow。
- [ ] 4.18 Digital Human workflow。
- [ ] 4.19 preflight tests。
- [ ] 4.20 workflow full mock integration。

---

# 64. Phase 5 — Scene Rerun + Video Staleness

- [ ] 5.1 扩 `staleness.py` 视频依赖图。
- [ ] 5.2 Script changed stale propagation。
- [ ] 5.3 Material replaced stale propagation。
- [ ] 5.4 Voice changed stale propagation。
- [ ] 5.5 Subtitle changed stale propagation。
- [ ] 5.6 Discoverability public metadata changed stale propagation。
- [ ] 5.7 Workflow rerun payload 支持 scene scope。
- [ ] 5.8 unsupported scope 返回 422。
- [ ] 5.9 Scene output cache。
- [ ] 5.10 WorkflowStepAttempt 保存 scoped execution metadata。
- [ ] 5.11 staleness tests。
- [ ] 5.12 scene rerun tests。

---

# 65. Phase 6 — Local Render / FFmpeg

- [ ] 6.1 新增 VideoRender model。
- [ ] 6.2 完成 Migration V2-C 剩余部分。
- [ ] 6.3 实现 `render.ffmpeg@1`。
- [ ] 6.4 禁止 shell=True。
- [ ] 6.5 Resolve Timeline materials 到 temp job dir。
- [ ] 6.6 Preview Render。
- [ ] 6.7 Segment Render。
- [ ] 6.8 Final Render。
- [ ] 6.9 output hash。
- [ ] 6.10 output → BlobStore → MaterialRevision。
- [ ] 6.11 MaterialDerivation 记录 render。
- [ ] 6.12 render input hash / cache reuse。
- [ ] 6.13 worker crash cleanup。
- [ ] 6.14 VideoRender progress。
- [ ] 6.15 render golden test。
- [ ] 6.16 segment render test。
- [ ] 6.17 idempotency test。

验收：

```text
Timeline
→ real mp4
→ content hash
→ MaterialRevision
```

---

# 66. Phase 7 — Queue Split

- [ ] 7.1 Celery 增 `media` queue。
- [ ] 7.2 增 `render` queue。
- [ ] 7.3 增 `publisher` queue 或记录 defer reason。
- [ ] 7.4 新建 video_tasks.py。
- [ ] 7.5 大 payload 禁止进入 Celery。
- [ ] 7.6 render task 只传 render_id。
- [ ] 7.7 provider task 只传 ProviderJob/entity IDs。
- [ ] 7.8 queue routing tests。
- [ ] 7.9 单 worker multi-queue dev 配置。
- [ ] 7.10 docker/README 更新。

---

# 67. Phase 8 — TTS

- [ ] 8.1 Voice Profile CRUD。
- [ ] 8.2 TTS Provider contract。
- [ ] 8.3 Mock TTS integration。
- [ ] 8.4 至少一个真实 TTS Provider adapter。
- [ ] 8.5 Preview TTS。
- [ ] 8.6 TTS output MaterialRevision。
- [ ] 8.7 MaterialDerivation。
- [ ] 8.8 rights gate。
- [ ] 8.9 ExecutionUsage。
- [ ] 8.10 TTS golden test。
- [ ] 8.11 real provider manual validation。

---

# 68. Phase 9 — Digital Human

- [ ] 9.1 Avatar Profile CRUD。
- [ ] 9.2 consent / rights fields。
- [ ] 9.3 DigitalHumanProvider contract。
- [ ] 9.4 Mock Avatar Provider。
- [ ] 9.5 至少一个真实 Provider adapter（如可用）。
- [ ] 9.6 provider job status polling。
- [ ] 9.7 output → MaterialRevision。
- [ ] 9.8 MaterialDerivation。
- [ ] 9.9 allowed_channels gate。
- [ ] 9.10 avatar optional workflow test。
- [ ] 9.11 unauthorized avatar blocker test。
- [ ] 9.12 real provider validation 非 Core blocker。

---

# 69. Phase 10 — Subtitle + QC + Rules

- [ ] 10.1 Subtitle generate。
- [ ] 10.2 Subtitle manual edit revision。
- [ ] 10.3 timing check。
- [ ] 10.4 safe area profile。
- [ ] 10.5 audio existence / basic quality。
- [ ] 10.6 render exists。
- [ ] 10.7 duration/resolution/aspect ratio。
- [ ] 10.8 missing/stale material。
- [ ] 10.9 thumbnail rule。
- [ ] 10.10 rights rule。
- [ ] 10.11 avatar auth rule。
- [ ] 10.12 voice auth rule。
- [ ] 10.13 fact consistency aggregation。
- [ ] 10.14 video SEO ready rule。
- [ ] 10.15 如需 ArtifactCheckRun，执行 Migration V2-D。
- [ ] 10.16 rule tests。

---

# 70. Phase 11 — Video Discoverability + Thumbnail

- [ ] 11.1 Seed Bilibili video SEO profile。
- [ ] 11.2 Seed short video profile。
- [ ] 11.3 Post report 增 title/description/tags/chapters/thumbnail_copy/transcript keywords。
- [ ] 11.4 Video thumbnail workflow。
- [ ] 11.5 Thumbnail 复用 Image Material。
- [ ] 11.6 SEO apply 创建新的 metadata/candidate source revision，不静默改 Approved Candidate。
- [ ] 11.7 Discoverability tests。
- [ ] 11.8 Candidate invalidation tests。

---

# 71. Phase 12 — Candidate Manifest v3

- [ ] 12.1 candidates.py 支持 schema v3。
- [ ] 12.2 v2 reader 保持不变。
- [ ] 12.3 video source provenance。
- [ ] 12.4 timeline/script/storyboard refs。
- [ ] 12.5 final video hash。
- [ ] 12.6 subtitle。
- [ ] 12.7 thumbnail。
- [ ] 12.8 voice/avatar profiles。
- [ ] 12.9 rights snapshot。
- [ ] 12.10 checks。
- [ ] 12.11 discoverability。
- [ ] 12.12 workflow/plugins。
- [ ] 12.13 canonical hash tests。
- [ ] 12.14 video bytes change → hash change。
- [ ] 12.15 description change → hash change。
- [ ] 12.16 thumbnail change → hash change。

---

# 72. Phase 13 — VideoWorkspace Frontend

- [ ] 13.1 `pages/VideoWorkspace.tsx`。
- [ ] 13.2 `api/video.ts`。
- [ ] 13.3 VideoPreview。
- [ ] 13.4 SceneList。
- [ ] 13.5 StoryboardPanel。
- [ ] 13.6 VideoTimeline。
- [ ] 13.7 TimelineClip。
- [ ] 13.8 MaterialPicker。
- [ ] 13.9 SubtitleEditor。
- [ ] 13.10 AudioPanel。
- [ ] 13.11 AvatarPanel。
- [ ] 13.12 VideoRenderPanel。
- [ ] 13.13 save Timeline Revision。
- [ ] 13.14 Scene rerun。
- [ ] 13.15 Preview render polling。
- [ ] 13.16 stale UI。
- [ ] 13.17 frontend build。

---

# 73. Phase 14 — Review & Publish V2

- [ ] 14.1 review_center.py 聚合 video projection。
- [ ] 14.2 ReviewPublish artifact_kind=video。
- [ ] 14.3 Final video player。
- [ ] 14.4 Thumbnail preview。
- [ ] 14.5 Subtitle preview。
- [ ] 14.6 SEO panel。
- [ ] 14.7 Rights panel。
- [ ] 14.8 QC panel。
- [ ] 14.9 Workflow timeline。
- [ ] 14.10 Candidate Ready gate。
- [ ] 14.11 Approve candidate v3。
- [ ] 14.12 video review projection tests。

---

# 74. Phase 15 — Video Delivery

- [ ] 15.1 Video renderer/package contract。
- [ ] 15.2 Copy Package。
- [ ] 15.3 package manifest hash verification。
- [ ] 15.4 Bilibili renderer profile。
- [ ] 15.5 XHS short video renderer profile。
- [ ] 15.6 Douyin renderer profile。
- [ ] 15.7 Assisted upload provider contract。
- [ ] 15.8 至少一个平台真实 assisted/auto draft 验证。
- [ ] 15.9 unknown delivery no retry。
- [ ] 15.10 delivery regression。

---

# 75. Phase 16 — Platform Profiles

首批：

```text
bilibili.long_video
xiaohongshu.short_video
douyin.short_video
```

- [ ] 16.1 Channel Profiles。
- [ ] 16.2 Workflow definitions。
- [ ] 16.3 Rule Sets。
- [ ] 16.4 SEO Profiles。
- [ ] 16.5 Renderer。
- [ ] 16.6 Copy Package。
- [ ] 16.7 golden cases。
- [ ] 16.8 capability status 明确 verified/unverified。

---

# 76. Phase 17 — Acceptance / Docs

- [ ] 17.1 README 更新。
- [ ] 17.2 HANDOVER 更新。
- [ ] 17.3 North Star / V2 PRD 链接。
- [ ] 17.4 Workflow Canvas 文档视频扩展说明。
- [ ] 17.5 BlobStore runbook。
- [ ] 17.6 render worker runbook。
- [ ] 17.7 provider credential runbook。
- [ ] 17.8 backup / restore 涵盖 object storage。
- [ ] 17.9 real provider validation notes。
- [ ] 17.10 final OpenSpec strict validation。

---

# PART V — C2C CONTROL BATCHES

# 77. C2C 批次

建议 Codex 严格按以下批次推进，不跨批次修改同一基础对象。

```text
C2C-V2-01
Video Domain + Migration A

C2C-V2-02
Material V2 + BlobStore + Migration B

C2C-V2-03
Provider Runtime + ProviderJob + Migration C

C2C-V2-04
Workflow Video Nodes + Staleness

C2C-V2-05
Local Render + Queue Split

C2C-V2-06
TTS + Voice Profile

C2C-V2-07
Digital Human + Avatar Rights

C2C-V2-08
Subtitle + QC + Video Rules

C2C-V2-09
Discoverability + Thumbnail

C2C-V2-10
Candidate Manifest v3

C2C-V2-11
VideoWorkspace

C2C-V2-12
Review & Publish Video Projection

C2C-V2-13
Video Delivery + Platform Profiles

C2C-V2-14
Acceptance + Docs
```

每一批次必须：

```text
IMPLEMENTED
→ git diff review
→ targeted tests
→ full relevant regression
→ C2C EXECUTED handoff
```

下一批才开始。

---

# 78. C2C Message Contract

每个批次开始：

```text
[C2C START]
change: add-v2-video-content-harness
batch: C2C-V2-XX
goal:
files:
invariants:
tests:
```

完成：

```text
[C2C EXECUTED]
batch:
changed:
migrations:
tests:
commands:
known_deviations:
next_expected_step:
```

如果 blocked：

```text
[C2C BLOCKED]
batch:
reason:
evidence:
safe_next_step:
```

---

# PART VI — ACCEPTANCE

# 79. Core Acceptance

## Video Domain

- [ ] VideoProject 可创建。
- [ ] Script 历史 Revision 不覆盖。
- [ ] Storyboard Revision 不覆盖。
- [ ] Timeline Revision 不覆盖。
- [ ] Scene 可稳定寻址。
- [ ] Subtitle Revision 不覆盖。

## Material

- [ ] Video/Audio Material 可保存。
- [ ] content hash 正确。
- [ ] BlobStore 可读取。
- [ ] MaterialDerivation 可追溯。
- [ ] 大文件不进入 DB JSON。
- [ ] Rights 可阻断 Candidate。

## Runtime

- [ ] Provider Registry 可解析。
- [ ] required capability 缺失在 preflight blocker。
- [ ] ProviderJob unknown 不自动 retry。
- [ ] Provider Secret 不泄漏。

## Composition

- [ ] Timeline 可保存。
- [ ] Clip 引用 MaterialRevision。
- [ ] Scene 可局部重跑。
- [ ] Downstream stale 正确。
- [ ] Segment render 可执行。

## Render

- [ ] Preview 成功。
- [ ] Final 成功。
- [ ] Final output = MaterialRevision。
- [ ] input hash 幂等。
- [ ] 相同 render 可安全复用。
- [ ] FFmpeg 无 shell injection。

## TTS

- [ ] Voice Profile versioned。
- [ ] TTS 输出真实 audio material。
- [ ] rights gate。
- [ ] 至少一个真实 Provider 验证。

## Avatar

- [ ] Avatar Profile versioned。
- [ ] consent gate。
- [ ] channel restriction。
- [ ] 无 Avatar Provider 不阻塞普通视频。
- [ ] 至少一个实验 Provider 验证或记录 capability unavailable。

## Subtitle / QC

- [ ] Subtitle editable。
- [ ] timing check。
- [ ] Render exists。
- [ ] duration/resolution/aspect ratio。
- [ ] stale clip blocker。
- [ ] rights blocker。
- [ ] voice/avatar blocker。
- [ ] fact consistency。

## Candidate

- [ ] schema v3。
- [ ] final video hash 被冻结。
- [ ] thumbnail 被冻结。
- [ ] subtitle 被冻结。
- [ ] SEO 被冻结。
- [ ] rights snapshot 被冻结。
- [ ] workflow/plugin versions 被冻结。
- [ ] Approval 绑定 hash。

## Review

- [ ] Final video 可播放。
- [ ] Reviewer 看得到实际发布字段。
- [ ] 修改后 Candidate invalid。
- [ ] 不存在第二 Review 状态表。

## Delivery

- [ ] 复用 DeliveryTarget。
- [ ] Copy Package 完整。
- [ ] Package 与 Candidate hash 一致。
- [ ] Publisher 不修改 approved bytes。
- [ ] unknown 不 blind retry。

---

# 80. Golden Acceptance

至少四组。

## G1 — AI 观点 60 秒短视频

```text
9:16
60 sec
Script
Storyboard
TTS
Subtitle
Timeline
Preview
Final
Thumbnail
SEO
Candidate
Copy Package
```

## G2 — A 股复盘数字人

```text
FactPack
Market data
Chart
Voice
Avatar
Subtitle
Risk
Rights
Final Render
```

## G3 — 技术长视频

```text
16:9
Chapters
Long Script
Screenshot / Demo material
Timeline
Subtitle
Bilibili SEO
```

## G4 — 混合素材

```text
Upload
Web material
AI image
Chart
Generated video
Avatar
```

验证 Material Graph 和 Rights。

---

# 81. Regression Acceptance

必须保证：

- [ ] 公众号文章链路正常。
- [ ] 小红书图卡正常。
- [ ] 雪球文章正常。
- [ ] 掘金文章正常。
- [ ] X Thread 正常。
- [ ] Candidate Manifest v2 可读。
- [ ] V1 Approval 正常。
- [ ] V1 Delivery 正常。
- [ ] Material Library V1 图片正常。
- [ ] Discoverability V1 正常。
- [ ] Workflow schema v1/v2 兼容。

---

# 82. Migration Gates

必须运行：

```text
fresh SQLite → head
V1 current head → V2 head
PostgreSQL → V2 head
```

禁止：

- 伪造旧 VideoProject；
- 伪造旧 video candidate；
- 伪造 rights；
- 把 script 自动变成 video；
- 修改历史 Candidate Manifest。

---

# 83. Code Quality Gates

最终至少：

```bash
cd apps/api
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m ruff check app/ tests/

cd ../web
npm run build

openspec validate add-v2-video-content-harness --strict

git diff --check
```

如果仓库有额外 typecheck / migration smoke 命令，也必须加入。

---

# 84. Real Capability Gates

Mock 通过不代表真实能力 verified。

分别记录：

```text
TTS Provider
Digital Human Provider
Video Generation Provider
Render Provider
Bilibili Delivery
XHS Video Delivery
Douyin Delivery
```

状态：

```text
unconfigured
experimental
tested
verified
degraded
disabled
```

只有真实账号/真实 Provider 走完闭环才能：

```text
verified
```

---

# PART VII — IMPLEMENTATION INVARIANTS

# 85. 不变量

1. 视频事实继续受 FactPack 约束。
2. 历史 Revision 不覆盖。
3. Script / Storyboard / Timeline 不混为一个 mutable blob。
4. Video/Audio 使用统一 Material Library。
5. TTS / Avatar / VideoGen / Render 是 Provider。
6. 数字人不是普通视频必选项。
7. Scene / Segment 必须支持局部工作。
8. Final Render bytes 必须进入 Candidate Hash。
9. Thumbnail / Subtitle / Description / Tags 属于 Candidate。
10. Rights 未满足不得 Candidate Ready。
11. Voice / Avatar 授权未满足不得发布。
12. Review Center 不建第二套状态。
13. Delivery 继续使用 DeliveryTarget/Attempt。
14. Publisher 不修改批准媒体。
15. 远端 unknown 不盲目重试。
16. Binary 不进入 DB JSON / Workflow Context / Celery payload。
17. 插件版本在 WorkflowRun 中冻结。
18. V2 不破坏 V1。
19. 新视频平台原则上不改 Workflow Engine。
20. 新视频供应商原则上只增加 Provider Adapter。

---

# 86. Out-of-scope Deferred Items

明确延后：

```text
Professional keyframe editor
CRDT multi-user timeline
3D compositing
Automatic copyright clearance
Automatic public publish without human authorization
Full mobile editing
AI music generation mainline
Voice cloning product UX
Professional color grading
Live streaming
Real-time avatar
Multi-language auto dubbing pipeline
```

这些能力未来仍应通过相同 Plugin/Artifact 模型扩展。

---

# 87. Rollback Strategy

V2 所有 schema 变更以 additive 为主。

如果视频功能暂时下线：

```text
disable video channel content forms
disable video providers
stop media/render queues
hide VideoWorkspace navigation
```

V1 Text/Image 系统继续运行。

禁止为了 rollback 删除历史：

```text
VideoProject
TimelineRevision
MaterialRevision
ProviderJob
Candidate
```

---

# 88. Observability

每一个最终 Video Candidate 必须可以回答：

```text
Topic?
FactPack?
MotherRevision?
VideoProject?
Script revision?
Storyboard revision?
Timeline revision?
Materials?
Voice profile?
Avatar profile?
TTS provider?
Video provider?
Render provider?
Subtitle?
Thumbnail?
Discoverability report?
Rules?
Workflow version?
Plugin versions?
Final video hash?
Reviewer?
Delivery target?
Receipt?
```

这是 V2 完成的关键标准之一。

---

# 89. Final Success Definition

V2 不以：

> “接通一个 AI 视频 API”

为成功。

真正成功条件：

> **一个 Topic 能够在已有 Content Harness 上产生真实 VideoArtifact：脚本、分镜、素材、声音、可选数字人、Timeline、字幕、封面、SEO、最终视频全部版本化并可追溯；用户可以局部修改和重跑；Review & Publish Center 能审核真实最终载荷；Candidate Hash 冻结最终视频 bytes；Delivery 使用现有安全交付体系；V1 文、图能力不被破坏。**

---

# 90. Codex NEXT_EXPECTED_STEP

```text
CHANGE
add-v2-video-content-harness

NEXT_EXPECTED_STEP
1. 创建 openspec/changes/add-v2-video-content-harness/
2. 将本文件拆投影为 proposal.md / design.md / tasks.md / capability specs
3. 运行 openspec strict validation
4. 读取当前 git status/diff，不 reset
5. 记录当前 migration head 和 backend/web 门禁基线
6. 只实施 C2C-V2-01：Video Domain + Migration A
7. 完成后输出 C2C EXECUTED，停在下一个批次边界

DO NOT
- 一次性实现全部 V2
- 新建第二套 Review/Delivery/Material/Workflow
- 接真实付费 Provider 作为第一批次前置
- 修改 V1 历史 Candidate
- 传大 binary 到 DB/Celery/context
- 自动发布 public content
```
