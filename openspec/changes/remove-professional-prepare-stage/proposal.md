## Why

Video workflows end with 专业执行准备 after 导演稿. It packs the saved master into a 导演包 that the user accepts. The automatic edit no longer uses it: the edit task builds its own 导演包 from the saved master (`prepare_edit`). The stage only adds a step that goes stale whenever the master changes and shows 「需要处理」, which confuses the user. The user asked to remove it (2026-10-24).

## What Changes

- **New video workflows have one stage: 导演稿.** The 专业执行准备 node is removed from the persona video definition and the product video definition.
- **Defaults move.** The system-owned product video default moves to the new definition the next time it is used (same rule as the earlier storyboard change). Persona video defaults the user saved (persona 2 and 3) move too, as the user asked.
- **Existing runs keep their data but hide the stage.** Runs that already have 专业执行准备 (such as 海底光缆) keep it in the record, but it no longer shows in the step list, no longer counts as 「需要处理」, and 准备剪辑 no longer rebuilds or accepts it. It stays reachable under 更多 for anyone who wants it.
- **准备剪辑 becomes:** place material → decide DaVinci / AE → save → create and queue the edit task.
- Text and graphic workflows are unchanged.

## Impact

- API: `starter_personas._definition` (video branch), `workflow_templates` product video default (move when the old definition has `prepare`), a one-time move of persona 2/3 video defaults to a new revision; `edit_handoff` drops the prepare step.
- Web: `StageSubSteps` and the recipe summary skip `stage.professional.prepare`; `CreationRecipePanel` header no longer asks to rebuild it.
- No migration; old runs and packages stay as they are.
