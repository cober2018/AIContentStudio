# Design — align-v1-prd2-content-harness

> 来源：`AIContentStudio_V1_PRD2_开发OpenSpec_代码级_2026-09-24.md` §3–§5、§14–§17。原文为唯一基准，本文件是结构化投影。

## 总体架构

```text
Source / Evidence / FactPack → Topic → MotherRevision → Channel Selection
  → 每个 channel × content_form 一个独立 WorkflowRun（Content Harness）
  → Skills / Rules / SEO / Material / Render
  → Draft Revision + Document + Material Uses + Check Runs
  → Review & Publish Center → Candidate Manifest v2 → Approval
  → DeliveryTarget → DeliveryAttempt → Copy / Assisted / Auto Draft → Receipt → Feedback
```

## 关键设计决策（D1–D28）

| # | 决策 | 要点 |
|---|---|---|
| D1 | 不重命名现有业务表 | 产品语义 Content Core/Artifact Revision/Material/Candidate；代码继续用 MotherRevision/Draft/DraftMedia/ContentAsset |
| D2 | 提升 ChannelTemplateVersion 为 Channel Profile 载体 | 新增 `profile_schema_version`+`profile_json`（content_forms → artifact_kind/workflow/renderer/rule_sets/seo profile/publishers/media_requirements）；保留 structure 等兼容字段 |
| D3 | 新建 ChannelRegistry Service | `resolve_channel / resolve_content_form / list_channels / validate_target`；业务代码禁用 `channel in {c.value for c in Channel}`；enum 保留仅供兼容，禁止新增 enum item 接新渠道 |
| D4 | Workflow 变成版本化 Definition | 新增 workflow_key/version/parent_id/status/schema_version/checksum；unique(workflow_key, version)；历史行 workflow_key=`legacy.workflow.<id>`、version=1、schema_version=1（deviation：原文按 template_key 回填会同 key 冲突撞 unique，改为 id 兜底） |
| D5 | WorkflowRun 冻结 Definition 身份 | 新增 topic_id/channel/content_form/workflow_key/workflow_version/definition_checksum（nullable）；一个 Platform×ContentForm=一个 Run |
| D6 | Node Registry 替代 HANDLERS 中央 Map | `content_harness/registry.py`+`contracts.py`+`nodes/`；NodePlugin(key,version,human_gate,execute)；旧 handler 薄包装为 `builtin.*@1`；engine 只调 `registry.resolve` |
| D7 | Workflow Definition schema v2 | 节点 `{id,plugin,plugin_version,label,config,layout}`；schema v1 `{id,type,params}` 由 loader 内存映射（type=generate→builtin.generate@1），不迁移历史 JSON |
| D8 | WorkflowStep 保存执行版本与 hash | 新增 plugin_key/plugin_version/input_hash/output_hash/stale_reason/attempt_no；status 扩展 stale |
| D9 | Material + MaterialRevision，DraftMedia 变 Use/Placement | material(kind/title/tags/status)；material_revision(revision_no/parent/content_hash/file/rights/provider/prompt…)；DraftMedia 新增 material_revision_id/placement_json/alt_text/caption；旧数据不批量复制（显式 adoption） |
| D10 | AssetMedia 进入 Legacy Compatibility | 新受控内容唯一批准真源=DraftMedia/MaterialRevision→Candidate Manifest；禁止新 Candidate 把 SVG placeholder 当 media |
| D11 | Draft 增加 artifact_kind/content_form/document_json | artifact kinds: text/image/script（预留 video/audio）；Document v1 blocks（paragraph/image+placement）；Markdown 仍是文本真源 |
| D12 | 通用 DraftCheckRun | check_kind(fact/platform/safety/rights/seo/domain/media)/profile/input_hash/status(pass/warning/blocker/incomplete/stale)/report_json；`Draft.fact_check_json` 双写兼容 |
| D13 | Rule Registry 是代码 Registry | `content_harness/rules.py`；先内置 rule.fact.bound / rule.media.* / rule.platform.required_fields / rule.finance.* / rule.tech.* / rule.seo.required_fields；确定性规则不用 LLM |
| D14 | Discoverability 独立 Profile+Report | `discoverability_profile_version`（unique profile_key+version）+ `discoverability_report`（stage pre/post、topic/mother/draft 可空、input_hash、status） |
| D15 | SEO 走现有 LLM Route | `ROUTE_KEYS+discoverability`；Pre: search_intent/queries/entities/questions/gaps/outline；Post: title/coverage/description/tags/alt/issues；SEO 不自动改 Draft，应用建议=新 Draft Revision |
| D16 | Skill Registry 扩展 metadata | frontmatter version/license/kind/capabilities，缺省 unversioned/unknown/skill；不 vendor 第三方代码 |
| D17 | Skill Execution 与 Discovery 分离 | `skill_runtime.py` 协议；dsh adapter 仅在真实契约核实后实现；Workflow preflight 发现 skill 缺失 |
| D18 | Candidate Manifest schema v2 | source/content(document)/media(placement/rights)/checks/discoverability/render/execution(workflow+plugin 快照)/declarations/citations；hash 对 canonical JSON 计算 |
| D19 | Renderer Output 批准前冻结 | `content_harness/renderers.py`：render(candidate_source)→RenderResult(key/version/payload/content_hash/warnings)；Publisher 不做实质格式变换 |
| D20 | DeliveryAction 扩展 | manual_handoff(legacy alias)/copy_package/assisted_draft/auto_draft；V1 不加 auto_public_publish |
| D21 | DeliveryTarget 约束改服务层验证 | 移除 channel enum check；action check 扩四值；平台合法性由 ChannelRegistry+PublisherRegistry 验证 |
| D22 | 新增 DeliveryAttempt | attempt_no/idempotency_key/publisher/request_hash/status(prepared/running/succeeded/failed/unknown)/remote_id；先持久化 prepared→COMMIT→调远端→写结果；超时=unknown+target=reconciliation_needed，不自动 fallback 重发 |
| D23 | Publisher Registry | `content_harness/publishers/`；PublisherPlugin.capability/deliver；首批 publisher.copy@1、publisher.wechat.wewrite@1 |
| D24 | 公众号草稿移出 Workflow 副作用 | 新流程：Approved Candidate→Target(auto_draft)→Attempt→publisher；Publisher 用批准 render payload，不得临时改 title/正文/封面；长度不符→重新修订→re-render→re-approve |
| D25 | Copy Package 成为通用 Publisher | manifest.json/content.*/media//publish-guide.md，文件清单由 renderer 定义 |
| D26 | Review & Publish Center 是 Projection | `routers/review_center.py` 聚合既有实体，不建 ReviewCenter 表；readiness 是投影 |
| D27 | Node-level Rerun | `rerun`（新 attempt，成功且 hash 变化→downstream stale，不自动重跑）；`rerun-from-here`（当前+downstream 置 pending，产生新 Revision）；Publisher 副作用节点禁止泛化重跑 |
| D28 | Staleness Service | `content_harness/staleness.py`：mark_draft_changed/mark_media_changed/mark_discoverability_changed/invalidate_candidate/mark_workflow_downstream_stale；统一散落的 stale 逻辑 |

