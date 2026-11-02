# progress

- 2026-11-02 方案已写，等用户确认。
- 2026-11-02 已本地实施，未提交：product_video 新增 latest_main_image()；references() 与 direction() 主图改取商品最新一版主图（手动指定优先，商品资料仍用冻结版），references 结果多返回 main_image（第几版、是否已跟随最新）；九宫格面板「参考：商品」后显示「（第 N 版，已跟随商品最新主图）」。
  - 正式库核对：作品 90 取到主图 319（第 3 版，已跟随最新）。
  - 更新既有测试 test_shot_references_prefer_manual_then_primary_image_and_portrait 的期望；全量只剩 5 个已知失败；tsc 通过；API/worker 已重启。
