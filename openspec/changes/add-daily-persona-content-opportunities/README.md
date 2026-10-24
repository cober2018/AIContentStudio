# 角色每日机会与商品直达创作方案

2026-10-15补充：独立确认的停机补偿`add-discovery-offline-catchup`已正式接入，schema head为catchup000001，10路径当前hash记录在implementation_manifest.offline_catchup_extension。恢复先补采结案，再冻结未开始的当天选题证据；缺口持续可见。原9.5/9.6自然日批及归档仍独立开放，本补偿验收不代替次日经营角色自然日批。

## PRD / 需求背景

用户希望创建角色后，系统自行理解定位、搜索领域信息源及博主、保存来源库、持续跟踪热点并每天生成相关选题，无需逐次触发。本 change 复用 Easel 的画像驱动选题和 AIHOT 的采集、事件聚合方法，接入 AIContentStudio 既有内容机会与项目链。另支持指定商品跳过选题直接开始生成，两个入口共用后续创作流程。

## 当前阶段

`PUBLICATION_ROLE_FIXED_WAITING_NEW_NATURAL_RUN / 43 of 45`：用户已确认完整规范，2026-10-15进入apply。隔离工作区 `/Users/mshengran/.codex/worktrees/daily-persona-product-creation/AIContentStudio` 基于main@636d60e及原文件快照开发，已白名单接入原项目。实施和验证状态以progress.md为准。

## 目录结构

- `proposal.md`：目标与范围。
- `design.md`：借鉴方式、完整流程、数据与调度设计。
- `specs/`：可验收的行为规范。
- `tasks.md`：实施清单。
- `task_plan.md`、`progress.md`、`findings.md`、`review.md`：持续计划、实际证据、决策与复核。
- `source_inventory.json`、`source_inventory.md`：本轮搜集的首批来源储备与访问检查，供实施时导入。
- `reference_research.md`：两个参考项目的版本、文件证据及采用范围。

## 代码位置与版本

正式代码 `/Users/mshengran/Project/AIContentStudio`（35路径已集成、未提交），原实施worktree `/Users/mshengran/.codex/worktrees/daily-persona-product-creation/AIContentStudio`，基线 `main@636d60e`。已有相邻未提交改动保持原样。相关代码：`apps/api/app/services/opportunities.py`、`home_projection.py`、`content_identity.py`、`tasks/`、`apps/web/src/product/OpportunityPages.tsx`；商品路径复用 `services/project_brief.py`、`routers/content_projects.py`、`services/generation/orchestrator.py`、`services/stage_resolver.py` 和 `apps/web/src/product/PersistentProjectPage.tsx`。

## 已完成

42项清单沿用，角色研究/来源采集/机会/双入口/共用生产已在隔离worktree接入。91张旧表加法迁移保全；相关既有检查160通过、1跳过；Web/bundle与strict通过。MiniMax后台MCP和两角色真实商品首阶段成功，两个角色来源研究与机会已有真实产物。新角色自然首批与修复后真实输出已通过独立核验，正式日批仍开放，详见progress.md、review.md。

## 待完成 / TODO

正式启用9.3已完成；正式自然日批9.5与最终归档9.6等待修复后2026-10-19或之后08:00自然调度。已安排当前聊天每日08:20自动复核，满足规范后自动同步六份主规范并归档，用户已明确授权，无需重复确认。unknown不盲重发。默认时间、数量与预算已随用户确认的设计执行。

## 关键设计决策

复用现有 Python API、Celery、PersonaRevision、ContentOpportunity；新增来源发现与研究任务，不部署第二套内容站。来源发现及选题自动化，选题转项目仍沿用人工判断。来源库支持所有有效角色，首批为科技与生活两个角色。商品入口不依赖内容机会或联网成功；沿用普通项目、带商品上下文的版本化任务书和共享Recipe，满足资料要求后启动首阶段生成。

## 依赖与启动方式

新增服务沿用既有API/Web/Celery，不新增产品依赖。后台使用现有MiniMax官方MCP离线缓存和固定配置引用，Tavily可选；API/worker均需能读取本机配置与uvx缓存。生产技术模式仅支持环境凭据。正式入口为http://127.0.0.1:5173/opportunities，API8000；保持原launchd与Redis DB2，Worker修正为solo池单任务并发。原隔离5187/8017仅历史验收，正式库未混入隔离数据。参考项目未安装或运行。规范检查：`openspec validate add-daily-persona-content-opportunities --strict`。

## 正式启用与自然验收

