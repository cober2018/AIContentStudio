# SPEC 自查

2026-10-19：三项范围均有对应delta和tasks。新策略只绑定科技；48小时观测热度不改变；保留正文/引用/日期分离/双评分/去重/预算。Radar仓库与真实可消费feed明确区分，未配置不伪装成功。统计缺失不填0，页面读取无执行副作用。

canonical content-opportunities仅新增requirement，不覆盖旧requirements/scenarios；两个active依赖不改写，后续同步须按design第5节统一科技例外。本轮是执行者自查，不是独立审阅或业务验收。

实际门禁：单change strict通过、全量55/55通过、git diff --check通过。状态：READY_FOR_SPEC_REVIEW；business apply未授权。

## 2026-10-19 实施前复核
用户已授权本次复核后apply。现有实现使用单AIHOT源映射，需扩展为科技允许源集合而不改变生活来源。科技策略通过Starter blueprint稳定标识绑定，不以角色显示名称判断；已经开始模型检查点的旧Run仍按旧策略恢复。无产品设计阻断，进入实施。上述旧门禁不充当本轮代码验收。

## 实施独立复核与修复
- 独立只读审阅确认：双评分中途失败时不能把已进入评分的候选记为0。已将进入评分数持久化到第一次评分调用前；未完成的评分/淘汰结论不补0。
- 多源合并的`discovery_paths`必须参与AIHOT撤选匹配，已修复，旧主ID/timeline语义保留。
- Radar只证明指定日报读完，不证明整个停机区间覆盖；catchup始终保留区间partial与unknown gap，页面给出明确说明。
- 最后窄复核：上述三项均关闭，限定实现范围无剩余代码阻断。审阅不冒充真实Radar/自然日批验收。
- 执行者隔离smoke已验证合并路径撤选转watching、空日报读取后仍partial且保留unconfirmed_interval。初次临时夹具漏填User.name/Signal.label，补齐夹具后通过，无对应业务缺陷或正式数据修改。
# 2026-10-19 自动日报限定代码复核

- 范围：radar_producer、radar_discovery、catchup lease、Radar API配置、DiscoveryPanel自动开关；不扩大旧功能审查。
- 发现：普通SQLAlchemy JSON在expire_on_commit=False下原地修改state，最终回执不会写库。
- 修复：首次commit后复制state，后续修改独立对象再赋回。
- 复核：独立审阅确认闭合；执行方隔离SQLite以expire_on_commit=False、expire_all重新读取success和timeout终态通过，同日调用次数保持1。无剩余限定范围阻断。
- 正式API与页面已确认auto_daily=true；真实新日报/自然选题须等08:00，不以mock和配置回读冒充该项验收。


## 2026-10-19 08:20 自然批只读验收：链路接通，质量未通过

- 正式SQLite只读及API/UI回读：Run20科技technology.v1、Run21生活discovery.v2，业务日2026-10-19；均origin=celery_beat/execution_origin=celery_worker，task分别f034575e-2940-47b1-9b40-25035fc5dfc9、a3b4022f-d652-42ec-a8be-ee408158bb34。08:04:00/08:04:45台北时间完成，各1条机会19/20；均partial而非全网完整。
- Radar当日generation回执succeeded/attempts=1，commit2568cdcba5691cd21d03f2c0a86f4461dbcb7234；08:01:33.679开始、08:01:49.801结束。日期化report.json按生产digest规范（排序紧凑JSON）重算hash=79608f25ed5aa8dc930001e30b17fa9955cf569d17b309a035b512ffb635cc3b，与回执/导入/冻结一致。文件原始字节SHA256=4c5d9fae351f30ed6b6c050ae3a642e5c9a0990dcc6fd614de57aa962e2acfc6，两者算法不同，不是漂移。
- 当日报告2条lead：1可解析URL、1未解析；新增item769 harness2，checksum ee72d2a3460f63a4bf2bc03557245f78404808098049433d09aea9a5b1f101c6。08:01:49.806导入，catchup2257/batch483于08:01:49.812完成，先于Run20 collection_snapshot 08:02:31.293及正文冻结。覆盖仍radar_partial/无区间水位，54历史catchup_unsafe_url缺口保留。
- Run20冻结4个唯一item：746/722来自54、769/764来自56；769正文hash111868498e58c81c7031a26f4683c4ee1b62cafe1569c6c9a7b8e9bef9bdaa86，764正文hash7c3269abf1f2a2f8d9d27bed009cb3393cb0531523566d1a1463801008316919。Radar确实进入事件聚类LLM126与候选127；当天新增769未入选，旧报告item764经当日读取和评估生成#19，不冒称今日新发现。764原报告hash bc63d56d7e7d0deee14efcc965a1a692fe2feea4fe27bcac7e33187a536233b5，item checksum97d0d3e67b57f4fa0980379bf9b0f0cfb318951092856599234a868c373e8c5d。
- 科技3候选中769/722被supporting_evidence_missing淘汰，764通过独立评分128/129，证据85/85，最终confidence0.88425；常青、三类日期均null，有效期30天。生活3候选中2条日期门槛淘汰，1条独立评分133/134证据92/92、confidence0.8465。生活冻结来源仅55；748/766同事件合并为48。每角色1条，无同主体超2/日超5，无跨源同原文重复入选；总分与原始评分保留。科技未分析87、生活49为预算诊断，不等于质量通过；body_reads_succeeded=5而唯一冻结4项，不能把读取次数当不同文章数。
- 缺陷一：_quoted使用原始字符串包含；769和722的候选引文与冻结正文仅空白/换行不同，原始匹配false，折叠空白后匹配true。真实正文存在却被判缺证据；本次只记录，不放宽或重跑。
- 缺陷二：生活#20/item766冻结正文署名“央视财经客户端”，承载页为澎湃，页面日期仍被记作original_published_at而republished_at为空；展示原文2026-10-18T00:00:00+00:00，无法证明原始发布时刻。双评分未拦截。当天自然日期质量再次失败，父change与AIHOT不得归档。
- 正式GET /api/v1/content-opportunities/19及/20均200。5173/opportunities页面实际显示2026-10-19科技#19深度常青、生活#20近期报道；与旧机会分开。没有手动采集、模型调用、重发unknown、重跑、改业务数据/代码/配置/cron、测试、提交或发布。本次仅回写文档；5.2因筛选缺陷保留未勾，5.4未执行。后续需要限定修复和新的自然验收，不重复报告同一Radar接通结果。

