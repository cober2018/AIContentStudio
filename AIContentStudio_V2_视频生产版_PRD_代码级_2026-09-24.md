# AI Content Studio V2 视频生产版 PRD（代码级）

> 产品：AIContentStudio  
> 文档类型：V2 正式产品需求文档 / 代码级实施蓝图  
> 版本：V2 PRD 1.0  
> 日期：2026-09-24  
> 上位文档：`AIContentStudio 完整产品战略与架构 North Star（图 / 文 / 视）`  
> 前置基线：`AIContentStudio V1 PRD 2.0 — Text + Image Content Harness Foundation`  
> V2 主题：**Video & Multimodal Production**  
> 核心原则：**新增 Video Domain，复用 V1 Content Harness、Material Library、Review & Publish Center、Candidate、Approval、Delivery，不建设第二套视频内容系统。**

---

# 0. 文档定位

本 PRD 用于直接指导 AIContentStudio V2 视频版本的产品设计、OpenSpec 拆解和 Codex 实施。

它不是概念蓝图，而是代码级产品规格。

V2 的目标不是“给 V1 增加一个 AI 视频按钮”，而是在 V1 已经建立的 Content Harness 上正式增加第三种一级 Artifact：

```text
TextArtifact
ImageArtifact
VideoArtifact   ← V2
```

V2 完成后，AIContentStudio 应真正成为：

> **图 / 文 / 视一体化的 AI 内容生产、审核与分发中心。**

---

# 1. 当前 V1 代码基线

V2 必须基于现有实现增量开发，禁止重新实现已有基础设施。

当前仓库已经存在：

```text
apps/api/app/models.py
  MotherRevision
  DraftMedia
  Material
  MaterialRevision
  DiscoverabilityProfileVersion
  DiscoverabilityReport
  ContentAsset
  DeliveryTarget
  DeliveryAttempt
  Workflow
  WorkflowRun
  WorkflowStep
```

当前 Content Harness：

```text
apps/api/app/services/content_harness/
  registry.py
  contracts.py
  channel_registry.py
  providers.py
  renderers.py
  rules.py
  seo_rules.py
  domain_rules.py
  staleness.py
  skill_runtime.py
  nodes/
  publishers/
```

当前 API 已存在：

```text
routers/materials.py
routers/discoverability.py
routers/review_center.py
routers/delivery.py
routers/workflows.py
routers/channels.py
```

当前前端已存在：

```text
apps/web/src/pages/
  Materials.tsx
  ReviewPublish.tsx
  Workflows.tsx
  Workspace.tsx
  Topics.tsx
  Assets.tsx
  Settings.tsx
```

当前异步任务基础：

```text
apps/api/app/tasks/
  celery_app.py
  worker_tasks.py
```

因此 V2 的架构策略是：

```text
复用：
Evidence
Material
Workflow
Plugin Registry
Candidate
Approval
Delivery
Review Center

新增：
Video Composition
Storyboard
Scene
Timeline
Audio
TTS
Digital Human
Video Rendering
Video QC
Video SEO
```

---

# 2. V2 产品目标

V2 必须支持完整视频生产闭环：

```text
Topic / Content Core
       ↓
Video Strategy
       ↓
Script
       ↓
Storyboard
       ↓
Scene / Shot Plan
       ↓
Material Planning
       ↓
素材搜索 / 上传 / AI生成 / 图表 / 截图
       ↓
TTS / Voice
       ↓
Digital Human（可选）
       ↓
Timeline Composition
       ↓
Subtitle
       ↓
Render
       ↓
Video QC
       ↓
Thumbnail
       ↓
Video SEO
       ↓
Review & Publish Center
       ↓
Immutable Video Candidate
       ↓
Approval
       ↓
Auto / Assisted / Copy Package
```

---

# 3. V2 内容范围

## 3.1 Short Video

典型：

- 抖音；
- 小红书视频；
- B站竖屏短视频；
- 微博视频；
- X 视频；
- Shorts/Reels 类未来扩展。

典型长度：

```text
15s
30s
60s
90s
3min
```

不把时长写死进领域模型。

---

## 3.2 Long Video

典型：

- B站长视频；
- YouTube 类未来渠道；
- 技术演示；
- 深度知识；
- 量化研究讲解；
- AI 产品教程；
- 项目复盘。

---

## 3.3 Digital Human Video

场景：

```text
口播
新闻播报
A股复盘
产品介绍
技术说明
知识解读
```

数字人只是 Video Workflow 中一个可选 Provider。

---

## 3.4 Screen / Demo Video

适合：

- 软件演示；
- AI 工具教程；
- Coding；
- 数据平台演示；
- 量化系统展示。

V2 允许 Screen Recording 作为 Material 输入，不强制 V2 自动完成浏览器录屏。

---

# 4. V2 非目标

V2 不要求：

- 专业 NLE 级别视频编辑器替代 Premiere / Final Cut；
- 任意关键帧动画系统；
- 3D 动画；
- 多人实时协作编辑；
- 电影级调色；
- 自动购买版权素材；
- 自动判断肖像权合法性；
- 自动无人审批公开发布；
- 自研基础 Video Diffusion Model；
- 自研 TTS；
- 自研 Digital Human Model。

AIContentStudio 做：

```text
Control Plane
Composition
Workflow
Version
Review
Provider Orchestration
Delivery
```

底层生成能力由 Provider 插件完成。

---

# 5. V2 核心领域模型

V2 不新增第二套 Content Root。

继续：

```text
TopicBrief
→ MotherRevision / Content Core
→ WorkflowRun
```

新增以下视频领域对象：

```text
VideoProject
VideoScriptRevision
StoryboardRevision
VideoScene
TimelineRevision
TimelineClip
AudioTrackRevision
SubtitleTrackRevision
VideoRender
VideoCheckRun
VideoCandidate
```

其中最终批准仍然落入现有：

```text
ContentAsset
approved_candidate_hash
candidate_manifest_json
```

不要增加：

```text
VideoApprovedAsset
VideoDeliveryTarget
```

这种重复对象。

---

# 6. 数据模型：VideoProject

建议新增到：

```text
apps/api/app/models.py
```

模型：

```python
class VideoProject(Base):
    __tablename__ = "video_project"

    id: Mapped[int] = mapped_column(primary_key=True)

    topic_brief_id: Mapped[int] = mapped_column(
        ForeignKey("topic_brief.id"),
        index=True,
    )

    mother_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("mother_revision.id"),
        index=True,
    )

    channel: Mapped[str] = mapped_column(String(30), index=True)

    content_form: Mapped[str] = mapped_column(String(50))
    # short_video / long_video / digital_human / demo_video

    aspect_ratio: Mapped[str] = mapped_column(String(20))
    # 9:16 / 16:9 / 1:1 ...

    target_duration_ms: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(30), default="draft")
    # draft / producing / needs_review / ready / archived

    workflow_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("workflow_run.id")
    )

    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

职责：

> 代表一次具体视频 Artifact 生产项目。

不是最终成片。

---

# 7. VideoScriptRevision

脚本必须独立版本化。

```python
class VideoScriptRevision(Base):
    __tablename__ = "video_script_revision"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"),
        index=True,
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

`structured_json` 示例：

```json
{
  "hook": "...",
  "sections": [
    {
      "id": "sec_01",
      "narration": "...",
      "on_screen_text": "...",
      "intent": "explain"
    }
  ],
  "cta": "..."
}
```

---

# 8. StoryboardRevision

Storyboard 不等于 Timeline。

Storyboard 是语义规划。

