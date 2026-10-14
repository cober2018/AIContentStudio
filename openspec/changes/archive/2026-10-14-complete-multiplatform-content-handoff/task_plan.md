# Twelve-platform Content Handoff Implementation Plan

**当前：Batch A/B已授权并实施，33/43；下方原计划保留历史表述，最新执行段与progress为当前事实。**

> **For agentic workers:** apply 获准后使用 superpowers:executing-plans 分两批执行，批内连续完成，集中复核/冒烟；当前只完成规格与计划，不执行下面业务步骤。

2026-10-08 Persona前置校准：Stage统一为`stage.variant.adapt@1`；后续计划要求少量参数化持久覆盖＋十七形态集中冒烟。只同步计划，不新增测试文件、不进入本change业务；实际测试写入须单独明确授权。

**Goal:** 补齐原规划十二平台、十七种平台专属稿件与素材交付包；公众号维持既有草稿箱，其他平台人工发布。

**Architecture:** 单一 Channel Registry/profile + exact ChannelAdapter/canonical schema，复用 Master、append-only Variant、Candidate v5、Review/Delivery 和 Recipe Stage。零新表/零迁移/零新增依赖，不改变正式本机 crs 环境。

**Tech Stack:** 既有 FastAPI/SQLAlchemy/SQLite、React/TypeScript/Vite、原Worker/LLMRun/本地素材库。

## 状态

- [x] 按用户回答固定平台、形态、交付动作和禁止范围；不是远端发文授权。
- [x] 读取当前代码/canonical/active F6E和Recipe相关规格，确认缺口不是加菜单或执行seed即可解决。
- [x] 创建标准 change 的 proposal/design/specs/tasks。
- [x] 独立 SPEC/计划最终均APPROVE、零blocker；strict37/37、diff及原场景精确保留通过。
- [x] 用户明确确认后 business apply（2026-10-14 Batch A/B；独立权限边界见当前进度）。

## 文件职责与批次

| 批次 | 优先编辑现有文件 | 职责 |
|---|---|---|
| A1 | apps/api/app/services/content_harness/channel_registry.py；apps/api/app/seed.py；既有templates/profile管理服务与router | 单一目录、带版本profile、可审阅幂等增量；不是运行全库seed |
| A2 | apps/api/app/services/channel_variant_documents.py；apps/api/app/services/channel_adapters.py | 十二新增canonical schemas、十七exact adapters、typed descriptor、目标指令 |
| A3 | apps/api/app/services/channel_variants.py；apps/api/app/routers/channel_variants.py；既有Stage Variant resolver/handler | 受控建议/显式save、LLMRun及refs、Recipe实际参数消费 |
| A4 | apps/api/app/services/candidates_v5.py；production_validation.py；production_packages.py；既有Approval/Delivery dispatch | 冻结检查、独立currentness、各形态本地HTML/ZIP与live安全边界 |
| B1 | apps/web/src/product/ChannelVariantsPanel.tsx；ChannelVariantForm.tsx；既有Recipe/Stage面板；apps/web/src/api.ts | 服务端descriptor驱动目标选择/typed编辑/Preview，不维护第二份五目标清单 |
| B2 | apps/web/src/product/CandidatePreview.tsx；既有Project Review/Delivery页面 | 真实冻结预览、渠道差异、包下载/人工回执/公众号草稿区分 |
| B3 | 本change的README/progress/findings；根README/计划进度；既有验收记录 | 十七形态矩阵、集中代码复核/冒烟/回归、正式启用与生命周期授权状态 |

优先编辑已有文件；若文件实质超过可维护范围，只拆本次新增schema/adapter职责，不重构无关服务。所有 apps 文件在确认apply前保持原样。既有 F8/ACO/Recipe dirty 内容保留。

## 执行顺序

/// 批次 A：只读目录/profile差异 → additive descriptor/canonical schemas → exact adapters和受控建议 → Variant refs/checks/v5/local package → 既有stage.variant.adapt@1接线 → 集中源码自审，不逐个形态打断请求确认。

