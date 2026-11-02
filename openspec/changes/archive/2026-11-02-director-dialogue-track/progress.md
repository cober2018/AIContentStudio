# progress

- 2026-11-03 方案已写，等用户确认。
- 2026-11-03 实现完成（未提交）：video_documents（dialogue 轨与段校验）、content_masters（查库检查 + dialogue 素材种类）、video_chain（_save 先查库、RULES）、creative_mcp（save_director_draft 说明）、craft-resolve（sound.md「声音轨口播衔接」+ SKILL.md / choose.md 索引）、web（StoryboardTable 每句台词旁显示声音来源 / 镜头原声，表下列未对应台词的声音段；VideoStudioModel 类型）。
- 副本验证：作品 93 存一版带声音轨（455 截取 0.70–2.97 秒 → 成片 13.87–16.14 秒，line-5）成功；455 进入主稿素材引用与开剪素材包并通过素材检查；brief 带出声音轨。重叠、截取超素材时长、放置超出成片、长度不等、台词不存在都被拒并说明哪一段、为什么；页面保存路径同样拒绝超时长。
- openspec validate 通过；tsc 通过。
- 全量 pytest：2441 通过，只剩已知 5 个失败（aco 默认 schema、三个 migrations、plugins put）。验证用的库副本已删。
- 2026-11-03 API/worker 已重启，改动生效；未提交，等用户验收。
