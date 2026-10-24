# 提案复核

已核对两站映射、只读匿名接口、持久游标、正文不足不入选、日期和主体追溯、撤选与历史保全、可逆切换以及既有商品共享流程。

OpenSpec strict通过。源码审计、真实快照/增量/正文、正式自然日批尚未执行，不能视为已接通。无新增测试或业务代码。

## 2026-10-16 正式接通与切换（8/10，待自然日批）

- 使用同一change apply，正式工作区HEAD 421ef675d8935dc3823093645809bd102f3246b4；本轮10路径准确SHA256见implementation_manifest.json。旧脏工作区与相邻需求保留，未提交/push/公开发布，无新增依赖/迁移或持久测试。
- 开发前备份before.db、九个原路径与API配置0600；切换前再次在线备份before-switch.db，均在私有`backups/aihot-integration-20261016-8d749px6/`。
- 初期站点一度530/Cloudflare Tunnel1033，稍后恢复200。正式HTTP读取器遇本机198.18/15 fakeDNS，添加仅聚合路径的可信公网解析兼容：固定dns.google/8.8.8.8+TLS、只接受公网非multicast、ContextVar单主机作用域、原允许主机/逐跳检查/TCP固定地址/HTTPS验证/大小时限仍保留；原来源抓取默认路径不变。未开启ssrf_allow_private。
- 两站隔离与正式均真实同步完成：科技71条精选、生活22条精选。snapshot结束后继续changes追平才covered；原子落账后保存cursor、重建快照、编辑/撤选/恢复/ETag/304/Retry-After均有代码与临时验证。采集覆盖只限上游精选，不承诺全网或所有历史完整。
- 正文验证：科技取得NVIDIA真实正文9767字与另一篇10000字；生活取得中新网原文622字。中新网无article/main，按实际HTML的明确正文起止注释提取，仅聚合调用启用，并保留发布时间标签。1篇科技缺正文区域、生活3次正文读取超时/区域缺失如实留档，不当质量通过。科技二次聚合须继续追溯原始出处，摘要不能作正文；重定向后actor使用最终校验URL并保留跳转追溯，同发布者子域合并，日期/双评分/每角色0至5条沿用原筛选。
- 正式源54→科技角色2、55→生活角色3。两站正式同步+正文均成功后，才设置`system_settings.discovery.aggregate.1.personas={"2":54,"3":55}`。聚合模式停止这两个角色原逐站定时采集和自动搜源；原来源/订阅enabled及manually_paused、来源名称类型和处理权限原值保留，其他角色1保持direct。原12条机会、评估和信号逐行等于切换前备份。原当天Run不重跑，零模型/供应商unknown重发。
- 正式API与Worker在空闲时优雅重载；原Beat无需重启。两源由原Beat/Worker采集后均covered（UTC08:42:26/08:42:28）；正式API ready200、两源phase=changes、has_more=false、角色collection_mode=aggregate。API和页面可见两源角色关联、最近同步与补采状态；旧来源明确显示聚合模式暂停逐站采集且原配置保留。回执api-readback-final.json与formal-ui.png保存同一备份。
- 已有41项回归通过，1条既有Starlette警告；Web TypeScript/Vite/bundle、Ruff、diff与OpenSpec strict通过。临时验证九项涵盖快照→首次增量、版本回退/撤选重选、原子回滚、冻结后撤选阻断、Retry-After等；另校验私网/fakeIP/multicast拒绝及scope恢复、主体归并与隔离回滚。独立代码复核发现并关闭快照水位、撤选竞态、迟到回执、限流及重定向主体问题，最终APPROVE。
- 可逆回滚：恢复`discovery.aggregate.1`原状态（此前不存在，等价personas空映射）即可解除系统模式限制；不需要反向覆盖原来源或订阅开关。该路径已在隔离库验证，正式保持聚合模式。
- 两站热点榜附加读取未通过HTTP检查，错误回执单列；当前每日选题采用已经验证的精选快照/增量与原文，不把未读到的上游热榜计为证据。
- 剩余4.2完整自然日批与4.3最终规范同步/归档，须等2026-10-17或之后08:00修复后新入口真实自然日批。原automation-3已更新，仍每日08:20跟进本change和父change，零新增自动化。未用手动同步或启用标志替代自然选题验收，不提前归档。

## 2026-10-17 新入口自然日批：正文边界修复，待下一次自然验收

状态：BODY_SCOPE_FIXED_WAITING_NEW_NATURAL_RUN。父change仍43/45（9.5/9.6开放），聚合接入仍8/10（4.2/4.3开放）。今日不归档，不提前同步canonical通过状态。

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

状态PUBLICATION_ROLE_FIXED_WAITING_NEW_NATURAL_RUN；父change43/45、聚合接入8/10，原自然验收/归档项全部保持开放。

### 真实自然日批证据

