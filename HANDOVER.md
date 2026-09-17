# AI Content Studio 项目交接文档

> 交接时间：2026-09-17 · 交接基线：main @ c54fd41（+ 1 个未提交修复，见 §5.4）
> 读者：接手继续开发的 Agent / 工程师。本文档所有事实均已对照仓库实测核验。

---

## 0. 一分钟摘要

AI Content Studio 是一个**事实驱动的内容生产中心**：从结构化数据、研究笔记、URL、文件整理出
FactPack（冻结的事实包），面向抖音 / 小红书 / 公众号三渠道生成内容，经事实校验（FactCheck）
和人工审核（Review）后导出（MD / TXT / JSON / SRT）。

**执行计划 18 个 EPIC 全部完成**，V1 基线已在 main 分支。交接时点：63 个 pytest 全绿，
API / Web / dsh 三个服务都在线。主要遗留是接真实 LLM、dsh 沙箱路径、API 容器化三件事。

主链路：

```text
Source → Fact → FactPack(冻结) → Topic Brief → 三渠道生成
       → FactCheck → Review → Asset → Export(MD/TXT/JSON/SRT)
```

**最新战略定位（2026-09 确立）**：用 DeepSeek Harness（dsh，`~/.local/bin/dsh-studio` 起 :3080）
替代 Antigravity 做执行层，把已验证的 wewrite-\* skills 迁入；Studio 定位为**内容汇聚与管理中心**
（FactPack、生产、审核、导出），**不直接做文章输出**。

---

## 1. 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.13 / FastAPI / SQLAlchemy 2 / Celery / httpx / httpx_test |
| 数据库 | 默认 SQLite（零依赖）；生产 PostgreSQL 16 已实测（Alembic 迁移） |
| 前端 | React 18 + Vite + TanStack Query 5 + TipTap 2 + tiptap-markdown |
| LLM | 协议层 `LLMProvider` + Mock + OpenAI 兼容（MiniMax / DeepSeek / 任意网关） |
| 编排 | Celery 四队列（default / llm / ingestion / export）+ beat 60s 扫描 Connector 定时 |
| 存储 | DB 存原文；MinIO/S3 存导出副本（可降级） |
| 观测 | `/api/v1/health` 深探针 + `/metrics` Prometheus + trace_id 结构化日志 |
| CI | GitHub Actions（`.github/workflows/ci.yml`） |

## 2. 交接时点状态快照（已实测）

- **git**：main @ `c54fd41`；唯一未提交改动 `apps/web/src/pages/Workspace.tsx`（+5/−2，见 §5.4）
- **测试**：`make test` → **63 passed**（0.96s，Mock provider，零外部依赖）
- **服务在线**：API :8000（health 200）· Web :5173（200）· dsh :3080（401 = 需 token，脚本内置）
- **dsh 环境**：`~/.dsh/env.local` 存在（600 权限，3 行：MiniMax key 可用，DeepSeek key 留空）；
  `~/.local/bin/dsh-studio` 存在
- **dsh 沙箱产物**：`仓库根/.wewrite-scratch/`（runs / corpus / exemplars / lessons，已 gitignore）
- **docker-compose 服务**：postgres / redis / minio / minio-init / worker / beat —— **注意没有 api 服务**（见 §5.3）

## 3. 当前进度（对照执行计划，README「完成情况」表同源）

| EPIC | 内容 | 状态 |
|---|---|---|
| EPIC-00 | 工程基线（目录 / Makefile / compose / .env.example / CI） | ✅ |
| EPIC-01 | RBAC + Secret（Header 身份开发模式 + 角色矩阵；Key 只走环境变量） | ✅ |
| EPIC-02 | Source Library（文本/URL/文件、解析状态、可信等级、归档） | ✅ |
| EPIC-03 | Fact 模型（候选抽取、确认/拒绝/编辑、冲突检测、检索） | ✅ |
| EPIC-04 | FactPack（建/增删 item、冻结+checksum、Clone 版本链） | ✅ |
| EPIC-05 | Voice/Template/Prompt（版本化 + checksum + immutable + clone/publish/archive） | ✅ |
| EPIC-06 | Topic Brief（绑定 frozen 包 + 渠道 + 禁止表述） | ✅ |
| EPIC-07 | LLM Provider（协议 + registry + llm_run 记录 + JSON 一次修复） | ✅ |
| EPIC-08 | 多渠道生成（三渠道独立 job、fact_id 服务端校验、失败不互相回滚） | ✅ |
| EPIC-09 | Fact Checker（确定性层 + LLM 层接口 + approve gate 409） | ✅ |
| EPIC-10 | 编辑器与版本（TipTap + Markdown 契约、revision 不覆盖、选区改写、Diff） | ✅ |
| EPIC-11 | Review（队列 / 退回 / 批准三重校验） | ✅ |
| EPIC-12 | Asset/Export（MD/TXT/JSON(provenance)/SRT(estimated) + 分渠道限制） | ✅ |
| EPIC-13 | 前端页面（P01–P11 + Connector + TipTap 工具栏 + Diff） | ✅ |
| EPIC-14 | 原型验收（Mock 全链路走通） | ✅ |
| EPIC-15 | 测试（63 pytest + 30 Topic Golden 集与评测 CLI） | ✅ |
| EPIC-16 | 安全（SSRF 防护 / 上传双校验 / Prompt 注入包装） | ✅ |
| EPIC-17 | 运维（Celery 四队列 + 容器 + 可观测 + 备份 runbook） | ✅ |
| EPIC-18 | Connector（generic_rest + env 引用鉴权 + JSON→Fact 映射 + 前端页） | ✅ |

