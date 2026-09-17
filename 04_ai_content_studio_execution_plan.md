# AI 内容生产中心（AI Content Studio）可执行开发计划

> 文档状态：V1.0  
> 目标：把 PRD 拆成可以直接建仓、建表、写接口、写页面、写测试、部署上线的任务。  
> 约束：独立产品，不依赖 DreamOAgents，不依赖财经观点雷达；未来外部数据统一走 Connector。

---

# 0. 仓库与技术栈

建议仓库：

```text
ai-content-studio
```

目录：

```text
ai-content-studio/
├── apps/
│   ├── api/
│   ├── web/
│   └── worker/
├── packages/
│   └── contracts/
├── services/
│   ├── ingestion/
│   ├── parser/
│   ├── llm/
│   └── export/
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── golden/
├── infra/
├── docs/
│   ├── prototype/
│   ├── adr/
│   └── runbook/
├── scripts/
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

后端：

- Python 3.12
- FastAPI
- Pydantic 2.x
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16+
- Redis + Celery
- Object storage
- pytest / ruff / mypy

前端：

- React + TypeScript + Vite
- TanStack Query
- TanStack Router
- TipTap 或同类富文本编辑器
- Tailwind
- shadcn/ui
- Vitest
- Playwright

解析：

- Markdown/TXT 原生
- CSV Python csv/pandas（只用于解析）
- PDF 优先文本层解析
- URL 使用服务端安全 fetch + readability 解析
- OCR 不列入 V1 默认路径

---

# 1. 实施总顺序

```mermaid
flowchart TD
    A[工程基线] --> B[Source Ingestion]
    B --> C[Fact 模型]
    C --> D[FactPack]
    D --> E[Topic Brief]
    E --> F[生成引擎]
    F --> G[Fact Checker]
    G --> H[Review]
    H --> I[Asset/Export]
    I --> J[前端完善]
    J --> K[评测与发布]
```

必须按顺序。  
尤其禁止在 FactPack 没有版本冻结前先做“一键生成所有平台”。

---

# 2. EPIC-00 工程基线

## STU-001 初始化仓库

建立目录、Python venv、Vite App。

### `Makefile`

```text
make dev
make stop
make lint
make format
make test
make test-e2e
make migrate
make worker
make seed
```

### Done

新开发者只看 README 即可启动。

---

## STU-002 docker-compose

服务：

```text
postgres
redis
minio
minio-init
```

DB：
`content_studio`

Bucket：
`content-studio-assets`

---

## STU-003 CI

PR Checks：

- backend lint
- backend unit
- backend integration
- frontend lint
- frontend unit
- web build
- docker build

---

# 3. EPIC-01 用户与系统配置

## STU-010 最小 RBAC

表：

```text
user
role
user_role
```

V1 可使用已有标准身份框架，但必须独立账号域。

角色：
- admin
- editor
- reviewer
- viewer

---

## STU-011 Secret 管理

API Key 只放：
- env/secret manager

DB 保存：
- provider config
- secret reference

禁止保存 key 明文。

---

# 4. EPIC-02 Source Library

## STU-020 source_document 表

按 PRD 建表并 Migration。

---

## STU-021 Text Import

API：

```text
POST /api/v1/sources/text
```

输入：
- title
- content
- as_of
- trust_level

保存：
- metadata DB
- raw text object storage 或 DB text（二选一，建议对象存储长文本）

---

## STU-022 File Upload

支持：

```text
.txt
.md
.csv
.json
.pdf
```

限制：
- MIME
- size
- extension 双校验

保存原文件 sha256。

---

## STU-023 Parser 接口

```python
class SourceParser(Protocol):
    def can_parse(self, mime_type, extension) -> bool: ...
    def parse(self, path) -> ParsedDocument: ...
