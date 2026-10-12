# Creation Recipe Stage Control Loop 实施计划

## 2026-10-06 集中实施节奏（用户最新授权）

### 正式本机启用（本轮明确授权）

/// 核对正式SQLite/素材/Worker空闲与精确schema→停原API/Worker建立0700配套备份→副本演练aco到crs并比对全部历史行/素材hash→正式显式upgrade crs→对齐readiness目标并恢复原服务/本机Web→只读页面与健康回读→记录141/144，不执行模型/公众号/提交归档。

- [x] 核对正式库aco、代码crs、identity全NULL/inert；Worker active/reserved/scheduled及四队列均0。
- [x] 配套备份和副本迁移，验证原列数据/计数、既有FK异常集合、素材hash均不变。
- [x] 正式crs升级及approved/readiness目标校准，保持APP_ENV/auth/凭据/素材/Worker拓扑。
- [x] 恢复API/Worker，启动仅loopback Web，完成只读产品入口/历史/健康验证并记录。
- 用户仍暂缓19.4永久新回归及19.6完整backend。本轮仅授权备份/正式crs启用；canonical/archive、commit/push和真实Provider/公众号发送仍不执行。

### 本轮继续：剩余完整旅程统一冒烟

/// 读取剩余契约和既有入口→复制上批私有SQLite/素材到新的隔离夹具→统一验证Text创建/方法调节/审阅/Checks以及Graphic-Video渲染冻结/Review/本地包与Director回接→仅在发现具体断点时最小修正并独立复核→记录新鲜门禁和实际完成项，关闭私有服务。

- [x] Text从想法/Project上下文到Recipe、方法Preview、拒绝/修改接受/一次自动接续、Checks与run-only调整。
- [x] Graphic/Video真实本地渲染字节、精确Master/Candidate/Review/package，以及Director受控回接浏览器。
- [x] 集中review和规定轻量门禁，按证据更新tasks/progress/findings/README。
- 本轮从133/144继续；不新增永久测试、不跑pytest/完整backend，不读正式凭据、不调用真实Provider或公众号，不改正式库/素材/服务，不提交归档。
- 本轮结束140/144，剩4.7/19.4/19.6/19.12；不代关永久回归、完整backend或正式启用/规格生命周期门禁。Text检查真实保留warning，严格checks Stage停在blocked；接受的是人工临时调节后的内容，不把warning改成pass。

### 本轮继续：Graphic / Video 与媒体完整接线

/// 定向复核已有媒体Stage解析/ProviderGenerationTask/结果采用及Graphic-Video编辑入口→仅补已批准合同缺失接线→私有SQLite和素材副本完成受控图片/TTS/视频请求、Unknown回放、明确接受后Master绑定与方法复用→集中源码复核与统一构建/规格/格式/浏览器冒烟→只按实际证据勾验收任务。

- 不新增永久测试文件，不运行pytest/完整后端；模型与媒体仅使用显式标记的隔离受控实现，不能把夹具冒充真实Provider质量或远端能力。
- 不改正式SQLite/素材/凭据/服务，不迁移正式库、不提交、不归档。旧ACO/F8和原包保持现状；本轮从122/144继续。
- 文件边界优先已有stage_domain_integrations/stage_domain_adoptions与StageDomainResultPanel/ProviderMediaPanel；只有查到具体合同断点才修改业务代码。
- 已复现@3图片Stage接纳断点：解析/执行传入allow_aspect，采用校验漏传版本。只让采用校验按冻结node.plugin_version==3开放同一比例转换，不放宽@2；统一受控冒烟验证后再关闭任务。
- [x] 图片/TTS/视频的精确请求与持久Task/Attempt、Unknown不重发；@3采用和Task篡改边界验证。
- [x] Graphic/Video采用、独立Master保存、历史与导演方法跨Unit显式复用；页面刷新保留dirty。
- [x] 两项窄源码复核APPROVE，32组受控API/浏览器检查、构建/预算/格式/规格门禁，更新change记录。

### 本轮继续：有效调整与版本隔离