用户2026-10-15明确授权后，已完成一致性备份、迁移与经营角色2/3启用（测试角色1暂停）。91旧表858行、75素材保全；18引用校验。备份为私有 `backups/daily-discovery-enable-20261015-3pwbanpq/`；当前准确代码SHA256见implementation_manifest.json。今天首批/当日补跑与明日自然日批分开记录，不提前归档。自动跟进ID automation-3。

正式首批与当天补跑已实际完成：两角色各5条，正式API与5173页面回读通过；本轮正式无unknown。下一步只剩明日自然日批及归档，详细回执见production_activation.json。

## 今日选题质量审查补充（2026-10-15）

技术已正式接通40/42；10条选题质量没有全部通过。只读逐条审查已写入review.md：建议优先5条，其余合并/备选/补证，未修改正式记录。已发现空正文放行、转载时间误作事件新鲜度、旧文高时效与同质化问题。自然日批可以继续验收，但这些质量缺陷未关闭前不得自动归档，不能把技术回读当内容质量通过。

## 当前结论：质量修复完成，等待自然日批

2026-10-15已按确认结果修复并接入正式工作台，43/45。今日5条当前建议、3条备选、1条合并、1条缺正文暂缓；10条原评估均保留，新增v2。正文/日期/独立证据评分、同类合并、来源主体上限及每角色0至5条已验证；已有81检查、Web构建、独立审阅与两个角色隔离真实模型链完成。完整证据见progress/review；自然日批与归档仍待明日08:20跟进，不将历史40/42回执误作当前总数。目录、依赖和启动方式不变，代码位置main@636d60e脏工作区的五路径与既有35路径，manifest记录准确hash。

## 2026-10-16 自然日批复核与日期标签修复（43/45，未归档）

- 正式业务日2026-10-16：经营角色2/3的Run8/9均为`origin=celery_beat`、`execution_origin=celery_worker`，08:00:39自然创建，08:04:14/08:06:02结案，各5次模型调用、各1条选题（#11/#12），没有人工触发或补足配额。原始任务ID、冻结正文、精确引用、事件版本及双次同输入独立评分见私有`backups/daily-natural-20261016-3x15zlfq/natural-acceptance.json`。科技证据88/90、综合89.15/89.5；生活证据88/88、综合85.8/82.65。证据62/64的候选已被排除。
- 正文与角色定位可支撑当前两条，但科技#11把`Published October 15, 2026`同时当原文日期和事件日期；发布时间标签不能证明事件发生时间。故本轮自然质量验收未通过，9.5/9.6继续开放，不能凭成功调度或评分关闭清单。
- 最小修复仅`apps/api/app/services/daily_opportunities.py:_ground_candidate`：相同的发表日期证明、仅有日期、纯发布/更新时间标签不能作事件日期；无事件证据时按已验证原文日期降级为近期报道，过旧则拒绝。完整的实质事件句包含updated/published仍可保留。独立复核先发现宽泛词匹配误删，收窄为完整标签匹配后APPROVE。最终SHA256 `d5b84f991ccdd2310b308f2cfc1013207126758f0f89d506b001bc980cc4a1ac`，正式Git HEAD `49e4fdc11b433d3c32326f78eea7151dd5f8c0a6`，仍为未提交工作区。
- 先在线备份正式SQLite与原代码至`backups/daily-natural-20261016-3x15zlfq/`。#11追加评估v2（ID23）及校正信号15；原评估21和原信号13保留，原信号脱离当前证据但内容未覆盖。原文与页面更新日期为10/15，事件未知；保留原模型评分并标注未重新评分。Run8/9输入、输出、任务ID、所有原运行回执不改，昨日#1–10及今天#12逐行等于修复前备份。
- 冻结真实Run8重放及四个日期反例全部通过，零Provider调用；Ruff通过，既有41项回归通过（1条既有Starlette警告）。只读沙箱的素材可写探针曾使两项健康测试503，获授权正常权限复核后41/41通过；没有修改健康或测试代码。
- 正式Worker空闲后仅重启Worker以加载修复。正式API ready200，机会#11/#12回读200；5173正常页显示台北10/16各1条，均为近期报道，#11评估v2。来源coverage仍partial、catchup_coverage_incomplete及正文读取失败真实保留，不算内容质量通过、不加最低条数。回执与截图位于同一私有备份。
- 下一步：2026-10-17或之后08:00由修复后Worker真实自然日批，再按全部既定标准验收。automation-3继续跟进；本轮不手动重跑，不重发unknown，不同步六份canonical specs或归档，不push/公开发布。目录、依赖、迁移与原启动方式不变。