```python
class StoryboardRevision(Base):
    __tablename__ = "storyboard_revision"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"),
        index=True,
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

Storyboard JSON 示例：

```json
{
  "schema_version": 1,
  "scenes": [
    {
      "scene_key": "scene_001",
      "order": 1,
      "duration_ms": 6000,
      "narration": "过去一年...",
      "visual_intent": "market_chart",
      "material_brief": {
        "kind": "chart",
        "subject": "沪深300一年走势",
        "rights_requirement": "owned_or_generated"
      },
      "on_screen_text": "沪深300",
      "transition": "cut"
    }
  ]
}
```

---

# 9. VideoScene

Storyboard 中的 Scene 应有稳定 ID，方便局部重跑。

```python
class VideoScene(Base):
    __tablename__ = "video_scene"

    id: Mapped[int] = mapped_column(primary_key=True)

    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"),
        index=True,
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

Unique：

```text
(video_project_id, storyboard_revision_id, scene_key)
```

---

# 10. TimelineRevision

Timeline 才是最终视频 Composition 真源。

```python
class TimelineRevision(Base):
    __tablename__ = "timeline_revision"

    id: Mapped[int] = mapped_column(primary_key=True)

    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id"),
        index=True,
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

# 11. Timeline Composition Schema

V2 必须定义稳定 schema。

示例：

```json
{
  "schema_version": 1,
  "canvas": {
    "width": 1080,
    "height": 1920,
    "fps": 30
  },
  "tracks": [
    {
      "track_id": "video_main",
      "kind": "video",
      "clips": []
    },
    {
      "track_id": "avatar",
      "kind": "video",
      "clips": []
    },
    {
      "track_id": "voice",
      "kind": "audio",
      "clips": []
    },
    {
      "track_id": "caption",
      "kind": "subtitle",
      "clips": []
    },
    {
      "track_id": "overlay",
      "kind": "overlay",
      "clips": []
    }
  ]
}
```

Clip：

```json
{
  "clip_id": "clip_001",
  "scene_key": "scene_001",
  "start_ms": 0,
  "duration_ms": 5500,
  "material_revision_id": 123,
  "source_in_ms": 0,
  "source_out_ms": 5500,
  "transform": {
    "x": 0,
    "y": 0,
    "scale": 1.0,
    "crop": null
  }
}
```

---

# 12. Material Library V2 扩展

V1 `Material` / `MaterialRevision` 必须直接复用。

扩展 `Material.kind` 支持：

```text
image
video
audio
chart
screenshot
subtitle
thumbnail
avatar_asset
music
sfx
```

不要新建：

```text
VideoMaterial
AudioMaterial
```

除非有确切无法抽象的业务属性。

---

# 13. MaterialRevision V2 扩展字段

建议 additive migration 增加：

```python
codec: Mapped[str | None]
container_format: Mapped[str | None]

sample_rate: Mapped[int | None]
audio_channels: Mapped[int | None]

fps: Mapped[float | None]

bitrate: Mapped[int | None]

transcript_text: Mapped[str | None] = mapped_column(Text)

technical_metadata_json: Mapped[dict | None] = mapped_column(JSON)
```

大部分媒体技术元信息可先保存在：

```text
technical_metadata_json
```

避免过早拆太多列。

---

# 14. Material Derivation

新增素材派生关系表：

```python
class MaterialDerivation(Base):
    __tablename__ = "material_derivation"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_revision_id: Mapped[int] = mapped_column(
        ForeignKey("material_revision.id")
    )

    output_revision_id: Mapped[int] = mapped_column(
        ForeignKey("material_revision.id")
    )

    operation: Mapped[str] = mapped_column(String(50))
    # crop / extract_frame / tts / avatar / render / transcode ...

    provider_key: Mapped[str | None] = mapped_column(String(150))
    provider_version: Mapped[str | None] = mapped_column(String(50))

    config_json: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

形成：

> Media Graph。

---

# 15. TTS / Voice Profile

新增版本化 Voice Profile。

```python
class VoiceProfileVersion(Base):
    __tablename__ = "voice_profile_version"

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

Unique：

```text
(profile_key, version)
```

---

# 16. TTS Provider Contract

新增：

```text
apps/api/app/services/content_harness/video/
    tts.py
```

接口：

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

`TTSRequest`：

```python
@dataclass
class TTSRequest:
    language: str | None
    speed: float = 1.0
    style: str | None = None
    expected_duration_ms: int | None = None
```

TTS 返回：

```text
MaterialRevision(kind=audio)
```

不是临时文件路径。

---

# 17. Digital Human Profile

新增：

```python
class AvatarProfileVersion(Base):
    __tablename__ = "avatar_profile_version"

    id: Mapped[int] = mapped_column(primary_key=True)

    profile_key: Mapped[str] = mapped_column(String(150))
    version: Mapped[int] = mapped_column(Integer)

    name: Mapped[str] = mapped_column(String(200))

    avatar_kind: Mapped[str] = mapped_column(String(30))
    # authorized_real / virtual / brand_character

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

# 18. Digital Human Provider Contract

新增：

```text
apps/api/app/services/content_harness/video/avatar.py
```

接口：

```python
class DigitalHumanProvider(Protocol):
    key: str
    version: str

    def generate(
        self,
        *,
        avatar: AvatarProfileVersion,
        audio_material: MaterialRevision,
        request: AvatarRenderRequest,
    ) -> MaterialRevision:
        ...
```

输出必须是：

```text
MaterialRevision(kind=video)
```

并写 MaterialDerivation：

```text
audio
avatar source
→ generated video
```

---

# 19. Video Generation Provider

对于 AI B-roll / Text-to-Video：

```python
class VideoGenerationProvider(Protocol):
    key: str
    version: str

    def generate(
        self,
        brief: VideoGenerationBrief,
    ) -> MaterialRevision:
        ...
```

`VideoGenerationBrief`：

```text
prompt
negative_prompt
duration_ms
aspect_ratio
reference_material_ids
style
seed
rights_requirement
```

V2 不绑定具体供应商。

---

# 20. Video Render Provider

最终 Timeline 渲染单独抽象。

文件：

```text
services/content_harness/video/render.py
```

接口：

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
    ) -> "VideoRenderResult":
        ...
```

可以有：

```text
render.ffmpeg
render.remotion
render.external.xxx
```

V2 推荐优先实现：

```text
FFmpeg-based deterministic renderer
```

或者已有技术栈更适合时接外部 Render Provider。

---

# 21. VideoRender 模型

```python
class VideoRender(Base):
    __tablename__ = "video_render"

    id: Mapped[int] = mapped_column(primary_key=True)

    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id")
    )

    timeline_revision_id: Mapped[int] = mapped_column(
        ForeignKey("timeline_revision.id")
    )

    render_kind: Mapped[str] = mapped_column(String(30))
    # preview / final / segment

    segment_start_ms: Mapped[int | None] = mapped_column(Integer)
    segment_end_ms: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(30))
    # queued/running/succeeded/failed/canceled

    provider_key: Mapped[str] = mapped_column(String(150))
    provider_version: Mapped[str | None] = mapped_column(String(50))

    input_hash: Mapped[str] = mapped_column(String(64))

    output_material_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("material_revision.id")
    )

    error: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

同一个：

```text
timeline_revision_id + input_hash + render_kind
```

应具备幂等查重。

---

# 22. Subtitle Track

字幕是成品组成部分，不只是视频文件烧录结果。

新增：

```python
class SubtitleTrackRevision(Base):
    __tablename__ = "subtitle_track_revision"

    id: Mapped[int] = mapped_column(primary_key=True)

    video_project_id: Mapped[int] = mapped_column(
        ForeignKey("video_project.id")
    )

    revision_no: Mapped[int] = mapped_column(Integer)

    language: Mapped[str] = mapped_column(String(20))

    format: Mapped[str] = mapped_column(String(20))
    # srt / vtt / internal

    cues_json: Mapped[list] = mapped_column(JSON)

    text_hash: Mapped[str] = mapped_column(String(64))

    source_kind: Mapped[str] = mapped_column(String(30))
    # script / asr / manual

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
```