/// 批次 B：服务端目录接入页面 → typed稿件/素材/证据编辑 → 冻结Review/交付包 → 十七形态集中冒烟＋旧五形态/版本回归 → 独立代码复核 → 构建/预算/既有回归/strict/diff → 交付实测矩阵；仅方向/权限变化或无法解决的真实阻断询问用户。

/// 正式启用与生命周期：单独授权 → 配套备份/只读dry-run → 必要profile增量CAS/幂等启用 → 历史行/hash/素材/页面回读 → 主规格保留审计/归档/本地提交按获准范围执行，不推送或公开发布。

## 集中验证

- spec阶段：`openspec validate --all --strict`；`git diff --check`；三份delta的MODIFIED标题/旧场景保留；现有业务/F8/ACO/Recipe差异哈希不变。
- apply阶段：在明确测试写入授权后补少量参数化持久合同覆盖，复用backend回归并集中十七形态冒烟；未授权不写新测试，临时冒烟不代替持久覆盖。`cd apps/web && npm run build`（含既有bundle gate，若独立gate另跑npm run check:bundle）；新增页面保持lazy与原路由预算。
- 每个目标必须实际走 proposal/edit/save/reload/checks/freeze/approve/authorize local/ZIP/readback，核对frozen bytes/hash/结构/media；图文使用可证明实际图组，Douyin仅脚本包。十七目标的结果逐项记录，不只列平台名字。
- 同一Master多平台、同平台多形态、旧五schema/hash、v1-v5历史/归档、dirty隔离、profile CAS/幂等、撤权/损坏/错误refs/unsafe HTML/私有source投影、target/source字段篡改、Unknown不重发均在集中阶段验证。
- local smoke强制阻断供应商/微信出站；实际模型质量/平台编辑器效果/账号资格不冒称通过。任何付费生成/公众号新草稿或公开发布须按后续明确授权执行。

## 原规格阶段不执行（历史，现已由Batch A/B授权部分覆盖）

业务apply、测试代码、迁移、正式profile写入、运行环境操作、真实模型/公众号请求、其他平台登录/发布、主规格同步/归档、commit/push。

## 2026-10-14 Batch B 授权实施计划（沿用原计划）

当前用户贴入 BUSINESS_APPLY — BATCH_B，明确允许业务与持久测试；历史未授权记录保留。Batch A 17/43 为起点；本轮仅 1.1–1.5、2.1–2.4、6.1–6.7，2.5 正式启用继续待授权。

- [x] /// 合同：先参数化负向测试，再补 channel_variant_documents.py、channel_adapters.py 的十二新增合同及版控 Form Descriptor；原五 hash 保持，范围外登记保全。
- [x] /// 目录：专用 profile 增量 dry-run/CAS/幂等 apply 仅隔离库验证；17 项由同一服务端目录投影。
- [x] /// 目标：channel_variants.py、stage_domain_integrations.py 与 v5/交付消费 target account 修订/绑定/配置；按账号独立 key、冻结 refs 和 live drift，保留历史无目标候选。
- [x] /// 交付：production_packages.py 为每形态生成结构/安全 HTML、来源/声明和版控公开 manifest；安全投影覆盖所有成员，原 Candidate hash 与 export hash 分开。
- [x] /// 界面：ChannelVariantForm.tsx 与现有 Variant/Stage/Review 接口消费 Descriptor；字段/媒体/引用保全、409 保留 dirty、本地包与公众号草稿分开。
- [x] /// 验证：集中参数化 17-form smoke/旧五回归/完整 pytest/Web build/strict/diff，逐形态记录正文与包 hash、真实媒体或阻断；独立规范和代码复核后更新矩阵与 README。

不做正式 profile 写入、迁移、模型/公众号调用、Vite/配置操作、commit/push/canonical sync/archive。代码版本以当前 Git 与工作区为准，基线文件 hash 仅存 /tmp/aics-batch-b-baseline.json。