/// 复核13.5/12.7及上次中断的Graphic模板接线→补齐无参数差异时明确人工编写指令/选择方法的预览保存入口→区分已执行override与尚未实测的人工调整→在私有SQLite副本统一冒烟验证内容修改不推断patch、目标CAS/范围隔离、回放不重复与原Attempt不变→代码复核及Web/规格/格式门禁→按实际证据更新任务。

- 本轮不新增测试文件、不跑pytest或完整后端；所有数据库写入仅在隔离副本，不读取正式凭据、不调用真实Provider或公众号。
- 仅维护本change记录；main已有ACO/F8修改保留，不执行正式启用、canonical/archive、commit/push。

- [x] 补人工instruction/method路径，未实测来源标记、方法参数与Contract接线。
- [x] 独立代码复核提出方法live gate与默认scope问题，修复后定向复核APPROVE。
- [x] 24组统一隔离API/浏览器/并发/回滚/stale检查；构建/预算、Ruff、strict/diff通过。
- [x] 按证据关闭7.9/12.7/13.5/16.6；当前122/144、剩22，不代关真实媒体、永久回归、完整后端或正式启用。

### 继续批：剩余接线与统一冒烟

/// 定向核对媒体比例实际消费链与Director回传入口→补必要接线→从当前aco正式库只读备份到私有隔离副本演练crs迁移及素材恢复→集中代码复核→一次隔离媒体/Director/反馈冒烟→按证据更新任务，不运行pytest或新增测试代码。

- 正式SQLite、素材和运行服务只读；隔离副本的升级不代表正式启用。媒体/Agent只用明确标记的受控夹具，不调用真实模型或公众号。
- 不覆盖ACO/F8记录，不归档、不提交、不push。完整后端、永久新增测试与单独授权门禁继续保留。

### 前批交付状态（118/144 历史记录）

/// 剩余领域接线与前端/反馈/沉淀集中实现 → 三组独立源码复核 → 修正发现 → 一次统一构建和隔离冒烟 → 实施项118/144，剩26项保留后续验收/启用。

- [x] Text/Graphic/Video 提案和采用、媒体/检查/Human/Variant/Director Stage 统一接入既有真源。
- [x] Feedback、保存到项目/默认/方法、精确方法复用、可选 AI 调优和 lazy 日常界面接线。
- [x] 独立 backend/data/security、domain/Master/Agent 与 frontend 静态复核；发现修复后定向复核通过。
- [x] TypeScript/Vite/FE-P1、范围 Ruff、OpenSpec strict36/36、统一 Mock API/浏览器冒烟。
- [ ] 新增范围永久负向回归、跨模型/真实媒体/专业执行完整旅程、完整后端与迁移/恢复验收。
- [ ] 正式库启用、canonical sync/archive、commit/push：本批未执行，不以隔离冒烟代替授权或验收。

历史计划里的逐项TDD/全量测试步骤仅描述已结束的旧批次，不是本批执行口径。具体证据和未完成项见 progress.md/tasks.md；原包、根F8记录和正式服务未动。

### 领域 Stage 接入实施片段

/// 固定新插件契约及领域纯解析→共用 Stage claim 后委托既有生成/适配/校验/Package服务→显式采用时在领域事务内写 association 与父执行者 feedback helper→只读结果恢复与接受依赖证明→汇总给主执行者统一 review/smoke。

- 写入范围为 nodes 描述、creation_recipes、stage_domain_integrations、stage_domain_adoptions、stage_integrations router；只为事务回调窄改 generation_tasks/channel_variants。
- 不运行测试、构建、运行时、DB、供应商、远端或提交；本片段不把未验证功能标为通过，也不归档整个 change。

/// 并行完成互不重叠的Master多形态/现有领域Stage接入/专业结果UI→串联反馈、下游stale和保存有效调整→整批代码复核并修正→统一构建、规格静态门禁和功能冒烟→按真实证据更新状态。

- 暂停逐项测试与逐环节确认；本批不新增测试代码、不运行逐项pytest，既有结果仅作为历史证据。
- 先集中串联当前OpenSpec的功能范围，再统一代码review与功能冒烟；缺少正式运行授权的启用/迁移/外部调用不以实现完成代替验收。
- 并行写入范围：Master proposal/adoption；媒体/校验/渠道/专业执行Stage；Recipe及结果前端；主执行者负责反馈/沉淀/方法复用/汇总集成。不覆盖彼此或既有ACO/F8改动。
- 不升级正式SQLite，不改运行凭据，不发送公众号草稿或真实模型请求，不提交/归档/push。正式启用依然按4.7的独立授权处理。