---

# 23. 字幕 Cue Schema

```json
{
  "start_ms": 0,
  "end_ms": 2200,
  "text": "AI Agent 真正改变的不是写作。",
  "speaker": "host",
  "style": "default"
}
```

最终 Candidate 应冻结：

```text
字幕内容
字幕样式配置
是否烧录
外挂字幕文件 hash
```

---

# 24. Video SEO / Discoverability

复用 V1：

```text
DiscoverabilityProfileVersion
DiscoverabilityReport
```

新增视频 profile，不新增 VideoSEOReport。

视频 Discoverability 输出：

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

---

# 25. Video SEO 阶段

## Pre

进入 Script 前：

```text
Search Intent
Topic Gap
Query
Entity
Audience Intent
```

## Post

视频 Render 后：

```text
Title
Description
Tags
Thumbnail Copy
Chapters
Transcript
Caption
Entity Coverage
```

视频 SEO 修改公开字段后：

```text
Candidate invalid
```

---

# 26. Thumbnail

Thumbnail 属于 Image Artifact / Material。

不新增独立二进制模型。

但可新增关联：

```python
VideoProject.thumbnail_material_revision_id
```

或者放进 Candidate Manifest。

推荐：

> 不在 `VideoProject` 写 mutable thumbnail FK；让 Workflow 和 Candidate Manifest 冻结 thumbnail revision。

---

# 27. Video QC / Checks

复用：

```text
DraftCheckRun
Rule Registry
```

如果现有 DraftCheckRun 与 Draft 强绑定无法承载 Video Project，则 V2 应泛化，而不是新增 `VideoCheckRun` 第二套体系。

推荐升级方向：

```text
CheckRun
  target_type
  target_id
  check_kind
  profile_key
  input_hash
  status
  report_json
```

但为降低迁移风险，V2 可先新增：

```text
ArtifactCheckRun
```

后续统一。

本 PRD 推荐最终统一为通用 `ArtifactCheckRun`。

---

# 28. Video Rule Set

基础：

```text
video.render_exists
video.duration_valid
video.resolution_valid
video.aspect_ratio
video.no_missing_material
video.no_stale_clip
video.subtitle_present
video.subtitle_timing
video.subtitle_safe_area
video.audio_present
video.audio_peak
video.thumbnail_present
video.description_present
video.rights_ready
video.avatar_authorized
video.voice_authorized
video.fact_consistency
video.seo_ready
```

---

# 29. Audio QC

V2 deterministic rule 至少检测：

```text
audio exists
duration > 0
sample rate 可接受
峰值不过载
静音比例
音频长度与 Timeline 基本匹配
```

专业响度标准可以做 profile 配置，不强制一个固定 LUFS。

---

# 30. Video Rights Gate

Candidate Ready 前检查所有引用素材：

```text
public_use_allowed == true
```

如果内容用于商业账号且产品配置要求：

```text
commercial_use_allowed == true
```

还需要：

```text
music rights
avatar consent
voice consent
external footage attribution
```

---

# 31. Video Candidate Manifest v3

V1 Candidate Manifest v2 扩展为 schema v3。

示例：

```json
{
  "schema_version": 3,

  "artifact_kind": "video",
  "content_form": "short_video",

  "topic_id": 1,
  "mother_revision_id": 3,

  "video": {
    "project_id": 8,
    "script_revision_id": 12,
    "storyboard_revision_id": 14,
    "timeline_revision_id": 20,
    "final_render_id": 31,
    "video_material_revision_id": 900,
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

  "checks": [],

  "materials": [],

  "execution": {
    "workflow_key": "...",
    "workflow_version": 1,
    "plugins": []
  }
}
```

Candidate Hash 必须覆盖所有公开交付字段与最终二进制 hash。

---

# 32. Candidate Hash

视频 Candidate Hash 至少由以下内容构成：

```text
final video content hash
thumbnail hash
title
description
tags
chapters
subtitle payload/hash
platform content form
public declarations
rights snapshot
workflow/plugin versions
```

修改 Timeline 但最终 Render Hash 不变时，可以按实现策略决定 Candidate 是否变化。

推荐：

> Candidate Manifest 仍包含 Timeline Revision，因此生产 provenance 会变化；如果重新批准成本可接受，按新 Candidate 处理。

---

# 33. Workflow 扩展

V2 不改 Workflow Engine 核心逻辑。

增加 Node Plugin。

推荐新增：

```text
video.strategy
video.script
video.storyboard
video.material_plan
video.material_resolve
video.tts
video.avatar
video.timeline
video.subtitle
video.render
video.qc
video.thumbnail
video.discoverability
```

在：

```text
apps/api/app/services/content_harness/nodes/
```

注册。

---

# 34. Short Video Workflow

