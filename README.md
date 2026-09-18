# AI Content Studio（AI 内容生产中心）

事实驱动的内容生产系统：把结构化数据、研究笔记、文件、URL、人工观点整理成 **FactPack**，面向抖音 / 小红书 / 公众号生成内容，经事实校验与人工审核后导出。

需求与任务依据：`03_ai_content_studio_PRD.md`、`04_ai_content_studio_execution_plan.md`。

```text
Source → Fact → FactPack(冻结) → Topic Brief → 三渠道生成
       → FactCheck → Review → Asset → Export(MD/TXT/JSON/SRT)
```

核心不变量（"事实不可漂移"主干，全部有测试覆盖）：

- FactPack 冻结后不可变，修改必须 Clone vN+1
- Topic 只能绑定 frozen FactPack
- 模型输出的 fact_id 必须属于当前 FactPack，服务端校验
- Deterministic Checker：无 Fact 支持的数字 → blocker；blocker 未解决不能 approve（HTTP 409）
- 重新生成 / 人工保存产生新 revision，旧 Draft 永不覆盖
- 已生成内容永远记录生成时的 FactPack 版本与 checksum

## 快速启动

```bash
# 后端（默认 SQLite，零外部依赖；Mock provider，无需 API Key）
cd apps/api
python3 -m venv .venv && . .venv/bin/activate
pip install -e . pytest ruff
python -m app.seed                 # 建表 + 种子（4 用户 / 3 渠道模板 / Brand Voice / Prompt）
python -m uvicorn app.main:app --reload --port 8000

# 前端
cd apps/web
npm install && npm run dev         # http://localhost:5173（/api 代理到 8000）
```

或使用根目录 `Makefile`（`make seed` / `make dev` / `make dev-web` / `make worker` / `make test` / `make lint` / `make backup`）。

> 本机代理若为 fake-ip 模式（Clash 等），在 `.env` 设 `SSRF_ALLOW_PRIVATE=true`，否则 URL 抓取/Connector 全部会被 SSRF 防护拦截。生产必须保持 false。

生产部署（docker compose 全栈）：`docker compose up -d --build` 一键起 postgres / redis / minio /
api / web / worker / beat。标准流程：先 `up -d postgres redis minio minio-init`，等 postgres 健康，
宿主机 `DATABASE_URL=postgresql+psycopg://studio:studio@localhost:15432/content_studio make migrate`
（再跑 `python -m app.seed` 做幂等种子），最后 `up -d --build` 其余服务。
访问入口：Web `http://localhost:8088`（nginx 托管 + /api 反代），API `http://localhost:8000`。
入口服务（api 8000 / web 8088）绑定 0.0.0.0 对局域网开放；存储类端口绑定 127.0.0.1
（PG 15432 / Redis 16379 / MinIO 19000、19001），不对局域网暴露；容器内服务互通走 compose 内网。
注意：开发模式身份来自可伪造的 `X-Studio-User` header，局域网开放即局域网内任何人可冒充
admin，正式对外部署须改回 127.0.0.1 并接入真实鉴权。

### 演示账号（开发模式 Header 身份）

设置页可切换：`admin@ / editor@ / reviewer@ / viewer@ studio.local`。
身份通过 `X-Studio-User` header 传递，权限矩阵：admin 全部；editor 产线操作；reviewer 审核+改稿；viewer 只读。

### 系统配置管理页（设置页）

仿桌面客户端设置页（左侧分区导航：模型服务 / 数据与队列 / 对象存储 / 安全 / 身份与权限 / 关于）：

- **展示**：LLM Provider、模型、Base URL、API Key（脱敏掩码）、数据库连接串（脱敏）、队列、MinIO、
  SSRF/上传限制等全部生效配置，附 /health 深探针状态
- **修改**：admin 可在页内修改 LLM 配置并保存即时生效（无需重启），
  支持「测试连接」（对网关发一次最小请求）与「恢复环境变量默认」

### 外部 API 数据接入（Connector）

「数据接入」页配置量化平台等外部 API：base_url + 鉴权（密钥只存环境变量名，值不落库），
Endpoint 定义拉取路径与 JSON→Fact 映射（statement 模板 + fields 字段引用），
「立即拉取」后数据进入来源库走正常确认流程：

