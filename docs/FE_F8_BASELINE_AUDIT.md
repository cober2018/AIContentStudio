# FE-F8 Production Readiness 基线审计

> 当前正式验收 profile：单机 SQLite + 本地素材库 + loopback-only 访问。PostgreSQL/MinIO 仅作为未来部署 profile，不是本轮 F8 的验收前置；认证 schema 草案仍未批准。

## 2026-10-03 本机持久化配置盘点

在不输出任何配置值的前提下，当前本机 SQLite 的 6 条 `SystemSetting`
按 secret-policy 分类为：3 条含 secret-bearing 字段（`image`、`llm`、
`models`），3 条不含 secret-bearing 字段。该盘点已完成，但没有擅自删除、
迁移或覆盖这些个人配置；在将 `app_env=production` 或迁移到外部 secret
provider 前，仍需单独完成 remediation 与授权。

审计日期：2026-10-02
工作区：`AIContentStudio`  分支：`main`
基线：`da73bbb`（工作树包含既有 F7 未提交改动）

## 审计边界

本次只完成 FE-F8 的基线、安全边界和实施前缺口记录，不启用 F8 业务实现，不执行数据库迁移，不读取或打印真实 secret，不启动供应商生成，不发布公众号内容，也不改变默认路由。

F8 的身份列草案与 `f8a000000001_production_identity.py` 仍是未接受方案；它们不能被当前审计视为已实现或可迁移。

## 当前实现盘点

### 身份与授权

- 开发/测试模式仍使用 `X-Studio-User`，缺少 header 时回落本地默认用户，并可能自动创建用户。
- 生产模式已有草案级 HS256 校验、issuer/audience/expiry/subject 检查，并按 `identity_issuer + identity_subject` 查询已有用户。
- 生产角色来自数据库用户，不应来自 token role claim；未知 subject 应拒绝。
- 当前生产认证方案尚未完成独立身份/schema 复核，真实 issuer、audience、密钥来源和用户绑定尚未批准。

### 启动与迁移

- 非生产模式的 `lifespan` 会执行 `init_db()`，同步模板、归一化模板发布状态、加载运行时配置并写入开发种子数据。
- 生产模式已绕过 `init_db()` 和可变种子写入，并检查 `alembic_version` 与 `required_schema_head`。
- 生产启动仍需完成配置、迁移运维和回滚说明；不得在启动时自动迁移或修改业务配置。

### Secret 与配置

- API、MinIO、队列、WeChat 账号和模型配置已经有脱敏投影或环境变量引用边界。
- `SystemSetting` 仍可能保存历史配置覆盖；生产启用前必须盘点其 key/字段类型并制定人工 remediation，不打印原值、不静默删除。
- 日志、health、metrics、AuditLog、Provider task 和 worker 元数据只能保存白名单投影，不能保存原始 token、API key、Cookie、签名 URL 或 provider raw error。

### 媒体与存储

- 当前开发/测试媒体真源仍是 `MEDIA_ROOT` 下的本地相对路径，`MaterialRevision`、`DraftMedia`、`AssetMedia`、Workflow 输出、Review/Delivery 和 retention 仍存在直接读取或写入本地路径的调用点。
- `storage_service.py` 的 MinIO 能力目前主要服务导出/对象存储辅助路径，并不代表所有不可变媒体已经切到对象存储。
- F8 必须先建立统一 `StorageProvider` 兼容层、完整引用字节 inventory、hash/read 校验和可回滚切换 rehearsal，不能先切半套路径。

#### 直接 MEDIA_ROOT 调用者清单（2026-10-02 补充）

依据：在 `apps/api/app` 内搜索字面量 `MEDIA_ROOT`，逐一读取命中文件的实际函数；当前没有可用代码图工具，使用限定范围文本搜索。不读取素材内容或真实配置。本表包含直接路径构造、读写、stat、锁和删除；经这些函数间接访问字节的调用方仍需在存储切换时验收，不能由该 inventory 推断切换已完成。

