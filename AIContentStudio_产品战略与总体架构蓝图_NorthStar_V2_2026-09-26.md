# AIContentStudio 产品战略与总体架构蓝图 · North Star V2

> 文档类型：Product Strategy & Architecture Blueprint / North Star  
> 产品：AIContentStudio  
> 版本：V2  
> 状态：长期指导性蓝图  
> 适用范围：产品战略、总体架构、领域模型、PRD、OpenSpec、Workflow、模型与工具、内容身份、图/视/文生产、渠道适配、审核、发布、素材、数据反馈与学习  
> 修订日期：2026-09-26  
> 基线来源：2026-09-24《AI Content Studio 产品战略与架构基线》  
> 本版性质：蓝图级修订，不是某一个功能 PRD

---

# 0. V2 修订摘要

V2 不推翻 V1 已经建立的可信证据、版本、审核、Candidate、发布授权、渐进自动化和可追溯性原则。

本次修订主要解决 V1 中五个仍然偏弱的地方：

1. **从“内容生产流水线”升级为“内容智能与生产平台”**；
2. **把“内容身份”提升为贯穿全系统的一等坐标轴**；
3. **把 Topic 根对象升级为 ContentProject / 内容项目，并支持多身份、多形态、多渠道内容矩阵**；
4. **把文字、图片、视频提升为三个平级的一等生产引擎**；
5. **降低 Skill 的架构地位，改为“模型 + 工具 + 数据 + 规则 + Workflow”的长期结构**。

本版明确：

> **Skill 不再是 AIContentStudio 的核心产品对象，也不再作为长期架构扩展的中心单位。**

模型能力会持续增强。大量以提示词和固定步骤封装的 Skill，可能从“增强能力”逐渐变为限制模型规划与生成能力的历史包袱。

AIContentStudio 的核心应建立在更稳定的对象和契约上：

```text
内容身份
数据与证据
内容项目
创作任务书
内容资产
版本与血缘
渠道适配
审核与授权
发布记录
反馈与学习
```

执行层则保持为：

```text
Model
+ Tool
+ Data
+ Rule
+ Workflow
```

---

# 1. 文档目的

AIContentStudio 未来会持续增加：

- 新的数据源；
- 新模型；
- 新工具；
- 新图片与视频能力；
- 新渠道；
- 新账号；
- 新工作流；
- 新审核规则；
- 新发布方式；
- 新的品牌、角色与内容栏目。

如果这些需求继续以“一个需求对应一段业务代码”的方式累加，系统最终会演变成：

```text
if platform == ...
if content_type == ...
if publisher == ...
if model == ...
if persona == ...
```

或者变成一个由大量 Prompt、脚本、浏览器自动化、模型调用和平台按钮拼接而成的工具集合。

AIContentStudio 不应走向这种形态。

这份蓝图用于长期回答：

- 这个产品最终是什么；
- 产品真正管理的核心资产是什么；
- 内容从哪里来；
- “谁在表达”如何影响内容；
- 图、视、文如何成为平级生产能力；
- 一个主题如何形成多身份、多形态、多渠道内容矩阵；
- 哪些事实可以使用；
- 哪些能力由模型决定；
- 哪些动作必须由确定性工具完成；
- Workflow 应该约束什么、不应该约束什么；
- 人工判断位于哪里；
- 渠道如何适配；
- 最终发布了什么；
- 发布反馈如何成为下一轮内容生产的长期经验。

后续 PRD、OpenSpec 和具体实施方案都应服从本蓝图。

如果某个局部实现与本蓝图冲突，应优先重新检查局部实现，而不是为了保留已有代码去反向修改产品方向。

---

# 2. 产品使命

AIContentStudio 的使命不是：

> 用 AI 帮用户写文章。

也不是：

> 把一篇稿件自动同步到很多平台。

它的使命是：

> **把内部数据、外部信息、长期内容身份、内容策略、AI 创作能力、人工判断、多模态生产、多渠道分发与效果学习组织成一个持续进化的内容智能与生产系统。**

它需要持续回答：

1. 世界发生了什么；
2. 企业内部发生了什么；
3. 什么值得成为内容；
4. 哪些事实可信；
5. 谁应该表达这件事；
6. 这个角色长期怎么看这类问题；
7. 应该对谁说；
8. 应该用文字、图片还是视频表达；
9. 在不同渠道应该如何重新组织；
10. 哪些内容可以公开；
11. 哪些步骤由模型完成；
12. 哪些步骤必须由工具或规则确定性完成；
13. 哪些步骤必须人工判断；
14. 当前内容处于什么状态；
15. 为什么产生当前版本；
16. 最终批准的是哪个完整版本；
17. 最终发布到了哪里；
18. 真实结果如何；
19. 哪些经验应该沉淀；
20. 哪些经验还只是待验证假设。

因此，AIContentStudio 更接近：

> **AI-powered Content Intelligence & Production Platform**

中文可定义为：

> **AI 驱动的内容智能与生产平台**

而不是：

> AI Writer / Auto Publisher / Prompt Library / Skill Library

---

# 3. 一句话产品定义

AIContentStudio 是一个：

> **以可信数据和长期内容身份为基础，从内容机会发现、策划，到图/视/文生产、多身份表达、多渠道适配、审核发布，再到反馈学习的 AI 内容智能与生产平台。**

其中：

- **可信数据**：客观事实必须有来源、有证据、有可追溯边界；
- **长期内容身份**：品牌、角色、账号和栏目拥有长期稳定的定位、受众、表达与观点连续性；
- **图/视/文**：文字、图片、视频是平级的一等内容形态；
- **多身份表达**：同一事件由不同品牌或角色表达时，不应只是换语气，而应形成不同视角和内容；
- **多渠道适配**：渠道不是导出格式，而是独立内容场景；
- **人工可控**：AI 是创作与分析能力，不是最终授权者；
- **持续学习**：发布结果最终应改善下一轮内容生产，但不能未经验证自动篡改长期策略。

---

# 4. 产品北极星：从“内容流水线”升级为“四维内容系统”

V1 主要回答：

> 一条内容如何从 Source 走到最终发布？

V2 在此基础上增加一个更根本的问题：

> **是谁在表达这条内容？**

一条最终内容至少由四个维度共同决定：

```text
                说什么
          Topic / Event / Opportunity
                    │
                    │
      ┌─────────────┼─────────────┐
      │             │             │
      ▼             ▼             ▼
   谁来说         怎么表达        发到哪里
 Identity         Modality         Channel
 品牌/角色        文/图/视频       渠道/账号
```

因此最终内容不是：

```text
Topic → Content
```

而更接近：

```text
Topic / Event
× Content Identity
× Modality
× Channel
→ Content Variant
```

这四个维度必须彼此正交。

特别是：

> **“谁来说”与“发到哪里”必须分离。**

内容身份解决认知和表达差异。

渠道适配解决平台语境、格式和消费方式差异。

不能把两者混成一个 Prompt 参数。

---

# 5. 产品不是什么

## 5.1 不是通用聊天机器人

聊天可以是入口，但聊天不是产品核心。

真正重要的是形成可追踪的业务对象：

```text
Data / Source
→ Evidence
→ Opportunity
→ ContentProject
→ Identity Snapshot
→ Creative Brief
→ Text / Image / Video
→ Channel Variant
→ Review
→ Candidate
→ Approval
→ Delivery
→ Feedback
→ Learning
```

聊天只是创建、修改和操作这些对象的一种界面。

---

## 5.2 不是另一个上游研究系统

量化平台可以继续负责：

- 市场数据；
- 指标；
- 回测；
- 因子；
- 策略计算；
- 专业图表计算。

媒体分析系统可以继续负责：

- 信息抓取；
- 原始新闻；
- 视频/音频；
- 转写；
- 舆情数据；
- 第三方观点。

AIContentStudio 可以接收这些成果，也可以拥有通用 Web 搜索、网页读取和素材发现工具，但不应为了“做内容”而重复建设所有专业上游系统。

长期原则：

```text
Upstream System
      ↓
Connector / Import / Tool
      ↓
AIContentStudio
```

