# ADR: Persona-owned Editorial Series 与投放绑定的持久化方案

- **日期**：2026-10-14（Phase 0 / SPEC_REVISED 轮）
- **状态**：Proposed —— 待独立 SPEC 复核；正式库执行另需用户明确授权与备份
- **决策范围**：`complete-multiplatform-content-handoff` v2 批次 A（任务 5.1–5.3）
- **实时代码基线**：`main@4646ad3` + 未提交工作区；alembic head 实测 `idx000000001`（30 revisions）

## 1. 已核验的现状事实（2026-10-14 实测）

| 事实 | 位置 | 实测结果 |
|---|---|---|
| `ContentSeries.account_id` | `apps/api/app/models.py:1579` | `Mapped[int]`（NOT NULL）FK → `content_account.id` |
| 选栏目必须选账号 | `apps/api/app/services/content_identity.py:121-122` | `series_id is not None and account is None` → 422“选择栏目时必须选择所属账号” |
| `ContentUnit.account_id / series_id` | `apps/api/app/models.py:1717-1718` | 均可空 |
| v5 交付 409 锁 | `apps/api/app/services/delivery.py:173-174` | `is_variant and unit.account_id is not None and content_account_id != unit.account_id` → 409 |
| IdentitySnapshot 结构 | `apps/api/app/models.py:1598-1616` | brand/persona/account/series 的 id+revision_id 均可空，冻结 checksum |
| Series 版本真源 | `models.py:1585`（ContentSeriesRevision） | 存在，`profile_json` + `revision_no` + `checksum`，可承载栏目配置 |
| 交付账号唯一键 | `models.py:1549-1550` | `(platform_channel, platform_account_id)` 唯一；同平台多账号=多行，已支持 |
| 交付幂等键 | `models.py:1062-1065` | `uq_delivery_target_authorization` 含 `authorization_account_key`（`content-account:{id}`），同平台多账号可并存 |

结论：**账号多行并存与逐账号授权/幂等键在现 schema 已可用**；真正缺的只有两件事——(a) 栏目脱离账号归属的表达，(b) 栏目×账号×形态投放绑定的持久真源。

## 2. 备选方案

### 方案一：零迁移（复用现有列/JSON）

- 做法 A：把 Series×Account×Form 绑定写进 `ContentSeriesRevision.profile_json`。
- 做法 B：不建栏目真源，用“同名 Account Series 约定”表示同一跨平台栏目。

**拒绝**（对应 design D-v2.9）：

1. 做法 A 无稳定行标识、无独立 CAS、无外键、无审计主体；绑定启停要重写整份 profile_json 修订，与栏目创作配置版本耦合，任何读取方都无法对“一条绑定”做引用或权限判断。
2. 做法 B 无法检测同名冲突（两个账号各建“技术拆解”栏目，系统不能证明是同一企划），且换账号=换 Series 身份，冻结快照语义破碎。
3. `account_id NOT NULL` 使“无账号栏目”在零迁移下根本无法建行——除非塞虚拟账号行，制造假 `content_account` 记录污染账号唯一键与运营页。
4. 零迁移判定门槛（design D-v2.2）要求“现有稳定持久实体已可作 Persona-owned 唯一真源且有独立版本与投放关系”——实测不满足。

### 方案二（推荐）：最小增量迁移，演进唯一 `ContentSeries` 真源

```text
升级 1（改既有表，additive）：content_series
  + scope        VARCHAR(20) NOT NULL DEFAULT 'account_legacy'   -- 'persona_editorial' | 'account_legacy'
  + persona_id   INT NULL FK content_persona.id                  -- persona_editorial 必填
  ~ account_id   改为 NULLABLE                                    -- 仅 persona_editorial 可为空
  + CHECK: (scope='account_legacy' AND account_id IS NOT NULL AND persona_id IS NULL)
       OR (scope='persona_editorial' AND persona_id IS NOT NULL AND account_id IS NULL)
  存量行 backfill：scope='account_legacy'（默认值达成，不重写历史）

升级 2（新表）：series_account_target
  id, series_id FK content_series.id, account_id FK content_account.id,
  content_form VARCHAR(100), enabled BOOLEAN, version INT（CAS）, created_by/at, updated_at
  UNIQUE(series_id, account_id, content_form)
```

