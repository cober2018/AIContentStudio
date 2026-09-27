# AIContentStudio V1 PRD 2.0 开发 OpenSpec

> 建议 Change Name：`align-v1-prd2-content-harness`  
> 文档性质：Master Development OpenSpec / Codex Implementation Handoff  
> 基线仓库：AIContentStudio `main @ a6084b0`  
> 基线日期：2026-09-24  
> 上位需求：`AIContentStudio_V1_PRD_2.0_ContentHarness_2026-09-24.md`  
> 架构基线：AIContentStudio 图 / 文 / 视 Content Harness North Star  
> 当前仓库状态：dirty；本 OpenSpec 是规划，不应覆盖当前未提交改动  
> 目标：在现有模块化单体上完成 V1 PRD 2.0 的 **Text + Image Content Harness Foundation**

---

# 0. 执行约束

本 OpenSpec 是一个 V1 2.0 的主实施变更。它不是要求 Codex 一次性大爆炸重写全部系统，而是定义一个统一目标和严格的分阶段实施顺序。

实施时必须遵守：

1. **复用现有对象，不建第二套内容中心。**
2. `MotherRevision`、`DraftMedia`、`ContentAsset.approved_candidate_hash`、`DeliveryTarget`、`Workflow / WorkflowRun / WorkflowStep` 都视为已有正确基础。
3. 数据模型优先 additive migration；历史数据继续可读。
4. 新规则不能通过迁移把旧内容伪造成“新规则已验证”。
5. 任何远端副作用必须先持久化 Intent/Attempt，再执行远端调用。
6. 平台未真实验证的能力必须显示 `unverified / unavailable / experimental`，不能伪装 supported。
7. 当前工作区有未提交/未追踪内容；Codex apply 前必须先读取 `git_status` 和 `git_diff`，不能重置或覆盖用户改动。
8. 当前活动提案 `openspec/changes/complete-prd-v1-channel-deliverables/` 与本变更范围重叠。若其尚未实施，应标记为被本主变更吸收，不得并行执行两套渠道模型。
9. 不引入第二个 Workflow Engine。
10. 不为了“插件化”拆微服务；保持现有 FastAPI + SQLAlchemy + React + Celery 模块化单体。
11. V1 不实现完整视频成片、TTS、数字人和 Timeline，但新增对象/契约不得阻塞 V2 接入。

---

# 1. 当前代码事实基线

以下是本 OpenSpec 编写时实际源码状态，不是目标设计。

## 1.1 已有并应保留的能力

### Evidence / FactPack

现有：

- `apps/api/app/models.py`
  - `SourceDocument`
  - `Fact`
  - `FactPack`
  - `FactPackItem`
  - `EvidenceKind`
- `FactPackItem` 已有：
  - `evidence_kind`
  - `snapshot_version`
  - `snapshot_json`
  - `snapshot_checksum`
  - `public_use_allowed`
  - `model_use_allowed`
  - 撤权字段

结论：

> 新 V1 不新建通用 Evidence 平台；继续以 FactPackItem frozen snapshot 作为内容证据边界。

---

### Content Core / Mother Revision

已有：

- `MotherRevision`
- `Draft.mother_revision_id`
- `Draft.evidence_checksum`
- `Draft.input_hash`

已有 API：

- `POST /api/v1/article-handoff/topics/{topic_id}/mother-revisions`
- `GET /api/v1/article-handoff/topics/{topic_id}/mother-revisions`
- `POST /api/v1/article-handoff/mother-revisions/{revision_id}/drafts`

结论：

> V1 PRD 2.0 的 Content Core 文本实现直接复用 `MotherRevision`，本变更不新建 `ContentCore` 同义表。

---

### Draft Revision

已有：

- `Draft.revision_no`
- 人工编辑创建新 Draft
- 重新生成不覆盖旧 Draft
- `structured_json`
- `thread_posts_json`
- `candidate_readiness`

结论：

> `Draft` 继续作为平台 Artifact Revision 的 V1 实现，不新建平行 `ArtifactRevision` 表。

---

### Draft-stage Media

已有：

- `DraftMedia`
- content hash
- role
- sort order
- rights
- public use
- bytes file path
- reorder
- revoke public use
- approved candidate 引用后禁止删除

结论：

> 这是 Material Library 的正确起点，但当前仍绑定 Draft，缺“全局可复用 Material”与 placement。

---

### Immutable Candidate

已有：

- `services/candidates.py`
- `build_manifest`
- `candidate_hash`
- `readiness_reasons`
- `Review.candidate_hash`
- `ContentAsset.approved_candidate_hash`
- `ContentAsset.candidate_manifest_json`

结论：

> Candidate 不重造；升级 manifest schema 即可。

---

### Delivery

已有：

- `DeliveryTarget`
- `DeliveryReceipt`
- `DeliveryFeedback`
- account/action/authorization/candidate hash 绑定
- package ZIP
- human confirmed / reconciliation needed
- idempotent target/receipt 逻辑

结论：

> 交付核心对象正确；需要从 M1 的 `wechat/x_thread + manual_handoff` 扩展为通用 Delivery Router。

---

### Workflow

已有：

- `Workflow`
- `WorkflowRun`
- `WorkflowStep`
- DAG 推进
- waiting_input
- human complete
- failed retry
- React Flow UI

结论：

> 不替换 Workflow Engine；把 handler dispatch 从硬编码 Map 演进为 Registry。

---

### Skills / dsh

已有：

- `plugin_registry.py`
- 扫描 `~/.agents/skills`
- 扫描 `~/.zcode/skills`
- `SKILL.md` frontmatter `name/description`
- settings 可启用 Skills / MCP
- dsh 状态和模型配置
- ExternalContent ingest

结论：

> 已有 Discovery，但尚没有统一 Skill Execution Contract / Version / License / Capability 元数据。

---

### LLM Provider

已有：

- `LLMProvider`
- Mock
- OpenAI-compatible
- 场景路由
- `generate / rewrite / fact_check / topic_discovery`

结论：

> 新增 `discoverability` 等 purpose，不改 Provider 基本抽象。

---

## 1.2 当前关键缺口

### A. Channel 硬编码

硬编码位置至少包括：

- `models.py:Channel`
- `routers/topics.py:VALID_CHANNELS`
- `generation/orchestrator.py`
- `generation/renderers.py`
- `workflow_templates.py:CHANNEL_META`
- `templates.py:sync_prompt_versions_from_files`
- `seed.py`
- `external.py:CHANNELS`
- 前端 `Topics.tsx`
- 前端 `Workflows.tsx`
- 前端 Channel labels

当前 Channel 只有：

```text
douyin
xiaohongshu
wechat
x_thread
```

---

### B. Workflow Node 硬编码

`workflow_engine.py` 当前使用：

```python
HANDLERS = {...}
COMPLETE_HANDLERS = {...}
```

所有 Node Type 都由核心文件知道。

新增平台/能力持续向该文件增加 handler 会违背 V1 2.0。

---

### C. Workflow 无版本

`Workflow` 当前没有：

```text
workflow_key
version
checksum
status
parent_version
schema_version
```

历史 Run 只能通过 workflow_id 间接解释，不能明确冻结“哪个版本定义”。

---

### D. 无 Material Library

当前两套素材：

```text
DraftMedia
AssetMedia
```

其中：

- `DraftMedia` 更接近正确方向；
- `AssetMedia` 仍包含 “Prompt → 占位 SVG” 的旧产品语义；
- 素材不能脱离某个稿件独立管理；
- 无全局素材复用；
- 无 Material derivation；
- 无统一来源元数据；
- 无 placement。

---

### E. Candidate Manifest 不完整

当前 Candidate 包含：

```text
title
body
structured
thread
media
citations
declarations
fact_check
mother_revision
input_hash
```

缺少：

```text
content_form
artifact_kind
document/composition
media placement
generic check runs
SEO report
renderer output hash
channel profile version
workflow version
skill/plugin snapshots
```

---

### F. Check 体系仍以 FactCheck 为中心

当前：

```text
Draft.fact_check_json
```

V1 2.0 还需要：

```text
fact
platform
safety
rights
seo
finance
technical
media completeness
```

需要统一 Check Run 语义，否则 Review Center 会出现多个不可追溯 JSON。

---

### G. SEO / Discoverability 不存在

当前代码无正式：

```text
SEO Profile
Search Intent
Discoverability Report
SEO Rule
```

---

### H. Delivery 被 M1 约束锁定

`DeliveryTarget` DB CheckConstraint 当前：

```text
channel IN ('wechat', 'x_thread')
action = 'manual_handoff'
```

`article_handoff.py` 也只允许 WeChat / X Thread。

无法支持：

```text
copy_package
assisted_draft
auto_draft
```

---

### I. 公众号真实草稿路径仍是旧工作流副作用

`workflow_engine._h_publish_wechat`：

- 直接 `subprocess.run(["wewrite", "publish", ...])`
- 不通过新的 DeliveryTarget/Attempt
- 旧路径会在调用前临时截断 title/digest
- 无通用 unknown attempt 持久化

V1 2.0 必须把真实公众号草稿纳入统一 Delivery Router。

---

### J. 审核 / 资产 / Handoff UI 分散

当前：

```text
Review.tsx
Assets.tsx
Handoff.tsx
Workspace.tsx
Workflows.tsx
```

分别承担部分操作。

V1 2.0 需要一个 Topic-centric Review & Publish Center projection。

---

# 2. Proposal

## Why

当前系统已经拥有可信证据、稿件版本、候选哈希、素材字节、工作流和人工交付等关键基础，但这些能力仍带有三渠道原型阶段的硬编码：

- Channel 被枚举和前端常量限制；
- Workflow 依赖中央 handler map；
- 素材仍主要是稿件附件；
- SEO 不存在；
- Candidate 只覆盖部分派生状态；
- Delivery 只支持 M1 WeChat/X Thread 人工交付；
- Review / Delivery 操作面分散。

