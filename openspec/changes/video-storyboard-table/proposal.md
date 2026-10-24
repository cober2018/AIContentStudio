## Why

A video currently goes through three AI stages: 视频脚本 (script), 镜头计划 (shot plan), 导演稿确认 (director draft). Each one rewrites the video. On U80 the shot plan had 15 shots and the director draft came back with 7. Material picked in the shot slots also has to be picked again per shot later.

The user's view, and the common professional practice (see `openspec/视频分镜脚本表.xlsx`): the director draft is one storyboard table, produced in one go. One row per shot. Copy, picture, camera, spoken line, sound and material all sit in the same row. There is no separate script or shot plan.

## What Changes

- New video workflows SHALL have one AI stage, 导演稿 (`master`), followed by 专业执行准备. The 视频脚本 and 镜头计划 stages are removed from the video workflow definitions, including the product video workflow.
- The 导演稿 SHALL be a storyboard table with these columns per shot:
  1. 镜头: L01, L02…, one shot says one thing.
  2. 时长: start and end, computed by the platform. The total is always the sum. Durations are estimates. The final timing follows the narration audio.
  3. 信息点: the one point this shot gets across.
  4. 画面: framing, subject, action, scene and light, written so it can be shot or generated.
  5. 运镜: fixed, push in, pull out, follow, orbit or pan.
  6. 台词: the exact words spoken, marked 旁白, 口播 or 对白, or 无台词.
  7. 声音: sound effects, music, ambience.
  8. 备注: transition, on-screen text, notes.
  9. 素材: the material for this shot, filled in later in the same row through the shot slot.
- The AI SHALL return the whole table in one answer. The user reviews and accepts it once.
- 素材 is picked once in the shot slot. A shot with exactly one pick SHALL use it without a second selection. A shot with several picks asks the user to choose among those picks only.
- The system-owned product video workflow moves to the new definition the next time it is used. Persona video workflows the user already saved move only on the user's say-so (done for persona 2 and 3 on 2026-10-23).
- Existing runs keep their definition. U80 still has a shot plan stage, so its 导演稿 follows the plan (`master-follows-shot-plan`) and now produces the same table.

## Impact

- API: video workflow definitions (`starter_personas`, `workflow_templates`), the 导演稿 output contract (`stage_resolver`), the table builder (`stage_master_proposals`), and optional per-shot table fields in `video.master.v2` (`video_documents`). No migration. Older masters stay valid.
- Web: the 导演稿 review shows the table. The per-shot material panel takes slot picks directly.
- Not in this change: filling material automatically per row (own library → licensed stock → AE template → code animation), which comes after the AE template library; aligning the edit timeline to the real narration audio (to be checked separately), automatic acceptance, and graphic or text workflows.
