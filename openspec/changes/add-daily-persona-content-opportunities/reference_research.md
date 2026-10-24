# 参考项目研究与采用方式

研究日期：2026-10-15。以下基于公开 README、实际文件及固定提交；仓库描述不等同本机运行验收。未安装参考项目，也未执行其中脚本。

| 项目 | 固定提交 | 许可 | 本次参考范围 |
| --- | --- | --- | --- |
| [Easel](https://github.com/ZJU-REAL/Easel) | bb3c8ff0463f36c202454d74171682ba6e470cb1 | Apache-2.0 | 画像驱动发现、热榜入口、RSS与选题评价 |
| [AIHOT](https://github.com/KKKKhazix/AIHOT) | e57da5a4f151892a217529744cd68803aec580df | MIT | 信源配置、采集、独立评分、事件热度与后台周期任务 |

## Easel：选题从哪里来

其发现流程读取账号的定位、受众、平台及风格，再从热榜和资讯提取相关题材。热点技能通过第三方聚合 API 取得平台榜单，并筛出适合角色的切入点；评价技能使用统一维度解释是否值得做。参考的是画像注入和筛选过程，不继承其流量、变现或发布目标。

| 代码/文档依据 | 已观察行为 | 本项目适配 |
| --- | --- | --- |
| [trending-topics](https://github.com/ZJU-REAL/Easel/blob/bb3c8ff0463f36c202454d74171682ba6e470cb1/skills/builtin/skill-trending-topics/SKILL.md) | 热榜→赛道匹配→切入角度 | 读取现有 PersonaRevision，机会直接持久化 |
| [topic-evaluator](https://github.com/ZJU-REAL/Easel/blob/bb3c8ff0463f36c202454d74171682ba6e470cb1/skills/builtin/skill-topic-evaluator/SKILL.md) | 按多维度给依据和结论 | 保留匹配、读者价值、证据、差异化和时效；不增加商业化目标 |
| [trend-rider](https://github.com/ZJU-REAL/Easel/blob/bb3c8ff0463f36c202454d74171682ba6e470cb1/skills/builtin/skill-trend-rider/SKILL.md) | 同热点按画像设计切入点 | 同一事件允许科技/生活各有不同角度 |
| [hotlist-apis](https://github.com/ZJU-REAL/Easel/blob/bb3c8ff0463f36c202454d74171682ba6e470cb1/skills/shared/hotlist-apis.md) | 60s与备用聚合入口 | 仅作为可替换讨论信号，实测后才启用，保留第三方身份 |
| [rss_digest.py](https://github.com/ZJU-REAL/Easel/blob/bb3c8ff0463f36c202454d74171682ba6e470cb1/skills/builtin/skill-rss-aggregator/scripts/rss_digest.py) | RSS聚合实现入口 | 纳入后台采集适配，不搬CLI调用形式 |

这些文件提供 Agent 技能与工具编排参考；没有据此声称 Easel 已实现“本项目创建 Persona 后自动建来源库”。此触发闭环由本 change 接入。

## AIHOT：如何持续得到值得关注的事件

AIHOT 将来源配置、采集处理和展示分开。相同新闻先去重，再评分和归组；热度以独立参与来源及其发布时间计算。来源清单可替换，仓库包含示范源，不是其线上完整运营名单。

| 代码/文档依据 | 已观察行为 | 本项目适配 |
| --- | --- | --- |
| [sources.md](https://github.com/KKKKhazix/AIHOT/blob/e57da5a4f151892a217529744cd68803aec580df/docs/sources.md) | RSS、网页、JSON、账号等分类型采集，记录失败及发布时间 | 自动发现入口、自动验证适配，失败来源独立标记 |
| [collect.ts](https://github.com/KKKKhazix/AIHOT/blob/e57da5a4f151892a217529744cd68803aec580df/packages/backend/src/sources/collect.ts) | 游标、有限首次导入、错误状态与后续补齐 | 老内容不因新抓到就变成今日热点；正确来源不反复全量拉取 |
| [selection.ts](https://github.com/KKKKhazix/AIHOT/blob/e57da5a4f151892a217529744cd68803aec580df/industry/selection.ts) | 独立两次评分与来源分级门槛 | 对少量候选做两次独立角色评分；具体权重按角色目标修改 |
| [hot.ts](https://github.com/KKKKhazix/AIHOT/blob/e57da5a4f151892a217529744cd68803aec580df/packages/backend/src/events/hot.ts) | 48小时窗口、24小时半衰期、独立参与者去重；来源滞后影响趋势可信度 | 热度与角色价值分开，复制来源不增加独立支持，缺少覆盖时不称全网趋势 |
| [schedules.ts](https://github.com/KKKKhazix/AIHOT/blob/e57da5a4f151892a217529744cd68803aec580df/apps/worker/src/schedules.ts) | 后台周期采集、热度更新、到期汇总及恢复 | 对应到现有 Celery Worker，不新增 pg-boss/PostgreSQL 服务栈 |

## 融合边界

采用成熟流程与适配思想，保留可追溯上游归属。源码或提示词若在实施中直接移植，须在实际移植文件/第三方说明中保留相应许可证和修改说明。AIHOT 商标、Logo、站点样式、日报/周报/月报产品不进入本需求。

后台联网发现需明确搜索出口。现有项目暂无通用网页搜索适配，默认建议接 [Tavily Search](https://docs.tavily.com/documentation/api-reference/endpoint/search) 的 HTTP 搜索：返回 URL、标题、片段和可选日期，再由现有安全读取补证。当前聊天的联网能力用于本次研究，不是应用已安装的运行依赖。
