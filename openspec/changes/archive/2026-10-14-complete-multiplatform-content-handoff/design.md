## Context

本次是原 PRD 全渠道目标的受控补齐，不是再造创作引擎。用户已确认“平台专属稿件＋真实素材交付包”为第一阶段完成标准；公众号保留官方草稿箱，其他平台人工发布。平台公开发布、账号权限以及生成质量仍分别验收。

当前基线是 main@341ead8 加既有未提交 F8/ACO/Creation Recipe 实现，正式本机 schema 为 crs000000001。现有 ChannelRegistry 从 published ChannelTemplateVersion.profile_json 读取；seed.py 有十四平台的旧 profile 定义，但不能证明当前库已配置。F6E FIRST_BATCH、Variant canonicalizer 和前端 TARGETS/编辑表单仍限制五种形态，v5 manifest/package 已有可复用的 exact hash/rights/currentness 边界。

## Goals / Non-Goals

**Goals:** 十二平台/十七形态逐项可选、可审阅、可保存为 Variant、可冻结批准并生成本地素材包；实际适配规则和 Prompt 可见；Recipe/Production/Review 使用一个服务端渠道目录；保留公众号已验收的精确草稿箱路径和所有历史数据。

**Non-Goals:** 非公众号远端发布 API、浏览器自动登录/公开发布、排期、指标回收、账号资格自动核验、额外平台扩张、新建稿件/Recipe/渠道表、身份或服务器化迁移。本次也不将抖音脚本包冒充视频成片。

## Decisions

### 1. 固定平台与形态，不再用首批样本代替全范围

| 平台 | channel / content_form | source schema | Variant payload_schema | 最小平台结构 |
|---|---|---|---|---|
| 公众号 | wechat/article | text.master.v2 | wechat.article.v1（保留） | 标题、摘要、章节、封面、来源/声明 |
| 今日头条 | toutiao/article | text.master.v2 | toutiao.article.v1 | 信息流导语、分节论证、结论/来源 |
| 百家号 | baijia/article | text.master.v2 | baijia.article.v1 | 问题/主题导语、解释结构、来源 |
| 知乎文章 | zhihu/article | text.master.v2 | zhihu.article.v1 | 论点、论据、反面约束、引用 |
| 知乎回答 | zhihu/answer | text.master.v2 | zhihu.answer.v1 | 明确问题、先直接回答、再论证 |
| B站专栏 | bilibili/article | text.master.v2 | bilibili.article.v1 | 专栏标题、章节、图文位置/来源 |
| B站图文 | bilibili/image_note | graphic.master.v2 | bilibili.image_note.v1 | 真实有序图组、描述、图注 |
| 搜狐号 | sohu/article | text.master.v2 | sohu.article.v1 | 标题、导语、章节、来源/声明 |
| 企鹅号 | penguin/article | text.master.v2 | penguin.article.v1 | 标题、导语、章节、来源/声明 |
| 网易号 | netease/article | text.master.v2 | netease.article.v1 | 标题、导语、章节、来源/声明 |
| 小红书 | xiaohongshu/image_note | graphic.master.v2 | xiaohongshu.image_note.v1（保留） | 有序实际图片、卡片文案、标签 |
| X 单帖 | x/single | text.master.v2 | x.single.v1（保留） | 单条正文 |
| X 线程 | x/thread | text.master.v2 | x.thread.v1（保留） | 稳定 ID 的有序独立帖子 |
| X 长帖 | x/long_post | text.master.v2 | x.long_post.v1 | 单篇连续长正文，非线程 |
| X Articles | x/articles | text.master.v2 | x.articles.v1 | 标题、章节/媒体、来源；非长帖别名 |
| 微博 | weibo/single | text.master.v2 | weibo.single.v1 | 帖子、标签和显式选择的图片 |
| 抖音口播 | douyin/spoken_script | video.master.v2 | douyin.spoken_script.v1（保留） | 口播、分镜/B-roll、估算字幕 |

