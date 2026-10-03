# F8 Production Readiness Implementation Plan（2026-10-03 继续）

## 2026-10-04 本地 main 提交（已授权）

**Goal:** 将已验收的F8本机实现提交到当前main，保留未批准身份/schema草案和原始资料，不push/deploy/迁移/主规格同步或归档。

/// 检查main与空暂存区 → 私有索引只纳入获准本机代码/规格/证据，排除JWT/User字段/f8a/生产启动开关和未来MinIO实现 → 用无Git注册的临时源码快照验证拟提交树 → 核对差异/凭据与延期状态 → 本地提交main → 记录hash并检查草案仍完整保留。

- [x] 固定拟提交范围；混合config/product-settings/storage/observability/Web team仅纳入本机片段，不改正式工作文件的草案。
- [x] 拟提交快照完整后端、Web/FE-P1、Ruff/OpenSpec/diff及限定提交边界复核；全量1660/28 skipped、build/预算及静态门禁通过，Hubble限定复审APPROVE，3.3状态校准完成。
- [ ] 本地main提交并记录hash/ROADMAP本机状态；保留18延期与active change，不执行主规格同步/归档。

提交边界复核纠正：3.3声称MinIO已交付与实际拟提交树不符，已重开并按既定local-only profile列入未来范围。当前81/82本机、81/100原清单、18延期；下方17/83历史计数由此替代。不补做或混入未来MinIO实现。

## 当前补验批次（上轮 PASS 纠正）

/// 纠正 Golden/分组回归/历史浏览器的过度结论 → 仅批准 f7d head 隔离数据库 + local media + loopback 新浏览器验收 → 新运行状态页 admin/viewer/no-auto-probe/failure 投影 → 独立安全/架构复核 → 根据真实证据修正 tasks/README/progress，不启用 f8a、不提交推送归档。

- [x] 纠正正式 PASS、Golden 覆盖及 worker 临时库 head 说明；10.6 重开，75/100。
- [x] 隔离 f7d/no-draft-User schema、同 Project 三形态五渠道 13 个浏览器 gate、F8 状态页 7 个 gate及 legacy no-probe 复验。
- [x] 恢复 DB + 复制 media 实际启动/五包逐文件匹配；Identity/Content Golden 真正读取 hash 并验证事实、Brief、Run pinning 和成片 Video。
- [x] 收到并解决独立复核发现；此前总体复核及最终定向复审闭合四项 blocker，Harvey 安全/运维与 Copernicus 架构均 APPROVE（仅本机范围）。

/// 补三处定向复核残余：按字段拒绝JWT/正文/bool telemetry、每跳 query 跨域（含返回原域）零转发、integrity只读URI → 新鲜全量/strict/Ruff/diff → 独立窄复核 → 保持6.1–3和总体10.8/10.9开放，按证据关闭10.6，当前76/100。

/// 接收复核后的最小修正：先用临时隔离探针复现 approved f7d 被错拒和 backup integrity 失败仍 exit0 → 在既有 readiness/recovery 契约内修正 → 复跑探针/既有门禁/浏览器；不添加永久测试，不授权 f8a 或更改正式库。

/// 安全复核收口：临时RED探针验证 raw audit/worker exception、HTTP method cardinality、legacy Settings自动dsh probe、legacy fetch全量读取/跨域凭据 → 最小allowlist/固定错误/OTHER/no-probe/流式有界修正 → 既有定向和全量回归 + 独立定向复审。已批准业务范围不变，不添加永久测试。

> **For agentic workers:** 使用 superpowers:executing-plans 批量执行；仅对计划/实现作独立只读复核，不委派业务开发。

**Goal:** 完成本轮获准本机 F8 的 83 项实现、恢复与产品闭环验收，并与 NorthStar/产品契约核对；原 100 项中 17 项生产身份/Secret Provider/新真实远端发布按用户确认延期，保留未勾选义务。不能把一批基础设施通过等同整个产品完成。

**Architecture:** 沿用 User/Role、MaterialRevision/StorageProvider、Run/Attempt、Candidate/Receipt 真源。基线 main@a59d5de，F7 已本地提交及 canonical/archive。用户已确认本轮正式验收基准为单机 SQLite + 本地素材库 + loopback 访问；PostgreSQL/MinIO 仅保留未来部署 profile，不作为本轮门槛。身份/schema 草案仍未批准。

**Tech Stack:** 现有 FastAPI/SQLAlchemy、Celery、React/Vite、OpenSpec；不新增依赖、业务表或永久测试代码。旧 F8 身份/schema 草案仍需单独批准，不执行正式迁移。

/// Batch A：读取现行 F8 两份 delta/设计/任务，核对 F7 已归档前置 → 计划独立只读复核 → 健康检查 required storage/worker、safe status、retention/secret 既有边界实测及最小修补 → 既有定向回归/临时隔离探针、strict/Ruff/diff → 据完整证据勾选并同步进度。
/// Batch B：按获准本机范围完成认证边界说明、SQLite/local storage 全消费者/生成任务兼容、correlation/外部安全收口；身份配置/迁移切换仍需精确授权。
/// Batch C：隔离 SQLite + 本地媒体备份恢复/降级 preflight、版本化 Golden、三模态 Opportunity→Variant→Review→本地交付全链路；真实发布/学习分支没有证据时保持未验收，既有微信 draft-only 证据不冒充公开发表。
/// Batch D：实际浏览器与设计高保真核对、完整后端/Web/预算/迁移/strict/Ruff/diff、独立安全及产品架构终审、状态矩阵/本地提交与获准生命周期收尾；没有完成所有要求之前保持目标 active。

**Batch A files:** `apps/api/app/observability.py`、`apps/api/app/runtime_config.py`（实测签名URL/签名secret分类缺口）、`apps/api/app/services/retention.py`、`apps/api/app/services/product_settings.py`、`apps/web/src/product/ProductSettingsPage.tsx`（只补必要运行状态）；`docs/FE_F8_BASELINE_AUDIT.md` 和本三份进度文档。验证复用 `test_observability.py`、`test_retention.py`、`test_product_settings.py`、`test_settings.py`、`test_task_queue.py` 及相关现有 storage/material/package 回归，临时探针只使用内存/私有临时库。

- [x] 读取全部现行 F8 contextFiles，起点 spec-driven、18/100；核对已归档 F7 后关闭0.1，当前19/100。没有把 F8 dirty 草案视为已验收。
- [x] 独立复核本批计划；补齐可执行命令/明确断言、Web本批门禁和19/100当前计数后，计划复审Approved。提出的部署选择不阻止其他无副作用基础工作。
- [ ] 实测健康检查的真实本地 storage/worker 正负拓扑、optional provider 零调用；最小修复实际缺口。
- [ ] 实测保留项目/immutable Attempt/产物/AI receipt 历史，旧无引用 run 仍可清理；不清理正式库。
- [ ] 复用安全状态与 secret 回归，形成不泄漏配置值的证据；不删改正式 SystemSetting。
- [ ] 本批新鲜定向门禁、严格规格验证、限定实现复核、任务与 README/进度同步。

**Batch A runnable gates / expected evidence:**

- 在 `apps/api` 执行 `APP_ENV=test LLM_PROVIDER=mock DATABASE_URL=sqlite:////private/tmp/aics-f7-close-Ro2XB0/worker-test.sqlite .venv/bin/pytest tests/test_observability.py tests/test_retention.py tests/test_product_settings.py tests/test_settings.py tests/test_task_queue.py tests/test_material_library.py tests/test_f6a_v4_delivery_closure.py -q`；要求完整输出无失败，不碰正式 worker 库。
- 健康拓扑临时命令为 `APP_ENV=test LLM_PROVIDER=mock .venv/bin/python -`（内存 SQLite，`TemporaryDirectory`，Celery memory transport/solo worker；诊断正文与 stdout 由执行记录保留，不创建永久测试代码）：真实临时素材目录应 ready，不存在的目录必须 storage=false/503；真实 broker 无 worker→worker=false/503，活 worker→true/200，停止 worker→false/503。额外注入 credential-bearing probe 异常只得到固定 reason。探针保持 connect_timeout=2/零重试、有界 worker ping；任何真实供应商方法均替换为“调用即失败”守卫，要求调用计数0。
- 历史保留临时命令同为 `.venv/bin/python -`，只使用内存业务库和临时媒体目录；分别建立旧无引用 run、project-bound run、Attempt/候选/任务/Master/snapshot/output 引用，执行真实 `run_retention` 后要求仅旧无引用 run 被删除，两类 AI parsed receipt 原样保留且 raw payload 清空，孤儿处理不删除有引用字节。
- 若触及 Web，`npm --prefix apps/web run build`（含 FE-P1 预算）及隔离页面/API 的 admin/non-admin 安全状态、零供应商探测验收必须在本批完成，不推迟到终验。只读 Settings 不主动调用 health/network；显式刷新运行状态才读取就绪摘要。
- 结束执行 `OPENSPEC_TELEMETRY=0 openspec validate --all --strict`、`apps/api/.venv/bin/ruff check apps/api/app/observability.py apps/api/app/services/retention.py apps/api/app/services/product_settings.py`、`git diff --check`。缺少拓扑/浏览器/安全证据的复合任务保持未勾，不从窄单测推定完成。

下方为已完成批次的历史记录，不代替 F8 当前验收。

# F7 本地提交与主规格归档收尾（2026-10-03）

**Goal:** 用户授权继续剩余三项；将Commons明确记为暂缓/未实测，完成F7相关本地提交与canonical同步/归档，不扩展F8或其他change。

**Architecture:** 已有F7实现与证据保持不变；对混合工作树只提交F7所属文件/片段，F8及原始规格包保留。主F7五份delta、模型路由delta和已归档的公众号系统记录delta按要求级合并，保留canonical原有契约。

**Tech Stack:** 既有Git/OpenSpec、Python/FastAPI、React/Vite；不新增业务代码、表/迁移/永久测试，不发公众号、不调用供应商、不写正式库。

/// 确认Git/归档授权与Commons暂缓 → 独立只读核对混合改动边界并固定F7提交范围 → 在私有临时checkout验证只含F7的提交树 → 本地提交实现 → 要求级同步全部F7相关delta并做preservation audit → 归档主F7/模型路由 → strict/diff与本地归档提交；不推送、部署或提交F8。

- [x] 固定F7范围，保留F8/无关改动；Commons范围延期记录，不冒充真实PASS。独立边界/保留性复核完成，81文件私有投影排除F8认证/MinIO/schema迁移，仅保留F7本地字节依赖。
- [x] 验证并本地提交F7实现，记录确切commit：3f28a51d0145c49ae558766aeebbdbed68a8fcc1。81文件私有索引已提交，实际索引清空，F8/原始包与混合历史资料仍保留。
- [x] 同步五份主F7、模型路由及公众号系统记录长期契约；八份delta合并七份canonical，原有54条要求/146个场景精确保留，范围前言保留，Purpose正式化。
- [x] 归档已完成F7/模型路由，更新README/进度并完成最终strict/diff和本地归档提交；不推送，F8保留。归档日期2026-10-03；实际最终hash由Git提交后交付。

本轮技能：using-superpowers、writing-plans、executing-plans、openspec-archive-change、finishing-a-development-branch、verification-before-completion；执行范围已由用户明确选择为本地main收尾，跳过新分支/推送选择。

F7-only快照1660/28 skipped、Web/FE-P1/state、Ruff/strict34/diff及共享提交边界复核已通过；本轮另实际使用requesting-code-review、receiving-code-review、dispatching-parallel-agents、systematic-debugging。调试仅修正私有worker测试库初始化，未开发新业务或测试代码。

# F7 当前版本公众号单次草稿验证（2026-10-03）

**Goal:** 用户已明确授权原账号/原短稿正文/黄色封面再创建一次草稿；关闭成功Attempt与当前runtime的证据绑定缺口，不公开发布。

**Architecture:** 复用既有Candidate→Approval→DeliveryAttempt→Receipt→CapabilityVerification；在私有隔离库创建新的当前版本产品记录，原成功/Unknown记录不可改写。真实同账号人工确认才写human_confirmed。

/// 先细化既有规格并用无网络内存探针复现历史Attempt晋级缺口 → 最小修复和既有回归/限定复核 → 当前实现下重新冻结并审批原短稿和黄色封面 → 产品适配器一次draft/add，保留media_id → 等真实同账号确认后原子记录验证；结果未知不重发，不调用draft/get，不提交推送或归档。

- [x] 补齐Attempt指纹绑定、负向/正向/原子回滚验证及既有回归（临时无网络探针、120既有定向、Ruff；全量与限定复核另记录）。
- [x] 当前版本产品Candidate/Approval/单次草稿执行与安全证据（16:42 Target7/Attempt7 succeeded；原六Attempt不变，media_id持久保存，未回读或公开发布）。
- [x] 用户实际确认最新草稿后系统Receipt1/Verification1原子持久化；新进程重复幂等、精确scope拒绝六种变化通过，关闭8.3/10.5，当前107/110。

本轮使用using-superpowers、writing-plans、executing-plans、openspec-apply-change、systematic-debugging、test-driven-development（仅临时探针）、requesting-code-review、verification-before-completion；无新表、迁移或永久测试文件。

最终本地门禁：120既有定向、1660全量/28 skipped/8既有warnings、Ruff/strict34/diff及限定独立复核通过。真实微信外发一次成功，用户实际确认后Receipt1/Verification1持久化，网络禁止的新进程复验通过。当前F7为107/110，剩Commons暂缓、本地提交、主规格同步归档。无前端改动或本轮Web/native PG重跑；未commit/push/archive。实际另使用receiving-code-review核验复核反馈。

# F7 主清单剩余验收收口（2026-10-03）

**Goal:** 收口已批准范围内的 F7 验收与证据，不重复生成或发送草稿；基线为 main@8c0e3b8、F7 104/110、模型路由23/23。

**Architecture:** 继续复用 DeliveryAttempt/Receipt/CapabilityVerification 和 ProviderGenerationTask/MaterialRevision/Master。历史成功、当前运行验证、合成回归与用户排除分开记录；不得复制旧库记录到正式库或替换原验证指纹。

**Tech Stack:** 既有 SQLite、Python/FastAPI、OpenSpec；本批只核对记录并更新文档，不改业务代码、依赖、迁移或运行配置。

/// 只读核对两份已成功公众号记录及原账号/当前指纹 → 核对真实 MiniMax 图片、正式 TTS 接受和本机字幕记录 → 限定计划/证据复核与既有回归 → 只勾有完整证据的主任务，保留需要新外发授权的公众号验证 → strict/diff并交接；不发草稿、不重试Unknown、不付费生成、不提交推送或归档。

- [x] 公众号核对：短稿Attempt6和HTML Attempt1仍succeeded、有效remote_id、原账号匹配；两库Receipt/CapabilityVerification均0，正式库无公众号Attempt。两个历史registration和Attempt runtime均不匹配当前实现，不补签、不修改原记录。
- [x] 模型核对：真实image-01任务仍result_ready/rev3、JPEG33997bytes及原hash；正式TTS任务accepted/rev4→MaterialRevision6；Video Master5/v3仍43字幕、Text Master9/v3仍保留。视频/H3用户排除，CPA媒体未证实，Commons暂缓。
- [x] 限定独立计划/证据复核；复用既有交付、能力与ASR回归119通过，不新增测试代码。复核同意关闭10.3、保持8.3/10.5；已修正文档对历史Attempt指纹校验的夸大描述，实际缺口仍列8.3。
- [x] 按上述实际范围关闭10.3并更新主清单/README/验收文档；当前105/110、剩5条，其中Commons暂缓。8.3/10.5需补显式Attempt指纹绑定及当前实现的真实成功与系统收据，不从旧成功或夹具推定。
- [x] 最终OpenSpec strict34/34及git diff --check通过；本批无业务代码或前端修改，未重跑全量/前端/PG，不冒充旧结果。提交/归档另行收口。新的公众号外发是原单次授权已消费后的新副作用，必须先获一次精确授权。

本轮实际技能：using-superpowers、writing-plans、executing-plans、openspec-apply-change、requesting-code-review、receiving-code-review、verification-before-completion；dispatching-parallel-agents仅检查后未采用并行，openspec-archive-change未执行。

# F7 模型路由剩余五项批量收尾（2026-10-03）

**Goal:** 按已批准的当前账号范围一次收口2.1/2.5/2.6/2.7/2.9；沿用真实CPA/MiniMax/本机ASR验收，不重复付费或公众号发送。

**Architecture:** 复用SystemSetting、ProviderGenerationTask、现有Workflow/MaterialRevision/Master；原生Google/xAI不在范围、MiniMax真实视频为excluded而非PASS，公开/商业权利未验证时保持false。仅隔离库运行故障与Workflow验收。

**Tech Stack:** 现有Python/FastAPI/SQLAlchemy、React/Vite；无新表/迁移/永久测试代码，不改正式库或默认模型。

/// 核对当前契约与真实证据、修正旧文档 → 独立Provider安全和消费者复核并行 → 隔离Workflow全链路/现有回归 → 全量后端、Web预算、strict、Ruff/diff → 独立复核问题最小修正和统一任务记录；无push/deploy/canonical-sync/archive。

- [x] 2.1：精确CPA聊天及MiniMax image/TTS/ASR协议和权利界限；以当前已完成真实证据替换旧401/未接入描述。
- [x] 2.5：有界发送、私有字节/解码/哈希/权利、原job恢复与Unknown边界。
- [x] 2.6：Production/Workflow接受、项目精确引用、ASR血缘及native/plugin解释。
- [x] 2.7：既有安全兼容回归及隔离运行；不为补计数增加新功能或测试文件。
- [x] 2.9：新鲜全量门禁与独立Provider安全/消费者复核；完成后仅报告本change23/23及归档准备状态，不冒称整个F7已归档。

最终：23/23，backend1660 passed/28 skipped/8 warnings101.93秒，177定向5.98秒；Web/FE-P1/state、九文件Ruff、strict34/34、diff通过。五处原契约缺口逐项RED/GREEN修复，Provider安全与消费者独立复核APPROVE；新增真实供应商调用/正式库写入为0。仅五个既有源码文件及原规格/文档，未提交/推送/canonical-sync/archive。本轮实际技能：using-superpowers、writing-plans、executing-plans、openspec-apply-change、dispatching-parallel-agents、requesting-code-review、receiving-code-review、systematic-debugging、test-driven-development（临时探针，不新增永久测试）、verification-before-completion。

# F7 产品路由与页面链路整项验收（2026-10-03）

**Goal:** 连续核验既有模型配置→聊天模型自动媒体插件→持久任务→预览→人工接受的页面链路及不可用/Unknown边界；真实TTS和本机ASR沿用已经完成的真实证据，不重复供应商发送。

**Architecture:** 独立临时SQLite/API/Web，注册明确标识的合成image/TTS Provider；配置resolver、generation tasks、raw校验和素材接受使用真实服务。绝不把夹具结果当作MiniMax真实生图或改正式模型配置。

/// 读现有Panel/路由/规格 → 启动隔离fixture且供应商0调用 → 实际页面配置/准备/发送/预览/接受/刷新与不可用/Unknown验证 → 范围复核及现有门禁 → 按完整证据收口任务或列明真实合同缺口。

- [x] 隔离页面完整链路、原任务Unknown和unsupported路径验收；记录fixture与真实范围。两accept、Unknown不重发、缺video插件、页面配置保存及旧任务发送前拒绝均通过。
- [x] 只关闭2.8；2.1/2.5/2.6/2.7/2.9保持开放，不把页面fixture自动记为供应商协议或Workflow整体PASS。限定源码复核APPROVE，补丁后的中文提示/原task回读现场复验通过。
- [x] 更新README、进度与证据，不重复付费调用、不推送、不归档整个F7。当前18/23；本批使用OpenSpec apply、执行计划、调试、接收/请求复核及完成前验证技能。

# F7 生成任务可靠性整项收口（2026-10-03）

**Goal:** 一次完成已授权模型路由 tasks 3.2/3.4 的本地可靠性验收，不逐个环节请求确认。

**Architecture:** 沿用单一 ProviderGenerationTask、既有 CAS/lease/HMAC、受控本地 storage、MaterialRevision 及项目引用。故障仅在新私有 SQLite 和合成 Provider 中模拟；不修改正式库或真实任务，不调用 MiniMax/CPA/微信。

**Tech Stack:** 既有 Python/FastAPI/SQLAlchemy、SQLite、provider_calls/provider_media；无新依赖、表或 migration。

/// 核对现行 change 与源码 → 幂等/并发发送及接受/崩溃与晚worker/原job恢复/凭据和key漂移/篡改与回滚整批验证 → 只修复现有契约缺口 → 既有回归、strict/Ruff/diff及独立定向复核 → 统一更新 tasks、README、progress、findings；不付费调用、不推送、不归档整个F7。

- [x] 现行规格为 `add-model-capability-routing`；main@8c0e3b8 加既有未提交 F7/F8，15/23 完成；保留所有已有改动。
- [x] 补齐同键冲突、真正并行发送/接受、崩溃窗口、原job有界恢复和CAS/lease的实际证据；38个隔离场景通过，真实供应商0调用。
- [x] 补齐key/凭据漂移、foreign/篡改、撤权、回滚与历史兼容性证据；没有新增持久测试代码，144定向/1660全后端通过。
- [x] 独立复核APPROVE、最终后端1660/28 skipped及Web/strict/Ruff/diff通过，勾选3.2/3.4；本change17/23，余6复合项。真实视频仍排除，不冒称整个F7完成。

/// 定向复核新增：先复现 retained-key 对真实 MiniMax credential epoch 的误拒绝和 terminal foreign-job 接受 → 最小修复历史 key-ID 身份校验及所有输出的 job/file 契约 → 复跑对应场景、既有全量门禁与定向复审。来源撤权以既有 claim commit 授权边界核对，不新增跨网络数据库锁或业务对象。

- [x] 修复保留旧 receipt key 时，MiniMax 历史任务必须用原 key 派生 credential epoch；真实凭据仍不输出或修改。
- [x] terminal output 必须验证原 job/file，不把 foreign job 的合法字节签给本任务；known-job unavailable保留Unknown。
- [x] 复核撤权与 claim 的事务先后顺序及无网络 DB 锁约束，明确并验证安全线性化点。

# F7 模型能力下一项验收（2026-10-03）

**Goal:** 继续已批准的 `add-model-capability-routing`，关闭可证实的模型安全回归与产品接受链路；不重复已验收的公众号和本机ASR。

**Architecture:** 保留现有 SystemSetting、ProviderGenerationTask、MaterialRevision 与 Master 真源。正式库当前仅有一个 prepared TTS 任务；上传音频不能作为该任务的生成结果。新供应商调用须获得明确单次授权。

/// 核对实际任务与ASR既有证据 → 复用现有安全回归/前端构建与规格门禁 → 确认单次TTS授权后走页面执行、预览、接受、精确引用与Master保存 → 按实际证据核销；不改模型默认、不视频生成、不重发公众号、不提交推送。

- [x] 确认本机ASR已验收；正式TTS任务 `331e55283ab8402f9c564c3145d4a101` 为 prepared/revision1，未有 accepted MaterialRevision。
- [x] 运行当前模型路由/媒体接受/ASR安全回归、前端状态与构建预算、strict/diff；定向后端 `144 passed`，状态脚本与构建通过。
- [x] 获得单次≤10秒TTS明确授权后验收正式任务接受链路；任务实际执行一次并进入 `result_ready`，随后人工接受。
- [x] 将接受结果写入正式素材库，建立 Project 1 引用，并保存到当前可写 Unit 3 的 append-only Text Master revision 3；精确 hash 与权利状态已回读。
- [x] 记录真实范围与未覆盖项，不将通用供应商/所有任务并发恢复声明为通过；素材页显示任务 `accepted / revision 4 / MaterialRevision 6`，Unit 3 Production 显示 Master #9 与 rights blocker。

# Local MLX ASR Implementation Plan（2026-10-03，apply已授权）

> 用户本轮明确进入apply；使用superpowers:executing-plans和openspec-apply-change，直接main按两批执行，保留其他dirty改动。

**Goal:** 复用Radar/voice-pro的本机MLX能力，真实跑通正式音视频素材→ASR建议→校对/接受→显式保存Video Master；MiniMax只保留用户显式云端选择。

**Architecture:** 单一新增Provider桥接既有Registry、ASR receipt及Master；受控离线模型/进程/runtime指纹。本地优先仅ASR选择，不新建全局模型配置、任务引擎、表或migration。

**Tech Stack:** 现有Python/FastAPI/React/SQLite、ffmpeg/ffprobe与voice-pro ARM MLX环境。无新安装或模型下载。

**File responsibilities:** 新增`apps/api/app/services/local_mlx_asr_provider.py`负责固定MLX进程与结果适配；限定修改`config.py`及既有Registry初始化负责显式启用/受控配置；`provider_calls.py`负责仅服务端本机有界等待；`asr_suggestions.py`保持精确来源/currentness/receipt并传递本机上限；`routers/content_masters.py`和`AsrSuggestionPanel.tsx`负责安全可用投影/本地优先/云端提示。不修改Radar/voice-pro，不重构其他模态。

/// 用户确认当前标准OpenSpec apply → Batch A一次完成本机桥接/离线与有界执行/现有API及字幕面板接入 → Batch B真实音视频页面保存与兼容安全门禁 → 独立复核和文档交接 → 获准后仅同步本新增主规格并归档；不付费调用/上传云端/新增测试代码/迁移/推送。

- [x] 产品目标已确认，标准包位于openspec/changes/add-local-mlx-asr；现有路径/代码静态核对完成。
- [x] 当前proposal/design/spec/tasks完成严格验证（全部34/34）、diff-check和定向规格/计划独立复核（SPEC/PLAN Approved）；原主规格未改，上传入口上限归属已澄清。
- [x] 用户已明确批准当前标准提案apply。/// 精确代码与本机缓存预检 → Batch A本地Provider及现有UI → Batch B真实识别/显式保存和回归 → 独立复核；不云端调用、安装下载、迁移、推送。
- [x] Batch A：完成tasks1.1/1.2，实际环境缺失/大小/时间/模型许可与云端选择均fail-closed；不改CPA默认/文本routes/原素材权利。
- [x] Batch B/2.1：用户提供的真实MP4已进入MaterialRevision3与项目共享素材；页面本机MLX请求→43条字幕预览→人工接受→显式保存Master5/v3→刷新/API重启回读通过，source/runtime/provenance为本机且`verified_output_match`。未公开发布，public rights仍为false。
- [x] Batch B/2.2：新鲜全量门禁与最终独立复核通过；`local-asr-subtitles`已同步到canonical并归档本change。不提交其他dirty内容，不推送/部署/迁移。

**Required gates after apply:** 现有`test_f7_asr_suggestions.py`及相关capability/provider回归；`npm run build`含FE-P1；OpenSpec all strict与范围Ruff/diff；实际本机无云端发送证据/进程超时回收/模型fingerprint变更/源权限/CAS/历史边界以及页面保存证据。不得写新测试代码，不以旧全量结果或静态文件存在代替执行。

**Stop conditions:** 缺可用运行环境/模型/明确许可、不支持隔离，或必须新表/安装/放宽大文件和权限契约时回到规格，不自动使用MiniMax。新付费生成接受和其他F7/F8仍在原change中保持独立。

当前实施证据：241定向/1660全量既有后端通过（28跳过）、Web/FE-P1及strict34/34通过；断网adapter WAV/MP4、网络拒绝/无凭据/超时回收/输出限额实测通过。Unit2/Master3空Video页面已验证本机默认与显式云端警示；API重启后页面/库存仍可读。七源码限定安全复核APPROVE，旧离线旁路已闭合；当前2/4，仍需用户明确许可的短音视频完成真实字幕保存，不提前归档。

本轮实际技能：using-superpowers、openspec-apply-change、executing-plans、writing-plans、test-driven-development（遵守用户不新增测试代码，复用既有回归）、systematic-debugging、receiving-code-review、requesting-code-review、verification-before-completion；尚未提交/归档。

# FinanceOpinionRadar ASR 复用范围核对（2026-10-03）

**Goal:** 先解释新生成接受/ASR字幕两个验收边界，核对现有本机识别能力，确认目标后再修订OpenSpec；本轮不实施业务代码。

