# 科技与生活聚合站接入

## PRD / 需求背景
用户提供科技站https://aitech.kayoyo.top/映射经营角色2，生活站https://wonderlife.kayoyo.top/映射经营角色3；站点负责采集，本项目按角色选题并共用原创作流程。

## 当前阶段
PUBLICATION_ROLE_FIXED_WAITING_NEW_NATURAL_RUN；实施8/10，两个角色已验证后正式切换，完整自然日批与归档待完成。

## 目录结构
proposal.md、design.md、specs/为规范；tasks.md、task_plan.md为实施清单；progress.md、findings.md、review.md与interface_inspection.json记录证据。

## 已完成
两站Agent页声明匿名REST/RSS/MCP4.0.0；curl实读两站OpenAPI及各2条资讯均200，已核对字段、分页与精选同步合同。

## 待完成 / TODO
2026-10-19或之后08:00修复后新入口真实自然日批验收，再同步规范并归档；原automation-3每日08:20继续。

## 关键设计决策
首次精选snapshot，此后changes；保留原始来源及正文，沿用质量门槛。成功验收后两个角色切换为聚合采集，旧源与人工配置可恢复。

## 代码位置与版本
/Users/mshengran/Project/AIContentStudio当前脏工作区；本轮10路径准确hash见implementation_manifest.json，尚未提交。父change每日自然验收保持独立，不能用旧入口回执代替本接入验收。

## 依赖与启动方式
沿用FastAPI/Celery/Redis/Web，无新增产品依赖，不安装远程Skill或AIHOT。校验：openspec validate add-aihot-persona-source-integration --strict。

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

2026-10-16：按用户要求，仅将正式来源54/55显示名称统一为“卡哟哟 AI 热点”/“卡哟哟 生活热点”。正式PATCH后GET回读确认角色仍分别为2/3，采集URL、类型、暂停和分析开关不变；回执source-name-update.json。无代码改动，既有自然验收计划不变。本轮使用Superpowers。

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