## 2026-10-20 自然批只读复核：零结果不能算质量通过
- Run24科技/Run25生活业务日2026-10-20，真实celery_beat→celery_worker；task分别3d527804-02e3-48db-bbae-ccd46f1c4ebb、2aeaff67-ce14-4360-80f7-e5c289bc6bd6。08:05:36/08:04:02台北时间结束，均partial/no_grounded_candidates/0条，没有进入双评分。
- 新发现日期校验缺陷：item799正文原样“发布时间：2026-10-20 07:40:53”，候选2026-10-20T07:40:53+08:00，引用完全匹配；source_date先转UTC成为10月19日23:40，再由_date_proof用UTC的19日匹配本地20日引文，返回None，最终recent_date_unverified_or_outside_window淘汰。此为时区跨日误拒，不能作为合格零结果。本次未修复或重跑。
- 科技791/802均supporting_evidence_missing：791正文超链接断行在句点前引入空白，802中文段落换行与候选合并排版不一致；普通空白折叠仍不完全相等。不能沿用昨天“只折叠空白即通过”的复核结论，也未自动放行。科技读取失败1、预算未分析97；生活预算未分析68，均非质量通过。
- 当日Radar回执succeeded/attempts1，08:04:05.383→08:04:43.596，固定commit2568cdcba5691cd21d03f2c0a86f4461dbcb7234。6线索/4解析/2未解析，日期化报告规范hash重算7a673fc010555128022861db69cdc29e841d367df932e330c04950973bbf3e7b一致。catchup2953于08:04:43.609完成，先于Run24快照08:04:43.694；来源54/56，冻结802/803确有Radar参与LLM275/276；生活仅55。Radar无完整区间水位，partial保留。接通结果不重复作成功通知。
- 正式API两个角色business_date=2026-10-20均200/items=[]；5173机会页显示2026-10-20空筛选及“空不代表已运行”提示，与历史分开。本次仅业务只读和成果追加，无采集/模型触发、重发unknown、配置/代码/数据改动或新增测试。5.2、父9.5/9.6、AIHOT4.2/4.3不关闭，不同步归档。需修复现存日期/引文问题再自然验收。

## 2026-10-21 只读跟进：验收状态未变
Run28/29真实celery_beat→celery_worker，业务日2026-10-21；task039f0a6a-d2b2-469d-abfa-4720a34a97dc / 12261281-d4fb-47bd-a6ea-d41dccfd322f。科技1条#21、生活0条，均partial；正式日期过滤API分别200/[21]与200/[]。科技候选832的长引文与冻结正文完全相符，双评分LLM279/280证据95/90，原始候选hot且event=null，最终分类需以后续完整验收为准；本次不宣称整体通过。生活836将转载时间单独列出，原文/事件null，recent_date_unverified_or_outside_window退出；现有UTC跨日匹配缺陷仍未修复，不据此关闭验收。没有双评分的生活零结果不算双评分质量通过。
Radar当日一次成功，11线索7解析4未解析，规范hash d1e72eab5f45e9275fb8309454cd29c507bd16cfd8cf1cb405bc984079670429重算一致。catchup3217于00:02:14.473 UTC完成，科技快照00:02:42.787，冻结843/844来自56；科技54+56、生活55。未选Radar新推荐；科技读失败2/预算未分析117，生活预算未分析82，partial不改。既有缺陷和开放任务无实质解决，不重复通知Radar结果。业务全程只读，无重跑/模型/修改配置或数据/归档；本次未进行新的页面UI核验，不把API代替页面验收。后续仍需既有缺陷修复后完整自然验收。