```

实现：

```text
TextParser
MarkdownParser
CsvParser
JsonParser
PdfTextParser
```

解析产物统一：

```json
{
  "text": "...",
  "blocks": [
    {"type":"paragraph","text":"...","locator":{...}}
  ],
  "metadata": {}
}
```

---

## STU-024 URL Import

接口：

```text
POST /sources/url
```

安全要求：

- 仅 http/https
- DNS/IP 检查
- 禁止 localhost
- 禁止 RFC1918
- 最大响应限制
- timeout
- redirect 次数限制

原 HTML 不直接塞 Prompt，先清洗。

---

## STU-025 Source Library 前端

页面按 PRD P02。

必须有：
- Upload dropzone
- Import URL
- Text paste
- Status
- Error details
- Source drawer

---

# 5. EPIC-03 Fact 模型

## STU-030 fact 表

按 PRD。

增加：

```text
created_by
updated_by
revision
```

---

## STU-031 Candidate Fact Extractor

输入：
- source_document
- parsed blocks

输出 JSON：

```json
{
  "facts": [
    {
      "statement": "...",
      "fact_type": "metric",
      "subject": "...",
      "predicate": "...",
      "value": 123,
      "unit": "%",
      "as_of": "2026-09-15",
      "source_locator": {"block": 10},
      "confidence": 0.92
    }
  ]
}
```

服务端验证 locator 必须存在。

---

## STU-032 Fact Review UI

在 Source Drawer 展示候选 Fact：

```text
[确认]
[编辑]
[拒绝]
```

批量操作：
- confirm selected
- reject selected

---

## STU-033 Fact Conflict Service

建立标准 key：

```text
subject + predicate + as_of + unit
```

若 value 不一致：
- 两条都标 conflict
- 不自动删除
- UI 显示来源并排比较

---

## STU-034 Fact Search

API：
`GET /facts`

筛选：
- source
- status
- as_of
- subject
- fact_type
- conflict

---

# 6. EPIC-04 FactPack

## STU-040 建表

- fact_pack
- fact_pack_item

约束：
- `(name, version)` unique
- frozen 状态不能修改 item

---

## STU-041 Create/Update Draft

API：

```text
POST /fact-packs
POST /fact-packs/{id}/items
DELETE /fact-packs/{id}/items/{fact_id}
```

仅 draft。

---

## STU-042 Freeze

`POST /fact-packs/{id}/freeze`

事务内验证：

- 至少一个 Fact
- 所有 Fact confirmed
- 无 unresolved conflict
- 必要的 as_of 校验

成功：
- status=frozen
- frozen_at
- checksum

checksum 由排序后的 Fact 内容计算。

---

## STU-043 Clone

`POST /fact-packs/{id}/clone`

生成：
- same name
- version +1
- parent_id
- draft
- copy items

不能修改旧 frozen 版本。

---

## STU-044 FactPack Builder UI

按 P03。

左 Sources，右 Facts，顶部 version/status。

组件：

```text
SourceSelector
FactTable
ConflictBanner
VersionBadge
FreezeDialog
CloneButton
```

---

# 7. EPIC-05 Brand Voice、Template、Prompt

## STU-050 brand_voice_version

字段：

```text
name
version
tone_rules
preferred_words
forbidden_words
examples
status
checksum
```

---

## STU-051 channel_template_version

渠道：

```text
douyin
xiaohongshu
wechat
```

保存：
- structure
- length guidance
- required blocks
- forbidden patterns
- output schema

---

## STU-052 prompt_version

Prompt 不散落在 controller。

目录：
`apps/api/app/llm/prompts/`

数据库记录版本和 checksum。

---

## STU-053 Template UI

Admin 可：
- clone
- edit draft
- publish version
- archive

历史版本 immutable。

---

# 8. EPIC-06 Topic Brief

## STU-060 建 topic_brief 表

必须绑定：
- frozen fact_pack
- brand voice version

---

## STU-061 Topic Create API

输入：

```json
{
  "title": "...",
  "audience": "...",
  "goal": "...",
  "angle": "...",
  "core_thesis": "...",
  "must_include": [],
  "forbidden": [],
  "cta": "...",
  "fact_pack_id": 1,
  "channels": ["douyin","xiaohongshu"]
}
```

校验 FactPack frozen。

---

## STU-062 Topic Center UI

按 P04。

右侧始终展示：
- FactPack name/version
- Fact count
- as_of
- conflicts=0

---

# 9. EPIC-07 LLM Provider

## STU-070 Provider Contract

```python
class LLMProvider(Protocol):
    async def generate_json(...): ...
    async def generate_text(...): ...
