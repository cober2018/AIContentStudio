# AI Content Studio 北斗星指南与产品规划

> 文档状态：已批准的产品方向与本轮实施基线
>
> 日期：2026-10-04
>
> 目的：统一未来 2–3 年的产品方向、能力边界与使用逻辑；以 `align-creative-orchestration-product` 为实施规格，按阶段兑现，不把规划冒充已完成功能。
>
> 当前正式运行环境：单机正式使用，SQLite + 本地素材库 + loopback-only API/Web。

> 2026-10-05实施状态：`align-creative-orchestration-product` 已完成147/147及隔离验收/三类独立复核，日常入口统一、旧操作按兼容目录保留。canonical归档、提交及正式schema启用仍待分别授权；这不代表未来专业工具自动化或生成质量已验证。证据见 `ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md`。

---

## 1. 一句话定位

**AI Content Studio 是内容与创作决策中枢：负责把想法、事实、品牌身份、创作意图、素材、渠道策略和人工决定组织成可执行、可追溯的创作任务；基础创作由产品直接完成，复杂高质量创作通过 MCP / Agent 交给专业工具执行，成果再回传并进入统一的版本、审阅、交付和学习闭环。**

它不是要成为第二个 Premiere、Photoshop、DaVinci Resolve 或专业 DAW。

它要成为这些工具和 AI Agent 之前的“内容大脑”和“创作真源”。

---

# 2. 北斗星

## 2.1 核心目标

AI Content Studio 的核心目标不是“自己完成所有创作动作”，而是：

1. **把内容做对**：观点、事实、表达、渠道版本和创作目的正确；
2. **把要求说清楚**：让人、Agent 和专业软件都能准确理解要做什么；
3. **把结果接回来**：无论由内部模型还是外部专业工具产生，成果都回到统一的项目、版本和血缘体系；
4. **把决定留下来**：保存为什么这样做，而不仅保存最后做出了什么；
5. **把历史保住**：新版本、新工具、新流程不能覆盖旧内容、旧审批和旧交付事实；
6. **保持简单可维护**：本机正式使用优先，不为了“架构完整”引入不需要的基础设施。

---

## 2.2 北斗星原则一：按任务复杂度分层，而不是按媒介切割

产品能力不应简单划成：

- 文字由我们做；
- 图片交给外部；
- 音频交给外部；
- 视频交给外部。

更合理的划分是：

### A. 产品内直接完成的基础创作

只要满足以下条件，就优先由 AI Content Studio 原生完成：

- 高频；
- 输入相对明确；
- 一次或少量交互即可得到可用结果；
- 不需要复杂专业操作界面；
- 大模型或轻量工具已经能够稳定完成；
- 自己维护的成本不高。

例如：

- 文案生成与改写；
- 标题、摘要、渠道适配；
- 基础图片生成；
- 封面图、B-roll 素材图；
- 图片 variation；
- 简单尺寸与比例适配；
- TTS；
- ASR；
- 旁白音频；
- 简单音效或音乐素材；
- 字幕生成与校对；
- 基础视频素材生成；
- 简单预览和组合。

### B. 交给专业工具的高级创作

当任务出现以下特征时，不继续扩展内部编辑器，而是通过 MCP / Agent 交给专业工具：

- 对画面、声音或时间线有高精度要求；
- 需要复杂图层、蒙版、关键帧、调色、特效；
- 需要专业混音、母带、降噪或复杂音频处理；
- 需要复杂剪辑、镜头级控制或成片级质量；
- 需要大量人工审美判断；
- 专业软件已有成熟能力；
- 内部实现会逐渐演变成另一个专业软件。

对应工具可以是：

- Photoshop；
- Illustrator；
- Premiere Pro；
- After Effects；
- DaVinci Resolve；
- 专业 DAW；
- FFmpeg 或其他媒体处理工具；
- 未来更强的 Agent-native 专业创作软件。

### C. 同一媒介允许同时存在两条路径

例如：

**图片**

- 普通封面：AI Content Studio 直接生成；
- 高级商业视觉：把 Brief、品牌、参考素材和验收要求交给外部 Agent + Photoshop。

**音频**

- 普通旁白：产品内 TTS；
- 广播级声音处理：交给专业音频工具。

**视频**

- 脚本、分镜、字幕、旁白、素材、封面、B-roll 需求：产品内完成；
- 复杂剪辑、调色、特效、声音混合：交给专业视频工具。

因此：

> **媒介不是能力边界，复杂度、质量要求和维护成本才是。**

---

# 3. 北斗星原则二：AI Content Studio 是“创作上下文压缩器”

AI Agent 最大的问题往往不是“不会做”，而是：

- 不知道为什么要做；
- 不知道品牌是谁；
- 不知道哪些事实可靠；
- 不知道哪些内容不能改；
- 不知道不同平台的表达差异；
- 不知道历史上做过什么；
- 不知道最终应该满足什么验收标准。

AI Content Studio 的核心价值之一，就是把分散的信息压缩成一个结构化、准确、可追溯的创作上下文。

一个外部执行者不应该重新阅读整个项目、几十条来源和历史版本后自行猜测。

AI Content Studio 应直接告诉它：

- 这次内容为什么值得做；
- 面向谁；
- 核心观点是什么；
- 使用哪个 Identity / Persona；
- 哪些事实可以使用；
- 哪些事实存在不确定性；
- 哪些内容必须保留；
- 哪些内容允许自由发挥；
- 需要使用哪些素材；
- 目标渠道是什么；
- 目标内容形态是什么；
- 风格、节奏、时长和质量要求是什么；
- 哪些决定已经过人工确认；
- 最终结果如何判断合格。