## 数据库迁移（三次 additive）

- **Migration A `add_v1_content_harness_registry`**（Phase 1）：channel_template_version+profile 字段；workflow+key/version/status/schema/checksum+unique；workflow_run+6 元数据列；workflow_step+6 执行列；draft+artifact_kind/content_form/document_schema_version/document_json；新建 draft_check_run；content_job+content_form/artifact_kind/workflow_run_id/channel_profile_version_id；topic_brief+targets_json/product_ref/business_line。Backfill：旧 Workflow schema v1；Draft artifact_kind（douyin→script 其余→text）与 content_form（wechat→article/xiaohongshu→image_note/douyin→spoken_script/x_thread→thread）。不改旧 candidate hash。
- **Migration B `add_v1_material_and_discoverability`**（Phase 2）：material/material_revision/discoverability_profile_version/discoverability_report 建表；draft_media+4 列；不批量复制旧 DraftMedia。
- **Migration C `generalize_delivery_targets`**（Phase 5）：delivery_attempt 建表；delivery_target+publisher_key/publisher_version/capability_snapshot_json/requested_at；重建 check constraints（去掉 channel enum，action 扩四值）；历史 target publisher_key=`publisher.copy.legacy`。

## 兼容与安全不变量

- frozen evidence 永不漂移；旧 revision 永不覆盖；批准的是 actual media 不是 prompt；candidate hash 覆盖公开 payload；content approval ≠ delivery authorization；publisher 不得改已批准内容；unknown 远端结果不自动重试；新增渠道不要求改 workflow_engine。
- 禁止伪造性 backfill：不给旧图补 rights=true、不把 placeholder 变 actual material、不把旧 draft 标 ready、不把旧 workflow 标 v2、不把旧 receipt 标 verified、不把旧 Export 标 success。
- Material：上传双校验 MIME+signature、content-addressed 路径、非公开素材 raw 鉴权（不复用无 Header 的 `<img>` 模式）、SSRF 防护。Publisher 只拿所需 Secret，attempt 记录不含 token/cookie。

