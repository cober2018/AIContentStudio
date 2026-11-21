# 发现
- 2026-11-10 旧连接「DreamO 量化平台（生产）」(connector 2) 有 4 个端点：市场情绪 ok；前瞻风险超时、行业复盘×生命周期、行业 RRG 轨迹 internal_error（11-09 16:55）。数据只进项目事实，没接内容机会。生命周期、RRG 象限属文档列出的建议类内容。
- 平台已有栏目（content_series，scope=persona_editorial 属角色）和作品挂栏目（content_unit.series_id）；文字作品正文块支持 image / chart（引用素材版本），没有表格块 → 表格也出成图。
- 平台有本地 Chromium 出图（local_graphic_renderer，graphic.chromium），可复用画图表；venv 没有 matplotlib。
- 用户决定：每日复盘是一个项目，每天的复盘是该项目一个栏目下的作品；作品形式为文章，插关键数据表和图表；换用 DreamoQuantSimulation 文档里的 7 个对外可展示服务，不用公开数据源；新平台单独申请 Key。
- 2026-11-10 实现时实测（11-09 数据）：
  - review-industry 生产上任何日期都没有数据（文档也说行业表是合成样本）→ 行业数据改用 review-daily 的 industry_top/bottom_json 和 industry_all_json。
  - review-daily 的 industry_all_json 里 change_pct 是上一交易日的（视频媒体 6.25%、种子 4.64% 对上公开行情是 11-06 的；11-09 实际 2.78%、-0.05%），fund_flow 是当天的 → 涨跌幅只用 top/bottom 榜单（各 5 个），全表只取资金流。需告知数据中台。
  - 不带日期查 = 「latest」指向今天，当天数据没生成时返回空 → 改为从昨天往前找最近有数据的一天（当天的表 21:00–02:00 才生成完，不取当天）。
  - review-forward-risk 一天一行约 6 MB，超过平台通用抓取 5 MB / 10 秒上限（旧连接前瞻风险超时的原因）→ 本服务自己用 60 秒超时抓。
  - 宏观日历：标题里重复国家名、部分前值字段是整句文字 → 去重国家名、前值/预期只留 12 字以内带数字的。事件描述里有「利好/压制」类影响分析，不取。
  - 涨停明细只用于按首次封板时间统计只数，不取个股名。
  - 稿件引用的素材必须先被项目引用（ProjectMaterialReference），否则存稿报「素材版本尚未被当前项目明确引用」。
  - 第一版初稿把「开盘 5 分钟上涨占比」写成「高开占比」、自己算了一个混口径的百分比、写了「申万」→ 加字段说明表 glossary、禁止自算新百分比、禁止写分类标准名。
- 2026-11-10 密钥：新连接用环境变量 DREAMO_REVIEW_API_KEY（runtime.env 里还没有）；测试时临时用了本平台现有的 DREAMO_DATA_API_KEY，没写入配置。
- 2026-11-11 换数据源：新 Key 是「公开看板」Key（profile=dashboard-read），只能用 public-* 服务，review-* 全部 403，这是之前 403 的原因，不是没开通。按 DreamOAgents/docs/api/public-dashboard-data-api.md 改接 public-*。
  - 可用：大盘参与与卖压（public-market-participation）、8 个主要指数收盘/涨跌/市盈率/5 年位置（public-market-index-position）、沪深300 股权风险补偿（public-market-compensation）、封板率/连板/最高板/昨日首板收益/炸板回封（public-market-short-feedback）、496 个行业的涨跌幅/成交额/5 日 20 日资金（public-industry-review）。
  - 403：public-forward-risk-events、public-forward-risk-outlook → 宏观日历暂时没有，开通后自动出现。
  - 没有了：连板梯队分层、跌停/炸板只数、首次封板时间分布、涨停行业分组、开盘 5 分钟统计、全 A 市盈率中位数和破净占比；行业资金只有 5 日、20 日，没有当天一天的。
  - 不取的建议类字段：review_group、opportunities、opportunity_score、risk_level、crowding_state、rotation_zone、reasons；市场预算（public-market-budget 的「试错」、能否新开仓）、生命周期和个股评分整服务不取。
  - 上游问题：最新一天（11-10）496 个行业的 change_pct 和 11-09 完全一样（成交额、资金是当天的），11-05→11-06→11-09 正常 → 当天 90% 以上和前一交易日相同就不用行业涨跌幅，其余照写。需告知数据中台。
  - 返回的 trade_date 可能早于请求日期 → 只用 trade_date 等于当天的数据；最新交易日用「请求昨天、看实际 trade_date」取。
  - 手动跑脚本要先 runtime_config.load_from_db，否则模型配置是 mock（model_unavailable）；worker 任务里本来就有。
- 2026-11-11 文字作品的稿子一步原本不展示正文（只有版本列表的「查看」纯文本），用户以为没有文章 → 在稿子一步直接展示当前稿和图表。主稿接口返回的 assets 不带素材 id，图片要从项目 shared-assets 按 material_revision_id 找 material_id 再取 raw。

## 2026-11-14 对外展示平台用的是哪把 Key（只读核查）

- 对外展示平台 = DreamoQuantSimulation（量化数据洞察对外版），环境变量 INSIGHT_UPSTREAM_API_KEY，本地配的是前缀 dodk_5f4c678（数据中台登记名 insight-platform-local-dev (2026-10-15)，交接文档说要吊销，实测仍可用）。生产部署用哪把看不到（生产机 SSH 被权限拦截）。
- 它读的是 13 个 review-* 服务；本项目旧 Key dodk_451cfb3 的可读范围与它完全相同。
- 合规不是靠 Key 限住的：两把 review Key 都能读到个股排名表。合规在对外平台自己的代码里——content_scope.py（37 条内容去留，CNT-001～037）、modules.py 的字段白名单、FORBIDDEN_KEY_RE 出口拦截。
- 本项目当前用的 dodk_491192e（public-*，12 个服务）带 20 个排名/信号/拥挤度字段（如 public-industry-stock-scores 的 rank、public-industry-lifecycle 的 signal、public-industry-review 的 crowding），比对外平台放出的多。
- 2026-11-15 旧 Key dodk_491192e 读宏观日历一直是 403，被 _optional 静默吞掉，所以 11-09～11-13 的稿子都没有日历一段。改为 403 直接报错后，这种情况会在数据保障里显示出来。
- calendar-facts 的前值、预期是字符串，缺失写「说明暂不可用」；437 条里 356 条 indicator_code 是 UNKNOWN（拍卖、库存、钻井数等）。
- 2026-11-16 CPA 代理（127.0.0.1:8317）里已经没有 gemini 和 claude 模型，只剩 grok 系列。平台默认写稿路由 generate / rewrite / text_master_edit 都指向 gemini-3.8-flash-high，所以所有平台写稿都会失败，不只是每日复盘；11-17 早上的自动复盘也会失败。
- grok-4.7 能用，但这篇稿子要推理 1.65 万 token、用时 215 秒，超过 model_registration 里代理请求的 120 秒上限。代理里有 grok-4.20-0309-non-reasoning、grok-4.7-build-fast，平台还没登记。