这层能力将成为 AI Content Studio 长期最重要的差异化资产。

---

# 4. 北斗星原则三：外部执行结果必须回写

外部 Agent 或专业软件完成任务之后，结果不能变成一个孤立文件。

所有外部执行结果都应该能够回到 AI Content Studio，并绑定到原来的业务上下文。

回传至少需要保留：

- 来源 Project；
- 来源 Content Master / Channel Variant / Director Package；
- 输入版本；
- 输出文件；
- 文件内容 hash；
- 使用的工具；
- 使用的 Agent；
- 使用的模型（适用时）；
- 使用的素材；
- 执行说明；
- 工程文件引用（如存在）；
- 执行开始和完成时间；
- 是否满足验收条件；
- 是否需要人工补充；
- 是否经过人工接受。

### 一个重要原则

**外部执行完成 ≠ 自动成为正式内容。**

外部结果首先进入：

> Candidate / Proposed Result

只有人工接受后，才进入正式素材、正式版本、正式成品或后续审批链。

---

# 5. 北斗星原则四：保存“创作意图”，不只保存结果

产品不能只保存：

- 最后一篇文章；
- 最后一张图片；
- 最后一个 MP4；
- 最后一段音频。

还应该保存：

- 为什么选择这个角度；
- 为什么某句话必须保留；
- 为什么某一段被删除；
- 为什么要这个镜头；
- 为什么这里需要 B-roll；
- 为什么换成这种构图；
- 为什么公众号版与 X 版表达不同；
- 为什么小红书版强调另一个切入点；
- 为什么最终选择这张图；
- 哪些部分属于事实约束；
- 哪些部分属于创作自由；
- 哪些决定已经被人工确认。

未来 Agent 的重写、重剪、重配图、重做渠道版本，都依赖这些信息。

**最终文件可能会被重新生成，但创作意图不应该丢失。**

---

# 6. 北斗星原则五：专业执行能力必须可替换

AI Content Studio 不应绑定：

- 某一个 Agent；
- 某一个 MCP Client；
- 某一个图片模型；
- 某一个音频模型；
- 某一个视频软件；
- 某一家云服务。

Codex、Claude、ChatGPT、未来 Agent，以及不同专业创作软件，都只是执行端。

AI Content Studio 长期拥有的是：

- 内容目标；
- Identity；
- Brief；
- 事实；
- 来源；
- 素材；
- 创作意图；
- Content Master；
- Channel Variant；
- Director Package；
- Candidate；
- 审批状态；
- 交付状态；
- 发布事实；
- 学习结果。

执行工具可以变化，业务真源不应随之变化。

---

# 7. 北斗星原则六：产品负责“定义与验收”，不必负责所有“亲自执行”

未来看到一个新的专业能力时，不再默认：

> “我们是不是也应该自己做一个？”

而先问：

1. 这是我们的业务真源吗？
2. 这是高频、简单、明确的基础能力吗？
3. 内部实现是否能够明显降低使用成本？
4. 还是说专业软件明显更适合？
5. 我们真正需要的是“执行能力”，还是“把要求定义清楚并验收结果”？

如果是后者，就走 Creative Execution。

---

# 8. 北斗星原则七：单机正式使用，简单可维护优先

AI Content Studio 当前正式运行环境就是：

```text
一台电脑
SQLite
本地素材库
loopback-only API / Web
```

这不是临时环境。

因此产品架构应优先：

- 简单；
- 稳定；
- 易启动；
- 易排查；
- 易备份；
- 易恢复；
- 少依赖；
- 少基础设施。

不因为“生产环境”三个字主动引入：

- PostgreSQL；
- MinIO；
- Kubernetes；
- Docker 集群；
- 多租户；
- SSO；
- 复杂 Secret Provider；
- 远端对象存储；
- 额外部署控制面。

除非未来真实需求改变。

---


# 8.1 北斗星原则八：系统必须“越用越好”，但成长必须经过筛选、验证和版本化

AI Content Studio 不应该只保存内容资产，还应该逐步沉淀“什么方法真的有效”。

这里的“学习”不是让系统在后台任意修改自己，也不是把每一次执行都永久保存成技能，而是建立一个受控的 **Capability Memory（能力记忆）**：

```text
一次任务
    ↓
尝试执行
    ↓
得到有效结果
    ↓
捕获为候选方法
    ↓
人工 / 规则验证
    ↓
保存为可复用 Tool / Skill / Recipe / Prompt
    ↓
后续相似任务优先复用
    ↓
继续观察使用结果
    ↓
升级 / 固定 / 归档 / 废弃
```

目标是：

> **用户使用得越久，系统越懂他的工作方式，也越少重复从零解决同一个问题。**

---

## 8.1.1 借鉴的现实模式：Tool Library

After Effects MCP 的 Tool Library 展示了一个很有价值的现实模式：

- 成功执行的脚本自动捕获为候选；
- 相同内容按 hash 去重；
- 候选不会直接成为长期能力；
- 用户可以将有价值的候选提升为保存工具；
- Prompt 可以保存为 skill；
- 工具存在 candidate / saved / pinned / archived / deprecated 等状态；
- 保存内容带 revision、content hash、来源和使用次数；
- 后续执行优先搜索和精确复用已有工具；
- 被验证有价值的能力可以导出、迁移和继续演进。

