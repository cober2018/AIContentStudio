# AIContentStudio Frontend Product Contract V1

> 文档类型：Frontend Product Contract / 前端产品契约  
> 产品：AIContentStudio  
> 基线：North Star V2 + Product Experience Prototype V5  
> 状态：前端实施基线（V5 原型定稿后）  
> 日期：2026-09-27

---

# 0. 文档目的

本文件不是传统 PRD，也不是后端 API 文档。

它用于把已经定稿的 Product Experience Prototype V5 固化为一套可直接进入 React 实施的前端契约，回答：

1. 用户进入 AIContentStudio 后看到什么；
2. 一级导航与页面边界如何划分；
3. 一个 ContentProject 如何从机会、身份、创作任务书进入图 / 文 / 视频生产；
4. 内容矩阵如何增、删、改；
5. 项目级共享素材与系统级通用素材如何被生产工作台使用；
6. Workflow Run 如何同时承担执行、修改和调试；
7. Data Node 与 Data Source Plugin 如何在前端表达；
8. 审阅与发布如何按项目组织多个图 / 文 / 视频 Candidate；
9. 历史发布内容如何进入效果与学习；
10. 后端未来需要提供什么稳定数据对象，但本阶段不先被后端实现牵制。

前端首先以 Mock Data 完整跑通体验；后端在页面与数据契约稳定后再逐步替换 Mock。

---

# 1. 产品体验原则

## 1.1 用户看到业务，不看到底层技术

普通用户的核心语言是：

```text
机会
身份
项目
内容矩阵
素材
图 / 文 / 视频
审阅
发布
效果
学习
```

以下概念默认不进入一级产品体验：

```text
Registry
Provider
Node Runtime
Execution Plane
Prompt Registry
内部 Contract
```

它们只在高级模式、调试器或设置中出现。

## 1.2 ContentProject 是前端业务根对象

页面和导航不以“文章”“视频”“Workflow Run”为业务根对象。

一个项目可以同时包含：

```text
多个身份
×
多个内容形态
×
多个渠道
×
多个内容单元
```

## 1.3 内容身份贯穿生产，而不是账号设置项

内容身份决定：

```text
谁在说
长期怎么看
面对谁说
怎么说
哪些内容不能说
默认如何生产
```

身份必须影响 CreativeBrief、ContentMaster、Workflow Template、生产工作台和最终 Candidate。

## 1.4 图、文、视频是三个平级 Production Engine

三种形态共用：

```text
项目上下文
身份
事实 / Evidence
共享素材
Workflow Runtime
版本体系
Candidate / Approval
```

但编辑体验不能强行统一。

## 1.5 Workflow 是生产工作台的一部分

Workflow 不只是后台配置。

在具体 Content Unit 中，用户应能：

- 看当前单条 Workflow Run；
- 看各节点状态；
- 选中节点查看 Input / Output；
- 单步执行；
- 从当前节点重跑；
- 新增节点；
- 修改节点；
- 删除节点；
- 拖拽调整节点顺序；
- 修改 Data Source；
- 调试后保存为项目覆盖；
- 显式另存为新的“角色 × 内容形态”默认工作流版本。

## 1.6 项目素材池属于项目上下文，不占据生产主画布

生产工作台只提供“项目共享素材”入口。

素材以弹窗 / 抽屉方式进入，避免长期占据主编辑区域。

项目素材包含：

```text
人工上传
Web / 外部采集
系统通用素材引用
Workflow 自动生成的图片
Workflow 自动生成的数据图
Workflow 自动生成的视频片段
Workflow 自动生成的截图
中间成品
最终成品的可复用版本
```

统一以 Asset / AssetRevision 表达。

## 1.7 审阅与发布默认按项目组织

不是把所有 Candidate 平铺成待办列表。

默认层级：

```text
Project
  └─ Content Unit
       └─ Candidate
```

辅助视图可以按状态聚合：Ready / Blocked / Stale / Unknown / Approved。

---

