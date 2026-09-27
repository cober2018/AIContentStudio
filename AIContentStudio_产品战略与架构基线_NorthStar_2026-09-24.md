# AI Content Studio 产品战略与架构基线

> 文档类型：Product Strategy & Architecture North Star  
> 产品：AIContentStudio  
> 状态：长期指导性文档  
> 适用范围：产品设计、PRD、OpenSpec、架构设计、Workflow、Skills、渠道适配、审核、发布、素材、数据反馈  
> 日期：2026-09-24

---

# 1. 文档目的

AIContentStudio 未来会持续增加新的内容来源、新的模型、新的 Skills、新的平台、新的工作流、新的图片能力、新的审核规则以及新的发布方式。

如果这些需求以“一个需求对应一段业务代码”的方式不断累加，系统最终会演变成：

```text
if platform == ...
if content_type == ...
if publisher == ...
if model == ...
```

或者变成一个由大量 Prompt、脚本、浏览器自动化和平台按钮拼接而成的工具集合。

AIContentStudio 不应走向这种形态。

这份文档定义 AIContentStudio 的长期产品基调与架构原则，用于回答：

- 这个产品最终应该是什么；
- 什么能力属于 AIContentStudio；
- 什么能力应该交给外部系统；
- 什么东西应该成为稳定的核心对象；
- 什么东西应该做成可替换插件；
- 一个内容任务应该如何从来源走向最终发布；
- 人工审核在系统中处于什么位置；
- 新渠道、新 Skill、新模型和新发布方式应该如何接入；
- 后续产品设计和技术实现应该遵守哪些长期原则。

后续 PRD、OpenSpec 和具体实施方案都应服从本文档，而不是反过来改变本文档中的长期原则。

---

# 2. 产品使命

AIContentStudio 的使命不是“用 AI 帮用户写文章”。

它的使命是：

> **把可信素材、内容策略、AI 能力、人工判断、多平台适配与发布交付组织成一个可持续演进的内容生产系统。**

它解决的核心问题不是“生成速度”，而是：

1. 内容从哪里来；
2. 哪些事实是可信的；
3. 哪些观点属于作者；
4. 哪些内容可以公开；
5. 同一主题如何适配不同渠道；
6. 哪些步骤由 AI 完成；
7. 哪些步骤必须人工判断；
8. 一篇内容当前处于什么状态；
9. 为什么会生成现在这个版本；
10. 这个版本是否已经具备发布条件；
11. 最终到底发布了什么；
12. 发布后的反馈如何回到下一轮内容生产。

因此，AIContentStudio 更接近：

> **Content Operating System / Content Harness**

而不是：

> AI Writer / Auto Publisher

---

# 3. 一句话产品定义

AIContentStudio 是一个：

> **事实驱动、人工可控、插件式、多渠道的内容生产、审核与分发中心。**

其中：

- **事实驱动**：内容不允许脱离可追溯来源自由生成客观事实；
- **人工可控**：AI 是执行能力，不是最终决策者；
- **插件式**：模型、Skills、规则、工作流、图片能力和发布能力都应可替换；
- **多渠道**：渠道是独立内容产品，不是同一篇稿件的不同导出格式；
- **生产、审核与分发中心**：系统负责完整生命周期，而不是只负责生成。

---

# 4. 产品不是什么

## 4.1 不是通用聊天机器人

聊天可以作为入口，但聊天本身不是产品核心。

真正重要的是：

```text
Source
→ Evidence
→ Topic
→ Mother Content
→ Platform Adaptation
→ Review
→ Approved Candidate
→ Delivery
→ Feedback
```

## 4.2 不是另一个研究系统

量化平台继续负责市场数据、指标、回测、因子研究、策略计算和图表计算。

媒体分析系统继续负责信息抓取、原始新闻、视频/音频、转写、舆情数据和第三方观点。

AIContentStudio 接收这些成果，但不重新建设这些上游系统。

原则：

```text
Upstream System
      ↓
Connector / Import
      ↓
AIContentStudio
```

而不是：

```text
AIContentStudio
      ↓
直接访问上游数据库
```

## 4.3 不是纯自动发布工具

发布只是最后一个阶段。

产品价值主要来自内容质量、一致性、可追溯性、多平台适配、审核和可控交付。

如果前面的内容错误，一键发布只会更快地放大错误。

## 4.4 不是平台 API 聚合器

平台 API、浏览器自动化、第三方 CLI 都只是 Publisher 实现，可以被替换。

平台登录方式发生变化，不应该导致整个内容系统重构。

## 4.5 不是 Prompt 仓库

Prompt 是实现细节。

