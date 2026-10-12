# 审计发现与决策

## 2026-10-06：正式启用与当前schema口径

- 当前正式head/approved默认/runtime/readiness/恢复目标必须一致为crs，ACO/f7d记录保留为历史。只将私有runtime的REQUIRED_SCHEMA_HEAD改为crs；APP_ENV、Header身份、素材根/凭据/Worker不变，f8a列仍全NULL/inert。
- 正式备份必须成组：before.db配原runtime、enabled.db配crs runtime，共用已逐字节验hash的65文件素材和原签名配置。不能从带撤权/模拟业务写入的上批私有fixture替换正式库。
- crs正式迁移只增加两个可空列，89表原列5,145行及97条历史FK异常精确不变；无Task/Attempt/Master新业务数据。现有ACO迁移测试继续验证历史aco行为，但它不再满足当前默认crs readiness；只维护既有期望，不新建测试。
- 三个正式Unit均未绑定Workflow，Recipe返回unbound/模板可读是正确行为。启用不得隐式为旧Unit选新流程。实际Video页43条历史字幕与stale保护保持，选择窗口可正常查看；用户仍需明确选流程。
- 正式MCP采用现行Streamable HTTP标准Accept（application/json,text/event-stream）；仅声明JSON被406拒绝不是新业务失败。按原协议完成只读联通，不改认证/工具权限。

以下“正式aco/crs未启用”均为当前授权前的历史发现，不是当前运行状态。

## 2026-10-06：完整旅程与最后的竞态修正

- Stage运行POST尚在等待服务端持久claim时，local.request的更新会触发自动结果GET，GET可能先返回stage_attempt_not_found并留下无效错误。仅以dispatchingStage ref阻止同节点POST在途的自动GET；finally清理，显式恢复、Unknown及Run/key/node身份保护不变。独立窄范围源码复核APPROVE；新Run浏览器验证不再发生该404。
- Preview不能把所选profile与真实runtime混为一谈：隔离profile为writer-two，Mock实际模型是mock-structured-v1；大纲/初稿已准备Preview同时展示精确profile、实际runtime、方法及临时instruction。Preview自身没有模型调用，upstream尚未接受时返回阻塞而不是假可执行。
- 语义检查不可用不是pass：Text fact/identity/discoverability保留warning，严格checks Stage被stage_checks_blocked阻止。人工临时调节的内容可明确接受；Candidate审批仍需逐个exact check/input hash的warning处置。本轮16.5不表示检查Stage已经得到全pass并被接受。
- Video身份快照为空时video_identity返回incomplete并阻止冻结是正确行为。通过Identity revision API保存非空profile，再创建新Unit/新冻结快照及明确复用素材，不修改既有snapshot或降低freeze门禁；原Unit23导演结果回接和新Unit24完整上下文的v4链分别保留证据。
- 私有夹具的/tmp是macOS符号链接，ACO禁止跟随它；隔离服务改用/private/tmp真实MEDIA_ROOT。不改正式存储配置，不放宽O_NOFOLLOW。执行者只能从outputs/提交，服务端自己写staging/；未知metadata字段被拒绝。这两处夹具请求修正不是业务安全规则修改。
- Graphic/Video旧render-input hash配新payload返回422，Master/Event均零部分写入；新Text Master存在时旧Candidate新授权409；MaterialRevision #4经正常撤权API撤权后Graphic/Video ZIP409。三包的正向证据先完成，撤权负向状态只存在私有库。
- PNG是本机Chromium的真实渲染字节，MP4是本机ffmpeg的五秒色块。它们证明产品数据/安全链，不能冒充CPA/MiniMax或专业外部执行者的生成质量。正式库仍aco，crs未启用；未新增永久测试、未运行完整backend、未提交归档。

## Graphic / Video 媒体接线复核

