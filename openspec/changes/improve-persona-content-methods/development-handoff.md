# 角色内容方法改进：接续开发与验收交接

更新：2026-10-20，Asia/Taipei。用户要求把当前工作转交另一 Agent，沿原需求继续完成，再回交主 Agent 独立总验收。本文件替换旧开发交接的当前状态；历史过程在 progress.md、review.md 和原证据中保留。

**当前结论（接手Agent续做后）：16/25，其中新增 3.3、3.4、5.1、5.3、5.6 为接手自检勾选、待主Agent独立复核；整个变更未通过验收，未改变角色长期默认，未提交、push、归档或公开发布。** 第1–10节为接手前状态与原约束，仍有效；最新状态以本节为准。

## 0. 接手续做后的交回状态（2026-10-20，交本对话主Agent独立总验收）

**代码（均在已有在途文件内、相对交接新增，未提交）：**

| 编号 | 文件 | 改动 | 验证 |
| --- | --- | --- | --- |
| A17加载 | stage_resolver.py | 交接时的最终版按原命令加载 | `independent/a17-final-api-reload.json`；run25/refine真实续执行成功 |
| A18 | stage_feedback.py `rework_context` | 步骤stale时不再把旧尝试上的定位反馈带入重查 | `a18-api-checks.txt`、`a18-api-reload.json` |
| A19 | creation_recipes.py、stage_resolver.py | 角色域共享素材附source_kind/title，规则写明ai_generated不是实拍 | `a19-checks-and-reload.json`；visual168正确定性 |
| A20 | stage_resolver.py `_compact_method_audit` | 严格去重扩到角色域stage.creative.method（builtin@2） | `a20-api-checks.txt`、`a20-reload.json` |
| A21 | stage_resolver.py `_compact_method_audit` | 角色域无方法栈的professional.prepare只做分段位置引用 | `a21-api-checks.txt`（846 passed）、`a21-reload.json` |

最终：846项相关既有检查、Web完整构建（`final-web-build-20261020.txt`）、OpenSpec strict通过；15表原有行逐行一致（`final-preservation-20261020.json`，仅两项discovery时钟自然更新）；正式API8000 ready，最后一次加载为A21版。无running/claimed，只有既有Unknown129（run21 tts，非本变更）与155。

**真实样本：** 全部清单见 real-samples.md 末节，逐件技术/内容/认可三列见 review.md 顶部。要点：科技文字/图文A/B完成；生活图文A/B完成、生活文字B停在Master76（Unknown155）；两角色音频A/B完成；新题科技三形态、生活文字/音频完成，生活图文缺授权封面；6个视频导演计划/包完成，无真实MP4。

**仍开放（不能省略）：** 3.6 完整开关矩阵（含原生TTS/专业包/商品隔离，及科技角色capability-memory遮蔽@2的定性）；4.2 音视频时间定位反馈未实测；4.4 隔离UI综合边界（刷新草稿/空态等）；5.2 生活文字B需用户决定Unknown155处理；5.4 两角色B真实成片；5.5 生活新题图文封面素材；6.1 汇总复核；6.2 用户逐角色/形式采纳；6.3 规范同步与归档。另有开放问题：run质检阶段对4卡+长引用的图文快照超128KiB（改用Master级检查交付）、媒体暂存名额、UTC日期判定。

**需用户提供/决定：** 见 review.md“需用户提供或决定（素材清单）”7条。

**主Agent独立复核建议顺序：** ①核三处业务源码hash与A18–A21改动范围；②复跑846项相关检查/构建或抽样；③抽看review.md中每件作品的实际正文、PNG（`evidence/real-samples/png/`）与音频清单/SRT，确认结论；④核本地包hash与平台回读；⑤再决定5项自检勾选是否成立。

## 1. 唯一工作区和原始需求

