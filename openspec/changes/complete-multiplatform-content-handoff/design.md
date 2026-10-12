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

零数据库迁移/零新依赖；新 schema 存在现有 Variant JSON、profile 存在 ChannelTemplateVersion。先只读审阅和隔离验证，完成后再单独批准正式 profile 初始化。当前正式数据库、素材、模型凭据、Worker 拓扑和 crs approved head 均不变。必要回退只撤销本 change 尚未使用的代码/profile启用，不删除历史 Variant/Run/Material/Candidate；schema/身份无需降级。

## Open Questions

产品完成范围已由用户确定，无阻断性产品问题。正式 profile 写入、真实模型/公众号外发、公开发布、提交和生命周期操作按各自明确授权执行，不从本 proposal 推定。