AI Content Studio 应吸收这种思想，但扩展到整个内容创作系统，而不是只用于脚本。

---

## 8.1.2 我们要沉淀的不是“所有历史”，而是高质量有效方法

系统每天可能产生大量：

- Prompt；
- 图片提示词；
- 改写指令；
- 分镜模板；
- Director Package 片段；
- 渠道适配规则；
- MCP 调用组合；
- Agent 操作步骤；
- 图片生成参数；
- TTS / ASR 工作方式；
- 外部专业软件执行 Recipe；
- 错误修复方案。

这些内容不能全部永久进入长期能力库。

必须区分：

### Execution History

记录“发生过什么”。

用于审计和追溯。

### Capability Candidate

记录：

> “这一次方法似乎值得以后再用。”

可以短期保留、自动过期。

### Saved Capability

经过明确接受后成为可发现、可复用能力。

### Pinned Capability

用户明确认为非常重要、长期保留的能力。

### Archived / Deprecated Capability

历史仍可追溯，但不再作为默认建议。

---

## 8.1.3 能力记忆的对象类型

建议未来至少支持：

### Prompt Skill

例如：

- “把技术研究改成公众号长文”的稳定 Prompt；
- “小红书封面高级科技感”的 Prompt；
- 某 Persona 的标题生成策略；
- 某种旁白语气。

### Tool

可以实际执行的确定性操作。

例如：

- FFmpeg 转码；
- 图片尺寸处理；
- JSX；
- 脚本；
- 本地媒体处理命令；
- MCP 工具组合。

### Recipe

多个 Tool / Skill 组成的工作步骤。

例如：

```text
Director Package
→ 生成 rough cut
→ 自动字幕
→ 添加 B-roll placeholder
→ 导出 review MP4
```

### Creative Pattern

经过使用证明有效的创作模式。

例如：

- 某账号常用开场结构；
- 某系列视频节奏；
- 某类文章的信息排序；
- 某种封面构图。

### Execution Template

针对专业软件或 Agent 的稳定执行模板。

---

## 8.1.4 用户习惯也属于能力记忆，但不能和事实混在一起

系统应该逐渐记住：

- 用户通常喜欢哪些表达；
- 哪些修改经常被用户接受；
- 哪类图片常被选择；
- 哪种旁白风格常被使用；
- 哪些渠道结构经常被保留；
- 用户更喜欢一次生成几个候选；
- 哪些专业工具更适合某类任务。

但必须明确区分：

```text
事实真源 ≠ 用户偏好 ≠ 创作模式 ≠ Tool / Skill
```

用户偏好不能修改客观事实。

创作偏好不能绕过 Evidence Boundary。

历史使用频率也不能自动等同“质量更好”。

---

## 8.1.5 自动捕获，人工晋升

推荐原则：

> **系统可以自动发现候选，但不能未经确认自动把候选升级为长期能力。**

例如：

一次 Codex + Photoshop 执行最终被用户接受。

系统可以提示：

> “这套执行方式是否保存为「高级产品封面精修」Recipe？”

用户确认后再保存。

同样，一段 Prompt 连续多次产出高质量结果，可以提示：

> “是否保存为该 Persona 的常用标题 Skill？”

这样既能成长，又避免能力库迅速被垃圾方法污染。

---

## 8.1.6 能力本身也必须有版本和血缘

每一个长期能力至少应该保存：

- capability_id
- kind
- name
- scope
- version
- content / definition
- content_hash
- source_execution
- source_project（如适用）
- source_agent / tool
- created_at
- created_by
- acceptance / promotion reason
- use_count
- last_used_at
- success / rejection evidence
- supersedes
- status

修改能力不覆盖旧版本。

---

## 8.1.7 Scope 必须明确

能力不一定全部全局共享。

建议至少支持：

```text
global
user
identity
persona
account
series
project
channel
tool
```

例如：

- “公众号长文排版”可以是 global/channel；
- “某 Persona 的开场方式”属于 persona；
- “这个项目专用的研究图表生成方法”属于 project；
- “Premiere 字幕清理 Recipe”属于 tool。

这样才能真正做到“记住用户的习惯”，而不是所有经验互相污染。

---

## 8.1.8 Checkpoint / Revert 是 Agent 敢于执行复杂任务的基础

专业执行必须支持“试错”。

After Effects MCP 中 checkpoint/revert 的价值不只是备份，而是：

> Agent 在做复杂、有副作用的操作前，可以先创建恢复点。

AI Content Studio 的 Creative Execution 应吸收同样原则：

```text
准备执行
→ 建立 checkpoint / baseline
→ Agent 执行
→ 读取结果
→ 验证
→ 接受
```

若结果不好：

```text
revert
→ 修改方案
→ 再执行
```

对于外部软件，checkpoint 的具体形式可以不同：

- 专业工程文件快照；
- 文件副本；
- Git revision；
- 软件自身 Undo / checkpoint；
- AI Content Studio 的 Execution baseline。

AI Content Studio 不必自己实现每个软件的回滚机制，但 Execution Contract 应要求执行端声明：

- 是否支持 checkpoint；
- checkpoint id；
- 是否支持 revert；
- revert 是否验证成功。

---

## 8.1.9 Recover 不等于盲目 Retry

复杂执行失败后不能直接重新跑一遍。

应区分：

```text
failed_before_dispatch
failed_after_dispatch
unknown
recoverable
```

若可能已经产生副作用：

> 必须先读取实际状态，再决定 recover / continue / revert。

