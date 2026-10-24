# Progress

## 2026-10-19 自然链路验收已安排
- 用户要求等待今日08:00自然运行后验收；已将Radar完整链路检查并入既有每日08:20心跳任务automation-3，保持原时段，无重复采集调度。
- 验收覆盖当天生成回执/报告hash→source56导入及item版本→科技Run冻结/取证/双评分/退出原因→API/页面，生活来源隔离同时核对。批次运行中只读等待；不手动补跑或重派unknown。
- 自动任务已确认ACTIVE；完成或明确阻断才通知，状态不变静默。安排成功不等于自然验收通过，5.2保持开放。

## 2026-10-19 日报自动化启用（15/17）
- 用户明确授权每日自动生产并进入科技评估；在原change追加3项，不改08:00日批/Beat条目/生活角色/预算，无迁移。
- 新增radar_producer.py：固定安装目录/commit/免费参数，Python3.12、300秒超时；源码变化阻断；剥离Provider凭据环境，stdout/stderr不入应用日志。使用本机互斥及SystemSetting每日回执，失败/超时/中断同日不重派。日期化报告验证后原子替换，保留历史文件。
- catchup来源lease对Radar为8分钟；现有日批前置receipt保证生成→导入→冻结证据顺序。auto_daily支持正式API/前端开关与只读生成状态；普通手动文件模式保留。
- 新鲜81项既有检查通过（1既有warning）；隔离smoke覆盖08:00前无调用、同日单次、固定免费参数与安全env、超时unknown、崩溃不重放。代码复核发现普通JSON原地修改不持久化，已复制字典修复；使用expire_on_commit=False+重新加载验证成功/超时回执持久化，再复核通过。
- Web TypeScript/Vite/FE-P1通过，机会页287.76kB initial/93.97kB gzip；Ruff、diff-check通过；全量OpenSpec本轮56/56（工作区总数，以本轮实际输出为准）。未新增测试文件。
- 正式DB配置前在线备份 `backups/pre-radar-auto-20261019.db`，仅配置恢复快照，不冒充素材完整灾备。确认Worker空闲后加载API/Worker，通过正式PUT启用Persona2/source56的auto_daily；原15项保留。浏览器实见自动日报勾选、等待当天选题时段，日批仍08:00。
- 没有提前触发选题模型/真实生成、没有把隔离smoke记作自然批通过。下一自然计划2026-10-19 08:00台北时间，5.2仍开放；5.4归档未执行。无commit/push。

## 2026-10-19 Radar安装与真实导入
- 用户明确授权无本地日报时安装/运行。独立clone `/Users/mshengran/Project/new-term-radar`，版本0.4.0 / 2568cdcba5691cd21d03f2c0a86f4461dbcb7234，未改上游业务代码；无第三方依赖，隔离环境使用明确的 `.venv/bin/python3.12`（3.12.13）。首次命令实际由系统Python3.9执行成功；已补装满足上游要求的3.12运行入口，未为换解释器重复请求网络。
- 免费daily真实读取GitHub200个新仓库、HF100模型+100Spaces，生成15条GitHub线索；HF首次仅建快照。禁用x/newsites/revenue/asks/gsc/review/judge/usecases/tutorials/sitemaps，没有模型/付费API调用。
- 正式配置前SQLite在线备份 `backups/pre-radar-activation-20261019.db`（仅DB配置快照，不冒充数据库+素材完整灾备）。通过正式PUT配置Persona2、source56、report.json及exact producer版本。
- 自然既有Beat→Worker于00:52:36导入15/15、未解析0、预算未分析0；catchup receipt2078 partial/radar_partial，report hash `bc63d56d7e7d0deee14efcc965a1a692fe2feea4fe27bcac7e33187a536233b5`。partial真实原因是初次HF/GitHub基线及无区间水位；15项原始日期未知保持null。
- DB/API确认仅Persona2订阅56，既有2→54及3→55保持。没有手动触发选题模型或覆盖机会历史，没有改08:00日批、预算或凭据。
- 自动导入已通；上游日报生成目前仍为显式CLI，未设置第二个定时器，不能宣称每日新日报自动生产。自然选题结果仍待，5.2保持未勾；5.4归档未执行。
- 本轮新鲜检查：Python3.12配置/真实报告读取PASS；SQLite备份immutable只读quick_check=ok；单change strict和全量55/55通过，git diff --check通过。无业务代码变化，未重跑此前81项及前端构建。实际使用using-superpowers、openspec-apply-change、executing-plans，沿用既有计划。

