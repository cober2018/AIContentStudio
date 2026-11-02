# findings

- 现行规则（video_chain.RULES）：封面竖版 jpg/png、实拍当背景加大字，导出到 导出/封面、role cover 交付、在剪辑清单之前交；可剪进开头当 0.5 秒第一帧。成片通过后 _adopt_cover 把 cover 设为作品封面。
- 交付检查入口在 creative_executions 交付流程（delivery_checks.inspect 对 rough_cut/final），封面交付目前不做比对。
- 用户之前认可的封面做法（AE 同一合成出封面和首帧）与新规则冲突，以新规则为准。
- 比色要先把成片帧转成全尺寸 RGB 再缩小；先在 YUV 上缩小再转 RGB，同一帧也会差约 2.6（蓝通道 5），会掩盖真实差异。改后同一帧差 0.0，JPEG 截帧约 2.3。
- 比色结果存在后交的那一条输出的 metadata.cover_check（带 against=另一条输出 id），审阅页只在这对仍是当前那对时显示；sRGB 标记提示放进成片 shot_checks 的 warnings。
- 改标记必须同时改码流（h264_metadata/hevc_metadata）和容器（-color_primaries/-color_trc/-colorspace），只用 bsf 时容器 colr 仍是旧值（已实测）。