**Architecture:** 候选为复用Radar的MLX子进程桥接和统一毫秒段落结果，接入Studio现有ASRProvider/建议receipt/Video字幕显式保存；不搬雷达抓取、观点、数据库或任务引擎。

**Tech Stack:** 现有MLX Whisper与voice-pro Python运行环境，Studio现有Provider Registry/ASR建议UI/Video Master；是否需要新配置与执行上限待规格确认。

- [x] 核对两项目README、相关ASR源码和Radar非敏感ASR配置。图谱工具当前不可用，仅对相关目录做限定搜索。
- [x] Radar配置ASR_PROVIDER=mlx，使用voice-pro的venv_arm64/python3.12与mlx_worker.py；两路径存在。尚未实际加载模型或转写，不把路径存在当执行成功。
- [x] Studio已有ASR建议API/UI及receipt→本地字幕→显式保存Master，不是从零建设字幕系统。现有入口最多10分钟、同步调用30秒，不能盲搬Radar的1小时进程timeout。
- [x] 用户确认本机优先、MiniMax可选；首批沿用段级字幕及已有10分钟/文件上限，不加入逐字高亮/长素材扩容。真实样本和许可在apply验收前选择。
- [x] 按确认范围完成标准OpenSpec和规格/计划复核；后续apply等待明确确认，未复用业务模块或进行真实页面验收，不写新测试代码/付费调用/迁移/提交/归档。

本轮实际技能：using-superpowers、openspec-explore、writing-plans（仅维护核对计划，尚未产出实施方案）。

# MiniMax 本地正式接入 Implementation Plan（2026-10-03）

> 用户已明确授权现有本地库接入和页面→正式素材库→Master；使用 executing-plans / openspec-apply-change 在 main 成批执行。

**Goal:** 在当前个人本机运行环境启用已验证MiniMax能力，保留CPA默认/用途选择，并以真实既有音频验证素材精确引用与Master持久化。

**Architecture:** 沿用已批准F7 migration、SystemSetting能力路由、固定CLI、MaterialRevision/ProjectMaterialReference和Master；本地启动脚本加载明确稳定签名key。原隔离任务不可伪装成正式库任务，复用字节须如实标记导入；完整付费执行另按授权次数处理。

**Tech Stack:** 现有FastAPI/SQLite/Alembic、React/Vite、mmx和ffmpeg；不新增业务表或依赖，不启用F8身份migration。

/// 核对实际8000进程/本地库和启动配置 → 私有SQLite在线备份/副本迁移演练 → 精确升级到f7d且保留旧业务数据 → 固定私有签名配置与MiniMax image/TTS/ASR绑定（不启用视频、不改CPA） → 页面导入既有真实WAV/项目引用/Master保存刷新 → 无网络任务准备与重启可用性核对 → 既有回归、规格/构建检查与证据记录；不公开发布/推送。

- [x] 实际API PID17544、cwd apps/api、打开的库是content_studio.db；当前Alembic为d4audit00004，媒体/项目/Master为空，模型配置revision3。
- [x] 私有在线备份、迁移副本演练及数据保全核对；所有原表记录保留，97条既有FK问题未增加。
- [x] 精确升级f7d、稳定签名/CLI启用、image/TTS/ASR受限绑定及API/Worker重启；无f8a，CPA默认/文本routes/密钥保留。
- [x] 页面导入既有真实WAV→MaterialRevision2→项目精确引用→Master2/v2；浏览器显式保存、刷新和服务重启回读通过。来源仍upload，公开/商业许可未确认。
- [x] 页面仅准备TTS任务并显示Gemini→MiniMax插件路径；未执行生成，新进程验签通过。118项既有回归、Web/FE-P1、strict33/33、diff与限定只读复核通过。

**本批验收边界：** 本地激活与既有音频的正式引用链路完成；新正式任务的付费execute→preview→accept、Production ASR建议接受/字幕保存未在本批执行，不冒称F7全关。无新增测试文件/迁移版本、commit/push/归档。

**本批实际技能：** using-superpowers、writing-plans、executing-plans、openspec-apply-change、systematic-debugging、test-driven-development（配置例外及现场失败→修复→复验，不新增测试代码）、verification-before-completion、requesting-code-review。

# 模型设置提交与验证（2026-10-03）

/// 按用户决定排除MiniMax视频/H3下载验收 → 同步active规格与历史/范围记录 → 确认语音样本及单次调用限额 → 验证TTS、ASR和已有视频音轨转写；不生成或重试视频。

- [x] 用户明确不要求MiniMax视频；排除不是PASS，保留旧任务与generic协议，不再查询。
- [x] 用户确认共三次调用：一次≤10秒TTS、一次音频ASR、一次视频音轨ASR；不生成视频、不自动重试。采用短句“这是语音能力测试，请准确转写。”及其音频制成的明确标记测试容器。
- [x] 本轮三次真实调用完成：TTS 3.413秒、WAV ASR与MP4音轨ASR均准确返回原句；新进程同key验证任务/结果签名、凭据epoch及字节hash通过。
- [ ] 正式媒体binding/持久任务schema与签名配置、显式素材接受和完整Production ASR入口仍单列；本轮只是隔离持久任务TTS+真实ASR适配器验收，不授予公开/商业许可或混标F7完成。

/// 核对 HEAD/工作区与界面依赖 → 明确必要模型登记/路由后端是否纳入本次提交 → 仅对选定快照运行门禁并本地提交 → 用已保存配置做分能力真实验证；不推送、不改密钥、不重复生成。

- [x] 预检发现 HEAD 尚无 model-registration/model-capabilities API，前端登记/路由组件及状态 helper 也未跟踪；不可将仅四文件布局提交当作完整可复现版本。
- [x] 用户明确确认纳入模型登记/路由必要前后端依赖，并要求集中验收 F7 大模型；其他 F7/F8 未完成部分继续保留。
- [x] 精确模型依赖快照全量 1656 passed/28 skipped、Web/FE-P1、strict33/33、范围 Ruff/diff，独立依赖复核后本地提交 8c0e3b8；无 push。
- [x] 当前 CPA 三模型实际短聊天、模型发现、七用途消费者解析及 Gemini 结构化 JSON 调用通过；配置 revision3/默认/路由未变。
- 用户于本轮排除MiniMax视频下载闭环，不再要求完成，不勾作PASS。原H3远端成功/DNS拒绝为历史；当前语音与其他复合任务仍需独立验收。

# 模型与 AI 设置页整理 Implementation Plan（2026-10-03）

> 用户已明确确认 apply；使用 executing-plans / openspec-apply-change 在本地 main 成批实现，只整理模型与 AI。

**Goal:** 只整理模型分区，沿用老管理员配置风格，消除重复入口和信息堆叠。

**Architecture:** 复用登记与能力两个现有状态 owner 和版本化接口，三视图局部导航；配置数据不变，其他分区不动。

**Tech Stack:** React、TanStack Query、现有 Tailwind/UI 和 OpenSpec；无新增依赖。

/// 核对新旧设置页面 → 确认以老版管理员布局为基准的融合范围 → 形成标准 OpenSpec → 用户确认后成批实现与前端验收。

- [x] 对照实际 `/settings` 页面与原 `Settings.tsx` 的左侧分区、右侧配置面板。
- [x] 定位重复模型展示、Provider 指引、厂商登记及能力路由纵向堆叠的问题。
- [x] 用户明确“先只整理模型与 AI”；其他五分区与 `/legacy/settings` 原样保留。
- [x] 标准提案已归位 `openspec/changes/organize-model-ai-settings/`：三视图、四项批量任务，细节见 design/tasks。
- [x] 独立规格/计划复核 APPROVED，strict 34/34 和 diff-check PASS；父组件 dirty 汇总建议已采纳。
- [x] 用户明确“确认进入 apply”，本轮实施已授权。
- [x] 一批实现并验证原有草稿/CAS/保存范围/权限与懒加载边界；不更改正式配置、不调用供应商。
- [x] 两轮独立源码复核 APPROVE；桌面/窄屏/局部草稿/离开确认/viewer 只读、85 项既有后端回归、Web/FE-P1 与 strict/diff 门禁通过。原生 Back/Forward 未实际验收，单独记录，不宣称通过。
- [x] 仅同步本 change 的六条新增主规格要求并归档；原有 10 条要求/15 个场景完整保留，归档后 strict 33/33 与 diff-check PASS。保留其他 active change 和 dirty tree，不提交/推送。

# 2026-10-02：设置页旧 API 进程恢复（用户已同意）

/// 精确核对 8000 PID/工作目录/数据库与 5173 前端 → SIGTERM 温和停止旧 API → 等待本机服务自动拉起新版 → 同时核对后端直连与 Vite 代理三条设置接口；不改密钥、业务代码或迁移。

- [x] 仅停止已核对的旧 API PID 67478；5173 前端及 `content_studio.db` 未删除或重置。
- [x] 本机服务自动拉起 API PID 17544；新 OpenAPI 有 312 条路径并包含模型登记和产品设置。额外手动启动因端口已被该新进程占用而退出，未留下第二个 API 进程。
- [x] `/api/v1/settings/product`、`/model-registration`、`/model-capabilities` 经 8000 直连及 5173 前端代理均返回 HTTP 200。用户浏览器可能需刷新以清除旧错误状态。
- [ ] CPA 网关自身的 401 `invalid api key` 与此次本机 404 分开处理，不借页面恢复称远端模型可用。

# 2026-10-02：设置页 Not Found 只读诊断

/// 核对实际前后端监听与页面 URL → 对比浏览器请求路径、运行中 OpenAPI、当前源码 OpenAPI → 确认进程启动时间与源码更新时间；不重启或改配置。

- [x] 当前前端 `localhost:5173/settings` 可访问；后端 `127.0.0.1:8000` 的 `/api/v1/settings/product`、`/model-registration`、`/model-capabilities` 均返回 404。
- [x] 运行中后端 OpenAPI 仅 129 paths、缺模型登记接口；当前源码重新导入 OpenAPI 有 312 paths 且包含模型登记与能力路由接口。
- [x] 后端进程于 2026-09-25 启动且没有 `--reload`，相关新源码为 2026-10-01；前端进程于 2026-10-01 启动。根因是新版前端连旧版驻留后端。
- [x] 用户同意后温和停止旧后端；本机服务自动重启，新接口已读回。保留用户数据/密钥/未知生成任务，不做迁移或重复供应商请求。

# 2026-10-02：CPA 鉴权只读排查

/// 核对当前 API 使用的同一数据库与 CPA 登记 → 对 `/v1/models` 分别发送已保存 Bearer 和无凭据只读请求 → 对照 HTTP 状态及脱敏错误类别 → 追溯配置保存/发送链；不改密钥、不调用聊天或媒体。

- [x] 运行中 API 进程与本次检查均使用 `apps/api/content_studio.db`；CPA 精确地址为可信 LAN `http://192.168.31.37:8317/v1`。
- [x] 已保存密钥非空、`sk-` 前缀、51 字符、可打印 ASCII、无首尾空格；登记保存原值并以 `Authorization: Bearer` 发送。
- [x] 已保存凭据 `GET /v1/models` 返回 HTTP 401，响应分类 `invalid api key`；无凭据相同接口返回 HTTP 401、`missing api key`。网关可达且收到了鉴权字段。
- [ ] 需在 CPA 网关侧核对/更新当前有效的客户端访问密钥，再只读重验 `/models`；不在聊天或仓库暴露密钥。

# 2026-10-02：H3 视频能力与 CPA 配置核验

/// 核对已批准模型路由 OpenSpec 与本机 CLI → 只读额度/dry-run → 单次 5 秒 H3 提交 → 仅查询原任务 → 用产品安全下载器检验字节 → 只读核对 CPA 登记及 `/models`；不重发、不接受素材、不改默认或发布。

- [x] `mmx 1.0.27` 明确支持 MiniMax-H3；5 秒请求 dry-run 正确，额度查询当时显示本周期 3/3 可用。
- [x] 只提交一次 H3，原任务 `448101822222777`，终态 `succeeded` 并有下载地址；未切换 Gemini/Grok。
- [x] 产品安全下载未取得字节：成品 CDN 经当前 VPN DNS 映射到 `198.18.4.255`，被既有禁止非公网地址校验拒绝；不能记为 AIContentStudio 端到端成功。
- [x] CPA 本地已登记三模型，默认 `gemini-3.8-flash-high`；只读 `/models` 仍返回 `provider_authentication_rejected`，真实聊天/媒体未验证。
- [ ] 解决可信 DNS/下载路径并回查同一原任务的 MP4 字节、hash、权利；不重新生成。CPA 鉴权另行修正后再验证聊天。

# 2026-10-02：指定长文经产品适配器重新发送（已获单次外发确认）

/// 核对原HTML/八图/原封面 → 修订既有F7保真HTML契约 → 原HTML与可见内容/精确素材映射校验 → 独立长文授权与产品冻结审批 → 同账号一次草稿创建并保存media_id；不公开发布、不自动重试、不借独立WeWrite冒充产品验收。

- [x] 用户明确同意沿用上次指定长文HTML及封面、同公众号草稿箱重新发送一次。
- [x] 原HTML及八张已确认JPEG副本hash未变，正文47577字节、首图封面名称slide-01-封面与全景.jpg。
- [x] 实际调用产品validate_short_draft_body拒绝official_experiment_body_limit，零网络请求；一般remote_contract_ready仍false，结构化renderer没有原HTML保真入口。
- [x] 完整对照本机WeWrite两份实际源码，确认按原HTML/原文件名multipart/UTF-8 JSON传输；2KB是本地实验限制，不是WeWrite或微信限制。
- [x] 用户“继续做完整”确认上述最小长文修正；只扩精确HTML实验，不全局放开旧短稿或一般远端发布门槛。
- [x] 原HTML/可见blocks/精确素材映射、renderer v3、独立HTML authority及产品CLI已实现；候选实际API保存/检查/冻结/审批/preflight通过，未伪造检查或CapabilityVerification。
- [x] 定向256项、后端1660/28 skipped、前端build/FE-P1、strict33/33、范围Ruff/diff通过；独立复核修正unsafe CSS与真实src定位绕过。
- [x] 唯一外发已执行token/cover后停于首张inline响应；draft/add零次，旧Unknown及claim保留。对照WeWrite发现from=appmsg白名单兼容缺口，已修正并用八个既有真实URL离线验证。
- [x] 新独立私有库经AIContentStudio产品适配器完成9次图片上传和1次draft/add；Attempt=succeeded、有效media_id落库，Target=awaiting_manual_receipt。原失败记录不变；只关闭本次指定HTML草稿箱发送验收。
- [x] 用户“好的”并再次“OK，继续”授权修正后的新单次发送；使用独立新Candidate/Attempt，不复用旧Unknown/claim。

# 2026-10-02：F8 schema readiness 精确校验

/// 读取当前OpenSpec与现有健康/启动代码 → 抽取只读schema-head检查（代码单一head、DB单一head、显式配置三者相等） → 接入生产启动与readiness → 用隔离SQLite正反例和既有健康回归验证 → 更新F8进度。F7其余门禁仍单独处理。

- [x] 实现代码/数据库/配置三者精确单头校验，拒绝多头、缺表、陈旧配置及异常。
- [x] 生产启动和readiness共用校验，不执行迁移。
- [x] 隔离SQLite现行/陈旧/多头/空头检查、已有健康回归3项、OpenSpec strict 33/33、范围Ruff及diff-check通过；F8 5.3已勾选。

# 2026-10-02：F8 下一批——存储完整性、健康状态与安全边界

/// 从main@931915d及保留的F8工作区继续 → 先完成旧素材读写provider兼容桥/不可变文件/真实存储readiness → 隔离存储和健康回归 → 身份issuer/subject草案独立复核，等待schema批准 → 关闭有直接证据的F8任务；不联网生成、不公开发布、不迁移正式库、不推送或归档F8。

- [ ] 完成旧AssetMedia/Article Handoff字节provider桥，保留历史相对路径与hash校验；并发重复写不覆盖旧字节。
- [ ] 补存储连通性和可选provider零副作用readiness，保持安全错误分类。
- [ ] 复核retention不会删除已绑定历史血缘，相关失败日志不暴露路径或secret。
- [ ] 运行既有相关回归/隔离集成、范围Ruff、strict和diff；逐项记录实现与外部验证差异。
- [ ] 身份草案只读安全复核并等待用户明确批准绑定列；不先启用或迁移正式库。

# 2026-10-02：公众号补充变更最终收尾

用户选择必须保留原文件名：先补既有规范内的 renderer v2 槽冻结/安全名称验证/逐步live核对和multipart透传；不改旧manifest、不新增迁移、不外发。现有全量1660/28 skipped、原生PG22项已通过，但不充当随后文件名补丁的最终门禁。

/// 用户接受2.8及取消成功草稿回读 → 私有SQLite/原生PG、全后端、Web/FE-P1和隔离UI门禁 → 独立安全/交付复核 → 同步新增account-bound-wechat-draft-publisher主规格 → 归档补充变更 → 审查提交范围并本地提交；不推送、部署、迁移正式库或再发草稿。

- [x] 用户明确将公众号一般合同/指定真实账号验收视为通过；成功草稿回读为用户豁免，不冒充已执行或自动创建CapabilityVerification。
- [x] 新鲜全量/迁移/UI/规格/范围lint/diff门禁及独立复核通过，实际结果见公众号验收文档。
- [x] 已同步唯一新增主规格并归档，保留F7/F8及其他active changes，不关闭运行时一般合同安全门槛。
- [x] 已完成本地提交范围审查；本次提交保存公众号代码/规格/证据，无关MiniMax/F8改动继续留在工作区。

# 2026-10-02：AIContentStudio 产品草稿回读预检

/// 只读核对 Candidate6 / Account1 / Target6 / Attempt6 → 检查现有产品回读入口及原授权 → 保留成功/Unknown 历史 → 报告入口缺口；不重新上传、创建、公开发表或借 WeWrite 替代产品验证。

- [x] 确认产品 Attempt6 为 succeeded，Target6 为 awaiting_manual_receipt，已保存精确 remote_id；readback_hash 为空。
- [x] 确认原实验授权已过期；现有 official-readback 只接受 unknown / reconciliation_needed，不接受成功草稿。
- [x] 记录零网络预检结果；没有调用微信接口、修改验收数据库或新建交付。
- 已取消：用户明确确认成功草稿不需要回读，本次实验以有效 media_id 落库及后台人工确认结束；不开发新回读入口、不续签或再发送。此项不是回读测试通过。

# 2026-10-02：MiniMax 真实能力单次验收（已授权）

/// 私有副本 + 新临时 receipt key → 一次 image → 一次 TTS → result_ready 与字节哈希回读；不重试旧 Unknown、不接受素材、不写正式素材库、不调用 video/ASR。

- [x] 私有数据库副本 `/private/tmp/aics-minimax-fresh-pL9PPT` 与 0700/0600 权限的结果目录已建立；新任务使用独立临时 receipt key。
- [x] MiniMax `image-01` 新任务 `cc6f9c535ac94ab296916aff9b990d8f` 单次真实执行成功，`result_ready/rev3`，JPEG 33997 bytes，SHA256 `1e18a7be540f091ac7d71510a3aebe68a24ca57413f99b2e00667857c0db7298`；未接受为 MaterialRevision。
- [x] MiniMax `speech-2.8-hd` 新任务 `90a0d78b4fbd4d0e97bafbc922a5e25d` 单次真实执行成功，`result_ready/rev3`，WAV 180980 bytes，SHA256 `5e6c663fb225d07c8db2b0609294966b3a452e791160ef351443c05a39cbcb7b`；未接受为 MaterialRevision。
- [ ] 跨进程 HMAC receipt 验签未完成：临时 key 仅存在于本次命令环境，未持久化；为避免再次消耗额度，不重跑供应商。新进程仅完成 DB/文件存在性与 SHA256 一致性核对。

## 2026-10-02：F8 第一批——生产等价素材生命周期

/// 以现有 F8 storage contract 为规范：统一 MaterialRevision 字节读写边界 → 开发/生产分别使用持久化存储 → 生成结果仍先进入私有任务区，人工确认后晋级正式素材库并绑定项目；不运行正式迁移、不切生产配置、不提交推送。

- [x] 统一已覆盖的 MaterialRevision、Candidate、Review、Delivery、Project 输出 provider 读取路径，并保留明确的 legacy DraftMedia 兼容桥；绑定 revision 的读取失败不再回退旧本地路径。
- [x] 补齐 Local/MinIO provider 的 immutable key、hash 校验、未引用字节诊断和安全路径边界；管理员诊断接口不暴露路径/对象 key。MinIO 真实连接/切换仍待后续批次。
- [x] 增加显式 readiness/live 边界：`/api/v1/health/ready` 返回真实 HTTP 失败，旧 `/api/v1/health` 保持兼容；生产 `/metrics` 需要管理员，开发测试不破坏既有本地门禁。
- [x] 队列开启时 readiness 才检查 Celery broker，失败返回安全 `queue_unavailable`；同步开发模式不发起队列网络探针。
- [ ] 明确开发环境使用独立持久化 DB/媒体根，生产环境必须显式配置对象存储和 schema head；禁止把 `/private/tmp` 作为产品默认路径。
- [ ] 验证生成任务 `result_ready → 人工确认 → MaterialRevision → ProjectMaterialReference` 的持久化闭环；拒绝自动把未确认结果当正式素材。
- [ ] 运行现有相关回归、diff-check 和 OpenSpec strict；未覆盖的 F8 任务继续保留，不提前宣称 F8 完成。

# Codex with ChatGPT 连接配置计划

## 2026-10-02：指定 HTML 长文单次草稿测试（精确授权）

/// 原 HTML/hash 和八图预检 → 私有 JPEG 副本及 HTML 预览 → 同账号一次上传/创建 → 原 media_id 回读正文/图片/样式 → 记录结果，不自动重发。

- [x] 用户批准测试标题“决定 AI 量化成败的四根数据支柱”、首图封面、仅压缩图片副本、沿用原 HTML；只进入同一公众号草稿箱。
- [x] 八图 JPEG90 副本均小于 1 MB，尺寸仍为3840×2160；原 PNG/HTML不改。
- [x] 本地预览、一次 WeWrite 原 HTML API 创建及同草稿回读。标题/正文/216个style一致，8图资源顺序一致；初次本地解析缺src后仅只读重取同一草稿，未再次上传/create。属于指定文件独立测试，不冒充产品 Candidate/Delivery 验收，不解除产品一般合同 gate。
- [x] 安全证据与进度记录已同步；不公开发布、重试旧 Unknown、改正式库/配置、提交或归档。


## 2026-10-02：公众号验收统一记录 → MiniMax 原任务核验

本批沿用已授权 F7 / 公众号 / 模型路由 change，不重发草稿、重试 Unknown、公开发布、改正式库/配置、提交或归档。不要以短稿成功取消一般合同要求。

/// 回读原公众号证据库并核对历史 → 现有定向/全量/构建与独立逐任务复核 → 统一当前验收记录 → 回读原 MiniMax 任务/字节/验签配置 → 在明确额度与权利范围内继续真实媒体验收。

- [x] 只读确认 Attempt6 succeeded、精确 remote_id、Target awaiting_manual_receipt；旧五条 Attempt 全字段不变，Receipt/Published/Verification 都为0。
- [x] 最新129项公众号定向、1660全后端/28 skipped、Web构建/FE-P1、strict33/33、范围Ruff通过；独立逐任务复核批准8.5，其他一般验证任务保留。
- [x] 原MiniMax语音126738字节/hash/解码时长一致；图片仍Unknown/rev3且无原job，没有重发或接受素材。
- [ ] 完整公众号范围：一般长文合同及exact verified scope尚未通过；终验提交、主规格同步/归档未授权完成。原文件名透传差异需明确处理，不声称已保留原文件名。
- [ ] MiniMax真实闭环：恢复原验签key配置后方可验签/接受原语音；真实图片、视频原任务查询/下载、ASR与权限接受仍待完成，新增付费请求需明确额度。


## 2026-10-02：用户确认草稿后台可见性

- [x] 核对用户截图标题及封面与Candidate6测试稿一致，记录人工草稿箱验收PASS。
- [x] 保留一般合同/阶段终验/归档待办；不调用微信、不新增Receipt/Verification或发布动作。

## 2026-10-02：响应兼容修正后的新草稿测试（单次授权）

/// 备份隔离库并保留五条旧Unknown → 新测试稿经产品API冻结审批 → 本地预览/零网络preflight → 单次执行 → 回读安全证据并核对历史；不重试、不公开发布。

- [x] 用户明确授权一次新草稿箱测试，沿用先前批准账号和精确封面；私有目录已建立。
- [x] 新Unit6/Master7/Variant7/Candidate6经产品API冻结审批，118字节HTML和19723字节封面验证；零网络preflight/rollback及五条旧Attempt全字段核对通过。
- [x] 唯一一次执行：用户补齐精确正文/封面/账号授权后按原runner执行一次，Target6/Attempt6 succeeded，token/asset_0/create完成并持久化有效media_id。此前审批拒绝是历史，未绕过；无公开发布/第二次创建或远端回读。
- [x] 五条旧Attempt全字段不变，源库5条/副本6条，Receipt/PublishedContentRecord均0；关闭2.8a、公众号19/22，整体F7和一般合同不宣称完成。

用户随后明确批准所列正文/封面发往该公众号草稿箱一次；冻结输入/封面hash/五条历史再次核对一致，零网络preflight通过。现在仅执行既有runner一次，不新增或重试别的稿件。

## 2026-10-02：授权修正公众号响应兼容（本地）

/// 先补现有OpenSpec接受契约 → 无网络复现 → 最小修改MIME白名单 → 严格响应/既有回归验证 → 独立窄复核与记录；不继续F8，不追加真实请求或重试旧Unknown。

- [x] 用户已授权现有task2.1a的text/plain严格JSON兼容；先更新design/spec/tasks与既有实施计划。
- [x] 最小修改transport MIME白名单；无网络RED→GREEN、129定向、1660全后端/28 skipped、strict33/Ruff/diff通过。
- [x] 独立响应兼容窄复核APPROVE；本地补丁完成，保留2.8/2.8a/2.9/2.10未完成，无新微信请求或旧Unknown变更。

## 2026-10-02：F8身份/schema草案独立前置复核（只读）

/// 核对F7/F8真实任务边界 → 独立审阅既有身份草案 → 仅内存合成数据复现疑点 → 记录最小修订要求；不实施F8、不改业务代码、不运行正式迁移/认证，不调用供应商。

- [x] F8 0.1/0.7仍未关闭；保留公众号MIME修订与新调用需确认边界。
- [x] 内存探针确认f8a只按唯一约束名识别：同名UNIQUE(email)被误认，允许重复issuer/subject；嵌套JWT探针当前正确401，不报假缺陷。
- [ ] 收集独立只读review并同步基线审计/规格准备记录，不把review当成schema授权或生产就绪。

## 2026-10-02：新增诊断草稿测试（已授权一次）

/// 保留四条旧Unknown的私有库副本 → 同账号/精确封面和新测试稿API审批 → 零网络预检 → 产品execute一次 → 脱敏诊断只读/旧记录全字段比较 → 记录；不公开发布、不重试、不开一般合同。

- [x] 准备并预检新的批准Candidate 5（Unit 5/Master 6/Variant 6），118字节，原封面19723字节；rollback后仍四条旧Attempt、无新Target。
- [x] 单次远端执行和诊断回读：Attempt5 token成功，asset_0 HTTP200/text/plain被产品MIME门槛拒绝；无draft/add/media_id，保留Unknown，不重试。
- [x] 同步实际失败和WeWrite只读对照结果；旧四条全字段未变，无业务代码/正式库写入。

## 2026-10-02：上传脱敏诊断（仅本地已授权）

/// 更新既有规格和计划 → 无网络复现缺少分类 → 传输层添加固定分类 → Attempt再过滤 → 既有回归和独立窄复核 → 更新记录；不调用微信、不重试、不改历史。

- [x] 确认授权仅本地诊断，修订既有2.4契约。
- [x] 分类实现及脱敏探针：16拒绝分支、缺media_id、严格字段过滤和真实_finish路径（合成DB），未访问账号/凭据/接口。
- [x] 定向129、全后端1660/28 skipped、strict33/33、Ruff/diff及独立诊断窄复核APPROVE；记录同步，不关闭真实平台/全阶段/归档任务。

## 2026-10-02：token endpoint 修正后单次真实验收（用户已授权）