> 使用OpenSpec与Superpowers writing-plans维护本change记录；审定后用executing-plans按批推进。此文件不覆盖根F8进度记录。

**目标：** 把既有Workflow、Master、Material、Variant、CreativeExecution和Capability Memory串成可调节、可预览、可接受、可显式沉淀的创作闭环。

**架构：** Workflow仍是唯一流程真源；Effective Stage Resolver统一Preview与执行身份；Attempt保存Proposal/receipt，人工接受通过现有服务写入正式版本。无Recipe/Feedback/Improvement新表。

**技术栈：** 现有FastAPI/SQLAlchemy/Alembic、SQLite与本地素材、React/TypeScript/Vite、现有Workflow/LLM/Provider/MCP机制。

## 当前审计与归位

/// 全读原稿16文件→只读核对真实基线及Phase0证据→创建标准change并完整保留9delta→修两个缺失场景→strict/diff与独立SPEC复核→只确认一个执行节奏→用户确认后apply。

- [x] 全读README/C2C/manifest/.yaml/proposal/design/tasks/9specs。
- [x] 核对main@341ead8、已有dirty ownership与关键真实代码；不动原包/ACO/F8/根记录。
- [x] 归位标准change与本地记录，仅做语义等价格式修正。
- [x] 收到完整独立SPEC复核：6处执行契约需修正，未把格式PASS当语义批准。
- [x] 定向核对真实advance/输入映射、Master/Variant内部commit和旧output association，修正规格及对应任务，不写业务代码。
- [x] 修后strict36/36、tracked/19owned空白检查；独立定向复核六项全部closed，有条件APPROVE（仅执行节奏待用户决定）。
- [x] 用户确认接受后自动执行下一阶段；自动请求由服务端纯解析并记录，同样核对expected hash，到下一次人工确认/阻塞停下。
- [x] 审定后进入业务apply，CLI apply state ready，144任务逐项按证据勾选。

## 业务批次（确认后执行）

/// 继承Phase0的aco/null-inert/108回归→Recipe与Stage Contract/Resolver/Preview→Attempt additive receipt与本次override→Text3候选/接受Master/反馈/项目Recipe保存/下次Run/Review/ZIP→Graphic/Video/媒体/Variant/Execution→默认/方法与确定性改进→可选AI调优→全链路/兼容/安全/性能门禁。

1. Phase0核验：`app/db.py`、ACO四测试与runbooks，仅复核已有修正，不重复迁移真实库。
2. 核心批：`content_harness/contracts.py/registry.py`、`project_workflows.py`、`workflow_engine.py`、`models.py`及project-scoped API，Stage真执行与纯Preview；仅隔离库additive迁移。
3. Text闭环批：复用`content_masters.py`、text document/modality adapter及LLMRun；生成只留Attempt，明确采用才保存Master/ProjectWorkflowOutput/反馈。
4. 跨形态批：复用ProviderGenerationTask、ChannelVariant、CreativeExecution/Director各真源，不造第二套生成/执行引擎。
5. 沉淀批：复用Workflow Override/default portability与Capability Memory，所有保存都展示diff并要求确认，不自动改图/gate/权利。
6. UX与门禁批：Production Stage-first，原高级图保留、dirty独立、lazy隔离；完整回归、实际浏览器、迁移/恢复和独立复核。

实施时必须先封闭：成功Proposal与接受依赖分离；expected preview hash＋持久Attempt发送前claim；接受的结果/refs/association/feedback原子CAS与幂等；原Attempt不插入后产生的Master ID；旧plugin版本不隐式激活Stage；内容修改不自动推断配置patch。接受后按用户决定自动继续，但不自动接受下一个结果或绕过专业工具/审批/发布门槛。

具体步骤/文件清单在规格审定后细化；不新增示例代码，不以文档齐备冒充144项已实现。正式启用/归档/提交/push仍按各自授权。

