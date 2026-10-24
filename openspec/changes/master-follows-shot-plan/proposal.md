## Why

On U80 the user accepted a shot plan of 15 shots and filled material into all 15 shot slots. The next stage, 导演稿确认 (`master`, `stage.master.propose`), then produced a director draft of 7 shots. Accepting it would rebuild the slots as 7 shots, and 8 shots' material would no longer line up.

The causes are in the platform, not the model:

- The director draft rebuilds shots from scratch. The model gets the accepted shot plan only as reference text. The output contract asks for "title and beats", with no count and no tie to the plan.
- `_video_plan` caps a director draft at 1–8 beats. A plan with more than 8 shots can never come through intact, while the shot plan allows up to 100 shots and the video master up to 300.
- The draft assigns its own shot ids (`shot-1…`), while the plan uses `shot-0…`. The slots have to map them by order.

The user's understanding is that the shot plan and the director draft are the same set of shots. The shot plan comes first and the director draft finalises it. Under the first design principle ("the platform fixes outcomes, not steps"), "the director draft keeps the accepted shot plan's shots" is an outcome the platform must guarantee, not something the user has to remind the AI of each time.

## What Changes

- When a video director-draft stage has an accepted shot plan upstream, the platform SHALL take the shots from that plan: number, order, id and duration. The model SHALL only write each shot's final narration and visual description, polishing the plan's text, and SHALL return exactly one beat per planned shot, in order.
- A model answer with a different number of beats SHALL be rejected as invalid output. The provider answered, so the user can generate again directly.
- The 8-beat cap SHALL apply only when there is no accepted shot plan.
- Draft shot ids SHALL equal the plan's shot ids, so material in shot slots lines up by id.
- To change the shots (merge, split, drop), the user goes back to the shot-plan stage. The director draft does not do it.

## Impact

- API: `stage_master_proposals` (`_video_plan`, candidate building) and the director-draft output contract in `stage_resolver`, where the expected beat count is stated to the model. No migration.
- Existing masters and earlier drafts are not rewritten. Shot slots still map older drafts by order.
- U80: the current 7-shot draft (attempt 331) is left as is. After this change the user generates again, and the new draft will have the 15 planned shots.
- Out of scope: other modalities, the shot-plan stage itself, and any automatic acceptance.
