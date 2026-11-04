# review：fact-boundary-topic-templates

## 2026-11-03 实际使用中发现（作品 94，审计方）

代码版本：0054c0f。

### 缺陷：有事实边界以后，交事实和读模板都报错（数据其实存上了）

| 项目 | 内容 |
|---|---|
| 现象 | 第三方模型调 `submit_facts` 返回 `creative_domain_invalid_arguments`（422），但事实边界第 1、2 版都已冻结入库（project_fact_boundary_revision 14、15，fact_pack 12、13）。之后调 `get_fact_template` 也一样报 422。项目还没有事实边界时 `get_fact_template` 正常 |
| 原因 | `fact_templates.current()`（fact_templates.py:175）把 `pack.frozen_at` 原样放进结果，这是 datetime。MCP 结果转 JSON 时转不了，被当成参数错误返回 |
| 证据 | 本机直接调 `fact_templates.current(db, 49)`：`frozen_at` 类型是 `datetime.datetime`，`json.dumps` 报 `Object of type datetime is not JSON serializable` |
| 影响 | 模型以为没交成功，会重复提交，每次多一版事实边界；也读不到「哪几条被退回、哪几条带标注」，没法按规则换来源重交。看不到当前事实边界，导演稿和文章都只能盲写 |
| 建议改法 | `frozen_at` 转成 ISO 字符串，和其他接口一致 |

### 观察（不算这次需求的缺陷）

- 健康模板认的网站大多是 gov.cn。北京卫健委的两篇科普（wjw.beijing.gov.cn、www.beijing.gov.cn）平台抓取返回 403（网站拦自动访问，本机 curl 第二次起也 403），回执里的原因是 `fetch: internal_error`，模型看到的是「来源打不开」。这次改用美国儿科学会 healthychildren.org 和新华网（标「来源不在常见权威网站」）。
