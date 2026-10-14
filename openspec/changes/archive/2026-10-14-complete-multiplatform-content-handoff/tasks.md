## 0. 规格与授权（原批，2026-10-06）

- [x] 0.1 记录用户确认的十二平台/十七形态和本地人工交付完成标准，审阅原 PRD、Registry/seed、F6E adapter/v5/package 和 Recipe 接线；保存 proposal/design/三份 delta，不写业务或正式库。
- [x] 0.2 完成独立 SPEC/实施计划复核、OpenSpec strict 和 diff-check，并交付用户确认；用户确认 proposal 后才进入 business apply，不把范围确认当公开发布或正式 profile 写入授权。

## 4. v2 规格修订与事实确认（2026-10-14，Phase 0 — 本轮唯一授权范围）

- [x] 4.1 核验 workspace、Git HEAD/dirty/untracked（73 条未提交/未追踪条目、3 个 stash）、active changes、alembic head（实测 `idx000000001`，30 revisions）；未追踪的 `AccountDesk.tsx`、`channel_methods.py` 等全部保全，未做任何 reset/清理。
- [x] 4.2 对 2026-10-13 AUDITED 回执逐条核对真实代码：`ContentSeries.account_id` NOT NULL、`hierarchy()` 选栏目必须选账号、`delivery.py` v5 `unit.account_id` 等值 409、`FIRST_BATCH` 实为 14/17 约定形态（缺 bilibili/image_note、x/long_post、x/articles；xueqiu×2/juejin 为范围外既有登记）、`ChannelVariantForm.tsx` 仅 5 schema、`App.tsx` NAV 含 `/accounts`；实测细节记入 findings。
- [x] 4.3 将 `AIContentStudio_OpenSpec_Multiplatform_Operations_v2.md` 拆归到本 change 的 proposal/design/tasks 与六份 delta specs（含新 capability `persona-channel-series-operations`）；保留原批已完成条目与原 design 平台表，v2 增补以独立章节合并，未删除原要求/场景。
- [x] 4.4 以实时代码对比零迁移与最小增量迁移并产出 ADR（`docs/ADR_SERIES_ACCOUNT_MODEL.md`）：结论为零迁移不满足判定门槛，推荐 `content_series` scope/persona_id 可空化 + 新 `series_account_target` 表；含 SQLite batch rebuild、备份、downgrade fail-closed 策略。
- [x] 4.5 运行 `openspec validate --all --strict`（基线与本轮结果均如实回执）与 `git diff --check`；记录准确命令与输出。
- [x] 4.6 返回 `SPEC_REVISED`；未获得独立 SPEC APPROVE 前不改业务代码/正式库，Batch A/B 全部保持未勾选。
- [x] 4.7 完成独立代码级规格复核（回应 REVIEW_PENDING 六项，全只读）：scope 分支实测六处站点并补入 design D-v2.2 与 ADR §6（`project_authorization.py:123-131` join、`project_matrix.py:76` 校验为新增发现）；正式库只读实测 `content_series` 0 行/`account_id` NOT NULL/head `idx000000001`；v5 逐账号幂等结构确认无需改动；17 形态缺口与 xueqiu/juejin 保全再次确认；六份 delta 与两个 active change 需求名零冲突。复核结论记入 findings，spec 文档按发现同步强化，业务代码未动。

## 5. 批次 A（v2）：身份、账号与跨平台栏目完整闭环（2026-10-14 BUSINESS_APPLY 授权后实施完成）

- [x] 5.1 按 ADR 实施迁移 `a3series00000001`（content_series scope/persona_id 可空化 + series_account_target 新表）；副本演练 upgrade→downgrade→再升级→fail-closed 全绿（/tmp/aics-series-migration-rehearsal）；正式库备份至 `backups/pre-series-scope-20261014/` 后升级，integrity/FK 干净；`LOCAL_APPROVED_SCHEMA_HEAD` 与 runtime.env `REQUIRED_SCHEMA_HEAD` 同步推进，launchd API 重启后 ready:true。
- [x] 5.2 Persona-owned editorial Series 创建/更名/归档/查询/版本（复用 ContentSeriesRevision）；同名栏目不自动合并；legacy Account Series 原语义、原路由、原校验逐字节保留（`content_identity.py` hierarchy/owned_entity scope 分支）。
- [x] 5.3 `services/series_targets.py` + `/content-series/{id}/targets` CRUD：绑定/解绑/启停带 CAS version，跨 Persona 拒绝、平台在营校验、`resolve_content_form` 形态校验、AuditLog 全程；同平台 A/B 账号独立绑定行有持久测试。
- [x] 5.4 目标账号上下文冻结进授权 `capability_snapshot_json.target_account`（账号 ID/平台/公开标识/账号修订 ID/profile checksum）；来源身份继续由 unit IdentitySnapshot 承载。per-target Variant 适配上下文（6.4）留在批次 B，此处不冒认。
- [x] 5.5 `delivery.py` 移除 v5 `unit.account_id` 无条件 409 锁；同渠道/跨渠道、同平台多账号独立授权；未绑平台老式账号保持原行为；legacy（master）候选固定账号语义原样保留。
- [x] 5.6 fail-closed：跨 Persona 账号 404、归档账号 404、平台不一致 422、停用绑定 409（guard_enabled_binding）；Unknown 不自动重发等既有契约未动。
- [x] 5.7 `/identities` 统一四区（身份树含 editorial 栏目、平台公开身份登记、栏目创建、投放绑定面板）；`App.tsx` 移除一级导航项，`/accounts` 转兼容跳转；AccountDesk.tsx 保留文件不再挂载；`npm run build`（tsc/vite/FE-P1 bundle 预算）全绿。
- [x] 5.8 持久回归：新增 `tests/test_series_targets.py` 5 例（无账号栏目+单元创建、legacy 规则、绑定合同、解锁+冻结目标账号+跨 Persona+平台不一致、停用阻断）；`test_migrations.py` 5/5（head 钉住更新 + up/down/up）；聚焦五套件 121 通过。全量后端 2564 例中 4 失败：3 例为本次迁移链断言已修复，1 例 `test_models_plugins.py::test_plugins_put_and_view` 为既有环境依赖（`~/.codex/skills/wewrite-write` 断链符号链接指向已不存在的 `~/Project/wewrite`，与本 change 无关，正式库经 skill_dirs 指向 new_media 不受影响）。浏览器点击冒烟未执行（Vite 属用户进程未动），UI 以 tsc/vite 构建验证。