这些结构是本产品初始编辑配置，不声称是平台实时硬性规则。一个平台的多个形态分别验收；雪球、掘金及其他已有 profile 不删除、不计入本次十七形态，也不自动扩张。历史 v1/v2 Master 和 x_thread fallback 继续按原规则读取；现代适配先显式升级到相应 v2，不隐式转换。

### 2. 扩展现有 Registry 和 Adapter，不使用 UI 常量或全库 seed

采用服务端 exact source schema × published profile × adapter 合同。现有五种 schema 和 canonical hash 算法原样保留，新增十二种 schema；命名 key/version 属于 additive adapter 注册。候选生成前、保存前和冻结前均验证 source/current context、exact profile ID/hash、adapter key/version 和 artifact kind。

目录分别表达 planned、configured、executable、packageable 和 remote_verified，并返回 unavailable reason；这些是既有数据的投影，不另建状态表。前端可以显示尚未配置的计划目标，但不能将其表现为可执行。不同形态不套用同一能力验证。

profile 初始化使用专用 dry-run/review/apply 入口，复用 ChannelTemplateVersion，不运行会改用户/模型/默认流程的全库 seed。缺失 profile 可以显式新建；已有 profile 必须展示完整差异，用 expected current profile ID/hash 做 CAS 后 append-only 新版本，不静默替换。旧版本、用户编辑和旧 Run/Variant/Candidate 保留；再次相同 apply 无新增版本。正式库启用需要单独明确授权及配套备份，不是 business apply 的隐含步骤。

替代方案：只执行旧 seed 快，但缺长帖/Articles/B站图文且没有现代 adapter；只增加 UI TARGETS 会产生假可执行平台。均不采用。

### 3. 先定义可持久化 canonical payload，再适配和编辑

新增文章 schema 共享校验工具，但每个 channel/form 的 schema、adapter、profile 和适配指令独立，不能仅改 channel 标签。文章 envelope 使用 title、summary、blocks、tags、citations、declarations；title/blocks 必填。blocks 有稳定 id、连续 order、kind，kind 有 heading/paragraph/quote/list/callout/code/divider/image；按 kind 验证 text、items 或精确 image_ref_key/alt_text。列表项有独立稳定 id，图片/图表只引用实际 asset slot；未知字段/枚举、重复 ID、无效顺序、超界或错误类型拒绝。

zhihu.answer.v1 在文章 envelope 上必填 question（text、可选 url/context）。仅该 schema 额外允许 kind=direct_answer，且必须恰好为首块（order=0），其字段严格为 id/order/kind/text，text 必填；其他 schema 不能接受该 kind。descriptor、结构检查和renderer统一将该块作为“直接回答”的文字段落。问题必须由用户明确输入/确认，不能让模型伪造真实提问或链接。x.articles.v1 使用文章结构，x.long_post.v1 使用独立 text、citations、declarations，不能互转为同一 payload。weibo.single.v1 使用 text、tags、有序 images（id/order/image_ref_key）、citations、declarations。bilibili.image_note.v1 使用 title、description、tags、有序 cards（id/order/image_ref_key/caption）、citations、declarations，必须有真实 render 图组；共用图卡验证工具但保持独立 target profile。

新 schema 统一最大 canonical JSON 为 2 MB，blocks/posts/cards/refs 最多 250，稳定 ID 使用既有 ASCII 有界规则，字符串统一 NFC/换行并拒绝控制字符。产品技术上界与平台规则分开；本产品默认上界不冒充已验证的外部字数/图片数量限制。具体 per-field 上界与 kind 字段白名单随 adapter descriptor 返回前端，不能客户端自定。既有五种 schema 的原上界不改变。

citations 沿用 exact FactPackItem、snapshot checksum、location_id/start/end（canonical 可见文本 Unicode code-point 范围）及 ContentMaster/VariantEvidenceRef；正文/列表位置的 location_id 全局唯一。转换到新位置必须显式、可证明地重定位；无法证明时返回待用户重新绑定的警告/阻断，不能保留假的有效 citation。图片 asset slot、role/order/placement、hash 和 rights 不以 Prompt、外链或名称替代。