| 文件 / 函数（apps/api/app/ 下） | 读写用途与路径来源 | 当前 provider / 兼容桥边界 |
|---|---|---|
| `services/asset_media.py:79` `save_upload` | 按 Asset/Media ID 写图片，保存相对路径 | legacy 本地直写；待兼容桥 |
| `services/asset_media.py:101` `raw_response` | AssetMedia.file_path 拼根目录并读字节 | legacy 本地读取；现有字符串前缀检查不等于统一 provider 校验 |
| `services/material_storage.py:168` `provider` | 用 MEDIA_ROOT 构建 LocalMaterialStorage | 当前 Material/持久生成的 provider 入口；generation 私有 namespace；开发绝对路径桥不适用于 production |
| `services/material_byte_lock.py:15` `_lock_path` | 根目录 material/.locks 下按 hash stripe 建本地锁文件 | 本地事务锁，不是媒体对象；MinIO/多主机时不能照搬 |
| `services/materials.py:229` `adopt_draft_media` | 判断旧 DraftMedia.file_path 文件存在，引用既有字节 | legacy adoption 的本地存在性桥，未切对象存储 |
| `services/delivery.py:581,590` `_cover_bytes` | MaterialRevision / DraftMedia.file_path 读取 cover | legacy Publisher 字节路径；v5 exact cover 另走 checked reader，不代表该旧路径已迁移 |
| `services/delivery.py:755` `_media_bytes` | MaterialRevision / DraftMedia 与回退 revision 读取包内媒体 | legacy Copy Package 路径，外层有 manifest/hash/rights gate；待统一 reader |
| `routers/article_handoff.py:450` `get_draft_media_raw` | DraftMedia 路径或 MaterialRevision 回退，FileResponse | 已授权 Draft 的 legacy raw 读取，仍依赖本地文件 |
| `routers/article_handoff.py:680` `download_package_archive` | 读取旧 manifest DraftMedia 文件入 ZIP 并比对 hash | legacy 成品包，不能只切新 v4/v5 reader |
| `routers/project_assets.py:122` `upload_project_material` | 按 content hash 构造路径，检查写入前/失败后是否存在 | 真正 revision 写入走 Material provider；孤儿记录判断仍是本地存在性 |
| `services/retention.py:40` `_process_material_orphan_candidates` | 根据审计相对路径检查引用、加 hash 锁后 unlink | legacy 本地删除；只处理符合根目录/hash格式的孤儿候选，不是对象存储清理器 |
| `services/workflow_engine.py:378` `_h_generate_cover` | working/run+channel 路径交旧生成器写入；随后读入 Material | legacy cover 临时输出，未改为 media.generate 或对象存储 |
| `services/media_renderers.py:85` `_source_budget` | Master AssetRef→MaterialRevision 路径，stat 汇总实际大小 | renderer 发送前本地预算检查；完整 bytes/hash reader 在后续 gate，切换前必须一起改 |

根定义 `services/asset_media.py:19–22` 的 `AI_STUDIO_MEDIA_ROOT` 必须是绝对路径。当前 inventory 不读取该环境值、不披露本机媒体路径，也不替代生产 storage cutover rehearsal。

### Worker、日志与可观测性

- Celery worker 已有独立任务入口，并在任务执行前刷新运行时配置；队列默认关闭时仍可同步执行。
- 请求已有 `x-trace-id` 和结构化请求日志；metrics 已按 Starlette route template 记录，未匹配路由统一为 `__unmatched__`，避免把私有 ID 放进 label。
- 仍需把 correlation 贯穿 worker、Workflow、Provider、Delivery，并补充 actor/project/unit/run/master/variant/candidate/target 的安全投影和可查询审计。

### Health / readiness

