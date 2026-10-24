## 1. Contract

- [x] 1.1 Helper that returns the accepted shot plan's shots from `resolved["upstream"]` (any `video.shot-plan.*` handoff), or none.
- [x] 1.2 Director-draft output contract: with a plan, fix the beat count to N and add the "one beat per planned shot, in order" rule.

## 2. Build

- [x] 2.1 `_video_plan` with a plan: require N beats; take id, order and duration from the plan; derive script and item ids from the shot id; fall back to plan text for empty fields.
- [x] 2.2 Without a plan: keep the current behaviour and the 1–8 cap.

## 3. Verify

- [ ] 3.1 On a DB copy, generate the U80 director draft: 15 shots with the plan's ids. Accept it on the copy and check shot slots still show 15 chosen.
- [x] 3.2 A wrong-count answer fails as output invalid and the stage can run again.
- [x] 3.3 Related API tests pass; update pinned tests only where they assert the old cap for plan-backed drafts.

## 4. Docs

- [x] 4.1 README, task_plan, progress, findings; root README entry.