真正需要长期维护的是：

- 内容意图；
- 平台规则；
- 品牌 Voice；
- Workflow；
- Skill；
- Rule；
- Input / Output Contract；
- 版本；
- 评价结果。

---

# 5. 产品战略：稳定核心 + 可变能力

AIContentStudio 的长期架构应明确区分两类东西。

## 5.1 Stable Core

长期稳定，不应随模型或平台频繁变化：

```text
Source
Evidence
FactPack
Topic
MotherRevision
PlatformDraft
Media
Review
Candidate
Approval
DeliveryTarget
Receipt
Feedback
```

## 5.2 Replaceable Capabilities

允许快速变化：

```text
Model
Prompt
Skill
Rule
Workflow
Renderer
Image Provider
Browser Automation
Publisher
Search Provider
Platform Adapter
```

核心原则：

> **内容资产属于 Studio，执行能力属于插件。**

因此：

- 更换 LLM，旧文章仍然存在；
- 更换 Skill，旧版本仍然可以解释；
- 更换 Publisher，不影响已批准内容；
- 平台改版，不影响母稿和证据；
- 某个插件失效，不影响整个内容资产体系。

---

# 6. 核心产品模型

AIContentStudio 的长期核心对象建议保持以下层级：

```text
Source
  ↓
Evidence / Fact
  ↓
FactPack
  ↓
Topic
  ↓
MotherRevision
  ↓
PlatformWorkflowRun
  ↓
PlatformDraft
  ↓
Document + Media
  ↓
Checks
  ↓
Candidate
  ↓
Approval
  ↓
DeliveryTarget
  ↓
DeliveryAttempt / Receipt
  ↓
Feedback
```

这条链路是产品长期稳定的骨架。

---

# 7. Source：内容从哪里来

Source 是所有内容的原始来源，包括：

- 文件；
- URL；
- API；
- 数据平台；
- 研究报告；
- 用户手工输入；
- 已有文章；
- 第三方观点；
- 视频/音频转写；
- 项目代码；
- Git 仓库；
- 外部 Agent 产出。

Source 不等于 Fact。

一个来源可以同时包含客观事实、作者观点、第三方观点、推测、错误信息和未确认信息，因此 Source 必须经过整理才能进入内容生成。

---

# 8. Evidence 与 FactPack：可信性的基础

AIContentStudio 必须坚持：

> **模型不能因为“写文章需要”而自行制造事实。**

Evidence 至少应能表达：

```text
内容
来源
时间
主体
口径
可信状态
是否允许模型使用
是否允许公开使用
```

FactPack 是某一篇内容在某个版本下允许使用的事实边界。

FactPack 一旦冻结：

```text
不可原地修改
```

修改必须产生新版本。

这是整个内容系统可追溯性的基础。

---

# 9. Topic：内容任务的业务入口

Topic 不是一句标题。

它表达：

- 这次为什么写；
- 写给谁；
- 想表达什么；
- 哪些事实必须出现；
- 哪些观点需要讨论；
- 哪些内容不能写；
- 希望读者做什么；
- 最终准备适配哪些渠道。

Topic 是一次内容生产任务的根对象。

---

# 10. MotherRevision：跨平台内容的共同源头

所有平台稿原则上应从一个明确的 MotherRevision 派生。

MotherRevision 保存：

- 核心事实；
- 核心观点；
- 内容逻辑；
- 作者原始表达；
- 重要引用；
- 关键结论。

平台适配原则是：

```text
事实保持一致
观点保持可追溯
表达允许大幅变化
结构允许重新组织
```

不是：

```text
公众号文章
→ 换标题
→ 发知乎
→ 缩短
→ 发小红书
```

而是：

```text
MotherRevision
      ├─ 公众号 Workflow
      ├─ 知乎 Workflow
      ├─ 小红书 Workflow
      ├─ 雪球 Workflow
      ├─ 掘金 Workflow
      └─ X Workflow
```

---

# 11. Channel 是内容产品，不是导出格式

每个平台都有自己的：

- 用户心理；
- 内容消费方式；
- 内容长度；
- 社区语言；
- 算法机制；
- 图片习惯；
- 搜索机制；
- 互动方式；
- 发布能力。

因此：

> **Channel 不应该只是 Prompt 中的一个变量。**

一个 Channel 应定义：

```text
支持的 Content Forms
默认 Workflow
平台 Rules
默认 Skills
Renderer
Publisher Capability
Account Profile
```

一个 Channel 可以拥有多个 Workflow。

例如雪球可以同时存在：

```text
A股复盘
量化研究
行业分析
AI产业观察
短观点
```