### 4. 平台适配不是内容重新授权

确定性路径只处理已支持的内容结构。需要重写时复用已有受控模型路由和 LLMRun 提出 canonical 候选，Prompt 显示 source/目标/profile/方法/事实边界，Provider 数据不直接保存。用户预览、修改、接受后显式保存 Variant；Master 不变。

模型来源只使用服务端验证的成功 LLMRun 安全投影，绑定 exact source/context、profile、adapter、实际输入 hash 和生成 payload hash；不保存 raw response、error、secret。人工修改后的稿件如实标 user_edit 并保留建议来源，不谎称 final hash 等于模型原样结果。新的事实、声明或素材引用不得凭平台重写自动获得证据/权利。

### 5. 接入 Creation Recipe，而不是另开一套渠道流程

`stage.variant.adapt@1` 和 Variant 面板从同一服务端目录选择 target，实际 Prompt/模型/profile 在既有 Effective Preview 可见；Preview 不调用模型。本次 Stage 临时调节、Attempt receipt、幂等/Unknown、反馈和 Save What Worked 均继续走现有服务。

执行只给待接受稿件；接受/修改/拒绝继续 append-only 反馈，接受为 Variant 不自动冻结 Candidate，不创建 Review/DeliveryTarget，更不发布。Workflow、Master、各 Variant 的 dirty/save 独立，409 后保留本地稿。兼容的多个平台共享一个 source Master，但 (unit_id, variant_key) currentness 独立。

### 6. 所有本地包都从已批准 frozen v5 输出

保留 v5 的唯一 channel_variant_revision_id source FK，以及五个 legacy/workflow FK 为 null 的不变量；schema dispatch 先于 Draft/Master heuristic。无需新 manifest 版本，只让既有 v5 builder/live validator/package adapter 识别新 canonical schemas。

统一 ZIP 含 manifest.json、content.md、平台指南 publish-guide.md、sources.json、declarations.json，以及该形态的结构文件和实际 media/ 字节。

安全导出投影覆盖 ZIP 所有成员（包括 manifest.json），不能只清理 sources.json 却把完整内部 manifest 复制出去。manifest.json 使用有版本的本地 export projection，保留 exact Candidate ID/hash、schema/target/profile/adapter、必要且可公开的 refs/rights/attribution、文件/order/placement及文件哈希；来源于服务端验证后的 frozen Candidate。原 Candidate hash 是源记录标识，不声称可由删减后的公开字段重新计算；导出投影自身另有 canonical hash。内部完整 Candidate/manifest 在服务端保持原样，不能为导出改写其 hash 或省略 live integrity 检查。

sources 来自 frozen citation/provenance 的可公开安全投影，不导出整个 FactPack、原文、模型受限上下文或本机私有路径；必要署名/来源披露无法合法公开时明确阻断，不自动剥掉义务。现有五schema历史包保持原字节/合同；新的安全导出能力属于显式版本化 export projection，不能悄悄重写已交付历史包。

文章/回答/Articles 增加服务端从 frozen blocks 渲染的 content.html；回答另含 question.json，线程另含 thread.json，图文另含 cards.json，微博另含 post.json，抖音含 scenes.json 和明确标估算的 estimated.srt（如存在）。HTML 安全转义、禁脚本/远端主动请求，媒体使用包内精确路径；不承诺平台粘贴后完全保留布局。图组必须实际顺序/字节可核验，不生成占位“图片”；抖音包明确 script-only。

标题、body、refs/order/placement、profile、checks 和 hash 均来自批准冻结内容，不读取当前未批准正文、Draft 或新的 profile 替换历史。保存/审批/授权遵守原 currentness，历史已授权包依原 live rights/evidence/integrity 规则回读；撤权、文件缺失/hash 改变或引用不可证明时失败关闭，禁止 v5→v4/v3 fallback。ZIP 生成零远端调用，awaiting_manual_receipt 不等于 published。

