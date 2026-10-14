# Persona 委托 AI 质量复核

## PRD / 需求背景

用户明确选择“补齐持久测试，按委托 AI 评审收口”。本目录记录已有 Persona 成品的独立复核及必要图卡隔离修复，保留原始拒绝与来源，不把 AI 分析称为人类感官验收。

## 目录结构

`final-quality.json`、`quality-review.md`为最终固定rubric与精确选样；`repairs/`为六个新默认图卡及真实render/accept/权利/当前检查回执。`artifact-verification.json`为13原件，音频与补充出处JSON为完整ASR/声学/31Stage链核对。`daily-product-entry.json`为正常页面创建、默认继承、Preview和已有结果审阅；`runtime-readback.json`为8000/5173及临时服务关闭回读。`index.json`为本目录持久文件SHA；旧quality-review.json/vision-review.json保留历史。

## 已完成

四项质量任务经委托AI及独立审阅通过，change已156/156归档，13capability54新增/0修改/0删除，归档后strict42/42。原图文拒绝不擦除；两组新默认3卡实际像素检查通过。科技324秒/生活新84秒完整ASR及精确口播对齐99.5614%/99.1031%，未直接听音频。MiniMax新增图视觉请求额度失败，未记成通过，改为Codex实际像素独立复核。

正常UI隔离创建两Persona单元和快照，分别继承Workflow17/19 v3；科技Preview可执行，生活空白项目明确因fresh_current_evidence_required禁用。已有真实结果可审阅，未新增模型调用。正式API必要重载ready=true，Web5173可访问；仅本轮18767/5174和浏览器验收会话已关闭。

## 待完成 / TODO

本change无开放任务；原human_review_required、图文两current语义unavailable warning及私有声音权限保留。未观察主观音色/韵律/发音，未完成正式两角色新的全流程生成、远程账号验证或公开发布；日常使用仍需有效素材/事实证据和明确Audio Recipe/voice ID。

## 关键设计决策

旧生活原稿及246秒声音的拒绝、新假想稿及84秒声音分别记录。修复为明确署名编辑和既有插图crop，未伪称新模型生成或真实照片。方法出处、合同当前性、自动QC和委托质量结论分开记录；不继承其他change的质量批准，不改系统warning。

## 依赖与启动方式

复用既有API venv、renderer、ffmpeg、离线ASR缓存与React/Vite；无本次新产品依赖/迁移。正常API8000、Web5173，见需求README与本机运行手册；原件及私有副本保留。提交版本以本地Git回读为准，未push。
