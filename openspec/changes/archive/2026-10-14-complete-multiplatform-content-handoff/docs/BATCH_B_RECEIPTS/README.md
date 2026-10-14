# 当前验收证据（2026-10-14）

## PRD / 需求背景

12平台/17形态合同、逐账号Review/授权/本地包及两Persona真实成品验收。**当前43/43，委托AI质量验收通过，本change已归档。** 实际本地提交以Git回读为准；不代表直接试听或公开发布。

## 目录结构

- `<channel>-<form>.json/.zip`：17形态独立受控API/真实媒体/hash包。
- `browser-receipts.json`：受控17Production＋17Review/ZIP；`formal17-browser.json`：正式17可选，旧复杂来源3preview/14明确subset阻断。
- [accounts-real](accounts-real/README.md)：四sample账号独立真实本地交付，账号bound_unverified。
- [persona-real](persona-real/README.md)、[整模态评审](persona-real/quality-review.md)、[最终来源/完整检查](persona-real/final/README.md)。
- `profile-activation-20261014.json`：配套备份/dry-run/幂等19–30版本与旧行保全。
- `backend-delegated-closeout.log`、`web-delegated-closeout.log`：新鲜工作区完整门禁；原closeout/red日志保留为历史。
- `candidate-backend.log`、`candidate-web.log`、`candidate-editor.log`、`candidate-ruff.log`、`commit-scope.json`：真实选择性提交树的门禁/范围。
- `archive-result.log`、`archive-readback.json`、`strict-after-archive.log`、`final-runtime.json`：七capability归档/规范保全/运行readiness。
- `index.json`：基线Git版本、工作区文件与实际提交代码的独立精确SHA，递归证据hash。

## 已完成 / TODO

17受控UI/API/ZIP、四账号真实包、正式12Profile启用、两角色新文章/6PNG/2WAV、正确来源边界与完整检查、委托AI固定rubric均通过。工作流Provider累计19，另vision评审6和offlineASR2；无生成重跑、Unknown重试或公开发布。

新鲜工作区2639 passed/28 skipped/1既有wewrite环境失败（按授权豁免）；实际代码候选368 passed/1 skipped，Web/FE-P1、Node8/8、Ruff与独立复核通过。归档后strict40/40。本需求无开放项；相邻Persona151/156、Stage141/144各自保留。

## 关键设计决策

原manifest/样本保持初轮历史。模型观点不反向当证据，source明确author_opinion/假想；私有原文不公开。纯文字/形状图卡输出满足image_note，照片预设门槛不放宽。新图卡有依据地追加public=true/model=false/commercial=false，旧private图卡及WAV权限原样。

音频完整ASR/声学/签名QC和独立审阅已记录，**未直接听音频**；原human_review_required不改。提交只纳入owner，六共享文件按段筛选，保全并行plugin变化；索引区分工作区SHA与提交SHA。

## 依赖与使用

沿用API venv、React/Vite和既有Provider/renderer，无新增产品依赖。本需求Batch A已有a3series00000001迁移，Batch B与最终修复无新迁移。准确命令见owner progress.md，数据库/完整备份只在私有目录。不要重跑生成harness，按manifest只读复核。

临时18765/18766服务和浏览器已关闭，必要API已加载ready=true；Vite/worker/config未动。文件可以查看/播放，本轮没有公众号发送、push或其他平台公开发布。