而不是让内容业务代码直接耦合上游数据库。

---

## 5.3 不是纯自动发布工具

发布只是生命周期末端。

如果内容错误，一键发布只是更快地放大错误。

产品核心价值来自：

- 内容机会判断；
- 身份一致性；
- 事实可信；
- 图视文生产；
- 内容资产化；
- 多渠道适配；
- 审核；
- 可控交付；
- 效果学习。

---

## 5.4 不是平台 API 聚合器

平台 API、浏览器自动化、第三方 CLI 都只是最后一公里能力。

平台登录方式变化，不应该迫使内容核心重构。

---

## 5.5 不是 Prompt 仓库

Prompt 是实现细节。

长期需要维护的是：

- 内容身份；
- 内容记忆；
- 数据和证据；
- 创作任务书；
- 内容项目；
- 内容资产；
- 渠道规则；
- Workflow；
- Tool Contract；
- Rule；
- Input / Output Contract；
- 版本；
- 评价结果；
- 发布和反馈血缘。

---

## 5.6 不是 Skill Library

AIContentStudio 不以“拥有多少 Skill”衡量能力。

Skill 可以作为某个外部 Agent Runtime 的实现细节，也可以作为历史兼容层，但不应成为 Studio 的核心领域对象。

以下内容不应因为 Skill 存在而被强制绑定：

- 内容身份；
- 内容状态；
- Workflow 状态；
- 版本；
- 审核；
- 发布授权；
- 内容血缘。

当模型本身已经可以可靠理解目标并调用原子工具时，不应再为了“复用 Skill”强迫模型先进入固定能力脚本。

---

# 6. 产品总体闭环

V2 的产品闭环定义为：

```text
数据
  ↓
发现
  ↓
策划
  ↓
创作
  ↓
适配
  ↓
分发
  ↓
复盘
  ↓
学习
```

完整表达为：

```text
Data & Sources
      ↓
Content Intelligence
      ↓
Opportunity
      ↓
Creative Strategy / Brief
      ↓
Text / Image / Video Production
      ↓
Identity-aware Expression
      ↓
Channel Adaptation
      ↓
Review & Distribution
      ↓
Performance & Feedback
      ↓
Learning & Memory
```

其中“内容身份”不是其中某一步。

它是一条贯穿发现、策划、创作、渠道表达和学习全过程的横向主轴。

---

# 7. Stable Core：长期稳定的内容核心

长期稳定对象不应随着模型、工具或平台频繁变化。

推荐的 Stable Core：

```text
Workspace
Brand
Persona
Account
Series

Source
Evidence
FactPack

Opportunity
ContentProject
CreativeBrief
IdentitySnapshot
Perspective

ContentMasterRevision
ChannelVariant
Document
MediaRevision

CheckReport
Candidate
Approval

DeliveryTarget
DeliveryAttempt
Receipt

Feedback
Insight
LearningCandidate
ContentMemory
```

核心原则：

> **内容资产、身份资产、证据资产和业务状态属于 Studio；执行能力属于可替换层。**

因此：

- 更换模型，历史内容仍然存在；
- 更换 Tool Provider，历史内容仍可解释；
- 更换 Publisher，不影响已批准 Candidate；
- 平台改版，不影响 ContentProject、Evidence 和 ContentMaster；
- 外部 Agent 或 Skill 消失，不影响 Studio 的业务状态；
- 内容身份升级，不应改写历史内容当时使用的 IdentitySnapshot。

---

# 8. Replaceable Capabilities：可替换执行能力

允许快速变化的东西包括：

```text
Model Provider
Prompt / Instruction
Tool Provider
Data Connector
Search Provider
Image Provider
Video Provider
TTS / ASR Provider
Browser Automation
Renderer
Channel Adapter
Publisher
Agent / Planner
Runtime
```

这些能力可以有版本、权限、依赖与状态。

但它们不是内容资产本身。

---

# 9. 内容身份系统：Content Identity

这是 V2 最重要的新增核心之一。

内容身份回答：

> **我是谁，我代表谁，我长期关注什么，我通常从什么角度理解问题，我对谁说，我怎么说，以及什么不能说。**

它不能退化成：

```text
tone = professional
```

也不能只作为某个 Prompt 的一段文本。

内容身份至少包含：

```text
身份定位
目标受众
内容领域
表达风格
视觉语言
长期观点
价值主张
内容边界
风险边界
公开事实边界
```

---

# 10. 内容身份的层级与继承

推荐层级：

```text
Workspace
   ↓
Brand
   ↓
Persona / Role
   ↓
Account
   ↓
Series / Column
```

含义分别是：

## Workspace

组织或个人的总空间。

## Brand

决定长期品牌价值、核心定位、视觉规范和品牌边界。

## Persona / Role

决定“谁在讲话”。

例如：

```text
官方品牌
创始人
技术负责人
产品专家
研究员
编辑部
```

## Account

决定这个角色在哪个平台、面向什么具体用户运营。

## Series / Column

决定该账号长期某一类内容的固定主题、结构和节奏。

下层默认继承上层，只覆盖差异项。

例如：

```text
品牌层：
品牌价值观
视觉规范
禁止事项
核心定位
      ↓
角色层：
身份
专业领域
长期观点
表达方式
      ↓
账号层：
渠道
目标用户
账号定位
运营限制
      ↓
栏目层：
固定结构
内容主题
篇幅
节奏
```

---

# 11. 内容身份与内容记忆必须分离

内容身份回答：

> **我是谁。**

内容记忆回答：

> **我过去表达过什么、发生过什么、学到了什么。**

因此底层必须区分：

```text
Content Identity
        +
Content Memory
```

## Content Identity：稳定层

包括：

- 身份定位；
- 品牌价值；
- 专业领域；
- 目标受众；
- 长期观点；
- 表达方式；
- 视觉语言；
- 内容边界。

## Content Memory：动态层

包括：

- 已发布内容；
- 历史公开观点；
- 高表现内容；
- 低表现内容；
- 受众反馈；
- 渠道经验；
- 编辑修改偏好；
- 已验证策略；
- 待验证经验。

内容生成必须能够知道：

> 当前这条内容使用的是哪个 Identity Version，以及生成时可见的是哪一组 Memory / Strategy Context。

---

# 12. 内容大脑：Content Brain 是产品概念，不是巨型表

“内容大脑”可以作为产品层概念。

一个品牌或角色的 Content Brain 是以下内容的聚合：

```text
Content Identity
+ Content Memory
+ Brand Knowledge
+ Historical Content
+ Audience Understanding
+ Channel Experience
+ Performance Data
+ Strategy Learnings
```

但底层不应创建一个无边界的 `content_brain` 巨型实体。

长期原则：

> **产品上可以是一个大脑，数据模型上必须保持可分解、可版本、可追溯。**

---

# 13. 身份版本与 Identity Snapshot

历史内容不能跟随今天的品牌设置自动改变。

因此每次正式生产应冻结：

```text
IdentitySnapshot
```

至少包含或引用：

```text
brand_version
persona_version
account_profile_version
series_version
voice_version
policy_version
```

任何 Candidate 都必须能够回答：

> 这条内容是在怎样的身份定义下被创作和批准的？

身份更新只影响新的生产，不重写历史版本。

---

# 14. Source：内容从哪里来

Source 包括但不限于：

- 文件；
- URL；
- API；
- 数据平台；
- 内部数据库导出；
- 研究报告；
- 用户手工输入；
- 已有文章；
- 第三方观点；
- 视频/音频转写；
- 项目代码；
- Git 仓库；
- 外部 Agent 产出；
- Web 搜索结果；
- 社交媒体信息；
- 历史内容；
- 内部业务事件。

V2 明确：

> **内部数据与外部互联网信息是平级内容输入。**

这是 AIContentStudio 与普通社媒 Agent 的重要差异。

Source 不等于 Fact。

一个来源可以同时包含：

- 客观事实；
- 作者观点；
- 第三方观点；
- 推测；
- 错误信息；
- 未确认信息。

---

# 15. Evidence 与 FactPack：可信性的基础