建议默认模板：

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
→ candidate
```

最终 Render 可以放 Human Review 前后两段：

```text
Preview Render
Human Review
Final Render
```

避免每次编辑都高成本 final render。

---

# 35. Long Video Workflow

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
→ screen/demo materials
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

长视频允许多个 Human Review Gate。

---

# 36. Digital Human Workflow

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

数字人不是整条视频的必选轨道。

可以：

```text
Scene 1 avatar
Scene 2 chart
Scene 3 screenshot
Scene 4 avatar
```

---

# 37. Scene-level Rerun

必须支持：

```text
Rerun Scene
```

语义：

1. 找到 scene_key；
2. 重跑目标 Node 的 scene output；
3. 创建新 Material Revision / Scene result；
4. TimelineRevision +1；
5. 只标记依赖该 Scene 的 downstream stale；
6. Preview Render stale；
7. Candidate invalid。

---

# 38. Segment Render

Render Provider 必须支持：

```text
preview full
final full
segment
```

API：

```text
POST /video-projects/{id}/renders
```

Payload：

```json
{
  "kind": "segment",
  "start_ms": 12000,
  "end_ms": 26000,
  "timeline_revision_id": 10
}
```

长视频局部审核不应强制每次全量渲染。

---

# 39. Staleness V2

扩展现有：

```text
services/content_harness/staleness.py
```

依赖示例：

```text
Script
↓
Storyboard
↓
Material Plan
↓
TTS
↓
Timeline
↓
Subtitle
↓
Render
↓
QC
↓
Candidate
```

脚本修改：

```text
Storyboard stale
TTS stale
Timeline stale
Subtitle stale
Render stale
QC stale
Candidate invalid
```

只换 B-roll：

```text
Script valid
TTS valid
Timeline stale
Render stale
QC stale
Candidate invalid
```

只改 Description：

```text
Render valid
SEO report stale/new
Candidate invalid
```

---

# 40. API 设计

新增 router：

```text
apps/api/app/routers/video_projects.py
apps/api/app/routers/video_composition.py
apps/api/app/routers/video_providers.py
```

避免一个 `video.py` 超大文件。

---

# 41. Video Project API

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

# 42. Script API

```http
POST /api/v1/video-projects/{id}/scripts
GET  /api/v1/video-projects/{id}/scripts
POST /api/v1/video-projects/{id}/scripts/{revision_id}/clone
```

禁止：

```text
PATCH 原历史 revision
```

编辑操作必须创建新 Revision。

---

# 43. Storyboard API

```http
POST /api/v1/video-projects/{id}/storyboards/generate
POST /api/v1/video-projects/{id}/storyboards
GET  /api/v1/video-projects/{id}/storyboards
GET  /api/v1/storyboards/{id}
```

手动修改 Storyboard：

```text
clone + new revision
```

---

# 44. Scene API

```http
GET  /api/v1/video-projects/{id}/scenes
POST /api/v1/video-projects/{id}/scenes/{scene_key}/rerun
POST /api/v1/video-projects/{id}/scenes/{scene_key}/materials
```

Material attach 应复用 Material Library。

---

# 45. Timeline API

```http
POST /api/v1/video-projects/{id}/timelines
GET  /api/v1/video-projects/{id}/timelines
GET  /api/v1/timelines/{timeline_id}
POST /api/v1/timelines/{timeline_id}/clone
POST /api/v1/timelines/{timeline_id}/clips
DELETE /api/v1/timelines/{timeline_id}/clips/{clip_id}
```

V2 第一版可使用：

> 整个 composition_json revision 写入

而不是每一次 drag 都立即写数据库。

前端编辑：

```text
local timeline state
→ Save
→ new TimelineRevision
```

降低 API 复杂度。

---

# 46. Provider API

Admin / Settings：

```http
GET /api/v1/video-providers
GET /api/v1/video-providers/capabilities
```

Provider Registry 输出：

```json
{
  "tts": [],
  "avatar": [],
  "video_generation": [],
  "video_render": []
}
```

不把 Secret 返回前端。

---

# 47. Render API

```http
POST /api/v1/video-projects/{id}/renders
GET  /api/v1/video-projects/{id}/renders
GET  /api/v1/video-renders/{render_id}
POST /api/v1/video-renders/{render_id}/cancel
```

Render 一律异步。

---

# 48. Subtitle API

```http
GET  /api/v1/video-projects/{id}/subtitles
POST /api/v1/video-projects/{id}/subtitles
POST /api/v1/video-projects/{id}/subtitles/generate
```

生成来源：

```text
script timing
TTS timing
ASR
manual
```

---

# 49. TTS API

通常不让普通用户直接调 Provider，而通过 Workflow。

高级调试：

```http
POST /api/v1/video-projects/{id}/tts/preview
```

只生成短 preview，防止成本浪费。

---

# 50. Avatar API

```http
GET  /api/v1/avatar-profiles
POST /api/v1/avatar-profiles
POST /api/v1/avatar-profiles/{id}/versions
GET  /api/v1/avatar-profiles/{id}/versions
```

实际数字人视频生产由 Workflow Node 调用。

---

# 51. Review Center V2

复用：

```text
routers/review_center.py
ReviewPublish.tsx
```

扩展 projection。

目标：

```json
{
  "artifact_kind": "video",
  "video": {
    "project": {},
    "script": {},
    "storyboard": {},
    "timeline": {},
    "preview_render": {},
    "final_render": {},
    "subtitle": {},
    "thumbnail": {}
  }
}
```

不要新建独立：

```text
VideoReviewCenter
```

---

# 52. 前端：ReviewPublish.tsx

V2 增加 artifact_kind 分支。

```tsx
if (target.artifact_kind === "video") {
  return <VideoReviewPanel ... />
}
```

推荐拆组件：

```text
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
```

不要把所有逻辑继续堆到 `ReviewPublish.tsx`。

---

# 53. 前端 Timeline V2 范围

V2 第一版 Timeline 编辑器支持：

- 查看 Tracks；
- Scene 顺序；
- Clip Start / End；
- 替换 Material；
- 调整 Clip 顺序；
- 开关 Track；
- 字幕编辑；
- 选择 Avatar；
- 调整简单文本 Overlay；
- Preview；
- Save Revision。

暂不要求：

- 高级 Keyframe；
- Curve Editor；
- 多层特效；
- 专业 Transition Editor。

---

# 54. 前端 Video Workspace

建议新页面：

```text
apps/web/src/pages/VideoWorkspace.tsx
```

路由：

```text
/video-projects/:id
```

布局：

```text
左：
Scenes / Storyboard

中：
Player / Canvas

下：
Timeline

右：
Inspector
- scene
- material
- voice
- avatar
- subtitle
- seo
```

最终审批仍进入：

```text
/review-publish
```

VideoWorkspace 是生产面。

ReviewPublish 是批准面。

---

# 55. Materials.tsx V2

增加筛选：

```text
image
video
audio
music
sfx
avatar
subtitle
```

详情增加：

```text
duration
fps
codec
sample rate
derived_from
transcript
usage in timeline
```

---

# 56. Settings.tsx V2

新增设置组：

```text
Video Providers
TTS Providers
Digital Human Providers
Render Providers
Voice Profiles
Avatar Profiles
```

Secret 继续后端保存。

前端只看到：

```text
configured: true
```

---

# 57. Workflow UI V2

Workflows 页面 Node Palette 增加：

```text
Video Strategy
Video Script
Storyboard
Material Plan
TTS
Digital Human
Timeline Compose
Subtitle
Video Render
Video QC
Thumbnail
Video SEO
```

V2 不要求这些节点全都允许普通用户随意拖拽。

默认模板优先。

---

# 58. Async Queue 设计

现有 Celery 应扩展队列。

当前已有：

```text
default
llm
```

V2 推荐：

```text
llm
media
render
publisher
default
```

职责：

```text
llm:
  script
  storyboard
  seo

media:
  image generation
  tts
  avatar
  video generation
  material processing

render:
  ffmpeg/remotion final rendering

publisher:
  remote side effects
```

如果当前 publisher 仍同步，可以单独作为后续批次，但 V2 最终建议拆开。

---

# 59. celery_app.py

新增 route：

```python
task_routes = {
    "...generate_*": {"queue": "llm"},
    "...tts_*": {"queue": "media"},
    "...avatar_*": {"queue": "media"},
    "...video_generate_*": {"queue": "media"},
    "...render_video": {"queue": "render"},
    "...execute_delivery*": {"queue": "publisher"},
}
```

部署时 worker 可以：

```text
worker-default
worker-llm
worker-media
worker-render
worker-publisher
```

V2 单机开发允许同一 worker 消费多个 queue。

---

# 60. worker_tasks.py

新增：

```python
generate_video_script(project_id, ...)
generate_storyboard(project_id, ...)
generate_tts(project_id, scene_key, ...)
generate_avatar_clip(project_id, scene_key, ...)
generate_video_material(project_id, scene_key, ...)
render_video(render_id)
run_video_qc(project_id, render_id)
```

Task 参数尽量传 ID。

禁止把：

```text
大正文
音频 bytes
视频 bytes
```

放进 Celery message。

---

# 61. Object Storage

V2 视频文件可能非常大。

不能继续默认所有媒体依赖本地相对路径作为长期生产架构。

需要新增：

```python
class BlobStore(Protocol):
    def put(...)
    def open(...)
    def stat(...)
    def delete(...)
    def signed_url(...)