这与当前 F7/F8 已建立的 Unknown / no-auto-retry 原则完全一致。

Future Creative Execution MCP 应提供：

- execution recovery id；
- last known checkpoint；
- failure stage；
- touched outputs；
- current state readback；
- resume / recover / revert 的明确动作。

---

## 8.1.10 成长闭环

最终希望形成：

```text
用户提出创作目标
      ↓
AI Content Studio 提供完整上下文
      ↓
系统搜索已有 Skill / Tool / Recipe
      ↓
能复用 → 优先复用
不能复用 → Agent 新解决
      ↓
得到结果
      ↓
人工接受 / 拒绝
      ↓
高质量新方法进入 Candidate
      ↓
用户选择是否保存
      ↓
未来任务再次复用
```

长期效果应该是：

> 同一个用户做第 100 次内容创作时，系统明显比第 1 次更了解他的工作方式。

但这种成长必须是：

**可解释、可查看、可编辑、可版本化、可回滚、可删除、可停止使用的。**

不能做成不可见的黑盒自我修改。

---

## 8.1.11 与现有 Learning 的关系

Capability Memory 和现有“效果与学习”不是同一个系统。

### Learning

回答：

> “什么内容策略可能有效？”

来源通常是发布和效果数据。

### Capability Memory

回答：

> “我们怎样更高效、更稳定地完成这种创作任务？”

来源通常是创作和执行过程。

二者可以互相引用，但不能混成一个状态表。

例如：

Learning 发现：

> 某 Persona 的视频开头采用问题句效果更好。

经过人工确认后，可以产生一个新的 Creative Pattern / Prompt Skill candidate。

但 Learning 本身不能直接修改 Skill。

---

## 8.1.12 北斗星追加结论

因此 AI Content Studio 还应该具备第五个长期特征：

> **它不仅管理内容，而且管理“如何把内容做好”的方法。**

随着使用：

- 好 Prompt 被保留；
- 好 Recipe 被复用；
- 好工具被固定；
- 好创作模式被积累；
- 无效能力被淘汰；
- 用户习惯逐渐进入适当 scope；
- 每次复杂执行都更容易恢复；
- Agent 不必不断重新发明已经解决过的问题。

最终形成：

> **一个会成长，但不会失控；会记住，但不会污染真源；会优化，但永远保留人工决定权的创作系统。**


# 9. 产品真正要拥有的核心能力

## 9.1 内容机会与想法

系统允许从以下任何入口开始：

- 已有想法；
- 已有资料；
- 内容机会；
- 已有项目；
- 已有历史内容；
- 外部输入。

不强制所有创作都先经过“机会分析”。

机会分析是有价值的辅助能力，不是强制前置步骤。

---

## 9.2 Identity

Identity 用于表达：

- 品牌；
- Persona；
- 账号；
- 栏目；
- 长期表达风格；
- 内容边界；
- 目标受众；
- 长期观点与限制。

它不是“登录账号切换”。

它是：

> **这次内容代表谁在说话。**

---

## 9.3 Brief

Brief 定义：

- 为什么做；
- 做给谁；
- 希望达成什么；
- 核心观点；
- CTA；
- 时效；
- 渠道；
- 风格；
- 成功标准；
- 明确禁止事项。

---

## 9.4 Sources / Facts / Evidence

系统负责：

- 保存来源；
- 提取事实；
- 人工确认事实；
- 保存引用；
- 冻结本次内容实际使用的证据边界；
- 避免后续内容与事实漂移。

用户界面可以简化，但底层证据契约必须继续保留。

---

## 9.5 Assets

Assets 包括：

- 图片；
- 视频；
- 音频；
- 文档；
- 外部创作成果；
- AI 生成结果；
- 用户上传文件。

所有素材继续保持：

- 版本；
- hash；
- 权利；
- 来源；
- 项目引用；
- 历史不覆盖。

---

## 9.6 Content Master

Content Master 是平台无关或相对平台中立的“内容主真源”。

它应该表达：

- 主体内容；
- 结构；
- 创作意图；
- 与事实和素材的关系；
- 当前版本；
- 当前确认状态。

---

## 9.7 Channel Variant

Channel Variant 负责：

> **同一内容针对不同平台重新表达。**

不是简单截断。

不同渠道版本可以独立：

- 编辑；
- 确认；
- 审核；
- 交付。

修改一个渠道版本，不自动改主稿，也不自动改其他渠道。

---

# 10. 图片能力规划

## 10.1 产品内保留并加强

产品内继续提供：

- 文生图；
- 图生图；
- variation；
- 封面生成；
- B-roll 图；
- 图卡生成；
- 简单构图建议；
- 画幅适配；
- 简单裁切；
- 选择候选；
- 素材版本；
- 项目引用；
- 权利与 hash。

## 10.2 不向专业图片软件扩张

不把以下能力做成核心竞争方向：

- 复杂图层；
- 专业蒙版；
- 高级修图；
- 精确合成；
- 复杂路径；
- 专业色彩处理；
- 设计系统级排版编辑器。

这些任务通过 Creative Execution 交给专业工具。

---

# 11. 音频能力规划

## 11.1 产品内保留并加强

- TTS；
- ASR；
- 旁白；
- 字幕；
- 基础音效；
- 简单音乐素材；
- 声音角色与提示词；
- 音频导入；
- 素材版本；
- 与脚本和场景绑定。

## 11.2 不向专业 DAW 扩张

不把以下能力作为核心：

