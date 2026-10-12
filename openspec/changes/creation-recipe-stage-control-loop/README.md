# Creation Recipe Stage Control Loop

## PRD / 需求背景

把已存在的 Workflow、Content Master、素材、渠道版本和专业执行串成真正可控制的创作闭环。Creation Recipe 是 Workflow Definition 的产品投影，不新增 Recipe/Feedback 状态表。

`选择流程 → 调节阶段 → 预览实际 Prompt/方法/模型 → 执行 → 审阅并接受/修改/拒绝 → 写入既有领域资源 → 显式保存有效调整 → 下一次使用新版本`

用户已授权本 change apply，并确认接受后自动执行依赖就绪的下一阶段，遇到人工审阅、未知结果或阻塞时停止。2026-10-06 最新执行口径为整批实施、集中独立代码复核、最后统一冒烟；本批不新增测试代码、不跑 pytest/完整后端。

## 当前状态 / 已完成

**141/144 已勾选，3项未完成；受控三形态旅程闭环且本机正式crs已另行获准启用，永久回归/完整backend与规格生命周期仍未完成。** 配套备份/副本迁移、正式库历史与素材hash保全、loopback API/Web/原Worker及Recipe选择/MCP只读入口通过，见[启用记录](../../../docs/CREATION_RECIPE_LOCAL_ENABLEMENT.md)。

- Phase 0继承ACO lifecycle及108项历史回归。后续另行授权启用后，当前approved/runtime/readiness head统一`crs000000001`；f8a身份列仍null/inert，JWT未启用。原ACO验收保留为历史。
- Recipe 阶段条、基本/高级窗口、来源/版本/历史、精确模型/方法选择与纯 Preview；可见参数必须由 executor 实际消费，未知参数拒绝。
- 三形态 `stage.master.propose@1` 候选及显式采用，沿用 text/graphic/video.master.v2 canonical adapter。原 builtin.generate 不变；运行不自动写 Master。
- 发送前持久 Attempt claim/receipt、exact resolution hash、幂等回放、安全 Unknown/reconciliation。接受事务原子写 Master/refs/ProjectWorkflowOutput/反馈，旧 proposal/receipt 不改写。
- ProviderGenerationTask 媒体、F6E Variant、检查/Human 和 ACO Director/CreativeExecution 的 Stage 外壳；领域结果只能经原服务明确采用。素材接受不自动绑定 Master，专业执行只准备、不自动派发。
- 历史与接受/修改/拒绝/重跑/合法跳过反馈，append-only ProjectEvent；修改接受输入使受影响下游 stale。
- 保存到项目/Persona-Account-Series 默认/Capability candidate；精确 CAS、可移植性、完整默认模板替换差异可见，旧 Unit/Run 不隐式重新绑定。
- 无运行参数差异时，可明确编写指令或选择方法再预览保存；标记为人工拟定、尚未实测，不从正文修改推断成功经验。方法参数统一发送 `arguments_json`；所有调整来源在预览/写入时验证方法的实时可用性、精确版本与范围，系列/账号专用方法不能进入更宽默认范围。
- 显式复用已保存的方法；Installed Agent Skills 独立库存，无可执行 runtime 时诚实不可用。
- 可选 AI 调优：选择精确接受反馈 → LLMRun/hash → 允许字段差异 → 人工确认保存；不自动改 Workflow/Identity/事实/权利/审批。
- Recipe 与高级 Workflow 保存后双向回读版本；保留高级 dirty/Inspector 草稿并提示冲突，独立 Master 草稿不被重挂或覆盖。

## 此前隔离功能门禁（2026-10-06，正式启用前）

正式启用的新鲜schema/数据/素材/readiness/MCP证据见顶部链接；本节保留先前隔离旅程，不把其中“未迁移正式库”描述当当前运行状态。