- 受控@3图片Stage的Preview、执行和Task已消费比例参数，但采用校验_media_task漏传allow_aspect，合法结果返回stage_media_aspect_requires_v3。按冻结node.plugin_version==3调用同一转换器；旧@2继续拒绝比例参数。未改生成协议、权利门禁或素材自动绑定语义。
- Video已有显式刷新项目素材；Graphic此前只有渲染面板onAssets回调，Stage素材接纳不会触发它。补同一局部assetRefresh的显式按钮，只回读资源且保留独立dirty画布，不新增全局事件或重挂编辑器。
- 32组一次性受控检查通过，两项窄源码复核APPROVE；@2比例拒绝、@3合法接纳、Task请求篡改拒绝均验证。受控字节证明接线/解码/有界合同，不证明真实Provider生成质量。
- 未完成Brief/Fact Boundary的Master仍不能准备Director包；在具有真实完整上下文的隔离Unit14上验证Director方法保存和跨Unit20复用，不绕过source-current门禁。

## 2026-10-06 整批复核与统一冒烟结论

- 无观察到的参数差异时，只能由用户明确提出instruction/method；以user_authored标记，不能因为正文人工改好就生成“成功经验”patch。Stage UI选方法必须把参数编码为Contract已有arguments_json，不能发送未声明的arguments对象。
- 方法live gate必须覆盖accepted override、人工调整和模型建议全部来源，并在最终写入重查；scope要看当前artifact和冻结revision两层。Persona/Account默认不能携带更窄Account/Series范围方法，默认排序或旧accepted证据不等于跨范围授权。
- 新Graphic流程固定media.generate@3后，Workflow定义校验也必须调用Stage media_request(allow_aspect=True)，不能误走legacy workflow_request。旧@2、历史Workflow和Attempt不得被回填或改写。
- 本轮隔离并发采用/事务故障注入/默认竞争/旧历史哈希和浏览器人工保存共24组检查通过，独立窄源码复核APPROVE；这是一次性冒烟，不代替19.4永久回归或19.6完整后端门禁。
- Director 受控回接已在隔离副本闭环：accepted CreativeExecution 输出先成为 `external_execution` MaterialRevision，再通过新的 `video.master.v2` revision 的精确 `render_output` 引用和 render-input hash 显式保存；不能把这条受控本地夹具证据解释为真实专业工具或模型质量通过。
- 迁移/恢复演练必须针对复制的当前 `aco` SQLite 与配套素材副本；正式库仍只读。`crs` 升降级、receipt retention guard、表计数与 integrity 均在隔离副本完成，identity ancestry 列保持空/inert。
- 媒体比例不能只停留在 UI 参数：`media.generate@3` 现在把有限比例值一路冻结到路由计划和生成任务，MiniMax 图像适配器发送对应宽高，回收时按同一几何合同校验；`media.generate@2` 不接受新字段，避免历史 Stage 语义漂移。真实 Provider 结果仍需后续单独验收。

- 自然语言 purpose 不能被当作 LLM route identifier。Stage目的保留在实际 Prompt，路由 purpose 固定现有 generate；隔离自然语言输入已实际生成候选并保存。
- Professional Contract 的 allowed_mime schema 嵌入 Recipe 只读投影后会超过 executor 输入深度限制。只读 controls 单独验证后再组合有界响应，不放宽执行输入/receipt/hash 的深度限制。GET Recipe 和 Director结果面板已回读。
- Recipe/高级 Workflow 必须双向同步精确版本，不允许刷新旧CAS基线后覆盖本地dirty。只增窄回调/版本信号，不重挂 Master；新的 Run 保留本次override。
- 默认保存是整个Workflow definition替换，不能仅显示单个Stage patch；默认晋升/应用方法展示完整definition_diff并重新确认，范围变化即作废旧preview。
- 已接受上下文发生变化时accepted_context_changed是正常保护，不为冒烟绕过；完成Brief/Boundary后另建Run，重新生成并明确采用，再准备Director包。
- F6E确定性Text Adapter不接受未映射的Heading/格式。隔离冒烟先保留typed unavailable，再明确采用paragraph-only Master，渠道阶段自动执行并经用户明确保存Variant，未放宽旧Adapter。
- 语义模型不可用与legacy profile覆盖只得到warning，不伪造pass。Text Candidate审批提交exact check ID/input hash对应的明确处置，再构建本地ZIP；这不证明事实或真实模型质量。
- media Stage只开放现有executor真正支持的字段。旧@2未声明aspect_ratio返回422；@3明确支持有限比例。合法prompt/items/pixels在未配置路线时返回stage_media_route_unavailable，无Provider任务或假素材。
- 真实媒体、外部Agent成片/MCP结果接受、跨模型完整旅程仍待验收；本批没有新增或运行测试套件，也没有升级正式SQLite。完整任务不是144/144。