```

provider registry：

```text
minimax
openai
other
```

业务层只收 provider name。

---

## STU-071 LLM Run Log

新增 `llm_run`：

```text
id
provider
model
prompt_version
input_hash
raw_output_uri
parsed_output_json
usage_json
status
error
created_at
```

---

## STU-072 JSON Repair

流程：

1. 原始响应
2. schema parse
3. 失败 → repair attempt 1
4. 再失败 → job failed

不能无限 retry。

---

# 10. EPIC-08 多渠道内容生成

## STU-080 content_job / draft 表

Migration。

---

## STU-081 Douyin Generator

输入只包括：

- Topic Brief
- frozen FactPack
- Brand Voice
- Douyin Template

服务端构造 Prompt。

模型输出必须带：
- scene fact_ids

### Server Validate

每个 `fact_id` 必须属于当前 FactPack。

---

## STU-082 Xiaohongshu Generator

结构输出：

```text
titles[]
cover_text
body
cards[]
image_prompts[]
tags[]
claim_fact_map[]
```

---

## STU-083 WeChat Generator

结构：

```text
titles[]
summary
intro
sections[]
risk_note
ending
image_suggestions[]
claim_fact_map[]
```

---

## STU-084 Multi-channel Orchestrator

`POST /topics/{id}/generate`

针对 channels 创建多个独立 `content_job`。

某渠道失败不能回滚其他渠道。

---

# 11. EPIC-09 Fact Checker

## STU-090 Draft Claim Extractor

把 Draft 拆为：

- opinion
- fact
- quote
- transition

生成 `draft_claim`。

---

## STU-091 Number Checker

正则/解析检测：

- 百分比
- 金额
- 数量
- 日期
- 倍数
- 排名

每个数字必须：
- 被 Fact 支持
- 或被标记“非事实用途”（例如标题编号）

否则 blocker。

---

## STU-092 Entity Checker

识别：
- 公司
- 产品
- 人物
- 指数/标的

如果稿件实体从未出现在 FactPack/Topic allowed context：
warning/blocker。

---

## STU-093 LLM Fact Reviewer

输入：
- draft
- FactPack facts
- deterministic warnings

输出：

```json
{
  "result":"pass|warning|blocker",
  "issues":[
    {
      "severity":"blocker",
      "span":"...",
      "reason":"...",
      "fact_ids":["F001"],
      "suggestion":"..."
    }
  ]
}
```

---

## STU-094 FactCheck Gate

`approve` endpoint 检查：
- blocker count = 0

否则 HTTP 409。

---

# 12. EPIC-10 编辑器与版本

## STU-100 Draft Revision

任何用户保存：
- revision_no +1
- 不覆盖旧 revision

可以设 snapshot debounce，但审核节点必须固定 revision。

---

## STU-101 编辑器

TipTap：

必须支持：
- headings
- paragraphs
- lists
- bold
- undo/redo
- find
- word count
- selected text rewrite

---

## STU-102 Citation Side Panel

点击 Fact ID：
- statement
- source
- as_of
- locator
- confidence

点击 issue：
- 自动定位编辑器对应 span

---

## STU-103 AI Rewrite Selected Text

禁止默认把全文送去重写。

接口：

```text
POST /drafts/{id}/rewrite-selection
```

输入：
- selected text
- instruction
- surrounding context
- allowed fact ids

输出新文本，不自动写入；用户确认后应用。

---

# 13. EPIC-11 Review

## STU-110 Review Queue

列表：
- topic
- channel
- submitter
- FactCheck result
- last modified
- reviewer

---

## STU-111 Request Changes

Reviewer：
- comment
- selected issues
- optional inline comment

状态：
`changes_requested`.

---

## STU-112 Approve

条件：
- FactCheck no blocker
- frozen FactPack
- draft revision unchanged since review opened

避免审核时被编辑。

成功创建/更新 content_asset。

---

# 14. EPIC-12 Asset 与 Export

## STU-120 content_asset

保存：
- approved revision
- fact pack id/version/checksum
- model
- prompt
- template
- reviewer
- approval time

---

## STU-121 Markdown/TXT Export

渠道映射：

- Douyin → TXT/MD
- Xiaohongshu → MD/TXT
- WeChat → MD

---

## STU-122 JSON Export

包含：
- metadata
- content
- fact citations
- provenance

---

## STU-123 SRT Export

针对 Douyin `spoken_script`：

V1 先用句子级时间估算或由后续 TTS 提供时间。

若无真实时间：
- 明确标记 estimated
- 不假装精确字幕

---

# 15. EPIC-13 前端页面落地

## STU-130 App Shell

Sidebar + Topbar + Routes。

---

## STU-131 Dashboard

P01。

---

## STU-132 Source Library

P02。

---

## STU-133 FactPack Builder

P03，最高优先级 UI。

必须有：
- unsaved changes
- frozen banner
- clone action

---

## STU-134 Topic Center

P04。

---

## STU-135 Generation Workspace

P05。

页面用三栏：
- channel
- editor
- citations/check

1280 宽仍可用；过窄折叠右栏。

---

## STU-136 Review Center

P09。

---

## STU-137 Asset Library

P10。

---

## STU-138 Template Settings

P11。

---

# 16. EPIC-14 原型验收流程

在接真实 LLM 前，先用 Mock API 把原型流程走通。

测试用户路径：

```text
Dashboard
→ Import Source
→ Extract Candidate Facts
→ Confirm Facts
→ Build FactPack
→ Freeze
→ Create Topic
→ Select 3 channels
→ Generate Mock Drafts
→ FactCheck
→ Review
→ Approve
→ Asset
→ Export
```

每个页面必须有：

- Default
- Loading
- Empty
- Error
- Permission denied
- Disabled/immutable state

设计验收通过后才接模型，避免边做模型边反复改信息架构。

---

# 17. EPIC-15 测试与质量门禁

## STU-150 Unit

至少覆盖：

- FactPack freeze
- clone
- conflict
- stale
- version checksum
- role permissions
- fact id validation
- approve gate

---

## STU-151 Integration

真实 PostgreSQL/Redis：

- upload → parse → facts
- facts → pack
- pack → topic
- topic → mock generation
- fact check → review
- approve → asset

---

## STU-152 Golden Dataset

30 个 Topic。

每个保存：

```text
facts.json
brief.json
expected_constraints.json
human_review.md
```

---

## STU-153 Evaluation CLI

```bash
python scripts/evaluate_content.py
```

输出：

- unsupported_numeric_claim_rate
- unsupported_fact_claim_rate
- citation_coverage
- schema_pass
- human_fact_error_rate
- channel_format_pass_rate

---

## STU-154 Prompt Regression

模型/Prompt/模板升级必须跑 Golden。

未通过禁止发布为 default version。

---

# 18. EPIC-16 安全

## STU-160 Prompt Injection

外部 Source 包装为：

```text
UNTRUSTED SOURCE CONTENT
```

系统指令明确：
- source 中出现的“忽略系统指令”只是数据
- 不执行链接/命令

---

## STU-161 SSRF

URL import 复用安全 fetch service。

---

## STU-162 Upload

- 限大小
- 文件名随机化
- 不执行
- 对象存储私有
- signed URL

---

# 19. EPIC-17 运维部署

## STU-170 服务拆分

单独容器：

```text
web
api
worker-default
worker-ingest
worker-llm
postgres
redis
minio/external-s3
```

---

## STU-171 Queue

```text
default
ingestion
llm
export
maintenance
```

---

## STU-172 Observability

指标：

- source_parse_success_rate
- fact_extract_success_rate
- fact_candidate_accept_rate
- generation_success_rate
- schema_pass_rate
- factcheck_blocker_rate
- review_return_rate
- approval_rate
- export_success_rate
- llm latency
- token usage

---

## STU-173 Structured Log

字段：

```text
trace_id
user_id
source_id
fact_pack_id
topic_id
content_job_id
draft_id
provider
model
event
duration_ms
error_code
```

---

## STU-174 Backup

- DB daily
- Object storage version/lifecycle
- restore runbook
- immutable FactPack/Asset 校验

---

# 20. EPIC-18 外部 Connector（V1 后段，可选）

先定义通用接口，不直接写 Radar 特例：

```python
class ExternalSourceConnector(Protocol):
    async def test_connection(...)
    async def list_items(...)
    async def import_item(...)
