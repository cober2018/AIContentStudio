# 角色风格与阶段Skills：实施入口

## PRD / 需求背景

把角色定位、参考作品与分阶段专业方法沉淀为自己的资产。先科技角色，复用第三方有用的子Skills；平台管配置/素材/执行回执，Codex通过已有MCP使用达芬奇与AE。场景音乐可选且标签可改。

## 当前阶段与代码版本

2026-10-16：**正式接入、验收及归档完成，22/22**。实施工作区 `/Users/mshengran/.codex/worktrees/persona-production-skills/AIContentStudio`，分支 `codex/persona-production-skill-profiles`，基线 `49e4fdc`，本机main已完成本需求选择性提交（以Git HEAD为准）。本机原工作区已接入owner增量；初始156个相邻变更文件已复制为隔离基线，原件与SHA256清单保存在 `/tmp/aics-persona-production-baseline-20261016/manifest.json`。后续提交按该清单区分本需求修改。

## 目录结构

- [research.md](research.md)：全部候选、固定源码版本、许可、实际方法与接入结论。
- [proposal.md](proposal.md)、[design.md](design.md)、`specs/`：范围、设计/流程图与五个capability规范。
- [tasks.md](tasks.md)、[task_plan.md](task_plan.md)：22项待实施任务与同一份持续计划。
- [progress.md](progress.md)、[findings.md](findings.md)、[review.md](review.md)：真实进度、关键发现和方案复核。

## 已完成

- 核对23个相关仓库的固定快照、README/许可及重点Skill文件，另核对Remotion官方文档；新增AE场景装配与Resolve专业后期的组合操作候选，归入原22项。
- 明确Hypit参考分析价值及限制、talkcraft/dbskill商业使用限制、AE/Resolve适配边界。
- 形成科技优先、三模态风格提炼、阶段开关、场景BGM与新主题验收方案。
- 本change strict校验通过，独立计划复核Approved；这不是实现或作品验收。
- 阶段开关/多方法、风格资产显式应用、音乐标签修订已实现并通过独立代码复核；正式科技Persona2 v4已启用，保留旧版本与生活角色。
- 新主题47秒完整片、配音/字幕/配乐、AE包装和Resolve终混已完成；原生工程实际重开0缺失，正式正常API回收并接受8个产物，Master39已本地绑定。独立AI画面/文案及音轨技术检查通过，未直接试听、对齐仍为估计。

## 待完成 / TODO

22项已完成；当前首版已可使用。生活角色、数字人素材生成、完整产品宣传模板作为后续事项，本期不实施。

## 关键设计决策

复用现有Persona/Style Preset/Capability Memory/Recipe/执行包；共享方法与角色参数分开。关闭Skill应真实改变本次任务指令；技术合同不随之关闭。参考提炼形成可编辑规则，不训练模型或承诺完美复刻。Resolve主剪/终混，AE按需包装；专业方法不通过改工具名直接移植。

## 依赖与启动方式

优先复用现有依赖。只校验规范使用已安装OpenSpec CLI。实施沿用根README及apps/api、apps/web的启动方式，现有平台CLI/MCP与AE/Resolve MCP；第三方运行时是否必要须经选型验证，不能默认安装。

## 日常使用入口

| 操作 | 正常页面入口 |
|---|---|
| 调整科技角色默认 | `http://127.0.0.1:5173/identities` → AI科技研发技术博主 → 创作配置；各模态显示适用阶段，方法可多选、排序、改参数或关闭 |
| 修改角色风格 | 同一角色创作配置下的“参考风格草案”；保存、明确采纳后再应用到角色，形成新身份修订 |
| 仅调整当前作品 | 项目 → 内容单元 → 创作交接 →“阶段方法：继承与本次覆盖”；覆盖只冻结到本次执行包 |
| 选配乐、改标签 | `http://127.0.0.1:5173/materials`；按场景搜索音乐、修订元数据；视频Director可选择背景音乐或“无” |
| 执行与回收 | 页面准备任务，Codex通过CLI/MCP领取并加载启用方法；Resolve主剪、AE按需包装，回传成片/工程/字幕，再接受结果并绑定本地主稿 |

已有账号/栏目继续使用原whole-profile继承规则；显式覆盖不会被本次角色默认反写。阶段开关不改变模型能力。新作品仍需有效事实/素材权限；公开使用由现有Candidate/发布门禁另行检查。

## 下一步

用户已采纳完整样片，科技角色v4已正式启用；Project7/Unit13/Master39可查看样片与工程。32项正式API回读、纯候选521项既有检查及Web构建通过，五个主规范已同步（12条新增要求），已归档；归档后strict49/49通过；已选择性本地提交，本机默认可直接使用；未push。不得重开原已归档网页视频change或覆盖相邻修改。