```

Provider：

```text
blob.local
blob.s3
blob.s3_compatible
```

开发环境：

```text
local filesystem
```

生产：

```text
S3-compatible object storage
```

数据库保存：

```text
storage_key
content_hash
mime_type
metadata
```

而不是只依赖绝对文件路径。

---

# 62. MaterialRevision Storage Migration

建议逐步扩展：

```python
storage_provider: str | None
storage_key: str | None
file_path: str | None  # legacy / local compatible
```

读取顺序：

```text
storage_provider + storage_key
fallback file_path
```

避免一次性破坏 V1 数据。

---

# 63. Upload

视频 Upload 采用：

```text
multipart/chunk/resumable
```

V2 第一版至少支持：

- 普通 multipart 小文件；
- 大文件使用分块或直传对象存储。

阈值由配置决定。

不要让 FastAPI worker 长时间代理多 GB 文件作为唯一生产方案。

---

# 64. Render 临时文件

Render Worker 使用：

```text
job temp directory
```

流程：

```text
resolve Material
→ download/cache
→ render
→ hash output
→ BlobStore.put
→ create MaterialRevision
→ clean temp
```

任务失败也应清理临时目录。

---

# 65. Provider Registry V2

扩展：

```text
services/content_harness/providers.py
```

或者按视频域拆：

```text
services/content_harness/video/providers.py
```

注册：

```python
register_provider("tts.xxx", ...)
register_provider("avatar.xxx", ...)
register_provider("video_gen.xxx", ...)
register_provider("render.ffmpeg", ...)
```

Provider Descriptor：

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

---

# 66. Capability

Provider Capability 示例：

```json
{
  "key": "avatar.xxx",
  "capabilities": [
    "digital_human.talking_head"
  ],
  "max_duration_ms": 300000,
  "supported_aspect_ratios": ["9:16", "16:9"],
  "supports_idempotency": false,
  "supports_status_poll": true
}
```

Workflow 开始前先做 capability resolve。

缺 Provider 时：

```text
BLOCKED
```

而不是运行到一半才 ImportError。

---

# 67. Remote Provider Job

TTS / Avatar / Video Generation 往往异步。

新增通用：

```python
class ProviderJob(Base):
    __tablename__ = "provider_job"

    id
    provider_key
    provider_version
    operation
    local_entity_type
    local_entity_id

    idempotency_key
    remote_job_id

    status
    # prepared/running/succeeded/failed/unknown

    request_hash
    response_metadata_json
    error

    created_at
    started_at
    finished_at
```

这与 DeliveryAttempt 的思想一致，但 ProviderJob 用于内容生产侧。

---

# 68. Provider Job Unknown

远端生成 API timeout 后：

```text
unknown
```

不能盲目重复创建高成本 Video Job。

如果 Provider 有：

```text
status lookup
```

先 reconcile。

没有 lookup：

```text
人工选择 retry
```

---

# 69. 成本记录

V2 增加 Usage Ledger。

建议：

```python
class ExecutionUsage(Base):
    __tablename__ = "execution_usage"

    id
    workflow_run_id
    workflow_step_id

    provider_key
    operation

    usage_json
    currency
    cost_amount

    metadata_json
    created_at
```

usage：

```json
{
  "input_tokens": 1000,
  "output_tokens": 500,
  "generated_images": 1,
  "audio_seconds": 30,
  "video_seconds": 60,
  "render_seconds": 80
}
```

没有可验证价格时：

```text
cost_amount = null
```

不能估算成真值。

---

# 70. Workflow Node Contract

视频 Node 继续使用 V1 Node Registry。

Node 输入：

```python
NodeExecutionContext
```

输出：

```python
NodeResult
```

建议扩展 result：

```python
@dataclass
class NodeResult:
    status: str
    output_refs: list[EntityRef]
    context_patch: dict
    usage: dict | None
    warnings: list[dict]
```

不要把大 JSON/二进制塞回 Workflow context。

---

# 71. EntityRef

推荐加入统一引用：

```python
@dataclass(frozen=True)
class EntityRef:
    entity_type: str
    entity_id: int | str
    revision_id: int | None = None
    content_hash: str | None = None
```

Video Node 之间传：

```text
script_revision ref
storyboard_revision ref
material_revision ref
timeline_revision ref
render ref
```

---

# 72. Workflow Context V2

增加：

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

仍然只把 ID 当 Context。

---

# 73. Rerun API

复用 Workflow：

```http
POST /api/v1/workflow-runs/{run_id}/steps/{step_id}/rerun
POST /api/v1/workflow-runs/{run_id}/steps/{step_id}/rerun-from-here
```

V2 增加 scene scope：

```json
{
  "scope": {
    "scene_key": "scene_004"
  }
}
```

Node Plugin 自己决定是否支持 Scene Scope。

---

# 74. Scene Output Cache

对于可局部执行节点，缓存 key：

```text
plugin key
plugin version
scene input hash
provider config hash
```

如果完全一致，可以复用旧 Material Revision。

但复用必须可追踪：

```text
cache_hit=true
```

不能伪装成新生成。

---

# 75. Human Edit

用户手改 Script：

```text
new VideoScriptRevision
```

用户手改 Storyboard：

```text
new StoryboardRevision
```

用户手改 Timeline：

```text
new TimelineRevision
```

禁止原地修改历史 Revision。

---

# 76. Preview Render

编辑阶段优先生成低成本 preview：

```text
720p
lower bitrate
watermark optional
fast preset
```

Final Render：

```text
target platform profile
full resolution
final bitrate
final subtitle/style
```

两者独立 `VideoRender`.

---

# 77. Platform Video Profile

Channel Registry V2 增加 Video Content Forms。

示例：

```json
{
  "channel": "bilibili",
  "content_forms": {
    "long_video": {
      "artifact_kind": "video",
      "workflow_key": "workflow.bilibili.long_video",
      "renderer": "renderer.video.bilibili",
      "discoverability_profile": "seo.bilibili.video",
      "ruleset": "rules.bilibili.video"
    }
  }
}
```

---

# 78. Video Renderer vs Video Render Provider

必须区分。

## Video Render Provider

负责：

```text
Timeline → MP4
```

## Platform Renderer

负责：

```text
Video Candidate → 平台发布包
```

例如：

```text
title
description
tags
thumbnail
video file
chapter metadata
subtitle
```

不要混在一起。

---

# 79. Delivery V2

继续复用：

```text
DeliveryTarget
DeliveryAttempt
DeliveryReceipt
```

只扩展 content_form。

不要新建：

```text
VideoPublishJob
```

---

# 80. Video Copy Package

无法自动上传的平台：

ZIP：

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

Candidate Hash 与 package 必须一致。

---

# 81. Assisted Video Delivery

浏览器自动化：

```text
upload video
upload thumbnail
fill title
fill description
fill tags
save draft
```

必须停在：

```text
draft / submit-before-confirm
```

除非平台 capability 已明确允许 verified publish。

---

# 82. Review Center 视频 Ready Gate

Video Candidate Ready 必须：

## Content

```text
script exists
no content blocker
```

## Evidence

```text
fact checks complete
```

## Media

```text
all required material exists
rights ready
```

## Composition

```text
timeline valid
no missing clip
no stale scene
```

## Audio

```text
required voice exists
```

## Avatar

如果使用：

```text
profile authorized
```

## Render

```text
final render succeeded
```

## QC

```text
no blockers
```

## SEO

如果 profile required：

```text
report ready
```

## Delivery

```text
platform renderer can build payload
```

---

# 83. Review UI — Video

Video Review 页面至少：

```text
Player
Timeline
Scene List
Script
Subtitle
Material
Voice
Avatar
Thumbnail
SEO
Checks
Workflow Timeline
```

所有修改后明确显示：

```text
What became stale
```

---

# 84. 前端状态管理

VideoWorkspace 建议使用：

```text
React local state
+
server revisions
```

不建议 V2 第一版引入复杂多人 CRDT。

保存 Timeline：

```text
Save Revision
```

再触发 stale propagation。

---

# 85. 前端 API Client

如果当前 API client 已集中管理，则扩展。

建议新建：

```text
apps/web/src/api/video.ts
```

包含：

```text
createVideoProject
getVideoProject
createScriptRevision
generateStoryboard
saveTimeline
createRender
getRender
rerunScene
```

避免散落 fetch。

---

# 86. Video Player

优先使用浏览器原生：

```html
<video>
```

配合自定义 Timeline。

不在 V2 引入重型播放器框架，除非字幕/多轨预览确实需要。

---

# 87. Render Progress

Render Worker 更新：

```text
queued
running
progress
succeeded
failed
```

可以增加：

```python
progress_pct: int | None
stage: str | None
```

到 `VideoRender`。

Provider 不支持 progress 时保持 null。

---

# 88. WebSocket / Polling

V2 第一版允许：

```text
polling
```

例如 2–5 秒查询 Render 状态。

不把 WebSocket 作为视频上线阻塞条件。

---

# 89. 迁移方案

建议拆为 4 次 additive Alembic Migration。

## Migration V2-A — Video Core

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

## Migration V2-B — Media / Profiles

新增：

```text
material_derivation
voice_profile_version
avatar_profile_version
```

MaterialRevision additive columns：

```text
storage_provider
storage_key
technical_metadata_json
```

---

## Migration V2-C — Rendering / Provider Jobs

新增：

```text
video_render
provider_job
execution_usage
```

---

## Migration V2-D — Candidate / Check Generalization

根据实施情况：

- candidate manifest schema v3 不一定需要 DB migration；
- Channel seed 增加视频 forms；
- Discoverability profiles seed；
- Check model 若泛化，则单独 migration。

---

# 90. 迁移原则

必须：

```text
fresh SQLite upgrade head
历史 SQLite stepwise upgrade
PostgreSQL upgrade
```

全部验证。

不能：

- 自动把旧 Script 标成 VideoProject；
- 自动伪造历史视频；
- 给历史图片伪造 rights；
- 伪造旧 Candidate 的视频字段。

---

# 91. 文件结构

建议新增：

```text
apps/api/app/services/video/
    projects.py
    scripts.py
    storyboard.py
    composition.py
    subtitles.py
    renders.py
    qc.py

