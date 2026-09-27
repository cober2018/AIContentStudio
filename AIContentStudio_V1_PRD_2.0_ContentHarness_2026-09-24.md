# AI Content Studio V1 产品需求文档 PRD 2.0

> 产品：AIContentStudio  
> 文档类型：V1 正式产品需求文档  
> 版本：V1 PRD 2.0  
> 日期：2026-09-24  
> 上位文档：`AIContentStudio 完整产品战略与架构 North Star（图 / 文 / 视）`  
> V1 主题：**Text + Image Content Harness Foundation**  
> 产品形态：独立产品、独立代码仓、独立数据库、独立部署  
> 长期定位：图 / 文 / 视一体化、事实驱动、素材驱动、人工可控、插件式 AI 内容生产中心

---

# 0. 文档定位与优先级

本 PRD 定义 AIContentStudio 在 V1 阶段需要完成的产品能力。

V1 不是产品长期边界。

长期产品按照 North Star 建设：

```text
图 / 文 / 视
+
Content Harness
+
Material Library
+
Review & Delivery
```

V1 只选择其中最重要、最能形成完整闭环的一部分率先交付：

```text
文
+
图
+
多平台适配
+
素材中心
+
Workflow / Skill / Rule 基础
+
SEO / Discoverability 基础
+
审核与发布中心
+
可信交付
```

V2 在同一套核心对象与插件体系上增加：

```text
短视频成片
长视频成片
Storyboard
Timeline
TTS
Voice Profile
Digital Human
Video Material
Video Render
Video QC
Video SEO
Video Delivery
```

因此 V1 的设计必须满足一个长期原则：

> **V1 可以不实现视频成片，但不能把系统设计成一个只能容纳文章的产品。**

---

# 1. 产品定义

## 1.1 一句话定义

AIContentStudio V1 是一个：

> **把可信来源与素材组织成多平台“文 + 图”成品，并通过插件式工作流完成生成、优化、审核和交付的 AI 内容生产中心。**

---

## 1.2 V1 要解决的问题

普通 AI 写作工具通常存在以下问题：

- Prompt 每次临时编写；
- 同一事实在不同渠道中漂移；
- 多平台只是简单截断或换标题；
- 图片只是 Prompt 或临时附件；
- 不知道最终批准的是哪一版文字、哪一组图片；
- 平台规则散落在代码和 Prompt 中；
- 某个模型或 Skill 失效后很难替换；
- 修改一处内容后，不知道哪些检查已经失效；
- 自动发布与内容审核混在一起；
- 平台不支持自动发布时，只能手工复制并丢失格式；
- 没有统一的素材资产和权利记录；
- 没有独立的 SEO / 平台搜索优化能力；
- 无法回答“这篇内容到底用哪些事实、Skills、Prompt、素材和版本生成”。

AIContentStudio V1 需要把这些问题统一成一个可管理的内容生产系统。

---

# 2. V1 产品战略

V1 的战略不是：

> “支持尽可能多的平台按钮。”

而是建立一套可以不断扩展平台的共同生产底座。

V1 要完成以下六个战略基础。

## 2.1 可信内容核心

```text
Source
→ Evidence
→ FactPack
→ Topic
→ ContentCore / MotherRevision
```

客观事实必须可追溯。

---

## 2.2 文 + 图真实成品

V1 的最终结果不再是：

```text
文章正文
+
图片 Prompt
```

而是：

```text
实际文字
+
实际图片
+
顺序/位置
+
来源/权利
+
最终排版
```

---

## 2.3 插件式生产

平台差异通过：

```text
Channel
→ Workflow
→ Node
→ Skill / Rule / Provider
```

表达。

不能继续通过核心代码中的大量平台 `if/else` 扩展。

---

## 2.4 人工可控

系统允许：

```text
编辑
局部改写
重跑节点
从节点继续跑
换图
上传图
生成图
调整 Prompt
调整 Skill
```

人工是 Workflow 的一等参与者。

---

## 2.5 审核与交付统一

所有渠道最终汇合到：

> **Review & Publish Center**

不是生成后散落在不同页面和外部工具。

---

## 2.6 渐进自动化

平台交付能力允许逐步升级：

```text
Copy Package
→ Assisted Draft
→ Auto Draft
→ Verified Publish（未来）
```

V1 不要求所有平台全自动。

---

# 3. V1 范围

## 3.1 V1 一级能力范围

V1 包含：

1. Source / Evidence / FactPack；
2. Topic / Content Core；
3. 多平台 Text Artifact；
4. Image Artifact / 图文卡片；
5. Material Library V1；
6. Channel Registry；
7. Workflow 基础；
8. Skill / Rule Registry；
9. SEO / Discoverability V1；
10. 编辑、版本与局部重跑；
11. Review & Publish Center；
12. Immutable Candidate；
13. Content Approval；
14. Delivery Authorization；
15. Auto Draft / Assisted / Copy Package；
16. Delivery Receipt；
17. 最小效果反馈；
18. 现有抖音脚本能力兼容保留。

---