```bash
curl -X POST http://localhost:8000/api/v1/endpoints/1/pull -H "X-Studio-User: editor@studio.local"
# 定时拉取（生产交 Celery ingestion 队列或外部 cron）
```

### 运维

- 监控：`GET /api/v1/health`（深探针：DB/provider/队列），`GET /metrics`（Prometheus 文本格式），
  每个响应带 `x-trace-id` 并输出 JSON 结构化访问日志
- 多副本指标聚合：Prometheus 按 replica 逐个抓 `/metrics`（service discovery 自动发现实例），
  指标自带 `instance` label 天然区分副本；**不需要** Pushgateway——它适用于批任务，长驻服务抓取即可
- 异步队列：`.env` 设 `TASK_QUEUE_ENABLED=true` + Redis（`CELERY_BROKER_URL`），生成走 `llm` 队列、
  Connector 拉取走 `ingestion` 队列；`make worker` 启动 Celery worker（compose 部署含 worker 服务）
- 数据库迁移：开发环境 `make seed` 幂等建库；生产/PostgreSQL 执行 `make migrate`
  （`alembic upgrade head`，已在 PG 16 实测），后续 schema 变更用 `alembic revision --autogenerate`
- 备份恢复：`make backup`（SQLite 开发库，保留 7 份）；生产 PostgreSQL 流程见
  `docs/runbooks/backup-restore.md`

### Golden 评测

```bash
cd apps/api && python scripts/evaluate_content.py            # 30 Topic 全量评测
python scripts/evaluate_content.py --limit 3                 # 冒烟
```

输出无来源数字率 / Fact 覆盖率 / 校验通过率等指标，报告落 `apps/api/evals/reports/`。
mock provider 下是确定性基线；接真实模型后用同一数据集对比。

### 接真实模型

`.env` 设置：

```text
LLM_PROVIDER=openai_compatible   # 兼容 minimax / openai / 任意 OpenAI 风格网关
LLM_BASE_URL=...
LLM_API_KEY=...                  # 只放环境变量，DB 不存明文
LLM_MODEL=...
```

业务层只面向 `LLMProvider` 协议；`MOCK_INJECT_UNFACT_NUMBER=true` 可让 mock 注入一个
FactPack 外数字，用于验证 FactCheck blocker → 无法 approve 的完整链路。

## 目录结构

```text
apps/api/app/
├── models.py               # 全部数据模型（PRD §8 + Connector + STU 扩展字段）
├── routers/                # sources / facts / fact_packs / topics / generate
│                           # / reviews / assets / templates / dashboard / users
│                           # / connectors / settings / health
├── services/
│   ├── parsers.py          # TXT/MD/CSV/JSON/PDF/HTML 解析器（统一 ParsedDocument）
│   ├── url_fetch.py        # SSRF 安全抓取（禁内网/限大小/限跳转/鉴权 header）
│   ├── fact_extractor.py   # 确定性候选事实抽取
│   ├── factpack_service.py # 冲突检测 + 版本 checksum
│   ├── factchecker.py      # Deterministic Checker（数字/日期/风险词/实体）
│   ├── exports.py          # MD / TXT / JSON / SRT（SRT 标记 estimated）
│   ├── connector_service.py# 外部 API 拉取 + JSON→Fact 映射（EPIC-18）
│   └── generation/         # LLMProvider 协议 + mock/openai_compatible
│                           # + prompt 渲染 + 多渠道编排（fact_id 服务端校验）
├── tasks/                  # Celery app + worker 任务（llm/ingestion 队列，开关式启用）
├── observability.py        # trace_id 日志 / Prometheus 指标 / 深探针
├── llm/prompts/            # 三渠道 Prompt 模板（文件为准，启动时同步版本与 checksum）
└── seed.py
apps/api/scripts/           # evaluate_content.py（Golden 评测 CLI）
apps/api/evals/             # golden_topics.json（30 Topic）+ reports/
apps/web/src/pages/         # Dashboard / Sources / Connectors / FactPacks / Topics
│                           # / Workspace(三栏) / Review / Assets / Templates / Settings
apps/api/tests/             # 63 个测试：端到端主干 + 关键不变量 + 服务层单测
docs/runbooks/              # backup-restore.md
```

## 完成情况（对照执行计划）

