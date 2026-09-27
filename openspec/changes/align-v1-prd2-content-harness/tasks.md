# Tasks — align-v1-prd2-content-harness

> 强依赖顺序，不并行修改同一基础对象。来源：开发 OpenSpec §11。

## Phase 0 — Baseline / OpenSpec reconciliation

- [x] 0.1 读取 `git_status`/`git_diff`，记录未提交文件（5 modified + 未追踪文档），不 reset。
- [x] 0.2 `complete-prd-v1-channel-deliverables` 确认未实施，已标 `superseded_by=align-v1-prd2-content-harness`。
- [x] 0.3 本 change 建到 `openspec/changes/align-v1-prd2-content-harness/`（proposal/design/specs/tasks）。
- [x] 0.4 `openspec validate --strict --no-interactive` 通过（"align-v1-prd2-content-harness is valid"）。
- [x] 0.5 backend test baseline：141 passed（2026-09-24，mock provider），无既有失败。

## Phase 1 — Channel Registry + Workflow Versioning

- [x] 1.1 `models.py`：ChannelTemplate profile 字段、Topic targets_json、Workflow 版本字段、Run/Step 元数据、DraftCheckRun、ContentJob 扩展列。
- [x] 1.2 Alembic Migration A（`a1harness00001`，SQLite fresh + stepwise 验证通过；历史 Workflow 按 `legacy.workflow.<id>` 回填，dev 库 content_studio.db 已升级到 head）。
- [x] 1.3 新建 `content_harness/contracts.py`、`registry.py`、`channel_registry.py`。
- [x] 1.4 `templates.py`：profile schema/publish checksum 含 profile_json；normalize 去 Channel enum 遍历。
- [x] 1.5 `topics.py`：走 registry 校验，兼容 `channels`，新增 `targets`。
- [x] 1.6 `orchestrator.py`：target {channel, content_form}，去 Channel enum 新渠道依赖（x_thread 常量化）。
- [x] 1.7 `workflow_engine.py`：schema v1 compatibility + registry resolve；Run 冻结 key/version/checksum。
- [x] 1.8 现有 handler 包装为 builtin plugins（14 个 `builtin.*@1`），业务结果不变（test_workflows 全绿）。
- [x] 1.9 `workflow_templates.py`：保留 legacy templates，新增 `CATALOG_FAMILIES` 占位 catalog（Phase 7 实现）。
- [x] 1.10 `external.py` channel validation 改 registry（保留 `other`）。
- [x] 1.11 `sync_prompt_versions_from_files()` 遍历 prompts 目录实际文件。
- [x] 1.12 前端 `Topics.tsx`：动态 Channel/ContentForm targets（GET /channels，channel×form chips）。
- [x] 1.13 前端 `Workflows.tsx`：plugin key@version、Run 冻结元数据展示。
- [x] 1.14 前端 `Templates.tsx`：展示 profile_json（content form chips + JSON 展开）。
- [x] 1.15 新增 `test_channel_registry.py`（6）、`test_workflow_registry.py`（10）；全量 157 passed、web build 通过。

## Phase 2 — Material Library + Composition

- [x] 2.1 Alembic Migration B（`b2material00002`，fresh+stepwise 通过）。2.2 Material models/relations。2.3 `services/materials.py`。2.4 `routers/materials.py`（search 无 provider 返 422 capability_unavailable）。2.5 article_handoff 上传改走 materials service。2.6 DraftMedia placement/alt/caption。2.7 Draft document_json 操作 service（`document_composition.py`）。2.8 material/provider registry contract（`content_harness/providers.py`）。2.9 `generate_cover_image` 包装 `asset_provider.wewrite_image@1`。2.10 AssetMedia legacy：`_has_real_bytes` 排除 placeholder/SVG，schema v2 禁止 placeholder ready。
- [x] 2.11 前端 `Materials.tsx`（grid/upload/search/generate/rights/revision/usage/attach）。2.12 Workspace attach（素材库侧完成 attach/revoke；Workspace 内嵌编辑见 Phase 8 一并升级）。2.13 小红书卡片真实图片（Review/Workspace 走 raw 端点）。2.14 Review Preview 读 DraftMedia/MaterialRevision（raw 端点回退 revision）。
- [x] 2.15 测试：`test_material_library.py`（8）+ `test_artifact_composition.py`（5）：upload→revision、多稿复用、rights 撤权失效链、placement/document stale、approved 不可变、placeholder blocks ready、历史 DraftMedia 可读、adoption。