/// 私有副本保留旧三条 Unknown → 新 Unit/Master/Variant/checks/Candidate/Approval → 同一账号/封面/短 HTML 零网络预检 → 产品适配器执行一次 → 只读核对安全 Attempt/media_id；不公开发布、不重试、不迁移正式库。

- [x] 完成新测试稿及私有进程身份 key 配置，冻结预览和账号范围已通过零网络预检。
- [x] 仅一次真实执行：token 成功，封面 asset_0 响应未确认；Attempt 4 unknown，无 draft/add/media_id，不重发。
- [x] 同步验收文档和实际进度；失败不关闭 2.8a，公众号保持 18/22。

## 2026-10-02：WeWrite HTTP 协议移植（apply 后纠正）

/// 对照已批准 GET /cgi-bin/token 契约 → 纠正既有断言并离线复现 endpoint/dispatch 两处遗漏 → 最小传输补丁 → 110 定向/全后端及 strict/Ruff/diff → 更新真实 Attempt 证据；本轮不发起真实请求，不重试旧 Unknown。

- [x] endpoint 已从遗留 stable_token 改为 token；接口拒绝的发送提示按实际请求保留，不回填历史诊断。
- [x] 既有断言先复现 2 failed / 6 passed，修正后 110 项定向通过；没有新增测试文件。
- [x] 全后端 1660 passed / 28 skipped / 8 existing warnings（81.27秒）、Ruff/change strict/diff 及独立窄复核通过；未重跑前端、不改正式库。
- [ ] 真实产品草稿创建仍未成功；最新 Attempt 3 停在 token，不用本地门禁关闭 2.8/2.8a。

/// 以下为前一批规格、授权和移植步骤；最新纠正与真实结果以上述记录为准。

- [x] 对比 WeWrite 的 token、multipart、draft/add、media_id 判定与 AIContentStudio 当前实现。
- [x] 在现有公众号变更中补充 WeWrite wire parity 契约与实施计划。
- [x] 用户确认后 apply：仅移植 HTTP 行为，不移植全局凭据/CLI fallback/公开发布；传输层已完成并通过定向回归。
- [ ] 定向回归与（如再次授权）一次草稿箱-only 产品联调。

## 2026-10-02：公众号新测试稿真实产品联调

/// 用户明确授权新建一篇“请勿发布”测试稿 → 私有副本创建新Unit/Master/Variant/Candidate/Target → WeWrite式短稿预检 → 仅一次真实产品发送 → 读取安全Attempt结果；旧Unknown不动、不自动重试、不公开发布。

- [x] 在隔离数据库副本完成新测试内容的真实产品链路：Master检查、Variant检查、Candidate批准、账号绑定和短稿字节门禁。
- [x] 真实调用一次公众号产品适配器；token完成，素材上传未获确认，Attempt进入unknown/Target进入reconciliation_needed，系统未重试。
- [ ] 需要人工按远端实际状态对这次新Attempt进行核对；2.8尚不能标记完成，2.9/2.10未执行。

## 2026-10-02：批准Workflow持久生成接入apply

/// 用户确认design5.3 → 新media.generate节点与静态配置校验（旧cover不动） → 发送前真实started Attempt/内部task关联 → 原任务等待/查询与独立接受 → accepted后追加终态/ProjectWorkflowOutput → Inspector入口与禁止通用重跑 → 瞬时隔离探针及既有回归/build/strict/diff；不新增测试文件/迁移/供应商任务。

- [x] Backend：服务端关联、immutable started/terminal、等待与原任务恢复、归档权限和通用重跑拒绝；合成隔离链路已验证。
- [x] Frontend：新节点配置及原任务预览/独立接受/续进，旧节点行为保持；构建已验证。
- [x] 本批验证、进度与README；真实供应商/付费媒体验收仍不计入本批通过。

## 2026-10-02：MiniMax CLI 能力库存核验

/// 受控读取本机 `mmx` 版本与固定配置 → 注册 image/video/tts/asr 四类 provider → image dry-run → 记录不可逆 credential continuity；不生成、不扣费、不接受素材、不触碰公众号未知 Attempt。

- [x] `mmx 1.0.27`、四类固定 Provider 注册、credential epoch、`image-01` dry-run 已核验。
- [x] 更新 OpenSpec task 2.4、progress/findings/README/能力矩阵；strict33/33、Ruff、diff-check 已复核。
- [ ] 真实输出字节、媒体权利/许可、原视频任务恢复、公众号产品草稿箱回读和最终独立复核仍待完成。

## 2026-10-02：Workflow闭环定位与并发发送验收

/// 核对真实Workflow cover/Attempt生命周期与持久任务入口 → 私有副本双线程真实execute竞争（本地stub，不调用供应商） → 发送后保存前崩溃/原任务恢复禁止重发 → 记录Workflow未闭合与剩余门槛；许可待定、不执行真实接受或F8。

- [x] 定位旧cover链路及Attempt仅终态创建事实，独立任务prepare未绑定workflow_step_attempt_id；不能把独立预览当Workflow闭环。
- [x] 双线程真实execute竞争仅一次本地stub发送；两种子进程实际exit73后claim仍持久、等待期阻断、夹具lease过期后unknown且不重发。
- [x] 同步实施缺口和实际证据，不过勾任务；design5.3为待确认细化，不修改业务代码或既有Attempt契约。

## 2026-10-02：已有任务表外键保护

/// 内存SQLite复现缺少四个外键仍被迁移接受 → 既有f7d补精确外键目标校验 → 正常已有表与缺失/错目标负向探针 → 既有迁移回归/strict/diff → 同步记录；不新增测试文件、不运行正式迁移。

- [x] 修复已有任务表外键缺失/错误目标被静默接受。
- [x] 正常重复upgrade/down/up、缺失及错目标拒绝通过；既有迁移回归5 passed、Ruff/strict33/33/diff通过，不关闭F7整体任务。

## 2026-10-01：Video ASR本地输入闭合续批

/// 已批准MiniMax/ASR能力契约 → 核对Video Studio精确MP4/WAV来源及既有显式建议保存 → 在minimax_cli_provider.py受控临时目录从真实MP4提取首音轨到16kHz/mono PCM WAV（不裁剪补造） → 真实帧时长/500秒及请求限额/30MiB/总deadline检查 → 保持原来源hash与建议接受/CAS路径 → 既有回归/独立窄复核 → README/progress/findings；无新测试/真实转录/生产迁移/默认改变。

- [x] MiniMax ASR输入接口接受精确MP4或WAV，在发CLI前完成实际解码、时长与受限音频准备，缺音轨/工具/超限安全拒绝；真实转录未验收。
- [x] 最终既有全量1661/28、93定向及Ruff/strict33/diff、独立限定源码复核通过；不把fixture当真实账号验收。
- [x] 同步设计实现细节与进度，3.2/3.3/Batch B未满足全部要求不勾。

## 2026-10-01：MiniMax原任务协议续批

/// 已批准11/25基线 → 本机官方CLI源码/帮助锁定taskId与V1/V2 query/下载真实形状 → 固定H3 async submit+原job单次query → 复用pinned_transport有界无凭据下载而非CLI默认5GiB/重试下载 → 既有回归/独立复核 → 文档记录未完成认证/V1下载/Workflow；不调用供应商，不新测试或生产迁移。

- [x] 固定H3首次提交及V1/V2原任务查询接口，严格字段/状态/ID/model/protocol检查；真实执行仍blocked。
- [x] H3安全URL下载：TLS/DNS固定、无环境代理、无认证header、同源redirect、30MiB/spawn父进程绝对deadline，URL不持久化；尚无真实下载验收。
- [x] 运行身份缺证明仍blocked；修订后既有1661/28、Ruff/strict33/diff及限定源码复审APPROVE，任务3.2不提前完成。

## 2026-10-01：持久任务结果闭合续批

/// 核对当前11/25和授权规格 → 复用真实视频decode补时长上限（不信供应商metadata） → 任务私有文件0600/目录0700与原子无覆盖落盘 → 现有媒体/存储回归和范围Ruff → 独立只读复核 → 同步记录；不生成测试代码/真实调用/生产迁移/F8启用。

- [x] generation_tasks：视频实际时长证明及每次授权上限，安全冻结路由/限额投影。
- [x] material_storage：仅generation命名空间私有原子写入及新目录父项fsync，旧素材语义保持。
- [x] ProviderMediaPanel：模型/能力/限额选择→prepared→独立确认execute，原prepared回读；同输入保留幂等键，unknown不通过清键重发。
- [x] 现有全量1661 passed/28 skipped、TS/Vite/预算、Ruff/strict33/diff与限定独立复核通过；未覆盖新状态机/浏览器/真实Provider仍明示，3.2/3.3不提前勾选。

## 2026-10-01：持久生成任务 apply（进行中）

/// 用户确认修订稿/进入apply → 单任务表及独立F7加法迁移（不依赖未授权F8） → 签名/owner/idempotency/CAS与一次发送 → 原job恢复及私有结果 → 既有媒体原子接受/API → 既有回归/隔离迁移/独立代码复核 → 记录未完成UI/真实验证。

- [x] 修订稿独立APPROVE后收到明确apply授权；在本地main保留既有dirty tree。
- [x] 实现3.1单表/约束及部分Batch I/II：签名、CAS claim、原job查询框架、私有结果、原子接受/API和前端任务回读；完整provider/Workflow接入保持未完成。
- [x] 现有全量1661 passed/28 skipped；构建/预算、strict33/33、Ruff/diff、隔离SQLite up/down/up和独立底座复核通过。不新增测试代码、不消耗额度/迁移生产库/变更默认。
- [ ] 继续3.2/3.3：安全CLI身份连续性、真实submit/query接口、视频时长证明、Workflow/ASR及前端创建/执行。3.4针对新状态机的完整验收未覆盖，不以既有回归替代。

## 2026-10-01：持久生成任务修订计划

**Goal:** 本地正式使用环境中，一次提交的MiniMax生成任务可在重启后沿原job恢复并人工入库。
**Architecture:** 一个ProviderGenerationTask记录运行状态；沿用Registry、provider_media、MaterialRevision和真实Workflow Attempt。
**Tech Stack:** 既有SQLAlchemy/Alembic/FastAPI/React及固定mmx命令，无新外部依赖。

/// 修订proposal/design/spec/tasks → strict/diff与独立计划复核 → 用户确认修订稿 → Batch I模型/迁移/claim/原job恢复/字节存储 → Batch II消费者/UI/原子接受/隔离验收。

- [x] 同步一个任务表、幂等/claim/CAS、unknown不重发、私有结果和人工接受范围。
- [x] 独立复核修订稿并记录本轮实际门禁：初审两项修订后复审APPROVE，strict33/33与diff通过。
- [ ] 用户确认修订稿后实施Batch I/II；不生成新测试代码，不消耗额度，不迁移本地生产库或改默认。

相关文件：apps/api/app/models.py、apps/api/alembic/versions、services/provider_calls.py、provider_media.py、minimax_cli_provider.py、routers/materials.py及既有生产素材面板。迁移仅隔离库验证；如需要额外durable对象，回规格确认。

## 2026-10-01：供应商协议整批核查（无业务apply）

/// 官方MiniMax全球H3 create/query → 区分V1 file与V2 URL → Google Interactions REST与SDK区分/Omni与Veo两协议 → xAI image/video输出与状态 → 对照现有adapter注册 → 文档映射/范围验证。

- [x] 取得H3官方全球create/query协议，确认原task/URL/查询窗口及按量API要求；不推断账号权限或地区endpoint。
- [x] 取得Google REST steps输出、Omni/Veo协议分派和xAI图片base64/视频状态；纠正文档中xAI video“已注册”暗示。
- [ ] license/版本计价、完整操作覆盖、运行身份/消费者/持久任务范围确认及真实验收；task2.1/2.4–2.6保持未完成。

## 2026-10-01：MiniMax视频原任务恢复审计

/// 核对固定generate --async/task get/download命令 → 跟踪provider_calls/provider_media实际状态保存 → 检查WorkflowStepAttempt复用边界 → 记录持久化规格缺口 → 等待修订范围确认；不提交视频任务、不新增业务表/迁移。

- [x] CLI help确认异步提交、按原task查询和按file下载；H3查询必须传模型，不能走默认legacy query。
- [x] 实际源码确认provider_calls仅线程池，provider_media仅成功结果内存缓存，未知结果无原任务保存/恢复入口；独立素材入口不要求WorkflowRun。
- [ ] 取得持久任务契约修订确认后，先修订OpenSpec，再实施原任务恢复/配置与runtime绑定/下载及显式接受整批；不能把进程内缓存当本地生产恢复完成。

## 2026-10-01：MiniMax官方协议差异收口

/// 对照官方TTS/ASR及视频查询/下载协议 → 精确TTS型号与小于10000字符 → ASR实际WAV与声明上限均不超过500秒 → 既有回归/Ruff/strict/diff → 文档证据；不新增测试代码，不改默认路由，不调用付费生成。

- [x] 官方TTS/ASR、旧视频查询/下载契约已读取；H3创建协议读取失败，不猜测字段。
- [x] 修正CLI发送前模型/文本/时长限制；既有相关回归93 passed/1 warning、范围Ruff/语法检查、strict33/33、diff-check通过。未新增测试代码，既有回归不证明新增CLI边界或真实供应商验收已覆盖。
- [ ] 完整供应商协议、认证版本、视频原任务恢复与真实生成验收；聚合任务2.1/2.4不提前关闭。

## 2026-10-01：F8 第一批生产身份与启动安全（apply 中）

/// MiniMax图片精确模型续批：只读dry-run确认当前request.model=image-01 → 解析白名单model而非原始request/headers → binding/dispatch核对同一实际型号 → image runtime固定model → 零网络探针/既有回归；认证版本和完整路由仍不计完成。

- [x] /// 已安装CLI的dry-run型号证据与model/runtime精确校验；缺失/不匹配/null零网络拒绝探针和范围Ruff通过。
- [ ] /// 认证版本/实际生成/完整能力路由与浏览器验收；不能用本地dry-run替代。

/// MiniMax参数续批：复现Video/TTS忽略source refs且把任意model传CLI → 未实现输入模式发送前拒绝 → supported text-to-video型号/显式模型argv收口 → 零网络探针/既有回归/文档；真实reference-to-video仍待后续完整接通。

- [x] /// 参考输入/未知model发送前拒绝，显式默认参数；8类输入+3类binding零网络探针、93项现有定向回归、Ruff/strict/diff通过。
- [ ] /// 接通真实参考素材Video、原task恢复、精确image型号选择和配置→实际能力路由，不缩减最终设计范围。

/// MiniMax ASR续批：官方SRT协议/既有_output契约核对 → 固定asr-1.0/srt/sentence argv → 严格SRT转transcript+cues → 无网络探针/既有回归 → 文档。真实生成/额度/默认路由及F8方案不在此批。

- [x] /// 严格SRT转换与既有ASR_output组合探针通过，6类非法字幕拒绝；范围Ruff/变更strict/diff通过，未发供应商请求。
- [ ] /// 完整MiniMax语音/视频输入、运行身份、真实配置与浏览器链路验收，不以转换器替代整体接通。

本轮先完成既有批准的 MiniMax 输出边界，不推进待确认的 F8 身份 schema。

- [x] /// 复现 capture_output 超过512 KiB仍返回结果；仅调用本机解释器，零供应商请求。
- [x] /// 有界pipe读取/单一deadline替代capture；超限/超时结束本次进程组，返回不确定且不重发。
- [x] /// 限制临时媒体读取；正常/超限/超时探针、93项现有回归、strict/Ruff/diff通过，Batch B仍不计完成。
- [x] /// 关闭CLI未实现chat/未知能力的假可执行状态；先复现再修复，重新跑93项现有回归及strict/Ruff/diff通过。

状态纠正：上一批提前勾选的身份设计/实施任务已撤销完成标记。User 字段迁移与 HS256 是待授权、待独立复核草稿；/// 本批只修复草稿 JWT 输入验证、未知路径指标泄漏与存储开关兼容，随后复跑本地门禁。F7/F8 未完成，不执行默认数据库迁移。

/// F8 Batch 1：规格补齐 → User issuer/subject 映射 → HS256 production auth → production startup fail-closed → truthful readiness/metrics → Settings auth-mode projection → 回归门禁

- [x] /// 读取当前 main/F7/F8 状态，确认 F7 外部真实验证仍未关闭，不伪造进入 F8 完成态。
- [ ] /// 现有 User issuer+subject 与加法迁移仅为草案，取得单独方案确认后再验收，不升级生产库。
- [ ] /// production JWT 草案需独立确认、完整安全复核及真实本地生产登录验收，未完成。
- [ ] /// health/readiness/schema/auth/storage 尚缺完整依赖与实际存储验收；未知路由指标已修，不提前关闭整体任务。
- [ ] /// 完成本批独立安全复核、完整门禁和 F8 后续 Secrets/Storage/Recovery/Golden/Runbook 批次。

## 2026-10-01：CPA 厂商登记与功能模型选择（apply 中）

**Goal:** 厂商 API/Key → 获取/登记模型 → Gemini 默认 → 各业务环节选择，复用已有配置。
**Architecture:** SystemSetting/CAS 增量、写入型密钥、精确 LAN endpoint 白名单；独立提案 add-provider-model-registration，不覆盖 add-model-capability-routing。
**Tech Stack:** 现有 FastAPI/SQLAlchemy/React/OpenSpec；无新表/迁移。

- [x] /// 核对当前源码与用户默认选择，制定两批计划及增量规格，不回显实际密钥。
- [x] /// 新变更 strict 与 artifact status 校验。
- [x] /// 用户确认方案并实施 Batch A（登记/发现/持久化/UI）；密钥不回显。
- [ ] /// Batch B（真实功能消费者选择/兼容/验收）；未授权不生成测试代码/付费请求，不提交/推送/部署。

当前实况：登记配置可回读，CPA `/models` 返回 401，不能视为发现或模型可执行已通过；工作流异步选择和 route provenance 正在收口。

/// Batch B 当前推进：Google/xAI 精确 native adapter contract 与 MiniMax unavailable descriptor → Registry bootstrap → 文档/安全边界；尚未接 provider_calls/provider_media 实际 dispatch

模型能力路由 Batch A 已完成：CAS、能力声明/绑定、统一 resolver、限额/自动 fallback 授权、冻结计划、Workflow/Production 规划消费者和 Settings 编辑均已实现。定向回归 106 passed，前端构建/FE-P1、Ruff、strict、diff-check 通过；真实供应商媒体适配和付费执行仍未验证。

- [x] /// 增加 Google/xAI 版本化 native adapter 的无网络 capability/request contract，并将 MiniMax 保持为显式 unavailable；不读取或写入凭据，不发供应商请求。
- [ ] /// 接入既有 provider_calls/provider_media 的真实 dispatch、bytes/rights/acceptance、视频轮询和 TTS/ASR；需完成官方契约核对后再实现。

## 2026-10-01：模型能力路由 apply（当前）

用户“开始执行”已授权 add-model-capability-routing。直接 main 开发，保留原 F7 脏工作树，不提交/推送/部署/生产迁移，不重试微信 Unknown，Commons 暂缓。

/// Batch A：版本化声明与绑定 → CAS/安全投影 → 插件/预算编辑 → 共享计划与消费者 → 局部复核
/// Batch B：官方协议核验 → 原生供应商适配 → 受控执行/素材接受 → 浏览器与真实验收分离

/// MiniMax local CLI batch：已读取 `mmx --help`/version，仅确认固定命令族；已补本地 `mmx` Registry adapter 规格与实现入口，默认需 `AICS_ENABLE_MINIMAX_CLI=1`，不读取 CLI 配置、不执行真实生成；下一步是现有 provider_media/provider_calls 的定向回归与本地配置页/路由验收。

/// 当前增量：Registry binding_state 只读协议 → 显式/默认/ordered plugin resolver → canonical frozen plan → dispatch 前复验 → viewer 安全只读配置

Files: apps/api/app/services/model_capability_routing.py；apps/api/app/routers/settings.py；apps/web/src/product/ModelRoutingSettings.tsx；ProductSettingsPage.tsx；tests/test_model_capability_routing.py。
验证：在 apps/api 内 `.venv/bin/python -m pytest tests/test_model_capability_routing.py tests/test_settings.py tests/test_product_settings.py -q`；web `npm run build`；全后端私有临时库；strict/diff；独立只读复核。测试使用 isolated Registry fixture，不声明真实供应商已验证；没有网络调用。

- [x] Apply 授权、范围核对和原配置保留。
- [x] 首个配置切片：能力/绑定、CAS、无网络预览、Settings lazy 入口及定向回归。
- [x] 共享resolver/frozen signed plan核心与viewer安全读取，独立定向修复闭合；1661全量后端通过。尚未消费者dispatch/真实nativeadapter，不将此项当整个task1.7完成。
- [ ] Batch A 完整关闭；当前供应商状态均 unavailable，不能视为可执行。
- [ ] Batch B 与真实付费验收（单独授权额度），不得提前勾选。

独立复核发现的并发旧写入、编码 URL/存量元数据回显、保存中编辑丢失已补修并窄复核闭合；新增插件/预算 UI 的空路由及在途 GET 问题也已闭合。OpenSpec 20 项为聚合任务，不把配置切片冒充整批；接下来先完成共享 resolver/计划冻结与真实浏览器配置验收，再进入供应商适配。

## 2026-10-01：模型能力与插件路由新规格

**Goal:** 将用户要求的模型适配、手动能力标注、插件配置和自动路由归入标准OpenSpec，而非继续要求用户预先接好接口。
**Architecture:** SystemSetting版本化配置+Registry真实支持+共享resolver；自动fallback原则已确认，仅预授权硬上限。两批执行；真实付费测试与生产操作不从规格授权推断。
**Tech Stack:** existing Settings/Provider/Workflow/MaterialRevision；本轮只有规格。

- [x] /// 核对ModelProfile、文本路由、image与typed media入口；手动声明/配置/验证分离。
- [x] /// 新change add-model-capability-routing：proposal/design/two deltas/tasks/README，20项按两批组织，无业务apply。
- [x] /// 新change strict与全量32/32、diff通过；无业务apply。
- [ ] /// 独立规格review，用户明确确认apply后实施；不得将新方向当原F7/F8已完成。

## 2026-10-01：后续验收身份范围校正

**Goal:** 不把默认开发管理员路径误认成显式身份隔离；保持F8按顺序执行门槛。
**Architecture:** 只读deps与F8 tasks/design；纠正过程记录，不改历史业务数据、不重跑Commons。
**Tech Stack:** source review / acceptance records。

- [x] /// 核对真实X-Studio-User与默认用户分支，纠正Commons探针header范围。
- [x] /// 复核F8 0.1/0.7与现有User映射约束；不自动绕过F7或新增持久身份表。
- [ ] /// 等待生成接口配置位置与微信人工对账；若启动条件需调整，先明确修订规格并确认。

## 2026-10-01：Commons暂缓与生成素材接入前置

**Goal:** 按用户最新决定暂停Commons网络/导入验收，保留未验证状态；优先确认现有模型生成接口，不以聊天能力名称代替API能力。
**Architecture:** Commons保留可选来源；生成封面/插画/示意视频/配音与真实截图/新闻照片/事实证据分流。复用既有MaterialRevision与Provider契约，不删除历史或绕过rights/byte gates。
**Tech Stack:** existing capability matrix / provider contracts；本批只记录范围。

- [x] /// 记录Commons用户暂缓，不再发Commons请求、不将10.2勾成通过。
- [x] /// 核对既有注册与配置代码：SystemSetting image/models/plugins真源、OpenAI图片实现、Video/TTS/ASR协议无真实注册；保留统一provider_media接入点，不读取密钥。
- [ ] /// 确认Gemini/Grok/MiniMax生成API或插件配置位置及非敏感接口契约，先核对、不发送付费请求。
- [ ] /// 根据实际接口提出有界Provider规格调整，用户确认后实施；微信Unknown仍禁止重试。

## 2026-10-01：网络恢复后的真实Commons导入续验

**Goal:** 完成F7 10.2真实搜索→stage→raw→accept→磁盘哈希回读，不修改业务代码或rights gate。
**Architecture:** 全新私有临时库/素材目录，正常seed/bootstrap/header身份、未替换transport。搜索CC0候选，许可/证据/归属精确匹配，public/model/commercial均false；重复同decision只验证幂等。不动微信对账库或生产。
**Tech Stack:** existing product API / Commons adapter / MaterialRevision。

- [x] /// 真实Commons搜索曾返回200/7个候选；stage返回502/search_download_failed。随后复测搜索502，DNS确认API域名再次返回198.18.0.15；不以夹具/代理override替代。
- [ ] /// 下载预览并显式导入，核对MIME/精确SHA256/来源/rights与幂等；临时资源回收。
- [x] /// 按实际失败结果更新过程记录及能力矩阵，strict31/31与diff通过；10.2不勾，F8前置不虚增。

## 2026-10-01：已授权Commons两域名订阅排除

**Goal:** 当前订阅只追加commons.wikimedia.org/upload.wikimedia.org到Fake-IP blacklist排除，保留微信条目和全局网络设置。
**Architecture:** 已核对current=R7Cn5rJwP6V4、绑定script=sWS8XVoBoCyb；在现有幂等微信脚本中追加两域名，不改节点/凭据/DNS服务器/全局覆写/生成配置。先备份后修改，再语法/幂等/唯一差异检查；应用重载与真实DNS验收分开。
**Tech Stack:** existing Clash subscription JS / Node syntax / read-only DNS。

- [x] /// 当前订阅/脚本已读，用户明确授权两域名；Commons用于搜索许可和下载公开素材，不是发布接口，版权仍逐项判断。
- [x] /// 对精确脚本备份为同目录sWS8XVoBoCyb.js.aics-commons-20261001-17b.bak，最小追加两域名；Node语法/幂等/完整结构比较确认仅新增两个filter、其余配置不变。
- [x] /// 通过已授权Clash UI重新激活当前订阅，生成配置含微信+两Commons排除；全局enable_dns_settings仍false。实际DNS为公网、原host证书TLSv1.3通过。仅网络预检，不冒充真实素材导入或微信验收通过。

## 2026-10-01：F8 前置只读核查（不是 apply）

**Goal:** 在F7真实网络/对账等待期间，用当前代码和隔离探针证明F8起点，不跳过阶段门槛。
**Architecture:** 仅当前proposal/design/tasks/delta与auth/startup/health/metrics/storage已知入口；不启动lifespan、不读secret配置、不创建默认数据库，不改产品代码/规格。
**Tech Stack:** source review / in-process FastAPI read-only diagnostic。

- [x] /// 核对F8 0.1/0.7及完整100项边界，确认F7为97/105、F8为0/100；subject映射必须单独审定，不能拿email claim或token role替代。
- [x] /// 实际隔离健康故障和动态路径探针：200/degraded、合成异常标记进入响应、两条动态路径进入指标；0外部请求/0库文件/lifespan未启动，临时目录回收。
- [x] /// 记录当前startup写库、MinIO仅exports及已查到的直接媒体路径，声明存储清单仅已知入口而非全量；F8 tasks不勾，等待F7前置关闭及subject设计决策。

## 2026-10-01：F7 真实公共素材验收

**Goal:** 沿用10.2，以实际Commons搜索/下载和产品导入证明字节链路，不以夹具冒充真实平台。
**Architecture:** 私有临时SQLite/素材目录，仅现有API、正常注册和身份；不读取微信或模型凭据、不绕过固定公网/TLS/限额策略。接受许可必须精确匹配元数据，public/model/commercial均false。未知微信不重试。
**Tech Stack:** existing FastAPI TestClient / Commons adapter / MaterialRevision。

- [x] /// 通过provider-search真实搜索；无支持许可或网络拒绝时如实记录，禁止替换transport、代理或DNS来制造通过。2026-10-01返回502/search_provider_failed，零MaterialRevision/verification。
- [ ] /// 若返回支持许可，实际stage/raw/accept并回读磁盘字节、SHA256和来源/权利；当前系统DNS返回Commons两个Fake-IP，未进入下载/accept。本轮独立临时库/目录已回收。
- [x] /// 更新验收证据、进度及README；未取得真实字节，不关闭10.2/F8前置。只追加验收事实，未改业务代码/测试/迁移或VPN。

## 2026-10-01：F7 全应用 lint 门禁收尾批