# 2. 一级信息架构

```text
AIContentStudio
│
├── 今日工作台
├── 内容机会
├── 内容项目
├── 生产工作台
├── 审阅与发布
├── 内容身份
├── 素材与知识
├── 效果与学习
└── 设置
```

推荐路由：

| 页面 | 推荐路由 | 说明 |
|---|---|---|
| 今日工作台 | `/` 或 `/home` | 今日值得做什么、待决策、进行中项目 |
| 内容机会 | `/opportunities` | 外部趋势 + 内部信号 + 内容缺口 |
| 内容机会详情 | `/opportunities/:id` | 判断为什么值得做、适合什么身份 |
| 内容项目列表 | `/projects` | 所有 ContentProject |
| 内容项目 | `/projects/:projectId` | 项目总工作区 |
| 生产工作台 | `/projects/:projectId/units/:unitId/production` | 单个内容单元的核心生产界面 |
| 审阅与发布 | `/review` | 默认按项目聚合 |
| Candidate 审阅 | `/review/:projectId/:unitId` | 单个 Candidate 的完整审阅 |
| 内容身份 | `/identities` | Brand / Persona / Account / Series |
| 身份详情 | `/identities/:identityId` | 身份、观点、工作流偏好、记忆 |
| 素材与知识 | `/assets` | 系统级通用素材与知识集合 |
| 效果与学习 | `/learning` | 历史回收、长期分析、学习候选 |
| 设置 | `/settings` | 渠道、模型、数据源插件、规则、团队 |

项目内部状态优先用 URL Query / 子路由保持可分享：

```text
/projects/:id?tab=overview
/projects/:id?tab=brief
/projects/:id?tab=evidence
/projects/:id?tab=assets
/projects/:id?tab=matrix
/projects/:id?tab=versions
/projects/:id?tab=activity
```

---

# 3. 核心用户旅程

## 3.1 主旅程

```text
今日工作台
→ 发现一个值得做的机会
→ 查看机会依据
→ 创建 ContentProject
→ 确认参与身份
→ 完善 CreativeBrief
→ 建立 / 编辑内容矩阵
→ 进入某个 Content Unit
→ 使用角色默认 Workflow
→ 调试 / 覆盖当前 Workflow Run
→ 图 / 文 / 视频生产
→ 使用项目共享素材
→ 形成 Candidate
→ 按项目进入审阅中心
→ 冻结 Candidate
→ 内容批准
→ 发布授权
→ 创建草稿 / 辅助发布 / 发布包
→ 回收实际效果
→ 跨历史内容分析
→ 形成 Learning Candidate
→ 经验证后进入内容记忆 / 策略版本
```

## 3.2 项目内多内容并行

同一个项目可以同时存在：

```text
品牌官方 × 小红书 × 图文
创始人 × LinkedIn × 文字
产品专家 × B站 × 长视频
品牌官方 × 抖音 × 短视频
```

每个 Content Unit 有独立：

- Workflow Run；
- Draft / Master Revision；
- Candidate；
- Review 状态；
- Delivery 状态。

共享：

- Project；
- Evidence / Fact Boundary；
- 项目共享素材；
- CreativeBrief 的公共部分；
- 项目活动记录。

---

# 4. 今日工作台

## 4.1 用户问题

首页只回答三个问题：

1. 今天有什么值得做？
2. 哪些项目正在推进？
3. 现在有什么需要我决定？

## 4.2 页面区块

- 今日内容机会；
- 待我决定；
- 正在推进的 ContentProject；
- 未来 7 天内容节奏；
- 内容身份状态提示。

## 4.3 不做什么

首页不做完整 BI；不放 Workflow 详情；不放模型 / Provider 状态面板。

---

# 5. 内容机会

## 5.1 机会来源

```text
外部趋势
新闻 / 社交媒体
内部业务数据
内部研究 / 文档
历史内容表现
内容缺口
用户问题
产品变化
竞争对手变化
```

