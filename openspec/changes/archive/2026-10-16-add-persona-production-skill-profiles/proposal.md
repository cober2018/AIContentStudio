## Why

现有平台已经能按 Persona、Recipe 和冻结执行包组织创作，并通过本机 Agent 交接专业工具，但尚未把用户参考作品提炼成可确认的角色风格，也缺少贯穿制作各阶段的外部 Skill 组合、独立开关和选型验证。先以科技角色验证这一层，把已有专业方法转化成可用作品，避免仅因工具可调用就宣称创作质量合格。

## What Changes

- 从文字、图片、视频分别提炼带原文/画面/时间码证据的风格草案，确认后保存为角色资产；区分内容事实、作者身份与可迁移表达方式。
- 复用现有 Persona 创作配置、Style Preset、Capability Memory、Recipe 与 CreativeExecutionPackage；展示十个制作阶段，每阶段可选择多个确切版本的 Skill、调整顺序、逐项开关或全部关闭。
- 分离共享方法、角色风格与工具执行适配。首批候选从现有开源项目挑选，不整体引入所有插件；来源、许可证、改动和实际验证情况明确可查。
- 视频沿用图先确认、网页人工生视频、原片回传；配音完成并修正后冻结词级时间轴；达芬奇负责声音、节奏、调色与主剪，AE 按需完成后期包装，回到达芬奇终混与导出。
- 在现有素材库增加场景导向的可编辑音乐标签和可选选曲/混音交接，允许整片或某场景无 BGM。首批只纳入逐曲来源可核对的少量常用配乐。
- 用同一输入对比关闭 Skills、单项 Skills、组合 Skills 的效果；通过科技角色新主题作品验收后才固化默认组合。生活角色、数字人生成和完整产品广告模板仅记录后续事项。

## Capabilities

### New Capabilities
- `persona-reference-style`: 多模态参考证据提炼、可编辑确认、角色风格版本与新主题验证。

### Modified Capabilities
- `persona-creative-configuration`: 阶段多 Skill 顺序/独立开关、继承与执行快照。
- `studio-creative-skill-pack`: 外部子 Skill 来源与适配记录、依赖核实、任务级启用交接。
- `web-video-production-handoff`: 音频驱动时间线、专业步骤分工、配乐/剪辑/AE包装回传与质量核验。
- `material-library-v1`: 可编辑的场景音乐标签、逐曲来源与选用记录。

## Impact

预期最小影响：既有 IdentityWorkspace、VideoStudioShell、Assets 页面；creative_configuration/stage_resolver、Capability Memory、CreativeExecutionPackage 与现有视频交接 Skill。准确字段和扩展位置在 apply 前依据当前工作树核对，避免覆盖相邻改动。

平台保存配置与结果，Codex 等本机 Agent 领取任务并使用现有 AE/Resolve MCP；平台不新增视频渲染引擎、通用 Agent 框架或第二套剪辑工作台。Hypit 只评估参考分析部分；Remotion/HyperFrames 保留研究用途，不作为本期成片必需依赖。第三方工具未在本轮安装或执行。原网页视频 change 保持归档，本提案独立等待用户确认。