**Goal:** 清掉12项已实际复现的lint门禁，保留既有API ValueError和Workflow失败持久化语义。
**Architecture:** 沿用F7 10.7已批准的全量门禁；五项机械修复仅import/Iterator/re.IGNORECASE，其余7项使用逐行有理由的例外，不全局忽略规则、不把422改成TypeError/500、不让条件准备错误逃逸。main原dirty变更完整保留。
**Tech Stack:** Ruff/AST comparison/existing pytest/TypeScript Vite/OpenSpec/isolated databases。

- [x] /// 先记录lint RED、读取validator与调用边界，在active F7 design注明兼容性，保存六份修改前AST安全快照（代码不含凭据）。
- [x] /// 五项机械lint修复、六处ValueError兼容说明、一处节点失败持久化边界说明；检查六份规范化AST相同且全应用Ruff PASS。
- [x] /// 完整隔离后端1629/28 skipped、前端build/预算、strict31/diff和独立只读APPROVE；16原生PG及完整迁移往返通过并回收容器/卷，10.7关闭/F7现97/105，未推进F8业务apply或真实未知重试。

## 2026-10-01：上传未知的安全诊断修正批

**Goal:** 保留未来官方步骤的可判断脱敏错误，不重发上次上传或草稿。
**Architecture:** 沿用已批准2.4的Attempt安全metadata，明确固定code白名单与严格boolean提示；拒绝任意异常文本。上次历史保持原样，一般合同不变。
**Tech Stack:** existing Delivery/OfficialTransport/pytest。

- [x] /// 先将安全诊断scenario归入active spec/design；在既有Delivery回归中复现固定transport错误丢失和任意敏感code必须拒绝。
- [x] /// 最小修改execute_prepared/readback/_finish，只持久化白名单固定字段，不改unknown/claim/currentness，不调用远端。4项RED→GREEN、两次独立只读APPROVE。
- [x] /// 隔离临时库4项诊断定向GREEN、最终full1629/28 skipped/9 warnings，范围Ruff/OpenSpec strict31/diff；记录README/progress/findings，两次独立复核APPROVE，F7/F8不提前关单。

## 2026-10-01：已批准短稿的真实验收批

**Goal:** 指定批准账号仅创建一个明确“系统联调测试，请勿发布”的草稿并回读；不公开发布、不放行长文。
**Architecture:** 仅临时私有 SQLite/素材目录，用现有产品 API 创建 Persona/Account/连接、Project/Brief/真实冻结作者观点 FactPack、Master/检查/Variant/Candidate/Approval。禁止手填检查/hash/verification、旧CLI或gate override。执行前 rollback preflight，执行时精确候选/账号/有效期，一次create，Unknown保留不可重发。只在该验收进程明确配置随机独立身份key，非Publisher fallback、不用于生产，所有凭据不落盘/输出。
**Tech Stack:** existing API/SQLite/Pillow/official Delivery / accepted WeWrite configuration resolver。

- [x] /// 通过现有产品API建立私有验收库与原创测试封面；完整真实计算检查/冻结血缘，不从pytest夹具复制假的snapshot/hash。
- [x] /// 精确账号连接与角色权限、所有live gates、最终HTML810字节preflight，打印安全IDs/hash/状态，预检零Target/Attempt。
- [x] /// 仅该批准短稿显式execute一次；token成功，asset_0未确认，Target/Attempt=1/1，unknown/reconciliation_needed。未进入create/read；回读existing Attempt，不重试、不重新创建候选绕过防重。真实完整验收未通过。
- [x] /// 更新README/progress/findings和安全验收记录；不关闭完整F7/一般contract/F8，未push/deploy/生产迁移。

## 2026-10-01：F7 整阶段本地门禁与独立复核批

**Goal:** 关闭已批准 F7 的本地验证缺口，保留真实平台未验证和 F8 顺序门槛。
**Architecture:** 本轮仅执行现有10.7/10.9的完整本地门禁和只读复核。main既有dirty改动保留；reviewer不写代码、不读凭据、不发外部请求。临时PG仅127.0.0.1:15439/aics_account_test，缓存镜像，独立schema/无宿主挂载，结束stop/回读回收。不用本地通过关闭8.3/8.5/10.2/10.3/10.5/10.6或ARCHIVE_READY。
**Tech Stack:** existing pytest / TypeScript Vite FE-P1 / Ruff OpenSpec / isolated SQLite PostgreSQL。

- [x] /// 新鲜完整后端最终1625 passed/28 skipped及前端build/bundle；原生PG17 passed、完整PG全链/F7 up/down/up，SQLite迁移/保留史拒降级包含在full suite。只动临时库；不执行默认/生产迁移。
- [x] /// 对整阶段Security/Provider和Delivery/Account/GUI边界做两份独立只读review，主Agent确认具体发现再最小修正；Scope B APPROVE、Scope A两发现修复后独立定向APPROVE，不让reviewer成为第二业务writer。
- [x] /// 复核修正批：4个RED复现Connector fetch/mapping改动未失效及Commons字符串intern漂移，再将实际loaded code加入endpoint指纹、Commons改用稳定marshal v2，相关81 passed/独立修正复核APPROVE。沿用1.10/10.9，不新增领域对象或migration，完整后端最终重跑中。
- [x] /// 记录docs/FE_F7_FINAL_LOCAL_GATES.md及progress/findings/README，10.9按组合独立review关闭；10.7因full Ruff 12项HEAD baseline未通过保留。远端未验、未commit/push/部署/归档、不启动F8。

## 2026-10-01：真实短稿验收入口（等待测试稿确认，不发远端请求）

**Goal:** 让已审批的精确 Candidate 可以通过产品 Delivery 执行一次有界实验，不用旧发布 CLI。
**Architecture:** 新增验收脚本，仅接受私有临时目录内既有 SQLite 验收库，不创建/迁移数据库，不生成候选/检查/验证。默认 preflight + rollback；显式 execute 才原子 prepare → execute_prepared。固定批准的两份配置只在进程内读取并一致性校验，身份 key 必须显式提供；结果只投影允许的状态、ID、hash 和步骤。
**Tech Stack:** existing SQLAlchemy / official Delivery / PyYAML (already installed) / pytest。

- [x] /// 在 apps/api/tests/test_f7_wechat_short_acceptance_runner.py 添加 RED：默认零请求/零Target/Attempt、精确hash/admin/account/expiry拒绝、配置不一致及敏感错误不泄漏、私有临时路径与已有Target防重。初始17缺模块失败后通过；复核三项真实边界经4个RED复现并修复，现22通过。
- [x] /// 在既有 apps/api/scripts/ 下新增 accept_wechat_short_draft.py；只接现有产品服务，不改一般合同gate，不建立新HTTP入口/表/迁移，禁止自签随机fallback key。URI使用as_uri并PRAGMA核对实际文件；参数错误固定遮蔽；准备后失败保持exact IDs/unconfirmed/null dispatch/no retry。
- [x] /// 定向回归/Ruff/diff/OpenSpec strict及独立只读复核；更新 README/progress/findings。修复后full1620/28 skipped，后加Unknown定向共23 passed，strict31/31、Ruff/diff、独立纠正复核APPROVE。测试夹具不算平台验收，真实调用仍等待测试稿确认。

## 2026-10-01：已批准的短稿实验实施批

**Goal:** 通过产品链路验证指定账号短稿草稿箱，不公开发布、不放行长文。
**Architecture:** 一般合同gate保持false；产品显式实验scope绑定Account/AppID、Candidate/hash、Target/Attempt/action/expiry。沿用existing metadata、冻结审批、exact refs、live gates与Unknown；无新表或迁移。
**Tech Stack:** existing official runtime/transport/Delivery / OpenSpec / isolated regression。

当前接入批使用既有`delivery.py`和`wechat_official_delivery.py`：`prepare_short_draft_experiment`仅内部受信调用，接收明确account/AppID/Candidate/hash/actor/expiry授权，先复用一般授权的live检查，再原子准备Target/Attempt并签名。不增加公开HTTP实验入口或fabricated verification。`execute_prepared`复用逐步claim，签名在每步按DB真源重建scope核验；任何实验Target不允许第二Attempt，即使对账not_delivered。注册撤销/轮换/过期仍阻断。定向命令沿用API pytest，完成后Ruff/diff/OpenSpec strict。

- [x] /// 增加上述产品链路定向RED（无general verification、精确scope、签名篡改/过期、注册撤销、Unknown防重和先预算后token）；9个缺函数失败，新增撤销/known-ID回读与worker启动/发送点过期RED→GREEN，签名晚失败原子回滚通过。
- [x] /// 接入原子prepare、内部授权参数、existing Attempt签名校验与execute_prepared；103相关GREEN、1598全后端/28 skipped、16原生PG/guard、strict31/Ruff/diff及独立窄复核APPROVE。真实平台仍未验。

- [x] /// 将用户批准的例外写入active proposal/design/spec/tasks，保留一般拒绝和长文义务。
- [x] /// 实现纯函数UTF-8最终正文门槛与现有URL最大值的保守模板上界；6 RED后19 render回归GREEN，尚未接入执行路径。
- [x] /// 精确scope短期purpose-separated签名和transport基础；账号/runtime/token/过期/正文/单client未知create防重经87相关回归通过。仅基础，不代表DB权限或durable实验闭环完成。
- [x] /// 在wechat_official.py、wechat_official_delivery.py、delivery.py及transport中实现一致精确scope；capability_integrations保留一般未验证/合同拒绝，不制造实验verified，负向回归沿用批准的2.8任务。
- [x] /// token/上传前验证最终URL展开字节上界，create前验证实际UTF-8正文<2048；scope错配/过期/重用拒绝，unknown不能重发。发送点过期与原生PG新竞争通过；inline保守拒绝不算平台验收。
- [ ] /// 隔离产品数据链路准备并审批明确测试稿和精确素材，凭据只在进程内；执行一次真实草稿创建/回读，安全记录partial/ID/hash，不伪造verified或发布历史。

## 2026-10-01：网络恢复后的真实验收边界

**Goal:** 移除已解除的DNS阻塞，不把网络成功冒充公众号验收。
**Architecture:** 保留账号/审批/合同检查；只记录公网DNS与原域名TLS预检。正文限额冲突的实验例外须用户另行确认后才能修订规格，不默认放行。
**Tech Stack:** Python socket / system TLS / existing OpenSpec contracts。

- [x] /// 用户重启VPN后，解析117.144.228.18、117.144.228.62、221.181.99.40均为公网；直接连接首个解析地址并以api.weixin.qq.com校验证书，TLSv1.2通过，HTTP/账号请求为0。
- [x] /// 重新读取官方创建文档，content字段仍同时标注2KB与1MB；现行规格拒绝真实请求，补充方案保持17/20。
- [ ] /// 等待用户决定是否批准独立的小于2KB短稿实验；不得永久缩减产品限额、声称长文合同确定或绕过生产gate。

## 2026-10-01：当前Clash订阅微信域名最小排除

**Goal:** 用户已批准只为当前订阅排除api.weixin.qq.com，不开启全局DNS覆写、不替换已有DNS服务器。
**Architecture:** 当前R7Cn5rJwP6V4绑定sWS8XVoBoCyb.js为空main脚本；先备份，再在该订阅script中幂等追加blacklist条目。保留全局及其他订阅、凭据与公众号安全gate。
**Tech Stack:** Clash subscription script / Node syntax and structural comparison / existing pinned TLS preflight。

- [x] /// 解析profiles.yaml确认当前订阅与script，读取原脚本；DNS覆写false、blacklist、现有8项nameserver与空filter已确认。原script无业务改写。
- [x] /// 原script同目录备份；apply_patch只追加微信过滤，Node语法/幂等及完整结构比较确认差异仅dns.fake-ip-filter，8项上游与其他字段完整保留。
- [ ] /// 通过应用重新生成配置并验证实际DNS/TLS；生成文件尚无该条目，Computer Use未获Clash授权，需用户在当前订阅打开扩展脚本并保存/重新应用。不直接覆盖整个订阅/生成文件，不清全局缓存、不重置VPN；原文件备份已保留。


## 2026-10-01：真实公众号草稿测试授权与配置预检

**Goal:** 使用用户指定的new_media/WeWrite现有账号进行公众号草稿箱测试，不公开发布，不绕过批准内容与接口合同。
**Architecture:** 只从批准配置读取本账号凭据，在内存中解析；产品接入仍要求exact Account/Persona、Candidate审批、scope和官方合同。外部网络预检不带凭据。
**Tech Stack:** WeWrite YAML / existing official transport / OpenSpec。

- [x] /// 读取项目README、WeWrite主/发布skills与当前补充规格；确认两个配置源AppID一致且凭据已存在，仅输出存在性与不可逆摘要。
- [x] /// 确认真实token/upload/draft/create/readback已获用户授权，公开发布未授权；实际官方DNS安全预检失败，198.18.1.55非公网，无账号请求或外部素材/草稿写入。
- [ ] /// 用户修正官方域名fake-IP解析后重验；正文限额合同仍需闭合。不得绕过合同、SSRF、scope或冻结审批gate。满足后才运行真实草稿链路并回读，不以旧WeWrite脚本成功代替产品验收。


## 2026-10-01：F7整阶段官方Publisher审计与F8前置核对

**Goal:** 纠正能力矩阵过时的“官方实现不存在”，完成现有本地适配器整阶段只读安全复核，不把实现/配置/真实验收混同。
**Architecture:** 仅descriptor bootstrap读取、不解析secret/runtime、不访问账号或写数据库；审官方四模块及既有router/verification/receipt集成。F8前置依现行proposal/design/tasks，未满足不业务apply。
**Tech Stack:** existing Python Registry / read-only independent review / OpenSpec。

- [x] /// 读取实际bootstrap描述符及真实合同gate，更新docs/FE_F7_CAPABILITY_MATRIX.md当前官方路径与证据范围，保留旧记录历史及原F7/F8义务。
- [x] /// 独立整阶段local官方security/provider/delivery review APPROVE，无新增具体缺口；结论不关闭真实2.8、完整2.9、F7/F8。
- [x] /// 文档strict31/31 exit0、diff-check通过和状态回读，更新progress/findings/README；没有配置/凭据/动作授权的外部验收保持未完成，不盲目重复同一测试关闭真实门槛。

## 2026-09-30：跨项目共享Profile锁顺序验收

**Goal:** 补齐真实PG的跨项目授权/执行强制交错，不能由同项目project锁掩盖registration→profile反转。
**Architecture:** 两条独立真实项目/Candidate，复用同一published profile/Publisher registration。授权事务先锁profile，执行事务等待该profile；原生PG确认等待对象且registration可被独立NOWAIT探测取得，再完成授权/执行。只替换transport，无真实副作用。
**Tech Stack:** pytest / SQLAlchemy events / psycopg / opt-in PostgreSQL。

- [x] /// 扩展既有ready fixture用于第二个独立项目/账号且共用registration；PG test证明不同project/同profile，pg_blocking_pids/等待SQL/registration NOWAIT验证明确锁交错及零提前dispatch。
- [x] /// 原生PG14 gates通过；相反锁序进程mutation同gate精确RED，真实实现GREEN，独立只读复核允许2.2完成。追加prepared→rotate claim保留/零dispatch及两种foreign账号3 PASS；2.6/2.7最终复核待返回，20账号UI+12preview+9recovery共41 gate通过。
- [x] /// full1564/26 skipped、82相关、14PG/guard、1PG迁移、41UI fixture、TS/Vite/FE-P1、strict31/Ruff/diff通过；独立本地复核2.2/2.6与scope revoke APPROVE。临时PG/Vite回收；仅关闭2.2/2.6/2.7至17/20，不commit/远端/生产迁移/F8跳级。

## 2026-09-30：官方Delivery PostgreSQL竞争验收

**Goal:** 以独立PG连接实际验证prepare/execute/authorization竞争和撤权赢锁后的零dispatch，不以SQLite或唯一约束冒充。
**Architecture:** 新opt-in测试文件复用真实ready API链路，覆盖db_session为唯一临时schema中的PostgreSQL；只替换外部transport。临时容器使用既有16-alpine镜像、127.0.0.1:15439、无宿主目录挂载，仅镜像匿名临时数据卷。
**Tech Stack:** pytest / SQLAlchemy / psycopg / Docker local fixture。

- [x] /// 创建tests/test_f7_wechat_official_postgresql.py，exact测试URL/driver及禁query门槛、独立schema/连接/事务、prepare双请求与execute双请求竞争。修正连接query覆盖经6 RED→7 GREEN，6 native PG + 7 guards通过。
- [x] /// 追加同项目授权vs执行、registration撤权先赢与步骤持锁证据；Event/Barrier和pg_blocking_pids实际观察双向锁等待。不同项目共享profile的锁顺序证明未覆盖，不据此关闭2.2。
- [x] /// 实跑13定向PG/guard及独立1迁移，fresh full1561/25 skipped、strict31/Ruff/diff；URL隔离修复独立窄复核APPROVE；临时container/schema回收确认。2.2仍需跨项目证据，不勾选，F7/F8原门槛仍保留。

## 2026-09-30：双账号交付与恢复入口批

**Goal:** 同一角色A/B账号分别真实本地授权/Attempt/Receipt，跨账号runtime不可混用；Review显式恢复不得create或自动重发。
**Architecture:** 复用existing Account/Target/Attempt/Receipt和official-readback；不新增表/迁移。UI只能提交exact最新Attempt，不接受客户端draft ID或正文。
**Tech Stack:** pytest / React / Vite / isolated Playwright。

- [x] /// tests/test_f7_wechat_official_delivery.py补同Persona A/B链路与A-only rotation负向；修复draft Receipt误入发布历史和stale Receipt旁路，26项Delivery实测，旧F5B兼容。
- [x] /// ProjectReviewCenter接已有official-readback/explicit reconcile入口，浏览器RED→GREEN；cancel无动作、only exactAttempt、running人工对账/禁下载、归档禁用，36账号/preview/recovery fixture gates通过。不开放未验证自动草稿。
- [x] /// 修复后full1554/19 skipped、68 targeted、build/budget/strict31/Ruff/diff及独立窄复核APPROVE；36 UI fixture gate通过。仅完整满足的任务勾选，PG/真实门槛未验仍开。

## 2026-09-30：官方内文图片交付验收

- [x] /// 复用真实Master append/refs/checks和adapt-preview构建inline fixture，不以manual稿绕过semantic gate。
- [x] /// 验证exact PNG封面/内文上传和固定HTML槽位；cover后撤权/字节篡改均阻断后续create，18项Delivery定向通过。
- [x] /// 全后端1546/19 skipped、strict31/31、Ruff/diff及独立窄复核APPROVE；双账号/PG/恢复UI/真实平台仍待验证，不据此关F7/F8。

## 2026-09-30：官方Delivery执行批

**Goal:** 复用现有Target/Attempt把批准的官方表示接入可审计执行，不触及真实账号。
**Architecture:** delivery.py只给新official key分派；wechat_official_delivery.py负责目标CAS、私有claim、每步durable in-flight与重验、固定资源上传及安全结果。沿用现有表和stdlib transport，不新增迁移。
**Tech Stack:** 现有SQLAlchemy/FastAPI/pytest。

- [x] /// tests/test_f7_wechat_official_delivery.py先RED覆盖真实freeze/approval→official target→prepared commit、并发/崩溃拒重发、逐步撤权/轮换和partial metadata，再接新key；十五项本地验收通过。
- [x] /// official target选定/缺render拒绝、target写锁+claim、每个有界步骤持锁重验并保存安全metadata；独立三项缺口各RED→GREEN，显式崩溃/未交付恢复，不自动重发。PG授权/执行竞争仍未验。
- [x] /// 回读完全匹配后仅awaiting_manual_receipt；失败unknown与已知ID保留，156定向/1543全后端+19 skipped/build/strict/Ruff/diff及独立修复复核通过。真实gate、PG竞态/浏览器/整个F7/F8未证明项仍保留；补充方案13/20。

## 2026-09-30：官方传输与资源替换批

- [x] /// tests/test_f7_wechat_official_transport.py先覆盖token/upload/create/readback、非公网DNS、超时/限额/错误脱敏及缺冻结render RED，再实现wechat_official_transport.py；依赖仅stdlib，真实contract gate仍false。
- [x] /// 在wechat_official_render.py追加纯冻结render校验、exact账号/素材mapping替换和严格readback；旧v1–v5不补render、不改hash，异常不创建草稿/自动重试。
- [x] /// 定向141、全量1528/19 skipped、build/FE-P1、strict31/31/Ruff/diff与独立foundation修复复核通过，规格/文档同步；不声称DB步骤CAS/官方execute与真实账号终验完成，不新增表/迁移或push/deploy。

## 2026-09-30：Settings账号入口批

- [x] /// 在既有账号浏览器夹具增加Settings双账号/普通用户只读/无网络效果验收，缺入口RED→GREEN；独立复核发现祖先归档，再以API3 RED/UI RED→GREEN闭合。
- [x] /// CapabilitySettings复用AccountPublisherPanel并按actor/account隔离，角色旗下账号读取面向viewer开放，保留旧验证入口边界；read_only统一使用服务端完整层级投影。
- [x] /// 最终139定向/1 skipped、1501全后端/19 skipped、15账号/12预览UI、构建/FE-P1、规格和diff通过，独立本地复核APPROVE；仅关闭1.5/1.7/1.8至9/20，1.6远端兼容门槛仍开，F7不关单。

## 2026-09-30：批准本地apply与远端门槛分离

### 继续Batch A：账号runtime与冻结投影

- [x] /// 正文image block/slot纯契约与RED；修改channel_variant_documents、wechat_official_render，旧正文hash保持。
- [x] /// channel_variants共享素材/live rights校验及TextChannelAdapter精确source image映射；不放宽语义checks；API保存/冻结/Review/ZIP及撤权负向回归。
- [x] /// 更新渠道预览的图片位置/槽位显示，隔离浏览器与构建预算；独立只读复核整个新增链路，无真实账号动作。仅已定义paragraph/image来源和冻结HTML，本批不自动关闭整个1.5/Batch A。

- [x] /// Review 显示同一冻结 official_render；只读 sandbox/CSP、hash/槽位/不可用原因，先真实组件浏览器 RED 再 GREEN，旧候选缺字段不变。inline定位和整项1.5仍未关闭。

- [x] /// 在既有F7 capability测试加入账号A/B runtime/token/rotation及伪造verification RED；新wechat_official服务只复用settings/Account/Registry，不新增表，不取真实token。
- [x] /// exact official key的implementation/account fingerprint与验证分派；默认合同未核实拒绝verified/remote，旧WeWrite/Connector不放宽。
- [ ] /// 官方冻结render与Review/包兼容按已批准规格推进；local fixture不会关闭真实验收。
- [x] /// 已证明的canonical正文/cover冻结后端子集与局部回归；inline定位/UI尚待后续，不代表整项完成。
- [x] /// 本轮runtime/冻结后端子集的定向/全量回归、strict/Ruff/diff、文档与独立窄复核。保持main本地未push，F8不跳前置；不代替Batch A/整阶段终验。

**Goal:** 实现一角色多账号、真实账号独占及隔离官方适配器，不缩减F7/F8完整目标。
**Architecture:** 复用ContentAccount、Capability与Delivery；本地开发不取token，真实合同未核实远端拒绝。直接main单Agent开发。
**Tech Stack:** SQLAlchemy/Alembic、FastAPI、pytest、现有React工作区。

- [x] /// 按用户“好的，同意”修订0.1和spec，保留远端限额/精确授权门槛，strict验证。
- [x] /// Batch A账号基础：绑定/CAS配置API、加法迁移、SQLite/PG竞争与旧行保留；Identity安全UI及8项隔离gate。基础部分已验，剩余resolver/render/Settings不得提前勾。
- [ ] /// Batch A：先在test_fe_f3b_content_identity.py与账号迁移测试加入RED，再修改models/content_identity/router和加法migration；验证唯一性、父级/归档/foreign/viewer及旧行保留，随后账号配置/冻结render/UI整批。
- [ ] /// Batch B：官方transport/Delivery步骤CAS/readback在本地隔离环境实现，真实远端gate仍不满足；完整安全/浏览器/性能/迁移复核，不提前关闭F7或跳入F8。

- [x] /// 记录首批微信公众号权限已开放的用户确认；不写真实verified、不执行账号动作，正文合同冲突仍待处理。

## 2026-09-30：补充方案批准与官方接口证据

- [x] /// 记录本地实施批准和独立复核；对齐F7 design/tasks/Publisher delta，不更改canonical或旧WeWrite历史。
- [x] /// 通过直接HTTPS读取五份官方合同，记录字段/权限适用范围及正文上限冲突；不调用账号API。
- [ ] /// 获得具体账号权限只读证据并消除正文合同冲突，满足0.1后进入两大批业务实施；未满足前不绕过硬门槛。

## 2026-09-30：角色账号一对多与官方Publisher提案

- [x] /// 按用户“不允许”保留单Persona父级；核对当前模型/F7接口边界，不新增多对多关系。
- [x] /// 创建标准OpenSpec proposal/design/spec/tasks；20项两批组织，先冻结账号与内容合同，官方API证据不足作为前置，不执行业务apply。
- [x] /// 独立只读规格复核APPROVE，仅本地规格；31/31 strict与diff通过，维护README/progress/findings。官方证据与用户方案确认两项门槛仍开，不apply，真实上传另需授权。

## 2026-09-30：F7 剩余启动门槛复核

- [x] /// 以main@c216e41核对10项未完成任务和F8前置，独立只读阶段评估PARTIAL；已读路径无新增确定blocker，未穷尽全调用方/UI或PG并发，不关闭10.9。
- [x] /// 实际Commons读取仍因非公网DNS拒绝，安装descriptor确认video/TTS/ASR为空；不访问secret内容、不发付费请求/真实账号动作，不新增未批准Publisher方案。
- [x] /// 按实现未满足/外部未验证/待方案授权交接，更新progress/findings/README；strict30/30与diff通过，本地记录，不缩减F7/F8目标。

## 2026-09-30：F7 已实施链路安全复核

- [x] /// 以main@54978d5为准，主Agent与既有只读reviewer找到两项现有契约缺口：validation回显与ASR提交runtime窗口；未重做已关闭三项，也未调用真实Provider。
- [x] /// 11 RED/1兼容通过，包装入口另补2 RED后整批61 GREEN；固定F7输入错误与提交guard，不改普通CRUD、不新增迁移/适配器。两项窄复核APPROVE，不代表10.9整阶段通过。
- [x] /// 最终代码全后端1485 passed/2 skipped，构建/预算/strict30/30/范围Ruff/diff通过并本地提交；F7仍95/105、公众号替代选择及真实授权/凭据门槛保持，F8不开始。

## 2026-09-30：F7 最新迁移与公共来源实测

- [x] /// 以main@c828672和f7b000000001为准，独立PG16.15实际往返和两类保留史拒降级，旧行/约束/FK/索引回读通过；不碰其他容器或默认数据库。
- [x] /// 实际Commons搜索被DNS非公网198.18.0.41拒绝，零HTTP/下载/导入；记录真实失败，不改SSRF/代理，不勾10.2。
- [x] /// 本轮独立容器已停止/自动移除，脚本与报告保留；SQLite7项/strict30/30/diff通过，记录窄复核APPROVE，不改业务实现，F7仍95/105、F8不apply。

## 2026-09-30：F7 三项安全缺口整批修复

- [x] /// 先补既有F7规格边界与失败回归：14 RED/1原先通过→15 GREEN；两跳真实HTTPX/HTTPCore受控连接验证IP/TLS/Host/禁代理，实际db.commit并发配置串行。
- [x] /// 实现现有安全契约，不加供应商/业务表/迁移；历史读取和legacy safe_fetch保留，配置锁仅保障当前进程。
- [x] /// 150定向/1470全后端（2 skipped）、build/FE-P1/strict30/30/diff通过；范围Ruff记录已有workflow告警例外。独立窄复核APPROVE，关闭四项至95/105，10.9/F7终验及F8仍待办。

## 2026-09-30：F7 阶段安全与交付复核