### 7. 公众号保留，其余人工；公开发布不在本次授权中

公众号官方 auto_draft 继续要求 exact approved Candidate、有效精确账号/form/action/runtime capability、独立 Delivery Authorization 和 durable Attempt；publisher 只发送批准 render/media。原 WeWrite-compatible transport、原文件名/字节/MIME、成功 media_id 与人工确认验收口径不改变。缺 capability 时仍可使用本地包，不偷偷开放发送；Unknown 必须 reconcile，禁止重发。

其他十一平台的远端发布能力保持 unavailable，提供 copy_package/manual_handoff。X 长帖/Articles 的真实账号资格未验证时展示“交付包可用，账号发布资格未验证”，不影响本地导出，也不声称已接通。实际人工发布必须另有用户明确授权/操作并按既有 Receipt 记录真实结果；当前对阶段范围的确认不授权助手登录、发送或公开发布。

### 8. 两批交付和逐形态完成证据

批次 A：目录/profile、十二新增 canonical schemas、平台 adapter、refs/checks/v5/package、Recipe 后端接线。批次 B：去掉页面五形态常量、typed editor/preview、Review/人工交付、说明与集中复核/冒烟。每个形态都有独立结果：可选/适配审阅/保存/hash/审批/ZIP/媒体/状态，不用一个 WeChat 或 X 样本代表其他平台。

实施计划要求少量参数化持久合同测试加集中受控十七形态冒烟，复用既有回归/构建预算。持久覆盖至少包括新增canonical schema/hash、source/target compatibility、v5 source/currentness、公开export projection和live rights/篡改失败关闭。测试文件写入仍须取得明确授权；当前Persona批禁止新增测试代码的限制不因这次规格修正解除，未获授权不得用临时冒烟冒称持久覆盖完成。受控正文/媒体验证的是链路和契约；真实模型生成质量、真实平台粘贴效果、实际账号权限和真实发布单独标未验证，不能以 fixture 或下载 ZIP 冒充。

## Risks / Trade-offs

- 平台规则会变化 → 初始结构标产品配置；硬性限制只来自明确带版本、核验来源/时间的规则，未知处警告，不虚构平台认证。
- 旧 seed 与 published profile 冲突 → 专用增量 dry-run/CAS，不运行全库 seed；旧 profile 未经选择不改变。
- 共用渲染器导致“千篇一律” → 共用 canonical/HTML 工具，不共用隐形平台 Prompt；按 target 显示实际指令和结构检查，结果仍由用户审阅。
- 新 schema 漏接 v5/Review/package 或 UI → 同一 descriptor 驱动各层；未知 schema 明确拒绝，十七形态独立记录。
- 当前工作区 dirty → 仅在获准后增量实现，保留 F8/ACO/Recipe 和原资料；不重置、不自动归档或提交其他 change。

## Migration Plan

原批立场（2026-10-06）：零数据库迁移/零新依赖；新 schema 存在现有 Variant JSON、profile 存在 ChannelTemplateVersion。

**v2 修订（2026-10-14）**：上段零迁移立场被 v2 的最小增量迁移方案取代——Persona-owned 栏目与 Series×Account×Form 投放绑定无法用现有 JSON 字段安全表达，判定过程与备选对比见 `docs/ADR_SERIES_ACCOUNT_MODEL.md`。正式库升级（备份、测试库验证、外键检查、downgrade 策略）须单独授权后执行；在此之前当前正式数据库、素材、模型凭据、Worker 拓扑和 crs approved head 均不变。必要回退只撤销本 change 尚未使用的代码/profile启用，不删除历史 Variant/Run/Material/Candidate；schema/身份无需降级。

## Open Questions

产品完成范围已由用户确定，无阻断性产品问题。正式 profile 写入、正式库迁移、真实模型/公众号外发、公开发布、提交和生命周期操作按各自明确授权执行，不从本 proposal 推定。