如果继续按平台逐个增加 Prompt、Renderer 和发布按钮，会在扩展雪球、掘金、知乎、头条等渠道时累积大量平台条件逻辑，并在 V2 接视频时产生第二套生产系统。

V1 PRD 2.0 要求先建立 Text + Image Content Harness Foundation，使未来平台和 V2 视频能力都能够通过 Registry / Workflow / Plugin 扩展，而不是修改核心引擎。

---

## What Changes

本变更将：

1. 将现有 `ChannelTemplateVersion` 提升为 Channel Profile 的版本化载体，建立集中 Channel Registry。
2. 给 Workflow 增加稳定 key/version/checksum/schema，并把 Node handler 改为 Registry resolve。
3. 在 `DraftMedia` 之下建立全局 Material / MaterialRevision，让素材可复用、可追溯、可版本化。
4. 给 Draft 增加 `artifact_kind / content_form / document_json`，在不破坏 Markdown 真源的前提下保存图片 placement 和图文 composition。
5. 新增通用 `DraftCheckRun`，统一 Fact / Platform / Rights / SEO / Safety / Domain checks。
6. 新增 Discoverability Profile + Report，实现 Pre/Post SEO 节点。
7. 升级 Candidate Manifest 到 schema v2，覆盖最终 Document、真实素材、检查、SEO、Render 和 Plugin/Workflow 版本。
8. 扩展 DeliveryTarget 和新增 DeliveryAttempt，支持 `copy_package / assisted_draft / auto_draft`。
9. 将公众号 `wewrite publish` 移入 Publisher Plugin，通过批准 Candidate + DeliveryTarget 执行，而不再由遗留 Workflow 直接产生副作用。
10. 建立 Topic-centric Review & Publish Center。
11. 实现 Workflow Node 级 `rerun` / `rerun-from-here` 与 stale propagation。
12. 首批注册 V1 PRD 2.0 的 14 个平台/内容形态 profile；优先通过共享 Workflow Bundle + 薄平台适配避免复制 14 套逻辑。
13. 保留抖音 Script Package，不把其标为视频成片。
14. 给 V2 预留 `artifact_kind=video` 与 Provider 类型，但本变更不实现视频 Timeline/TTS/数字人。

---

## Capabilities

### New Capabilities

- `content-harness-registry`
- `versioned-channel-workflow`
- `material-library-v1`
- `artifact-composition-v1`
- `unified-check-runs`
- `discoverability-optimization`
- `workflow-rerun-staleness`
- `unified-review-publish-center`
- `delivery-router-v1`
- `v1-platform-artifacts`

### Modified Capabilities

- `typed-evidence-freeze`
- `versioned-article-candidate`
- `manual-article-handoff`
- `prd-v1-channel-deliverables`

---

## Non-Goals

本变更不实现：

- 视频成片；
- Storyboard 编辑器；
- Timeline；
- TTS；
- Voice Clone；
- 数字人；
- 视频剪辑；
- Video QC；
- 自动公开视频发布；
- SaaS 多租户；
- 计费；
- 通用插件市场；
- 任意第三方 Skill 无审计自动执行；
- 未经真实账号验证的平台自动发布承诺。

---

# 3. 总体目标架构

```text
Source / Evidence / FactPack
            ↓
         Topic
            ↓
      MotherRevision
            ↓
      Channel Selection
            ↓
┌───────────┼────────────────┐
│           │                │
WorkflowRun WorkflowRun  WorkflowRun
│           │                │
└───── Content Harness ───────┘
            │
 Skills / Rules / SEO / Material / Render
            │
        Draft Revision
        + Document
        + Material Uses
        + Check Runs
            │
     Review & Publish Center
            │
      Candidate Manifest v2
            │
         Approval
            │
      DeliveryTarget
            │
      DeliveryAttempt
            │
 Copy / Assisted / Auto Draft
            │
          Receipt
            │
         Feedback
```

---

# 4. 关键设计决策

## Decision 1 — 不重命名所有现有业务表

V1 使用兼容演进。

产品语义：

```text
Content Core
Artifact Revision
Material
Candidate
```

代码继续复用：

```text
MotherRevision
Draft
DraftMedia
ContentAsset
```

本轮不进行高风险大规模 rename migration。

---

## Decision 2 — Promote ChannelTemplateVersion，不新建第二套 Channel 配置表

现有 `ChannelTemplateVersion` 已：

- versioned
- immutable after publish
- ContentJob 引用
- 前端已有 Template 管理

因此 V1 2.0 将其提升为 **Channel Profile Version** 的 DB 载体。

新增字段：

```text
profile_schema_version INTEGER NOT NULL DEFAULT 1
profile_json JSON NULL
```

`profile_json` schema：

```json
{
  "content_forms": {
    "article": {
      "artifact_kind": "text",
      "default_workflow_key": "workflow.wechat.deep_article",
      "renderer_key": "renderer.wechat.article",
      "rule_sets": ["rules.common.article", "rules.wechat.article"],
      "discoverability_profile": "seo.wechat.article",
      "publisher_candidates": ["publisher.wechat.wewrite", "publisher.copy"],
      "media_requirements": {
        "cover": "required",
        "inline": "optional"
      }
    }
  }
}
```

保留现有：

```text
structure
length_guidance
forbidden_patterns
output_schema
```

作为兼容字段。

---

## Decision 3 — 新建 ChannelRegistry Service，删除业务层的渠道枚举依赖

新增：

```text
apps/api/app/services/content_harness/channel_registry.py
```

职责：

```python
resolve_channel(db, channel_key)
resolve_content_form(db, channel_key, content_form)
list_channels(db)
validate_target(...)
```

业务代码不再使用：

```python
channel in {c.value for c in Channel}
```

`models.Channel` 在迁移期保留给旧代码 / Export 兼容，禁止继续新增 enum item 作为新渠道接入方式。

最终读取渠道列表的唯一业务入口：

```text
ChannelRegistry
```

---

## Decision 4 — Workflow 变成真正的版本化 Definition

`Workflow` 新增：

```text
workflow_key STRING(120) NULL
version INTEGER NOT NULL DEFAULT 1
parent_id FK workflow.id NULL
status STRING(20) DEFAULT 'draft'
schema_version INTEGER NOT NULL DEFAULT 2
checksum STRING(64) NULL
```

新增 unique：

```text
(workflow_key, version)
```

历史 rows：

```text
workflow_key = template_key ? "legacy." + template_key : "legacy.workflow.<id>"
version = 1
schema_version = 1
status = enabled ? published : archived
```

不把旧 Definition 自动转换成新 Plugin schema；通过 loader compatibility adapter 读取。

---

## Decision 5 — WorkflowRun 冻结 Definition 身份

`WorkflowRun` 新增 nullable：

```text
topic_id
channel
content_form
workflow_key
workflow_version
definition_checksum
```

新 V1 多平台生产：

> 一个 `Platform × ContentForm` = 一个独立 WorkflowRun。

不再用一个新 Run 串行推进所有渠道。

旧 `gen_export` 历史 Run 保留。

---

## Decision 6 — Node Registry 替代 HANDLERS 中央 Map

新增：

```text
apps/api/app/services/content_harness/registry.py
apps/api/app/services/content_harness/contracts.py
apps/api/app/services/content_harness/nodes/
```

接口：

```python
class NodePlugin(Protocol):
    key: str
    version: str
    human_gate: bool

    def execute(
        self,
        db: Session,
        ctx: WorkflowExecutionContext,
        config: dict,
        user: User,
    ) -> NodeResult: ...
```

Human node 可实现：

```python
complete(...)
```

旧 handler 首先薄包装为 Built-in Node Plugin：

```text
builtin.connector_pull@1
builtin.extract_facts@1
builtin.factpack_freeze@1
builtin.topic_suggest@1
builtin.generate@1
builtin.humanize@1
builtin.content_censor@1
builtin.fact_check@1
builtin.approve@1
builtin.export@1
builtin.generate_cover@1
```

`workflow_engine.py` 只调用：

```python
registry.resolve(kind="node", key=..., version=...)
```

---

## Decision 7 — Workflow Definition schema v2

节点：

```json
{
  "id": "write",
  "plugin": "node.skill",
  "plugin_version": "1",
  "label": "雪球量化写作",
  "config": {
    "skill": "studio-xueqiu-article",
    "skill_version": "1.0.0"
  },
  "layout": {"x": 0, "y": 0}
}
```

兼容 schema v1：

```json
{"id":"gen","type":"generate","params":{}}
```

loader 在内存中映射：

```text
type=generate → builtin.generate@1
```

不迁移重写历史 JSON。

---

## Decision 8 — WorkflowStep 保存执行版本和 Hash

新增：

```text
plugin_key STRING(150)
plugin_version STRING(50)
input_hash STRING(64)
output_hash STRING(64)
stale_reason TEXT
attempt_no INTEGER DEFAULT 0
```

status 扩展：

```text
pending
running
waiting_input
succeeded
failed
skipped
stale
```

---

## Decision 9 — Material Library 使用 Material + MaterialRevision，DraftMedia 变为 Use/Placement

新增：

### `material`

```text
id
kind                  # image/chart/screenshot/video/audio/brand/other
title
tags_json
status                # active/archived
created_by
created_at
```

### `material_revision`

```text
id
material_id FK
revision_no
parent_revision_id FK nullable
status                # candidate/usable/revoked/archived
source_kind            # upload/web_search/ai_generated/chart/screenshot/upstream/legacy
source_url
source_metadata_json
content_hash
file_path
mime_type
width
height
duration_ms nullable
rights_status
public_use_allowed
model_use_allowed
commercial_use_allowed nullable
attribution_text
provider_key
provider_version
prompt_text
metadata_json
created_by
created_at
```

unique：

```text
(material_id, revision_no)
content_hash index
```

