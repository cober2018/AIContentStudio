# 发现

- discovery_aggregation.allowed_source_ids：角色选了聚合站就只返回 {聚合站, 雷达}；eligibility 因此对 21 个单独源给出 no_eligible_subscription，它们自 10-16 起没再抓。
- 卡哟哟 aitech / wonderlife 两个快照接口正常返回，但最新 discoveredAt 是 2026-10-26 14:40Z，之后无新内容；平台每分钟同步，new_versions=0。
- discovery_runtime.check_current：任何一条聚合证据不再 selected 就整次 DiscoveryBlocked("aggregate_evidence_withdrawn")；角色 3 自 10-27 起每天都被拦。