## Rollout

Milestone A（Harness Core：Registry/Workflow/Material/Check/Candidate v2，用 WeChat+X Thread 跑通）→ B（XHS/雪球/掘金/知乎文章+回答）→ C（头条/百家/搜狐/企鹅/网易/B站/微博）→ D（逐平台验证 Publisher，未验证平台保持 Copy Package + `unverified` 标识）。

## 实施批次

C2C-01 Channel/Workflow Registry（=Phase 1）→ C2C-02 Material → C2C-03 Checks+Discoverability → C2C-04 Candidate v2+Render → C2C-05 Delivery Router+WeChat → C2C-06 Rerun/Staleness → C2C-07 Platform Profiles → C2C-08 Review & Publish Center → C2C-09 Acceptance/Docs。每批次以 diff review + tests 为完成依据，不以自述判定完成。

## Deviations（实施期偏差记录，供评审 Agent 订正）

> 原则为：与原文冲突时记录在案并给出理由；实现取向始终满足 §10 需求语义。

### Phase 1（C2C-01）
- **D1-a Workflow 历史 workflow_key 回填改为 `legacy.workflow.<id>`**：原文 Decision 4 按 `legacy.<template_key>` 回填，但同模板多实例会撞 `unique(workflow_key, version)`；id 兜底保证约束可满足。
- **D1-b ContentJob 扩展列并入 Migration A**：原文 §6.9 要求 content_form/artifact_kind/workflow_run_id/channel_profile_version_id，但 §5 迁移清单漏列；提前并入 A（additive）。
- **D1-c 模板实例 workflow_key=`legacy.<template_key>`、status=published、schema_version=1**：Phase 1 模板实例仍为 v1 定义（引擎经 registry 兼容解析）；v2 catalog 定义在 Phase 7 切换。
- **D1-d 人工节点判定改读 plugin descriptor 的 `human_gate`**（v1 type 集合兜底）：原文未明确 schema v2 节点如何被判人工门；descriptor 是 D6 语义的自然落点。

### Phase 2（C2C-02）
- **D2-a DraftMedia(use) 无独立字节时 raw 路径回退 MaterialRevision**：原文未提及 use 行与 M1 raw/package 路径的字节关系；已实现 raw 端点回退，article_handoff 上传的新 use 行直接共享 revision 的 content-addressed 文件以保持 M1 package.zip 兼容。
- **D2-b attach 必须走 relationship 追加**：`DraftMedia(draft_id=...)` 直插不会更新 `draft.media` 集合，同事务 document sync 读到旧集合（实现约束，非产品语义）。
- **D2-c 真实媒体判定 `_has_real_bytes` 同时看 use 行与 revision**：mime 含 svg / metadata.placeholder / 双侧无 file_path → 非真实媒体（原文只说 placeholder SVG 不算，未给判定算法）。
- **D2-d Rule Registry 提前到 Phase 2 落地 5 条规则**（fact.bound / media.required / media.public_rights / media.order / platform.required_fields）：artifact-composition 的「placeholder 不算成品」验收依赖 rules，原文排在 Phase 3。
- **D2-e legacy 渠道 media_requirements 兜底**：无 profile 时 wechat 封面必需、其余不强制（原文 §5 未给 legacy 渠道的 media_requirements 映射）。
- **D2-f Materials Search/Generate 当前无内置搜索 provider**：`POST /materials/search` 恒 422 capability_unavailable（原文要求不返回假数据）；`generate` 复用 `asset_provider.wewrite_image@1`（依赖设置页 AI 生图开关）。