## 批次一：纯解析与注册契约（当前执行）

/// 校准健康检查的隔离夹具→永久测试先失败→StageContract严格配置/消费清单→纯ResolvedStageExecution→Recipe读模型和project-scoped Preview→兼容/零调用/权限回归→独立复核与全量门禁→只勾真实完成项。

1. `apps/api/tests/test_observability.py`：基线失败因内存夹具无Alembic ledger；只让成功探针使用明确approved head，补无ledger应503的回归。不改正式readiness。
2. 新建`apps/api/tests/test_creation_recipe_stages.py`：真实Registry/配置校验/纯Resolver和API测试。先运行观察缺失功能失败，再实现；Provider/Agent调用以失败哨兵验证Preview零调用。
3. 新建`apps/api/app/services/stage_contracts.py`，修改`content_harness/contracts.py`、`registry.py`：不可变有界契约，所有普通控件和tunable字段必须在executor消费清单，未知/非法配置及override拒绝；旧plugin无contract不改。
4. 新建`apps/api/app/services/stage_resolver.py`：统一canonical JSON、精确身份与各层hash、参数override、prompt层、阻塞原因、expected-hash门槛；任何密钥/credential URL不能进入结果。
5. 新建`apps/api/app/services/creation_recipes.py`，修改`routers/content_projects.py`：只读有效Workflow、历史版本、stage/run/attempt/accepted projection；Preview取真实项目上下文/精确方法/模型路由，不调用生成器。旧节点返回Advanced/不支持Preview，不能伪装已支持。
6. 如需修改`project_workflows.py`，仅增加已注册且显式pin Stage Contract的新plugin验证路径，绝不放宽旧图/副作用/portability规则。
7. 验证：`uv run pytest tests/test_creation_recipe_stages.py tests/test_observability.py tests/test_workflow_registry.py tests/test_fe_f2_workflows.py -q`；`uv run ruff check`本批文件；完整backend；`openspec validate --all --strict`；`git diff --check`。

本批不新增迁移/ORM列、不对正式库发请求，不完成UI或执行claim/人工采用；这些仍归后续批次。根F8记录不改。

### 首批门禁

- [x] 合同/模型/方法/权限/证据/旧入口负向先失败后修复，59项永久Stage案例。
- [x] 定向96 passed、完整1828 passed/28 skipped；范围Ruff、strict36/36、diff-check。
- [x] 原包16文件逐一未变；无迁移/真实库/运行配置/外部调用。
- [x] 独立实现复核APPROVE（三项发现、证据完整性和七个旧入口防绕过均闭合；不包括后续claim/采用/UI）。

### 下一批计划（已获业务实施授权）

/// 先隔离库证明nullable receipt与旧schema兼容→发送前原Step/Attempt持久claim→exact preview/hash与幂等防重→Text propose真实消费参数→采用Master/refs/association/feedback单一事务→从已提交接受结果准备并记录自动下一Stage→定向与全量门禁。

正式aco库不自动升级；新增字段读取/legacy写入必须有旧schema兼容边界，不得让未启用的新功能破坏当前本机使用。真实执行与自动续跑验收完成前不勾3.9/4.x/7.1。

### 批次二实施细化（先回执与防重，再 Text Proposal）

/// 先读旧 schema/隔离迁移→写持久 receipt 模型与兼容探针→用 TDD 固化 claim/idempotency/expected-hash/override→接入一个只返回 Text proposal 的真实 Stage plugin→只做 proposal，不写 Master、不调用正式模型；每一小段完成后跑定向回归，再进入下一段。

**A. 迁移与旧库兼容（4.1–4.7）**

- 新增 `apps/api/alembic/versions/crs000000001_stage_attempt_receipts.py`，down_revision=`aco000000001`，只给 `workflow_step_attempt` 增加 nullable `input_snapshot_json` 与 `execution_receipt_json`；两列均使用 JSON、默认 NULL，不回填旧行，不创建第二张执行表。
- ORM 两列使用 deferred + nullable + server default NULL，旧 ACO schema 的普通读写不触发新列查询；Stage receipt path 先检查真实列存在，不存在时返回可识别的 unavailable/upgrade-required 错误，不写用户数据。
- 迁移在隔离 SQLite 上验证 up/down/up、旧行保留、非空 receipt 阻止 downgrade；正式 `apps/api/content_studio.db` 不升级。

