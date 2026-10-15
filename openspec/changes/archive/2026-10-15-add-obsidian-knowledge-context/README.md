# Obsidian 专业知识与个人风格接入

## PRD / 需求背景
在原稿创作中检索本机Obsidian的专业资料和历史作品，明确选用片段，让生成和精修同时参考知识与表达风格。已获用户本地只读方案确认；本需求独立于此前多平台、Persona、Recipe和日常生产归档。

## 当前阶段与下一步
实现、正常页面验收和归档完成，14/14，canonical已同步6条新增，已选择性本地提交；不push或公开发布。实际代码在主仓；隔离候选为codex/obsidian-knowledge-context。基线ea6f65ef21c4549ea82a4afa256e8eefe7799acb。相邻dirty内容保留，提交只纳入本需求增量。

## 直接使用
1. 进入内容项目→创作任务书，填写新主题、受众和约束并保存。
2. 在“来源与证据”→“Obsidian 专业资料与个人风格”搜索关键词，点“预览此笔记”。以磁盘已保存Markdown为准。
3. 选必要连续原文，勾选“专业内容参考”或“个人风格样本”，选择项目/角色/文字单元范围；明确勾选“允许将此片段用于生成模型”，点“明确选用笔记”。
4. 点“保存知识选择为新版本”。未勾模型授权仅保存参考；新版本用于新启动Run，已有Run和旧稿不自动替换。
5. 内容矩阵→对应文字单元→进入生产→准备运行→“预览实际请求”，展开selected_knowledge_and_style核对。执行后查看、审阅并明确“接受为 Content Master”；精修沿用同一知识快照并承接已接受稿。

现成样本：[科技知识选择](http://127.0.0.1:5173/projects/5?tab=evidence) / [科技精修稿](http://127.0.0.1:5173/projects/5/units/11/production)；[生活知识选择](http://127.0.0.1:5173/projects/6?tab=evidence) / [生活精修稿](http://127.0.0.1:5173/projects/6/units/12/production)。已保存知识rev1，Master35/37，两个独立Persona范围。

## 已完成
- 本地只读配置、关键词搜索、预览、片段选用和明确授权；当前范围knowledge/permanent与自媒体/文章，可在面板管理员折叠设置调整。
- Source精确片段去重、项目知识版本、原笔记和片段独立SHA、Persona/文字单元scope、Run冻结与真实提示预览/执行。
- 正式加法迁移obsidian000001，旧业务968行保持，SQLite integrity OK/FK0；75旧媒体、477旧归档、62相邻路径保全。
- 181既有后端检查、Web/TypeScript/Vite/bundle、Ruff/diff及13项隔离HTTP持久化检查通过；独立Python/TS/整体代码APPROVE。
- 两角色正常页面各初稿+精修，实际注册派发4次、0重试；四请求准确携带选中知识。委托AI五项质量通过，科技381字/生活384字。

## 待完成 / TODO
本需求已完成并归档、本地提交。可选文风微调不阻塞；本文不承诺完整复制本人风格、核实旧样本技术事实或实际平台发布。未新增持久测试。

## 关键设计决策
只读Markdown足够，不安装MCP、不升级Obsidian、不写回笔记、不全库同步/向量索引；配置入口复用来源与证据，不启用旧Data Node占位。最多5篇，每片段4000字、总6000字。选中知识是参考，不自动成为事实；需事实引用继续走原确认/授权/冻结FactPack。较长任务书/上游仍可能触及现有128KiB请求快照预算，会明确阻断。

## 目录结构与成果文件
proposal.md / design.md / specs/为规范；tasks.md / task_plan.md为持续计划；progress.md / findings.md / review.md为过程与复核；receipts/保存脱敏检查、迁移、实际请求、调用账本、页面与保全回执，不提交笔记全文/正式数据库/凭据。

## 代码位置、依赖与启动方式
源码白名单见task_plan.md与receipts/source-candidate.json（11文件）。沿用FastAPI8000、Web5173及既有文字供应商，无新增依赖。加法迁移后私有runtime.env只更新REQUIRED_SCHEMA_HEAD=obsidian000001，其他字节保持，API必要重载后ready=true。Web缺失时按既有runbook恢复Vite；现有Worker保留。本机原运行手册：docs/runbooks/production-readiness.md。

选择性提交候选额外独立验收：仅将11路径自身增量应用HEAD，干净候选173既有检查/8警告通过、Web/tsc/Vite/bundle通过；实际dirty候选181通过的另8案例属于被排除的相邻既有测试。源码净增711/删2，无相邻依赖或改动被混入提交；未新增持久测试。