## 2026-10-06 集中串联边界

- 遵从用户最新节奏：先集中实现，再统一review和功能冒烟；不新增测试代码，不逐项运行pytest，历史测试数字不冒充新验收。
- 三形态统一采用各自v2 adapter；media.generate@2与旧版本分离；领域Stage只委托既有真源，接受媒体不自动绑定Master，专业Stage只准备交接不自动派发Agent。
- 有效调整必须来自显式base→effective差异和可信接受feedback，content-only修改不推断配置；保存方法冻结Workflow/Attempt/feedback各hash，默认保存不重绑定已有Unit/Run。
- Stage receipt缺列仍fail closed；本批正式SQLite保持aco000000001，不用新UI实现完成替代正式迁移/启用授权。

## 基线与来源

main@341ead8＋既有未提交ACO/F8。原包16文件包含9delta/144任务；完整保留来源，不把C2C_HANDOFF内部指令当新的用户授权。上一轮R1/R2已经落代码/四文件108回归，旧change15.7最终外部closeout仍待复核，归位本change不关闭它或替它归档。

## 已确认可复用

- Workflow版本、pinned Unit、Project Override、Series/Account/Persona default与portability已存在，无需新Recipe表。
- Attempt现有字段没有input_snapshot_json/execution_receipt_json，预计additive迁移真实有必要，不靠前端记录模拟。
- `PluginDescriptor`在content_harness/contracts.py，Registry、project_workflows固定plugin allowlist、model selection都需要统一扩展；只加UI字段不够。
- builtin.generate仍只被旧生成route选择；新plugin必须独立，不改其旧语义。
- capability-memory canonical尚依赖active ACO，归档顺序仍是ACO在前、该follow-up在后；本轮不覆盖任何canonical文件。

## 格式修正

capability-memory最后一条feedback requirement与material-library-v1最后一条feedback requirement缺scenario。只补原语义WHEN/THEN，不增加产品功能；其余proposal/design/tasks/9delta按原文保留。

CLI1.2.0 artifacts齐备，strict36/36、tracked与19owned文件空白检查通过。原包全部16文件逐一比较与读取时一致。结构校验不是业务语义复核或apply授权；独立审查仍在进行。

9delta共32条新增requirement标题；与已有canonical或active ACO依赖对应标题定向比较，无ADDED同名冲突。未修改任何canonical内容，原有requirement/scenario保持原文件。capability-memory仍需先归档ACO再归档此change，不能把pending namespace当成新的重复真源。

## 唯一需要用户拍板的执行节奏

现有workflow_engine.advance在普通node成功后继续ready下游。新Stage proposal生成成功不等于Master已经接受；若直接沿用advance，可能在用户尚未查看结果时跑完后续模型或误消费未接受结果。

已知必须保留人工采用与正式内容分离；仍需确认用户接受之后是只解锁下一阶段等待点执行，还是允许自动触发下一阶段。建议日常默认仅解锁，不自动调用后续模型/Agent；只读检查连跑不改变内容采用/发布gate。确认前不把这一建议写成已批准业务契约或实现。

## 权限与验证

不写正式SQLite/素材、不读私有runtime.env、不重启或真实调用模型/微信。后续tests已由原任务19.4明确要求；执行时使用隔离存储。未使用worktree，因为用户要求本项目后续在main开发；所有既有未提交片段保留。

## 独立SPEC首轮发现及修正