---

# 12. 核心架构思想：Content Harness

AIContentStudio 应借鉴 DeepSeek Harness 的核心架构思想：

> **Everything that changes frequently should be a plugin.**

不是照搬某个具体框架，而是借鉴：

- Registry；
- Dependency；
- Context；
- Profile；
- Bundle；
- Replaceable Provider；
- Versioned Capability。

最终形成：

```text
Content Harness
    │
    ├─ Channel Registry
    ├─ Workflow Registry
    ├─ Node Registry
    ├─ Skill Registry
    ├─ Rule Registry
    ├─ Renderer Registry
    ├─ Asset Provider Registry
    └─ Publisher Registry
```

插件化不是一个前端功能，而是产品持续演进的机制。

---

# 13. Channel → Workflow → Node → Skill / Rule

这是 AIContentStudio 最重要的抽象关系：

```text
Channel
   └─ Workflows
         └─ Nodes
               ├─ Skills
               ├─ Rules
               ├─ Models
               ├─ Asset Providers
               └─ Publishers
```

## Channel

代表平台能力与内容生态。

## Workflow

代表这个平台某一种内容生产方式。

## Node

代表工作流中的一个处理步骤。

## Skill

负责复杂的生成、分析和改写能力。

## Rule

负责确定性判断、限制和 Gate。

---

# 14. Skill 与 Rule 必须严格区分

## Skill

回答：

> “应该怎么做？”

例如：

- 如何写公众号文章；
- 如何写雪球复盘；
- 如何拆成 X Thread；
- 如何优化标题；
- 如何去 AI 味。

Skill 是概率性的、生成式的。

## Rule

回答：

> “当前结果是否满足要求？”

例如：

- 是否出现新数字；
- 是否缺数据日期；
- 是否缺封面；
- 是否存在 placeholder；
- 是否遗漏免责声明；
- 是否违反标题限制；
- 是否缺少回测区间。

因此：

```text
Skill ≠ Validator
LLM Review ≠ Rule Engine
```

确定性问题优先交给确定性规则。

---

# 15. Workflow 是产品能力的主要组织形式

普通用户不应该直接面对几十个 Skills。

普通用户看到的是：

```text
选择内容
→ 选择渠道
→ 选择内容类型
→ 开始生产
```

背后实际运行的是 Workflow。

例如“公众号深度文章”的 Workflow 可能是：

```text
Mother Adapt
→ Writer Skill
→ Humanizer
→ Image Plan
→ Asset Prepare
→ Fact Check
→ Content Rules
→ Render
→ Human Review
```

高级用户或管理员才需要进入 Workflow 配置。

---

# 16. Workflow 必须支持局部调整

AI 内容生产不是一次性流水线。

真实使用必然包含：

- 某个标题不好；
- 某段需要重写；
- 图片不好；
- 图片位置不合适；
- 某个规则报警；
- 用户手工改了一段；
- 用户想换模型；
- 用户想临时改 Prompt。

因此 Workflow 必须天然支持：

```text
Rerun Node
Rerun From Here
Manual Edit
Replace Asset
Override Prompt
Switch Skill
Switch Model
```

而不是任何变化都重新跑整条链路。

---

# 17. Derived State 与 Stale Propagation

所有派生结果都必须知道自己的输入版本。

例如：

```text
Draft
→ FactCheck
→ ImagePlan
→ Render
→ Candidate
```

如果 Draft 改变：

```text
FactCheck stale
ImagePlan possibly stale
Render stale
Candidate invalid
Approval invalid
```

如果只替换图片：

```text
FactCheck remains valid
Render stale
Candidate invalid
Approval invalid
```

如果只换发布账号：

```text
Candidate remains valid
Content Approval remains valid
Delivery Authorization changes
```

系统应该根据依赖图自动判断，而不是靠人工记忆。

---

# 18. 人工永远是 Workflow 的一等参与者

AIContentStudio 不追求“尽可能去掉人工”。

它追求：

> **把人工判断放在最有价值的位置。**

Human Node 应与 AI Node 地位相同。

例如：

```text
AI Generate
→ Human Edit
→ AI FactCheck
→ Human Approve
→ Auto Delivery
```

人工不是自动化失败后的补救方案。

人工本身就是 Workflow 的组成部分。

---

# 19. Review & Publish Center 是产品核心

AIContentStudio 最重要的界面之一不是“生成页面”，而是：

> **审核与发布中心**

这个页面回答：

```text
哪些渠道已经完成？
哪些还缺东西？
为什么不能发布？
当前最终版本是什么？
需要我做什么？
```