## Phase 3 — Generic Checks + SEO

- [x] 3.1 启用 `DraftCheckRun` 写入（checks.py）。3.2 FactCheck 双写兼容（generate.py 镜像 + approve 兼容补录）。3.3 Rule Registry + 首批内置规则（5 基础 + seo + finance×2 + tech）。3.4 Discoverability models/service/router。3.5 `ROUTE_KEYS+discoverability/platform_adaptation`。3.6 基础 discoverability profiles（seo.default / seo.wechat.article，幂等 seed）。3.7 SEO deterministic rules（seo_rules.py）。3.8 finance/tech rules 首批（domain_rules.py）。3.9 candidate readiness 读 generic checks（readiness_v2 + approve 自动补跑）。
- [x] 3.10–3.12 前端 SEO/checks 展示并入 ReviewPublish（偏差 D3-c）。
- [x] 3.13 测试：test_checks_v2（6）/ test_discoverability（4）/ test_finance_rules（4）/ test_tech_rules（3）。

## Phase 4 — Candidate Manifest v2 + Render

- [x] 4.1 `candidates.py` schema v2 builder + readiness_v2（v1 保留）。4.2 renderer registry（content_harness/renderers.py）。4.3 WeChat renderer。4.4 X Thread renderer。4.5 generic article renderer。4.6 XHS card manifest renderer。4.7 readiness Gate（checks current + 媒体真实权利 + render 冻结 + discoverability 声明才必需）。4.8 `reviews.py` v1/v2 dual path（mother→v1，非 mother→v2）。4.9 ContentAsset 保存 artifact/content_form/workflow 列（Migration C）。
- [x] 4.10 测试：test_renderers_v2（8）/ test_candidate_manifest_v2（5）：canonical hash stable、placement/SEO 变化 hash 变化、stale check 阻止 approve、v1 可读。

## Phase 5 — Delivery Router + WeChat Auto Draft

- [x] 5.1 Migration C（`c3delivery00003`，fresh+dev 库通过；ContentAsset 列折入，见 D4-b）。5.2 publisher contract/registry。5.3 `publisher.copy@1`。5.4 `publisher.wechat.wewrite@1`（unverified 如实标注；超长标题 fail 不截断）。5.5 `services/delivery.py`（唯一远端副作用入口）。5.6 `routers/delivery.py`（targets/execute/package/receipt/feedback/reconcile；manual_handoff 委托旧路径）。5.7 article_handoff 保留兼容 alias。5.8 关闭 schema v2 内容从 workflow_engine 直发路径（builtin.publish_wechat guard）。5.9 attempt prepared-before-call。5.10 unknown/reconciliation。5.11 Copy Package 用 renderer manifest（含实时权利复核 D5-d）。
- [x] 5.12 测试：test_delivery_router（7）：幂等授权、账号隔离、prepared→succeeded→remote_id、duplicate execute 409、timeout→unknown 不自动 retry、reconcile not_delivered→新 attempt、candidate mismatch、v2 旧路径封锁、包 hash/media 一致；真实远端为手工 acceptance script。

## Phase 6 — Node Rerun + Staleness

- [x] 6.1–6.2 `staleness.py` 统一失效（draft/media/SEO/素材撤权/invalid_candidate；D28）。6.3 Step input/output hash（engine `_execute_node`）。6.4 rerun node（新 attempt + output 变化→downstream stale）。6.5 rerun-from-here（当前+下游 pending，新 Revision 不回滚历史）。6.6 side-effect node rerun guard（单节点与 from-here 集合双重拒绝，D6-a）。6.7 Run context 保留历史 output（output_json 覆盖前已 commit 可审计）。
- [x] 6.8 前端重跑按钮 + stale 状态展示（Workflows.tsx）。6.9 stale 显示并入 Review Center。6.10 测试：test_workflow_rerun（6）/ test_staleness（4）。

## Phase 7 — V1 Platform Profiles / Writer Skills

