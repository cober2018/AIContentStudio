> **v2 修订（2026-10-14）**：本 proposal 在 2026-10-06 版（十二平台/十七形态本地交付）基础上，按
> `openspec/AIContentStudio_OpenSpec_Multiplatform_Operations_v2.md` 与 2026-10-13 `AUDITED` 回执合并修订：
> 增加 Persona-owned 跨平台栏目、多账号 v5 交付授权、统一身份运营入口与服务端 Form Descriptor 四个方向。
> 原有十二平台/十七形态范围、公众号草稿箱例外与人工交付边界全部保留。本轮仅修订规格，业务 apply、
> 正式库迁移、真实 Provider/发布、commit/push 均未授权。

## Why

原 PRD 的 11 个文章/图文/社交平台加抖音，不能被“公众号真实草稿验收通过”或 F6E 首批五种形态替代。当前现代 Variant adapter 只覆盖四个平台，本机 Registry 还主要返回 legacy 四渠道，尚未形成完整的十二平台创作与交付闭环。

用户于 2026-10-06 确认本次完成标准：所有十二个平台先提供平台专属稿件和真实素材交付包；公众号继续使用既有官方草稿箱能力，其他平台先人工发布，不新增自动发布接口。

2026-10-13 审计进一步确认：单账号绑定语义同时承担“内容创作来源”和“交付唯一目标”，使一个 Persona 的一个 Master 无法可靠投放多个渠道及同渠道多个账号（`delivery.py` 对 v5 Variant Candidate 的 `unit.account_id` 无条件等值校验造成 409）；`ContentSeries.account_id` 非空导致栏目强制归属单账号，跨平台栏目被迫复制为多个同名 Series；渠道账号配置分散在 `/identities` 与 `/accounts` 两个入口；前端 Variant 编辑器仍只支持五种形态的硬编码表单。只修 409 或搬动 AccountDesk 无法实现真正运营闭环。

## What Changes

原批（2026-10-06，全部保留）：

- 固定十二平台、十七种独立内容形态：公众号、头条、百家号、知乎文章/回答、B站专栏/图文、搜狐号、企鹅号、网易号、小红书、X 单帖/线程/长帖/Articles、微博、抖音口播脚本。雪球/掘金等现有登记保留，但不是本次新增完成义务。
- 扩展既有 Channel Registry、ChannelAdapter 和 canonical Variant payload，复用 Master → ChannelVariantRevision → Candidate v5 → Review/Approval → local package；不新增另一套渠道、稿件或分发真源。
- 每个平台提供可见的目标受众、结构、语气、标题、标签/来源/声明、素材与发布步骤配置；模型只能提出供用户审阅的适配稿，不能把同一稿件换标签冒充平台适配。
- 把所有目标接入当前 Creation Recipe 的渠道版本 Stage 和 Production/Review 界面；先复用既有 `stage.variant.adapt@1` 与领域服务，保持接受和保存显式。
- 补齐平台本地 ZIP：冻结正文/结构、实际有序素材、精确 refs/rights、来源/声明、发布指南与安全 manifest；缺媒体、撤权、来源漂移或 schema 不支持时明确阻断，不回退旧 schema。
- 非公众号平台仅开放既有 copy_package/manual_handoff。公众号 auto_draft 保留精确账号、内容形态、授权、CapabilityVerification 和 Unknown/reconciliation 边界；本 proposal 不授权新发送，所有平台公开发布仍需单独明确授权。
- 提供增量、幂等、可审阅的平台 profile 初始化方案；不会在启动时偷偷覆盖用户配置或发布新 profile，既有 Unit/Run/Variant/Candidate 不自动升级或改绑。
- 分两大实施批次，要求少量参数化持久合同测试与集中十七形态冒烟，复用现有回归；测试写入须取得明确授权，当前Persona批的“不新增测试代码”限制仍有效。不把受控夹具当真实账号/真实生成质量验收。

v2 增补（2026-10-14）：