独立review完整读取proposal/design/tasks及9delta，提出6处实施前契约修正。主执行者已核对真实代码，不照单假设：

| 发现 | 真实代码依据与最小规格修正 |
|---|---|
| 成功不等于接受 | advance及input_mapping只看succeeded；Stage所需人工接受单独阻断Run完成，accepted-content输入只读精确接受实体/hash，人工修改后按接受hash传播stale。 |
| Preview身份缺协议 | run/rerun必须expected_resolution_hash＋invocation key；包括route/adapter/runtime，发送前持久化原Attempt claim/receipt，丢响应重用/协调原claim，Unknown不重发。 |
| 接受可能部分提交 | Master/Variant save内部commit；可信接受路径由单一事务负责结果/refs/输出关联/反馈及context/Master CAS，幂等重试先返回原已提交结果而非误报head漂移。 |
| 原proposal没有后产生的Master ID | 旧associate_step_output依赖Step实体ID及Attempt输出一致；新增可信adoption关联验证原receipt＋接受Master/decision，禁止重写原proposal/output/hash。 |
| Registry改动可能影响历史 | 新Stage Contract须新plugin version和新定义显式固定，不对原media/check/human版本追补语义。 |
| 内容修改不等于配置修改 | 只把真实显式tunable-field差异确定性保存为Recipe；仅改正文保留为feedback，无patch时先由用户明确写/选instruction或method。 |

上述修正已同步design、proposal、tasks和相关delta，任务仍144项，未勾业务完成。Phase0改成核验继承既有R1/R2与108案例，旧ACO15.7仍分开保留。接受后仅解锁还是自动调用下一阶段仍未决定；安全门槛不依赖该选择。本轮只改本change，不改原包/ACO/F8业务或正式运行。

定向复核确认5项完全闭合，第2项核心协议闭合，只剩Material delta把必要receipt写成MAY与通用SHALL冲突；已改为必要input/config/provenance/receipt必须冻结、仅额外展示投影可选，task8.2同步。最终定向确认及执行节奏仍待结果，未将有条件结论冒充业务apply授权。

最终定向复核已返回：六项全部closed、有条件APPROVE。唯一条件是用户选择接受后下一Stage的执行节奏；旧ACO15.7仍独立，不代关。review为只读规格复核，未运行测试；本轮新鲜命令证据为strict36/36、tracked/19owned空白检查、原包16文件内容不变和既有tracked diff摘要一致，业务任务0/144。

## 用户最终决定与首批实现发现

- 以上“待决定/建议仅解锁”是此前历史。用户本轮选择**自动执行下一阶段**，不是只解锁；设计/主delta/F2/tasks已同步。自动请求记录服务端准备身份，到下一处人工接受/阻塞停下。实际续跑依赖后续Attempt claim及采用事务，当前没有启用或伪称实现。
- 基线health两个失败来自metadata-only测试夹具没有Alembic ledger；只修隔离夹具并保留无ledger应503的负向案例，正式approved head/readiness不变。
- Registry只给明确新plugin版本加契约，消费清单与有界schema先校验；普通旧版本仍Advanced，不能因注册新契约改历史行为。
- 新Recipe GET/Preview POST使用只读身份查找，不继承旧Header自动建号的提交副作用。旧业务身份行为保持原样。
- Stage模型选择必须将明确route传入现有provider解析，缺失/禁用不能沿用legacy fallback。Preview绑定安全runtime连续性hash，不公开API地址或密钥。
- Capability方法同时检查精确历史revision的冻结scope和当前artifact限制；同名方法不择优、不创建使用记录。Installed Skill只有inventory没有精确可执行binding时明确阻断，不调用未知hook。
- FactPack与item快照重算hash后才可进Prompt；禁model-use/撤权内容不提供正文。无接受证明的上游Proposal即使succeeded也不能当accepted content。
- 首批只有纯Preview，旧start/advance/complete/retry/rerun入口统一在写状态前拒绝Stage定义，避免未安装发送前claim时绕过；该保护不影响无contract旧定义。
- 当前22/144。1.2/3.1/3.5/3.9/3.10仍未勾：接受目标/完整上游输入映射、媒体路由、真正调用协议尚未完成；UI、迁移、执行、反馈与晋升均未冒报。