## 3.2 V1 不包含

以下能力属于 V2 或更后续阶段：

- 完整短视频成片自动生产；
- 完整长视频成片自动生产；
- Timeline 视频编辑器；
- TTS 正式生产主链；
- Voice Clone；
- 数字人正式生产主链；
- 自动 B-roll 视频剪辑；
- AI Video 全自动生成主链；
- 完整视频 QC；
- 视频平台自动公开发布；
- 多租户 SaaS；
- 计费与套餐；
- 通用插件市场；
- 完全自由的低代码工作流平台；
- 无人批准的全自动公开发布；
- 自动法律权利判断。

V1 可以输出：

```text
视频脚本
分镜建议
B-roll Brief
字幕文本
```

但必须明确标记：

> 这不是视频成片。

---

# 4. 产品边界

## 4.1 上游系统负责

量化平台负责：

- A 股 / 市场数据；
- 因子；
- 回测；
- 策略统计；
- 图表原始数据；
- 量化研究结果。

媒体采集分析系统负责：

- 新闻；
- 社媒；
- 视频；
- 音频；
- 转写；
- 原始作者；
- 发布时间；
- 第三方观点；
- 舆情数据。

其他系统负责各自专业领域。

---

## 4.2 AIContentStudio 负责

- 接收上游内容；
- 保存来源快照；
- 整理 Evidence；
- 冻结 FactPack；
- 管理 Topic；
- 建立 Content Core；
- 选择渠道；
- 运行渠道 Workflow；
- 调用 Skills / Models / Rules；
- 搜索、生成、上传和管理素材；
- 生成文字和图片成品；
- SEO / 平台发现性优化；
- Fact / Rule / Rights 校验；
- 人工编辑；
- 版本管理；
- 形成最终 Candidate；
- 审批；
- 交付；
- 保存回执；
- 收集最小反馈。

---

## 4.3 明确禁止的耦合

外部系统只能通过：

```text
API
Webhook
File
Connector
Local Git / Approved Interface
```

进入 Studio。

禁止：

```text
Studio 直接依赖其他产品内部数据库结构
```

---

# 5. 用户与角色

V1 主要服务个人 / 小团队内部内容生产。

## 5.1 Editor / Content Operator

负责：

- 选择 Topic；
- 编辑内容；
- 调整素材；
- 重跑；
- 查看 SEO；
- 准备候选成品。

## 5.2 Reviewer

负责：

- 查看事实；
- 查看规则；
- 查看最终排版；
- 查看真实素材；
- 处理 warning；
- Approve / Request Changes。

## 5.3 Admin

负责：

- 模型；
- Channel；
- Workflow；
- Skills；
- Rules；
- Provider；
- Account；
- 权限和运行配置。

## 5.4 System

负责：

- 自动生产；
- 状态管理；
- 校验；
- 版本；
- 依赖失效；
- 交付路由；
- 审计。

---

# 6. V1 内容形态与渠道

## 6.1 长文章

目标渠道：

- 微信公众号；
- 头条号；
- 百家号；
- 知乎文章；
- B站专栏 / 图文；
- 搜狐号；
- 企鹅号；
- 网易号；
- 雪球；
- 掘金。

---

## 6.2 问答

目标：

- 知乎回答。

知乎回答必须使用独立内容形态和 Workflow。

不能把知乎文章直接改标题当作回答。

---

## 6.3 图文

目标：

- 小红书；
- 微博图文；
- 雪球图文；
- 其他支持图文的平台形态。

小红书 V1 必须包含真实有序图片组，而不是图片 Prompt。

---

## 6.4 社交文本

目标：

- X；
- 微博。

X 的不同形态应分别建模：

- single post；
- thread；
- long-form / article style（账号能力允许时）。

---

## 6.5 现有视频脚本兼容

保留：

- 抖音口播脚本；
- Hook；
- scene blocks；
- on-screen text；
- B-roll Brief；
- 估算 SRT；
- estimated duration。

不把其标记为 VideoArtifact Ready。

---

# 7. V1 平台目标矩阵

