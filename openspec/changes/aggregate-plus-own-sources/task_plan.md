# 计划

///
1. discovery_aggregation.allowed_source_ids 返回 聚合 + 雷达 + 订阅启用源；accepts_source 随之放行
2. daily_opportunities._evidence 用新集合；确认上限 / 预算逻辑不变
3. discovery_runtime.check_current：aggregate_evidence_withdrawn 改为剔除该证据，全空才 DiscoveryBlocked
4. 测试；看 worker 一轮抓取（21 个源到期）
///
