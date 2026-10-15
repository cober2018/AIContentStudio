# Website Video Production Handoff Implementation Plan

> For agentic workers: 用户确认完整revision 2后，使用superpowers:executing-plans按编号实施；每步采用checkbox与///。这是同一需求计划的修订，不另建实施目录。第三版已获确认并进入apply，第四版具体增量已确认，不生成示例或持久测试代码。

**Goal:** 从正常视频生产页完成API图片、Grok/Gemini网页素材、Codex交接、达芬奇主剪与AE按需制作，再回收可播放、可修改的完整视频。
**Architecture:** 复用Video Master v2、原生图片ProviderGenerationTask、外部CreativeExecution和MaterialRevision。分镜web_video任务与director.video.v1后期任务使用既有MCP/版本/接受机制；达芬奇是主时间线，AE输出指定合成。
**Tech Stack:** 既有Python/FastAPI/SQLAlchemy/SQLite、React/TypeScript、平台CLI/MCP、用户本机AE/Resolve MCP、Pillow/ffprobe。新增一个项目Skill，目标零新运行依赖/业务表/迁移。

## 已完成的核验和规范历史

- [x] /// 原接口与型号核验：Grok API图片真实成功；Gemini旧接口400，正确generateContent真实成功；诊断回执保留。
- [x] /// 用户确认当前视频走网页，并确认本机AE/达芬奇MCP可用；不继续视频API前置或工具配置排查。
- [x] /// 核对导演页、director.video.v1、外部执行/素材接受和30MiB传输约束，修订同一proposal/design/spec/tasks。
- [x] /// 本版独立方案复核Approved、strict通过，已准备交用户确认；该项仅为文档阶段，不算下方实现。

## 文件职责与范围

仓库根目录为 /Users/mshengran/Project/AIContentStudio；下列为从根起的精确路径。只触碰对应增量必需位置，先读目标目录README。已有相邻dirty不归本需求所有，禁止整体覆盖或顺带重构。

| 路径 | 责任 |
| --- | --- |
| apps/api/app/services/cpa_image_provider.py | 在既有模块增加明确Gemini图片协议/版本执行，旧Grok/V1保留 |
| apps/api/app/services/model_registration.py | 固定原生图片操作传输及安全确认拒绝分类 |
| apps/api/app/services/model_capability_routing.py | 明确图片协议/版本登记、能力与冻结身份，不增加网页伪provider |
| apps/api/app/services/content_harness/providers.py | 必要的新图片适配器版本注册 |
| apps/api/app/services/video_documents.py | 可选shot production配置/引用归一化，旧v2兼容 |
| apps/api/app/services/web_video_handoff.py（新增） | 从精确shot生成网页任务扩展，人工接管/回传入口编排；委托原执行服务 |
| apps/api/app/services/creative_packages.py | web_video与postproduction受限扩展、参考/父素材集冻结、输入缺口 |
| apps/api/app/services/creative_contracts.py | 版本化传输策略、网页/后期安全metadata、必需成果合同 |
| apps/api/app/services/creative_executions.py | 原CAS/状态/输出/接受复用、反馈版本/接管、大小政策和工程依赖保全 |
| apps/api/app/services/creative_execution_files.py | 授权目录分块落地/读取/hash/提交，聚合额度与原路径保护 |
| apps/api/app/services/material_storage.py、materials.py、asset_media.py | 仅为文件流式存储/精确素材接受的必要接口适配，保留其他调用行为 |
| apps/api/app/services/creative_mcp.py | 只传小型引用/进度/安全字段，保持白名单，不增任意文件/主稿写工具 |
| apps/api/app/routers/creative_orchestration.py | 网页任务准备/人工上传/受限预览、沿用接受与反馈服务 |
| apps/api/app/routers/materials.py | 必要的已接受视频授权流式/Range读取，不改无关上传 |
| apps/web/src/product/VideoStudioModel.ts、VideoStudioShell.tsx | 分镜制作字段、素材汇总/明确批量绑定及导演入口 |
| apps/web/src/product/VideoShotMaterialPanel.tsx（新增） | 小型lazy分镜任务面板、网页交接/回传/候选播放 |
| apps/web/src/product/CreativeExecutionPanel.tsx | 剪辑包、实际领取/进度、粗剪反馈、成片/工程审阅与接受 |
| apps/web/src/product/ProductionWorkspace.tsx、ProductionQueuePage.tsx | 必要的阶段投影和精确任务/镜头导航，沿用现有路由 |
| apps/web/src/product/ProviderMediaPanel.tsx、CapabilitySettings.tsx | 区分已实现API图片与网页视频交接，禁止API能力虚标 |
| .codex/skills/video-production-handoff/SKILL.md（新增） | 一个项目执行Skill：读取指定任务、人工网页素材交接、平台CLI/MCP与专业工具执行、原文件提交、对账、复核要求 |