**B. 持久 claim / execution receipt（3.9、4.3–4.5、5.1–5.6）**

- 新增 `apps/api/app/services/stage_invocations.py`，只允许已解析的 Stage Contract plugin 进入；显式 run/rerun 必须携带 `run_id + node_id + invocation_key + expected_resolution_hash`，自动 successor 只能复用服务端已保存的 prepared resolution，不能伪称用户重新预览。
- claim 先在同一个事务中持久化原 `WorkflowStepAttempt` 的输入快照和不可变 receipt，再允许外部调用；receipt 包含 workflow/node/plugin/contract/config/override/method/model/prompt/upstream/output contract 与 route/adapter/runtime 身份哈希，不含密钥、URL、provider 原始错误或 raw output。
- receipt 的最小可重放字段固定为 `schema/request_mode/prepared_by_server/invocation_key/request_fingerprint/run_id/workflow_id/node_id/plugin_key/plugin_version/stage_contract_hash/resolution_hash/config_hash/prompt_hash/upstream_hash/model_route_hash/runtime_identity_hash/output_contract/dispatch_certainty`；状态为 `running → succeeded|failed|unknown`，确认未发送用 `status=failed + outcome_state=failed_before_dispatch + dispatch_certainty=not_dispatched` 表示，不能把超长业务语义塞进现有 20 字段。
- 列探针只读取 `inspect(bind).get_columns("workflow_step_attempt")`，必须同时发现两个新增列才启用 Stage receipt path；探针不缓存跨连接结果。缺列返回 503 `stage_receipt_schema_upgrade_required`，不显式 select/update 新字段、不写用户业务数据；legacy path 继续依赖 ORM 的 deferred/server-default NULL。
- 同一 `(run_id,node_id,invocation_key)` 对应不同 `request_fingerprint` 一律 409；同 key 同 fingerprint 返回原 Attempt；不同 key 只有显式请求可以创建新 attempt，automatic 请求遇到任何 `unknown/possibly_dispatched` 先 409 reconciliation，禁止自动重发。SQLite 的 claim 以持久行和 CAS 终态为事实，不能只靠内存锁。
- 本批 Text proposal 只允许隔离 fake provider/哨兵测试实际消费解析后的 request；不连接正式 CPA、MiniMax、公众号或任何真实外部模型。真实 provider 适配和正式运行调用留到单独授权的后续验收。
- 相同 invocation key/fingerprint 的响应丢失重试只返回原 claim/最终结果；不同 fingerprint 冲突；`unknown`/`possibly_dispatched` 永不自动重发；确认未 dispatch 才允许记录 `failed_before_dispatch` 语义并由用户新 key 重试。
- run-only override 只接受 Stage Contract allowlist tunable fields，校验默认值与 override 后 canonical config；不允许改 plugin/version/graph/dependency/mapping/evidence/rights/gate/side-effect。
- 现有 legacy workflow start/advance/complete/retry/rerun 行为继续保留；新增 receipt path 在旧 schema、旧 plugin 或非 Stage Contract 节点上 fail closed，不把普通节点静默升级为 Stage。
- 现代 Stage Run 只允许全量由已注册 Stage Contract 节点组成的 Workflow；混合旧节点定义 fail closed，避免以 Stage 入口绕过 legacy 执行语义。

**C. Text proposal plugin（6.1–6.8 的后端最小闭环）**

- 新增版本化 `stage.master.propose@1` Stage Contract 与 registry plugin；先只实现 Text v2 proposal，保留 `builtin.generate` 原语义，Graphic/Video 后续批次接入。
- executor 只消费 Effective Stage Resolver 的实际 instruction/model/method/candidate_count/length 等字段，返回 1–5 个 bounded `stage.master.proposal.v1` 候选和稳定 hash；Proposal 只写 Attempt output/LLM receipt，不写 `ContentMasterRevision`、`ProjectWorkflowOutput` 或 Candidate。
- 模型调用通过既有 provider/model routing，测试使用隔离 fake provider 哨兵证明 preview/expected-hash 冲突不调用外部；正式运行配置、真实模型、正式素材库不触碰。
- 本批只完成 stage contract、claim、proposal receipt 与定向 API/service tests；Master adoption、自动下游执行、Material/Variant/CreativeExecution、UI 与正式迁移验收留到后续批次。