| 平台 | V1 内容形态 | V1 最低成品 | SEO / Discoverability | 交付策略 |
|---|---|---|---|---|
| 微信公众号 | 长文章 | 富文本/HTML + 实际图片 + 封面 | 标题/摘要/结构 | Auto Draft 优先 |
| 头条号 | 长文章 | 平台稿 + 图片 + 标签 | 推荐/搜索关键词 | Auto/Assisted/Copy 依能力 |
| 百家号 | 长文章 | 搜索型文章 + 图片 | 搜索意图/实体 | Auto/Assisted/Copy |
| 知乎文章 | 知识长文 | 论证型文章 + 素材 | 问题/实体/搜索 | Auto/Assisted/Copy |
| 知乎回答 | 问答 | 直接回答 + 论证 | Question Intent | Auto/Assisted/Copy |
| B站 | 专栏/图文 | 专栏成品 + 图片 | 站内关键词/标签 | Auto/Assisted/Copy |
| 搜狐号 | 长文章 | 资讯/解读稿 + 图片 | 新闻实体/搜索 | Auto/Assisted/Copy |
| 企鹅号 | 长文章 | 完整平台稿 | 平台关键词 | Copy 至少可用 |
| 网易号 | 长文章 | 新闻/观点稿 | 新闻实体/主题 | Auto/Assisted/Copy |
| 小红书 | 图文 | 标题 + 正文 + 有序真实图卡 + 标签 | 站内搜索词 | Assisted/Copy；验证后 Auto |
| X | single/thread | 有序帖子 + 素材 | 实时话题/实体 | Auto/Assisted/Copy |
| 微博 | 短帖/图文 | 文案 + 图片 + 话题 | 热点/话题 | Auto/Assisted/Copy |
| 雪球 | 财经文章/图文 | 数据/观点稿 + 图表/素材 | 股票实体/主题 | Auto/Assisted/Copy |
| 掘金 | 技术文章 | Markdown 技术稿 + 图片/代码 | 技术关键词/搜索 | Auto/Assisted/Copy |
| 抖音 | 脚本（兼容） | Script Package | 标题/话题建议 | Copy Package |

表中的自动能力不是静态承诺。

真实状态按：

```text
Platform
× Account
× Content Form
× Action
× Verified At
```

记录。

---

# 8. 核心业务流程

```text
上游结果 / 用户输入 / 已有原稿
          ↓
       Source
          ↓
 Evidence / Fact Review
          ↓
      FactPack Freeze
          ↓
        Topic
          ↓
 Content Core / MotherRevision
          ↓
     Select Channels
          ↓
 ┌────────┼───────────────┐
 ↓        ↓               ↓
Workflow Workflow       Workflow
A        B              C
 ↓        ↓               ↓
Text / Image Artifacts
 ↓        ↓               ↓
SEO / Rules / Material / FactCheck
 ↓        ↓               ↓
Review & Publish Center
          ↓
 Immutable Candidate
          ↓
       Approval
          ↓
 Delivery Authorization
          ↓
Auto Draft / Assisted / Copy Package
          ↓
        Receipt
          ↓
       Feedback
```

每个平台分支独立运行。

一个平台失败不得回滚其他平台。

---

# 9. Source Library

支持：

- 文本；
- Markdown；
- PDF；
- TXT；
- CSV；
- JSON；
- URL；
- API；
- Connector；
- Local Git；
- 外部 Agent 产出；
- 已有内容导入。

Source 至少保存：

```text
origin
origin_ref
source_url
author
published_at
captured_at
raw snapshot
hash
trust
rights metadata
```

同一来源发生变化时，不允许静默改变历史内容使用的快照。

---

# 10. Evidence / Fact / FactPack

## 10.1 Evidence 类型

V1 至少支持：

```text
objective_fact
event
quote
third_party_opinion
author_opinion
source_excerpt
```

非数值观点不能为了进入 FactPack 而伪装成数值 Fact。

---

## 10.2 FactPack 冻结

FactPack Freeze 后：

- 值不可漂移；
- 日期不可漂移；
- 单位不可漂移；
- 来源定位不可漂移；
- 权利状态可撤销；
- 修改需要新版本。

生成结果永远记录使用的 Evidence Snapshot / FactPack Version。

---

# 11. Topic & Content Core

## 11.1 Topic

至少包括：

```text
title
audience
goal
angle
core_thesis
must_include
forbidden
cta
fact_pack
selected_channels
business_line
product
```

---

## 11.2 Content Core

V1 可以继续复用 / 演进当前 `MotherRevision`，但产品语义上定义为 Content Core 的文本实现。

至少包含：

- 核心事实；
- 核心观点；
- 叙事顺序；
- 作者表达；
- 引用；
- 内容原子；
- 使用素材建议；
- 内容边界。

已有优秀原稿允许：

```text
Import as Content Core
```

不强制重写。

---

# 12. Material Library V1

Material Library 是 V1 一级功能，不是 Article 附件功能。

## 12.1 V1 素材类型

至少包括：

- 图片；
- 图表；
- 截图；
- 封面；
- 图卡；
- Logo / 品牌素材；
- 视频/音频文件可作为 Source/Material 保存，但 V1 不做完整视频制作。

---

## 12.2 V1 素材来源

支持：

```text
Upload
Existing Material
Upstream Import
Web / Image Search
AI Image Generation
Chart Generation
Screenshot
Template Rendering
```

---

## 12.3 Material Candidate

通过全网搜索找到的素材先进入：

```text
Material Candidate
```

而不是直接成为可公开素材。

记录：

```text
source_url
owner / author
captured_at
file_hash
rights_status
attribution
public_use_allowed
model_use_allowed
```

---

## 12.4 素材版本

任何：

- Crop；
- Resize；
- Edit；
- Regenerate；
- 替换；

都创建新 Material Revision。

已批准 Candidate 引用的素材字节不能覆盖。

---

## 12.5 素材搜索

至少支持：

- 标题 / 标签；
- 来源；
- 类型；
- 项目；
- rights；
- 时间；
- 最近使用；
- 使用在哪些内容。

