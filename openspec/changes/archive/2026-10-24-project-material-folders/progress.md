# Progress: project-material-folders

- 2026-10-24: proposal written (proposal, design, spec, tasks). Waiting for 确认.
- 2026-10-24: applied. Placement read path, move with rollback, user's-own-copy rule, hooks (准备剪辑, voiceover, rough cut returned/accepted), 导演稿 file, endpoints, floating window tabs, material page filter, drawer action.
- Sandbox run on DB / media / library copies first, then the real run. 海底光缆: 15 files moved (13 user videos with their names, 1 web video, 1 web image), voiceover → 音频/, 导演稿-v11.md, 小样 for tasks 6 and 7. 13 byte-identical platform copies removed from `apps/api/app/media/material`. DB backup before the run: scratchpad `db-before-archive.sqlite`.
- Checked: raw file read through the API from the new place (200); folder scan shows the 15 files as linked; `place=project` filter returns 18 materials; task 7's input copies are independent (Resolve project unaffected). Related tests: 122 passed. Web type-check passed. Browser check not done (DevTools lost the page).
- 2026-10-24: user checked 素材库 → 项目 → 海底光缆 in the floating window: OK. Change archived; spec now in `openspec/specs/project-material-folders/`.