### Phase 3（C2C-03）
- **D3-a 批准路径对非 M1 内容自动补跑确定性检查**：原文未定义 platform/media/domain 检查的触发时机；实现为 approve(v2) 时自动运行（输入绑定、可复算），fact check 仍必须先于批准存在；历史稿只有 `fact_check_json` 无 run 时兼容镜像补录。
- **D3-b mandatory 集合 = fact + platform（+domain for finance/tech）**：media/rights 在「有素材」时才参与阻断（无素材不阻断）——与 D4-a 一并构成对旧 wechat 无封面批准流的兼容。
- **D3-c Discoverability 前端面板并入 ReviewPublish（Phase 8）**：原文 3.10–3.12 要求改 Workspace/Review；为避免在三个页面重复建设检查/SEO 展示，统一并入新的 Review & Publish Center。
- **D3-d ROUTE_KEYS 增加 `discoverability` + `platform_adaptation`**（§6.21 全量落地）；mock provider 下 Pre/Post 报告为 `incomplete`（不伪造 ready）。

### Phase 4（C2C-04）
- **D4-a schema v2 批准路径按「非 mother_revision 内容」划分**：M1 母稿内容保持 v1 manifest + 原 Gate；新 V1 内容走 v2。原文未给出 v1/v2 的判定字段。
- **D4-b ContentAsset 查询列并入 Migration C**：§6.23 的 artifact_kind/content_form/workflow_key/workflow_version 未列入 §5 迁移清单；折入 Migration C 避免第四次迁移。
- **D4-c 渠道→renderer 静态映射兜底**：profile 未声明 renderer_key 时按渠道映射（wechat→article、x_thread→thread、xiaohongshu→cards、其余→generic.markdown）。
- **D4-d `test_wechat_auto_draft_delivery.py` 并入 `test_delivery_router.py`**（语义同一执行链：prepared-before-call/timeout/reconcile 均为 wechat auto_draft 场景），不重复建设。

### Phase 5（C2C-05）
- **D5-a delivery_target 约束重建为「仅 action 四值 check」**：渠道 check 删除；平台合法性完全由 ChannelRegistry+PublisherRegistry 服务层验证（原文 Decision 21 的完整落地）。
- **D5-b auto_draft 成功后 target=awaiting_manual_receipt**：远端动作是「草稿箱创建」，人工仍需在平台发布并回填 receipt——复用 M1 状态机语义，不新增 enum 值（原文未指定成功后的 target 状态）。
- **D5-c unknown 对账 not_delivered 后允许新 attempt**：`DeliveryAttempt#N+1` 与历史 attempt 并存可审计；prepared/running/succeeded 仍禁止重复。
- **D5-d v2 成品包对素材做实时权利复核**：批准快照后撤权（revision revoked / use revoked）阻止导出并阻断目标（与 M1 `get_package` 同语义；原文只写了 M1 路径）。

### Phase 6（C2C-06）
- **D6-a rerun-from-here 对波及的 side_effect 节点整体拒绝**：原文只规定单节点 rerun 拒绝副作用节点；from-here 会自动推进下游、同样可能触达远端，因此从节点集合层面拒绝。
- **D6-b stale 步骤不自动重跑**：rerun 只标 stale，重跑由用户显式触发（UI 按钮）——与原文「不自动重跑 downstream」一致，此处记录 UI 承载方式。
- **D6-c `attempt_no` 初值为 0（start_run 首次执行不递增）**：rerun 后从 1 计（原文未定义首跑语义）。

### Phase 7（C2C-07）
- **D7-a built-in fallback writer 的实现位置**：`compose_prompt` 无渠道专属 prompt 文件时回退 `wechat.txt`；mock provider 未知渠道回退 wechat 结构；`render_body` 未知渠道走 generic markdown。原文 7.4 要求 fallback 但未定义实现。
- **D7-b 14 平台 profile 以 `ChannelTemplateVersion`(version=100, published, profile_json) 承载**：幂等 seed 判重以「该渠道已存在 profile 行」为准；profile 行发布时会按既有 normalize 规则下线同渠道 legacy 模板（ContentJob 历史 id 引用不受影响）。
- **D7-c golden cases = 16 个 channel×form 目标**（14 渠道，zhihu/x 各双形态）在 mock 下跑通最小验收环：profile resolves → workflow instantiates（plugin 可解析）→ draft renders → required rules run → candidate builds（v2 批准）→ copy package builds；远端自动发布一律不验证、capability 标注 unverified（`publisher.wechat.wewrite.verified=False`）。