如执行时发现更下层storage_service/media helper必须修改，只增加完成上述端到端路径所必需的既有文件并说明原因；不把列表变成全文件重构白名单。新Skill目录创建前核对父目录；编写时按writing-skills/skill-creator流程，但不新增独立工程或账户系统。

## 1. 范围与基线（对应tasks 1.1–1.2）

- [x] /// 1.1 记录用户对revision 2的明确确认；检查Git真实状态、保存相邻diff/正式配置与素材基线，隔离实施，不复制或改动无关工作。
- [x] /// 1.2 复核原执行/视频/MCP合同及当前测试入口；确认本需求JSON扩展与旧默认限额兼容，不关闭相邻align change。

## 2. API图片（对应2.1–2.2）

- [x] /// 2.1 在上述四个图片/注册模块完成Gemini正确协议和已确认拒绝分类；旧V1原请求、unknown不自动重发和原路由优先级保持。
- [x] /// 2.2 更新能力/素材入口的执行路径显示；分别预览Grok/Gemini API图片与网页视频的实际方式，网页功能不得产生API成功状态。

## 3. 分镜与网页（对应3.1–3.5）

- [x] /// 3.1 在video_documents/VideoStudioModel加入可选versioned production字段；来源ref复用原精确asset_refs，生成时长与使用时长区分。
- [x] /// 3.2 在web_video_handoff/creative_packages按saved Master+shot构建不可变web_video扩展与单输出合同；准备不派发。
- [x] /// 3.3 新网页任务只允许human/manual-web-video；保留历史Codex幂等读取、CAS/unknown和人工接管边界；通用prepare入口同样拦截新自动网页任务。
- [x] /// 3.4 新VideoShotMaterialPanel挂到现有VideoStudioShell，提供任务说明/打开网页/回传/状态；队列和deep link定位准确，不创建新聊天或守护调度。
- [x] /// 3.5 接受素材期间不改Master，完成批次后按shot_id统一明确绑定保存；主动改稿导致旧包过期，旧结果只读并允许已接受素材明确复用。

## 4. 文件与采用（对应4.1–4.4）

- [x] /// 4.1 人工上传与MCP本地文件提交共用输出角色/attempt/来源服务，拒绝错误scope/镜头及重复错配，不靠文件名自动绑定。
- [x] /// 4.2 canonical_output_contract增加显式受限传输策略，确定新合同512MiB单文件/4GiB聚合和单文件并发限制；旧合同30MiB不变，真实已占用/在途字节计入额度。
- [x] /// 4.3 顺序打通HTTP暂存→输入落地/submit引用→hash/ffprobe→Material存储→授权预览。使用有界流式接口，失败清理不碰已接受/被工程引用的依赖，浏览器播放不要求先buffer整个原视频；保持现有身份校验，凭据不进URL。
- [x] /// 4.4 完成真实参数/音轨/权利校验、预览拒绝补交和明确接受，随后从页面明确保存对应分镜引用，刷新核对。

## 5. 专业制作（对应5.1–5.6）

- [x] /// 5.1 creative_packages与CreativeExecutionPanel扩展director.video.v1后期阶段/精确素材/声音/剪辑范围；缺口可见、完整包可复制Codex指令。
- [x] /// 5.2 收口项目Skill为人工素材交接＋专业剪辑MCP；Codex操作平台只用MCP/命令行API，不操作生成网站或点击产品页。
- [x] /// 5.3 固化达芬奇主时间线与AE局部合成清单；音频优先按旁白时间码，网页原声按明确意图，导入AE中间文件后保存可复现的素材/时间线映射。
- [x] /// 5.4 页面反馈绑定rough_cut输出hash/时间码；未接受按高attempt补交，已接受准备新修改执行并冻结新主稿/父成果/反馈，旧任务不重开。
- [x] /// 5.5 校验每阶段MP4、必要字幕、Resolve工程、清单与条件AE工程；保留工程依赖、实际重开/无缺媒体回读，不把路径字符串当成果。
- [x] /// 5.6 最终页面接受与主稿最终绑定保存保持独立操作，执行既有F6D检查和Candidate路径，不自动批准/发布。