一个 Topic 可以同时显示：

```text
公众号       Ready
知乎文章     Ready
雪球         Warning
小红书       Missing Image
掘金         Ready
X            Ready
```

进入某个渠道后应同时看到：

```text
最终内容
最终图片
图片位置
事实状态
规则状态
Workflow 状态
版本
发布能力
```

并允许：

- 修改标题；
- 编辑正文；
- 局部 AI 重写；
- 调整 Prompt；
- 调整 Skill；
- 重跑某节点；
- 从某节点重新执行；
- 上传图片；
- 生成图片；
- 替换图片；
- 调整图片顺序；
- 移动图片位置；
- 修改标签；
- 修改 CTA；
- 保存新版本。

---

# 20. 文本与图片必须属于同一内容版本

最终文章不是：

```text
正文
+
附件列表
```

而应该是一个结构化 Document。

例如：

```text
Heading
Paragraph
Paragraph
Image
Paragraph
Chart
Paragraph
Image
```

图片具有：

```text
位置
顺序
caption
alt
来源
rights
revision
hash
```

这样才能保证：

- 排版不会丢；
- 图片不会乱序；
- 手工发布包知道图应该插在哪里；
- 审批覆盖完整内容；
- 发布时不会临时重新选择图片。

---

# 21. Media 必须版本化

图片不能覆盖旧版本。

每次修改：

```text
MediaRevision +1
```

素材应记录：

- 来源；
- 文件 hash；
- 是否允许公开使用；
- 是否允许模型处理；
- 生成模型；
- Prompt；
- 创建时间；
- 原图；
- 编辑版本。

因此任何历史 Candidate 都应该能够重新构建。

---

# 22. Candidate 是发布前唯一可信对象

Draft 不等于可发布内容。

真正进入发布阶段的是：

> **Immutable Candidate**

Candidate 冻结：

- 标题；
- 正文；
- 文档结构；
- 图片；
- 图片位置；
- 图片顺序；
- 标签；
- 引用；
- 声明；
- 检查结果；
- Workflow Version；
- Skill Version；
- Prompt Version；
- Candidate Hash。

任何内容变化都产生新的 Candidate。

Approval 永远绑定：

```text
Candidate Hash
```

---

# 23. 审核与发布授权必须分离

两个问题不同：

## Content Approval

> 这份内容是否可以对外？

## Delivery Authorization

> 这份已批准内容是否可以发送到这个账号？

因此：

换账号：

```text
不一定需要重新审核内容
```

改正文：

```text
一定需要重新审核内容
```

这个边界必须长期保持。

---

# 24. “一键发布”的产品定义

AIContentStudio 的“一键发布”不意味着：

> 一键公开上线。

正确含义是：

> **一键完成当前平台能力允许的最远安全交付动作。**

长期分为三种模式。

## AUTO_DRAFT

平台支持稳定草稿能力：

```text
Approved Candidate
→ Publisher
→ Platform Draft
```

## ASSISTED_DRAFT

没有稳定 API，但浏览器流程可自动化：

```text
Approved Candidate
→ Browser Automation
→ 自动填标题/正文/图片
→ 保存草稿
→ 人工核对
```

## COPY_PACKAGE

无法稳定自动创建草稿：

```text
Approved Candidate
→ Platform Renderer
→ Manual Publish Package
```

包内保存：

- 标题；
- 富文本正文；
- 图片；
- 图片顺序；
- 插图位置；
- 标签；
- 发布说明。

目标是：

> **人工发布，但不丢失格式和排版。**

---

# 25. Publisher 是最后一公里插件

Publisher 不负责：

- 写文章；
- 修文章；
- 改标题；
- 生成图片；
- 自动删除内容；
- 发布前临时截断正文。

Publisher 接收的必须是：

```text
Approved Candidate
```

并执行明确动作：

```text
create_draft
update_draft
assist_publish
copy_package
```

平台最终格式转换必须发生在 Approval 之前，不能在 Publisher 内偷偷改变内容。

---

# 26. Publisher Capability 是动态能力

平台支持不能只记录：

```text
supported = true
```

而应该按：

```text
Platform
× Account
× Content Form
× Action
× Verification Time
```

记录。

例如：

```text
微信公众号
  article
    create_draft: verified

雪球
  long_post
    browser_draft: tested
    copy_package: verified

企鹅号
  article
    auto_draft: unavailable
    copy_package: verified
```

---

# 27. 插件体系

长期至少包含以下插件类型：

```text
Channel Plugin
Workflow Plugin
Node Plugin
Skill Plugin
Rule Plugin
Renderer Plugin
Asset Provider Plugin
Publisher Plugin
Research Plugin
```