AIContentStudio 必须坚持：

> **模型不能因为“创作需要”而自行制造客观事实。**

Evidence 至少应能表达：

```text
内容
来源
时间
主体
口径
可信状态
引用位置
是否允许模型使用
是否允许公开使用
权利状态
```

FactPack 表达某个内容范围内允许作为事实使用的证据集合。

FactPack 一旦冻结：

```text
不可原地修改
```

修改必须产生新版本。

---

# 16. 内容机会系统：Opportunity 不等于热点

V1 对 Topic 的描述偏向“已经决定要写什么”。

V2 在 Topic 之前增加：

> **Content Opportunity / 内容机会**

内容机会可以来自：

```text
互联网热点
新闻
搜索趋势
竞品变化
用户问题
社区讨论
内部数据异常
产品更新
销售变化
客户反馈
研究发现
历史内容表现
运营计划
人工选题
```

系统需要回答：

```text
发生了什么？
为什么值得做内容？
对哪个 Brand / Persona 有价值？
适合什么受众？
时效性多强？
有多少证据？
潜在风险是什么？
```

“热点发现”只是内容机会发现的一种。

---

# 17. ContentProject：内容项目成为业务根对象

V1 中 Topic 是一次内容生产任务的根对象。

V2 升级为：

> **ContentProject / 内容项目**

原因是现实中的“一件事”往往不会只生成一篇文章。

一个内容项目可以包含：

```text
主题 / 事件
证据
内部数据
创作策略
多个身份视角
多个 CreativeBrief
文字成果
图片成果
视频成果
多个渠道版本
素材
审核
发布
效果数据
复盘
学习结果
```

例如：

```text
项目：某 AI 新模型发布
│
├── Evidence / 数据
├── 品牌官方视角
│   ├── 微信文章
│   └── 小红书图文
├── 创始人视角
│   ├── LinkedIn
│   └── X
├── 产品专家视角
│   ├── B站视频
│   └── 抖音短视频
└── Feedback / Learning
```

Topic 仍然存在，但它不再等同于整个项目。

---

# 18. CreativeBrief：创作任务书

正式创作之前，应形成结构化 CreativeBrief。

中文统一称：

> **创作任务书**

它不是 Prompt。

它是整个创作项目的一份业务契约。

建议包括：

```text
project_id
objective
identity
audience
topic
angle
key_message
evidence / fact_pack
required_points
forbidden_points
tone
visual_direction
modality
channels
cta
constraints
references
success_criteria
```

CreativeBrief 是文字、图片、视频共同理解创作目标的上游对象。

---

# 19. Perspective：同一事实允许产生不同身份视角

同一事件不应先生成一篇“中性母稿”，再简单换语气给不同角色。

身份可能改变：

- 选取哪些事实；
- 强调什么；
- 解释顺序；
- 观点；
- CTA；
- 对风险的处理方式。

因此 V2 增加：

> **Perspective / 身份视角**

推荐链路：

```text
Evidence + Opportunity + IdentitySnapshot
                  ↓
              Perspective
                  ↓
             CreativeBrief
```

一个 ContentProject 可以拥有多个 Perspective。

事实边界应一致或可追溯，但观点与表达可以因身份不同而变化。

---

# 20. “同一件事，多种身份表达”是一级产品能力

未来用户不应只说：

> 生成一篇关于这件事的文章。

还应该可以说：

> 让我的 4 个角色分别表达这件事。

系统可以产生：

```text
CEO            → 行业判断
品牌官方        → 官方解读
产品专家        → 产品与用户价值
研究账号        → 数据与竞争格局
```

这不是“洗稿”。

它依赖：

```text
不同 Identity
+ 不同 Perspective
+ 相同可追溯事实边界
```

这是 AIContentStudio 相对于简单“一稿多发”工具的重要能力。

---

# 21. 图、视、文必须成为三个平级 Production Engine

V2 明确：

```text
Text
Image
Video
```

是三个一级内容模态。

不能继续默认：

```text
文章
+ 配图
+ 视频附件
```

应该是：

```text
                CreativeBrief
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      Text Engine  Image Engine  Video Engine
```

每种形态都可以是：

- 主内容；
- 另一形态的派生；
- 组合内容的一部分。

例如一个 ContentProject 可以只产出视频，也可以只产出图组，也可以同时产出三种。

---

# 22. Text Production：文字生产

文字生产至少覆盖：

```text
长文章
短文章
研究解读
评论
社交帖
Thread
脚本
旁白
标题
摘要
Newsletter
FAQ
```

文字资产必须版本化，并保留：

```text
identity_snapshot
evidence_refs
brief_version
model/runtime
editor_changes
revision
```

---

# 23. Image Production：图片生产

图片不是“文章附件”，而是独立内容生产体系。

包括：

```text
AI 生成图片
全网素材发现
用户上传素材
截图
图表
信息图
卡片
封面
缩略图
配图
图片编辑
```

每个素材必须保留：

```text
origin
source_url / source_ref
rights
license
public_use_allowed
model_processing_allowed
generation_info
prompt
revision
hash
```

---

# 24. Video Production：视频生产

视频是一等内容形态。

包括：

```text
选题与结构
视频脚本
镜头规划
素材检索
AI 视频生成
图片转视频
旁白
TTS
字幕
音乐
剪辑
重构比例
长转短
封面
发布版本
```

视频需要自己的版本与血缘，而不能只在最终导出时保存一个 `final.mp4`。

建议至少可追踪：

```text
script_revision
shot_plan
source_assets
timeline_revision
voice_revision
subtitle_revision
render_revision
final_hash
```

---

# 25. ContentMasterRevision：母版仍存在，但不再是全局唯一母稿

V1 规定所有平台稿原则上从一个 MotherRevision 派生。

V2 需要修正。

当同一事件由多个身份表达，并同时存在图、视、文三种形态时：

> **一个全局唯一 MotherRevision 会变成错误抽象。**

V2 改为：

> **ContentMasterRevision / 内容母版版本**

它属于：

```text
ContentProject
× Perspective / Identity
× Modality
```

例如：

```text
项目：AI 新模型
│
├── CEO Perspective
│   ├── Text Master
│   └── Video Master
│
└── Brand Perspective
    ├── Text Master
    ├── Image Story Master
    └── Video Master
```

平台版本从对应的 ContentMasterRevision 派生。

因此真正共享的不是“一篇母稿”，而是：

```text
Evidence
+ Project Intent
+ Identity Snapshot
+ CreativeBrief
```

---

# 26. 内容矩阵：Identity × Modality × Channel

V2 把“一稿多平台”升级为：

> **内容矩阵**

一个 ContentProject 的输出空间可以表示为：

```text
Identity
× Modality
× Channel
```

例如：

```text
                  一个事件
                     │
         ┌───────────┼───────────┐
         │           │           │
      品牌官方       CEO       产品专家
         │           │           │
       图/文        文/视频       视频
         │           │           │
     微信/小红书   X/LinkedIn   B站/抖音
```

系统未来可以给出：

```text
这件事适合：
3 个身份
3 种内容形态
5 个账号
建议生产 8 个内容单元
```

内容矩阵不是要求组合全部笛卡尔积。

系统应根据：

- 身份相关性；
- 内容机会；
- 渠道价值；
- 成本；
- 时效；
- 历史表现；

选择合理单元。

---

# 27. Channel：渠道是内容场景，不是导出格式

每个平台都有自己的：

- 用户心理；
- 内容消费方式；
- 内容长度；
- 社区语言；
- 推荐机制；
- 搜索机制；
- 图片/视频习惯；
- 互动方式；
- 发布限制；
- 账号能力。

因此：

> **Channel 不只是 Prompt 中的一个变量。**

但 V2 同时明确：

> **Channel 也不应该拥有一套复制出来的独立内容世界。**

身份、证据和项目在渠道之上。

渠道负责平台语境和适配。

---

# 28. Channel Adapter：渠道适配器

每个渠道应该通过标准 Channel Adapter 描述：

```text
content_forms
constraints
format_rules
media_rules
metadata_rules
preview
validation
capabilities
account_requirements
```

