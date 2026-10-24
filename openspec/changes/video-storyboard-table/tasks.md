## 1. Workflow

- [x] 1.1 Video definition: `master` (导演稿) → `prepare`; move shot-direction rules into the `master` instruction. Same for the product video workflow.

## 2. Table

- [x] 2.1 `video_documents`: optional shot `board` {message, visual, camera, speaker, sound, notes}.
- [x] 2.2 `stage_resolver`: 导演稿 answer schema and rules for the table; up to 30 rows, fixed to the plan when one exists.
- [x] 2.3 `stage_master_proposals._video_plan`: build shots, script blocks, timeline and `board` from table rows.

## 3. Web

- [x] 3.1 导演稿 review shows the table (L01 numbers, start–end, all columns; older masters degrade).
- [x] 3.2 `VideoShotMaterialPanel`: start from the slot pick; with several picks list only those.

## 4. Verify

- [x] 4.1 On a DB copy: a new video workflow has two stages; a generated 导演稿 is a full table; U80 still generates 15 rows from its plan.
- [x] 4.2 Related API tests pass; web build passes.

## 5. Docs

- [x] 5.1 README, task_plan, progress, findings; root README entry.
