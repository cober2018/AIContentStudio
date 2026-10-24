## Context

- Video workflow nodes live in `starter_personas._definition` (script → shots → master → prepare). The product video workflow (`workflow_templates.ensure_product_workflow`) reuses it and adds method and instruction per node.
- `stage.master.propose` builds `video.master.v2` from `{title, beats:[{narration, visual, duration_ms?}]}` in `stage_master_proposals._video_plan`. Shot fields allowed by `video_documents`: `id, order, label, purpose, duration_ms, script_block_id, source_material_revision_id, framing, transition, production, filming, capture_takes`. Narration sits in `script.blocks`. Start and end come from `timeline`.
- Shot slots (`shot_slots.view`) read shots from the latest master, or from the shot plan before a master exists. Picks are accepted candidates in material-match runs. They are not written into the master, so `VideoShotMaterialPanel` asks again per shot.
- Reference: `openspec/视频分镜脚本表.xlsx`, 8 columns plus its fill rules.

## Decisions

1. **One stage.** The video definition becomes `master` (导演稿) → `prepare`. The product workflow keeps its product method and instruction on `master`. The shot-direction rules from the old `shots` node move into the `master` instruction. Old workflow versions and runs are untouched.
2. **Table fields on the shot.** `video.master.v2` shots gain one optional object `board`:
   - `message` (信息点), `visual` (画面), `camera` (enum: fixed, push_in, pull_out, follow, orbit, pan), `speaker` (enum: narration, presenter, dialogue, none), `sound`, `notes`.
   - The spoken line stays in `script.blocks`. Duration stays in `duration_ms`. Start and end come from the timeline. Material stays in `source_material_revision_id`.
   - `label` keeps a short form of 画面, so existing readers keep working.
3. **Model answer.** Each beat is `{message, visual, camera, speaker, line, sound, notes, duration_ms}`. The rules taken from the reference sheet:
   - One shot says one thing.
   - 信息点 is the point, and 台词 is the exact words. They must not repeat each other.
   - 画面 names framing, subject, action, scene and light.
   - Use `speaker: none` with an empty line for a shot with no speech.
   - Durations are estimates. The final timing follows the narration audio.
   - Without a shot plan the table allows up to 30 shots. With a plan (old runs) the count is fixed to the plan, as in `master-follows-shot-plan`.
4. **One material pick.** In `VideoShotMaterialPanel`:
   - A shot with no bound material and exactly one slot pick starts with that pick selected.
   - With several picks, the choice lists only the picks.
   - The user still saves the master once. Nothing is bound without the user's save.
5. **Display.** The 导演稿 review renders the candidate as the table, with L01-style numbers and start–end times. Older masters without `board` show 画面 from `label` and leave the new columns empty.

## Risks

- A 30-row table is a long answer. Rows are short, and the current 128 KiB output limit leaves room.
- Removing the stages changes only new workflow versions. A user who wants a separate script can still write one as reference material.