- 多轨混音；
- 复杂效果链；
- 母带；
- 专业降噪；
- 精细 EQ；
- 自动化曲线；
- 高级音频工程。

需要时通过 Creative Execution 交给专业工具。

---

# 12. Video 方向调整

## 12.1 Video 不删除，但改变重点

Video 不再以“完整视频生产编辑器”为目标。

核心保留：

- 视频想法；
- Hook；
- 口播稿；
- Script；
- Scene；
- Shot；
- Storyboard；
- B-roll 需求；
- 素材引用；
- Voice；
- Subtitle；
- Overlay；
- Cover；
- Aspect Ratio；
- 目标时长；
- 节奏；
- CTA；
- 平台要求；
- 创作意图；
- 审批；
- 成果回传。

## 12.2 不继续深挖

未来不重点投入：

- 完整 NLE；
- 高级 timeline 编辑；
- 复杂 trim；
- 关键帧；
- 转场设计器；
- 调色；
- 特效系统；
- 专业混音；
- 完整渲染管线；
- 与 Premiere / Resolve 正面竞争。

## 12.3 新方向

Video 的主流程逐渐演进为：

```text
Idea / Brief
    ↓
Script
    ↓
Director Package
    ↓
基础素材生成
    ↓
Creative Execution（可选）
    ↓
外部专业执行
    ↓
成果回传
    ↓
Review / Approval
```

已有 F6D 的历史数据、Candidate、package 和 Review 不删除、不重写。

---

# 13. Director Package

Director Package 是视频和复杂多媒体创作的核心中间对象。

它不是工程文件。

它表达的是：

> **导演希望专业执行端完成什么。**

建议结构包括：

## 13.1 基础上下文

- project_id
- content_master_revision
- channel_variant_revision（如适用）
- Identity
- Brief
- target audience
- target channel
- target format
- target duration
- aspect ratio

## 13.2 创作目标

- core message
- emotional tone
- narrative objective
- CTA
- must_keep
- must_avoid
- creative_freedom

## 13.3 场景

每个 Scene 包括：

- scene id
- purpose
- script
- voice
- shot intent
- B-roll requirement
- selected assets
- subtitle emphasis
- overlay text
- pacing
- transition intention
- quality notes

## 13.4 素材

- 精确 MaterialRevision
- hash
- role
- rights
- placement intent
- optional / required

## 13.5 验收标准

例如：

- 60 秒以内；
- 9:16；
- 必须出现某个产品镜头；
- 必须保留某句；
- 不能改变某事实；
- 字幕必须完整；
- 不使用某类视觉风格；
- 人声必须清楚；
- 输出 MP4 + 工程文件引用。

---

# 14. Creative Execution Package

Director Package 可以看作 Creative Execution Package 在视频场景中的专业化表达。

统一 Creative Execution Package 应支持：

- image；
- audio；
- video；
- document；
- future creative media。

它只描述：

- 要做什么；
- 使用什么上下文；
- 使用什么素材；
- 哪些内容不能改变；
- 允许怎样创作；
- 输出什么；
- 如何验收。

**它不描述某个软件具体怎么点按钮。**

---

# 15. Creative Execution MCP

## 15.1 定位

MCP 是 AI Content Studio 暴露给外部 Agent 的一个标准接口。

它不是 AI Content Studio 本身。

系统仍保留自己的：

- API；
- 数据库；
- UI；
- 业务模型。

MCP 是额外的 Agent 接口。

---

## 15.2 第一批 Resource

建议第一批只读能力：

- get_project
- get_identity
- get_brief
- get_approved_facts
- get_sources
- get_materials
- get_content_master
- get_channel_variant
- get_director_package
- get_creative_execution_package
- get_acceptance_criteria

---

## 15.3 第一批 Tool

建议第一批写能力：

- start_external_execution
- report_execution_progress
- report_execution_blocker
- submit_execution_output
- attach_external_asset
- submit_project_file_reference
- request_human_review

后续再增加：

- accept_external_result
- create_variant_from_result
- retry_execution
- supersede_execution

---

## 15.4 安全原则

MCP 写操作必须遵守：

- 明确 Project scope；
- 明确 execution package；
- 明确输入 hash；
- 明确幂等 key；
- 不能绕过项目权限；
- 不能直接覆盖 MaterialRevision；
- 不能直接覆盖正式 Master；
- 不能自动批准 Candidate；
- 不能把“执行完成”自动转换成“已发布”。

---

# 16. 外部执行的完整生命周期

```text
AI Content Studio
    ↓
CreativeExecutionPackage
    ↓
MCP
    ↓
Codex / Claude / Other Agent
    ↓
Premiere / Resolve / Photoshop / DAW / etc.
    ↓
外部成果
    ↓
MCP 回传
    ↓
Execution Result
    ↓
MaterialRevision / Project Artifact
    ↓
人工验收
    ↓
正式版本 / Candidate
```

状态建议：

```text
draft
prepared
dispatched
in_progress
blocked
result_ready
accepted
rejected
superseded
unknown
```

外部执行出现不确定结果时：

**Unknown 不自动重发。**

继续沿用 F7/F8 已建立的安全原则。

---

# 17. 外部成果回写协议

回写成果分三类：

## 17.1 Binary Asset

例如：

- PNG；
- PSD 导出图；
- WAV；
- MP3；
- MP4；
- MOV。

进入 MaterialRevision。

## 17.2 Project File Reference

例如：

- Premiere project；
- Resolve project；
- Photoshop document；
- AE project。

第一阶段可以只保存：

