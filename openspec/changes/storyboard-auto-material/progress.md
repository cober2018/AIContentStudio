# Progress

## 2026-10-23
- Proposal written. No code changed.
- Applied (user confirmed):
  - `services/material_autofill.py`: `start` runs a shots search with `auto_fill` over rows with no pick or bound material; `finish` (inside the search worker, run still running) accepts eligible top candidates with licence rights and records `auto`, sends motion and gap rows to one model call that picks and fills ready templates without image slots, renders with `craft_skills.render`, records the pick with `record_attach`, and writes `autofill.rows` (outcome, source, score, reason).
  - `material_matching`: `auto_fill` setting; `record_attach` split out of `attach` (usable mid-run, labelled, auto flag); `accept` stores `auto`.
  - `shot_slots.view`: picks carry `auto`; slots carry `autofill`.
  - REST `POST /content-projects/{p}/units/{u}/material-autofill`; MCP `start_material_autofill` (pinned tool list updated; `material_autofill_*` codes surface).
  - Web: AI 补齐素材 button with progress and explanation on the 分镜表; 素材 column shows 自动 source/score, 缺口 reason, 已选 or 已绑定; shot slots show 自动 picks and gap reasons.
- API suite: only the 7 pre-existing failures. Web build passes.
- Verify on a DB copy with the real models (U80): regenerated and accepted the 15-row table (master 133); cleared picks on 6 rows; auto-fill ran 440 s. Results: shot-2 and shot-3 (数据) filled with AE 数字卡 (600+条, >150万公里); shot-0 (UI transition) and shot-1, 4, 5 (real) left as gaps with reasons — best stock scored 0.45 / 0.40 / 0.20 (no cable in frame; diagram instead of a real cross-section; patch cords instead of a bare fibre), and the model found no fitting template. The 9 earlier picks were untouched; the master was unchanged with nothing bound. The stock auto-pick path was not exercised because no candidate reached 0.6. NASA search failed during the run; the other four sources answered.
- API restarted while idle.