## 1. 批次 B（原批次 A）：后端合同、适配与交付包

> v2 注：本节与第 2 节共同构成 v2 Batch B 的平台合同部分，任务原文保留；账号维度增量见 6.x。

- [x] 1.1 扩展服务端目录/descriptor 和增量 profile dry-run/apply：十七 exact forms、source compatibility、profile hash/version、可执行/本地包/远端分层；保留用户 profile，CAS/幂等/append-only，无全库 seed、默认改绑或新表/迁移。
- [x] 1.2 实现十二个新增 versioned canonical payload/validators 及共享 typed 文本/列表/图组工具：字段白名单、ID/order/边界/规范 hash、明确知乎 question/direct-answer、X 长帖≠Articles、真实图组；原五 schema/hash 不变。实施前先按 4.2 实测修正 catalog（补 bilibili/image_note、x/long_post、x/articles；xueqiu×2/juejin 仅保留登记不计入完成义务）。
- [x] 1.3 注册每目标 adapter/实际适配指令和受控模型建议，保存保持明确人工确认；精确引用/引用重定位/derived rights、safe verified LLMRun、人工修改来源可证明，零隐式 Master/事实/权利写入。
- [x] 1.4 完整接通新增 schema 的 checks/v5 builder/live validation/Review Approval/authorization/local ZIP：唯一 source FK、每目标 currentness、不 fallback、冻结正文/结构/安全 sources/declarations/HTML/media/平台指南；所有ZIP成员含manifest使用版本化公开export projection和独立export hash，Candidate原hash不变/不冒称可从删减字段重算，旧历史包不暗改；live 撤权/hash/旧授权历史完整。
- [x] 1.5 将十七目标接入既有 Recipe Variant Stage/Effective Preview/Attempt/feedback，明确接受为 Variant 不自动 freeze/approve/deliver；临时调节真实消费、409保留dirty、Unknown不重发；运行范围不扩到公众号或其他平台发送。

## 2. 批次 B（原批次 B）：产品入口、集中验收与收尾

- [x] 2.1 Production/Recipe/Variant 界面去掉五目标常量，消费服务端目录/descriptor；完成新增形态 typed editor、目标说明/实际Prompt、素材/证据引用和独立dirty/save，计划但不可执行目标给出原因。
- [x] 2.2 Review 展示各形态冻结预览/diff/checks和发布指南，本地包下载/人工回执与公众号自动草稿明确分开；缺账号资格仍可合法导出，缺远端验证不展示可发送，包/草稿不等于公开发布。
- [x] 2.3 在明确测试写入授权后增加少量参数化持久合同覆盖（canonical/hash、source/target、v5/currentness、安全export、live rights/篡改），集中完成十七形态页面/API/ZIP 冒烟和旧五形态/v1-v5/Graphic/Video/Recipe 回归；每形态核对保存刷新、独立系列、批准hash、完整媒体/来源、安全HTML/结构和人工状态，并验证 stale/撤权/篡改/409/无远端调用。未授权前不写新测试；受控链路、真实生成质量与平台真实发布分开记录。
- [x] 2.4 统一独立代码/安全/前端复核，复用既有backend回归及Web build/FE-P1预算，最终strict/diff；更新README/计划/进度/验收矩阵，逐项标真实完成或待授权，不以一个样本代替全部。
- [x] 2.5 得到单独正式启用授权后，配套备份当前SQLite/素材并dry-run审阅profile增量，在原本机库幂等启用必要profile；核对旧行/hash/素材/历史绑定保全及页面十七目标可用，不重启无关服务或改凭据/approved head。没有该授权时保留待启用，不写正式库。