## 5.2 每个 Opportunity 至少展示

- 标题；
- 为什么现在值得做；
- 来源类型；
- 主要证据；
- 与品牌 / 身份的相关性；
- 推荐身份；
- 推荐内容形态；
- 推荐渠道；
- 是否与历史内容重复；
- 创建项目入口。

## 5.3 Opportunity 不直接等于 Topic

用户确认后才创建 ContentProject，并生成可编辑 CreativeBrief。

---

# 6. ContentProject 工作区

项目页是项目级 Control Plane 的主要前端投影。

## 6.1 Tab 结构

```text
总览
创作任务书
来源与证据
项目素材
内容矩阵
版本
活动
```

## 6.2 总览

展示：

- 项目目标；
- 当前阶段；
- Content Unit 数；
- 图 / 文 / 视频分布；
- 参与身份；
- 项目风险；
- 待处理问题；
- 推荐下一步。

## 6.3 创作任务书

CreativeBrief 至少包含：

```text
objective
primary_audience
core_message
angle
required_evidence
content_constraints
identity_scope
modality_scope
channel_scope
cta
references
```

公共 Brief 可以被 Content Unit 局部覆盖，但覆盖必须显式可见。

## 6.4 来源与证据

需要区分：

```text
Source
Evidence
Fact Boundary / FactPack
```

用户可以新增来源、查看证据、判断是否允许进入当前项目事实边界。

## 6.5 项目素材

项目页允许管理项目素材，但生产工作台不常驻显示素材列表。

## 6.6 版本

至少记录：

- CreativeBrief 版本；
- Identity Snapshot；
- Evidence / Fact Boundary 版本；
- 各 Content Unit 的 ContentMasterRevision；
- Candidate；
- 关键 Workflow Template / Override 版本。

## 6.7 活动

统一显示：

```text
创建项目
修改 Brief
新增 / 删除 Content Unit
刷新 Data Node
生成素材
人工编辑
冻结 Candidate
内容批准
发布授权
远端结果回写
```

---

# 7. 内容矩阵编辑器

## 7.1 矩阵不是只读推荐表

必须支持完整 CRUD：

- 新增 Content Unit；
- 编辑；
- 删除；
- 复制；
- 启用 / 暂停；
- 批量修改身份 / 渠道 /形态（后续增强）；
- 进入对应 Production Workspace。

## 7.2 Content Unit 基本字段

```ts
interface ContentUnit {
  id: string
  projectId: string
  identityId: string
  identitySnapshotId: string
  modality: 'text' | 'image' | 'video'
  channelId: string | null
  accountId: string | null
  seriesId: string | null
  title: string
  status: ContentUnitStatus
  workflowTemplateId: string | null
  workflowRunId: string | null
  masterRevisionId: string | null
  candidateId: string | null
}
```

## 7.3 创建 Content Unit 时

系统建议：

- 身份；
- 模态；
- 渠道；
- 角色默认工作流。

用户可覆盖。

---

# 8. 内容身份工作区

## 8.1 层级

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

## 8.2 身份详情 Tab

```text
身份
表达与视觉
观点与边界
账号与栏目
工作流偏好
内容记忆
```

## 8.3 身份稳定层

包含：

- 身份定位；
- 目标受众；
- 内容领域；
- 表达风格；
- 视觉语言；
- 长期观点；
- 内容边界；
- 禁止事项。

## 8.4 内容记忆

属于动态层：

- 已发布内容；
- 历史观点；
- 高表现内容；
- 失败案例；
- 用户反馈；
- 已验证学习；
- 最近形成的策略记忆。

## 8.5 工作流偏好

角色可以维护：

```text
Persona × Modality → Default Workflow Template
```

例如：

```text
创始人 × 文字
品牌官方 × 图文
产品专家 × 长视频
```

Account / Series 可以覆盖 Persona 默认值。

---

# 9. Production Workspace：系统最核心工作面

## 9.1 页面结构

推荐保持四层：