**批次二已落地（本地未提交）**

- crs000000001 已在隔离 SQLite 完成 up/down/up；旧 Attempt 保持双 NULL，任一回执非空时拒绝 downgrade。正式 SQLite 未升级。
- Stage Run 新增显式 run_id + expected_resolution_hash + invocation_key 入口；领取回执先提交，再调用 Stage executor；同 key 重放复用原 Attempt，冲突和 unknown/possibly-dispatched 自动重发均 fail closed。
- stage.master.propose@1 已注册并只生成 bounded Text v2 proposal；成功停在 waiting_input，不写 Master/Variant/Candidate；Provider 失败按可能已 dispatch 进入未知处理。
- 本批定向回归覆盖 69 项并通过；范围 Ruff 通过。全量 backend/OpenSpec/diff 门禁待本批文件稳定后执行。

**批次二补强（当前执行，先校正过勾再验收）**

/// 恢复LLMRun持久断言并查清事务回滚→现有Step数据库锁序列化claim→running重放只回读不发送→CAS封存及Step投影同事务→服务端输入快照与safe错误→精确模型与有界输出校验→旧ACO ORM兼容→定向/全量与独立复核→按真实范围更新任务。

- [x] 修复schema探针通过Engine第二连接回滚SQLite未提交LLMRun的问题；测试必须证明真实行仍存在。
- [x] 序列化同Step竞争，领取者才可调用provider；unknown和未决claim只能协调原Attempt。
- [x] 输入由服务端解析冻结，终态CAS及当前Step投影同事务，不泄露provider错误。
- [x] 核验Preview实际prompt/模型runtime与发送一致；拒绝空/超量/外来引用候选，不伪造正文。
- [x] 在隔离旧ACO schema证明legacy ORM读写；修正4项过勾，UI/自动续跑仍未实现，采用后端已实现。

### 批次三完成记录

- [x] `accepted` 上游只读取经过 `ProjectWorkflowOutput + creation_recipe.stage_feedback` 证明的精确实体、revision/hash 和 decision；成功但未接受的 proposal 继续阻塞。
- [x] 接受事务提交后，服务端按 `visual_order` 选择依赖就绪的下一 Stage，准备真实 resolver 输入并复用相同的 expected-resolution/持久 claim 门禁。
- [x] 自动请求保存 `request_mode=automatic` 和 `prepared_by_server=true`；同一接受重放复用原自动 invocation，不重复模型调用；到下一次 review、失败、未知或不可用即停止。
- [x] 新增 `test_creation_recipe_continuation.py` 三项永久回归；相关 Creation Recipe/receipt/proposal/adoption 测试共108项通过。
- [ ] Stage Result UI、完整控制窗口、accepted-with-edits 下游 stale、跨形态及浏览器闭环仍未完成。

- [x] 3.1/3.5/6.3 的服务端证据补齐：纯 Resolver、显式模型路由失败、当前 Unit/上下文/accepted 上游投影均已覆盖并收口。

**D. 批次二验收出口**

- 必须有持久测试覆盖：旧 ACO schema 读写兼容、receipt 字段 bounded/secret-safe、expected hash drift、same-key idempotency、conflicting fingerprint、possible-dispatch no-auto-retry、override allowlist、Text proposal 不写 Master。
- 任务勾选只按实现证据更新；本批不勾 3.10、4.7、5.6、6.8 或 7.x，除非对应完整契约与定向回归已经实际完成。

### Text 人工接受：本批后续步骤

/// 先写精确候选采用/不可变Proposal/重复回放/失败原子回滚测试→既有Master服务增加内部事务回调（普通保存语义不变）→校验Run/Attempt/候选与上下文/CAS→同事务创建Master、专用输出关联和反馈→仅更新接受投影，不改Proposal→定向和全量回归。

