# Persona Creative Studio

**当前：156/156，2026-10-14独立AI范围验收并归档。本地main提交以Git回读为准。**

## PRD / 需求背景

以Persona作为创作默认根，提供科技研发、日常生活两个Starter，复用既有Workflow/Stage/Master/素材/Review/交付真源，支持文字、图文与声音的明确审阅和采用。

## 目录结构

proposal/design/specs记录确认范围；tasks/task_plan为持续计划；progress/findings/review记录真实版本与证据。[最终评审](docs/final-closeout-20261014/quality-review.md)、[选择的精确样本](docs/final-closeout-20261014/final-quality.json)、[默认图卡修复](docs/final-closeout-20261014/repairs/README.md)为当前入口；旧回执保留历史。

## 已完成

Persona版本化创作配置、产品Skill/风格/Quality/Profile目录、Starter幂等初始化和Text/Graphic/Audio/Video导演包方法已实施。配置入口与正常Production的Recipe控制/结果审阅已验证，继承规则与显式采用/权限/Unknown不重发保护保全。

用户明确委托AI评审后，原13文件及31Stage出处独立回验。科技采用原冻结工程文章/324秒声音及修订technical-editorial3卡；生活采用真实新假想文章/84秒声音及修订warm-magazine3卡。六图实际render/accept，Master24/26当前、精确refs/rights/hash保全，固定rubric与独立审阅通过。科技口播对齐99.5614%、生活99.1031%；完整离线ASR和声学检查，未直接听音频。

原科技人像图和旧生活稿/246秒声音的角色错配拒绝不擦除。修复计划是明确编辑，不伪装新AI生成；生活封面复用已有cleared插图PNG的画布crop，不伪称恢复JPEG或纪实照片。图文产品各6pass＋2current语义unavailable warning保留，委托质量批准不改系统warning。

13capability54新增/0删除已同步归档。Recipe已独立144/144、cef1bee提交；实际候选2670通过/28跳过/1已知wewrite环境豁免，Web/FE-P1/Ruff/strict及独立复核通过。已归档多平台160文件SHA保持，其他active change不关闭。

## 待完成 / TODO

本change无开放任务。主观音色/韵律/发音感官验收未观察；原human_review_required与private声音权限保留。正常使用仍需有效Provider配置、在项目显式选择Audio Recipe和真实voice ID，以及项目来源/素材的实际权限。正式页面的partial/blocked状态如实展示；本轮没有在正式两角色执行新的日常生成，缩短代表样本不称完整九阶段默认重跑。未push或公开发布。

## 关键设计决策与流程

Persona为创作默认根，Brand仅约束；Account/Series可显式替换整体modality配置。合同/运行提案/采用/Review/交付分别验收，模型观点不能反向成为verified事实。质量评审按用户指定角色执行且记录真实方法，编辑后的实际新成品独立批准，不能把旧拒绝改为通过。

```mermaid
flowchart LR
  I[内容身份 / 角色创作配置] --> P[项目 / 来源 / 栏目 / 单元]
  P --> R[Recipe配置与实际Preview]
  R --> E[显式运行 / 结果审阅]
  E --> A[明确采用Master / 素材]
  A --> Q[真实QC / 委托AI评审]
  Q --> D[独立Review / 本地交付]
```

## 依赖与启动

沿用API venv、SQLite/本机素材、React/Vite和已有Provider/renderer，无本次新产品依赖、迁移或配置更换。API8000、Web5173，见[本机运行手册](../../../../docs/runbooks/production-readiness.md)。原备份/耐久样本与新repairclone保留，临时UI18767/5174关闭；不可重跑有真实调用的harness。source/schema状态以Git与当前运行回读为准。

## 实际Skill

using-superpowers、writing-plans、executing-plans/subagent-driven-development、openspec-apply-change、systematic-debugging、test-driven-development、verification-before-completion、playwright、openspec-archive-change、finishing-a-development-branch。