- 文件路径；
- hash；
- 工具；
- 工具版本；
- 是否可重新打开；
- 是否属于本机。

不强制解析专业工程文件内部结构。

## 17.3 Execution Metadata

包括：

- agent
- tool
- tool_version
- model
- execution instructions
- source package hash
- output hash
- notes
- blockers
- acceptance report

---

# 18. 完整日常使用流程

未来产品不应该要求用户理解 F6/F7/F8。

用户只需要理解日常工作。

## 18.1 起点 A：我已经有想法

```text
新建内容
→ 写一句想法
→ 选择 Identity
→ 建立 Project
→ 补 Brief
→ 搜集资料
→ 创作
```

## 18.2 起点 B：我已经有资料

```text
上传 / 粘贴 / 网页
→ 创建 Project
→ 提取事实
→ 确认本次使用的信息
→ 创作
```

## 18.3 起点 C：我看到一个内容机会

```text
Opportunity
→ 人工决定采用
→ 转成 Project
→ 创作
```

## 18.4 起点 D：我继续已有项目

```text
Home
→ 待我处理
→ Project
→ 继续上一次工作
```

---

# 19. Project 内部工作流

一个 Project 内建议统一成：

```text
总览
创作任务书
资料与事实
素材
内容
渠道版本
执行
审阅与交付
版本历史
活动
```

用户不必在 Sources、FactPack、Materials、Workspace、ReviewPublish 等不同技术模块之间跳转。

---

# 20. 内容创作工作流

## 20.1 Content Master

主稿先完成“说什么”。

对于文字：

- 大纲；
- 正文；
- 事实；
- 结构；
- 创作意图。

对于图文：

- 文字主体；
- 图卡计划；
- 图片需求；
- 已选图片。

对于视频：

- 脚本；
- Director Package；
- 素材；
- 声音；
- 字幕；
- 场景。

---

## 20.2 Channel Variant

然后决定：

> **在每个平台怎么说。**

例如：

同一篇内容：

- 公众号长文；
- X thread；
- X single；
- 小红书图文；
- 抖音口播脚本。

每个版本：

- 独立保存；
- 独立编辑；
- 独立检查；
- 独立审批；
- 独立交付。

---

# 21. 审阅与交付

用户界面不要要求用户学习：

- Freeze Candidate；
- Approval；
- Delivery Authorization。

日常语言可以是：

```text
准备定稿
→ 查看最终内容
→ 查看问题与证据
→ 确认这版内容
→ 选择交付方式
```

底层仍保留：

- Candidate；
- exact hash；
- Approval；
- Authorization；
- DeliveryTarget；
- Attempt；
- Receipt。

---

# 22. “交付”与“发布”必须继续分开

### 交付

可能是：

- 下载 ZIP；
- 复制内容；
- 进入平台草稿箱；
- 交给 Agent；
- 交给专业软件。

### 发布

只有真实平台发布事实成立后才叫发布。

本地 ZIP 不等于发布。

草稿箱不等于公开发布。

执行完成不等于发布。

---

# 23. Learning

只有真实发布确认后，才进入真正的效果学习。

Learning 应该回答：

- 什么表达有效；
- 哪个渠道有效；
- 哪个 Persona 有效；
- 哪类结构有效；
- 哪些结论只是单样本；
- 哪些经验已经被人工确认。

Learning 不能自动改写 Identity。

它只能提出候选。

---

# 24. 未来主导航建议

最终主导航建议继续保持较少一级入口：

1. 今日工作台
2. 内容机会
3. 内容项目
4. 创作与执行
5. 审阅与交付
6. 内容身份
7. 素材与知识
8. 效果与学习
9. 设置

---

# 25. 各主页面职责

## 今日工作台

回答：

- 今天要处理什么？
- 哪个项目被阻塞？
- 哪个内容待审？
- 哪个 Agent 返回结果？
- 哪个外部执行出现 blocker？
- 哪个发布需要确认？

---

## 内容项目

项目是日常工作的核心容器。

所有内容、素材、渠道版本和 execution 都围绕 Project 组织。

---

## 创作与执行

未来替代现在比较技术化的 Production Workspace。

日常优先显示：

- 当前内容；
- 当前素材；
- 当前渠道版本；
- 当前执行任务；
- 下一步。

Workflow graph、Node Inspector 等能力放到：

> 高级 / 自动化

而不是默认主角。

---

## 素材与知识

全局长期库。

负责：

- 来源；
- 事实；
- 素材；
- AI 生成结果；
- 外部成果；
- 搜索；
- 复用。

项目内负责：

> **这次具体用了什么。**

---

## 设置

只放低频配置：

- 模型；
- Provider；
- 路由；
- 数据源；
- 渠道；
- 默认工作流；
- 高级本机运行配置。

创作过程中不应该频繁进入设置页。

---

# 26. 旧页面处理原则

当前旧页面不能立刻删除。

原因很简单：

> 有些新页面仍没有接住旧功能。

正确顺序：

```text
盘点旧操作
    ↓
新页面承接
    ↓
验证历史数据
    ↓
验证日常 E2E
    ↓
从主导航退出
    ↓
保留兼容路由
    ↓
最后再决定删除重复 UI
```

---

# 27. Legacy Operation Parity Matrix

下一阶段需要对所有旧页面逐操作盘点，而不是“这个页面迁了没有”。

例如：

## Sources

旧能力包括：

- 文本导入；
- URL 导入；
- 文件上传；
- 事实提取；
- 事实确认；
- 事实拒绝；
- 批量操作；
- 事实编辑；
- 历史查看。