1. **明确身份的两个阶段**：Source Creative Context（Persona + 跨平台栏目，可有显式 origin Account）与 Target Delivery Context（目标 Account + exact channel/form + Account/Series 适配）。两者的冻结快照独立且可追溯。
2. **演进唯一 `ContentSeries` 真源**：支持 Persona-owned editorial Series 作为跨平台栏目，保留历史 Account-owned Series 的 legacy 语义；通过显式 Series × Account × Content Form 投放绑定实现一对多。方案对比见 `docs/ADR_SERIES_ACCOUNT_MODEL.md`。
3. **v5 目标账号独立授权**：无论跨渠道或同渠道，都允许明确选择同一 Persona 下符合目标平台/内容形态/权限要求的多个账号；每个目标有独立 Review/Authorization/Attempt/Receipt。旧 Candidate 保持原行为。
4. **统一运营入口**：`/identities` 下“角色 / 渠道账号 / 栏目 / 投放绑定”；`/accounts` 仅兼容路由；渠道身份、公开标识、能力与授权状态同处可见但不把登录凭据写进 Profile JSON。
5. **服务端驱动的 17 形态编辑**：从现有 Channel Registry / canonical schema 生成版本化的 Form Descriptor，UI 不再硬编码仅 5 种内容形态；任何可编辑字段均需进入真实 adapter/校验链。
6. **两批集中实施与验收**：先身份/栏目/目标授权真源，再 17 形态 UI/交付；最后用两个 Persona 跑真内容和真实本地包，集中浏览器冒烟与回归。

## Out of Scope

- 不增加自动发布接口，不启动 `social-auto-upload` 平台 Driver，不抓取或导入平台 Cookie，不绕开网站验证。
- 不替换 Creation Recipe 引擎、CreativeExecution、MaterialRevision、v5 Candidate 或发布数据真源。
- 规格修订阶段不执行数据库迁移、模型调用、发布、归档、commit 或 push；正式库迁移按 ADR 另行审批。
- 不用模拟数据声称真实创作/真实发布质量已通过。

## Capabilities

### New Capabilities

- `multiplatform-content-handoff`: 十二平台/十七形态的 exact source/target/schema 契约、平台专属适配、Recipe 接线、稿件和素材包、人工交付与逐形态真实完成状态。
- `persona-channel-series-operations`（v2）: Persona-owned 跨平台栏目、Series × Account × Form 投放绑定、源/目标身份分离与统一账号栏目运营入口。

### Modified Capabilities

- `content-harness-registry`: 渠道目录区分 planned/configured/executable/packageable/remote_verified；缺 published profile 不伪装可执行；增量 profile 初始化不会覆盖用户版本。
- `delivery-router-v1`: 本阶段十二平台的完成标准是本地受控交付，非公众号只开放人工动作；包就绪不等于发布，公众号草稿成功也不等于公开发布。v2 增加：现代 v5 Variant 交付按具体目标 ContentAccount 独立授权，不再把 `unit.account_id` 当无条件目标账号规则。
- `fe-f3b-content-identity`（v2）: Brand 约束与 Persona 创作根分离保持；新 editorial Series 创建不需要 Account；冻结记录显式区分 origin 与 destination 身份。
- `creation-recipe-stage-control-loop`（v2）: 渠道适配 Stage 继续复用 `stage.variant.adapt@1`，接受解析后的精确目标上下文（exact Account/form/Series 绑定），不新建 Variant 插件真源。
- `fe-f0-f1-project-experience`（v2）: 日常旅程从 Persona 与栏目进入，创作链路不强制先选交付账号，投放账号后置选择。

## Impact

原批影响面（保留）：`apps/api/app/services/channel_adapters.py`、`channel_variant_documents.py`、`channel_variants.py`、`candidates_v5.py`、`production_packages.py`、既有 ChannelTemplateVersion/profile 初始化与相关项目 API，以及 Production 的渠道版本/Recipe、Review 预览和人工交付界面。

v2 增补影响面：`apps/api/app/models.py`（`ContentSeries`/`ContentAccount`/`ContentUnit` 及新 `SeriesAccountTarget` 关系）、`content_identity.py`（hierarchy/snapshot/effective）、`delivery.py`（v5 目标授权）、`apps/web/src/product/IdentityWorkspace.tsx`、`AccountDesk.tsx`（并入统一入口）、`ChannelVariantForm.tsx`（Descriptor 驱动）、`App.tsx`（导航收敛）。

迁移立场修订：原批“目标零新表、零迁移”被 v2 取代——按 `docs/ADR_SERIES_ACCOUNT_MODEL.md`，Persona-owned 栏目与投放绑定需要最小增量迁移（`content_series` scope/persona_id 可空化 + 新 `series_account_target` 表），正式库执行前须单独授权、备份与测试库验证；零迁移 JSON 方案因无持久引用/CAS/审计被拒绝。本轮（Phase 0）不执行任何迁移。

正式基线仍为当前本机 SQLite＋素材库＋loopback；alembic head 实测 `idx000000001`（30 个 revision）。不更改当前 F8/ACO/Recipe 业务工作区与未追踪文件（`AccountDesk.tsx`、`channel_methods.py` 等），不运行正式迁移、profile 写入、模型或公众号请求，不提交、推送、主规格同步或归档。
