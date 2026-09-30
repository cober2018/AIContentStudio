# FE-F6E Channel Variants Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改旧 Candidate 语义的前提下，让精确渠道变体从 Master 产生并进入 Candidate v5、本地审核与人工交付。

**Architecture:** 以四个追加式 Variant 表和一个 nullable Candidate FK 保存精确来源；Adapter 针对已发布 Channel Registry profile 输出有界 canonical payload。v5 按 schema dispatch 和 `(unit_id, variant_key)` 判当前性，Matrix 只读投影；远端 Provider 留给 F7。

**Tech Stack:** FastAPI、SQLAlchemy、Alembic、Pytest、React、TypeScript、Vite。

---

### Task 1: 持久化与迁移

**Files:** `apps/api/app/models.py`、`apps/api/alembic/versions/f6e000000001_channel_variants.py`、`apps/api/tests/test_f6e_variant_persistence.py`、`apps/api/tests/test_migrations.py`。

- [x] /// 写模型/迁移 RED：四表、一列、系列唯一约束、精确外键和 v5 历史降级拒绝。
- [x] /// 运行定向测试确认失败原因是能力缺失。
- [x] /// 仅实施 OpenSpec 计划内加法模型与迁移，不回填 v3/v4。
- [x] /// 复跑定向测试、SQLite up/down/up 和隔离 PostgreSQL 约束检查。

### Task 2: Canonical adapters 与 Variant service

**Files:** `apps/api/app/services/` 的现有渠道/生产服务、`apps/api/app/routers/` 的项目路由，以及对应 `apps/api/tests/` 定向回归。

- [x] /// 先写五种 schema、source→target 兼容矩阵和 unsupported/profile mismatch 的失败测试。
- [ ] /// 实现 exact published profile 的 adapter canonicalize/validate/preview；不可用时无写入。
- [ ] /// 先写 series CAS、幂等、foreign raw-ID、rights/evidence 失败测试，再实现项目级 Variant revision 与 exact refs/checks。
- [ ] /// 运行后端相关回归并核对没有新增持久业务对象。

**同系列真实并发子步骤（2026-09-30）**

- [ ] /// 用文件 SQLite 和两条独立 Session 同步到同一个旧 series head，先写 RED：竞争后恰好一版持久化，失败方 409，未留下孤立 ref/Event；同幂等键胜者回读不重写。
- [ ] /// 读锁错误与唯一键冲突的来源及事务状态，只在 Variant save 边界归一化真实并发冲突；其它数据库错误不吞掉。
- [ ] /// 定向 GREEN、F6E 相关回归、OpenSpec strict、Ruff、diff-check；根据证据勾任务并更新 README/progress/findings。

### Task 3: Candidate v5 与审核交付

**Files:** 现有 Candidate、Review、Approval、Delivery、Package 服务与测试。

- [ ] /// 先写 v5 唯一来源 FK、五个 legacy 字段污染拒绝、跨系列独立当前性、v3/v4 兼容 RED。
- [ ] /// 实现纯 manifest builder、冻结、schema-first 读取与 live gates。
- [ ] /// 实现 Review/Approval/本地包分派；远端能力未验证必须 fail closed。
- [ ] /// 跑无 Draft 的 Master→Variant→v5→Approval→ZIP 集成回归。

**v5 审批与系列当前性子步骤（2026-09-30）**

- [x] /// 在 `apps/api/tests/test_f6e_freeze_v5.py` 使用已冻结的 X single/thread 写 RED：反序审批均可通过；同系列新版本及五旧 FK/清单污染不能审批。
- [x] /// 在 `apps/api/app/services/production_validation.py` 共用服务端 v5 live gate；检查唯一 Variant FK、同系列最新 Candidate、源 Master/上下文/rights/refs/checks/render 与冻结内容，不用 Unit 最大 ID。
- [x] /// 在 `apps/api/app/services/project_review.py` 按 `schema_version` 分派，v5 审批及 commit 前重验；v3/v4 路径保持原语义；Review revision 使用 Variant revision_no。
- [x] /// 定向 GREEN、全后端及规格/静态门禁后核销确证任务；Authorization 与本地包后端已接通，跨形态与浏览器验收尚未完成。

