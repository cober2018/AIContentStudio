# AI Content Studio 全量测试报告（PRD 对照 + 真实生产环境 E2E）

> 测试时间：2026-09-17 · 测试人：ZCode Agent · 基线：main 工作区（含设置页/模板删除/单版本生效三项未提交改动）
> 85 个 pytest 全绿（0.96s）· 前端 build 通过 · ruff 干净

---

## 第一部分：PRD / 执行计划 对照缺口清单

### 已完整实现（抽查验证 + 测试覆盖）

PRD §15 验收标准 15 条全部有测试覆盖（85 pytest，含 §22 端到端用例 20 步）；
EPIC-00~18 全部完成。特别核实以下曾怀疑项，**实际已实现**：
- `draft_claim` / `draft_claim_fact` 表与 STU-090 对齐逻辑（generate.py:214）
- `audit_log` 实际写入（reviews/sources 多处）
- Facts 批量确认/拒绝 `POST /facts/bulk-status`
- Topic `PATCH /topics/{id}`
- 资产一键复制（clipboard）

### 功能缺口（PRD/计划明确要求，未实现）

| # | 缺口 | 依据 | 建议 |
|---|---|---|---|
| 1 | 编辑器缺 **查找(find)** 与 **字数统计** | STU-101 | TipTap 生态有现成扩展，前端小改 |
| 2 | 模板层缺 **Content Policy**（四层模板只建了三层） | PRD §7.12 | 与 Brand Voice 同构，一个表+一个 Tab |
| 3 | 缺 `POST /drafts/{id}/regenerate-section` 分节重生成 | PRD §12 | 现有整篇 regenerate + 选区改写可覆盖 80% 场景，优先级低 |
| 4 | 资产库多维筛选（date/topic/status/tags/FactPack/Voice），现仅渠道 | P10 | 前端查询参数扩展 |
| 5 | 业务指标缺失：`/metrics` 只有 HTTP 层，STU-172 列的 source_parse_success_rate / generation_success_rate / factcheck_blocker_rate 等全部没有 | STU-172 | 在服务层埋 Counter |
| 6 | 集成测试未按计划跑真实 PostgreSQL/Redis（全部内存 SQLite） | STU-151 | compose 起 PG 跑一遍标记 integration |
| 7 | 前端无 Vitest/Playwright 测试；无 mypy | STU-003/计划技术栈 | CI 已有 web build，测试框架待补 |
| 8 | 队列四条（default/llm/ingestion/export），计划五条（缺 maintenance） | STU-171 | 低优先级 |
| 9 | compose 缺 api/web 容器（已知遗留） | STU-170 | 补 Dockerfile + service |
| 10 | 上传文件名随机化 / 对象存储私有 + signed URL（V1 原文存 DB，已文档化） | STU-162 | 按升级路径走 MinIO 时一并做 |
| 11 | Secret 加密存储（env 明文；设置页覆盖表存明文 API Key 是本周为前端配置加的权衡，已记 README 决策 9） | PRD §14.3 | 生产走 secret manager |
| 12 | **自动发布**：PRD V1 明确排除（§3「V1 不直接自动发布」、计划 §24），本期用户需求已要求 → 属 V2 开发项 | — | 见第二部分发布能力结论 |

### 本次 E2E 实测新发现的产品缺陷/缺口

| # | 发现 | 影响 | 修复建议 |
|---|---|---|---|
| 13 | **Connector Endpoint 无编辑接口**（只有建/删/拉，PATCH → 405） | 改映射要删了重建，历史配置丢失 | 补 PATCH |
| 14 | **Connector 映射不支持嵌套字段路径**（fields/statement 只支持一层；DreamO dashboard 的 market_temperature.turnover_amount 取不到） | 深层数据无法直接映射 | 支持 `a.b.c` 点路径 |
| 15 | **映射缺 subject 时冲突检测产生跨实体假冲突**（5 条行业事实 subject=None + 同 predicate + 同日期 → 4 条被标 conflict） | 冲突检测把不同行业当成同一指标 | 映射校验强制 subject；或 conflict key 含 statement |
| 16 | **长转写文本抽取重复严重**：无分隔 6.6k 字文本抽出 48 条完全相同语句；分句后 50 条中仍有 15 条重复 | 候选确认负担大 | 抽取器按 statement 去重 |
| 17 | **真实模型同步生成撞超时**：小红书 120s 撞 httpx timeout 失败（抖音 93s/公众号 38s 成功） | 同步模式 + 真实模型不可靠 | httpx timeout 调到 300s；或接真实模型时默认 TASK_QUEUE_ENABLED=true |
| 18 | **短时效 JWT 不适配 Connector 静态凭据**：DreamO access_token 数小时过期，env 变量模式无法续期 | 量化平台定时拉取会断 | Connector 增加 token 刷新型 auth（login_url + 凭据换 token），或量化平台发长期服务 token |

---

## 第二部分：真实生产环境端到端测试（全链路走通）

### 数据源（真实生产系统）