Channel Plugin 描述平台能力与默认组合。

Workflow Plugin 描述如何完成一种内容任务。

Node Plugin 是最小执行单元。

Skill Plugin 负责复杂生成和推理。

Rule Plugin 负责确定性判断。

Renderer Plugin 把内部 Document 转换为平台成品格式。

Asset Provider Plugin 提供图片、图表、截图等素材能力。

Publisher Plugin 负责最后一公里交付。

Research Plugin 负责搜索和趋势发现，但其结果只能进入 Source / Candidate Evidence，不能自动变成 Fact。

---

# 28. Plugin Registry

所有插件进入统一 Registry。

至少记录：

```text
key
type
version
provider
source
license
status
capabilities
dependencies
permissions
verified_at
```

状态建议：

```text
discovered
installed
enabled
vetted
active
deprecated
disabled
```

---

# 29. 插件版本必须冻结

Workflow 不应该引用：

```text
latest
```

而应该引用：

```text
studio-xueqiu-article@1.3.0
```

原因：

> 同一个 Workflow 今天重跑和下个月重跑，必须能够解释差异来自哪里。

插件升级流程：

```text
Install
→ Test
→ Vet
→ Publish Workflow Version
```

历史 Workflow 继续引用历史版本。

---

# 30. 外部 Skills 的战略

AIContentStudio 应大量利用现有 Skills。

但“拿来用”不等于“复制代码进仓库”。

根据情况分为：

```text
Vetted Dependency
External Runtime
Reference Implementation
Custom Studio Skill
```

外部 Skill 至少检查：

- License；
- Cookie；
- credentials；
- 网络请求；
- 文件权限；
- 自动公开发布；
- 是否上传私有数据；
- 是否存在重复发布风险。

已经成熟的公共能力优先复用，Studio 不重复造轮子。

但外部能力不能成为 Studio 业务状态的唯一存储。

---

# 31. Profile 与 Bundle

借鉴 Harness 思路，配置分层。

## Channel Profile

平台级能力。

## Account Profile

账号级差异。

## Voice Profile

表达风格。

## Workflow Bundle

一组可复用节点。

## Runtime Profile

模型、Skill、浏览器、图片服务、超时、重试等执行环境。

最终优先级：

```text
System Defaults
↓
Channel Profile
↓
Workflow
↓
Account Profile
↓
Run Override
```

---

# 32. Run Override

用户在某一篇稿件中调整 Prompt、Skill 或模型时：

默认只影响：

```text
当前 Run
```

不能偷偷影响全局。

如果用户确认长期生效，可以显式：

```text
Save as Account Preference
Publish New Workflow Version
```

---

# 33. Context 是 Workflow 的数据总线

Workflow Node 不应直接互相依赖具体实现。

通过统一 Context 连接。

Context 保存：

```text
topic_id
mother_revision_id
fact_pack_id
draft_revision_id
media_revision_ids
rules_report_id
candidate_id
delivery_target_id
```

主要传 ID、版本和 Hash，而不是在每个 Node 之间复制完整正文。

---

# 34. Workflow Engine 的职责必须保持极小

Engine 只负责：

- 加载 Workflow；
- 解析依赖；
- 调度 Node；
- 管理状态；
- 暂停；
- 恢复；
- 重试；
- stale propagation；
- 写运行记录。

Engine 不负责：

- 怎么写公众号；
- 怎么生成图片；
- 怎么发雪球；
- 怎么做金融检查。

这些都属于 Plugin。

---

# 35. 默认 Workflow，而不是默认自由画布

底层支持 DAG，不代表普通用户应该设计 DAG。

默认体验应该是：

```text
选择内容
→ 选择渠道
→ 使用推荐 Workflow
```

高级模式才允许：

- 加节点；
- 删除节点；
- 换 Skill；
- 调整 Rule；
- 拖线；
- 创建 Workflow。

原则：

> 架构灵活，不代表产品必须复杂。

---

# 36. 内容编辑器是 Workflow 的人工节点

用户编辑正文后：

```text
new Draft Revision
```

然后系统根据依赖决定哪些派生物失效。

不是：

```text
编辑器保存
→ 覆盖数据库正文
```

每一次修改都应可追踪。

---

# 37. Review Center 是 Workflow 的 Projection

不要建立第二套状态系统。

Review Center 聚合：

```text
Workflow Run
Draft
Media
Checks
Candidate
Approval
Delivery
```

显示成用户容易操作的工作台。

Workflow 是执行事实。

Review Center 是操作视图。

---