V1 不强制完成高级向量视觉搜索，但数据模型应允许后续扩展。

---

# 13. Text Artifact

Text Artifact 是 V1 核心成品类型。

内部应支持结构化 Document，而不只是一段 Markdown 字符串。

长期 Document Block 至少允许：

```text
heading
paragraph
quote
list
image
chart
code
callout
divider
```

Markdown 可以继续作为可编辑真源之一，但平台排版和 Candidate 必须能保留图片位置与顺序。

---

# 14. Image Artifact

V1 正式支持 Image Artifact。

包括：

- 封面；
- 配图；
- 信息图；
- 数据图；
- 小红书卡片；
- 社交图片。

图卡类至少记录：

```text
card order
canvas size
text
image
layout/template
source material
output bytes
hash
```

仅有图片 Prompt：

```text
不算 Image Artifact Ready
```

---

# 15. Channel Registry

V1 应建立集中 Channel Registry。

不能继续在：

```text
models
router
frontend
workflow
renderer
```

分别维护不同渠道清单。

Channel Profile 至少定义：

```text
channel_key
name
content_forms
default_workflows
rule_sets
seo_profile
renderer
publisher_candidates
media_requirements
```

前端从统一 Registry 读取渠道能力。

---

# 16. Workflow

Workflow 是 V1 一级产品概念。

用户不一定需要自己画 Workflow，但系统内部生产必须以 Workflow 组织。

一个 Channel 可以拥有多个 Workflow。

例如：

```text
xueqiu.market_recap
xueqiu.quant_research
xueqiu.ai_industry

juejin.tutorial
juejin.architecture
juejin.project_log

wechat.deep_article
wechat.quant_review
```

---

# 17. Workflow Node

V1 至少支持以下 Node 类别：

```text
skill
llm
rule
transform
research
material_search
material_select
asset_generate
render
seo
human_review
delivery
publisher
manual_handoff
feedback
```

现有 `generate / fact_check / humanize / censor / approve / export` 等能力可先包装成 built-in Node。

---

# 18. Skill Registry

V1 继续使用现有本地 `SKILL.md` 自动发现能力，并提升为正式能力注册体系。

Skill 至少记录：

```text
name
version
source
path/runtime
description
license
status
capabilities
permissions
verified_at
```

外部 Skill 分为：

```text
Vetted Dependency
External Runtime
Reference Implementation
Custom Studio Skill
```

Studio 不因第三方 Skill 改版而丢失业务状态。

---

# 19. Rule Registry

Rule 与 Skill 必须分开。

Rule 示例：

```text
fact.no_new_number
fact.citation_coverage
media.required_cover
media.order_integrity
media.public_rights
finance.as_of
finance.no_return_guarantee
juejin.code_provenance
seo.required_description
platform.title_limit
```

Rule 输出：

```text
pass
warning
blocker
incomplete
```

未执行或执行失败不得默认为 pass。

---

# 20. SEO / Discoverability V1

SEO 是 V1 独立插件能力。

不能只在 Writer Prompt 里写一句“优化 SEO”。

---

## 20.1 Pre-Production SEO

在平台生成前可以产生：

```text
Search Intent
Primary Queries
Secondary Queries
Entity Map
Topic / Question Map
Content Gap
Outline Suggestions
```

---

## 20.2 Post-Production SEO

对成品产生：

```text
Title Suggestions
Heading Check
Keyword Coverage
Entity Coverage
Description
Tags
Alt Text
Caption
Internal Link Suggestions
Platform Search Issues
```

---

## 20.3 不同平台不同 Profile

示例：

### 百家号

偏：

```text
Query
Entity
Definition
Search Intent
```

### 知乎

偏：

```text
Question
Problem Intent
Entity
Long-tail Search
```

### 小红书

偏：

```text
站内搜索词
收藏型 Query
标题关键词
标签
```

### 雪球

偏：

```text
股票代码
公司实体
行业实体
主题词
```

### 掘金

偏：

```text
技术名词
框架/版本
问题型搜索
```

---

## 20.4 SEO 约束

SEO 不能：

- 修改冻结事实；
- 关键词堆砌；
- 制造夸张结论；
- 偷换标题事实含义。

SEO 修改进入最终 Candidate，必须一起审核。

---

# 21. Platform Adaptation

平台适配不是翻译或截断。

原则：

```text
Facts stay
Core thesis stays traceable
Structure can change
Tone can change
Length can change
Media can change
SEO can change
CTA can change
```

每个平台生成独立 Draft / Artifact Revision。

---

# 22. 重点平台内容规则

本节只定义内容方向，具体规则应版本化进入 Channel Profile / Rule Set。

## 22.1 微信公众号

重点：

- 深度；
- 叙事；
- 作者 Voice；
- 完整结构；
- 封面；
- 章节配图；
- 最终 HTML / Rich Text。

---

## 22.2 知乎文章

重点：

```text
观点
证据
反方
边界
案例
```

---

## 22.3 知乎回答

第一部分必须：

```text
直接回答问题
```