## 批次二实现前决策与实现发现

- WorkflowStepAttempt.status 现有长度为20，不能把 failed_before_dispatch 直接写入 status；实现采用 status=failed 加 receipt outcome_state=failed_before_dispatch，保持旧表兼容并保留可读语义。
- Stage executor 必须显式通过 execute_resolved，不能让 workflow_engine.advance 直接调用普通 execute；Stage Run 入口创建 Run/Step 但不自动执行，只有带预览 hash 和 invocation key 的调用才可领取。
- Mock Provider 的既有结构化输出不保证返回请求数量，因此 Text proposal contract 只承诺1–5个有界候选并把 candidate_count 放入真实请求上下文；不能在服务端伪造重复候选来满足数量。
- 现代 Stage Workflow 暂定要求所有节点均为已注册 Stage Contract 节点；混合 legacy/Stage 图先拒绝，避免未定义的自动继续和旧节点旁路。

- `WorkflowStepAttempt` 继续是唯一执行历史，不新建 Receipt/Invocation 表；两个 receipt/input snapshot 作为 additive nullable JSON 字段落在现有 Attempt 上。
- 旧 ACO 正式 schema 不自动升级。ORM 新字段必须 deferred/server-default NULL，Stage path 必须先探测列存在；旧 schema 上 legacy workflow 可继续运行，新的 Stage invocation 明确返回 unavailable/upgrade-required 而不写入。
- 持久 claim 的唯一幂等键是 owner-scoped invocation key + resolution/request fingerprint；同 key 同 fingerprint 重放返回原 Attempt，same key 不同 fingerprint 冲突，possible-dispatch/unknown 不自动再发。
- Text proposal 先使用新的版本化 Stage plugin，不改 `builtin.generate`，且返回值只进入 Attempt output；Master adoption、refs/association、feedback 和自动 successor 分到后续批次。
- 独立计划复核提醒：`deferred/server_default` 不能单独证明旧 ACO schema 兼容；实际边界必须是每次 Stage receipt path 的 column probe + 缺列 fail-closed。receipt 字段、状态、并发键已在批次计划中固定，Text proposal 本批只允许隔离 fake provider 哨兵，不调用真实 CPA/MiniMax/公众号或其他外部模型。

## 批次三实现发现：接受后自动续跑

- `WorkflowStep.status=waiting_input` 同时表示“proposal 已成功但仍待人工确认”；下游 accepted 输入判断必须结合最新成功 Attempt 与独立 ProjectWorkflowOutput/feedback 证明，不能只看 Step status。
- 采用后的 Master 不能从 mutable Step output 推断。下游 Preview 读取 `content_master_revision` 的 exact entity/revision/payload hash/context hash，并验证对应 `creation_recipe.stage_feedback` 的 accepted decision 与 hash 一致。
- 自动续跑必须在接受事务已提交之后调用；接受成功不能因 provider 不可用而回滚。自动 invocation key 绑定 source run/node/accepted hash/target node/resolution hash，原 Attempt receipt 保存服务端准备的完整 resolution。
- replay 不能重新解析后再 dispatch：相同自动 key 在 `execute_stage` 的 currentness 检查前回读原 Attempt；测试已证明重复接受不会新增下游 Attempt 或 LLMRun。
- 当前只实现 Text Stage 的后端 continuation；Stage Result UI、accepted-with-edits 后续 stale、媒体/Variant/CreativeExecution continuation和浏览器验收仍必须单独完成，不能把本批后端证据冒充完整 Creation Recipe 产品闭环。

## 批次四实现发现：日常 Stage 控制入口

