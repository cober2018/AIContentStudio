# 网页视频素材与专业剪辑交接

## PRD / 需求背景
已确认先图片→据图提示词→人工网页图生视频→平台回传→达芬奇主剪、AE按需；API承担图片。Codex只通过CLI/MCP操作平台。最终样片需有科技角色旁白、字幕和可重开的工程。

## 当前阶段、代码位置与版本
**ARCHIVED_CONFIRMED，29/29。有声样片与独立复核完成，canonical已同步；本地选择性提交以Git记录核验。** 本地main基线636d60e；已审查31个代码/Skill路径及同一成果目录。干净候选在codex/web-video-candidate，实际本地工作区/相邻修改保留；提交号以最终本地Git记录为准。没有push、公开发布或正式数据库写入。

## 正常入口与使用
项目→内容矩阵→视频单元→视频主稿·导演工作台。分镜先确认图片再写提示词，人工生成后精确上传/接受，应用所选素材并保存。旁白需单独选择已接受音频，原片静音不代表成片无旁白。准备导演包→Codex领取→粗剪反馈→新修改执行→成果接受→明确绑定并保存。非公开成片显示“仅本地使用；公开交付仍需授权”；私有预览可用，Candidate仍检查公开权限。

## 本次真实结果
- 隔离项目7/单元13，Master45→最终绑定46，执行8六项accepted，final素材40。
- 60秒1080p/30fps、6逻辑分镜，含Grok/Gemini真实回传片、14秒AE、10句冷淡熊掌旁白、逐句字幕与结束标题。
- 单次TTS，原声ASR102/102字匹配；实际成片十句波形及完整解码通过；DRP/AEP实际重开，无缺媒体。
- 私有preview200/Range206，公开/商业false；Candidate409明确保留。舒缓示范片、留白较多；未直接试听，不能等同人类感官验收。
- 最终MP4：`/Users/mshengran/DaVinci Resolve Media/edit/aics-web-video-20261015/narrated/final-voiced.mp4`。同目录有SRT/DRP/edit-manifest；AE原生工程和中间MOV在其父目录。原片与全部本机依赖保留，不宣称独立跨机包。

## 目录结构与证据
proposal/design/specs是已确认规范；tasks/task_plan持续维护；progress/findings/review记录事实与复核；receipts/final-sample-acceptance.json是当前脱敏验收。原始媒体/敏感运行配置只在Git忽略backups及用户媒体目录。

## 已完成与TODO
功能、真实图片/网页回传、有声剪辑、反馈/修改、工程重开、本地绑定与独立复核均完成。本次生命周期关闭已完成；选择性本地提交随本成果进入Git，不push。已知候选244通过/1项HEAD旧schema断言失败单列，81定向、14本地绑定、5大文件、Web/FE-P1、Ruff/diff通过；无新增持久tests。

## 关键设计决策
复用Video Master、MaterialRevision和CreativeExecution，无新业务表。旧合同30MiB保持，新视频合同单件512MiB/执行4GiB并有界流式处理；图像协议保留原兼容。接受与明确绑定分离，本地绑定不授予公开权利。已接受旧版本和失败稿历史不覆盖；相邻change不接管。

## 依赖与启动方式
沿用根README的API/Web、已安装aicontentstudio-creative MCP与本机达芬奇/AE。隔离验收8016/5186；正式运行入口8000/5173不作为本次发布验收声明。MCP适配scripts/creative_mcp_stdio.py沿原私有runtime读取凭据，15工具握手已验证。

## 历史过程（以下状态均为当时记录，当前结论以上述验收为准）

## Revision 3 确认项
网页素材只走人工生成，不再自动填写/提交/轮询/下载；平台保留精确回传和素材版本。Codex仍负责已回传素材的达芬奇/AE后期。旧任务/结果保留，样片未完成不归档。用户已确认，按同一计划完成页面/Skill收口及后续验收。

Codex操作入口：现有Creative Execution MCP（正式8000已列举15工具）负责执行域；准备/上传/用户已授权的接受及保存用命令行调用原REST，沿用权限/CAS。不以浏览器点击平台，不新增CLI工程。原设计依据：../../../../docs/AI_CONTENT_STUDIO_NORTH_STAR.md第15–16节。

## 已安装的Codex MCP
`aicontentstudio-creative`已注册并启用，stdio适配`apps/api/scripts/creative_mcp_stdio.py`连接正式loopback8000。已按Codex注册启动参数核验握手与15工具，不在配置存放令牌。若当前对话未热加载，在新会话加载该MCP；当前仍可通过同一CLI适配使用。

## 第三版验收记录（2026-10-15）

第三版入口、冻结复制内容、历史幂等和通用prepare防绕过已通过独立代码/Python/TypeScript复核；150项既有相关回归、Web构建/FE-P1和临时合同检查通过。完整相关组合此前244通过、1项HEAD已有迁移号断言失败，未把它记为全绿。重启仅隔离8016，新HTTP确认3条历史任务保留、逐条冻结说明可读、新自动网页执行422且不创建任务。