## 6. 验证（对应6.1–6.6）

- [x] /// 6.1 在隔离数据/素材环境运行已有tests/test_model_capability_routing.py、test_f7_openai_image_provider.py、test_f6d_video_documents.py、test_f6d_video_capabilities.py、test_aco_creative_executions.py、test_aco_creative_mcp.py、test_aco_schema_lifecycle.py。命令在apps/api中使用.venv/bin/python -m pytest -q与这些路径；使用既有隔离初始化方式，禁止正式DB。apps/web中npm run build包含tsc/Vite/FE-P1；执行git diff --check。
- [x] /// 6.2 一次性隔离验证旧v2/旧合同、错镜头/重复/CAS/过期/撤权、unknown无重发、反馈版本、接管并发、工程依赖/原件保护；用本地受控大于30MiB文件验证完整流式链及512MiB/4GiB边界，检查内存有界，不生成持久测试文件。
- [x] /// 6.3 依已确认预算通过现有CLI API各生成1张真实图片、接受并GET回读；保留用户页面，Codex按revision 3不点击平台。两个新样本均1024×1024，素材版本19/20，仅本地评审。
- [x] /// 6.4 在每次网页可见型号/时长/账户额度核对后完成两个网站各至少1片，累计最多4次网页提交，历史已用2次（含Gemini待核验），剩余最多2次图生视频；由用户人工生成/下载并回传两段原片，Codex只验证精确上传/接管路径，不做无界重试。
- [x] /// 6.5 形成60–90秒至少6镜头样片，其中有两网站素材与1处AE合成；执行达芬奇粗剪、带时间码反馈的新修改任务、最终导出，过程由正常任务包驱动。
- [x] /// 6.6 完整播放检查字幕/音画/黑帧/衔接，重开工程核对依赖；最终MP4及必要成果页面接受、主稿明确绑定、刷新回读；生成质量/AI判断和用户审美确认分清。

## 7. 审查与关闭（对应7.1–7.2）

- [x] /// 7.1 按代码类型的评审规则独立审查实际diff、任务/权限/质量和旧数据保全，修复真实缺陷后定向复核；更新同一README/progress/findings/review。
- [x] /// 7.2 只有全项完成才执行openspec validate verify-grok-gemini-media-capabilities --strict、canonical同步/归档、本地选择性提交；不归档相邻change，不push/公开发布。

## 回退和状态口径

停用新入口/协议即可停止新工作，旧模型/素材/任务仍保留；已产生网页素材、AE/Resolve工程和用户反馈不可因回退删除。当前已实施工程增量并完成独立代码复核，真实网页原片与专业样片尚待完成。提案文档的ready/strict不等于产品可用或实际视频通过。

## Revision 3 调整步骤（已确认）

- [x] /// 网页任务入口只保留人工模式：复制文案、提示词、参数；可打开网站；人工上传精确镜头。历史执行不删、不自动重发。
- [x] /// 更新项目Skill：网页素材等待人工回传；素材齐备后平台MCP交给Codex，达芬奇主剪/AE局部制作保持。
- [x] /// 用用户回传原片完成原样片/反馈/成片/工程验收；不再自动操作Grok/Gemini，不将未生成或未取回媒体记成通过。

- [x] /// 按原设计复用creative-mcp的15个现有工具；prepare/upload/授权accept/save走命令行现有REST，不扩MCP权限或新建CLI框架。正常页面保留给用户，Codex不以浏览器点击执行或验收平台。

## Revision 3 已确认实施与MCP安装

用户已明确确认第三版并授权安装本平台MCP。
- [x] /// 收口人工网页任务/复制包与Skill；Codex不点击本平台或生成网页。
- [x] /// 使用轻量stdio到本机HTTP传输适配注册Codex MCP，凭据仍从原私有runtime读取；不新增daemon/第三方依赖或MCP业务权限。
- [x] /// 实测Codex MCP握手/15工具与只读调用，质量审查后记录安装回执。
- [x] /// 完成不依赖人工原片的工程验证；原片回传前保留真实样片/归档闸门，不虚报完成。

## Revision 4 先图后视频提示词（方向已确认，具体规范已确认）