```text
A. Context Header
B. Workflow Run Mini Canvas
C. Modality Workspace
D. Contextual Side Panel / Modal
```

### A. Context Header

展示：

- Project；
- 当前 Identity；
- Modality；
- Channel；
- 当前版本；
- 保存版本；
- 提交审阅；
- 项目共享素材入口。

### B. Workflow Run Mini Canvas

必须始终是“当前 Content Unit 的单条工作流”。

它不是全局自由画布。

### C. Modality Workspace

根据 text / image / video 切换完全不同的工作体验。

### D. Side Panel / Modal

承载：

- 节点调试；
- 输入输出；
- 素材选择；
- AI 建议；
- Evidence；
- 历史版本；
- 规则结果。

---

# 10. Workflow Run Mini Canvas 与设计 / 调试器

## 10.1 双模式

### Run Mode

默认模式，用于：

- 看当前执行进度；
- 看节点状态；
- 选节点；
- 查看输入输出；
- 单步执行；
- 从节点重跑；
- 刷新 Data Node；
- 处理等待人工节点。

### Design / Debug Mode

用于：

- 新增节点；
- 修改节点；
- 删除节点；
- 拖拽排序；
- 修改连接关系；
- 修改输入输出映射；
- 修改 Provider / Model / Tool；
- 修改失败策略；
- 修改节点条件；
- 项目内保存覆盖；
- 另存为角色默认 Workflow Template 新版本。

## 10.2 节点类型

```ts
type WorkflowNodeType =
  | 'data'
  | 'ai'
  | 'tool'
  | 'rule'
  | 'human'
  | 'system'
```

### Data Node
读取有版本的数据快照。

### AI Node
负责理解、生成、分析和判断。

### Tool Node
负责原子执行，例如图片生成、转录、渲染。

### Rule Node
确定性检查和 Gate。

### Human Node
人工编辑、确认、批准等显式人工行为。

### System Node
版本冻结、状态转换、Context 操作等系统行为。

## 10.3 拖拽调整

V1 前端至少支持：

- 节点横向 / 纵向拖拽调整顺序；
- 拖拽后即时显示新的执行序列；
- 未保存状态提示；
- 保存前进行基础依赖校验；
- 保留键盘 / 上下移动的替代操作。

后续如演化为真正 DAG，可继续扩展 edge 编辑，但第一阶段不要把 UI 做成通用低代码平台。

## 10.4 调试行为

```text
Run Node
Run From Here
Refresh Data
Inspect Input
Inspect Output
Edit Node
Disable Node
Delete Node
```

任何重跑都必须基于依赖关系更新 Stale 状态。

---

# 11. Data Node 与 Data Source Plugin

## 11.1 Data Node 是独立一等节点

它不能被退化为“Tool Node 换名字”。

Data Node 至少表达：

```text
data_source_plugin
connection
query / selector
input parameters
snapshot policy
snapshot id
lineage
normalized output
last refreshed at
stale impact
```

## 11.2 Data Source Plugin

统一抽象：

```ts
interface DataSourcePlugin {
  key: string
  name: string
  category: string
  connectionMode: string
  supportsSearch: boolean
  supportsQuery: boolean
  supportsSnapshot: boolean
  configSchema: unknown
  resultSchema: unknown
}
```

原型已确定的来源：

```text
量化 / 内部数据平台
媒体分析系统
Notion
Obsidian
通用 API
SQL / Database
```

未来自然扩展：

```text
Google Drive / Docs
飞书
Confluence
Airtable
RSS
企业知识库
其他 Connector
```

## 11.3 数据节点运行规则

```text
连接数据源
→ 执行 Query / Selector
→ 生成 Data Snapshot
→ 标准化 Output
→ 写 Lineage
→ 下游节点消费 Snapshot ID
```

刷新 Data Node 后：

```text
旧 Snapshot ≠ 新 Snapshot
→ 依赖旧 Snapshot 的 Derived State 进入 stale
```

---