---

# v2 设计增补（2026-10-14）：Persona、跨平台栏目与多账号交付闭环

> 来源：`openspec/AIContentStudio_OpenSpec_Multiplatform_Operations_v2.md` Part B。以下 D-v2.1–D-v2.9 与上文原设计共同生效；冲突处以本节为准。

## D-v2.1 模型语义：Owner、Persona、Series、Account 与 Channel

| 对象 | 唯一职责 | 不能承担 |
|---|---|---|
| Owner/User | 权限、Provider/Model、本机配置、通用技术能力 | 任意 Persona 的默认创作风格 |
| Persona | 创作身份、Creative Profile 根、创作记忆隔离 | 具体平台登录凭据 |
| Brand | 品牌/合规/事实约束 | 默认 Creative Skill/Style/Recipe |
| **Editorial Series**（新） | 属于 Persona 的唯一跨平台栏目：选题定位、栏目创作方法、通用更新规划 | 锁定唯一交付账号 |
| ContentAccount | Persona 下一个明确的真实平台账号、公开身份、平台能力和可选授权引用 | Master 的唯一合法交付终点 |
| SeriesAccountTarget | 一档栏目将某种内容形态投到某个具体账号的显式绑定 | 独立稿件、发布审批或登录真源 |
| ContentUnit/Master | 某角色、某栏目下的内容创作及接受真源 | 把 `unit.account_id` 等同于所有未来目标账号 |
| ChannelVariant/Candidate | 某平台/账号语境下的具体表现与候选 | 自动认为已审核或已发布 |
| Delivery Authorization/Attempt/Receipt | 针对**精确目标账号**的一次合法交付与证据 | 反向篡改源内容身份 |

**术语约束**：`platform_channel` 表示平台类型（如 `xiaohongshu`），不是具体 Account；同一平台可以有多个 ContentAccount，不能通过频道字符串猜测账号身份。

## D-v2.2 保留历史数据的首选模型

**优先复用既有 `ContentSeries`，不造“SeriesGroup + Account Series + 额外虚拟栏目”三重真源。** 已核验现状（2026-10-14，`models.py`/`content_identity.py` 实测）：`ContentSeries.account_id` 为 NOT NULL FK；`hierarchy()` 要求选栏目必须选账号；`ContentUnit.account_id/series_id` 可空。首选最小增量迁移（语义合同，最终以 ADR 与实施为准）：

```text
ContentSeries (existing truth, additive evolution)
  scope: persona_editorial | account_legacy   # old rows backfill account_legacy
  persona_id: nullable-for-legacy, required-for-persona_editorial
  account_id: nullable-for-persona_editorial, required-for-account_legacy

SeriesAccountTarget (new relation only, not new Series truth)
  series_id -> ContentSeries
  account_id -> ContentAccount
  content_form  # exact versioned Channel Registry form
  enabled
  version / CAS metadata
  unique(series_id, account_id, content_form)
```

- 老数据：现有 Account Series 保持 `account_legacy`，原 `account_id`、Unit 引用、IdentitySnapshot、旧默认 Recipe 不动；**不自动合并同名栏目**。
- 新数据：Persona-owned editorial Series 可以在**未选择 Account**时创建；栏目身份与创作默认明确继承 Persona，可选配置多份投放绑定。
- 老栏目升级：必须先进行用户可审查的 dry-run mapping、权限冲突与默认配置 diff，再显式合并/关联；不得依据标题相同自动合并。
- 若真实需要新增表/列或 SQLite batch rebuild，应提供 Alembic upgrade、保留历史的 downgrade 策略、数据备份/完整性/外键校验，以及“新模式已有记录时拒绝破坏性 downgrade”的 fail-closed 处理。

**零迁移替代方案的判定门槛**：只有当现有某一稳定持久实体已经可以作为 Persona-owned 跨平台栏目唯一真源、拥有独立版本与投放关系，且没有同名 Series 复制/JSON 假绑定，才能选零迁移。不可为了规避迁移牺牲正确关系。实测结论：零迁移不满足门槛，详见 ADR。

