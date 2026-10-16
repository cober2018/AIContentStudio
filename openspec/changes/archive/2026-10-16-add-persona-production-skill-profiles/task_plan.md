# Persona Production Skill Profiles Implementation Plan

> For agentic workers: 用户确认提案后使用 superpowers:executing-plans；沿用本目录和 tasks.md，不新建计划。无需用户选执行模式。2026-10-16用户已确认，进入apply。

**Goal:** 在现有平台/本机Agent/AE/Resolve分工下，以科技角色验证可提炼、可选择、可评审的阶段Skills与场景配乐。

**Architecture:** Persona保存作品标准与方法引用；Recipe/执行包冻结有效配置；Codex使用精确方法执行并回传。复用既有素材库和方法库，不复制第三方工作台。

**Tech Stack:** 既有FastAPI/SQLAlchemy、React、OpenSpec、Creative MCP/CLI、AE/Resolve MCP；外部子Skill作为有来源的任务方法。

## 实施顺序和文件责任

任务勾选以 [tasks.md](tasks.md) 为唯一状态；下面是各组的执行与验证说明，不另计完成数。

| 对应任务 | 主要落点 | 完成证据 |
|---|---|---|
| 1.1–1.3 | 既有Capability Memory/Installed Agent Skill库存；`.codex/skills/video-production-handoff/`及按必要新增的引用资源 | 确切上游/许可/适配记录、AE/Resolve实际操作回读；不得先装全套 |
| 2.1–2.4 | `apps/api/app/services/capability_memory.py`、`creative_configuration.py`、`apps/web/src/product/IdentityWorkspace.tsx` | 三模态观察与角色资产实际保存/回读；用户风格采纳和暂定项分列 |
| 3.1–3.3 | `creative_configuration.py`、`stage_resolver.py`、现有执行包服务/`creative_mcp.py`，`IdentityWorkspace.tsx`、`VideoStudioShell.tsx` | 配置→预览→冻结→实际载入一致；历史版本不漂移；关闭方法不出现于本次指令 |
| 4.1–4.4 | `.codex/skills/video-production-handoff/SKILL.md`、其按需引用资源、既有视频Director/Stage合同 | 词级时轴与编辑映射、三类AE实际小样、Resolve回读与可重开工程 |
| 5.1–5.3 | `apps/web/src/pages/Materials.tsx`、`VideoStudioShell.tsx`、现有Material元数据服务 | 改标签后检索变化、逐曲来源、无BGM路径、真实混音成片 |
| 6.1–6.5 | 本目录review/progress/findings、受影响模块README、相关canonical specs | 对照样本、新主题完整片、验收/回退/归档回执与选择性提交 |

路径为当前仓库已有责任边界；进入目录先读对应README，再核对具体服务入口，优先图工具（当前会话无可用graph工具，必要时窄范围搜索）。不预先指定新增表/通用调度器，确需加法迁移时记录理由和旧数据保全方案。

## 按组执行

1. **选型**：核对安装库存，避免重复安装；选择被许可且有必要的子文件；记录依赖与适配差异；用现有MCP做最小操作验证。talkcraft/dbskill/无许可营造不进入商业试验依赖。没有可用能力时缩小对应镜头，不暗换整套工具。
2. **提炼**：文字/图像先复用已有认可作品，视频使用用户给定原片；保存观察、推断、未知与证据；以可读风格卡呈现并通过既有资产修订服务保存。视频样本不能自动推断全文风格；未经用户采纳不提升默认。
3. **接线**：先记录当前profile与有效解析，再以最小字段扩展旧结构。逐项检查继承、显式覆盖、全关、disabled保留、精确revision；前端使用同一有效解析接口。执行包包含方法清单，Agent回报真实使用；不要靠改全局Skill文件模拟开关。
4. **视频**：先修正配音并核对真实时间，再定最终镜头；真实视频原件只读，编辑映射独立。以三类实际AE镜头验证移植；Resolve负责声音、节奏、校色与终混，包装回片核对时长/帧率/色彩。检查源文件、原生工程与最终MP4。
5. **配乐**：先让现有素材能表达场景与来源，再整理少量曲目，最后做实际选曲/无BGM与混音比较；未知节奏留空，音量以人声清晰和当前作品为准，不建立统一强制数值。
6. **验收**：先用同主题单变量对照选方法，再用新主题整片验证风格可迁移；检查页面入口与执行读回。测试代码遵守用户约束：本方案不新增测试文件；运行受影响的既有测试及临时行为检查，保留实际输出。

## 检查命令与预期

2026-10-16补充来源，保持原22项：1.1–1.3加入yumehiko、odaiouattara、ChaiWithJai；4.2参考语义剪辑/精确时间线装配；4.3参考AE场景组合与局部修改；4.4/5.3参考声音、配乐、校色及分层交付。优先复用现有AE工具库的保存/重放接口。原Skill依赖的Remotion/HyperFrames与GUI步骤须逐项映射、实测，不把读过文档视为实现通过；详见research.md。此补充已包含在用户确认范围。

- `openspec validate add-persona-production-skill-profiles --strict`：本change规范通过。
- 后端先读`apps/api/README.md`，按其环境运行受影响的既有persona/recipe/capability/material测试；预期通过，无假造provider成功或正式库写入。
- 前端先读`apps/web/README.md`及package scripts，按其既有构建/类型检查命令运行；预期通过。测试命令与真实输出写入progress，不复制过去日志充当本次结果。
- 临时验证重点：角色隔离、旧profile兼容、开关真实生效、项目覆盖不反写、标签修订、音频修改后全链对齐、工程可重开、最终MP4实际内容。

## 确认与发布边界

用户已确认；沿用本计划。

/// 核对现有能力与隔离基线
/// 接通角色配置、阶段开关与冻结执行包
/// 适配并验证AE/Resolve组合操作
/// 新主题作品与质量评审，真实完成后归档提交
第一轮仅科技角色；用户的参考标准与小样采纳仍是具体作品决策。发布生产配置与默认方法时保留旧revision可回退；归档须实际任务完成，未试听不得宣称试听完成、未采纳不得宣称风格采纳。2026-10-16用户已采纳完整样片并授权正式接入及归档；质量结论沿用委托AI评审，保留未直接试听和估计对齐边界。无push、公开发布或对外托管授权。