可抽象为：

```text
capabilities()
validate()
adapt()
preview()
render()
```

发布动作由 Publisher / Delivery Capability 负责。

Channel Adapter 解决：

> 内容应该怎样适配到这个平台。

Publisher 解决：

> 最终怎样送到这个平台。

二者不要混在一起。

---

# 29. 身份适配必须先于渠道适配

正确顺序：

```text
事实 / 主题
    ↓
身份与视角
    ↓
内容母版
    ↓
渠道适配
```

而不是：

```text
事实
  ↓
先生成一个平台稿
  ↓
再尝试把语气改成某个角色
```

原因是：

- 身份影响认知和观点；
- 渠道影响表达结构和格式。

这是不同层级的问题。

---

# 30. 模型、工具、数据、规则、Workflow：新的执行核心

V2 不再使用：

```text
Channel
→ Workflow
→ Node
→ Skill
```

作为最重要抽象。

新的执行关系是：

```text
                    Workflow
                       │
              ┌────────┼────────┐
              │        │        │
              ▼        ▼        ▼
            Model     Tool     Human
              │        │
              └────┬───┘
                   ▼
             Data / Context
                   │
                   ▼
                  Rule
```

更准确地说：

```text
Model   负责理解、规划、分析、创作、判断
Tool    负责确定性的外部动作和能力
Data    负责事实、上下文和业务状态
Rule    负责确定性限制、校验和 Gate
Workflow负责状态、依赖、审批、重试和业务过程
Human   负责不可替代的编辑、判断与授权
```

---

# 31. Model：模型负责认知与生成，不负责业务真相

模型适合：

- 理解意图；
- 形成观点；
- 内容规划；
- 结构设计；
- 写作；
- 改写；
- 摘要；
- 多模态理解；
- 语义判断；
- 工具选择；
- 动态规划。

模型不应该成为：

- 事实真源；
- 审批状态真源；
- 发布状态真源；
- 业务版本真源；
- 权限系统；
- 可靠副作用执行器。

---

# 32. Tool：工具应尽量原子化

Tool 用于提供真实世界能力，例如：

```text
search_web
read_url
query_data
read_file
generate_image
generate_video
transcribe
tts
render_chart
edit_image
cut_video
publish_draft
fetch_metrics
fetch_comments
```

Tool 应有明确：

```text
input
output
permissions
side_effect
timeout
error semantics
version
```

工具越原子，模型越能根据当前任务动态组合。

这比堆叠大量场景 Skill 更适合长期演进。

---

# 33. Skill 的长期定位

Skill 不被禁止，但被降级。

它可以存在于：

```text
External Agent Runtime
Legacy Compatibility
Instruction Package
Reference Implementation
Workflow Template Source
```

但不能成为：

```text
ContentProject 的业务真源
Content Identity 的存储
Workflow 状态存储
Candidate 的组成前提
Approval 的绑定对象
```

如果外部 Skill 有价值，应优先拆解它真正包含的东西：

```text
可复用工具
领域知识
规则
模板
工作流
```

再分别进入 Studio 的对应层。

---

# 34. Rule：确定性问题优先确定性解决

Rule 回答：

> 当前结果是否满足明确要求？

例如：

- 是否出现未经 Evidence 支持的新数字；
- 是否缺日期；
- 是否缺封面；
- 是否存在 placeholder；
- 是否遗漏必要声明；
- 是否违反标题限制；
- 是否缺少回测区间；
- 是否超平台限制；
- 是否缺素材权利信息。

原则：

```text
LLM Review ≠ Rule Engine
Semantic Judgment ≠ Deterministic Validation
```

确定性问题优先使用确定性规则。

---

# 35. Workflow：约束业务过程，而不是限制模型思考

Workflow 仍然是关键基础设施。

但它的职责应该是：

- 状态；
- 依赖；
- 执行边界；
- 人工节点；
- Gate；
- 重试；
- 暂停与恢复；
- 副作用；
- 版本；
- 审计；
- stale propagation。

Workflow 不应变成：

> 一套为了让模型“按照固定教程思考”的刚性脚本。

当模型可以在某个 Node 内自主规划时，Workflow 只需要约束：

```text
输入是什么
允许调用什么
输出契约是什么
什么时候算完成
失败怎么处理
是否允许副作用
```

---

# 36. Agent / Planner 的位置

Agent 可以存在。

但 Agent 应处于：

```text
业务对象之上
执行工具之上
Workflow Runtime 之内或之上
```

Agent 可以：

- 理解用户目标；
- 选择 Workflow；
- 规划内容矩阵；
- 选择工具；
- 动态生成执行计划；
- 提议下一步。

但 Agent 不应：

- 独占业务状态；
- 用自己的运行目录替代 Studio 数据库；
- 绕过 Candidate；
- 绕过 Approval；
- 绕过权利和安全规则。

---

# 37. Workflow 必须支持局部调整

真实内容生产必然包含：

- 标题不好；
- 某段需要重写；
- 图片不好；
- 视频某个镜头不好；
- 音频需要重做；
- 规则报警；
- 用户手工改了一段；
- 用户想换模型；
- 用户想更换素材。

因此 Workflow 必须支持：

```text
Rerun Node
Rerun From Here
Manual Edit
Replace Asset
Override Instruction
Switch Model
Switch Provider
```

而不是任何变化都重新跑整条链路。

---

# 38. Derived State 与 Stale Propagation

所有派生结果必须知道自己的输入版本。

例如：

```text
TextMaster
→ FactCheck
→ ImagePlan
→ ChannelVariant
→ Candidate
```

如果 TextMaster 改变：

```text
FactCheck stale
ImagePlan possibly stale
ChannelVariant stale
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
Candidate may remain valid
Content Approval may remain valid
Delivery Authorization changes
```

系统应根据依赖图自动判断。

---

# 39. 人工永远是一等参与者

AIContentStudio 不追求“尽可能去掉人工”。

目标是：

> **把人工判断放到最有价值的位置。**

Human Node 与 Model / Tool Node 地位相同。

例如：

```text
Model Generate
→ Human Edit
→ Rule Check
→ Semantic Review
→ Human Approve
→ Delivery Tool
```

人工不是自动化失败后的补救。

人工是系统正式设计的一部分。

---

# 40. 内容资产必须统一版本化

最终内容不是：

```text
正文
+
附件列表
```

而是结构化资产。

文字可能包含：

```text
Heading
Paragraph
Image
Chart
Quote
Video Embed
CTA
```

视频可能包含：

```text
Script
Shot
Asset
Voice
Subtitle
Music
Timeline
Render
```

图片可能组成：

```text
Cover
Card 1
Card 2
Card 3
...
```

所有组成部分都必须能绑定版本。

---

# 41. Media 必须版本化并具有权利状态

所有素材记录至少包括：

```text
来源
文件 hash
创建时间
rights
license
可存储
可模型处理
可内部使用
可公开使用
生成模型
生成参数
原始版本
编辑版本
```

因此任何历史 Candidate 都应该能够重新构建。

网上找到图片不自动意味着可以公开发布。

用户上传内容也不自动意味着可以发送到第三方模型。

---

# 42. Candidate 是发布前唯一可信对象

Draft 不等于可发布内容。

真正进入发布阶段的是：

> **Immutable Candidate**

Candidate 冻结：

- 身份快照；
- 标题；
- 正文；
- 视频/图片；
- 文档结构或时间线；
- 素材位置；
- 素材顺序；
- 标签；
- 引用；
- 声明；
- 检查结果；
- Workflow Version；
- Model / Provider 信息；
- Instruction Version；
- Candidate Hash。

任何会改变用户最终看到内容的变化，都必须产生新 Candidate。

Approval 永远绑定：

```text
Candidate Hash
```

---

# 43. 审核与发布授权必须分离

两个问题不同。

## Content Approval

> 这份完整内容是否可以对外？

## Delivery Authorization

> 这份已批准内容是否允许发到这个具体账号？

因此：

换账号：

```text
不一定需要重新审核内容
```

改正文、图片、视频或最终元数据：