### DraftMedia 扩展

保留现有 fields，并新增：

```text
material_revision_id FK nullable
placement_json JSON nullable
alt_text TEXT nullable
caption TEXT nullable
```

旧 DraftMedia 没有 material_revision_id 仍可读。

新上传流程：

```text
Material
→ MaterialRevision
→ DraftMedia(use)
```

不再让同一文件只能属于一个 Draft。

---

## Decision 10 — AssetMedia 进入 Legacy Compatibility

`AssetMedia` 不删除。

但新 V1 受控内容：

```text
DraftMedia / MaterialRevision
→ Candidate Manifest
```

为唯一批准真源。

`/assets/{id}/media`：

- 新 Candidate 读取 candidate manifest / material revision；
- legacy asset 才 fallback 到旧 `AssetMedia` 懒生成。

禁止新正式 Candidate 把 SVG placeholder 当实际 media。

---

## Decision 11 — Draft 增加 Artifact / ContentForm / Document

`Draft` 新增：

```text
artifact_kind STRING(20) DEFAULT 'text'
content_form STRING(50) NULL
document_schema_version INTEGER DEFAULT 1
document_json JSON NULL
```

V1 artifact kinds：

```text
text
image
script
```

预留但不实现：

```text
video
audio
```

Document v1：

```json
{
  "blocks": [
    {"id":"p1","type":"paragraph","text":"..."},
    {
      "id":"img1",
      "type":"image",
      "draft_media_id":123,
      "material_revision_id":88,
      "alt":"...",
      "caption":"..."
    }
  ]
}
```

Markdown 仍作为文本可编辑真源。

`document_json` 的作用是保存：

- 图片位置；
- 卡片顺序；
- 结构；
- 平台 Render 所需的 composition。

---

## Decision 12 — 新建通用 DraftCheckRun

新增：

```text
draft_check_run
```

字段：

```text
id
draft_id
check_kind              # fact/platform/safety/rights/seo/domain/media
profile_key
profile_version
input_hash
status                  # pass/warning/blocker/incomplete/stale
report_json
provider_key nullable
provider_version nullable
created_at
```

索引：

```text
(draft_id, check_kind, created_at)
```

当前 `Draft.fact_check_json`：

- 继续写，保持兼容；
- 同时镜像写一条 `DraftCheckRun(check_kind='fact')`；
- 新 Review Gate 统一读取 `DraftCheckRun`。

---

## Decision 13 — Rule Registry 是代码/插件 Registry，不需要 Rule DB

新增：

```text
apps/api/app/services/content_harness/rules.py
```

接口：

```python
class Rule(Protocol):
    key: str
    version: str
    def evaluate(ctx) -> RuleResult: ...
```

RuleSet 在 Channel Profile / Workflow config 中以 key 引用。

先内置：

```text
rule.fact.bound
rule.media.public_rights
rule.media.required
rule.media.order
rule.platform.required_fields
rule.finance.as_of
rule.finance.no_return_guarantee
rule.tech.code_provenance
rule.seo.required_fields
```

不使用 LLM 实现可确定性规则。

---

## Decision 14 — Discoverability 是独立 Profile + Report

新增：

### `DiscoverabilityProfileVersion`

```text
id
profile_key
version
channel
content_form
config_json
status
checksum
created_at
```

unique：

```text
(profile_key, version)
```

### `DiscoverabilityReport`

```text
id
topic_id nullable
mother_revision_id nullable
draft_id nullable
stage                  # pre / post
channel
content_form
profile_version_id
input_hash
status                 # ready/incomplete/stale/failed
report_json
model_provider nullable
model_name nullable
created_at
```

---

## Decision 15 — Discoverability Provider 使用现有 LLM Route

`providers.ROUTE_KEYS` 新增：

```text
discoverability
```

新增 service：

```text
apps/api/app/services/discoverability.py
```

Pre：

```text
FactPack + Topic
→ search_intent
→ primary_queries
→ secondary_queries
→ entities
→ questions
→ content_gaps
→ outline_suggestions
```

Post：

```text
Draft
→ title suggestions
→ keyword/entity coverage
→ description
→ tags
→ alt suggestions
→ issues
```

SEO 不自动改最终 Draft。

如果用户应用建议：

```text
产生新 Draft Revision
→ downstream stale
```

---

## Decision 16 — Skill Registry 扩展 metadata，但不复制第三方代码

`plugin_registry.py` 读取 frontmatter：

```text
name
description
version
license
kind
capabilities
```

缺字段：

```text
version = "unversioned"
license = "unknown"
kind = "skill"
```

Settings 显示：

```text
source/path/version/license/enabled/vetted
```

新增内部 `PluginDescriptor` contract。

V1 不需要把所有第三方 Skill vendor 进 repo。

---

## Decision 17 — Skill Execution 与 Discovery 分离

新增：

```text
apps/api/app/services/content_harness/skill_runtime.py
```

协议：

```python
class SkillRuntime(Protocol):
    def execute(
        skill: PluginDescriptor,
        input_payload: dict,
        timeout_sec: int,
    ) -> SkillExecutionResult: ...
```

V1 要求：

- Built-in skill adapter；
- External runtime contract；
- dsh adapter 只有在实际本地 DSH invocation contract 被核实后才实现；
- 禁止猜测不存在的 DSH HTTP endpoint；
- 如果外部 Skill 只有“产出后回调”，继续使用 `ExternalContent` ingest 做兼容。

Workflow preflight 必须在运行前发现：

```text
required skill not installed/enabled
```

而不是运行中 ImportError。

---

## Decision 18 — Candidate Manifest schema v2

`services/candidates.py` 新增 schema v2：

```json
{
  "schema_version": 2,
  "artifact_kind": "text",
  "content_form": "article",
  "channel": "wechat",

  "source": {
    "topic_id": 1,
    "mother_revision_id": 2,
    "evidence_checksum": "..."
  },

  "content": {
    "title": "...",
    "body_markdown": "...",
    "document": {...},
    "structured": {...}
  },

  "media": [
    {
      "draft_media_id": 1,
      "material_revision_id": 8,
      "hash": "...",
      "role": "cover",
      "sort_order": 0,
      "placement": {...},
      "alt_text": "...",
      "caption": "...",
      "rights": {...}
    }
  ],

  "checks": [
    {
      "id": 9,
      "kind": "fact",
      "input_hash": "...",
      "status": "pass"
    }
  ],

  "discoverability": {
    "report_id": 11,
    "input_hash": "...",
    "profile": "seo.wechat.article@1"
  },

  "render": {
    "renderer_key": "renderer.wechat.article",
    "renderer_version": "1",
    "content_hash": "...",
    "payload": {...}
  },

  "execution": {
    "workflow_key": "...",
    "workflow_version": 1,
    "workflow_checksum": "...",
    "plugins": [...]
  },

  "declarations": [],
  "citations": []
}
```

Candidate Hash 对整个 v2 manifest canonical JSON 计算。

---

## Decision 19 — Renderer Output 必须在批准前冻结

新增：

```text
apps/api/app/services/content_harness/renderers.py
```

renderer 接口：

```python
render(candidate_source) -> RenderResult
```

RenderResult：

```text
renderer_key
version
payload
content_hash
warnings
```

公众号 HTML、X Thread JSON、小红书 Card Manifest 等都在 Approval 前生成。

Publisher 不再临时进行实质格式变换。

---

## Decision 20 — DeliveryAction 扩展

`DeliveryAction`：

```text
manual_handoff       # legacy alias
copy_package
assisted_draft
auto_draft
```

V1 不加：

```text
auto_public_publish
```

---

## Decision 21 — DeliveryTarget DB 约束从硬编码平台改为服务层能力验证

移除：

```text
ck_delivery_target_channel channel IN ('wechat','x_thread')
ck_delivery_target_action action='manual_handoff'
```

替换为 action status check：

```text
action IN (
  'manual_handoff',
  'copy_package',
  'assisted_draft',
  'auto_draft'
)
```

平台/content_form/action 合法性由：

```text
ChannelRegistry
PublisherRegistry
```

共同验证。

原因：

> SQLite/PostgreSQL 的 CheckConstraint 不应成为新增渠道必须修改 migration 的原因。

---

## Decision 22 — 新增 DeliveryAttempt

字段：

```text
id
target_id
attempt_no
idempotency_key
publisher_key
publisher_version
request_hash
status              # prepared/running/succeeded/failed/unknown
remote_id
response_metadata_json
error
started_at
finished_at
```

unique：

```text
(target_id, attempt_no)
idempotency_key
```

执行顺序：

```text
1. validate target
2. persist attempt(prepared)
3. COMMIT
4. call publisher
5. persist result
```

超时无法确认：

```text
status = unknown
target = reconciliation_needed
```

不得自动 fallback 重发。

---

## Decision 23 — Publisher Registry

新增：

```text
apps/api/app/services/content_harness/publishers/
  __init__.py
  base.py
  copy_package.py
  wechat_wewrite.py
```

协议：

```python
class PublisherPlugin(Protocol):
    key: str
    version: str

    def capability(account, channel, content_form) -> Capability: ...
    def deliver(candidate, target, attempt) -> PublisherResult: ...
```

首批：

```text
publisher.copy@1
publisher.wechat.wewrite@1
```

第三方 Wechatsync 等后续可作为 external runtime publisher plugin。

---

## Decision 24 — 公众号草稿移出 Workflow Engine 副作用

删除新流程对：

```text
workflow_engine._h_publish_wechat
```

的依赖。

旧 node 保留 legacy guard，只读历史。

新流程：

```text
Approved Candidate
→ DeliveryTarget(action=auto_draft)
→ DeliveryAttempt
→ publisher.wechat.wewrite
→ remote media_id
```

Publisher 使用 **批准 render payload**，不得：

- 临时改 title；
- 临时改正文；
- 临时换封面。

若平台长度限制需要变化：