# 12. 项目共享素材弹窗

## 12.1 入口

Production Workspace Header 只显示：

```text
项目共享素材 · N
```

点击打开 Modal / Drawer。

## 12.2 素材来源分类

```text
项目上传
Web 采集
系统通用素材引用
内部数据生成图表
AI 生成图片
Workflow 生成截图
Workflow 生成视频片段
Workflow 中间成品
历史项目复用
```

## 12.3 AssetRevision 最小前端契约

```ts
interface AssetRevision {
  id: string
  assetId: string
  projectId: string | null
  type: 'image' | 'video' | 'audio' | 'document' | 'chart' | 'screenshot' | 'data' | 'other'
  sourceType: 'upload' | 'web' | 'system_library' | 'workflow' | 'generated' | 'external'
  generatedByRunId?: string
  generatedByNodeId?: string
  title: string
  previewUrl?: string
  rightsStatus: 'unknown' | 'internal' | 'public_ok' | 'restricted'
  modelProcessingAllowed: boolean
  publicUseAllowed: boolean
  revision: number
  hash?: string
  createdAt: string
}
```

## 12.4 使用方式

同一个 AssetRevision 可以被：

- 文章插图；
- 小红书卡片；
- 视频 B-roll；
- 视频 Overlay；
- 封面；
- 数据图；

共同引用。

引用不复制素材本体。

---

# 13. Text Production Workspace

重点：

- 结构化正文；
- Heading / Paragraph / Quote / Image / Chart；
- 来源引用；
- 插图位置；
- 身份一致性；
- 事实边界；
- 局部重写；
- 版本保存。

文字不是纯 Markdown 文本框，而是最终应能映射为结构化 Document。

---

# 14. Image / Graphic Production Workspace

图文生产需要支持：

- 多卡片 / 多画布；
- 图上文字；
- 图片与文字共同版本化；
- 引用项目共享素材；
- AI 生成图片；
- 数据图表；
- 不同平台尺寸；
- 页面 / 卡片重排；
- 素材权利状态；
- 生成变体。

关键原则：

> 图上的文字也是内容本体，不能当成视觉装饰绕过 Candidate 版本。

---

# 15. Video Production Workspace

至少包含：

```text
脚本
分镜
素材
镜头
配音
字幕
Overlay
预览
时间线
```

V1 不要求完整专业 NLE，但必须围绕内容生产而非单一“生成视频”按钮。

项目共享素材可以直接进入镜头或 Overlay。

---

# 16. Review & Distribution Center

## 16.1 默认按项目

页面第一层：

```text
Project A
  文字 1 / 图文 1 / 视频 2
  待处理 3 / Ready 1

Project B
  ...
```

展开项目后显示 Content Unit。

## 16.2 辅助按状态

```text
待我处理
Ready
Blocked
Unknown
Approved
```

## 16.3 单个 Content Unit 审阅 Tab

```text
预览
改动
检查
发布
```

## 16.4 审阅主链

```text
解决 Blocker
→ Freeze Candidate
→ Content Approval
→ Delivery Authorization
→ Delivery
```

Content Approval 与 Delivery Authorization 在 UI 上必须分开。

## 16.5 重要状态

### Blocked
存在确定性阻断条件，不能批准。

### Stale
上游输入改变，当前派生结果需要重新运行或重新确认。

### Unknown
外部副作用结果无法确认，不能自动重复执行。

---

# 17. 素材与知识

此页面管理系统级通用资产，不等于项目素材弹窗。

包括：

```text
图片
视频
文档
网页
AI 生成
知识集合
权利状态
来源
```

系统素材被项目使用时优先建立引用关系，而不是复制。

---

# 18. 效果与学习

## 18.1 不只分析新内容

必须支持持续回收历年已发布内容。

历史回收范围尽可能包含：

```text
正文
标题
图片
视频
字幕
身份
账号
渠道
发布时间
历史指标
评论
外链
可恢复的生产信息
```

## 18.2 三个前端工作区

