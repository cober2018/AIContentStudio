# Twelve-platform Content Handoff Implementation Plan

> **For agentic workers:** apply 获准后使用 superpowers:executing-plans 分两批执行，批内连续完成，集中复核/冒烟；当前只完成规格与计划，不执行下面业务步骤。

2026-10-08 Persona前置校准：Stage统一为`stage.variant.adapt@1`；后续计划要求少量参数化持久覆盖＋十七形态集中冒烟。只同步计划，不新增测试文件、不进入本change业务；实际测试写入须单独明确授权。

**Goal:** 补齐原规划十二平台、十七种平台专属稿件与素材交付包；公众号维持既有草稿箱，其他平台人工发布。

**Architecture:** 单一 Channel Registry/profile + exact ChannelAdapter/canonical schema，复用 Master、append-only Variant、Candidate v5、Review/Delivery 和 Recipe Stage。零新表/零迁移/零新增依赖，不改变正式本机 crs 环境。

**Tech Stack:** 既有 FastAPI/SQLAlchemy/SQLite、React/TypeScript/Vite、原Worker/LLMRun/本地素材库。

## 状态

- [x] 按用户回答固定平台、形态、交付动作和禁止范围；不是远端发文授权。
- [x] 读取当前代码/canonical/active F6E和Recipe相关规格，确认缺口不是加菜单或执行seed即可解决。
- [x] 创建标准 change 的 proposal/design/specs/tasks。
- [x] 独立 SPEC/计划最终均APPROVE、零blocker；strict37/37、diff及原场景精确保留通过。
- [ ] 用户明确确认后 business apply。

## 文件职责与批次

| 批次 | 优先编辑现有文件 | 职责 |
|---|---|---|
| A1 | apps/api/app/services/content_harness/channel_registry.py；apps/api/app/seed.py；既有templates/profile管理服务与router | 单一目录、带版本profile、可审阅幂等增量；不是运行全库seed |
| A2 | apps/api/app/services/channel_variant_documents.py；apps/api/app/services/channel_adapters.py | 十二新增canonical schemas、十七exact adapters、typed descriptor、目标指令 |
| A3 | apps/api/app/services/channel_variants.py；apps/api/app/routers/channel_variants.py；既有Stage Variant resolver/handler | 受控建议/显式save、LLMRun及refs、Recipe实际参数消费 |
| A4 | apps/api/app/services/candidates_v5.py；production_validation.py；production_packages.py；既有Approval/Delivery dispatch | 冻结检查、独立currentness、各形态本地HTML/ZIP与live安全边界 |
| B1 | apps/web/src/product/ChannelVariantsPanel.tsx；ChannelVariantForm.tsx；既有Recipe/Stage面板；apps/web/src/api.ts | 服务端descriptor驱动目标选择/typed编辑/Preview，不维护第二份五目标清单 |
| B2 | apps/web/src/product/CandidatePreview.tsx；既有Project Review/Delivery页面 | 真实冻结预览、渠道差异、包下载/人工回执/公众号草稿区分 |
| B3 | 本change的README/progress/findings；根README/计划进度；既有验收记录 | 十七形态矩阵、集中代码复核/冒烟/回归、正式启用与生命周期授权状态 |

优先编辑已有文件；若文件实质超过可维护范围，只拆本次新增schema/adapter职责，不重构无关服务。所有 apps 文件在确认apply前保持原样。既有 F8/ACO/Recipe dirty 内容保留。

## 执行顺序

/// 批次 A：只读目录/profile差异 → additive descriptor/canonical schemas → exact adapters和受控建议 → Variant refs/checks/v5/local package → 既有stage.variant.adapt@1接线 → 集中源码自审，不逐个形态打断请求确认。

/// 批次 B：服务端目录接入页面 → typed稿件/素材/证据编辑 → 冻结Review/交付包 → 十七形态集中冒烟＋旧五形态/版本回归 → 独立代码复核 → 构建/预算/既有回归/strict/diff → 交付实测矩阵；仅方向/权限变化或无法解决的真实阻断询问用户。

/// 正式启用与生命周期：单独授权 → 配套备份/只读dry-run → 必要profile增量CAS/幂等启用 → 历史行/hash/素材/页面回读 → 主规格保留审计/归档/本地提交按获准范围执行，不推送或公开发布。

## 集中验证

- spec阶段：`openspec validate --all --strict`；`git diff --check`；三份delta的MODIFIED标题/旧场景保留；现有业务/F8/ACO/Recipe差异哈希不变。
- apply阶段：在明确测试写入授权后补少量参数化持久合同覆盖，复用backend回归并集中十七形态冒烟；未授权不写新测试，临时冒烟不代替持久覆盖。`cd apps/web && npm run build`（含既有bundle gate，若独立gate另跑npm run check:bundle）；新增页面保持lazy与原路由预算。
- 每个目标必须实际走 proposal/edit/save/reload/checks/freeze/approve/authorize local/ZIP/readback，核对frozen bytes/hash/结构/media；图文使用可证明实际图组，Douyin仅脚本包。十七目标的结果逐项记录，不只列平台名字。
- 同一Master多平台、同平台多形态、旧五schema/hash、v1-v5历史/归档、dirty隔离、profile CAS/幂等、撤权/损坏/错误refs/unsafe HTML/私有source投影、target/source字段篡改、Unknown不重发均在集中阶段验证。
- local smoke强制阻断供应商/微信出站；实际模型质量/平台编辑器效果/账号资格不冒称通过。任何付费生成/公众号新草稿或公开发布须按后续明确授权执行。

## 本轮不执行

业务apply、测试代码、迁移、正式profile写入、运行环境操作、真实模型/公众号请求、其他平台登录/发布、主规格同步/归档、commit/push。