- [x] 接受请求绑定 exact output/candidate/resolution/context hashes、Master expected revision、最终payload/refs和幂等键。
- [x] 服务端生成可信workflow_stage血缘；普通保存不接受伪造血缘。
- [x] Master/refs、ProjectWorkflowOutput、接受ProjectEvent单事务；任一失败完整回滚。
- [x] committed replay先返回原结果，冲突键/旧Attempt/旧context/只读请求拒绝；历史Proposal和LLM receipt保持原样。
- [ ] 自动下游续跑、UI、跨形态和完整Text E2E另按现有未完成任务实现，不提前勾选。

### 批次三：接受后的自动续跑与精确上游证明

/// 先固化“成功不等于接受”、接受目标只认项目输出与反馈的回归→让依赖 `accepted` 的 Stage 读取精确实体/哈希→接受事务提交后由服务端准备唯一自动请求并复用同一 claim/expected-hash 门禁→到下一次人工确认、失败、未知或不可用即停止。

- 不新增 Recipe/Feedback/Queue 真源；沿用 WorkflowRun、WorkflowStep、WorkflowStepAttempt、ProjectWorkflowOutput 与 ProjectEvent。
- 自动请求只使用已提交接受结果构造，保存 `request_mode=automatic` 的原始 claim；同一接受事件重放不得重复调用。
- 自动续跑不自动接受候选，不绑定媒体，不调度专业工具，不冻结 Candidate，不审批、不发布。
- `unknown`、可能已 dispatch、上下文漂移、归档/只读和不支持的旧节点全部 fail closed。
- 本批只覆盖 Text Stage 的真实后端闭环；完整 Stage Result UI、媒体/Variant/CreativeExecution 仍按后续任务处理。

### 批次四：Creation Recipe 日常控制入口

/// 先把现有 Recipe 投影接入 Production 默认工作区→阶段条/阶段细节→契约声明的临时调节→服务端 Effective Stage Preview→执行回执；高级画布继续保留，不改变旧 Workflow 语义。

- [x] Production 默认显示阶段条与阶段详情，保留当前 Content Master 编辑器；原始画布继续位于高级自动化入口。
- [x] 阶段读模型展示节点身份、插件/版本、状态、依赖、最近 Attempt、精确 accepted target 和阻塞提示；本次临时调节保持客户端未保存状态。
- [x] Stage Contract 控件从服务端声明生成，不显示未声明字段；Preview 展示 base config、temporary override、effective config、模型/方法/上游及 resolution hash。
- [x] 执行前必须经过 Preview；执行请求继续携带 expected resolution hash 和稳定 invocation key。
- [x] 接受后续跑绑定本次精确 ProjectWorkflowOutput/Attempt/hash/decision/context；阻塞可回读，进程中断的 running claim 必须显式 reconcile 为 unknown，不自动重发。
- [ ] Stage Result Review 的候选选择/接受 UI、accepted-with-edits stale、跨形态 Stage 和完整浏览器验收仍未完成。

### 批次五：接续安全与真实请求窗口

/// 先用永久回归复现外来Attempt/接续误完成/上下文漂移→最小修复精确采用证明和状态投影→展示真正prompt_sections及保存配置→临时调节按阶段保留并使旧Preview失效→隔离定向/全量与Web/strict门禁→只按完成范围更新任务。

- [x] 恢复入口拒绝不同Run/Step/Node的Attempt，未知/失败投影不被接续改成普通blocked。
- [x] 接续回放显示原waiting/blocked/unknown状态；接受的实际正文进入有界上游请求，上下文漂移不执行。
- [x] Recipe显示来源/版本/默认差异、可回读阻塞；阶段切换保留本次调节，控件改变立即作废旧Preview。
- [x] 实际请求窗口展示服务端system/user与分层Prompt；重试保持同一invocation，明确新生成使用新key。
- [x] 定向与全量后端、TypeScript/Vite/FE-P1、范围Ruff、strict与owned文件空白验证；无真实库升级或外部调用。

### 批次六：Text候选查看与显式接受