```text
历史回收
长期分析
学习候选
```

## 18.3 数据完整度必须可见

旧年份 / 旧平台存在缺失数据时：

- 显示覆盖率；
- 显示置信度；
- 不伪造缺失数据；
- 不把不完整历史样本与当前完整数据直接作无提示比较。

## 18.4 Learning Candidate

任何观察先进入候选，不直接改变身份或策略。

```text
Observation
→ Learning Candidate
→ Evidence Accumulation
→ Human / Rule Validation
→ Strategy / Memory Version
```

---

# 19. 全局前端状态词典

建议统一：

```ts
type WorkStatus =
  | 'draft'
  | 'running'
  | 'waiting_human'
  | 'blocked'
  | 'stale'
  | 'ready'
  | 'candidate_ready'
  | 'approved'
  | 'delivery_ready'
  | 'submitted'
  | 'published'
  | 'unknown'
  | 'failed'
  | 'archived'
```

不要用一个模糊的 `done=true` 覆盖这些语义。

---

# 20. 前端核心数据契约

以下是页面所需要的最小 View Model，不代表最终数据库表。

## 20.1 ContentProjectView

```ts
interface ContentProjectView {
  id: string
  title: string
  status: string
  objective: string
  opportunityId?: string
  briefRevisionId: string
  factBoundaryId: string
  identityIds: string[]
  contentUnits: ContentUnit[]
  assetCount: number
  pendingReviewCount: number
  risks: ProjectRisk[]
  updatedAt: string
}
```

## 20.2 IdentityView

```ts
interface IdentityView {
  id: string
  type: 'workspace' | 'brand' | 'persona' | 'account' | 'series'
  parentId?: string
  name: string
  positioning: string
  audience: string[]
  voiceTraits: string[]
  visualTraits: string[]
  longTermViews: IdentityViewpoint[]
  boundaries: IdentityBoundary[]
  defaultWorkflows: WorkflowPreference[]
  memorySummary: IdentityMemorySummary
  revisionId: string
}
```

## 20.3 WorkflowRunView

```ts
interface WorkflowRunView {
  id: string
  projectId: string
  contentUnitId: string
  templateId: string
  templateVersion: string
  overrideRevisionId?: string
  status: string
  nodes: WorkflowNodeView[]
  staleNodeIds: string[]
  activeNodeId?: string
  updatedAt: string
}
```

## 20.4 WorkflowNodeView

```ts
interface WorkflowNodeView {
  id: string
  type: WorkflowNodeType
  name: string
  order: number
  status: string
  inputSummary?: string
  outputSummary?: string
  providerLabel?: string
  dataSourcePluginKey?: string
  canRun: boolean
  canEdit: boolean
  canDelete: boolean
  isStale: boolean
}
```

## 20.5 ProjectAssetView

```ts
interface ProjectAssetView extends AssetRevision {
  usedBy: Array<{
    contentUnitId: string
    usage: 'inline' | 'cover' | 'card' | 'broll' | 'overlay' | 'reference'
  }>
}
```

## 20.6 ReviewProjectView

```ts
interface ReviewProjectView {
  projectId: string
  projectTitle: string
  counts: {
    text: number
    image: number
    video: number
    pending: number
    ready: number
    blocked: number
    unknown: number
  }
  items: ReviewContentUnit[]
}
```

---

# 21. 前端状态管理边界

不预设具体状态库；若现有 React 工程已经有统一方案，优先沿用。

但状态职责必须分离：

## URL State

保存：

```text
当前页面
Project Tab
Review Tab
筛选条件
选中的 Content Unit
```

## Server / Remote State

保存：

```text
Projects
Identities
Workflow Runs
Assets
Candidates
Review Status
Learning Data
```

## Local Draft State

保存：

```text
未保存的正文修改
未保存的卡片修改
未保存的 Workflow 节点排序
Node Editor 表单
Modal / Drawer 临时输入
```

## Durable Version State