```text
Candidate invalid
→ 用户修订
→ re-render
→ re-approve
```

---

## Decision 25 — Copy Package 成为通用 Publisher

`publisher.copy` 根据 Renderer 输出构建包：

```text
manifest.json
content.*
media/
publish-guide.md
```

不再在 `article_handoff.py` 写：

```python
if channel == "wechat": ...
else: x_thread ...
```

不同平台 package 由 renderer 定义文件清单。

---

## Decision 26 — Review & Publish Center 是 Projection，不建重复状态表

新增聚合 Router：

```text
apps/api/app/routers/review_center.py
```

不新增 ReviewCenter DB 表。

Endpoint 通过既有：

```text
Topic
WorkflowRun
Draft
DraftCheckRun
DraftMedia
ContentAsset
DeliveryTarget
```

组装视图。

---

## Decision 27 — Node-level Rerun

新增 API：

```text
POST /api/v1/workflow-runs/{run_id}/nodes/{node_id}/rerun
POST /api/v1/workflow-runs/{run_id}/nodes/{node_id}/rerun-from-here
```

`rerun`：

- 当前 node 新 attempt；
- 成功且 output hash 变化后 downstream 标 stale；
- 不自动重跑 downstream。

`rerun-from-here`：

- 当前及 downstream 变 pending；
- 不回滚历史实体；
- 产生新 Draft/Check/Render Revision。

禁止自动重跑 Publisher external side-effect node。

---

## Decision 28 — Staleness Service

新增：

```text
apps/api/app/services/content_harness/staleness.py
```

职责：

```text
mark_draft_changed(...)
mark_media_changed(...)
mark_discoverability_changed(...)
invalidate_candidate(...)
mark_workflow_downstream_stale(...)
```

现有散落的：

```text
candidate_readiness = "stale"
fact_check_json = None
```

逐步统一调用该服务。

---

# 5. 数据库迁移设计

建议拆成三次 Alembic migration，减少一次改动面。

---

## Migration A — Harness / Workflow / Checks

建议文件语义：

```text
add_v1_content_harness_registry.py
```

修改：

### `channel_template_version`

```text
+ profile_schema_version INTEGER DEFAULT 1 NOT NULL
+ profile_json JSON NULL
```

### `workflow`

```text
+ workflow_key VARCHAR(120)
+ version INTEGER DEFAULT 1 NOT NULL
+ parent_id INTEGER FK workflow.id
+ status VARCHAR(20) DEFAULT 'draft'
+ schema_version INTEGER DEFAULT 1 NOT NULL
+ checksum VARCHAR(64)
```

unique：

```text
(workflow_key, version)
```

### `workflow_run`

```text
+ topic_id INTEGER nullable
+ channel VARCHAR(30) nullable
+ content_form VARCHAR(50) nullable
+ workflow_key VARCHAR(120) nullable
+ workflow_version INTEGER nullable
+ definition_checksum VARCHAR(64) nullable
```

### `workflow_step`

```text
+ plugin_key VARCHAR(150)
+ plugin_version VARCHAR(50)
+ input_hash VARCHAR(64)
+ output_hash VARCHAR(64)
+ stale_reason TEXT
+ attempt_no INTEGER DEFAULT 0 NOT NULL
```

### `draft`

```text
+ artifact_kind VARCHAR(20) DEFAULT 'text'
+ content_form VARCHAR(50)
+ document_schema_version INTEGER DEFAULT 1
+ document_json JSON
```

### `draft_check_run`

create table as above.

Backfill：

- old Workflow = schema v1
- old Draft artifact_kind:
  - douyin -> `script`
  - others -> `text`
- old content_form:
  - wechat -> `article`
  - xiaohongshu -> `image_note`
  - douyin -> `spoken_script`
  - x_thread -> `thread`

不修改旧 candidate hash。

---

## Migration B — Material Library / SEO

建议语义：

```text
add_v1_material_and_discoverability.py
```

create：

```text
material
material_revision
discoverability_profile_version
discoverability_report
```

modify `draft_media`：

```text
+ material_revision_id
+ placement_json
+ alt_text
+ caption
```

不批量把旧 DraftMedia 复制成新 Material。

只在首次编辑/复用时执行显式 adoption。

原因：

> Migration 不应伪造原素材 provenance。

---

## Migration C — Delivery Router

建议语义：

```text
generalize_delivery_targets.py
```

create：

```text
delivery_attempt
```

modify `delivery_target`：

```text
+ publisher_key
+ publisher_version
+ capability_snapshot_json
+ requested_at
```

重建 SQLite check constraints：

- 删除 channel enum check；
- action 允许四种；
- status 扩展通用状态。

PostgreSQL 同步更新 constraint。

历史 target：

```text
publisher_key = "publisher.copy.legacy"
action = manual_handoff
```

不改变历史 receipt。

---

# 6. Backend 文件级改动清单

## 6.1 `apps/api/app/models.py`

必须：

- 增加 migration 对应字段/模型；
- 新增 enums：
  - `ArtifactKind`
  - `CheckKind`
  - `CheckStatus`
  - `MaterialKind`
  - `MaterialRevisionStatus`
  - `MaterialSourceKind`
  - 扩展 `DeliveryAction`
  - 扩展通用 Delivery status；
- relationship：
  - Material → revisions
  - DraftMedia → MaterialRevision
  - Draft → check_runs
  - Draft → discoverability reports
  - Target → attempts

不得：

- 删除现有 M1 字段；
- 修改旧 candidate hash；
- 将历史 AssetMedia 自动变成 MaterialRevision。

---

## 6.2 新建 `services/content_harness/contracts.py`

定义：

```text
PluginDescriptor
NodeResult
WorkflowExecutionContext
RuleResult
RenderResult
PublisherCapability
PublisherResult
MaterialSearchResult
SkillExecutionResult
```

禁止各模块自行发明不同结构。

---

## 6.3 新建 `services/content_harness/registry.py`

统一注册：

```text
node
rule
renderer
publisher
asset_provider
material_search
skill_runtime
```

API：

```python
register(kind, key, version, provider)
resolve(kind, key, version)
list(kind)
```

同一 `(kind,key,version)` 重复注册直接报错。

---

## 6.4 新建 `services/content_harness/channel_registry.py`

负责：

- 读取 published `ChannelTemplateVersion.profile_json`；
- fallback legacy template；
- validate channel；
- validate content form；
- 提供 Workflow / Rule / SEO / Renderer / Publisher 配置。

---

## 6.5 `routers/templates.py`

修改：

- Channel Template UI/API 语义提升为 Channel Profile；
- `TemplateIn` 增加 `profile_json`；
- publish checksum 包含 `profile_json`；
- clone 完整复制；
- 保留原 endpoints；
- 增加 profile schema validation。

`normalize_template_publication`：

- 不再遍历 `models.Channel`；
- 查询 DB distinct channel。

---

## 6.6 `seed.py`

删除三渠道固定作为唯一渠道来源的假设。

保留 legacy seed，并新增 V1 profile seeding：

```text
wechat
toutiao
baijia
zhihu
bilibili
sohu
penguin
netease
xiaohongshu
x
weibo
xueqiu
juejin
douyin
```

注意：

```text
zhihu.article
zhihu.answer
x.single
x.thread
```

由 `profile_json.content_forms` 区分。

Seed 必须幂等。

---

## 6.7 `routers/topics.py`

删除：

```python
VALID_CHANNELS = {...}
```

创建/更新 Topic 时调用：

```python
channel_registry.validate_selection(...)
```

Topic request 建议升级：

```json
"targets": [
  {"channel":"zhihu","content_form":"article"},
  {"channel":"zhihu","content_form":"answer"}
]
```

兼容旧：

```json
"channels": ["wechat"]
```

旧 `channels` 继续保存/读取；新字段建议新增：

```text
TopicBrief.targets_json
```

migration 可放 A。

---

## 6.8 `models.TopicBrief`

新增：

```text
targets_json JSON nullable
product_ref VARCHAR(100) nullable
business_line VARCHAR(100) nullable
```

不要删除 `channels`。

新 Topic 同时：

- `targets_json` 为真源；
- `channels` 写去重后的兼容值。

---

## 6.9 `services/generation/orchestrator.py`

修改：

- `create_jobs_for_topic()` 接 target `{channel, content_form}`；
- 不再校验 `models.Channel`；
- 从 ChannelRegistry 解析：
  - channel profile version
  - workflow
  - content form
- `ContentJob` 新增：
  - `content_form`
  - `artifact_kind`
  - `workflow_run_id`
  - `channel_profile_version_id`
- generation body 不再直接依赖 renderer dict。

现有 direct `/topics/{id}/generate` 可以作为 legacy shortcut：

```text
internally instantiate/reuse channel workflow
```

V1 新生产入口优先 Workflow。

---

## 6.10 `generation/renderers.py`

拆职责。

保留：

```text
topic_brief_text
brand_voice_text
legacy render
```

新平台 Render 移到：

```text
services/content_harness/renderers.py
```

旧三渠道 adapter 注册：

```text
renderer.legacy.douyin
renderer.legacy.xhs
renderer.wechat.article
```

禁止继续扩充：

```python
renderer = {channel: func}
```

作为新平台机制。

---

## 6.11 `templates.py:sync_prompt_versions_from_files`

当前只遍历：

```text
douyin
xiaohongshu
wechat
```

V1 修改为：

- 遍历 prompts 目录实际文件；
- 或由 profile 显式声明 built-in prompt；
- 不通过 Channel enum 控制。

外部 Skill 自己拥有 prompt 时，不强行建立 PromptVersion。

Workflow/Candidate 记录 Skill version 即可。

---

## 6.12 `services/plugin_registry.py`

frontmatter parser 增加：

```text
version
license
kind
capabilities
```

返回：

```json
{
  "name": "...",
  "version": "...",
  "license": "...",
  "kind": "skill",
  "capabilities": [],
  "path": "...",
  "source": "local"
}
```