# 38. 内容状态必须真实

系统禁止使用模糊的：

```text
完成
已发布
成功
```

如果事实不是这样。

应该区分：

```text
Generated
Needs Review
Blocked
Candidate Ready
Approved
Delivery Ready
Draft Created
Waiting Human
Submitted
Published
Unknown
Failed
```

没有平台确认时不能叫 Published。

---

# 39. Unknown 是合法状态

任何外部副作用都可能发生：

```text
请求超时
但远端可能已经成功
```

这时应该进入：

```text
Unknown
```

而不是自动重试。

原则：

> **外部发布的结果未知优先人工核对，而不是冒险重复发送。**

---

# 40. 每个平台分支必须独立

选择五个平台后：

```text
Platform A 失败
```

不能导致：

```text
Platform B/C/D/E 全部失败
```

渠道 Workflow 是独立 Run。

共享：

```text
MotherRevision
Evidence
```

不共享：

```text
执行状态
发布状态
重试状态
```

---

# 41. 系统必须支持渐进自动化

不是所有平台都必须一次实现完全自动发布。

能力可以按：

```text
Manual
→ Copy Package
→ Assisted Draft
→ Draft Automation
```

逐步提升。

产品不能因为一个平台缺少稳定自动化能力就放弃该平台，也不能为了追求“全自动”而降低可靠性。

---

# 42. 模型是供应商，不是架构

AIContentStudio 不应绑定任何单一模型供应商。

模型通过 Model Provider / Runtime Profile 接入。

业务对象不存“只有某模型才能理解的状态”。

模型选择发生在场景层，例如：

```text
Research
Topic Discovery
Longform Writing
Rewrite
Fact Review
Image Prompt
Code Review
```

Workflow Node 声明任务目的，Runtime 决定具体模型。

---

# 43. Fact Check 不能完全依赖 LLM

Fact Check 应分层：

```text
Deterministic Check
Semantic Check
Human Review
```

LLM 失败不能默认 pass。

检查没有完整执行时：

```text
incomplete
```

---

# 44. 权利是内容系统的一部分

文本和图片都需要区分：

```text
可存储
可模型处理
可内部使用
可公开使用
```

这些是不同权限。

用户上传内容不自动意味着可以发送给第三方模型。

网上找到的图片也不自动意味着可以公开发布。

---

# 45. 数据反馈的目标不是做 BI

Feedback 的核心作用是：

> **改善下一轮内容生产。**

可以记录：

- 阅读；
- 收藏；
- 点赞；
- 评论；
- 分享；
- 点击；
- 用户反馈；
- 内容满意度；
- 编辑修改；
- 退稿原因。

但不同平台指标不强行求和。

---

# 46. 反馈不能自动修改全局策略

某一篇文章高流量：

```text
只是一个观察
```

不能立即变成：

```text
以后所有标题都这么写
```

反馈首先进入：

```text
Learning Candidate
```

经过多次样本或人工确认后：

```text
Voice / Workflow / Rule 新版本
```

---

# 47. AIContentStudio 的长期竞争力

产品真正长期有价值的不是：

- Prompt；
- 某个模型；
- 某个平台接口；
- 某个自动化脚本。

这些都会快速变化。

真正的长期资产是：

```text
可信证据体系
内容版本体系
平台 Workflow
品牌 Voice
经过验证的 Skills
规则集
真实内容资产
审核历史
发布记录
效果反馈
```

---

# 48. 产品演进顺序

每增加一个能力，优先顺序应为：

```text
1. 定义业务对象和边界
2. 定义输入输出 Contract
3. 定义 Plugin 能力
4. 加入 Workflow
5. 增加 Review / Observability
6. 最后增加自动化
```

而不是：

```text
先写一个自动脚本
再想怎么管理它
```

---

# 49. 新平台接入决策框架

增加任何新渠道时，不应该先问：

> “我们要不要支持这个 API？”

应该先问：

```text
这个平台值得生产什么内容？
有哪些 Content Forms？
对应什么用户？
内容结构有什么不同？
需要什么 Workflow？
哪些 Rules？
需要哪些 Media？
Renderer 怎么做？
可以做到哪一级 Delivery？
```

然后再决定技术实现。

---

# 50. 新 Skill 接入决策框架

增加 Skill 时，需要回答：

1. 它解决什么能力；
2. 是否已有相同能力；
3. 输入是什么；
4. 输出是什么；
5. 是否有副作用；
6. 是否会读取敏感信息；
7. 是否会调用网络；
8. License 是什么；
9. 如何版本化；
10. 如何测试；
11. 失败时是否安全。

---