- 最新完整旅程：从页面创建Project/Brief/Unit、显式绑定Frozen FactPack，到Text三候选、拒绝/新Attempt、第二候选修改采用、一次自动接续并等待审阅、临时调节/方法/模型Preview、保存项目Recipe v2并在新Run回读；Text/Graphic/Video均通过页面内容审批、copy_package授权和ZIP下载。三包冻结正文/输入hash/素材字节hash一致。Video Script/Director→prepared execution→本地受控MP4→页面人工接受为MaterialRevision→明确绑定并保存Master通过。
- Text语义模型未配置和legacy profile覆盖仍为warning，严格checks Stage没有被假标pass或自动放行；Review提交明确warning处置。Video空身份快照被正确阻止冻结，后续通过正规Identity revision API和新Unit建立非空快照，旧快照/历史不改写；具备完整上下文的新Unit通过v4本地包。Graphic是真实本机Chromium画布渲染，Video是ffmpeg五秒色块夹具，不证明真实Provider/专业工具内容质量。
- 修复同节点POST在途时自动结果GET早于持久claim的404竞态，仅增加局部ref守卫；独立静态复核APPROVE，浏览器新Run回读无竞态404。未放宽Unknown、原Run/key/node或Preview hash保护。旧render输入证明422且零部分Master/Event写入、过期Master新授权409、素材撤权后Graphic/Video package409均验证。
- 本轮新鲜TypeScript/Vite/FE-P1 PASS：/projects224.22kB raw/72.74gzip，commonProduction282.44/90.16，Text lazy609.20/190.37；范围Ruff、OpenSpec strict36/36、diff-check PASS。只关闭10.6/16.1/16.2/16.3/16.5/17.6/18.6，不关闭未执行的完整backend/永久测试/正式启用。
- 最新媒体继续批：32组受控API/浏览器检查PASS。图片@3采用版本接线修正；Graphic增加显式刷新项目素材，保留dirty；脚本/镜头→TTS→素材→明确Video Master保存；Director方法candidate→saved→另一个Video Unit明确复用；脚本采用后自动准备精确Director包、不派发。两项窄源码复核APPROVE。浏览器0 page errors；Text调Prompt/模型/候选数后一次显式运行与Preview hashes相符。仅受控夹具，不冒称真实模型或专业工具质量。
- 最新TypeScript/Vite/FE-P1 PASS：/projects224.22kB raw/72.75gzip，commonProduction282.44/90.17，Text lazy609.20/190.38；范围Ruff、strict36/36及diff-check PASS。未新增永久测试或跑完整backend。关闭6.8/8.6/17.1–17.5/18.1–18.3/18.7。
- 此前继续批：保存调整/默认隔离API、范围与撤权API、人工调整浏览器、新Run继承/并发采用及下游stale共24组隔离冒烟检查通过；浏览器0 page errors/0 Stage run POST。独立窄范围源码复核APPROVE。仅据此关闭7.9/12.7/13.5/16.6；没有新增永久测试或运行完整后端。
- 独立 backend/data/security、domain/Master/Agent、frontend 三组静态代码复核均 **APPROVE**；发现的自然语言 purpose、只读投影深度、跨面板版本/dirty 同步、调优接受反馈与 typed error 问题已修复并复核。
- 最新 TypeScript/Vite/FE-P1 **PASS**。/projects 224.22 kB raw /72.74 kB gzip；common Production 282.44/90.16；Text lazy closure 609.20/190.38。TipTap 与 Stage 面板保留 lazy，Graphic/Video 和无关首包不引入 TipTap。
- 统一隔离 Mock 浏览器 **9 gates PASS /0 page errors**，只产生1次浏览器显式 run POST；另4个 Text/Video/Variant/Director lazy 回读入口 **PASS /0 page errors /0 run POST**。
- API 冒烟通过三形态3候选/显式编辑采用/同请求精确回放，历史反馈、方法候选/晋升/复用、默认保存隔离、调优→项目新版本→新 Run、Human 审阅、Variant 显式保存和 Director 包准备/接受/回放。
- Text Stage → 修改采用 → checks → Candidate v4 → 显式处置 warning 后审批 → copy_package ZIP **PASS**，ZIP manifest.json/content.md/publish-guide.md 与冻结正文一致。仅本地包，不公开发布。
- 无配置的媒体路由诚实返回 unavailable，不生成假素材；缺事实/Brief、语义模型不可用、legacy profile、旧 context 或不支持的结构均保留真实阻塞/warning。
- 范围 Ruff、OpenSpec strict 和 whitespace 最终结果见 progress.md。本批**未跑完整后端**；此前1908 passed/28 skipped 是历史证据，不代表本次新增范围验收。