- 工作区：`/Users/mshengran/Project/AIContentStudio`。
- 唯一成果目录：`/Users/mshengran/Project/AIContentStudio/openspec/changes/improve-persona-content-methods/`。不另建 change，不重复提案，不重开已归档 change。
- 实际分支与HEAD：`main@8539806eb3a1bebf5bf71ee08df3a286cdf9e00a`；交接只读盘点225个 dirty/untracked条目。必须重新核对，不 checkout/reset/clean/stash，不整文件覆盖相邻修改。
- 原需求以 proposal.md、design.md、六项 specs/*/spec.md、tasks.md 为准。原开发责任与约束继续见 AGENT_DEVELOPMENT_PROMPT.md；本文件提供最新停止位置，不缩减原25项验收。
- 用户已授权这版方案开发、有界真实样本及发现问题修复。正常平台业务只用CLI/API/MCP；浏览器只在隔离环境验收。不要重复询问这些已明确授权。

原需求不是只解决本轮三个错误：以角色内容工作台为主，抽象吸收 Easel 方法，在现有角色五步中接通参考正反例、共用方法与角色风格分离、各形态策划、知识用途、定位反馈和明确偏好积累。科技、生活必须分别做真实对照与新主题迁移，原模型/音色/参数、商品六步和旧历史保留。

原用户六项补充、页面与Skills分工分别对应 design第1/2/3节，精确数据合同见第5节，最终验收矩阵以第7节为唯一标准。不是只修完当前阻断就能归档。

## 2. 开始接手的读取顺序

1. README.md → 本文件 → tasks.md → task_plan.md。
2. proposal.md、design.md，重点第7节；六项 spec delta。
3. review.md头部2026-10-20及A1–A17返修证据；findings.md。
4. real-samples.md 和 `evidence/real-samples/state.json`、`operations.jsonl`。
5. `evidence/independent/handoff-current-state.json`、`handoff-checks.json`、`handoff-services.json`。

继续维护同一 README/task_plan/progress/findings/review，不用用户再贴聊天记录。按仓库AGENTS及现有skills执行；本轮采用OpenSpec apply、executing-plans、systematic-debugging、Playwright。不要新增持久测试代码。

## 3. 25项原要求的覆盖与缺口

已勾选：**1.1、1.2、1.3、2.1、2.2、2.3、3.1、3.2、3.5、4.1、4.3，共11项。** 技术接口通过与用户风格认可分开。

| 原任务 | 当前已经证明 | 接手者必须完成 / 不能省略 |
| --- | --- | --- |
| 1.1–1.3 | 原作品/配置/文件安全快照、原行保全；授权同题/新题及标准登记；新旧合同兼容 | 结束前再次回读；不能用Git HEAD覆盖原在途文件 |
| 2.1–2.3 | 正常参考搜索翻页、精确文字/PNG/WAV/MP4预览、正反例及定位保存；试用/明确默认保存与409字段保全；按用途/形态裁剪知识 | 隔离默认保存只是功能验证，正式角色默认须见6.2；合成媒体解码不是试听或风格验收 |
| 3.1–3.2 | 14个自有方法@2及graphic/card/shot等兼容合同 | 有些真实输出质量退步，登记方法不代表有效，必要时修方法而不是无限抽样 |
| 3.3 | 声明式关系排版已接，旧8图已实际看过 | 尚无本轮完整新PNG；两组逐张检查手机可读/关系语义/图文一致/裁切，核对实际参数消费 |
| 3.4 | 新口播和声音方法在，原音频资产/配置已冻结 | 本轮原音色TTS→完整ASR→声学QC→本地包未做，不能用旧音频替代 |
| 3.5 | 精确已接受shot-plan.v2的连续性/参考/声音进入导演包，v1兼容及伪造引用阻断已独立验证 | 只是交接技术合同；真实视频仍见5.4 |
| 3.6 | 双角色四形态AI规划节点224项真实请求构造器开关/继承/本次覆盖检查通过（未派发） | 原生TTS、确定性工具与专业包的完整合同/商品隔离矩阵补齐，不宣称224项全是真实模型输出 |
| 4.1、4.3 | 五步、返回、折叠与真实状态/权限；当前作品反馈到明确范围偏好候选 | 不擅自把意见提升长期默认 |
| 4.2 | 文字Mock采用闭环；真实图文页定位反馈已进入返修；科技精修定位意见已保存 | 图文页/元素、音视频时间、失效目标、实际最小返修范围和相关下游重查仍需完整闭环 |
| 4.4 | 窄屏/键盘、只读/归档、Unknown回读、409、商品六步保留已有分项证据 | 补齐刷新草稿/离开保护、空态等未覆盖项并汇总，保留模型配置内部 |
| 5.1、5.2 | 科技/生活正文B已真实生成与编辑，科技卡片计划和生活视觉方案已有真实输出 | 同条件A仍未生成，新PNG未完成，技术/内容结论分开；不能拿已人工编辑的旧成品冒充同条件A |
| 5.3 | 原科技/生活音频只读已登记 | 两角色本轮音频A/B、完整转写/QC与本地交付 |
| 5.4 | 仅计划交接技术验证 | 两角色A/B导演计划、各一支B完整真实小样、Resolve主剪/按需AE回收；素材缺口明确列出，不造MP4 |
| 5.5 | 已选科技机会19、生活机会7，既有来源证据已存 | 两角色新题文字/整组图文/音频真实迁移和视频计划，不能只做一个新正文 |
| 5.6 | 最新601相关既有检查、Web构建、独立页面/配置保全通过 | 真实正常入口到正确已保存版本本地交付回读及最终保全仍待 |
| 6.1–6.3 | 独立问题/返修记录持续维护 | 汇总技术/内容/角色认可；交用户实际对照，明确逐角色/形式新默认；必需任务全部完成后strict/canonical/归档。提交推送遵循原授权，不自行扩大 |

## 4. 当前真实样本：不要重复创建或盲发

原件全部只读：科技 P35/U41文字Master61v4、U43图文Master73；生活 P36/U42文字Master65v4、U45图文Master74。科技音频U44 Master66/run24，生活音频U46 Master67。原件的Brief/FactPack/Identity/知识快照见 real-samples/original-*.json 及 independent/original-*context*.json。

新试验通过正常API建在 P37（科技）、P38（生活），共8个作品：

| 对象 | 精确位置 | 当前真实状态与下一步 |
| --- | --- | --- |
| 科技文字B | P37/U47/run25，Identity23 | draft143做一次定位编辑后保存Master75v1，hash `ebdc00fabc2226a870b997e5df4e3647f2f5259955cff38198fcbaf372d1e7fa`。quality152无blocker、1 warning已带理由正常采用；精修156成功但未采用，全文tech-text-B-refine.md。主Agent认为表达仍抽象、缺贯穿例子，已保存定位反馈。quality1返修预览超限，尚未派发新尝试；从A17最终修复加载/预览接续 |
| 科技图文B | P37/U49/run26，Identity25 | visual137已采用；cards138错继承旧capability方法且合同失败；正确@2 cards151后做一次内容返修154，仍未采用。154又把转人工摆成第四个图示节点、含置信度阈值，不能判质量通过。尚无新Graphic Master/PNG |
| 生活文字B | P38/U51/run27，Identity27 | draft147编辑后保存Master76v1，hash `1322301d39269bac3ad28aac4b122b13f4b99bd1d059d214f927b19043cf72e6`。quality153八项pass已采用；自动精修155为Unknown `stage_dispatch_unknown`，GET再次回读仍Unknown，没有重发 |
| 生活图文B | P38/U53/run28，Identity29 | visual150真实成功待采用，指出封面缺图片。尚无cards/PNG。先核已有授权素材是否适合复用；原Material71是AI情境插画，不能冒称真实实物照片或实测证据，也不能静默改成纯文本绕过原预设 |
| 科技A | P37/U48文字、U50图文 | 载体/原工作流已建，无run、无真实产物；不要重建 |
| 生活A | P38/U52文字、U54图文 | 同上 |

原初稿分别保存为 tech-text-B-draft.md、life-text-B-draft.md，编辑差异在同名前缀-draft-edits.json。初稿有事实/效果保证退步；人工修正不得归因于Skill自动提升。tech refine156仍是候选，不是Master75的新修订。不要跳过实际阅读自动accept。

科技最新定位反馈文件：`tech-text-B-refine-quality-feedback.json`。它要求用明确假设的“工卡丢了，去哪里补办”贯穿输入/预期答案/判定，减少术语、保留人工复核和未知；不得编造真实部门/规程。实际工具需重做当前精修阶段整稿，反馈已说明范围。后续拟用唯一key `persona-methods-20261020-tech-text-B-refine-quality1`，但当前未派发、state仍指向156；必须先实际回读核实。

生活Unknown155精确key：`auto-accept:f0298e597390a356276ea8174eb26c8639287c0ae4d60a7d1032305f515b2c45`。只能先GET原result/正常恢复证据；Unknown不是失败，不用新key绕过guard，不改模型重抽。还原接收结果无证据时，该项保留待处理，先做独立任务。

新主题：科技机会19 ESP32-iPhone-Agent；生活机会7 Pneuhaus针孔暗箱。原已存 `new-topic-opportunity-19/7.json`、`new-topic-signals-19/7.json`，尚未启动这些新题生产，不把选题登记当迁移通过。

## 5. 实际配置与执行注意事项

- 真实文字/图文规划原路由仍是 `openai_compatible / gemini-3.8-flash-high / profile registered.ddd9b006056eae2bfb76b2ee / configuration_revision13`，原temperature0.4等按实际冻结请求读取。重启前后runtime_hash可能变化，不把它伪装成同一个runtime，也不推断网关真正上游。
- 科技原音色 `lengdan_xiongzhang`，生活 `chunzhen_xuedi`，原TTS `speech-2.8-hd`、rate1；其它参数以原快照/API为准，不凭记忆重设。
- B仅本作品profile选择适用@2。text的research为证据/角度，script为大纲/长文/精修/标题；graphic storyboard为视觉/卡片/素材简报。原script阶段本来关闭，启用是已登记的方法变项，不能称纯单变量因果实验。原Persona2/3默认不改。
- 只把节点method改@2，仍可能被继承capability-memory遮蔽。自动继续也要核真实method_stack，错方法attempt138/140完整保留，不计@2成果。
- **accept-master / accept-creative / accept-result 都会正常派发一个后续就绪阶段。** 这不是只写采用记录；授权说明/预算和回执都要包含副作用，采用后先回读continuation，不重复显式run。
- 原始失败LLM输出可能raw/parsed=NULL；只能依据LLMRun.usage.validation_code，不猜丢失正文，不为了看原文放宽安全策略。138对应LLMRun173 `creative_card_diagram_plan_required`；136对应171 `creative_method_exact_references_required`。
- 同一候选生成与明确缺陷一次返修的约束继续生效，不能反复抽样到好看为止；已用返修次数见operations。质量未过就记未过，必要时修方法/编辑正常版本，不直接写DB制造接受。
- 模型派发首次曾被自动审批拒绝；补齐直接用户授权/原目的地/空知识载荷证据后同一命令重审通过。见first-dispatch-review-rejection.json、dispatch-authorization-and-payload-summary.json。不能绕过审批；后续仍明确原目的地与已选授权资料，不导出密钥。

## 6. 最新修复与尚未加载的代码

主Agent本轮新增业务修改仅：

1. `apps/api/app/services/factchecker.py`：A15否定追求零风险不误当投资承诺，外层否定/引用/反问保守保留；A16允许FP正文明确日期，as_of时效仍独立。显式禁语、正向承诺和无依据日期仍拦；19项临时边界检查及两类代码复核通过。已按原API命令加载，quality152/153为真实复验。
2. `apps/api/app/services/stage_resolver.py`：A17继承多方法精修+定位反馈的快照超128KiB。仅原本超限的persona `stage.master.propose`、相同builtin@2栈及相同聚合正文才压缩重复审计指令；完整creative栈/manifest及实际prompt保留。最终再把与完整effective_prompt严格相同的prompt_sections正文改为UTF-16位置/hash引用，仍校验128KiB完整claim封套，不放大门禁。
3. `apps/web/src/product/CreationRecipePanel.tsx`：按指针还原各提示层，旧text格式兼容，坏范围明确不可读；完整System/User仍可查看。

A17分两版，**不要混淆代码与当前服务**：

- 第一版仅去重method审计正文，已加载正式API，科技refine156真实生成成功；有定位反馈后仍超限。
- 最新最终版加prompt_sections去重及UI还原，**已在本地代码中、未再重载API、未做正常正式续执行**。601项检查/完整Web构建、只读真实反馈重放30/30和真实TS函数/原JSX渲染33/36项均通过，见handoff-checks与final回执。交接阶段不再派发模型；接手先核这版并按原命令安全加载，然后用空override验证正常继承再执行。
- 最终A17真实反馈快照由原超限降至claim封套99587B；完整GenerateRequest和input_hash前后相同，实际反馈到达请求；正常小形状result/hash不变；商品/@1/混合/不等栈/仍超限拒绝。证据 `refine-preview-bounds-final.json`。这是本地只读重放，不冒称正式续链已通过。
- 最新源码hash在handoff-current-state.json。共享文件相对HEAD还含此前开发/相邻改动，不能把整份diff都算本轮，不能还原整文件。

## 7. 验证与保全证据

以下均已由主Agent实际读取/复跑，仍须区分技术和质量：

| 证据 | 本轮结果 |
| --- | --- |
| handoff-api-checks.txt / handoff-checks.json | 最新代码601 passed，8条既有弃用warning，23.41s；未新增持久测试代码 |
| handoff-web-build.txt | 最新TS+vite+bundle检查通过 |
| fact-rules-after.json | 19/19，无模型/写库 |
| refine-preview-bounds-final.json | 最新A17真实只读链30/30；完整请求相等；旧20/20只适用中间版 |
| prompt-sections-ui-final.json | 真实函数33项、原JSX渲染36项通过；不是浏览器实页验收 |
| browser-reference.json / browser-media-reference.json | 31项翻页、反例、精确PNG/WAV/MP4解码与区域/时间保存刷新，明确合成媒体 |
| browser-readonly.json / browser-boundaries.json | 五步、返回、折叠、375px、只读/归档/Unknown与零写入 |
| browser-default.json / frontend-final-recheck.jsonl | 隔离默认新修订、409草稿及其它模型/声音字段保全；正式默认未采纳 |
| browser-product-preservation.json | 正常SKU启动零角色商品作品、桌面/375px六步Enter/来源返回，16项、零页面错误/写请求 |
| all-form-chat-switches.json | 224条实际请求构造器检查，不是224次模型派发 |
| a12-v2/v1/feedback-priority.json | 精确导演计划入包、伪造/漂移拒绝、反馈优先级，不是实际MP4 |
| handoff-current-state.json | 交接时14表所有原有行仍与样本前私有快照一致，新试验行另计；静态模型等11项设置hash保持；仅discovery.heartbeat/catchup_clock自然更新 |
| catalog-final-preservation.json / old-files-final-preservation.json | 旧50资源与75个v1文件保持，不以HEAD对照相邻旧修改 |

旧开发data-preservation-recheck.json的序列化有缺陷，不能用来推断库变更。主Agent后来的备份/逐行比较是有效证据；私有SQLite快照`/tmp/persona-independent-before-real-samples.sqlite`（0600），只读比较应使用mode=ro&immutable=1，不入Git。

## 8. 服务与临时工具

交接只读核验：正式API8000 ready=true、Web5173可达。隔离API8019/Web5174当前不可达，历史UI通过回执有效但不代表服务仍运行；接手需要时按原命令恢复，不能向正式数据跑UI写测试。

- 正式API沿用 `com.aicontent.api` launchd和 `apps/api/scripts/startup/start_api.sh`，不输出被忽略runtime.env内容。需要加载最终A17时先查无running/claimed等在途任务，保留Unknown155；原命令 `launchctl kickstart -k gui/$(id -u)/com.aicontent.api`，正确健康入口 `/api/v1/health/ready`。不重启Worker或改变原启动环境。
- 隔离API：`apps/api/.venv/bin/python /tmp/persona-independent-isolated-server.py`，绑定8019，/tmp/persona-methods-ui-20261019.sqlite，Mock/lifespan off。
- 隔离Web：在apps/web运行 `AI_STUDIO_API_TARGET=http://127.0.0.1:8019 npm run dev -- --host 127.0.0.1 --port 5174 --strictPort`。
- 捆绑Playwright NODE_PATH：`/Users/mshengran/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules`，无需安装。
- 真实样本临时runner：`/tmp/persona-real-samples-runner.py`；stage默认会显式覆盖B method，只适合明确试用，**不要用它掩盖正常继承的A17缺陷**。accept仅处理候选，不是通用自动验收脚本，使用前先审原文及continuation。
- checks采用脚本：`/tmp/persona-real-accept-checks.py`，每次会自动尝试后续生成，不能当无副作用保存。
- 只读A17探针：`/tmp/persona-refine-preview-bounds-review.py`；UI还原探针：`/tmp/persona-prompt-sections-ui-review.cjs`；事实规则：`/tmp/persona-fact-rules-recheck.py`。必要操作脚本都在/tmp；若已丢失，依保存的请求/正常API重建最小执行，不猜状态或批量重发。
- 网络沙箱可造成localhost假拒绝；需要时按具体已授权动作申请工具网络执行，不把沙箱失败说成服务离线。不得用换工具绕自动审批。

## 9. 下一位 Agent 的最短执行顺序

/// 1. 只读核当前Git、tasks、正式run25–28及Unknown155；保留本文件所有未完成项，不把接手当重做。
/// 2. 复核A17最终代码/新指针展示，安全加载当前API；用run25/refine的空stage_override预览，核方法正文各一次、真实反馈、原模型/参数。与现有候选分开，不复发155。
/// 3. 执行尚未派发的科技精修定位返修，实际读稿；不合格记明差距，按已授权有界方式修，不无限抽样。继续标题/最终稿/检查/准确本地交付。生活Unknown先正常回读可恢复性，保持原模型。
/// 4. 处理科技卡片154内容/关系错误，生活封面素材缺口；通过正常采用/排版/渲染，逐张真实看PNG。不能因想交付就采用有误计划或假造素材。
/// 5. 补原同配置A，记录所有变项和人工改动；再补原音色音频A/B、新题各形态和视频实际小样，所需外部素材集中列清。保留已有额度/Unknown，缺素材继续其它独立任务。
/// 6. 补3.6/4.2/4.4/5.6剩余合同和正常入口/返修/交付验收；只在新改动或真实缺口时增加必要检查，不反复全仓跑测试。
/// 7. 回写完整25项证据和技术/内容/用户认可三列，交本对话主Agent独立总验收。用户看实际对照并逐角色/形式采纳后，再按6.3 strict/同步六项canonical/归档。任何必需项开放不得提前归档或宣称通过。

## 10. 可直接发给接手 Agent 的提示词

> 接续 `/Users/mshengran/Project/AIContentStudio` 的已批准 OpenSpec `improve-persona-content-methods`，不要重新提案。先读该change的README.md和development-handoff.md，再读原proposal/design第7节、六项spec及tasks，核实际Git与运行状态。当前11/25，保留全部原25项验收，按交接第9节从A17最终修复加载和科技run25/refine定位返修继续。生活run27/attempt155为Unknown，禁止盲重发。科技/生活原始草稿、人工编辑、同条件A/B、PNG/音频/视频真实质量和新主题都分开记录；原模型音色、商品六步、原作品和相邻修改保留。平台业务只用CLI/API/MCP，UI写验证只在隔离库；不要新增持久测试、提交、push、归档或公开发布。维护同一成果目录，把开发/自检证据、准确剩余项和需用户提供的素材清单写回；完成后回交本对话主Agent做独立总验收，不能用601项检查或文档齐全替代整变更通过。

## 11. 2026-10-20 验收反馈第二轮修复（本地代码，未加载正式API）

针对交回报告中的开放代码问题，本轮只改了三处业务文件并跑过相关既有检查；正式API8000仍运行旧版本，加载按第6节原命令由主Agent决定。

1. UTC日期误判未来（`studio_creative_catalog.py`、`factchecker.py`）：`freshness_projection` 的上界从 `now(UTC)` 改为操作者本地日末（服务器本地时区），台北凌晨录入的当天 `as_of` 不再判成未来；真正未来日期（本地两天后）与过期日期仍排除。factchecker 的“今天/当前”表述核对同步改用本地日期。单测三项验证见 `evidence/development/checks-post-acceptance-fixes.log`。
2. 图文质检128KiB（`creation_recipes.py`、`stage_resolver.py`）：`stage.checks` 节点快照原来把 master payload 复制三份（context.master、`__current_master__`、上游边）。现 checks 节点的两处上游副本改为 `payload_ref`（与 audio_qc 同一先例），并允许 checks 节点走 `_compact_method_audit` 的 sections-only 压缩（仅角色域，商品仍拒绝）。隔离四卡链证明 preview 200、快照只剩一份 canvas payload；合成超限样例压缩到 120,383B 通过（`graphic-qc-overflow-probe.json`）。正常小形状 hash 不受影响（593项含 persona 328 全过）。
3. 自动续接@2（不改代码）：`auto-continue-probe.json` 证明试用配方（`method_trial_definition`）钉住的 Run 在 automatic 续接下每个节点回执仍是 @2（angles/outline/draft 均 mode=automatic、stack=@2）。掉回 @1 的情形是 Run 钉在默认 v1 定义或阶段选择里继承 capability-memory 方法（第5节已记录），按设计需要仅本作品显式配置，不自动改写。

检查：`tests/test_persona_creative_studio.py + test_persona_graphic_quality.py + test_creation_recipe_stages.py + test_stage_master_adoptions.py + test_stage_master_proposals.py` 593 passed；`test_services + test_review_center + test_fe_f4_project_review + test_candidate_manifest_v2` 42 passed；freshness 本地日三项行为验证。日志 `evidence/development/checks-post-acceptance-fixes.log`。

仍未动：媒体暂存每人8个名额（平台既有行为，需产品决定）；生活run27/attempt155 Unknown（现有合同无解除路径，不盲重发，需用户/主Agent决定）；4.2 音视频时间定位实测、4.4 隔离UI边界、3.6 完整开关矩阵、5.4 真实成片、5.5 生活新题封面素材。
