# master-follows-shot-plan

**Stage:** applied locally (not committed). Kept for runs that still have a shot-plan stage, such as U80. New workflows drop that stage; see `video-storyboard-table`.

**What:** a video director draft (导演稿确认) keeps the accepted shot plan's shots: same number, order, ids and durations. The AI only writes each shot's final narration and visual description. To change the shots, go back to the shot plan.

**Trigger:** U80 (project 41). The shot plan has 15 shots with material in all 15 slots; the director draft (attempt 331) came back with 7 shots. Root causes: the plan was only reference text, and `_video_plan` caps drafts at 8 beats.

**Files:** `proposal.md`, `design.md`, `specs/video-master-from-shot-plan/spec.md`, `tasks.md`, `task_plan.md`, `progress.md`, `findings.md`.

**Next:** accept-on-copy slot check (3.1) is still open. Do not accept U80 attempt 331.