- [x] /// 依据既有10.9启动只读阶段复核；主Agent核实调用前撤权漏洞，独立复核仍未完成，不把浏览器subset或测试总数替代安全审查；公众号方案待明确选择。
- [x] /// 主Agent复核调用前source撤权窗口，两个RED→GREEN含实际SQLite双连接；只修现有stage事务及既有spec说明，不开始F8、不新增Publisher对象或真实账号动作。
- [x] /// 记录SQLite source竞态覆盖和PG/project-archive未覆盖；125定向/1448全后端（2 skipped）、新build/FE-P1/strict30/30/Ruff/diff通过。独立review PARTIAL/BLOCK，dispatch无阻断但3新缺口，8.4/8.6/8.11/8.13重新打开至91/105；保留10.9和F7/F8终验。

- [x] /// 三项安全缺口已在上方整批修复并独立复核，不新增供应商/远端授权；真实Publisher方案仍待用户选择。

## 2026-09-30：F7 隔离浏览器再验收

- [x] /// 按既有F7任务10.8，在新临时SQLite/media运行已批准的Settings/Search/Media/Graphic/ASR/Delivery脚本；七脚本52 gate/零page error，不触碰默认旧库，不调用真实模型/账号。
- [x] /// 分别报告actual Chromium、Provider fixture和UI route fixture，保留首次Graphic环境缺失失败/未覆盖范围；仅临时库补admin/Profile后整套通过，无真实账号证据不关闭10.5/10.6或F8前置。
- [x] /// 回收报告、停本轮四个隔离服务；strict30/30、diff和记录窄复核APPROVE。F7 95/105，剩余Publisher方式待确认；不改业务实现或归档。

## 2026-09-30：F7 外部读取边界与能力清单

- [x] /// 在既有 F7 3.6/4.4/10.4/10.10 范围校准压缩拒绝和 Connector 总读取期限；不改 legacy safe_fetch，不扩账号或供应商范围。计划/SPEC窄复核通过。
- [x] /// RED→GREEN：Commons/typed Connector identity negotiation、压缩读取前拒绝、慢流 deadline、正常响应与现有权利/配置回归；修复仅两个现有函数。11新增，84定向通过，包含空响应和redirect时限。
- [x] /// 集中门禁、只读窄复核、记录 capability matrix 与缺失凭据/Publisher真实阻塞；全后端1446/2 skipped、build/FE-P1/strict30/Ruff/diff通过，窄复核APPROVE；F7 94/105，不借本地包/fixture宣称 F7或F8完成。

## 2026-09-30：F7 已配置图片 Adapter

- [x] /// 校准 5.8 的单次 HTTPS/base64/config fingerprint；复用 KEY_IMAGE 和 stage/accept，无新对象/迁移，不发送真实凭据请求；独立计划复核通过。
- [x] /// RED→GREEN：原生图片 adapter、safe endpoint/response cap/timeout/rotation、真实 PNG 入 preview/明确接受；legacy generate 与 Settings 不写 WeWrite 全局配置，其他 Provider 不 fallback。28 新回归，DNS→TCP pin；压缩响应失败回归后拒绝读取，独立复核缺口关闭。
- [x] /// 集中定向52/全量1435 +2 skipped、构建预算、strict30/30/Ruff/diff、独立窄复核通过；配置与 Mock transport 不作为真实厂商验证，10.3 保留待办，F7 92/105。

## 2026-09-30：F7 人工对账闭环

- [x] /// 补严既有 8.8：exact latest attempt、非空安全证据、原子人类回执与幂等；不将草稿箱对账当已发布，不新增表。
- [x] /// 失败回归后实现 target 锁与 evidence hash 投影；Project Review 明确确认并只提交本地证据摘要，保留 legacy note 输入兼容。
- [x] /// 集中跑交付/安全定向109、全后端1407/2 skipped、前端构建预算、strict30/30/Ruff/diff；五项 UI fixture gate 与独立整批窄复核 APPROVE。记录实际覆盖，不冒充真实远端验证或阶段终验。

## 2026-09-30：F7 媒体 Renderer 精确范围执行

- [x] /// 复用两个既有 capability 表和已真实渲染的 actor stage：明确确认 input/output hash 才追加媒体 scope 验证；当前来源/字节/rights/runtime/Profile 事务内重验，不再调用 Renderer，不写 Master/素材。per-stage operation lock 保护 accept/verify，全局 cache 锁不等待 DB；提交边界重验身份/TTL/冻结字节。registration 写锁串行化 revoke/accept commit。
- [x] /// 普通 editor 执行另走 verified media output 入口，起始/返回/接受/commit 均检验 exact registration/runtime/schema/channel/form/MIME/expiry。26 新回归、106 定向、实际 SQLite 两连接撤销→接受与缓存锁边界通过；PG 并发未跑。
- [x] /// Graphic UI 显式验证与按已记录范围请求分离；安全库存不检查 runtime/文件，仅记录可请求且服务端执行时重验。13 真实 browser gate、全量 1400/2 skipped、构建/预算/strict/Ruff/窄复核通过后本地提交。F7 90/105，Video 实际 renderer/其他外部能力仍待办，无发布/迁移/归档。

## 2026-09-30：F7 Graphic Studio 渲染产品入口

- [x] /// Settings 提供安全 media preview descriptor，不调用 runtime/env/files/probe；失败 API 测试后实现，三项 API 回归通过。
- [x] /// Graphic-only lazy 面板绑定 saved Master/canvas，dirty/history/archive 禁止操作；复用接受面板，分别显式接受素材、引用最终图、保存 Master，不改 Workflow/自动验证。归档和 canvas/actor 切换 guards 经静态复核，本批没有单列浏览器验收。
- [x] /// 真实 Chromium 隔离浏览器 RED→GREEN：十个 browser gate、全后端 1374/2 skipped、构建/预算/strict/Ruff/diff 与窄独立复核通过，记录后本地提交。不推送/归档/生产迁移。

## 2026-09-30：F7 真实本地图文渲染实现

- [x] /// 明确配置 Node / Playwright / Chromium / 单一字体，运行身份绑定脚本、依赖、浏览器和字体字节；缺配置不可执行，不依赖 Codex 私有默认路径。
- [x] /// RED→GREEN：真实 PNG 像素、裁剪/形状/文字、重复输入确定性、缺素材/字体覆盖/非法文档拒绝、配置漂移；固定 DOM/CSP/route/proxy/DNS/sandbox 防御，不冒充 OS 无网络验收。仅接现有 admin preview，不自动写 Master/attestation/verified。
- [x] /// 独立复核与集中门禁：73 定向、1371 全后端、构建/预算/strict/Ruff/Node syntax/diff PASS；API 证明显式人工最终绑定，产品 UI 与普通用户 verified 执行保持待办，不勾完整 7.5–7.7。记录真实本地运行与窄复核 APPROVE。

## 2026-09-30：F7 媒体 Renderer 输出接受边界

- [x] /// 依 F7 7.5–7.7：定义已加载 exact renderer 的有界 MediaRenderOutput 协议与当前 Master/hash/context/canvas 请求；只复用既有 15 分钟 actor preview 与 MaterialRevision，不建表。未安装 renderer 仍 unavailable，不做假渲染。
- [x] /// API RED→GREEN：来源/新版本/上下文/实现漂移、错 input hash/画布/MIME/尺寸、秘密元数据、foreign/viewer、公开权利撤销、模型/商业权限升级、CC BY、超限与去重。归档仍走已有 owned_unit mutate 拒绝，本批未单列归档/真实双连接竞态测试。仅调用一次，接受前后重验来源；不改 Master 或自动 attestation。
- [x] /// admin-only media-render-previews 复用 provider-media raw/accept。32 新回归、77 定向、全后端 1354/2 skipped、构建/预算/strict/Ruff/diff 通过，独立 foundation 复核 APPROVE。记录基础契约而非媒体 Renderer 完成；真实实现与 UI/成片绑定继续，7.5–7.7 不提前全勾。

## 2026-09-30：F7 共享消费与配置指引批

- [x] /// 依现有 F7 4.9/9.7，验收搜索 preview→accept→项目精确引用→两 Unit 独立保存/生产页回读及撤权；不重复入库，不以 fixture 宣称真实外部能力已验证。没有自动 Video render，不能将回读算成成片验证。
- [x] /// 测试先行添加只读 Provider 指引：仅加载 descriptor 和安全 registration 标识，不调用 runtime fingerprint、秘密配置、网络、子进程或 Provider；缺实现保持 unavailable，配置记录不等于有效验证。
- [x] /// Settings 模型分区 lazy 接只读配置指引，缺 durable 配置 API 不放假 Save；48 定向、1322 全后端、前端/预算、7 浏览器 gate 与独立窄复核通过，记录本地提交。真实媒体 Renderer 和 F8 保持原范围未核销。

## 2026-09-30：Renderer 持久验证批

- [x] /// 校准已批准 F7 Renderer 精确 scope、确定性/人工性质与真实 Text probe；规格定向复核 APPROVE 后进入代码，不新增业务表或自动 verified。
- [x] /// 测试先行：增量 scope constraint、旧证据保留/拒降级、exact loaded renderer/runtime/scope、只读清单无探测、viewer/异项目/旧 Master 拒绝。独立复核三项缺口已用失败回归复现并闭合。
- [x] /// 实现既有 Production Text/Manual Renderer descriptor 与管理员明确 Text probe；记录实际 input/output hash，不改 Master/Candidate，不把人工媒体当自动 renderer。Text-only lazy 入口、Settings 只读清单和六浏览器 gate 已通过。
- [x] /// 集中定向 55、全后端 1318/2 skipped、隔离 SQLite/DDL、前端构建/预算、strict 30/30、Ruff/diff 与独立窄复核通过；同步 README/progress/findings，提交本地 main。实际媒体 renderer 输出接受/成片绑定继续后续实施，不能冒充本批完成。

## 2026-09-30：F7 两批实施，随后 F8

- [x] /// ASR 批：先写失败回归，验证精确 Project-visible 音频/视频字节与 model-use 权利、真实时长、actor/base/runtime/context 有界 receipt，建议不得写 Master；只通过显式 save 验证并记录安全血缘。
- [x] /// Video Studio 接 ASR 预览/拒绝/明确接受，本地字幕编辑和 Master save 分离，接受使成片绑定失效；模型未配置仍显示不可用，旧三形态路径保持兼容。
- [x] /// 集中跑来源撤权、坏 cues、过期/伪造 receipt、旧 Master/跨项目回归及浏览器门禁；调用事务边界回归通过，ASR 双连接竞态未单独重跑，不冒充并发终验。全套 1291 passed/2 skipped、四浏览器 gate、build/预算/strict/Ruff/diff 与独立窄复核通过，已更新 README/progress/findings，不以 fixture 冒充真实 Provider。

- [x] /// 接续搜索整批：限定公共 Wikimedia 搜索 adapter 与 exact key/version，服务端只缓存短期抓取定位符，API 只返回有界安全候选/许可摘要；旧搜索入口不直传原始 Provider metadata。
- [x] /// 显式选择候选才下载有界真实字节并进入既有 stage/accept，固定来源域名/同源跳转、许可/署名核对、配置漂移、过期/跨身份和项目归档均 fail-closed；不建新表/迁移。
- [x] /// Assets 与旧素材搜索共用 lazy 搜索/接受面板，集中验收搜索→预览→许可确认→精确版本/项目引用，真实公共读取与 fixture 清楚区分；全量 1270 passed/2 skipped，8 个浏览器 gate、预算/strict/独立复核通过。本批本地提交，真实外部验证和跨 Unit 实际消费仍待办。

- [ ] /// 第二批接续：先实现共享 ProviderOutput/ASROutput 协议与有界临时预览；精确 actor/runtime/input/bytes 绑定，重启/过期需重新预览，不建第三张持久表。
- [x] /// 将旧 generate 自动写素材改成 stage→明确权利/许可确认→atomic MaterialRevision + 可选精确项目引用；无字节、错 MIME、过期、外部身份、runtime 漂移或输入撤权不写业务对象。新 Assets 与旧入口共享接受面板；20 项定向回归及隔离浏览器四项通过。真实 WeWrite CLI 因内部重试/配置不可证明而 unavailable，不计真实 Provider 实现完成。
- [ ] /// 复用共享接受边界接图像/视频/TTS/ASR Provider；真实 WeWrite 生图仅在明确配置时可请求，不以 mock 代替外部验证。按批末集中跑 API/权利/秘密泄漏与全量门禁，再接 Assets/Production UX。
- [x] /// 核实本地 main、F6E 100/100、F7/F8 标准规格、Alembic head 与后端/前端基线；修正 F7 Endpoint fingerprint 和 v5 WeWrite 输入边界，strict 与 diff-check 通过。
- [x] /// 接续第一批：以失败回归锁定 typed Data Source 的逐块响应体上限、分页与总量边界；仅在 F7 受控调用生效，旧 Connector 路径保持兼容。
- [x] /// 审查并实现 v5 已批准公众号文章到 WeWrite 只读确定性投影；先证明无 Draft fallback、精确封面与无重写，缺字段须在创建远端 Attempt 前阻断。
- [x] /// 集中补足 Capability 表约束、SQLite/PostgreSQL 迁移与授权/审计回归，更新 OpenSpec 勾选、README、progress、findings 后跑整批门禁。
- [x] /// 将数据 profile 配置/探测、账号验证/撤销接入 Settings 六分区；Data Node 用真实 profile 选择器固定版本，完成构建与隔离浏览器验收。
- [x] /// 第一批：两张能力表、版本/范围验证、Registry/Connector 映射、未验证远端动作 fail-closed 与安全日志；集中做回归和迁移门禁。独立复核四项修复通过；真实 WeWrite 不满足账号绑定/无改写契约，8.3/8.5 保持待办，人工包不受影响。
- [ ] /// 第二批：受控搜索/生成/TTS/ASR/渲染、精确素材与项目引用、Settings、发布验证、浏览器与最终门禁。
- [ ] /// F7 验收后复核并实施 F8，完成全产品隔离闭环和生产准入审计；无单独授权不做真实远端副作用、push、deploy、生产迁移或规格归档。

详细步骤：`docs/superpowers/plans/2026-09-30-fe-f7-capability-integrations-delivery.md`。

## 2026-09-30：F6E 集中验收批

- [x] /// 从当前 `main` 保留既有 F6E 工作区，重新跑全量后端门禁；不把上一轮失联的测试会话当作通过证据。
- [x] /// 核对 9.8、11.1/11.2/11.14 的现有回归与缺口，缺口以失败测试先行补齐，再统一核销已证明的任务。
- [x] /// 在独立 SQLite/媒体目录启动 API 与前端，先做 Matrix 只读建议和选择性确认，再做 Text 三目标、Graphic、Video 的浏览器闭环；发现缺陷时先复现后修复。
- [x] /// 隔离迁移/性能/规格/差异门禁与文档记录集中执行；未获授权不做 F6E canonical 同步、归档、推送、部署或生产迁移。

## 2026-09-30：F6E 剩余工作改为两批交付

- [x] /// 本轮先将 Matrix 限量建议接到现有项目页；仅明确勾选并确认的建议才调用既有 Unit 创建 API，错误不吞没，项目归档只读。
- [x] /// 随后将 Variant 历史/适配预览/保存/检查接入 Production 独立面板，并按当前 source/profile/adapter 显示不可用或 stale，不改变 Master 与 Workflow 编辑状态。
- [ ] /// 最后接 v5 Review 多系列选择及授权目标校验，完成浏览器与性能门禁；本地提交按两大批收口，不推送/部署/生产迁移。（Review UI 已接，浏览器验收待完成。）
- [x] /// F6E 7.6：复现 Variant 当前 warning 已 ready、v5 Freeze 却拒绝；对照 v4 warning disposition，要求 v5 冻结保留精确 warning、审批必须按 check ID/input hash 提交理由、授权与包读取重验处置；实时素材/证据安全门槛不得降级。
- [ ] /// 第一批：连续完成剩余后端契约。包含 Variant refs/CAS/漂移与检查、Matrix 只读建议、Candidate v5 完整性、Review/Versions/Overview、五形态本地成品包及新旧安全回归；在批末集中核对 OpenSpec 任务、跑后端/迁移/规格门禁并提交本地 `main`。
- [x] /// 用真实文件 SQLite、两条独立连接同时进入同一 Variant 系列保存入口；验证不同幂等键一成功一 409、相同幂等键只回读胜者，且仅一条 revision/event。项目写锁先于 head 查询，故不在 head 处设置屏障；精确引用原子性另由现有引用回归验证。
- [x] /// 并发回归未揭示需修复的 SQLite 锁异常；服务端写入路径与 PostgreSQL 唯一键冲突恢复保持不变。
- [x] /// 同一精确 v5 Variant 以双连接并发 Freeze：两请求回读同一 Candidate，且仅一条冻结事件；对照已有 currentness/live rights/evidence/bytes/render 回归核销 8.6。
- [x] /// 跨项目与归档安全回归：外部身份 raw-ID 不可读 Variant/Candidate/Package；项目归档后可读历史但不可 Freeze、重跑检查、审批、授权或取包。
- [x] /// 当前切片：先以真实 API 回归构造已有 Brief/Fact Boundary/Identity 与 Graphic v2 最终渲染，验证 Xiaohongshu Variant→checks→v5 Freeze→Approval→local ZIP 的精确素材和无远端副作用；失败则仅修其阻断点，随后补撤权负例。
- [x] /// 接续用已有 Video v2 脚本/镜头创建完整来源上下文，验证 Douyin spoken_script 的当前检查、v5 Freeze→Approval→local ZIP 与 estimated SRT；不引入 F7 Provider 或伪造最终视频。
- [x] /// Text v2 原稿携带准确 FactPackItem 引用时，分别验证公众号文章、X Thread、X Single 的确定性 Variant→检查→v5→审批→本地包；ZIP 清单保留准确引用 locator，公众号仍带真实封面。
- [x] /// Text v2 原稿引用的精确继承：只在段落原文、FactPackItem/checksum、引用位置和 Master 证据 ref 可逐一证明时转换；删引用/改位置拒绝，撤权后的 Variant 检查失效。
- [x] /// v5 已授权历史包再核来源 Master 最新适用检查；新 blocker 或 warning 集合变化时拒绝下载，保留目标形态专属检查豁免和实时撤权错误语义。
- [x] /// Text 原文/引用未变时，新增有界披露声明只改变声明字段；定向验证审批、清单与人工本地包均保留声明和准确引用。
- [x] /// 非法 v5 Freeze 的缺哈希、错哈希、双来源或异项目输入不回退 v4/v3，且不产生 Review/DeliveryTarget。
- [x] /// 五种受控形态分别验收人工本地包、精确媒体/引用和非空披露；同一候选的两个账号各有授权，单账号 unknown 不覆盖另一账号，Overview 仍优先提示对账。
- [x] /// 保留性审计：五种 canonical schema/哈希/refs 的测试与唯一 Registry 真源、既有授权历史/对账语义均有证据，核销对应 F6E 任务；未覆盖边界继续保留待办。
- [x] /// 同一源稿的公众号、X Thread、X Single 先全部冻结再反序审批/授权；单系列推进不伤其他系列，旧 v4 与 v5 同 Unit 时历史包可读而新 v4 授权保持旧闸门。
- [x] /// 审计 3.10/4.7/9.3：来源/能力/引用漂移只读投影，未证实新事实保持 incomplete，v5 本地授权核准确目标与账号；远端动作待 F7 验证而拒绝。
- [x] /// 不兼容来源/目标、缺真实 render 和断连模型均返回类型化不可用；模型失败不产生 Variant。
- [x] /// 对照已有 WeChat/Graphic/Video 精确 MaterialRevision、Text FactPackItem 引用和提交前撤权回滚回归，核销 F6E 3.7–3.9；复杂改写仍保持不可证实。
- [ ] /// 第二批：连续完成 Matrix/Production/Review 前端、路由性能、五形态隔离浏览器闭环、旧七场景、全套门禁与独立复核；批末集中更新验收记录并提交本地 `main`。
- [ ] /// 100 个 OpenSpec 条目保留作验收清单，不再按单条任务暂停、重复走完整流程或单独汇报。只有破坏性迁移、规格外持久对象、安全边界削弱或真实外部授权缺口才暂停并提出一个明确问题；不推送/部署/生产迁移，F7/F8 仍按顺序推进。

## 2026-09-30：F6E 后端第一批持续实施

- [x] /// v5 Review 只读投影按冻结 manifest 展示文字、图文卡片、脚本、检查及同系列差异；旧 v3/v4 保留。
- [x] /// Review 媒体端点按冻结 v5 MaterialRevision 引用读取真实字节，校验 live rights/hash/MIME；撤权与无关 revision fail closed。
- [x] /// Versions/Overview 保留同 Unit 多渠道系列与未知交付优先级，来源漂移投影为 stale，不创建状态表。
- [x] /// Matrix 只读 API 按 Brief/身份/Registry/现有 Unit/已转换 Opportunity 生成有界建议，未知表现与估值不伪造。
- [x] /// 模型辅助适配复用现有 Provider/LLMRun：当前 Master 的确定性适配作为有界输入；服务端验证并记录 canonical 建议，显式保存时核对 exact actor/source/Profile/Adapter/input/output；失败或过大输出不生成可信 Variant。归档预览/建议拒绝。
- [x] /// v5 冻结从真实 `LLMRun` 再验成功状态和安全摘要，单系列 Variant 版本差异输出稳定 ID 的 add/remove/move/modify 与 Profile/Adapter/refs 区段；公众号/X 双形态已有受控本地包路径。
- [ ] /// 第一批剩余：双连接保存并发、Matrix 估值诚实投影、Text 引用/声明成品包、全形态权限及历史回归与集中验收。

## 2026-09-30：F6E v5 Review 冻结展示

- [x] /// 对照 F6E 9.1 和当前 Review API，写失败回归：v5 文字预览显示冻结正文与检查；Graphic/Video 分别显示真实卡片/场景，不能冒充文本相似度；同 Unit 不同系列不互相作为 diff 前版。
- [x] /// 只在 v5 schema 分支读取冻结 canonical payload/render/checks，按 `(unit_id, variant_key)` 选择上一 Candidate；旧 v3/v4 分支不变，污染来源与投影列 fail closed。
- [ ] /// 定向及全后端、OpenSpec strict、Ruff/diff；同步 README/progress/findings、OpenSpec tasks 并本地提交，不推送/部署/归档。

## 2026-09-30：F6E v5 系列当前性、内容审批与本地包

- [x] /// 对照 F6E 8.7–9.2/9.8，先写真实 API RED：同一 Master 的 X 推串/单条候选反序审批、同系列新版阻断旧候选、污染的五个旧 FK 和篡改清单 fail closed，审批不改 Variant/Master。
- [x] /// 在现有服务抽取 schema-first v5 live validator：核对唯一 Variant source、系列 head、manifest/列一致、当前来源/检查/权利/证据/渲染；v3/v4 继续原校验。
- [x] /// 让 Approval 使用系列级当前性及提交前复核，Review 固定 v5 revision，不增加新表或批准时重写稿件。
- [x] /// 运行定向/全量后端、OpenSpec strict、Ruff/diff；据实更新任务、README/progress/findings 并仅本地 main 提交。交付授权/本地包在后端已接通，跨形态与浏览器验收仍待完成。

## 2026-09-30：F6E Variant → v5 Candidate 实时冻结

- [x] /// 对照 F6E 8.1–8.9 与现有 v4 路由，写真实项目 API 回归：同一来源多系列独立冻结、重复请求同一 Candidate、撤权/历史 Variant 无写入、五个旧来源指针为空。跨项目、并发竞态及五字段逐一污染仍属后续 8.x/11.x。
- [x] /// 从已授权当前 Variant 装载真实 Project/Unit/Identity/Brief/Fact Boundary、Master/Workflow、Profile/Adapter、refs/check/render 快照，并调用纯 `build_manifest_v5()`；只用服务端对象，不信任客户端清单。
- [x] /// 在现有 Freeze API 增加显式 Variant 分派和 expected hash；提交前重验 live gates，Candidate 仅填 Variant source FK，保持 v3/v4 路径原样。
- [x] /// 运行定向/全量回归、OpenSpec strict、Ruff/diff，按实际完成勾任务并同步 README/progress/findings；仅提交本地 main，不推送/部署/归档。

## 2026-09-30：F6E Candidate v5 冻结清单

- [x] /// 对照 v5 OpenSpec、v4 清单与当前 Variant 字段，先写纯 builder 的失败回归：完整血缘、哈希确定性、输入不别名、缺失字段/伪造 LLM 原始输出拒绝。
- [x] /// 在独立 `candidates_v5.py` 实现有界、不可变的 canonical manifest builder；不接 Candidate 写入、不复用 v4 Draft/Master 来源指针。
- [x] /// 定向及全量门禁，按覆盖范围勾 OpenSpec 8.x；同步 README/progress/findings 后仅本地 `main` 提交（8.x 尚需 DB loader/Freeze，故不提前核销）。

## 2026-09-30：F6E Variant 来源与成品投影闸门

- [x] /// 先以失败回归锁定：已有 Variant check pass 不代表来源 Master 的 Brief/Boundary/Identity 和其 checks 已 current；Adapter 仅可验证确定性的本地包投影，不得声称 ZIP 或远端效果已生成。
- [x] /// 增加只读 source gate（复用 Master 现有 check/readiness）、追加式 variant_package projection check；只有二者及其它 required checks 均通过时 `ready=true`，不要求 channel-neutral Master 获得 v4 直接 Freeze 资格。
- [x] /// 定向/全量测试与 strict/Ruff/diff 后，按真实范围核销 F6E 检查任务；同步 README/progress/findings 并只在本地 main 提交。

## 2026-09-30：F6E 公众号封面精确引用

- [x] /// 先写失败回归：公众号 Text Variant 绑定项目共享图片的 exact MaterialRevision/hash/字节/公开权利后，Profile 不再因缺封面阻断；伪造 hash、撤权或无项目可见性零写入。
- [x] /// 仅在 `wechat.article.v1` 开放受限 `cover` ref，复用现有 ProjectMaterialReference/WorkflowOutput 与 live bytes 验证；保存和检查共享同一校验，提交前重验，Text Master 无素材路径不改。
- [x] /// 回归、全套门禁、文档与本地提交；不提前核销全部 inherited refs/包/审批任务。

## 2026-09-29：F6E Variant Profile/Evidence/Rights 检查

- [x] /// 对照 F6E 7.2–7.5 和 Registry published Profile，先写检查 RED：X 简单正文的精确 Profile/无素材权限通过；公众号缺必需封面保持 blocker；撤权证据/图片不能保持 pass。
- [x] /// 在既有 ChannelVariantCheckRun 实现 profile、evidence、rights 的追加式结果与诚实 coverage；不把来源 Master 的语义审查或远端能力冒充已执行。
- [x] /// 运行定向及全量回归、Ruff、OpenSpec strict、diff-check，按实际完成范围勾任务并更新 README/progress/findings，只提交本地 main。

## 2026-09-29：F6E Variant 历史检查的实时漂移投影

- [x] /// 对照已批准的 F6E 任务 3.10/7.5 与现有项目级检查读取，先补失败回归：同系列新版本、源 Master 更新、Profile 退役和 Evidence 撤权不得沿用旧 pass。
- [x] /// 最小化复用现有 Master、Profile、FactPack 和 Material 验证，只在读取时投影 stale，不改写历史 CheckRun；漂移后拒绝重新执行旧检查。
- [x] /// 跑全量后端、Ruff、OpenSpec strict、diff-check，更新进度/发现/README；此批只是 3.10/7.5 的一部分，暂不勾任务。

## 2026-09-29：F6E 独立规格复核通过，进入 backend-first apply

