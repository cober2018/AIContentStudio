# 全链路冒烟测试报告（生产环境 · 全配置遍历 · 工作流全支线）

> 测试时间：2026-09-18 · 方式：真实生产环境（量化看板 API + dtk 归档 + MiniMax-M3 真实模型 + 公众号草稿箱）
> 结论：**所有配置项遍历完成；数据接入、内容链、工作流全部支线端到端打通（含异步队列模式）；过程中发现并修复 5 个真实缺陷，评估出 4 个业务缺口并处置。**

---

## 一、测试前的业务评估与功能补齐

从业务视角把全链支线过了一遍，发现两个设计缺口并**先补齐再测试**：

| 缺口 | 业务影响 | 处置 |
|---|---|---|
| 工作流缺「人工确认事实」节点（设计稿 S3 承诺） | 舆情转写等低可信来源被静默自动确认，违背 PRD「人工确认事实」核心 | 实现 `confirm_facts` 人工节点：抽取后挂起，勾选确认/拒绝后断点续跑；「每日舆情→荐题」模板升级为 6 节点（pull→extract→**人工确认**→freeze→suggest→**人工采纳**） |
| 工作流生成节点只适配同步模式 | 异步队列（TASK_QUEUE_ENABLED）下节点拿 queued 空转，支线断裂 | 引擎轮询 job 至终态（上限 420s），画布在同步/异步两种模式下行为一致 |

## 二、冒烟中实测发现并修复的缺陷（5 个）

| # | 缺陷 | 修复 |
|---|---|---|
| 1 | 定时拉取必失败：beat 派发的 actor「scheduler」非真实用户，任务直接取消 | worker 兜底创建系统账号 |
| 2 | 工作流生成节点 dispatch 后未 commit：异步消息先于事务落库到达，worker「查无此 job」 | dispatch 前 commit |
| 3 | **异步队列 + SQLite 并发写锁**：worker 与 API 同时写库触发 database is locked，fact-check/改写全线 500 | SQLite 开 WAL + busy_timeout=8000 + synchronous=NORMAL（生产 PG 不受影响） |
| 4 | MiniMax 思考模型 `<think>` 泄漏进取区改写结果 | generate_text 输出同样剥离 think 块 |
| 5 | 工作流批准节点固定操作 context 里的旧 draft_id——人工修稿产生新 revision 后，画布批的是过期稿 | 批准/校验节点统一改取该渠道**最新 revision** |

另修复：人工节点 complete 被闸门拒绝（409）后节点卡在 running——现恢复 waiting_input 可再次操作；AI 荐题对模型偶发解析失败增加一次调用级重试（record_run 留痕）。

## 三、配置遍历（全部配置项过了一遍）

| 配置 | 结果 |
|---|---|
| 模型 Profiles：minimax（启用，真实 key）+ deepseek（占位停用，key 留待配置） | ✅ |
| 场景路由 4 项显式配置：generate / rewrite / fact_check / topic_discovery → minimax | ✅ 实测各环节按路由生效 |
| 技能插件：默认目录扫描 66 个技能；启用 wewrite-write/topic/review；MCP 登记 dsh-web | ✅ |
| dsh 执行层：默认模型/备选/超时/重试/产出目录保存，并真实写回 `~/.dsh/settings.yaml`（自动备份） | ✅ |
| Connector 定时：dtk 端点 interval=2min + Celery beat 60s 扫描 + ingestion 队列消费 | ✅ 自动拉取 source 23 |
| 队列：TASK_QUEUE_ENABLED=true + 独立 Redis DB(/2)，worker(-B) 消费 llm/ingestion | ✅ 冒烟后恢复同步默认 |

## 四、端到端支线清单（23 项全过）

**数据接入（8）**：REST 拉取×3（量化情绪/底部共振/行业，新 token 后）✅ · local_git 拉取（DreamO CHANGELOG+git log）✅ · URL 导入 ✅ · CSV 上传 ✅ · JSON 上传 ✅ · 文本导入→抽取→批量确认 ✅ · dtk 定时拉取（beat→队列→worker）✅ · 抖音手动拉取 ✅

**内容链（9）**：AI 荐题（真实模型 13s）✅ · FactPack 冻结+克隆 ✅ · 三渠道生成（异步队列 40s+）✅ · 生成失败异步重试 ✅ · 选区改写（真实模型）✅ · FactCheck 三稿 ✅ · **blocker→人工修稿(新 revision)→复检 pass→批准**（PRD §22 核心用例真实复现）✅ · Review 退回→再提交→批准 ✅ · 导出 6 文件（txt/srt/md×2/html/json）✅

**工作流（4）**：「每日舆情→荐题」双人工闸全链（真实拉取+真实荐题+采纳建题）✅ · 「生成→出库」**异步队列模式**三渠道分叉（生成→校验→批准→导出→公众号草稿箱真实发布 media_id `TrHZ...9lc...`）✅ · 失败→从失败节点重试 ✅ · 取消支线（测试覆盖）✅

**横切（4）**：RBAC（viewer 启动工作流/改配置均 403）✅ · health 深探针 ✅ · Golden 评测 --limit 3（无源数字率 0，Fact 覆盖率 1.0）✅ · make backup ✅

## 五、业务评估结论：仍缺失/建议项（本轮不阻塞，已记录）

1. **dtk 映射缺「发布日期」fact**：本轮 blocker 全部源于模型引用了原始数据中存在、但未映射成 Fact 的视频发布日期。建议端点映射增加 `published_at → as_of fact`，让日期引用有事实支撑（数据层 10 分钟改动）。
2. **真实模型 blocker 率偏高**：自由度大的选题下 MiniMax 约 1/3 概率引入无源数字。这正是校验闸门的价值，但建议：① 荐题候选附「必含事实」更严格约束生成；② 考虑生成后自动追加一次「删句式自修」降人工负担。
3. 工作流 approve 节点暂只支持批准；「退回修改」需到工作台/审核中心操作后重跑导出线（画布内循环 = V2 条件分支）。
4. Connector Endpoint 仍无 PATCH（改配置需删除重建）、无嵌套字段映射、无 token 自动续期（DreamO JWT 数小时过期需手动换）——沿用上轮报告缺口 #13/#14/#18。
5. 业务指标埋点（生成成功率/blocker 率等到 /metrics）仍缺（上轮缺口 #5）。

## 六、最终状态

- 全量 124 个 pytest 通过；ruff 干净；前端构建通过
- 生产环境：API 同步默认模式（:8000）+ worker/beat 常驻（定时拉取持续工作）+ MiniMax 路由生效
- 本轮新增改动：confirm_facts 节点、异步轮询、WAL、think 剥离、latest-revision、scheduler 兜底、dispatch 前 commit、荐题重试——全部含测试，随工作区一并待提交
- 冒烟产物：Source 14-31、FactPack 8-11、Topic 5、Assets 10-15、两篇公众号草稿箱草稿（可后台删除）
