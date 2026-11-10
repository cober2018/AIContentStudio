## 1. 查明
- [x] 1.1 写锁等待超时时记录：project_authorization.lock_project_context 报 project_context_busy 时记下项目和等待的调用链；占锁的长写已查实（见 findings）
## 2. 后端
- [x] 2.1 查实是 content_masters.run_checks / run_variant_checks 拿项目写锁后等模型几十秒不提交；已由 search-runner-output-format 变更改成先提交放锁（不在本变更重复改）
- [x] 2.2 routers/edit_agent.video_chain_decide：遇到 project_context_busy 或 database is locked 时回滚重试（重试窗 22 秒，连同单次 8 秒等锁约 30 秒）；仍失败就清「正在通过」标记，返回 409 video_chain_db_busy「数据库正忙，这次没通过，请再点一次」（放在路由层，避开 video_chain.py 里别的需求未提交的改动）
- [x] 2.3 maintenance：数据库忙就跳过本轮（stats 记 skipped_busy），记一行 info，不打整段报错
## 3. 页面
- [x] 3.1 VideoChainPanel：失败原因显示在按钮下面（原来在面板最底下），失败后也刷新状态，按钮恢复可点
## 4. 验证
- [x] 4.1 库副本复现：占写 10 秒 → 第 2 次通过（9.8 秒）；占写 45 秒 → 3 次后返回「数据库正忙…」（27.7 秒）；占写时清理任务 retention=skipped_busy
- [x] 4.2 全量后端 2353 通过（5 个旧失败不变）；tsc / build 通过；api 已重启，health 200