# 51. 新 Workflow 设计原则

每个 Workflow 应该：

- 明确输入；
- 明确最终产物；
- 节点数量适度；
- 可单独重跑；
- 有确定性的 Gate；
- 人工节点位置合理；
- 不隐藏副作用；
- 不把 Publisher 放在 Approval 前；
- 不在 Publisher 中修改正文；
- 不在运行中偷偷切换最新 Skill。

---

# 52. 技术实现原则：模块化单体优先

AIContentStudio 当前最适合继续保持：

```text
Modular Monolith
```

插件化是：

```text
逻辑边界
注册机制
依赖接口
```

不是：

```text
网络服务数量
```

只有真正存在独立扩缩容、安全隔离、不同运行环境或独立失败域时，再考虑拆服务。

---

# 53. Harness Runtime 与 Studio 的关系

DeepSeek Harness / dsh 可以作为：

```text
Execution Runtime
```

AIContentStudio 是：

```text
Content Control Plane
```

Studio 负责：

- 任务；
- 数据；
- 版本；
- 审核；
- Workflow；
- 状态；
- 发布授权。

Harness 负责：

- 执行 Skill；
- 模型调用；
- Tool 调用；
- 沙箱；
- Agent Runtime。

长期不应把 Studio 的业务状态放到 Harness 的运行目录中作为唯一真源。

---

# 54. Control Plane 与 Execution Plane

推荐长期明确：

```text
AIContentStudio = Control Plane
DSH / Skill Runtime / Browser = Execution Plane
```

Control Plane 决定：

```text
做什么
用什么版本
能不能做
结果是什么
下一步是什么
```

Execution Plane 决定：

```text
具体怎么执行
```

---

# 55. 为什么这是 Content Harness，而不只是 Workflow Engine

普通 Workflow Engine 主要关心：

```text
任务有没有执行
```

Content Harness 还必须关心：

```text
使用了什么事实
用了哪个版本
文字和图片是不是同一版本
哪些规则执行过
谁修改过
谁批准
最终交付了什么
```

因此核心对象必须高于普通自动化 DAG。

---

# 56. 长期产品体验

最终用户应该能够：

```text
打开一个 Topic
```

看到：

```text
母稿
证据
渠道
工作流
版本
素材
审核
发布
数据
```

而不是需要在素材页、Prompt 页、Workflow 页、脚本页、发布工具和浏览器之间自行拼接流程。

---

# 57. 三个主要工作区

长期建议形成三个主要产品工作区。

## Content Workspace

解决：

```text
写什么
内容是什么
```

包括：

- Source；
- FactPack；
- Topic；
- MotherRevision；
- Draft；
- Editor。

## Production Workspace

解决：

```text
怎么生产
```

包括：

- Channel；
- Workflow；
- Node；
- Skill；
- Rule；
- Media。

## Review & Delivery Workspace

解决：

```text
能不能发
发到哪里
发了什么
```

包括：

- Preview；
- Checks；
- Candidate；
- Approval；
- Delivery；
- Receipt。

---

# 58. 设置页不是业务中心

模型、Skills、插件和账号应该集中管理。

但日常生产不应要求用户频繁进入 Settings。

配置应该通过 Profile 被 Workflow 自动引用。

---

# 59. 可观察性

每次内容生产必须能回答：

```text
哪个 Workflow？
哪个 Workflow Version？
哪个 Skill？
哪个 Skill Version？
哪个模型？
哪个 Prompt？
哪个 FactPack？
哪个 MotherRevision？
哪些 Media？
哪些 Rule？
谁修改？
谁审核？
哪个 Candidate？
发布到哪个账号？
最终 Receipt？
```

如果无法回答，说明运行链缺乏可追溯性。

---

# 60. 成本与性能原则

AIContentStudio 不追求每一步都使用最强模型。

应根据任务分层：

- 简单 transform 用代码；
- 确定性判断用 Rule；
- 简单分类用小模型；
- 复杂写作用强模型；
- Research 使用适合搜索和工具调用的模型。

原则：

> **能确定性完成的事情，不交给生成式模型。**

---

# 61. 测试战略

测试分成四层。

## Unit

测试：

- Rule；
- Contract；
- Registry；
- Renderer；
- 状态迁移。

## Golden

测试：

- Writer；
- Platform Adaptation；
- Voice；
- 事实保持。

## Integration

测试：

```text
MotherRevision
→ Workflow
→ Candidate
```

## Real Platform

真实账号验收：

```text
Approved Candidate
→ Draft
→ Read Back / Human Verify
```

只有最后一级通过才能标记：

```text
Publisher Capability = verified
```

