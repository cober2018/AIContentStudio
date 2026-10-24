## Context

- Accepted upstream results reach the director-draft stage as `resolved["upstream"][node]`. For U80, `upstream["shots"]["selected_content"]["shots"]` holds 15 shots. Each shot has `id`, `order`, `script`, `visual`, `purpose`, `framing`, `duration_seconds` and `asset_requirements`.
- `stage_resolver` gives the director draft a response schema of `{title, beats:[{narration, visual, duration_ms?}]}` and rules that do not mention the plan.
- `stage_master_proposals._video_plan` turns beats into `video.master.v2`. It allows 1–8 beats, assigns `script-{n}`, `shot-{n}` and `item-{n}` ids from 1, and uses 1500 ms when a beat has no duration.
- `video_documents` accepts ids matching `^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$` and up to 300 shots, so plan ids such as `shot-0` are valid.

## Decisions

1. **Plan skeleton.** Add a small helper that reads the accepted shot plan from `resolved["upstream"]`. It looks for any upstream handoff whose `output_schema` is a `video.shot-plan.*` schema, and returns its shots sorted by `order`, or `None` when there is none.
2. **Tell the model the count.** When a plan exists, the director-draft output contract states two things:
   - the exact number of beats: `minItems = maxItems = N` in the response schema;
   - a rule: "Return exactly N beats, one per accepted shot, in the shot plan's order. Keep each shot's meaning; polish narration and visual. Do not merge, split, add or drop shots."

   This sits in `stage_resolver`, where the contract is built, so the preview shows the user exactly what is asked.
3. **Build from the plan.** In `_video_plan`, when a plan is supplied:
   - The number of beats must equal N; otherwise `stage_proposal_output_invalid`. That error is already treated as "provider answered", so the stage can be run again.
   - Shot i takes the plan's `id`, `order` and `duration_ms`. This duration is an estimate; the final timing follows the narration audio, and the rule tells the model so. The duration is `duration_seconds × 1000`, clamped to the master's 200–15000 ms range. The beat's `duration_ms` is used only when the plan has none.
   - Script block and timeline item ids are derived from the shot id (`script-{shot id}`, `item-{shot id}`), so all three stay stable together.
   - Narration and visual come from the beat. An empty beat field falls back to the plan's `script` or `visual`.
   - Without a plan, the current behaviour is unchanged, including the 1–8 cap.
4. **No new storage, no change to provenance.** The plan is already in the frozen resolution, so the resolution hash already covers it. Accepted masters keep their ids. Shot slots keep the by-order mapping for drafts made before this change.

## Risks

- A long plan means a longer model answer. 15 short beats are well within current limits, and the plan's own cap is 100.
- A model that keeps returning the wrong count fails visibly with "output invalid", and the user can retry. Nothing is silently trimmed.