### Phase 8（C2C-08）
- **D8-a readiness.media 的「无素材」态显示 `none`**：原文 §7.1 示例未定义无素材场景；有素材时按 rights 判 ready/warning/blocked。
- **D8-b ReviewPublish 旧页保留**：`Review.tsx`/`Handoff.tsx` 保留为 alias/legacy 视图（导航标「旧」），未做 redirect——避免破坏既有入口，符合原文「旧页面可 redirect / legacy display」的宽松表述。

### 验收补缺（Acceptance pass，2026-09-24）
- **A-1 验收发现的缺口已补齐**：① plugin_registry frontmatter 扩展 version/license/kind/capabilities（§6.12/D16）；② `content_harness/skill_runtime.py` 契约 + BuiltIn adapter（如实 unavailable；dsh adapter 按原文不猜 endpoint 不注册）；③ Workflow preflight（技能缺失启动前 409，`start_run` 前置）；④ `POST /workflows/{id}/clone|publish`（published immutable，修改=clone 新版本）；⑤ Workspace.tsx 渠道标签改 `/channels` 动态拉取（§1.2.A 最后一个前端硬编码点）。
- **D-async 引擎异步化债务（§16 明确要求记录）**：新 v2 节点执行仍为同步推进（与 legacy 一致）；`publisher.wechat.wewrite` 单次调用 180s 超时（非盲目重试，失败/超时即终止并落状态）。目标形态 `dispatch → step running → worker callback → engine continue` 留待后续变更；UI 已按轮询 Run 读取状态，不依赖请求内长等待返回结果以外的行为。

### R2 验收复核发现与修复（Acceptance Fix 批次，2026-09-24）

独立复核（静态代码核对）判定 CONDITIONAL FAIL，提出 4 阻断 + 6 次级问题。逐项核实均属实，本批次全部修复；修复本身构成对既有偏差的**取代/修订**，记录如下（编号沿用复核结论）：

- **R2-B1 主生产入口绕过 WorkflowRun（阻断）**：`/topics/{id}/generate` 原直接 `create_jobs_for_topic`。修复：按 target 解析 profile `default_workflow_key` → `ensure_bundle_workflow()`（复用/创建 target 无关的共享 Bundle Workflow，version 递增、checksum 冻结）→ `start_run`（params 携带 topic/channel/content_form）。节点链在 run 内执行（gen→humanize/censor→check→approve 挂起），ContentJob 挂 `workflow_run_id`。批准可经引擎 approve 节点 complete（内部调用同一 Review Gate，§0 不建第二审批系统）或 Review Center 页面。legacy 渠道（无 profile，如 x_thread 兜底）保留直连生成（M1 兼容）。
  - **修订 D7-c（golden 验收环）**：golden test 不再「先建 workflow 再绕开」，而是断言 /generate 返回 run_id、冻结 family、批准节点经引擎 complete 走到 ContentAsset → copy package。
  - **新增偏差 D-R2-1（共享 Bundle 的 target 承载）**：原文 §9.1「多平台复用 Workflow」未定义 channel 如何进入节点。实现为节点不携带 channel，`step.params_json.channel` 优先、`run.params_json.channel` 兜底（`_channel_of`）；catalog 页面实例化（带 channel 参数烘焙）行为不变，`ensure_bundle_workflow` 只复用 target 无关定义（`_is_target_agnostic` 判据），避免跨渠道误用烘焙副本。
  - **新增偏差 D-R2-2（异步模式的推进载体）**：`TASK_QUEUE_ENABLED` 时 generate 请求只创建 run（`start_run(advance_now=False)`），由 `worker_tasks.advance_workflow_run`（default 队列）推进；生成任务仍走 llm 队列（与画布现状同构，依赖 EPIC-17 的分队列部署）。