不能把长文原样塞入回答。

---

## 22.4 小红书

从 Content Core 拆出一个明确价值点。

成品必须包含：

```text
title
cover
ordered cards/images
body
tags
search keywords
```

---

## 22.5 雪球

重点内容：

```text
A股复盘
量化研究
行业/公司分析
AI产业观察
```

金融专项必须保留：

```text
as_of
数据来源
样本范围
回测口径
风险
事实/推断区分
```

---

## 22.6 掘金

重点：

```text
AI
Agent
Python/FastAPI
React
量化工程
数据工程
项目建设复盘
```

要求：

- 技术环境清楚；
- 代码来源可信；
- 不虚构 API；
- Benchmark 有口径；
- Limitation 明确。

---

# 23. Editor & Revision

编辑器必须支持：

- Markdown / Rich Text；
- Block / 图片位置；
- Undo / Redo；
- Revision History；
- Diff；
- 选区 AI 改写；
- 标题重写；
- 不覆盖历史。

保存修改：

```text
DraftRevision + 1
```

而不是覆盖旧正文。

---

# 24. Node-level Rerun

V1 必须支持至少两种重跑语义。

## 24.1 Rerun Node

只重新执行当前 Node。

适合：

```text
标题
SEO
Humanizer
某一张图
```

## 24.2 Rerun From Here

从当前节点重新执行后续派生链。

所有重跑必须创建新版本并保留历史。

---

# 25. Stale Propagation

V1 需要建立依赖失效语义。

例如正文修改：

```text
FactCheck → stale
SEO → stale
Render → stale
Candidate → invalid
```

只换图片：

```text
Text FactCheck → valid
Media Check → stale
Render → stale
Candidate → invalid
```

只换账号：

```text
Candidate → valid
Approval → valid
Delivery Authorization → new
```

前端必须明确展示 stale，而不能继续显示旧检查为绿色。

---

# 26. Review & Publish Center

这是 V1 核心工作台。

一个 Topic 下统一展示所有渠道：

```text
公众号         Ready
头条           Needs Review
知乎文章       Ready
知乎回答       Blocked
小红书         Missing Media
雪球           Warning
掘金           Ready
X              Ready
...
```

---

## 26.1 渠道详情

至少包含：

### Final Preview

最终平台呈现预览。

### Editor

正文 / 图卡 / 图片位置。

### Evidence

Fact / Citation。

### Rules

Fact / Platform / Finance / Safety / SEO / Rights。

### Workflow Timeline

每一个 Node 当前状态。

### Version

Content Core / Draft / Material / Workflow / Skill。

### Delivery

当前平台账号具备什么能力。

---

## 26.2 审核中心允许的动作

- Edit；
- Rewrite Selection；
- Rerun Node；
- Rerun From Here；
- Override Prompt；
- Switch Skill；
- Upload Image；
- Search Material；
- Generate Image；
- Replace Image；
- Reorder Image；
- Move Placement；
- Edit Tags；
- Re-run SEO；
- Save Revision；
- Request Changes；
- Approve；
- Deliver。

---

# 27. Candidate

Draft 不是最终发布对象。

V1 正式引入：

> **Immutable Candidate**

Candidate 至少覆盖：

```text
title
canonical body/document
structured content
ordered media hashes
media placement
citations
declarations
SEO metadata
rule/check reports
renderer output
workflow version
skill versions
prompt versions
candidate hash
```

只有：

```text
Candidate Ready
```

才能申请 Approval。

---

# 28. Candidate Ready Gate

至少经过四层。

## 28.1 Content Ready

- 正文完整；
- 必填字段完整；
- 无 stale 必要派生物；
- 无 blocker。

## 28.2 Evidence Ready

- FactCheck 完成；
- 引用有效；
- 无无来源关键事实。

## 28.3 Media Ready

- Required Media 实际存在；
- 非 placeholder；
- 顺序 / placement 有效；
- 权利可公开。

## 28.4 Platform Ready

- Renderer 成功；
- 格式规则通过；
- SEO 必填项完成；
- 平台声明完整。

---

# 29. Approval

Content Approval 绑定：

```text
candidate_hash
```

修改任何以下内容都需要新 Candidate：

- 标题；
- 正文；
- 图片；
- 图片顺序；
- 图片位置；
- 标签（若属于公开载荷）；
- 声明；
- SEO 标题/描述；
- Render 后载荷。

---

# 30. Delivery Authorization

Approval 不等于可以发到任意账号。

DeliveryTarget 至少绑定：

```text
approved_candidate_hash
platform
content_form
account_ref
action
authorization_version
```

更换账号创建新的目标授权。

---

# 31. Delivery Modes

## 31.1 AUTO_DRAFT

平台能力验证通过：

```text
Approved Candidate
→ Publisher
→ Platform Draft
→ remote id
```

公众号是 V1 已有重点路径。

---

## 31.2 ASSISTED_DRAFT

浏览器辅助：

```text
自动填写
自动上传素材
保存草稿或停在提交前
```

需要独立 Capability 验证。