apps/api/app/services/content_harness/video/
    contracts.py
    providers.py
    tts.py
    avatar.py
    generation.py
    render.py
    rules.py
    nodes.py

apps/api/app/routers/
    video_projects.py
    video_composition.py
    video_providers.py

apps/api/app/tasks/
    worker_tasks.py
```

如果 `worker_tasks.py` 继续膨胀，V2 可以拆：

```text
tasks/video_tasks.py
tasks/provider_tasks.py
tasks/delivery_tasks.py
```

但 Celery task name 必须稳定。

---

# 92. Model 文件是否拆分

当前所有模型集中在：

```text
models.py
```

V2 若继续增加大量视频表，文件会过大。

建议在 V2 架构批次决定是否拆成：

```text
models/
  core.py
  content.py
  material.py
  workflow.py
  delivery.py
  video.py
```

但：

> 模型拆文件不是 V2 功能验收前置条件。

如果拆分会扩大迁移风险，可以先保持单文件。

---

# 93. Plugin Keys

建议：

```text
node.video.strategy@1
node.video.script@1
node.video.storyboard@1
node.video.material_plan@1
node.video.tts@1
node.video.avatar@1
node.video.timeline@1
node.video.subtitle@1
node.video.render@1
node.video.qc@1
node.video.thumbnail@1