**2026-10-14 独立复核补充（scope 分支代码位面实测）**：`account_id` 可空化影响的旧查询不止 `hierarchy()`/`effective()`。以下六处实测站点在批次 A（5.2/5.4/5.7）必须逐处加 scope 分支，legacy 分支行为逐字节保持：

| # | 站点 | 现状（实测） |
|---|---|---|
| 1 | `content_identity.py:146-151` `owned_entity("series")` | 经 `entity.account_id` 取 account，None 即 404；persona_editorial 栏目必须改走 persona 归属校验 |
| 2 | `content_identity.py:121-125` `hierarchy()` | 选栏目强制选账号（422）；persona_editorial 分支只要求 persona 归属 |
| 3 | `routers/content_identities.py:277,285` | 栏目 list/create 仅存在于 `/content-accounts/{account_id}/series`；需要 persona 作用域的创建/列表入口 |
| 4 | `project_authorization.py:123-131` | 工作流默认解析 join `ContentSeries.account_id == ContentAccount.id`；persona_editorial 栏目在此路径不可达，须补 persona→series 解析 |
| 5 | `project_matrix.py:76` | 矩阵建议校验 `series.account_id != account.id` 即拒绝；NULL account_id 会被误判非法，须按 scope 分支 |
| 6 | `IdentityWorkspace.tsx:87-88,135,189` | 前端经 `current.account_id` 反查 persona/account 并按账号挂载栏目树；须支持 persona_editorial 挂载与创建 |

正式库实测（只读）：`content_series` 当前 **0 行**，`account_id` NOT NULL，alembic_version=`idx000000001`——本机迁移 backfill 风险为零，但 legacy 语义仍对历史快照、测试夹具与其他环境生效，不可省略。

## D-v2.3 源创作身份与目标投放身份完全分开

```text
Persona / Editorial Series
       │
       ├─ Source Creative Context (for Master)
       │    Persona → Series; optional explicit origin-account context
       │    Brand constraints always apply; no owner/Brand creative fallback
       │    accepted Master + source identity/recipe hashes frozen
       │
       └─ SeriesAccountTarget → selected concrete Account(s)
                 │
                 └─ Target Delivery Context
                      Persona → Account → Series (when applicable)
                      platform + exact form + account requirements
                      Variant → v5 Candidate → Review → Authorization
                      → Manual Package / approved WeChat Draft
```

- 不选 Account 即可创建新栏目和 Master；源创作身份来自 Persona/Series，不能因为“默认平台”偷偷引入某个 Account 的创作偏好。
- 若为单账号内容显式选取 origin Account，应在 Preview 显示来源，冻结到源身份快照。它是创作来源/偏好，并不自动禁止现代 v5 后续其他账号分发；目标端仍需重适配与独立审核。
- Legacy Account Series + legacy Candidate 的固定账号约束仍保持。切换到 persona_editorial 模式须显式迁移/新 revision，不可后台偷偷改变历史含义。
- Target-specific Account Creative Profile、Series 覆盖、平台限制、账号限制，**只作用于对应 Variant/Delivery**；不得回写或重算已接受 Master。
- 若同平台两个账号存在不同 Account/Profile/rights/广告声明等要求，必须分别生成或确认兼容的 Variant，且每个目标有独立 Candidate/Review/Authorization；**禁止通过换一个 `account_id` 复用不兼容的冻结 Candidate**。
- 每次执行冻结来源 Persona/Series revision、origin context（若有）、target Account revision/渠道/form、effective profile hashes、Content/Variant/Candidate refs、审核和 rights/capability evidence；拒绝 stale/串 Persona/权限不明。

## D-v2.4 v5 Delivery 账号规则

已实测确认的阻断条件（`apps/api/app/services/delivery.py`）：