## 6. 批次 B（v2 增量）：17 形态 Descriptor 编辑与逐账号交付（待 BUSINESS_APPLY 授权）

- [x] 6.1 逐项对照约定 12/17 catalog 与实际 `FIRST_BATCH`/canonical validators 差异清单（依据 4.2 实测），真实缺失的 schema/adapter/profile/required media roles 逐个实现；不依靠 README 功能宣称。
- [x] 6.2 实现或完善服务端 `ChannelFormDescriptor` 版控只读投影（字段路径/类型/label/required/readonly/default/边界/枚举、media roles、校验错误映射）；单一真源，不在前端复制第二套 schema。
- [x] 6.3 改造 `ChannelVariantForm.tsx` 为 Descriptor 驱动的全部 17 形态编辑器：blocks/text/citations/media/平台字段渲染、未知字段明确阻断或只读（不静默丢弃）、保存重开 hash 一致。
- [x] 6.4 按每个目标 Account 执行现有 `stage.variant.adapt@1`；必要时 target-specific Variant，明确复用条件与独立 Candidate/Review；目标账号上下文进入 Effective Preview 与冻结 refs。
- [x] 6.5 完成 12 平台/17 form 的真实 ZIP 本地交付（稿件+真实 media bytes+manifest/rights/hash，含安全 export projection），公众号仍只走原有授权草稿箱能力；导出包不记录为发布成功。
- [x] 6.6 加入少量参数化持久合同测试覆盖 17 forms、12 schema/adapter 契约、ref/hash/stale/rights/tamper、target account、candidate freeze、package（与 2.3 授权边界一致）；不写 17 套重复 E2E。
- [x] 6.7 对 UI 和本地包执行集中 17-form smoke，校验打开/编辑/保存/重开/候选/导出；对缺真实媒体或需实际 Provider 的 form 如实阻断，而非虚构成功。

## 7. 最终验收（v2）：两 Persona 实际工作流与关闭条件

- [x] 7.1 技术 Persona 从 Persona-owned Series 创建内容，真实生成并接受一篇文章、成套图文 PNG 和一份可播放音频（调用真实 Provider 前先取得明确授权），保留 QC、哈希与署名质量评审证据（2026-10-14 用户明确委托 Codex；实际评审方法与限制分别记录）。
- [x] 7.2 生活方式 Persona 独立完成 Text/Graphic/Audio，同样通过真实成品检查；涉及“正在发生”的事实必须来自 fresh source，不能编造新闻。
- [x] 7.3 同一技术栏目跨公众号/知乎/小红书的不同 Account：各自精准 Variant/Review/授权/本地包或公众号草稿，证明无 409；另证明小红书 A/B 双账号能够独立分发而不串用身份。
- [x] 7.4 老 Account Series/Unit/legacy Candidate 在迁移后与迁移前一致；旧快照、交付历史、F6D/F6E 契约和 DB 完整性保持正常。
- [x] 7.5 完整 backend tests、UI build/perf/关键浏览器 smoke、OpenSpec strict、diff-check、SQLite integrity/foreign keys、schema-head readiness 全部留回执。
- [x] 7.6 汇总并独立复核 `add-persona-creative-studio` 剩余人工质量项和 `creation-recipe-stage-control-loop` 收尾项；不得因为当前 change 完成而将它们自动标为通过。
- [x] 7.7 交付可查的完成矩阵（Requirement → current code → persistent test → UI → real artifact/receipt），明确 `contract-complete` 和 `quality-accepted` 两种不同状态。
- [x] 7.8 经用户分别授权后，才允许正式库迁移、真实 Provider 测试、canonical sync/archive、commit/push；本文件和 SPEC_APPROVE 都不自动授权这些动作。

## 3. 生命周期（原批）

- [x] 3.1 实施/验收/独立复核全部通过并获准收尾后，同步本change delta（含 v2 六份）到canonical、保留原要求/场景，再归档/strict/diff和本地提交；不归档或覆盖F8/ACO/Recipe，push与公开发布仍需单独授权。

Batch B回执：本轮授权的16项实现/持久覆盖/集中17-form UI/API/ZIP与独立代码复核已完成，详见progress.md和docs/BATCH_B_RECEIPTS；2.5及第7节/3.1仍独立，不能据此宣称真实质量或公开发布完成。

全权授权后回执：2.5正式启用及7.3–7.8机器/独立核对项完成，40/43；新两Persona生成/QC成果汇总中，7.1/7.2复合项的人审仍不冒称通过。3.1全验收收尾条件未满足；不是等待权限。正式与隔离、真实成品与QUALITY_ACCEPTED分别记于progress/findings/review及E5。

最终质量回执：用户明确委托的 Codex 与独立整模态评审通过，7.1/7.2关闭，42/43；quality-review.md/json保留真实方法，未冒称人工试听。3.1由通过后的规范/Git收尾完成。

生命周期回执：七capability同步23新增/2修改/0删除，原requirement/scenario与两相邻任务hash保全；本change归档于2026-10-14，43/43。本地提交以实际Git回读为准，未push/公开发布。归档运行时唯一未勾项为此生命周期自身，42/43日志如实保留。
