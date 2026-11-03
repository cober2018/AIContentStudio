# 设计要点

## 换算
- 当前倍速 old：声音段的 speed_percent（没写算 100）。各段倍速不一致时拒绝，提示让第三方模型先统一（滑块只管整片统一倍速）。
- 比例 r = old / new。时间点 t 换成 round(t × r)，所有时间点用同一个函数，所以原来对齐的边界换算后还对齐。
- 镜头：按 order 累加出切点，切点换算后相减得新时长（至少 1 毫秒）。
- 声音段：start 按 r 换算；end = start + round(截取长度 × 100 / new)，再夹到下一段 start 和总长以内，保证不重叠。
- 视频轨元素长度不超过所属镜头新时长。非声音段的素材截取不动：变快时放置变短，截取仍够长；变慢超出截取长度时，按现有校验拒绝并说明哪段不够长。
- 不动的：素材截取、拍摄任务的原始时长、生成请求时长（都是素材自身的时间）。

## 保存
- 走 `edit_handoff._save`，edit_summary 记 `{"speech_speed": {"from": old, "to": new}}`。
- `video_chain._keeps_draft` 加上 `speech_speed`，所以不算新导演稿、不用重新采用。
- 定稿后 `save_revision` 已经拒绝（`video_chain_locked`），不另加检查。

## 接口
- `GET .../voiceover` 多返回 `speech`：有 dialogue 声音轨时 `{speed_percent, duration_ms}`，没有是 null。页面用 duration_ms × speed_percent / new 实时估算新时长。
- `PUT .../voiceover/speed` `{speed_percent: 80–150}`（滑块范围；导演稿字段本身允许 50–200）。