tts.<provider>@<version>
avatar.<provider>@<version>
video_gen.<provider>@<version>
render.ffmpeg@1
```

Workflow Definition 必须冻结版本。

---

# 94. Provider Secrets

所有 Provider Credential：

- 不写 `workflow.definition_json`；
- 不写 `provider_job.response_metadata_json`；
- 不写 Candidate；
- 不返回前端。

使用：

```text
environment
secret manager
system settings encrypted/opaque ref
```

---

# 95. Remote URL 安全

Provider 返回 URL 时：

- 必须限制 scheme；
- 下载设置 size limit；
- timeout；
- content-type 验证；
- SSRF 防护；
- hash；
- 落入 BlobStore 后不再依赖临时 URL。

---

# 96. 文件安全

上传素材：

- MIME sniff；
- 文件扩展名不能作为唯一判断；
- 限制最大大小；
- 可选恶意文件扫描；
- 禁止将用户文件路径拼进 shell command。

FFmpeg 参数不得直接拼接未经验证的用户字符串。

---

# 97. FFmpeg 安全

如果使用 FFmpeg：

```text
subprocess.run([...], shell=False)
```

禁止：

```text
shell=True
```

用户输入只经过结构化参数转换。

---

# 98. Rights

Video Candidate 引用的每一个外部 Material 必须拥有：

```text
public_use_allowed
```

Digital Human：

```text
consent_ref
```

Voice：

```text
rights_status
```

缺失：

```text
blocker
```

---

# 99. AI Generated Media Provenance

AI Image / Video / Voice 记录：

```text
provider
provider version
prompt
seed（有则记录）
input material refs
created_at
```

不要求向普通观众展示全部 provenance，但系统内部必须保存。

---

# 100. Content Safety

Video Workflow 继续复用现有 Content Censor / Rules。

如果使用外部视频 Provider：

Provider 自己拒绝并不等于 Studio 的安全检查通过。

Studio Candidate Gate 仍独立执行。

---

# 101. Fact Consistency

视频脚本 FactCheck 后，如果：

```text
subtitle
on-screen text
chart
thumbnail
```

加入新的事实性表达，也必须检查。

Candidate Rule 应抽取：

```text
script text
subtitle
overlay text
thumbnail text
description
```

共同验证关键客观信息。

---

# 102. Chart

量化/A股视频强依赖 Chart。

V2 复用 Asset Provider：

```text
asset.chart
```

Chart 生成结果是：

```text
MaterialRevision(kind=chart/image)
```

Storyboard / Timeline 只是引用。

---

# 103. Screen Capture

V2 可以先支持：

```text
manual screen recording upload
```

以后增加：

```text
screen.capture.browser
screen.capture.desktop
```

仍作为 Material Provider。

---

# 104. Music / SFX

V2 第一版允许：

```text
user upload
approved library
provider asset
```

必须有 rights。

不要求自动音乐生成。

---

# 105. Long Video Chapter

长视频应有：

```text
chapter title
start_ms
```

Discoverability Report 可生成建议。

最终 chapter metadata 进入 Candidate。

---

# 106. Thumbnail Workflow

建议：

```text
video summary
→ thumbnail copy
→ image brief
→ generate/search/select
→ human select
→ rule check
```

Thumbnail 选择必须发生 Approval 前。

---

# 107. Short Video Hook Evaluation

短视频可加入：

```text
skill.video.hook-review
```

但不能把“流量评分”当成发布 Gate。

发布 Gate 只检查：

```text
完整性
事实
权利
格式
安全
```

Hook Score 作为建议。

---

# 108. 视频 Provider Fallback

Provider A 失败不能立即自动换 Provider B，因为：

- 风格可能变化；
- 成本变化；
- 输出不可重复；
- 权利条款不同。

允许 Workflow 明确：

```text
fallback_policy
```

默认：

```text
manual_select
```

---

# 109. Queue Retry

允许自动 retry：

```text
pure local render
temporary network read
idempotent status lookup
```

谨慎 retry：

```text
paid video generation
digital human generation
```

必须有 Provider Job / idempotency 支持。

---

# 110. Render Idempotency

Render request hash：

```text
timeline_hash
render_profile
provider_key
provider_version
```

完全相同：

可以复用成功 Render。

---

# 111. Provider Job Idempotency

如果外部 Provider 支持 idempotency key：

直接使用 Studio 生成的稳定 key。

如果不支持：

```text
prepared
COMMIT
remote call
```

超时：

```text
unknown
```

与 DeliveryAttempt 同一安全哲学。

---

# 112. 删除语义

已经被 Candidate /历史 Workflow 引用的：

```text
MaterialRevision
TimelineRevision
VideoRender
Voice Profile Version
Avatar Profile Version
```

不可 hard delete。

使用：

```text
archived
revoked
disabled
```

---

# 113. Rights Revocation

某 Material rights 被撤销后：

- 历史 Candidate 保留；
- 未交付 DeliveryTarget Block；
- 已发布内容显示 warning / remediation；
- 不重写历史审计记录。

---

# 114. Video Candidate Approval

Reviewer 必须能看到：

```text
Final Render
Thumbnail
Title
Description
Tags
Subtitles
Chapters
Rights
Checks
Workflow
Provider Versions
```

批准的是：

> 最终平台包，而不是 Timeline 草稿。

---

# 115. Final Render Mutation

Approval 后：

禁止重新编码后直接替换最终视频。

如果平台需要新规格转码：

推荐将：

```text
platform transcode
```

作为 Candidate 前 Renderer 阶段。

转码后的最终 bytes hash 进入 Candidate。

---

# 116. Platform Package

不同平台可有不同转码 Candidate。

例如：

```text
同一个 master timeline
↓
Bilibili Render Candidate
↓
XHS Render Candidate
```

这两个是两个独立 Platform Candidate。

共享 Timeline 不代表共享最终 Candidate。

---

# 117. Master Render

可选保存：

```text
master mezzanine render
```

再派生平台版本。

Material Derivation：

```text
Master
→ Bilibili
→ XHS
→ X
```

V2 第一版不强制 Master Pipeline，但模型必须允许。

---

# 118. Review & Publish Projection

`review_center.py` 不新增视频专属状态真源。

只聚合：

```text
VideoProject
WorkflowRun
TimelineRevision
VideoRender
Checks
Discoverability
ContentAsset
DeliveryTarget
```

---

# 119. Dashboard

V2 增加：

```text
Rendering
Needs Voice
Needs Avatar Authorization
Needs Material
Video QC Blocked
```

状态必须真实。

---

# 120. Notifications

V2 可选支持：

```text
render completed
render failed
provider unknown
review required
```

但通知系统不是 V2 发布阻塞条件。

---

# 121. V2 Golden Tests

至少建立以下 Golden。

## 短视频

主题：

```text
AI Agent 产品观点
```

验证：

```text
60秒
9:16
脚本
分镜
TTS
字幕
Timeline
Preview
Final
Thumbnail
SEO
```

---

## A股复盘数字人

验证：

```text
事实日期
指数数据
图表
数字人
Voice
风险声明
字幕
雪球/短视频平台
```

---

## 技术长视频

验证：

```text
章节
代码截图/录屏素材
长脚本
Timeline
字幕
B站 SEO
```

---

## 素材混合视频

验证：

```text
上传图片
web material
AI generated image
chart
avatar
```

全部 rights gate。

---

# 122. Unit Tests

新增至少：

```text
test_video_project_models.py
test_storyboard_revision.py
test_timeline_schema.py
test_video_staleness.py
test_video_rules.py
test_tts_provider_registry.py
test_avatar_provider_registry.py
test_render_idempotency.py
test_provider_jobs.py
test_video_candidate_manifest.py
test_video_delivery_package.py
```

---

# 123. Integration Tests

至少：

```text
Topic
→ VideoProject
→ Script
→ Storyboard
→ Timeline
→ Mock Render
→ QC
→ Candidate
→ Approval
→ Copy Package
```

使用 Mock Provider，不依赖真实收费 API。

---

# 124. Real Provider Tests

收费 Provider 不能进入普通 CI。

使用：

```text
manual integration marker
```

例如：

```bash
pytest -m real_video_provider
```

需要显式 Secret。

---

# 125. Migration Tests

扩展现有：

```text
test_migrations.py
```

验证：

```text
fresh SQLite
V1 head → V2 head
PostgreSQL
```

---

# 126. Frontend Tests

至少：

- Video Workspace 能加载；
- Timeline 保存创建新 revision；
- Replace Material 后 stale；
- Render 状态更新；
- Final Candidate 未 Ready 时不能 Approve；
- rights blocker 不允许 Delivery；
- Unknown Provider Job 不显示 success。

---

# 127. 性能要求

V2 不给视频生成承诺绝对秒数。

但要求：

- API 创建任务 < 1s（不含 DB 极端负载）；
- 所有长任务异步；
- 页面不因 render 阻塞；
- Timeline metadata 分页/按需；
- 视频 bytes 不经 JSON；
- Material 列表使用分页。

---

# 128. 可恢复性

Worker 重启后：

```text
queued task 可恢复
running remote provider job 可 reconcile
running local render 标 stale/failed 后可安全 retry
```

不能永久卡在 running。

---

# 129. Render Worker Crash

local render：

```text
heartbeat / started_at
```

超过阈值：

```text
orphaned
```

允许重新 render。

这不是远端副作用，可基于相同 input hash 安全重试。

---

# 130. Provider Polling

远端视频 job：

```text
poll interval
max duration
backoff
```

必须配置。

长时间没有结果：

```text
unknown / timeout
```

不是 failed 除非远端明确失败。

---

# 131. OpenSpec 拆分建议

V2 不建议一个超大 Change 一次完成。

建议按以下 changes。

## Change V2-01

```text
add-video-domain-model
```

模型、迁移、API Skeleton。

## Change V2-02

```text
add-video-provider-runtime
```

TTS / Avatar / VideoGen / Render contract。

## Change V2-03

```text
add-storyboard-timeline-composition
```

Storyboard / Timeline / Scene rerun。

## Change V2-04

```text
add-video-rendering
```

Render Worker / BlobStore / Preview。

## Change V2-05

```text
add-video-review-candidate
```

QC / Candidate v3 / ReviewPublish。

## Change V2-06

```text
add-video-discoverability-delivery
```

Video SEO / Platform package / Delivery。

---

# 132. 推荐实施阶段

## Phase 0 — 架构门

- V1 回归全绿；
- 当前 migration head 记录；
- 定义 V2 contracts；
- 不先接任何真实付费 Provider。

---

## Phase 1 — Video Domain

完成：

```text
VideoProject
Script
Storyboard
Scene
Timeline
Subtitle
API
Migration
```

验收：

纯 Mock 数据完成版本链。

---

## Phase 2 — Local Render

完成：

```text
BlobStore
FFmpeg/Render Provider
Preview Render
Final Render
Video Material
```

验收：

本地素材可以合成真实 mp4。

---

## Phase 3 — TTS

完成：

```text
Voice Profile
TTS Contract
Mock TTS
1 个真实 TTS Provider
```

---

## Phase 4 — Digital Human

完成：

```text
Avatar Profile
Rights Gate
Provider Job
1 个真实 Digital Human Provider
```

数字人不是 V2 视频基础链的阻塞项。

即：

> 没数字人仍然能完成普通视频。

---

## Phase 5 — Review & Candidate

完成：

```text
Video Review UI
Video Rules
Candidate Manifest v3
Approval
```

---

## Phase 6 — Video SEO & Delivery

完成：

```text
Video Discoverability
Thumbnail
Description/Tags/Chapters
Copy Package
至少一个真实视频平台 Assisted/Auto Draft
```

---

# 133. 发布优先级

建议首批渠道：

## P0

### B站

因为：

- 长视频；
- 技术/AI 内容；
- 封面；
- SEO；
- 章节；
- 视频综合能力最完整。

### 小红书短视频

验证：

- 竖屏；
- 封面；
- 搜索；
- 短视频。

### 抖音

验证：

- 短视频；
- 口播；
- 数字人；
- 高密度字幕。

---

# 134. Finance Video

雪球本身主要保留文章/图文。

金融短视频可以发布到：

```text
抖音
小红书
B站
微博
```

但内容来源和 FactPack 仍来自：

```text
量化 / A股复盘 Content Core
```

V2 必须确保：

> 视频生产不产生第二套财经事实。

---

# 135. 技术 Video

掘金主要保持文章。

同一个技术 Content Core 可以派生：

```text
掘金文章
B站长视频
X Thread
公众号文章
```

代码截图、架构图、Demo Material 可跨 Artifact 复用。

---

# 136. V2 核心验收条件

V2 Core Ready 必须满足以下条件。

## Video Domain

1. VideoProject 可创建；
2. Script Revision 不覆盖；
3. Storyboard Revision 不覆盖；
4. Timeline Revision 不覆盖；
5. Scene 可稳定寻址。

## Material

6. 视频/音频 Material 可保存；
7. content hash 可验证；
8. Material Derivation 可追踪；
9. 大文件不进入 JSON；
10. 权利字段进入 Gate。

## TTS

11. Voice Profile 版本化；
12. Mock TTS 可用；
13. 至少一个真实 TTS Provider 验证；
14. TTS 输出成为 MaterialRevision。

## Avatar

15. Avatar Profile 版本化；
16. Consent Gate 存在；
17. 无授权不可 Candidate Ready；
18. 至少一个 Provider 可实验验证；若供应商不可用，不阻塞普通视频 V2。

## Composition

19. Timeline 可保存 Revision；
20. Clip 引用真实 Material；
21. 替换 Scene 可局部 stale；
22. Segment Render 可执行。

## Render

23. Preview Render 可用；
24. Final Render 可用；
25. Render 有 input hash；
26. 同输入可幂等复用；
27. Final mp4 成为 MaterialRevision。

## Subtitle

28. Subtitle Revision 可编辑；
29. 字幕 timing 可检查；
30. Candidate 冻结 subtitle。

## Review

31. Review Center 可播放 Final Video；
32. 可看到 Thumbnail；
33. 可看到 SEO；
34. 可看到 Rights；
35. 可看到 QC；
36. 修改后 Candidate invalid。

## Candidate

37. Manifest schema v3；
38. candidate hash 包含视频 bytes hash；
39. Approval 绑定 hash；
40. Approval 后不能静默改视频。

## Delivery

41. Video Copy Package 可用；
42. 至少一个平台完成真实手工包发布验证；
43. 至少一个视频平台完成 Assisted 或 Auto Draft 验证；
44. Unknown 远端结果不重复提交。

---

# 137. V2 发布门禁

上线真实生产前必须：

```text
backend full pytest
ruff
frontend build
OpenSpec strict
fresh SQLite migration
V1 → V2 migration
PostgreSQL migration
local render golden
candidate hash golden
rights blocker golden
delivery unknown golden
```

所有真实 Provider 还需要：

```text
manual provider validation
```

---

# 138. 回归保护

V2 不允许破坏 V1：

- 文章仍可生成；
- 图片素材仍可用；
- V1 Candidate Manifest v2 仍可读；
- V1 ContentAsset 仍可 Delivery；
- 微信草稿仍正常；
- Review & Publish Center 仍能显示 Text/Image；
- V1 Workflow schema 仍兼容；
- 旧 MaterialRevision `file_path` 仍能读。

---

# 139. 向后兼容 Candidate

Candidate Reader：

```python
if schema_version == 2:
    read_v1_candidate()

