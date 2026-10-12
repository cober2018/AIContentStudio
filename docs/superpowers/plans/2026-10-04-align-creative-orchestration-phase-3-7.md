# Creative Intent / Execution 后端实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. 本批按下列成组步骤执行，不逐个细项向用户重复确认。

**Goal:** 按已批准的同一 change 实现阶段 3–7 的后端持久化、创作意图、冻结执行包、执行状态及人工接受；页面验收与 MCP 保留后续批次。

**Architecture:** 延续 ContentMaster / ChannelVariant / MaterialRevision 真源。新执行系统只负责有界执行合同、暂存及人工接受，不替代 ProviderGenerationTask，不自动修改正文、审批或发布。SQLite＋本地素材库＋loopback 是正式架构；本批迁移只在隔离副本演练。

**Tech Stack:** 现有 FastAPI / SQLAlchemy / Alembic / 本地 StorageProvider；不新增依赖。

## /// 1. 持久化与迁移

- [x] 修改 `apps/api/app/models.py`：Master/Variant nullable intent/hash；Package、Execution、Output、CapabilityArtifact/Revision/Use；增加 `external_execution` source kind。
- [x] 新增一份以 `f8a000000001` 为前置的 additive Alembic migration。source exactly-one、合法状态/范围、幂等与输出 index/attempt 约束和降级前置保护与 ORM 一致。
- [x] 对当前 SQLite 的隔离备份执行 up/down/up，比较原历史表哈希；新历史存在时 downgrade 必须拒绝。

## /// 2. Creative Intent

- [x] 在 `services/creative_intents.py` 定义 bounded/versioned canonical intent 和 hash；拒绝秘密、原始 provider/source 内容、非法 JSON 和重复 rationale ID。
- [x] 在现有 `services/content_masters.py`、`services/channel_variants.py` 及两个 router 中接入 intent。继续沿用现有 CAS、幂等和原子事件；省略字段保留前版意图，显式 null 清除；旧 null 行不回填。
- [x] 暴露 intent 历史与 diff，不改既有正文/hash/evidence 语义。

## /// 3. Package

- [x] `services/creative_packages.py` 提供 canonical builder/currentness；仅接受本项目 current Master/Variant，精确资产/证据和 live rights。
- [x] 冻结 role/kind/required/MIME/min-max count/max bytes；Director 支持未最终渲染的 Video v2，timeline 原样保留为 guidance。
- [x] package 创建不执行、不批准、不改 source；过期包只读，claim/start/accept 都 fail closed。

## /// 4. Execution / Acceptance

- [x] `services/creative_executions.py` 接入 prepare、CAS claim/start/report、unknown/reconcile、confirmed-before-dispatch retry、cancel/reject/supersede。
- [x] 私有工作目录及 materialize/stage 限定本 execution 的普通文件，拒绝路径逃逸/符号链接；输出按 role/index/attempt 保留不可变历史。
- [x] `result_ready` 按 required staged min_count，`accepted` 按 required accepted min_count 判定；required reject 可同 execution replacement，终态不再收新输出。
- [x] 使用现有 StorageProvider/Material API 接受结果；live input rights 不升级，归因/许可继承，项目引用显式且原子，绝不自动改 Master/Variant/Candidate。
- [x] `routers/creative_orchestration.py` 使用现有 user/editor 授权及 project/unit 归属，注册到 main。

## /// 5. 本批门禁与记录

- [x] 运行隔离 API/SQL assertions 和现有后端 suite；遵守不新增永久测试代码的要求，不调用外部服务。
- [x] 独立规格/数据安全复核，修正后复核；OpenSpec strict、Ruff、diff-check、F8 13 文件 SHA256。
- [x] 更新 change 自有 README/task_plan/progress/findings 及准确任务数；未实现 UI/MCP/Capability 服务的项不勾选。

本批结果：新增 42 项，累计 64/147；SPEC/Python/数据安全复核均 APPROVE。验收与剩余范围见 `docs/ALIGN_CREATIVE_PHASE_3_7_BACKEND_ACCEPTANCE.md`。

## 禁止项

不升级正式 SQLite、不修改正式素材/凭据、不新建工作树、不 commit/push/deploy、不 canonical sync/archive、不碰 F8 13 个 owned 文件。不因为本批模型已存在就声称 Capability Memory 已可用，也不因 API 通过就声称页面验收通过。