必须逐条确认新入口。

---

## FactPacks

旧能力包括：

- 新建；
- 添加事实；
- 删除事实；
- Clone；
- Freeze；
- 查看历史。

不是仅展示 FactPack 列表就算完成。

---

## Materials

旧能力包括：

- 上传；
- AI 生成；
- 搜索；
- 版本；
- rights；
- revoke；
- 项目引用；
- 预览。

---

## Settings

旧页面必须拆成：

- 真正常用配置；
- 高级本机维护；
- 已过时功能。

不能整页永久藏在“旧管理员工具”里。

---

# 28. 产品架构建议

建议未来逻辑分为六层：

```text
1. Intent Layer
   Opportunity / Idea / Brief / Identity

2. Knowledge Layer
   Sources / Facts / Evidence / Assets

3. Content Layer
   Content Master / Creative Intent / Channel Variant

4. Execution Layer
   Native Generation / Creative Execution Package / MCP / Agent

4.5 Capability Memory Layer
   Skill / Tool / Recipe / Creative Pattern / Preference

5. Decision Layer
   Candidate / Review / Approval / Delivery

6. Learning Layer
   Published Facts / Performance / Learning
```

这六层比“文章模块 / 图片模块 / 视频模块”更适合作为长期架构。

---

# 29. 当前已有能力怎么处理

## 保留并升权

- Identity；
- Project；
- Brief；
- Fact Boundary；
- MaterialRevision；
- Content Master；
- Channel Variant；
- Candidate；
- Review；
- Delivery；
- Receipt；
- Learning；
- ProviderGenerationTask。

## 改造

- Production Workspace；
- Video Studio；
- Graphic Studio；
- System Assets；
- Settings；
- Workflow UI。

## 降低长期投入

- 深视频 timeline；
- 内部复杂视频 render；
- 完整 NLE；
- 专业修图；
- 专业音频工程。

## 新增

- Creative Intent；
- Creative Execution Package；
- Director Package；
- External Execution；
- MCP；
- External Result Acceptance。

---

# 30. 规划阶段

## Phase 0：蓝图确认

当前阶段。

只做：

- 北斗星；
- 用户流程；
- 能力边界；
- Execution 架构；
- UI 信息架构；
- Legacy 承接原则。

不进入 OpenSpec。

---

## Phase 1：统一日常产品入口

目标：

> 不再需要普通用户在新旧页面之间跳。

工作：

- Landing 进入 Home；
- Production 不再占位；
- Assets 接住基础素材与来源操作；
- Project 接住事实与证据编辑；
- Settings 接住日常配置；
- Review 统一新旧必要入口；
- 建立 Legacy Operation Parity Matrix。

---

## Phase 2：创作工作区收敛

目标：

> Content First，而不是 Workflow First。

工作：

- 简化 Production Workspace；
- Workflow 放高级区域；
- 内容主稿成为主视图；
- Channel Variant 支持真正独立编辑；
- 图片 / 音频基础生成统一；
- Video 工作区转向 Script + Director Package。

---

## Phase 3：Creative Execution Core

新增：

- CreativeExecutionPackage；
- DirectorPackage；
- Execution；
- ExecutionResult；
- acceptance；
- provenance；
- external output → MaterialRevision。

---

## Phase 4：MCP 第一版

同时建立最小 Capability Memory：

- 成功执行可捕获为短期 candidate；
- candidate 可被人工提升为 Skill / Tool / Recipe；
- 保存版本、hash、scope、来源执行和使用次数；
- 支持 archived / deprecated；
- 不自动把一次成功变成长期能力；
- 外部复杂执行优先支持 checkpoint / recover 契约。

第一版 MCP 只要求：

- 读取项目；
- 读取 package；
- 读取素材；
- 提交结果；
- 提交 blocker；
- 请求人工审阅。

不要求 Premiere 自动化。

验收：

```text
Project
→ Execution Package
→ MCP
→ Test Agent
→ Output
→ 回传
→ MaterialRevision
→ 人工接受
→ Candidate
```

---

## Phase 5：专业工具执行

根据实际价值逐个接：

- Codex；
- Claude；
- Photoshop；
- Premiere；
- Resolve；
- After Effects；
- DAW。

不是为了“支持更多工具”而接。

只有真实使用价值才接。

---

## Phase 6：结果与学习闭环

最终做到：

```text
Intent
→ Content
→ Execution
→ Result
→ Publish
→ Performance
→ Learning
→ Future Intent
```

但 Learning 永远保留人工判断。

---

# 31. 不应该做的事情

未来两三年尤其避免：

## 31.1 不自己做第二个 Premiere

不要继续堆：

- timeline；
- keyframe；
- color grading；
- effect editor；
- audio mixer。

---

## 31.2 不自己做第二个 Photoshop

不要为了高级图片编辑重新实现：

- layers；
- masks；
- paths；
- professional retouching。

---

## 31.3 不为 MCP 重写业务系统

MCP 是接口。

不是新真源。

---

## 31.4 不让 Agent 直接修改真源

Agent 输出永远先成为候选结果。

---

## 31.5 不把执行完成当发布完成

ExecutionResult ≠ PublishedContent。

---

## 31.6 不让 AI 自动修改长期 Identity

Learning 只能提出候选。

---

## 31.7 不破坏历史

旧 Content Master、Candidate、Receipt、DeliveryAttempt、MaterialRevision 永远不因为产品重构被改写。

---

# 32. 长期竞争力

