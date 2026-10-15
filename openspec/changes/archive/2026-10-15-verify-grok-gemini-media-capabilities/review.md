# Review

## Revision 2（2026-10-15）
状态：APPROVED_FOR_USER_CONFIRMATION。用户已确认分工，完整revision 2仍待确认；未apply，实施0/27。

本版复核对象为proposal/design、web-video-production-handoff的12条新增要求、model-capability-routing的1条图片修改要求、27项tasks及同一task_plan。

检查重点：页面入口具体；分镜与冻结版本/回传候选精确关联；Codex和人工路径同一执行合同；网页派发一次与unknown对账；视频大文件全过程可用；达芬奇主剪/AE按需；粗剪终态后新执行；成片/工程依赖和重开真实验收；旧任务、相邻change和本轮文档权限边界。

## 历史审查边界
Revision 1独立评审Approved和strict只覆盖原API视频提案；用户改变范围后已失效为当前实施依据。Grok/Gemini图片诊断继续有效，旧视频目录/参数校验不算网页/专业制作验收。原始回执保持，费用和网关内部重试不作零值推断。

## 本版复核结果

writing-plans要求的独立只读方案评审web_video_plan_review：Approved，未发现阻碍交用户确认的实质问题。已核对页面/服务职责、creative.execution.v1与director.video.v1复用、素材接受与主稿保存分离、accepted后新修改执行、大文件全过程/旧限额兼容、图片API与网页视频分工，以及测试/相邻change/本机工具边界。

OpenSpec strict：valid。机械核对：12条新增要求、1条修改要求、27项实施任务全部未勾选；proposal/design/specs/tasks均ready。旧API视频待实现断言已从当前文档删除，历史回执留在receipts/progress。git diff --check通过。

这只是方案审查与规范结构检查，没有运行应用测试、模型、网页生成或专业工具，也没有完成真实样片、apply、归档或提交。

## 实施独立复核（进行中）
图片SPEC/Python通过；后端SPEC发现5项跨层遗漏已修复并复核Approved。前端独立复核两项真实缺陷已修复并Approved；Python发现视频仅首秒解码，改完整有界解码并临时损坏/超时验证。最终MP4大文件流式预览新增两文件经独立code-reviewer只读Approved。完整样片质量、工程重开与最终采用未验收，不因此归档。

Revision 3方案独立只读复核：清除自动网页操作旧要求、明确MCP/命令行REST与正常用户页职责后Approved，最后版本号文字已同步。strict通过，尚待用户确认后改入口和Skill，不把方案确认当真实样片验收。

## Revision 3 实施独立复核（2026-10-15）

manual_revision3_impl实现后，handoff_frontend_review（TypeScript）Approved；handoff_backend_python_review（Python，含stdio适配）Approved；stdio_bridge_review（code-reviewer）Approved。handoff_backend_spec_review先报告通用prepare可绕过人工网页限制，修复后再次Approved。未增加持久测试。

验证：150既有相关回归、Web/tsc/Vite/FE-P1、临时人工4项/通用入口6项与实际HTTP回读通过；实际Codex注册命令初始化/15工具通过。两真实API图片视觉检查及接受回读通过。

结论仅为工程增量复核通过；此前244通过/1项HEAD已有schema断言失败仍单列。人工原片、完整剪辑与反馈、工程重开、最终接受绑定未通过，故不归档提交。

## Revision 4 先图后提示词

第四版规范自检：保留第三版工程证据及历史文生视频任务，新增顺序/换图/专用与通用prepare验证；仅复用原图片/素材/执行职责，不新增业务表或提示词服务。真实新图生视频、专业样片及生命周期仍未完成。独立方案审查和strict结果随后追加。

第四版独立方案复核revision4_plan_review：Approved。已消除v1/v2新建任务歧义、Skill旧浏览器职责及网页预算累计口径差异；OpenSpec strict通过。仅文档审查，不代表第四版实施或样片验收完成。

## Revision 4 图片独立AI目检

revision4_image_quality直接查看两张真实JPEG：A宽景、B近景均具备图生视频起始帧条件，无可辨文字或品牌，未见阻断使用的几何错误。优先推荐B；笔记本、卡片摆法和棱镜比例不同，不能声称两图为同一地点严格连续机位。透明玻璃折射和细边须在实际视频中继续验收。用户图片审美确认仍待完成，当前未写视频动作提示词。

首次工程SPEC复核发现参考图下载仅使用通用raw及缓存权利标志，未在下载时实时复查。正在以同一项目/单元范围的读取校验修复；不修改无关全局raw语义。

## Revision 4 最终工程复核

revision4_spec_compliance：修复参考图下载实时权限后Approved。revision4_python_quality：指定6个Python增量Approved，Ruff通过。revision4_typescript_quality：换图A→B→A不应恢复旧确认的问题已修复，最终Approved，tsc通过。实际图片AI目检结论与用户选B均已记录；视频画面质量尚无结果，不把图片通过当作视频/工程验收。


## 2026-10-15 真实回传与专业样片

