## Why
模型在用户的浏览器里点「发表」之后，回执的 status 也记成 `human_confirmed`，交付页也显示「人工已确认」，和用户自己回填的回执分不开。这批回执里有 5 条只有截图、没有作品链接，现在也和带链接的一样算作已发布。CT-001 审计查出了这个问题，用户 2026-11-16 裁决 C3：模型发表要和人工确认分开记录，没有 URL 的回执不计入「已核实发布」。

## What Changes
- **确认方由什么决定**：回执表 `delivery_receipt.verification_method` 本来就记着确认方式。模型浏览器发表那条路径（`browser_publish.record_published`）写的是 `third_party_model_browser`，其余路径都是人工（交付页回填时为空，另有 `human_reconciliation`、`human_attestation`）。这次直接按这个字段推出确认方：`third_party_model_browser` 算 `model`，其余算 `human`。**不加新字段，不加新状态，不迁移数据。** 现有 21 条模型回执本身已经带着 `third_party_model_browser`，所以不需要回填。
- **「已核实发布」的口径**：只看平台发布的作品（origin=studio）。满足下面任一条就算已核实：
  - 回执是人工确认的；
  - 记录上有平台作品链接（`canonical_url` 以 http 开头）。
  模型确认、又没有链接的，算「待补链接」。从外部导入的历史作品（origin=external_import）不参与这个口径，返回 null。
- **接口**：
  - `record_json` 增加三个字段：`confirmed_by`（`human` / `model` / null）、`publication_verified`（true / false / null）、`pending_link`（true / false）。
  - `GET /published-content` 增加两个数：`verified_total`（按当前筛选条件下的全部记录算，不只是当前这一页）和 `pending_link_total`。
  - 交付目标的回执列表里增加 `verification_method`。
- **交付页**：回执那一行，如果是模型发表的，显示「模型已发表」，不再只显示 `human_confirmed`。
- **补 3 条测试**：
  - Brand 的 tone_rules 不进入 Persona 的 expression_style；
  - 模型发表后没有 URL，不计入已核实发布；补上链接后计入；
  - 两个用户之间，品牌、账号、已发布记录互相越权访问返回 404。

## 为什么不新增状态 model_confirmed，也不新增 confirmed_by_kind 字段
- 新增状态 `model_confirmed`：`delivery_target` 的 CHECK 约束要改（SQLite 上只能重建表），另外大约 20 处判断 `human_confirmed` 的代码也都要改，包括发布记录同步、补链接、效果复盘、项目阶段判断等，改动面大，风险也大。
- 新增字段 `confirmed_by_kind`：它和现有的 `verification_method` 记的是同一件事，要多维护一份数据，还要回填和准备回滚。
- 直接用现有字段推出确认方：零迁移，回滚只要 revert 这一个提交。

## 不做
- 不改回执和交付目标的 status 取值，不改任何判断 `human_confirmed` 的流程，比如补链接、效果复盘、发布记录同步。
- 不改本地正式库。不做 allowed_brands，不做一个账号挂多个 Persona（裁决 C2）。不接 freepublish（裁决 C4）。

## Impact
- `apps/api/app/services/published_history.py`：新增 `publication_evidence()`，并在 `record_json` 里返回上面三个字段。
- `apps/api/app/routers/performance_history.py`：`list_history` 返回 `verified_total`、`pending_link_total`。
- `apps/api/app/routers/delivery.py`：回执 JSON 里增加 `verification_method`。
- `apps/web/src/product/ProjectReviewCenter.tsx`：回执那一行按确认方式显示「模型已发表」。
- 测试：`apps/api/tests/test_receipt_confirmer_kind.py`（新文件）。