---

## 31.3 COPY_PACKAGE

所有目标渠道必须至少能够退化到 Copy Package。

包中包含：

```text
title
body / rich body
images
image order
image placement
tags
SEO metadata
public citations/declarations
publish guide
manifest
```

必须做到：

> **人工发布但尽量不丢格式、素材和顺序。**

---

# 32. Publisher 原则

Publisher：

- 不重写内容；
- 不修改标题含义；
- 不临时截断；
- 不临时换图；
- 不自动补免责声明；
- 不在 Approval 后改变公开载荷。

如果平台限制要求发生实质变化：

```text
回到 Candidate
→ New Candidate
→ Re-approve
```

---

# 33. Delivery Unknown

远端可能存在：

```text
请求超时
远端已成功
本地未知
```

此时进入：

```text
Unknown
```

不得盲目自动重试。

需要：

```text
Verify / Human Check
```

---

# 34. Feedback

V1 至少支持人工回填：

- URL；
- 发布状态；
- 阅读；
- 点赞；
- 收藏；
- 评论；
- 分享；
- 用户反馈；
- 内容满意度；
- 返工原因。

未知值保持 Unknown，不能用 `0` 代替。

---

# 35. Feedback 与 Learning

反馈不能自动修改全局规则。

进入：

```text
Learning Candidate
```

用户可以确认后将其转化为：

```text
Voice Profile 新版本
Workflow 新版本
SEO Profile 新版本
Rule 新版本
```

---

# 36. 产品信息架构

V1 建议一级导航：

```text
总览
来源与证据
选题 / Content
生产工作台
素材库
审核与发布
内容资产
Workflows
Templates / Profiles
Skills & Plugins
设置
```

---

# 37. Dashboard

显示：

- 当前 Topics；
- 各渠道生产状态；
- Needs Review；
- Blocked；
- Missing Material；
- Delivery Ready；
- Unknown Delivery；
- 最近发布；
- 最近失败。

Dashboard 不使用模糊的：

```text
完成
```

而使用真实阶段。

---

# 38. Content Workspace

核心体验：

```text
Topic
├─ Evidence
├─ Content Core
├─ Channels
│  ├─ WeChat
│  ├─ XHS
│  ├─ Xueqiu
│  └─ ...
└─ Feedback
```

用户可以从 Topic 一处进入整个生产生命周期。

---

# 39. Material Library 页面

至少：

- Grid / List；
- 类型；
- Source；
- Rights；
- Project；
- Usage；
- Search；
- Upload；
- Generate；
- Archive。

点击素材显示：

```text
preview
source
rights
revisions
derived_from
used_by
```

---

# 40. Workflow 页面

普通模式：

- 查看；
- 使用模板；
- 查看运行状态。

高级 / Admin 模式：

- 修改 Node 配置；
- 切换 Skill；
- 切换 Rule Set；
- 修改 Workflow Version。

V1 不要求完整自由拖拽 Workflow Builder 才能发布。

---

# 41. Templates / Profiles

不再只包含 Channel Template。

建议：

```text
Voice Profile
Visual Style Profile
Channel Profile
SEO Profile
Rule Set
Workflow Version
Prompt Version
```

所有已被历史 Run 引用的版本不可原地覆盖。

---

# 42. Plugin Registry

V1 可在现有 Skill Scanner 基础上扩展。

至少统一管理：

```text
Skills
MCP
Publishers
Asset Providers
SEO Providers
Renderers
```

若 V1 实现成本过高，可先统一 Manifest/Registry Contract，再逐类迁入。

关键是避免继续增加第二份平台或插件清单。

---

# 43. Runtime / DSH

DeepSeek Harness / dsh 定位为：

```text
Execution Plane
```

Studio 定位为：

```text
Content Control Plane
```

Studio 保存：

- 业务状态；
- 内容版本；
- 权限；
-审核；
- 交付。

DSH / Skills 保存的运行文件不能成为唯一业务真源。

---

# 44. 数据模型方向

以下是产品语义，不要求一次重命名所有现有数据库表。

## Stable Core

```text
source_document
evidence / fact
fact_pack
topic
content_core_revision / mother_revision
workflow
workflow_run
workflow_step
draft / artifact_revision
material / draft_media
review
content_asset / candidate
delivery_target
delivery_attempt / receipt
feedback
audit_log
```

现有同义对象优先复用。

---

# 45. 状态模型

## 45.1 Artifact / Channel Run

建议：

```text
planned
queued
running
waiting_input
generated
needs_material
needs_review
blocked
candidate_ready
approved
delivery_ready
failed
canceled
```

---

## 45.2 Delivery

建议：

```text
not_authorized
authorized
queued
delivering
draft_created
waiting_human
submitted
published
unknown
failed
canceled
```

没有平台证明时不能写 `published`。

---

# 46. Audit & Observability

每篇成品必须能回答：