- 复用既有 `ContentSeriesRevision` 承载栏目版本/创作配置；`identity_snapshot`、`hierarchy()`、`effective()` 按 scope 分支，legacy 分支行为逐字节保持。
- `hierarchy()` 新分支：persona_editorial 只要求 persona 归属，不要求 account；legacy 分支原校验原样。
- `delivery.py` 修改按 design D-v2.4 新合同，不碰 legacy Candidate 分支。

**为什么最小**：不动 `content_account`/`identity_snapshot`/`content_unit`/交付四表；两处变更都可直接由现表推导；老数据零重写（scope 默认值即 backfill）。

## 3. 风险与对策

| 风险 | 对策 |
|---|---|
| SQLite 修改列非空性需 batch rebuild（重建全表） | Alembic `batch_alter_table`；先在复制的测试库跑 upgrade+downgrade 全程演练；正式执行前对 `content_studio.db`（含 WAL checkpoint）做文件级备份并记录 schema/行数指纹 |
| `hierarchy()`/快照回归面广 | 任务 5.8 要求持久回归覆盖 legacy 分支逐字节行为 + persona_editorial 新分支；IdentitySnapshot 读写两侧都要测 |
| 破坏性 downgrade 丢 editorial 数据 | downgrade 在 `scope='persona_editorial'` 行数>0 或 `series_account_target` 非空时 fail-closed 拒绝；只有全空才允许回退 |
| 与未提交工作区冲突 | apply 前先盘点 73 条未提交/未追踪条目；本 ADR 不迁移任何业务行 |
| 投放绑定被当授权书用 | 规格已定（persona-channel-series-operations）：绑定只是可选择性，不绕过 Review/Authorization/CapabilityVerification |

## 4. 决策

采用**方案二**。方案一被零迁移判定门槛明确排除。若独立 SPEC 复核发现既有等价 Persona-owned Series 机制（本轮实测未发现），需回到本 ADR 重议而非绕过。

## 5. 授权边界

本 ADR 仅为规格决策记录。`alembic upgrade`、正式库写入、测试库演练的执行都属于批次 A（任务 5.1），须在独立 SPEC APPROVE 与 BUSINESS_APPLY 授权之后进行。

## 6. 独立复核补充证据（2026-10-14 SPEC review）

回应 `REVIEW_PENDING` 第 1/2/3/4 项的实测证据（全部只读）：

- **正式库事实**：`alembic_version` 实测 `idx000000001`（与本报告一致）；`PRAGMA table_info(content_series)` 确认 `account_id INTEGER NOT NULL`（notnull=1）；`SELECT COUNT(*)` = **0 行**——本机无存量栏目，迁移 backfill 在本环境为空操作，但 scope 默认值与 legacy 分支仍对 IdentitySnapshot/测试夹具/历史语义生效。执行正式迁移时仍须按第 5 节重新确认实况 head，不得沿用本文数值。
- **batch rebuild 先例**：`batch_alter_table` 已在 `f8a000000001`（user 表）、`f6e000000001`（content_asset）、`f6a000000001`、`g31415926535`（delivery_target/receipt）、`f7b000000001`（capability_verification）使用——方案二的 batch rebuild 是本仓既有模式，非新风险类别。
- **scope 分支全量站点**：六处（`owned_entity`/`hierarchy`/series 路由/`project_authorization` join/`project_matrix` 校验/`IdentityWorkspace` UI），明细表见 design D-v2.2 复核补充；`seed.py`/`starter_personas.py` 无 ContentSeries 引用，无其他创建路径。
- **跨 Persona 拒绝已有底座**：`ContentAccount.persona_id` NOT NULL FK（models.py:1554）；`delivery.py:177` 已拒绝 `account.persona_id != unit.persona_id` 的账号。`series_account_target` 的跨 Persona 校验复用同一字段，Batch A 只需在绑定服务层强制 `target.account.persona_id == series.persona_id`。
- **v5 逐账号幂等已结构正确**：`uq_delivery_target_authorization` 含 `authorization_account_key`；幂等回查两次（delivery.py:247-257 常规、311-323 并发）均以 account_key 为键；`platform_channel+platform_account_id` 唯一且绑定不可变（`platform_identity_immutable`），绑定行的 content_form 兼容性稳定。Batch A 5.5 仅需移除 173-174 行等值锁并补目标账号上下文冻结（5.4），无需改幂等结构。
- **唯一性补充**：`series_account_target` unique(series_id, account_id, content_form) 之外，启用校验必须另经 `resolve_content_form(db, account.platform_channel, content_form)`，保证绑定只指向该账号平台的真实形态（delta C1 "Explicit Series distribution targets" 已覆盖）。