## 4. 核心不变量（改动前必读，全部有测试覆盖）

1. **FactPack 冻结后不可变**，修改必须 Clone vN+1；Topic 只能绑定 frozen FactPack
2. 模型输出的 `fact_id` 必须属于当前 FactPack，**服务端校验**（不信任客户端）
3. Deterministic Checker：无 Fact 支持的数字 → blocker；**blocker 未解决不能 approve（HTTP 409）**
4. 重新生成 / 人工保存产生**新 revision，旧 Draft 永不覆盖**；已生成内容永远记录生成时的
   FactPack 版本与 checksum
5. Connector 鉴权凭据**只存环境变量名**（DB 记 `api_key_env`，值运行时从进程环境读取，不落库不入日志）
6. SSRF 防护默认禁私网；本机代理（Clash fake-ip）需 `.env` 设 `SSRF_ALLOW_PRIVATE=true`，**生产必须 false**

关键实现决策（同步/异步双模式、原文存 DB、Alembic 建表、LLM Reviewer mock 透传、
TipTap+Markdown 契约、SRT 标记 estimated、朴素实体启发式）详见 README「关键决策」节，共 8 条。

## 5. 未完成 / 已知遗留（按优先级）

> 注：README「TODO」节目前只写了第 1、2 条；第 3、4 条是本次交接补充，接手后建议顺手同步 README。

### 5.1 dsh 沙箱限制
skill 无法写 `~/.wewrite/runs/`，产出暂落仓库根 `.wewrite-scratch/`（已 gitignore）。
需沙箱放行该路径，或把 wewrite 运行目录迁移到可写位置。

### 5.2 DeepSeek API key 未配置
`~/.dsh/env.local` 中 DeepSeek key 留空；**MiniMax 已可用**（key 在同一文件，600 权限）。

### 5.3 API 容器化缺口
PG 生产化已实测，但 docker-compose 里 postgres / redis / minio / worker / beat 都有，
**唯独没有 api 服务本身**——目前 api 只能裸进程跑。补一个 api service 是自然下一步。

### 5.4 一个已修但未自测的前端修复（当前未提交改动）
**背景**：用户报告「重新生成」看起来没变化——后端每次都成功、前端也每次拉到新版本，
实际是 mock provider 对同选题输出几乎一字不差造成的假象。
**修复**（`apps/web/src/pages/Workspace.tsx`，+5/−2 未提交）：regenerate 成功后明确提示
「已生成新版本 r{N}（旧版本保留，可用『对比上一版』查看差异）」。
**待办**：在前端验证一次（生成 → 重新生成 → 看提示与 Diff），确认后提交。

## 6. 如何启动

```bash
# 后端（默认 SQLite，零外部依赖；Mock provider，无需 API Key）
cd apps/api && python3 -m venv .venv && . .venv/bin/activate
pip install -e . pytest ruff
python -m app.seed                      # 幂等建表 + 种子（4 用户 / 3 渠道模板 / Brand Voice / Prompt）
python -m uvicorn app.main:app --reload --port 8000

# 前端
cd apps/web && npm install && npm run dev    # :5173，/api 代理到 8000

# dsh 内容产出中心
~/.local/bin/dsh-studio                 # :3080（带 token 鉴权）

# 一键命令（根目录 Makefile）
make dev          # 后端
make dev-web      # 前端
make worker       # Celery worker（四队列；需 Redis，先 make compose-up）
make seed         # 幂等建库 + 种子（开发）
make migrate      # 生产 PG：alembic upgrade head（已在 PG 16 实测）
make test         # 63 个测试
make lint         # ruff
make backup       # SQLite 在线备份（保留 7 份）
make compose-up   # postgres/redis/minio/worker/beat
```

**演示账号**（开发模式 Header 身份，无密码）：`admin@ / editor@ / reviewer@ / viewer@ studio.local`，
请求带 `X-Studio-User: <email>`。权限矩阵：admin 全部；editor 产线操作；reviewer 审核+改稿；viewer 只读。
前端设置页可一键切换身份。