```text
哪个 Topic？
哪个 FactPack？
哪个 Content Core？
哪个 Workflow？
哪个 Workflow Version？
哪个 Skill？
哪个 Skill Version？
哪个 Model？
哪个 Prompt？
哪些 Material？
哪个 SEO Report？
哪些 Rules？
谁修改？
谁审核？
哪个 Candidate Hash？
发到哪个 Account？
执行了什么 Action？
最终 Receipt 是什么？
```

---

# 47. Provider 原则

所有 Provider 均通过接口接入。

包括：

- LLM；
- Image Gen；
- Search；
- Chart；
- Publisher。

业务层禁止：

```text
if provider == ...
```

散落在核心逻辑。

---

# 48. 安全与权限

V1 至少保证：

- Secret 不落内容数据库明文；
- 外部 Skill 最小权限；
- Source Prompt Injection 隔离；
- SSRF 防护；
- 文件校验；
- Material Rights；
- Model Use Permission；
- Public Use Permission；
- 审核权限；
- Delivery Authorization；
- Audit Log。

---

# 49. 成本与使用量

V1 至少记录：

```text
LLM usage
Image generation usage（接入时）
Storage
Provider run metadata
```

价格不可用时只显示 usage，不虚构成本金额。

---

# 50. 性能与任务

耗时任务必须支持异步：

- LLM；
- 图片生成；
- Material Search；
- 多渠道生成；
- Export / Render；
- Publisher。

一个渠道失败不能阻塞其他渠道。

---

# 51. 重试原则

内部纯计算 Node 可以根据幂等能力重试。

外部副作用：

```text
Publisher
Remote Draft
```

必须具备明确幂等和 Unknown 处理后才允许自动重试。

---

# 52. V1 核心验收

以下能力通过，才认为 Content Harness Foundation 完成。

## Evidence

1. Source 可以版本化保存；
2. Fact / Evidence 可人工确认；
3. FactPack 可冻结；
4. 历史 FactPack 不随活数据漂移。

## Content Core

5. Topic 可绑定 Evidence；
6. 可导入已有原稿；
7. 平台稿绑定明确 Content Core / Mother Revision；
8. 修改创建 Revision，不覆盖历史。

## Materials

9. 可上传真实图片；
10. 可保存来源和 rights；
11. 可排序和定位图片；
12. 已批准图片不能被覆盖；
13. Image Prompt 不得被标记为真实成品。

## Workflow

14. 多渠道分别形成独立 Run；
15. Node 状态可追踪；
16. 单渠道失败不影响其他渠道；
17. 支持人工 Node；
18. 至少支持 Node 级重跑或等价的局部重生产语义。

## Skills / Rules

19. Skill 可发现、可版本识别；
20. 规则结果区分 pass/warning/blocker/incomplete；
21. 未执行的检查不能默认为通过。

## SEO

22. 至少一个长文平台完成 Pre/Post SEO；
23. 至少一个站内搜索平台完成平台 Discoverability Profile；
24. SEO 修改进入 Candidate。

## Review

25. 审核能看到最终正文；
26. 审核能看到真实有序图片；
27. 审核能看到 Fact / Rule / SEO；
28. 修改后旧检查正确 stale。

## Candidate

29. Candidate Hash 覆盖最终公开载荷；
30. Candidate 只有 Ready 后才能批准；
31. Approval 绑定 Candidate Hash。

## Delivery

32. 内容审批与账号授权分开；
33. 至少公众号 Auto Draft 实际验证；
34. 所有重点渠道至少有可用 Copy Package；
35. Copy Package 保留图片顺序/位置；
36. 结果 Unknown 不自动重发。

## Feedback

37. 可以回填发布链接/状态；
38. 可以保存至少一种真实效果或人工反馈。

---

# 53. 渠道验收模型

不再用：

```text
“30 个 Topic 通过 = 所有 V1 渠道完成”
```

替代为两个层级。

## 53.1 Core V1 Acceptance

验证共同基础：

```text
Evidence
Material
Workflow
Candidate
Review
Delivery
```

---

## 53.2 Platform Capability Acceptance

每个：

```text
Platform × Content Form
```

单独验收。

例如：

```text
wechat.article
zhihu.article
zhihu.answer
xiaohongshu.cards
xueqiu.quant
juejin.tech_article
x.thread
```

每个记录：

```text
content_adaptation_status
media_status
seo_status
renderer_status
delivery_status
verified_at
```

未验的平台不能被汇总为“全渠道已上线”。

---

# 54. 建议首批真实 Golden / Acceptance 样本

为了覆盖不同内容逻辑，至少使用以下真实类型。

## 54.1 量化/A股复盘

重点验证：

- 时间；
- 数值；
- 图表；
- 风险；
- 雪球。

## 54.2 量化研究/因子方法

重点验证：

- 样本区间；
- 回测口径；
- 技术解释；
- 雪球/知乎/公众号。

## 54.3 AI / 技术工程

重点验证：

- 代码；
- 软件版本；
- 架构；
- 掘金/B站/知乎。

## 54.4 产品建设记录

重点验证：

- 作者观点；
- 第一人称；
- 图片；
- 公众号/小红书/X。

## 54.5 第三方媒体观点

重点验证：