- **R2-B2 零图小红书可批准（阻断）**：`rule.media.required` 原以 `if draft.media:` 为前提、`_media_requirements()` 无调用方。修复：approve 无条件运行 media 规则集；`readiness_reasons_v2` 直接按 profile `media_requirements` 强制（missing_required_cover / missing_required_inline_media，placeholder/Prompt 不算成品）。legacy 渠道沿用 wechat 封面必需兜底。
- **R2-B3 Publisher 修改批准载荷（阻断）**：`publisher.wechat.wewrite` 原无封面时现场生成 placeholder PNG、digest `[:60]` 截断。修复：无已批准封面字节 → fail（candidate blocker → 回 Review Center 补图 → 新 Candidate）；digest 只取批准值，超 120 字 fail 不截断。`_placeholder_png` 从 publisher 删除（legacy `_h_publish_wechat` 的占位为 M1 显式启用路径，保留并继续受 v2 guard 封锁）。
- **R2-B4 Candidate v2 未冻结 SEO/插件版本（阻断）**：`build_manifest_v2` 原 `discoverability: None`、`execution.plugins` 恒空、`discoverability_required` 未设置。修复：`_discoverability_freeze()` 冻结当前有效 post 报告（report_id/stage/profile_version/input_hash/status/report/model）+ profile 声明才必需；`_execution_snapshot()` 从 WorkflowStep 钉死记录去重产出 plugins（key@version）+ definition 引用的 skills。SEO 报告由此进入 candidate hash。
  - **新增偏差 D-R2-3（SEO 报告状态不作硬闸）**：readiness 只要求报告「存在并冻结」；status（ready/incomplete）如实冻结供审批者判断，不作批准 blocker（原文未规定 incomplete 报告阻止批准；确定性 SEO 字段检查仍走 check 层）。
- **R2-H5 node.skill 只有 preflight 无执行（高）**：实现 `node.skill@1` SkillNodePlugin（经 `resolve_executable_runtime()` 委托非内置 runtime 执行，unavailable 即节点失败）；preflight 对含 node.skill 的工作流在无「可执行」runtime（内置 runtime 如实不算）时启动前拒绝（409），而非运行期 RegistryError。
- **R2-H6 skills_enabled 字段失配（高）**：`_enabled_skills()` 原读 `plugins.enabled`，实际配置字段为 `plugins.skills_enabled`。已修正并补 disabled 回归。
- **R2-H7 rerun 新旧 output 不可审计（高）**：新增 `workflow_step_attempt` 表（Migration D `d4audit00004`，_has_table 防御与 a1/b2 一致）；引擎在 advance/complete/rerun/_fail 四个终态路径写入不可变 attempt 行（output/output_hash/error）；`GET /workflow-runs/{id}/nodes/{node}/attempts` 查询审计历史。
  - **修订 D6-c（attempt_no 语义）**：首次执行即 attempt 1（审计行计数），rerun 递增；原「首跑记 0」语义作废。
- **R2-M8 staleness 粒度（中）**：`mark_media_changed` 原 `mark_draft_changed`（清空 fact_check_json）且不动 check runs。修复：只置 candidate stale + 仅 media/rights check runs 标 stale（`checks.mark_kinds_stale`）；fact_check_json 与 fact/platform 检查保留（换图不重跑正文 FactCheck）。`mark_draft_changed` 补 `mark_all_stale`（正文变化时 check runs 一并失效）。
- **R2-M9 Renderer 未由 profile 驱动（中）**：`render_for` 原只走静态渠道映射（x+thread 错落 generic）。修复：profile 声明 renderer_key 优先；未声明回退静态映射（补 form 感知：x/x_thread+thread → renderer.x.thread）；profile 声明了未注册 renderer 时降级 generic 并记 `renderer_unregistered:` warning（不静默成功）。
- **R2-M10 unverified auto_draft 可执行（中）**：`execute_attempt` 对 `verified=False` 的 auto_draft 默认 409（「未真实验收的自动能力不可执行」落为硬 Gate）；`system_settings delivery.allow_unverified_auto_draft=true` 显式放行（测试/真实验收用）。前端 ReviewPublish 对 unverified 目标禁用执行按钮并显示原因。authorize_target 仍如实记录 capability snapshot（不阻止授权本身）。
- **R2-Evidence 门禁证据留档**：复核指出「226 passed 无 Connector 可读执行证据」——本批次起 tasks.md Phase 10 记录命令级结果；另更正前次验收报告表述：未勾人工项为 **9.5/9.7/9.12–9.15 共 6 项**（非 4 项）。

### R3 二次复核收口（Acceptance Fix 批次 2，2026-09-24）

二次复核升级为 CONDITIONAL PASS，列 3 个 archive blocker + 3 个次级问题。全部修复：