只有显式 Save / Freeze 后才能成为后端长期版本。

---

# 22. 前端组件边界建议

```text
AppShell
├── PrimaryNav
├── GlobalCommand / Search（后续）
└── RouteOutlet

ContentProjectPage
├── ProjectHeader
├── ProjectTabs
├── ProjectOverview
├── CreativeBriefPanel
├── EvidencePanel
├── ProjectAssetsPanel
├── ContentMatrixEditor
├── VersionTimeline
└── ActivityFeed

ProductionWorkspace
├── ProductionHeader
├── WorkflowMiniCanvas
│   ├── WorkflowNode
│   ├── WorkflowNodeInspector
│   └── WorkflowDesigner
├── TextWorkspace
├── GraphicWorkspace
├── VideoWorkspace
└── ProjectAssetModal

ReviewCenter
├── ReviewToolbar
├── ProjectReviewGroup
├── ReviewContentUnitList
└── CandidateReviewPanel

IdentityWorkspace
├── IdentityTree
├── IdentityEditor
├── VoiceVisualPanel
├── ViewpointBoundaryPanel
├── AccountSeriesPanel
├── WorkflowPreferencePanel
└── MemoryPanel
```

---

# 23. Mock Data 基线

真实后端接入前，前端至少准备 3 个完整项目 Fixture：

## Project A：正常完整项目

包含：

- 3 个身份；
- 4 个 Content Unit；
- 图 / 文 / 视频；
- 完整 Evidence；
- 22 个共享素材；
- 角色默认 Workflow；
- Ready / Waiting Human 状态。

## Project B：异常项目

覆盖：

```text
Blocked
Stale
Unknown
Data Node refresh
素材权利缺失
Candidate 失效
```

## Project C：历史迁移项目

用于效果学习：

- 缺少完整旧指标；
- 有历史正文 / 图片 / 视频；
- 身份映射不完整；
- 有可识别的长期内容模式。

---

# 24. 前端实施切片

## F0：Shell 与 Mock Runtime

目标：建立稳定页面骨架，不接真实后端。

完成：

- App Shell；
- 9 个一级页面路由；
- Mock repository / fixtures；
- 统一状态 Badge；
- Modal / Drawer / Tabs / Empty State 基础组件；
- 页面级 loading / error / empty 骨架。

## F1：ContentProject + Content Matrix + Project Assets

完成：

- 项目工作区 7 Tabs；
- Content Matrix CRUD；
- Content Unit 创建 / 编辑 / 删除；
- 项目共享素材弹窗；
- 系统素材引用；
- Workflow 生成素材显示；
- 进入 Production Workspace。

## F2：Production Workspace + Workflow Debugger

完成：

- Text / Graphic / Video 三种工作台框架；
- Workflow Mini Canvas；
- Node Inspector；
- Add / Edit / Delete Node；
- Drag Reorder；
- Run Node / Run From Here；
- Data Node；
- Data Source Plugin 选择；
- Refresh Data → Stale 演示；
- 保存项目覆盖。

## F3：Identity + Role Workflow Defaults

完成：

- Identity Tree；
- 继承 / 覆盖展示；
- Voice / Visual；
- 长期观点 / 边界；
- Account / Series；
- Persona × Modality 默认 Workflow；
- Content Memory。

## F4：Review & Distribution

完成：

- 按项目聚合；
- 按状态辅助视图；
- Candidate Preview / Diff / Checks / Publish；
- Freeze Candidate；
- Content Approval；
- Delivery Authorization；
- Blocked / Stale / Unknown 完整状态。

## F5：Opportunity + Learning + System Assets + Settings

完成：

- Opportunity；
- 历史内容回收；
- 长期分析；
- Learning Candidate；
- 系统素材与知识；
- Data Source Plugin 管理入口；
- Channel / Model / Rule / Team 设置壳。

---

# 25. 前端验收标准

前端第一阶段完成，不以“页面都画出来”为标准，而以以下用户任务能在 Mock Data 下走通为标准：