## 2026-10-16 用户确认的聚合入口接入

相邻且明确授权的add-aihot-persona-source-integration已在备份/两站真实同步与原文验证后切换角色2/3为来源54/55；旧源/订阅及原12条机会历史保全，原质量筛选继续。共用模块最新hash见implementation_manifest.aggregate_source_extension，须在此前所有overlay后合并。父9.5/9.6仍开放；automation-3等待10/17或之后08:00新入口自然日批，不能用本次同步取代。接入change另有同一成果与8/10清单，最终两份均符合规范后再分别同步归档。

## 2026-10-17 新入口自然日批：正文边界修复，待下一次自然验收

状态：PUBLICATION_ROLE_FIXED_WAITING_NEW_NATURAL_RUN。父change仍43/45（9.5/9.6开放），聚合接入仍8/10（4.2/4.3开放）。今日不归档，不提前同步canonical通过状态。

- 正式HEAD8539806eb3a1bebf5bf71ee08df3a286cdf9e00a；本需求代码仍为原工作区未提交文件。共享url_fetch.py新增model_vision限额属于已授权相邻需求，原manifest去掉该单行即匹配；保留并记录最新hash，不误判漂移。
- 真实2026-10-17 08:00 Beat→Worker日批Run12/13分别对应角色2/3，科技2条（13/14）、生活1条（15），仅源54/55；独立双评分输入hash一致、request/llm_run不同，五阶段各完整。无凑数、无主体超过2条、无角色超过5条；均recent_report，原文10月16日，转载/事件日期未知，不把发布时间冒充事件时间。
- 当前补采回执918/919已covered且早于证据冻结；此前HTTP530缺口729/730继续显示partial、缺失数量未知。科技1篇正文读取失败被排除，生活无正文失败；不把读取失败或unknown记作质量通过。相似选题/原事件版本追溯已核对。
- 质量失败：机会14摘要称VERID用于3D状态追踪/测试，但冻结正文仅含论文链接名；该事实来自上游摘要。双次高分不能代替正文支撑。机会13/15逐项正文核对通过，未作改动。
- 最小修复daily_opportunities.py：模型引用投影剔除upstream，保留字面excerpt及来源追溯；候选与独立评分提示逐事实核对冻结正文，链接名/标题/上游摘要/未读正文不能作证据，实质缺证设grounded=false走既有淘汰门槛。未增加依赖、迁移、测试、模型调用、重试或日批。
- 修改前在线备份backups/daily-natural-20261017-o3nb90tg/before.db与原代码。机会14仅移除不获正文支撑的细节，追加评估27/v2和信号19；原评估25、信号17、Run12/13、原双评分与输入输出保留，旧信号detach而非删除。审计明确本次未重评分，不把人工修订当自然质量通过。
- 验证：独立代码复核APPROVE；真实冻结引用投影回放无upstream且不改原ref；Ruff通过。41项既有检查40通过1失败，停用Profile回退断言在修复前代码同样复现（providers.py模型选择行为），本轮不改相邻需求，不能写全绿。历史机会1–12、13/15及其评估/信号逐行等于备份，原评估25和自然Run12/13不变。
- 正式Worker确认空闲后优雅重载并pong，API ready200、GET机会14返回新摘要v2。正常页面只读回读可见当天2/1条、近期报道、原文/转载/事件分列、来源partial和机会14修订v2；未手动生成。证据natural-acceptance.json、natural-runs.json、repair-receipt.json与api14-readback.json位于同一备份。
- 下一步：automation-3保持每日08:20，已更新同一提示，验收2026-10-18或之后修复后08:00真实自然日批。全部规范满足后才关闭两change剩余任务、分别同步规范并归档。未push或公开发布。

本轮实际使用Superpowers、OpenSpec apply、systematic-debugging、requesting-code-review；archive skill仅用于核对归档条件，未执行归档。

## 2026-10-18 自然日批复核：转载日期语义修复，待再次自然验收

自然日批科技0/生活3，有真实零结果依据；发现天气转载页日期误标原文，备份后接入最小提示修复，追加#18日期v2及#17正文措辞v2，保留原运行/评分/历史。40项既有检查通过、1项原有失败；API/页面和Worker核验通过。仍43/45与8/10，等待2026-10-19或之后自然日批再判断归档。详见本目录review.md同日证据与最新manifest。