如果这个方向成立，AI Content Studio 真正的竞争力将不是：

> “我们有一个视频编辑器。”

而是：

### 1. 创作上下文

系统真正理解：

- 你是谁；
- 你为什么要做；
- 什么事实可信；
- 以前怎么说；
- 这次怎么说；
- 不同平台怎么说。

### 2. 创作意图

知道：

> 为什么这么做。

### 3. 跨工具执行

同一个任务可以交给不同 Agent / 软件。

### 4. 完整 provenance

知道：

> 谁、用什么、基于哪个版本、做出了哪个结果。

### 5. 长期学习

知道：

> 哪些真实结果应该影响未来创作。

这些能力不会因为某个图片模型、视频模型或剪辑软件升级而失去价值。

---

# 33. 判断新功能是否应该进入产品的决策框架

以后新增能力时统一问：

### Q1
它是不是内容或创作业务真源？

是 → 应进入 AI Content Studio。

### Q2
它是不是高频、简单、低维护的基础创作？

是 → 可以原生做。

### Q3
它是不是需要专业编辑体验？

是 → 优先 MCP / Agent。

### Q4
专业软件已经明显做得更好吗？

是 → 不重复造轮子。

### Q5
结果能否被标准化回传？

能 → 优先外部执行。

### Q6
如果外部工具明天换掉，业务数据是否还能成立？

如果不能 → 设计有问题。

---

# 34. 下一步讨论需要确定的关键事项

在进入 OpenSpec 前，建议我们先确认以下产品选择。

## 34.1 Director Package 是否作为正式核心概念

建议：是。

但可以讨论它最终是否命名为：

- Director Package；
- Creative Brief Package；
- Execution Package；
- Creative Plan。

---

## 34.2 CreativeExecutionPackage 是否成为通用对象

建议：是。

Video 的 Director Package 作为其专业化 schema。

---

## 34.3 External Execution 第一版做到什么程度

建议第一版只做到：

- MCP；
- 任务读取；
- 素材读取；
- 输出回传；
- blocker；
- 人工接受。

暂不要求自动 Premiere。

---

## 34.4 Video UI 如何收敛

建议：

主界面保留：

- Script；
- Scene；
- Shots；
- Assets；
- Voice；
- Subtitle；
- Director Package；
- External Execution。

高级 timeline 进入：

> 历史兼容 / 高级

不继续扩展。

---

## 34.5 旧页面最终处理

建议：

1. 新页面完整承接；
2. 退出日常导航；
3. 保留兼容期；
4. 再删除重复 UI；
5. 永不删除历史数据。

---

# 35. 成功标准

这次产品重构最终是否成功，不以“新增多少功能”衡量。

而看以下问题：

### 日常使用

一个正常内容项目，是否可以在一套新入口内完成，而不需要知道哪个是旧系统页面？

### 内容质量

系统是否保存了足够的事实、上下文和创作意图，让 Agent 得到的任务比单纯 Prompt 明显更准确？

### 执行弹性

同一个创作任务能否：

- 产品内生成；
- Codex 做；
- Claude 做；
- 专业软件做；

而业务真源保持不变？

### 可追溯

最终成果能否回答：

> 它来自哪个内容版本、哪些素材、哪些事实、哪次执行？

### 可维护

换模型、换 Agent、换专业工具时，是否不需要重写整个内容系统？

如果以上都能做到，产品方向就是正确的。

---

# 36. 最终北斗星总结

AI Content Studio 未来不应该成为一个越来越庞大的“全能编辑器”。

它应该成为：

> **一个懂你的内容、事实、品牌、创作意图和渠道策略的内容操作系统。**

它自己完成简单高频创作。

它把复杂任务交给当下最合适的 Agent 和专业工具。

它让所有外部结果重新回到同一套项目、版本、审阅、交付和学习体系。

**专业工具负责执行，AI Content Studio 负责理解、组织、决定、验收和记忆。**

这就是未来两到三年的核心方向。

---

# 37. 当前阶段结论

本文件只用于确定产品方向和实施规划。

在本文件得到确认之前：

- 不创建新的业务 OpenSpec；
- 不大规模修改 UI；
- 不删除旧页面；
- 不迁移历史数据；
- 不废弃 F6D；
- 不改变 F7/F8 已验证边界；
- 不修改当前正式运行环境。

确认后再进入下一阶段：

> **基于本北斗星重新梳理 OpenSpec、领域对象、页面承接矩阵和分阶段实施任务。**

## 37.1 实施状态（2026-10-05）

方向和 `align-creative-orchestration-product` 已经独立批准并进入分批实施；上面的确认前禁令是历史阶段边界，不表示当前仍未授权 apply。本轮产品方向不变，不通过措辞把已规划能力说成全部完成。

当前本地 main@341ead8 加未提交 change：**138/147**。日常入口、Creative Intent/Execution、成果人工接受、受限 MCP、Capability Memory、Director-first Video 与受控恢复已按各批记录实施。新日常项目已经从 Source/Fact/Pack 走到 Text Master、Candidate v4、审批和本地 ZIP；旧稿件/候选/回执仍保留原 ID 和读取路径。

剩余是 Assets/Settings 全操作 parity、完整浏览器补验、最终独立复核及持续安全边界。旧日常导航没有隐藏，正式 SQLite 未迁移，canonical/archive/提交/外部调用未执行；配套验收见 `ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md`。正式环境继续是本机 SQLite、本地素材库和 loopback API/Web，不新增服务器化目标。