/// 先用API回归证明只读结果必须绑定本项目Run/Stage/Attempt→复用原回执/快照供刷新查看，不再调用模型→候选选择和结构化本地编辑→精确幂等采用与冲突保留编辑→回读已提交Master及自动接续→隔离Web/API门禁；拒绝反馈和跨形态按未完成项保留。

- [x] 增加project-scoped只读结果入口，原Attempt/安全receipt/实际输入可回读；外来Attempt/旧schema fail closed。
- [x] Text候选选择、局部编辑和显式接受；采用请求绑定原hash/context/expected revision，响应丢失重试保持完整原请求。
- [x] 显示接受后的Master与自动下一阶段，刷新恢复原候选/回执；不自动接受、不覆盖其他Master未保存状态。
- [x] 定向后端/客户端状态测试、build/budgets、strict/diff；不把部分UI记为完整7.1或Text最终验收。

本批独立复核指出刷新恢复前的新调用窗口和跨窗口Run漂移，已先用客户端/隔离浏览器/API回归重现：恢复未成功则只允许只读回读，pending请求优先固定原run_id与invocation_key，返回身份不符不得替换本地状态。Task7.1因拒绝反馈尚未完成保留未勾，7.9的accepted-with-edits下游stale仍待下一批。当前按15.4/15.5/15.6/15.8实际证据为56/144，剩88，不冒称完整Text闭环。

### 2026-10-06：前端 Stage 全量实施（共享 main，实施先行）

/// 保留共享 dirty main→扩展已有四个 Stage 文件的类型/恢复边界→契约模型与方法选择器→三形态 ModalityWorkspace 候选审阅→领域结果显式接受→历史/拒绝/重跑/允许跳过反馈→有效调整 destination/diff/CAS 显式确认→模板选择与方法应用→交父任务统一复核和 smoke。

- [x] `CreationRecipePanel.tsx`、`creationRecipeState.ts`：契约控件、Basic/Advanced、可行动阶段深链、只读和精确请求恢复（实施已交接，未运行验证）。
- [x] `StageProposalReview.tsx`、`stageProposalState.ts`：保留 Text 类型编辑，Graphic/Video 使用现有 ModalityWorkspace；接受请求补 payload_schema（实施已交接，未运行验证）。
- [x] 新小型 lazy Stage 面板：领域结果、历史反馈、保存有效调整/应用方法、显式 Recipe 模板选择及可选显式 AI 调优。只使用父任务/领域任务提供的 API（实施已交接，未运行验证）。
- [x] 同步本 change 进度/发现/README，并列出 API schema 需求；不改独立 Workflow/Master 文件。
- [ ] 父任务统一复核/smoke（本工作者不执行测试、新测试代码、build、运行时/provider、commit；不提前归档或冒称验收）。

### Plato 前端复核三项窄修（2026-10-06）

/// 核对源码与已有版本契约→准备运行仅清执行状态，保留 override→Production 回调/版本信号双向同步已保存流程，dirty 时保留并显式冲突，不重挂 Master→调优接受反馈强制保留且请求前校验→同步本 change 记录并再次冻结，无测试/build。

- [x] `CreationRecipePanel.prepareRun` 保留所有阶段的本次调节，清空 preview/request/result/旧重跑反馈关联（仅实施，未验证）。
- [x] 窄改 `ProductionWorkspace` / `useProductionWorkflow`：Recipe 保存/采用通知高级流程刷新；高级保存通知 Recipe 回读并作废旧 preview；保留 dirty 并显示明确冲突（仅实施，未验证）。
- [x] `StageTuningPanel` 的 acceptedFeedbackId 必选、不能取消，请求前再校验（仅实施，未验证）。
- [x] 用户追加：全部阶段已结束且无 running/unknown/未决请求时，正常 Recipe 可明确准备新 Run；waiting_input 隐藏入口。不改 Master 或历史。
- [x] 更新 README/progress/findings 并冻结；统一验证留父任务。

/// 父任务 TypeScript 错误回传→核对当前第118行 unknown 条件→仅加 != null JSX 守卫→更新记录并冻结，不运行测试/构建。
- [x] StageDomainResultPanel 第118行 unknown 条件窄修；无 as any；父任务统一验证仍待重跑。
