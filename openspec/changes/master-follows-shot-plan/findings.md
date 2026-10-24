# Findings

- U80 director draft attempt 331 has 7 shots and 7 script blocks, against the accepted 15-shot plan.
- `stage_master_proposals._video_plan` allows only 1–8 beats and assigns ids `shot-1…`. The shot plan schema allows up to 100 shots; `video_documents` allows up to 300 and accepts ids such as `shot-0`.
- The plan reaches the stage as `resolved["upstream"]["shots"]["selected_content"]["shots"]`, with fields `id, order, script, visual, purpose, framing, duration_seconds, asset_requirements`. Because it is part of the frozen resolution, it is already covered by the resolution hash.
- Decision (user, 2026-10-23): the director draft takes the shots from the plan; the AI only polishes each shot's narration and visual. Changing the shots belongs to the shot-plan stage.

## 2026-10-23
- 用户确认：视频以口播音频为主线。镜头计划/导演稿定镜头数量、顺序、内容；时长只是估计，最终以配音实际长度为准。剪辑是否已按音频对齐尚未核实，另行处理。
- 新发现：镜头素材格子里选好的素材（素材匹配里的「采用」）不会写进导演稿的镜头，分镜素材面板要求每镜再选一次，属于重复操作。
