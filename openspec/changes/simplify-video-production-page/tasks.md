## 1. 内容方案

- [x] 1.1 `StageProposalReview`: video drafts render the table only (no video editor below).
- [x] 1.2 Video plan page: `CreationRecipePanel simple` shows 导演稿 + one state button; stages, request preview, history in 更多. Master panel hidden on this step.
- [x] 1.3 采用这版: accept (creates the master) → start AI 补齐素材; plain-word failure with a retry hint.

## 2. 制作内容

- [x] 2.1 `VideoStudioShell view="simple"`: main area is the table, 配音/音乐/封面, 导演包; everything else (per-shot material desk, script/shot editors, project assets, ASR, subtitles, timeline, final MP4) behind 更多. `ContentMasterPanel` keeps only 保存当前主稿 in front; versions and checks behind 更多.
- [ ] 2.2 One-click 生成配音 from the 台词 column. Not built: there is no server path that turns the master's 台词 into a voice track in one step today (TTS only exists as a workflow audio stage or the manual native-generation panel). Needs its own small change.

## 3. Verify

- [x] 3.1 `tsc` and web build pass. U80 plan page shows one 15-row table, 采用这版 and 更多; make page shows table, 配音, 导演包 and the 更多 toggle opens the rest.

## 4. Docs

- [x] 4.1 README, task_plan, progress, findings.