```text
需要重新检查 Candidate 是否失效
```

这个边界必须长期保持。

---

# 44. Review & Distribution Center 是产品核心

AIContentStudio 最重要的工作台之一不是“生成页面”，而是：

> **审核与分发中心**

它回答：

```text
哪些内容单元已完成？
属于哪个身份？
哪个版本？
哪些渠道已 Ready？
哪些还缺素材？
为什么不能发布？
需要我做什么？
最终批准的是什么？
```

一个 ContentProject 可以显示内容矩阵：

```text
                    微信   小红书   X   LinkedIn   B站   抖音
品牌官方             Ready  Ready   -      -       -    Ready
CEO                   -      -     Ready  Ready     -      -
产品专家              -      -      -      -      Ready  Ready
```

进入具体单元后显示：

```text
身份
CreativeBrief
最终内容
素材
事实状态
规则状态
Workflow 状态
版本
发布能力
Candidate
Approval
```

---

# 45. “一键发布”的产品定义

“一键发布”不意味着：

> 一键公开上线。

正确含义是：

> **一键完成当前平台能力允许的最远安全交付动作。**

长期分为：

```text
COPY_PACKAGE
ASSISTED_DRAFT
AUTO_DRAFT
AUTO_PUBLISH（仅在平台与授权明确支持时）
```

其中任何有公开副作用的能力都必须受明确授权和平台能力验证约束。

---

# 46. Publisher 是最后一公里能力

Publisher 不负责：

- 写内容；
- 修内容；
- 临时换标题；
- 临时生成图片；
- 临时截断正文；
- 偷偷改变已批准格式。

Publisher 接收的是：

```text
Approved Candidate
+
Delivery Authorization
```

并执行明确动作：

```text
create_draft
update_draft
assist_publish
publish
copy_package
```

平台最终格式转换必须发生在 Approval 前，不能在 Publisher 内悄悄改变用户已审核内容。

---

# 47. Publisher Capability 是动态能力

平台支持不能只记录：

```text
supported = true
```

而应按：

```text
Platform
× Account
× Content Form
× Action
× Verification Time
```

记录。

没有真实验证的平台能力不能显示为“已支持”。

---

# 48. 渠道分支必须独立

选择多个平台后：

```text
Platform A 失败
```

不能导致其他分支全部失败。

共享的是：

```text
ContentProject
Evidence
Identity
CreativeBrief
ContentMaster
```

不共享：

```text
执行状态
发布状态
重试状态
远端结果
```

---

# 49. 系统必须支持渐进自动化

平台能力可以按：

```text
Manual
→ Copy Package
→ Assisted Draft
→ Draft Automation
→ Verified Publish
```

逐步提升。

产品不能因为某个平台缺少稳定 API 就放弃该平台。

也不能为了“全自动”牺牲可控性。

---

# 50. Capability Registry：替代 Skill Registry 的长期注册机制

V2 推荐统一 Capability Registry。

至少覆盖：

```text
Model Provider
Tool Provider
Data Connector
Search Provider
Image Provider
Video Provider
Renderer
Channel Adapter
Browser Automation
Publisher
```

Registry 记录：

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
side_effects
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

历史 Run 必须能够解析到实际使用版本。

---

# 51. 外部能力的战略

AIContentStudio 可以大量利用成熟外部能力。

但“利用”不等于把整套外部 Agent 或 Skill 框架变成自己的业务核心。

外部能力可分为：

```text
Tool Provider
External Runtime
Reference Implementation
Data Connector
Model Provider
Renderer / Publisher Adapter
```

接入前至少检查：

- License；
- 凭据；
- 网络请求；
- 文件权限；
- 是否上传私有数据；
- 副作用；
- 自动公开发布；
- 数据存储位置；
- 是否会形成重复发送风险。

原则：

> **外部能力可以替换，Studio 的内容资产与业务状态不能跟着丢失。**

---

# 52. Context 是 Workflow 的数据总线

Workflow Node 不应直接依赖彼此具体实现。

统一 Context 主要传递：

```text
content_project_id
identity_snapshot_id
perspective_id
creative_brief_id
fact_pack_id
content_master_revision_id
channel_variant_id
media_revision_ids
checks_report_id
candidate_id
delivery_target_id
```

Context 传 ID、版本和 Hash。

不要在节点之间复制越来越多的隐式全文状态。

---

# 53. Workflow Engine 的职责必须保持极小

Engine 只负责：

- 加载 Workflow；
- 解析依赖；
- 调度 Node；
- 管理状态；
- 暂停；
- 恢复；
- 重试；
- stale propagation；
- 写运行记录；
- 执行 Side-effect Gate。

Engine 不负责：

- 怎么写公众号；
- 怎么做视频；
- 怎么生成图片；
- 怎么判断一个品牌应该持什么长期观点；
- 怎么发某个具体平台。

这些属于：

```text
Model
Tool
Rule
Channel Adapter
Publisher
Content Identity
```

---

# 54. 默认 Workflow，而不是默认自由画布

底层支持 DAG，不代表普通用户应该设计 DAG。

默认体验更应该是：

```text
发现/选择内容机会
→ 选择要参与的身份
→ 系统建议内容矩阵
→ 用户确认
→ 生产
→ 审核
→ 分发
```

高级模式才允许：

- 增删节点；
- 换模型；
- 换 Provider；
- 调整 Rule；
- 修改 Workflow；
- 自定义执行图。

原则：

> **架构灵活，不代表产品必须复杂。**

---

# 55. 编辑器是 Workflow 的人工节点

用户修改文字、图片、视频时间线后：

```text
new Revision
```

再由系统根据依赖判断派生物失效范围。

不是：

```text
编辑器保存
→ 原地覆盖最终内容
```

每一次关键修改都应可追踪。

---

# 56. 内容状态必须真实

系统禁止使用模糊的：

```text
完成
已发布
成功
```

如果事实并非如此。

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

# 57. Unknown 是合法状态

外部副作用可能出现：

```text
请求超时
但远端可能已经成功
```

此时进入：

```text
Unknown
```

而不是自动重复发送。

原则：

> **外部发布结果未知时，优先核对，不冒险重复副作用。**

---

# 58. 模型是供应商，不是架构

AIContentStudio 不绑定单一模型。

业务对象不存“只有某模型才能理解”的关键状态。

模型选择发生在任务层，例如：

```text
Research
Opportunity Analysis
Longform Writing
Image Understanding
Video Planning
Rewrite
Semantic Review
```

Workflow Node 声明任务目的与输出契约。

Runtime 决定具体模型。

---

# 59. Fact Check 不能完全依赖 LLM

Fact Check 应分层：

```text
Deterministic Check
Semantic Check
Human Review
```

LLM 失败不能默认 pass。

检查未完整执行时应明确：

```text
incomplete
```

---

# 60. 反馈的目标不是做 BI，而是改善下一轮内容生产

Feedback 可以记录：

- 阅读；
- 播放；
- 完播；
- 收藏；
- 点赞；
- 评论；
- 分享；
- 点击；
- 转化；
- 用户反馈；
- 内容满意度；
- 编辑修改；
- 退稿原因；
- 渠道表现。

不同平台指标不强行求和。

真正需要形成的是：

```text
Performance
→ Analysis
→ Insight
→ Learning Candidate
```

---

# 61. Learning Candidate：反馈不能自动篡改长期身份

某一篇内容高流量：

```text
只是观察
```

不能立即变成：

```text
以后所有标题都这样写
```

反馈首先进入：

```text
Learning Candidate
```

可能归类为：

```text
Identity Learning
Audience Learning
Channel Learning
Format Learning
Topic Learning
Workflow Learning
```

经过：

- 多样本验证；
- 人工确认；
- 明确实验；

之后才可以进入：

```text
Content Memory
Strategy Version
Identity Version
Channel Strategy
Workflow Version
```

稳定身份的修改尤其需要谨慎。

---

# 62. 长期观点连续性

内容身份系统必须解决一个普通“品牌语气 Prompt”解决不了的问题：

> **长期观点是否连续。**

系统应能够知道：