- **R3-1 node.skill 执行路径 ImportError（blocker，代码 bug）**：`SkillNodePlugin._runtime()` 的 `from . import skill_runtime` 与 `execute()` 的 `from .contracts import` 均为错误相对导入（nodes 的上级包才是 content_harness）——preflight 与注册测试均测不到执行路径。修正为 `..`；新增完整执行链测试：注册 fake executable runtime → skill 已安装 → `start_run` 真正执行 `node.skill` → runtime 被调用 → 节点 succeeded → WorkflowStepAttempt 审计行落库。
- **R3-2 Discoverability 成为 Workflow Stage（blocker，spec 完整性）**：新增 `builtin.discoverability_post@1` 节点（`_h_discoverability_post`：profile 声明 `discoverability_profile` 才生成 post 报告并如实落状态；未声明形态节点空转返回 `ran=False`），插入全部 9 个 shared family 的 check/censor 之后、approve 之前。golden test 不再手工 POST /discoverability/post——SEO 审查是 Workflow Timeline 的组成部分，mock 返回 incomplete 如实进入 Candidate 冻结与 Review Center。
- **R3-3 auto_draft 统一实时校验（blocker）**：新增 `delivery.validate_live_candidate_payload()`，任何 Publisher 远端调用前（prepare attempt 之前）统一执行：① manifest 本体完整性（重算 candidate hash = 批准值）；② render payload/content_hash 已冻结；③ 每个批准媒体实时权利未撤销（`_live_media_rights`）；④ 实际字节 SHA-256 与批准 manifest hash 一致（`_media_bytes`）。任一失败 409 且**不产生 DeliveryAttempt**。测试覆盖「批准后磁盘字节被替换 → 409 + publisher 子进程从未被调用」「批准后撤权 → 409」。Copy Package 路径原有逐项校验保留。
- **R3-4 skills_enabled 三态语义（安全边界）**：`_enabled_skills` 返回 (gate_active, 集合)——plugins 配置不存在/无该键 → 系统默认政策（不启用 enable gate）；`[]` → 明确全部禁用；`[...]` → 白名单。修正原「空集 == 全放行」的违反直觉行为；disabled/白名单/未配置三态均有测试。
- **R3-5 fork_draft_revision 统一入口（图文一致性）**：新增 `services/draft_fork.py`——新 revision 克隆 DraftMedia use（同 MaterialRevision 新 use 行）、document 由 fork 后的 use 重建（杜绝引用旧稿 draft_media_id）、fact_check 不继承、candidate stale 起步。`update_draft`（人工编辑）与 `apply_suggestion`（SEO apply）两个入口收敛到同一实现；原 apply_suggestion 直拷 document_json 导致的「新稿 media=[] 但 document 引用旧稿素材」不一致消除。
- **R3-6 Immutable Candidate（不变量修复）**：`invalidate_candidate()` 不再向已批准的 `ContentAsset.candidate_manifest_json` 追加 stale_reason（历史 Candidate 及其 hash 永不改写）；改为写 `candidate.invalidated` AuditLog，失效语义由素材权利状态/交付目标状态承载。测试断言 manifest 字节不变 + 审计行存在。
- **R3-Evidence 说明**：Connector execution records 侧仍无本轮运行的原始 pytest 输出（与 R2 相同的客观限制）；tasks.md 继续记录命令级结果作为仓库内证据。

### R4 三次复核收口（Contract & Rights Integrity 批次，2026-09-24）

三次复核确认 R3 六项成立，另发现 3 个 blocker（产品语义）+ 2 个高优（fork 继承）+ 2 个非 blocker。全部修复：

