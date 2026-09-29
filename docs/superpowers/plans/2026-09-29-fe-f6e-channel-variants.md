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

### Task 3: Candidate v5 与审核交付

**Files:** 现有 Candidate、Review、Approval、Delivery、Package 服务与测试。

- [ ] /// 先写 v5 唯一来源 FK、五个 legacy 字段污染拒绝、跨系列独立当前性、v3/v4 兼容 RED。
- [ ] /// 实现纯 manifest builder、冻结、schema-first 读取与 live gates。
- [ ] /// 实现 Review/Approval/本地包分派；远端能力未验证必须 fail closed。
- [ ] /// 跑无 Draft 的 Master→Variant→v5→Approval→ZIP 集成回归。

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
- [ ] /// 记录独立复核；只在实际完成后勾 OpenSpec 任务并本地提交，不推送/部署/归档。