- 现有 `creation-recipe` GET 已经提供阶段 Contract、最近 Attempt、accepted target 和 blockers；前端无需新增 Recipe 状态表即可接入日常工作区。
- 临时调节必须以空对象表示“继承已保存配置”，只有用户实际改动的字段才进入 `stage_override`；Preview 回读 `base_config`、`override` 和 `effective_config`，避免把默认值伪装成一次性调节。
- Stage UI 只渲染服务端 Contract 的 tunable fields；旧节点保留 Advanced/legacy 提示，不能因新面板出现而改变旧 Workflow 解释。
- 预览是纯解析；执行前仍由服务端重新解析并以 `resolution_hash` fail-closed，前端不持有或展示凭据/原始 provider 错误。
- 当前批次完成 Creation Recipe 的日常入口，但没有冒称完成 Stage Result acceptance、跨形态 Stage、Save What Worked 或浏览器全链路。

## 批次四复核补强

- 自动续跑不能只把 accepted hash 放进 invocation key；必须在续跑前读取本次接受对应的唯一 ProjectWorkflowOutput，并核对 Attempt、decision、payload hash 及当前解析中的 Master/context。否则历史多个 accepted output 或后续 Master 变化会造成输入漂移。
- 自动续跑阻塞不能只通过 HTTP 返回临时 projection；现有 `WorkflowStep.status/error` 与 `WorkflowRun.status/error` 已足够作为第一版可回读真源，不新增 blocker 表。
- claim 在发送前提交意味着进程可能停在 `running`。同 key 重试现在要求显式 reconciliation；reconcile 会将无法证明是否发送的 attempt 封存为 `unknown`，保留原 receipt/input snapshot，且 `_prior_unresolved` 继续阻止任何自动重发。
- 为保持既有“响应丢失的同 key 重放复用原 Attempt”契约，普通同 key 重放仍返回原 running Attempt；这不代表再次 dispatch。新增的显式 reconcile API 负责把该 Attempt 封存为 unknown，之后所有新 key/自动请求仍被 reconciliation gate 阻断。

## 批次五/六：真实请求、结果接受与恢复

- reconcile必须在任何返回前验证Attempt所属Run/Step/Node；终态回读也不能泄漏外来Attempt。接续回放保留waiting/unknown/failed/stale，而不是以普通blocked覆盖原事实。
- 下游必须消费接受后的真实canonical Master正文，不是只把ID/hash传给模型；加入正文前重新验证context和精确Material/Evidence的live hash、字节、状态及model-use权利。public-use不等于model-use，禁止把只能公开展示的素材发给AI。
- 客户端阶段调节按node保留，改控件即作废Preview；实际窗口展示服务端System/User、分层Prompt、base/override/effective config与精确hash，不用客户端重新拼Prompt。
- 只读result API绑定本项目Run/Node的exact Attempt，或固定原invocation_key；安全receipt/原输入快照验证后才能显示。刷新恢复不再借用执行POST，历史/归档可查看但不可采用。
- 独立复核实际发现两个恢复竞态：原结果GET尚未完成/失败时可发新key；另一个窗口的新Run可替代原pending。最小修复是首次渲染就禁止新调用，回读绑定原Run/key并验证身份；网络失败保持禁止，只有已确认恢复之后才显示明确“再次生成（新尝试）”。
- Text候选使用现有结构化Text编辑器，独立本地dirty；采用请求冻结候选/原expected revision/context/最终payload+refs。接受后展示真实保存正文/version/hash；下方Master未保存编辑不自动覆盖。
- Browser夹具曾发现请求3个候选而Mock实际只返回1个；只给明确stage.master.proposal.v1的隔离Mock分支按请求数量返回清楚标注的Mock数据，旧Mock输出不变。永久断言已先失败后修复，不能以这些候选证明真实模型生成质量。
- 本批9项隔离浏览器gate覆盖调参/Preview、键盘导航、3候选未写Master、延迟/失败回读不再dispatch、刷新原结果、修改后接受且保留独立dirty、自动下一阶段停审阅、接受Master刷新回读。拒绝/保存有效调整、Graphic/Video和Candidate→Review→ZIP仍不是本批验收范围。

## 2026-10-06：前端实施接口与所有权

