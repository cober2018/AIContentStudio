# Findings

## 2026-10-23
- Three video stages each rewrite the video, so counts drift (U80: plan 15, draft 7).
- Slot picks live in material-match runs and are never written into the master, so the per-shot panel asks again.
- User decision: remove 视频脚本 and 镜头计划 for new video workflows; one 导演稿 table. Keep it simple, follow common storyboard practice.
- From the reference sheet: one shot says one thing; 信息点 is the point, 台词 is the exact words; 画面 is written so it can be shot; durations add up to the total (the platform computes it); shots with no speech say 无台词.
- Durations are estimates; final timing follows the narration audio. Whether the edit already aligns to the audio is unchecked.
- Saved persona video workflows (persona.2.video v3, persona.3.video v3) and project workflows still have script/shots. Product defaults (system-owned) upgrade on next use; persona ones need the user's decision.
- A shot with no speech has no script block. The channel adapter that maps script to scenes rejects such masters (`script_scene_mapping_incomplete`); this only matters for that channel variant.
