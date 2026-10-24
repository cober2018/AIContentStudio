# Progress

- 2026-10-22: proposal written; waiting for user confirmation. 海底光缆 sample paused (graphic attempt 329 waiting, not accepted).
- 2026-10-22: applied. Live checks through the real MCP endpoint (local client, bearer read from runtime.env, never printed): `get_stages`, `get_stage_result` (unit 79 attempt 329: 1 candidate, 7 canvases, quality pass, review_url), `get_stage_decision` → `waiting_for_you`, `get_material_match` (run 10: 7 segments, picks/rejections empty), `run_stage` with a wrong hash → `stage_resolution_changed` (code visible, nothing run).
- Card previews: first render 2.3 s per card, cached 0.03 s; review page (`?stage=master&open=result`) shows 7 thumbnails and the 1080×1440 enlargement (checked in Chrome).
- Footage page shows 「都不合适」 on all 7 segments of run 10 (not clicked: the decision is the user's).
- Tests: MCP 74 passed; full API suite 2797 passed, 7 failed, 28 skipped. The 7 failures are outside this change (5 pin an old schema head `a3series00000001` while the tree's head is `matmatch0001` from earlier uncommitted migrations; `test_models_plugins` ×2 and `test_topic_suggest` are model/plugin settings). Web type-check and build pass.
- No unit tests were added beyond the MCP whitelist (user rule: tests only when asked).