```python
if is_variant and unit.account_id is not None and content_account_id != unit.account_id:
    raise HTTPException(409, "渠道候选不得绕过内容单元固定账号")
```

**不可只修改为“同渠道锁定、跨渠道放行”**，因为会继续阻断同一平台的不同账号。新合同：

1. 对符合现代 v5 定义的 Variant Candidate，Delivery `target_account_id` 由显式选择、冻结 Candidate 或授权记录决定；不得用 `unit.account_id` 强制覆盖。不同平台、同平台多个 Account 均支持。
2. 授权前要求同一合法 Persona、与 Variant exact `channel/form` 相符、账号有效、用户权限、相关绑定或明确一次性授权、Candidate currentness、Review/rights/compliance/需要的平台 Account CapabilityVerification；缺一项则 blocked。
3. `SeriesAccountTarget` 表示默认投放目标，**不是永久授权书**。临时投放未绑定 Account 需显式选择并按策略批准，不能暗中持久写入默认映射。
4. 目标账号不同就产生独立的 authorization/attempt/receipt。幂等键至少区分 Candidate、target_account、action/mode；允许合法同平台多账号独立交付，但不得对同一授权重复副作用。
5. `failed_before_dispatch` / `unknown` / confirmed 的语义遵守旧 Delivery 合同。真实派发可能发生后遇到超时或 UI 不确定性 => `unknown`，不自动重试；须 readback/reconcile/人工证据。
6. 对 legacy Candidate/固定账号路径不做静默松绑；提供明确版本分支和持久回归证明。
7. 不得让 Client 直接指定与 Candidate/Persona 不一致的账号、伪造 capability/rights 结果或通过 Project route 绕过 Review gate。

## D-v2.5 账号、栏目与投放绑定的管理界面

在 `/identities` 中统一提供四个工作区 Tab：

- **角色**：两个 Starter Personas、Identity/Creative Profile 与继承来源显示。
- **渠道账号**：每个 Account 的 Persona、平台、公开标识、账号昵称、可用内容形态、绑定状态、必要认证/草稿箱能力状态；同平台多账号可区分。Secret/Cookie/浏览器登录态不放进公开 Profile 或页面响应。
- **栏目**：Persona-owned editorials 的创建/编辑/版本/Creative defaults；清楚展示 `persona_editorial` 与历史 `account_legacy`；已有栏目升级须 preview + explicit review。
- **投放绑定**：Series × Account × Form 的启停、可投放状态和 per-target 预览；冲突/不可用目标给出理由；不得将绑定操作直接视为已审核或已发布。

保持 `/accounts` 旧链接作为到统一工作区的兼容跳转；不要增加无必要的第十个一级导航。Project 创建页先选 Persona/栏目，渠道目标允许稍后指定；Review/Delivery 展示精确账号而非只有平台图标。微信 AppID/授权说明等应归于对应 Account detail，系统 Provider/Model 仍留 Settings。

UI 需明确四种状态：`not_configured`、`registered`（公开身份登记完成）、`verified`（具备某种经证实能力）、`blocked/expired`。登记公开标识不等于平台已登录，不等于自动发布已经就绪。

## D-v2.6 17 种内容形态：后端合同驱动，不在 React 重建清单

- 12 平台 / 17 form 的**准确枚举、schema version、canonical payload、required media roles**以本 change 原 design 的平台表和 Channel Registry 为准；实施时必须核对实际 catalog（2026-10-14 实测：`FIRST_BATCH` 现有 17 个 (channel, form) 中仅 14 个属于约定的 17 形态，缺 `bilibili/image_note`、`x/long_post`、`x/articles`；多出的 `xueqiu`×2、`juejin` 属范围外既有登记），不可按文档猜测平台/内容形态清单。
- API 提供版控 `ChannelFormDescriptor` read-only projection：`channel_id`、`content_form`、`schema_id/version`、字段路径/类型/label/required/readonly/default/长度/枚举/列表约束、Media roles/尺寸限制、校验错误映射。仅投影服务器允许暴露的 schema，不泄露 secrets/internal-only 字段。
- 前端 `ChannelVariantForm.tsx` 不再用仅支持 5 forms 的 `fieldsFor` 硬编码，按 descriptor 安全渲染 Text、Block/List、Citation、MediaRef、平台特有字段；未知/不可安全编辑字段只能明确阻断或只读展示，绝不静默丢弃。
- Save/Reload/Freeze/Export 必须使用相同 canonical schema 与 exact ref/hash；前端不是 canonical validator。对 legacy 5 forms 不改变既有 payload 含义；对新增 12 schemas 支持可视化编辑和错误定位。
- 真实媒体字节、rights、citation relocation、stale、tamper、required output roles、package manifest 均维持原 gates；缺素材不可导出假素材；script-only 不可冒充最终 MP4。