- [x] 7.1 seed 14 个 channel profiles（幂等，`seed_v1_channel_profiles`）。7.2 shared workflow families（`FAMILY_STEPS` + `build_catalog_workflow`，schema v2 节点；catalog API 实例化）。7.3 外部 Skill references（profile publisher_candidates / skill metadata 机制已备；wewrite/XHS Skills 由 Discovery 发现）。7.4 built-in fallback writer（prompt 回退 wechat + generic render，D7-a）。
- [x] 7.5–7.19 Golden cases：`test_platform_profiles.py` 覆盖 16 个 channel×form 最小验收环（profile→workflow→draft→rules→candidate→copy package，mock 全链路）；不要求远端自动发布。

## Phase 8 — Unified Review & Publish Center

- [x] 8.1 `routers/review_center.py`（projection，不建新表）。8.2 Topic aggregate（topic/content_core/targets）。8.3 readiness projection（content/evidence/media/platform/delivery）。8.4 workflow timeline 投影（target.workflow_run）。8.5 delivery capability projection（publisher/capability/unverified 标注）。
- [x] 8.6–8.11 前端 `ReviewPublish.tsx` 完整版（左 targets/中文稿 preview+素材/右 checks+SEO+delivery；SEO 报告生成与 apply→新 revision；package 下载与 auto_draft execute）。8.12 `Review.tsx`/`Handoff.tsx` 保留 legacy（导航标「旧」，D8-b）。
- [x] 8.13 测试：test_review_center（2）：批准前/批准后投影、delivery 授权联动。

## Phase 9 — Docs / Acceptance / Migration Cleanup

- [x] 9.1 README 产品主链增量更新（不覆盖未提交改动）。9.2 原 PRD 顶部标注 legacy→指向 V1 PRD 2.0。9.3 HANDOVER 顶部增量说明。9.4 `docs/WORKFLOW_CANVAS_DESIGN.md` 顶部实施更新（registry/one-target-run）。
- [x] 9.6 fresh SQLite Alembic head（三次迁移 fresh+stepwise+dev 库验证）。9.8 backend full pytest：**220 passed**（基线 141 → +79 新测试，零回归）。9.9 ruff：新增代码全绿（仓库存量 I001 等未动）。9.10 web TypeScript build 通过。9.11 OpenSpec strict validation 通过。
- [ ] 9.5 runbook 备份与 Material bytes（待运维补充）。
- [ ] 9.7 PostgreSQL migration smoke（本地无 PG 实例；迁移均用 batch/服务端默认写法，待 CI/PG 环境执行）。
- [ ] 9.12 真实 WeChat 草稿验收（手工 acceptance script；默认测试已 mock subprocess）。9.13 XHS 实际图片 Candidate。9.14 雪球量化 Candidate。9.15 掘金技术 Candidate（三者 golden case 已在 mock 下全链路；真实素材/账号验收待人工）。
- [x] 9.16 平台 capability 记录：capability_snapshot_json 如实标注 verified/unverified；未验证平台保持 copy package + unverified。

## Phase 10 — R2 Acceptance Fix（复核 CONDITIONAL FAIL → 修复收口）

对应 `design.md` §R2（复核发现与修复）。阻断 4 + 高 3 + 中 3 全部代码级修复，并留命令级门禁证据。