真实API图片：Grok任务c20ca5b40cc949de84780987391f33fb、Gemini任务6ee48ed9b4ca4085a43b671869b792e7均生成并接受，素材版本19/20；1024×1024 JPEG已视觉检查。实际预算2/2；仅本地评审，外部使用权未核验。

代码仍在上述隔离分支，正式平台代码尚未整体集成。MCP适配已放入主仓库并注册到Codex，连接现有正式8000；未把隔离样片数据冒充正式数据。未archive/commit/push。

## 历史文生视频交接（第四版不再作为当前生成指令）

以下保存旧任务依据；先图后提示词流程生效后，不再按下面文生视频提示词发起新生成。已有结果可保留取回用于历史对账，不算本版图生视频证据。把两个原始MP4直接交回本对话，或告知本机绝对文件路径，并注明Grok/Gemini。Codex负责精确关联任务、校验、达芬奇主剪和AE合成。不要提前修改本次冻结主稿39。

Grok先前已有结果：[打开原生成记录](https://grok.com/imagine/post/2d09c50f-e394-4a5f-8b3e-d94d08529d5b?conversation=66d9f1c8-1610-4a11-ae8b-7291a6699dd8)。Gemini请查看账号内先前以“Generate an 8-second 16:9 cinematic…”开头的记录；这里只确认提交过，未确认结果。

以下仅为主稿39冻结的历史提示词，不是当前应提交的网站指令。

### 1. Grok｜光进入画面

16:9；生成6秒；成片使用6秒；无参考图；剪辑时静音。本次样片无旁白，字幕另行制作。任务1（保留历史执行）；镜头`a4ee76d9-6a1b-487b-8471-13091b0ddc8c`。

```text
Create a 6-second cinematic 16:9 shot. Warm sunrise light travels slowly across a minimalist walnut desk, a blank ivory notebook and a single amber glass prism. Gentle dust motes, calm teal shadows, subtle camera push-in, photorealistic material detail. No people, no logos, no text, no cuts. This is an original fictional scene. Silent visual footage.
```

### 2. Gemini｜想法开始流动

16:9；生成8秒；成片使用8秒；无参考图；剪辑时静音。本次样片无旁白，字幕另行制作。任务3（人工执行）；镜头`9d4e2fab-931c-4176-8219-a0591ee7679f`。

```text
Generate an 8-second 16:9 cinematic video, one uninterrupted slow lateral camera move. An original fictional minimalist creative studio: warm sunbeam refracted by an amber glass prism onto blank ivory cards on a walnut desk, deep teal background, delicate floating dust. Calm tactile photorealism, coherent geometry, no people, no brands, no letters, no text. Visual-only B-roll; no speech.
```

收到原片后继续：文件/时长/画幅校验 → 接受素材 → 明确绑定并保存主稿 → 导演包 → AE局部合成 → 达芬奇粗剪 → 时间码反馈修改 → 成片/字幕/工程重开与质量评审 → 全项通过后归档并选择性本地提交。

## Revision 4 当前流程与下一步

1. 从分镜目的出发制作图片，或选用已有图片。
2. 预览并明确选定本镜头的图片，保存具体版本；样片先确定16:9构图。
3. 查看这张图后编写视频提示词：哪些元素保持、哪些元素运动、镜头如何移动、节奏与时长。先前的生图描述与视频提示词分开。
4. 确认图片＋对应视频提示词，再交给用户下载图片、复制提示词与参数，人工到Grok/Gemini做图生视频。
5. 原片回传后CLI/MCP接收，达芬奇主剪、AE按需，按原质量/工程验收收口。

本轮已核看两张旧API图片：Grok为排列卡片与金字塔状棱镜，Gemini为叠放卡片与柱状棱镜；均1024×1024，适合作为风格候选，未选定为同一连续场景的关键帧，且素材19/20尚无模型外发授权。具体新提示词等选定图片后再写。本版已追加2次横屏图片请求，累计4/4次；用户已选B两段共用。现有图片与已生成网页结果均保留。

具体方案见proposal.md、design.md及task_plan.md。本版代码已在隔离分支实施并通过独立SPEC/Python/TypeScript复核；没有归档、提交或push。

## 当前可执行交接：用户已选B，两段共用

用户已明确选择B。选定图片是新Gemini真实JPEG，1376×768，素材版本21；已先明确选图保存Master40，再查看实际图片后编写并保存视频提示词Master41。两任务冻结同一图片/hash，没有网站生成派发。Grok候选A保留在原生成任务中，未被替用户采用。

下载本机图片：[B共同参考图](/Users/mshengran/Project/AIContentStudio/backups/web-video-handoff-20261015/acceptance/revision4/gemini-keyframe.jpg)。保留原始尺寸与字节，没有隐式裁切。上传该图到网站后选择图生视频与16:9；有声音开关时关闭，否则剪辑时静音。字幕后期制作。

### Grok｜任务4｜6秒

图生视频；同一B图；16:9；分辨率选网页可用720p或更高；原片后期静音。

```text
Use the uploaded image as the exact starting-frame reference. Preserve the horizontal amber-glass triangular prism on the right, the blank ivory notebook and three paper cards on the left, the walnut desk, the deep teal wall and the warm upper-left sunlight. Keep all objects stationary and preserve their shapes, scale and arrangement. Create one continuous 6-second 16:9 cinematic shot. Make an extremely slow, smooth camera push-in of about 3 percent. Let the warm highlight on the prism brighten very gently, with coherent reflections and stable glass edges. Restrained, calm, photorealistic. No cuts, no new objects, no hands or people, no text or logos. Do not deform, duplicate, move or rotate the prism or the cards. No speech or music.
```

### Gemini｜任务5｜8秒

图生视频；同一B图；16:9；分辨率选网页可用720p或更高；原片后期静音。

```text
Use the uploaded image as the exact starting-frame reference. Preserve the horizontal amber-glass triangular prism on the right, the blank ivory notebook and three paper cards on the left, the walnut desk, the deep teal wall and the warm upper-left sunlight. Keep all objects stationary and preserve their shapes, scale and arrangement. Create one continuous 8-second 16:9 cinematic shot. Make a very slow, short camera slide to the right with subtle natural parallax; do not orbit around the prism. Maintain the original lighting direction and let the refracted amber caustic shift only slightly and plausibly on the wood. Keep the prism geometry and paper edges stable throughout. Restrained, tactile, photorealistic. No cuts, no zoom jumps, no new objects, no hands or people, no text or logos, no speech or music.
```

生成完成后下载原始MP4，分别注明Grok/Gemini回传，或提供本机文件绝对路径；不要预先转码/加字幕。若网页时长选项不同，记录实际值后交回校验。现有工程/样片仍在隔离8016/5186，正式平台尚未整体集成；creative MCP正式安装保持8000，隔离任务已用同一MCP协议CLI回读4/5成功。

## 第四版验证与范围

执行/Video既有168通过、图片/路由既有83通过；撤权修复后相关150再次通过；4项临时合同检查、临时Node状态与Web/TypeScript/Vite/FE-P1、Ruff/diff通过。无持久测试新增。独立SPEC发现下载授权检查不足，修复为项目/单元范围实时校验及每次下载重新请求；TypeScript发现A→B→A会恢复旧提示词确认，修复后复核通过。Python独立复核通过。已知HEAD旧schema断言失败与真实样片门槛仍单列，不声称全工作区全绿或已完成归档。


## 真实样片与本地绑定补充（2026-10-15）

真实Grok/Gemini已回传、校验并接受，72秒粗剪/反馈/修改/最终导出及AE合成完成；执行6与7各6项成果均accepted。原生AE/达芬奇工程已重开，达芬奇重开后再次完整导出。委托AI媒体质量通过，原片与工程依赖保存在用户媒体目录edit/aics-web-video-20261015；详细证据见progress/findings/review。用户已确认受限成片仅本地绑定的规范补充，正在完成后端保存、前端选择和私有预览的最小一致性修复；Candidate/公开交付门禁继续保留，权利标记不升级。尚未归档/提交。


## 配音纠正与当前阶段（2026-10-15）

用户指出当前样片无配音；实际Master voice为none、ResolveExportAudio=false，文件确实无音轨。此选择由执行方将网页素材静音误延续至整片，不代表用户要求无旁白。当前72秒文件只作为无声粗/成片历史证据保留，不能作为用户最终有声交付。归档和提交暂不执行；已建议使用当前科技角色已有音色补旁白，等待本次音色方向确认后重做音画/字幕对齐与有声评审。

本地绑定补充已真实HTTP验证：Master44绑定final素材33成功，rights仍public=false/model=true；私有会话200、Range206；Candidate409 readiness_blocked/asset_unready，公开门禁未放宽。独立代码复核继续，不把本地绑定等同公开交付。


## 2026-10-15 已确认补旁白

用户确认按当前科技角色音色与现有文案补旁白，并重新剪辑/对齐字幕。只读核对隔离identity snapshot13：lengdan_xiongzhang、speech-2.8-hd、minimax.speech、rate1。平台TTS任务355a4f33b1a046c29cb84bcf2ad2aee2已准备，单次执行进行中；不重新生成网页视频或图片。以实际声音为时序依据，时长保留60–90秒样片范围；无声accepted历史保留，有声成果另建执行。


归档后干净候选OpenSpec全量strict：45 passed / 0 failed。