- 这个角色过去公开说过什么；
- 哪些观点属于长期观点；
- 哪些只是当时事件判断；
- 当前稿件是否与历史观点发生明显冲突；
- 冲突是合理更新，还是生成漂移。

系统不应强行禁止观点变化。

但应该让用户知道：

> 这是一次新的观点变化，而不是模型无意识地产生了人格断裂。

---

# 63. 权利是内容系统的一部分

文本、图片、视频、音频都需要区分：

```text
可存储
可模型处理
可内部使用
可公开使用
```

这些是不同权限。

尤其是全网素材发现能力，必须记录：

```text
origin
rights
license
source
usage_scope
```

“能搜索到”不等于“能发布”。

---

# 64. Control Plane 与 Execution Plane

长期明确：

```text
AIContentStudio = Content Control Plane
Execution Runtime / Model / Tools / Browser = Execution Plane
```

Control Plane 决定：

```text
做什么
代表谁做
使用什么数据
使用什么版本
能不能做
当前结果是什么
下一步是什么
能不能公开
```

Execution Plane 负责：

```text
具体怎样执行
```

外部 Runtime 可以更换。

Studio 的业务状态不能只存在某个 Runtime 工作目录里。

---

# 65. 为什么仍然需要 Content Harness

虽然 V2 降低了 Skill 的地位，但 Content Harness 思想仍然成立。

普通 Workflow Engine 主要关心：

```text
任务有没有执行
```

Content Harness 还必须关心：

```text
代表哪个身份
使用了哪些事实
使用了哪个 Brief
使用了哪个版本
文字/图片/视频是否属于同一 Candidate
哪些 Rule 执行过
谁修改过
谁批准
最终交付了什么
反馈回到了哪里
```

因此核心始终高于普通 DAG。

---

# 66. 长期产品工作区

V2 建议形成四个主要工作区。

## 66.1 Intelligence Workspace / 内容智能工作区

解决：

```text
发生了什么
什么值得做
证据是什么
```

包括：

- Data；
- Source；
- Evidence；
- FactPack；
- Opportunity；
- Research；
- Internal Signal；
- External Signal。

## 66.2 Identity & Brain Workspace / 内容身份与大脑

解决：

```text
我是谁
我代表谁
我长期怎么表达
过去学到了什么
```

包括：

- Brand；
- Persona；
- Account；
- Series；
- Content Identity；
- Content Memory；
- Historical Viewpoints；
- Audience Learning；
- Strategy Learning。

## 66.3 Content Project Workspace / 内容项目工作区

解决：

```text
这件事怎么变成内容
```

包括：

- ContentProject；
- Perspective；
- CreativeBrief；
- Content Matrix；
- Text；
- Image；
- Video；
- ContentMaster；
- ChannelVariant；
- Editor；
- Asset。

## 66.4 Review & Distribution Workspace / 审核与分发工作区

解决：

```text
能不能发
发到哪里
最终发了什么
效果如何
```

包括：

- Preview；
- Checks；
- Candidate；
- Approval；
- Delivery；
- Receipt；
- Feedback；
- Learning Candidate。

---

# 67. 设置页不是业务中心

模型、Provider、渠道账号、Connector 和 Runtime 配置应集中管理。

但日常生产不应要求用户频繁进入 Settings。

身份、渠道和运行环境应该被 ContentProject / Workflow 自动引用。

用户面对的是内容业务，而不是基础设施拼装。

---

# 68. 可观察性

每次内容生产必须能回答：

```text
哪个 ContentProject？
哪个 Opportunity？
哪个 Identity Snapshot？
哪个 Perspective？
哪个 CreativeBrief？
哪个 FactPack？
哪个 ContentMasterRevision？
哪个 Channel Variant？
哪个 Workflow？
哪个 Workflow Version？
哪个模型？
哪些 Tool / Provider？
哪个 Instruction Version？
哪些 Media？
哪些 Rule？
谁修改？
谁审核？
哪个 Candidate？
发布到哪个账号？
最终 Receipt？
反馈是什么？
形成了什么 Learning Candidate？
```

如果无法回答，说明运行链缺乏可追溯性。

---

# 69. 成本与性能原则

AIContentStudio 不追求每一步都使用最强模型。

应按任务分层：

- 简单 transform 用代码；
- 确定性判断用 Rule；
- 简单分类可用小模型；
- 复杂写作使用更强模型；
- 复杂图像/视频使用对应多模态模型；
- Research 使用适合搜索与工具调用的模型。

原则：

> **能确定性完成的事情，不交给生成式模型；能让模型自主完成的认知任务，也不要被多余 Skill 人为束缚。**

---

# 70. 测试战略

测试至少分为五层。

## Unit

测试：

- Rule；
- Contract；
- Registry；
- Adapter；
- Renderer；
- 状态迁移；
- 继承与版本。

## Identity Golden

测试：

- 品牌身份保持；
- Persona 差异；
- 历史观点连续性；
- 内容边界；
- 不同身份对同一事件是否产生合理差异。

## Content Golden

测试：

- 事实保持；
- CreativeBrief 遵循；
- Text / Image / Video 方向一致；
- Channel Adaptation；
- 风格质量。

## Integration

测试：

```text
Opportunity
→ ContentProject
→ Identity
→ Brief
→ Production
→ ChannelVariant
→ Candidate
```

## Real Platform

真实账号验收：

```text
Approved Candidate
→ Delivery
→ Read Back / Human Verify
```

只有最后一级通过，相关 Publisher Capability 才能标记为 verified。

---

# 71. 向后兼容原则

系统演进必须保证：

- 旧内容可读；
- 旧版本可解释；
- 历史 MotherRevision 可以迁移映射为 ContentMasterRevision，而不伪造历史身份信息；
- 没有历史 IdentitySnapshot 时必须明确 unknown / legacy，而不是补造；
- 不通过迁移伪造新证据；
- 不把历史内容自动标为已审核；
- 新规则不倒灌修改历史事实；
- 新内容身份不能自动重写历史内容的身份。

---

# 72. 安全边界

所有外部执行能力都应视为：

```text
Untrusted Capability
```

包括：

- 第三方 Tool；
- MCP；
- Browser Automation；
- CLI；
- Plugin；
- Web Content；
- External Agent；
- Legacy Skill Runtime。

原则：

```text
最小权限
显式授权
凭据隔离
运行审计
副作用确认
数据出境可见
```

---

# 73. 技术实现原则：模块化单体优先

AIContentStudio 当前仍适合：

```text
Modular Monolith
```

逻辑模块边界可以清晰划分为：

```text
identity
intelligence
evidence
projects
production
assets
channels
workflow
review
delivery
feedback
learning
```

插件化和 Provider 化是：

```text
逻辑边界
注册机制
依赖接口
版本契约
```

不是微服务数量。

只有真正存在独立扩缩容、安全隔离、不同运行环境或独立失败域时，再拆服务。

---

# 74. 总体架构

