## 1. 实现
- [x] 1.1 `craft_skills.py`：aerender 外面加按到达顺序的单线排队
- [x] 1.2 `creative_executions.transition_execution`：领取 `codex-video-production` 任务时检查别的作品有没有正在剪的（已领取 / 进行中 / 受阻，且 30 分钟内有动静），有就返回 `video_edit_queue_busy`
- [x] 1.3 `video_chain.py` 剪辑说明加「每 20 分钟内至少回报一次进度」
- [x] 1.4 `project_folders`：关掉 `_clean_work` 自动清理
- [x] 1.5 `video-production-handoff/SKILL.md`：删掉「平台会清理旧任务文件」；加删 `-reopen`、删同作品旧任务项目两条

## 2. 验证（数据库副本）
- [x] 2.1 两个渲染同时调用，aerender 先后执行
- [x] 2.2 作品 A 剪辑进行中时领作品 B 被拒；A 交片后能领；A 超 30 分钟没动静能领
- [x] 2.3 成片通过后硬盘工作文件一个不少
- [x] 2.4 相关已有测试

## 3. 一次性清理达芬奇项目（用户确认清单后）
- [x] 3.1 列出要删的达芬奇项目
- [x] 3.2 用户确认后通过达芬奇脚本删除