- 用户明确指定共享 main 和四个 Stage 文件所有权，Workflow/Master 的其他 dirty 编辑独立保留。
- 当前会话没有 codebase-memory-mcp 的代码图工具；定向读取已知文件和必要字符串检索作为 fallback。
- Master 接受继续 /accept-master，仅增加明确 payload_schema；其他结果只经 /accept-result，不以通用 UI 伪造领域写入。
- /methods、/history、/feedback、/improvement-preview、/save-adjustment、/apply-method-preview、/apply-method、/options、/adopt-recipe 由父任务提供。AI tuning suggestion 未提供时保持禁用；不进行 smoke 或外部请求。

### 前端冻结交接接口核对

- 当前 Master 请求仍是 content_projects 的 /accept-master，payload_schema 接受 text/graphic/video.master.v2；未改该路由或 request 其他字段。
- /accept-result 只按领域服务已有协议写：共同 run/attempt/domain/output/resolution/context hashes、expected_revision、adoption_key、decision/note/reason_tags；media 带 task_id/expected_result_hash/rights，variant 带精确 payload/asset_refs/evidence_refs，professional 带 package_id/execution_id；checks/human 不伪造 Candidate 审核或工具执行。
- media_profiles 的 selected_profile 只按所选 capability 的 declared/configured 及 profile.available 筛选，仍以 preview 实际路由为最终权威。installed_skills 独立只读库存，不当作可执行方法。
- accepted feedback_event_id 优先用接受/result 回执，缺失从同 run/node/attempt 的 history accepted 事件读取。tuning-suggestion 使用精确 feedback_event_ids/model_profile_id/invocation_key；保存链保持 llm_run_id → tuning_suggestion_id 与 suggestion_hash → expected_suggestion_hash。
- improvement/apply preview 的 definition_diff 已由父任务同步加入；前端递归展示全部键和精确值（不使用 raw JSON），默认模板缺完整差异时 fail closed。切换范围、方法、建议或编辑参数后必须重新预览、确认。
- 尚需权威 skip 权限投影：result.allowed_decisions 包含 skipped_when_allowed，或 Contract output_contract 明确声明；前端不自行推断 failure_policy 及副作用门禁。后端再次校验仍是最终权威。
- 本轮仅冻结实施；统一 TypeScript/Vite/独立复核与 smoke 均留父任务，不声称通过。

### Plato 复核修正的源码依据

- 原 prepareRun 的 setLocals({}) 会丢弃准备运行前的调节；改为按 node 保留 override，以 emptyStage 重置其余执行状态。新增终态运行入口复用同一守卫和 /runs，不触碰 Master 或不可变旧 Attempt。
- 原 useProductionWorkflow 与 CreationRecipePanel 各自初次读取流程，没有保存后的互相通知。修正只新增局部回调和递增版本信号，不重挂整个 Production，也不改独立 Content Master 的 key/base。
- 流程刷新比较 binding/effective/default 的 exact workflow/revision/checksum；有 dirty 或 Inspector 未应用编辑时保留旧草稿和旧 CAS 基线并提示冲突，不换成新 revision 后盲覆盖。刷新返回时再检查当前草稿；显式丢弃期间的新编辑仍不覆盖。
- StageTuningPanel 原逻辑只验证接受事件在库存中，未要求它仍在 selected/request 中。现禁用该 checkbox 的取消并检查最终 feedback_event_ids，不能绕过必选接受反馈调用模型。
- 本轮新增所有权仅限 ProductionWorkspace/useProductionWorkflow 的同步片段；其他 dirty 修改保持现状。无新后端字段/API 需求，无测试/build 证据。

- TypeScript 回传的 StageDomainResultPanel 第118行当前字段是 checkpoint?: unknown。unknown && JSX 的表达式仍可能为 unknown，不能当 ReactNode；!= null 使条件成为 boolean，同时收窄可空 execution 链，正文继续只渲染 stageValue 返回的字符串。只改该守卫，不更改领域协议或使用 as any；未自行重跑门禁。