**环境变量**：复制根目录 `.env.example` 为 `.env`。关键项：`DATABASE_URL`、`LLM_PROVIDER`、
`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、`MOCK_INJECT_UNFACT_NUMBER`、`SSRF_ALLOW_PRIVATE`、
`TASK_QUEUE_ENABLED`、`CELERY_BROKER_URL`。

## 7. 接真实模型

业务层只面向 `LLMProvider` 协议，切换零业务改动。`.env` 设：

```text
LLM_PROVIDER=openai_compatible   # 兼容 minimax / deepseek / 任意 OpenAI 风格网关
LLM_BASE_URL=...
LLM_API_KEY=...                  # 只放环境变量，DB 不存明文
LLM_MODEL=...
```

MiniMax key 已在 `~/.dsh/env.local`（600 权限）可直接取用。接真实模型后用同一 Golden 集对比：

```bash
cd apps/api && python scripts/evaluate_content.py --limit 3   # 冒烟
python scripts/evaluate_content.py                            # 30 Topic 全量，报告落 evals/reports/
```

`MOCK_INJECT_UNFACT_NUMBER=true` 可让 mock 注入 FactPack 外数字，验证 blocker → 409 全链路。

## 8. 目录速查（已逐目录核对）

```text
apps/api/app/
├── models.py                # 全部数据模型（PRD §8 + Connector + STU 扩展字段）
├── config.py / db.py / deps.py / main.py / seed.py / observability.py
├── routers/                 # sources facts fact_packs topics generate reviews assets
│                            # templates dashboard users connectors health external
├── services/
│   ├── parsers.py           # TXT/MD/CSV/JSON/PDF/HTML → 统一 ParsedDocument
│   ├── url_fetch.py         # SSRF 安全抓取（禁内网/限大小/限跳转）
│   ├── fact_extractor.py    # 确定性候选事实抽取
│   ├── factpack_service.py  # 冲突检测 + 版本 checksum
│   ├── factchecker.py       # ★ Deterministic Checker（数字/日期/风险词/朴素实体）+ LLM 层
│   ├── exports.py           # MD / TXT / JSON / SRT
│   ├── connector_service.py # 外部 API 拉取 + JSON→Fact 映射
│   ├── storage_service.py   # MinIO/S3（可降级）
│   └── generation/          # providers(mock/openai_compatible) + orchestrator + renderers + mock_content
├── tasks/                   # celery_app.py + worker_tasks.py（llm/ingestion 队列，开关式启用）
└── llm/prompts/             # douyin.txt / xiaohongshu.txt / wechat.txt（文件为准，启动同步版本+checksum）
apps/api/alembic/           # 初始迁移（Base.metadata）
apps/api/scripts/evaluate_content.py    # Golden 评测 CLI
apps/api/evals/             # golden_topics.json（30 Topic）+ reports/
apps/api/tests/             # 63 个 pytest（端到端主干 + 不变量 + 服务层单测）
apps/web/src/pages/         # Dashboard Sources Connectors FactPacks Topics Workspace(三栏)
│                           # Review Assets Templates Settings
apps/web/src/components/    # ui.tsx / editor.tsx(TipTap) / RevisionDiff.tsx(LCS)
docs/runbooks/backup-restore.md
.github/workflows/ci.yml
docker-compose.yml          # postgres/redis/minio/minio-init/worker/beat（无 api，见 §5.3）
03_ai_content_studio_PRD.md / 04_ai_content_studio_execution_plan.md   # 需求与任务依据
```

## 9. 给下一个 Agent 的建议

1. **第一件事：冒烟确认零退化。** 按本文档 §6 启动，对照 README「完成情况」表 / 本文 §3 逐项勾；
   跑 `make test`（应 63 passed）。服务现在都活着（API :8000、Web :5173、dsh :3080），
   可直接先做页面级冒烟。
2. **顺手处理 §5.4**：前端验证 regenerate 提示修复，确认后提交（这是当前唯一的脏工作区）。
3. **然后决定优先解哪条遗留**：交接人倾向先做 §5.1（dsh 沙箱路径）与 §5.3（compose 补 api 服务）。
4. **高频改动热点**：`apps/api/app/services/factchecker.py`（风险词/实体启发式 + LLM 层接口）。
   调过规则后务必 `make test` + `python scripts/evaluate_content.py --limit 5` 双验证，
   防止确定性规则退化（Golden 集指标：无来源数字率 / Fact 覆盖率 / 校验通过率）。
5. **接真实模型**见 §7，MiniMax 可立即接入，是投入产出比最高的增强。
6. 需求背景与任务拆解看根目录 `03_*_PRD.md` 与 `04_*_execution_plan.md`；
   日常参考 README（含「关键决策」8 条与多副本指标方案：Prometheus 逐副本抓 /metrics，
   自带 instance label，不需要 Pushgateway）。