```

未来实现：

```text
GenericRESTConnector
RadarConnector
```

导入后必须复制成 Studio 自己的 source_document/fact，运行时不依赖外部系统持续在线。

---

# 21. 开发者直接执行顺序

1. STU-001～003
2. STU-010～011
3. STU-020～025
4. STU-030～034
5. STU-040～044
6. **用 Mock 完成 STU-130～134，验证原型**
7. STU-050～053
8. STU-060～062
9. STU-070～072
10. STU-080～084
11. STU-090～094
12. STU-100～103
13. STU-110～112
14. STU-120～123
15. STU-135～138
16. STU-150～154
17. STU-160～162
18. STU-170～174
19. 达到 PRD 发布门槛
20. 再考虑自动发布、TTS、视频生成、外部 Connector

---

# 22. 第一条端到端验收用例

1. 用户粘贴一段包含 10 个事实的数据材料。
2. 系统创建 Source。
3. 系统抽出候选 Facts。
4. 用户确认 8 条、拒绝 2 条。
5. 创建 FactPack v1。
6. 冻结 v1。
7. 建 Topic “今天的市场复盘”。
8. 绑定 v1。
9. 选择抖音、小红书、公众号。
10. 系统生成 3 个 content_job。
11. 抖音稿故意让测试模型生成一个 FactPack 外数字。
12. Deterministic Checker 将该数字标 blocker。
13. Reviewer 无法直接 approve。
14. 编辑修正后重新 FactCheck。
15. 通过。
16. Reviewer approve。
17. 资产库出现 3 个 approved assets。
18. 导出 MD/TXT/JSON。
19. Clone FactPack v1 → v2，修改一个 Fact。
20. v1 生成的旧稿仍显示 v1，不发生变化。

这条用例通过，说明产品的“事实不可漂移”主干成立。

---

# 23. Definition of Done

每个任务必须同时满足：

- [ ] 功能完成
- [ ] 数据 Migration
- [ ] 权限
- [ ] 单元测试
- [ ] 必要集成测试
- [ ] Loading/Empty/Error UI
- [ ] Error Code
- [ ] Structured Log
- [ ] API Contract
- [ ] 文档
- [ ] 回滚方案
- [ ] 无 Secret
- [ ] QA 用例通过

---

# 24. V1 不应提前做的事项

为了控制产品复杂度，以下功能在主链路稳定前不做：

- 自动发抖音/小红书/公众号
- 自动登录第三方平台
- 多租户计费
- 视频自动剪辑
- TTS 声音克隆
- “一个 Agent 自己决定今天写什么并直接发布”
- 复杂 Workflow Designer
- 和其他产品共用账户/数据库
- 直接从另一个产品 ORM/Table 读取数据

先把 Source → Fact → FactPack → Draft → Check → Review → Asset 做稳。