| 数据源 | 地址/位置 | 鉴权 | 状态 |
|---|---|---|---|
| DreamOAgents 量化平台（生产） | https://dreamotech.cn | JWT（POST /api/auth/login） | ✅ 在线，数据日期 2026-09-17（当日） |
| └ 复盘看板 /api/v1/review/dashboard | 市场状态：震荡偏强 68 分；涨 2576/跌 2820；涨停 47；成交 18365 亿 | Bearer | ✅ |
| └ 情绪看板 /api/v1/review/sentiment | 总分 2.6/8，局部恐慌区，仓位建议 0-20% 防守（source_mode=ads_v2） | Bearer | ✅ |
| └ 行业看板 /api/v1/review/industry | 主攻：通信设备/塑料/仪器仪表/元件/汽车零部件 | Bearer | ✅ |
| dtk 抖音归档 API | http://localhost:8080（Douyin_TikTok_Download_API v5.1.0） | X-API-Key | ✅ 122 条抖音内容 |
| 抓取转写库（radar PG :5544） | source_item 123 条 + transcript_segment 2849 段（55 视频完整口播转写，当日仍在更新） | PG | ✅ |

### E2E 执行记录（全部真实操作）

1. **Connector 接入**：建 2 个 Connector、4 个端点（情绪总分/底部共振/行业主攻/抖音归档），全部拉取成功 → Source 3-6
2. **转写文本导入**：9.17 财经收评（610 段 ASR 转写，6622 字）→ 分句重组导入 Source 8 → 抽取 50 候选（去重 35）
3. **事实确认**：确认 27 条（量化看板 7 + 行业 5 + 转写 14 + 其他 1）；处理 subject 缺失假冲突（见缺陷 #15）
4. **FactPack 版本链**：v1(18) → 冻结 → v2(18) → v3(+行业 5，22 条) → 冻结，checksum `bf8eb5f38d6a0247`；「冻结后不可改、Clone 递增」不变量全程成立
5. **Topic**：「9·17复盘：油价新高、美联储加息落地，A股的结构性机会」绑定 v3 + 三渠道
6. **生成（真实 MiniMax-M3）**：抖音 ✅ 93s；公众号 ✅ 38s；小红书 ❌ 120s 超时 → regenerate ✅ 69s（顺带验证了「失败不互相回滚 + 失败可重试不覆盖旧稿」）
7. **内容质量**：抖音稿 Hook/口播/分镜/字幕/B-roll/事实引用（F072/F081…）完整；量化数据（情绪 2.6/局部恐慌区/0-20% 仓位）与转写事实（129 美元/+14%/3.75-4%/10Y 5.02%/科创50 +4.14%/成交 1.85 万亿）交叉引用正确
8. **FactCheck**：抖音 pass / 小红书 pass / 公众号 warning（实体启发式把「某AI公司」当新实体——误报样本，非阻塞）；LLM Reviewer 层随 openai_compatible 自动启用
9. **Review**：三稿 submit → reviewer 批准（201）→ 资产 4/5/6 入库，待审队列清零
10. **Export**：6 份产物全部成功——抖音 SRT(标记 estimated)+TXT、公众号 MD+JSON(12k 含 provenance)、小红书 MD+TXT
11. **自动发布·公众号草稿箱** ✅ **真实推送成功**：
    - `wewrite preview` 排版 → 微信兼容性校验通过
    - `wewrite publish --cover` → access_token 获取 → 封面上传(media_id `TrHZ7fvz...K69oNuTx7...`) → **草稿创建成功 media_id `TrHZ7fvz...qxPn1Nsf85ltlBKgJqwCL82_oh-`**
    - 该草稿现在就在你的公众号后台草稿箱，可随时查看/删除
12. **自动发布·抖音/小红书** ⚠️ **未打通**：`new_media/social-auto-upload`（浏览器自动化上传工具）已部署，但 `cookies/douyin_uploader` 与 `cookies/xiaohongshu_uploader` 目录为空——**未登录，需要扫码配置账号**；Studio 本体无发布模块（PRD V1 明确排除）

### 结论

- **核心链路（Source→Fact→FactPack→Topic→生成→FactCheck→Review→Asset→Export→公众号草稿箱）端到端全部走通，用的全部是真实生产数据与真实大模型**
- 抖音/小红书草稿箱差「账号登录配置」这一步（工具已在），Studio 侧需要新增导出→发布的对接（建议做成 EPIC-19：Publish Connector）
- 建议优先修复缺陷 #17（真实模型超时）与 #15（冲突假阳性），它们直接影响日常使用

### 环境备注

- Studio API 已带 `DREAMO_API_TOKEN / DTK_API_KEY / SSRF_ALLOW_PRIVATE=true` 重启（nohup，日志 /tmp/studio_api.log）；DreamO token 过期后 Connector 拉取会 401，需重新登录换 env（长期方案见缺陷 #18）
- E2E 产生的数据都在开发库：Source 3-10、FactPack 3-5(v1-v3)、Topic 2、Job 13-15/23、Draft 21-23、Asset 4-6，可在前端逐页复查