不要读取 Skill body 当系统指令。

---

## 6.13 `services/system_settings.py`

Plugins view 增加：

```text
registry status
version
license
vetted flag
capabilities
```

新增 runtime settings keys（如需要）：

```text
publishers
material_providers
discoverability
```

但 Secret 继续脱敏。

---

## 6.14 新建 `services/materials.py`

职责：

```text
create_material
create_revision
adopt_draft_media
attach_to_draft
revoke_rights
find_usage
read_bytes_checked
```

所有新正式素材写入都通过该服务。

文件存储继续复用当前 `MEDIA_ROOT` / object storage abstraction。

V1 不要求立即迁移到 S3-only。

---

## 6.15 新建 `routers/materials.py`

Endpoints：

```text
GET    /api/v1/materials
POST   /api/v1/materials/upload
GET    /api/v1/materials/{id}
GET    /api/v1/materials/{id}/revisions
POST   /api/v1/materials/{id}/revisions/{rid}/revoke-public-use

POST   /api/v1/materials/search
POST   /api/v1/materials/generate

POST   /api/v1/drafts/{draft_id}/materials
PATCH  /api/v1/drafts/{draft_id}/materials/{draft_media_id}
DELETE /api/v1/drafts/{draft_id}/materials/{draft_media_id}
```

`materials/search` 如果没有已配置 Provider：

```text
422 capability_unavailable
```

不能返回假数据。

---

## 6.16 `routers/article_handoff.py`

迁移职责：

保留：

- MotherRevision APIs
- legacy paths

逐步把：

- media
- target
- package
- receipt
- feedback

业务逻辑抽到：

```text
services/materials.py
services/delivery.py
```

旧 API 可调用新 Service 保持前端兼容。

---

## 6.17 新建 `services/checks.py`

统一：

```text
run_fact_check
run_rule_set
run_rights_check
run_platform_check
run_seo_check
current_checks_for_candidate
```

每次写 `DraftCheckRun`。

FactCheck 仍复用 `services/factchecker.py`。

---

## 6.18 `routers/generate.py`

`run_fact_check`：

- 继续写 `draft.fact_check_json`；
- 同时写 `DraftCheckRun`;
- old clients 不破。

`update_draft`：

- 调用 `staleness.mark_draft_changed(new_draft)`;
- document_json 不应静默复制成 valid；需要重建或明确继承无 media anchors 的部分。

增加：

```text
POST /drafts/{id}/checks/{kind}
GET  /drafts/{id}/checks
```

或新 `routers/checks.py`。

---

## 6.19 新建 `services/discoverability.py`

支持：

```text
run_pre_topic(...)
run_post_draft(...)
apply_suggestion(...)
```

不得自动写 Draft。

`apply_suggestion` 使用现有 Draft revision 机制创建新版本。

---

## 6.20 新建 `routers/discoverability.py`

Endpoints：

```text
POST /api/v1/topics/{topic_id}/discoverability/pre
GET  /api/v1/topics/{topic_id}/discoverability

POST /api/v1/drafts/{draft_id}/discoverability/post
GET  /api/v1/drafts/{draft_id}/discoverability

POST /api/v1/drafts/{draft_id}/discoverability/{report_id}/apply
```

---

## 6.21 `providers.py`

`ROUTE_KEYS` 增加：

```text
discoverability
platform_adaptation
```

如果 Skill 已处理平台写作，`platform_adaptation` 可不调用 LLM。

---

## 6.22 `services/candidates.py`

升级：

```text
build_manifest_v2
readiness_reasons_v2
candidate_hash
```

必须检查：

- required check kinds 都存在且 input_hash current；
- required material real bytes；
- rights；
- renderer output current；
- discoverability required fields；
- workflow/plugin version snapshot。

保留 schema v1 builder 用于 legacy M1 读取。

---

## 6.23 `routers/reviews.py`

Approve 改为：

```text
if manifest.schema_version == 2:
    use readiness_v2
else:
    legacy path
```

approval 仍生成 `ContentAsset`。

`ContentAsset` 建议新增：

```text
artifact_kind
content_form
render_payload_json
workflow_key
workflow_version
```

或以上全部放 candidate_manifest；为了查询性能建议前四字段实体列。

---

## 6.24 新建 `services/delivery.py`

职责：

```text
authorize_target
resolve_publisher
prepare_attempt
execute_attempt
mark_unknown
build_copy_package
record_receipt
```

唯一远端副作用入口。

---

## 6.25 新建 `routers/delivery.py`

Generic APIs：

```text
POST /api/v1/assets/{asset_id}/delivery-targets
GET  /api/v1/assets/{asset_id}/delivery-targets

POST /api/v1/delivery-targets/{target_id}/execute
GET  /api/v1/delivery-targets/{target_id}

GET  /api/v1/delivery-targets/{target_id}/package.zip

POST /api/v1/delivery-targets/{target_id}/receipt
POST /api/v1/delivery-targets/{target_id}/feedback
POST /api/v1/delivery-targets/{target_id}/reconcile
```

旧 `/article-handoff/...` 路径作为兼容 alias。

---

## 6.26 `workflow_engine.py`

重构目标：

- 保留 advance/start/complete 核心；
- handler resolve 走 Registry；
- schema v1 compatibility；
- 新运行 schema v2；
- 支持 stale；
- 支持 rerun；
- Publisher Node 不允许 generic retry。

不要把新平台逻辑写入 `workflow_engine.py`。

---

## 6.27 `workflow_templates.py`

当前文件保留 legacy template。

新增 catalog/standard workflow builders，建议：

```text
workflow.article.base
workflow.feed.article
workflow.zhihu.article
workflow.zhihu.answer
workflow.xhs.cards
workflow.social.post
workflow.social.thread
workflow.xueqiu.quant
workflow.juejin.tech
workflow.douyin.script
```

多个平台复用 Workflow，不复制代码。

---

## 6.28 `routers/workflows.py`

新增：

```text
GET  /workflows/catalog
POST /workflows/{id}/clone
POST /workflows/{id}/publish
POST /workflow-runs/{id}/nodes/{node_id}/rerun
POST /workflow-runs/{id}/nodes/{node_id}/rerun-from-here
GET  /workflow-runs?topic_id=&channel=&content_form=
```

新 Workflow publish 后 immutable。

---

## 6.29 `routers/external.py`

删除硬编码：

```python
CHANNELS = {"douyin","xiaohongshu","wechat","other"}
```

改用 ChannelRegistry。

允许：

```text
channel = other
```

作为无平台外部内容。

对于正式已知平台必须 validate。

---

## 6.30 `services/asset_media.py`

定位改为：

> Legacy approved-asset compatibility / preview helper。

新 Material 生产不再依赖：

```text
ensure_generated → placeholder SVG
```

正式 Candidate Readiness 不读取 placeholder。

---

## 6.31 `main.py`

注册新增 routers：

```text
materials
discoverability
delivery
review_center
channels
```

启动时：

- runtime config；
- prompt sync；
- channel profile validation；
- node/plugin registry bootstrap；
- 不主动联网；
- 不执行远端发布。

---

# 7. Review & Publish Center Backend

新建：

```text
routers/review_center.py
services/review_center.py
```

## 7.1 Aggregate Endpoint

```text
GET /api/v1/review-center/topics/{topic_id}
```

输出：

```json
{
  "topic": {...},
  "content_core": {...},
  "targets": [
    {
      "channel": "xueqiu",
      "content_form": "quant_research",
      "workflow_run": {...},
      "draft": {...},
      "checks": {...},
      "discoverability": {...},
      "materials": [...],
      "candidate": {...},
      "approval": {...},
      "delivery": {...},
      "readiness": {
        "content": "ready",
        "evidence": "ready",
        "media": "warning",
        "platform": "ready",
        "delivery": "not_authorized"
      }
    }
  ]
}
```

Readiness 是 projection，不新增 DB 状态副本。

---

# 8. Frontend 文件级改动

## 8.1 `App.tsx`

导航建议调整：

```text
总览
来源与证据
选题
生产工作台
素材库
审核与发布
内容资产
工作流
模板 / Profiles
Skills & Plugins
设置
```

旧 `/review`、`/handoff` 可以先保留 route alias。

新增：

```text
/materials
/review-publish
/review-publish/:topicId
```

---

## 8.2 `Topics.tsx`

删除本地 `CHANNELS` 常量。

查询：

```text
GET /channels
```

选择 target：

```text
channel + content_form
```

UI 必须允许：

```text
知乎文章
知乎回答
```

同时选择。

---

## 8.3 `Workspace.tsx`

升级：

- Channel tab 由 Topic targets 动态生成；
- 展示 content_form；
- 展示 Workflow Run；
- 编辑保存保留 revision；
- 增加：
  - Rerun Node
  - Rerun From Here
  - SEO report
  - Material inline anchors
- 不承担最终 Approval/Delivery 复杂动作；跳 Review Center。

---

## 8.4 新建 `pages/Materials.tsx`

功能：

- Grid/List；
- Upload；
- Search；
- Generate；
- filters；
- rights；
- revision；
- used_by；
- attach。

Material Search 无 provider 时显示：

```text
未配置可用素材搜索 Provider
```

---

## 8.5 重构 `Review.tsx` + `Handoff.tsx`

建议创建：

```text
pages/ReviewPublish.tsx
```

逐步吸收两者功能。

布局：

```text
Left: channel/content form
Center: final preview/editor/material
Right: checks/SEO/workflow/delivery
Bottom: workflow timeline/actions
```

旧页面可 redirect / legacy display。

---

## 8.6 `Assets.tsx`

定位：

> Approved Content Assets / historical library。

删除“批准后再补正式素材”的主流程语义。

对于 schema v2 asset：

- media 来自 candidate manifest；
- 不允许直接修改 approved media；
- 编辑必须回到 Draft/Topic 创建新 Candidate。