---

# 62. 向后兼容原则

系统演进必须保证：

- 旧内容可读；
- 旧版本可解释；
- 不通过迁移伪造新证据；
- 不把历史内容自动标为已审核；
- 新规则不倒灌修改历史事实。

---

# 63. 安全边界

所有外部执行能力都应被视为：

```text
Untrusted Capability
```

包括：

- 第三方 Skill；
- MCP；
- Browser Automation；
- CLI；
- Plugin；
- Web Content。

原则：

```text
最小权限
显式授权
凭据隔离
运行审计
副作用确认
```

---

# 64. 总体架构

```text
                    ┌──────────────────────────┐
                    │      Upstream Systems     │
                    │ Quant / Media / Files / Web│
                    └────────────┬─────────────┘
                                 │
                         Source / Connector
                                 │
                    ┌────────────▼─────────────┐
                    │       Evidence Core       │
                    │ Source / Fact / FactPack  │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │       Content Core        │
                    │ Topic / MotherRevision    │
                    └────────────┬─────────────┘
                                 │
                          Channel Selection
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
  Channel Workflow        Channel Workflow        Channel Workflow
        │                        │                        │
        └────────────── Content Harness ─────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Skills / Rules / Models   │
                    │ Assets / Renderers        │
                    │ Human Nodes               │
                    └────────────┬─────────────┘
                                 │
                     Draft + Document + Media
                                 │
                    ┌────────────▼─────────────┐
                    │ Review & Publish Center   │
                    │ Checks / Preview / Edit   │
                    └────────────┬─────────────┘
                                 │
                         Immutable Candidate
                                 │
                              Approval
                                 │
                    ┌────────────▼─────────────┐
                    │      Delivery Router      │
                    └────────────┬─────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
             Auto Draft      Assisted Draft    Copy Package
                 │               │               │
                 └───────────────┼───────────────┘
                                 ▼
                              Receipt
                                 │
                              Feedback
```

---

# 65. 核心架构不变量

未来所有开发必须保护以下不变量。

## 不变量 1

事实不能因为重新生成而漂移。

## 不变量 2

历史版本不能被覆盖。

## 不变量 3

平台稿必须绑定明确 MotherRevision。

## 不变量 4

文字和图片必须属于同一个可批准版本。

## 不变量 5

Approval 必须绑定完整 Candidate Hash。

## 不变量 6

内容审批和发布授权必须分开。

## 不变量 7

Publisher 不允许临发布时修改已批准内容。

## 不变量 8

未知的远端结果不能自动重试。

## 不变量 9

人工操作是一等 Workflow Node。

## 不变量 10

插件升级不能改变历史 Run。

## 不变量 11

没有真实验证的平台能力不能显示为已支持。

## 不变量 12

新增平台原则上不修改 Workflow Engine。

---

# 66. 产品决策检查表

未来讨论任何新需求时，先回答：

### 它属于 Core 还是 Plugin？

如果经常变化，优先 Plugin。

### 它创建新的业务对象了吗？

如果与现有对象同义，不创建。

### 它会不会破坏版本一致性？

如果会，先设计 revision/hash。

### 它产生外部副作用吗？

如果会，需要 Delivery Intent / Receipt / Unknown 状态。

### 它能不能局部重跑？

不能时，需要重新检查依赖边界。

### 它能不能被替换？

模型、Skill、Publisher 原则上必须可替换。

### 它是否绕过 Review？

不能。

### 它是否改变最终 Candidate？

如果是，需要重新 Approval。

---

# 67. 产品战略总结

AIContentStudio 的长期方向不是：

> 支持越来越多平台。

也不是：

> 集成越来越多 AI 工具。

真正方向是：

> **建立一个稳定的内容核心，并允许外部能力围绕这个核心不断替换和进化。**

因此产品最终应该具备：

```text
事实可信
内容可追溯
工作流可编排
能力可插拔
人工可介入
局部可重跑
多渠道可适配
文字图片同版本
发布动作可控
结果可验证
反馈可沉淀
```

当新的模型、新的平台、新的 Skill、新的 Agent、新的发布技术出现时：

```text
AIContentStudio 不需要重构
```

而只是：

```text
注册一个新能力
组合一个新 Workflow
验证一个新 Capability
```

这就是这套产品架构最终要达到的状态。

---

# 68. 产品北极星

如果未来面对复杂需求不知道怎么取舍，可以回到这一句话：

> **AIContentStudio 不是替用户自动写内容，而是把“可信内容如何被生产、修改、审核、适配和交付”变成一套长期可管理、可解释、可演进的系统。**