**实时 loader / Freeze 子步骤**

- [x] /// 在 `apps/api/tests/test_f6e_freeze_v5.py` 写项目级 RED：完整来源/Variant checks 后 POST Freeze v5；检查 manifest、唯一 Variant FK、两个系列独立冻结、重复请求幂等及历史/撤权拒绝。跨项目/并发竞态及全部污染字段仍待补测。
- [x] /// 在 `apps/api/app/services/candidates_v5.py` 补服务端 snapshot loader（授权/当前性/实时检查由调用者证明），在 `apps/api/app/services/project_review.py` 加 v5 Freeze，并在现有 `apps/api/app/routers/project_review.py` 明确三选一 source dispatch。
- [x] /// 定向 GREEN 后跑完整门禁；Review/Approval/Delivery 另行实现，不用 Freeze 通过冒充 v5 全闭环。

**本轮 v5 manifest builder 子步骤（先于 Freeze）**

- [x] /// 在 `apps/api/tests/test_f6e_candidate_manifest_v5.py` 写完整上下文与安全模型血缘的纯函数 RED；执行 `.venv/bin/pytest -q tests/test_f6e_candidate_manifest_v5.py`，确认因 builder 缺失而失败。
- [x] /// 新建 `apps/api/app/services/candidates_v5.py`，只做有界 canonical manifest 的严格校验与 JSON 深拷贝；其输入必须由后续授权/实时 gate 提供，不用客户端自报即可冻结。
- [x] /// 同一测试 GREEN，随后全后端、OpenSpec all-strict、Ruff 和 diff-check；不把纯 builder 误称为 Candidate v5 已可冻结。

### Task 4: Matrix、前端与最终门禁

**Files:** 现有 Project Matrix/Production/Review 前端、FE-P1 检查脚本及隔离浏览器验收。

- [ ] /// 先写非持久建议与受控选择的服务测试，再实现 Matrix API。
- [ ] /// 按需加载 Variant 编辑/差异/状态/交付 UI，不污染通用首包。
- [ ] /// 跑旧七场景对应回归、隔离浏览器、全后端、前端、性能、strict、Ruff、diff-check 和迁移门禁。

**v5 Review 冻结展示子步骤（2026-09-30）**

- [ ] /// 在 `apps/api/tests/test_f6e_freeze_v5.py` 写项目级 RED：v5 各受控形态的冻结 Preview/Checks 与同系列 Diff；跨系列 Candidate 不充当前版，五个旧来源字段污染时拒绝 Review。
- [ ] /// 在 `apps/api/app/services/project_review_projection.py` 增加 schema-first v5 Preview/Diff 只读投影，并在 `apps/api/app/routers/project_review.py` 限定 v5 Diff 选择同 Unit 同 variant_key 的前一 Candidate；不改 v3/v4。
- [ ] /// 回归、strict、Ruff、diff-check 后只核销已证实的任务；文档与本地提交记录未完成的前端 Review UI、Versions/Overview 与跨形态验收。
- [ ] /// 记录独立复核；只在实际完成后勾 OpenSpec 任务并本地提交，不推送/部署/归档。
# F6E v5 warning 处置闭环（2026-09-30）

/// 在既有 v5 API fixture 将一条当前检查置为 warning：Variant readiness 仍为 ready，当前 Freeze 拒绝，锁定 RED。
/// v5 清单仅允许 pass/warning，保留精确 check ID/input hash；审批调用现有 `validate_warning_dispositions`，授权和包的 approved gate 复验已保存的理由。
/// 回归拒绝缺失/伪造处置、被删除的历史处置；保留 live rights/evidence/bytes 检查，定向及全后端门禁通过后才核销 7.6。