| EPIC | 状态 | 说明 |
|---|---|---|
| EPIC-00 工程基线 | ✅ | 目录 / Makefile / docker-compose / .env.example / GitHub Actions CI |
| EPIC-01 RBAC + Secret | ✅ | Header 身份开发模式 + 角色矩阵；Key 只走环境变量 |
| EPIC-02 Source Library | ✅ | 文本/URL/文件（txt/md/csv/json/pdf）、解析状态、可信等级、归档 |
| EPIC-03 Fact 模型 | ✅ | 候选抽取、确认/拒绝/编辑、冲突检测、检索 |
| EPIC-04 FactPack | ✅ | 建/增删 item、冻结（校验+checksum）、Clone 版本链 |
| EPIC-05 Voice/Template/Prompt | ✅ | 版本化 + checksum + immutable + clone/publish/archive |
| EPIC-06 Topic Brief | ✅ | 绑定 frozen 包 + 渠道 + 禁止表述 |
| EPIC-07 LLM Provider | ✅ | 协议 + registry + llm_run 记录 + JSON 一次修复 |
| EPIC-08 多渠道生成 | ✅ | 三渠道独立 job、结构化输出、fact_id 服务端校验、失败不互相回滚 |
| EPIC-09 Fact Checker | ✅ | 确定性层（数字/日期/风险词/朴素实体）+ LLM 层接口 + approve gate(409) |
| EPIC-10 编辑器与版本 | ✅ | TipTap 富文本（Markdown 存储契约不变）；revision 递增不覆盖；选区 AI 改写（按位置替换）；上一版 Diff 视图 |
| EPIC-11 Review | ✅ | 队列 / 退回 / 批准（blocker=0 + frozen + revision 未变三重校验） |
| EPIC-12 Asset/Export | ✅ | MD/TXT/JSON(含 provenance)/SRT(标记 estimated) + 分渠道格式限制 |
| EPIC-13 前端页面 | ✅ | P01-P11 全部页面 + 数据接入页（TipTap 编辑器 + 工具栏 + Diff） |
| EPIC-14 原型验收 | ✅ | Mock 全链路（§22 用例含注入口径）已在测试与冒烟中走通 |
| EPIC-15 测试 | ✅ | 63 个测试；30 Topic Golden 集 + evaluate_content.py 评测 CLI |
| EPIC-16 安全 | ✅ | SSRF 防护 / 上传双校验 / Prompt 注入包装（source 只作数据） |
| EPIC-17 运维 | ✅ | Celery 四队列 + worker 容器；/health + /metrics + trace_id 日志；备份 runbook |
| EPIC-18 Connector | ✅ | generic_rest：API 拉取 + 鉴权（env 引用）+ JSON→Fact 映射 + 前端页 |

## 关键决策

1. **同步/异步双模式生成**：默认同步（Mock 毫秒级、测试零依赖）；`TASK_QUEUE_ENABLED=true` 时同一 API 分发到
   Celery `llm/ingestion` 队列，前端以 queued 状态轮询，接口契约不变。
2. **原文存 DB**：V1 长文本存 `source_document.raw_text`；对象存储是文档化升级路径。
3. **建表走 Alembic**：开发环境 seed 幂等可重跑；生产/PostgreSQL 用 `make migrate`（`alembic upgrade head`）建表，已在 PG 16 实测。
4. **LLM Reviewer mock 下透传确定性结果**：不伪造审查结论；接真实模型后自动启用。
5. **编辑器用 TipTap、存储仍是 Markdown**：`tiptap-markdown` 在边界做双向转换，导出 md/txt/srt 契约不变；选区改写按文档位置替换（不再字符串查找首个匹配）。
6. **SRT 时间轴为估算**：明确标记 estimated，不假装精确字幕。
7. **Connector 鉴权凭据只存环境变量名**：DB 记 `api_key_env`，值运行时从进程环境读取，不落库不入日志。
8. **朴素实体检查**：机构后缀启发式，已剥动词前缀/时间指示词降噪；误报为 warning 不阻塞，NER 是升级项。
9. **运行时配置覆盖（前端设置页）**：设置页展示全部生效配置（Secret 一律脱敏回显）；LLM 配置 admin 可在页内
   修改，写入 `system_settings` 表并即时生效（页面覆盖优先于 .env，「恢复默认」回落环境变量；Celery worker
   执行任务前刷新覆盖）。API Key 允许存覆盖表以支持前端配置（本地开发便利），但任何接口都不返回明文；
   生产建议仍走环境变量 / secret manager。
