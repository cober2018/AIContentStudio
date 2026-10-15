# Findings

- 本机models revision13：Grok4.7/Gemini3.8-flash-high为chat；Grok imagine image/Gemini3.1-flash-image各有图片binding，模型登记和执行不同。
- CPA目录包含Grok imagine video/1.5/preview，未列Veo/Gemini Omni；模型列表明确verified_capabilities=false。
- 当前provider_request仅允许models/chat-completions/images-generations，未实现CPA视频；原生google/xai文件只是codec，不具备执行器。
- xAI现行Responses image_generation工具可显式调用Imagine；普通chat请求未携带工具无自动媒体能力。xAI视频是显式Imagine视频请求、job轮询。
- Google现行文档已有Gemini Omni Flash视频和Veo，不能概括为Gemini不能生成视频；也不能把普通Flash多模态理解等同于生成所有模态。

- 实测Grok图片能由当前CPA OpenAI图片协议返回真实图；此为适配器级验证，未从正常页面采用或提升formal verified状态。
- Gemini图片本次HTTP边界拒绝而非图像解码错误；普通模型存在、image binding存在不足以证明此端点支持。需核对该网关Gemini图片协议和拒绝原因，不能靠勾选能力或盲换model解决。
- 网关根说明CLI Proxy API Server，公开模型列表同时含专用视频型号；根端点列表不完整（实际images可用），因此不能用根目录没列video证明网关video不可用。openapi.json404，models响应无可验证版本；不把其他fork公开代码当成本部署事实。
- 当前图片适配器只支持文生图，不接受source_bytes/source_revision_ids，不能把已验证文生图扩大为图片编辑/图生视频。
- Grok原生Harness底层具体链路本轮未见trace；官方API显式工具路由可以证实，不能据品牌或模型自述推断每次内部路由。

## 2026-10-15 根因与方案更新（取代上方待查状态）
- Gemini独立诊断捕获HTTP400原文：gemini-3.1-flash-image不支持/v1/images/generations或edits。不是从502猜鉴权/配额原因；旧适配器丢失上游状态而泛化unknown。
- 同一已登记网关与凭据，固定/v1beta/models/gemini-3.1-flash-image:generateContent、responseModalities IMAGE成功。实际JPEG361211字节、1024×1024、15.682秒、modelVersion一致、usage1468tokens；解码和可视通过。没有更换provider或盲试别名。
- Grok视频空prompt POST返回400 Prompt cannot be empty，只证明校验可达；随机job GET返回静态not-found，不能证明可查询或不存在完整查询接口。0有效视频生成提交。
- Gemini Omni/Veo当前未出现在目录，查询的两个型号详情404。Gemini图片型号详情包含text/image输出，无法外推video。
- 当前8317是SSH转发；只确权中转，不改远端。网关当前部署版本仍未证明，公开上游合同只作参考。
- 方案复用原路由/任务/采用；V2明确协议，旧V1不改写，MiniMax默认优先级保持。Gemini视频缺失属于未完成前置；不以不可用展示宣称全能力完成。
- 新增七条要求、修改一条现有要求、19项未实施任务。用户要求先确认方案，应用代码和正式配置未改。
- 官方参考：Google https://ai.google.dev/gemini-api/docs/image-generation 、https://ai.google.dev/gemini-api/docs/video 、https://ai.google.dev/gemini-api/docs/omni ；xAI https://docs.x.ai/developers/model-capabilities/video/generation 。实际核验回执优先于品牌、目录及公开上游推断。

## 制作流程范围调整
- 用户明确当前使用的API通道不支持所需Grok/Gemini视频，仍支持图片；按此通道约束设计，不能泛化为官方完全没有视频API。
- 用户确认AE与达芬奇本机MCP可用，只是程序未打开；后续不以本轮查到的disabled配置阻塞方案，也不再自行排查或启用。
- 已有creative_packages.py支持director.video.v1，打包script/shots/voice/subtitles/overlays/music/cover/timeline；creative_mcp.py和creative_execution_files.py提供既有受限外部执行/成果基础。已有受控验收文档明确未证明真实专业工具完整成片，需复用后做实际验收。
- 建议以完整脚本/旁白节奏驱动分镜，逐镜头确定已有素材、API图片、网页视频或AE动画；以镜头ID关联生成指令、参考图、实际MP4及采用版本，再统一交给达芬奇时间线。AE只制作需要的合成/动效，避免两套主时间线。
- 调整方向待用户确认；本轮只记录范围变更与调查，不替代正式规范重写、apply或成片验收。