- [x] /// 核对 `main@6f5e022`、F6D 79/79、F6E 六份 delta 与独立复核结论，核销 F6E 0.2；不将外部记录的门禁数字冒充本地重跑。
- [x] /// 先做 append-only Variant 四表及 Candidate v5 nullable FK；以 RED→GREEN 回归验证系列唯一性、精确 FK、SQLite up/down/up 与历史降级拒绝。
- [x] /// 建立 Text 三目标保守确定性适配、Variant 系列 CAS 写入和新增 citation 的精确证据引用；全套回归在后端目录运行，未完成的素材/来源引用仍拒绝写入。
- [x] /// 增加 non-durable adapt-preview，只对精确当前 Master 和 published Profile 给出受控 Text 建议，确认无 Variant/Event 写入。
- [x] /// 将 Graphic v2 已验证的逐画布最终 render 映射为小红书有序图文卡片和精确 MaterialRevision；缺 render、撤权、字节或顺序不符时 fail closed。
- [x] /// 为 Video v2→抖音口播脚本开放无媒体/无定时内容的确定性子集；未映射 B-roll、配音、字幕及叠字一律拒绝，绝不声称已生成视频。
- [x] /// 先写 Video v2 shot_source→spoken_script B-roll 精确引用的失败回归，覆盖预览/保存、撤权、缺字节与无部分写入。
- [x] /// 仅映射可证明的 shot_source 素材；服务端验证项目可见、媒体类型、hash/字节/公开权利，并在事务提交前复核。其他音轨、定时字幕和成片仍拒绝；根据镜头计划时长生成标明 estimated 的字幕。
- [x] /// 复跑定向及全后端、Ruff、OpenSpec strict、diff-check；更新 README/progress/findings，核销真实完成的 OpenSpec 任务并本地提交。
- [x] /// 先写 Variant schema/content CheckRun 的失败回归：项目权限、append-only、精确 payload/context/ref 输入哈希和最新 blocker 覆盖旧 pass。
- [x] /// 复用既有 CheckRun 表添加项目级运行/投影 API；未实现的 profile/rights/evidence/render 检查继续显式 incomplete，禁止借 schema pass 冒充可冻结。
- [x] /// 完成定向/全量门禁和本地提交，之后继续补完整 Variant live gate 与 Candidate v5。
- [ ] /// 实现 exact Registry/profile 的 canonical adapters，再接项目级 Variant CAS/refs/checks 和 Candidate v5；任何额外持久对象或安全边界削弱先停下修规格。
- [ ] /// 完成 Review/Approval/本地包、Matrix、前端与隔离浏览器验收；保留 v3/v4 和未知发布状态，不声称 F7 远端能力已验证。
- [ ] /// 最终门禁和独立复核后仅本地范围提交；主规格同步/归档、push、deploy、生产迁移另行授权。

## 2026-09-29：F6E 前置门槛核销（不进入 business apply）

- [x] /// 对照 F6C 74/74 独立复核记录和 F6D 79/79 独立复核结论，核实 F6E 0.1 的前置条件。
- [x] /// 只勾 F6E 0.1，更新 README/progress/findings；保留 F6E 0.2 独立 SPEC re-review 门槛和全部业务任务未执行。
- [x] /// 运行 OpenSpec strict、diff-check 并范围提交本地 main；不触碰用户源包、业务代码、迁移或外部发布。

## 2026-09-29：F6D 独立复核收口与 F6E v5 来源字段窄修（仅规格）

- [x] /// 核对外部复核结论与当前 ContentAsset/Master 字段、F6D/F6E 标准 change，明确 v5 的来源 FK 和工作流血缘。
- [x] /// 据独立 APPROVE 关闭 F6D 8.4，并在 F6E design/tasks/相关 delta 中写死四个 legacy source FK 及 workflow_run_id 的 v5 规则；不改业务代码/迁移。
- [x] /// 同步 README/progress/findings/验收记录，运行 OpenSpec all-strict、保留性核对和 diff-check，按范围本地提交；F6E business apply 等窄范围独立 SPEC re-review。

## 2026-09-29：F8 生产身份与发布历史验收契约预审（仅规格）

- [x] /// 对照 F8 active OpenSpec、现有 User/auth 模型与 F5B PublishedContentRecord 真源，核实生产身份映射和本地交付到学习链路的实际前提。
- [x] /// 仅在 F8 design/tasks/主 delta 写明身份映射前置决策及本地包不得自动生成已发布历史；不选未授权的持久对象，不改业务代码。
- [x] /// 同步 README/progress/findings，运行 OpenSpec all-strict 与 diff-check，提交本地规格检查点；F6D/F6E 门槛保持原状。

## 2026-09-29：F7 搜索来源地址安全契约预校准（仅规格）

- [x] /// 对照 F7 design/tasks/Capability delta 与 `MaterialRevision.source_url`/`create_revision()`，确认“记录来源 URL”和“禁止签名抓取 URL”之间的实施歧义。
- [x] /// 只在 F7 active OpenSpec 区分可公开稳定引用地址与临时获取地址，明确后者不得进素材/审计/响应；同步 README/progress/findings。
- [x] /// 运行 OpenSpec all-strict、diff-check 与保留性检查，只提交本轮规格文档到本地 main；不实施 F7 业务代码。

## 2026-09-29：F6D 独立复核修复与 F6E 当前性规格补丁

目标：只关闭复核 D1–D3 和 E1；F6D 8.4 与 F6E business apply 仍需外部定向复核。

- [x] /// 对照当前 main、F6D/F6E active OpenSpec 与实现，复现预览漏显、跨轨道媒体槽位重复和非法枚举类型。
- [x] /// 在既有 F6D 测试/隔离浏览器脚本中增加回归，再最小修正前端冻结预览和 Video 文档服务；保持 v1/Graphic/Text 原路径。
- [x] /// 在 F6E design/tasks/主 delta/Review/Project delta 规定 v5 按稳定 Variant 系列判断当前性，并增加跨系列/跨 schema 场景；不写 F6E 业务代码。
- [x] /// 跑定向与全量门禁，更新 README/progress/findings 和验收记录，只提交本轮文件到本地 main；保留独立 re-review 门槛。

## 2026-09-29：F7 既有字段的秘密脱敏契约审计

- [x] /// 读取 F7 标准 proposal/design/tasks/主 delta 与现有 MaterialRevision、ConnectorEndpoint、Delivery 代码，核实可能保存 raw prompt、签名 URL、异常文字的字段。
- [x] /// 只将这些既有字段的安全投影/禁止写入原值约束补入 F7 design/spec/tasks 与 README/progress/findings，不新增表或提前实施 F7。
- [x] /// 复跑 OpenSpec strict、diff-check，核 F6D/F6E 门禁未变；仅提交本地规格检查点。

## 2026-09-29：F6E 六份 delta 本地保留性复核

- [x] /// 对照 F6E 六份 delta、FE-F4 canonical 授权契约与当前设计，寻找与人工本地包/远端能力边界相冲突的措辞。
- [x] /// 只修 FE-F4 delta 的 v5 授权语义，明确本地人工动作与远端效果的不同能力闸门；同步 findings/progress/README。
- [x] /// 复跑 OpenSpec strict 和 diff-check，检查任务门禁不被提前勾选，仅将规格检查点提交本地 main。

## 2026-09-29：F6E 前置基线与旧 V1 验收审计

- [x] /// 复核当前 main、既有 Unit/Master/Candidate/Review/Delivery/Registry 代码与 Alembic head；记录仍未落地的 Variant/v5 边界。
- [x] /// 并行运行当前后端全套和前端 build/FE-P1，记录真实测试与路由预算；仅作为 F6E apply 前基线，不算 F6E 功能验收。
- [x] /// 对 superseded V1 七个 Scenario、PRD §15 15 条与 §16 30 Topic/指标/发布门槛逐项映射到现有真源和 F6E/F7/F8 后续验收，不将文档映射算完成。
- [x] /// 证据足够后只勾 F6E 0.3/0.4，更新 README/progress/findings，复跑 strict/diff 并本地提交检查点；保留 F6D 8.4 与 F6E re-review 门禁。

## 2026-09-29：F6D→F7 Provider 移交核销与 F6E 规格检查点

- [x] /// 在当前 main 核对 F6D 4.5 文字、F7 标准规格/任务与真实 Provider 未实现边界，确认“移交已写入”不等于“F7 已实现”。
- [x] /// 仅将 F6D 4.5 作为文档移交勾选；更新验收记录、README 和进度/发现，保留 8.4 独立复核未完成。
- [x] /// 对 F6E 五项修订与 F6D 移交跑 OpenSpec all-strict、diff-check、文件范围审计，并仅将本轮范围文件本地提交；F6E business apply 仍须 F6D 8.4 与 F6E re-review。

## 2026-09-29：F6E 独立 SPEC 复核修订（仅规格）

目标：针对独立复核提出的五个需求缺口修正标准 active change，保留原有场景；F6D 独立实施复核通过前不执行 F6E 业务 apply。

- [x] /// 核对旧 V1 change 元数据、现有 Registry 五种 published form、ContentAsset source 指针及 LLMRun 真实字段。
- [x] /// 在 proposal/design/tasks/相关 delta 定义 superseded 验收来源、版本化 canonical Variant payload、首批 Master→form 矩阵、v5 source-pointer/投影列及 LLMRun 安全血缘。
- [x] /// 同步 README/progress/findings；运行 OpenSpec all-strict 30/30、旧场景保留审计与 git diff --check；不改业务代码/迁移。
- [ ] /// 获取修订后独立 SPEC re-review；F6D 8.4 独立实施复核通过前不进入 F6E business apply。

## 2026-09-29：F6D WAV 精确音频闭环

目标：让有效 RIFF/WAVE 录音在 Video v2 的保存与本地包中保持准确的 MIME、字节/哈希和文件名，不放宽素材权利或通用未知格式闸门。该批按 F6D active OpenSpec apply；当时 4.5/8.4 尚未勾选，后续 4.5 已按 F7 移交证据单独核销，8.4 仍待独立复核；不启动 F6E 业务 apply。

- [x] /// RED：在 `apps/api/tests/test_material_library.py` 添加真实 RIFF/WAVE 与 WEBP/未知 RIFF MIME 回归；在 `apps/api/tests/test_f6d_video_documents.py` 添加临时字节的 Video v2 录音精确引用保存回归。确认当前失败原因是无声明的字节嗅探返回 octet-stream。
- [x] /// GREEN：仅在 `apps/api/app/services/materials.py` 的既有嗅探器识别 RIFF/WAVE，并保持 WEBP/未知 RIFF 不误判；复跑定向测试。必要时在 `apps/api/app/services/production_packages.py` 对 WAV 同步使用 `.wav` 扩展名。
- [x] /// 隔离验收：将 `apps/web/scripts/fe-f6d-browser-acceptance.mjs` 的音频 fixture 改为真实 WAV，在全新临时 DB/素材目录走 Video v2→Candidate→Review→ZIP 并核对音频成员字节；复跑全后端、前端构建/预算、OpenSpec strict、Ruff、diff-check。
- [x] /// 更新 `README.md`、`progress.md`、`findings.md`、F6D 验收记录，只提交本项范围的本地 main 文件；独立实施复核仍需外部证据。

## 2026-09-29：中断后规格检查点收口

- [x] /// F6D 验收隔离修补：先用定向测试复现素材根目录未隔离，再为 API 验收进程配置临时素材目录并在浏览器脚本中强制校验 DB/素材同一临时父目录。
- [x] /// 在独立临时 DB/素材目录复跑 F6D 浏览器验收与必要门禁，更新验收记录和 README；不清理旧共享素材，不把自身复核当独立复核。

- [x] /// 重新读取一次性目标，核对当前 main/dirty scope 与 F6D/F6E/F7 active tasks，保留用户原始包不动。
- [x] /// 对照 F7 原包任务与标准 change：原任务行全部逐字保留，新增九条安全/执行门禁；不把此审计当 F7 实施。
- [x] /// F6E 规格修订完成后复跑全库 OpenSpec strict 30/30、diff-check，核对暂存范围并提交本地文档检查点。
- [ ] /// F6D 独立实施复核仍待外部入口/用户结论；其未过前不进入 F6E 业务 apply。

## 2026-09-29：F6E 原包范围保留复核

- [x] /// 复查用户一次性总目标、原始 F6E 102 项计划与当前标准 96 项 change，核对已经发布的 X 内容形态。
- [x] /// 将原包明确要求的 `x/single` 受控适配、单独验收与 source_kind/edit summary 血缘补回标准 F6E 规格；适配器完成前仍 fail closed，旧 `x_thread` 不变。
- [x] /// 复核其余原包要求映射、全库 strict 30/30 和 diff-check，并记录本轮纯规格检查点。
- [ ] /// F6D 独立实施复核通过后再做 F6E 独立 SPEC review 与业务 apply；不把本轮规格校准当成功能完成。

本轮仍不修改 F6E 业务代码、迁移或用户原始包，不推送、部署、归档或同步主规格。

## 2026-09-29：F6D 收尾门槛与 F6E 规格基线复核

- [x] /// 核对本地 main、F6D 实际任务数、F7 已承接的真实 Provider 义务；F6D 独立实施复核仍未获得，不虚报完成。
- [x] /// 对照现有 Channel Registry、账号/Unit/Master、交付授权代码审计 F6E 六份 delta；只修正规格，不改业务代码。
- [x] /// 明确 `x/thread` 与 `x/single` 已发布但适配器未实现、`x_thread/thread` 仅旧版 fallback 且 v3/v4 行为不变，以及 v5 跨渠道授权须按 Variant 目标分派。
- [ ] /// 获得 F6D 实施独立复核并处理结论；之后完成 F6E 独立 SPEC review，再进入 F6E 业务 apply。
- [ ] /// F6E 实施/验收后依序推进 F7、F8 与全链路；缺真实凭据时仅能标记未验证。

本批只做 F6E 标准规格校准及 strict/diff 门禁；F6D 保持 77/79，不勾 F7 真正 Provider 任务，也不提前实施 F6E。原始包、主规格、业务代码、生产环境均不动。

## 2026-09-29：North Star 完整剩余开发（目标进行中）

- [x] /// F6D 6.9/6.10/6.11：隔离浏览器验证 Video v1 显式预览/追加修订、稳定 ID diff、历史/归档只读，以及 409 后保留本地草稿；后端 CAS/警告仍是最终闸门。
- [x] /// F6D 7.1–7.11：后端 Video/旧版本回归与隔离浏览器闭环已证实精确媒体、成片失效、检查、Candidate/Review/审批/本地 ZIP、撤权阻断和未验证 Provider；前端路由预算通过。F7 真正 Provider 接收不计入 F6D。
- [ ] /// F6D 8.x：保留独立实施复核待办；补最终门禁/验收记录，范围提交本地 main，不推送/部署/运行生产迁移或提前归档。
- [x] /// F6D 4.3/6.6–6.8：全角色项目精确素材 picker、MP4 字节/hash 限额预览、诚实能力状态与手工输入绑定确认 UI；模型 8/8、TypeScript/Vite/FE-P1 PASS。完整浏览器验收仍在 7.x，累计 56/79。
- [x] /// F6D 6.4/6.5：纯模型 RED→GREEN 界定 track/item 时间边界、精确 media refs、字幕 cue 重叠/SRT 导入及旧 render 失效；类型化时间线、配音/音乐/封面、字幕与叠层控件已接通。模型 7/7、TypeScript/Vite/FE-P1 PASS；累计 52/79。
- [x] /// F6D 6.3：为镜头 source 精确引用先加 RED 顺序测试，再实现项目共享素材选择、rights/kind/hash gate、景别/转场/用途/脚本关联；镜头重排与删除同步重排 refs。模型 4/4、TypeScript/Vite/FE-P1 PASS；累计 50/79。
- [x] /// F6D 6.1/6.2/6.12：先为 Video v2 typed draft、稳定脚本/镜头 ID、重排与变更后成片失效写模型 RED 测试，再实现纯模型并接入 Video-only lazy Studio；旧 v1 只读待显式升级。模型 3/3，TypeScript/Vite/FE-P1 PASS；累计 49/79。
- [x] /// F6D 4.1/4.2：project-scoped Video/TTS/ASR capability 先 RED（端点 404），后在既有 Project Assets 路由实现 configured/executable/verified 均 false 的真实状态；三种 Provider 形态请求 typed unavailable 且不回显输入 secret，MaterialRevision/Master/项目引用均不增加，跨项目不可读。Video/Graphic 能力定向 2 passed；全量门禁待本批复跑。
- [x] /// F6D 4.4/4.6/4.7：在真实 Video v2 本地包链路加伪造 renderer origin/version、错误类型、缺字节和字节篡改的成片负向验证；payload/context/source/profile 变更分别改变当前输入 hash，旧成片不得误冻结。跨时钟重复打包暴露 ZIP 条目时间戳导致字节不确定，复现 RED 后固定 v4 ZIP 元数据，定向两例 GREEN；全后端门禁进行中。
- [x] /// F6D 5.3：精确 source ref 替换、Brief context 修订分别改变新 Master render-input hash；旧检查随 Brief 变化 stale，素材撤权使 rights stale/冻结不可用，历史 Master hash 不变。定向回归通过；全量门禁与交付文档在本批收尾复跑。
- [x] /// F6D 5.4：stable-ID Video diff 与 Project 路由先 RED 后 GREEN；脚本/镜头/轨道/片段/字幕/叠层及媒体/上下文差异均按 v2 schema 分派，Video/Graphic/Text 定向 83 passed；Candidate Review 冻结差异仍在 5.5。
- [x] /// F6D 5.5：两份自洽冻结 Video v2 Candidate 的 Review preview/diff 先 RED 后 GREEN，准确显示脚本/镜头/时间线/字幕/叠层/成片与稳定 ID 改动，无整片文本相似度；Video/Graphic/既有 Review 68 passed。完整后端/规格门禁待本批复跑。
- [x] /// F6D 后端闭环：隔离 fixture 真实保存 Video v2、手工输入绑定 MP4、检查、冻结 v4、Review、带 warning 处置的审批、授权与 byte-exact ZIP；撤权/篡改/新 Master 后旧授权拒绝，无 Draft 回退或远程调用。全后端 1004 passed/2 skipped，跨形态定向 255 passed；5.6–5.10 已据证完成，累计 36/79。
- [x] /// F6D 3.5–3.9：派生 API 先见 404 RED，再验证“只改镜头标签”也曾错误通过，现要求精确新素材；long-to-short/aspect-ratio/shot-regeneration 均仅以具体 v2 结果创建追加子修订。来源 ID/hash/context/head 与 request 指纹、server-only derived_video 血缘已验证，Provider 503 无 Master/素材写入；全后端 1005 passed/2 skipped、strict 30/30、相关 Ruff/diff PASS。累计 41/79。
- [x] /// F6D 5.1/5.2：对有效/空 Video v2 先测结构/时间线缺口 RED，再接入 append-only CheckRun；补精确 published profile 与身份覆盖状态，未验证画面/音频不报 PASS。定向 46 passed、全后端 998 passed/2 skipped、strict 30/30、Ruff/diff PASS。5.3 的完整 source/context freshness 尚待验收。
- [x] /// F6D 2.5/2.6/2.9：旧 Video 仅保留可证脚本与镜头 ID/顺序；预览不伪造画幅/时间线；专用 API 要求完整 v2 文档、警告确认和精确 refs，追加式 CAS/幂等且不继承旧 render。定向升级 8 passed，另有候选历史哈希与浏览器验收留在 2.7/7.x。
- [x] /// F6D 3.2：明确音轨片段必须有精确素材版本；未绑定 audio/music 两例先 RED，修复后定向 34 passed、全后端 986 passed/2 skipped、strict 30/30、相关 Ruff 和 diff-check PASS。空音轨、全片语音/音乐、字幕重叠回归通过。
- [x] /// F6D 冻结 Video v2 候选增加独立读时一致性校验：规范化文档、Master payload hash、精确成片 ref/MP4、已冻结 profile 与 render-input hash、人工 attestation；先 RED 后 GREEN，后端全量与 strict 门禁通过。Review 的冻结读已保护，Package/浏览器全链路仍待后续任务验证。
- [x] /// F6D 3.1：服务端拒绝镜头时长超过时间线，或绑定镜头的片段时长超过镜头；先观察两条 RED，再确认定向回归通过，保留空草稿合法性。
- [x] /// F6D 3.3：叠层文字必须非空，x/y 必须同时存在并在 0–1 内；封面继续由 Master 保存时的 image/字节/权利闸门约束。负向先 RED，正向与三形态相关定向回归通过。
- [x] /// F6D 3.4：从已保存 canonical Video v2 文档确定性投影脚本、镜头、时间线、语音、字幕、叠层、音乐、封面；明确 `local_assembly_preview` 和未验证成片，不把结构预览当视频渲染。
- [x] /// 从 `main@361265d` 与 F8 用户源包出发，审计 auth/startup/health/metrics/media/worker 当前实现，区分已有功能与生产缺口。
- [x] /// 以 `openspec-propose` 归位 F8 proposal/design、新 Production Readiness 规格和 Settings delta；为原十条要求补可验收场景及当前代码边界。
- [x] /// 审核 F8 原 91 项任务保留与八项现状安全门禁，运行全库 OpenSpec strict 30/30 和 diff-check；仅规格检查点准备本地提交。
- [ ] /// F8 业务 apply 须在 F6C 独立复核及 F6D/F6E/F7 前序验收与项目规则确认之后；不得把规格存在当成生产就绪。
- [x] /// 对照真实 `main`、F6C/F6D/F6E 已有标准 change 和 F7 用户原包，确认当前不重复实施 F6B，也不越过 F6C 独立复核门槛。
- [x] /// 以 `openspec-propose` 将 F7 源稿归位为标准 proposal/design、五份 delta 与任务，补齐场景、精确验证、Project 素材引用和全链路 Provider 脱敏。
- [x] /// 验证 F7 源稿十条长期要求逐项保留、全库 strict 和 diff-check；业务代码/迁移未触及，规格检查点已本地提交 `361265d`。
- [x] /// 恢复 F6C 独立复核并关闭 7.10。
- [x] /// 对 F6D 标准 change 做独立 SPEC review；将 Video Profile、精确媒体 slot、受信派生、显式升级和 frozen integrity 五项缺口回写 proposal/design/delta/tasks。
- [x] /// 复跑 F6D 全库 strict、保留审计与 diff-check，交独立规格复核；通过后再按 backend-first 实施 Video v2。
- [ ] /// F6D/F6E/F7 依次完成各自规格复核、前序验收和实施门禁；不得因 F6C 通过就将后续能力视为已实现。
- [x] /// 读取一次性开发目标与总包；对照真实仓库，确认 F6B 已从总包旧基线 131/162 推进为本地 `main@670dd49` 的 162/162。
- [x] /// 按 `openspec-propose` 将 F6C 图文工作台源包校准为标准 active change，补齐 Scenario、显式 v1 升级、冻结画布顺序、现有渠道分类与能力可用性边界。
- [x] /// 跑 F6C 标准 change 和全部 OpenSpec strict；建立独立实施计划。
- [x] /// 按 `openspec-apply-change` 从 F6C 0.1 起完成真实基线、后端/前端/浏览器/门禁，逐项更新任务、进度和发现。
- [ ] /// F6C 通过后依次机械校准并实施 F6D、F6E、F7、F8，最后按 North Star 全链路证明；每个模块不以局部测试代替完整验收。

当前 F6C 为 74/74：隔离 SQLite/浏览器闭环和独立 SPEC/后端/前端复核均有记录；ChatGPT 在公网连接恢复后实际读取 `main@2891bac`，定向复核给出 SPEC/前端 APPROVE，后端前轮 APPROVE 因未改业务代码继续有效。最终新跑全后端 951 passed / 2 skipped、TypeScript/Vite/FE-P1、OpenSpec strict 30/30、F6C 相关 Ruff PASS。真实 Provider 接收/许可/项目关联/响应脱敏仍属 F7 未实施义务；F6C 仅证明未验证能力 fail-closed。主规格同步/归档未获单独授权，不 push/deploy/生产迁移。全量 Ruff 另外发现 23 个既有、非 F6C 范围问题，不能误记为全库 Ruff PASS。

F6D 独立规格审阅已读到 `main@34ef5af` 和现有后端，判定五项实施前边界缺失。修订后 ChatGPT 再次读当前 diff，返回 SPEC APPROVE / DONE；全库 strict 30/30、diff-check 通过。已有总目标授权覆盖 F6D apply；仍须按后端优先、各项门禁执行，迁移及后续阶段尚未启动。

独立复核第一轮后定向修复：/// F7 Provider 执行/结果响应脱敏与负向测试写入后续标准化义务；/// GraphicStudioModel 改为仅 Graphic 运行时动态载入，并由 bundle gate 验证通用 Production/Text/Video 静态闭包；/// 画布选中态加 aria-pressed。前端 build/FE-P1 与模型 20/20 已复跑 PASS；等待第二轮独立复核，不提前勾 7.10。

第二轮复核因 ChatGPT 连接器连续 internal error 而 NOT_VERIFIED；工作区隧道重建遇 Cloudflare API EOF，虽本地诊断恢复在线，ChatGPT 仍未能读取当前文件。保持 7.10 未完成；先提交已验证的规格/前端修补检查点，恢复真实独立读取后再复核并决定是否进入 F6D。

/// F6D 仅做标准 OpenSpec propose：从源包生成 Video v2 proposal/design/四份 delta/73 项 tasks，补 Scenario 与 Provider 真伪/渲染血缘边界；全库 strict 27/27。F6C 独立复核和本轮用户规则要求的明确 apply 确认之前，不运行 F6D 业务代码。

/// F6D 规格复核追加无假衍生约束：派生子修订必须携带明确编辑或确定性本地变换后的有效 v2 内容，未验证 Provider 不得以“已转换”写入；本地 strict 27/27。ChatGPT 模型加载失败，F6C 独立复核继续待验。

/// F6E 仅做标准 OpenSpec propose：读取用户总包、当前 canonical 与 Unit/Master/Registry 模型，将 ChannelVariant/Matrix/Candidate v5 归位为 proposal/design/六份 delta/96 项任务；保留 active V1 交付七场景，锁定 Matrix 不提前创建 DeliveryTarget。全库 strict 28/28 与 diff-check 通过；独立 SPEC review、F6C/F6D 门禁及用户明确确认前不 apply。

边界：源总包目录/ZIP 保持原样；F6B 主规格同步/归档、后续各 change 的 canonical/归档仍须另行授权；不 push、deploy 或运行生产迁移。用户已要求以后续方案连续开发，不再把 F6C 之后缩减为仅规划。

## 2026-09-29：FE-F6B FINAL-CLOSE（131/162 起点）

- [x] /// 复核 active OpenSpec 31 项与当前本地 main；只复用临时 SQLite 和现有 fixture/API 建验收数据，不接触生产。
- [x] /// 用真实 Text Studio 页面核对 v2 payload、图片/图表精确引用、FactPack 引文绑定/解绑与边界漂移、AI 五操作、升级、Draft seed、diff、Review/Approval/ZIP；完成一项才勾一项。
- [x] /// 跑 legacy `/workspace`、历史 v1、Graphic/Video、F2–F6A 定向及浏览器回归；发现缺口只做范围内最小修复。
- [x] /// 跑全后端、前端构建与路由包预算、OpenSpec strict、Ruff、diff-check，核实零新 migration；留可复查的隔离验收记录。
- [x] /// 按可用评审能力复核 SPEC、后端、前端与性能，更新 README/progress/findings 和真实任务数；无独立 reviewer 不虚报 APPROVE。
- [x] /// 记录最终文件/门禁/限制并在本地 main 提交 F6B；原始规格包和 ZIP 保持未跟踪，主规格同步/归档另行授权。

本轮不扩产品能力，不新建迁移，不推送/部署/运行生产迁移，不启动 F6C/F6D。主规格同步/归档仍需单独授权；F6B 代码留在本地 main 未提交工作区。

## 2026-09-29：FE-F6B Professional Text Studio Frontend（本轮继续）

- [x] /// 复核后端 v2 接口与前端 F6A 边界，先把 Text 的 typed document/ref/edit state 接入 ContentMasterPanel；Graphic/Video 保持原路径。
- [x] /// 先写纯模型/适配器定向回归，再实现 Text-only lazy TipTap、稳定 block ID 与显式本地 dirty/save；不持久化 ProseMirror JSON。
- [x] /// 接项目素材、精确证据引用、AI 建议与 provenance、只读身份/检查、历史升级/diff，逐项用真实 API 契约验证。
- [x] /// 测量 Production/Text 路由包边界，运行 TypeScript/Vite、FE-P1、后端定向/全量及 strict/diff 门禁；只对真实完成项勾 OpenSpec。
- [x] /// 更新 README/progress/findings，报告实际任务数与前端 PASS/PARTIAL；15–20 完成前不开始最终浏览器验收。

本轮前端 15–20 已完成，累计 131/162；22 浏览器验收已开始但未完成，5.6/6.1/6.3 与 21–23 保持未勾。下一批先建有权利的共享素材和冻结 Fact Boundary 隔离夹具，再完成精确引用与完整浏览器/跨模态回归。