---

## 8.7 `Workflows.tsx`

修改：

- Node label 不再硬编码所有 Node type；
- 由 registry descriptor / workflow definition label 展示；
- 支持 plugin key/version；
- 支持 stale status；
- 支持 rerun/rerun from here；
- new run 以单 target 为主；
- legacy multi-channel run 继续可读。

---

## 8.8 `Templates.tsx`

重命名产品语义：

```text
Profiles
```

至少展示：

- Brand Voice
- Channel Profile
- Discoverability Profile
- Prompt Version

Workflow 单独在 Workflows 管理。

---

## 8.9 `Settings.tsx`

Plugins 区增加：

```text
Version
License
Kind
Capabilities
Enabled
Vetted
Source
```

Provider 区后续显示：

```text
Image
Material Search
Publisher
```

但 V1 可以只读 Registry，配置入口分阶段交付。

---

# 9. Platform Profiles V1

首批需要建 profile，不代表每个平台 Auto Draft 已验证。

建议 channel keys：

```text
wechat
toutiao
baijia
zhihu
bilibili
sohu
penguin
netease
xiaohongshu
x
weibo
xueqiu
juejin
douyin
```

---

## 9.1 Shared Workflow families

### `workflow.article.editorial`

用于：

```text
wechat
zhihu article
bilibili column
```

### `workflow.article.feed`

用于：

```text
toutiao
baijia
sohu
penguin
netease
```

### `workflow.qa.answer`

用于：

```text
zhihu answer
```

### `workflow.image.cards`

用于：

```text
xiaohongshu
```

### `workflow.social.short`

用于：

```text
weibo
x single
```

### `workflow.social.thread`

用于：

```text
x thread
```

### `workflow.finance.article`

用于：

```text
xueqiu
```

### `workflow.tech.article`

用于：

```text
juejin
```

### `workflow.script.spoken`

用于：

```text
douyin script
```

---

## 9.2 Suggested standard node sequences

### Editorial

```text
adapt_from_core
→ platform_writer
→ discoverability_pre/post
→ material_plan
→ material_prepare
→ fact_check
→ rule_check
→ render
→ human_review
```

### Feed

```text
adapt_from_core
→ feed_writer
→ discoverability
→ material_prepare
→ fact_check
→ platform_rules
→ render
→ human_review
```

### XHS

```text
atomize
→ xhs_writer
→ card_plan
→ material_prepare
→ card_render
→ fact_check
→ rights_check
→ discoverability
→ human_review
```

### Xueqiu

```text
finance_adapt
→ xueqiu_writer
→ finance_rules
→ chart/material_prepare
→ fact_check
→ discoverability
→ render
→ human_review
```

### Juejin

```text
tech_adapt
→ juejin_writer
→ code_provenance_rules
→ screenshot/material_prepare
→ fact_check
→ discoverability
→ render
→ human_review
```

---

# 10. OpenSpec Requirements

## Capability: `content-harness-registry`

### Requirement: Channel selection uses one registry

系统 SHALL 使用单一 Channel Registry 校验 Topic target、Generation、Workflow、Renderer、Delivery，不得让前后端维护互相独立的合法渠道集合。

#### Scenario: 新增平台配置

- **WHEN** admin 发布一个合法的新 Channel Profile
- **THEN** Topic target selector、Workflow target validation 和 Delivery capability 均从 Registry 读取
- **AND** 不要求修改 `models.Channel` 才能识别新平台

---

### Requirement: Runtime plugin resolution is version-pinned

系统 MUST 对新 Workflow Node 保存 plugin key/version，并在运行时按该版本解析。

#### Scenario: Skill 后续升级

- **WHEN** `studio-xueqiu-article` 从 1.0 升到 1.1
- **THEN** 历史 WorkflowRun 仍显示并引用 1.0
- **AND** 新 Workflow Version 才使用 1.1

---

## Capability: `versioned-channel-workflow`

### Requirement: Workflow definitions are immutable after publish

- **WHEN** published Workflow 被修改
- **THEN** 系统创建新 Workflow Version
- **AND** 历史 Run 的 definition checksum 不变化

### Requirement: Platform branches are independent

- **WHEN** 同一 Topic 选择多个 target
- **THEN** 每个 `channel × content_form` 创建独立 WorkflowRun
- **AND** 一个 Run failed/waiting 不改变其他 Run

---

## Capability: `material-library-v1`

### Requirement: Actual media is globally reusable

- **WHEN** 用户上传一张图片
- **THEN** 系统建立 Material + MaterialRevision
- **AND** 多个 Draft 可以通过 DraftMedia 引用同一个 MaterialRevision

### Requirement: Web-found media starts as candidate

- **WHEN** Material Search Provider 返回一张网络图片
- **THEN** 系统保存 source URL/provenance/rights 状态
- **AND** 在 `public_use_allowed != true` 前不能满足 Candidate media readiness

### Requirement: Approved material bytes are immutable

- **WHEN** MaterialRevision 已被 approved Candidate 引用
- **THEN** 替换/编辑必须产生新 Revision
- **AND** 历史 Candidate 可按旧 hash 重建

---

## Capability: `artifact-composition-v1`

### Requirement: Text candidate preserves image placement

- **WHEN** 用户把某张图片移动到另一段之后
- **THEN** Draft document/placement 产生新版本
- **AND** prior Candidate 不变化
- **AND** Render/Candidate 标 stale

### Requirement: Placeholder is not final media

- **WHEN** draft 只有 image prompt / generated placeholder SVG
- **THEN** required actual-media rule 返回 blocker/incomplete
- **AND** 不得批准为最终图文成品

---

## Capability: `unified-check-runs`

### Requirement: All mandatory checks are input-bound

- **WHEN** draft body/material/SEO metadata 改变
- **THEN** 受影响 check run 标 stale
- **AND** Review Center 不显示旧 pass 为当前有效

### Requirement: Incomplete is not pass

- **WHEN** semantic checker、SEO checker 或 provider 执行失败/截断
- **THEN** 状态为 incomplete/failed
- **AND** mandatory check 不允许 Approval

---

## Capability: `discoverability-optimization`

### Requirement: Discoverability is a distinct stage

- **WHEN** 平台 Workflow 启用 SEO profile
- **THEN** 系统生成结构化 DiscoverabilityReport
- **AND** 不把 SEO 指令隐藏在普通 Writer Prompt 中作为唯一实现

### Requirement: SEO suggestion cannot mutate approved content

- **WHEN** 用户将 SEO 标题建议应用到 Draft
- **THEN** 创建新 Draft Revision
- **AND** downstream checks/render/candidate stale

---

## Capability: `workflow-rerun-staleness`

### Requirement: Node can rerun without resetting upstream

- **WHEN** 用户对一个纯生成 Node 选择 `Rerun Node`
- **THEN** 上游实体版本不变化
- **AND** 新 Node output 与旧 output 都可审计
- **AND** output 改变时 downstream stale

### Requirement: External side effect cannot be generic-rerun

- **WHEN** Node 属于 Publisher/remote side effect 且结果 failed/unknown
- **THEN** generic rerun API MUST reject
- **AND** 用户通过 Delivery reconciliation/retry contract 处理

---

## Capability: `unified-review-publish-center`

### Requirement: Review Center is a projection

- **WHEN** 用户打开一个 Topic
- **THEN** 页面聚合每个目标的 draft/check/media/SEO/candidate/delivery
- **AND** 不创建第二份 approval/delivery state

### Requirement: Approval sees actual final payload

- **WHEN** reviewer approves
- **THEN** title/body/document/actual media/order/placement/SEO/render/check versions 都进入 Candidate manifest
- **AND** Candidate Hash 与实际交付包一致

---

## Capability: `delivery-router-v1`

### Requirement: Delivery target resolves explicit action

- **WHEN** 用户选择“交付”
- **THEN** 系统按 account capability 选择/展示 `copy_package / assisted_draft / auto_draft`
- **AND** 不将 unavailable action 显示为可执行

### Requirement: WeChat auto draft is candidate-bound

- **WHEN** approved WeChat Candidate 授权 `auto_draft`
- **THEN** 系统先创建并提交 DeliveryAttempt(prepared)
- **AND** publisher 使用批准 render payload 和批准媒体
- **AND** 成功保存 remote media_id

### Requirement: Timeout becomes unknown

- **WHEN** publisher 调用超时且无法确认远端结果
- **THEN** attempt=unknown
- **AND** target=reconciliation_needed
- **AND** 系统不得自动再次创建远端草稿

### Requirement: Copy package is universal fallback

- **WHEN** 平台没有 verified draft publisher
- **THEN** approved Candidate 至少可以生成格式完整的 Copy Package
- **AND** 包保留 media order/placement 和平台交付说明

---

## Capability: `v1-platform-artifacts`

### Requirement: Article and answer are separate content forms

- **WHEN** Topic 同时选择知乎文章和知乎回答
- **THEN** 系统创建两个独立 WorkflowRun/Draft
- **AND** Answer 使用 direct-answer 结构规则

### Requirement: Xueqiu finance rules are mandatory

- **WHEN** content form 是 quant / market recap
- **THEN** as_of / scope / risk / no-return-guarantee Rule Set 必须完成
- **AND** 未完成时不可批准

### Requirement: Juejin technical rules are mandatory

- **WHEN** content form 是 tech article
- **THEN** code/provenance/version/benchmark 条件按 profile 执行
- **AND** 无依据代码不得被标记为 verified runnable

### Requirement: Douyin remains script-only in V1

- **WHEN** 抖音 Script Candidate approved
- **THEN** package 可含 spoken script/scenes/B-roll brief/estimated SRT
- **AND** UI 明确显示 `script package`
- **AND** 不显示“视频成片 Ready”

---

# 11. 分阶段实施任务

下面顺序是强依赖顺序。不要并行修改同一基础对象。

