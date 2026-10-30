# redo-sent-back-cut

- 阶段：缺陷修复（执行方反馈），已本地实施，未提交
- 问题：作品 85 成片（执行 23）被「按意见修改」退回后，prepare_video_edit(phase=final) 报 video_chain_sample_not_approved；即使放行，主稿没变时 idempotency_key 相同会拿回执行 23；上游小样按当前执行找，会找成执行 23。小样退回后重开有同样的 key 问题。
- 修复（apps/api/app/services/video_chain.py prepare_edit）：
  1. 成片在 finishing 或 final_changes 都能开。
  2. key = chain-{主稿}-{阶段}，该阶段被退回过就加 -after-{最近一次退回的执行号}；重试时 key 不变，复用新任务。
  3. 上游小样从任务记录里倒着找最近一条已接受的小样。
- 验证：作品 85 回滚事务里重开成片 → 新执行 24（key chain-194-final-after-23），上游小样输出 241（执行 22 的已接受小样）；再调一次仍是 24；回滚后任务记录不变。相关测试 170 passed。API 已重启。