```text
┌──────────────────────────────────────────────────────────────┐
│                     Internal / External Data                  │
│  DB / API / Files / Reports / Web / News / Social / Media   │
└──────────────────────────────┬───────────────────────────────┘
                               │
                    Connector / Tool / Import
                               │
                ┌──────────────▼──────────────┐
                │     Evidence & Knowledge     │
                │ Source / Evidence / FactPack │
                └──────────────┬──────────────┘
                               │
                ┌──────────────▼──────────────┐
                │      Content Intelligence    │
                │ Opportunity / Trend / Signal │
                └──────────────┬──────────────┘
                               │
                ┌──────────────▼──────────────┐
                │        Content Project       │
                └──────────────┬──────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                                           │
         ▼                                           ▼
┌──────────────────────┐                  ┌──────────────────────┐
│   Content Identity    │                  │   Creative Strategy   │
│ Brand / Persona /     │─────────────────▶│ Perspective / Brief  │
│ Account / Series      │                  └──────────┬───────────┘
└──────────┬───────────┘                             │
           │                                          │
           │                            ┌─────────────┼─────────────┐
           │                            ▼             ▼             ▼
           │                        Text Engine   Image Engine   Video Engine
           │                            │             │             │
           │                            └─────────────┼─────────────┘
           │                                          │
           │                                  Content Masters
           │                                          │
           │                                  ┌───────▼────────┐
           └─────────────────────────────────▶│ Content Matrix  │
                                              │ Identity ×      │
                                              │ Modality ×      │
                                              │ Channel         │
                                              └───────┬────────┘
                                                      │
                                              Channel Adapters
                                                      │
                                              Channel Variants
                                                      │
                                      ┌───────────────▼───────────────┐
                                      │ Review & Distribution Center  │
                                      │ Checks / Preview / Candidate  │
                                      │ Approval / Authorization      │
                                      └───────────────┬───────────────┘
                                                      │
                                                Delivery Router
                                                      │
                             ┌────────────────────────┼───────────────────────┐
                             ▼                        ▼                       ▼
                         Auto Draft              Assisted Draft          Copy Package
                             │                        │                       │
                             └────────────────────────┼───────────────────────┘
                                                      ▼
                                                   Receipt
                                                      │
                                                   Feedback
                                                      │
                                         Performance / Insight
                                                      │
                                             Learning Candidate
                                                      │
                                ┌─────────────────────┴────────────────────┐
                                ▼                                          ▼
                         Content Memory                              Strategy Update
                                │                                          │
                                └──────────────→ Future Projects ←──────────┘
```

横向基础设施：

```text
Workflow Engine
Model Runtime
Tool Runtime
Rule Engine
Capability Registry
Version / Lineage
Permissions / Audit
Observability
```

---

# 75. 核心架构不变量

未来开发必须保护以下不变量。

## 不变量 1：事实不因重新生成而漂移

客观事实必须绑定 Evidence / FactPack。

## 不变量 2：历史版本不能被覆盖

内容、身份、素材、规则、Candidate 都必须可追溯。

## 不变量 3：历史内容必须绑定当时的身份版本

今天修改 Persona，不能改变昨天是谁说的。

## 不变量 4：ContentProject 是完整内容工程的业务容器

文章、图片、视频、渠道稿和反馈不能散落成无关联对象。

## 不变量 5：图、视、文是平级一等内容形态

任何一种都可以成为主内容。

## 不变量 6：同一事件的不同身份表达必须共享可追溯事实边界

允许观点不同，不允许事实来源失控。

## 不变量 7：身份适配与渠道适配必须分离

“谁来说”和“在哪里说”是两个独立维度。

## 不变量 8：ContentMasterRevision 必须绑定身份与模态

不再假设全项目只有一个全球唯一母稿。

## 不变量 9：文字、图片、视频及最终元数据必须属于一个可批准 Candidate

不能只审核正文、发布时再换素材。

## 不变量 10：Approval 必须绑定完整 Candidate Hash

审批不能绑定模糊“当前稿件”。

## 不变量 11：内容审批和发布授权必须分开

换账号和改内容不是同一种变化。

## 不变量 12：Publisher 不允许临发布时修改已批准内容

最后一公里不能偷偷改变成品。

## 不变量 13：外部发布结果未知不能自动重复副作用

Unknown 是合法状态。

## 不变量 14：Human 是一等 Workflow 参与者

人工不是异常兜底。

## 不变量 15：模型、Tool Provider 和外部 Runtime 可替换

业务状态不能依赖某一个执行框架。

## 不变量 16：Skill 不是核心业务依赖

外部 Skill 消失不能让历史内容无法解释。

## 不变量 17：没有真实验证的平台能力不能显示为已支持

Capability 必须基于真实验证。

## 不变量 18：新增平台原则上不修改 Workflow Engine

新增渠道主要通过 Adapter / Renderer / Publisher / Rule 扩展。

## 不变量 19：反馈不能未经验证自动改写长期身份

Learning 必须经过验证或人工确认。

## 不变量 20：Content Brain 是聚合概念，不是不可拆解的黑盒状态

长期资产必须可版本、可引用、可审计。

---

# 76. 新平台接入决策框架

增加任何新渠道时，不应该先问：

> 我们要不要支持它的 API？

应该先问：

```text
这个平台值得生产什么内容？
有哪些 Content Forms？
对应什么用户？
哪些 Identity 适合在这里表达？
内容结构有什么不同？
需要哪些 Media？
Channel Adapter 需要描述什么？
Renderer 怎么做？
有哪些 Rule？
可以做到哪一级 Delivery？
```

然后才决定 API、浏览器自动化或手工包。

---

# 77. 新工具 / Provider 接入决策框架

增加执行能力时，需要回答：

1. 它解决什么原子能力；
2. 是否已有相同 Tool；
3. 输入是什么；
4. 输出是什么；
5. 是否有副作用；
6. 是否会读取敏感信息；
7. 是否访问网络；
8. 数据会发到哪里；
9. License 是什么；
10. 如何版本化；
11. 如何测试；
12. 失败语义是什么；
13. 是否能被另一个 Provider 替换。

如果一个外部 Skill 实际只是几个工具加指令，应优先拆成这些稳定能力。

---

# 78. 新 Workflow 设计原则

每个 Workflow 应该：

- 明确输入；
- 明确最终产物；
- 明确身份上下文；
- 明确 Evidence 边界；
- 节点数量适度；
- 可局部重跑；
- 有确定性 Gate；
- 人工节点位置合理；
- 不隐藏副作用；
- Publisher 不在 Approval 前；
- Publisher 不修改正文；
- 不在运行中偷偷切换 Provider 最新版本；
- 给模型足够的任务内自主空间；
- 不为了复用历史 Skill 而增加无意义步骤。

---

# 79. 产品演进顺序

每增加一个重要能力，优先顺序应为：

```text
1. 明确用户价值与蓝图位置
2. 定义业务对象和边界
3. 定义身份 / 数据 / 权利上下文
4. 定义输入输出 Contract
5. 定义 Tool / Provider / Adapter 能力
6. 放入 Workflow
7. 增加 Review / Observability
8. 增加 Feedback / Learning
9. 最后提高自动化程度
```

而不是：

```text
先写一个自动脚本
再想怎么管理它
```

---

# 80. AIContentStudio 的长期竞争力

真正长期有价值的不是：

- 某个 Prompt；
- 某个模型；
- 114 个 Skill；
- 某个平台接口；
- 某个自动化脚本。

这些都会快速变化。

真正的长期资产是：

```text
可信证据体系
内容身份体系
长期观点与内容记忆
内容项目与内容矩阵
图/视/文资产体系
版本与血缘
渠道适配模型
审核历史
发布记录
效果反馈
经过验证的策略经验
```

AIContentStudio 的壁垒应来自三个特别明确的方向：

## Data Native

内部数据与外部信息都是一等输入。

## Multi-modal Native

图、视、文是三个平级 Production Engine。

## Identity & Channel Native

系统同时理解：

```text
谁在说
说什么
用什么形式说
在哪里说
```

---

# 81. 产品战略总结

AIContentStudio 的长期方向不是：

> 支持越来越多平台。

也不是：

> 集成越来越多 AI 工具。

更不是：

> 收集越来越多 Skills。

真正方向是：

> **建立一个以内容身份、可信数据和内容资产为稳定核心，以模型和工具为可替换执行能力，可以持续完成发现、策划、图视文生产、多身份表达、多渠道适配、审核分发和学习的内容智能系统。**

最终应该具备：

```text
数据可追溯
事实可信
身份稳定
观点连续
内容可版本
图视文平级
工作流可编排
模型可替换
工具可替换
人工可介入
局部可重跑
多身份可表达
多渠道可适配
发布动作可控
结果可验证
反馈可沉淀
经验可学习
```

---

# 82. 最终产品北极星

如果未来面对复杂需求不知道如何取舍，回到这一句话：

> **AIContentStudio 不是替用户自动生成更多内容，而是让一个品牌、角色或组织能够基于可信数据和长期内容身份，把值得表达的事情持续转化为高质量的图、视、文内容，并在不同渠道正确表达、可控发布、持续学习。**

技术层面的另一句约束是：