## Revision 2已确认分工与最小实现范围
- 用户已确认平台编排、网页生成素材、达芬奇主剪、AE按需；本轮授权为更新原OpenSpec并再次提交确认，非apply。
- 实际入口为VideoStudioShell导演工作台及CreativeExecutionPanel；主路由/projects/:projectId/units/:unitId/production。采用分镜任务＋现有外部执行区，不增加顶层导航或平行任务库。
- 单镜头web_video扩展沿用creative.execution.v1；专业剪辑扩展沿用director.video.v1。接受素材后批次统一保存Master，避免自动改稿让同批其他任务过期。
- 接受后的外部执行已是终态；粗剪反馈必须绑定输出hash并新建修改任务，不能往旧accepted任务补写。
- creative_contracts.MAX_FILE_BYTES实际为30MiB；完整视频交付需新增显式有界传输策略，并贯通上传/落地/校验/存储/授权预览。只调常量不足。
- 工程交付需要实际重开与素材依赖保全；路径/项目文件存在不足以证明可继续编辑。保留原MCP只提交/请求审阅、不自动接受或改Master的职责。
- 同目录规范改为12新增/1修改和27项待实施；原API视频实现范围被替代，诊断证据仍保留，不关闭相邻change。

实际验收：指定Gemini账号可见Create video，旧账号菜单不可用不代表此账号不可用。已切换且不购买订阅。首秒解码不足以验证原片完整性，现完整流式解码限300秒。最终绑定MP4须走新材料会话桥接而非旧raw完整buffer；Range GET逐次检查实时公开权限。

用户决策（revision 3）：网页自动操作耗时不符合效率目标；网页生成改为人工，平台只提供文案、提示词、参数及原片回传。该决定替代第二版自动浏览器执行验收要求，保留已派发任务历史；专业剪辑仍按原方案。

本平台接入核验：原北斗星第15–16节规划Creative Execution MCP，相邻align设计第9节已落位为loopback Streamable HTTP，同FastAPI进程。正式8000 live tools/list已成功返回15个工具；读取/领取/落输入/进度/提交/unknown支持。prepare、accept和Master save明确不在MCP工具清单，已有REST接口可由命令行调用，不需要浏览器或新CLI框架。用户明确要求本平台后续只走CLI/MCP，人工网站生成边界不变。

MCP安装决策：桌面进程未继承项目专用Bearer环境变量，故使用标准stdio客户端入口到固定loopback HTTP的无依赖适配；适配从既有私有runtime文件仅读AICS_CREATIVE_MCP_TOKEN，不执行其shell内容、不保存新凭据、不重试写请求。Codex注册名aicontentstudio-creative，owner范围继续由服务端原绑定决定。

## Revision 3 实施事实

仅封网页专用prepare不足：通用prepare_execution也可新建旧Codex网页模式。现于历史幂等回放之后限制新的web_video为human/manual-web-video/1，director专业剪辑不受影响；受控检查与独立复核通过。

Codex现有MCP可通过stdlib stdio转本地HTTP接入，不需要另建业务MCP。aicontentstudio-creative已注册；令牌继续留在原私有runtime，初始化与15工具已验证。正式8000与隔离8016职责分开。

Gemini图片V2原生generateContent真实成功；Grok旧V1同样真实成功。两张图片接受仅用于本地评审，不能凭生成成功宣称公开/商业使用授权。网页Grok原片未本地取得、Gemini结果未核验；用户人工回传前不闭合专业样片或归档。

## Revision 4 先图后提示词

先图后提示词不等于给旧文生视频提示词附图：须在实图确定后编写动作/运镜，记录提示词所依据的精确图片版本，换图重核。现有Grok图片排列卡片＋金字塔状棱镜，Gemini叠放卡片＋柱状棱镜，均1024×1024；既有accepted仅代表本地素材入库，非分镜定稿，且model_use_allowed=false。新关键帧拟使用已有/上传或最多追加2次API请求，不擅自升级素材授权。

## Revision 4 横屏图片实际制作

