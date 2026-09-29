# Codex with ChatGPT 连接配置计划

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
