## Context

- `material_matching.start` creates a run for scope `shots`. `_execute` plans segments (search words, `footage` real or motion, prompts), searches own and open libraries, judges previews with a vision model, and marks segments `matched`, `gap` or `motion`. Candidates carry `score`, `eligible_main`, `seen`, `reason` and the licence.
- `material_matching.accept` downloads an open candidate under its licence (rights flags supplied by the caller), attaches it to the project and marks it picked in the segment. `attach` puts an existing project material into a segment as a pick.
- `shot_slots.view` reads picks from runs. A shot is `chosen` when it has a pick or a bound material.
- `craft_skills.render` renders a ready AE template into a candidate project material.
- Open licences admitted by the search (CC0, PDM, CC BY, CC BY 4.0, Pexels, Pixabay and NASA terms) all allow commercial use with the stored attribution.

## Decisions

1. **Job.** `material_autofill.start(project, unit)` checks the unit has a draft with shots, then starts one shots run with `auto_fill: true` in its settings, covering only rows with no pick and no bound material. The job state is the run itself plus an `autofill` block in its result: per-row outcome, source, reason and errors.
2. **Pick after search.** When the run finishes searching, rows with an `eligible_main` top candidate are accepted through `accept`. The decision is `public_use_allowed = commercial_use_allowed = model_use_allowed = true` for the licences above. The pick is recorded as automatic, with the score and the model's reason.
3. **Templates.** Rows with status `motion`, plus `gap` rows, go to one model call with:
   - the row text and board columns;
   - the ready templates' `use` and fields.

   The model returns, per row, either `{template, version, content}` or `none` with a reason. Its content is checked against the manifest field rules. Each chosen row is rendered with `craft_skills.render` and attached to its segment with `attach`. A render failure leaves the row as a gap, with the error.
4. **Never overwrite.** A row picked by the user before or during the job is skipped. Own uploads stay.
5. **Display.** The 素材 column reads the slot:
   - `自动 · Pixabay 0.82`;
   - `自动 · AE 数字卡 v1`;
   - `缺口：<reason>`;
   - `已选` for the user's own picks.

   A button shows progress while the run is queued or running.
6. **MCP.** `start_material_autofill(project_id, unit_id)` returns the run id. The existing `get_material_match` and `get_shot_slots` read the result.

## Risks

- A wrong automatic pick: the user reviews the assembled video and swaps a single row. Every auto pick names its source and score.
- Template rendering takes about 15 seconds per row; a 15-row video with five template rows adds about a minute and a half.
