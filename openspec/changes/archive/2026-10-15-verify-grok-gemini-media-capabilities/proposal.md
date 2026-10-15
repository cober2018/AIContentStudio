## Why

用户已确认采用“平台编排、网页生成素材、达芬奇主剪、AE按需制作”。当前所用API通道继续承担图片生成；先确认分镜起始图片，再据图编写动作/运镜提示词，Grok/Gemini视频通过网页图生视频获得，再作为分镜素材进入既有外部执行与剪辑链。需要把页面入口、素材回传、剪辑交接和成片回收连起来，避免依赖当前不可用的视频API或散落聊天记录。

本文件为同一change的第四版：用户已确认“先制作并确认图片，再基于实际图片编写视频提示词”的流程方向。第三版人工网页、CLI/MCP操作平台与专业剪辑分工保持；本版具体规范已确认并进入实施，不新建change。

## What Changes

- 保留Grok已验证的API图片路径，修复Gemini图片的generateContent协议；按真实能力选择执行路径，网页视频不伪装为原生API生成。
- 在现有项目视频生产页的“视频主稿·导演工作台”中补齐分镜素材任务：已有素材、API图片、Grok/Gemini网页视频、AE动效四种来源；每个任务绑定稳定镜头ID、已保存主稿版本、提示词、画幅、目标使用时长、生成时长、参考图和声音意图。
- 分镜按“制作图片 → 确认用于本镜头的图片 → 据图编写视频提示词 → 人工图生视频 → 原片回传”顺序操作。生图描述用于主体/构图/色调；视频提示词在图片确定后编写，描述动作、运镜、节奏及须保持的画面元素。
- 图片可以来自已有素材、人工上传或现有API生成；确认绑定精确MaterialRevision/hash，不能把入库接受自动等同于镜头图片选定。换图后旧视频提示词须重新核对确认，历史包不改写。
- 从已确认图片和据图提示词准备人工网页任务：页面提供可下载图片、分镜文案、可复制视频提示词、画幅、生成时长和声音要求。用户自行粘贴到Grok/Gemini并下载原片，平台不自动打开/填写/提交/轮询/下载网页结果。回传仍走原始视频校验、候选预览、明确接受和镜头绑定；账号登录留在浏览器。
- Codex操作AIContentStudio只走既有Creative Execution MCP或命令行调用现有REST API，不通过浏览器点击；正常页面为用户使用保留。MCP以现有工具边界为准，不新增独立CLI框架或审批工具。
- 复用CreativeExecutionPackage/CreativeExecution/Output和本机MCP；图片API仍由ProviderGenerationTask负责。没有新增品牌任务库、通用调度器或网页私有API。
- 已接受素材集与完整脚本、旁白、字幕、剪辑要求组成导演包；Codex按项目Skill领取，达芬奇维护主时间线，AE按需输出局部合成，回到达芬奇。
- 普通页面接收粗剪、带时间码反馈、精剪/最终成片、字幕和可重新打开的工程；粗剪接受后的修改创建新执行，最终MP4接受与绑定主稿仍为明确操作。
- 解决现有30MiB单文件限制：仅对明确的新视频/工程传输合同提供有界大文件路径，保持旧合同和其他上传上限；不把MP4塞进MCP JSON或无上限读取内存。
- 通过一条正常页面到真实网页素材、AE合成、达芬奇粗剪/修改/导出/工程重开的完整样片验收，再按授权范围归档和本地提交。

## Capabilities

### New Capabilities
- `web-video-production-handoff`: 分镜素材任务、网页生成与回传、Codex专业剪辑交接、粗剪反馈和工程/成片回收；复用既有执行与素材模型。

### Modified Capabilities
- `model-capability-routing`: 注册CPA图片按明确协议执行，Gemini与Grok操作区分，旧V1兼容，确认拒绝与unknown分开。

## Impact

复用VideoStudioShell/VideoStudioModel、CreativeExecutionPanel、ProductionWorkspace、Video Master v2、creative_packages/executions/files/mcp、素材接受及原生图片能力路由。新增一个小型网页视频交接服务、一个分镜素材面板及一个项目Skill，具体职责见task_plan.md。

本机AE/达芬奇MCP可用由用户确认，按执行时使用，不另开配置排障工作。现有creative-orchestration实现和director.video.v1来自相邻未归档change，作为依赖记录，不接管其生命周期。目标不新增业务表/迁移或产品依赖；只有必要的版本化JSON合同与有界传输扩展。保持MiniMax、旧素材/任务和相邻工作；不新增Grok/Gemini视频API适配器、不升级网关、不引入官方直连或自动发布。


## 2026-10-15 已确认：受限成片本地绑定

用户明确确认：已接受且具有当前本地/model使用授权的最终MP4允许明确绑定为本地主稿并私有预览；不提升任何权利标记，Candidate/交付/发布继续检查public_use_allowed。同步调整现有后端保存、前端选择/绑定/预览，不新增权限类别、业务表或发布路径。
