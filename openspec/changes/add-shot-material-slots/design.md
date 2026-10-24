## Context

- **Video draft shots** (`VideoShot`) already have `source_material_revision_id` and `production` (`existing` / `api_image` / `web_video` with prompt / `ae`).
- **Shot plan output** (stage `shots`) has `script`, `visual`, `purpose` and `asset_requirements`.
- **Match runs** with scope `shots` store per-segment candidates, `picked_ids` and uploads, keyed by shot id and linked to project and unit.

## Decisions

- **Brief lives with the shot's material search (changed during apply, 2026-10-22).** The search words, prompt and route are fields of the shot's segment in its latest match run (`query_zh`, `queries_en`, `keywords_en`, `prompt`, `footage`).
  - The planner writes them, including the new `prompt` field.
  - Shots without a prompt get one from a planner-only call (`POST …/shot-slots/briefs`), with no search.
  - The user edits them with `PATCH …/shot-slots/{id}/brief`.
  - Why: adding fields to the shot-plan or draft schema would change pinned schema hashes. A brief stored in the draft also would not exist before the draft does, and U80 has no draft yet.
- **Slot view is derived, not stored.** Candidates come from the unit's match runs by shot id, plus the draft binding.
  - Why: avoids a second store that could disagree with the match runs or the draft.
- **Generation prompt reuse:** choosing the web-video route pre-fills `production.prompt` from `brief.prompt`. The user can still edit it.
- **Shot ids:** the draft numbers shots `shot-1…` while the plan numbers `shot-0…` (`stage_master_proposals._video_plan`).
  - Runs created before the unit's first draft are mapped by order: plan order k becomes the draft shot with order k.
  - Later runs use draft ids.
- **Slots without any search** take uploads through a finished one-shot run (`…/upload-target`), so uploads stay in the match-run store.
- **Status:** 已选定 means the user picked or uploaded something for the shot, or the draft binds a source. Being put into the final cut is still the draft binding.

## Risks

- Older runs without shot ids do not appear in slots. They stay visible in the 素材库.