本批不新增 migration，不 commit/push/deploy，不同步 canonical/归档，不启动 F6C/F6D；Workflow 与 Text 保存状态必须独立。

## 2026-09-29：FE-F6B Backend Milestone B（任务 11–14，本批继续）

- [x] /// 先读取并锁定 AI suggestion、receipt/provenance、structured diff、Review/package 的现有实现边界，记录本批 RED 测试入口。
- [x] /// 复核上一批过早勾选的 11–14，先以伪造血缘、冻结预览完整性和 ZIP 字节回归暴露缺口，再逐项恢复完成标记。
- [x] /// 先写定向回归：项目/单元权限、当前 v2 基础、选择范围与 patch 有界性、suggestion 不写 Master。
- [x] /// 实现 `text_master_ai`：五种操作、服务端 patch 校验、模型使用上下文、服务端 LLMRun receipt；不接受模型自报 provenance。
- [x] /// 先写定向回归：receipt 精确绑定、连续 hash chain、伪造/失败/外来/断链/后续修改与无 AI 内容。
- [x] /// 接入 v2 保存的 receipt 验证与 compact edit provenance；保持 append-only、CAS、旧 v1/v2/v3/v4 兼容。
- [x] /// 先写定向回归：v2 stable-ID add/remove/move/modify、refs/provenance/context 分组与只读权限。
- [x] /// 实现 bounded `text_master_diff` 与 project-scoped diff route；不新增 diff 表。
- [x] /// 先写 v2 Candidate/Review/package 端到端回归，再修复 deterministic frozen render、exact citations、schema dispatch 与本地包闭环。
- [x] /// 运行 Backend Milestone B 定向/全量后端、strict、Ruff、diff-check；不启动前端、migration、commit、push、deploy、canonical sync 或 archive。


## 2026-09-29：FE-F6B Backend Milestone A（任务 9–10，本批继续）

- [x] /// 为 v2 建立按检查种类解析的要求、精确 profile 与输入哈希；保留 v1 历史语义。
- [x] /// 将执行、当前投影、Candidate v4、历史包及 warning 处置统一到要求解析；先写定向回归并验证失败。
- [x] /// 实现结构、事实、身份、渠道与条件性可发现性检查，诚实报告不可用/截断/模型使用权限。
- [x] /// 跑定向及全量后端、OpenSpec strict、Ruff、diff-check；逐项更新 9/10 任务和进度。
- 本批只做后端 Milestone A；不启动 AI、前端、migration、F6C/F6D，不推送/部署/运行生产迁移。

## 2026-09-29：FE-F6B apply（用户明确授权，本地 main）

- [x] /// 本批先在text_documents统一纯转换，测试Markdown权威、稳定hash、未知结构显式warning与exact refs；两个入口不得另起parser。
- [x] /// 独立upgrade preview/commit验证最新v1父版本、payload/context CAS及先幂等回放；generic跨schema保护不放宽。
- [x] /// Draft seed复用同转换器，仅替换内容转换，保留Run/Workflow/Step/Attempt/最新Draft与媒体证据证明；测试两入口一致。
- [ ] /// 依次关闭专业checks（A）与AI/receipt/diff/Candidate/Review/package（B）；A/B未绿不动前端。
- [x] /// 阶段全量后端/定向/strict/Ruff/diff及只读复核，记录实际任务与未闭合项；零迁移、不推送部署。

- [x] /// 核对已审标准包/main@ca52aa5/现有文档改动，运行 fresh backend/build/budget/strict/Ruff/diff 基线；保留源包及 ZIP。
- [x] /// 先 RED 后实现有界 Studio Document、Unicode/list/citation 精确定位、确定性 renderer/hash 和 schema-aware adapter；保留 v1/Graphic/Video。
- [ ] /// 接入 append-only v2 save、显式 upgrade、Draft seed、schema/profile checks、AI suggestion/receipt、structured diff 和冻结 Review/package；零新表/迁移。
- [ ] /// 接 Text-only lazy TipTap editor、素材/证据/AI/check/history UX，保持 Workflow/Master dirty/save 独立。
- [ ] /// 完整回归、性能、浏览器及独立只读评审后记录实际完成项；canonical 同步/归档另待授权，不启动 F6C/F6D。
- 仅主 Agent 写代码；沿用用户要求直接 main，不创建隔离分支。规格内定向测试已明确要求并随 apply 授权，不生成无关示例或测试。
- 已接 generic v2 save/refs、共用 converter、显式 upgrade 和 Draft v2 seed，任务51/162；checks/AI/diff/Review 与前端仍未完成，后端 A/B 门禁不能提前算通过。

## 2026-09-29：FE-F6B SPEC REVIEW（仅规格，apply 未授权）

- [x] /// 核对 main@ca52aa5、F6A canonical/archive 与原始包；完整读取 proposal/design/tasks/四份 delta 和现有三份主规格。
- [x] /// 对照实际 Master/LLMRun/编辑器/Review/package/预算，校准引用定位、转换、AI 血缘与检查 currentness；原始包不改。
- [x] /// 将校准包归位 openspec/changes/fe-f6b-text-production-studio，审计三份 MODIFIED 的旧要求/场景保留。
- [x] /// 独立只读 SPEC/后端契约/前端与包复核，运行 strict/保留审计/diff-check，更新 README/进度/发现后等待单独 apply 授权。
- 禁止业务代码、测试代码、migration、canonical 同步、归档、commit、push、deploy；162 项实施任务保持未执行。

## 2026-09-29：FE-F6A 五份主规格同步与归档（用户已授权）

- [x] /// 核对 main d060428、tree clean、4/4 artifacts、214/214 tasks；保存五份delta、四份旧主规格和原始包校验基线。
- [x] /// 同步新增 production-content-master 及 FE-F2/F3A/F3B/F4 四份更新，归档标准change；旧要求/场景完整保留，补正式Purpose。
- [x] /// 核对归档与五份canonical，更新README/验收/进度/发现，全量strict24/24和diff-check通过，准备已授权白名单本地提交。
- 本轮只改规格和文档，不改业务代码，不push/deploy/生产迁移，不启动F6B或后续方案。

## 2026-09-28：FE-F6A FINAL-CLOSE（完成214/214，仅本地main收尾）

- [x] /// 核对114/214与既有165项回归，补后端剩余输出支持、检查/权限、冻结并发/历史及迁移SQLite往返和PostgreSQL约束；不扩能力。
- [x] /// 按v3/v4分派Review Preview/Changes/Checks；三形态结构化diff，只有text可有相似度；Versions/Overview加入真实Master，Unknown优先。
- [x] /// 拆ProductionWorkspace/ContextHeader/MiniCanvas/Inspector/AssetDrawer/MasterPanel及三最小壳；Workflow与Master的dirty/save独立。
- [x] /// 新临时DB浏览器覆盖三形态save/reload/409/stale/seed/check/freeze/review/approval/package及v3/debugger回归；不使用生产数据。
- [x] /// 全量backend、TypeScript/Vite、route预算、strict、Ruff、diff及迁移fresh gates，独立SPEC/backend/frontend-review-package评审；验收后勾任务并准备白名单本地提交。
- 验收映射见 docs/FE_F6A_FINAL_ACCEPTANCE.md：753 passed / 206项F6A；三形态与历史浏览器完整通过；三独立评审APPROVE。
- F6B不启动，原始包/canonical不覆盖，不push/deploy/生产迁移；归档和canonical同步另待授权。

## 2026-09-28：FE-F6A v4审批→本地成品包（main）

- [x] /// 先写无Draft Text的端到端和撤权/篡改/新Master负向回归，确认既有Draft-only/schema-v3阻断。
- [x] /// 抽services/production_validation.py共享Master/Candidate live validator；Freeze、审批、新授权共用，已有授权包只校验冻结来源和live gates，不悄然换成最新Master。
- [x] /// project_review.py按schema分派审批，delivery.py按schema分派包；包内使用冻结内容与精确引用，v4失败禁止回退。
- [x] /// 用隔离SQLite复跑全量/定向、strict/Ruff/diff，核对ZIP字节/哈希/Review/Target和历史不变；更新README/进度，按本轮白名单本地提交。
- 禁止前端修改、push、deploy、生产迁移、canonical同步或归档。
- 已验证流程：手工Text Master（无Draft/Topic/Mother/Run）→ 当前检查 → v4 Candidate → exact-hash Review → DeliveryTarget → 本地ZIP；新Master/Brief阻断新增审批/授权，已有授权继续使用冻结历史内容且须通过live gates。
- 阶段门禁712 passed/6既有警告、strict24/24、Ruff/diff通过，任务114/214；下一段继续Review v4/Versions/Overview，尚不代表前端或完整F6A验收。

## 2026-09-28：FE-F6A Adapter → seed → v4后端（main）

- [x] /// Adapter定向测试先RED：精确render输入、显式人工attestation、多canvas覆盖、字节/MIME/权利和Registry不匹配。
- [x] /// production_modalities收口validate/preview/render/package/availability；content_masters接只读readiness、检查与追加式确认，保留v3行为。
- [x] /// DraftMedia/claim映射和显式unmapped检查；独立manifest builder/hash回归，并验证工作流seed完整快照。
- [x] /// builder验收后接v4 Freeze：expected_payload_hash、latest/current checks/live rights、提交前复核回滚。
- [ ] /// 接schema-dispatched Approval/local package、完整无Draft端到端及并发冻结回归；前端仍不动。
- OpenSpec已核92/214；不把Freeze通过写成Approval/Package闭环，不同步canonical或归档。

## 2026-09-28：FE-F6A 后端不可变量（main，继续apply）

- [x] /// 回归先行：跨Unit项目生成素材、未知渠道/形态与原子保存边界；修复后复跑。
- [ ] /// 封严Master上下文事务锁、完整live evidence/rights检查及Draft seed血缘。
- [ ] /// 完成Modality Adapter，再实现纯manifest v4 builder和无Draft的Freeze→Approval→local package。
- [ ] /// 后端链路通过后再做Review/Versions/Overview；前端暂不改。
- 仅主工作区main；不push/deploy/生产迁移，不同步canonical或归档未完成change。

## 2026-09-28：FE-F6A 阶段代码整合到main（用户已授权）

- [x] /// 核对两工作区共同基线661e30a与重叠审计文档，保留原始包
- [x] /// 分支复跑阶段门禁，白名单提交；可恢复保存main重叠改动后快进
- [x] /// main复跑回归/构建/规格/diff，记录阶段提交与后续main直接开发原则
- F6A仍为44/214，禁止以本次整合宣称完整验收或归档；不push/deploy/生产迁移。

## 2026-09-28：FE-F6A apply 前置核验（用户已授权 apply）

- [x] /// 核对main、F5C归档/五份主规格、OpenSpec状态与只读Alembic code head
- [x] /// 用隔离临时库复跑后端基线，并复跑前端构建/预算与strict/diff
- [x] /// 取得ChatGPT连接器实际读到post-F5C main、两份canonical和迁移的证据
- [x] /// 选择隔离工作树，从main@661e30a新建codex/fe-f6a-production-core-content-master
- [ ] /// 依实施计划逐层完成持久化、Master服务、v4候选/交付和生产界面
- [x] /// 复核并纠正过早任务勾选；补回退历史保护、归档只读、幂等重试、详情/边界和检查/Seed时效回归
- [ ] /// 完成共享事务锁/上下文冲突和引用权利/渲染绑定，再进入完整v4与界面实施
- [ ] /// 隔离回归、浏览器验收与独立复核；归档/合入另待授权
- 不push/merge/deploy/生产迁移；原始包与现有未提交文件保留。

## 2026-09-28：FE-F6A 规格审计与标准归位（仅规格）

- [x] /// 核对post-F5C main、canonical及真实Alembic code head，读取完整源包
- [x] /// 对照现有Master相关业务路径审计版本/权限/素材/检查/候选兼容边界
- [x] /// 生成标准change，完整保留四份MODIFIED旧要求与场景并补必要实施边界
- [x] /// 运行strict/diff及规格保留核验，更新README/记录，等待用户单独确认apply
- 不改业务代码、不生成测试、不运行迁移、不commit/push/deploy；原始包不变。

## 2026-09-28：FE-F5C 五份主规格同步与归档（已授权）

- [x] /// 核对main ac6d4dc、4/4产物、95/95任务及五份delta；保留原始包
- [x] /// 同步两份新增与三份更新主规格并归档，逐块核对全部旧要求/场景保留
- [x] /// 补正式Purpose，更新记录，运行全量strict/diff-check并本地提交
- 本轮仅规格及文档收尾；不改业务代码、不push/deploy/生产迁移，不恢复旧规格副本。

## 2026-09-28：FE-F5C 本地main整合（用户已授权）

- [x] /// 对比分支与main的重叠文档/标准规格，限定路径可恢复保存，不碰原始包
- [x] /// 分支复跑547测试、build/bundle、strict/Ruff/diff，仅提交本次白名单文件
- [x] /// 快进本地main，合入后复跑门禁并提交整合记录
- 仅本地commit/main；不canonical同步归档、不push/deploy/生产迁移。保留工作树供后续归档。

## 2026-09-28：FE-F5C 审计归位与 apply（已授权定向回归）

- [x] /// 核对 main49d6c4b/F5B canonical、迁移head，复用空闲工作树隔离F5C
- [x] /// 完整审查源包，标准change保留既有MODIFIED块并补权限/并发/权利/性能边界
- [x] /// 独立SPEC复核、strict/diff-check，记录隔离门禁基线后进入apply
- [x] /// Collection持久化/API、SQL有界Library/usage、Project引用复用
- [x] /// 安全Settings投影与两工作区真实前端、lazy预算
- [x] /// 定向/全量回归、迁移往返、独立SPEC/QUALITY与隔离浏览器验收
- 本轮不commit/main合入/canonical归档/push/deploy/生产迁移；实施在 codex/fe-f5c-system-assets-knowledge-settings。

## 2026-09-28：FE-F5B 六份主规格同步与归档（已授权）

- [x] /// 核对 main 6452ad2、4/4 产物、94/94 任务及六份 delta，保留原始包
- [x] /// 同步两份新增与四份更新主规格，归档并核对历史要求/场景保留
- [x] /// 补正式 Purpose，更新记录，运行全量 strict/diff-check 并本地提交
- 不 push、deploy 或运行生产迁移；本轮不改业务代码。

## 2026-09-28：FE-F5B 本地main整合（已授权）

- [x] /// 核对dd71a14共同基线，保留主工作区原始包、规划和审计文档
- [x] /// 分支复跑门禁，仅提交FE-F5B实现、规格及本任务文档
- [x] /// 可恢复保存main的重叠审计改动，快进本地main，核对保留结果
- [x] /// 合入后复跑全量后端、前端build/bundle、strict和diff-check，记录提交
- 本次仅本地整合；不同步canonical、不归档、不push/deploy/生产迁移，保留工作树供后续归档。

## 2026-09-28：FE-F5B apply（已授权，隔离实施）

- [x] /// 复用空闲工作树，从main `dd71a14`创建`codex/fe-f5b-performance-learning-memory`，转入校准规格与计划
- [x] /// 基线门禁与七资源/可逆迁移
- [x] /// Receipt/外部历史、观察粒度、Coverage/Analysis真实服务
- [x] /// Insight、候选验证冻结、Memory晋升及版本闸门
- [x] /// 四标签Learning、Identity Memory、Home和lazy预算
- [x] /// 全量回归、隔离浏览器、独立规格/代码复核；归档/提交另待授权

## 2026-09-28：FE-F5B 规格审计与标准归位

- [x] /// 核对 main `dd71a14`、F5A canonical/archive 与 Alembic code head `f5a000000001`
- [x] /// 审计用户原始包与当前 Receipt/Feedback/Identity/Home，校准发布时间、指标粒度、证据冻结、Memory旁路和并发边界
- [x] /// 六份 delta 归位，四份 MODIFIED 保留现有完整块；新规格改为 ADDED delta 格式
- [x] /// 独立复核、全量 strict / diff-check / 源包保留核对
- [x] /// 用户已确认校准proposal并授权测试；隔离分支apply与验收完成，尚未合入main，完整记录见隔离工作树progress.md

## 2026-09-28：FE-F5A 六份主规格同步与归档（已授权）

- [x] /// 核对 main `682df71`、4/4 产物、17/17 任务和六份 delta
- [x] /// 同步新增两份与更新四份主规格，归档 FE-F5A 并补正式 Purpose
- [x] /// 逐块核对 delta 与历史要求保留，运行全量 strict、diff-check，更新记录并准备本地提交
- 不推送、部署或运行生产迁移；不开始 FE-F5B 业务实现。

## 2026-09-28：FE-F5A 本地 main 整合（已授权）

- [x] /// 核对 main 与隔离分支同源，保留主工作区未跟踪的原始规格包
- [x] /// 重新执行后端、前端、OpenSpec 和差异门禁，仅提交 FE-F5A 文件
- [x] /// 快进合入本地 main，在合并结果上复跑门禁并记录提交
- [x] /// 六份 delta 同步与归档已获单独授权并完成；不 push、deploy 或生产迁移

## 2026-09-28：FE-F5A apply（实施/复核通过，已同步归档）

- [x] /// 核实 main `2f52053` 含 FE-F4/FE-P1，隔离分支 `codex/fe-f5a-home-opportunity`
- [x] /// 四资源持久化、状态闸门、评估版本、信号权限、原子显式转换
- [x] /// Home / Opportunity 真实页面及 lazy 预算，项目来源回链
- [x] /// 临时库 upgrade → downgrade → upgrade，真实浏览器机会 → 评估 → 项目 → 刷新
- [x] /// 关闭独立复核问题，完成全项目待决策批量投影，再跑最终门禁
- [x] /// 完成规格同步归档；本地 main 整合已单独授权，不 push、deploy 或生产迁移

## 2026-09-28：FE-F5A-SPEC-R1 review 修订（SPEC_R1_READY）

- [x] /// 核对 review 反馈与当前 OpenSpec、AuditLog/ProjectEvent 模型和既有 Home/Review 投影
- [x] /// 补状态生命周期闸门、Assessment 并发、来源真源、Home 排序/失败语义和四个 Modified Capabilities
- [x] /// 将定向自动化回归要求写入 tasks，保留不新增独立测试框架的边界
- [x] /// 运行全量 OpenSpec strict 与 `git diff --check`
- [ ] /// 等待 SPEC_R1 确认后执行 `/opsx:apply`，不提前改业务代码

## 2026-09-28：FE-F5A Home + Opportunity 规格审计与归位（SPEC_READY）

目标：在 FE-P1 `85b8c08` 基线上，为内容生命周期补上 Opportunity 决策层和 Home 聚合工作台；本轮仅完成 OpenSpec 规格，不 apply 业务代码。

- [x] /// 核对 FE-P1 本地 commit、主规格、现有 Home/Opportunity placeholder、Project Overview/Review/Delivery 事实来源
- [x] /// 创建 `fe-f5a-home-opportunity` proposal/design/specs/tasks，写明 Opportunity 与 Topic、Home 与第二状态机的边界
- [x] /// OpenSpec strict 校验、diff 检查、记录 connector 基线前置
- [x] /// 审计用户解压标准包，补齐四份 FE-F0/F1、F3A、F3B、F4 delta，并统一 Source binding / Fact Boundary 语义
- [ ] /// 等待 connector 可读 FE-F4/FE-P1 最终基线后执行 `/opsx:apply`

## 2026-09-28：FE-P1 主规格同步与归档（已授权）

目标：将五条 ADDED Requirement 归入 canonical `openspec/specs/` 并归档已复核的 FE-P1；不推送、合并或部署。

- [x] /// 核对隔离工作树、4/4 OpenSpec 产物、10/10 任务与主规格未同步状态
- [x] /// 使用 OpenSpec 归档并同步 FE-P1 主规格，核对五条长期要求
- [x] /// 归档后运行 strict、前端构建预算与 diff-check，更新 README/progress/findings

## 2026-09-28：FE-P1 apply（已授权）

目标：按已确认 OpenSpec 限定前端加载边界和首包预算；实施计划见 `docs/superpowers/plans/2026-09-28-fe-p1-frontend-bundle-performance.md`。

- [x] /// 复跑 FE-F4 基线与直接访问，确认隔离工作树
- [x] /// 拆分项目列表、详情、生产与共享类型
- [x] /// 路由级 lazy、加载/错误恢复，不改原有路径和业务动作
- [x] /// 生成 manifest，检查 `/projects` 初始 JS 静态闭包与重型依赖
- [x] /// 构建、预算、OpenSpec、浏览器冒烟、文档回填与独立复核；归档需同步主规格后执行

## 2026-09-28：FE-P1 前端首包性能规格审计（不 apply）

目标：以 FE-F4 `2f3ced2` 为基线，核实加载依赖并提出独立 OpenSpec；用户确认前不修改前端实现。

- [x] /// 核对 FE-F4 工作树、入口路由、项目/生产模块和真实构建产物
- [x] /// 写出 FE-P1 proposal、design、spec 与 tasks，限定首轮范围
- [x] /// 运行 OpenSpec strict、差异检查，记录基线和待确认边界
- [ ] /// 等待用户明确确认；本轮不 apply、不归档、不推送

## 2026-09-28：FE-F4 apply（已授权）

目标：按 `openspec/changes/fe-f4-project-review-distribution/` 实施项目优先审核与分发，保持旧 Topic 链兼容；详细步骤见 `docs/superpowers/plans/2026-09-28-fe-f4-project-review-distribution.md`。

- [x] /// 确认 FE-F3B 本地 `main` 基线、OpenSpec 57 项任务（3 项已完成）和隔离分支 `codex/fe-f4-project-review-distribution`
- [x] /// 模型与可逆迁移：ContentAsset / Review / DeliveryTarget
- [x] /// Candidate v3 冻结、精确审批与不可变血缘
- [x] /// 交付授权、v3 人工包、legacy raw-ID 权限、unknown 对账
- [x] /// 项目 Review 投影、Overview/Versions/Activity 与 `/review` 前端
- [x] /// 回归、隔离迁移、浏览器验收、独立复核与五份主规格同步归档
- [x] /// 归档后五份主规格及全部主规格严格校验、差异检查；准备本地提交，不推送/合并/部署

## 2026-09-28：FE-F4 Project-first Review & Distribution 规格审计（不 apply）

目标：以本地 FE-F3B 提交 `55eba02` 为基线，审计用户提供的 FE-F4 包，将校准后的提案放入标准 OpenSpec；主工作区本地 `main` 后续已快进到该提交，但 FE-F4 仍需单独确认才能 apply、推送、合并或部署。

- [x] /// 核对主工作区与 FE-F3B 隔离工作树、canonical specs、模型和迁移前置
- [x] /// 审计来源 proposal/design/specs/tasks 对现有 Candidate/Review/Delivery 结构与权限的适配
- [x] /// 创建标准 `openspec/changes/fe-f4-project-review-distribution/` 并补全五份 delta 的归档安全边界
- [x] /// OpenSpec strict、`git diff --check`、文档与独立规格复核；保持业务代码未改动
- [x] /// 复核主工作区 FE-F3B 主规格、身份实现、迁移 head 与隔离库测试/前端构建基线

## 2026-09-27：FE-F3B Content Identity apply

目标：在隔离工作树审计并实施 `fe-f3b-content-identity`，交付身份层级、不可变快照、工作流偏好和真实工作区；不做生产迁移、推送或合并。详细步骤见 `docs/superpowers/plans/2026-09-27-fe-f3b-content-identity.md`。

- [x] /// 将来源提案归入标准 OpenSpec，校准四份 delta 规格和历史安全边界
- [x] /// 核对 296 项后端和前端构建基线，隔离初始化 worker 数据库
- [x] /// 模型/迁移、版本化身份解析与授权 API
- [x] /// Unit/Run 快照固定、层级默认工作流与项目读模型
- [x] /// 身份工作区、矩阵/生产 UI 与隔离浏览器验收
- [x] /// 全量门禁、独立复核、OpenSpec 归档；不推送/合并/部署

## 2026-09-27：FE-F3A apply

目标：按已确认的 `fe-f3a-content-project-core-completion` 实现五类项目核心持久化、真实七标签与回归验收；不做生产迁移、推送或合并。详细步骤见 `docs/superpowers/plans/2026-09-27-fe-f3a-project-core.md`。

- [x] /// 五表迁移、模型、ProjectEvent 和项目归档权限边界
- [x] /// Brief、Source/Fact Boundary、共享素材和 Versions/Overview API
- [x] /// 七标签前端接真实 API，保留 FE-F2 Matrix/Production
- [x] /// 隔离库迁移、后端/前端回归、OpenSpec strict 与文档同步（296 后端测试通过）
- [x] /// 外部复核通过并归档；仅提交本地 FE-F3A 分支，不推送/合并/部署

## 2026-09-27：FE-F3A 规格复核与标准目录归位（不 apply）

目标：核对用户提供的 FE-F3A 包与 FE-F2 基线，纳入标准 OpenSpec 变更目录，修补实施前必须明确的边界；不修改业务代码、运行迁移或发布。

- [x] /// 核对 FE-F3A 来源包、FE-F2 基线、现有项目/Source/FactPack/Material 实体及路由
- [x] /// 从 `734990c` 创建 `codex/fe-f3a-project-core-completion`，将结构化提案归位到标准 `openspec/changes/`，保留原始包
- [x] /// 修补项目删除历史安全、事件事务、并发修订、重新绑定与素材字节回滚边界
- [x] /// 运行 OpenSpec strict 与 diff 检查，核对本轮仅文档变更，更新 README/progress/findings
- [x] 用户已确认进入 `/opsx:apply`；本轮按已校准规格实施

## 2026-09-27：FE-F2-R1 收尾补丁（待外部复核）

目标：按已核对的 review 缺口，恢复固定版本所见即所执行、矩阵安全 CRUD、可解析模板占位符与真实 Attempt 审计；不扩大到新插件或生产迁移。

- [x] /// 确认仅项目覆盖、无 Run/快照/产物的单元可原地修改；补 FE-F2 OpenSpec 场景
- [x] /// 先写固定版本、矩阵生命周期与模板 Gate 的定向回归，观察旧行为失败
- [x] /// 加 effective-workflow、原地修改/历史替换/归档和显式重绑，前端加载固定版本
- [x] /// 收紧占位符到 config，持久化节点 Kind，清理失败重跑的当前输出
- [x] /// 全量后端测试、前端构建、OpenSpec strict 与 diff 检查
- [x] /// 外部 R1 小补丁复核通过；完成 OpenSpec 6.3，归档后仅提交 FE-F2 分支，不推送或合并

## 2026-09-27：FE-F2 apply（codex 分支）

目标：按已确认的 `fe-f2-persistent-production-workflow` 实施真实持久化、权限、版本、Data Node、项目产物和生产工作台；不触碰生产迁移或发布。实施细目见 `docs/superpowers/plans/2026-09-27-fe-f2-persistent-production-workflow.md`。

- [x] /// 从当前干净 main 建立 `codex/fe-f2-persistent-production-workflow` 分支，核对 OpenSpec 0/21 与基线测试
- [x] /// 持久化项目/单元/角色/默认绑定及迁移，补定向回归测试（OpenSpec 1.1）
- [x] /// 统一项目权限覆盖新旧 Workflow API
- [x] /// 工作流校验、项目覆盖与角色默认版本双保存
- [x] /// Data Source Plugin、快照、stale 与项目产物
- [x] /// 三形态生产工作台与设计/调试器
- [ ] /// 完整回归、本地验收、文档及归档

## 2026-09-27：FE-F2 正式 review 的实施前边界（仅规范）

目标：封闭旧 Workflow API 旁路、角色默认模板的项目值泄漏与拖拽误改依赖，并把回归测试列为 FE-F2 实施任务；本轮不 apply。

- [x] 核对现有 Workflow 旧接口及 FE-F2 草案中的四项缺口
- [x] /// 将统一项目授权覆盖旧 run、attempt、retry、rerun、human、cancel、list 及定义入口
- [x] /// 将服务端模板可移植性 Gate 和视觉顺序/依赖图分离写入设计、规格与任务
- [x] /// 将定向回归测试纳入 FE-F2 任务与验收
- [x] 严格校验新版 OpenSpec 并核对差异；保持 apply 未执行

## 2026-09-27：FE-F2 V5 规格校准（仅规范）

目标：把现有 FE-F2 OpenSpec 与 V5 对齐；用户已确认角色 × 内容形态默认工作流新版本须真实持久化并供后续内容单元选择。本轮不执行 apply。