用户回传Grok/Gemini原始MP4，保全原件及SHA256；Grok1280×704补上下各8px，明确取6秒；Gemini10秒明确取前8秒，静音副本已通过精确任务4/5接受为素材22/23。Gemini场景结构偏离B，仅作独立氛围镜头，不宣称严格连续同景。

Master42驱动真实达芬奇72秒粗剪（6分镜）与AE14秒合成（23层），6项成果均通过执行6接受。AI评审在68秒要求结束标题及最后12帧淡出；新Master43与执行7冻结父输出ID/hash和反馈，实际达芬奇修改并导出final-cut.mp4。原生DRP以新工程名导入重开并再次完整渲染；AE原生AEP重开，1合成/23层/0缺媒体。原片、全部依赖和校验记录保存在用户媒体目录edit/aics-web-video-20261015。

最终主稿绑定仍未通过：素材链public_use_allowed=false，现有后端及前端要求render_output公开权限。保留权限而不伪造升级；已请求用户确认“仅本地绑定、Candidate/发布门禁保持”的同一规范补充，未确认前不改合同。5.6、6.6、7.2保持未完成，不能归档。


## 配音纠正与当前阶段（2026-10-15）

用户指出当前样片无配音；实际Master voice为none、ResolveExportAudio=false，文件确实无音轨。此选择由执行方将网页素材静音误延续至整片，不代表用户要求无旁白。当前72秒文件只作为无声粗/成片历史证据保留，不能作为用户最终有声交付。归档和提交暂不执行；已建议使用当前科技角色已有音色补旁白，等待本次音色方向确认后重做音画/字幕对齐与有声评审。

本地绑定补充已真实HTTP验证：Master44绑定final素材33成功，rights仍public=false/model=true；私有会话200、Range206；Candidate409 readiness_blocked/asset_unready，公开门禁未放宽。独立代码复核继续，不把本地绑定等同公开交付。


## 2026-10-15 有声最终验收（当前结论）

用户确认按科技角色原音色补旁白。已核对snapshot13的lengdan_xiongzhang/speech-2.8-hd/rate1，平台单次TTS任务355a4f33b1a046c29cb84bcf2ad2aee2成功并接受素材36；25.309844秒原声离线ASR102/102字匹配、95词/子词时间，无削波。按实测停顿/词界形成10句旁白，不扩写、不拉伸语速、网页原声仍静音。达芬奇04时间线60秒/6逻辑镜头（主轨7段含片尾）、14秒AE、9段烧录字幕与结束标题。

质量中实际发现两处媒体问题并修复：输出侧seek未重置PTS使初次分段fade错静音，改atrim→asetpts→30ms淡入淡出，10段全部非零；Resolve AAC尾填充60.074667秒超过既定一帧容差，保留原导出并stream-copy remux为60.010秒，不放宽校验。H264逐字节不变、AAC为原数据精确前缀；所有讲话58.31秒前结束。最终10句AAC对PCM相关最低0.9999938，最大lag0ms；原始声道peak.842、满幅0，-15.3LUFS/-1.5dBTP，1800帧完整解码通过。

实际重开最终DRP至AICS_Narrated_Fixed_Reopen_20261015/04_Narrated_Final_60s，44个本机媒体依赖均存在，再次完整有声导出，AAC与native原导出完全同字节。AE原生AEP已真实重开，14秒/23层/0缺媒体，本轮未改变该合成字节。独立最终媒体和代码复核Approved；未直接试听的感官边界保留，舒缓且留白较多，不宣称节奏紧凑。

平台执行8的6项成果均accepted；源Master45→明确绑定Master46，final素材40。实际私有会话200/Range206，公开/商业仍false、本地资格true；Candidate409/asset_unready，发布门禁保持。初次无声执行6/7和QC失败03草稿作为历史，未覆盖accepted历史。

最终候选补齐大视频Variant遗漏：_validate_video_assets使用有界verify_bytes_checked，保留全部公开/状态/hash/MIME门禁；31MiB+64字节临时5例红绿、81既有回归通过。31个精确代码/Skill路径经独立提交范围复核；候选244通过/1项HEAD既有schema断言失败已单列，Web/FE-P1、Ruff/diff、local14通过，无持久测试新增。工作区安装时70个相邻dirty tracked文件逐字节保全，url_fetch现有邻接响应元数据不覆盖。

最终数据均在隔离8016/5186及用户媒体edit目录；本轮未写正式业务数据库，未push或公开发布。所有源片、原TTS、依赖、失败与归一化回执保留。质量/接受/权利/工程与测试的脱敏汇总见同目录receipts/final-sample-acceptance.json。


## 生命周期关闭回执

2026-10-15已执行OpenSpec strict及archive --yes：13新增/1修改同步canonical，归档2026-10-15-verify-grok-gemini-media-capabilities。CLI当时28/29的唯一未勾选项正是7.2归档/提交操作本身，未跳过功能、质量或媒体验收；现29/29。代码与文档按最终干净blob选择性本地提交，相邻dirty保留；无push。


归档后干净候选OpenSpec全量strict：45 passed / 0 failed。