> **稳定的是身份、数据、内容资产、版本、审核和反馈；变化的是模型、工具、渠道实现和执行技术。**

产品层面的最终闭环是：

```text
Data
  ↓
Intelligence
  ↓
Identity
  ↓
Content
  ↓
Distribution
  ↓
Learning
  └──────────────→ Future Content
```

这就是 AIContentStudio V2 的长期产品与架构蓝图。


---

# 83. Capability 版本冻结

任何影响可复现性的执行能力都不能在历史 Workflow 中只引用：

```text
latest
```

而应冻结到可以解释的版本或能力快照，例如：

```text
model_provider_version
tool_provider_version
channel_adapter_version
renderer_version
publisher_version
workflow_version
instruction_version
```

升级流程应遵循：

```text
Install / Discover
→ Test
→ Vet
→ Activate
→ Publish New Workflow / Runtime Version
```

历史 Run 继续引用历史版本。

如果外部 Provider 无法提供稳定版本号，Studio 至少需要记录：

```text
provider
model / capability name
resolved configuration
verified_at
request contract version
```

保证未来能够解释差异来自哪里。

---

# 84. Runtime Profile 与 Run Override

V2 仍然保留“运行配置分层”的思想，但不再以 Skill 配置为中心。

Runtime Profile 可以包含：

```text
model routing
tool providers
image provider
video provider
search provider
browser runtime
timeouts
retry policy
sandbox
cost policy
```

推荐优先级：

```text
System Defaults
↓
Workspace Runtime Policy
↓
Workflow
↓
Account / Channel Constraints
↓
Run Override
```

用户在某一个 ContentProject 或某一次 Run 中临时：

- 换模型；
- 换图片 Provider；
- 换搜索工具；
- 调整 Instruction；
- 调整超时；
- 替换某个工具；

默认只影响：

```text
当前 Run / 当前内容单元
```

不能偷偷改变全局。

如果用户希望长期生效，应显式提升为：

```text
Save as Runtime Preference
Publish New Workflow Version
Update Channel Strategy
Update Identity / Account Preference
```

具体落到哪一类长期配置，应由修改内容决定。

---

# 85. Review Center 是业务状态的 Projection

Review & Distribution Center 不应建立第二套状态系统。

它只是聚合并投影：

```text
ContentProject
IdentitySnapshot
Workflow Run
ContentMasterRevision
ChannelVariant
Media
Checks
Candidate
Approval
Delivery
Receipt
```

Workflow / Content Core 是执行与业务事实。

Review Center 是人类可操作视图。

任何“审核页显示 Ready，但底层 Candidate 实际失效”的情况，都属于架构错误。

---

# 86. 新增需求的产品决策检查表

未来讨论任何新需求时，应优先回答以下问题。

## 它强化的是哪一层？

```text
Data
Intelligence
Identity
Project
Production
Channel
Review
Delivery
Learning
```

如果无法说明它属于哪里，先不要实现。

## 它创建新的长期业务对象了吗？

如果只是现有对象的另一种表现，不创建重复实体。

## 它应该进入 Stable Core 还是 Replaceable Capability？

与身份、证据、内容资产、版本、审批相关的长期业务状态优先进入 Core。

经常变化的模型、工具、平台实现优先进入 Capability。

## 它会不会破坏身份一致性？

如果内容代表某个 Brand / Persona，对外前必须能解释使用了哪个 IdentitySnapshot。

## 它会不会破坏事实边界？

任何新增生成能力都不能绕过 Evidence / FactPack 原则。

## 它改变最终 Candidate 吗？

如果改变用户最终看到的内容，需要新 Candidate 或重新判断 Approval 有效性。

## 它产生外部副作用吗？

如果会，需要：

```text
Authorization
Idempotency Strategy
Receipt
Unknown State
Audit
```

## 它能否局部重跑？

不能时，需要重新检查依赖边界是否过粗。

## 它能否被替换？

模型、Tool Provider、Renderer、Channel Adapter、Publisher 原则上必须可替换。

## 它是不是在用 Skill 包装本来可以直接由模型 + 工具完成的事情？

如果是，优先减少中间层。

## 它是否真正改善内容，而只是增加自动化？

自动化不是产品价值本身。

---

# 87. V1 → V2 核心概念迁移表

| V1 概念 | V2 定义 | 修订原因 |
|---|---|---|
| Topic 作为根对象 | `Opportunity + ContentProject` | 一件事可能产生多个身份、多个模态和多个渠道内容 |
| MotherRevision | `ContentMasterRevision`，绑定 Perspective / Identity + Modality | 不再假设整个项目只有一个全局母稿 |
| Voice Profile | Content Identity 的一个组成部分 | “怎么说”只是身份的一部分 |
| Account Profile | Brand → Persona → Account → Series 分层身份 | 区分品牌、角色、账号和栏目 |
| Profile | `Content Identity + Content Memory` | 稳定身份与动态经验必须分离 |
| PlatformDraft | `ChannelVariant` | 渠道版本不仅是草稿，还包含结构化适配结果 |
| Skill | 非核心兼容能力 | 避免模型能力被固定 Skill 架构束缚 |
| Skill Registry | `Capability Registry` | 注册真正可替换的 Model / Tool / Provider / Adapter |
| Skill Plugin | Tool / Instruction / Rule / Workflow / External Runtime | 将外部 Skill 拆回其真实构成 |
| Channel → Workflow → Node → Skill | Model + Tool + Data + Rule + Workflow + Human | 形成更长期稳定的执行模型 |
| Mother Content → 多平台 | Content Matrix：Identity × Modality × Channel | 支持“一件事，多身份、多形态、多渠道” |
| Content Workspace | Intelligence + Content Project Workspace | 把机会发现与实际内容工程分开 |
| Production Workspace | Content Project + Runtime Advanced View | 生产不再围绕 Skill 列表组织 |
| 三个工作区 | 四个主要工作区 | 新增 Identity & Brain 以及 Intelligence 的一级地位 |
| Feedback | Feedback → Insight → Learning Candidate → Memory / Strategy | 防止单次指标直接改变全局策略 |
| Brand Voice | Content Identity | 从文风升级为长期认知与表达身份 |

迁移原则：

> **V2 不要求为了概念升级立即重写所有现有数据表。**

技术实现可以渐进迁移。

但所有新增 PRD、OpenSpec、表结构和接口命名，应优先按照 V2 语义设计，避免继续扩大 V1 中已经被修正的抽象。

---

# 88. 蓝图与 PRD / OpenSpec 的关系

本文件定义：

```text
产品哲学
核心对象
架构不变量
系统边界
长期模块关系
```

它不直接定义：

```text
某个页面具体有几个按钮
某个版本必须实现哪些字段
某个 Sprint 的开发任务
某个 API 的最终 Schema
```

后续关系应保持：

```text
North Star / Blueprint
        ↓
Domain Model
        ↓
System Architecture
        ↓
Version Scope
        ↓
PRD
        ↓
OpenSpec
        ↓
Implementation
```

如果后续 PRD 为了局部便利重新引入：

```text
Skill 作为核心业务对象
全局唯一 MotherRevision
品牌 Voice = 一个 Prompt
图像 = 文章附件
视频 = 二级能力
渠道 = 输出格式
反馈 = BI 看板
```

应视为与本蓝图冲突，需要重新评审。

---

# 89. V2 蓝图最终判断标准

未来可以用以下问题判断产品是否仍在正确方向：

```text
我们是否越来越理解“谁在说”？
我们是否越来越理解“什么值得说”？
我们是否能证明“依据什么说”？
我们是否能用图、视、文选择最合适的表达？
我们是否针对渠道真正重新表达，而不是复制？
我们是否知道最终批准和发布的准确版本？
我们是否能从结果中形成可靠经验？
模型和工具升级时，核心内容资产是否仍然稳定？
```

如果答案持续是“是”，AIContentStudio 就在向正确的长期形态演进。

如果系统的主要增长指标变成：

```text
又增加了多少 Prompt
又增加了多少 Skill
又接了多少自动化脚本
```

则说明架构和产品方向正在偏离 North Star。
