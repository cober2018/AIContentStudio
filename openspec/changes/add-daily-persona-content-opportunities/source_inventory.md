# 首批来源储备

公开来源储备。HTTP可达不等于采集适配验证；feed_candidates来自页面声明，feed_check另记本次解析结果。所有记录尚未导入或启用。

科技与生活均包含官方/媒体/个人来源；热榜为第三方讨论线索，不能替代原始事实。作者是否“大V”不虚构粉丝数字，采用可核验公开主页与领域代表作。

| 来源 | 适用角色 | 类别 | 本次访问 | 用途 |
| --- | --- | --- | --- | --- |
| [OpenAI News](https://openai.com/news/) | 科技 | official | http_accessible | 模型与工具官方发布，回到一手说明核对能力 |
| [Anthropic Engineering](https://www.anthropic.com/engineering) | 科技 | official | http_accessible | Agent工程、上下文、工具与评估实践 |
| [Hugging Face Blog](https://huggingface.co/blog) | 科技 | official | http_accessible | 开放模型、推理与工具生态 |
| [LangChain Blog](https://blog.langchain.com/) | 科技 | official | http_accessible | Agent编排与工程案例；产品方观点需标明 |
| [GitHub Blog](https://github.blog/) | 科技 | official | http_accessible | 开发工作流、工程工具及发布 |
| [Simon Willison](https://simonwillison.net/) | 科技 | creator | http_accessible | LLM与编程工具的实测、限制与工程观察 |
| [Hamel Husain](https://hamel.dev/) | 科技 | creator | http_accessible | LLM评估、调试与产品工程 |
| [Chip Huyen](https://huyenchip.com/blog/) | 科技 | creator | http_accessible | AI系统设计与工程实践 |
| [Lilian Weng](https://lilianweng.github.io/) | 科技 | creator | http_accessible | 深度技术综述；低频更新，作为背景来源 |
| [Andrej Karpathy](https://karpathy.ai/) | 科技 | creator | http_accessible | 模型与开发范式；主页用于确认作者及官方账号 |
| [宝玉](https://baoyu.io/) | 科技 | creator | http_accessible | AI工程、工具与译介，译文追溯原作者 |
| [归藏](https://guizang.ai/) | 科技 | creator | http_accessible | AI工具、设计与独立开发 |
| [阮一峰](https://www.ruanyifeng.com/blog/) | 科技 | creator | http_accessible | 开发者周刊、开源工具和工程观察 |
| [Addy Osmani](https://addyosmani.com/blog/) | 科技 | creator | http_accessible | 软件工程、开发工具与AI辅助开发 |
| [Latent Space](https://www.latent.space/) | 科技 | media | http_accessible | AI工程访谈与领域趋势 |
| [InfoQ中文](https://www.infoq.cn/) | 科技 | media | http_accessible | 软件架构与研发案例 |
| [少数派](https://sspai.com/) | 两角色 | media | http_accessible | 数字生活与工具使用；按角色区分工程和生活角度 |
| [爱范儿](https://www.ifanr.com/) | 两角色 | media | http_accessible | 科技产品对日常生活的新影响 |
| [果壳](https://www.guokr.com/) | 生活 | media | http_accessible | 日常现象、自然与科学好奇心，健康结论回原始证据 |
| [新周刊](https://www.neweekly.com.cn/) | 生活 | media | http_accessible | 城市、年轻人及生活方式观察 |
| [一条](https://www.yit.com/) | 生活 | media | http_accessible | 生活方式与人物故事；官网需区分商城和编辑内容 |
| [下厨房](https://www.xiachufang.com/) | 生活 | community | http_accessible | 日常饮食与厨房生活趋势；社区体验不是普遍事实 |
| [豆瓣生活社区](https://www.douban.com/) | 生活 | community | http_accessible | 兴趣小组与普通人的生活变化，只作为讨论信号 |
| [Dezeen](https://www.dezeen.com/) | 生活 | media | http_accessible | 设计、居住空间与未来生活变化 |
| [Colossal](https://www.thisiscolossal.com/) | 生活 | media | http_accessible | 艺术、自然与有趣的视觉观察 |
| [Atlas Obscura](https://www.atlasobscura.com/) | 生活 | media | http_accessible | 地方文化、日常奇趣与探索线索 |
| [Austin Kleon](https://austinkleon.com/) | 生活 | creator | http_accessible | 观察、创作习惯与具体日常 |
| [Maria Popova / The Marginalian](https://www.themarginalian.org/) | 生活 | creator | http_accessible | 文化阅读、自然与生活观察 |
| [日食记](https://space.bilibili.com/8960728) | 生活 | creator | http_accessible | 食物与日常叙事；元数据线索，不自动搬运视频 |
| [盗月社食遇记](https://space.bilibili.com/99157282) | 生活 | creator | http_accessible | 城市小店、饮食与普通人的生活故事 |
| [60s 小红书热点聚合](https://60s.viki.moe/v2/rednote) | 两角色 | hotlist | fetch_failed | 平台话题线索；第三方聚合，保留原帖链接 |
| [60s 知乎热榜聚合](https://60s.viki.moe/v2/zhihu) | 两角色 | hotlist | fetch_failed | 讨论信号；不以热榜证明事实 |
| [60s 微博热搜聚合](https://60s.viki.moe/v2/weibo) | 两角色 | hotlist | fetch_failed | 发现公共热点，必须按角色过滤 |
| [60s 抖音热点聚合](https://60s.viki.moe/v2/douyin) | 两角色 | hotlist | fetch_failed | 发现生活与产品话题，非正文来源 |

完整机器可读元数据、来源依据、HTTP结果与发现的订阅入口见 source_inventory.json。失败源保留候选；正式启用时自动验证适配器，不将失败源伪装成可采集。
本清单没有全网覆盖保证；它是首版种子，后续按角色自动增补与淘汰失效来源。

## RSS/Atom本次检查

| 来源 | 订阅检查 | 条目数 |
| --- | --- | --- |
| [OpenAI News](https://openai.com/news/rss.xml) | feed_parsed | 1293 |
| [Hugging Face Blog](https://huggingface.co/blog/feed.xml) | feed_parsed | 876 |
| [GitHub Blog](https://github.blog/feed/) | feed_parsed | 10 |
| [Simon Willison](https://simonwillison.net/atom/everything/) | feed_parsed | 30 |
| [Hamel Husain](https://hamel.dev/index.xml) | feed_parsed | 20 |
| [Chip Huyen](https://huyenchip.com/feed.xml) | feed_parsed | 10 |
| [Lilian Weng](https://lilianweng.github.io/index.xml) | feed_parsed | 53 |
| [宝玉](https://baoyu.io/feed.xml) | feed_parsed | 50 |
| [阮一峰](https://feeds.feedburner.com/ruanyifeng) | feed_parsed | 6 |
| [Addy Osmani](https://addyosmani.com/rss.xml) | feed_parsed | 10 |
| [Latent Space](https://www.latent.space/feed) | feed_parsed | 20 |
| [少数派](https://sspai.com/feed) | feed_parsed | 10 |
| [Colossal](https://www.thisiscolossal.com/feed/) | feed_parsed | 10 |
| [Atlas Obscura](https://www.atlasobscura.com/feeds/latest) | feed_parsed | 27 |
| [Austin Kleon](https://austinkleon.com/feed/) | feed_parsed | 10 |
| [Maria Popova / The Marginalian](https://feeds.feedburner.com/brainpickings/rss) | feed_parsed | 20 |

一条官网本次返回生活馆商城入口，需另找编辑内容入口，未标为可采集资讯源。4个60s热榜入口本次失败，保留候选，不沿用上游“已可用”声明。

GitHub订阅首轮因研究读取大小限制截断，复核结果以JSON中feed_check为准，不将本地截断误报为源站损坏。