10. **模板中心只增不改、单版本生效**：模板 / Voice / Prompt 内容一律不可编辑（克隆出的草稿也不可改，API 层
    无内容更新端点，PATCH/PUT → 405），变更 = Clone 新版本再发布；同渠道（模板/Prompt）、同名（Voice）至多
    一个 published 生效，发布新版本自动把旧版本降级 archived（选题/任务按 id 引用历史版本，不受影响）；
    启动时修复历史多生效数据（只留最高版本）。生成时取该渠道最新 published 模板兜底。
11. **多模型 Profiles + 场景路由**：设置页可登记多个模型（DeepSeek / MiniMax / OpenAI / 任意兼容网关，模板化
    添加），并按场景路由——内容生成（generate）/ 选区改写（rewrite）/ 事实校验与审核复核（fact_check）/
    选题发现（topic_discovery，基于冻结 FactPack AI 荐题：模型只读已确认事实提候选，人采纳后预填建题表单，
    仍走完整生成→FactCheck→审核链）各自指向不同 Profile；停用或缺失回落默认（页面 llm 覆盖 → .env）。
    provider 实例按 Profile 缓存，保存即失效重载，无需重启。
12. **技能与插件登记 + local_git 文档数据源**：设置页自动发现本机 Agent skills（~/.agents/skills、
    ~/.zcode/skills，frontmatter 解析），勾选启用集存 system_settings.plugins；MCP server 手工登记；
    dsh :3080 状态探测。Connector 新增 local_git 类型：仓库目录（须在 LOCAL_DOCS_ALLOWLIST 前缀内）读
    文档 + best-effort git log，为「开发进展」类内容供数；只读不执行。资产封面为动态 SVG
    （GET /api/v1/assets/{id}/cover.svg，按渠道配色渲染标题，<img> 直接引用故不做 Header 鉴权）。
13. **配图素材随文走 + 公众号 HTML 导出 + dsh 配置面板**：asset_media 统一素材池（底层全量，前端按资产
    归属展示）；首次查看素材时从 structured_json 的 image_prompts / image_suggestions 懒生成占位位
    （含配图说明），上传实体图「只增不改」顶同序位（占位历史保留，与 revision 哲学一致），占位渲染
    渠道配色 SVG；公众号导出新增 HTML（零依赖 MD 渲染 + 微信兼容内联样式）。dsh 执行层：settings.yaml
    只读快照（providers / 默认模型 / env key 状态布尔）+ Studio 侧稳定性配置（默认与备选模型路由、
    超时、重试、产出目录），可勾选「写回 dsh 默认模型」（自动备份 settings.yaml；结构异常拒绝写入）。
    技能扫描目录可配置（空 = 默认两目录）。
14. **工作流画布（仿扣子编排层）**：`/workflows` 页，React Flow 画布把已有能力点串成可执行 DAG——
    节点 handler 直接调用既有路由函数（同一套校验/审计/409 闸门），结果只沉淀到既有实体
    （Source/FactPack/Topic/Draft/Asset），context 是节点间数据总线（copy-on-write 落库）。
    人工节点（采纳/批准）执行到即暂停（waiting_input），节点上内联操作后断点续跑；失败即停、
    可从失败节点重试（生成 handler 校验 job 状态，真实模型偶发解析失败会被暴露而非静默跳过）。
    内置两条模板：「每日舆情 → 荐题」（拉取→抽取自动确认→打包冻结→AI 荐题→人工采纳）、
    「生成 → 出库」（共享一个 Topic，抖音口播/小红书/公众号各自独立一条线：生成→校验→
    人工批准→导出，公众号线再接 wewrite 草稿箱真实发布）。已实测：荐题工作流与三渠道出库
    工作流均以真实 MiniMax 全链跑通，草稿箱 media_id 真实返回。

## TODO（按优先级）

1. dsh 沙箱限制：skill 无法写 `~/.wewrite/runs/`，产出暂落 `.wewrite-scratch/`（待沙箱放行或路径迁移）
2. DeepSeek API key 尚未配置（`~/.dsh/env.local` 留空，MiniMax 已可用）
