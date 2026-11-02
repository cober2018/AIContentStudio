# progress

- 2026-11-02 第 1 条已紧急修复：creative_contracts._METADATA_KEYS 加 cover_check；safe_metadata 接受平台写的比色结果；全量只剩 5 个已知失败；API/worker 已重启。第 2 条方案已写，等用户确认。
- 2026-11-02 第 2 条已实施并重启服务，未提交：video_chain.decide 通过小样/成片时先写 approving 标记并提交，成功后随决定一起清掉，失败（HTTP 或其他异常）回滚并清掉再抛出；_state 遇到同一任务的标记（5 分钟内）返回 state=approving、label「正在通过…」、detail 说明别当待你看；get_video_decision（decisions）随之返回。页面：approving 时每 3 秒刷新、归到对应步骤；点通过后按钮显示「正在通过…」。
  - 正式库副本验证（作品 84，小样待你看）：采纳过程中另一连接读到 approving「正在通过…」；成功后进入排版中、无残留标记；采纳失败时回到小样待你看、无残留标记。全量只剩 5 个已知失败；tsc 通过。