- [x] 10.1 R2-B1：`/topics/{id}/generate` 按 target 启动独立 WorkflowRun（`ensure_bundle_workflow` 共享 Bundle + run 参数承载 target；异步模式 `advance_workflow_run` worker 任务）；golden test 重写为真实工作流链（16 target：/generate→run 冻结→approve 节点 complete→ContentAsset→copy package）。
- [x] 10.2 R2-B2：approve 无条件跑 media 规则 + `readiness_reasons_v2` 按 profile media_requirements 强制（小红书零图 blocker 先失败后补图通过，见 golden）。
- [x] 10.3 R2-B3：publisher.wechat.wewrite 删除 placeholder/digest 截断；缺已批准封面 fail、digest>120 fail。
- [x] 10.4 R2-B4：candidate v2 冻结 DiscoverabilityReport + execution.plugins（step 钉死记录）+ skills 引用 + discoverability_required；报告进入 candidate hash。
- [x] 10.5 R2-H5：`node.skill@1` SkillNodePlugin + `resolve_executable_runtime()`；preflight 无可执行 runtime 时启动前 409。
- [x] 10.6 R2-H6：`_enabled_skills()` 改读 `plugins.skills_enabled` + disabled 回归测试。
- [x] 10.7 R2-H7：Migration D（`d4audit00004` workflow_step_attempt，fresh+stepwise 通过）+ 四终态路径写审计行 + `GET /workflow-runs/{id}/nodes/{node}/attempts`；rerun 新旧 output 均可审计。
- [x] 10.8 R2-M8：`mark_media_changed` 粒度修正（fact_check_json 保留；仅 media/rights check runs stale）+ `checks.mark_kinds_stale` + 回归测试。
- [x] 10.9 R2-M9：`render_for` 由 profile renderer_key 驱动（x/thread 用 renderer.x.thread；未注册 renderer 降级 + warning）。
- [x] 10.10 R2-M10：unverified auto_draft 默认 409（`delivery.allow_unverified_auto_draft` 显式放行）；ReviewPublish 前端禁用按钮。
- [x] 10.11 节点 complete 端点权限放宽为 editor_or_reviewer（批准类人工节点由 reviewer 触发；节点内部仍走各自闸门）。
- [x] 10.12 新增 `tests/test_acceptance_r2.py`（12）+ 存量测试对齐（golden/candidate_v2/core_pipeline/workflows/delivery/rerun/preflight）；仓库存量 lint 债清理（ruff 全绿）。

### Phase 10 门禁证据（2026-09-24，命令级留档）

```text
cd apps/api && .venv/bin/python -m pytest tests/ -q
  → 238 passed, 5 warnings in 8.87s        （基线 220 → R2 批次 +18：acceptance_r2 12 + platform_profiles 重写净增）

.venv/bin/python -m ruff check app/ tests/
  → All checks passed!                      （含存量 lint 债清理）

cd apps/web && npm run build
  → ✓ built in 1.63s                        （vite tsc build）

openspec validate align-v1-prd2-content-harness --strict
  → Change 'align-v1-prd2-content-harness' is valid

git diff --check
  → clean（无空白错误）

迁移冒烟（fresh SQLite，stepwise）：a1harness00001 → b2material00002 → c3delivery00003 → d4audit00004
  → 全部 OK；workflow_step_attempt 表存在；alembic current = d4audit00004 (head)
开发库 content_studio.db 已 upgrade head（c3→d4 增量）；import app.main OK
```

未勾人工项不变：**9.5 runbook 备份、9.7 PostgreSQL migration smoke、9.12–9.15 真实账号/真实素材平台验收，共 6 项**（前次报告「4 项」为表述错误，已更正）。

## Phase 11 — R3 二次复核收口

对应 `design.md` §R3。archive blocker 3 + 次级 3 全部代码级修复。

- [x] 11.1 R3-1：`node.skill` 相对导入修正（`..` skill_runtime/contracts）；新增真实执行链测试（fake runtime 注册 → start_run 执行 → attempt 审计；测试自清理全局 registry）。
- [x] 11.2 R3-2：`builtin.discoverability_post@1` 节点 + 全部 9 个 family 插入（check/censor → disco → approve）；golden 不再手工 POST，SEO 报告由 Workflow Timeline 产出并冻结。
- [x] 11.3 R3-3：`validate_live_candidate_payload()`（manifest 完整性 + render 冻结 + 实时权利 + 字节 SHA-256 对批准 hash）在 prepare attempt 前统一执行；算改/撤权 → 409 且零 attempt、publisher 零调用。
- [x] 11.4 R3-4：`skills_enabled` 三态（未配置=默认政策 / []=全禁用 / 白名单）；三态测试。
- [x] 11.5 R3-5：`services/draft_fork.py` 统一 fork（media use 克隆 + document 重建 + stale 起步）；`update_draft` 与 `apply_suggestion` 收敛；fork/SEO apply 继承测试。
- [x] 11.6 R3-6：`invalidate_candidate` 只写审计不改历史 manifest；测试断言 manifest 不变 + AuditLog 存在。
- [x] 11.7 存量对齐：delivery（注入封面须在 authorize 前并重算批准 hash）、staleness（immutable 断言）、platform_profiles（disco 节点断言）、acceptance_r2（disco 由节点产出新前提）。

