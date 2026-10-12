# AIContentStudio Persona Creative Studio — OpenSpec package

用户当前要求跳过WeWrite Skill测试，先交付功能；本change无未完成功能实施项。151/156中的5项仅质量复核/人审记录和另行授权生命周期，不阻塞继续使用当前版本，不虚记通过；不再重跑旧插件测试，不改现有公众号适配器或运行配置。依赖与启动方式不变。

集中产物已保存在[本地验收包](/Users/mshengran/Project/AIContentStudio/backups/persona-review-20261009.O02VLb/README.md)：两篇冻结稿及生活编辑稿、两ZIP、六PNG、两完整WAV和安全manifest。最新隔离后端2528 passed/12 skipped、Web/FE-P1与Ruff通过；旧插件测试所需临时Skill元数据及首轮失败保留在[回执](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。零新Provider/正式写入，依赖/启动不变。质量确认和单独授权生命周期未完成，仍151/156；21.3只完成证据整理，不冒称人审通过。

2026-10-09 **当前151/156、5开放；生活完整Audio通过**。用户明确恢复Gemini出口后，新隔离Run9/Attempts32–35完成两次Gemini规划→一次MiniMax→246.535秒真实WAV→受限MaterialRevision2接受→QC pass/零问题/整链complete；20.4关闭。旧Unknown25/26/31和原停止批保留，正式5,170行/70素材/配置保持，正式API/Web/Worker继续运行。待人听/全模态rubric、21.3/独立质量及单独授权生命周期；无新业务补丁/迁移/全量测试/归档提交。目录/依赖/启动不变。[完整回执](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下为历史检查点。

2026-10-09 **当前150/156、6开放，科技完整Audio已通过功能链**。用户修复外部网络后，新隔离Run7完成精确Gemini口播/声音规划→MiniMax→324.028秒真实WAV→受限MaterialRevision→同Run QC/接受；19.4关闭。两处实际串接缺口已最小修正，497现有集中回归通过；普通inventory不探测、AI/ASR/公开权限不放宽。生活首个新CPA请求仍无有效响应并保守Unknown，本批停止，不重发；人听/独立质量/生命周期仍待。正式库/素材/配置/服务不动，目录/依赖/启动不变；[本轮回执](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下为历史检查点。

2026-10-09 **Audio失败层只读定位完成**：两原失败窗口的CPA请求均500/Google上游EOF；一次无凭据HEAD也TLS失败。未改VPN/配置/服务、无新模型调用，360秒成品上限保留，旧Unknown不重发；当前149/156及7项开放保持，不把诊断记为完整Audio通过。目录、依赖与启动不变，[安全回执](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-09 **最终图文实物已核对，生活真实封面遗漏已纠正**：新隔离副本复用原MiniMax真实图，三PNG/接受/Master15/render及确定性QC完成，原色块fixture记录保留仅作功能证据。固定视觉自评已记录，不冒充人审或全模态独立批准；零追加模型/正式写入，仍149/156、7开放，Audio未关闭。依赖与启动不变。[本批回执](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-09 **当前149/156、7开放；360秒正式配置再次只读确认**。运行中API返回revision9/360秒成品上限/120秒等待/273音色，新模板一致；无额外生成或配置写入。13.6已完成，完整真实Audio、人听/质量及生命周期仍待。目录、依赖与启动方式不变，以下为历史检查点。见[当前回执](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-09 **360秒Audio上限已生效，当前148/156、8开放**。正式routing revision9，仅改TTS输出max_seconds，120秒等待/273音色/其余配置不变；新内置模板同步360、历史流程不改，104项Audio定向回归/Ruff和正式模板checksum回读通过。新完整Recipe首个CPA口语改编Unknown，实际CPA1次/MiniMax0次后停止，不重发；完整Audio与人听仍待，不冒称六分钟音频已经产出。目录/依赖/启动方式保留，API已刷新、Worker不动；见[本轮回执](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下为历史。

2026-10-09 **图文功能链已在隔离副本收口，148/156，8项开放**。科技与生活 Persona 均完成精确素材引用、确定性 compose、三张真实 PNG、产品接受、append-only Graphic Master、render attestation 和结构/平台/render 检查；Mock fact/identity warning、真实 Audio、人审质量、全样本 provenance、独立质量复核、13.6 与生命周期仍开放。正式 SQLite/素材/配置未被隔离验收改动。见[progress](progress.md)与[图文音频验收回执](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-09 **已授权补使用配置，146/156不变**。正式routing revision5→7；chat8192tokens/最多3候选/120秒等待，MiniMax音色目录一次同步273项。两个角色文字配置ready，实际页面显示音色搜索/筛选；尚未替角色选voice ID，不冒称生成或质量验收。私有SQLite备份后通过现有接口CAS保存，5,162其他行/67素材/私有Provider配置/runtime.env保全；API/Key/默认模型及旧媒体限额不变，无业务代码、迁移、生成、归档提交或push。目录/依赖/启动不变，详见[progress](progress.md)与[配置回执](../../../docs/PERSONA_CREATIVE_FRAMEWORK_HANDOFF_2026-10-08.md)。以下均为历史检查点。

2026-10-09 **正式初始化 / 146/156，10开放**。已获启用授权并完成SQLite＋67文件素材备份、原API/Worker刷新、科技Persona2/生活Persona3及独立Workflow7–12幂等初始化；5,147旧行、素材及运行配置hash不变，schema仍crs。实际角色/风格/流程及生产、媒体、ChatGPT手动入口冒烟通过；就绪/Fork接口已加载，API ready=true。正式chat限额缺失、voice目录为空/未选voice ID是新发现的使用配置阻断，未擅自扩大原image1张/TTS10秒限额。仅关闭5.8/22.7，真实Audio/完整QC/独立质量/13.6及生命周期仍如实分开；零Provider调用/迁移/业务代码或永久测试，不重跑全量/审美生成。目录/依赖/启动方式不变，详见[启用回执](../../../docs/PERSONA_CREATIVE_FRAMEWORK_HANDOFF_2026-10-08.md)和[progress](progress.md)。以下均为历史。

最新状态 **144/156，12项开放**。生活混合卡片已获明确授权并落地：暖杂志封面需精确图片、正文可纯文字；纪实每卡图片规则不放宽。Preview/排版/结构QC共享策略及hash，既有生活计划已生成三张1080×1440真实PNG预览；历史不改，完整成品接受/事实身份QC/人审未冒称完成。无新Provider、正式数据/配置/服务、永久测试、依赖/迁移或生命周期动作，目录/启动不变。[预览及集中验证记录](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下未答复/blocked是历史检查点。

Current **144/156,12 open**. The newly approved120-second Graphic batch exhausted CPA3/3 and MiniMax2/2 with all five actual supplier calls returned. Two JPEGs and three real1080×1440 text-only technical PNGs exist; actual Stage acceptance/composition created isolatedMaster9 under the exact defaulttechnicalpreset. New media/render acceptance, context/evidence, fullGraphicQC and human quality remainopen; lifestyleplanning was not completed because automatic continuation consumed one planning slot. No additional dispatch, audio, formalwrite, businesssource/test/dependency/migration/startup or lifecyclechange. See[receipt](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md) and[progress](progress.md). Prior statuses below are historical.

Current **144/156,12 open**. Frozen image/TTS wait consumption is fixed, including the Audio v4 Stage's separate upstream25second range: contract and service now accept existing1–300seconds, default25 unchanged. Formalpolicy120 still blocks excessive requests. Latest21disposable offlinechecks and six existing regression suites **475passed/8warnings,15.20s,exit0**, appRuff/strict38/38/diff pass. Previous fullbackend2495 and Webbuild are historical, not rerun for this two-line upstream correction. No Providercall, Unknownreplay, permanenttest, formaldata/config/service write, dependency/migration/startup or lifecycle change. Realquality/13.6/init/lifecycle remainopen. See[progress](progress.md) and[exact receipt](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md).

The following are previous checkpoints; the runner-only25second explanation is supplemented by the product diagnosis above.

Current **144/156,12 open**. The newly authorized Graphic batch used CPA1/4 and MiniMax2/2: real technical Visual Direction and one1152×864 JPEG returned; the lifestyle image hit the temporary runner's25-second wait and remainsUnknown with no original job handle. All later dispatches stopped; no replay or full defaultGraphic/human-quality approval. FormalSQLite/media/configuration/services and dependencies/startup remain unchanged. See[progress](progress.md) and the[real acceptance receipt](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md). Earlier unanswered-authorization records below are historical.

Latest concentrated gates on current code: **2495 passed/12 skipped/80 warnings,134.01s,exit0**;16 existing renderer cases now actually run, no new tests. CurrentWeb TypeScript/Vite/FE-P1, appRuff, strict38/38 anddiff pass. Manual image panel remains outside five initial static graphs. Progress stays144/156: real-quality,13.6,formalinit/lifecycle remain open and no newProvidercall or formalservice/configuration/write occurred. The paid-call budget is exhausted; awaiting the human's new-batch decision, not repeating gates. Directory/dependencies/startup unchanged; full evidence in[progress](progress.md).

2026-10-08 latest delivery: **144/156，剩12项**。0.3/0.4前置规格纠正完成，真实`stage.variant.adapt@1`与未来少量参数化覆盖计划一致；不授权多平台apply或新增测试。两张1080×1440中文PNG由手工计划＋显式architecture-diagram preset＋现有本机renderer产生，已有223项图文/渲染/API回归通过；这不是默认Persona全链路或人工质量批准，19.3/20.3仍开放。无追加Provider调用、正式写入、依赖/迁移/服务变化，四次MiniMax预算耗尽；其余真实质量、13.6、初始化和生命周期待完成。启动方式不变，详见[当前回执](progress.md)及[PNG证据](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下计数均为历史检查点。

2026-10-08 latest delivery: **142/156，剩14项**。用户授权的本机MiniMax四次真实生成已结束，两图一短音频返回、一超限音频Unknown且不重发；只关闭授权21.2，不冒称完整Persona/人工质量验收。修复CLI帮助stderr兼容，已有165项相关回归/Ruff通过，无新增永久测试或依赖/迁移，启动方式不变。CPA图片协议10.11和ChatGPT手动交接10.12保留；本批不调用CPA、不改正式数据/配置/服务，不归档提交推送。真实图文/音频Stage与成品验收、正式初始化/生命周期仍开放。详见[回执](progress.md)和[样本/哈希](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-08 latest delivery: **140/156，剩16项**，仅关闭已授权10.12。新增轻量lazy `ManualChatGPTImagePanel.tsx`：完整提示词/复制、多图立即暂存/校验/预览/选择和明确接受，复用现有CreativeExecution与MaterialRevision；原自动路由不变，接受不改Master。入口在素材与知识/项目共享素材的生成面板。既有后端2479通过/28跳过、Web/FE-P1、Ruff、strict38/38与隔离API/页面合同检查通过；实际文件选择与组件onDrop分别验证，不冒称原生OS拖拽或真实ChatGPT质量。无新依赖/迁移/正式写入/重启、Provider调用或提交归档。CPA10.11、真实质量/永久覆盖/正式初始化/生命周期仍开放；详细[回执](progress.md)。以下未apply/139记录均为历史。

2026-10-08 latest confirmed design: **ChatGPT manual images**, replacing browser-Agent automation. The frontend option exposes full prompt/copy plus drag/file upload; drop immediately stages temporary candidates, explicit selected acceptance createsMaterialRevision, andMasterbinding stays separate. No browser/session/Cookie dependency, automatic site submission/download or fabricatedproviderreceipt. Samechangeproposal/design/delta/tasks/plan aligned;139/156,17open unchanged. Businessapply still awaits explicitauthorization; no dependency/schema/startup/formal-runtime change. See[progress](progress.md). Earlier Chrome/blocked entries are historical.

2026-10-08 browser choice confirmed: reuse the user's already logged-in localChromeChatGPTsession with browser-owned authentication, no cookie export/profile copy/app credential storage. Read-only loaded composer observed; no image prompt sent. Task10.12 remainsopen and current139/156is unchanged. No dependency/schema/startup change; earlier blocked notes are pre-answer history. See[progress](progress.md).

Current139/156,17open; automatic continuation is blocked after three repeated unresolved protocol/browser and permission checks. Await human clarification under the OpenSpec apply ambiguity rule; no generation or formal runtime change occurred. Existing local startup/dependencies remain unchanged, and the complete requested scope is retained. See[progress](progress.md).

## 2026-10-08 requested image routes restored to scope

Current139/156,17open. The already requested CPA Gemini/Grok images and ChatGPT website images now have explicit open tasks10.11/10.12 in this same change. MiniMax/Voice delivery below is preserved but cannot stand in for those routes. Read-only local settingsrevision5 confirms registered Gemini/Grok have chat only and no image binding; MiniMax image has a binding but currently reports credential_continuity_unverified. No generation request or formal configuration/service change occurred. Exact CPA media protocol review and the user's pending browser/session answer precede dispatch implementation. The amendment does not claim full implementation/quality approval or authorize real calls. No new dependency/table/migration; existing startup remains unchanged. See[progress](progress.md). Earlier139/154/15open entries are historical.

## 当前实施回执：2026-10-08

本 change 当前 **139/154，15项开放**。本批完成共享Image/Audio契约、MiniMax原生1–4图片候选和精确选择、Voice Catalog及普通/高级设置；普通生成页和Persona配置均复用可搜索的有界音色选择器。明确接受仍只写MaterialRevision，不自动改Master/Variant/发布状态。无新依赖、表或迁移，项目启动方式不变。新鲜门禁：backend2479 passed/28 skipped、Web/FE-P1、Ruff、strict38/38、六项隔离浏览器冒烟；限定前端独立复核APPROVE。待办包含13.6持久覆盖、真实Graphic/Audio质量、正式初始化和生命周期；Gemini/Grok直接生图及ChatGPT网站外部执行未在本批实现。零真实调用、正式写入、提交/归档/推送。详见[progress](progress.md)与[实施计划](../../../docs/superpowers/plans/2026-10-08-add-persona-creative-studio-multimedia.md)。以下为历史规格/验收记录。

2026-10-08 规格补充：图片生成与音频生成统一纳入本 change 的多媒体生成契约，不拆成两份 OpenSpec。两者共享配置、Effective Preview、精确绑定、候选结果、回执和人工接受边界；图片与音频仍分别由各自 Adapter、输出校验和质量规则负责。本轮仅修改规格与进度记录，不改业务代码、不建迁移、不调用 Provider。

2026-10-08 当前133/154：科技文字样稿与生活文字编辑稿已获用户人工接受。生活编辑候选仍是隔离证据，不覆盖原Master/Candidate/ZIP；不关闭 Graphic/Audio 真实成品质量、全模态22.6或正式初始化。图片/音频统一多媒体生成契约已补入本 change，新增7项实现任务尚未执行。两个角色文字流程框架已串通，后续在程序内继续调整；原流水线/ZIP/SQLite/回执及正式配置保持，零新Provider调用，无生命周期动作。详见[文字回执](../../../docs/PERSONA_TEXT_FINAL_REVIEW_2026-10-08.md)。

2026-10-08 **当前133/147、剩14，两个真实Text流程已完成19.2/20.2**。科技保留原真实九阶段祖先并追加明确编辑Master5；生活新Run4九阶段接受、Master6→7→8，均经精确当前checks/Candidate v4/Approval/copy_package ZIP回读。17/30请求、实测peak1/最短启动间隔10.0008075秒，原Unknown与正式配置hash保持。Agent阅稿与warning处置不冒充用户质量确认；独立最终工具额度无结论，19.6/20.6/21.3/22.6仍开放。Graphic/Audio/正式初始化/生命周期未执行；自有18337已停，目录/依赖/正式启动保持。[本次回执](../../../docs/PERSONA_TEXT_REAL_ACCEPTANCE.md)，以下131/147状态为历史。

2026-10-08 **科技编辑稿新隔离Master4回接完成，仍131/147**。保留既有稿件APPROVE_EDITORIAL_SAMPLE，仅在新副本经现有服务追加user_edit/parent3、七条精确引用和一事件；幂等/回读/渲染/历史行不变通过。新稿九条checks仍incomplete，实际freeze409且无部分Candidate写入；限定独立APPROVE_ISOLATED_ADOPTION、strict38/38/diff通过。[编辑稿](../../../docs/PERSONA_TECH_TEXT_EDITORIAL_2026-10-07.md)和[回执](../../../docs/PERSONA_TECH_TEXT_EDITORIAL_REVIEW_2026-10-07.md)保留精确hash。不覆盖停止批次、旧Master/Candidate/ZIP，不代替用户或双角色全模态质量验收；正式数据、产品目录、依赖与启动方式保持，零真实调用。

2026-10-07 当前131/147。用户确认验收批次最大并发3、相邻请求启动间隔至少10秒；私有调度器7项离线检查/Ruff通过，默认真实预算0，不启动模型请求或改正式配置/数据。本机依赖/启动方式不变；这是批次级限制，不是产品/CPA全局限流。[证据](../../../docs/PERSONA_TEXT_REAL_ACCEPTANCE.md)，以下130/147及15秒串行记录为历史。

## 2026-10-07 真实Text质量→精修交接修正

实际隔离数据修前186597bytes超过128KiB；修后129061bytes且完整resolution可canonicalize。仅传精确CheckRun ID/input hash/status/full-report hash及必要问题/coverage；完整报告留在immutable源头，原live/currentness/人工warning处置不变。科技初稿已明确编辑保存，实际fact/identity完成，正在同批继续精修；347既有回归通过/8warnings/13.46s，130/147暂不改变。未新增持久测试或放宽大小/调用限制；当前真实质量尚未终验。

2026-10-07 fresh双PersonaText验收已获明确人工授权：应用调用≤30、含首次每请求尝试≤5、Unknown停止；仅新隔离库。旧blocked是未执行的状态计划，实际goal仍active。130/147、17剩余不提前改变；正式初始化/Graphic/Audio/生命周期均未授权。

2026-10-07 **8项持久测试补齐并独立APPROVE，130/147、剩17**。仅关闭3.7/4.6/18.1–18.3/18.7–18.9；最新集中568PASS，18.9落库模态/幂等rowID断言补强后正确拒绝Video→Audio反例。新增Identity/Graphic/Audio三个测试文件，扩展既有catalog/resolver/recipe测试；隔离SQLite、Mock与合成PNG/WAV不替代真实成品质量。零CPA/真实Provider/ASR、正式库/配置/服务或生命周期动作。依赖/启动不变；修后全量终态、映射及17项剩余范围见[progress](progress.md)与[findings](findings.md)。下方122/25及待授权/复核均为历史。

后续自动续行只读核对旧TextUnknown/零Master/原reporthash/临时API已停止，130/147保持；新的真实文字调用授权连续三轮未获人工回答，自动目标置blocked停止重复续行，不把自动消息当新调用许可。正式运行环境/依赖不变，完整目标继续保留。

2026-10-07 **CPA总尝试上限运行修正已生效，仍122/147**。首次计入最多5次；0额外轮次×单轮2凭据，含401补发保守最多4次，stream bootstrap与credits兜底关闭。原配置0600备份，15:58:28原PID700热加载，无服务重启或模型调用。URL/Key、VPN、正式库、旧Unknown及业务任务未动；未新增固定请求间隔，不冒称网络/真实质量通过。目录、依赖与启动方式不变，见[安全回执](../../../docs/PERSONA_TEXT_REAL_ACCEPTANCE.md)。下方未改配置为历史。

2026-10-07 **CPA出站进一步定位，仍122/147、8/30**。原失败窗口Clash147条HTTP出口peer reset与CPA错误相符，v8端口配置正确；日本节点两个Google探针通过，香港超时，原路径后来也恢复HEAD404但不等于稳定生成。未改代理/VPN/配置/服务、不重发或改写Unknown。仅CPA的Google专用路由是待确认的最小策略，不切其他软件出口；目录/依赖/启动不变，详见[回执](../../../docs/PERSONA_TEXT_REAL_ACCEPTANCE.md)，真实Text质量PARTIAL。

2026-10-07 **fresh真实默认Text批次PARTIAL，122/147保持**。新授权30次上限使用8次，两个角色各自研究/角度/大纲真实返回并明确接受；默认三候选初稿Attempt7/8无可用响应、保留Unknown，未重发或替换模型。CPA认证模型发现前后均200/32，但尚无本批文章、Master、Candidate或质量PASS。隔离库integrity=ok，正式models/llm hash不变，自有18336停止。无业务代码/永久测试/正式写入/Graphic/Audio/生命周期变化，沿用现有依赖与启动。见[真实回执](../../../docs/PERSONA_TEXT_REAL_ACCEPTANCE.md)。

2026-10-07 **当前122/147，剩25：19.5 prepared-handoff功能验收关闭**。两个角色默认Video普通页面21检查点通过：中间接受不造Master、显式video.master.v2、Director包人工接受、刷新不重跑；隔离库精确hash/零dispatch回读通过。没有真实质量或新独立APPROVE；此前121/147及无页面证据是历史。本批无业务代码/永久新测试/真实调用/正式写入/生命周期变化，目录/依赖/启动方式不变。完整命令、截图及限制见[progress](progress.md)和[集中回执](../../../docs/PERSONA_NORMAL_PAGE_CONTRACT_ACCEPTANCE.md)。

2026-10-07 **Video prepared-handoff合同补验，仍121/147**：两角色默认Recipe隔离API37点通过，修正UI9:16与canonical[9,16]同值误判；actualDirector包/方法/hash/人工接受幂等/零dispatch成立。相关233回归、Ruff、strict38/38/diff通过；前批1968/full及Web证据分开。独立review工具额度耗尽无结论，19.5仍开放；不冒称普通页面新验收或真实质量。正式库/角色/模型/服务、目录/依赖/启动方式不变，无真实调用/新测试/迁移/生命周期。见[完整回执](progress.md)。

2026-10-07 **当前121/147，剩26：6.4已验证关闭、原独立reviewerAPPROVE**。实际内存Capability→resolver→Graphic composer及Director/Audio就绪临时诊断22/22通过，修后完整backend1968/28skip（102.20s）、Web/FE-P1、全appRuff、strict38/38和范围内空白检查通过。方法参数作为Persona默认、Project覆盖、Run最高；最终method/output/package一致，selector替换阻断，每个参与的确定性节点就绪与执行一致。正式库/模型/角色/服务不变，无永久新测试、真实调用、迁移或生命周期动作；依赖/启动方式沿用现有方案。真实质量/永久覆盖/正式初始化及归档授权仍分开，详见[完整回执](progress.md)。下方6.4待答/暂态数字为历史。

## 10月7日前序记录

2026-10-07 当前120/147、剩27。整体产品/UX22.5与整体backend/data/security22.4均独立APPROVE。原reviewer确认Master回执与中间素材live parent/derived rights两处缺口已闭合、全范围无剩余确认缺陷，不是窄批准。上轮34项临时红绿检查及修后backend1968/28skip（104.40s）、Web/FE-P1、Ruff/root strict38/38、空白检查通过。本次剩余范围核验只读确认旧真实Text库仍有7Unknown、两成稿hash不变、18332无监听；没有新业务实施或重复backend/build，仅校验本次文档。逐项证据/权限缺口见[findings](findings.md)，普通页面证据见[集中回执](../../../docs/PERSONA_NORMAL_PAGE_CONTRACT_ACCEPTANCE.md)。真实质量、6.4、永久覆盖、正式初始化/生命周期仍分开；目录/依赖/启动方式不变，不动正式数据/配置/服务。下面118/147为历史。

2026-10-07 whole复核补充4处既有合同修复：Variant先验证再记安全回执、Quality模态匹配、配置role/祖先归档只读、Text→Audio正确QC/素材指引。69临时后端检查、六组UI与原15状态检查通过；最新1968passed/28skipped（105.15s）、Web/FE-P1、Ruff与root strict38/38通过。仍118/147，不用窄修复关闭整体22.4/22.5、6.4或真实质量。目录、依赖和启动方式不变，正式数据/配置/服务未改；详见[执行证据](progress.md)。
2026-10-07 五处复核缺陷已实施并获限定独立APPROVE：完整profile安全校验、validated Stage回执、只读不建号、精确身份异步归属、跨形态/保存期间编辑保护。41项安全与15项UI状态检查、24点双角色Text合同闭环、最新Web/FE-P1和Ruff通过。最终后端/strict/diff见[本批回执](progress.md)。仍118/147，whole22.4/22.5、6.4、真实创作质量和正式初始化/生命周期不因此关闭；目录/依赖/启动方式不变，正式库/配置/服务未动。

2026-10-07 浏览器启动补充：Dock手动Chrome正常；现有Persona验收脚本改用本机已有headless shell（显式`PERSONA_TEXT_BROWSER`仍优先），无新增安装/依赖或用户profile改动。两个角色Text全链路新鲜24检查点PASS、pageErrors=[]；临时Mock服务已停止，不影响正式库/API/Web。仅验收入口修正，118/147不变，不冒称真实质量或整体复核完成。详情见[当前执行回执](progress.md)。

2026-10-07 **当前实施进度：118/147，剩29项**。两个角色默认图文已在隔离SQLite/Mock规划中走通确定性排版→真实1080×1440 PNG→显式素材接受/保存Master→QC/可冻结；10.1/10.2、17.3精确scope确认及6.6路由修正获限定独立复核APPROVE。组合路由/逐方法使用反馈通过182项既有回归，Web/FE-P1、Ruff、strict38/38通过。非AI组合方法消费边界待一次明确选择；真实创作质量、持久测试补充、正式初始化及生命周期仍未关闭，不宣称全部完成或修好了日常Chrome。

Change: `add-persona-creative-studio`

This change closes the gap between “controllable workflow” and “out-of-box high-quality creation.”

It establishes:

- Persona-native creative defaults instead of User-global style;
- two starter personas: AI科技研发技术博主 and 日常生活方式博主;
- product-owned Studio Creative Skills inspired by Easel's Skill engineering pattern;
- versioned Text/Graphic/Audio style presets and quality profiles;
- Auto / Custom / Composed method configuration;
- intermediate creative stages and thin exact stage handoff;
- real rendered Graphic and playable Audio production loops;
- deterministic quality gates plus real-provider human-rubric acceptance;
- external professional Agent handoff for final video production.

Core truth boundaries remain:

- Identity = who this Persona is and its creative defaults;
- Workflow/Creation Recipe = execution order;
- Studio Skill Pack = product-owned methods;
- Capability Memory = learned/custom reusable methods;
- Provider/Model/Tool = executor;
- Master/Material/Variant/CreativeExecution = authoritative results;
- Candidate/Review/Delivery = final decision and distribution.

The design targets zero new business tables/migrations.

The separate `complete-multiplatform-content-handoff` change remains deferred. Its two prior wording issues are corrected: existing `stage.variant.adapt@1` and future small parameterized persistent coverage. Actual platform apply and new test-file writing still need explicit authorization; neither is granted by this reconciliation.

## 当前实施状态（2026-10-07）

当前以顶部121/147和[progress.md](progress.md)为准；下列120/147、119/147、118/147及99/147等为前序历史。整体22.4安全和22.5产品合同复核保持通过，6.4窄复核已APPROVE；正式库、目录、依赖及启动方式不变。不把临时合同检查当永久覆盖或真实成品质量批准。

### 10月7日前序批次历史

最新续行仍99/147、剩48：Chat Stage/Run精确模型覆盖与Graphic Recipe缺图补料入口已接好，权限与临时锁定分开、素材保存后Preview及时失效，定向独立复核APPROVE。新鲜165项既有后端回归、最终Web/FE-P1、Ruff、strict38/38/diff通过；没有重跑下段1,968项全量。Audio从已接受素材显式执行本机ASR的完整Recipe入口、两角色跨模态产品冒烟与真实质量仍待，不能宣称全部开发完成。目录/依赖/启动方式不变；本批无正式数据、配置、服务或生命周期动作。

当前99/147，剩48；本批新增关闭11.5/12.6/15.6/15.7。Recipe→图文编辑器与真实render状态承接、Persona解码尺寸检查、明确已有ASR对稿/SRT、Starter Fork/只读readiness已落地；dirty Master不覆盖，旧手工Graphic凭据保持。限定独立复核通过，readiness自动建号问题已修正。新鲜后端1968 passed/28 skipped/80 warnings（104.77s），最终依赖修正后105定向passed/1skipped；Web/FE-P1、Ruff、strict38/38通过，444mock/14字幕/10SQLite Starter/5render断言是合同证据，不是实际成品质量。

待完成重点：完整Graphic/Audio Recipe与跨模态产品收口、ASR完整执行入口/浏览器、剩余持久测试和产品复核、两个Persona真实Text/Graphic/Audio默认流程与固定rubric；正式初始化/主规格同步/归档/提交需各自授权。本批没有新测试、依赖、迁移、正式数据/配置/服务或Provider/发布变更；目录与启动方式不变。下方65/147和图文未开始是10月6日历史记录，不是本轮当前状态。

## 10月6日文字批次历史

STATE: EXECUTED — 两个角色文字合同闭环。独立SPEC review已APPROVE，business apply已获授权；65/147项完成、82项待完成。任务只按已有实现和证据勾选，跨形态复合项不因Text部分完成而整项勾选。真实模型创作质量尚未验收，CLI artifact complete不代表业务全部完成。

最新：两个角色都已产出真实Gemini文章，独立编辑复核后以7条精确引用接受到隔离Master，实际checks、Candidate v4/Review及本地ZIP闭环通过。原稿/编辑稿分存；这不是用户质量认可，也不是两个九阶段默认Recipe的完整真实验收。默认Text输出grammar与确定性引用选文转换已补、345项既有回归/Ruff及窄复核通过；真实新合同复测call18/33.76s无响应，Unknown不重发，累计18/30。无正式数据/配置/Persona、图文/音频、迁移或生命周期动作，详见[真实回执](../../../docs/PERSONA_TEXT_REAL_ACCEPTANCE.md)。

### PRD / 需求背景

本轮以用户提供的完整版为来源，将现有Recipe控制面收敛为Persona原生创作系统；十二平台提案暂缓。按用户最新顺序：两个角色文字单独验收→图文单独验收→音频单独验收。Mock合同正确不等于真实成品质量不错。

### 目录结构

```text
add-persona-creative-studio/
├── .openspec.yaml
├── proposal.md / design.md / tasks.md
├── specs/                    13份delta，不同步canonical
├── docs/
│   ├── STUDIO_CREATIVE_SKILL_SPEC.md
│   ├── STARTER_PERSONAS.md
│   └── CURRENT_GAP_MATRIX.md
├── C2C_HANDOFF.md / PACKAGE_MANIFEST.json
└── task_plan.md / progress.md / findings.md
```

### 已完成

- 原包23份文件全部读取、归位；辅助设计放在本change的docs/，避免混入既有运行文档。
- strict所需的6个等价Scenario和1处SHALL用语已补齐；原要求/场景、任务及产品决策不删除。
- Persona→Account→Series配置/快照、Custom精确绑定、两个Starter初始化预览、八个研究/Text方法包已接入；Brand不提供创作默认值。
- 两个九阶段Text Recipe、人工选择/修改/显式接受、fresh-source约束、现有Text checks中的角色化确定性检查和warning人工处置已串通。
- 隔离Chrome浏览器24个检查点通过，覆盖最终Master→Candidate v4→Review/Approval→授权→本地ZIP；完整后端1968 passed/28 skipped及Web/FE-P1通过。
- 代码定向复核已修复数值claim引用范围、身份普通保存丢创作配置、接受中间结果后回读500三个问题。证据与边界见[文字验收](../../../docs/PERSONA_TEXT_CONTRACT_ACCEPTANCE.md)及[progress.md](progress.md)。

### 待完成 / TODO

- 当前仍待：完整九阶段Recipe与用户固定rubric；确定性引用新合同的真实provider验证。两篇文章到本地包已通过，但不能以单阶段/编辑样稿替代默认开箱验收，19.2/20.2保持未勾。以下11/30/零Master等为之前历史记录。

- 最新Gemini文章探针成功：新隔离Unit3/Run7单阶段单候选，50.79s返回完整文章，经真实产品路径校验为text.master.v2；[原稿](../../../docs/PERSONA_GEMINI_ARTICLE_2026-10-06.md)已保存，1822字符。未换模型或重发旧Unknown，累计11/30调用；未接受Master/发布。工程论断仍需收敛，完整两角色Recipe与人工质量验收仍PARTIAL，65/147不变。以下未产出文章/等待模型选择是此前历史状态。

- 最新真实验收为PARTIAL：两个角色研究已接受、生活角度已接受，Gemini在科技角度和生活大纲各120秒超时，旧Unknown不重发；累计10/30调用，未产出Master/完整文章。输出格式与确定失败分类已修正，132项回归、strict38/38/Ruff/diff通过。下一步需明确本轮模型选择，不改变默认Gemini。任务仍65/147；详细证据见真实文字验收报告，下面中途描述保留为历史。

- 当前续行：CPA正式revision5/127.0.0.1:8317已生效，下面旧LAN阻断/未保存描述保留为历史。真实研究响应揭示输出格式合同错误，具体schema/count与确定失败分类已修正，132项现有定向回归和strict38/38通过。隧道已用既有SSH配置恢复；旧Unknown不重写、不重发。两个角色真实正文/人工rubric仍未完成，65/147不变；继续只在隔离库验收Text。

- 两个角色真实模型文章及固定人工rubric单独验收已获授权，但当前CPA地址连接失败；首次科技evidence Attempt保留unknown，生活角色未调用，未产出真实文章。记录见[真实文字尝试](../../../docs/PERSONA_TEXT_REAL_ACCEPTANCE.md)；当前不是“开箱质量已通过”。
- 用户后续指定本机隧道127.0.0.1:8317；最新只读模型发现200，三个已登记模型存在。隧道/鉴权已恢复，但登记入口拒绝loopback且仍未保存新地址；按精确可信端点合同处理，不变更Key/模型/路由、不绕过校验。
- 图文真实PNG/composer/QC随后实施与验收，音频最后；其他模态目前只有部分catalog配置，不能当作已可用。
- 部分Text高级配置/方法扩展/Settings inventory/critic/UX和跨形态复合测试仍待补齐，完整清单见[tasks.md](tasks.md)。
- 真实模型/费用、正式Persona初始化、canonical同步/归档/提交/推送均按各自权限处理。

### 关键设计决策

Persona是创作根；Workflow是Recipe唯一真源；三种Skill inventory分离；图文使用确定性composer和真实renderer；音频以MaterialRevision为真源、不是第四Master。视频继续Director/外部执行，不建内部专业剪辑器。目标零新表/零migration。

### 依赖与启动方式

复用当前ACO/Creation Recipe及既有Identity/Master/Material/Variant服务；业务运行沿用根README的本机SQLite＋素材库＋loopback方式，不新增依赖/migration或改变正式服务。Studio方法作为application package data随API发布。浏览器脚本为`apps/web/scripts/persona-text-browser-acceptance.mjs`，只允许显式标记的隔离Mock库；不会向正式库初始化。检查规格从仓库根目录执行：

```sh
OPENSPEC_TELEMETRY=0 openspec validate --all --strict
git diff --check
```

原始来源包保持不变，路径为`openspec/AIContentStudio_add_persona_creative_studio_OpenSpec/`。本README上方为原包说明，下方归位记录不改变其产品契约。
2026-10-09 **13.6持久覆盖完成，当前149/156、7开放**。两个既有测试文件新增33参数化用例；集中离线236passed/1既有warning/5.29秒，stale-plan与结果签名保护旁路按预期被测试抓住，Ruff/strict38/38/diff通过。仅补已批准合同覆盖，未改正式配置/数据库/素材/服务、未调用Provider或重发Unknown。完整Audio/人审/独立质量及生命周期不虚关；目录/依赖/启动方式不变，[回执](../../../docs/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下为历史检查点。