- `/api/v1/health/live` 是 liveness；`/api/v1/health` 是 readiness，并在 required dependency 不可用时返回 503。
- readiness 当前检查 DB、schema head、生产配置及已启用 MinIO 的必要配置；诊断使用固定 reason code，不返回底层异常文本。
- 仍需明确 queue/worker 是否是当前部署的 required dependency，并验证 optional provider 不会因库存读取触发网络探测，也不会阻断核心 readiness。

### 外部副作用

- F7 的 capability、ProviderGenerationTask、Unknown/reconciliation、WeChat draft-only 和本地 package 边界继续有效。
- MiniMax 目前只完成受控 CLI 能力库存和隔离链路证据；真实输出权利、完整重启恢复和产品 Workflow/素材接受仍未整体验收。
- 公众号产品链路已有一次真实 Unknown/reconciliation_needed 记录，不能重试绕过；独立 WeWrite 成功不等价于产品 Publisher 已回读成功。
- Google、Grok、Commons 暂不纳入本阶段真实验收。

## F8 威胁模型摘要

| 面 | 当前风险 | F8 必须保持的边界 |
|---|---|---|
| 身份 | Header/default-user/自动建号不可用于生产 | 签名身份经过 issuer/audience/key/JWKS 或批准等价验证，映射已有 active User |
| 权限 | token 自带 role 可能越权 | 角色只来自 durable User，未知 subject fail closed |
| 启动 | 自动建表/种子写入会绕过运维审批 | 生产只读校验，迁移由操作员显式执行 |
| Secret | 历史 SystemSetting 可能有明文覆盖 | 盘点、脱敏、外部 secret reference 和安全日志投影 |
| 存储 | 直接 MEDIA_ROOT 读写会绕过统一校验 | 所有候选/包/交付字节走 provider 或明确兼容桥，重算 hash |
| 外部调用 | Provider/Publisher 是副作用边界 | 精确 capability、账号、动作、幂等和 Unknown 对账，不因安装或配置冒充 verified |
| 观测 | 动态 URL/原始异常可能泄露信息 | bounded route labels、固定 reason code、相关 ID 白名单 |
| 恢复 | DB 与媒体不一致会破坏血缘 | 隔离备份恢复、迁移 head、引用字节抽样和可回滚能力 |

## 当前门禁记录

| 门禁 | 审计时可见的已记录基线（不是文档审计新跑结果） |
|---|---|
| Backend | `1661 passed, 28 skipped, 8 warnings`，工作目录为 `apps/api` |
| Frontend | TypeScript/Vite build PASS；FE-P1 bundle gate PASS |
| Bundle | `/projects` 224.89 kB raw / 72.96 kB gzip；Production 284.42 kB / 90.46 kB；Text Studio TipTap 保持 lazy |
| OpenSpec | `openspec validate --all --strict`：33 passed / 0 failed |
| Ruff | 既有记录的相关 F7/F8 触点范围检查 PASS；不把全仓既有问题混入本轮结果 |
| Diff | `git diff --check` PASS |
| Database | 本轮不执行正式数据库迁移；F8 draft migration 未启用 |

## 实施前仍未关闭的门

1. F7 implementation gates、MiniMax/公众号真实产品回读和整阶段独立验收尚未全部完成，因此 F8 task 0.1 保持未勾选。
2. issuer + subject 到现有 active User 的稳定绑定、认证协议和 schema 变更需要独立安全/schema review；F8 task 0.7 保持未勾选。
3. 真实生产 secret provider、storage cutover、queue topology、backup/restore 环境尚未选择或演练。
4. Golden fixtures、全链路 Opportunity→Learning 和真实平台发布证据不能由本地 ZIP、mock、dry-run 或历史草稿替代。

## 审计结论

F8 基线审计完成，F8 仍处于“可继续规格/实施准备，尚不可启用生产身份或迁移”的状态。当前不改变生产配置、不运行迁移、不推送、不部署、不公开发布。
