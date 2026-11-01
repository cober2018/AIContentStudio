# 进展

- 2026-10-31：用户确认方案，开始实施。
- 2026-10-31：后端 `discovery_sources.health` + `GET /content-opportunities/discovery/source-health`；前端 `SourceHealthTable.tsx` 放在内容机会页顶部，有问题的行排前面并标黄。
- 验证：接口真实数据 50 个已订阅源（正常 23、报错 27、未被安排 26、近 3 天无新内容 37）（卡哟哟两站 10-27 起每天 0 条，21 个单独源今天恢复有新内容，多个源 adapter_unavailable / credential_required 未被安排）；tsc 通过；discovery 相关测试 31 passed；API 已重启。
- 2026-10-31：提示文字「需要登录凭据」改为「网站拦截访问」（DiscoveryPanel.tsx 标签表，信息源列表和数据源情况表共用）；tsc 通过。