- **R4-B1 schema v2 `config` 丢失（blocker，契约分裂）**：`start_run()` 原只读 `node.get("params")`，而 D7 定义 v2 用 `config`、preflight 也读 `config`——标准 v2 节点 preflight 通过但执行拿到空配置（R3 执行测试当时用 `params` 书写，绕开了正式 schema）。修复：`node_config_of(node)` = params 与 config 兼容合并、**config 优先**；`start_run`、preflight（skill 引用）共用该语义。skill 执行测试改回正式 `config` schema。
- **R4-B2 social.short / script.spoken 不自洽（blocker）**：两 family 缺 `fact_check` 节点而 Approval Gate 要求 FactCheck——用户只跑 Workflow 会在批准节点卡死（golden 当时手工补调用 /fact-check 掩盖了这一点）。修复：两 family 正式插入 `fact_check` 节点；golden 移除手工补调用并新增断言「check 节点 succeeded」——16 个 target 现在纯靠 Workflow 自洽走到批准。
- **R4-B3 全局撤权未进 Approval Gate（blocker）**：rule/readiness 原只查 `DraftMedia` 缓存的权利字段，素材库全局撤权（revision revoked）后重新批准可产出新 Approved Candidate（直到 Delivery live gate 才被挡）。修复：统一 `rules.effective_media_rights()`（use 撤权/未授权/缺 rights_status + revision 全局撤权/未授权四态），`rule.media.public_rights`、`readiness_reasons_v2`、Review Center 投影共用；delivery `_live_media_rights` 的 use 行路径同步补 revision 全局检查。测试：全局撤权后 rule=blocker、readiness 含 `media_rights_incomplete:…:revision_revoked`。
- **R4-H4a fork 撤权字段（高）**：fork 原不复制 `public_use_revoked_at/public_use_revocation_note`——「仅对本稿撤权」的图 fork 后被洗白。已随 use 克隆继承，测试覆盖。
- **R4-H4b fork composition 语义（高）**：fork 原一律 `sync_document()` 重建——只改 SEO 标题会把手工编排的图片重排回默认位置。修复：**title-only fork（正文未变）克隆 document 并把旧 draft_media_id 映射为新 use id**（保留手工编排；无法映射的块丢弃，绝不保留旧稿引用）；body 变更才重建。测试：手工编排 → title-only fork → 块序保持、image id 全部映射为新 use。
- **R4-H4c fork 派生数据策略（高）**：fork 原无条件继承 `structured_json/thread_posts_json`——X Thread 手工改正文后旧推串仍会被渲染发送。修复：**title-only 继承；body-changing 清空**（与旧 update_draft 语义一致），document 按新正文重建。测试双向覆盖。
- **R4-N1 copy package 扩展名（非 blocker）**：包内媒体原硬编码 `.png`；新增 `_media_suffix()` 按 revision/use 的 mime 推导（png/jpeg/webp/gif/pdf/mp4/mp3，未知 `.bin`）。测试：JPEG 素材 → 包内 `.jpg`。
- **R4-N2 Review Center media readiness（非 blocker）**：投影原只看「有无素材/撤权」，不结合 profile `media_requirements`——小红书零图汇总卡显示 `none`。修复：readiness 计算 `_draft_has_required_media`（与 rule.media.required 同语义），缺必需图 → `blocked`；同时接入 effective rights 三态（revoked→blocked、其他权利问题→warning）。测试：小红书/公众号零图 blocked → 补图 ready。
- **R4-Evidence 说明**：同前两轮——Connector execution records 无法覆盖本机测试运行，仓库内证据以 tasks.md 命令记录为准。

### R4.1 Contract Consistency Fix（2026-09-24）

四次复核确认 R4 七项成立，另发现 2 个残余契约问题。修复（无架构变动）：

- **R4.1-1 preflight 配置盲区（blocker）**：R4 将 `node_config_of()`（config 优先合并）引入了 start_run，但 `_referenced_skills()` 仍是 `config or params`、`_is_target_agnostic()` 同样——兼容定义 `{params:{skill}, config:{timeout}}` 会 preflight 通过却带着已合并配置执行（可执行 runtime 存在时绕过 installed/enabled/version 检查）。修复：`node_config_of` 下沉到 `contracts.py`（无依赖模块，避免循环导入），`skill_runtime._referenced_skills`、`workflow_templates._is_target_agnostic`、`start_run`（经 nodes re-export）四处统一同一实现。测试：混合字段定义的 skill 引用被 preflight 检出；target-agnostic 判据对 params 藏 channel 的定义正确返回 False。
- **R4.1-2 Delivery use 级撤权旁路（blocker）**：`_live_media_rights()` 原先查 `material_revision_id` 即 return——v2 manifest 同时带 draft_media_id + material_revision_id 时，「仅对本稿撤权 use（revision 仍公开）」后在撤权之后创建的 target 可照常 copy package / auto_draft。修复：**draft_media_id 存在且能定位 use 行时，一律先经 `effective_media_rights(use)` 判定（use + revision 双层）**，无 use 行才退化为 revision-only——Delivery 与 rule/readiness 从此真正共用 R4 的同一 Rights 语义。测试按复核给出的路径全程回归：批准 → 仅撤 use → 撤权后创建 target → copy package 409 + auto_draft 409 + 零 DeliveryAttempt + publisher 零调用。
- **R4.1-Evidence**：同前，Connector 侧以仓库内命令记录为准。