- 当前HEAD8539806eb3a1bebf5bf71ee08df3a286cdf9e00a；复核前daily_opportunities.py匹配10月17日最终manifest（f583eac79973204f77a2eb068116201690f9227d68bb3d4019fabee9ea545151），无该路径漂移。新单文件SHA6435df371efd93d016b3951f14409a505b14a9657658f6e5a32d52c2d1f6553f；相邻商品工作区修改保持原样。
- 科技Run16与生活Run17，业务日2026-10-18，UTC00:00:33由Beat创建，execution_origin=celery_worker；task分别db2e88c5-da0e-4074-9812-92cc26089537、65c52de5-2aab-4d51-92b3-63e0a195fbd9，分别2/5次原模型请求。Run16于00:03:26结案、Run17于00:04:21结案，无手动触发或重发unknown。
- 科技0条是有真实处理依据的零结果：事件34/40/35三个候选在原evaluation_time下重放_ground_candidate均因原文日期超48小时、无可证近期事件日期且候选未标常青而退出（10月16日/15日/16日）。没有进入最终双评分，不虚构评分通过、不因缺正文直接宣称质量通过；另item655/723正文读取错误如实保留。事件35旧版本沿用，VERID只在论文链接名出现，今日候选已明确其具体技术方案未读到，没有再次采纳上游摘要功能描述。
- 生活3条：#16 Roadster/企业负责人评论（澎湃评论）；#17网购野生发菜（中新网）；#18冷空气/预警（中新网与澎湃转载央视两份正文合并，同事件41/version1）。内容与生活新变化/日常观察定位相关，无虚构个人体验，均recent_report，事件日期未知；不标全网热点或新发生。三条问题不同，同主来源最多2条、每日3<=5，不凑数。天气两稿并为1条，保留两个item和版本；angle_comparison无重复。原文/转载/事件分列。
- 生活两评分A/B相同input_hash、独立request_id与llm_run_id123/124。#16证据88/88、总分89.00/86.95；#17证据90/90、总分87.60/87.15；#18证据92/92、总分84.35/82.65。冻结正文非空、服务digest校验和一致、支撑引用及日期引用逐字位于正文。分数合格不能覆盖以下语义错误。
- 补采1666/1667均covered，分别在00:01:35/00:01:38结束，早于科技00:02:33/生活00:03:26冻结。角色仍只用54/55。此前1576/1577在10月17日UTC11:15–11:20因catchup_unsafe_url失败的缺口保留，missing_count未知；整体partial真实可见，不推断全网完整、不额外修采集网络。

### 失败、修复与定向修订

1. #18第二来源item737的冻结正文明确署名“央视新闻”，链接是澎湃转载页；候选把该页面2026-10-17日期归入original_published_at。代码只核对日期逐字存在，没有提示评分核对日期归属；两个评分也因此放行。今日自然质量验收失败，不能以手工修订冒充自然通过。
2. 单文件最小修复：候选提示明确不同署名/来源的转载页面日期只能证明republished_at，原文日期须原始出处的明确日期证明，否则null；双次评分都检查timeline日期语义，转载误标原文则grounded=false。仍由既有证据淘汰链执行，不增加模型调用、日期推断器、依赖、迁移或持久测试。独立只读代码复核APPROVE，并明确提示修复不等于自然验收通过。
3. 先在线备份至backups/daily-natural-20261018-2cp4tmro/before.db及原代码。#18追加评估31/v2、信号24：item737原文未知、转载10月17日、事件未知；原信号23仅detach，原评估30保留。原双评分保留并标明未重新评分。#17正文只说“经鉴定”，删去多推断的“司法”限定，追加评估32/v2，保留原评估29与信号21。零本轮Provider调用。
4. 历史机会1–16及其评估/信号逐行等于备份；自然Run16/17原输入/输出、原评估29/30与#18原信号22保持。既有41项检查40通过、1项停用Profile回退断言失败，仍为10月17日已在修复前复现的相邻providers.py模型配置行为，不扩改、不宣称全绿。Ruff通过，临时审计重放及正文/日期逐字校验通过。
5. 正式Worker空闲后优雅重载，Beat不重启；正式API ready200，GET17/18与普通5173页面可见科技0/生活3、partial、17/18评估v2及修订日期。服务重载只为下次自然任务，不触发当天重跑。

### 下一步与边界

automation-3沿用每日08:20，验收2026-10-19或之后修复后真实08:00自然日批；同时满足两个change规范后才关闭原9.5/9.6与4.2/4.3，同步各canonical并归档，随后停止跟进。未归档、提交、push或公开发布。私有备份含natural-runs.json、natural-acceptance.json、repair-receipt.json、api17-readback.json、api18-readback.json；精确代码覆盖以manifest最后的natural_publication_role_extension为准。

本轮实际使用Superpowers、OpenSpec apply、systematic-debugging、executing-plans及requesting-code-review；archive skill仅核对条件，未执行归档。

## 2026-10-19自然验收未通过
Run20科技technology.v1来源54+56生成#19常青；Run21生活仅55生成#20近期报道，各1条，真实Beat→Worker。生活#20/item766澎湃转载央视财经内容仍误标原文日期，双评分未阻止；科技769/722因引文换行空白差异被误判缺证据。详细IDs/hash/顺序/API/UI回读证据见 ../improve-tech-opportunity-selection/review.md 2026-10-19末节。本次只读业务数据并回写文档；原Run/评分/修订/历史保留，未重跑未修复未归档，原未完成项保持。

## 2026-10-20 自然复核
Run24/25各0条；生活item799本地日期经UTC跨日后与原引文不匹配被误拒，质量未通过。详见../improve-tech-opportunity-selection/review.md末节。业务只读，未重跑/改数据/归档，既有未完成项保留。

2026-10-21只读跟进：Run28/29科技1条#21、生活0条；既有缺陷未修复，验收状态不变，不关闭清单或归档。证据见../improve-tech-opportunity-selection/review.md同日记录。