1. 用户能从 Opportunity 创建 ContentProject；
2. 用户能编辑 Content Matrix，并增删改 Content Unit；
3. 每个 Content Unit 能进入独立 Production Workspace；
4. 同一项目图 / 文 / 视频能共用项目素材；
5. Workflow 自动生成素材会进入项目素材池；
6. Workflow 节点可新增 / 修改 / 删除 / 拖拽调整；
7. Data Node 能切换不同 Data Source Plugin；
8. Data Node 刷新后下游能显示 Stale；
9. 角色可以拥有不同 Modality 默认 Workflow；
10. 项目覆盖 Workflow 不会静默污染角色模板；
11. 用户能把 Content Unit 提交到按项目组织的 Review Center；
12. 用户能区分 Freeze Candidate、Content Approval、Delivery Authorization；
13. Blocked / Stale / Unknown 在 UI 上有不同处理路径；
14. 历史内容能进入“历史回收 → 长期分析 → 学习候选”；
15. 普通主流程不要求用户理解 Provider / Registry / Prompt Registry。

---

# 26. 反推后端时的原则

前端完成 F0–F4 后，再从真实页面需求反推 API。

不要直接把前端 View Model 当数据库表。

建议后端优先支持以下稳定业务资源：

```text
ContentProject
CreativeBriefRevision
Evidence / FactBoundary
ContentUnit
Identity / IdentitySnapshot
WorkflowTemplate / WorkflowRun / WorkflowNodeRun
DataSnapshot
Asset / AssetRevision
ContentMasterRevision
Candidate
Approval
DeliveryAuthorization
DeliveryAttempt / Receipt
Feedback
LearningCandidate
```

API 设计以“页面需要什么稳定业务语义”为依据，而不是以现有 ORM 表结构为依据。

---

# 27. 当前实施决策

1. V5 HTML 原型冻结，作为交互与信息架构参考；
2. 本 Frontend Product Contract V1 作为正式 React 实施契约；
3. 第一批代码应从 F0 + F1 开始，不先改后端；
4. 全部用 Mock Data / local fixtures 跑通；
5. F1 完成后再进入 F2 Workflow Debugger；
6. F0–F4 前端体验稳定后，再正式冻结 Backend API Contract。

---

# 28. C2C · 第一实施切片

```text
TASK: FE-F0-F1 — Build the finalized AIContentStudio product shell and ContentProject core from Frontend Product Contract V1.

GOAL
Implement the approved V5 product experience in the existing React frontend using mock/local data only. Do not redesign backend APIs and do not introduce backend migrations in this slice.

SCOPE
1. App shell + routes for the 9 top-level workspaces.
2. ContentProject page with tabs:
   overview / brief / evidence / assets / matrix / versions / activity.
3. Content Matrix CRUD for ContentUnit.
4. Project shared-assets modal/drawer; include uploaded, system-referenced and workflow-generated asset fixtures.
5. Navigation from a ContentUnit into the Production Workspace shell.
6. Shared status components for blocked / stale / unknown / ready / waiting_human.
7. Mock fixtures for one healthy project and one abnormal project.

CONSTRAINTS
- Preserve existing project conventions where they exist.
- Do not expose Skill as a primary user-facing concept.
- Do not build a generic low-code DAG editor in this slice.
- Do not bind UI state to a specific future backend schema.
- Project shared assets are opened through an entry/modal, not permanently occupying the production page.
- ContentProject remains the business root object.

ACCEPTANCE
- User can browse the main shell.
- User can open a project and navigate all project tabs.
- User can add/edit/delete a ContentUnit in the matrix.
- User can open project shared assets.
- User can enter the production workspace for a selected unit.
- Mock Blocked/Stale/Unknown states render distinctly.
- Existing frontend build/tests remain green.

NEXT_EXPECTED_STEP
After EXECUTED, review git diff and recorded test/build output, then issue FE-F2 for Production Workspace + Workflow Debugger.
```

