# 手动来源配置与统一管理

## PRD / 需求背景

用户需要自行添加新闻网站、RSS/Atom、博主主页，并指定这些来源服务哪些角色；手动来源与自动发现来源共用同一来源库和每日选题链路。

## 当前阶段

`ARCHIVED / 16 of 16`：用户已明确确认，代码已接入正式工作台，隔离真实后台及页面验收完成，本capability已同步并归档。当前基础能力来自 `../../add-daily-persona-content-opportunities/`，其自然日批验收与归档继续按原清单执行；本提案单独承载新增手动管理范围，不改变已批准清单或运行中的调度。

## 目录结构

- `proposal.md`：需求与范围。
- `design.md`：交互、数据与后台衔接。
- `specs/manual-discovery-source-management/spec.md`：可验收行为。
- `tasks.md`、`task_plan.md`：同一实施清单和持续计划。
- `findings.md`、`progress.md`、`review.md`：实际发现、进度和规范复核。

## 代码位置与版本

基线 `/Users/mshengran/Project/AIContentStudio`，Git `main@636d60e`，含已启用的未提交来源发现与质量修复。相关入口为 `apps/web/src/product/DiscoveryPanel.tsx`、`apps/api/app/routers/discovery.py`，来源与订阅为 `apps/api/app/models.py`，采集与维护为 `discovery_ingestion.py`、`source_discovery.py`、`discovery_runtime.py` 及既有Celery任务。实施前重新核实工作区状态，保留相邻修改。

## 已完成

已完成7路径正式集成、手动添加/配置/角色关联与自动来源统一管理、后台验证与人工设置保护；独立审阅、既有检查和真实隔离后台验收完成，主规范已同步。

## 待完成 / TODO

16/16完成，本capability已同步并归档；前一change的正式自然日批仍待原计划验收。

## 关键设计决策

复用现有来源和订阅，不另建手动来源库。保存链接与采集成功是不同状态；手工指定来源仍受正文、日期、角色相关性及选题质量规则约束。人工配置优先，历史来源与证据保留。

## 依赖与启动方式

计划复用现有API、Web、Celery及安全HTTP读取，无新增外部服务。实现沿用本机API8000/Web5173/Redis2/Celery；隔离8018/5188/Redis9仅验收使用并在结束停止；校验命令为 `openspec validate add-manual-discovery-source-management --strict`。

## 实施与验证回执

正式根main@636d60e工作区7路径已集成、未提交；精确hash见implementation_manifest.json。81既有检查/1既有warning、Web构建/bundle、Ruff、strict通过；code-reviewer/Python/TypeScript独立复核通过。正常页面添加/配置、页面关闭后自然Beat验证采集、隔离当天日批真实使用手动来源并只生成1条已通过；未用此替代原经营角色明日自然验收。正式库未加入验收来源、角色或选题；原Persona/修订/机会/评估历史逐值保全。私有备份见manifest，完整证据见progress/review。