## D-v2.7 Source → Target 的完整用户流程

```text
/identities
  选择 Persona → 编辑/选择跨平台栏目
  → 绑定多个 Account + content_form (或选择一次性明确目标)
  → Project / Unit (可不先绑定发布 Account)
  → Creation Recipe: Research / Text / Graphic / Audio
  → Stage Review & Accept → Master / MaterialRevision
  → stage.variant.adapt@1 (per target exact form/account context)
  → Variant Candidate → Review/Approval
  → Delivery Authorization (per concrete Account)
  → WeChat Draft (authorized) OR Local Manual Handoff Package
  → Receipt / Manual confirmation / Unknown reconciliation
```

Content production 和 delivery 的状态不能混写。**“下载 ZIP”“交给外部 Agent”“导出文件”都不是 publication succeeded**。

## D-v2.8 实施与数据安全

- 单机正式 SQLite 是生产数据库：迁移前必须有原始 schema/HEAD 备份与可恢复确认、Alembic migration dry-run/测试库验证、外键检查、历史回放验证。不得自行清库、重建用户 Persona、重置历史账号或回滚已接受 Master。
- 2026-10-13/14 审计存在 73 条未提交/未追踪条目（含 `AccountDesk.tsx`/`ChannelPluginPanel.tsx`/`channel_methods.py` 等）与 3 个 stash；apply 前必须精确盘点，不可重置、覆盖、遗失或误归档。
- 当前只授权 **spec materialization**。数据库升级、真实 Provider、网页登录、微信草稿、外部 Agent 调用、自动发布、commit/push/归档均需后续明确授权。

## D-v2.9 被拒绝的捷径

| 方案 | 为什么拒绝 |
|---|---|
| 只按 same-channel/cross-channel 修 409 | 同平台多账号依然被锁死；未解决 v5 目标账号真源。 |
| 同名 Account Series 直接当同一栏目 | 无唯一栏目版本/创作默认，冲突不可检测。 |
| 把 Series × Account 放在散装 JSON 映射 | 无持久引用、CAS、审计和稳定身份。 |
| 对历史 Series 原地改为 Persona-owned | 破坏旧 Unit、IdentitySnapshot 和默认流程解释。 |
| 所有 Variant 自动复用给同平台所有账号 | 无法执行 Account override、rights、授权和审核差异。 |
| 在前端复制 Python schema enum | 后端新增 form 后 UI/Executor 漂移。 |
| 直接引入 `social-auto-upload` 实现发布 | 越过当前人工交接授权边界，增加凭据与平台风险。 |

## 2026-10-14 最终验收校准

用户指定Codex作最终质量评审者并授权通过后直接归档提交。评审记录署名AI代理、实际全文/像素/音频转录与检测方法，不冒称真人。来源保留真实approved design与original brief的private source locator，明确author_opinion/假想场景，不把Modeloutput当verified事实。image_note平台cover/inline指输出封面/正文图卡，纯形状/文字稿在明确非照片preset下合法；现有照片必需preset检查及render精确PNG/rights/currentness门禁独立保持。不得修改旧角色默认、旧素材权限或历史payload；仅追加新来源/身份/素材/主稿revision。
