# Batch B 实施提示词（交由执行 Agent；完成后由独立验收方逐项复核）

```text
[C2C]
WORKSPACE: AIContentStudio
CHANGE: complete-multiplatform-content-handoff
STATE: SPEC_APPROVED + BATCH_A_DONE（tasks 17/43）
MODE: BUSINESS_APPLY — BATCH_B
NEXT_EXPECTED_STEP: BATCH_B_IMPLEMENTED（如实勾选 + 全量回执，等待独立验收，不自我宣告完成）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
一、环境与工作目录
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 仓库/工作目录：/Users/mshengran/Project/AIContentStudio（macOS arm64 本机单机产品，非容器）。
- 后端：apps/api —— Python/FastAPI + 同步 SQLAlchemy + SQLite（WAL），正式库 apps/api/content_studio.db。
  venv 在 apps/api/.venv；pytest 必须在 apps/api 目录用 .venv/bin/python 运行（系统 Python 缺依赖）。
- 前端：apps/web —— React + Vite。验收命令：cd apps/web && npm run build（tsc + vite + FE-P1 bundle 预算）。
- API 服务：launchd `com.aicontent.api` → http://127.0.0.1:8000。
  重启：launchctl kickstart -k gui/$(id -u)/com.aicontent.api；禁止 launchctl print（会泄露 env secrets）。
  重启后用 GET /api/v1/health 验证 ready:true。
- 前端 dev server：http://localhost:5173（IPv6 [::1]；127.0.0.1 会拒绝）——用户自管进程，禁止启动/重启。
- 测试鉴权：非生产环境用请求头 X-Studio-User: admin@studio.local（admin）；editor 场景见 tests 内 seed_users 夹具。
- DB schema head：`a3series00000001`（已 pin 在 apps/api/app/db.py 的 LOCAL_APPROVED_SCHEMA_HEAD 与
  apps/api/scripts/startup/runtime.env 的 REQUIRED_SCHEMA_HEAD）。新迁移必须同步推进这两处。
- openspec CLI 1.2.0：必须从仓库根运行（在子目录会误报 No items found）。
- 迁移先例：apps/api/alembic/versions/（SQLite batch_alter_table 用法见 f8a/f6e/a3series00000001）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
二、必读文档（直接引用仓库现文件，不得凭记忆改写）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
以仓库现文件为第一事实源：
1. openspec/changes/complete-multiplatform-content-handoff/ —— 唯一 owner change（不要新建重叠 change）：
   - proposal.md：范围与 Out of Scope。
   - design.md：原批"12 平台/17 形态"exact 表 + v2 增补 D-v2.1–D-v2.9；其中 D-v2.6 是 Form Descriptor 合同。
   - tasks.md：当前 17/43。本阶段 = 第 1、2、6 节（批次 B）；最终验收 = 第 7 节；生命周期 = 第 3 节。
   - specs/multiplatform-content-handoff/spec.md：17 形态 exact payload_schema 表与 canonical 合同。
   - specs/delivery-router-v1/spec.md：逐目标账号独立授权、本地包≠发布、Unknown 不重发。
   - specs/persona-channel-series-operations/spec.md：Batch A 已实现的栏目/绑定合同（只能消费，不得重定义）。
   - docs/ADR_SERIES_ACCOUNT_MODEL.md、docs/CURRENT_GAP_MATRIX.md：含实测缺口——
     channel_adapters.FIRST_BATCH 有 17 组合但仅 14 个属约定形态，缺 bilibili/image_note、x/long_post、x/articles。
   - findings.md / progress.md：历史证据与边界。只追加，不覆盖、不删改既有记录。
2. 背景参考（只读）：
   - openspec/AIContentStudio_OpenSpec_Multiplatform_Operations_v2.md（v2 设计源稿，change 文件已是其落位）。
   - docs/PRODUCTION_ACCEPTANCE_REPORT_2026-10-13.md（首批五形态真实验收基线）。
3. 相邻 active change（不得破坏、不得归档）：add-persona-creative-studio（151/156）、
   creation-recipe-stage-control-loop（141/144）。三个 change 对同一 capability 的归档合并义务见本 change tasks 3.1。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
三、当前现状（已完成，不可回退、不可重写）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Phase 0（v2 拆归）与批次 A（tasks 5.1–5.8）于 2026-10-14 完成：
  1) 迁移 a3series00000001 已在副本四段演练（升级/降级/再升级/fail-closed）后升级正式库
     （备份在 backups/pre-series-scope-20261014/），integrity/FK 干净，API ready:true。
  2) Persona-owned editorial series（content_series.scope=persona_editorial，无需账号）+
     series_account_target 投放绑定（CAS version、AuditLog、停用阻断）+
     API：POST/GET /api/v1/content-personas/{id}/series、/api/v1/content-series/{id}/targets[/{target_id}]。
  3) v5 交付解锁：delivery.py 不再用 unit.account_id 做目标锁；同平台多账号/跨平台目标独立授权；
     目标账号身份冻结在 capability_snapshot_json.target_account；legacy（master）候选固定账号语义保留。
  4) /identities 统一身份树（栏目挂角色）/平台公开身份登记/栏目创建/投放绑定面板；
     /accounts 一级导航已移除、路由兼容跳转；主导航回到九项。
  5) 测试：tests/test_series_targets.py（5 例）、test_migrations.py 5/5；npm run build 全绿。
- 首批五形态（wechat/article、xiaohongshu/image_note、x/single、x/thread、douyin/spoken_script）
  此前已真实走通 冻结→批准→授权→ZIP（见 PRODUCTION_ACCEPTANCE_REPORT_2026-10-13.md）。
- 已知既有失败，不要"修"它：tests/test_models_plugins.py::test_plugins_put_and_view ——
  ~/.codex/skills/wewrite-write 是指向已不存在的 ~/Project/wewrite 的断链符号链接（纯环境问题）。
- 工作区存在大量未提交改动（Batch A 与更早工作）。禁止 reset/rebase/清理不认识的文件；
  禁止 commit/push（除非用户明确要求）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
四、本阶段任务：批次 B（tasks 1.1–1.5、2.1–2.5、6.1–6.7）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
目标：把 12 平台/17 形态从"部分后端合同"做成"全部可选、可编辑、可审、可打包"的产品能力，
并与 Batch A 的栏目绑定、逐账号授权闭环接通。四组：

A. 服务端合同（1.1–1.5 + 6.1/6.2）
   1) catalog 补齐：新增 bilibili/image_note、x/long_post、x/articles 的 canonical schema
      （channel_variant_documents.py 校验分支）+ adapter（channel_adapters.py）+ published profile；
      xueqiu×2、juejin 保留登记、不计入完成义务、不得删除。
   2) ChannelFormDescriptor：版控只读投影（字段路径/类型/label/required/readonly/边界/枚举、
      media roles、校验错误映射），单一真源；17 形态（含原五）都由 descriptor 驱动。
   3) 新增 12 schema 接通 checks/v5 builder/Review Approval/authorization/local ZIP；
      安全 export projection 覆盖所有 ZIP 成员（含 manifest），Candidate 原 hash 不变。
   4) 17 目标全部接入既有 stage.variant.adapt@1（不存在 stage.variant.propose，不得新造）；
      接受为 Variant 不自动 freeze/approve/deliver；409 保留 dirty；Unknown 不重发。
B. 产品界面（2.1/2.2 + 6.3）
   - apps/web/src/product/ChannelVariantForm.tsx 去掉五形态硬编码 fieldsFor，改 Descriptor 驱动；
     未知/不可安全编辑字段只读或明确阻断，绝不静默丢弃；校验错误可定位到字段。
   - Review 展示各形态冻结预览/diff/checks/发布指南；本地包下载与公众号草稿明确分开；
     包/草稿都不等于公开发布。
C. 逐账号适配（6.4）
   - 按目标账号执行 stage.variant.adapt@1；target account 上下文进入 Effective Preview 与冻结 refs；
     同平台 A/B 账号要求不兼容（声明/风格/权利）时各自独立 Variant/Candidate，
     禁止换 account_id 复用冻结候选。
D. 交付与验收（2.3/2.4 + 6.5–6.7）
   - 17 形态真实 ZIP 本地交付（冻结正文/结构 + 真实 media bytes + manifest/rights/hash +
     publish-guide）；公众号只走既有授权草稿箱能力；缺真实媒体的形态如实阻断，不造占位素材。
   - 持久合同测试：17 schema/hash、source/target compatibility、v5 currentness、安全 export、
     live rights/tamper、target account、freeze、package；加集中 17-form smoke 与旧五形态回归。
     不写 17 套重复 E2E。
   - progress.md 为每个形态独立记录一行结果：可选/适配/保存/检查/冻结/批准/授权/ZIP/媒体/状态，
     不用一个样本代表全平台。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
五、授权边界（现在可做 / 须再问）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTHORIZED NOW：
- 批次 B 的业务代码、持久测试编写、隔离环境（内存/临时 SQLite）验证、副本库演练、
  openspec 文档与 tasks 勾选更新、progress/findings 回执。
STILL SEPARATE（不得自作主张，完成后列出待授权清单）：
- 正式库 profile 启用（tasks 2.5）：需用户单独授权 + 备份 + dry-run 审阅。
- 真实模型/Provider 调用、真实发布、公众号新发送：禁止。
- 正式库 schema 迁移（若本批需要）：副本演练 + 备份 + 用户确认后才可执行。
- commit / push / canonical sync / archive：禁止。
- 不得启动/重启用户 Vite dev server；不得改 launchd/worker 运行配置。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
六、硬约束（违反即验收失败）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
安全：
- 不打印 runtime.env 或任何 secret；被拒输入的错误信息不回显原值。
- 不收集/存储平台 Cookie、密码、AppSecret；WeChat platform-binding 仍仅限 wechat + wx 开头 AppID，
  该端点语义不得放宽。
- 结果未知的 provider 调用不得重试；超时/异常一律按 unknown 走对账。
- 不放宽 SSRF 固定传输、微信封面规则、空段落规则、24px 图文边距、technical-editorial 校验。
产品真源：
- 不新建第二套渠道/稿件/审批/发布真源；复用 ChannelRegistry/adapter、Master/Variant/v5 Candidate/
  Review/Delivery、stage.variant.adapt@1。
- 包就绪 ≠ 发布；草稿 ≠ 公开发布；ZIP/导出不写 PublishedContentRecord。
- 冻结候选不得换账号复用；同平台 A/B 是不同目标；persona_editorial 与 account_legacy 语义不得互串。
- 历史不可改写：已冻结快照、已交付包、旧 Candidate、workflows 7–20、既有 persona/账号/模板。
- 禁止浏览器自动发布 driver（social-auto-upload 仅作未来参考，本轮不接入）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
七、验收口径（验收方事后逐项复核，一切以文档回执为准）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
完成定义（见 change docs/CURRENT_GAP_MATRIX.md E3）：
CONTRACT_COMPLETE = 代码 + 持久测试 + 构建 + 每形态独立证据齐全；
真实生成质量（QUALITY_ACCEPTED）与公开发布另行，不得混称。
必须交付的文档回执：
1. tasks.md 勾选逐项对应真实证据；未完成/被阻断的项保持未勾选并写明原因。
2. progress.md 追加执行回执：准确命令、测试计数、关键 hash、每个形态的独立结果行。
3. findings.md 记录与规格的偏离、新发现的事实（不得只写在对话里）。
4. openspec validate --all --strict（仓库根）与 git diff --check 全绿的真实输出。
5. 后端全量 pytest 回执（已知 test_plugins_put_and_view 断链失败可豁免，须原样引用）；
   cd apps/web && npm run build 全绿。
6. docs/CURRENT_GAP_MATRIX.md 更新为 17 形态完成矩阵：
   Requirement → code path → test → UI → 包/阻断原因，逐形态标注 CONTRACT_COMPLETE 或缺失原因。
```
