## Why

当前系统已拥有可信证据（FactPackItem 冻结快照）、稿件版本（MotherRevision/Draft）、候选哈希（ContentAsset.approved_candidate_hash）、素材字节（DraftMedia）、工作流画布（Workflow/WorkflowRun/WorkflowStep）与 M1 人工交付（DeliveryTarget/Receipt/Feedback）等关键基础，但这些能力仍带有三渠道原型阶段的硬编码：

- Channel 被枚举（`models.Channel`）和前端常量限制；
- Workflow 依赖中央 handler map（`workflow_engine.HANDLERS`），且无 key/version/checksum；
- 素材仍主要是稿件附件（DraftMedia 绑定单一 Draft），无全局复用；
- SEO / Discoverability 不存在；
- Candidate Manifest 只覆盖部分派生状态；
- Delivery 只支持 M1 WeChat/X Thread 人工交付（DB CheckConstraint 锁死）；
- 公众号真实草稿仍是旧 Workflow 的直接副作用；
- Review / Delivery 操作面分散在多个页面。

如果继续按平台逐个增加 Prompt、Renderer 和发布按钮，扩展雪球、掘金、知乎、头条等渠道会持续累积平台条件逻辑，并在 V2 接视频时产生第二套生产系统。V1 PRD 2.0 要求先建立 **Text + Image Content Harness Foundation**，使未来平台和 V2 视频能力都能通过 Registry / Workflow / Plugin 扩展，而不是修改核心引擎。

上位文档：`AIContentStudio_V1_PRD2_开发OpenSpec_代码级_2026-09-24.md`（唯一实施基准原文）与 `AIContentStudio_V1_PRD_2.0_ContentHarness_2026-09-24.md`。本 change 是原文档的 OpenSpec 标准化投影，原文保持不变。

## What Changes

1. 将现有 `ChannelTemplateVersion` 提升为 Channel Profile 的版本化载体，建立集中 Channel Registry。
2. 给 Workflow 增加稳定 key/version/checksum/schema，并把 Node handler 改为 Registry resolve。
3. 在 `DraftMedia` 之下建立全局 Material / MaterialRevision，让素材可复用、可追溯、可版本化。
4. 给 Draft 增加 `artifact_kind / content_form / document_json`，在不破坏 Markdown 真源的前提下保存图片 placement 和图文 composition。
5. 新增通用 `DraftCheckRun`，统一 Fact / Platform / Rights / SEO / Safety / Domain checks。
6. 新增 Discoverability Profile + Report，实现 Pre/Post SEO 节点。
7. 升级 Candidate Manifest 到 schema v2，覆盖最终 Document、真实素材、检查、SEO、Render 和 Plugin/Workflow 版本。
8. 扩展 DeliveryTarget 和新增 DeliveryAttempt，支持 `copy_package / assisted_draft / auto_draft`。
9. 将公众号 `wewrite publish` 移入 Publisher Plugin，通过批准 Candidate + DeliveryTarget 执行，不再由遗留 Workflow 直接产生副作用。
10. 建立 Topic-centric Review & Publish Center。
11. 实现 Workflow Node 级 `rerun` / `rerun-from-here` 与 stale propagation。
12. 首批注册 V1 PRD 2.0 的 14 个平台/内容形态 profile；优先通过共享 Workflow Bundle + 薄平台适配避免复制 14 套逻辑。
13. 保留抖音 Script Package，不把其标为视频成片。
14. 给 V2 预留 `artifact_kind=video` 与 Provider 类型，但本变更不实现视频 Timeline/TTS/数字人。

## Capabilities

### New Capabilities

- `content-harness-registry`: 单一 Channel Registry 与版本化 plugin resolve，新增平台不改核心。
- `versioned-channel-workflow`: Workflow 定义发布后 immutable，平台分支各自独立 WorkflowRun。
- `material-library-v1`: Material/MaterialRevision 全局素材库，真实素材全局复用与权利追踪。
- `artifact-composition-v1`: Draft document/placement 保存图文 composition，placeholder 不算最终媒体。
- `unified-check-runs`: 统一 input-bound 的 DraftCheckRun 检查体系，incomplete 不等于 pass。
- `discoverability-optimization`: 独立 Discoverability Profile + Report（Pre/Post SEO），建议不自动改稿。
- `workflow-rerun-staleness`: 节点级 rerun / rerun-from-here 与 stale 传播，远端副作用禁止泛化重跑。
- `unified-review-publish-center`: Topic-centric Review & Publish Center projection，批准看到真实最终 payload。
- `delivery-router-v1`: Delivery Router（copy_package/assisted_draft/auto_draft）+ DeliveryAttempt，超时即 unknown 不自动重发。
- `v1-platform-artifacts`: V1 十四平台内容形态（知乎文章/回答、雪球财经、掘金技术、抖音 script-only 等）。

### Modified Capabilities

- `typed-evidence-freeze`: 继续以 FactPackItem frozen snapshot 作为内容证据边界，不新建通用 Evidence 平台。
- `versioned-article-candidate`: Candidate 升级 manifest schema v2，v1 保持可读。
- `manual-article-handoff`: 交付路径迁移到 Delivery Router，旧 API 作为兼容 alias。
- `prd-v1-channel-deliverables`: 被本主变更吸收（原 change 已标 superseded，不并行实施）。

## Impact

- **后端**：`apps/api/app/models.py`（additive 字段/枚举）、`services/content_harness/`（新增 registry 契约层）、`workflow_engine.py`（registry resolve + schema v1 兼容）、`routers/templates.py|topics.py|external.py|workflows.py`、`services/generation/orchestrator.py`、`seed.py`、三次 Alembic additive migration（A: harness/workflow/checks；B: material/SEO；C: delivery router）。
- **前端**：`Topics.tsx`（动态渠道/targets）、`Workflows.tsx`（plugin descriptor/stale）、`Templates.tsx`（profile_json）、新建 `Materials.tsx`、`ReviewPublish.tsx`。
- **不修改**：现有 M1 字段、旧 candidate hash、历史 ExportRecord；不新建第二套内容中心 / Workflow Engine / 审批系统 / 交付状态系统；V1 不实现视频成片、TTS、数字人、Timeline、SaaS 多租户、计费、通用插件市场、未验证平台的自动发布。
- **兼容承诺**：旧 Source/FactPack/三渠道 Topic/旧 Draft/AssetMedia/Candidate v1/manual target/Workflow schema v1/ExportRecord 全部保持可读；不做伪造性 backfill。
