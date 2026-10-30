# 进度

- 2026-10-30 写好方案，待确认
- 2026-10-30 实施完成：music_direction 删除（模型、表单助手、旧输入框、作品留存；旧修订读回和任务包快照都过滤）；主稿 music 三态 {material_revision_id} / {none:true} / {}；页面「不用配乐」按钮；prepare_video_edit 在配乐未定时拒绝开剪；剪辑规则说明三态。
- 验证：相关 6 个测试文件 226 passed；全量 2466 passed，失败 5 个均为已知旧失败；三态校验直接核对通过；前端 tsc 通过；API 已重启。
- 2026-10-30 修复回归：上一版在 profile_snapshot 里去掉 music_direction，改变了主稿上下文哈希，旧作品在已有主稿上保存全报 master_context_conflict。改为快照保持原样（主稿哈希不变），只在打任务包时去掉（production_profiles.for_task / context_for_task：任务包 production_profile、product_context、commercial_context，以及旧包比对）。creative_mcp 的 _SAFE_CODES 加 master_context_conflict，执行方能看到真实原因。
- 验证：作品 83（主稿 179）set_materials(music=216) 在回滚事务里跑通（未落库，最新主稿仍是 179）；全量 2466 passed，失败 5 个为已知旧失败；API 已重启。