elif schema_version == 3:
    read_multimodal_candidate()
```

不要强制 migrate 历史 Candidate Manifest。

---

# 140. V2 完成后的产品状态

V2 完成后，一个 Topic 可以同时生产：

```text
公众号文章
知乎文章
雪球研究稿
掘金技术稿
小红书图卡
X Thread
抖音短视频
小红书短视频
B站长视频
数字人口播
```

这些 Artifact：

共享：

```text
Evidence
FactPack
Content Core
Material Library
Brand
Workflow Infrastructure
Review Center
Approval
Delivery
Feedback
```

但分别拥有：

```text
独立 Workflow
独立 Revision
独立 Candidate
独立 DeliveryTarget
```

---

# 141. V2 最终架构

```text
                     Content Core
                          │
            ┌─────────────┼─────────────┐
            │             │             │
          Text          Image          Video
            │             │             │
            │             │       Video Strategy
            │             │             ↓
            │             │          Script
            │             │             ↓
            │             │        Storyboard
            │             │             ↓
            │             │       Material Plan
            │             │             ↓
            └─────────────┴────── Material Library
                                          │
                       ┌──────────────────┼───────────────┐
                       │                  │               │
                     Image              Audio           Video
                       │                  │               │
                    AI/Search            TTS          AI/Search
                       │                  │               │
                       └──────────── Digital Human ──────┘
                                          │
                                       Timeline
                                          │
                                   Preview / Render
                                          │
                                       Video QC
                                          │
                                  SEO / Thumbnail
                                          │
                                Review & Publish Center
                                          │
                                Immutable Candidate
                                          │
                                       Approval
                                          │
                                     Delivery
```

---

# 142. V2 产品原则

## 原则 1

视频是一级 Artifact，不是文章附件。

## 原则 2

Storyboard 是语义规划，Timeline 是最终 Composition。

## 原则 3

所有视频素材进入统一 Material Library。

## 原则 4

TTS、数字人、视频生成、Render 都是 Provider Plugin。

## 原则 5

数字人不是视频生产必选项。

## 原则 6

视频必须支持 Scene / Segment 粒度局部重跑。

## 原则 7

Final Render 真实 bytes 必须进入 Candidate Hash。

## 原则 8

视频审核复用统一 Review & Publish Center。

## 原则 9

视频发布复用统一 DeliveryTarget / DeliveryAttempt。

## 原则 10

SEO / Discoverability 是视频独立生产阶段。

## 原则 11

图片、视频、音乐、人像、声音都必须进入 Rights Gate。

## 原则 12

V2 不能破坏 V1 文 + 图生产能力。

---

# 143. Codex 实施 HANDOFF

```text
GOAL
在已完成 V1 PRD 2.0 Content Harness 的 AIContentStudio 上新增 VideoArtifact
生产能力，不创建第二套 review/delivery/material/workflow 系统。

BASELINE
- Material Library 已存在
- Channel Registry 已存在
- Workflow/Run/Step 已版本化
- Node Plugin Registry 已存在
- Discoverability 已存在
- Candidate Manifest v2 已存在
- DeliveryTarget/Attempt/Receipt 已存在
- ReviewPublish 已存在
- Celery 已存在

ARCHITECTURE
VideoProject
→ VideoScriptRevision
→ StoryboardRevision
→ VideoScene
→ TimelineRevision
→ MaterialRevision
→ VideoRender
→ Checks
→ ContentAsset candidate manifest v3
→ existing Approval
→ existing DeliveryTarget

NEW PLUGINS
- TTSProvider
- DigitalHumanProvider
- VideoGenerationProvider
- VideoRenderProvider
- video nodes
- video rules
- video discoverability profiles

DO NOT
- create VideoDeliveryTarget
- create VideoReviewCenter
- copy Material Library
- store video bytes in DB
- pass large bytes via Celery
- mutate historical revisions
- blindly retry paid remote provider jobs
- publish public content by default

PHASE ORDER
1. domain + migration
2. provider contracts + mock providers
3. storyboard/timeline
4. local render + blob store
5. TTS
6. digital human
7. QC + review + candidate v3
8. discoverability + delivery
9. real provider validation

REQUIRED GATES
- full backend regression
- frontend build
- ruff
- OpenSpec strict
- fresh SQLite migration
- V1→V2 migration
- PostgreSQL migration
- candidate hash golden
- video render golden
- rights golden
- unknown provider/delivery golden
```

---

# 144. 最终定义

V2 成功不是：

> “系统可以调用某个 AI 视频 API。”

而是：

> **AIContentStudio 已经能够把同一个可信 Content Core，通过可插拔工作流组织成真实、版本化、可局部编辑、可审核、可交付的视频成品；视频、声音、数字人、字幕、封面、SEO 和素材全部进入统一的 Content Harness，并与 V1 的文、图能力共享同一套事实、素材、审批和发布基础设施。**
