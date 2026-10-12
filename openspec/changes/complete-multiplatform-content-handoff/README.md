# Twelve-platform Content Handoff

2026-10-08 Persona前置规格校准：统一引用现有`stage.variant.adapt@1`，后续验收计划明确少量参数化持久合同覆盖＋十七形态集中冒烟。仅纠正规格，不启动本change业务、不写测试/正式库、不授予模型/公众号调用或生命周期权限；当前Persona“不新增测试代码”限制保持，未来测试写入需单独授权。原要求/22个场景和2/13历史规格准备计数保留，原APPROVE记录不冒充本次修改后的独立复核。

## PRD / 需求背景

补齐原PRD十二平台的日常渠道交付：平台专属稿件＋实际素材包，公众号保留草稿箱、其他平台人工发布。不能以公众号验收代表全平台完成。用户已确认完成标准；本proposal尚待确认business apply。

## 目录结构

- proposal.md / design.md / tasks.md：范围、exact矩阵/合同和13个复合任务。
- specs/multiplatform-content-handoff/：新增十二平台/十七形态长期契约。
- specs/content-harness-registry/、specs/delivery-router-v1/：单一目录与本阶段人工交付delta。
- task_plan.md / progress.md / findings.md：实施计划、真实进度和代码证据。

## 已完成

原需求/代码边界核对，十二平台/十七形态及动作范围固定，标准OpenSpec文档与两批计划创建。独立SPEC/PLAN最终均APPROVE，strict37/37、diff/原场景精确保留通过；2/13为规格准备，业务任务仍0实施。

## 待完成 / TODO

等待用户确认proposal并明确进入apply；随后批次A后端/包，批次B界面/集中验收，再按独立授权处理正式profile启用、主规格同步归档与本地提交。公众号真实调用、其他平台公开发送/账号资格不包含在当前授权。

## 关键设计决策

十二平台为公众号、头条、百家号、知乎、B站、搜狐号、企鹅号、网易号、小红书、X、微博、抖音；知乎/B站各两个形态、X四个形态，共十七。复用ChannelRegistry/adapter、Master/Variant/v5/Review/Delivery/Recipe，不新建真源/表/迁移；不同目标有独立有效指令/结构/编辑与包，来源/权利/审批/Unknown不变。

## 依赖与启动方式

仍是本机SQLite＋本地素材库＋loopback API/Web＋必要Worker，current head为crs000000001。无新依赖；沿用根README和runbooks/production-readiness.md启动方式。当前只做文档，不重启服务、执行seed、改库/模型凭据或发送内容。

## 实际技能

using-superpowers、brainstorming、openspec-propose、writing-plans、receiving-code-review、verification-before-completion；Spec/计划review为只读，不进行business apply。