- [x] /// 更新同一proposal/design/spec/tasks与流程图；检查现有两张真实图片：均1:1，主体布局不同且未授权模型外发，保留为风格候选。
- [x] /// 3.6 在video_documents/VideoStudioModel复用reference引用，引入v2制作配置及prompt_reference版本/hash；VideoShotMaterialPanel串起现有图片入口、选图确认、据图提示词编辑。图片接受不自动选定；换图后重核提示词。复用现有图片能力，不新增提示词服务。
- [x] /// 3.7 在web_video_handoff/creative_packages与creative_executions校验新图生视频准备合同；同一包冻结图片/视频提示词/参数，授权图片可下载；缺图/错版本/撤权均不可新准备。历史v1包/幂等/原片保持，不批量回填。
- [x] /// 5.2 更新既有项目Skill，实际看图后才写视频提示词；平台CLI/MCP、网页人工、达芬奇主剪及AE按需保持。
- [x] /// 6.4 确认适合16:9的关键帧并保存来源与授权，再据图交接两网站；本版拟最多追加2次图片生成，未确认前不发请求。API图片原2/2验收保留，新关键帧不冒充已验收。先对账旧网页任务，不删除历史或重复提交。
- [x] /// 使用已有回归与临时验证检查顺序/换图/历史兼容/权限，构建前端；仅在真实图生视频、剪辑、反馈与工程重开全部完成后归档选择性提交。

已实测按用户选B：接受图片21 → 先保存仅图片主稿40 → 看图编写两个视频提示词并保存41 → 只准备人工网页执行4/5 → MCP协议CLI回读；网站未派发，等待人工原片。实际图片请求累计4/4；完整样片/反馈/工程重开与归档提交仍待完成。


## 2026-10-15 已确认：受限成片本地绑定

用户明确确认：已接受且具有当前本地/model使用授权的最终MP4允许明确绑定为本地主稿并私有预览；不提升任何权利标记，Candidate/交付/发布继续检查public_use_allowed。同步调整现有后端保存、前端选择/绑定/预览，不新增权限类别、业务表或发布路径。

- [x] /// 在同一已确认规范内修改content_masters保存和VideoStudioModel/VideoStudioShell本地绑定、私有预览；保留Candidate、渲染和发布公开检查。
- [x] /// 临时隔离验证受限最终绑定/回读/私有预览成功，撤权或未接受结果拒绝，Candidate公开门禁阻断；不新增持久测试。独立代码复核后继续原归档提交。


## 配音纠正与当前阶段（2026-10-15）

用户指出当前样片无配音；实际Master voice为none、ResolveExportAudio=false，文件确实无音轨。此选择由执行方将网页素材静音误延续至整片，不代表用户要求无旁白。当前72秒文件只作为无声粗/成片历史证据保留，不能作为用户最终有声交付。归档和提交暂不执行；已建议使用当前科技角色已有音色补旁白，等待本次音色方向确认后重做音画/字幕对齐与有声评审。

本地绑定补充已真实HTTP验证：Master44绑定final素材33成功，rights仍public=false/model=true；私有会话200、Range206；Candidate409 readiness_blocked/asset_unready，公开门禁未放宽。独立代码复核继续，不把本地绑定等同公开交付。

- [x] /// 用户确认音色方向后，以角色既有TTS/旁白能力生成并验收旁白；不得把素材静音沿用为整片无声。
- [x] /// 新保存有声主稿/导演包，达芬奇以旁白为时间基准完成新成片、字幕与工程回传，再做有声质量及绑定回读；保留无声历史，不就地覆盖accepted输出。


## 2026-10-15 已确认补旁白

用户确认按当前科技角色音色与现有文案补旁白，并重新剪辑/对齐字幕。只读核对隔离identity snapshot13：lengdan_xiongzhang、speech-2.8-hd、minimax.speech、rate1。平台TTS任务355a4f33b1a046c29cb84bcf2ad2aee2已准备，单次执行进行中；不重新生成网页视频或图片。以实际声音为时序依据，时长保留60–90秒样片范围；无声accepted历史保留，有声成果另建执行。


## 当前结论：有声版完成，准备生命周期关闭

已完成上列真实媒体、MCP/CLI交接、私有采用及独立复核；当前29/29；已同步13新增/1修改并归档，选择性本地提交以对应Git记录核验。最终主稿46/执行8/素材40，60秒有声版；旧无声与失败QC草稿保留为历史。最终回执见receipts/final-sample-acceptance.json。
