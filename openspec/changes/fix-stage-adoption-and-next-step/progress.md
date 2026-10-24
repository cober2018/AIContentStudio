# Progress

- 2026-10-22: proposal, design, spec and tasks written.
- 2026-10-22: applied.
  - Adoption checks compare `adoption_basis` / `context_basis`, and errors carry `changed`.
  - Web: next-step card and plain-language accept errors.
  - On a DB copy, attempt 328 was accepted, and the continuation started the master stage (attempt 330 on the copy only). Changed upstream, master and model configuration revision are each still refused and named.
  - API tests `-k "stage or adoption or creative or recipe or master or mcp or material"`: 1042 passed, 2 skipped. Web build passes.
  - API restarted while idle. In the browser on U80, the card shows 「镜头计划」等你确认, and 去确认 opens the shot-plan stage with its result expanded. Not accepted.
- 2026-10-22: at the user's request, the top card was removed and the stages became sub-steps under 内容方案 in the left navigation (`StageSubSteps.tsx`). Build passes; checked in the browser on U80 (镜头计划 highlighted, 等你确认).
- 2026-10-22: the user accepted the shot plan (attempt 328). The automatic director-draft attempt 330 failed about 5 s into the model call and was sealed unknown; no detail was recorded. No path out of unknown existed.
- 2026-10-22: added provider-failure classification and the user's abandon action.
  - On a DB copy: attempt 330 was abandoned, the preview was ready, and a new run produced attempt 331 (`waiting_input`, real model call on the copy).
  - API tests (`-k "stage or adoption or creative or recipe or master or mcp or material or provider or model or generation"`): 1212 passed, 2 skipped, 2 failed. The 2 failures are in `tests/test_models_plugins.py` (`test_models_disabled_profile_not_routed`, `test_plugins_put_and_view`) and fail the same way with this change's provider edits reverted. They come from earlier uncommitted settings/runtime-config work, not this change.
  - Web build passes. API restarted while idle. On U80 the 导演稿确认 stage shows the abandon box; it was not clicked.
- 2026-10-22: the user gave up attempt 330 on the platform, but the page stayed in read-back mode ("回读原尝试（不重发）", preview disabled). The page rebuilt a pending request from any unknown result. Fixed:
  - `restoreStageRequest` ignores a given-up attempt.
  - `unresolvedLocal` ignores it too.
  - The rerun skips the separate rerun feedback, which the server refuses on an unknown attempt.
  - The build passes. In the browser, preview resolved and 「再次生成（新尝试）」 is enabled. It was not clicked.
