# Creation Recipe Stage Control Loop

**当前：144/144，2026-10-14独立验收并归档。本地main提交以Git HEAD回读为准。**

## PRD / 需求背景

把Workflow、Master、素材、Variant和专业执行串成可控制的创作闭环；Recipe是既有Workflow Definition的产品投影，没有新Recipe/Feedback状态表。

## 目录结构

proposal/design/specs为已确认目标；tasks/task_plan为同一持续计划；progress/findings/review记录真实发现、最小修复与复核。[最终回执](docs/final-closeout-20261014/README.md)包含持久覆盖/实际候选日志/提交范围及产品入口边界。

## 已完成

typed Stage合同、纯Preview/精确hash、发送前持久claim/receipt、显式采用/原子关联/反馈、自动接续停止规则、显式保存调整/方法候选/默认隔离和有界调优已验收。新增66持久案例，复用已有核心Contract/Resolver/Receipt/Master覆盖；两实际缺陷已先复现再修：非法反馈ID先判型、合法nestedDescriptor有界冻结深度16（17拒绝）。

实际HEAD＋7代码路径候选独立复核APPROVE；2670 passed/28 skipped/1既有wewrite断链环境豁免，143相关通过；Web/FE-P1、Ruff、strict通过。九capability同步32新增/0删除，原要求/场景保全，相邻align任务保持153/154、multiplatform归档保持。

## 待完成 / TODO

本change无开放项。真实专业工具成片、直接音频试听、远端账号验证与公开发布分别保留边界；未push。本轮产品入口读取/历史/纯Preview已验证，未称正式两Persona执行了新真实生成。

## 关键设计决策

运行/提案/明确采用/Review/发布分开；Unknown不重发，事务故障无部分领域写入，旧running/unknownclaim和snapshot不改。调优只能建议有界字段，不能自动保存。候选以HEAD＋归属小块验证，未引入共享dirty的channel_methods/plugins或Studio新模型响应形状。

## 依赖与启动

沿用apps/api/.venv、SQLite和React/Vite，无新增依赖或本轮迁移。既有crs已启用，当前approved head a3series00000001；启动见[本机运行手册](../../../../docs/runbooks/production-readiness.md)。API8000，Web5173。临时UI18767/5174验证后停止，生成harness不要复跑。

## 实际Skill

using-superpowers、writing-plans、executing-plans/subagent-driven-development、openspec-apply-change、systematic-debugging、test-driven-development、verification-before-completion、playwright、openspec-archive-change、finishing-a-development-branch。
