## Why

用户已部署科技AI与生活热点两站，希望将采集维护集中到已有AIHOT站点，AIContentStudio负责按角色生成选题与后续创作，减少逐站适配的重复工作。

## What Changes

- 配置科技站aitech.kayoyo.top关联角色2、生活站wonderlife.kayoyo.top关联角色3，复用现有来源储备、定时采集与停机补偿。
- 优先接入站点既有匿名REST API，初次精选快照、后续增量同步，保存去重键、游标、修改与撤选；热点及事件接口用于补充上下文。
- 聚合站与原始出处分开记录，冻结可核验正文；原文/转载更新/事件日期分开，沿用当前质量筛选、双评估及每角色0至5条上限。
- 正式切换前备份和验证两个入口；切换后这两个角色停止自动扩展及逐站定时采集，旧来源/历史/用户配置保留，可恢复；证据不足时允许按原文链接定向取证。
- 未完成接口验证不得标为接通；失联、补采缺口和撤选明确显示，保留既有机会历史。

## Capabilities

### New Capabilities
- `aihot-persona-source-integration`: 两站角色映射、可恢复精选同步、来源追溯与可见失败，以及沿用既有选题创作流程。

### Modified Capabilities
无。本项新增聚合入口适配，不改原质量标准或商品创作合同。

## Impact

预计涉及discovery_sources、discovery_ingestion、discovery_catchup、source_discovery、daily_opportunities与DiscoveryPanel，复用既有模型JSON配置与Celery；具体改动以实施前追踪为准。不安装AIHOT、不修改外部站、不新增产品依赖；本阶段仅文档，未改变正式来源与调度。父change的自然验收独立开放，不能用本提案关闭或冒称新入口验收。