---

## Phase 0 — Baseline / OpenSpec reconciliation

- [ ] 0.1 读取 `git_status` / `git_diff`，记录当前用户未提交文件，不 reset。
- [ ] 0.2 核对 `complete-prd-v1-channel-deliverables` 是否未实施；如果未实施，在文档中标 `superseded_by=align-v1-prd2-content-harness`，不要并行 apply。
- [ ] 0.3 将本 change 建到 `openspec/changes/align-v1-prd2-content-harness/`，按 OpenSpec schema 拆出 proposal/design/specs/tasks。
- [ ] 0.4 运行 `openspec validate ... --strict --no-interactive`。
- [ ] 0.5 运行当前 backend test baseline 并记录真实失败，不把既有失败归到新变更。

---

## Phase 1 — Channel Registry + Workflow Versioning

### Backend

- [ ] 1.1 修改 `models.py`：ChannelTemplate profile fields、Topic targets_json、Workflow version fields、Run/Step metadata。
- [ ] 1.2 Alembic Migration A，覆盖 SQLite + PostgreSQL constraints/backfill。
- [ ] 1.3 新建 `content_harness/contracts.py`、`registry.py`、`channel_registry.py`。
- [ ] 1.4 修改 `templates.py` profile schema/publish checksum。
- [ ] 1.5 修改 `topics.py` 使用 registry，兼容 channels。
- [ ] 1.6 修改 `orchestrator.py` 去除 Channel enum 新渠道依赖。
- [ ] 1.7 修改 `workflow_engine.py`：schema v1 compatibility + registry resolve。
- [ ] 1.8 将现有 handler 包装 built-in plugins，不改变业务结果。
- [ ] 1.9 修改 `workflow_templates.py` 为 catalog，保留 legacy templates。
- [ ] 1.10 修改 `external.py` channel validation。
- [ ] 1.11 修改 `templates.sync_prompt_versions_from_files()` 去除 3-channel 固定遍历。

### Frontend

- [ ] 1.12 `Topics.tsx` 动态 Channel/ContentForm。
- [ ] 1.13 `Workflows.tsx` 动态 plugin descriptor、stale status。
- [ ] 1.14 `Templates.tsx` 展示 profile_json。

### Tests

新增：

```text
test_channel_registry.py
test_workflow_registry.py
```

覆盖：

- profile publish；
- duplicate content form；
- new channel 无 enum 修改；
- schema v1 workflow compatibility；
- published workflow immutable；
- run freezes version/checksum。

---

## Phase 2 — Material Library + Composition

### Backend

- [ ] 2.1 Alembic Migration B。
- [ ] 2.2 新建 Material models 和 relations。
- [ ] 2.3 新建 `services/materials.py`。
- [ ] 2.4 新建 `routers/materials.py`。
- [ ] 2.5 将 `article_handoff` draft upload 改为调用 materials service。
- [ ] 2.6 扩展 DraftMedia placement/alt/caption。
- [ ] 2.7 Draft 新增 document_json 操作 service。
- [ ] 2.8 新建 material/provider registry contract。
- [ ] 2.9 将 `writing_pipeline.generate_cover_image` 包装为 `asset_provider.wewrite_image@1`，旧函数继续兼容。
- [ ] 2.10 `AssetMedia` 标 legacy，新 schema v2 asset 禁止 placeholder ready。

### Frontend

- [ ] 2.11 新建 `Materials.tsx`。
- [ ] 2.12 Workspace 支持 attach/reorder/placement。
- [ ] 2.13 小红书卡片至少能显示真实有序图片。
- [ ] 2.14 Review Preview 读取 DraftMedia/MaterialRevision，不读取 placeholder 作为最终图。

### Tests

新增：

```text
test_material_library.py
test_artifact_composition.py
```

覆盖：

- upload → material revision；
- same material multi-draft reuse；
- rights；
- placement change stale；
- approved material cannot mutate；
- placeholder blocks ready；
- historical DraftMedia remains readable。

---

## Phase 3 — Generic Checks + SEO

### Backend

- [ ] 3.1 建 `DraftCheckRun`。
- [ ] 3.2 FactCheck 双写兼容。
- [ ] 3.3 新建 Rule Registry。
- [ ] 3.4 新建 Discoverability models/service/router。
- [ ] 3.5 `providers.ROUTE_KEYS` 增 `discoverability`。
- [ ] 3.6 建基础 discoverability profiles。
- [ ] 3.7 实现 common SEO deterministic rules。
- [ ] 3.8 finance / tech rules 首批落地。
- [ ] 3.9 更新 candidate readiness 从 generic checks 读取。

### Frontend

- [ ] 3.10 Workspace 展示 Pre/Post Discoverability。
- [ ] 3.11 支持 Apply SEO Suggestion → new Draft revision。
- [ ] 3.12 Review 显示 mandatory checks / incomplete。

### Tests

新增：

```text
test_checks_v2.py
test_discoverability.py
test_finance_rules.py
test_tech_rules.py
```

---

## Phase 4 — Candidate Manifest v2 + Render

### Backend

- [ ] 4.1 `candidates.py` 墠 schema v2 builder。
- [ ] 4.2 新建 renderer registry。
- [ ] 4.3 WeChat renderer 迁入 registry。
- [ ] 4.4 X Thread renderer。
- [ ] 4.5 generic article Markdown/rich copy renderer。
- [ ] 4.6 XHS card manifest renderer。
- [ ] 4.7 Candidate readiness Gate 4 层。
- [ ] 4.8 `reviews.py` schema v1/v2 dual path。
- [ ] 4.9 ContentAsset 保存 artifact/content_form/workflow/render summary。

### Tests

```text
test_candidate_manifest_v2.py
test_renderers_v2.py
```

必须验证：

- 同一 manifest canonical hash stable；
- media placement 变化 hash 改变；
- SEO metadata 变化 hash 改变；
- stale check 阻止 approve；
- old candidate v1 仍可读。

---

## Phase 5 — Delivery Router + WeChat Auto Draft

### Backend

- [ ] 5.1 Alembic Migration C。
- [ ] 5.2 新建 publisher contract/registry。
- [ ] 5.3 实现 `publisher.copy@1`。
- [ ] 5.4 将 wewrite publish 包装 `publisher.wechat.wewrite@1`。
- [ ] 5.5 新建 `services/delivery.py`。
- [ ] 5.6 新建 `routers/delivery.py`。
- [ ] 5.7 `article_handoff` legacy target APIs 改 delegate。
- [ ] 5.8 关闭新内容从 `workflow_engine.publish_wechat` 直接副作用的路径。
- [ ] 5.9 实现 attempt prepared-before-call。
- [ ] 5.10 unknown/reconciliation。
- [ ] 5.11 Copy Package 使用 renderer manifest。

### Tests

```text
test_delivery_router.py
test_wechat_auto_draft_delivery.py
```

WeChat 真实远端测试不能放默认 pytest。

默认测试必须 mock subprocess/provider，真实测试作为手工 acceptance script。

必须测试：

- duplicate execute 不重复 attempt；
- timeout -> unknown；
- unknown 不自动 retry；
- candidate mismatch；
- account change new target；
- copy package hash/media consistency。

---

## Phase 6 — Node Rerun + Staleness

### Backend

- [ ] 6.1 新建 `staleness.py`。
- [ ] 6.2 所有 Draft/Media/SEO 变更统一调用。
- [ ] 6.3 Workflow Step input/output hash。
- [ ] 6.4 rerun node。
- [ ] 6.5 rerun-from-here。
- [ ] 6.6 side-effect node generic rerun guard。
- [ ] 6.7 Run context 记录 latest output refs，但历史 output 不删除。

### Frontend

- [ ] 6.8 Workflows inspector 加两个重跑按钮。
- [ ] 6.9 Workspace / Review Center 显示 stale。
- [ ] 6.10 用户修改正文后明确提示需重跑哪些节点。

### Tests

```text
test_workflow_rerun.py
test_staleness.py
```

---

## Phase 7 — V1 Platform Profiles / Writer Skills

### Registry / Profiles

- [ ] 7.1 seed 14 个 channel profiles。
- [ ] 7.2 定义 shared workflow families。
- [ ] 7.3 将已有 wewrite / XHS Skills 作为推荐外部 Skill references。
- [ ] 7.4 建 built-in fallback writer nodes，避免外部 skill 缺失时静默用错误平台风格。

### Minimum platform acceptance

每个 target 至少：

```text
profile resolves
workflow instantiates
draft renders
required rules run
candidate builds
copy package builds
```

不要求远端自动发布。

### Golden cases

- [ ] 7.5 WeChat deep article
- [ ] 7.6 Toutiao feed article
- [ ] 7.7 Baijia search article
- [ ] 7.8 Zhihu article
- [ ] 7.9 Zhihu answer
- [ ] 7.10 Bilibili column
- [ ] 7.11 Sohu article
- [ ] 7.12 Penguin article
- [ ] 7.13 NetEase article
- [ ] 7.14 XHS cards
- [ ] 7.15 X single/thread
- [ ] 7.16 Weibo
- [ ] 7.17 Xueqiu market recap / quant
- [ ] 7.18 Juejin tech
- [ ] 7.19 Douyin script-only

---

## Phase 8 — Unified Review & Publish Center

### Backend

- [ ] 8.1 新建 `review_center.py` service/router。
- [ ] 8.2 Topic aggregate response。
- [ ] 8.3 readiness projection。
- [ ] 8.4 workflow timeline projection。
- [ ] 8.5 delivery capability projection。

### Frontend

- [ ] 8.6 新建 `ReviewPublish.tsx`。
- [ ] 8.7 左栏 target 状态。
- [ ] 8.8 中栏 final preview/editor/media。
- [ ] 8.9 右栏 Evidence/Checks/SEO/Delivery。
- [ ] 8.10 timeline。
- [ ] 8.11 Edit/Rerun/Upload/Generate/Approve/Deliver actions。
- [ ] 8.12 `Review.tsx` / `Handoff.tsx` 迁移为 alias / legacy view。