- Attribution；
- Quote；
- 外部 Source；
- 权利；
- 搜索/SEO。

---

# 55. V1 发布门槛

V1 可对实际生产开放前，应满足：

- FactPack / Evidence Freeze 可靠；
- Revision 不覆盖；
- Candidate Hash 可重建；
- 实际图片参与审批；
- Material Rights Gate 可用；
- Review 不能绕过 blocker；
- Publisher 不能修改已批准载荷；
- DeliveryTarget 幂等；
- Unknown 状态正确；
- 至少一个真实 Auto Draft 渠道验证；
- Copy Package 可生产使用；
- 数据备份/恢复可用；
- 运行审计可查询。

---

# 56. V1 与当前代码的兼容策略

当前代码已经存在：

```text
FactPack
TopicBrief
Draft Revision
MotherRevision
DraftMedia
ContentAsset
approved_candidate_hash
DeliveryTarget
Workflow
WorkflowRun
WorkflowStep
Skill Scanner
dsh integration
```

新 PRD 原则上复用这些对象。

不创建第二套同义：

```text
ContentItem
AssetCenter
PublishJob
```

除非现有对象语义确实无法扩展。

---

# 57. V1 需要重点改造的现有假设

## 57.1 三渠道硬编码

从：

```text
douyin / xiaohongshu / wechat
```

演进为集中 Channel Registry。

---

## 57.2 Asset Prompt 即成品

必须废止这一产品语义。

Prompt 是中间态。

---

## 57.3 Export 即结束

从：

```text
Review → Export
```

演进为：

```text
Review
→ Candidate
→ Approval
→ Delivery
→ Receipt
```

---

## 57.4 Channel Template 即平台能力

从：

```text
Channel Template
```

演进为：

```text
Channel Profile
+ Workflow
+ Skill
+ Rule Set
+ SEO Profile
+ Renderer
+ Publisher Capability
```

---

## 57.5 全文重跑

逐步升级为 Node / Dependency 粒度重跑。

---

# 58. 为 V2 必须预留但 V1 不实现的接口

V1 数据和 Plugin Contract 必须允许后续增加：

```text
VideoArtifact
Storyboard
Scene
Timeline
Audio Material
Video Material
TTS Provider
Voice Profile
Digital Human Provider
Avatar Profile
Video Renderer
Video QC
Video SEO
Video Publisher
```

但 V1 不需要因此提前建设完整视频编辑器。

---

# 59. V2 的自然扩展路径

V2 应沿用：

```text
Source
Evidence
FactPack
Material Library
Topic
Content Core
Channel
Workflow
Skill
Rule
Review
Candidate
Approval
Delivery
Feedback
```

只增加：

```text
Video Composition
```

而不是建立第二套视频内容中心。

---

# 60. 产品决策原则

后续 V1 开发遇到新需求时，按以下问题判断：

1. 它是 Core 还是 Plugin？
2. 它是否创造了已有对象的同义副本？
3. 它是否会改变最终 Candidate？
4. 它是否需要 Revision？
5. 它是否影响 downstream stale？
6. 它能否局部重跑？
7. 它是否属于 Rule 而不是 AI？
8. 它是否涉及 Material Rights？
9. 它是否产生远端副作用？
10. 它是否应该成为未来 V2 可复用能力？

---

# 61. V1 产品北极星

V1 成功的标准不是：

> “我们支持了多少平台”。

而是：

> **我们已经建立了一套可信、可编辑、可审核、可扩展的文 + 图内容生产 Harness；新的平台主要通过 Channel / Workflow / Skill / Rule / Renderer / Publisher 组合接入，而不是重新修改整个内容系统。**

---

# 62. V1 结束时产品应达到的状态

一个用户应该能够：

```text
导入一份真实来源或已有内容
→ 冻结事实与观点来源
→ 建立一个 Topic / Content Core
→ 勾选多个目标渠道
→ 系统运行各自 Workflow
→ 自动完成平台写作、SEO、规则和素材准备
→ 在同一个审核与发布中心检查
→ 人工修改、换图、局部重跑
→ 形成不可变 Candidate
→ 批准
→ 一键完成该平台允许的最远安全交付
→ 保存回执和反馈
```

同时系统可以清楚解释：

```text
这篇内容从哪里来
用了哪些事实
用了哪些素材
运行了哪个 Workflow
用了哪个 Skill / Model / Prompt
经过哪些 Rules
为什么现在能发布
最终实际交付的是什么
```

如果 V1 达到这个状态，那么 V2 增加视频、TTS、数字人和 Timeline 时，产品只是在同一个 Content Harness 中增加新的 Artifact 与 Provider，而不需要重建产品基础。

---

# 63. 最终原则

AIContentStudio V1 不再定义为：

> “事实驱动的三渠道 AI 写作工具”。

而定义为：

> **AIContentStudio 完整内容操作系统的第一个生产版本：先把“文 + 图”的可信生产、素材、工作流、SEO、审核和交付真正做完整，并建立未来“视”能力能够自然接入的 Content Harness Foundation。**