### Phase 11 门禁证据（2026-09-24，命令级留档）

```text
cd apps/api && .venv/bin/python -m pytest tests/ -q
  → 243 passed, 5 warnings in 8.95s        （R2 收口 238 → R3 +5 净增）

.venv/bin/python -m ruff check app/ tests/
  → All checks passed!

cd apps/web && npm run build
  → ✓ built in 1.61s

openspec validate align-v1-prd2-content-harness --strict
  → Change 'align-v1-prd2-content-harness' is valid

git diff --check
  → clean

迁移：R3 无新迁移（d4audit00004 仍为 head；dev 库已在此版本）
```

未勾人工项不变：9.5 / 9.7 / 9.12–9.15 共 6 项（真实环境验收）。

## Phase 12 — R4 Contract & Rights Integrity

对应 `design.md` §R4。blocker 3 + 高优 2 + 非 blocker 2 全部修复。

- [x] 12.1 R4-B1：`node_config_of()`（params/config 合并、config 优先）——`start_run` 与 preflight 共用；skill 执行测试改用正式 v2 `config` schema。
- [x] 12.2 R4-B2：`workflow.social.short` / `workflow.script.spoken` 插入 `fact_check` 节点；golden 移除手工 /fact-check 补调用，断言 check 节点 succeeded（16 target 工作流自洽）。
- [x] 12.3 R4-B3：`rules.effective_media_rights()` 统一判定（use 四态 + revision 全局撤权）——rule/readiness/Review Center 共用；delivery `_live_media_rights` use 路径补全局检查；全局撤权 → rule blocker + readiness blocker 测试。
- [x] 12.4 R4-H4：fork 继承修正——撤权字段随 use 克隆；title-only 克隆 document 并映射 use id（保留手工编排）、body 变更才重建；body-changing 清空 structured/thread_posts（title-only 继承）。三个方向测试。
- [x] 12.5 R4-N1/N2：copy package 媒体扩展名按 mime 推导（JPEG→.jpg 测试）；Review Center media readiness 结合 media_requirements + effective rights（零图小红书 blocked → 补图 ready 测试）。
- [x] 12.6 R4 无新迁移（d4audit00004 仍为 head）。

### Phase 12 门禁证据（2026-09-24，命令级留档）

```text
cd apps/api && .venv/bin/python -m pytest tests/ -q
  → 249 passed, 5 warnings in 8.20s        （R3 收口 243 → R4 +6 净增）

.venv/bin/python -m ruff check app/ tests/
  → All checks passed!

cd apps/web && npm run build
  → ✓ built in 1.63s

openspec validate align-v1-prd2-content-harness --strict
  → Change 'align-v1-prd2-content-harness' is valid

git diff --check
  → clean
```

未勾人工项不变：9.5 / 9.7 / 9.12–9.15 共 6 项（真实环境验收）。

### Phase 12.1 — R4.1 Contract Consistency Fix

- [x] 12.1.1 `node_config_of` 下沉 `contracts.py`；`_referenced_skills` / `_is_target_agnostic` / `start_run` 统一（混合 params+config 盲区关闭，含测试）。
- [x] 12.1.2 `_live_media_rights` use 行优先、经 `effective_media_rights` 判定（use 级撤权旁路关闭）；回归：批准→仅撤 use→撤权后建 target→copy package 409 + auto_draft 409 + 零 attempt。

### Phase 12.1 门禁证据（2026-09-24，命令级留档）

```text
cd apps/api && .venv/bin/python -m pytest tests/ -q
  → 252 passed, 5 warnings in 8.25s        （R4 收口 249 → R4.1 +3）

.venv/bin/python -m ruff check app/ tests/
  → All checks passed!

cd apps/web && npm run build
  → ✓ built（见下）

openspec validate align-v1-prd2-content-harness --strict
  → Change 'align-v1-prd2-content-harness' is valid

git diff --check
  → clean

迁移：R4.1 无新迁移（d4audit00004 仍为 head）
```

未勾人工项不变：9.5 / 9.7 / 9.12–9.15 共 6 项（真实环境验收）。