当前执行结果：33/43，BATCH_B_IMPLEMENTED；16项本地实施与合同/集中页面证据已交付，正式启用和最终质量/生命周期按既有范围待授权。

## 2026-10-14 全权授权后的启用与最终验收

用户明确要求“授权呀，全权授权，你直接该干什么干什么”，覆盖前轮列出的正式Profile启用、真实Provider验证、必要运行加载及规范/Git收尾。沿用同一change；不将其解释为新增自动公开发布产品范围。

- [x] /// 2.5：保存正式SQLite在线备份与真实素材配套备份，审阅12平台增量dry-run；在副本演练apply/幂等/旧行保全后正式apply，加载必要API代码并核对17目标。
- [x] /// 7.1/7.2/7.3：核对已有真实两Persona成品与当前Provider链，复用正确来源；完成Persona-owned Series和目标账号实际工作流，保存真实QC/媒体/冻结/Review/授权/ZIP证据，不重发Unknown。人工评审单列。
- [x] /// 7.4/7.5：旧Account/快照/交付历史保全检查，完整测试、Web预算/浏览器、SQLite/head readiness和strict/diff真实回执。
- [x] /// 7.6/7.7/7.8：独立复核当前及相邻change尚开放项，更新Requirement到实际产物矩阵；授权已取得，但未发生的操作不冒称完成。
- [x] /// 3.1：仅在验收条件满足后合并本change delta到canonical、保留相邻active change要求，归档本change并白名单提交；不混入其它工作区改动。

Ruling: 全权授权解除上一轮逐项权限等待；人工质量证据、Unknown不重发与历史保全仍是完成条件，不用授权代替结果。

/// 验收发现的两项修复：先复现正式Master旧封面ref无法映射和Profile apply未原子归档旧published；仅桥接合法源cover默认形态、复用既有版本归档，保全payload/hash和严格target校验，先红后绿再集中复验。

当前40/43。7.1/7.2真实生成/技术采纳部分已交付，完整质量仍有事实边界、平台inline媒体及人审门槛；3.1依赖全部验收，保持开放。新Provider11调用、无Unknown/重试；不再为缺事实/权限强造通过，未使用额外QC2调用额度。

## 2026-10-14 剩余质量与直接归档提交（用户明确委托）

用户明确要求“补齐事实边界和图文平台检查，质量评审也由你做，通过后直接归档提交”。指定评审者为Codex；记录真实代理评审和手段，不冒称用户已人工试听。沿用现有40/43和真实成品，无新change。

- [x] /// 来源：使用已批准设计与本批真实创作输入建立author_opinion/假想场景事实边界；只新增合法revision/refs，保持旧Model/素材/Unknown历史；不把模型输出反向当证据。
- [x] /// 图文：真实PNG精确绑定render_asset_ref与权利证据，复核平台检查是否把input照片与最终图卡混同；确有代码缺陷才先红后绿最小修复。
- [x] /// 质量：完整阅读2篇、逐张评审6PNG、完整音频转录/时序/响度与可用听感检测，按固定rubric记录受委托AI评审；必要编辑只追加revision并重做受影响产物。
- [x] /// 验证：独立复核事实/媒体/质量记录，fresh后端/Web/strict/diff与旧行保全；满足实际标准后关闭7.1/7.2。
- [x] /// 收尾：审阅canonical六份（实际capability枚举以目录为准）与相邻active change要求合并，归档本change，白名单提交本地main；保全未归属改动，不主动push或公开发布。

Ruling: 用户已明确指定Codex执行此前human评审职责，采用署名AI代理评审而非伪造真人记录；本文与review记录真实检查范围。

最终委托质量结果：来源、真实图卡、完整机器检查、六张像素评审与全文音频ASR/声学检查通过，独立评审通过，7.1/7.2关闭。/// 收尾执行中：候选提交树仅纳入owner，规范同步/归档后白名单提交。

收尾：七capability canonical同步23新增/2修改，无删除；旧要求/场景和相邻taskhash回验保持。本change已归档，43/43；实际提交仅白名单，最终commit以Git回读为准。