---

## Phase 9 — Docs / Acceptance / Migration Cleanup

- [ ] 9.1 更新 `README.md` 产品主链。
- [ ] 9.2 更新原 `03_ai_content_studio_PRD.md` 指向 V1 PRD 2.0 或明确 legacy。
- [ ] 9.3 更新 `HANDOVER.md`。
- [ ] 9.4 更新 `docs/WORKFLOW_CANVAS_DESIGN.md`：handler registry / one-target-run。
- [ ] 9.5 更新 runbook 备份与 Material bytes。
- [ ] 9.6 运行 fresh SQLite Alembic head。
- [ ] 9.7 增加 PostgreSQL migration smoke。
- [ ] 9.8 跑 backend full pytest。
- [ ] 9.9 跑 ruff。
- [ ] 9.10 跑 web TypeScript build。
- [ ] 9.11 运行 OpenSpec strict validation。
- [ ] 9.12 真实 WeChat 草稿验收。
- [ ] 9.13 至少一份 XHS 实际图片 Candidate。
- [ ] 9.14 至少一份雪球量化 Candidate。
- [ ] 9.15 至少一份掘金技术 Candidate。
- [ ] 9.16 记录每个平台 capability，未真实发布验证的保持 unverified。

---

# 12. 测试文件规划

现有测试不删除，新增建议：

```text
apps/api/tests/
  test_channel_registry.py
  test_workflow_registry.py
  test_workflow_rerun.py
  test_staleness.py
  test_material_library.py
  test_artifact_composition.py
  test_checks_v2.py
  test_discoverability.py
  test_finance_rules.py
  test_tech_rules.py
  test_candidate_manifest_v2.py
  test_renderers_v2.py
  test_delivery_router.py
  test_review_center.py
  test_platform_profiles.py
```

现有需扩展：

```text
test_core_pipeline.py
test_workflows.py
test_media_dsh.py
test_models_plugins.py
test_migrations.py
test_templates.py
test_external_ingest.py
```

---

# 13. 关键测试矩阵

| 场景 | Unit | Integration | Real |
|---|---:|---:|---:|
| Evidence freeze | ✅ | ✅ | |
| New channel profile | ✅ | ✅ | |
| Workflow version pin | ✅ | ✅ | |
| External skill missing | ✅ | ✅ | |
| Material upload/reuse | ✅ | ✅ | |
| Rights revoke | ✅ | ✅ | |
| Media placement | ✅ | ✅ | |
| SEO pre/post | ✅ | ✅ | |
| Draft changed stale | ✅ | ✅ | |
| Node rerun | ✅ | ✅ | |
| Candidate v2 | ✅ | ✅ | |
| WeChat copy package | ✅ | ✅ | |
| WeChat auto draft | mock | ✅ | ✅ |
| Unknown remote result | ✅ | ✅ | |
| XHS actual images | | ✅ | 人工 |
| Xueqiu finance | ✅ | ✅ | 人工 |
| Juejin technical | ✅ | ✅ | 人工 |
| Legacy M1 read | ✅ | ✅ | |

---

# 14. Migration / Backward Compatibility Requirements

## 14.1 必须保持可读

- 旧 Source；
- 旧 FactPack；
- 旧 3-channel Topic；
- 旧 Draft；
- 旧 AssetMedia；
- 旧 ContentAsset；
- 旧 Candidate Manifest v1；
- 旧 manual WeChat/X target；
- 旧 Workflow schema v1；
- 旧 ExportRecord。

---

## 14.2 不做的 Backfill

禁止自动：

- 给旧图片补 rights=true；
- 把 placeholder 变成 actual material；
- 把旧 draft 标 Candidate Ready；
- 把旧 workflow 标插件化 v2；
- 把旧 manual receipt 标 platform verified；
- 把旧 Export 标 Delivery success。

---

# 15. Security Requirements

## 15.1 Material

- 上传双校验 MIME + signature；
- 文件路径必须 content-addressed / 防 traversal；
- raw endpoint 对非公开素材要求鉴权；
- 网络素材下载复用 SSRF 防护；
- source URL 和 rights 分开。

注意：当前部分 `/assets/.../raw` 为 `<img>` 方便没有 Header 鉴权；新 Material API 不应默认复制这一模式。前端需要可鉴权 blob URL 或受控 signed URL。

---

## 15.2 Skills

- 不执行未 enabled 的 skill；
- 未 vetted skill 显示风险；
- 不把 secrets 注入 Skill prompt；
- Skill requested permissions 可展示；
- 外部 Skill 结果仍视为 untrusted data，进入正常检查链。

---

## 15.3 Publisher

- Publisher 只拿目标账号所需 Secret；
- Writer Skill 不获取发布 Secret；
- attempt 记录不能包含 token/cookie；
- remote response 只保存安全 metadata。

---

# 16. 性能与异步要求

以下 Node 默认应允许 Celery：

```text
LLM writer
Discoverability
Material Search
Image Generation
Renderer（重任务）
Publisher
```

但 Workflow Engine 不应同步 sleep 等待 420 秒作为长期模型。

当前 `_h_generate` 的同步轮询属于 legacy。

本 OpenSpec 后期应将新 v2 node execution：

```text
dispatch
→ step running
→ worker callback/status
→ engine continue
```

作为目标。

若此异步改造会显著扩大 Phase 1，允许先保留现有同步兼容，但：

- 新 Publisher 不得在 API request 中盲目长 retry；
- UI 必须轮询 Run；
- phase completion 文档要明确 async engine debt。

---

# 17. Rollout Strategy

不按“14 平台同时实现完成”发布。

建议内部 rollout：

## Milestone A — Harness Core

```text
Channel Registry
Workflow Registry
Material
Check
Candidate v2
```

先用：

```text
WeChat
X Thread
```

跑通。

---

## Milestone B — V1 High-value

加入：

```text
XHS
Xueqiu
Juejin
Zhihu article
Zhihu answer
```

原因：

- 覆盖图文；
- 财经；
- 技术；
- 问答；
- 社交。

---

## Milestone C — Feed Expansion

加入：

```text
Toutiao
Baijia
Sohu
Penguin
NetEase
Bilibili
Weibo
```

---

## Milestone D — Delivery Automation

逐个平台验证 Publisher。

未验证平台仍保留 Copy Package。

---

# 18. Completion Definition

本 OpenSpec 只有同时满足以下条件才可声明 V1 PRD 2.0 工程基础完成。

## Core

- [ ] Channel Registry 成为唯一新渠道合法性入口；
- [ ] Workflow v2 plugin resolve 生效；
- [ ] Material Library 可用；
- [ ] Draft composition 保存 actual media placement；
- [ ] Generic Check Run 生效；
- [ ] SEO/Discoverability 至少两类 profile 真实运行；
- [ ] Candidate Manifest v2 可重建；
- [ ] Content Approval / Delivery Authorization 分离；
- [ ] Copy Package 通用；
- [ ] WeChat Auto Draft 走 DeliveryAttempt；
- [ ] Node rerun/stale 生效；
- [ ] Review & Publish Center 可完成完整操作。

## Platform

- [ ] 所有 V1 platform/content form 能生成受控 Candidate 或明确显示 capability unavailable；
- [ ] 不允许“配置存在”被显示为“真实发布已验证”。

## Compatibility

- [ ] legacy data readable；
- [ ] existing three-channel tests preserved；
- [ ] M1 WeChat/X history preserved。

## Quality

- [ ] `pytest` 全绿（除记录且与本变更无关的既有环境失败）；
- [ ] migrations fresh SQLite + existing-upgrade test；
- [ ] PostgreSQL migration smoke；
- [ ] frontend build；
- [ ] OpenSpec strict validate；
- [ ] `git diff --check`。

---

# 19. Codex apply 建议批次

不要让一次 Codex 执行跨越全部 Phase。

建议一个 task 对应一个可验证批次：

```text
C2C-01 Channel/Workflow Registry
C2C-02 Material Library
C2C-03 Checks + Discoverability
C2C-04 Candidate v2 + Render
C2C-05 Delivery Router + WeChat
C2C-06 Rerun/Staleness
C2C-07 Platform Profiles
C2C-08 Review & Publish Center
C2C-09 Acceptance/Docs
```

每个批次完成后：

1. `EXECUTED`
2. 读取 execution output（如果可读）
3. git diff review
4. tests
5. 再进入下一批

不得只根据 Codex 自述判定完成。

---

# 20. 最终 HANDOFF

```text
GOAL
Implement AIContentStudio V1 PRD 2.0 as a Text + Image Content Harness
without replacing the existing modular monolith.

TRUST
1. Current code
2. This OpenSpec
3. V1 PRD 2.0 / North Star
4. Older alignment documents

REUSE
- FactPackItem frozen evidence
- MotherRevision
- Draft revision
- DraftMedia
- ContentAsset candidate hash
- DeliveryTarget/Receipt/Feedback
- Workflow/Run/Step
- LLM Provider routing
- Skill discovery / dsh config

DO NOT CREATE
- second content center
- second workflow engine
- second approval system
- second delivery state system
- video/TTS/digital-human implementation in V1

FIRST EXPECTED STEP
Phase 0, then Phase 1 only:
- verify dirty git state
- create/validate OpenSpec artifacts
- implement Channel Registry + Workflow version/plugin dispatch
- preserve legacy workflows
- run scoped backend/frontend tests
- report diff and test evidence before proceeding

CRITICAL INVARIANTS
- frozen evidence never drifts
- old revisions never overwritten
- actual media is approved, not prompts
- candidate hash covers public payload
- content approval != delivery authorization
- publisher cannot mutate approved content
- unknown remote result is not auto-retried
- adding a channel must not require editing workflow_engine
```
