# Findings

- 自动日报复用catchup step即可保证日批前置，无需第二个scheduler；将Radar lease扩至8分钟覆盖300秒CLI上限。文件完成仍不等于时间区间覆盖，原partial保持。
- SystemSetting是普通JSON、正式Session expire_on_commit=False；首次保存running后必须复制字典再更新终态，否则SQLAlchemy不检测原对象变化。独立复核发现并修复，以重新加载持久值验证。

- 2026-10-19补充授权后实际安装并运行。免费GitHub/HF无需新凭据；不要把README付费AIsa路径误作全部信号前置。实际日报15条可解析GitHub原文URL，来源56已启用。Radar CLI是批处理而非常驻服务：既有scanner只导入文件，尚不能自动生成下一天日报。明确区分这两层。

- 科技信源54、生活55当前分流成立；本次是扩科技资格及补充线索，不重做两个角色。
- daily_opportunities.py:_ground_candidate 对hot/recent_report有48小时门槛；evergreen已有但依赖模型正确分类。
- _collect_articles 有20条尝试/12KB输入限制，未分析不等于不合格。增加Radar须保留预算并显式反映覆盖。
- OpportunityPages.tsx默认当天+recommended；后端recommended_only原本仅按状态筛选，需显式科技有效期契约。
- daily-persona和AIHOT基础规格仍active，不存在daily-persona-opportunities canonical。本包采用独立补充capabilities而不伪造MODIFIED目标；归档顺序和默认视图冲突处理见design第5节。
- Radar官方README明确新词/项目发现及可选付费信号：https://github.com/zhuyansen/new-term-radar/blob/main/README.zh-CN.md 。本轮仅文档核查，没有安装、可用实例或输出样本验收。后续SEO/GEO技能复用不属于本change。
- 新有效期具体值是本次规格提案默认值（hot48小时、近期7天、常青30天），待规格复核；不是声称现有系统已经这样运行。
# 2026-10-19 Radar真实输出核实

- 上游 https://github.com/zhuyansen/new-term-radar ，0.4.0，commit `2568cdcba5691cd21d03f2c0a86f4461dbcb7234`。`radar/__main__.py` daily `--out PATH.md` 写同名JSON；`radar/report.py`定义leads；未执行上游软件。
- Daily JSON含leads及x/hf/breakout/sitemap/newsite/revenue/ask/gsc/review/summary/keywords；并非RSS或公开HTTP feed。Saved-lead `{leads,hit_rates}`不是该格式。
- 可证明引用来自repo、posts[].url、about[0]及明确Reddit join。无原文URL的term保留未解析计数，不猜URL。输出通常无原始发布时间/发现时间，缺失保持null；import时间不补成发布时间/发现时间。
- 对现有配置文件的窄检查未建立Radar report path；不等于断言整台电脑未安装。接入采用用户显式配置的既有本地daily JSON，使用adapter版本与实际producer标识分开记录。


- 2026-10-19自然验收发现：逐字引文未规范空白导致真实正文误拒；生活转载日期仍误标原文。详见review末节，未改代码或数据。

2026-10-20：自然Run24/25各0条；新增确认_date_proof按UTC日期匹配本地日期引文导致跨日误拒。验收未通过，未修复/重跑/归档，证据见review.md末节。
