## Why

科技选题不应因原文超过48小时就失去参评资格；现有页面又将当天零结果、日期筛选和执行失败混成空列表。新增 Radar 发现线索可补充 AIHOT，但必须保持角色分流及原始证据判断。

## What Changes

- 科技角色采用即时动态（48小时）、近期技术进展（30天）、深度/常青三类判断；热度窗口不等于选题资格窗口。
- 科技默认展示有效且未处理的建议，保留当天及历史筛选；空结果解释依据持久运行记录。
- new-term-radar 仅作为科技角色补充发现源，与 AIHOT 并存、合并去重、追溯原始证据。
- 保留生活角色规则、评分门槛、调用预算、调度及历史人工决策。

## Capabilities

### New Capabilities
- `tech-opportunity-policy`: 科技分类、证据时效及有效建议策略。
- `radar-discovery-source`: Radar补充发现、标准化、去重和真实可用状态。
- `opportunity-run-explanations`: 运行覆盖、筛选原因及空态可解释读模型。

### Modified Capabilities
- `content-opportunities`: 添加科技有效建议视图和显式日期筛选的契约。

## Impact

复用 DiscoverySource/Item、PersonaResearchRun、ContentOpportunity 及现有 API/Web。主要涉及 daily_opportunities.py、discovery_aggregation.py、discovery_runtime.py、机会路由及 OpportunityPages/DiscoveryPanel。预计无需新业务表；不复制第二套选题引擎。

依赖仍 active 的 add-daily-persona-content-opportunities 和 add-aihot-persona-source-integration；本包不伪造其 canonical 状态或完成状态。只在本包明确的科技规则与页面范围覆盖旧默认，所有其余契约保留。已获business apply及2026-10-19本机Radar安装、免费采集和科技补充信源启用授权；不触发付费模型、不提交或归档。