- [x] 对照 V5 契约与 FE-F2 proposal/design/specs/tasks，确认插件与角色默认模板边界
- [x] /// 订正 Data Source Plugin 注册/选择、断连失败闭合、Data Snapshot 与 stale 规格
- [x] /// 订正项目覆盖与角色默认版本双保存路径，以及六类节点、拖拽和项目共享产物规格
- [x] 严格校验 OpenSpec、差异检查；校准后的完整 FE-F2 提案待用户确认

## 2026-09-27：FE-F0-F1 复核补丁与本地 main 提交

- [x] 核对主规格的异常状态解释缺口与脏工作树边界
- [x] 在异常项目总览/内容矩阵增加状态说明，不改后端
- [x] 前端构建与浏览器页面核对
- [x] 仅暂存 FE-F0-F1 所属文件/差异，审阅暂存快照并提交本地 main（1b8ef04）

## 2026-09-27：连接器故障检查

目标：判断当前项目的 ChatGPT 连接器是否异常；仅在诊断仍指向隧道故障时重启并复核。

- [x] 检查 C2C 更新、授权白名单、固定连接配置和协议配置
- [x] 运行项目连接诊断；诊断自动重新建立安全连接，当前检查全绿
- [x] /// 根据四项独立 `internal error` 复现定位到隧道外部连通异常，执行定向隧道重启
- [x] /// 复核 HTTP/2、健康连接数及公开 MCP 未授权响应
- [ ] /// 请用户重试 `workspace_info`，确认 ChatGPT 连接器调用恢复

复查（2026-09-27）：用户报告疑似再次断开。诊断仍全绿；外部 MCP 返回 401、HTTP/2 正确、HA 连接数大于 0。未重启，待 ChatGPT 端具体现象确认。

## 2026-09-27：FE-F2 真实执行与持久化提案

目标：用户明确 FE-F2 工作流调试器须接后端、真实执行并保存流程；先完成 OpenSpec 设计确认，再进入实施。

- [x] 核对 FE-F2 产品契约、现有前后端工作流与未提交改动
- [x] 提出复用既有引擎的项目级持久化方案，建立完整 OpenSpec 并严格校验
- [ ] 等待用户明确确认校准后的 `fe-f2-persistent-production-workflow` 完整范围（角色默认版本单项已确认）
- [ ] /// 确认后编写实施计划并执行 `/opsx:apply`
- [ ] /// 本地真实运行验收、文档同步与归档

## 2026-09-27：FE-F0-F1 前端实施

目标：按已批准的 V5 产品体验和 Frontend Product Contract V1，建立九个一级工作区、ContentProject 七标签、内容矩阵 CRUD、共享素材与生产入口。新项目数据仅在本地模拟，不改后端。

- [x] 核对交接材料、现有前端和未提交改动
- [x] 建立并严格校验 `implement-fe-f0-f1-product-shell` OpenSpec
- [x] /// 模拟项目数据与状态组件
- [x] /// 主导航、项目列表与七标签
- [x] /// 内容矩阵、共享素材与生产入口
- [x] /// 构建核验、文档与归档

- [x] 确认当前项目与连接方式
- [x] 为 `AIContentStudio` 配置固定连接
- [x] 在 ChatGPT 创建并完成当前项目连接器授权
- [x] 创建并绑定 ChatGPT 专属项目（账号切换后重新绑定）
- [x] 通过 `workspace_info` 验证当前工作区

## 2026-09-22：与产品蓝图对齐（仅规划）

目标：在现有系统上形成文章/图文 V1 的实施顺序与验收标准，不实施业务代码、不发布内容。

- [x] 找到并阅读指定对话「自媒体平台对比总结」，以用户最后明确的需求为准
- [x] 核对当前代码能力与蓝图差距，区分实现、文档声明与未验收项
- [x] 在原 ChatGPT 对话开展三轮讨论：范围对齐、最小改造、实施和验收收敛
- [x] 保存三轮规划建议与证据，更新进度、发现和 README（不是实施授权）
- [x] 独立复核本地草案，修正候选采纳顺序与单目标可靠性前置；不进入实现
- [x] 原对话恢复后完成三轮讨论，收敛首个待确认的提案范围与建议名称
- [x] 根据 ChatGPT 最终复核创建 `add-evidence-bound-article-handoff` OpenSpec，并通过严格校验
- [x] 读取原 ChatGPT 最终复核后归档；M1 实现和全部本地验收已完成

当前状态：首批 M1 已实现并完成本地验收：已有文章的公众号 + X 线程 ZIP 成品包、人工交付回执与反馈；公众号自动进入草稿箱不作为首批硬门槛。原 ChatGPT 最终代码复核已返回 DONE，OpenSpec 已归档。真实发布、排期与任何远端 API 副作用均不在本次范围。

## 2026-09-24：继续按 PRD 补齐 V1 全渠道

目标：以 `03_ai_content_studio_PRD.md` 为长期需求基线，补入原对话明确的 11 平台 V1 文章/图文范围，保留抖音脚本；分阶段推进受控成品与逐形态验收。

- [x] 核对 PRD 首选三渠道、原对话 11 平台目标及现有生成/受控交付差距
- [x] 建立 `complete-prd-v1-channel-deliverables` 的 OpenSpec 提案、设计、规格和任务
- [x] 完成严格提案校验（4/4 产物齐全）
- [ ] 等待用户确认此具体变更
- [ ] 用户确认后执行 `/opsx:apply`，按 `/// 迁移与契约 /// 渠道成品 /// 交付界面 /// 验证归档` 推进

当前状态：用户纠正后正在修订提案；尚未修改业务代码。PRD §15 的 15 项标准、§16 的 30 个真实 Topic 门槛及 §3.1 的全渠道逐形态验收分别跟踪。
## 2026-10-01：MiniMax CLI 认证连续性规格修订

- [x] 记录用户授权：允许系统在本机受控读取官方 MiniMax CLI 认证配置，用于固定调用和检测凭据变化。
- [x] 将 raw credential 禁止落库、日志、receipt、UI、素材，改为受控 receipt key HMAC credential epoch。
- [x] 独立复核规格修订后实现认证读取器；不发起真实生成请求。
- [x] 根据复核补齐 OAuth/token 轮换指纹和 `O_NOFOLLOW` 文件描述符读取，避免旧 api_key 残留与 symlink/TOCTOU 漏检。
- [ ] 继续完成 MiniMax 持久任务的真实 submit/query/recovery、素材接受和浏览器闭环；缺少稳定 receipt key 或真实供应商证据时保持阻断。

## 2026-10-02：MiniMax 真实生成收口批

范围：继续已授权 add-model-capability-routing，Google/Grok/Commons 暂缓，不进入 F8。

/// 固定图片 submit_task 与尺寸/base64边界 /// 隔离任务一次真实生成 /// 私有字节校验及只读重启回读 /// 现有回归与文档证据

- [x] 复现图片缺少持久 dispatch；补固定入口与不超过像素预算的8倍数正方形尺寸，base64避免CLI CDN重试。
- [x] 隔离库/素材目录/显式测试receipt key执行一次图片任务；结果unknown保持不重发，另外独立TTS任务取得真实WAV，不改正式配置或默认模型。
- [x] 记录真实语音字节、新进程原任务回读及新鲜回归结果，不把单条成功当整个F7通过。
- [ ] 后续补完整媒体接受/Workflow/浏览器和产品公众号回读；图像未知必须先对账，不通过另一任务重发同请求。

Ruling：遵守用户不新增测试代码要求，使用临时运行探针和已有测试；未覆盖的状态机边界继续保持未完成。本轮不提交/推送/归档/生产迁移，不重复发送未知微信交付。

## 2026-10-02：CLI 配置前端对齐续批

目标：修复已保存 MiniMax CLI binding 在 Settings 下拉框中误显其他协议的问题；沿用已授权 add-model-capability-routing，不开放素材使用权。

/// 隔离浏览器复现 /// 补齐已有适配器选项和本地字段提示 /// 构建与既有状态回归 /// 浏览器回读及证据更新

- [x] 隔离浏览器读取已有两个 CLI binding，确认协议下拉框只有四个远端选项，缺 minimax.cli；后端 Binding 明确支持该值。
- [x] 最小修改 ModelRoutingSettings，补 CLI 选项，不自动改模型、URL、凭据或权限。
- [x] 运行既有状态回归、TypeScript/Vite/bundle、OpenSpec strict 和 diff-check；浏览器确认原绑定不被误表示。
- [x] 同步 README、progress、findings；不将这个配置修复当作媒体完整验收，不发新供应商请求。

产品只读验收：原 TTS 任务打开持久校验预览，浏览器 audio readyState=4/error=null/duration=1.962094；图片 unknown revision=3、语音 result_ready revision=3、accepted FK 均空，MaterialRevision 数量仍 0。许可人工确认待用户回答，未勾确认或使用权。截图 /tmp/aics-f7-minimax-preview.png。

## 2026-10-02：设置读取与明确执行的认证边界

/// 复现库存读取触发认证 /// 分离只读描述与内部执行检查 /// 保持任务验签/认证连续性 /// 现有回归和证据更新

- [x] 确认 configuration_view/plan 共用 CLI binding_state，读取库存会调用 credential epoch，违背已批准 Settings 禁止读取 CLI 认证配置的契约。
- [x] CLI binding_state 仅描述配置/能力且不执行 CLI；内部 execution_binding_state 保留实际 runtime 与认证检查。
- [x] 只有明确任务 prepare 和执行前 revalidate 启用内部执行检查；Settings API不暴露该参数，原恢复/接受 gate 不放宽。
- [x] 既有回归、零网络边界探针、范围 Ruff/strict/diff 验证，记录未覆盖项，不关闭完整 F7/F8。

新全量终态exit0：1661 passed /28 skipped /8既有warnings（85.16秒），在上述业务补丁全部完成后启动；144相关回归与范围Ruff通过，all strict33/33、设计说明更新后的变更strict及diff-check通过。只证明既有覆盖和本轮无网络边界探针，不代替新CLI协议/任务竞争/真实外部全链路。没有新增测试文件或本轮前端改动。

## 2026-10-02：持久任务迁移与回读验收续批

/// 隔离 f7d migration 往返 /// 保留记录 downgrade 拒绝 /// 原真实任务跨进程回读/拒绝重发 /// 文档证据同步

- [x] 在新建私有 SQLite 中验证 f7d create/up/down/up、owner/key 唯一、state/revision/query/size/accepted-ref 及关联 FK；只调用该迁移，不启用 F8。
- [x] 使用隔离记录验证 downgrade 拒绝且任务保留；编译 PostgreSQL DDL 仅为兼容证据，不冒充原生PG执行。
- [x] 新进程只读原语音实际字节、原图片 unknown，确认执行被409拒绝且没有 Provider 调用；原任务记录不修改。
- [x] 同步 README/findings/progress，保留真实接受/任务竞争/原job恢复/原生PG等未完成门禁。

额外私有副本探针：旧/未来revision、双session读旧版本后串行CAS输家、晚worker token均409；无job恢复只写副本unknown，不提交Provider；原实际图片仍unknown/revision3。不是并行进程竞争或崩溃fault injection。临时脚本初次MediaOutput模块导入错误未执行业务，改为真实content_harness.providers导入后通过；没有改业务代码绕过。
## 2026-10-02：F8 基线/生产准备审计

/// 只读核对 F8 OpenSpec、认证/启动/存储/可观测性/health/worker 代码接缝 → 记录威胁模型与生产缺口 → 记录当前门禁 → 保留F7前置和身份/schema独立复核阻断；不改业务代码、不启用F8、不执行生产迁移。

- [x] 完成 `docs/FE_F8_BASELINE_AUDIT.md`，覆盖 auth、secret、storage、worker、logging、migration、deployment、health、external side effects。
- [x] 将 F8 task 0.2–0.6 标记为已完成，并保留 0.1（F7 前置）与 0.7（issuer/subject + existing User 独立复核）未完成。
- [x] 记录当前 backend/frontend/OpenSpec/Ruff/diff 门禁与“实现完成 / 已配置 / 外部已验证”区别。
- [ ] F7 整阶段门禁、F8 身份/schema review、production migration、deployment、remote publish 仍未授权/未完成。

## 2026-10-02：模型路由 Batch B 本地门禁续批

/// 仅运行既有 migration/CAS/capability 回归 → 核对隔离 SQLite up/down/up 与能力注册/权限/脱敏/兼容边界 → 标记 Batch B 3.5；不调用供应商、不执行生产迁移、不替代 MiniMax/公众号真实验收。

- [x] `tests/test_migrations.py`、`tests/test_model_capability_routing.py`、`tests/test_f7_capability_persistence.py`：88 passed，5 existing warnings。
- [x] add-model-capability-routing task 3.5 已完成；保留 2.1–2.3、2.5–2.10、3.2、3.4 的实际未完成边界。
- [ ] MiniMax 稳定 receipt key/完整原任务恢复、Google/Grok、真实素材权利、公众号产品回读仍未关闭；不把本地门禁当外部验证。

## 2026-10-02：CPA 模型登记验收收口

/// 既有模型路由状态回归 + 登记相关后端回归 → 核对保存/刷新/CAS/脱敏/默认与显式路由 → 记录 CPA `/models` 401 为未验证 → 关闭登记任务；不发起生成、不归档、不推送。

- [x] `apps/web/scripts/test-model-routing-state.mjs`：PASS；模型登记相关后端：`32 passed`，1 个既有 warning。
- [x] `add-provider-model-registration`：`4/4` 完成；CPA 实际发现接口仍为 HTTP 401，配置保留为 registered/configured，不标 executable/verified。
- [ ] `add-model-capability-routing` 的官方适配、MiniMax 稳定 receipt key/完整任务恢复和 F7 真实外部验收仍未关闭。

## 2026-10-02：公众号官方草稿适配器收口批

/// 真实验收库只读预检 → 适配器定向回归 → 保留 Unknown 安全边界；待远端 reconciliation/新授权候选后再执行 2.8，最后做 2.9/2.10

- [x] 核对现有官方公众号适配器、传输层、冻结 HTML 和验收脚本。
- [x] 对既有 Candidate/Target/Attempt 做无网络预检，确认 `acceptance_already_claimed`，不重试、不创建新候选、不公开发布。
- [x] 在正确 API 工程路径复跑公众号定向回归：130 passed / 1 warning。
- [ ] 2.8 真实 HTML/素材上传/草稿创建/回读。
- [ ] 2.9 全量门禁与独立安全/发布复核。
- [ ] 2.10 同步主规格并归档补充变更。

## 2026-10-02：公众号成功判定与 WeWrite 对齐

/// 采用接口成功响应作为草稿创建确认 → 保留异常 Unknown → 回归与规格门禁

- [x] 正常 `draft/add` 响应包含 `media_id` 时直接确认草稿创建，不强制二次回读。
- [x] 超时、断连、缺少 `media_id` 或含糊响应仍进入 Unknown，不自动重发。
- [x] 公众号适配器定向回归：129 passed / 1 warning；OpenSpec strict、Ruff、diff-check 通过。
- [ ] 2.8 仍需真实产品路径的一次明确成功证据；2.9/2.10 依赖 2.8 后续收口。

## 2026-10-02：F7 持久任务验收与证据校准

/// 独立核对复合任务的实际证据 /// 隔离数据库验证原任务查询、幂等接受和失败回滚 /// 原生 PostgreSQL 验证精确 f7d 迁移约束 /// 更新真实结果；不调用供应商、不变更正式配置或数据库。

- [x] 独立复核 routing 3.5、registration 2.2、F8 0.6，证据不足的完成项恢复为待验收；F8调用清单已补齐，0.1/0.7保留。
- [x] 使用合成 Provider 与私有 SQLite 验证原 job 恢复、owner/key/CAS/receipt、source revocation 与接受原子性；不新增持久测试文件。完整并发接受/崩溃窗口仍不计通过。
- [x] 在新建临时 PostgreSQL 实例验证 f7d 实际 up/down/up、约束和保留记录降级保护；不使用其他项目数据库，临时实例全部清理。
- [x] 若隔离验收暴露缺陷，仅修正已授权契约，复跑定向和最终门禁并同步 README/progress/findings；两个缺陷和三处schema guard边角修复，fresh全量/实际PG/浏览器/限定独立复核通过。

F8 仅准备，0.1 前置仍有效；用户同意不代替独立安全/schema 复核或生产迁移授权。Google/Grok/Commons 保持暂缓，不计 PASS；公众号 Unknown 不重发。
# 2026-10-02：F7 公众号回读与 CPA 模型适配范围校准

/// 核对既有真实草稿证据和 CPA/模型路由代码 → 修订两份 active OpenSpec 的验收/任务边界 → 同步 README、矩阵与进度 → strict/diff 校验；不改业务代码、不触发微信或模型外部请求。

- [x] 用户明确成功草稿无须 API 回读，且 Gemini/`grok-4.7` 经第三方 CPA 网关接入，不做 Google/xAI 专用适配器。
- [x] 将成功草稿 `media_id` + 同账号人工确认与一般 CapabilityVerification 分开；保留 Unknown 对账。
- [x] 模型路由改为通用 CPA 兼容协议 + 逐操作能力验证；移出专用适配器任务，不标为实现成功。
- [x] OpenSpec strict 33/33、`git diff --check` 通过；主 F7 104/110、模型路由 14/23、归档公众号补充 22/22，合计 140/155、剩 15 项。本轮未 apply 业务代码。
# 2026-10-02：模型路由剩余九项批量收口

/// 核对已批准 OpenSpec 与现有脏工作区 → 审计 MiniMax 原任务恢复、通用 CPA 聊天与媒体边界 → 一批修复可证实的本地缺口 → 用现有回归和隔离探针验证 → 同步规格任务/进度/README；外部付费调用、Unknown 重发、公众号外发、正式迁移、推送均不在本批授权内。

- [x] 核对九项剩余任务、现有持久任务及供应商/素材适配实现，保留其他未提交改动。
- [x] 关闭已证实的同步 CLI 不确定输出误判和任务历史路由不透明缺口；不把通用 CPA 聊天当作生图/视频能力。更广的 2.5/2.6/3.2/3.4 仍开放。
- [x] 既有定向 83、后端全量 1660/28 skipped、前端 TS/Vite/FE-P1、OpenSpec strict 33/33、范围 Ruff、diff-check 通过；真实供应商、浏览器、独立安全复核单列为未完成。
- [x] 更新当前 README、progress、findings 与 OpenSpec 状态，仅勾选完整通过的任务；文档/矩阵对账 task 2.10 已闭合，其余外部与安全验收保留。
# 2026-10-03：公众号草稿成功后的系统能力记录（apply阶段）

/// 复用现有 DeliveryReceipt/DeliveryAttempt/CapabilityVerification → 明确精确账号/文章/auto_draft范围 → 设计原子幂等晋级与安全投影 → 等用户确认后再apply；不调用公众号、不改业务代码、不新增表或migration。

- [x] 已确认缺口：成功草稿和同账号人工确认目前没有自动形成 durable `CapabilityVerification`。
- [x] 已创建 `openspec/changes/record-wechat-capability-verification/` 的 proposal/design/spec/tasks 草案。
- [x] 用户已授权 apply；完成通用收据事务中的精确 scoped capability promotion、库存投影与安全边界。
- [x] 定向回归 165 passed、Ruff PASS；未重新发送公众号、未公开发布、未新增表或migration。
- [x] OpenSpec change 已归档至 `openspec/changes/archive/2026-10-03-record-wechat-capability-verification/`；canonical 主规格同步留待单独授权。
# F8 当前批次：Batch B 可观测性

///
- [x] 请求与异步任务 trace 传递
- [x] worker / workflow / connector 安全状态、耗时、错误分类
- [x] 项目事件关联 metadata 与 admin-only audit debug projection
- [x] 定向回归、临时 SQLite readback、Ruff
///
# F8 当前批次：Batch C 前置恢复

///
- [x] SQLite 在线备份→隔离恢复脚本
- [x] 恢复 integrity/head 与本地素材 hash 回读
- [x] Missing referenced bytes/orphan diagnostics
- [x] Downgrade preflight fail-closed and capability rollback runbook
- [x] Recovery acceptance record
///
/// F8 Batch D：Identity / Content Golden

1. 新增并审查版本化 Identity/Content Golden 夹具，不复制事实真源。
2. 用现有隔离 SQLite mock evaluator 跑全量 30 场景，记录生成、Fact 覆盖和无来源数字指标。
3. 将真实模型质量评审与确定性评测分开，并明确本机范围不执行真实供应商/远端平台。
4. 更新 F8 tasks/progress/findings/README，保留未授权的生产认证、部署和真实发布门槛。

/// F8 Batch D 执行结果

- 夹具：`apps/api/evals/goldens/`。
- 证据：30 topics / 64 jobs / 0 failed / fact coverage 1.0 / unfact number rate 0。
- 下一批：继续处理本机范围内的集成链路与最终门禁；不自动执行远端发布或 F8 draft migration。

/// F8 Batch E：素材存储收口

1. 审计 selected StorageProvider 覆盖的正式素材、历史 DraftMedia、工作流输出、Review/Delivery package 和 retention 消费者。
2. 新增只读 SQLite → 新素材根 copy/hash rehearsal，任何缺失、源 hash 或目标 hash 不一致均失败。
3. 在本机正式范围完成 storage diagnostics、隔离预演和既有集成回归，不执行实际切换。

/// F8 Batch E 执行结果

- 5/5 referenced keys copy/hash verified；0 failure；storage diagnostics 6/6 checked、0 issues。
- 3.8/3.9/3.10 已关闭；下一批继续本机 full-chain/health/runbook/final gate。

/// F8 Batch F：配置库存与健康失败路径

1. 只读盘点当前 SystemSetting 的 secret-bearing 分类，不读取或打印值。
2. 用隔离 fake DB/production Settings 临时探针验证 readiness/startup fail-closed。
3. 更新运行记录，保持本机 profile 不依赖 production auth/MinIO/Celery；不改凭据、不跑迁移。

/// F8 Batch F 执行结果

- 6 行配置 / 3 secret-bearing / 3 safe；数据库异常与生产配置缺失均返回固定安全结果。
- 2.8/5.7 已关闭；下一批继续本机 full-chain 与最终产品门禁。

/// F8 Batch G：本机产品闭环

1. 复用既有隔离回归覆盖 Opportunity→Project→Identity/Brief/Boundary。
2. 覆盖 Text/Graphic/Video Master、ChannelVariant、Candidate、Approval、Authorization 和 local package。
3. 明确 remote Publisher、真实发布、PublishedContentRecord/Learning 不由本地 mock/package 冒充。

/// F8 Batch G 执行结果

- 50 + 182 + 79 项定向回归通过（1 个既有跳过）；9.1–9.4 已关闭。
- 下一批处理 Unknown/published 边界与 lineage/capability matrix，再进入最终 Web/README/独立复核。

/// F8 Batch H：失败发布与能力矩阵

1. 复用 Delivery/PublishedHistory 回归确认 Unknown、失败、超时不进入 published。
2. 复核项目读模型、冻结 manifest、Target/Receipt/Event/audit 的 lineage 查询入口。
3. 输出本机实现/已验证/已配置/远端未执行矩阵。

/// F8 Batch H 执行结果

- 9.8/9.9/9.10 已关闭；下一步只处理本机前端/运行手册/最终门禁与独立 review，生产认证和远端真实执行保持未授权。

/// F8 Batch I：运行手册与部署模板

1. 增加未来部署环境变量模板，不写真实 secret。
2. 增加 readiness-first API/Web/Worker 启动说明。
3. 合并迁移、备份、素材 copy/hash、secret remediation、reverse-proxy/TLS/auth 边界。

/// F8 Batch I 执行结果

- 10.1–10.4 已关闭；未启动 production profile，下一步做本机 frontend/browser/strict/final gates。
## F8 Batch J：本机正式验收收口（2026-10-03）

/// 按用户确认的 SQLite + 本地素材库 + loopback-only profile，完成外部能力边界、全量后端、前端 bundle、规格与静态门禁，并把未来生产项显式分离。

- [x] /// 复核并记录 6.4–6.8 的真实授权、Unknown/幂等、只读库存、审计和安全回归证据；保留 6.1–6.3 未关闭。
- [x] /// 在隔离 SQLite 中完成全后端复跑；临时库父目录和 head 初始化问题仅修正验收环境，不改业务代码或正式库。
- [x] /// 完成前端构建/FE-P1 bundle、OpenSpec strict、范围 Ruff 和 git diff-check。
- [x] /// 写入本机最终验收状态，区分 implemented/configured/locally verified/real-platform-unverified。
- [ ] /// 生产身份、统一 outbound policy、真实远端发布、独立复核和本地最终 commit 仍需各自授权/配置，不在本轮伪造完成。

/// F8 Batch K：统一模型出站请求边界

- [x] 让 OpenAI-compatible 注册模型与旧环境配置共用同一条有界请求路径。
- [x] 统一请求/响应体积与总超时上限，禁止单一路径保留 120 秒或无界 JSON 读取。
- [x] 用临时本机探针验证边界，更新 F8 安全证据；不调用真实供应商、不保存测试凭据。

/// 接收安全复核：在既有模型出站 bounds 上补齐 deadline 耗尽拒绝与供应商响应结构安全分类；不扩大到真实供应商调用或生产身份。已完成，整体 F8 6.1–6.3 仍保持开放。

## F8 Batch L：本机范围出站安全收口（2026-10-03）

///

## F8 Batch M：出站策略与本机终审

/// 复核中发现统一 10 秒会削弱既有聊天/生图能力；统一的是策略入口，不是所有能力的数值。

/// 架构终审发现恢复工具 URI 未编码、同 key 多引用 hash 被丢弃 → 私有特殊路径/冲突 hash 探针先复现 → 用 Path.as_uri 只读连接及每条引用 hash 校验最小修正 → 真实 f7d 备份/字节重演与定向复审；不改正式库或新增永久测试。

/// 安全终审发现 httpx 空闲超时不能拦住慢响应头、query URL 进入第三方日志 → loopback 慢头/内存日志探针先复现 → 共用绝对 deadline 的 TCP/TLS/read/write stream＋上下文日志抑制 → 既有回归/复审；无新依赖、不调用远端、不改权限范围。

- [x] /// 在 `url_fetch.py` 集中定义按能力区分的有界时限/字节预算，保留聊天 120 秒、生图 25 秒；各传输仍保留自己的协议/Unknown gate。
- [x] /// 在 `config.py` 加可选精确域名白名单，所有可控制 HTTP 路径在 DNS/发送前校验；空配置保留现有逐能力策略，拒绝 wildcard/非法配置。MiniMax CLI 内部网络明确不受该 HTTP 策略管理。
- [x] /// 执行临时失败→通过探针与既有全量回归；不生成永久测试、不调用真实供应商、不修改正式库/凭据。186 定向＋1660 全量/28 skipped；socket-family 兼容修正后另 28 生图定向及 Ruff PASS。
- [x] /// 完成安全/运维及产品架构独立复核，按批准 profile 标注 17 项延期并保留原验收义务。最终定向复审分别 APPROVE，不冒称 reviewer 亲跑全部门禁。
- [x] 盘点并统一仍在使用的 URL Import / Connector / Commons / image provider 请求上限；既有定向与全量回归通过。
- [x] 保留各能力的精确 host/SSRF 限制，禁止代理、重定向越界和无界请求体；CLI 内部网络控制边界单独记录。
- [x] 用临时本机探针复核 deadline、请求体、响应体和错误脱敏，不调用真实供应商。
- [x] 将生产身份、Secret Provider、真实远端发布列为本轮明确延期，不修改对应 OpenSpec 完成状态；82/83 本机、17 原义务延期。

/// 本机收口记录：正确 apps/api cwd 的全量 1660 passed / 28 skipped / 8 warnings（84.32 秒）、186 定向、Web/预算、strict/Ruff/diff → 两份独立 APPROVE → 关闭 6.1–6.3、10.8/10.9/10.12 → 更新本机 82/83、原 82/100，保留 17 延期与 10.11；等单独授权本地提交/主规格同步归档，不把未批准身份 draft 混入。

- [ ] 10.11 的本地最终提交与 ROADMAP 状态记录；须先获明确授权并排除未批准身份/schema draft，不能自动提交整个 dirty tree。
///
