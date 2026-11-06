# 修复：成片带角色片段时交成片被拒（creative_video_duration_mismatch）

## Why
作品 95 成片任务 57（执行包 68，director.persona_clips 有收尾 618，4200 ms）：成片按规则 = 小样 217283 + 片段 4200 = 221483 ms（60 fps），submit_output(final) 报 422 creative_video_duration_mismatch（trace 5aeeef73ba31412087aa60024fb6166e）。
原因：`creative_media_stream.validate` 交 rough_cut / final 时目标时长只取 `director.timeline.duration_ms`，没加角色片段；上一版改执行包、清单、审片页时漏了这里。

## What Changes
- `creative_media_stream.validate`：role final 的目标时长 = `director.timeline.duration_ms` + `director.persona_clips` 所有片段的 `duration_ms`（进门 + 收尾）；容差照旧（1 帧 + 1 ms），容器时长和视频流时长都按它比。
- rough_cut 不变；没有角色片段的成片不变。

## 顺手查过、不改的
| 位置 | 用 timeline.duration_ms 做什么 | 结论 |
|---|---|---|
| `web_video_handoff.validate_edit_manifest` 第 369 行 | 清单 timeline 里每镜的起止不超出导演稿时间线 | 镜头在导演稿时间线上的位置，片段规定不写进 timeline，不是成片总长，不改 |
| `delivery_checks.inspect` | 按镜头抽查亮度 / 响度 | 只按镜头位置抽查、只提示，不卡交付，不改 |
没有别的地方拿它当成片总长来卡。

## 不在范围
不动任务 57 的数据（停在「制作中」revision 6，两张封面已交）；修好后由第三方模型接着交。
