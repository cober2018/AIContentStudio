## Why

原 PRD 的 11 个文章/图文/社交平台加抖音，不能被“公众号真实草稿验收通过”或 F6E 首批五种形态替代。当前现代 Variant adapter 只覆盖四个平台，本机 Registry 还主要返回 legacy 四渠道，尚未形成完整的十二平台创作与交付闭环。

用户于 2026-10-06 确认本次完成标准：所有十二个平台先提供平台专属稿件和真实素材交付包；公众号继续使用既有官方草稿箱能力，其他平台先人工发布，不新增自动发布接口。

## What Changes

- 固定十二平台、十七种独立内容形态：公众号、头条、百家号、知乎文章/回答、B站专栏/图文、搜狐号、企鹅号、网易号、小红书、X 单帖/线程/长帖/Articles、微博、抖音口播脚本。雪球/掘金等现有登记保留，但不是本次新增完成义务。
- 扩展既有 Channel Registry、ChannelAdapter 和 canonical Variant payload，复用 Master → ChannelVariantRevision → Candidate v5 → Review/Approval → local package；不新增另一套渠道、稿件或分发真源。
- 每个平台提供可见的目标受众、结构、语气、标题、标签/来源/声明、素材与发布步骤配置；模型只能提出供用户审阅的适配稿，不能把同一稿件换标签冒充平台适配。
- 把所有目标接入当前 Creation Recipe 的渠道版本 Stage 和 Production/Review 界面；先复用既有 `stage.variant.adapt@1` 与领域服务，保持接受和保存显式。
- 补齐平台本地 ZIP：冻结正文/结构、实际有序素材、精确 refs/rights、来源/声明、发布指南与安全 manifest；缺媒体、撤权、来源漂移或 schema 不支持时明确阻断，不回退旧 schema。
- 非公众号平台仅开放既有 copy_package/manual_handoff。公众号 auto_draft 保留精确账号、内容形态、授权、CapabilityVerification 和 Unknown/reconciliation 边界；本 proposal 不授权新发送，所有平台公开发布仍需单独明确授权。
- 提供增量、幂等、可审阅的平台 profile 初始化方案；不会在启动时偷偷覆盖用户配置或发布新 profile，既有 Unit/Run/Variant/Candidate 不自动升级或改绑。
- 分两大实施批次，要求少量参数化持久合同测试与集中十七形态冒烟，复用现有回归；测试写入须取得明确授权，当前Persona批的“不新增测试代码”限制仍有效。不把受控夹具当真实账号/真实生成质量验收。

## Capabilities

### New Capabilities

- `multiplatform-content-handoff`: 十二平台/十七形态的 exact source/target/schema 契约、平台专属适配、Recipe 接线、稿件和素材包、人工交付与逐形态真实完成状态。

### Modified Capabilities

- `content-harness-registry`: 渠道目录区分 planned/configured/executable/packageable/remote_verified；缺 published profile 不伪装可执行；增量 profile 初始化不会覆盖用户版本。
- `delivery-router-v1`: 本阶段十二平台的完成标准是本地受控交付，非公众号只开放人工动作；包就绪不等于发布，公众号草稿成功也不等于公开发布。

## Impact

主要涉及 `apps/api/app/services/channel_adapters.py`、`channel_variant_documents.py`、`channel_variants.py`、`candidates_v5.py`、`production_packages.py`、既有 ChannelTemplateVersion/profile 初始化与相关项目 API，以及 Production 的渠道版本/Recipe、Review 预览和人工交付界面。目标零新表、零迁移、零新增依赖；如果无法使用现有 JSON 字段表达合同，应先回到规格层，不自行扩表。

本轮只产出 proposal/design/specs/tasks 与计划文档，business apply 等待用户明确确认。正式基线仍为当前本机 SQLite＋素材库＋loopback，schema 为 crs000000001。不更改当前 F8/ACO/Recipe 业务工作区，不运行正式迁移、profile 写入、模型或公众号请求，不提交、推送、主规格同步或归档。