## 2026-10-19 规格落盘
- 已建立单一change，proposal/design/4份delta/tasks及交接文件齐备。
- 业务任务0/14，未修改业务代码、正式数据库、信源配置或调度。
- 未安装Radar、未调用模型、未提交/推送、未同步canonical或归档。
- 实际校验：单change strict通过；全量strict 55 passed / 0 failed；git diff --check通过；OpenSpec 4/4 artifacts complete。规格完成不等于business apply获授权。

## 2026-10-19 已授权实施
- 已复核规范和调用链，启动三项一批apply；保留原dirty工作区。
- 科技策略/推荐期限、Run诊断及API有效建议过滤已接线，正在进行Radar适配与前端联动。
- Radar上游0.4.0 / commit 2568cdcba5691cd21d03f2c0a86f4461dbcb7234已只读核实；无本机可消费日报路径证据。不安装/执行上游，不新增凭据或真实模型调用。
- 当前2/14为准备项完成，其余待统一验证后更新；未修改正式数据库/调度，无提交推送。

## 2026-10-19 实施与验证回执
- 12/14：三项功能实现/代码复核完成；5.2真实Radar输出与自然日批、5.4依赖协调后归档未关闭。
- 业务变更：新增opportunity_policy.py/radar_discovery.py；daily_opportunities、discovery_aggregation/runtime/catchup、discovery/opportunities路由、home_projection及OpportunityPages/DiscoveryPanel接线。复用已有模型与JSON，无迁移/新依赖。
- 科技策略通过稳定blueprint绑定；48h最新动态、30d近期进展、无统一年龄线的常青，双评分/证据/预算不放宽。新建议期限48h/7d/30d，旧行不延长，处理中旧检查点不重解释。
- Radar使用已核实daily JSON格式，明确路径+版本确认后配置；至多300项/次、技术角色专用、正文仍须核验、相同report重读幂等。报告本身不提供完整时间水位或撤回协议：缺项不撤回，区间覆盖保持partial。
- 新鲜既有回归：`test_fe_f5a_opportunities.py` + `test_persona_creative_identity.py`，81 passed / 1既有Starlette弃用warning（7.85s）。没有新增持久测试文件。
- 隔离smoke：10d进展/180d常青/未知日期/角色隔离；有效期与跨日API、GET不建Run；Radar导入幂等、失败后可恢复且不使用失败源旧证据；合并发现路径撤选与unknown区间保留，均通过。纯解析/内存库证明合同，不是实际Radar源验收。
- 最终Web TypeScript/Vite及FE-P1通过：机会页286.23kB initial /93.55kB gzip；/projects297.34/100.91；assets262.47/84.42、settings246.28/80.36、learning253.81/82.56。Ruff通过。
- 本机只读页面：科技4条既有有效建议（#14/#13/#3/#1）跨日期可见；生活仍当天，未出现Radar配置；科技Radar入口显示未配置。今日无Run与10/18历史partial分开展示，不将历史缺诊断补0。
- 检查Worker active_count=0后加载现有服务。发现8000被本项目旧孤立uvicorn PID33354占用、launchd反复bind失败；已对确切旧进程正常TERM，恢复既有launchd接管，无新部署方式。API确认科技technology.v1/生活discovery.v2、Radar未配置。
- 未手动触发采集/模型、未导入正式Radar数据、未改正式机会历史/来源配置/凭据/调度；既有自动采集继续按原计划。未提交、推送、归档。
- 收尾新鲜全量OpenSpec strict：55 passed / 0 failed；git diff --check通过；本change及新增未跟踪服务/页面尾随空白检查无匹配。最终API/Worker均running，正式只读API返回科技有效建议#14/#13/#3/#1。

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