最新完整旅程证据：`/tmp/aicontent-recipe-journey.CbtUHx/`（私有SQLite/素材、Text/Graphic/Video页面截图与三个package.zip，实际物理目录为`/private/tmp/`）。末尾撤权负向检查有意保留在私有库；已下载的冻结ZIP保留原字节。此前媒体/控件证据：`/tmp/aicontent-recipe-media.Wmmtm2/`（私有SQLite/素材、Graphic明确绑定、Video TTS和Text实际Preview截图）。此前人工调整浏览器证据：`/tmp/aicontent-recipe-preserve.jDklos/authored-learning.png`，同目录保留范围/新运行隔离副本。前批浏览器证据：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-recipe-browser-xlUmK3/`。原隔离 API fixture：`/tmp/aicontent-recipe-final.pY3pqr/studio.db`，没有正式凭据或 Alembic ledger，不作为迁移证据。

## 待完成 / TODO

3项：19.4新增范围永久回归、19.6包含完整backend的最终全量门禁、19.12生命周期复合项。19.12正式迁移子步骤已授权完成，canonical/archive/commit/push未执行；永久测试/full backend按用户决定延后，不用受控检查代替或宣称全部144完成。

本批新增的 `media.generate@3` 只负责有限画面比例的确定性参数接线；新Graphic生产流程明确固定@3，默认比例1:1，Workflow定义保存校验复用同一请求转换器。旧Workflow定义、`media.generate@2` 和历史运行保持不变。真实 Provider 生成质量和远端能力仍需单独验收。

当前正式库已升级crs并恢复原API/Worker和本机Web。升级前缺列时Stage入口503的验证保留为历史；未正式调用模型/公众号、写新内容或素材、canonical sync/archive、commit/push。旧Unit只读保持原绑定，用户明确选择新流程后才能进入阶段执行。

## 目录结构

- proposal.md / design.md / tasks.md：范围、契约与144项实施/验收。
- specs/：9份 delta；未覆盖 canonical 历史要求。
- C2C_HANDOFF.md / PACKAGE_MANIFEST.json：原始交接与清单；来源记录不代表当前执行状态。
- task_plan.md / progress.md / findings.md：本 change 的独立计划、进度和证据，不覆盖根 F8 文件。
- 原来源包 `openspec/AIContentStudio_creation_recipe_stage_control_loop_OpenSpec/` 保持不变。

## 关键设计决策

Workflow 保存流程，Capability Memory 保存可复用方法。Preview 不调用外部系统；执行重新解析并核对精确 hash。接受后自动续跑不等于自动采用、审批或发布。原节点版本、v1/v2/v3/v4/v5 历史、权利/证据/渲染门禁和 Unknown 不自动重发保持不变。

自然语言创作目的进入实际 Prompt，而 LLM 路由 purpose 固定既有 generate，不能把自然语言当路由 ID。只读合同投影分段验证，不放宽 executor 输入/receipt 的有界 canonical hash 规则。

## 依赖与启动方式

复用本机SQLite/素材、原API/Web/必要Worker和ACO，无服务器化依赖。唯一additive crs迁移只加两个nullable Attempt字段，已按4.7明确授权完成。当前head/配套备份见启用记录；启动/日志仍沿用根README与运行手册。

此前功能冒烟仅18331/15331；本轮另行授权后正式8000/5173恢复，只读验证未运行生成。构建仍为apps/web的`npm run build`，本轮未重跑；新鲜门禁为范围Ruff、`openspec validate --all --strict`及`git diff --check`。

## 实际使用技能

using-superpowers、openspec-apply-change、writing-plans、executing-plans、dispatching-parallel-agents、subagent-driven-development、requesting-code-review、receiving-code-review、systematic-debugging、verification-before-completion。用户最新指令覆盖逐项 TDD 节奏，本批不新增测试代码。