新Grok候选1280×720（145179字节）、Gemini候选1376×768（667404字节）均一次真实生成，保留原始JPEG与任务回执，待用户审美确认；没有替用户绑定镜头、写视频动作提示词或操作网站。API图片累计4/4。Gemini原生1K横图1376×768见[官方尺寸表](https://ai.google.dev/gemini-api/docs/generate-content/image-generation)，与本地通用1280×720不同；仅对确切Gemini3.1/v2校验使用其原生尺寸，不放宽实际像素硬上限。隔离图片像素策略1048576→1100000并保全其他配置，正式配置未改。

用户选B后两段共用同一图，避免两张候选细节不同造成连续场景误认。图库接受、镜头选图保存、据图写提示词保存、准备网页任务是四个实际独立步骤，已由CLI按40→41→4/5完整回读。参考图下载必须在项目/单元及可选冻结包范围重新检查实时权限；浏览器已生成的blob只用于预览，下载重新请求。图片版本/hash变化即清除prompt_reference，保留正文，切回旧图也不能自动恢复确认。


## 2026-10-15 真实回传与专业样片

用户回传Grok/Gemini原始MP4，保全原件及SHA256；Grok1280×704补上下各8px，明确取6秒；Gemini10秒明确取前8秒，静音副本已通过精确任务4/5接受为素材22/23。Gemini场景结构偏离B，仅作独立氛围镜头，不宣称严格连续同景。

Master42驱动真实达芬奇72秒粗剪（6分镜）与AE14秒合成（23层），6项成果均通过执行6接受。AI评审在68秒要求结束标题及最后12帧淡出；新Master43与执行7冻结父输出ID/hash和反馈，实际达芬奇修改并导出final-cut.mp4。原生DRP以新工程名导入重开并再次完整渲染；AE原生AEP重开，1合成/23层/0缺媒体。原片、全部依赖和校验记录保存在用户媒体目录edit/aics-web-video-20261015。

最终主稿绑定仍未通过：素材链public_use_allowed=false，现有后端及前端要求render_output公开权限。保留权限而不伪造升级；已请求用户确认“仅本地绑定、Candidate/发布门禁保持”的同一规范补充，未确认前不改合同。5.6、6.6、7.2保持未完成，不能归档。


## 2026-10-15 已确认：受限成片本地绑定

用户明确确认：已接受且具有当前本地/model使用授权的最终MP4允许明确绑定为本地主稿并私有预览；不提升任何权利标记，Candidate/交付/发布继续检查public_use_allowed。同步调整现有后端保存、前端选择/绑定/预览，不新增权限类别、业务表或发布路径。


## 配音纠正与当前阶段（2026-10-15）

用户指出当前样片无配音；实际Master voice为none、ResolveExportAudio=false，文件确实无音轨。此选择由执行方将网页素材静音误延续至整片，不代表用户要求无旁白。当前72秒文件只作为无声粗/成片历史证据保留，不能作为用户最终有声交付。归档和提交暂不执行；已建议使用当前科技角色已有音色补旁白，等待本次音色方向确认后重做音画/字幕对齐与有声评审。

本地绑定补充已真实HTTP验证：Master44绑定final素材33成功，rights仍public=false/model=true；私有会话200、Range206；Candidate409 readiness_blocked/asset_unready，公开门禁未放宽。独立代码复核继续，不把本地绑定等同公开交付。


## 2026-10-15 已确认补旁白

用户确认按当前科技角色音色与现有文案补旁白，并重新剪辑/对齐字幕。只读核对隔离identity snapshot13：lengdan_xiongzhang、speech-2.8-hd、minimax.speech、rate1。平台TTS任务355a4f33b1a046c29cb84bcf2ad2aee2已准备，单次执行进行中；不重新生成网页视频或图片。以实际声音为时序依据，时长保留60–90秒样片范围；无声accepted历史保留，有声成果另建执行。


## 2026-10-15 有声最终验收（当前结论）

用户确认按科技角色原音色补旁白。已核对snapshot13的lengdan_xiongzhang/speech-2.8-hd/rate1，平台单次TTS任务355a4f33b1a046c29cb84bcf2ad2aee2成功并接受素材36；25.309844秒原声离线ASR102/102字匹配、95词/子词时间，无削波。按实测停顿/词界形成10句旁白，不扩写、不拉伸语速、网页原声仍静音。达芬奇04时间线60秒/6逻辑镜头（主轨7段含片尾）、14秒AE、9段烧录字幕与结束标题。

质量中实际发现两处媒体问题并修复：输出侧seek未重置PTS使初次分段fade错静音，改atrim→asetpts→30ms淡入淡出，10段全部非零；Resolve AAC尾填充60.074667秒超过既定一帧容差，保留原导出并stream-copy remux为60.010秒，不放宽校验。H264逐字节不变、AAC为原数据精确前缀；所有讲话58.31秒前结束。最终10句AAC对PCM相关最低0.9999938，最大lag0ms；原始声道peak.842、满幅0，-15.3LUFS/-1.5dBTP，1800帧完整解码通过。

实际重开最终DRP至AICS_Narrated_Fixed_Reopen_20261015/04_Narrated_Final_60s，44个本机媒体依赖均存在，再次完整有声导出，AAC与native原导出完全同字节。AE原生AEP已真实重开，14秒/23层/0缺媒体，本轮未改变该合成字节。独立最终媒体和代码复核Approved；未直接试听的感官边界保留，舒缓且留白较多，不宣称节奏紧凑。

平台执行8的6项成果均accepted；源Master45→明确绑定Master46，final素材40。实际私有会话200/Range206，公开/商业仍false、本地资格true；Candidate409/asset_unready，发布门禁保持。初次无声执行6/7和QC失败03草稿作为历史，未覆盖accepted历史。

最终候选补齐大视频Variant遗漏：_validate_video_assets使用有界verify_bytes_checked，保留全部公开/状态/hash/MIME门禁；31MiB+64字节临时5例红绿、81既有回归通过。31个精确代码/Skill路径经独立提交范围复核；候选244通过/1项HEAD既有schema断言失败已单列，Web/FE-P1、Ruff/diff、local14通过，无持久测试新增。工作区安装时70个相邻dirty tracked文件逐字节保全，url_fetch现有邻接响应元数据不覆盖。

最终数据均在隔离8016/5186及用户媒体edit目录；本轮未写正式业务数据库，未push或公开发布。所有源片、原TTS、依赖、失败与归一化回执保留。质量/接受/权利/工程与测试的脱敏汇总见同目录receipts/final-sample-acceptance.json。
